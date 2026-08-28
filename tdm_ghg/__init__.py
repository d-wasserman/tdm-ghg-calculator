"""tdm_ghg: Travel Demand Management GHG Reduction Calculator.

A Python library for calculating GHG emission reductions from transportation
demand management (TDM) measures, based on the CAPCOA 2024 Handbook for
Analyzing GHG Emission Reductions, Assessing Climate Vulnerabilities, and
Advancing Health and Equity.

All reduction functions return decimal fractions where negative values
represent GHG reductions (e.g., -0.14 = 14% reduction).

Context-Aware Usage
-------------------
Build a ``TDMContext`` to use the subsector orchestrators, which
automatically filter applicable measures and apply CAPCOA combining rules::

    from tdm_ghg import TDMContext, Scale, LocationType, LandUseType
    from tdm_ghg import run_land_use, run_transit, run_multi_subsector

    ctx = TDMContext(
        scale=Scale.PROJECT_SITE,
        location_type=LocationType.URBAN,
        land_use_type=LandUseType.RESIDENTIAL,
        params={
            "proposed_residential_density": 20.0,
            "transit_mode_share": 0.05,
            "vehicle_mode_share": 0.80,
        },
    )
    land_use_reduction = run_land_use(ctx)
    total = run_multi_subsector(ctx)

Direct Function Usage
---------------------
All measure functions are also accessible directly for single-measure use::

    from tdm_ghg import t1_increase_residential_density
    result = t1_increase_residential_density(proposed_residential_density=20.0)

Subsectors and Caps
-------------------
Land Use (Project/Site, T-1 through T-4, T-55): cap 65%
    t1_increase_residential_density       [residential only]
    t2_increase_job_density               [commercial only]
    t3_provide_transit_oriented_development
    t4_integrate_affordable_housing       [residential only]
    t55_infill_development                [residential; excl. T-1 and T-3]

Trip Reduction Programs (Project/Site, T-5 through T-13): cap 45% commute VMT
    t5_implement_voluntary_commute_trip_reduction   [excl. T-6, T-7–T-11]
    t6_implement_mandatory_commute_trip_reduction   [excl. T-5, T-7–T-11]
    t7_implement_commute_trip_reduction_marketing   [excl. T-5, T-6]
    t8_provide_ridesharing_program                  [excl. T-5, T-6]
    t9_implement_subsidized_transit_program         [excl. T-5, T-6]
    t10_provide_end_of_trip_bicycle_facilities      [excl. T-5, T-6]
    t11_provide_employer_sponsored_vanpool          [excl. T-5, T-6]
    t12_price_workplace_parking                     [excl. T-13]
    t13_implement_employee_parking_cash_out         [excl. T-12]

Parking Management (Project/Site, T-14 through T-16): cap 35%
    t14_provide_ev_charging_infrastructure
    t15_limit_residential_parking_supply            [residential only]
    t16_unbundle_residential_parking_costs          [residential only]

Land Use (Plan/Community, T-17): cap 30%
    t17_improve_street_connectivity

Neighborhood Design (Plan/Community, T-18 through T-22-D): cap 10%
    t18_provide_pedestrian_network_improvement
    t20_expand_bikeway_network
    t21a_implement_conventional_carshare
    t21b_implement_electric_carshare
    t22a_implement_pedal_bikeshare
    t22b_implement_electric_bikeshare
    t22c_implement_scootershare
    t22d_transition_conventional_to_electric_bikeshare

Trip Reduction Programs (Plan/Community, T-23): cap 2.3% commute VMT
    t23_provide_community_based_travel_planning     [residential only]

Parking Management (Plan/Community, T-24): cap 30%
    t24_implement_market_price_public_parking

Transit (Plan/Community, T-25 through T-29, T-46): cap 15%
    t25_extend_transit_network_coverage_or_hours
    t26_increase_transit_service_frequency    [excl. T-28 when BRT]
    t27_implement_transit_supportive_roadway_treatments  [excl. T-28]
    t28_provide_bus_rapid_transit             [excl. T-26/T-27/T-46]
    t29_reduce_transit_fares
    t46_provide_transit_shelters              [excl. T-28 when BRT]

School Programs (Project/Site, T-40 & T-56): cap 72% school VMT
    t40_establish_school_bus_program
    t56_active_modes_transportation_youth

Multi-Subsector (Land Use + Neighborhood Design + Parking + Transit): cap 70%

Utilities
---------
    multiplicative_dampening
    registry               (MeasureRegistry — inspect all registered measures)

Derived Metrics
---------------
Back-calculate absolute quantities from the library's percent reductions given
supplementary baseline inputs (baseline VMT, average trip distance, emission
factor, baseline mode shares)::

    from tdm_ghg import run_multi_subsector, trips_reduced, co2_tonnes_reduced
    from tdm_ghg import per_measure_reductions, estimate_mode_split

    frac = run_multi_subsector(ctx)
    trips = trips_reduced(baseline_vmt=1_000_000, reduction_fraction=frac,
                          average_trip_distance=9.5)
    tonnes = co2_tonnes_reduced(1_000_000, frac)
    split = estimate_mode_split(per_measure_reductions(ctx),
                                baseline_mode_shares={"auto": 0.80, "transit": 0.05,
                                                      "bike": 0.05, "walk": 0.10})
"""

