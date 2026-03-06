# Name: mitigations.py
# Purpose: CAPCOA 2024 TDM GHG reduction measure functions, registered with
#          context metadata via @register_measure.
# Author: David Wasserman
# Copyright 2026 David J. Wasserman
# License: Apache 2.0

# All functions return a decimal fraction where negative values represent
# GHG reductions (e.g., -0.14 = 14% reduction). Positive values indicate
# an increase. Each function enforces its individual measure cap internally.

from tdm_ghg.context import LandUseType, LocationType, Scale
from tdm_ghg.registry import register_measure

# Shorthand aliases used in decorator arguments only.
_U = LocationType.URBAN
_S = LocationType.SUBURBAN
_R = LocationType.RURAL
_PS = Scale.PROJECT_SITE
_PC = Scale.PLAN_COMMUNITY
_RES = LandUseType.RESIDENTIAL
_COM = LandUseType.COMMERCIAL
_SCH = LandUseType.SCHOOL


# ==============================================================================
# LAND USE SUBSECTOR (Project/Site)
# Measures T-1, T-2, T-3, T-4, T-55
# Subsector cap: 65%
# ==============================================================================

@register_measure(
    measure_id="T-1",
    name="Increase Residential Density",
    subsector="land_use",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.30,
    land_use_types={_RES},
    # T-2 mutual exclusivity is handled naturally by land_use_type context.
    # T-55 also applies to residential — exclude one when using the other.
    mutually_exclusive_with={"T-55"},
)
def t1_increase_residential_density(
        proposed_residential_density,
        typical_residential_density=9.1,
        elasticity_vmt_residential_density=-0.22):
    """Measure T-1: Increase Residential Density.
    Accounts for the VMT reduction achieved by a project designed with a higher
    density of dwelling units compared to the average residential density in the U.S.
    Applies to project/site VMT in the study area.

    Formula: A = ((B - C) / C) * D

    Parameters
    ----------
    proposed_residential_density : float
        Residential density of project development [du/acre].
    typical_residential_density : float, optional
        Residential density of typical development [du/acre]. Default is 9.1
        (Ewing et al. 2007 blended U.S. average forecast for 2025).
    elasticity_vmt_residential_density : float, optional
        Elasticity of VMT with respect to residential density. Default is -0.22
        (Stevens 2016 meta-regression; 0.22% decrease in VMT per 1% density increase).

    Returns
    -------
    float
        Percent reduction in GHG emissions from project VMT (as a decimal).
        Capped at -0.30 (-30%). Negative values indicate reductions.
    """
    a = ((proposed_residential_density - typical_residential_density)
         / typical_residential_density) * elasticity_vmt_residential_density
    return max(a, -0.30)


@register_measure(
    measure_id="T-2",
    name="Increase Job Density",
    subsector="land_use",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.30,
    land_use_types={_COM},
)
def t2_increase_job_density(
        proposed_job_density,
        typical_job_density=145,
        elasticity_vmt_job_density=-0.07):
    """Measure T-2: Increase Job Density.
    Accounts for the VMT reduction achieved by a project designed with a higher
    density of jobs compared to the average job density in the U.S.
    Applies to project/site VMT in the study area.

    Formula: A = ((B - C) / C) * D

    Parameters
    ----------
    proposed_job_density : float
        Job density of project development [jobs/acre].
    typical_job_density : float, optional
        Job density of typical development [jobs/acre]. Default is 145
        (ITE 2020).
    elasticity_vmt_job_density : float, optional
        Elasticity of VMT with respect to job density. Default is -0.07
        (Stevens 2016).

    Returns
    -------
    float
        Percent reduction in GHG emissions from project VMT (as a decimal).
        Capped at -0.30 (-30%). Negative values indicate reductions.
    """
    a = ((proposed_job_density - typical_job_density)
         / typical_job_density) * elasticity_vmt_job_density
    return max(a, -0.30)


@register_measure(
    measure_id="T-3",
    name="Provide Transit-Oriented Development",
    subsector="land_use",
    scale=_PS,
    # Rural applies only if adjacent to commuter rail — include and document.
    location_types={_U, _S, _R},
    measure_max=0.31,
    mutually_exclusive_with={"T-55"},
)
def t3_provide_transit_oriented_development(
        transit_mode_share,
        vehicle_mode_share,
        tod_transit_ratio=4.9,
        tod_transit_share_cap=0.27):
    """Measure T-3: Provide Transit-Oriented Development.
    Reduces project VMT by locating a project in a compact, walkable area with
    easy access to high-quality public transit (within 0.5-mile walk of a high
    frequency transit station). Applies to project/site VMT in the study area.

    Rural context only applies if adjacent to a commuter rail station with
    convenient service to a major employment center.

    Formula: A = -(min(B * C, cap)) / D

    Parameters
    ----------
    transit_mode_share : float
        Transit mode share in the surrounding city (as a decimal, e.g., 0.037
        for 3.7%). From FHWA 2017a NHTS Table T-3.1 by CBSA.
    vehicle_mode_share : float
        Auto mode share in the surrounding city (as a decimal). From FHWA
        2017b NHTS Table T-3.1 by CBSA.
    tod_transit_ratio : float, optional
        Ratio of transit mode share for TOD area vs. surrounding city. Default
        is 4.9 (Lund et al. 2004 California TOD study).
    tod_transit_share_cap : float, optional
        Cap on TOD transit mode share (as a decimal). Default is 0.27 (27%),
        based on weighted average of five California TOD sites near rail stations
        (Lund et al. 2004).

    Returns
    -------
    float
        Percent reduction in GHG emissions from project VMT (as a decimal).
        Capped at -0.31 (-31%) when using default CBSA data. Negative values
        indicate reductions.
    """
    bc = min(transit_mode_share * tod_transit_ratio, tod_transit_share_cap)
    a = -(bc / vehicle_mode_share)
    return max(a, -0.31)


