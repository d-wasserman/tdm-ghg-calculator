"""Integration tests for TDM GHG context, registry, and subsector orchestration.

Tests the integration of TDMContext with registry filtering, call_measure parameter
matching, multiplicative_dampening, and all subsector orchestrators. These are
separate from the per-strategy unit tests in test_tdm_calcs.py.
"""

from math import isclose

import pytest

import tdm_ghg
from tdm_ghg import (
    MULTI_SUBSECTOR_CAP,
    SUBSECTOR_CAPS,
    LandUseType,
    LocationType,
    Scale,
    TDMContext,
    multiplicative_dampening,
    registry,
    run_land_use,
    run_multi_subsector,
    run_neighborhood_design,
    run_parking_management,
    run_school_programs,
    run_subsector,
    run_transit,
    run_trip_reduction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(scale, location_type, land_use_type, **params):
    return TDMContext(
        scale=scale,
        location_type=location_type,
        land_use_type=land_use_type,
        params=params,
    )


# ---------------------------------------------------------------------------
# TDMContext creation and enum values
# ---------------------------------------------------------------------------


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

    def test_params_default_to_empty_dict(self):
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.SUBURBAN,
            land_use_type=LandUseType.COMMERCIAL,
        )
        assert ctx.params == {}

    def test_params_stored_correctly(self):
        params = {"proposed_residential_density": 20.0, "transit_mode_share": 0.05}
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params=params,
        )
        assert ctx.params["proposed_residential_density"] == 20.0
        assert ctx.params["transit_mode_share"] == 0.05

    def test_scale_enum_string_values(self):
        assert Scale.PROJECT_SITE == "project_site"
        assert Scale.PLAN_COMMUNITY == "plan_community"

    def test_location_type_enum_string_values(self):
        assert LocationType.URBAN == "urban"
        assert LocationType.SUBURBAN == "suburban"
        assert LocationType.RURAL == "rural"

    def test_land_use_type_enum_string_values(self):
        assert LandUseType.RESIDENTIAL == "residential"
        assert LandUseType.COMMERCIAL == "commercial"
        assert LandUseType.MIXED == "mixed"
        assert LandUseType.SCHOOL == "school"

    def test_scale_is_str_enum(self):
        assert isinstance(Scale.PROJECT_SITE, str)

    def test_different_contexts_are_independent(self):
        ctx1 = TDMContext(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                          params={"a": 1})
        ctx2 = TDMContext(Scale.PLAN_COMMUNITY, LocationType.RURAL, LandUseType.SCHOOL,
                          params={"b": 2})
        assert ctx1.scale != ctx2.scale
        assert ctx1.location_type != ctx2.location_type
        assert ctx1.params != ctx2.params


# ---------------------------------------------------------------------------
# Registry: get and filter
# ---------------------------------------------------------------------------


class TestRegistryGet:

    def test_get_known_measure_returns_metadata(self):
        meta = registry.get("T-1")
        assert meta is not None
        assert meta.measure_id == "T-1"
        assert meta.name == "Increase Residential Density"
        assert meta.subsector == "land_use"
        assert meta.scale == Scale.PROJECT_SITE

    def test_get_unknown_measure_returns_none(self):
        assert registry.get("T-999") is None
        assert registry.get("") is None

    def test_measures_property_is_nonempty_dict(self):
        measures = registry.measures
        assert isinstance(measures, dict)
        assert len(measures) > 0

    def test_measures_contains_expected_ids(self):
        measures = registry.measures
        for mid in ("T-1", "T-2", "T-3", "T-4", "T-55", "T-17", "T-18"):
            assert mid in measures, f"Expected {mid} in registry"

    def test_measures_property_returns_copy(self):
        m1 = registry.measures
        m2 = registry.measures
        assert m1 is not m2  # should be different dict objects


