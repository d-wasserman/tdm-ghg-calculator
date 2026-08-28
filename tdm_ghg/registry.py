# --------------------------------
# Copyright 2026 David J. Wasserman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# --------------------------------
"""Measure registry for TDM GHG reduction functions.

The global ``registry`` singleton holds metadata for every measure function
decorated with ``@register_measure``. Registrations happen at import time
when mitigations.py is imported.

Typical usage::

    from tdm_ghg.registry import registry
    from tdm_ghg.context import TDMContext, Scale, LocationType, LandUseType

    ctx = TDMContext(
        scale=Scale.PROJECT_SITE,
        location_type=LocationType.URBAN,
        land_use_type=LandUseType.RESIDENTIAL,
        params={"proposed_residential_density": 20.0},
    )
    applicable = registry.filter(ctx, subsector="land_use")
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Collection, Optional

from tdm_ghg.context import LandUseType, LocationType, Mode, Scale, TDMContext


class MeasureExclusivityError(ValueError):
    """Raised when mutually exclusive measures are activated together.

    CAPCOA requires selecting at most one measure from each mutually
    exclusive group (e.g. T-5 voluntary vs. T-6 mandatory commute trip
    reduction). The subsector orchestrators raise this rather than silently
    combining conflicting measures, which would overstate the reduction.
    Resolve by excluding all but one measure via ``excluded_measure_ids``, or
    by scoping inputs per measure with measure-ID-keyed params.
    """


class MeasureSelectionError(ValueError):
    """Raised when an explicit ``TDMContext.measures`` selection is invalid.

    With an explicit selection, problems that would otherwise cause a
    measure to be silently skipped fail loudly instead: unknown measure
    IDs, selected measures that are inapplicable to the context (scale,
    location type, or land use type), selected measures excluded by the
    orchestrator (``excluded_measure_ids`` or ``use_brt`` logic), and
    selected measures whose required parameters are missing from
    ``TDMContext.params``.
    """


@dataclass
class MeasureMetadata:
    """Metadata describing a single CAPCOA TDM measure.

    Attributes
    ----------
    measure_id : str
        CAPCOA measure identifier, e.g. ``"T-1"``.
    name : str
        Human-readable measure name.
    subsector : str
        Subsector key, e.g. ``"land_use"``, ``"transit"``. See
        ``SUBSECTOR_CAPS`` in subsectors.py for valid values.
    scale : Scale
        Scale of application (PROJECT_SITE or PLAN_COMMUNITY).
    location_types : frozenset[LocationType]
        Locational contexts where this measure applies.
    land_use_types : frozenset[LandUseType] | None
        Land use types where this measure applies, or ``None`` if the
        measure applies to all land use types.
    measure_max : float
        Individual measure maximum reduction as a positive fraction
        (e.g., ``0.30`` for a 30% cap). The measure function itself
        enforces this cap; this field is for metadata/documentation.
    mutually_exclusive_with : frozenset[str]
        Measure IDs that cannot be combined with this measure. Not
        automatically enforced; pass ``excluded_measure_ids`` to the
        subsector orchestrators to handle exclusivity.
    func : Callable
        The underlying measure function.
    target_modes : frozenset[Mode]
        Travel modes the measure's avoided auto travel shifts toward, drawn
        from the ``Mode`` taxonomy (never includes ``Mode.SOV``, the source).
        A measure that applies to all modes declares ``NON_SOV_MODES``;
        clean-vehicle measures that change emissions per mile without shifting
        mode declare an empty set. Used by ``tdm_ghg.derived_metrics`` for
        mode-shift estimation.
    """
    measure_id: str
    name: str
    subsector: str
    scale: Scale
    location_types: frozenset
    land_use_types: Optional[frozenset]
    measure_max: float
    mutually_exclusive_with: frozenset
    func: Callable
    target_modes: frozenset = frozenset()

    @property
    def implies_mode_shift(self) -> bool:
        """Whether this measure implies any mode shift.

        ``True`` when the measure declares one or more ``target_modes``;
        ``False`` for clean-vehicle measures (e.g. EV charging, cleaner fuels)
        that cut emissions per mile without changing travel mode.
        """
        return bool(self.target_modes)


class MeasureRegistry:
    """Registry of all decorated TDM measure functions."""

    def __init__(self) -> None:
        self._measures: dict[str, MeasureMetadata] = {}

    def register(self, meta: MeasureMetadata) -> None:
        """Register a measure. Called automatically by ``@register_measure``."""
        self._measures[meta.measure_id] = meta

    def get(self, measure_id: str) -> Optional[MeasureMetadata]:
        """Return metadata for a single measure, or None if not found."""
        return self._measures.get(measure_id)

    @property
    def measures(self) -> dict[str, MeasureMetadata]:
        """Read-only view of all registered measures."""
        return dict(self._measures)

    def filter(
        self,
        context: TDMContext,
        subsector: Optional[str] = None,
        excluded_ids: Collection[str] = (),
    ) -> list[MeasureMetadata]:
        """Return measures applicable to the given context.

        Parameters
        ----------
        context : TDMContext
            Analysis context to filter against.
        subsector : str, optional
            If provided, only return measures in this subsector.
        excluded_ids : collection of str
            Measure IDs to exclude (for handling mutual exclusivity).

        Returns
        -------
        list[MeasureMetadata]
            Measures matching all filter criteria, in registration order.
        """
        results = []
        for meta in self._measures.values():
            if meta.scale != context.scale:
                continue
            if context.location_type not in meta.location_types:
                continue
            if (meta.land_use_types is not None
                    and context.land_use_type not in meta.land_use_types):
                continue
            if subsector is not None and meta.subsector != subsector:
                continue
            if meta.measure_id in excluded_ids:
                continue
            results.append(meta)
        return results

    def call_measure(
        self,
        meta: MeasureMetadata,
        params: dict[str, Any],
    ) -> Optional[float]:
        """Call a measure function, resolving each argument from ``params``.

        Parameter resolution uses ``inspect`` to match keys to function
        argument names, with two layers (most specific wins):

        1. **Measure-scoped overrides** — a ``params`` entry keyed by this
           measure's ID (e.g. ``params["T-9"]``) holding a sub-dict. Values
           there apply only to this measure. Use this to disambiguate
           parameter-name collisions, where a single name (e.g.
           ``transit_mode_share``) means different things to different
           measures, or to scope activation to a specific measure.
        2. **Flat (shared) params** — top-level ``params`` entries, applied to
           every measure whose signature accepts that name.

        Returns ``None`` if any required (no-default) argument is unresolved,
        allowing the orchestrator to skip that measure gracefully. A measure
        can therefore be activated by flat params, by a measure-scoped
        sub-dict, or by a combination of the two.

        Parameters
        ----------
        meta : MeasureMetadata
            Measure to call.
        params : dict[str, Any]
            Parameter dictionary (typically ``TDMContext.params``). May mix
            flat parameter entries with measure-ID-keyed override sub-dicts.

        Returns
        -------
        float or None
            The GHG reduction fraction, or None if required params are absent.
        """
        kwargs, missing = self._resolve_kwargs(meta, params)
        if missing:
            return None  # required param(s) missing — skip this measure
        return meta.func(**kwargs)

    def missing_params(
        self,
        meta: MeasureMetadata,
        params: dict[str, Any],
    ) -> list[str]:
        """Return required argument names of ``meta`` unresolved by ``params``.

        Resolution follows the same two layers as ``call_measure``
        (measure-scoped overrides, then flat params). An empty list means
        the measure can be called.
        """
        return self._resolve_kwargs(meta, params)[1]

    def _resolve_kwargs(
        self,
        meta: MeasureMetadata,
        params: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        """Resolve call kwargs for ``meta`` and list unresolved required args."""
        scoped = params.get(meta.measure_id)
        overrides = scoped if isinstance(scoped, dict) else {}
        sig = inspect.signature(meta.func)
        kwargs: dict[str, Any] = {}
        missing: list[str] = []
        for name, param in sig.parameters.items():
            if name in overrides:
                kwargs[name] = overrides[name]
            elif name in params:
                kwargs[name] = params[name]
            elif param.default is inspect.Parameter.empty:
                missing.append(name)
        return kwargs, missing


# Module-level singleton — populated when mitigations.py is imported.
registry = MeasureRegistry()


def register_measure(
    measure_id: str,
    name: str,
    subsector: str,
    scale: Scale,
    location_types: Collection[LocationType],
    measure_max: float,
    land_use_types: Optional[Collection[LandUseType]] = None,
    mutually_exclusive_with: Collection[str] = (),
    target_modes: Collection[Mode] = (),
) -> Callable:
    """Decorator that registers a measure function with the global registry.

    Parameters
    ----------
    measure_id : str
        CAPCOA measure ID, e.g. ``"T-1"``.
    name : str
        Human-readable name.
    subsector : str
        Subsector key (must match keys in ``SUBSECTOR_CAPS``).
    scale : Scale
        Scale of application.
    location_types : collection of LocationType
        Applicable locational contexts.
    measure_max : float
        Individual measure maximum (positive fraction, e.g. ``0.30``).
    land_use_types : collection of LandUseType, optional
        Applicable land use types. ``None`` means all types.
    mutually_exclusive_with : collection of str, optional
        IDs of measures that cannot be combined with this one.
    target_modes : collection of Mode, optional
        Travel modes the measure shifts avoided auto travel toward (never
        ``Mode.SOV``). Use ``NON_SOV_MODES`` for measures that apply to all
        modes; leave empty for clean-vehicle measures with no mode shift.

    Returns
    -------
    Callable
        The unmodified decorated function.
    """
    def decorator(func: Callable) -> Callable:
        meta = MeasureMetadata(
            measure_id=measure_id,
            name=name,
            subsector=subsector,
            scale=scale,
            location_types=frozenset(location_types),
            land_use_types=(
                frozenset(land_use_types) if land_use_types is not None else None
            ),
            measure_max=measure_max,
            mutually_exclusive_with=frozenset(mutually_exclusive_with),
            func=func,
            target_modes=frozenset(target_modes),
        )
        registry.register(meta)
        return func
    return decorator
