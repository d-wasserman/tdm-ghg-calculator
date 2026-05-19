"""Unit tests for tdm-calcs library."""

import numpy as np
import pytest
from math import isclose
import tdm_ghg

# ---- Constants ----


class TestMitigations:
    def test_t1_increase_residential_density_strategy(self):
        """Test the residential density strategy."""
        # Mock the input data
        proposed_residential_density = 16
        typical_residential_density = 9.1
        elasticity_vmt_residential_density = -0.22
        # Expected result based on the mock data
        expected_result = -0.166

        # Call the function under test
        result = tdm_ghg.mitigations.t1_increase_residential_density(
            proposed_residential_density,
            typical_residential_density,
            elasticity_vmt_residential_density,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t2_increase_job_density_strategy(self):
        """Test the job density strategy."""
        # Mock the input data
        proposed_job_density = 500
        typical_job_density = 145
        elasticity_vmt_job_density = -0.07
        # Expected result based on the mock data
        expected_result = -0.171

        # Call the function under test
        result = tdm_ghg.mitigations.t2_increase_job_density(
            proposed_job_density, typical_job_density, elasticity_vmt_job_density
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t3_provide_tod_strategy(self):
        """Test the tod strategy."""
        # Mock the input data
        transit_mode_share = .04
        auto_mode_share = .9
        ratio = 4.9
        # Expected result based on the mock data
        expected_result = -0.217

        # Call the function under test
        result = tdm_ghg.mitigations.t3_provide_transit_oriented_development(
            transit_mode_share, auto_mode_share, ratio
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t4_integrate_affordable_housing(self):
        """Test the affordable housing strategy."""
        # Mock the input data
        pct_multifamily_units_affordable = 0.2
        vmt_reduction_per_qualified_unit = -0.286
        # Expected result based on the mock data
        expected_result = -.0572

        # Call the function under test
        result = tdm_ghg.mitigations.t4_integrate_affordable_housing(
            pct_multifamily_units_affordable,
            vmt_reduction_per_qualified_unit,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t5_implement_voluntary_commute_trip_reduction(self):
        """Test the voluntary CTR program strategy."""
        # Mock the input data
        pct_employees_eligible = .88
        pct_reduction_commute_vmt = -0.04
        # Expected result based on the mock data
        expected_result = -0.0352

        # Call the function under test
        result = tdm_ghg.mitigations.t5_implement_voluntary_commute_trip_reduction(
            pct_employees_eligible,
            pct_reduction_commute_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t6_implement_mandatory_commute_trip_reduction(self):
        """Test the mandatory CTR program strategy."""
        # Mock the input data
        pct_employees_eligible = .85
        pct_reduction_vehicle_mode_share = -0.26
        adjustment_vehicle_mode_to_vmt = 1.0
        # Expected result based on the mock data
        expected_result = -0.221

        # Call the function under test
        result = tdm_ghg.mitigations.t6_implement_mandatory_commute_trip_reduction(
            pct_employees_eligible,
            pct_reduction_vehicle_mode_share,
            adjustment_vehicle_mode_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t7_implement_commute_trip_reduction_marketing(self):
        """Test the CTR marketing strategy."""
        # Mock the input data
        pct_employees_eligible = .7
        pct_reduction_vehicle_trips = -0.04
        adjustment_vehicle_trips_to_vmt = 1.0
        # Expected result based on the mock data
        expected_result = -0.028

        # Call the function under test
        result = tdm_ghg.mitigations.t7_implement_commute_trip_reduction_marketing(
            pct_employees_eligible,
            pct_reduction_vehicle_trips,
            adjustment_vehicle_trips_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t8_provide_ridesharing_program(self):
        """Test the ridesharing program strategy."""
        # Mock the input data
        pct_employees_eligible = 0.60
        pct_reduction_commute_vmt = -0.08  # urban place type, SANDAG 2019
        # Expected result based on the mock data
        expected_result = -0.048

        # Call the function under test
        result = tdm_ghg.mitigations.t8_provide_ridesharing_program(
            pct_employees_eligible,
            pct_reduction_commute_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t9_implement_subsidized_transit_program(self):
        """Test the subsidized transit program strategy."""
        # Mock the input data (SF-Oakland CBSA handbook example)
        transit_fare = 100.0
        subsidy_amount =  80
        pct_eligible = .95
        pct_project_vmt_from_employees = .8
        transit_mode_share = 0.2  # SF-Oakland-Hayward CBSA work trips
        elasticity_transit_boardings_fare = -0.43
        pct_transit_replacing_vehicle = 0.50
        conversion_vehicle_trips_to_vmt = 1.0
        # Expected result based on the mock data
        expected_result = -0.026144


        # Call the function under test
        result = tdm_ghg.mitigations.t9_implement_subsidized_transit_program(
            transit_fare,
            subsidy_amount,
            pct_eligible,
            pct_project_vmt_from_employees,
            transit_mode_share,
            elasticity_transit_boardings_fare,
            pct_transit_replacing_vehicle,
            conversion_vehicle_trips_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t11_provide_employer_sponsored_vanpool(self):
        """Test the employer-sponsored vanpool strategy."""
        # Mock the input data (handbook Amax example: B=15%, San Diego CBSA)
        pct_employees_vanpooling = 0.027
        avg_vehicle_commute_trip_length = 20
        avg_vanpool_trip_length = 42.0
        avg_vanpool_occupancy = 6.25
        avg_employee_vehicle_emission_factor = 307.5
        vanpool_emission_factor = 763.4
        # Expected result based on the mock data
        expected_result = -0.033192035


        # Call the function under test
        result = tdm_ghg.mitigations.t11_provide_employer_sponsored_vanpool(
            pct_employees_vanpooling,
            avg_vehicle_commute_trip_length,
            avg_vanpool_trip_length,
            avg_vanpool_occupancy,
            avg_employee_vehicle_emission_factor,
            vanpool_emission_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t12_price_workplace_parking(self):
        """Test the price workplace parking strategy."""
        # Mock the input data (50% price increase, 100% employees paying)
        proposed_parking_price = 10
        baseline_parking_price = 8
        share_employees_paying_for_parking = .8
        elasticity_parking_demand = -0.4
        ratio_vehicle_trip_reduction_to_vmt = 1.0
        expected_result = -0.08

        # Call the function under test
        result = tdm_ghg.mitigations.t12_price_workplace_parking(
            proposed_parking_price,
            baseline_parking_price,
            share_employees_paying_for_parking,
            elasticity_parking_demand,
            ratio_vehicle_trip_reduction_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t13_implement_employee_parking_cash_out(self):
        """Test the employee parking cash-out strategy."""
        # Mock the input data (100% eligible, default -12% VMT reduction)
        pct_employees_eligible = .75
        pct_reduction_commute_vmt = -0.12
        # Expected result based on the mock data
        expected_result = -0.09

        # Call the function under test
        result = tdm_ghg.mitigations.t13_implement_employee_parking_cash_out(
            pct_employees_eligible,
            pct_reduction_commute_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t14_provide_ev_charging_infrastructure(self):
        """Test the EV charging infrastructure strategy."""
        # Mock the input data (handbook Amax example: 20 chargers, 200 vehicles, Dmax=7, I=0)
        num_chargers = 10
        total_vehicles_per_day = 80
        avg_phevs_served_per_charger_per_day = 2
        pct_phev_miles_electric_without_measure = 0.46
        pct_phev_miles_electric_with_measure = 0.80
        phev_gasoline_emission_factor = 205.1
        ev_energy_efficiency_kwh_per_mile = 0.327
        electricity_carbon_intensity = 54
        fleet_emission_factor = 307.5
        # Expected result based on the mock data
        expected_result = -0.054478302 

        # Call the function under test
        result = tdm_ghg.mitigations.t14_provide_ev_charging_infrastructure(
            num_chargers,
            total_vehicles_per_day,
            avg_phevs_served_per_charger_per_day,
            pct_phev_miles_electric_without_measure,
            pct_phev_miles_electric_with_measure,
            phev_gasoline_emission_factor,
            ev_energy_efficiency_kwh_per_mile,
            electricity_carbon_intensity,
            fleet_emission_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t15_limit_residential_parking_supply(self):
        """Test the limit residential parking supply strategy."""
        # Mock the input data (supply=0, demand=100, 100% resident VMT)
        residential_parking_demand = 20
        project_parking_supply = 5
        pct_project_vmt_from_residents = .7
        pct_household_vmt_commute = 0.37
        pct_reduction_commute_mode_share = 0.37
        # Expected result: -(100/100)*1.0*0.37*0.37 = -0.1369 (capped at -0.137)
        expected_result = -0.0718725

        # Call the function under test
        result = tdm_ghg.mitigations.t15_limit_residential_parking_supply(
            residential_parking_demand,
            project_parking_supply,
            pct_project_vmt_from_residents,
            pct_household_vmt_commute,
            pct_reduction_commute_mode_share,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t16_unbundle_residential_parking_costs(self):
        """Test the unbundle residential parking costs strategy."""
        # Mock the input data (Bmax=$3,600/yr)
        annual_parking_cost_per_space = 1000
        avg_annual_vehicle_cost = 9282.0
        elasticity_vehicle_ownership = -0.4
        adjustment_ownership_to_vmt = 1.01
        # Expected result: (3600/9282)*-0.4*1.01 = -0.1567
        expected_result = -0.043525102

        # Call the function under test
        result = tdm_ghg.mitigations.t16_unbundle_residential_parking_costs(
            annual_parking_cost_per_space,
            avg_annual_vehicle_cost,
            elasticity_vehicle_ownership,
            adjustment_ownership_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t17_improve_street_connectivity(self):
        """Test the improve street connectivity strategy."""
        # Mock the input data (high connectivity area: 100 intersections/sq mi)
        proposed_intersection_density = 60
        avg_intersection_density = 36.0
        elasticity_vmt_intersection_density = -0.14
        # Expected result: ((100-36)/36)*-0.14 = -0.249
        expected_result = -0.093333333

        # Call the function under test
        result = tdm_ghg.mitigations.t17_improve_street_connectivity(
            proposed_intersection_density,
            avg_intersection_density,
            elasticity_vmt_intersection_density,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t18_provide_pedestrian_network_improvement(self):
        """Test the pedestrian network improvement strategy."""
        # Mock the input data (double existing sidewalk coverage)
        existing_sidewalk_length = 100
        proposed_sidewalk_length = 150
        elasticity_vmt_sidewalk_ratio = -0.05
        # Expected result: (100/50 - 1)*-0.05 = -0.05
        expected_result = -0.025

        # Call the function under test
        result = tdm_ghg.mitigations.t18_provide_pedestrian_network_improvement(
            existing_sidewalk_length,
            proposed_sidewalk_length,
            elasticity_vmt_sidewalk_ratio,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t21a_implement_conventional_carshare(self):
        """Test the conventional carshare program strategy."""
        # Mock the input data
        num_carshare_vehicles = 20
        total_vmt_plan_community = 8000000
        conventional_vmt_avoided_per_vehicle = 68.2
        conventional_vmt_added_per_vehicle = 24.4
        # Expected result based on the mock data
        expected_result = -0.0001095

        # Call the function under test
        result = tdm_ghg.mitigations.t21a_implement_conventional_carshare(
            num_carshare_vehicles,
            total_vmt_plan_community,
            conventional_vmt_avoided_per_vehicle,
            conventional_vmt_added_per_vehicle,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t21b_implement_electric_carshare(self):
        """Test the electric carshare program strategy."""
        # Mock the input data (zero-carbon electricity)
        num_ev_carshare_vehicles = 100
        total_vmt_plan_community = 10000000.0
        conventional_vmt_avoided_per_ev = 54.8
        electric_vmt_added_per_ev = 13.7
        fleet_emission_factor = 307.5
        ev_energy_efficiency_kwh_per_mile = 0.327
        electricity_carbon_intensity = 0.0
        # Expected result based on the mock data
        expected_result = -0.000548

        # Call the function under test
        result = tdm_ghg.mitigations.t21b_implement_electric_carshare(
            num_ev_carshare_vehicles,
            total_vmt_plan_community,
            conventional_vmt_avoided_per_ev,
            electric_vmt_added_per_ev,
            fleet_emission_factor,
            ev_energy_efficiency_kwh_per_mile,
            electricity_carbon_intensity,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t22c_implement_scootershare(self):
        """Test the scootershare program strategy."""
        # Mock the input data
        pct_residences_with_access_with_measure = 0.50
        pct_residences_with_access_without_measure = 0.0
        daily_scootershare_trips_per_person = 0.021
        vehicle_to_scootershare_substitution_rate = 0.385
        scootershare_avg_oneway_trip_length = 2.14
        daily_vehicle_trips_per_person = 2.7
        regional_avg_oneway_vehicle_trip_length = 9.72
        # Expected result based on the mock data
        expected_result = -0.000329635



        # Call the function under test
        result = tdm_ghg.mitigations.t22c_implement_scootershare(
            pct_residences_with_access_with_measure,
            pct_residences_with_access_without_measure,
            daily_scootershare_trips_per_person,
            vehicle_to_scootershare_substitution_rate,
            scootershare_avg_oneway_trip_length,
            daily_vehicle_trips_per_person,
            regional_avg_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t23_provide_community_based_travel_planning(self):
        """Test the community-based travel planning strategy."""
        # Mock the input data (all residences targeted — Amax scenario)
        total_residences = 40000
        targeted_residences = 10000
        pct_targeted_residences_participating = 0.19
        pct_vehicle_trip_reduction = -0.12
        adjustment_trips_to_vmt = 1.0
        expected_result = -0.0057

        # Call the function under test
        result = tdm_ghg.mitigations.t23_provide_community_based_travel_planning(
            total_residences,
            targeted_residences,
            pct_targeted_residences_participating,
            pct_vehicle_trip_reduction,
            adjustment_trips_to_vmt,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t24_implement_market_price_public_parking(self):
        """Test the market price on-street public parking strategy."""
        # Mock the input data (priced area = 50% of community VMT, 2x price, 50% trips park on-street)
        vmt_in_priced_area = 1000000.0
        total_vmt_plan_community = 10000000.0
        proposed_parking_price = 4.0
        initial_parking_price = 2.0
        pct_trips_parking_on_street = 0.25
        elasticity_parking_demand = -0.4 # Assumes loss of vehicle trips
        ratio_vmt_to_vehicle_trips = 1.0
        expected_result = -0.01

        # Call the function under test
        result = tdm_ghg.mitigations.t24_implement_market_price_public_parking(
            vmt_in_priced_area,
            total_vmt_plan_community,
            proposed_parking_price,
            initial_parking_price,
            pct_trips_parking_on_street,
            elasticity_parking_demand,
            ratio_vmt_to_vehicle_trips,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t25_extend_transit_network_coverage_or_hours(self):
        """Test the extend transit network coverage or hours strategy."""
        # Mock the input data (100% service expansion, SF-Oakland CBSA transit mode share)
        existing_transit_service = 300
        proposed_transit_service = 450
        transit_mode_share = 0.2
        elasticity_transit_demand_service = 0.7
        statewide_mode_shift_factor = 0.578
        ratio_vmt_to_vehicle_trips = 1.0
        expected_result = -0.0405
        # Call the function under test
        result = tdm_ghg.mitigations.t25_extend_transit_network_coverage_or_hours(
            existing_transit_service,
            proposed_transit_service,
            transit_mode_share,
            elasticity_transit_demand_service,
            statewide_mode_shift_factor,
            ratio_vmt_to_vehicle_trips,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t29_reduce_transit_fares(self):
        """Test the reduce transit fares strategy."""
        # Mock the input data (50% fare reduction, all routes, San Jose CBSA)
        pct_fare_reduction = 0.4
        pct_routes_with_reduced_fares = .8
        transit_mode_share = 0.15   # San Jose-Sunnyvale-Santa Clara CBSA
        vehicle_mode_share = 0.8
        elasticity_transit_ridership_fare = -0.3
        statewide_mode_shift_factor = 0.578
        # Expected result based on the mock data
        expected_result = -0.010404


        # Call the function under test
        result = tdm_ghg.mitigations.t29_reduce_transit_fares(
            pct_fare_reduction,
            pct_routes_with_reduced_fares,
            transit_mode_share,
            vehicle_mode_share,
            elasticity_transit_ridership_fare,
            statewide_mode_shift_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t55_infill_development(self):
        """Test the infill development strategy."""
        # Mock the input data
        proposed_project_distance_to_downtown = 4
        conventional_development_distance_to_downtown = 10
        elasticity_vmt_distance_to_downtown = -0.22
        # Expected result based on the mock data
        expected_result = -0.132

        # Call the function under test
        result = tdm_ghg.mitigations.t55_infill_development(
            proposed_project_distance_to_downtown,
            conventional_development_distance_to_downtown,
            elasticity_vmt_distance_to_downtown,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t10_provide_end_of_trip_bicycle_facilities(self):
        """Test the end-of-trip bicycle facilities strategy."""
        # Mock the input data
        bike_mode_adjustment_factor = 4.86
        existing_bicycle_trip_length = 2.3
        existing_vehicle_trip_length = 10.5
        existing_bicycle_mode_share_work = 0.02
        existing_vehicle_mode_share_work = 0.85
        # Expected result based on the mock data
        expected_result = -0.01989

        # Call the function under test
        result = tdm_ghg.mitigations.t10_provide_end_of_trip_bicycle_facilities(
            bike_mode_adjustment_factor,
            existing_bicycle_trip_length,
            existing_vehicle_trip_length,
            existing_bicycle_mode_share_work,
            existing_vehicle_mode_share_work,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t20_expand_bikeway_network(self):
        """Test the expand bikeway network strategy."""
        # Mock the input data
        existing_bikeway_miles_in_community = 20.0
        proposed_bikeway_miles_in_community = 100.0
        bike_mode_share = 0.03
        vehicle_mode_share = 0.85
        average_oneway_bicycle_trip_length = 2.3
        average_oneway_vehicle_trip_length = 10.5
        elasticity_of_bike_commuters_per_pop = 0.25
        # Expected result based on the mock data
        expected_result = -0.00773

        # Call the function under test
        result = tdm_ghg.mitigations.t20_expand_bikeway_network(
            existing_bikeway_miles_in_community,
            proposed_bikeway_miles_in_community,
            bike_mode_share,
            vehicle_mode_share,
            average_oneway_bicycle_trip_length,
            average_oneway_vehicle_trip_length,
            elasticity_of_bike_commuters_per_pop,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t22a_implement_pedal_bikeshare(self):
        """Test the pedal bikeshare strategy."""
        # Mock the input data
        pct_residences_with_access_with_measure = 0.8
        pct_residences_with_access_without_measure = 0.0
        daily_bikeshare_trips_per_person = 0.021
        vehicle_to_bikeshare_substitution_rate = 0.196
        bikeshare_avg_oneway_trip_length = 1.4
        daily_vehicle_trips_per_person = 2.7
        regional_avg_oneway_vehicle_trip_length = 9.72
        # Expected result based on the mock data
        expected_result = -0.000175656
        # Call the function under test
        result = tdm_ghg.mitigations.t22a_implement_pedal_bikeshare(
            pct_residences_with_access_with_measure,
            pct_residences_with_access_without_measure,
            daily_bikeshare_trips_per_person,
            vehicle_to_bikeshare_substitution_rate,
            bikeshare_avg_oneway_trip_length,
            daily_vehicle_trips_per_person,
            regional_avg_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t22b_implement_electric_bikeshare(self):
        """Test the electric bikeshare strategy."""
        # Mock the input data
        pct_residences_with_access_with_measure = 0.85
        pct_residences_with_access_without_measure = 0.0
        daily_ebikeshare_trips_per_person = 0.021
        vehicle_to_ebikeshare_substitution_rate = 0.35
        ebikeshare_avg_oneway_trip_length = 2.1
        daily_vehicle_trips_per_person = 2.7
        regional_avg_oneway_vehicle_trip_length = 9.72
        # Expected result based on the mock data
        expected_result = -0.000499914

        # Call the function under test
        result = tdm_ghg.mitigations.t22b_implement_electric_bikeshare(
            pct_residences_with_access_with_measure,
            pct_residences_with_access_without_measure,
            daily_ebikeshare_trips_per_person,
            vehicle_to_ebikeshare_substitution_rate,
            ebikeshare_avg_oneway_trip_length,
            daily_vehicle_trips_per_person,
            regional_avg_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t22c_implement_scootershare(self):
        """Test the scootershare strategy."""
        # Mock the input data
        pct_residences_with_access_with_measure = 0.85
        pct_residences_with_access_without_measure = 0.0
        daily_scootershare_trips_per_person = 0.021
        vehicle_to_scootershare_substitution_rate = 0.385
        scootershare_avg_oneway_trip_length = 2.14
        daily_vehicle_trips_per_person = 2.7
        regional_avg_oneway_vehicle_trip_length = 9.72
        # Expected result based on the mock data
        expected_result = -0.00056

        # Call the function under test
        result = tdm_ghg.mitigations.t22c_implement_scootershare(
            pct_residences_with_access_with_measure,
            pct_residences_with_access_without_measure,
            daily_scootershare_trips_per_person,
            vehicle_to_scootershare_substitution_rate,
            scootershare_avg_oneway_trip_length,
            daily_vehicle_trips_per_person,
            regional_avg_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t22d_transition_conventional_to_electric_bikeshare(self):
        """Test the transition to electric bikeshare strategy."""
        # Mock the input data
        pct_residences_with_traditional_bikeshare_access = 0.85
        pct_bikes_transitioned_to_electric = 0.85
        daily_bikeshare_trips_per_person = 0.021
        vehicle_to_ebikeshare_substitution_rate = 0.35
        ebikeshare_avg_oneway_trip_length = 2.1
        vehicle_to_conventional_bikeshare_substitution_rate = 0.196
        conventional_bikeshare_avg_oneway_trip_length = 1.4
        daily_vehicle_trips_per_person = 1.7
        regional_avg_oneway_vehicle_trip_length = 9.72
        # Expected result based on the mock data
        expected_result = -0.00042292

        # Call the function under test
        result = tdm_ghg.mitigations.t22d_transition_conventional_to_electric_bikeshare(
            pct_residences_with_traditional_bikeshare_access,
            pct_bikes_transitioned_to_electric,
            daily_bikeshare_trips_per_person,
            vehicle_to_ebikeshare_substitution_rate,
            ebikeshare_avg_oneway_trip_length,
            vehicle_to_conventional_bikeshare_substitution_rate,
            conventional_bikeshare_avg_oneway_trip_length,
            daily_vehicle_trips_per_person,
            regional_avg_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t26_increase_transit_service_frequency(self):
        """Test the transit service frequency strategy."""
        # Mock the input data
        pct_increase_in_transit_frequency = 2.0
        level_of_implementation = 0.8
        transit_mode_share = 0.1
        vehicle_mode_share = 0.85
        elasticity_ridership_frequency = 0.5
        statewide_mode_shift_factor = 0.578
        # Expected result based on the mock data
        expected_result = -0.0544

        # Call the function under test
        result = tdm_ghg.mitigations.t26_increase_transit_service_frequency(
            pct_increase_in_transit_frequency,
            level_of_implementation,
            transit_mode_share,
            vehicle_mode_share,
            elasticity_ridership_frequency,
            statewide_mode_shift_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t27_implement_transit_supportive_roadway_treatments(self):
        """Test the transit-supportive roadway treatments strategy."""
        # Mock the input data
        pct_transit_routes_receiving_treatments = 0.30
        transit_mode_share = 0.15
        vehicle_mode_share = 0.8
        pct_change_in_transit_travel_time = -0.10
        elasticity_ridership_travel_time = -0.4
        statewide_mode_shift_factor = 0.578
        # Expected result based on the mock data
        expected_result = -0.0013

        # Call the function under test
        result = tdm_ghg.mitigations.t27_implement_transit_supportive_roadway_treatments(
            pct_transit_routes_receiving_treatments,
            transit_mode_share,
            vehicle_mode_share,
            pct_change_in_transit_travel_time,
            elasticity_ridership_travel_time,
            statewide_mode_shift_factor,
        )
        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t28_provide_bus_rapid_transit(self):
        """Test the bus rapid transit strategy."""
        # Mock the input data
        pct_increase_in_transit_frequency = 2
        level_of_implementation = 0.8
        transit_mode_share = 0.15
        vehicle_mode_share = 0.8
        statewide_mode_shift_factor = 0.578
        pct_ridership_increase_brt_bonus = 0.25
        pct_change_in_transit_travel_time = -0.20
        elasticity_ridership_frequency = 0.5
        elasticity_ridership_travel_time = -0.4
        # Expected result based on the mock data
        expected_result = -0.115311
        # Call the function under test
        result = tdm_ghg.mitigations.t28_provide_bus_rapid_transit(
            pct_increase_in_transit_frequency,
            level_of_implementation,
            transit_mode_share,
            vehicle_mode_share,
            statewide_mode_shift_factor,
            pct_ridership_increase_brt_bonus,
            pct_change_in_transit_travel_time,
            elasticity_ridership_frequency,
            elasticity_ridership_travel_time,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t46_provide_transit_shelters(self):
        """Test the transit shelters strategy."""
        # Mock the input data
        num_stops_with_new_shelters = 20
        avg_boardings_per_day_at_improved_stops = 200.0
        avg_boardings_per_day_across_agency = 12000.0
        transit_mode_share = 0.15
        include_real_time_information = True
        pct_transit_users_who_would_otherwise_drive = 0.833
        avg_auto_occupancy = 1.45
        pct_travel_time_waiting_existing = 0.249
        pct_perceived_waiting_with_shelters = 0.203
        pct_perceived_waiting_with_shelters_and_rti = 0.158
        wait_time_elasticity = -0.54
        # Expected result based on the mock data
        expected_result = -0.000713508

        # Call the function under test
        result = tdm_ghg.mitigations.t46_provide_transit_shelters(
            num_stops_with_new_shelters,
            avg_boardings_per_day_at_improved_stops,
            avg_boardings_per_day_across_agency,
            transit_mode_share,
            include_real_time_information,
            pct_transit_users_who_would_otherwise_drive,
            avg_auto_occupancy,
            pct_travel_time_waiting_existing,
            pct_perceived_waiting_with_shelters,
            pct_perceived_waiting_with_shelters_and_rti,
            wait_time_elasticity,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t40_establish_school_bus_program(self):
        """Test the school bus program strategy."""
        # Mock the input data
        pct_students_who_begin_riding_bus = 0.8
        pct_students_served_by_bus = 0.90
        light_duty_emission_factor = 350.0
        school_bus_emission_factor = 1200.0
        pct_new_riders_who_previously_drove = 0.79
        avg_student_occupancy_cars = 1.58
        avg_student_occupancy_buses = 14.9
        bus_tour_to_driving_distance_ratio = 3.42
        # Expected result based on the mock data
        expected_result = -0.13844472

        # Call the function under test
        result = tdm_ghg.mitigations.t40_establish_school_bus_program(
            pct_students_who_begin_riding_bus,
            pct_students_served_by_bus,
            light_duty_emission_factor,
            school_bus_emission_factor,
            pct_new_riders_who_previously_drove,
            avg_student_occupancy_cars,
            avg_student_occupancy_buses,
            bus_tour_to_driving_distance_ratio,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t56_active_modes_transportation_youth(self):
        """Test the active modes transportation youth strategy."""
        # Mock the input data
        pct_near_students_driven_after_implementation = 0.45
        pct_students_within_2_miles = 0.62
        pct_near_students_driven_before_implementation = 0.51
        pct_far_students_driven = 0.66
        avg_driving_distance_near_students = 2.0
        avg_driving_distance_far_students = 8.66
        # Expected result based on the mock data
        expected_result = -0.02653042

        # Call the function under test
        result = tdm_ghg.mitigations.t56_active_modes_transportation_youth(
            pct_near_students_driven_after_implementation,
            pct_students_within_2_miles,
            pct_near_students_driven_before_implementation,
            pct_far_students_driven,
            avg_driving_distance_near_students,
            avg_driving_distance_far_students,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t19a_construct_or_improve_bike_facility(self):
        """Test the construct/improve bike facility strategy (T-19-A Amax)."""
        # Mock the input data (CAPCOA Amax example: B=100%, Sacramento CBSA,
        # highest C, D, E values from Tables T-19.1–T-19.3, Sacramento County
        # annual days of use from Table T-19.4.)
        pct_community_vmt_on_parallel_roadway = .5
        active_transportation_adjustment_factor = 0.0207
        key_destination_credit = 0.003
        growth_factor_adjustment = 1.54
        annual_days_of_use = 307
        average_oneway_bicycle_trip_length = 2.9
        average_oneway_vehicle_trip_length = 10.9
        # Expected result based on the mock data
        expected_result = -0.00408

        # Call the function under test
        result = tdm_ghg.mitigations.t19a_construct_or_improve_bike_facility(
            pct_community_vmt_on_parallel_roadway,
            active_transportation_adjustment_factor,
            key_destination_credit,
            growth_factor_adjustment,
            annual_days_of_use,
            average_oneway_bicycle_trip_length,
            average_oneway_vehicle_trip_length,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=2e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t19b_construct_or_improve_bike_boulevard(self):
        """Test the construct/improve bike boulevard strategy (T-19-B Amax)."""
        # Mock the input data (CAPCOA Amax example: B=100%, San
        # Jose-Sunnyvale-Santa Clara CBSA defaults from Tables T-10.1/T-10.2.)
        pct_community_vmt_on_roadway = .75
        average_oneway_bicycle_trip_length = 2.8
        average_oneway_vehicle_trip_length = 11.5
        bicycle_mode_share_work_trips = 0.041
        vehicle_mode_share_work_trips = 0.866
        bike_mode_adjustment_factor = 1.14
        # Expected result based on the mock data
        expected_result = -0.001265

        # Call the function under test
        result = tdm_ghg.mitigations.t19b_construct_or_improve_bike_boulevard(
            pct_community_vmt_on_roadway,
            average_oneway_bicycle_trip_length,
            average_oneway_vehicle_trip_length,
            bicycle_mode_share_work_trips,
            vehicle_mode_share_work_trips,
            bike_mode_adjustment_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t30_use_cleaner_fuel_vehicles_bev(self):
        """Test the BEV mode of T-30 (CAPCOA example: 50% fleet conversion,
        renewable electricity provider)."""
        # Mock the input data
        pct_fleett_converted = 0.50
        existing_vehicle_emission_factor = 400.0  # g CO2e/mile
        bev_efficiency_kwh_per_mile = 0.33
        electricity_carbon_intensity = 0.0  # zero-carbon grid
        # Expected result: 0.5 * (0 - 400)/400 = -0.5
        expected_result = -0.50

        # Call the function under test
        result = tdm_ghg.mitigations.t30_use_cleaner_fuel_vehicles(
            pct_fleet_converted,
            existing_vehicle_emission_factor,
            vehicle_type="BEV",
            bev_efficiency_kwh_per_mile=bev_efficiency_kwh_per_mile,
            electricity_carbon_intensity=electricity_carbon_intensity,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t30_use_cleaner_fuel_vehicles_phev(self):
        """Test the PHEV mode of T-30 (50% fleet conversion, renewable grid)."""
        # Mock the input data
        pct_fleet_converted = 0.50
        existing_vehicle_emission_factor = 400.0
        # Expected result: with E=0, A2 = B * ((1/I)*(1-H) - 1) =
        # 0.5 * ((1/1.5)*0.54 - 1) = 0.5 * (0.36 - 1) = -0.32
        expected_result = -0.32

        # Call the function under test
        result = tdm_ghg.mitigations.t30_use_cleaner_fuel_vehicles(
            pct_fleet_converted,
            existing_vehicle_emission_factor,
            vehicle_type="PHEV",
            bev_efficiency_kwh_per_mile=0.33,
            electricity_carbon_intensity=0.0,
            pct_phev_miles_electric=0.46,
            hybrid_to_gasoline_mpg_ratio=1.5,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )

    def test_t30_use_cleaner_fuel_vehicles_wtw(self):
        """Test the well-to-wheels mode of T-30."""
        # Mock the input data (50% fleet, cleaner fuel 100 g/mi vs.
        # conventional 400 g/mi well-to-wheels)
        pct_fleet_converted = 0.50
        existing_vehicle_emission_factor = 400.0  # unused in WTW
        cleaner_fuel_wtw_emission_factor = 100.0
        existing_vehicle_wtw_emission_factor = 400.0
        # Expected result: 0.5 * (100 - 400) / 400 = -0.375
        expected_result = -0.375

        # Call the function under test
        result = tdm_ghg.mitigations.t30_use_cleaner_fuel_vehicles(
            pct_fleet_converted,
            existing_vehicle_emission_factor,
            vehicle_type="WTW",
            cleaner_fuel_wtw_emission_factor=cleaner_fuel_wtw_emission_factor,
            existing_vehicle_wtw_emission_factor=existing_vehicle_wtw_emission_factor,
        )

        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), (
            f"Expected {expected_result}, but got {result}"
        )