class TestRegistryFilter:

    def test_filter_project_site_scale_only(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        for meta in registry.filter(ctx):
            assert meta.scale == Scale.PROJECT_SITE

    def test_filter_plan_community_scale_only(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL)
        for meta in registry.filter(ctx):
            assert meta.scale == Scale.PLAN_COMMUNITY

    def test_scales_are_disjoint(self):
        ctx_ps = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        ctx_pc = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL)
        ps_ids = {m.measure_id for m in registry.filter(ctx_ps)}
        pc_ids = {m.measure_id for m in registry.filter(ctx_pc)}
        assert len(ps_ids & pc_ids) == 0

    def test_urban_residential_includes_t1(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        ids = {m.measure_id for m in registry.filter(ctx)}
        assert "T-1" in ids

    def test_rural_excludes_t1(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.RURAL, LandUseType.RESIDENTIAL)
        ids = {m.measure_id for m in registry.filter(ctx)}
        assert "T-1" not in ids

    def test_residential_excludes_t2(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        ids = {m.measure_id for m in registry.filter(ctx)}
        assert "T-2" not in ids

    def test_commercial_includes_t2(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL)
        ids = {m.measure_id for m in registry.filter(ctx)}
        assert "T-2" in ids

    def test_commercial_excludes_t1(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL)
        ids = {m.measure_id for m in registry.filter(ctx)}
        assert "T-1" not in ids

    def test_t3_applies_to_all_location_types(self):
        for loc in (LocationType.URBAN, LocationType.SUBURBAN, LocationType.RURAL):
            ctx = _ctx(Scale.PROJECT_SITE, loc, LandUseType.RESIDENTIAL)
            ids = {m.measure_id for m in registry.filter(ctx)}
            assert "T-3" in ids, f"T-3 missing for {loc}"

    def test_filter_by_subsector_returns_only_that_subsector(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        for meta in registry.filter(ctx, subsector="land_use"):
            assert meta.subsector == "land_use"

    def test_filter_by_subsector_trip_reduction(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL)
        for meta in registry.filter(ctx, subsector="trip_reduction"):
            assert meta.subsector == "trip_reduction"

    def test_filter_excluded_ids_removes_measure(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        all_ids = {m.measure_id for m in registry.filter(ctx, subsector="land_use")}
        assert "T-1" in all_ids

        filtered = {m.measure_id for m in registry.filter(ctx, subsector="land_use",
                                                           excluded_ids={"T-1"})}
        assert "T-1" not in filtered
        assert "T-3" in filtered  # T-3 still present

    def test_school_measures_absent_for_non_school_land_use(self):
        for lu in (LandUseType.RESIDENTIAL, LandUseType.COMMERCIAL, LandUseType.MIXED):
            ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, lu)
            ids = {m.measure_id for m in registry.filter(ctx, subsector="school_programs")}
            assert len(ids) == 0, f"Unexpected school measures for land_use={lu}: {ids}"

    def test_school_measures_present_for_school_land_use(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.SCHOOL)
        ids = {m.measure_id for m in registry.filter(ctx, subsector="school_programs")}
        assert "T-40" in ids
        assert "T-56" in ids

    def test_neighborhood_design_only_in_plan_community(self):
        ctx_ps = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        assert registry.filter(ctx_ps, subsector="neighborhood_design") == []

        ctx_pc = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL)
        nd_ids = {m.measure_id for m in registry.filter(ctx_pc, subsector="neighborhood_design")}
        assert len(nd_ids) > 0

    def test_t23_only_for_residential(self):
        ctx_res = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL)
        ctx_com = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.COMMERCIAL)
        res_ids = {m.measure_id for m in registry.filter(ctx_res, subsector="trip_reduction")}
        com_ids = {m.measure_id for m in registry.filter(ctx_com, subsector="trip_reduction")}
        assert "T-23" in res_ids
        assert "T-23" not in com_ids


# ---------------------------------------------------------------------------
# Registry: call_measure parameter dispatch
# ---------------------------------------------------------------------------