# Context and registry — import order matters: context first, then registry,
# then mitigations (which registers functions at import time).
from tdm_ghg.context import LandUseType, LocationType, Scale, TDMContext
from tdm_ghg.registry import MeasureExclusivityError, MeasureSelectionError, registry

# Importing mitigations registers all @register_measure functions.
from tdm_ghg.mitigations import (
    t1_increase_residential_density,
    t2_increase_job_density,
    t3_provide_transit_oriented_development,
    t4_integrate_affordable_housing,
    t55_infill_development,
    t5_implement_voluntary_commute_trip_reduction,
    t6_implement_mandatory_commute_trip_reduction,
    t7_implement_commute_trip_reduction_marketing,
    t8_provide_ridesharing_program,
    t9_implement_subsidized_transit_program,
    t10_provide_end_of_trip_bicycle_facilities,
    t11_provide_employer_sponsored_vanpool,
    t12_price_workplace_parking,
    t13_implement_employee_parking_cash_out,
    t14_provide_ev_charging_infrastructure,
    t15_limit_residential_parking_supply,
    t16_unbundle_residential_parking_costs,
    t17_improve_street_connectivity,
    t18_provide_pedestrian_network_improvement,
    t19a_construct_or_improve_bike_facility,
    t19b_construct_or_improve_bike_boulevard,
    t20_expand_bikeway_network,
    t21a_implement_conventional_carshare,
    t21b_implement_electric_carshare,
    t22a_implement_pedal_bikeshare,
    t22b_implement_electric_bikeshare,
    t22c_implement_scootershare,
    t22d_transition_conventional_to_electric_bikeshare,
    t23_provide_community_based_travel_planning,
    t24_implement_market_price_public_parking,
    t25_extend_transit_network_coverage_or_hours,
    t26_increase_transit_service_frequency,
    t27_implement_transit_supportive_roadway_treatments,
    t28_provide_bus_rapid_transit,
    t29_reduce_transit_fares,
    t46_provide_transit_shelters,
    t40_establish_school_bus_program,
    t56_active_modes_transportation_youth,
    t30_use_cleaner_fuel_vehicles,
)

from tdm_ghg.subsectors import (
    SUBSECTOR_CAPS,
    MULTI_SUBSECTOR_CAP,
    run_subsector,
    run_land_use,
    run_neighborhood_design,
    run_trip_reduction,
    run_transit,
    run_school_programs,
    run_parking_management,
    run_clean_vehicles,
    run_multi_subsector,
)

