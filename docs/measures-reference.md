# Measures Reference

All 16 CAPCOA 2024 TDM measures implemented in `tdm_ghg`. Each measure returns a negative decimal fraction representing GHG reduction (e.g., `-0.14` = 14% reduction).

All examples below assume a `TDMContext` with the appropriate scale, location, and land use has been created. The context validates applicability before running each strategy.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType
```

---

## Land Use Subsector

**Scale:** Project/Site | **Subsector cap:** 65%

### T-1: Increase Residential Density

Accounts for VMT reduction from higher dwelling-unit density compared to the U.S. average.

**Applicability:** Urban, Suburban | Residential only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)

result = ctx.t1_increase_residential_density(
    proposed_residential_density=20.0,        # du/acre (required)
    typical_residential_density=9.1,          # du/acre — Ewing et al. 2007 U.S. average
    elasticity_vmt_residential_density=-0.22, # Stevens 2016
)
```

**Formula:** `A = ((B - C) / C) * D`

| Parameter                          | Default | Source              |
|------------------------------------|---------|---------------------|
| `proposed_residential_density`     | —       | Project-specific    |
| `typical_residential_density`      | 9.1     | Ewing et al. 2007   |
| `elasticity_vmt_residential_density` | -0.22 | Stevens 2016        |

**Cap:** -0.30 (-30%) | **Mutually exclusive with:** T-55

---

### T-2: Increase Job Density

Accounts for VMT reduction from higher job density compared to the U.S. average.

**Applicability:** Urban, Suburban | Commercial only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.SUBURBAN, LandUseType.COMMERCIAL)

result = ctx.t2_increase_job_density(
    proposed_job_density=300.0,          # jobs/acre (required)
    typical_job_density=145,             # ITE 2020
    elasticity_vmt_job_density=-0.07,    # Stevens 2016
)
```

**Formula:** `A = ((B - C) / C) * D`

| Parameter                    | Default | Source         |
|------------------------------|---------|----------------|
| `proposed_job_density`       | —       | Project-specific|
| `typical_job_density`        | 145     | ITE 2020       |
| `elasticity_vmt_job_density` | -0.07   | Stevens 2016   |

**Cap:** -0.30 (-30%)

---

### T-3: Provide Transit-Oriented Development

Reduces VMT by locating a project within 0.5-mile walk of a high-frequency transit station.

**Applicability:** Urban, Suburban, Rural (if adjacent to commuter rail)

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)

result = ctx.t3_provide_transit_oriented_development(
    transit_mode_share=0.037,       # FHWA 2017a NHTS by CBSA (required)
    vehicle_mode_share=0.80,        # FHWA 2017b NHTS by CBSA (required)
    tod_transit_ratio=4.9,          # Lund et al. 2004
    tod_transit_share_cap=0.27,     # Lund et al. 2004
)
```

**Formula:** `A = -(min(B * C, cap)) / D`

| Parameter              | Default | Source            |
|------------------------|---------|-------------------|
| `transit_mode_share`   | —       | FHWA 2017a NHTS   |
| `vehicle_mode_share`   | —       | FHWA 2017b NHTS   |
| `tod_transit_ratio`    | 4.9     | Lund et al. 2004  |
| `tod_transit_share_cap`| 0.27    | Lund et al. 2004  |

**Cap:** -0.31 (-31%) | **Mutually exclusive with:** T-55

---

### T-4: Integrate Affordable and Below Market Rate Housing

VMT reductions for multifamily projects with deed-restricted affordable units (at or below 80% AMI).

**Applicability:** Urban, Suburban | Residential only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)

result = ctx.t4_integrate_affordable_housing(
    pct_multifamily_units_affordable=0.50,      # 50% affordable (required)
    vmt_reduction_per_qualified_unit=-0.286,     # ITE 2021
)
```

**Formula:** `A = B * C`

| Parameter                          | Default | Source     |
|------------------------------------|---------|------------|
| `pct_multifamily_units_affordable` | —       | Project-specific |
| `vmt_reduction_per_qualified_unit` | -0.286  | ITE 2021   |

**Cap:** -0.286 (-28.6%)

---

### T-55: Infill Development

VMT reductions from housing closer to downtown than conventional development. Requires rezoning to high-density residential or mixed-use.

**Applicability:** Urban, Suburban | Residential only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)

result = ctx.t55_infill_development(
    proposed_project_distance_to_downtown=3.0,              # miles (required)
    conventional_development_distance_to_downtown=13.4,     # miles (required)
    elasticity_vmt_distance_to_downtown=-0.22,              # Ewing & Cervero 2010
)
```

**Formula:** `A = ((C - B) / C) * D`

