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
* **Mode shift** — how the avoided SOV (single-occupancy vehicle) travel
  redistributes across the other modes in the :class:`~tdm_ghg.context.Mode`
  taxonomy (HOV / Transit / Bike / Walk / WFH / Other).

Every function here is a pure back-calculation: it takes a signed reduction
fraction (or a ``{measure: fraction}`` mapping) plus supplementary inputs and
returns a derived quantity. Reductions are returned as positive magnitudes
(miles, trips, tonnes avoided) regardless of the sign of the input fraction, so
callers may pass the library's negative fractions directly.

Mode shift is driven by explicit measure metadata rather than inferred from
names: each measure declares the modes it shifts travel toward via
``MeasureMetadata.target_modes`` (see ``registry.py``) and whether it implies
any mode shift at all via the derived ``implies_mode_shift`` property
(clean-vehicle measures such as EV charging declare no target modes). A
measure's reduction magnitude is apportioned across its target modes in
proportion to those modes' baseline shares (falling back to an equal split when
no baseline is supplied); SOV is always the source whose share shrinks.

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

from tdm_ghg.context import Mode
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
# Mode shift (metadata-driven — from each measure's declared target_modes)
# --------------------------------------------------------------------------- #

def _apportion(magnitude, target_modes, baseline_mode_shares=None):
    """Split ``magnitude`` across ``target_modes``.

    The split is proportional to each target mode's baseline share (normalized
    within the target set). When ``baseline_mode_shares`` is ``None`` or every
    target mode has zero baseline share, the split is equal.

    Parameters
    ----------
    magnitude : float
        Non-negative amount to apportion (a measure's reduction magnitude).
    target_modes : Collection[Mode]
        Destination modes to split across.
    baseline_mode_shares : Mapping, optional
        Baseline shares keyed by ``Mode`` (or its string value). ``Mode`` is a
        ``str`` enum, so string- and enum-keyed mappings both resolve.

    Returns
    -------
    dict[Mode, float]
        Portion of ``magnitude`` assigned to each target mode.
    """
    modes = list(target_modes)
    if not modes:
        return {}
    total_base = 0.0
    if baseline_mode_shares is not None:
        base = {m: float(baseline_mode_shares.get(m, 0.0)) for m in modes}
        total_base = sum(base.values())
    if total_base > 0:
        return {m: magnitude * base[m] / total_base for m in modes}
    share = magnitude / len(modes)
    return {m: share for m in modes}


def generate_mode_shift_weights(
    measure_reductions,
    baseline_mode_shares=None,
    target_modes_override=None,
):
    """Sum per-mode mode-shift weights across a set of measures.

    For each measure, its target modes come from the registry
    (``MeasureMetadata.target_modes``) unless overridden. Measures with no
    target modes — clean-vehicle measures where ``implies_mode_shift`` is
    ``False`` — contribute nothing. Each measure's reduction magnitude
    (``abs(fraction)``) is apportioned across its target modes in proportion to
    those modes' baseline shares (equal split when no baseline is supplied; see
    :func:`_apportion`), and the contributions are summed per mode.

    Parameters
    ----------
    measure_reductions : Mapping[str, float]
        Mapping of measure ID to its signed reduction fraction.
    baseline_mode_shares : Mapping, optional
        Baseline mode shares keyed by ``Mode`` (or its string value), used for
        the proportional apportionment.
    target_modes_override : Mapping[str, Collection[Mode]], optional
        Per-measure target modes overriding (or, for measures not in the
        registry, supplying) the registered ``target_modes``.

    Returns
    -------
    dict[Mode, float]
        Summed weight per destination mode.
    """
    weights: dict = {}
    override = target_modes_override or {}
    for measure, fraction in measure_reductions.items():
        magnitude = abs(float(fraction))
        if magnitude == 0.0:
            continue
        if measure in override:
            target_modes = override[measure]
        else:
            meta = registry.get(measure)
            target_modes = meta.target_modes if meta is not None else ()
        for mode, amount in _apportion(
            magnitude, target_modes, baseline_mode_shares
        ).items():
            weights[mode] = weights.get(mode, 0.0) + amount
    return weights


@dataclass
class ModeSplit:
    """Result of a mode-shift estimation.

    Attributes
    ----------
    weights : dict[Mode, float]
        Summed mode-shift weight per destination mode.
    shares : dict[Mode, float]
        Normalized weights (each weight / total), summing to 1.0. Empty when
        the total weight is zero.
    total_sov_reduction : float
        Aggregate SOV reduction (sum of ``weights``); the magnitude shifted out
        of SOV into the destination modes.
    apportioned : dict[Mode, float]
        Portion of ``total_sov_reduction`` assigned to each destination mode
        (identical to ``weights``).
    new_mode_shares : dict or None
        Resulting mode shares when ``baseline_mode_shares`` was supplied,
        otherwise ``None``. ``Mode.SOV`` is reduced by ``total_sov_reduction``
        (floored at 0) and each destination mode is incremented by its
        apportionment.
    """
    weights: dict
    shares: dict
    total_sov_reduction: float
    apportioned: dict
    new_mode_shares: Optional[dict] = None


def estimate_mode_split(
    measure_reductions,
    baseline_mode_shares=None,
    target_modes_override=None,
):
    """Estimate how avoided SOV travel redistributes across the other modes.

    Each measure's reduction is apportioned across its declared ``target_modes``
    in proportion to those modes' baseline shares (equal split without a
    baseline) and summed per mode (:func:`generate_mode_shift_weights`). SOV is
    the source: its share shrinks by the total and the destination modes grow.
    The combination is additive; to combine the fractions with CAPCOA
    multiplicative dampening instead, pre-combine them with
    :func:`tdm_ghg.utils.multiplicative_dampening` before calling.

    Parameters
    ----------
    measure_reductions : Mapping[str, float]
        Mapping of measure ID to its signed reduction fraction.
    baseline_mode_shares : Mapping, optional
        Baseline mode shares keyed by ``Mode`` (or its string value), including
        a ``Mode.SOV`` entry, e.g. ``{Mode.SOV: 0.80, Mode.HOV: 0.05,
        Mode.TRANSIT: 0.05, Mode.BIKE: 0.05, Mode.WALK: 0.05}``. When supplied,
        ``ModeSplit.new_mode_shares`` is computed and the per-measure
        apportionment is weighted by these shares.
    target_modes_override : Mapping[str, Collection[Mode]], optional
        Per-measure target modes overriding the registered classification.

    Returns
    -------
    ModeSplit
        The weights, normalized shares, aggregate SOV reduction, per-mode
        apportionment, and (optionally) resulting mode shares.
    """
    weights = generate_mode_shift_weights(
        measure_reductions,
        baseline_mode_shares=baseline_mode_shares,
        target_modes_override=target_modes_override,
    )
    total = sum(weights.values())
    shares = {mode: w / total for mode, w in weights.items()} if total > 0 else {}

    new_mode_shares = None
    if baseline_mode_shares is not None:
        new_mode_shares = dict(baseline_mode_shares)
        new_mode_shares[Mode.SOV] = max(
            0.0, float(baseline_mode_shares.get(Mode.SOV, 0.0)) - total
        )
        for mode, amount in weights.items():
            new_mode_shares[mode] = (
                float(baseline_mode_shares.get(mode, 0.0)) + amount
            )

    return ModeSplit(
        weights=weights,
        shares=shares,
        total_sov_reduction=total,
        apportioned=dict(weights),
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
