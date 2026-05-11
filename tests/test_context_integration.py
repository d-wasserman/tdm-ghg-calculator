"""Integration tests for TDM GHG context system.

Focused on the integration surface: TDMContext construction, subsector cap
constants, and the run_multi_subsector orchestrator. Per-measure formula
correctness is covered by test_tdm_calcs.py.
"""

from math import isclose

from tdm_ghg import (
    MULTI_SUBSECTOR_CAP,
    SUBSECTOR_CAPS,
    LandUseType,
    LocationType,
    Scale,
    TDMContext,
    run_land_use,
    run_multi_subsector,
)


class TestTDMContextCreation:

    def test_basic_creation_stores_attributes(self):
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
        )
        assert ctx.scale == Scale.PROJECT_SITE
        assert ctx.location_type == LocationType.URBAN
        assert ctx.land_use_type == LandUseType.RESIDENTIAL
        assert ctx.params == {}

    def test_params_stored_correctly(self):
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.SUBURBAN,
            land_use_type=LandUseType.MIXED,
            params={"proposed_residential_density": 20.0, "transit_mode_share": 0.05},
        )
        assert ctx.params["proposed_residential_density"] == 20.0
        assert ctx.params["transit_mode_share"] == 0.05

    def test_enum_string_values(self):
        assert Scale.PROJECT_SITE == "project_site"
        assert Scale.PLAN_COMMUNITY == "plan_community"
        assert LocationType.URBAN == "urban"
        assert LocationType.RURAL == "rural"
        assert LandUseType.RESIDENTIAL == "residential"
        assert LandUseType.SCHOOL == "school"


class TestSubsectorCaps:

    def test_all_expected_caps_defined(self):
        expected = {
            ("project_site", "land_use"),
            ("project_site", "trip_reduction"),
            ("project_site", "parking_management"),
            ("project_site", "school_programs"),
            ("plan_community", "land_use"),
            ("plan_community", "neighborhood_design"),
            ("plan_community", "trip_reduction"),
            ("plan_community", "parking_management"),
            ("plan_community", "transit"),
        }
        for key in expected:
            assert key in SUBSECTOR_CAPS, f"Missing cap for {key}"

    def test_cap_values_match_capcoa(self):
        assert SUBSECTOR_CAPS[("project_site", "land_use")] == 0.65
        assert SUBSECTOR_CAPS[("project_site", "trip_reduction")] == 0.45
        assert SUBSECTOR_CAPS[("project_site", "parking_management")] == 0.35
        assert SUBSECTOR_CAPS[("project_site", "school_programs")] == 0.72
        assert SUBSECTOR_CAPS[("plan_community", "neighborhood_design")] == 0.10
        assert SUBSECTOR_CAPS[("plan_community", "transit")] == 0.15

    def test_multi_subsector_cap_is_70_percent(self):
        assert MULTI_SUBSECTOR_CAP == 0.70


class TestRunMultiSubsector:

    def test_no_params_returns_zero(self):
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
        )
        assert run_multi_subsector(ctx) == 0.0

    def test_combined_result_within_70_percent_cap(self):
        # Push every contributing subsector hard; cross-subsector cap must hold
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params={
                "proposed_residential_density": 500.0,
                "transit_mode_share": 0.25,
                "vehicle_mode_share": 0.60,
                "pct_multifamily_units_affordable": 1.0,
                "annual_parking_cost_per_space": 5000.0,
                "residential_parking_demand": 100,
                "project_parking_supply": 0,
                "num_chargers": 200,
                "total_vehicles_per_day": 50,
            },
        )
        assert abs(run_multi_subsector(ctx)) <= MULTI_SUBSECTOR_CAP + 1e-9

    def test_single_subsector_propagates_to_multi(self):
        # Only T-17 contributes; multi should equal land_use result
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.MIXED,
            params={"proposed_intersection_density": 60.0},
        )
        assert isclose(run_multi_subsector(ctx), run_land_use(ctx), rel_tol=1e-6)

    def test_use_brt_flag_respected(self):
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.MIXED,
            params={
                "existing_sidewalk_length": 100.0,
                "proposed_sidewalk_length": 150.0,
            },
        )
        result_no_brt = run_multi_subsector(ctx, use_brt=False)
        result_brt = run_multi_subsector(ctx, use_brt=True)
        assert abs(result_no_brt) <= MULTI_SUBSECTOR_CAP + 1e-9
        assert abs(result_brt) <= MULTI_SUBSECTOR_CAP + 1e-9
