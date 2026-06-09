# --------------------------------
# Copyright 2026 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------
"""Subsector orchestration for TDM GHG reduction calculations.

Each ``run_*`` function filters the measure registry to measures applicable
in the provided ``TDMContext``, calls each with matching parameters from
``context.params``, then combines results with multiplicative dampening
capped at the CAPCOA subsector maximum.

Measures whose required parameters are absent from ``context.params`` are
silently skipped. Mutual exclusivity (e.g., T-28 vs. T-26/T-27/T-46) is
handled via the ``excluded_measure_ids`` argument.

Subsector caps by scale (from CAPCOA 2024 Table, Transportation section):

  Project/Site
    land_use                65%  (T-1 through T-4, T-55)
    trip_reduction          45%  commute VMT (T-5 through T-13)
    parking_management      35%
    school_programs         72%  school VMT (T-40, T-56)

  Plan/Community
    land_use                30%
    neighborhood_design     10%  (T-18 through T-22-D)
    trip_reduction           2.3% commute VMT
    parking_management      30%
    transit                 15%  (T-25 through T-29, T-46)

Multi-subsector cap (Land Use + Neighborhood Design + Parking + Transit): 70%
"""

from __future__ import annotations

from typing import Collection

from tdm_ghg.context import TDMContext
from tdm_ghg.registry import MeasureExclusivityError, MeasureMetadata, registry
from tdm_ghg.utils import multiplicative_dampening

# Subsector caps as positive fractions. Negated when passed to
# multiplicative_dampening (which uses abs() internally, so either sign works,
# but negative is consistent with the reduction sign convention).
SUBSECTOR_CAPS: dict[tuple, float] = {
    # Project/Site
    ("project_site", "land_use"):           0.65,
    ("project_site", "trip_reduction"):     0.45,
    ("project_site", "parking_management"): 0.35,
    ("project_site", "school_programs"):    0.72,
    # Plan/Community
    ("plan_community", "land_use"):              0.30,
    ("plan_community", "neighborhood_design"):   0.10,
    ("plan_community", "trip_reduction"):        0.023,
    ("plan_community", "parking_management"):    0.30,
    ("plan_community", "transit"):               0.15,
    ("plan_community", "clean_vehicles"):        1.00,
}

# Cross-subsector cap applied to Land Use + Neighborhood Design + Parking + Transit.
MULTI_SUBSECTOR_CAP: float = 0.70