class TestRegistryCallMeasure:

    def test_call_with_required_param_returns_float(self):
        meta = registry.get("T-1")
        result = registry.call_measure(meta, {"proposed_residential_density": 20.0})
        assert isinstance(result, float)
        assert result < 0

    def test_call_missing_required_param_returns_none(self):
        meta = registry.get("T-1")
        assert registry.call_measure(meta, {}) is None

    def test_call_uses_function_defaults_for_optional_params(self):
        meta = registry.get("T-1")
        # Provide only the required arg; defaults: typical=9.1, elasticity=-0.22
        result = registry.call_measure(meta, {"proposed_residential_density": 20.0})
        expected = ((20.0 - 9.1) / 9.1) * -0.22  # = -0.26352...
        assert isclose(result, expected, rel_tol=1e-3)

    def test_call_t17_with_required_param(self):
        meta = registry.get("T-17")
        result = registry.call_measure(meta, {"proposed_intersection_density": 60.0})
        # ((60 - 36) / 36) * -0.14 = -0.09333
        expected = ((60.0 - 36.0) / 36.0) * -0.14
        assert isclose(result, expected, rel_tol=1e-3)

    def test_call_t3_with_required_params(self):
        meta = registry.get("T-3")
        result = registry.call_measure(meta, {
            "transit_mode_share": 0.04,
            "vehicle_mode_share": 0.90,
        })
        assert result is not None
        assert result < 0

    def test_call_ignores_irrelevant_extra_params(self):
        meta = registry.get("T-1")
        result = registry.call_measure(meta, {
            "proposed_residential_density": 20.0,
            "unrelated_param_xyz": 999,
            "another_extra": "foo",
        })
        assert result is not None
        assert result < 0

    def test_call_t18_with_sidewalk_params(self):
        meta = registry.get("T-18")
        result = registry.call_measure(meta, {
            "existing_sidewalk_length": 100.0,
            "proposed_sidewalk_length": 150.0,
        })
        # (150/100 - 1) * -0.05 = 0.5 * -0.05 = -0.025
        assert isclose(result, -0.025, rel_tol=1e-3)

    def test_call_t23_missing_total_residences_returns_none(self):
        meta = registry.get("T-23")
        # total_residences and targeted_residences are required
        result = registry.call_measure(meta, {"targeted_residences": 1000})
        assert result is None

    def test_call_t23_with_required_params(self):
        meta = registry.get("T-23")
        result = registry.call_measure(meta, {
            "total_residences": 40000,
            "targeted_residences": 10000,
        })
        # (10000/40000) * 0.19 * -0.12 * 1.0 = -0.0057
        assert isclose(result, -0.0057, rel_tol=1e-2)

    def test_call_t16_with_required_param(self):
        meta = registry.get("T-16")
        result = registry.call_measure(meta, {"annual_parking_cost_per_space": 1000.0})
        # (1000 / 9282) * -0.4 * 1.01 ≈ -0.04353
        assert result is not None
        assert result < 0


# ---------------------------------------------------------------------------
# Multiplicative dampening utility
# ---------------------------------------------------------------------------