@register_measure(
    measure_id="T-4",
    name="Integrate Affordable and Below Market Rate Housing",
    subsector="land_use",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.286,
    land_use_types={_RES},
)
def t4_integrate_affordable_housing(
        pct_multifamily_units_affordable,
        vmt_reduction_per_qualified_unit=-0.286):
    """Measure T-4: Integrate Affordable and Below Market Rate Housing.
    Accounts for VMT reductions for multifamily residential projects where
    units are deed restricted or permanently dedicated as affordable housing
    (at or below 80% of area median income). Applies to project/site VMT.

    Formula: A = B * C

    Parameters
    ----------
    pct_multifamily_units_affordable : float
        Percent of multifamily units permanently dedicated as affordable
        (as a decimal, e.g., 0.50 for 50%). Must be 0.0-1.0.
    vmt_reduction_per_qualified_unit : float, optional
        Percent reduction in VMT for qualified units compared to market rate
        units (as a decimal). Default is -0.286 (-28.6%) based on ITE 2021
        Trip Generation Manual comparison of ITE codes 221 and 223.

    Returns
    -------
    float
        Percent reduction in GHG emissions from project/site multifamily VMT
        (as a decimal). Capped at -0.286 (-28.6%). Negative values indicate
        reductions.
    """
    a = pct_multifamily_units_affordable * vmt_reduction_per_qualified_unit
    return max(a, -0.286)


@register_measure(
    measure_id="T-55",
    name="Infill Development",
    subsector="land_use",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.30,
    land_use_types={_RES},
    # Cannot be combined with T-1 or T-3 per CAPCOA guidance.
    mutually_exclusive_with={"T-1", "T-3"},
)
def t55_infill_development(
        proposed_project_distance_to_downtown,
        conventional_development_distance_to_downtown,
        elasticity_vmt_distance_to_downtown=-0.22):
    """Measure T-55: Infill Development.
    Accounts for VMT reductions from infill housing development programs where
    residents live closer to downtown areas with greater access to jobs and
    activities. Requires rezoning commercial or industrial lots to high-density
    residential or mixed-use. Cannot be combined with T-1 or T-3.
    Applies to project/site residential VMT.

    Formula: A = ((C - B) / C) * D

    Parameters
    ----------
    proposed_project_distance_to_downtown : float
        Distance to downtown for proposed project [miles].
    conventional_development_distance_to_downtown : float
        Distance to downtown of conventional development in the region [miles].
        Should be estimated as population-weighted average distance to downtown
        for the relevant metro area (e.g., 13.4 miles for SF-Oakland-Berkeley MSA).
    elasticity_vmt_distance_to_downtown : float, optional
        Elasticity of VMT with respect to distance to downtown. Default is -0.22
        (Ewing & Cervero 2010; Stevens 2016).

    Returns
    -------
    float
        Percent reduction in GHG emissions from project VMT (as a decimal).
        Capped at -0.30 (-30%). Negative values indicate reductions.
    """
    a = ((conventional_development_distance_to_downtown
          - proposed_project_distance_to_downtown)
         / conventional_development_distance_to_downtown) * elasticity_vmt_distance_to_downtown
    return max(a, -0.30)


# ==============================================================================
# TRIP REDUCTION PROGRAMS SUBSECTOR (Project/Site — Employee Commute)
# Measure T-10
# Subsector cap: 45% commute VMT (across T-5 through T-13)
# ==============================================================================

