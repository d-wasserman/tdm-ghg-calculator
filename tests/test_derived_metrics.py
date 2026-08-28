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
"""Unit tests for the derived-metrics utilities.

These back-calculate absolute quantities (VMT, trips, tonnes CO2, mode shift)
from the library's signed percent reductions. Reduction inputs may be negative
(the library convention) or positive; results are positive magnitudes.
"""

import pytest

from tdm_ghg import (
    TDMContext,
    Scale,
    LocationType,
    LandUseType,
)
from tdm_ghg.derived_metrics import (
    DEFAULT_EMISSION_FACTOR_G_PER_MILE,
    NON_AUTO_MODES,
    DerivedMetrics,
    ModeSplit,
    vmt_reduced,
    trips_from_vmt,
    trips_reduced,
    co2_tonnes_from_vmt,
    co2_tonnes_reduced,
    infer_measure_mode,
    generate_mode_shift_weights,
    estimate_mode_split,
    per_measure_reductions,
    summarize,
)


class TestVmtReduced:
    def test_basic_magnitude(self):
        assert vmt_reduced(1_000_000, -0.14) == pytest.approx(140_000)

    def test_sign_ignored(self):
        assert vmt_reduced(1_000_000, 0.14) == pytest.approx(
            vmt_reduced(1_000_000, -0.14)
        )

    def test_zero_reduction(self):
        assert vmt_reduced(1_000_000, 0.0) == pytest.approx(0.0)


class TestTripsFromVmt:
    def test_basic(self):
        assert trips_from_vmt(100_000, 10.0) == pytest.approx(10_000)

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError):
            trips_from_vmt(100_000, 0.0)

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError):
            trips_from_vmt(100_000, -5.0)


class TestTripsReduced:
    def test_composition(self):
        # 1_000_000 * 0.10 = 100_000 VMT avoided / 10 mi = 10_000 trips.
        assert trips_reduced(1_000_000, -0.10, 10.0) == pytest.approx(10_000)


class TestCo2:
    def test_from_vmt_default_factor(self):
        # 100_000 mi * 307.5 g/mi / 1e6 = 30.75 tonnes.
        assert co2_tonnes_from_vmt(100_000) == pytest.approx(30.75)

    def test_reduced_default_factor(self):
        assert co2_tonnes_reduced(1_000_000, -0.10) == pytest.approx(30.75)

    def test_custom_factor(self):
        assert co2_tonnes_from_vmt(100_000, emission_factor_g_per_mile=400.0) == (
            pytest.approx(40.0)
        )

    def test_default_factor_value(self):
        assert DEFAULT_EMISSION_FACTOR_G_PER_MILE == 307.5


class TestInferMeasureMode:
    def test_transit_measure_by_id(self):
        # T-9 = "Implement Subsidized or Discounted Transit Program".
        assert infer_measure_mode("T-9") == "transit"

    def test_bike_measure_by_id(self):
        # T-20 = "Expand Bikeway Network".
        assert infer_measure_mode("T-20") == "bike"

    def test_pedestrian_measure_by_id(self):
        # T-18 = "Provide Pedestrian Network Improvement".
        assert infer_measure_mode("T-18") == "walk"

    def test_no_mode_measure_returns_none(self):
        # T-1 = "Increase Residential Density" names no travel mode.
        assert infer_measure_mode("T-1") is None

    def test_raw_name_string(self):
        assert infer_measure_mode("Reduce Transit Fares") == "transit"

    def test_unknown_returns_none(self):
        assert infer_measure_mode("something with no mode words") is None