class TestMultiplicativeDampening:

    def test_empty_list_returns_zero(self):
        assert multiplicative_dampening([]) == 0.0

    def test_single_reduction_no_cap(self):
        result = multiplicative_dampening([-0.10])
        assert isclose(result, -0.10, rel_tol=1e-6)

    def test_single_reduction_within_cap(self):
        result = multiplicative_dampening([-0.10], max_reduction_percentage=-0.20)
        assert isclose(result, -0.10, rel_tol=1e-6)

    def test_single_reduction_exceeds_cap(self):
        result = multiplicative_dampening([-0.30], max_reduction_percentage=-0.20)
        assert isclose(result, -0.20, rel_tol=1e-6)

    def test_two_reductions_formula(self):
        # Formula uses negative inputs: 1 - (1-r1)(1-r2) with rᵢ negative
        # 1 - (1-(-0.10)) * (1-(-0.20)) = 1 - 1.10*1.20 = 1 - 1.32 = -0.32
        result = multiplicative_dampening([-0.10, -0.20])
        assert isclose(result, -0.32, rel_tol=1e-4)

    def test_three_reductions_formula(self):
        # 1 - 1.10 * 1.15 * 1.20 = 1 - 1.518 = -0.518
        result = multiplicative_dampening([-0.10, -0.15, -0.20])
        assert isclose(result, -0.518, rel_tol=1e-3)

    def test_cap_limits_combined_large_reductions(self):
        result = multiplicative_dampening([-0.40, -0.35, -0.30], max_reduction_percentage=-0.65)
        assert abs(result) <= 0.65 + 1e-9

    def test_result_is_negative_for_all_negative_inputs(self):
        result = multiplicative_dampening([-0.05, -0.10, -0.08])
        assert result < 0

    def test_zero_value_in_list_is_neutral(self):
        result_without_zero = multiplicative_dampening([-0.10])
        result_with_zero = multiplicative_dampening([-0.10, 0.0])
        assert isclose(result_without_zero, result_with_zero, rel_tol=1e-6)

    def test_cap_none_means_no_cap(self):
        # With no cap, a large single reduction should pass through
        result = multiplicative_dampening([-0.80])
        assert isclose(result, -0.80, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Subsector cap constants
# ---------------------------------------------------------------------------


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

    def test_cap_values_are_positive_fractions(self):
        for key, val in SUBSECTOR_CAPS.items():
            assert 0 < val <= 1.0, f"Cap {key} out of range: {val}"

    def test_multi_subsector_cap_is_70_percent(self):
        assert MULTI_SUBSECTOR_CAP == 0.70

    def test_project_site_land_use_cap(self):
        assert SUBSECTOR_CAPS[("project_site", "land_use")] == 0.65

    def test_plan_community_neighborhood_design_cap(self):
        assert SUBSECTOR_CAPS[("plan_community", "neighborhood_design")] == 0.10

    def test_project_site_school_programs_cap(self):
        assert SUBSECTOR_CAPS[("project_site", "school_programs")] == 0.72


# ---------------------------------------------------------------------------
# run_subsector generic orchestrator
# ---------------------------------------------------------------------------


class TestRunSubsector:

    def test_no_params_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        assert run_subsector(ctx, "land_use") == 0.0

    def test_single_measure_result_correct(self):
        # T-17 via plan/community land_use with only intersection density
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   proposed_intersection_density=60.0)
        result = run_subsector(ctx, "land_use")
        expected = ((60.0 - 36.0) / 36.0) * -0.14  # = -0.09333
        assert isclose(result, expected, rel_tol=1e-3)

    def test_result_negative_when_measures_apply(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0)
        result = run_subsector(ctx, "land_use")
        assert result < 0

    def test_subsector_cap_enforced(self):
        # Use extreme params that would exceed the 65% land_use project cap
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=500.0,
                   transit_mode_share=0.25,
                   vehicle_mode_share=0.60,
                   pct_multifamily_units_affordable=1.0)
        result = run_subsector(ctx, "land_use")
        assert abs(result) <= 0.65 + 1e-9

    def test_excluded_ids_reduces_result(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0,
                   transit_mode_share=0.04,
                   vehicle_mode_share=0.90)
        result_all = run_subsector(ctx, "land_use")
        result_no_t1 = run_subsector(ctx, "land_use", excluded_measure_ids={"T-1"})
        # Excluding a measure with negative reduction should make the combined
        # reduction smaller in magnitude (or equal if cap was hit)
        assert abs(result_all) >= abs(result_no_t1) - 1e-9

    def test_wrong_scale_returns_zero(self):
        # Trip reduction measures are project/site; use plan/community context
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.COMMERCIAL,
                   pct_employees_eligible=0.90)
        # No plan/community trip_reduction measures apply (T-23 is residential-only)
        result = run_subsector(ctx, "trip_reduction")
        assert result == 0.0

    def test_plan_community_neighborhood_design(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=150.0)
        result = run_subsector(ctx, "neighborhood_design")
        assert isclose(result, -0.025, rel_tol=1e-3)

    def test_unknown_subsector_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0)
        result = run_subsector(ctx, "nonexistent_subsector")
        assert result == 0.0


# ---------------------------------------------------------------------------
# run_land_use
# ---------------------------------------------------------------------------


class TestRunLandUse:

    def test_residential_urban_t1_fires(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0)
        result = run_land_use(ctx)
        expected = ((20.0 - 9.1) / 9.1) * -0.22
        assert isclose(result, expected, rel_tol=1e-3)

    def test_commercial_urban_no_t1(self):
        # T-1 is residential-only; same param should give 0 for commercial
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   proposed_residential_density=20.0)
        assert run_land_use(ctx) == 0.0

    def test_commercial_t2_fires(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   proposed_job_density=300.0)
        result = run_land_use(ctx)
        expected = ((300.0 - 145.0) / 145.0) * -0.07
        assert isclose(result, expected, rel_tol=1e-3)

    def test_plan_community_t17_fires(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   proposed_intersection_density=80.0)
        result = run_land_use(ctx)
        expected = ((80.0 - 36.0) / 36.0) * -0.14
        assert isclose(result, expected, rel_tol=1e-3)

    def test_result_within_project_land_use_cap(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=500.0,
                   transit_mode_share=0.25,
                   vehicle_mode_share=0.60)
        assert abs(run_land_use(ctx)) <= 0.65 + 1e-9

    def test_result_within_plan_community_land_use_cap(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   proposed_intersection_density=500.0)
        assert abs(run_land_use(ctx)) <= 0.30 + 1e-9

    def test_rural_no_t1_but_t3_applies(self):
        # Rural context: T-1 excluded by location_type, T-3 still included
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.RURAL, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0,
                   transit_mode_share=0.04,
                   vehicle_mode_share=0.90)
        result = run_land_use(ctx)
        # T-3 should fire (applies to rural); T-1 should not
        assert result < 0