| Parameter                                      | Default | Source                     |
|------------------------------------------------|---------|----------------------------|
| `proposed_project_distance_to_downtown`        | —       | Project-specific           |
| `conventional_development_distance_to_downtown`| —       | Metro area average         |
| `elasticity_vmt_distance_to_downtown`          | -0.22   | Ewing & Cervero 2010; Stevens 2016 |

**Cap:** -0.30 (-30%) | **Mutually exclusive with:** T-1, T-3

---

## Trip Reduction Programs Subsector

**Scale:** Project/Site (Employee Commute) | **Subsector cap:** 45% commute VMT

### T-10: Provide End-of-Trip Bicycle Facilities

Encourages bicycle commuting by providing showers, lockers, and bike parking for employees.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL)

result = ctx.t10_provide_end_of_trip_bicycle_facilities(
    bike_mode_adjustment_factor=4.86,          # Parking + showers + lockers (required)
    existing_bicycle_trip_length=2.3,          # miles, NHTS by CBSA (required)
    existing_vehicle_trip_length=10.5,         # miles, NHTS by CBSA (required)
    existing_bicycle_mode_share_work=0.01,     # NHTS by CBSA (required)
    existing_vehicle_mode_share_work=0.85,     # NHTS by CBSA (required)
)
```

**Formula:** `A = C * E * (1 - B) / (D * F)`

| Parameter                         | Default | Source              |
|-----------------------------------|---------|---------------------|
| `bike_mode_adjustment_factor`     | —       | Buehler 2012 (4.86 full, 1.78 parking only) |
| `existing_bicycle_trip_length`    | —       | FHWA 2017a NHTS     |
| `existing_vehicle_trip_length`    | —       | FHWA 2017a NHTS     |
| `existing_bicycle_mode_share_work`| —       | FHWA 2017b NHTS     |
| `existing_vehicle_mode_share_work`| —       | FHWA 2017b NHTS     |

**Cap:** -0.044 (-4.4%)

---

## Neighborhood Design Subsector

**Scale:** Plan/Community | **Subsector cap:** 10%

### T-20: Expand Bikeway Network

Increases community bikeway mileage (lanes, paths, routes, cycle tracks) to encourage mode shift from vehicles to bicycles.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t20_expand_bikeway_network(
    existing_bikeway_miles_in_community=50.0,          # (required)
    proposed_bikeway_miles_in_community=75.0,          # (required)
    bike_mode_share=0.02,                              # (required)
    vehicle_mode_share=0.80,                           # (required)
    average_oneway_bicycle_trip_length=2.5,            # miles (required)
    average_oneway_vehicle_trip_length=9.7,            # miles (required)
    elasticity_of_bike_commuters_per_pop=0.25,         # Pucher & Buehler 2011
)
```

**Formula:** `A = -1 * (((B - C) / C) * D * E * F) / (G * H)`

| Parameter                              | Default | Source                  |
|----------------------------------------|---------|-------------------------|
| `existing_bikeway_miles_in_community`  | —       | Project-specific        |
| `proposed_bikeway_miles_in_community`  | —       | Project-specific        |
| `bike_mode_share`                      | —       | NHTS by CBSA            |
| `vehicle_mode_share`                   | —       | NHTS by CBSA            |
| `average_oneway_bicycle_trip_length`   | —       | NHTS by CBSA            |
| `average_oneway_vehicle_trip_length`   | —       | NHTS by CBSA            |
| `elasticity_of_bike_commuters_per_pop` | 0.25    | Pucher & Buehler 2011   |

**Cap:** -0.005 (-0.5%)

---

### T-22-A: Implement Pedal (Non-Electric) Bikeshare Program

On-demand pedal bikeshare providing short-term bike rentals to shift trips from vehicles.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t22a_implement_pedal_bikeshare(
    pct_residences_with_access_with_measure=0.30,       # (required)
    pct_residences_with_access_without_measure=0.0,     # default
    daily_bikeshare_trips_per_person=0.021,              # MTC 2017
    vehicle_to_bikeshare_substitution_rate=0.196,        # McQueen et al. 2020
    bikeshare_avg_oneway_trip_length=1.4,                # Lazarus et al. 2019
    daily_vehicle_trips_per_person=2.7,                  # FHWA 2018 NHTS
    regional_avg_oneway_vehicle_trip_length=9.72,        # FHWA 2017 NHTS
)
```

**Formula:** `A = -1 * ((C - B) * D * E * F) / (G * H)`

**Cap:** -0.0002 (-0.02%)

---

### T-22-B: Implement Electric Bikeshare Program

Pedal-assist electric bikeshare with higher substitution rate and longer trip lengths than traditional bikeshare.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t22b_implement_electric_bikeshare(
    pct_residences_with_access_with_measure=0.40,       # (required)
    pct_residences_with_access_without_measure=0.0,     # default
    daily_ebikeshare_trips_per_person=0.021,             # MTC 2017
    vehicle_to_ebikeshare_substitution_rate=0.35,        # Fitch et al. 2021
    ebikeshare_avg_oneway_trip_length=2.1,               # Fitch et al. 2021
    daily_vehicle_trips_per_person=2.7,                  # FHWA 2018 NHTS
    regional_avg_oneway_vehicle_trip_length=9.72,        # FHWA 2017 NHTS
)
```

