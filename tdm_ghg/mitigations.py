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
# Measures T-5, T-6, T-7, T-8, T-9, T-10, T-11, T-12, T-13
# Subsector cap: 45% commute VMT (across T-5 through T-13)
# ==============================================================================

@register_measure(
    measure_id="T-5",
    name="Implement Commute Trip Reduction Program (Voluntary)",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.04,
    # T-5 covers the same activities as T-6 (mandatory version); select one.
    # T-5 also bundles T-7 through T-11; combining would double-count.
    mutually_exclusive_with={"T-6", "T-7", "T-8", "T-9", "T-10", "T-11"},
)
def t5_implement_voluntary_commute_trip_reduction(
        pct_employees_eligible,
        pct_reduction_commute_vmt=-0.04):
    """Measure T-5: Implement Commute Trip Reduction Program (Voluntary).
    Implements a voluntary CTR program with employers, encouraging alternatives
    to single-occupancy vehicles (carpooling, transit, walking, biking).
    Applies to project/site employee commute VMT.

    Formula: A = B * C

    Parameters
    ----------
    pct_employees_eligible : float
        Percent of employees eligible for the program (as a decimal,
        e.g., 1.0 for 100%). Excludes night-shift or drive-required workers.
    pct_reduction_commute_vmt : float, optional
        Percent reduction in commute VMT for eligible employees (as a decimal).
        Default is -0.04 (-4%), per Boarnet et al. 2014 low-end estimate.

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.04 (-4%). Negative values indicate
        reductions.
    """
    a = pct_employees_eligible * pct_reduction_commute_vmt
    return max(a, -0.04)


@register_measure(
    measure_id="T-6",
    name="Implement Commute Trip Reduction Program (Mandatory)",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.26,
    # T-6 covers the same activities as T-5 (voluntary version); select one.
    # T-6 also bundles T-7 through T-11; combining would double-count.
    mutually_exclusive_with={"T-5", "T-7", "T-8", "T-9", "T-10", "T-11"},
)
def t6_implement_mandatory_commute_trip_reduction(
        pct_employees_eligible,
        pct_reduction_vehicle_mode_share=-0.26,
        adjustment_vehicle_mode_to_vmt=1.0):
    """Measure T-6: Implement Commute Trip Reduction Program (Mandatory).
    Implements a mandatory CTR program with employer monitoring requirements.
    Based on Genentech South SF campus data (2006-2014): vehicle mode share
    dropped from ~90% to ~64% (26% reduction). Applies to employee commute VMT.

    Formula: A = B * C * D

    Parameters
    ----------
    pct_employees_eligible : float
        Percent of employees eligible for the program (as a decimal,
        e.g., 1.0 for 100%). Usually 100% for mandatory programs.
    pct_reduction_vehicle_mode_share : float, optional
        Percent reduction in vehicle mode share of commute trips (as a decimal).
        Default is -0.26 (-26%), per Nelson/Nygaard Consulting Associates 2015.
    adjustment_vehicle_mode_to_vmt : float, optional
        Adjustment factor from vehicle mode share to commute VMT. Default is 1.0
        (assumes percentage reduction in trips equals reduction in VMT).

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.26 (-26%). Negative values indicate
        reductions.
    """
    a = (pct_employees_eligible
         * pct_reduction_vehicle_mode_share
         * adjustment_vehicle_mode_to_vmt)
    return max(a, -0.26)


@register_measure(
    measure_id="T-7",
    name="Implement Commute Trip Reduction Marketing",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.04,
    # Cannot be combined with T-5 or T-6 (bundled programs); may pair with T-8 to T-13.
    mutually_exclusive_with={"T-5", "T-6"},
)
def t7_implement_commute_trip_reduction_marketing(
        pct_employees_eligible,
        pct_reduction_vehicle_trips=-0.04,
        adjustment_vehicle_trips_to_vmt=1.0):
    """Measure T-7: Implement Commute Trip Reduction Marketing.
    Markets alternative travel options to employees via onsite/online commuter
    information services, encouraging shift away from single-occupancy vehicles.
    Applies to project/site employee commute VMT.

    Formula: A = B * C * D

    Parameters
    ----------
    pct_employees_eligible : float
        Percent of employees eligible for the program (as a decimal,
        e.g., 1.0 for 100%). Usually 100%; excludes drive-required workers.
    pct_reduction_vehicle_trips : float, optional
        Percent reduction in employee commute vehicle trips (as a decimal).
        Default is -0.04 (-4%), per TRB 2010 low-end of 4-5% range.
    adjustment_vehicle_trips_to_vmt : float, optional
        Adjustment factor from vehicle trips to VMT. Default is 1.0
        (assumes all trip lengths are equal; reduction in trips equals VMT).

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.04 (-4%). Negative values indicate
        reductions.
    """
    a = (pct_employees_eligible
         * pct_reduction_vehicle_trips
         * adjustment_vehicle_trips_to_vmt)
    return max(a, -0.04)