# ---------------------------------------------------------------------------
# run_neighborhood_design
# ---------------------------------------------------------------------------


class TestRunNeighborhoodDesign:

    def test_project_site_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=200.0)
        assert run_neighborhood_design(ctx) == 0.0

    def test_plan_community_t18_sidewalk(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=150.0)
        result = run_neighborhood_design(ctx)
        assert isclose(result, -0.025, rel_tol=1e-3)

    def test_cap_at_10_percent(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=150.0,
                   num_carshare_vehicles=50,
                   total_vmt_plan_community=1_000_000.0,
                   conventional_vmt_avoided_per_vehicle=68.2,
                   conventional_vmt_added_per_vehicle=24.4)
        result = run_neighborhood_design(ctx)
        assert result < 0
        assert abs(result) <= 0.10 + 1e-9

    def test_no_params_returns_zero(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL)
        assert run_neighborhood_design(ctx) == 0.0

    def test_rural_context_t18_applies(self):
        # T-18 has location_types={URBAN, SUBURBAN, RURAL}
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.RURAL, LandUseType.RESIDENTIAL,
                   existing_sidewalk_length=50.0,
                   proposed_sidewalk_length=75.0)
        result = run_neighborhood_design(ctx)
        assert result < 0


# ---------------------------------------------------------------------------
# run_trip_reduction
# ---------------------------------------------------------------------------


class TestRunTripReduction:

    def test_project_site_with_eligible_employees(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   pct_employees_eligible=0.80)
        result = run_trip_reduction(ctx)
        assert result < 0
        assert abs(result) <= 0.45 + 1e-9

    def test_plan_community_residential_t23(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   total_residences=40000,
                   targeted_residences=10000)
        result = run_trip_reduction(ctx)
        # (10000/40000) * 0.19 * -0.12 * 1.0 = -0.0057
        assert isclose(result, -0.0057, rel_tol=1e-2)

    def test_plan_community_t23_within_023_cap(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   total_residences=100,
                   targeted_residences=100)
        result = run_trip_reduction(ctx)
        assert abs(result) <= 0.023 + 1e-9

    def test_plan_community_commercial_no_t23(self):
        # T-23 is residential-only; commercial plan/community gives 0
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.COMMERCIAL,
                   total_residences=40000,
                   targeted_residences=10000)
        assert run_trip_reduction(ctx) == 0.0

    def test_project_site_cap_at_45_percent(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   pct_employees_eligible=1.0,
                   pct_reduction_vehicle_mode_share=-0.26)
        result = run_trip_reduction(ctx)
        assert abs(result) <= 0.45 + 1e-9


# ---------------------------------------------------------------------------
# run_transit
# ---------------------------------------------------------------------------


class TestRunTransit:

    def test_project_site_returns_zero(self):
        # Transit measures are all plan/community
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   existing_transit_service=100.0,
                   proposed_transit_service=200.0,
                   transit_mode_share=0.1138)
        assert run_transit(ctx) == 0.0

    def test_no_params_returns_zero(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED)
        assert run_transit(ctx) == 0.0

    def test_plan_community_with_t25_params(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   existing_transit_service=100.0,
                   proposed_transit_service=200.0,
                   transit_mode_share=0.1138)
        result = run_transit(ctx, use_brt=False)
        assert result < 0
        assert abs(result) <= 0.15 + 1e-9

    def test_brt_and_non_brt_both_within_cap(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   existing_transit_service=100.0,
                   proposed_transit_service=200.0,
                   transit_mode_share=0.10)
        result_no_brt = run_transit(ctx, use_brt=False)
        result_brt = run_transit(ctx, use_brt=True)
        assert abs(result_no_brt) <= 0.15 + 1e-9
        assert abs(result_brt) <= 0.15 + 1e-9

    def test_rural_no_transit_measures(self):
        # Check if rural context excludes transit measures that require urban/suburban
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.RURAL, LandUseType.MIXED,
                   existing_transit_service=100.0,
                   proposed_transit_service=200.0,
                   transit_mode_share=0.05)
        result = run_transit(ctx)
        # Result depends on which transit measures allow rural; just verify it's bounded
        assert abs(result) <= 0.15 + 1e-9