def run_subsector(
    context: TDMContext,
    subsector: str,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Compute the combined GHG reduction for a single subsector.

    Filters the registry for measures applicable to ``context`` and
    ``subsector``, calls each with matching parameters, then applies
    multiplicative dampening with the CAPCOA subsector cap.

    Parameters
    ----------
    context : TDMContext
        Analysis context (scale, location type, land use type, params).
    subsector : str
        Subsector key, e.g. ``"land_use"``, ``"transit"``.
    excluded_measure_ids : collection of str, optional
        Measure IDs to skip (use for mutual exclusivity, e.g. exclude
        ``{"T-26","T-27","T-46"}`` when using BRT/T-28).

    Returns
    -------
    float
        Combined subsector GHG reduction as a decimal fraction (negative =
        reduction). Returns 0.0 if no applicable measures have sufficient
        parameters.
    """
    cap_key = (context.scale.value, subsector)
    subsector_cap = SUBSECTOR_CAPS.get(cap_key)

    measures = registry.filter(context, subsector=subsector, excluded_ids=excluded_measure_ids)
    activated: list[MeasureMetadata] = []
    reductions = []
    for meta in measures:
        result = registry.call_measure(meta, context.params)
        if result is not None:
            activated.append(meta)
            reductions.append(result)

    conflicts = _find_exclusivity_conflicts(activated)
    if conflicts:
        raise MeasureExclusivityError(_format_conflicts(subsector, conflicts))

    cap_arg = -subsector_cap if subsector_cap is not None else None
    return multiplicative_dampening(reductions, cap_arg)


def _find_exclusivity_conflicts(
    activated: Collection[MeasureMetadata],
) -> set[frozenset]:
    """Return the set of mutually exclusive measure pairs among ``activated``.

    Each conflict is a ``frozenset`` of two measure IDs, so a symmetric or
    one-directional ``mutually_exclusive_with`` declaration yields a single
    entry regardless of declaration direction.
    """
    active_ids = {meta.measure_id for meta in activated}
    conflicts: set[frozenset] = set()
    for meta in activated:
        for other in meta.mutually_exclusive_with & active_ids:
            conflicts.add(frozenset((meta.measure_id, other)))
    return conflicts


def _format_conflicts(subsector: str, conflicts: Collection[frozenset]) -> str:
    pairs = ", ".join(sorted(" + ".join(sorted(pair)) for pair in conflicts))
    return (
        f"Mutually exclusive measures were activated together in subsector "
        f"'{subsector}': {pairs}. CAPCOA requires selecting one measure per "
        f"conflict. Resolve by excluding all but one via excluded_measure_ids, "
        f"or scope inputs per measure using measure-ID-keyed params "
        f"(e.g. params={{'T-6': {{...}}}})."
    )


def run_land_use(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Land Use subsector.

    Applicable measures (by context):
      - Project/Site: T-1, T-2, T-3, T-4, T-55 (cap 65%)
      - Plan/Community: T-17 (cap 30%)

    Notes
    -----
    T-55 is mutually exclusive with T-1 and T-3. When using T-55, pass
    ``excluded_measure_ids={"T-1","T-3"}`` (or scope params per measure) to
    avoid a ``MeasureExclusivityError``.
    """
    return run_subsector(context, "land_use", excluded_measure_ids=excluded_measure_ids)


def run_neighborhood_design(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Neighborhood Design subsector.

    Applicable measures (Plan/Community only, cap 10%):
      T-18, T-19-A, T-19-B, T-20, T-21-A, T-21-B, T-22-A, T-22-B, T-22-C, T-22-D
    """
    return run_subsector(
        context, "neighborhood_design", excluded_measure_ids=excluded_measure_ids
    )


def run_trip_reduction(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Trip Reduction Programs subsector.

    Applicable measures:
      - Project/Site: T-5–T-13 (cap 45% commute VMT)
      - Plan/Community: T-23 (cap 2.3% commute VMT)

    Notes
    -----
    T-5 and T-6 are mutually exclusive (select one). T-5 or T-6 also
    bundle T-7 through T-11, so they cannot be combined with those measures.
    T-12 and T-13 are mutually exclusive (select one parking pricing approach).
    Because many of these measures share the ``pct_employees_eligible``
    parameter, supplying it as a flat param activates several at once and
    raises ``MeasureExclusivityError``. Pass ``excluded_measure_ids`` to
    select one per conflict, or scope inputs with measure-ID-keyed params.
    """
    return run_subsector(
        context, "trip_reduction", excluded_measure_ids=excluded_measure_ids
    )


def run_transit(
    context: TDMContext,
    use_brt: bool = False,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Transit subsector (Plan/Community, cap 15%).

    Parameters
    ----------
    context : TDMContext
        Analysis context.
    use_brt : bool, optional
        If True, use T-28 (Bus Rapid Transit) and exclude T-26, T-27, T-46,
        which are mutually exclusive with BRT when it covers all routes.
        If False (default), use T-26, T-27, T-46 and exclude T-28.
    excluded_measure_ids : collection of str, optional
        Additional measure IDs to exclude, merged with the BRT-driven
        exclusions above.

    Returns
    -------
    float
        Combined transit subsector GHG reduction (negative = reduction).
    """
    if use_brt:
        excluded = {"T-26", "T-27", "T-46"}
    else:
        excluded = {"T-28"}
    excluded |= set(excluded_measure_ids)
    return run_subsector(context, "transit", excluded_measure_ids=excluded)



def run_school_programs(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the School Programs subsector.

    Applicable measures (Project/Site, SCHOOL land use, cap 72% school VMT):
      T-40, T-56
    """
    return run_subsector(
        context, "school_programs", excluded_measure_ids=excluded_measure_ids
    )


def run_parking_management(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Parking or Road Pricing/Management subsector.

    Applicable measures:
      - Project/Site: T-14, T-15, T-16 (cap 35%)
      - Plan/Community: T-24 (cap 30%)
    """
    return run_subsector(
        context, "parking_management", excluded_measure_ids=excluded_measure_ids
    )


def run_clean_vehicles(
    context: TDMContext,
    excluded_measure_ids: Collection[str] = (),
) -> float:
    """Combined reduction for the Clean Vehicles and Fuels subsector.

    Applicable measures (Plan/Community only, cap 100%):
      T-30 (the only quantified measure in this subsector at any scale).
    """
    return run_subsector(
        context, "clean_vehicles", excluded_measure_ids=excluded_measure_ids
    )


def run_multi_subsector(
    context: TDMContext,
    use_brt: bool = False,
) -> float:
    """Combined cross-subsector GHG reduction capped at 70%.

    Combines Land Use, Neighborhood Design, Parking Management, and Transit
    subsectors using multiplicative dampening, per CAPCOA guidance. Trip
    Reduction Programs and School Programs are excluded from this combination
    (they address commute/school VMT independently).

    Parameters
    ----------
    context : TDMContext
        Analysis context.
    use_brt : bool, optional
        Passed through to ``run_transit``. See ``run_transit`` for details.

    Returns
    -------
    float
        Multi-subsector combined GHG reduction (negative = reduction),
        capped at -0.70 (-70%).
    """
    land    = run_land_use(context)
    design  = run_neighborhood_design(context)
    parking = run_parking_management(context)
    transit = run_transit(context, use_brt=use_brt)
    return multiplicative_dampening([land, design, parking, transit], -MULTI_SUBSECTOR_CAP)
