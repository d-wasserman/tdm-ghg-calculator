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

from tdm_ghg.context import LandUseType, LocationType, Scale, TDMContext


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
        """Call a measure function using matching values from ``params``.

        Uses ``inspect`` to match params dict keys to function argument
        names. Returns ``None`` if any required (no-default) argument is
        missing from ``params``, allowing the orchestrator to skip that
        measure gracefully.

        Parameters
        ----------
        meta : MeasureMetadata
            Measure to call.
        params : dict[str, Any]
            Flat parameter dictionary (typically ``TDMContext.params``).

        Returns
        -------
        float or None
            The GHG reduction fraction, or None if required params are absent.
        """
        sig = inspect.signature(meta.func)
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name in params:
                kwargs[name] = params[name]
            elif param.default is inspect.Parameter.empty:
                return None  # required param missing — skip this measure
        return meta.func(**kwargs)


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
        )
        registry.register(meta)
        return func
    return decorator
