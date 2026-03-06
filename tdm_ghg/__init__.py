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
    t10_provide_end_of_trip_bicycle_facilities

Neighborhood Design (Plan/Community, T-18 through T-22-D): cap 10%
    t20_expand_bikeway_network
    t22a_implement_pedal_bikeshare
    t22b_implement_electric_bikeshare
    t22d_transition_conventional_to_electric_bikeshare

Transit (Plan/Community, T-25 through T-29, T-46): cap 15%
    t26_increase_transit_service_frequency    [excl. T-28 when BRT]
    t27_implement_transit_supportive_roadway_treatments  [excl. T-28]
    t28_provide_bus_rapid_transit             [excl. T-26/T-27/T-46]
    t46_provide_transit_shelters              [excl. T-28 when BRT]

School Programs (Project/Site, T-40 & T-56): cap 72% school VMT
    t40_establish_school_bus_program
    t56_active_modes_transportation_youth

Multi-Subsector (Land Use + Neighborhood Design + Parking + Transit): cap 70%

Utilities
---------
    multiplicative_dampening
    registry               (MeasureRegistry — inspect all registered measures)
"""

# Context and registry — import order matters: context first, then registry,
# then mitigations (which registers functions at import time).
from tdm_ghg.context import LandUseType, LocationType, Scale, TDMContext
from tdm_ghg.registry import registry

# Importing mitigations registers all @register_measure functions.
from tdm_ghg.mitigations import (
    t1_increase_residential_density,
    t2_increase_job_density,
    t3_provide_transit_oriented_development,
    t4_integrate_affordable_housing,
    t55_infill_development,
    t10_provide_end_of_trip_bicycle_facilities,
    t20_expand_bikeway_network,
    t22a_implement_pedal_bikeshare,
    t22b_implement_electric_bikeshare,
    t22d_transition_conventional_to_electric_bikeshare,
    t26_increase_transit_service_frequency,
    t27_implement_transit_supportive_roadway_treatments,
    t28_provide_bus_rapid_transit,
    t46_provide_transit_shelters,
    t40_establish_school_bus_program,
    t56_active_modes_transportation_youth,
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
    run_multi_subsector,
)

from tdm_ghg.utils import multiplicative_dampening

__version__ = "0.1.0"
__author__ = "David Wasserman"

__all__ = [
    # Context
    "Scale",
    "LocationType",
    "LandUseType",
    "TDMContext",
    # Registry
    "registry",
    # Individual measure functions
    "t1_increase_residential_density",
    "t2_increase_job_density",
    "t3_provide_transit_oriented_development",
    "t4_integrate_affordable_housing",
    "t55_infill_development",
    "t10_provide_end_of_trip_bicycle_facilities",
    "t20_expand_bikeway_network",
    "t22a_implement_pedal_bikeshare",
    "t22b_implement_electric_bikeshare",
    "t22d_transition_conventional_to_electric_bikeshare",
    "t26_increase_transit_service_frequency",
    "t27_implement_transit_supportive_roadway_treatments",
    "t28_provide_bus_rapid_transit",
    "t46_provide_transit_shelters",
    "t40_establish_school_bus_program",
    "t56_active_modes_transportation_youth",
    # Subsector orchestrators
    "run_subsector",
    "run_land_use",
    "run_neighborhood_design",
    "run_trip_reduction",
    "run_transit",
    "run_school_programs",
    "run_parking_management",
    "run_multi_subsector",
    # Constants
    "SUBSECTOR_CAPS",
    "MULTI_SUBSECTOR_CAP",
    # Utilities
    "multiplicative_dampening",
]
