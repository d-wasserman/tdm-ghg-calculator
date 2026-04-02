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

    # def test_t55_infill_development(self):
    #     """Test the infill development strategy."""
    #     # Mock the input data
    #     proposed_project_distance_to_downtown = 5.0
    #     conventional_development_distance_to_downtown = 13.4
    #     elasticity_vmt_distance_to_downtown = -0.22
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t55_infill_development(
    #         proposed_project_distance_to_downtown,
    #         conventional_development_distance_to_downtown,
    #         elasticity_vmt_distance_to_downtown,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t10_provide_end_of_trip_bicycle_facilities(self):
    #     """Test the end-of-trip bicycle facilities strategy."""
    #     # Mock the input data
    #     bike_mode_adjustment_factor = 4.86
    #     existing_bicycle_trip_length = 2.3
    #     existing_vehicle_trip_length = 10.5
    #     existing_bicycle_mode_share_work = 0.01
    #     existing_vehicle_mode_share_work = 0.85
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t10_provide_end_of_trip_bicycle_facilities(
    #         bike_mode_adjustment_factor,
    #         existing_bicycle_trip_length,
    #         existing_vehicle_trip_length,
    #         existing_bicycle_mode_share_work,
    #         existing_vehicle_mode_share_work,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t20_expand_bikeway_network(self):
    #     """Test the expand bikeway network strategy."""
    #     # Mock the input data
    #     existing_bikeway_miles_in_community = 100.0
    #     proposed_bikeway_miles_in_community = 150.0
    #     bike_mode_share = 0.01
    #     vehicle_mode_share = 0.85
    #     average_oneway_bicycle_trip_length = 2.3
    #     average_oneway_vehicle_trip_length = 10.5
    #     elasticity_of_bike_commuters_per_pop = 0.25
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t20_expand_bikeway_network(
    #         existing_bikeway_miles_in_community,
    #         proposed_bikeway_miles_in_community,
    #         bike_mode_share,
    #         vehicle_mode_share,
    #         average_oneway_bicycle_trip_length,
    #         average_oneway_vehicle_trip_length,
    #         elasticity_of_bike_commuters_per_pop,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t22a_implement_pedal_bikeshare(self):
    #     """Test the pedal bikeshare strategy."""
    #     # Mock the input data
    #     pct_residences_with_access_with_measure = 0.50
    #     pct_residences_with_access_without_measure = 0.0
    #     daily_bikeshare_trips_per_person = 0.021
    #     vehicle_to_bikeshare_substitution_rate = 0.196
    #     bikeshare_avg_oneway_trip_length = 1.4
    #     daily_vehicle_trips_per_person = 2.7
    #     regional_avg_oneway_vehicle_trip_length = 9.72
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t22a_implement_pedal_bikeshare(
    #         pct_residences_with_access_with_measure,
    #         pct_residences_with_access_without_measure,
    #         daily_bikeshare_trips_per_person,
    #         vehicle_to_bikeshare_substitution_rate,
    #         bikeshare_avg_oneway_trip_length,
    #         daily_vehicle_trips_per_person,
    #         regional_avg_oneway_vehicle_trip_length,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t22b_implement_electric_bikeshare(self):
    #     """Test the electric bikeshare strategy."""
    #     # Mock the input data
    #     pct_residences_with_access_with_measure = 0.50
    #     pct_residences_with_access_without_measure = 0.0
    #     daily_ebikeshare_trips_per_person = 0.021
    #     vehicle_to_ebikeshare_substitution_rate = 0.35
    #     ebikeshare_avg_oneway_trip_length = 2.1
    #     daily_vehicle_trips_per_person = 2.7
    #     regional_avg_oneway_vehicle_trip_length = 9.72
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t22b_implement_electric_bikeshare(
    #         pct_residences_with_access_with_measure,
    #         pct_residences_with_access_without_measure,
    #         daily_ebikeshare_trips_per_person,
    #         vehicle_to_ebikeshare_substitution_rate,
    #         ebikeshare_avg_oneway_trip_length,
    #         daily_vehicle_trips_per_person,
    #         regional_avg_oneway_vehicle_trip_length,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t22d_transition_conventional_to_electric_bikeshare(self):
    #     """Test the transition to electric bikeshare strategy."""
    #     # Mock the input data
    #     pct_residences_with_traditional_bikeshare_access = 0.40
    #     pct_bikes_transitioned_to_electric = 0.50
    #     daily_bikeshare_trips_per_person = 0.021
    #     vehicle_to_ebikeshare_substitution_rate = 0.35
    #     ebikeshare_avg_oneway_trip_length = 2.1
    #     vehicle_to_conventional_bikeshare_substitution_rate = 0.196
    #     conventional_bikeshare_avg_oneway_trip_length = 1.4
    #     daily_vehicle_trips_per_person = 1.7
    #     regional_avg_oneway_vehicle_trip_length = 9.72
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t22d_transition_conventional_to_electric_bikeshare(
    #         pct_residences_with_traditional_bikeshare_access,
    #         pct_bikes_transitioned_to_electric,
    #         daily_bikeshare_trips_per_person,
    #         vehicle_to_ebikeshare_substitution_rate,
    #         ebikeshare_avg_oneway_trip_length,
    #         vehicle_to_conventional_bikeshare_substitution_rate,
    #         conventional_bikeshare_avg_oneway_trip_length,
    #         daily_vehicle_trips_per_person,
    #         regional_avg_oneway_vehicle_trip_length,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t26_increase_transit_service_frequency(self):
    #     """Test the transit service frequency strategy."""
    #     # Mock the input data
    #     pct_increase_in_transit_frequency = 1.0
    #     level_of_implementation = 0.75
    #     transit_mode_share = 0.04
    #     vehicle_mode_share = 0.85
    #     elasticity_ridership_frequency = 0.5
    #     statewide_mode_shift_factor = 0.578
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t26_increase_transit_service_frequency(
    #         pct_increase_in_transit_frequency,
    #         level_of_implementation,
    #         transit_mode_share,
    #         vehicle_mode_share,
    #         elasticity_ridership_frequency,
    #         statewide_mode_shift_factor,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t27_implement_transit_supportive_roadway_treatments(self):
    #     """Test the transit-supportive roadway treatments strategy."""
    #     # Mock the input data
    #     pct_transit_routes_receiving_treatments = 0.50
    #     transit_mode_share = 0.04
    #     vehicle_mode_share = 0.85
    #     pct_change_in_transit_travel_time = -0.10
    #     elasticity_ridership_travel_time = -0.4
    #     statewide_mode_shift_factor = 0.578
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t27_implement_transit_supportive_roadway_treatments(
    #         pct_transit_routes_receiving_treatments,
    #         transit_mode_share,
    #         vehicle_mode_share,
    #         pct_change_in_transit_travel_time,
    #         elasticity_ridership_travel_time,
    #         statewide_mode_shift_factor,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t28_provide_bus_rapid_transit(self):
    #     """Test the bus rapid transit strategy."""
    #     # Mock the input data
    #     pct_increase_in_transit_frequency = 1.5
    #     level_of_implementation = 0.60
    #     transit_mode_share = 0.04
    #     vehicle_mode_share = 0.85
    #     statewide_mode_shift_factor = 0.578
    #     pct_ridership_increase_brt_bonus = 0.25
    #     pct_change_in_transit_travel_time = -0.10
    #     elasticity_ridership_frequency = 0.5
    #     elasticity_ridership_travel_time = -0.4
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t28_provide_bus_rapid_transit(
    #         pct_increase_in_transit_frequency,
    #         level_of_implementation,
    #         transit_mode_share,
    #         vehicle_mode_share,
    #         statewide_mode_shift_factor,
    #         pct_ridership_increase_brt_bonus,
    #         pct_change_in_transit_travel_time,
    #         elasticity_ridership_frequency,
    #         elasticity_ridership_travel_time,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t46_provide_transit_shelters(self):
    #     """Test the transit shelters strategy."""
    #     # Mock the input data
    #     num_stops_with_new_shelters = 20
    #     avg_boardings_per_day_at_improved_stops = 50.0
    #     avg_boardings_per_day_across_agency = 25000.0
    #     transit_mode_share = 0.04
    #     include_real_time_information = False
    #     pct_transit_users_who_would_otherwise_drive = 0.833
    #     avg_auto_occupancy = 1.45
    #     pct_travel_time_waiting_existing = 0.249
    #     pct_perceived_waiting_with_shelters = 0.203
    #     pct_perceived_waiting_with_shelters_and_rti = 0.158
    #     wait_time_elasticity = -0.54
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t46_provide_transit_shelters(
    #         num_stops_with_new_shelters,
    #         avg_boardings_per_day_at_improved_stops,
    #         avg_boardings_per_day_across_agency,
    #         transit_mode_share,
    #         include_real_time_information,
    #         pct_transit_users_who_would_otherwise_drive,
    #         avg_auto_occupancy,
    #         pct_travel_time_waiting_existing,
    #         pct_perceived_waiting_with_shelters,
    #         pct_perceived_waiting_with_shelters_and_rti,
    #         wait_time_elasticity,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t40_establish_school_bus_program(self):
    #     """Test the school bus program strategy."""
    #     # Mock the input data
    #     pct_students_who_begin_riding_bus = 0.30
    #     pct_students_served_by_bus = 0.80
    #     light_duty_emission_factor = 350.0
    #     school_bus_emission_factor = 1200.0
    #     pct_new_riders_who_previously_drove = 0.79
    #     avg_student_occupancy_cars = 1.58
    #     avg_student_occupancy_buses = 14.9
    #     bus_tour_to_driving_distance_ratio = 3.42
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t40_establish_school_bus_program(
    #         pct_students_who_begin_riding_bus,
    #         pct_students_served_by_bus,
    #         light_duty_emission_factor,
    #         school_bus_emission_factor,
    #         pct_new_riders_who_previously_drove,
    #         avg_student_occupancy_cars,
    #         avg_student_occupancy_buses,
    #         bus_tour_to_driving_distance_ratio,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )

    # def test_t56_active_modes_transportation_youth(self):
    #     """Test the active modes transportation youth strategy."""
    #     # Mock the input data
    #     pct_near_students_driven_after_implementation = 0.30
    #     pct_students_within_2_miles = 0.62
    #     pct_near_students_driven_before_implementation = 0.51
    #     pct_far_students_driven = 0.66
    #     avg_driving_distance_near_students = 2.0
    #     avg_driving_distance_far_students = 8.66
    #     # Expected result based on the mock data
    #     expected_result = 0

    #     # Call the function under test
    #     result = tdm_ghg.mitigations.t56_active_modes_transportation_youth(
    #         pct_near_students_driven_after_implementation,
    #         pct_students_within_2_miles,
    #         pct_near_students_driven_before_implementation,
    #         pct_far_students_driven,
    #         avg_driving_distance_near_students,
    #         avg_driving_distance_far_students,
    #     )

    #     # Assert that the result matches the expected output
    #     assert isclose(result, expected_result, rel_tol=1e-2), (
    #         f"Expected {expected_result}, but got {result}"
    #     )