# ---------------------------------------------------------------------------
# run_parking_management
# ---------------------------------------------------------------------------


class TestRunParkingManagement:

    def test_project_site_residential_t16(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   annual_parking_cost_per_space=1000.0)
        result = run_parking_management(ctx)
        # (min(1000,3600)/9282) * -0.4 * 1.01 ≈ -0.04353
        assert result < 0
        assert abs(result) <= 0.35 + 1e-9

    def test_project_site_cap_at_35_percent(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   annual_parking_cost_per_space=5000.0,   # capped at 3600 internally
                   residential_parking_demand=100,
                   project_parking_supply=0,
                   num_chargers=500,
                   total_vehicles_per_day=10)
        result = run_parking_management(ctx)
        assert abs(result) <= 0.35 + 1e-9

    def test_no_params_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        assert run_parking_management(ctx) == 0.0

    def test_commercial_land_use_no_t15_t16(self):
        # T-15 and T-16 are residential-only
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   annual_parking_cost_per_space=1000.0,
                   residential_parking_demand=50,
                   project_parking_supply=10)
        # No residential parking measures apply; result comes from T-14 if params match
        result = run_parking_management(ctx)
        # T-14 needs num_chargers, total_vehicles_per_day; those aren't provided → 0
        assert result == 0.0

    def test_t14_ev_chargers_fires_for_any_land_use(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                   num_chargers=10,
                   total_vehicles_per_day=80)
        result = run_parking_management(ctx)
        assert result < 0


# ---------------------------------------------------------------------------
# run_school_programs
# ---------------------------------------------------------------------------


class TestRunSchoolPrograms:

    def test_non_school_land_use_returns_zero(self):
        for lu in (LandUseType.RESIDENTIAL, LandUseType.COMMERCIAL, LandUseType.MIXED):
            ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, lu,
                       pct_students_who_begin_riding_bus=0.30,
                       pct_students_served_by_bus=0.80)
            result = run_school_programs(ctx)
            assert result == 0.0, f"Expected 0 for land_use={lu}, got {result}"

    def test_plan_community_scale_returns_zero(self):
        # School programs are project/site only
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.SCHOOL,
                   pct_students_who_begin_riding_bus=0.30,
                   pct_students_served_by_bus=0.80)
        assert run_school_programs(ctx) == 0.0

    def test_school_land_use_no_params_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.SCHOOL)
        assert run_school_programs(ctx) == 0.0

    def test_school_land_use_with_t40_params(self):
        # Use an efficient bus (800 g/mi) so it beats per-student car emissions
        # car: 350/1.58=221.5 g/student, bus: 3.42*800/14.9=183.6 g/student → net reduction
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.SCHOOL,
                   pct_students_who_begin_riding_bus=0.30,
                   pct_students_served_by_bus=0.80,
                   light_duty_emission_factor=350.0,
                   school_bus_emission_factor=800.0)
        result = run_school_programs(ctx)
        assert result < 0
        assert abs(result) <= 0.72 + 1e-9


# ---------------------------------------------------------------------------
# run_multi_subsector — cross-subsector combination
# ---------------------------------------------------------------------------