@register_measure(
    measure_id="T-8",
    name="Provide Ridesharing Program",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.08,
    # Cannot be combined with T-5 or T-6; may pair with T-7 and T-9 to T-13.
    mutually_exclusive_with={"T-5", "T-6"},
)
def t8_provide_ridesharing_program(
        pct_employees_eligible,
        pct_reduction_commute_vmt=-0.08):
    """Measure T-8: Provide Ridesharing Program.
    Establishes a ridesharing program (carpool/vanpool) with a permanent
    transportation management association. Designated parking, loading areas,
    and ride-coordination app/website are required. Applies to employee commute VMT.

    Formula: A = B * C

    Parameters
    ----------
    pct_employees_eligible : float
        Percent of employees eligible for the program (as a decimal,
        e.g., 1.0 for 100%). Usually 100%; excludes night-shift workers.
    pct_reduction_commute_vmt : float, optional
        Percent reduction in employee commute VMT by place type (as a decimal).
        Default is -0.08 (-8%), corresponding to urban place type per SANDAG 2019
        Table T-8.1. Not applicable in rural areas.

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.08 (-8%). Negative values indicate
        reductions.
    """
    a = pct_employees_eligible * pct_reduction_commute_vmt
    return max(a, -0.08)


@register_measure(
    measure_id="T-9",
    name="Implement Subsidized or Discounted Transit Program",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.055,
    # Cannot be combined with T-5 or T-6; may pair with T-7, T-8, T-10 to T-13.
    mutually_exclusive_with={"T-5", "T-6"},
)
def t9_implement_subsidized_transit_program(
        transit_fare,
        subsidy_amount,
        pct_eligible,
        pct_project_vmt_from_employees,
        transit_mode_share,
        elasticity_transit_boardings_fare=-0.43,
        pct_transit_replacing_vehicle=0.50,
        conversion_vehicle_trips_to_vmt=1.0):
    """Measure T-9: Implement Subsidized or Discounted Transit Program.
    Provides subsidized/discounted or free transit passes for employees and/or
    residents, improving transit competitiveness against driving and reducing VMT.
    Site must be within 1 mile of high-quality transit or 0.5 mile of local transit.
    Applies to employee/resident vehicles accessing the site.

    Formula: A = (C / B) * G * D * E * F * H * I

    Parameters
    ----------
    transit_fare : float
        Average transit fare without subsidy [$]. May be per-ride or monthly pass.
    subsidy_amount : float
        Subsidy amount provided to employees/residents [$]. Same unit as transit_fare.
    pct_eligible : float
        Percent of employees/residents eligible for the subsidy (as a decimal,
        e.g., 1.0 for 100%). Accounts for workers without subsidy benefits.
    pct_project_vmt_from_employees : float
        Percent of project-generated VMT from employees/residents (as a decimal).
        Use 1.0 for office or pure residential; less for visitor-intensive uses.
    transit_mode_share : float
        Transit mode share for work trips or all trips in the project area
        (as a decimal). From FHWA 2017 NHTS Table T-3.1 or T-9.1 by CBSA.
    elasticity_transit_boardings_fare : float, optional
        Elasticity of transit boardings with respect to transit fare price.
        Default is -0.43 (Taylor et al. 2008; 0.43% decrease per 1% fare increase).
    pct_transit_replacing_vehicle : float, optional
        Fraction of new transit trips that would otherwise be made by vehicle.
        Default is 0.50 (50%), per Handy & Boarnet 2013 for high-quality BRT.
    conversion_vehicle_trips_to_vmt : float, optional
        Conversion factor from vehicle trips to VMT. Default is 1.0 (assumes
        all trip lengths are equal).

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee/resident vehicles
        accessing the site (as a decimal). Capped at -0.055 (-5.5%). Negative
        values indicate reductions.
    """
    a = ((subsidy_amount / transit_fare)
         * elasticity_transit_boardings_fare
         * pct_eligible
         * pct_project_vmt_from_employees
         * transit_mode_share
         * pct_transit_replacing_vehicle
         * conversion_vehicle_trips_to_vmt)
    return max(a, -0.055)


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


@register_measure(
    measure_id="T-11",
    name="Provide Employer-Sponsored Vanpool",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S, _R},
    measure_max=0.204,
    # Cannot combine with T-5 or T-6 (bundled programs that already include vanpool).
    mutually_exclusive_with={"T-5", "T-6"},
)
def t11_provide_employer_sponsored_vanpool(
        pct_employees_vanpooling,
        avg_vehicle_commute_trip_length,
        avg_vanpool_trip_length=42.0,
        avg_vanpool_occupancy=6.25,
        avg_employee_vehicle_emission_factor=307.5,
        vanpool_emission_factor=763.4):
    """Measure T-11: Provide Employer-Sponsored Vanpool.
    Replaces single-occupancy vehicle commute trips with shared vanpool trips,
    reducing per-employee commute GHG. Vanpool routes are typically longer than
    solo commutes but emissions are shared among occupants.
    Applies to project/site employee commute VMT.

    Formula: A = [(1-B)*C*F + B*(D/E)*G] / [(1-B)*C*F + B*D*F] - 1

    Parameters
    ----------
    pct_employees_vanpooling : float
        Percent of employees participating in the vanpool (as a decimal,
        e.g., 0.15 for 15%). Bmax = 0.15 per U.S. vanpool participation data.
    avg_vehicle_commute_trip_length : float
        Average one-way vehicle commute trip length in the region [miles].
        From FHWA 2017 NHTS Table T-11.1 by CBSA (e.g., 14.52 mi, San Diego).
    avg_vanpool_trip_length : float, optional
        Average one-way vanpool commute trip length [miles]. Default is 42.0
        (longer than solo commute due to pick-up routing; SANDAG 2019).
    avg_vanpool_occupancy : float, optional
        Average vanpool occupancy including driver. Default is 6.25 occupants
        (SANDAG 2019 vanpool program data).
    avg_employee_vehicle_emission_factor : float, optional
        Average emission factor of employee vehicles [g CO2e/mile].
        Default is 307.5 (CARB EMFAC 2021 statewide light-duty fleet).
    vanpool_emission_factor : float, optional
        Average vanpool vehicle emission factor [g CO2e/mile].
        Default is 763.4 (CARB EMFAC 2021 van/minivan fleet average).

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.204 (-20.4%). Negative values indicate
        reductions.
    """
    solo = (1 - pct_employees_vanpooling) * avg_vehicle_commute_trip_length
    without_emissions = (solo * avg_employee_vehicle_emission_factor
                         + pct_employees_vanpooling * avg_vanpool_trip_length
                         * avg_employee_vehicle_emission_factor)
    with_emissions = (solo * avg_employee_vehicle_emission_factor
                      + pct_employees_vanpooling
                      * (avg_vanpool_trip_length / avg_vanpool_occupancy)
                      * vanpool_emission_factor)
    a = (with_emissions / without_emissions) - 1
    return max(a, -0.204)