**Formula:** `A = -1 * ((C - B) * D * E * F) / (G * H)`

**Cap:** -0.0006 (-0.06%)

---

### T-22-D: Transition Conventional to Electric Bikeshare

Accounts for VMT reduction from transitioning an existing traditional bikeshare fleet to electric bikes. Does not cover coverage expansion (use T-22-A/B for that).

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t22d_transition_conventional_to_electric_bikeshare(
    pct_residences_with_traditional_bikeshare_access=0.25,  # (required)
    pct_bikes_transitioned_to_electric=0.50,                # (required)
    daily_bikeshare_trips_per_person=0.021,                 # MTC 2021
    vehicle_to_ebikeshare_substitution_rate=0.35,           # Fitch et al. 2021
    ebikeshare_avg_oneway_trip_length=2.1,                  # Fitch et al. 2021
    vehicle_to_conventional_bikeshare_substitution_rate=0.196, # McQueen et al. 2020
    conventional_bikeshare_avg_oneway_trip_length=1.4,      # Lazarus et al. 2019
    daily_vehicle_trips_per_person=1.7,                     # FHWA 2023
    regional_avg_oneway_vehicle_trip_length=9.72,           # FHWA 2017 NHTS
)
```

**Formula:** `A = -(B * C * D * ((E * F) - (G * H))) / (I * J)`

**Cap:** -0.00059 (-0.059%)

---

## Transit Subsector

**Scale:** Plan/Community | **Subsector cap:** 15%

### T-26: Increase Transit Service Frequency

Improves transit frequency to encourage mode shift from vehicles to transit.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t26_increase_transit_service_frequency(
    pct_increase_in_transit_frequency=1.0,    # 100% = double frequency (required)
    level_of_implementation=0.50,             # 50% of routes (required)
    transit_mode_share=0.05,                  # (required)
    vehicle_mode_share=0.80,                  # (required)
    elasticity_ridership_frequency=0.5,       # Handy et al. 2013
    statewide_mode_shift_factor=0.578,        # FHWA 2017b
)
```

**Formula:** `A = -C * (B * E * D * G) / F`

| Parameter                          | Default | Source            |
|------------------------------------|---------|-------------------|
| `pct_increase_in_transit_frequency`| —       | Project-specific (capped at 3.0) |
| `level_of_implementation`          | —       | Project-specific  |
| `transit_mode_share`               | —       | FHWA 2017a NHTS   |
| `vehicle_mode_share`               | —       | FHWA 2017a NHTS   |
| `elasticity_ridership_frequency`   | 0.5     | Handy et al. 2013 |
| `statewide_mode_shift_factor`      | 0.578   | FHWA 2017b        |

**Cap:** -0.113 (-11.3%) | **Mutually exclusive with:** T-28

---

### T-27: Implement Transit-Supportive Roadway Treatments

Transit signal priority, bus-only signal phases, queue jumps, curb extensions, or dedicated bus lanes.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t27_implement_transit_supportive_roadway_treatments(
    pct_transit_routes_receiving_treatments=0.30,   # (required)
    transit_mode_share=0.05,                        # (required)
    vehicle_mode_share=0.80,                        # (required)
    pct_change_in_transit_travel_time=-0.10,         # TRB 2007 (capped at -0.20)
    elasticity_ridership_travel_time=-0.4,           # TRB 2007
    statewide_mode_shift_factor=0.578,               # FHWA 2017b
)
```

**Formula:** `A = -1 * (B * C * D * E * G) / F`

**Cap:** -0.006 (-0.6%) | **Mutually exclusive with:** T-28

---

### T-28: Provide Bus Rapid Transit

Converts bus routes to full BRT with exclusive right-of-way, increased frequency, advanced vehicles, enhanced stations, and efficient fare payment. Combines frequency, travel time, and BRT branding effects.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

result = ctx.t28_provide_bus_rapid_transit(
    pct_increase_in_transit_frequency=1.5,          # (required, capped at 3.0)
    level_of_implementation=0.60,                   # (required)
    transit_mode_share=0.05,                        # (required)
    vehicle_mode_share=0.80,                        # (required)
    statewide_mode_shift_factor=0.578,              # FHWA 2017b
    pct_ridership_increase_brt_bonus=0.25,          # TRB 2007
    pct_change_in_transit_travel_time=-0.10,         # TRB 2007 (capped at -0.20)
    elasticity_ridership_frequency=0.5,              # Handy et al. 2013
    elasticity_ridership_travel_time=-0.4,           # TRB 2007
)
```

