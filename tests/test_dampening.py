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
"""Unit tests for ``multiplicative_dampening``.

The library uses a signed convention where **negative values are reductions**.
The combining rule is the signed form of the CAPCOA multiplicative dampening
formula::

    combined = ∏(1 + rᵢ) - 1

so two 10% and 8% reductions combine to -0.172 (not -0.18 arithmetic sum, and
not the -0.188 amplification produced by applying the unsigned ``1 - ∏(1 - rᵢ)``
formula to already-negative inputs).
"""

import math

import pytest

from tdm_ghg import multiplicative_dampening


class TestSingleValue:
    def test_single_reduction_returned_unchanged(self):
        assert multiplicative_dampening([-0.10]) == pytest.approx(-0.10)

    def test_single_value_under_cap_unchanged(self):
        assert multiplicative_dampening([-0.05], -0.15) == pytest.approx(-0.05)

    def test_single_zero_is_zero(self):
        assert multiplicative_dampening([0.0]) == pytest.approx(0.0)


class TestCombining:
    def test_two_reductions_are_dampened(self):
        # 0.90 * 0.92 - 1 = -0.172. Guards against the amplification bug
        # (which returned -0.188) and the naive arithmetic sum (-0.18).
        assert multiplicative_dampening([-0.10, -0.08]) == pytest.approx(-0.172)

    def test_result_magnitude_below_arithmetic_sum(self):
        result = multiplicative_dampening([-0.10, -0.08])
        assert abs(result) < abs(-0.10) + abs(-0.08)

    def test_three_reductions(self):
        # 0.90 * 0.92 * 0.95 - 1 = -0.2134
        assert multiplicative_dampening([-0.10, -0.08, -0.05]) == pytest.approx(-0.2134)

    def test_order_independent(self):
        forward = multiplicative_dampening([-0.10, -0.08, -0.05])
        reverse = multiplicative_dampening([-0.05, -0.10, -0.08])
        assert forward == pytest.approx(reverse)

    def test_combining_reductions_never_exceeds_100_percent(self):
        result = multiplicative_dampening([-0.5, -0.5, -0.5])
        assert -1.0 <= result < 0.0


class TestCap:
    def test_cap_applied_when_combined_exceeds_it(self):
        assert (
            multiplicative_dampening([-0.10, -0.08, -0.05], -0.15)
            == pytest.approx(-0.15)
        )

    def test_cap_not_applied_when_combined_under_it(self):
        assert multiplicative_dampening([-0.05], -0.15) == pytest.approx(-0.05)

    def test_cap_sign_insensitive(self):
        positive_cap = multiplicative_dampening([-0.5], 0.15)
        negative_cap = multiplicative_dampening([-0.5], -0.15)
        assert positive_cap == pytest.approx(negative_cap) == pytest.approx(-0.15)

    def test_none_cap_is_uncapped(self):
        # 0.5 * 0.5 - 1 = -0.75, no clamping
        assert multiplicative_dampening([-0.5, -0.5], None) == pytest.approx(-0.75)

    def test_default_cap_is_none(self):
        assert multiplicative_dampening([-0.5, -0.5]) == pytest.approx(-0.75)


class TestIncreases:
    def test_increase_not_limited_by_reduction_cap(self):
        # A reduction cap must not bound a net increase.
        assert multiplicative_dampening([0.20], -0.35) == pytest.approx(0.20)

    def test_mixed_increase_and_reduction(self):
        # 1.20 * 0.90 - 1 = 0.08 (net increase)
        assert multiplicative_dampening([0.20, -0.10]) == pytest.approx(0.08)

    def test_increase_can_offset_reduction_to_net_zero(self):
        # 0.90 * (1 / 0.90) - 1 = 0.0
        assert multiplicative_dampening([-0.10, (1 / 0.9) - 1]) == pytest.approx(
            0.0, abs=1e-9
        )


class TestEdgeCases:
    def test_empty_returns_zero(self):
        assert multiplicative_dampening([]) == 0.0

    def test_all_zeros_returns_zero(self):
        assert multiplicative_dampening([0.0, 0.0, 0.0]) == pytest.approx(0.0)

    def test_nan_treated_as_no_effect(self):
        assert multiplicative_dampening([float("nan"), -0.10]) == pytest.approx(-0.10)

    def test_full_reduction(self):
        assert multiplicative_dampening([-1.0]) == pytest.approx(-1.0)

    def test_full_reduction_dominates_others(self):
        # (1 - 1) * (1 - 0.5) - 1 = -1.0
        assert multiplicative_dampening([-1.0, -0.5]) == pytest.approx(-1.0)

    def test_returns_python_float(self):
        result = multiplicative_dampening([-0.10, -0.08])
        assert isinstance(result, float)
        assert not math.isnan(result)


class TestReadmeExamples:
    def test_readme_capped_example(self):
        # From README "Combining Measures" section.
        assert (
            multiplicative_dampening(
                [-0.10, -0.08, -0.05], max_reduction_percentage=-0.15
            )
            == pytest.approx(-0.15)
        )