@register_measure(
    measure_id="T-12",
    name="Price Workplace Parking",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.20,
    # Cannot combine with T-13 (cash-out is an alternative pricing mechanism).
    mutually_exclusive_with={"T-13"},
)
def t12_price_workplace_parking(
        proposed_parking_price,
        baseline_parking_price,
        share_employees_paying_for_parking,
        elasticity_parking_demand=-0.4,
        ratio_vehicle_trip_reduction_to_vmt=1.0):
    """Measure T-12: Price Workplace Parking.
    Charges employees for workplace parking, discouraging solo driving through
    a direct out-of-pocket cost. Price increase is capped at 50% over baseline
    in the formula per CAPCOA guidance.
    Applies to project/site employee commute VMT.

    Formula: A = ((B - C) / C) * E * D * F

    Parameters
    ----------
    proposed_parking_price : float
        Proposed daily (or monthly) parking price charged to employees [$].
    baseline_parking_price : float
        Current (baseline) parking price [$]. If zero (free parking),
        the formula uses C = proposed_parking_price / 4 per CAPCOA guidance.
    share_employees_paying_for_parking : float
        Share of employees who will pay the parking price (as a decimal,
        e.g., 0.80 for 80%).
    elasticity_parking_demand : float, optional
        Elasticity of parking demand with respect to price. Default is -0.4
        (Shoup 2005; 0.4% decrease in parking demand per 1% price increase).
    ratio_vehicle_trip_reduction_to_vmt : float, optional
        Adjustment from vehicle trip reduction to VMT reduction. Default is 1.0.

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.20 (-20%). Negative values indicate
        reductions.
    """
    effective_baseline = (baseline_parking_price if baseline_parking_price > 0
                          else proposed_parking_price / 4)
    price_ratio = min((proposed_parking_price - effective_baseline) / effective_baseline, 0.50)
    a = (price_ratio * elasticity_parking_demand
         * share_employees_paying_for_parking
         * ratio_vehicle_trip_reduction_to_vmt)
    return max(a, -0.20)


@register_measure(
    measure_id="T-13",
    name="Implement Employee Parking Cash-Out",
    subsector="trip_reduction",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.12,
    # Cannot combine with T-12 (workplace pricing is an alternative mechanism).
    mutually_exclusive_with={"T-12"},
)
def t13_implement_employee_parking_cash_out(
        pct_employees_eligible,
        pct_reduction_commute_vmt=-0.12):
    """Measure T-13: Implement Employee Parking Cash-Out.
    Offers employees who forgo their employer-subsidised parking space a cash
    payment equal to the parking subsidy value, incentivising mode shift.
    Applies to project/site employee commute VMT.

    Formula: A = B * C

    Parameters
    ----------
    pct_employees_eligible : float
        Percent of employees eligible for the cash-out program (as a decimal,
        e.g., 1.0 for 100%).
    pct_reduction_commute_vmt : float, optional
        Percent reduction in commute VMT for eligible employees (as a decimal).
        Default is -0.12 (-12%), per Shoup 1997 cash-out study literature.

    Returns
    -------
    float
        Percent reduction in GHG emissions from employee commute VMT
        (as a decimal). Capped at -0.12 (-12%). Negative values indicate
        reductions.
    """
    a = pct_employees_eligible * pct_reduction_commute_vmt
    return max(a, -0.12)


# ==============================================================================
# PARKING MANAGEMENT SUBSECTOR (Project/Site)
# Measures T-14, T-15, T-16
# Subsector cap: 35% (across T-14 through T-16)
# ==============================================================================