**Formula:** `A = -C * (D * F * ((B * I) + (H * J) + G)) / E`

**Cap:** -0.138 (-13.8%) | **Mutually exclusive with:** T-26, T-27, T-46

---

### T-46: Provide Transit Shelters

Bus shelters with optional real-time arrival information to reduce perceived wait times.

**Applicability:** Urban, Suburban

```python
ctx = TDMContext(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)

# Shelters only
result = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=15,                          # (required)
    avg_boardings_per_day_at_improved_stops=200.0,           # (required)
    avg_boardings_per_day_across_agency=40000.0,             # (required)
    transit_mode_share=0.04,                                 # (required)
    include_real_time_information=False,                      # default: shelters only
)

# Shelters + real-time arrival information (greater ridership gains)
result_rti = ctx.t46_provide_transit_shelters(
    num_stops_with_new_shelters=15,
    avg_boardings_per_day_at_improved_stops=200.0,
    avg_boardings_per_day_across_agency=40000.0,
    transit_mode_share=0.04,
    include_real_time_information=True,
)
```

**Formulas:**
- Shelters only: `A = B * (C/D) * E * (F/G) * (H - I_shelters) * J`
- Shelters + RTI: `A = B * (C/D) * E * (F/G) * (H - I_rti) * J`

| Parameter                                        | Default | Source              |
|--------------------------------------------------|---------|---------------------|
| `num_stops_with_new_shelters`                    | —       | Project-specific    |
| `avg_boardings_per_day_at_improved_stops`        | —       | Transit agency data |
| `avg_boardings_per_day_across_agency`            | —       | Transit agency data |
| `transit_mode_share`                             | —       | FHWA 2017 NHTS     |
| `include_real_time_information`                  | False   | Project choice      |
| `pct_transit_users_who_would_otherwise_drive`    | 0.833   | FHWA 2017 NHTS     |
| `avg_auto_occupancy`                             | 1.45    | FHWA 2023 NHTS     |
| `pct_travel_time_waiting_existing`               | 0.249   | FHWA 2023 NHTS     |
| `pct_perceived_waiting_with_shelters`            | 0.203   | Fan et al. 2016    |
| `pct_perceived_waiting_with_shelters_and_rti`    | 0.158   | Watkins 2011       |
| `wait_time_elasticity`                           | -0.54   | Taylor et al. 2009 |

**Cap:** -0.0032 (-0.32%) | **Mutually exclusive with:** T-28

---

## School Programs Subsector

**Scale:** Project/Site (School Commute) | **Subsector cap:** 72% school VMT

### T-40: Establish a School Bus Program

Establishes or expands school bus service, replacing private vehicle trips with shared bus trips.

**Applicability:** Urban, Suburban, Rural | School only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.SUBURBAN, LandUseType.SCHOOL)

result = ctx.t40_establish_school_bus_program(
    pct_students_who_begin_riding_bus=0.20,         # (required)
    pct_students_served_by_bus=0.80,                # (required)
    light_duty_emission_factor=296.0,               # g CO2e/mile (required)
    school_bus_emission_factor=1735.0,              # g CO2e/mile (required)
    pct_new_riders_who_previously_drove=0.79,       # FHWA 2023 NHTS
    avg_student_occupancy_cars=1.58,                # FHWA 2023 NHTS Pacific
    avg_student_occupancy_buses=14.9,               # Wang 2019
    bus_tour_to_driving_distance_ratio=3.42,        # FHWA 2023 + Duran 2013
)
```

**Formula:** `A = B * C * D * ((H/E) - (G*I/F)) / (H/E)`

**Cap:** -0.57 (-57%)

---

### T-56: Active Modes of Transportation for Youth

Infrastructure for walking and biking to school (Safe Routes to School), targeting students within 2 miles.

**Applicability:** Urban, Suburban | School only

```python
ctx = TDMContext(Scale.PROJECT_SITE, LocationType.SUBURBAN, LandUseType.SCHOOL)

result = ctx.t56_active_modes_transportation_youth(
    pct_near_students_driven_after_implementation=0.35,     # (required)
    pct_students_within_2_miles=0.62,                       # SR2S Partnership 2013
    pct_near_students_driven_before_implementation=0.51,    # SR2S Partnership 2013
    pct_far_students_driven=0.66,                           # FHWA 2023
    avg_driving_distance_near_students=2.0,                 # miles
    avg_driving_distance_far_students=8.66,                 # FHWA 2023 NHTS
)
```

**Formula:** `A = C * F * (B - D) / (G * E * (1 - C) + C * D * F)`

**Cap:** -0.222 (-22.2%)
