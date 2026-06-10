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
"""Tests for CAPCOA documented input maxima and packaging hygiene.

The handbook documents per-input maxima for several measures. Some were
already clamped in-formula (T-26/T-28 frequency at 3.0, T-29 fare at 0.5,
T-12 price ratio at 0.5, T-16 cost at $3,600); T-11 (Bmax = 0.15
participation) and T-14 (Dmax = 7 PHEVs/charger/day) were documented but
unenforced, letting out-of-range inputs overstate reductions up to the
measure cap. These tests pin the clamps and related default-value hygiene.
"""

import inspect
import pathlib
import re

import pytest

import tdm_ghg
from tdm_ghg import (
    t11_provide_employer_sponsored_vanpool,
    t14_provide_ev_charging_infrastructure,
    t22a_implement_pedal_bikeshare,
    t22b_implement_electric_bikeshare,
    t22c_implement_scootershare,
    t22d_transition_conventional_to_electric_bikeshare,
)


class TestT11ParticipationClamp:
    def test_participation_above_bmax_equals_bmax(self):
        at_max = t11_provide_employer_sponsored_vanpool(
            pct_employees_vanpooling=0.15,
            avg_vehicle_commute_trip_length=14.52,
        )
        above_max = t11_provide_employer_sponsored_vanpool(
            pct_employees_vanpooling=0.60,
            avg_vehicle_commute_trip_length=14.52,
        )
        assert above_max == pytest.approx(at_max)

    def test_participation_below_bmax_unclamped(self):
        low = t11_provide_employer_sponsored_vanpool(
            pct_employees_vanpooling=0.05,
            avg_vehicle_commute_trip_length=14.52,
        )
        at_max = t11_provide_employer_sponsored_vanpool(
            pct_employees_vanpooling=0.15,
            avg_vehicle_commute_trip_length=14.52,
        )
        assert abs(low) < abs(at_max)


class TestT14ChargerUtilizationClamp:
    def test_utilization_above_dmax_equals_dmax(self):
        at_max = t14_provide_ev_charging_infrastructure(
            num_chargers=10, total_vehicles_per_day=1000,
            avg_phevs_served_per_charger_per_day=7,
        )
        above_max = t14_provide_ev_charging_infrastructure(
            num_chargers=10, total_vehicles_per_day=1000,
            avg_phevs_served_per_charger_per_day=20,
        )
        assert above_max == pytest.approx(at_max)

    def test_utilization_below_dmax_unclamped(self):
        low = t14_provide_ev_charging_infrastructure(
            num_chargers=10, total_vehicles_per_day=1000,
            avg_phevs_served_per_charger_per_day=2,
        )
        at_max = t14_provide_ev_charging_infrastructure(
            num_chargers=10, total_vehicles_per_day=1000,
            avg_phevs_served_per_charger_per_day=7,
        )
        assert abs(low) < abs(at_max)


class TestSharedDefaultConsistency:
    def test_t22_family_daily_vehicle_trips_default_agrees(self):
        # T-22-A/B/C/D all normalize by daily vehicle trips per person;
        # the default baseline must be identical across the family.
        defaults = {
            func.__name__: inspect.signature(func)
            .parameters["daily_vehicle_trips_per_person"]
            .default
            for func in (
                t22a_implement_pedal_bikeshare,
                t22b_implement_electric_bikeshare,
                t22c_implement_scootershare,
                t22d_transition_conventional_to_electric_bikeshare,
            )
        }
        assert len(set(defaults.values())) == 1, defaults


class TestVersionMetadata:
    def test_dunder_version_matches_pyproject(self):
        pyproject = (
            pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        ).read_text()
        declared = re.search(
            r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE
        ).group(1)
        assert tdm_ghg.__version__ == declared
