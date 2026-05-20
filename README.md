# tdm-ghg

A Python library for calculating GHG emission reductions from Transportation Demand Management (TDM) measures, based on the CAPCOA 2024 [*Handbook for Analyzing GHG Emission Reductions, Assessing Climate Vulnerabilities, and Advancing Health and Equity*](https://www.airquality.org/ClimateChange/Documents/Handbook%20Public%20Draft/CAPCOA%20GHG%20Handbook%20-%20Public%20Draft.pdf) (transportation section).

Given a project's characteristics (density, location type, land use), `tdm-ghg` returns the expected percent reduction in vehicle miles traveled (VMT) and associated GHG emissions for each applicable CAPCOA mitigation measure and combines them using the handbook's multiplicative dampening rules and subsector caps.

## Installation

```bash
pip install tdm-ghg
```

Or install from source for development:

```bash
git clone https://github.com/your-org/tdm-ghg-calculator.git
cd tdm-ghg-calculator
pip install -e ".[dev]"
```

## Quick Start

### Context-aware usage (recommended)

Build a `TDMContext` describing your project, then let the subsector orchestrators automatically select applicable measures and combine results:

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType
from tdm_ghg import (
    run_land_use, run_trip_reduction, run_parking_management,
    run_neighborhood_design, run_transit, run_school_programs,
    run_clean_vehicles, run_multi_subsector,
)

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

# Run a single subsector
land_use_reduction = run_land_use(ctx)          # e.g. -0.24 (24% reduction)

# Run all combinable subsectors (Land Use + Neighborhood Design + Parking + Transit)
total = run_multi_subsector(ctx)                # capped at -0.70
```

### Direct function usage

Every measure function is importable for standalone use:

```python
from tdm_ghg import t1_increase_residential_density

result = t1_increase_residential_density(proposed_residential_density=20.0)
# -0.2637... (26.4% reduction in project VMT)
```

### Inspecting the registry

All registered measures and their metadata are accessible at runtime:

```python
from tdm_ghg import registry

for measure_id, meta in registry.measures.items():
    print(f"{measure_id}: {meta.name} (max {meta.measure_max:.0%})")
```

## Return Value Convention

All mitigation functions return a **decimal fraction** where **negative values represent reductions**:

| Return value | Meaning |
|---|---|
| `-0.14` | 14% reduction in VMT/GHG |
| `-0.30` | 30% reduction (measure cap hit) |
| `0.0` | No effect |

## Implemented Measures

### Land Use (Project/Site) -- cap 65%

| ID | Function | Applies to |
|---|---|---|
| T-1 | `t1_increase_residential_density` | Residential |
| T-2 | `t2_increase_job_density` | Commercial |
| T-3 | `t3_provide_transit_oriented_development` | All |
| T-4 | `t4_integrate_affordable_housing` | Residential |
| T-55 | `t55_infill_development` | Residential (excl. T-1, T-3) |

### Trip Reduction Programs (Project/Site) -- cap 45% commute VMT

| ID | Function | Notes |
|---|---|---|
| T-5 | `t5_implement_voluntary_commute_trip_reduction` | Excl. T-6, T-7 through T-11 |
| T-6 | `t6_implement_mandatory_commute_trip_reduction` | Excl. T-5, T-7 through T-11 |
| T-7 | `t7_implement_commute_trip_reduction_marketing` | Excl. T-5, T-6 |
| T-8 | `t8_provide_ridesharing_program` | Excl. T-5, T-6 |
| T-9 | `t9_implement_subsidized_transit_program` | Excl. T-5, T-6 |
| T-10 | `t10_provide_end_of_trip_bicycle_facilities` | Excl. T-5, T-6 |
| T-11 | `t11_provide_employer_sponsored_vanpool` | Excl. T-5, T-6 |
| T-12 | `t12_price_workplace_parking` | Excl. T-13 |
| T-13 | `t13_implement_employee_parking_cash_out` | Excl. T-12 |

### Parking Management (Project/Site) -- cap 35%

| ID | Function | Notes |
|---|---|---|
| T-14 | `t14_provide_ev_charging_infrastructure` | |
| T-15 | `t15_limit_residential_parking_supply` | Residential only |
| T-16 | `t16_unbundle_residential_parking_costs` | Residential only |

### Land Use (Plan/Community) -- cap 30%

| ID | Function | Notes |
|---|---|---|
| T-17 | `t17_improve_street_connectivity` | |

### Neighborhood Design (Plan/Community) -- cap 10%

| ID | Function | Notes |
|---|---|---|
| T-18 | `t18_provide_pedestrian_network_improvement` | |
| T-19-A | `t19a_construct_or_improve_bike_facility` | Class I, II, or IV bike facility |
| T-19-B | `t19b_construct_or_improve_bike_boulevard` | Class III bike boulevard |
| T-20 | `t20_expand_bikeway_network` | |
| T-21-A | `t21a_implement_conventional_carshare` | |
| T-21-B | `t21b_implement_electric_carshare` | |
| T-22-A | `t22a_implement_pedal_bikeshare` | |
| T-22-B | `t22b_implement_electric_bikeshare` | |
| T-22-C | `t22c_implement_scootershare` | |
| T-22-D | `t22d_transition_conventional_to_electric_bikeshare` | |

### Trip Reduction Programs (Plan/Community) -- cap 2.3% commute VMT

| ID | Function | Notes |
|---|---|---|
| T-23 | `t23_provide_community_based_travel_planning` | Residential only |

### Parking Management (Plan/Community) -- cap 30%

| ID | Function | Notes |
|---|---|---|
| T-24 | `t24_implement_market_price_public_parking` | |

### Transit (Plan/Community) -- cap 15%

| ID | Function | Notes |
|---|---|---|
| T-25 | `t25_extend_transit_network_coverage_or_hours` | |
| T-26 | `t26_increase_transit_service_frequency` | Excl. T-28 when BRT |
| T-27 | `t27_implement_transit_supportive_roadway_treatments` | Excl. T-28 |
| T-28 | `t28_provide_bus_rapid_transit` | Excl. T-26, T-27, T-46 |
| T-29 | `t29_reduce_transit_fares` | |
| T-46 | `t46_provide_transit_shelters` | Excl. T-28 when BRT |

### Clean Vehicles and Fuels (Plan/Community) -- cap 100%

| ID | Function | Notes |
|---|---|---|
| T-30 | `t30_use_cleaner_fuel_vehicles` | BEV, PHEV, or well-to-wheels (WTW) modes |

### School Programs (Project/Site) -- cap 72% school VMT

| ID | Function | Notes |
|---|---|---|
| T-40 | `t40_establish_school_bus_program` | |
| T-56 | `t56_active_modes_transportation_youth` | |

## Combining Measures

Within a subsector, individual reductions are combined using **multiplicative dampening** with a subsector-specific cap:

```
combined = min(cap, 1 - (1 - r1)(1 - r2)...(1 - rn))
```

This prevents double-counting overlapping reductions and ensures results stay within documented CAPCOA limits.

```python
from tdm_ghg import multiplicative_dampening

combined = multiplicative_dampening([-0.10, -0.08, -0.05], max_reduction_percentage=-0.15)
# -0.15 (capped at 15%)
```

## Key Concepts

- **Scale**: `PROJECT_SITE` or `PLAN_COMMUNITY`. Measures from different scales must never be combined.
- **LocationType**: `URBAN`, `SUBURBAN`, or `RURAL` -- based on census-tract development level (Salon 2014 neighborhood typology).
- **LandUseType**: `RESIDENTIAL`, `COMMERCIAL`, `MIXED`, or `SCHOOL` -- filters measures to applicable land uses.
- **Mutual exclusivity**: Some measures cannot be combined within a subsector:
  - **Trip Reduction**: T-5 (voluntary) and T-6 (mandatory) each exclude T-7 through T-11; T-12 and T-13 are mutually exclusive.
  - **Transit**: T-28 (BRT) excludes T-26, T-27, and T-46. The `run_transit(use_brt=True)` orchestrator handles this automatically.

## Testing

```bash
pytest
pytest --cov=tdm_ghg
```

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