@register_measure(
    measure_id="T-10",
    name="Provide End-of-Trip Bicycle Facilities",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.044,
)
def t10_provide_end_of_trip_bicycle_facilities(
        bike_mode_adjustment_factor,
        existing_bicycle_trip_length,
        existing_vehicle_trip_length,
        existing_bicycle_mode_share_work,
        existing_vehicle_mode_share_work):
    """Measure T-10: Provide End-of-Trip Bicycle Facilities.
    Provides end-of-trip facilities for employees (showers, lockers, bike parking)
    to encourage bicycle commuting in place of vehicle trips.
    Applies to employee project/site commute VMT.

    Formula: A = C * E * (1 - B) / (D * F)

    Parameters
    ----------
    bike_mode_adjustment_factor : float
        Likelihood ratio of bicycle commuting with end-of-trip facilities vs.
        without. Use 4.86 for parking + showers + lockers; 1.78 for bike
        parking only (Buehler 2012).
    existing_bicycle_trip_length : float
        Existing bicycle trip length for all trips in region [miles].
        From FHWA 2017a NHTS Table T-10.1 by CBSA.
    existing_vehicle_trip_length : float
        Existing vehicle trip length for all trips in region [miles].
        From FHWA 2017a NHTS Table T-10.1 by CBSA.
    existing_bicycle_mode_share_work : float
        Existing bicycle mode share for work trips in region (as a decimal).
        From FHWA 2017b NHTS Table T-10.2 by CBSA.
    existing_vehicle_mode_share_work : float
        Existing vehicle mode share for work trips in region (as a decimal).
        From FHWA 2017b NHTS Table T-10.2 by CBSA.

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT (as a decimal).
        Capped at -0.044 (-4.4%) when using default CBSA data. Negative values
        indicate reductions.
    """
    a = (existing_bicycle_trip_length
         * (existing_bicycle_mode_share_work
            - (bike_mode_adjustment_factor * existing_bicycle_mode_share_work))
         / (existing_vehicle_trip_length * existing_vehicle_mode_share_work))
    return max(a, -0.044)


# ==============================================================================
# NEIGHBORHOOD DESIGN SUBSECTOR (Plan/Community)
# Measures T-20, T-22-A, T-22-B, T-22-D
# Subsector cap: 10% (across T-18 through T-22-D)
# ==============================================================================

@register_measure(
    measure_id="T-20",
    name="Expand Bikeway Network",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.005,
)
def t20_expand_bikeway_network(
        existing_bikeway_miles_in_community,
        proposed_bikeway_miles_in_community,
        bike_mode_share,
        vehicle_mode_share,
        average_oneway_bicycle_trip_length,
        average_oneway_vehicle_trip_length,
        elasticity_of_bike_commuters_per_pop=0.25):
    """Measure T-20: Expand Bikeway Network.
    Increases the length of a city or community bikeway network (bike lanes,
    bike paths, bike routes, cycle tracks). Encourages mode shift from vehicles
    to bicycles, displacing VMT and reducing GHG emissions.
    Applies to commute vehicle travel in community (Plan/Community scale).

    Formula: A = -1 * (((B - C) / C) * D * E * F) / (G * H)

    Parameters
    ----------
    existing_bikeway_miles_in_community : float
        Existing bikeway miles in the community.
    proposed_bikeway_miles_in_community : float
        Proposed bikeway miles in the community with the measure.
    bike_mode_share : float
        Existing bike mode share in community (as a decimal).
    vehicle_mode_share : float
        Existing vehicle mode share in community (as a decimal).
    average_oneway_bicycle_trip_length : float
        Average one-way bicycle trip length [miles].
    average_oneway_vehicle_trip_length : float
        Average one-way vehicle trip length [miles].
    elasticity_of_bike_commuters_per_pop : float, optional
        Elasticity of bike commuter share per increase in bike lane distance.
        Default is 0.25 (Pucher & Buehler 2011: 0.25% increase in commute
        cycling per 1% increase in bike lane distance).

    Returns
    -------
    float
        Percent reduction in GHG emissions from commute vehicle travel
        (as a decimal). Negative values indicate reductions.
    """
    bike_way_ratio = ((proposed_bikeway_miles_in_community - existing_bikeway_miles_in_community)
                      / existing_bikeway_miles_in_community)
    numerator = (bike_way_ratio * bike_mode_share * average_oneway_bicycle_trip_length
                 * elasticity_of_bike_commuters_per_pop)
    denominator = vehicle_mode_share * average_oneway_vehicle_trip_length
    return -1 * numerator / denominator


