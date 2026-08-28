# Name: derived_metrics.py
# Purpose: Back-calculate absolute derived metrics (trips, mode shift, tonnes
#          CO2) from the percent VMT/GHG reductions produced by tdm_ghg.
# Author: David Wasserman
# Python Version:   3.9+
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
"""Derived metrics for TDM GHG reductions.

The measure functions and subsector orchestrators in :mod:`tdm_ghg` return a
signed decimal fraction where negative values are reductions (``-0.14`` = 14%
reduction in VMT/GHG). Those percentages are the library's primary output, but
planners often need the *absolute* quantities they imply once a baseline and a
few supplementary inputs are supplied:

* **VMT reduced** — vehicle miles avoided.
* **Trips reduced** — vehicle trips avoided, from an average trip distance.
* **Tonnes of CO2 reduced** — metric tonnes CO2e avoided, from an emission
  factor.
* **Mode shift** — how the avoided auto travel redistributes across non-auto
  modes (transit / bike / walk).

Every function here is a pure back-calculation: it takes a signed reduction
fraction (or a ``{measure: fraction}`` mapping) plus supplementary inputs and
returns a derived quantity. Reductions are returned as positive magnitudes
(miles, trips, tonnes avoided) regardless of the sign of the input fraction, so
callers may pass the library's negative fractions directly.

Mode shift is intentionally decoupled from the measure registry: the mode a
measure shifts travel toward is *inferred* from the measure's name/subsector via
keyword matching (see :data:`MODE_KEYWORDS`), rather than stored on each
measure. A measure whose name mentions a mode ascribes all of its magnitude to
that mode; a measure that names no mode splits its magnitude equally across the
non-auto modes.

Examples
--------
>>> from tdm_ghg.derived_metrics import trips_reduced, co2_tonnes_reduced
>>> round(trips_reduced(1_000_000, -0.10, average_trip_distance=10.0))
10000
>>> round(co2_tonnes_reduced(1_000_000, -0.10), 2)
30.75
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tdm_ghg.registry import registry

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: Grams in one metric tonne (1,000 kg). CO2 output is reported in metric
#: tonnes CO2e, the standard unit for GHG inventories (incl. CAPCOA).
GRAMS_PER_METRIC_TON = 1_000_000

#: Default tailpipe emission factor for a typical light-duty gasoline vehicle
#: [g CO2e/mile]. Matches the light-duty default used across ``mitigations.py``
#: (CARB EMFAC). Override per analysis via the ``emission_factor_g_per_mile``
#: argument.
DEFAULT_EMISSION_FACTOR_G_PER_MILE = 307.5

#: Non-auto modes that avoided auto travel is redistributed across.
NON_AUTO_MODES = ("transit", "bike", "walk")

#: Substring -> mode heuristic used to infer which mode a measure shifts travel
#: toward, matched (case-insensitive) against a measure's name and subsector.
#: Tunable: pass a custom mapping to the mode-shift functions to adjust it.
MODE_KEYWORDS = {
    "transit": "transit",
    "bus": "transit",
    "rapid transit": "transit",
    "fare": "transit",
    "shelter": "transit",
    "bike": "bike",
    "bicycle": "bike",
    "bikeway": "bike",
    "bikeshare": "bike",
    "boulevard": "bike",
    "scooter": "bike",
    "pedestrian": "walk",
    "walk": "walk",
    "active modes": "walk",
}


# --------------------------------------------------------------------------- #
# Core conversions
# --------------------------------------------------------------------------- #

def vmt_reduced(baseline_vmt, reduction_fraction):
    """Absolute VMT avoided by a reduction applied to a baseline.

    Parameters
    ----------
    baseline_vmt : float
        Baseline vehicle miles traveled (any period; the result shares its
        period). Must be non-negative.
    reduction_fraction : float
        Signed reduction fraction from a measure or orchestrator, e.g.
        ``-0.14``. The sign is ignored; the magnitude is used.

    Returns
    -------
    float
        Vehicle miles avoided (a positive magnitude).
    """
    return baseline_vmt * abs(reduction_fraction)


def trips_from_vmt(vmt, average_trip_distance):
    """Number of trips implied by a VMT total and an average trip distance.

    Parameters
    ----------
    vmt : float
        Vehicle miles traveled.
    average_trip_distance : float
        Average one-way vehicle trip length [miles]. Must be positive.

    Returns
    -------
    float
        Number of trips (``vmt / average_trip_distance``).

    Raises
    ------
    ValueError
        If ``average_trip_distance`` is not positive.
    """
    if average_trip_distance <= 0:
        raise ValueError("average_trip_distance must be positive")
    return vmt / average_trip_distance


def trips_reduced(baseline_vmt, reduction_fraction, average_trip_distance):
    """Vehicle trips avoided by a reduction, given an average trip distance.

    Parameters
    ----------
    baseline_vmt : float
        Baseline vehicle miles traveled.
    reduction_fraction : float
        Signed reduction fraction (sign ignored).
    average_trip_distance : float
        Average one-way vehicle trip length [miles]. Must be positive.

    Returns
    -------
    float
        Vehicle trips avoided (a positive magnitude).
    """
    return trips_from_vmt(
        vmt_reduced(baseline_vmt, reduction_fraction), average_trip_distance
    )


def co2_tonnes_from_vmt(
    vmt_reduced_miles,
    emission_factor_g_per_mile=DEFAULT_EMISSION_FACTOR_G_PER_MILE,
):
    """Metric tonnes CO2e avoided for a quantity of VMT reduced.

    Parameters
    ----------
    vmt_reduced_miles : float
        Vehicle miles avoided (positive magnitude).
    emission_factor_g_per_mile : float, optional
        Emission factor [g CO2e/mile]. Default is
        :data:`DEFAULT_EMISSION_FACTOR_G_PER_MILE` (307.5).

    Returns
    -------
    float
        Metric tonnes CO2e avoided.
    """
    return vmt_reduced_miles * emission_factor_g_per_mile / GRAMS_PER_METRIC_TON


def co2_tonnes_reduced(
    baseline_vmt,
    reduction_fraction,
    emission_factor_g_per_mile=DEFAULT_EMISSION_FACTOR_G_PER_MILE,
):
    """Metric tonnes CO2e avoided by a reduction applied to a baseline.

    Parameters
    ----------
    baseline_vmt : float
        Baseline vehicle miles traveled.
    reduction_fraction : float
        Signed reduction fraction (sign ignored).
    emission_factor_g_per_mile : float, optional
        Emission factor [g CO2e/mile]. Default is
        :data:`DEFAULT_EMISSION_FACTOR_G_PER_MILE` (307.5).

    Returns
    -------
    float
        Metric tonnes CO2e avoided (a positive magnitude).
    """
    return co2_tonnes_from_vmt(
        vmt_reduced(baseline_vmt, reduction_fraction), emission_factor_g_per_mile
    )


# --------------------------------------------------------------------------- #
# Mode shift (decoupled — inferred from measure names, not the decorators)
# --------------------------------------------------------------------------- #

def infer_measure_mode(measure, mode_keywords=None):
    """Infer the non-auto mode a measure shifts travel toward.

    The measure's descriptive text is matched (case-insensitive) against
    ``mode_keywords``. ``measure`` may be a CAPCOA measure ID (e.g. ``"T-9"``),
    which is resolved to its registered name and subsector, or a raw name
    string.

    Parameters
    ----------
    measure : str
        A registered measure ID or a raw measure name.
    mode_keywords : Mapping[str, str], optional
        Substring -> mode mapping. Defaults to :data:`MODE_KEYWORDS`.

    Returns
    -------
    str or None
        The inferred mode (e.g. ``"transit"``), or ``None`` if no keyword
        matches (the caller then splits the magnitude across all non-auto
        modes).
    """
    if mode_keywords is None:
        mode_keywords = MODE_KEYWORDS
    meta = registry.get(measure)
    if meta is not None:
        text = f"{meta.name} {meta.subsector}".lower()
    else:
        text = str(measure).lower()
    for keyword, mode in mode_keywords.items():
        if keyword in text:
            return mode
    return None


def generate_mode_shift_weights(
    measure_reductions,
    non_auto_modes=NON_AUTO_MODES,
    mode_keywords=None,
):
    """Sum per-mode mode-shift weights across a set of measures.

    For each measure with reduction magnitude ``m = abs(fraction)``:

    * if a mode can be inferred (:func:`infer_measure_mode`), all of ``m`` is
      ascribed to that mode;
    * otherwise ``m`` is split equally across ``non_auto_modes``.

    The contributions are summed per mode. The total of the returned weights is
    the aggregate auto-mode change apportioned across modes.

    Parameters
    ----------
    measure_reductions : Mapping[str, float]
        Mapping of measure ID (or name) to its signed reduction fraction.
    non_auto_modes : tuple of str, optional
        Modes to split unattributed magnitude across. Defaults to
        :data:`NON_AUTO_MODES`.
    mode_keywords : Mapping[str, str], optional
        Passed through to :func:`infer_measure_mode`.

    Returns
    -------
    dict[str, float]
        Summed weight per mode (keys are ``non_auto_modes``).
    """
    weights = {mode: 0.0 for mode in non_auto_modes}
    for measure, fraction in measure_reductions.items():
        magnitude = abs(float(fraction))
        if magnitude == 0.0:
            continue
        mode = infer_measure_mode(measure, mode_keywords=mode_keywords)
        if mode in weights:
            weights[mode] += magnitude
        else:
            share = magnitude / len(non_auto_modes)
            for m in non_auto_modes:
                weights[m] += share
    return weights


@dataclass
class ModeSplit:
    """Result of a mode-shift estimation.

    Attributes
    ----------
    weights : dict[str, float]
        Summed mode-shift weight per non-auto mode.
    shares : dict[str, float]
        Normalized weights (each weight / total), summing to 1.0. Empty when
        the total weight is zero.
    total_auto_change : float
        Aggregate auto-mode change (sum of ``weights``); the magnitude
        redistributed from auto to non-auto modes.
    apportioned : dict[str, float]
        Portion of ``total_auto_change`` assigned to each non-auto mode.
    new_mode_shares : dict[str, float] or None
        Resulting mode shares when ``baseline_mode_shares`` was supplied,
        otherwise ``None``. Auto is reduced by ``total_auto_change`` (clamped at
        0) and each non-auto mode is incremented by its apportionment.
    """
    weights: dict
    shares: dict
    total_auto_change: float
    apportioned: dict
    new_mode_shares: Optional[dict] = None


def estimate_mode_split(
    measure_reductions,
    baseline_mode_shares=None,
    non_auto_modes=NON_AUTO_MODES,
    mode_keywords=None,
):
    """Estimate how avoided auto travel redistributes across non-auto modes.

    Weights are inferred per measure (:func:`generate_mode_shift_weights`) and
    summed. Their total is the aggregate auto-mode change; it is apportioned
    across non-auto modes in proportion to each mode's weight. This uses the
    additive combination the model calls for; to combine the fractions with
    CAPCOA multiplicative dampening instead, pre-combine them with
    :func:`tdm_ghg.utils.multiplicative_dampening` before calling.

    Parameters
    ----------
    measure_reductions : Mapping[str, float]
        Mapping of measure ID (or name) to its signed reduction fraction.
    baseline_mode_shares : Mapping[str, float], optional
        Baseline mode shares including an ``"auto"`` key (e.g.
        ``{"auto": 0.80, "transit": 0.05, "bike": 0.05, "walk": 0.10}``). When
        supplied, resulting shares are computed on ``ModeSplit.new_mode_shares``.
    non_auto_modes : tuple of str, optional
        Non-auto modes. Defaults to :data:`NON_AUTO_MODES`.
    mode_keywords : Mapping[str, str], optional
        Passed through to :func:`infer_measure_mode`.

    Returns
    -------
    ModeSplit
        The weights, normalized shares, aggregate auto change, per-mode
        apportionment, and (optionally) resulting mode shares.
    """
    weights = generate_mode_shift_weights(
        measure_reductions, non_auto_modes=non_auto_modes, mode_keywords=mode_keywords
    )
    total = sum(weights.values())
    if total > 0:
        shares = {mode: w / total for mode, w in weights.items()}
    else:
        shares = {}
    apportioned = {mode: total * shares.get(mode, 0.0) for mode in non_auto_modes}

    new_mode_shares = None
    if baseline_mode_shares is not None:
        new_mode_shares = dict(baseline_mode_shares)
        new_mode_shares["auto"] = max(
            0.0, baseline_mode_shares.get("auto", 0.0) - total
        )
        for mode in non_auto_modes:
            new_mode_shares[mode] = (
                baseline_mode_shares.get(mode, 0.0) + apportioned[mode]
            )

    return ModeSplit(
        weights=weights,
        shares=shares,
        total_auto_change=total,
        apportioned=apportioned,
        new_mode_shares=new_mode_shares,
    )


# --------------------------------------------------------------------------- #
# Context bridge — per-measure reductions from a TDMContext
# --------------------------------------------------------------------------- #

def per_measure_reductions(context, subsector=None, excluded_ids=()):
    """Compute each applicable measure's reduction fraction for a context.

    Bridges a :class:`~tdm_ghg.context.TDMContext` to the ``{measure: fraction}``
    mapping the mode-shift functions consume. Measures are filtered and called
    through the registry (read-only reuse of ``registry.filter`` and
    ``registry.call_measure``); measures whose required parameters are missing
    are skipped.

    Parameters
    ----------
    context : TDMContext
        Analysis context supplying scale, location/land-use type, and params.
    subsector : str, optional
        Restrict to a single subsector (e.g. ``"transit"``).
    excluded_ids : Collection[str], optional
        Measure IDs to exclude (for mutual exclusivity).

    Returns
    -------
    dict[str, float]
        Mapping of measure ID to its signed reduction fraction.
    """
    results = {}
    for meta in registry.filter(context, subsector=subsector, excluded_ids=excluded_ids):
        value = registry.call_measure(meta, context.params)
        if value is not None:
            results[meta.measure_id] = value
    return results


# --------------------------------------------------------------------------- #
# Summary aggregator
# --------------------------------------------------------------------------- #

@dataclass
class DerivedMetrics:
    """Bundle of absolute derived metrics for a single combined reduction.

    Attributes
    ----------
    vmt_reduced : float
        Vehicle miles avoided.
    trips_reduced : float or None
        Vehicle trips avoided, or ``None`` if no average trip distance was
        supplied.
    co2_tonnes_reduced : float
        Metric tonnes CO2e avoided.
    mode_split : ModeSplit or None
        Mode-shift estimate, or ``None`` if no per-measure reductions were
        supplied.
    """
    vmt_reduced: float
    co2_tonnes_reduced: float
    trips_reduced: Optional[float] = None
    mode_split: Optional[ModeSplit] = None


def summarize(
    baseline_vmt,
    reduction_fraction,
    average_trip_distance=None,
    emission_factor_g_per_mile=DEFAULT_EMISSION_FACTOR_G_PER_MILE,
    measure_reductions=None,
    baseline_mode_shares=None,
):
    """Compute all derived metrics for a combined reduction in one call.

    Parameters
    ----------
    baseline_vmt : float
        Baseline vehicle miles traveled.
    reduction_fraction : float
        Combined signed reduction fraction (e.g. from ``run_multi_subsector``).
    average_trip_distance : float, optional
        Average one-way vehicle trip length [miles]. When supplied,
        ``trips_reduced`` is computed.
    emission_factor_g_per_mile : float, optional
        Emission factor [g CO2e/mile]. Default 307.5.
    measure_reductions : Mapping[str, float], optional
        Per-measure reductions (e.g. from :func:`per_measure_reductions`). When
        supplied, ``mode_split`` is estimated.
    baseline_mode_shares : Mapping[str, float], optional
        Baseline mode shares for the mode-split estimate.

    Returns
    -------
    DerivedMetrics
        Populated derived-metrics bundle.
    """
    miles = vmt_reduced(baseline_vmt, reduction_fraction)
    trips = (
        trips_from_vmt(miles, average_trip_distance)
        if average_trip_distance is not None
        else None
    )
    mode_split = (
        estimate_mode_split(measure_reductions, baseline_mode_shares=baseline_mode_shares)
        if measure_reductions is not None
        else None
    )
    return DerivedMetrics(
        vmt_reduced=miles,
        co2_tonnes_reduced=co2_tonnes_from_vmt(miles, emission_factor_g_per_mile),
        trips_reduced=trips,
        mode_split=mode_split,
    )