class TestGenerateModeShiftWeights:
    def test_named_mode_gets_full_magnitude(self):
        weights = generate_mode_shift_weights({"T-9": -0.05})
        assert weights["transit"] == pytest.approx(0.05)
        assert weights["bike"] == pytest.approx(0.0)
        assert weights["walk"] == pytest.approx(0.0)

    def test_unnamed_mode_splits_equally(self):
        # T-1 names no mode -> 0.09 split across 3 non-auto modes = 0.03 each.
        weights = generate_mode_shift_weights({"T-1": -0.09})
        for mode in NON_AUTO_MODES:
            assert weights[mode] == pytest.approx(0.03)

    def test_weights_sum_across_measures(self):
        weights = generate_mode_shift_weights({"T-9": -0.05, "T-20": -0.02})
        assert weights["transit"] == pytest.approx(0.05)
        assert weights["bike"] == pytest.approx(0.02)

    def test_zero_magnitude_skipped(self):
        weights = generate_mode_shift_weights({"T-9": 0.0})
        assert sum(weights.values()) == pytest.approx(0.0)


class TestEstimateModeSplit:
    def test_apportionment_matches_weights(self):
        split = estimate_mode_split({"T-9": -0.06, "T-20": -0.02})
        assert isinstance(split, ModeSplit)
        assert split.total_auto_change == pytest.approx(0.08)
        assert split.apportioned["transit"] == pytest.approx(0.06)
        assert split.apportioned["bike"] == pytest.approx(0.02)
        assert split.apportioned["walk"] == pytest.approx(0.0)

    def test_shares_sum_to_one(self):
        split = estimate_mode_split({"T-9": -0.06, "T-20": -0.02})
        assert sum(split.shares.values()) == pytest.approx(1.0)

    def test_new_mode_shares(self):
        baseline = {"auto": 0.80, "transit": 0.05, "bike": 0.05, "walk": 0.10}
        split = estimate_mode_split({"T-9": -0.06}, baseline_mode_shares=baseline)
        assert split.new_mode_shares["auto"] == pytest.approx(0.74)
        assert split.new_mode_shares["transit"] == pytest.approx(0.11)
        # Shares still sum to 1 (travel moved, not created).
        assert sum(split.new_mode_shares.values()) == pytest.approx(1.0)

    def test_empty_reductions_no_change(self):
        split = estimate_mode_split({})
        assert split.total_auto_change == pytest.approx(0.0)
        assert split.shares == {}

    def test_auto_share_floored_at_zero(self):
        baseline = {"auto": 0.05, "transit": 0.95}
        split = estimate_mode_split({"T-9": -0.10}, baseline_mode_shares=baseline)
        assert split.new_mode_shares["auto"] == pytest.approx(0.0)


class TestPerMeasureReductions:
    def _ctx(self):
        return TDMContext(
            scale=Scale.PROJECT_SITE,
            location_type=LocationType.URBAN,
            land_use_type=LandUseType.RESIDENTIAL,
            params={"proposed_residential_density": 20.0},
        )

    def test_returns_activated_measure(self):
        result = per_measure_reductions(self._ctx())
        assert "T-1" in result
        assert result["T-1"] < 0.0

    def test_skips_measures_missing_params(self):
        # Only density is supplied, so measures needing other params are skipped.
        result = per_measure_reductions(self._ctx())
        assert all(v is not None for v in result.values())


class TestSummarize:
    def test_full_bundle(self):
        metrics = summarize(
            baseline_vmt=1_000_000,
            reduction_fraction=-0.10,
            average_trip_distance=10.0,
            measure_reductions={"T-9": -0.06, "T-20": -0.02},
            baseline_mode_shares={"auto": 0.80, "transit": 0.05,
                                  "bike": 0.05, "walk": 0.10},
        )
        assert isinstance(metrics, DerivedMetrics)
        assert metrics.vmt_reduced == pytest.approx(100_000)
        assert metrics.trips_reduced == pytest.approx(10_000)
        assert metrics.co2_tonnes_reduced == pytest.approx(30.75)
        assert metrics.mode_split.total_auto_change == pytest.approx(0.08)

    def test_optional_fields_none(self):
        metrics = summarize(baseline_vmt=1_000_000, reduction_fraction=-0.10)
        assert metrics.trips_reduced is None
        assert metrics.mode_split is None
        assert metrics.co2_tonnes_reduced == pytest.approx(30.75)
