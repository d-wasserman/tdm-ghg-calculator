# Usage Examples

The `TDMContext` class captures the analysis context (scale, location type, land use) and exposes each CAPCOA strategy as a method. The context validates that a strategy is applicable before running it and raises an error if it is called in an incompatible context (e.g., calling a residential-only measure on a commercial project). Strategy parameters are passed directly to each method call — the context does not store them.

## 1. Residential Density Project (Project/Site)

A developer proposes a high-density urban residential project at 25 du/acre, near transit, with 30% affordable housing.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.RESIDENTIAL,
)

# Call each strategy as a method — parameters go directly to the call
t1 = ctx.t1_increase_residential_density(proposed_residential_density=25.0)
t3 = ctx.t3_provide_transit_oriented_development(
    transit_mode_share=0.037,
    vehicle_mode_share=0.80,
)
t4 = ctx.t4_integrate_affordable_housing(pct_multifamily_units_affordable=0.30)

print(f"T-1 reduction: {t1:.2%}")
print(f"T-3 reduction: {t3:.2%}")
print(f"T-4 reduction: {t4:.2%}")

# Combine at the subsector level (multiplicative dampening, capped at 65%)
land_use = ctx.combine_land_use([t1, t3, t4])
print(f"Combined land use reduction: {land_use:.2%}")
```

## 2. Commercial Job Density Project

An office development with 300 jobs per acre in a suburban area, with end-of-trip bicycle facilities.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.SUBURBAN,
    land_use_type=LandUseType.COMMERCIAL,
)

# T-2 applies to commercial; T-1 would raise an error here
t2 = ctx.t2_increase_job_density(proposed_job_density=300.0)

# T-10 applies to employee commute VMT (any land use)
t10 = ctx.t10_provide_end_of_trip_bicycle_facilities(
    bike_mode_adjustment_factor=4.86,       # Full facilities
    existing_bicycle_trip_length=2.3,
    existing_vehicle_trip_length=10.5,
    existing_bicycle_mode_share_work=0.01,
    existing_vehicle_mode_share_work=0.85,
)

land_use = ctx.combine_land_use([t2])
trip_red = ctx.combine_trip_reduction([t10])
print(f"Land use reduction (project VMT):    {land_use:.2%}")
print(f"Trip reduction (commute VMT):        {trip_red:.2%}")
```

## 3. Infill Development (T-55 Instead of T-1/T-3)

T-55 is **mutually exclusive** with T-1 and T-3. Simply call T-55 and T-4 and combine only those results — no exclusion flags needed since you control which methods you call.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.RESIDENTIAL,
)

t55 = ctx.t55_infill_development(
    proposed_project_distance_to_downtown=3.0,
    conventional_development_distance_to_downtown=13.4,
)
t4 = ctx.t4_integrate_affordable_housing(pct_multifamily_units_affordable=0.50)

# Only T-55 and T-4 — no risk of combining with T-1 or T-3
land_use = ctx.combine_land_use([t55, t4])
print(f"Land use reduction (infill + affordable): {land_use:.2%}")
```

## 4. Community Bikeway and Bikeshare Plan

A community plan to expand the bikeway network and introduce an electric bikeshare program.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PLAN_COMMUNITY,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.MIXED,
)

t20 = ctx.t20_expand_bikeway_network(
    existing_bikeway_miles_in_community=50.0,
    proposed_bikeway_miles_in_community=75.0,
    bike_mode_share=0.02,
    vehicle_mode_share=0.80,
    average_oneway_bicycle_trip_length=2.5,
    average_oneway_vehicle_trip_length=9.7,
)

t22b = ctx.t22b_implement_electric_bikeshare(
    pct_residences_with_access_with_measure=0.40,
)

design = ctx.combine_neighborhood_design([t20, t22b])
print(f"Neighborhood design reduction: {design:.4%}")
```

## 5. Transit Improvements — Standard vs. BRT

Compare standard transit improvements (T-26 + T-27 + T-46) against Bus Rapid Transit (T-28). Since you call strategies explicitly, mutual exclusivity is naturally handled — you simply choose which methods to call.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PLAN_COMMUNITY,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.MIXED,
)

# --- Option A: Standard (T-26 + T-27 + T-46) ---

t26 = ctx.t26_increase_transit_service_frequency(
    pct_increase_in_transit_frequency=1.0,
    level_of_implementation=0.50,
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)
t27 = ctx.t27_implement_transit_supportive_roadway_treatments(
    pct_transit_routes_receiving_treatments=0.30,
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)
t46 = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=20,
    avg_boardings_per_day_at_improved_stops=150.0,
    avg_boardings_per_day_across_agency=50000.0,
    transit_mode_share=0.05,
)

standard = ctx.combine_transit([t26, t27, t46])
print(f"Standard transit reduction: {standard:.2%}")

# --- Option B: BRT (T-28 alone) ---

t28 = ctx.t28_provide_bus_rapid_transit(
    pct_increase_in_transit_frequency=1.0,
    level_of_implementation=0.50,
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)

