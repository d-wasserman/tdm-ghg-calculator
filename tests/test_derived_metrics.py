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

Mode shift is metadata-driven: each measure declares ``target_modes`` and a
derived ``implies_mode_shift`` property, and a measure's reduction is apportioned
across its target modes in proportion to their baseline shares (equal split when
no baseline is supplied). SOV is the source mode that shrinks.
"""

import pytest

from tdm_ghg import (
    TDMContext,
    Scale,
    LocationType,
    LandUseType,
    Mode,
    NON_SOV_MODES,
    registry,
)
from tdm_ghg.derived_metrics import (
    DEFAULT_EMISSION_FACTOR_G_PER_MILE,
    DerivedMetrics,
    ModeSplit,
    vmt_reduced,
    trips_from_vmt,
    trips_reduced,
    co2_tonnes_from_vmt,
    co2_tonnes_reduced,
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


class TestModeTaxonomy:
    def test_mode_values(self):
        assert [m.value for m in Mode] == [
            "sov", "hov", "transit", "bike", "walk", "wfh", "other",
        ]

    def test_non_sov_modes_excludes_sov(self):
        assert Mode.SOV not in NON_SOV_MODES
        assert NON_SOV_MODES == frozenset({
            Mode.HOV, Mode.TRANSIT, Mode.BIKE, Mode.WALK, Mode.WFH, Mode.OTHER,
        })

    def test_mode_is_str_comparable(self):
        # str-enum: metadata keyed by Mode resolves with plain strings too.
        assert Mode.TRANSIT == "transit"


class TestMeasureModeMetadata:
    """The classification lives on the measure metadata, not in name inference."""

    def test_transit_measure(self):
        assert registry.get("T-9").target_modes == frozenset({Mode.TRANSIT})

    def test_hov_measure(self):
        assert registry.get("T-8").target_modes == frozenset({Mode.HOV})

    def test_bike_measure(self):
        assert registry.get("T-20").target_modes == frozenset({Mode.BIKE})

    def test_scootershare_is_bike(self):
        # Bike encompasses the broader micromobility category.
        assert registry.get("T-22-C").target_modes == frozenset({Mode.BIKE})

    def test_active_youth_is_bike_and_walk(self):
        assert registry.get("T-56").target_modes == frozenset({Mode.BIKE, Mode.WALK})

    def test_all_modes_measure(self):
        assert registry.get("T-1").target_modes == NON_SOV_MODES

    def test_clean_vehicle_has_no_mode_shift(self):
        for mid in ("T-14", "T-30"):
            meta = registry.get(mid)
            assert meta.target_modes == frozenset()
            assert meta.implies_mode_shift is False

    def test_every_other_measure_implies_mode_shift(self):
        for mid, meta in registry.measures.items():
            if mid in {"T-14", "T-30"}:
                continue
            assert meta.implies_mode_shift, mid

    def test_sov_is_never_a_destination(self):
        for meta in registry.measures.values():
            assert Mode.SOV not in meta.target_modes


class TestGenerateModeShiftWeights:
    def test_single_mode_gets_full_magnitude(self):
        weights = generate_mode_shift_weights({"T-9": -0.05})
        assert weights[Mode.TRANSIT] == pytest.approx(0.05)
        assert set(weights) == {Mode.TRANSIT}

    def test_clean_vehicle_contributes_nothing(self):
        assert generate_mode_shift_weights({"T-30": -0.5}) == {}

    def test_equal_split_without_baseline(self):
        # T-1 targets all six non-SOV modes -> 0.06 / 6 = 0.01 each.
        weights = generate_mode_shift_weights({"T-1": -0.06})
        assert set(weights) == set(NON_SOV_MODES)
        for mode in NON_SOV_MODES:
            assert weights[mode] == pytest.approx(0.01)

    def test_proportional_to_baseline(self):
        # Transit baseline share is double bike's, so transit absorbs 2x the shift.
        baseline = {Mode.TRANSIT: 0.10, Mode.BIKE: 0.05, Mode.HOV: 0.05}
        weights = generate_mode_shift_weights(
            {"T-1": -0.06}, baseline_mode_shares=baseline
        )
        assert weights[Mode.TRANSIT] == pytest.approx(0.03)   # 0.06 * 0.10/0.20
        assert weights[Mode.BIKE] == pytest.approx(0.015)
        assert weights[Mode.HOV] == pytest.approx(0.015)
        # Modes with zero baseline share absorb nothing.
        assert weights.get(Mode.WFH, 0.0) == pytest.approx(0.0)
        # And more than an equal split (0.01) went to transit.
        assert weights[Mode.TRANSIT] > 0.06 / len(NON_SOV_MODES)

    def test_target_modes_override(self):
        weights = generate_mode_shift_weights(
            {"custom": -0.04}, target_modes_override={"custom": {Mode.WFH}}
        )
        assert weights == {Mode.WFH: pytest.approx(0.04)}

    def test_zero_magnitude_skipped(self):
        assert generate_mode_shift_weights({"T-9": 0.0}) == {}


class TestEstimateModeSplit:
    def test_sov_is_the_source(self):
        baseline = {Mode.SOV: 0.80, Mode.TRANSIT: 0.05, Mode.BIKE: 0.05}
        split = estimate_mode_split({"T-9": -0.06}, baseline_mode_shares=baseline)
        assert isinstance(split, ModeSplit)
        assert split.total_sov_reduction == pytest.approx(0.06)
        assert split.new_mode_shares[Mode.SOV] == pytest.approx(0.74)
        assert split.new_mode_shares[Mode.TRANSIT] == pytest.approx(0.11)

    def test_shares_sum_to_one(self):
        split = estimate_mode_split({"T-9": -0.06, "T-8": -0.02})
        assert sum(split.shares.values()) == pytest.approx(1.0)

    def test_new_shares_conserve_total(self):
        baseline = {Mode.SOV: 0.80, Mode.HOV: 0.03, Mode.TRANSIT: 0.05,
                    Mode.BIKE: 0.04, Mode.WALK: 0.06, Mode.WFH: 0.0, Mode.OTHER: 0.02}
        split = estimate_mode_split(
            {"T-1": -0.10, "T-3": -0.05}, baseline_mode_shares=baseline
        )
        assert sum(split.new_mode_shares.values()) == pytest.approx(1.0)

    def test_empty_reductions_no_change(self):
        split = estimate_mode_split({})
        assert split.total_sov_reduction == pytest.approx(0.0)
        assert split.shares == {}

    def test_sov_share_floored_at_zero(self):
        baseline = {Mode.SOV: 0.05, Mode.TRANSIT: 0.95}
        split = estimate_mode_split({"T-9": -0.10}, baseline_mode_shares=baseline)
        assert split.new_mode_shares[Mode.SOV] == pytest.approx(0.0)


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
        result = per_measure_reductions(self._ctx())
        assert all(v is not None for v in result.values())


class TestSummarize:
    def test_full_bundle(self):
        metrics = summarize(
            baseline_vmt=1_000_000,
            reduction_fraction=-0.10,
            average_trip_distance=10.0,
            measure_reductions={"T-9": -0.06, "T-8": -0.02},
            baseline_mode_shares={Mode.SOV: 0.80, Mode.HOV: 0.05,
                                  Mode.TRANSIT: 0.05, Mode.BIKE: 0.05,
                                  Mode.WALK: 0.05},
        )
        assert isinstance(metrics, DerivedMetrics)
        assert metrics.vmt_reduced == pytest.approx(100_000)
        assert metrics.trips_reduced == pytest.approx(10_000)
        assert metrics.co2_tonnes_reduced == pytest.approx(30.75)
        assert metrics.mode_split.total_sov_reduction == pytest.approx(0.08)

    def test_optional_fields_none(self):
        metrics = summarize(baseline_vmt=1_000_000, reduction_fraction=-0.10)
        assert metrics.trips_reduced is None
        assert metrics.mode_split is None
        assert metrics.co2_tonnes_reduced == pytest.approx(30.75)