@register_measure(
    measure_id="T-14",
    name="Provide Electric Vehicle Charging Infrastructure",
    subsector="parking_management",
    scale=_PS,
    location_types={_U, _S, _R},
    measure_max=0.119,
)
def t14_provide_ev_charging_infrastructure(
        num_chargers,
        total_vehicles_per_day,
        avg_phevs_served_per_charger_per_day=2,
        pct_phev_miles_electric_without_measure=0.46,
        pct_phev_miles_electric_with_measure=0.80,
        phev_gasoline_emission_factor=205.1,
        ev_energy_efficiency_kwh_per_mile=0.327,
        electricity_carbon_intensity=0.0,
        fleet_emission_factor=307.5):
    """Measure T-14: Provide Electric Vehicle Charging Infrastructure.
    Installs Level 2 or DC fast chargers at the project site so plug-in hybrid
    (PHEV) employees can charge and drive more miles in electric mode, reducing
    net GHG per mile. Net benefit depends on local grid carbon intensity.
    Applies to vehicles accessing the project site.

    Formula: A = [B * D * (F - E) * (G - H * I * 454 * 0.001)] / (-C * J)

    Parameters
    ----------
    num_chargers : int
        Number of EV chargers installed at the site.
    total_vehicles_per_day : int
        Total vehicles accessing the site per day.
    avg_phevs_served_per_charger_per_day : int, optional
        Average number of PHEVs served per charger per day. Default is 2
        (Dmax = 7; CARB 2021 PHEV utilisation data).
    pct_phev_miles_electric_without_measure : float, optional
        Percent of PHEV miles driven in electric mode without chargers (decimal).
        Default is 0.46 (46%), per CARB 2020 PHEV usage study.
    pct_phev_miles_electric_with_measure : float, optional
        Percent of PHEV miles driven in electric mode with chargers (decimal).
        Default is 0.80 (80%), per CARB 2020 PHEV usage study.
    phev_gasoline_emission_factor : float, optional
        Average emission factor of PHEV in gasoline mode [g CO2e/mile].
        Default is 205.1 (CARB EMFAC 2021).
    ev_energy_efficiency_kwh_per_mile : float, optional
        Energy efficiency of PHEV in electric mode [kWh/mile].
        Default is 0.327 (EPA 2021 PHEV average).
    electricity_carbon_intensity : float, optional
        Carbon intensity of local electricity provider [lb CO2e/MWh].
        Default is 0.0 (conservative zero-carbon assumption; replace with
        utility-specific value from CARB Tables E-4.3/E-4.4).
    fleet_emission_factor : float, optional
        Average emission factor of non-electric vehicles at site [g CO2e/mile].
        Default is 307.5 (CARB EMFAC 2021 statewide light-duty fleet).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicles accessing the site
        (as a decimal). Capped at -0.119 (-11.9%). Negative values indicate
        reductions; positive values indicate net increase (dirty grid).
    """
    # Electricity emission equivalent [g CO2e/mile in electric mode]
    lb_to_g = 454 # Constant conversion factor
    kw_to_mw = .001 # Constant conversion factor
    electricity_emission_rate = (ev_energy_efficiency_kwh_per_mile
                                 * electricity_carbon_intensity * lb_to_g * kw_to_mw)
    net_emission_factor_diff = phev_gasoline_emission_factor - electricity_emission_rate
    numerator = (num_chargers * avg_phevs_served_per_charger_per_day
                 * (pct_phev_miles_electric_with_measure
                    - pct_phev_miles_electric_without_measure)
                 * net_emission_factor_diff)
    denominator = -total_vehicles_per_day * fleet_emission_factor
    a = numerator / denominator
    return max(a, -0.119)


@register_measure(
    measure_id="T-15",
    name="Limit Residential Parking Supply",
    subsector="parking_management",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.137,
    land_use_types={_RES},
)
def t15_limit_residential_parking_supply(
        residential_parking_demand,
        project_parking_supply,
        pct_project_vmt_from_residents=1.0,
        pct_household_vmt_commute=0.37,
        pct_reduction_commute_mode_share=0.37):
    """Measure T-15: Limit Residential Parking Supply.
    Reduces VMT by providing fewer parking spaces than demand, discouraging
    vehicle ownership and encouraging alternative modes. Applies only when
    supply is below ITE-estimated demand. Applies to resident vehicles at site.

    Formula: A = -((B - C) / B) * D * E * F

    Parameters
    ----------
    residential_parking_demand : float
        Residential parking demand estimated per ITE standards [spaces].
    project_parking_supply : float
        Actual project parking supply [spaces]. Must be less than demand
        to claim a reduction.
    pct_project_vmt_from_residents : float, optional
        Percent of project VMT generated by residents (as a decimal).
        Default is 1.0 (100%) for pure residential projects.
    pct_household_vmt_commute : float, optional
        Percent of household VMT that is commute-based (as a decimal).
        Default is 0.37 (37%), per NHTS 2017.
    pct_reduction_commute_mode_share : float, optional
        Percent reduction in commute mode share by driving in areas with
        constrained parking (as a decimal). Default is 0.37 (37%),
        per Weinberger et al. 2010.

    Returns
    -------
    float
        Percent reduction in GHG emissions from resident vehicles at the site
        (as a decimal). Capped at -0.137 (-13.7%). Returns 0.0 if supply
        meets or exceeds demand. Negative values indicate reductions.
    """
    if project_parking_supply >= residential_parking_demand:
        return 0.0
    a = (-((residential_parking_demand - project_parking_supply)
           / residential_parking_demand)
         * pct_project_vmt_from_residents
         * pct_household_vmt_commute
         * pct_reduction_commute_mode_share)
    return max(a, -0.137)