@register_measure(
    measure_id="T-22-A",
    name="Implement Pedal (Non-Electric) Bikeshare Program",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0002,
)
def t22a_implement_pedal_bikeshare(
        pct_residences_with_access_with_measure,
        pct_residences_with_access_without_measure=0.0,
        daily_bikeshare_trips_per_person=0.021,
        vehicle_to_bikeshare_substitution_rate=0.196,
        bikeshare_avg_oneway_trip_length=1.4,
        daily_vehicle_trips_per_person=2.7,
        regional_avg_oneway_vehicle_trip_length=9.72):
    """Measure T-22-A: Implement Pedal (Non-Electric) Bikeshare Program.
    Establishes a traditional pedal bikeshare program providing on-demand access
    to bikes for short-term rentals, encouraging mode shift from vehicles.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Formula: A = -1 * ((C - B) * D * E * F) / (G * H)

    Parameters
    ----------
    pct_residences_with_access_with_measure : float
        Percent of residences in plan/community with access to bikeshare system
        WITH the measure (as a decimal, within 0.25 mi of a station).
    pct_residences_with_access_without_measure : float, optional
        Percent of residences with access WITHOUT the measure (as a decimal).
        Default is 0.0.
    daily_bikeshare_trips_per_person : float, optional
        Daily bikeshare trips per person in locations with bikeshare access.
        Default is 0.021 trips/day/person (MTC 2017 SF Bay Area analysis).
    vehicle_to_bikeshare_substitution_rate : float, optional
        Fraction of bikeshare trips that substitute for vehicle trips. Default
        is 0.196 (19.6%) from McQueen et al. 2020 literature review.
    bikeshare_avg_oneway_trip_length : float, optional
        Average one-way bikeshare trip length [miles]. Default is 1.4 miles
        (Lazarus et al. 2019 SF case study).
    daily_vehicle_trips_per_person : float, optional
        Daily vehicle trips per person. Default is 2.7 (FHWA 2018 NHTS).
    regional_avg_oneway_vehicle_trip_length : float, optional
        Regional average one-way vehicle trip length [miles]. Default is 9.72
        miles (Los Angeles-Long Beach-Anaheim CBSA from FHWA 2017 Table T-10.1).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.0002 (-0.02%) using default CBSA data.
        Negative values indicate reductions.
    """
    a = (-1 * ((pct_residences_with_access_with_measure
                - pct_residences_with_access_without_measure)
               * daily_bikeshare_trips_per_person
               * vehicle_to_bikeshare_substitution_rate
               * bikeshare_avg_oneway_trip_length)
         / (daily_vehicle_trips_per_person * regional_avg_oneway_vehicle_trip_length))
    return max(a, -0.0002)


@register_measure(
    measure_id="T-22-B",
    name="Implement Electric Bikeshare Program",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0006,
)
def t22b_implement_electric_bikeshare(
        pct_residences_with_access_with_measure,
        pct_residences_with_access_without_measure=0.0,
        daily_ebikeshare_trips_per_person=0.021,
        vehicle_to_ebikeshare_substitution_rate=0.35,
        ebikeshare_avg_oneway_trip_length=2.1,
        daily_vehicle_trips_per_person=2.7,
        regional_avg_oneway_vehicle_trip_length=9.72):
    """Measure T-22-B: Implement Electric Bikeshare Program.
    Establishes an electric bikeshare program providing on-demand access to
    pedal-assist bikes for short-term rentals. Electric bikes increase ridership
    and accessibility over traditional bikes, encouraging greater mode shift.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Formula: A = -1 * ((C - B) * D * E * F) / (G * H)

    Parameters
    ----------
    pct_residences_with_access_with_measure : float
        Percent of residences in plan/community with access to electric bikeshare
        WITH the measure (as a decimal, within 0.25 mi of a station).
    pct_residences_with_access_without_measure : float, optional
        Percent of residences with access WITHOUT the measure (as a decimal).
        Default is 0.0.
    daily_ebikeshare_trips_per_person : float, optional
        Daily electric bikeshare trips per person in locations with access.
        Default is 0.021 trips/day/person (MTC 2017).
    vehicle_to_ebikeshare_substitution_rate : float, optional
        Fraction of e-bikeshare trips that substitute for vehicle trips. Default
        is 0.35 (35%) from Fitch et al. 2021 Sacramento dockless e-bikeshare study.
    ebikeshare_avg_oneway_trip_length : float, optional
        Average one-way electric bikeshare trip length [miles]. Default is 2.1
        miles (Fitch et al. 2021).
    daily_vehicle_trips_per_person : float, optional
        Daily vehicle trips per person. Default is 2.7 (FHWA 2018 NHTS).
    regional_avg_oneway_vehicle_trip_length : float, optional
        Regional average one-way vehicle trip length [miles]. Default is 9.72
        miles (Los Angeles CBSA from FHWA 2017 Table T-10.1).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.0006 (-0.06%) using default CBSA data.
        Negative values indicate reductions.
    """
    a = (-1 * ((pct_residences_with_access_with_measure
                - pct_residences_with_access_without_measure)
               * daily_ebikeshare_trips_per_person
               * vehicle_to_ebikeshare_substitution_rate
               * ebikeshare_avg_oneway_trip_length)
         / (daily_vehicle_trips_per_person * regional_avg_oneway_vehicle_trip_length))
    return max(a, -0.0006)