class TestRunMultiSubsector:

    def test_no_params_returns_zero(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL)
        assert run_multi_subsector(ctx) == 0.0

    def test_residential_urban_project_site_scenario(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0,
                   transit_mode_share=0.04,
                   vehicle_mode_share=0.90,
                   pct_multifamily_units_affordable=0.20,
                   annual_parking_cost_per_space=1500.0)
        result = run_multi_subsector(ctx)
        assert result < 0
        assert abs(result) <= MULTI_SUBSECTOR_CAP + 1e-9

    def test_plan_community_mixed_scenario(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   proposed_intersection_density=60.0,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=150.0)
        result = run_multi_subsector(ctx)
        assert result < 0
        assert abs(result) <= MULTI_SUBSECTOR_CAP + 1e-9

    def test_multi_subsector_at_least_as_large_as_land_use(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=20.0,
                   transit_mode_share=0.04,
                   vehicle_mode_share=0.90)
        land = run_land_use(ctx)
        multi = run_multi_subsector(ctx)
        assert abs(multi) >= abs(land) - 1e-9

    def test_use_brt_flag_respected(self):
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   existing_sidewalk_length=100.0,
                   proposed_sidewalk_length=150.0)
        result_no_brt = run_multi_subsector(ctx, use_brt=False)
        result_brt = run_multi_subsector(ctx, use_brt=True)
        assert abs(result_no_brt) <= MULTI_SUBSECTOR_CAP + 1e-9
        assert abs(result_brt) <= MULTI_SUBSECTOR_CAP + 1e-9

    def test_combined_cap_70_percent_maximum(self):
        # Load all residential project/site params to push toward cap
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=500.0,
                   transit_mode_share=0.25,
                   vehicle_mode_share=0.60,
                   pct_multifamily_units_affordable=1.0,
                   annual_parking_cost_per_space=5000.0,
                   residential_parking_demand=100,
                   project_parking_supply=0,
                   num_chargers=200,
                   total_vehicles_per_day=50)
        result = run_multi_subsector(ctx)
        assert abs(result) <= MULTI_SUBSECTOR_CAP + 1e-9

    def test_single_subsector_result_propagates(self):
        # Only T-17 params provided in plan/community context
        ctx = _ctx(Scale.PLAN_COMMUNITY, LocationType.URBAN, LandUseType.MIXED,
                   proposed_intersection_density=60.0)
        land = run_land_use(ctx)
        multi = run_multi_subsector(ctx)
        # With no other subsector contributions, multi == land
        assert isclose(multi, land, rel_tol=1e-6)

    def test_suburban_context_scenario(self):
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.SUBURBAN, LandUseType.RESIDENTIAL,
                   proposed_residential_density=15.0,
                   transit_mode_share=0.02,
                   vehicle_mode_share=0.92)
        result = run_multi_subsector(ctx)
        assert result < 0
        assert abs(result) <= MULTI_SUBSECTOR_CAP + 1e-9


# ---------------------------------------------------------------------------
# End-to-end context filtering correctness
# ---------------------------------------------------------------------------


class TestContextFilteringCorrectness:

    def test_t55_infill_excluded_when_t1_t3_present(self):
        # T-55 is mutually exclusive with T-1 and T-3 per CAPCOA
        ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                   proposed_project_distance_to_downtown=4.0,
                   conventional_development_distance_to_downtown=10.0,
                   proposed_residential_density=20.0,
                   transit_mode_share=0.04,
                   vehicle_mode_share=0.90)
        # When using T-55, T-1 and T-3 should be excluded
        result_t55_only = run_subsector(ctx, "land_use",
                                         excluded_measure_ids={"T-1", "T-3"})
        assert abs(result_t55_only) <= 0.65 + 1e-9

    def test_residential_land_use_excludes_t4_for_commercial(self):
        ctx_res = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.RESIDENTIAL,
                       pct_multifamily_units_affordable=0.20)
        ctx_com = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, LandUseType.COMMERCIAL,
                       pct_multifamily_units_affordable=0.20)
        # T-4 is residential-only; commercial context should give 0
        res_result = run_land_use(ctx_res)
        com_result = run_land_use(ctx_com)
        assert res_result < 0
        assert com_result == 0.0

    def test_each_measure_metadata_has_valid_measure_max(self):
        for mid, meta in registry.measures.items():
            assert meta.measure_max > 0, f"{mid} has non-positive measure_max"
            assert meta.measure_max <= 1.0, f"{mid} has measure_max > 1"

    def test_each_measure_metadata_has_func(self):
        for mid, meta in registry.measures.items():
            assert callable(meta.func), f"{mid} func is not callable"

    def test_mutually_exclusive_metadata_stored(self):
        meta_t1 = registry.get("T-1")
        assert "T-55" in meta_t1.mutually_exclusive_with

        meta_t55 = registry.get("T-55")
        assert "T-1" in meta_t55.mutually_exclusive_with
        assert "T-3" in meta_t55.mutually_exclusive_with

    def test_location_types_are_frozensets(self):
        for mid, meta in registry.measures.items():
            assert isinstance(meta.location_types, frozenset), \
                f"{mid} location_types is not frozenset"

    def test_land_use_types_none_means_all_land_uses(self):
        # T-3 has no land_use restriction — should appear in all land use contexts
        for lu in (LandUseType.RESIDENTIAL, LandUseType.COMMERCIAL,
                   LandUseType.MIXED, LandUseType.SCHOOL):
            ctx = _ctx(Scale.PROJECT_SITE, LocationType.URBAN, lu)
            ids = {m.measure_id for m in registry.filter(ctx)}
            assert "T-3" in ids, f"T-3 missing for land_use={lu}"