@register_measure(
    measure_id="T-16",
    name="Unbundle Residential Parking Costs from Property Cost",
    subsector="parking_management",
    scale=_PS,
    location_types={_U, _S},
    measure_max=0.157,
    land_use_types={_RES},
)
def t16_unbundle_residential_parking_costs(
        annual_parking_cost_per_space,
        avg_annual_vehicle_cost=9282.0,
        elasticity_vehicle_ownership=-0.4,
        adjustment_ownership_to_vmt=1.01):
    """Measure T-16: Unbundle Residential Parking Costs from Property Cost.
    Charges residents separately for parking rather than including it in rent
    or purchase price, reducing vehicle ownership and associated VMT.
    Annual parking cost is capped at $3,600/year ($300/month) per CAPCOA.
    Applies to project VMT in the study area.

    Formula: A = (B / C) * D * E

    Parameters
    ----------
    annual_parking_cost_per_space : float
        Annual parking cost charged per space [$]. Capped at $3,600/year
        ($300/month) in the formula per CAPCOA guidance.
    avg_annual_vehicle_cost : float, optional
        Average annual total vehicle cost [$/year]. Default is $9,282
        (AAA 2019 average annual cost of vehicle ownership).
    elasticity_vehicle_ownership : float, optional
        Elasticity of vehicle ownership with respect to total vehicle cost.
        Default is -0.4 (Litman 2020).
    adjustment_ownership_to_vmt : float, optional
        Adjustment factor from vehicle ownership to VMT. Default is 1.01
        (accounts for slightly higher VMT per additional vehicle owned).

    Returns
    -------
    float
        Percent reduction in GHG emissions from project VMT (as a decimal).
        Capped at -0.157 (-15.7%). Negative values indicate reductions.
    """
    capped_cost = min(annual_parking_cost_per_space, 3600.0)
    a = (capped_cost / avg_annual_vehicle_cost) * elasticity_vehicle_ownership * adjustment_ownership_to_vmt
    return max(a, -0.157)


# ==============================================================================
# LAND USE SUBSECTOR (Plan/Community)
# Measure T-17
# Subsector cap: 30%
# ==============================================================================

@register_measure(
    measure_id="T-17",
    name="Improve Street Connectivity",
    subsector="land_use",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.30,
)
def t17_improve_street_connectivity(
        proposed_intersection_density,
        avg_intersection_density=36.0,
        elasticity_vmt_intersection_density=-0.14):
    """Measure T-17: Improve Street Connectivity.
    Increases street grid intersection density to reduce block sizes, shortening
    trip distances and enabling non-motorised mode shift. Higher connectivity
    correlates with lower per-capita VMT.
    Applies to vehicle travel in the plan/community.

    Formula: A = ((B - C) / C) * D

    Parameters
    ----------
    proposed_intersection_density : float
        Intersection density in the project area with the measure
        [intersections/sq mile].
    avg_intersection_density : float, optional
        Baseline average intersection density [intersections/sq mile].
        Default is 36 (FHWA 2017 national average for urbanised areas).
    elasticity_vmt_intersection_density : float, optional
        Elasticity of VMT with respect to intersection density. Default is -0.14
        (Ewing & Cervero 2010; 0.14% decrease in VMT per 1% density increase).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.30 (-30%). Negative values
        indicate reductions.
    """
    a = ((proposed_intersection_density - avg_intersection_density)
         / avg_intersection_density) * elasticity_vmt_intersection_density
    return max(a, -0.30)


# ==============================================================================
# NEIGHBORHOOD DESIGN SUBSECTOR (Plan/Community)
# Measures T-18, T-20, T-21-A, T-21-B, T-22-A, T-22-B, T-22-C, T-22-D
# Subsector cap: 10% (across T-18 through T-22-D)
# ==============================================================================

@register_measure(
    measure_id="T-18",
    name="Provide Pedestrian Network Improvement",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S, _R},
    measure_max=0.064,
)
def t18_provide_pedestrian_network_improvement(
        existing_sidewalk_length,
        proposed_sidewalk_length,
        elasticity_vmt_sidewalk_ratio=-0.05):
    """Measure T-18: Provide Pedestrian Network Improvement.
    Extends sidewalk coverage within a 0.6-mile study area radius, encouraging
    walking in place of short vehicle trips. Sidewalk length is measured on
    both sides of the street.
    Applies to household vehicle travel in the plan/community.

    Formula: A = (C / B - 1) * D

    Parameters
    ----------
    existing_sidewalk_length : float
        Existing total sidewalk length in the study area [miles].
    proposed_sidewalk_length : float
        Total sidewalk length with the measure [miles]. Must exceed existing.
    elasticity_vmt_sidewalk_ratio : float, optional
        Elasticity of household VMT with respect to the sidewalk-to-street
        ratio. Default is -0.05 (Ewing & Cervero 2010; 0.05% decrease in VMT
        per 1% increase in sidewalk coverage ratio).

    Returns
    -------
    float
        Percent reduction in GHG emissions from household vehicle travel
        (as a decimal). Capped at -0.064 (-6.4%). Negative values indicate
        reductions.
    """
    a = (proposed_sidewalk_length / existing_sidewalk_length - 1) * elasticity_vmt_sidewalk_ratio
    return max(a, -0.064)


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
    measure_id="T-22-C",
    name="Implement Scootershare Program",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0007,
)
def t22c_implement_scootershare(
        pct_residences_with_access_with_measure,
        pct_residences_with_access_without_measure=0.0,
        daily_scootershare_trips_per_person=0.021,
        vehicle_to_scootershare_substitution_rate=0.385,
        scootershare_avg_oneway_trip_length=2.14,
        daily_vehicle_trips_per_person=2.7,
        regional_avg_oneway_vehicle_trip_length=9.72):
    """Measure T-22-C: Implement Scootershare Program.
    Deploys shared scooters (docked or dockless) accessible to residents for
    short trips, replacing vehicle trips within the community. Does not account
    for electricity to charge scooters or staff rebalancing vehicle trips
    (conservative estimate). Applies to vehicle travel in the plan/community.

    Formula: A = -1 * ((C - B) * D * E * F) / (G * H)

    Access is measured as the percent of residences within 0.25-mile of a
    scootershare station; for dockless scooters, all residences within
    0.25-mile of the designated dockless service area are considered to have
    access.

    Parameters
    ----------
    pct_residences_with_access_with_measure : float
        (C) Percent of residences in plan/community with access to scootershare
        WITH the measure (as a decimal, e.g., 0.50 for 50%). Range 0-1.
        User input.
    pct_residences_with_access_without_measure : float, optional
        (B) Percent of residences in plan/community with access to scootershare
        WITHOUT the measure (as a decimal). Range 0-1. Default is 0.0.
        User input.
    daily_scootershare_trips_per_person : float, optional
        (D) Daily scootershare trips per person in locations with access
        [trips/day/person]. Default is 0.021, the low (conservative) end of
        the 21-25 bikeshare trips per 1,000 residents range reported for
        San Francisco Bay Area service areas (MTC 2017); bikeshare data used
        due to lack of scootershare-specific data.
    vehicle_to_scootershare_substitution_rate : float, optional
        (E) Fraction of scootershare trips that substitute for vehicle trips
        (as a decimal). Default is 0.385 (38.5%), the average car-trip
        substitution rate found in a literature review of scootershare
        programs in Santa Monica, Minneapolis, San Francisco, and Portland
        (McQueen et al. 2020).
    scootershare_avg_oneway_trip_length : float, optional
        (F) Scootershare average one-way trip length [miles per trip].
        Default is 2.14, from Portland's scootershare pilot data dashboard
        (PBOT 2021).
    daily_vehicle_trips_per_person : float, optional
        (G) Daily vehicle trips per person [trips/day/person]. Default is 2.7,
        the U.S. average from the 2017 National Household Travel Survey
        summary report (FHWA 2018).
    regional_avg_oneway_vehicle_trip_length : float, optional
        (H) Regional average one-way vehicle trip length [miles per trip].
        Ideally calculated for the plan/community at a scale no larger than a
        census tract (U.S. Census, California Household Travel Survey
        preferred, or local survey). If unavailable, use the regional average
        for one of the six most populated CBSAs in California from Table
        T-10.1 in Appendix C (FHWA 2017); trip lengths are likely longer
        outside the listed CBSAs. Default is 9.72 (Los Angeles CBSA).

    Returns
    -------
    float
        (A) Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.0007 (-0.07%). Negative
        values indicate reductions.
    """
    a = (-1 * ((pct_residences_with_access_with_measure
                - pct_residences_with_access_without_measure)
               * daily_scootershare_trips_per_person
               * vehicle_to_scootershare_substitution_rate
               * scootershare_avg_oneway_trip_length)
         / (daily_vehicle_trips_per_person * regional_avg_oneway_vehicle_trip_length))
    return max(a, -0.0007)

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


