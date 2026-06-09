# Name: utils.py
# Purpose: Utility functions for the tdm-ghg-calculator.
# Author: David Wasserman
# Copyright: David Wasserman
# Python Version:   3.9+
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
# Import Modules

import pandas as pd

def multiplicative_dampening(reduction_values, max_reduction_percentage=None):
    """Combine signed reduction fractions using CAPCOA multiplicative dampening.

    This library follows the convention that **negative values are reductions**
    (e.g. ``-0.10`` = 10% reduction) and positive values are increases. Each
    value ``rᵢ`` scales the remaining VMT by ``(1 + rᵢ)``, so the combined
    effect is::

        combined = ∏(1 + rᵢ) - 1

    which is the signed-convention form of the CAPCOA rule
    ``1 - ∏(1 - |rᵢ|)``. Combining reductions this way yields a result whose
    magnitude is *smaller* than the arithmetic sum (dampening), avoiding the
    double-counting of overlapping reductions.

    The optional cap is a maximum **reduction**. It is applied as a one-sided
    floor: a combined *reduction* (negative result) is never more negative than
    ``-|max_reduction_percentage|``. A combined *increase* (positive result) is
    returned unchanged, since a reduction cap does not bound an increase.

    Parameters
    ----------
    reduction_values : iterable of float
        Signed reduction fractions (negative = reduction). ``NaN`` entries are
        treated as 0.0 (no effect).
    max_reduction_percentage : float, optional
        Maximum allowable reduction. Either sign is accepted; only its
        magnitude is used. ``None`` (default) means uncapped.

    Returns
    -------
    float
        The combined (dampened) reduction fraction. Negative = reduction.
        Returns ``0.0`` for an empty input.

    Examples
    --------
    >>> multiplicative_dampening([-0.10, -0.08])
    -0.172
    >>> multiplicative_dampening([-0.10, -0.08, -0.05], max_reduction_percentage=-0.15)
    -0.15
    """
    value_series = pd.Series(reduction_values, dtype="float64").fillna(0.0)
    combined = float((1.0 + value_series).prod() - 1.0)
    if max_reduction_percentage is not None and combined < 0.0:
        combined = max(combined, -abs(max_reduction_percentage))
    return combined