@register_measure(
    measure_id="T-22-D",
    name="Transition Conventional to Electric Bikeshare",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.00059,
)
def t22d_transition_conventional_to_electric_bikeshare(
        pct_residences_with_traditional_bikeshare_access,
        pct_bikes_transitioned_to_electric,
        daily_bikeshare_trips_per_person=0.021,
        vehicle_to_ebikeshare_substitution_rate=0.35,
        ebikeshare_avg_oneway_trip_length=2.1,
        vehicle_to_conventional_bikeshare_substitution_rate=0.196,
        conventional_bikeshare_avg_oneway_trip_length=1.4,
        daily_vehicle_trips_per_person=1.7,
        regional_avg_oneway_vehicle_trip_length=9.72):
    """Measure T-22-D: Transition Conventional to Electric Bikeshare.
    Accounts for VMT reductions from transitioning an existing traditional
    bikeshare program to electric bikes. Does not account for expansion of
    coverage area; use T-22-A/B for that.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Formula: A = -(B * C * D * ((E * F) - (G * H))) / (I * J)

    Parameters
    ----------
    pct_residences_with_traditional_bikeshare_access : float
        Percent of residences in plan/community with access to the traditional
        bikeshare system (as a decimal, within 0.25 mi of a station).
    pct_bikes_transitioned_to_electric : float
        Percent of bikeshare bikes transitioned from conventional to electric
        (as a decimal). E.g., 0.50 = 50 out of 100 bikes switched to e-bikes.
    daily_bikeshare_trips_per_person : float, optional
        Daily bikeshare trips per person. Default is 0.021 (MTC 2021).
    vehicle_to_ebikeshare_substitution_rate : float, optional
        Fraction of e-bikeshare trips substituting for vehicle trips. Default
        is 0.35 (Fitch et al. 2021).
    ebikeshare_avg_oneway_trip_length : float, optional
        Average one-way electric bikeshare trip length [miles]. Default is 2.1
        (Fitch et al. 2021).
    vehicle_to_conventional_bikeshare_substitution_rate : float, optional
        Fraction of conventional bikeshare trips substituting for vehicle trips.
        Default is 0.196 (McQueen et al. 2020).
    conventional_bikeshare_avg_oneway_trip_length : float, optional
        Average one-way conventional bikeshare trip length [miles]. Default is
        1.4 (Lazarus et al. 2019).
    daily_vehicle_trips_per_person : float, optional
        Daily vehicle trips per person. Default is 1.7 (FHWA 2023).
    regional_avg_oneway_vehicle_trip_length : float, optional
        Regional average one-way vehicle trip length [miles]. Default is 9.72
        miles (Los Angeles CBSA from FHWA 2017 Table T-10.1).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.00059 (-0.059%). Negative values indicate
        reductions.
    """
    electric_term = (vehicle_to_ebikeshare_substitution_rate
                     * ebikeshare_avg_oneway_trip_length)
    conventional_term = (vehicle_to_conventional_bikeshare_substitution_rate
                         * conventional_bikeshare_avg_oneway_trip_length)
    a = (-(pct_residences_with_traditional_bikeshare_access
           * pct_bikes_transitioned_to_electric
           * daily_bikeshare_trips_per_person
           * (electric_term - conventional_term))
         / (daily_vehicle_trips_per_person * regional_avg_oneway_vehicle_trip_length))
    return max(a, -0.00059)


# ==============================================================================
# TRANSIT SUBSECTOR (Plan/Community)
# Measures T-26, T-27, T-28, T-46
# Subsector cap: 15% (across T-25 through T-29, T-46)
# IMPORTANT: T-28 (BRT) is mutually exclusive with T-26, T-27, and T-46
# when BRT covers all transit routes. Use excluded_measure_ids in the
# subsector orchestrator to enforce this.
# ==============================================================================

@register_measure(
    measure_id="T-26",
    name="Increase Transit Service Frequency",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.113,
    mutually_exclusive_with={"T-28"},
)
def t26_increase_transit_service_frequency(
        pct_increase_in_transit_frequency,
        level_of_implementation,
        transit_mode_share,
        vehicle_mode_share,
        elasticity_ridership_frequency=0.5,
        statewide_mode_shift_factor=0.578):
    """Measure T-26: Increase Transit Service Frequency.
    Implements frequency improvements on transit routes to encourage mode shift
    from vehicles to transit, reducing VMT and GHG emissions.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Formula: A = -C * (B * E * D * G) / F

    Parameters
    ----------
    pct_increase_in_transit_frequency : float
        Percent increase in transit frequency (as a decimal, e.g., 1.0 = 100%
        increase = doubling frequency). Calculated as (freq_with - freq_without)
        / freq_without. Capped at 3.0 (300%) per SANDAG 2019.
    level_of_implementation : float
        Fraction of transit routes in plan/community receiving the improvement
        (as a decimal, 0.0-1.0).
    transit_mode_share : float
        Transit mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    vehicle_mode_share : float
        Vehicle mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    elasticity_ridership_frequency : float, optional
        Elasticity of transit ridership with respect to frequency. Default is
        0.5 (Handy et al. 2013: 0.5% ridership increase per 1% frequency increase).
    statewide_mode_shift_factor : float, optional
        Adjustment factor reflecting reduction in vehicle trips per reduction
        in person trips (= 1 / average vehicle occupancy). Default is 0.578
        (57.8%) from FHWA 2017b.

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.113 (-11.3%) using default CBSA data with
        maximum frequency increase. Negative values indicate reductions.
    """
    b = min(pct_increase_in_transit_frequency, 3.0)
    a = (-level_of_implementation
         * (b * transit_mode_share * elasticity_ridership_frequency * statewide_mode_shift_factor)
         / vehicle_mode_share)
    return max(a, -0.113)


