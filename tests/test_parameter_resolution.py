# --------------------------------
# Copyright 2026 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------
"""Tests for parameter-collision handling in subsector orchestration.

Covers two related fixes:

1. Per-measure parameter namespacing (``registry.call_measure``): a
   measure-ID-keyed sub-dict in ``params`` overrides flat values for that
   measure and can scope which measures activate.
2. Mutual-exclusivity enforcement (``run_subsector``): activating mutually
   exclusive measures together raises ``MeasureExclusivityError`` instead of
   silently combining them.
"""

import pytest

from tdm_ghg import (
    LandUseType,
    LocationType,
    MeasureExclusivityError,
    Scale,
    TDMContext,
    registry,
    run_land_use,
    run_subsector,
    run_trip_reduction,
)


def _trip_ctx(params):
    return TDMContext(
        scale=Scale.PROJECT_SITE,
        location_type=LocationType.URBAN,
        land_use_type=LandUseType.RESIDENTIAL,
        params=params,
    )


class TestParameterNamespacing:
    def test_flat_params_still_work(self):
        # Backward compatibility: flat dict resolves required args.
        meta = registry.get("T-1")
        result = registry.call_measure(meta, {"proposed_residential_density": 20.0})
        assert result == pytest.approx(-0.2635, abs=1e-3)

    def test_missing_required_param_returns_none(self):
        meta = registry.get("T-1")
        assert registry.call_measure(meta, {}) is None

    def test_measure_scoped_override_wins_over_flat(self):
        meta = registry.get("T-1")
        params = {
            "proposed_residential_density": 20.0,  # flat -> -0.2635
            "T-1": {"proposed_residential_density": 50.0},  # scoped -> cap -0.30
        }
        assert registry.call_measure(meta, params) == pytest.approx(-0.30)

    def test_scoped_params_alone_can_activate_a_measure(self):
        meta = registry.get("T-1")
        params = {"T-1": {"proposed_residential_density": 20.0}}
        assert registry.call_measure(meta, params) == pytest.approx(-0.2635, abs=1e-3)

    def test_scoped_params_for_other_measure_do_not_activate_this_one(self):
        # A T-6 sub-dict must not leak into T-5 (collision-free activation).
        meta = registry.get("T-5")
        params = {"T-6": {"pct_employees_eligible": 1.0}}
        assert registry.call_measure(meta, params) is None

    def test_scoping_avoids_semantic_conflation(self):
        # transit_mode_share means different things to different measures;
        # each can receive its own value via scoping.
        t3 = registry.get("T-3")
        scoped = {
            "T-3": {"transit_mode_share": 0.10, "vehicle_mode_share": 0.80},
            "transit_mode_share": 0.02,  # flat default for other measures
        }
        flat = {"transit_mode_share": 0.10, "vehicle_mode_share": 0.80}
        assert registry.call_measure(t3, scoped) == pytest.approx(
            registry.call_measure(t3, flat)
        )


class TestExclusivityEnforcement:
    def test_conflicting_flat_param_raises(self):
        # pct_employees_eligible activates T-5, T-6, T-7, T-8 (mutually
        # exclusive) simultaneously.
        ctx = _trip_ctx({"pct_employees_eligible": 1.0})
        with pytest.raises(MeasureExclusivityError):
            run_trip_reduction(ctx)

    def test_error_message_names_the_conflict(self):
        ctx = _trip_ctx({"pct_employees_eligible": 1.0})
        with pytest.raises(MeasureExclusivityError) as exc:
            run_trip_reduction(ctx)
        message = str(exc.value)
        assert "T-5" in message and "T-6" in message
        assert "trip_reduction" in message
        assert "excluded_measure_ids" in message

    def test_excluded_ids_resolve_the_conflict(self):
        # Isolate T-6: exclude the conflicting bundle and T-13 (which also
        # activates from pct_employees_eligible but conflicts only with T-12).
        ctx = _trip_ctx({"pct_employees_eligible": 1.0})
        result = run_trip_reduction(
            ctx, excluded_measure_ids={"T-5", "T-7", "T-8", "T-13"}
        )
        # T-6 alone: 1.0 * -0.26 -> -0.26 (under the 45% cap)
        assert result == pytest.approx(-0.26)

    def test_scoped_params_avoid_the_conflict(self):
        # Scoping activation to T-6 only — no exclusions needed.
        ctx = _trip_ctx({"T-6": {"pct_employees_eligible": 1.0}})
        assert run_trip_reduction(ctx) == pytest.approx(-0.26)

    def test_non_conflicting_measures_do_not_raise(self):
        # T-1, T-3, T-4 all activate but none are mutually exclusive with
        # each other (only with the inactive T-55).
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params={
                "proposed_residential_density": 20.0,
                "transit_mode_share": 0.05,
                "vehicle_mode_share": 0.80,
                "pct_multifamily_units_affordable": 0.5,
            },
        )
        assert run_land_use(ctx) < 0.0  # combines without raising

    def test_t55_conflict_with_t1_and_t3_raises(self):
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params={
                "proposed_residential_density": 20.0,
                "transit_mode_share": 0.05,
                "vehicle_mode_share": 0.80,
                "proposed_project_distance_to_downtown": 2.0,
                "conventional_development_distance_to_downtown": 13.4,
            },
        )
        with pytest.raises(MeasureExclusivityError):
            run_land_use(ctx)

    def test_t55_conflict_resolved_by_excluding_t1_t3(self):
        ctx = TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params={
                "proposed_residential_density": 20.0,
                "transit_mode_share": 0.05,
                "vehicle_mode_share": 0.80,
                "proposed_project_distance_to_downtown": 2.0,
                "conventional_development_distance_to_downtown": 13.4,
            },
        )
        assert run_land_use(ctx, excluded_measure_ids={"T-1", "T-3"}) < 0.0

    def test_empty_subsector_does_not_raise(self):
        ctx = _trip_ctx({})
        assert run_subsector(ctx, "trip_reduction") == 0.0