brt = ctx.combine_transit([t28])
print(f"BRT transit reduction:      {brt:.2%}")
```

## 6. School Transportation Programs

A school implements both a bus program and Safe Routes to School improvements.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.SUBURBAN,
    land_use_type=LandUseType.SCHOOL,
)

t40 = ctx.t40_establish_school_bus_program(
    pct_students_who_begin_riding_bus=0.20,
    pct_students_served_by_bus=0.80,
    light_duty_emission_factor=296.0,
    school_bus_emission_factor=1735.0,
)

t56 = ctx.t56_active_modes_transportation_youth(
    pct_near_students_driven_after_implementation=0.35,
)

school = ctx.combine_school_programs([t40, t56])
print(f"School programs reduction (school VMT): {school:.2%}")
```

## 7. Full Multi-Subsector Analysis

Combine multiple subsectors for a comprehensive community plan. The multi-subsector combiner applies multiplicative dampening with a 70% cap across Land Use + Neighborhood Design + Parking + Transit.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PLAN_COMMUNITY,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.MIXED,
)

# Transit strategies
t26 = ctx.t26_increase_transit_service_frequency(
    pct_increase_in_transit_frequency=1.5,
    level_of_implementation=0.60,
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)
t27 = ctx.t27_implement_transit_supportive_roadway_treatments(
    pct_transit_routes_receiving_treatments=0.40,
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)
t46 = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=30,
    avg_boardings_per_day_at_improved_stops=200.0,
    avg_boardings_per_day_across_agency=60000.0,
    transit_mode_share=0.05,
)

# Neighborhood design strategies
t20 = ctx.t20_expand_bikeway_network(
    existing_bikeway_miles_in_community=45.0,
    proposed_bikeway_miles_in_community=90.0,
    bike_mode_share=0.015,
    vehicle_mode_share=0.80,
    average_oneway_bicycle_trip_length=2.5,
    average_oneway_vehicle_trip_length=9.7,
)
t22b = ctx.t22b_implement_electric_bikeshare(
    pct_residences_with_access_with_measure=0.50,
)

# Combine at subsector level first
transit_result = ctx.combine_transit([t26, t27, t46])
design_result = ctx.combine_neighborhood_design([t20, t22b])
print(f"Transit subsector:              {transit_result:.2%}")
print(f"Neighborhood design subsector:  {design_result:.4%}")

# Then combine across subsectors (capped at 70%)
total = ctx.combine_multi_subsector(
    land_use=0.0,           # No land use measures in this example
    neighborhood_design=design_result,
    parking_management=0.0,
    transit=transit_result,
)
print(f"Multi-subsector combined:       {total:.2%}")
```

## 8. Context Validation

The context validates applicability before running a strategy. Calling a strategy in the wrong context raises an error:

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.COMMERCIAL,
)

# T-1 is residential-only — this raises an error
try:
    ctx.t1_increase_residential_density(proposed_residential_density=25.0)
except ValueError as e:
    print(f"Blocked: {e}")
    # "T-1 (Increase Residential Density) is not applicable to COMMERCIAL land use"

# T-26 is Plan/Community scale — calling it on a Project/Site context raises an error
try:
    ctx.t26_increase_transit_service_frequency(
        pct_increase_in_transit_frequency=1.0,
        level_of_implementation=0.50,
        transit_mode_share=0.05,
        vehicle_mode_share=0.80,
    )
except ValueError as e:
    print(f"Blocked: {e}")
    # "T-26 (Increase Transit Service Frequency) requires PLAN_COMMUNITY scale"
```

## 9. Transit Shelters with Real-Time Information

T-46 supports an optional real-time arrival information (RTI) variant:

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PLAN_COMMUNITY,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.MIXED,
)

# Shelters only
shelters_only = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=15,
    avg_boardings_per_day_at_improved_stops=200.0,
    avg_boardings_per_day_across_agency=40000.0,
    transit_mode_share=0.04,
    include_real_time_information=False,
)
print(f"Shelters only:  {shelters_only:.4%}")

# Shelters + real-time arrival info
shelters_rti = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=15,
    avg_boardings_per_day_at_improved_stops=200.0,
    avg_boardings_per_day_across_agency=40000.0,
    transit_mode_share=0.04,
    include_real_time_information=True,
)
print(f"Shelters + RTI: {shelters_rti:.4%}")
```

## 10. Inspecting Available Strategies

List all registered measures and check which are applicable to a given context:

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType, registry

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.SUBURBAN,
    land_use_type=LandUseType.RESIDENTIAL,
)

# List all strategies applicable to this context
applicable = ctx.applicable_measures()
print(f"{len(applicable)} measures applicable to suburban residential (project/site):")
for meta in applicable:
    print(f"  {meta.measure_id}: {meta.name} (max {meta.measure_max:.1%})")

# Or browse the full registry
for measure_id, meta in registry.measures.items():
    print(
        f"{meta.measure_id:6s} | {meta.name:50s} | "
        f"subsector={meta.subsector:20s} | max={meta.measure_max:.1%}"
    )
```