@register_measure(
    measure_id="T-27",
    name="Implement Transit-Supportive Roadway Treatments",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.006,
    mutually_exclusive_with={"T-28"},
)
def t27_implement_transit_supportive_roadway_treatments(
        pct_transit_routes_receiving_treatments,
        transit_mode_share,
        vehicle_mode_share,
        pct_change_in_transit_travel_time=-0.10,
        elasticity_ridership_travel_time=-0.4,
        statewide_mode_shift_factor=0.578):
    """Measure T-27: Implement Transit-Supportive Roadway Treatments.
    Implements transit signal priority, bus-only signal phases, queue jumps,
    curb extensions, or dedicated bus lanes to improve transit travel times,
    encouraging mode shift from vehicles to transit.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Formula: A = -1 * (B * C * D * E * G) / F

    Parameters
    ----------
    pct_transit_routes_receiving_treatments : float
        Fraction of plan/community transit routes that receive treatments
        (as a decimal, 0.0-1.0).
    transit_mode_share : float
        Transit mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    vehicle_mode_share : float
        Vehicle mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    pct_change_in_transit_travel_time : float, optional
        Percent change in transit travel time due to treatments (as a decimal,
        negative = improvement). Default is -0.10 (-10%), midpoint of 8-12%
        range for transit signal prioritization (TRB 2007). Capped at -0.20.
    elasticity_ridership_travel_time : float, optional
        Elasticity of transit ridership with respect to transit travel time
        (as a decimal). Default is -0.4 (TRB 2007).
    statewide_mode_shift_factor : float, optional
        Adjustment factor (= 1 / average vehicle occupancy). Default is 0.578
        (FHWA 2017b).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.006 (-0.6%) using default CBSA data with
        maximum travel time reduction. Negative values indicate reductions.
    """
    c = max(pct_change_in_transit_travel_time, -0.20)
    a = (-1 * (pct_transit_routes_receiving_treatments
               * c
               * elasticity_ridership_travel_time
               * transit_mode_share
               * statewide_mode_shift_factor)
         / vehicle_mode_share)
    return max(a, -0.006)


@register_measure(
    measure_id="T-28",
    name="Provide Bus Rapid Transit",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.138,
    # Mutually exclusive with T-26, T-27, T-46 when applied to all routes.
    mutually_exclusive_with={"T-26", "T-27", "T-46"},
)
def t28_provide_bus_rapid_transit(
        pct_increase_in_transit_frequency,
        level_of_implementation,
        transit_mode_share,
        vehicle_mode_share,
        statewide_mode_shift_factor=0.578,
        pct_ridership_increase_brt_bonus=0.25,
        pct_change_in_transit_travel_time=-0.10,
        elasticity_ridership_frequency=0.5,
        elasticity_ridership_travel_time=-0.4):
    """Measure T-28: Provide Bus Rapid Transit.
    Converts existing bus routes to BRT with exclusive right-of-way, increased
    frequency, intelligent transportation technology, advanced vehicles, enhanced
    stations, and efficient fare payment.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Mutually exclusive with T-26, T-27, and T-46 when applied to ALL routes.
    Use excluded_measure_ids={"T-26","T-27","T-46"} in the transit orchestrator.

    Formula: A = -C * (D * F * ((B * I) + (H * J) + G)) / E

    Parameters
    ----------
    pct_increase_in_transit_frequency : float
        Percent increase in transit frequency due to BRT (as a decimal,
        e.g., 1.0 = 100%). Capped at 3.0 (300%) per SANDAG 2019.
    level_of_implementation : float
        Fraction of transit routes in plan/community receiving BRT (as a decimal,
        0.0-1.0).
    transit_mode_share : float
        Transit mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    vehicle_mode_share : float
        Vehicle mode share in plan/community (as a decimal). From FHWA 2017a
        NHTS Table T-3.1 by CBSA.
    statewide_mode_shift_factor : float, optional
        Adjustment factor (= 1 / average vehicle occupancy). Default is 0.578
        (FHWA 2017b).
    pct_ridership_increase_brt_bonus : float, optional
        Additional percent increase in ridership from full-featured BRT beyond
        travel time and frequency improvements (as a decimal). Default is 0.25
        (25%) from TRB 2007 BRT Practitioner's Guide.
    pct_change_in_transit_travel_time : float, optional
        Percent change in transit travel time due to BRT components (as a decimal,
        negative = improvement). Default is -0.10 (-10%) from TRB 2007. Capped
        at -0.20 (-20%).
    elasticity_ridership_frequency : float, optional
        Elasticity of transit ridership with respect to frequency. Default is
        0.5 (Handy et al. 2013).
    elasticity_ridership_travel_time : float, optional
        Elasticity of transit ridership with respect to transit travel time
        (as a decimal). Default is -0.4 (TRB 2007).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.138 (-13.8%) using default CBSA data.
        Negative values indicate reductions.
    """
    b = min(pct_increase_in_transit_frequency, 3.0)
    h = max(pct_change_in_transit_travel_time, -0.20)
    frequency_term = b * elasticity_ridership_frequency
    travel_time_term = h * elasticity_ridership_travel_time
    a = (-level_of_implementation
         * (transit_mode_share
            * statewide_mode_shift_factor
            * (frequency_term + travel_time_term + pct_ridership_increase_brt_bonus))
         / vehicle_mode_share)
    return max(a, -0.138)


