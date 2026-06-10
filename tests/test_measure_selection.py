# --------------------------------
# Copyright 2026 David J. Wasserman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# --------------------------------
"""Tests for explicit measure selection via ``TDMContext.measures``.

When ``measures`` is declared, only the listed strategies run (drawing
values from shared and measure-scoped params), and selection problems raise
``MeasureSelectionError`` instead of being silently skipped. When ``measures``
is ``None``, measures auto-activate from parameter presence (legacy mode).
"""

import pytest

from tdm_ghg import (
    LandUseType,
    LocationType,
    MeasureExclusivityError,
    MeasureSelectionError,
    Scale,
    TDMContext,
    run_land_use,
    run_multi_subsector,
    run_transit,
    run_trip_reduction,
)


def _residential_ctx(params, measures=None):
    return TDMContext(
        scale=Scale.PROJECT_SITE,
        location_type=LocationType.URBAN,
        land_use_type=LandUseType.RESIDENTIAL,
        params=params,
        measures=measures,
    )


class TestExplicitSelection:
    def test_only_declared_measures_run(self):
        # Params would auto-activate T-1, T-3, and T-4; declaring only T-1
        # must restrict the run to T-1.
        params = {
            "proposed_residential_density": 20.0,
            "transit_mode_share": 0.05,
            "vehicle_mode_share": 0.80,
            "pct_multifamily_units_affordable": 1.0,
        }
        only_t1 = run_land_use(_residential_ctx(params, measures=["T-1"]))
        auto = run_land_use(_residential_ctx(params))
        assert only_t1 == pytest.approx(-0.2635, abs=1e-3)  # T-1 alone
        assert abs(auto) > abs(only_t1)  # auto mode combined more measures

    def test_declared_measures_share_flat_params(self):
        # One flat vehicle/transit share pair feeds both declared measures.
        params = {
            "proposed_residential_density": 20.0,
            "transit_mode_share": 0.05,
            "vehicle_mode_share": 0.80,
        }
        result = run_land_use(_residential_ctx(params, measures=["T-1", "T-3"]))
        t1, t3 = -0.26352, -(min(0.05 * 4.9, 0.27) / 0.80)
        expected = (1 + t1) * (1 + t3) - 1
        assert result == pytest.approx(expected, abs=1e-4)

    def test_scoped_params_apply_to_declared_measures(self):
        params = {"T-1": {"proposed_residential_density": 50.0}}  # hits cap
        result = run_land_use(_residential_ctx(params, measures=["T-1"]))
        assert result == pytest.approx(-0.30)

    def test_empty_selection_runs_nothing(self):
        params = {"proposed_residential_density": 20.0}
        assert run_land_use(_residential_ctx(params, measures=[])) == 0.0

    def test_none_preserves_auto_activation(self):
        params = {"proposed_residential_density": 20.0}
        assert run_land_use(_residential_ctx(params)) == pytest.approx(
            -0.2635, abs=1e-3
        )

    def test_selection_in_other_subsector_is_ignored_by_this_one(self):
        # T-25 (transit) declared alongside T-1; land_use run only sees T-1.
        params = {"proposed_residential_density": 20.0}
        result = run_land_use(_residential_ctx(params, measures=["T-1", "T-25"]))
        assert result == pytest.approx(-0.2635, abs=1e-3)


class TestSelectionErrors:
    def test_unknown_measure_id_raises(self):
        ctx = _residential_ctx(
            {"proposed_residential_density": 20.0}, measures=["T-999"]
        )
        with pytest.raises(MeasureSelectionError, match="T-999"):
            run_land_use(ctx)

    def test_missing_required_params_raises_with_names(self):
        ctx = _residential_ctx({}, measures=["T-1"])
        with pytest.raises(
            MeasureSelectionError, match="proposed_residential_density"
        ):
            run_land_use(ctx)

    def test_inapplicable_land_use_raises(self):
        # T-2 is commercial-only; declaring it in a residential context fails.
        ctx = _residential_ctx({"proposed_job_density": 200.0}, measures=["T-2"])
        with pytest.raises(MeasureSelectionError, match="T-2"):
            run_land_use(ctx)

    def test_inapplicable_scale_raises(self):
        # T-17 is Plan/Community; declaring it in a Project/Site context fails.
        ctx = _residential_ctx(
            {"proposed_intersection_density": 60.0}, measures=["T-17"]
        )
        with pytest.raises(MeasureSelectionError, match="T-17"):
            run_land_use(ctx)

    def test_selected_measure_conflicting_with_orchestrator_exclusion_raises(self):
        # T-28 declared while use_brt=False (which excludes T-28).
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.MIXED,
            params={
                "pct_increase_in_transit_frequency": 1.0,
                "level_of_implementation": 1.0,
                "transit_mode_share": 0.05,
                "vehicle_mode_share": 0.80,
            },
            measures=["T-28"],
        )
        with pytest.raises(MeasureSelectionError, match="T-28"):
            run_transit(ctx, use_brt=False)
        # With use_brt=True the same selection runs cleanly.
        assert run_transit(ctx, use_brt=True) < 0.0

    def test_declaring_mutually_exclusive_measures_raises(self):
        ctx = _residential_ctx(
            {"pct_employees_eligible": 1.0}, measures=["T-5", "T-6"]
        )
        with pytest.raises(MeasureExclusivityError):
            run_trip_reduction(ctx)


class TestExplicitSelectionMultiSubsector:
    def test_cross_subsector_declaration(self):
        # One declaration spanning land use and neighborhood design.
        ctx = TDMContext(
            scale=Scale.PLAN_COMMUNITY,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.MIXED,
            params={
                "proposed_intersection_density": 60.0,
                "existing_sidewalk_length": 100.0,
                "proposed_sidewalk_length": 150.0,
            },
            measures=["T-17", "T-18"],
        )
        t17 = ((60.0 - 36.0) / 36.0) * -0.14
        t18 = (150.0 / 100.0 - 1) * -0.05
        expected = (1 + t17) * (1 + t18) - 1
        assert run_multi_subsector(ctx) == pytest.approx(expected, abs=1e-6)

    def test_declared_trip_reduction_measure_not_run_by_multi(self):
        # run_multi_subsector covers land use, neighborhood design, parking,
        # and transit only; a declared trip-reduction measure contributes 0
        # there but still runs via its own orchestrator.
        ctx = _residential_ctx(
            {"pct_employees_eligible": 1.0}, measures=["T-6"]
        )
        assert run_multi_subsector(ctx) == 0.0
        assert run_trip_reduction(ctx) == pytest.approx(-0.26)