from tdm_ghg.utils import multiplicative_dampening

from tdm_ghg.derived_metrics import (
    DEFAULT_EMISSION_FACTOR_G_PER_MILE,
    GRAMS_PER_METRIC_TON,
    NON_AUTO_MODES,
    MODE_KEYWORDS,
    DerivedMetrics,
    ModeSplit,
    vmt_reduced,
    trips_from_vmt,
    trips_reduced,
    co2_tonnes_from_vmt,
    co2_tonnes_reduced,
    infer_measure_mode,
    generate_mode_shift_weights,
    estimate_mode_split,
    per_measure_reductions,
    summarize,
)

__version__ = "0.2.1"
__author__ = "David Wasserman"

__all__ = [
    # Context
    "Scale",
    "LocationType",
    "LandUseType",
    "TDMContext",
    # Registry
    "registry",
    "MeasureExclusivityError",
    "MeasureSelectionError",
    # Individual measure functions
    "t1_increase_residential_density",
    "t2_increase_job_density",
    "t3_provide_transit_oriented_development",
    "t4_integrate_affordable_housing",
    "t55_infill_development",
    "t5_implement_voluntary_commute_trip_reduction",
    "t6_implement_mandatory_commute_trip_reduction",
    "t7_implement_commute_trip_reduction_marketing",
    "t8_provide_ridesharing_program",
    "t9_implement_subsidized_transit_program",
    "t10_provide_end_of_trip_bicycle_facilities",
    "t11_provide_employer_sponsored_vanpool",
    "t12_price_workplace_parking",
    "t13_implement_employee_parking_cash_out",
    "t14_provide_ev_charging_infrastructure",
    "t15_limit_residential_parking_supply",
    "t16_unbundle_residential_parking_costs",
    "t17_improve_street_connectivity",
    "t18_provide_pedestrian_network_improvement",
    "t19a_construct_or_improve_bike_facility",
    "t19b_construct_or_improve_bike_boulevard",
    "t20_expand_bikeway_network",
    "t21a_implement_conventional_carshare",
    "t21b_implement_electric_carshare",
    "t22a_implement_pedal_bikeshare",
    "t22b_implement_electric_bikeshare",
    "t22c_implement_scootershare",
    "t22d_transition_conventional_to_electric_bikeshare",
    "t23_provide_community_based_travel_planning",
    "t24_implement_market_price_public_parking",
    "t25_extend_transit_network_coverage_or_hours",
    "t26_increase_transit_service_frequency",
    "t27_implement_transit_supportive_roadway_treatments",
    "t28_provide_bus_rapid_transit",
    "t29_reduce_transit_fares",
    "t46_provide_transit_shelters",
    "t40_establish_school_bus_program",
    "t56_active_modes_transportation_youth",
    "t30_use_cleaner_fuel_vehicles",
    # Subsector orchestrators
    "run_subsector",
    "run_land_use",
    "run_neighborhood_design",
    "run_trip_reduction",
    "run_transit",
    "run_school_programs",
    "run_parking_management",
    "run_clean_vehicles",
    "run_multi_subsector",
    # Constants
    "SUBSECTOR_CAPS",
    "MULTI_SUBSECTOR_CAP",
    # Utilities
    "multiplicative_dampening",
    # Derived metrics
    "DEFAULT_EMISSION_FACTOR_G_PER_MILE",
    "GRAMS_PER_METRIC_TON",
    "NON_AUTO_MODES",
    "MODE_KEYWORDS",
    "DerivedMetrics",
    "ModeSplit",
    "vmt_reduced",
    "trips_from_vmt",
    "trips_reduced",
    "co2_tonnes_from_vmt",
    "co2_tonnes_reduced",
    "infer_measure_mode",
    "generate_mode_shift_weights",
    "estimate_mode_split",
    "per_measure_reductions",
    "summarize",
]