@register_measure(
    measure_id="T-46",
    name="Provide Transit Shelters",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0032,
    mutually_exclusive_with={"T-28"},
)
def t46_provide_transit_shelters(
        num_stops_with_new_shelters,
        avg_boardings_per_day_at_improved_stops,
        avg_boardings_per_day_across_agency,
        transit_mode_share,
        include_real_time_information=False,
        pct_transit_users_who_would_otherwise_drive=0.833,
        avg_auto_occupancy=1.45,
        pct_travel_time_waiting_existing=0.249,
        pct_perceived_waiting_with_shelters=0.203,
        pct_perceived_waiting_with_shelters_and_rti=0.158,
        wait_time_elasticity=-0.54):
    """Measure T-46: Provide Transit Shelters.
    Constructs bus shelters (with or without real-time arrival information) to
    reduce perceived wait times and encourage transit use over driving.
    Applies to vehicle travel in plan/community (Plan/Community scale).

    Mutually exclusive with T-28 when T-28 covers all routes.

    Formula (shelters only):     A1 = B * (C/D) * E * (F/G) * (H - I1) * J
    Formula (shelters + RTI):    A2 = B * (C/D) * E * (F/G) * (H - I2) * J

    Parameters
    ----------
    num_stops_with_new_shelters : int or float
        Number of transit stops receiving new bus shelters and benches.
    avg_boardings_per_day_at_improved_stops : float
        Average number of boardings per day at each transit stop before new
        amenities are added [boardings/day/stop].
    avg_boardings_per_day_across_agency : float
        Average total number of boardings per day across the entire transit
        agency [boardings/day].
    transit_mode_share : float
        Transit mode share in the CBSA (as a decimal). From FHWA 2017 NHTS
        Table T-3.1 by CBSA.
    include_real_time_information : bool, optional
        If True, use the formula variant with real-time arrival information
        (RTI), which yields greater ridership gains. Default is False.
    pct_transit_users_who_would_otherwise_drive : float, optional
        Fraction of transit users who would otherwise drive (as a decimal).
        Default is 0.833 (83.3%) from FHWA 2017 NHTS.
    avg_auto_occupancy : float, optional
        Average car occupancy for trips. Default is 1.45 (FHWA 2023 NHTS).
    pct_travel_time_waiting_existing : float, optional
        Percent of total transit trip time spent waiting, existing conditions
        (as a decimal). Default is 0.249 (24.9%) from FHWA 2023 NHTS Pacific region.
    pct_perceived_waiting_with_shelters : float, optional
        Percent of perceived total travel time spent waiting with shelters only
        (as a decimal). Default is 0.203 (20.3%) from Fan et al. 2016.
    pct_perceived_waiting_with_shelters_and_rti : float, optional
        Percent of total travel time spent waiting with shelters AND real-time
        information (as a decimal). Default is 0.158 (15.8%) from Watkins 2011.
    wait_time_elasticity : float, optional
        Elasticity of transit ridership with respect to wait time (as a decimal).
        Default is -0.54 (Taylor et al. 2009 LA Metro study).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in plan/community
        (as a decimal). Capped at -0.0032 (-0.32%). Negative values indicate
        reductions.
    """
    i = (pct_perceived_waiting_with_shelters_and_rti if include_real_time_information
         else pct_perceived_waiting_with_shelters)
    a = (num_stops_with_new_shelters
         * (avg_boardings_per_day_at_improved_stops / avg_boardings_per_day_across_agency)
         * transit_mode_share
         * (pct_transit_users_who_would_otherwise_drive / avg_auto_occupancy)
         * (pct_travel_time_waiting_existing - i)
         * wait_time_elasticity)
    return max(a, -0.0032)


# ==============================================================================
# SCHOOL PROGRAMS SUBSECTOR (Project/Site)
# Measures T-40, T-56
# Subsector cap: 72% school VMT
# To convert to community-scale reductions, multiply by 0.0164 (1.64%).
# ==============================================================================