@register_measure(
    measure_id="T-21-A",
    name="Implement Conventional Carshare Program",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0015,
)
def t21a_implement_conventional_carshare(
        num_carshare_vehicles,
        total_vmt_plan_community,
        conventional_vmt_avoided_per_vehicle=68.2,
        conventional_vmt_added_per_vehicle=24.4):
    """Measure T-21-A: Implement Conventional Carshare Program.
    Deploys a carshare fleet in the community so residents can access vehicles
    on demand without owning one, reducing personal vehicle ownership and VMT.
    Net VMT avoided per carshare vehicle reflects displaced personal vehicles
    minus the additional carshare vehicle trips induced.
    Applies to vehicle travel in the plan/community.

    Formula: A = (B * (E - D)) / C

    Parameters
    ----------
    num_carshare_vehicles : int
        Number of conventional carshare vehicles deployed in the plan/community.
    total_vmt_plan_community : float
        Total daily VMT in the plan/community without the measure [VMT/day].
    conventional_vmt_avoided_per_vehicle : float, optional
        Conventional personal-vehicle VMT avoided per carshare vehicle per day
        [VMT/day/vehicle]. Default is 68.2 (UC Berkeley CarSharing Study 2010).
    conventional_vmt_added_per_vehicle : float, optional
        Additional VMT generated by the carshare vehicle itself per day
        [VMT/day/vehicle]. Default is 24.4 (UC Berkeley CarSharing Study 2010).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.0015 (-0.15%). Negative
        values indicate reductions.
    """
    a = (num_carshare_vehicles
         * (conventional_vmt_added_per_vehicle - conventional_vmt_avoided_per_vehicle)
         / total_vmt_plan_community)
    return max(a, -0.0015)


