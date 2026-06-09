# Name: utils.py
# Purpose: Utility functions for the tdm-ghg-calculator.
# Author: David Wasserman
# Copyright: David Wasserman
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
# Import Modules

import pandas as pd

def multiplicative_dampening(reduction_values, max_reduction_percentage=None):
    """Combine signed reduction fractions via multiplicative dampening.

    Negative values are reductions (``-0.10`` = 10% reduction); positive
    values are increases. Each value scales remaining VMT by ``(1 + r)``::

        combined = ∏(1 + rᵢ) - 1

    The optional cap is a one-sided floor on reductions: a net reduction is
    clamped to ``-|max_reduction_percentage|``, while a net increase passes
    through unchanged. ``NaN`` entries count as no effect; empty input
    returns ``0.0``.

    Examples
    --------
    >>> multiplicative_dampening([-0.10, -0.08])
    -0.172
    >>> multiplicative_dampening([-0.10, -0.08, -0.05], -0.15)
    -0.15
    """
    value_series = pd.Series(reduction_values, dtype="float64").fillna(0.0)
    combined = float((1.0 + value_series).prod() - 1.0)
    if max_reduction_percentage is not None and combined < 0.0:
        combined = max(combined, -abs(max_reduction_percentage))
    return combined