@register_measure(
    measure_id="T-40",
    name="Establish a School Bus Program",
    subsector="school_programs",
    scale=_PS,
    location_types={_U, _S, _R},
    measure_max=0.57,
    land_use_types={_SCH},
)
def t40_establish_school_bus_program(
        pct_students_who_begin_riding_bus,
        pct_students_served_by_bus,
        light_duty_emission_factor,
        school_bus_emission_factor,
        pct_new_riders_who_previously_drove=0.79,
        avg_student_occupancy_cars=1.58,
        avg_student_occupancy_buses=14.9,
        bus_tour_to_driving_distance_ratio=3.42):
    """Measure T-40: Establish a School Bus Program.
    Establishes a new school bus program or expands an existing one, replacing
    private vehicle trips with shared bus trips for school commutes.
    Applies to vehicle travel among students (Project/Site school commute scale).

    Formula: A = B * C * D * ((H/E) - (G*I/F)) / (H/E)

    Parameters
    ----------
    pct_students_who_begin_riding_bus : float
        Percent of students at the school who begin riding the bus as a result
        of the program (as a decimal).
    pct_students_served_by_bus : float
        Percent of students for whom the bus program provides service (as a
        decimal).
    light_duty_emission_factor : float
        Light-duty vehicle emission factor [grams CO2e/mile]. From CARB EMFAC
        or Table T-30.2.
    school_bus_emission_factor : float
        School bus emission factor [grams CO2e/mile]. From CARB EMFAC or Table
        T-40.2. For electric buses, use the electric emission factor.
    pct_new_riders_who_previously_drove : float, optional
        Fraction of new bus riders who drove or were driven before. Default is
        0.79 (79%) from FHWA 2023 NHTS.
    avg_student_occupancy_cars : float, optional
        Average student occupancy of cars driving to school [students/car].
        Default is 1.58 (FHWA 2023 NHTS Pacific division).
    avg_student_occupancy_buses : float, optional
        Average student occupancy of school buses [students/bus]. Default is
        14.9 (Wang 2019 Table T-40.1 average).
    bus_tour_to_driving_distance_ratio : float, optional
        Ratio of bus touring distance to private driving distance. Default is
        3.42 (FHWA 2023 NHTS + Duran 2013: avg school trip = 9.3 mi by car,
        avg bus tour = 31.7 mi).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel among students
        (as a decimal). Capped at -0.57 (-57%). Negative values indicate
        reductions.
    """
    car_ghg_per_student = light_duty_emission_factor / avg_student_occupancy_cars
    bus_ghg_per_student = (bus_tour_to_driving_distance_ratio
                           * school_bus_emission_factor / avg_student_occupancy_buses)
    a = (pct_students_who_begin_riding_bus
         * pct_students_served_by_bus
         * pct_new_riders_who_previously_drove
         * (bus_ghg_per_student - car_ghg_per_student)
         / car_ghg_per_student)
    return max(a, -0.57)


@register_measure(
    measure_id="T-56",
    name="Active Modes of Transportation for Youth",
    subsector="school_programs",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.222,
    land_use_types={_SCH},
)
def t56_active_modes_transportation_youth(
        pct_near_students_driven_after_implementation,
        pct_students_within_2_miles=0.62,
        pct_near_students_driven_before_implementation=0.51,
        pct_far_students_driven=0.66,
        avg_driving_distance_near_students=2.0,
        avg_driving_distance_far_students=8.66):
    """Measure T-56: Active Modes of Transportation for Youth.
    Provides infrastructure to support active transportation (walking, biking)
    among youth for trips to school and extracurricular activities, including
    Safe Routes to Schools (SR2S) projects. Applies to school commute vehicle
    travel (Project/Site).

    Formula: A = C * F * (B - D) / (G * E * (1 - C) + C * D * F)

    Parameters
    ----------
    pct_near_students_driven_after_implementation : float
        Known or estimated percent of students within 2 miles of school who are
        driven after project implementation (as a decimal). Obtain via SR2S
        student travel surveys.
    pct_students_within_2_miles : float, optional
        Percent of students living within 2 miles of the school (as a decimal).
        Default is 0.62 (62%) from SR2S Partnership 2013.
    pct_near_students_driven_before_implementation : float, optional
        Percent of students within 2 miles who are driven to school BEFORE
        measure implementation (as a decimal). Default is 0.51 (51%) from SR2S
        Partnership 2013.
    pct_far_students_driven : float, optional
        Percent of students more than 2 miles from school who are driven (as a
        decimal). Default is 0.66 (66%) from FHWA 2023.
    avg_driving_distance_near_students : float, optional
        Average driving distance for students who could walk or bike (< 2 miles)
        [miles]. Default is 2.0 miles (assumed).
    avg_driving_distance_far_students : float, optional
        Average driving distance for students who cannot walk or bike (> 2 miles)
        [miles]. Default is 8.66 miles (FHWA 2023 NHTS).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel among students
        within walking/biking distance (as a decimal). Capped at -0.222 (-22.2%).
        Negative values indicate reductions.
    """
    c = pct_students_within_2_miles
    f = avg_driving_distance_near_students
    b = pct_near_students_driven_after_implementation
    d = pct_near_students_driven_before_implementation
    e = pct_far_students_driven
    g = avg_driving_distance_far_students
    denominator = g * e * (1 - c) + c * d * f
    a = c * f * (b - d) / denominator
    return max(a, -0.222)