@register_measure(
    measure_id="T-21-B",
    name="Implement Electric Carshare Program",
    subsector="neighborhood_design",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.0018,
)
def t21b_implement_electric_carshare(
        num_ev_carshare_vehicles,
        total_vmt_plan_community,
        conventional_vmt_avoided_per_ev=54.8,
        electric_vmt_added_per_ev=13.7,
        fleet_emission_factor=307.5,
        ev_energy_efficiency_kwh_per_mile=0.327,
        electricity_carbon_intensity=0.0):
    """Measure T-21-B: Implement Electric Carshare Program.
    Deploys electric carshare vehicles, combining the vehicle-ownership-
    reduction benefit of carsharing with the lower per-mile emissions of EVs.
    Net GHG benefit accounts for electricity grid carbon intensity.
    Applies to vehicle travel in the plan/community.

    Formula: A = B * ((E * G * H * 454 * 0.001) - (D * F)) / (C * F)

    Parameters
    ----------
    num_ev_carshare_vehicles : int
        Number of electric carshare vehicles deployed in the plan/community.
    total_vmt_plan_community : float
        Total daily VMT in the plan/community without the measure [VMT/day].
    conventional_vmt_avoided_per_ev : float, optional
        Personal-vehicle VMT avoided per EV carshare vehicle per day
        [VMT/day/vehicle]. Default is 54.8 (UC Berkeley CarSharing Study 2010).
    electric_vmt_added_per_ev : float, optional
        EV carshare VMT added per vehicle per day [VMT/day/vehicle].
        Default is 13.7 (UC Berkeley CarSharing Study 2010).
    fleet_emission_factor : float, optional
        Emission factor of non-electric light-duty fleet [g CO2e/mile].
        Default is 307.5 (CARB EMFAC 2021).
    ev_energy_efficiency_kwh_per_mile : float, optional
        Energy efficiency of the EV carshare vehicle [kWh/mile].
        Default is 0.327 (EPA 2021 EV average).
    electricity_carbon_intensity : float, optional
        Carbon intensity of local electricity [lb CO2e/MWh].
        Default is 0.0 (conservative zero-carbon; replace with utility value
        from CARB Tables E-4.3/E-4.4).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.0018 (-0.18%). Negative
        values indicate reductions.
    """
    # GHG from EV carshare miles [g CO2e/day per vehicle]
    ev_emissions = (electric_vmt_added_per_ev * ev_energy_efficiency_kwh_per_mile
                    * electricity_carbon_intensity * 454 * 0.001)
    # GHG avoided from displaced personal vehicles [g CO2e/day per vehicle]
    avoided_emissions = conventional_vmt_avoided_per_ev * fleet_emission_factor
    a = (num_ev_carshare_vehicles * (ev_emissions - avoided_emissions)
         / (total_vmt_plan_community * fleet_emission_factor))
    return max(a, -0.0018)



# ==============================================================================
# TRIP REDUCTION PROGRAMS SUBSECTOR (Plan/Community)
# Measure T-23
# Subsector cap: 2.3% commute VMT
# ==============================================================================

@register_measure(
    measure_id="T-23",
    name="Provide Community-Based Travel Planning",
    subsector="trip_reduction",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.023,
    land_use_types={_RES},
)
def t23_provide_community_based_travel_planning(
        total_residences,
        targeted_residences,
        pct_targeted_residences_participating=0.19,
        pct_vehicle_trip_reduction=-0.12,
        adjustment_trips_to_vmt=1.0):
    """Measure T-23: Provide Community-Based Travel Planning.
    Delivers personalised travel planning to targeted households, encouraging
    residents to switch from driving to walking, cycling, or transit for some
    trips. Applies to household vehicle travel in the plan/community.

    Formula: A = (C / B) * D * E * F

    Parameters
    ----------
    total_residences : int
        Total number of residences in the plan/community.
    targeted_residences : int
        Number of residences targeted with the community-based travel
        planning programme.
    pct_targeted_residences_participating : float, optional
        Percent of targeted residences that actively participate (as a decimal).
        Default is 0.19 (19%), per Socialdata 2003 Perth TravelSmart study.
    pct_vehicle_trip_reduction : float, optional
        Percent reduction in vehicle trips by participating residences
        (as a decimal). Default is -0.12 (-12%), per Socialdata 2003.
    adjustment_trips_to_vmt : float, optional
        Adjustment factor from vehicle trip reduction to VMT reduction.
        Default is 1.0 (assumes all trip lengths are equal).

    Returns
    -------
    float
        Percent reduction in GHG emissions from household vehicle travel in
        the plan/community (as a decimal). Capped at -0.023 (-2.3%). Negative
        values indicate reductions.
    """
    a = ((targeted_residences / total_residences)
         * pct_targeted_residences_participating
         * pct_vehicle_trip_reduction
         * adjustment_trips_to_vmt)
    return max(a, -0.023)


# ==============================================================================
# PARKING MANAGEMENT SUBSECTOR (Plan/Community)
# Measure T-24
# Subsector cap: 30%
# ==============================================================================

@register_measure(
    measure_id="T-24",
    name="Implement Market Price Public Parking (On-Street)",
    subsector="parking_management",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.30,
)
def t24_implement_market_price_public_parking(
        vmt_in_priced_area,
        total_vmt_plan_community,
        proposed_parking_price,
        initial_parking_price,
        pct_trips_parking_on_street,
        elasticity_parking_demand=-0.4,
        ratio_vmt_to_vehicle_trips=1.0):
    """Measure T-24: Implement Market Price Public Parking (On-Street).
    Prices on-street public parking at market rates to manage demand, reducing
    cruising for parking and discouraging driving for destinations in the
    priced area. Price increase over initial price is uncapped in the formula
    (market-rate pricing can be substantial).
    Applies to vehicle travel in the plan/community.

    Formula: A = (B / C) * ((D - E) / E) * F * G * H

    Parameters
    ----------
    vmt_in_priced_area : float
        Daily VMT generated within the priced parking area [VMT/day].
    total_vmt_plan_community : float
        Total daily VMT in the plan/community [VMT/day].
    proposed_parking_price : float
        Proposed on-street parking price [$/hour]. Typical range $1–$5/hr.
    initial_parking_price : float
        Initial (current) parking price [$/hour]. If zero (free parking),
        the formula uses E = proposed_parking_price / 2 per CAPCOA guidance.
    pct_trips_parking_on_street : float
        Fraction of vehicle trips that park on-street in the priced area
        (as a decimal). Typical range 0.05–0.75.
    elasticity_parking_demand : float, optional
        Elasticity of parking demand with respect to price. Default is -0.4
        (Shoup 2005).
    ratio_vmt_to_vehicle_trips : float, optional
        Adjustment from vehicle trip reduction to VMT reduction. Default is 1.0.

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.30 (-30%). Negative values
        indicate reductions.
    """
    effective_initial = (initial_parking_price if initial_parking_price > 0
                         else proposed_parking_price / 2)
    a = ((vmt_in_priced_area / total_vmt_plan_community)
         * ((proposed_parking_price - effective_initial) / effective_initial)
         * pct_trips_parking_on_street
         * elasticity_parking_demand
         * ratio_vmt_to_vehicle_trips)
    return max(a, -0.30)


