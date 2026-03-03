# Name: tdm-utils.py
# Purpose: Uitility functions for the tdm-ghg-calculator. 
# Author: David Wasserman
# Last Modified: 3/8/20232026
# Copyright: David Wasserman
# Python Version:   3.6
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
    """Implementation of multiplicative dampening with a maximum value given a passed parameter. 
    Formula: min(X%, 1 - ∏(1 - rᵢ))
        where X% is the cap and rᵢ are the individual reduction values.
     Parameters
     ---------------
     reduction_values - list of decimal numbers (below 1)
     max_reduction_percentage - the maximum possible reduction possible. 
     Returns
     ---------------
     final_value - the dampened result for a GHG calculation reduction."""
    value_series = pd.Series(reduction_values).fillna(0)
    dampened = float(1.0 - (1.0 - value_series).product())
    final_value = min([abs(i) for i in [max_reduction_percentage, dampened] if i is not None])
    if dampened < 0:
        final_value = -(final_value)
    return final_value