# ==============================================================================
# TRANSIT SUBSECTOR (Plan/Community)
# Measures T-25, T-26, T-27, T-28, T-29, T-46
# Subsector cap: 15% (across T-25 through T-29, T-46)
# IMPORTANT: T-28 (BRT) is mutually exclusive with T-26, T-27, and T-46
# when BRT covers all transit routes. Use excluded_measure_ids in the
# subsector orchestrator to enforce this.
# ==============================================================================

@register_measure(
    measure_id="T-25",
    name="Extend Transit Network Coverage or Hours",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.046,
)
def t25_extend_transit_network_coverage_or_hours(
        existing_transit_service,
        proposed_transit_service,
        transit_mode_share,
        elasticity_transit_demand_service=0.7,
        statewide_mode_shift_factor=0.578,
        ratio_vmt_to_vehicle_trips=1.0):
    """Measure T-25: Extend Transit Network Coverage or Hours.
    Expands transit service by adding new routes, extending route coverage, or
    increasing operating hours, making transit accessible to more riders.
    Does not account for increased transit vehicle emissions (conservative).
    Applies to vehicle travel in the plan/community.

    Formula: A = -1 * ((C - B) / B) * D * E * F * G

    Parameters
    ----------
    existing_transit_service : float
        Total transit service miles or hours in the plan/community before
        expansion [miles or hours/day]. Use consistent units with proposed.
    proposed_transit_service : float
        Total transit service miles or hours after expansion. Must exceed
        existing to claim a reduction.
    transit_mode_share : float
        Transit mode share in the plan/community (as a decimal). From FHWA
        2017 NHTS Table T-3.1 by CBSA (e.g., 0.1138 for SF-Oakland CBSA).
    elasticity_transit_demand_service : float, optional
        Elasticity of transit demand with respect to service miles/hours.
        Default is 0.7 (Litman 2020; 0.7% ridership increase per 1% service
        increase).
    statewide_mode_shift_factor : float, optional
        Statewide average fraction of new transit trips that displace vehicle
        trips (1 / average vehicle occupancy). Default is 0.578 (CARB 2020).
    ratio_vmt_to_vehicle_trips : float, optional
        Adjustment from vehicle trip reduction to VMT reduction. Default is 1.0.

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.046 (-4.6%). Negative
        values indicate reductions.
    """
    a = (-1 * ((proposed_transit_service - existing_transit_service)
               / existing_transit_service)
         * transit_mode_share
         * elasticity_transit_demand_service
         * statewide_mode_shift_factor
         * ratio_vmt_to_vehicle_trips)
    return max(a, -0.046)


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


@register_measure(
    measure_id="T-29",
    name="Reduce Transit Fares",
    subsector="transit",
    scale=_PC,
    location_types={_U, _S},
    measure_max=0.012,
)
def t29_reduce_transit_fares(
        pct_fare_reduction,
        pct_routes_with_reduced_fares,
        transit_mode_share,
        vehicle_mode_share,
        elasticity_transit_ridership_fare=-0.3,
        statewide_mode_shift_factor=0.578):
    """Measure T-29: Reduce Transit Fares.
    Lowers transit fares on some or all routes to increase ridership and
    attract new riders from private vehicles, reducing community VMT.
    Fare reduction is capped at 50% (Bmax) per CAPCOA guidance.
    Applies to vehicle travel in the plan/community.

    Formula: A = (B * C * D * E * G) / F

    Parameters
    ----------
    pct_fare_reduction : float
        Percent reduction in transit fare (as a decimal, e.g., 0.50 for 50%).
        Capped at 0.50 (50%) in the formula per CAPCOA guidance.
    pct_routes_with_reduced_fares : float
        Percent of plan/community transit routes receiving reduced fares
        (as a decimal, e.g., 1.0 for 100% of routes).
    transit_mode_share : float
        Transit mode share in the plan/community (as a decimal). From FHWA
        2017 NHTS Table T-3.1 by CBSA.
    vehicle_mode_share : float
        Vehicle mode share in the plan/community (as a decimal). From FHWA
        2017 NHTS Table T-3.1 by CBSA.
    elasticity_transit_ridership_fare : float, optional
        Elasticity of transit ridership with respect to transit fare.
        Default is -0.3 (Litman 2020; 0.3% ridership increase per 1% fare
        decrease).
    statewide_mode_shift_factor : float, optional
        Statewide average fraction of new transit trips displacing vehicle
        trips. Default is 0.578 (CARB 2020).

    Returns
    -------
    float
        Percent reduction in GHG emissions from vehicle travel in the
        plan/community (as a decimal). Capped at -0.012 (-1.2%). Negative
        values indicate reductions.
    """
    capped_fare_reduction = min(pct_fare_reduction, 0.50)
    a = (capped_fare_reduction
         * pct_routes_with_reduced_fares
         * elasticity_transit_ridership_fare
         * transit_mode_share
         * statewide_mode_shift_factor
         / vehicle_mode_share)
    return max(a, -0.012)


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
