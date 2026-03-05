# Name: mitigations.py
# Purpose: Contains main functions used to determine GHG impact of travel demand management 
# across those represented in CAPCOA's 2024 Handbook for Analyzing GHG Emission Reductions,
# Assessing Climate Vulnerabilities, and Advancing Health and Equity.
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

def t20_expand_bikeway_network(existing_bikeway_miles_in_community,
    proposed_bikeway_miles_in_community,bike_mode_share,vehicle_mode_share,
    average_oneway_bicycle_trip_length, average_oneway_vehicle_trip_length,
    elasticity_of_bike_commuters_per_pop =.25):
    """This measure will increase the length of a city or community bikeway
    network. A bicycle network is an interconnected system of bike lanes,
    bike paths, bike routes, and cycle tracks. Providing bicycle
    infrastructure with markings and signage on appropriately sized
    roads with vehicle traffic traveling at safe speeds helps to improve
    biking conditions (e.g., safety and convenience). In addition,
    expanded bikeway networks can increase access to and from transit
    hubs, thereby expanding the “catchment area” of the transit stop or
    station and increasing ridership. This encourages a mode shift from
    vehicles to bicycles, displacing VMT and thus reducing GHG
    emissions. When expanding a bicycle network, a best practice is to
    consider bike lane width standards from local agencies, state
    agencies, or the National Association of City Transportation Officials’
    Urban Bikeway Design Guide.
    Applies to commute vehicle travel in community.
    Parameters
    -------------
    existing_bikeway_miles_in_community - existing bikeway miles
    proposed_bikeway_miles_in_community - proposed bikeway miles with measure
    bike_mode_share -existing bike mode share in community
    vehicle_mode_share - existing vehicle mode share in community
    average_oneway_bicycle_trip_length - average bike trip length
    average_oneway_vehicle_trip_length - average vehicle trip length
    elasticity_of_bike_commuters_per_pop - A multivariate analysis of the impacts of bike lanes on cycling levels in the 100
    largest U.S. cities found that a 0.25 percent increase in commute cycling occurs for
    every 1 percent increase in bike lane distance (Pucher & Buehler 2011). 
    Returns
    -------------
    ghg_reduction - ghg reduction from employee commute vehicle travel in community
    """
    bike_way_ratio = (proposed_bikeway_miles_in_community - existing_bikeway_miles_in_community)/existing_bikeway_miles_in_community
    numerator = bike_way_ratio * bike_mode_share * average_oneway_bicycle_trip_length * elasticity_of_bike_commuters_per_pop
    denominator = vehicle_mode_share * average_oneway_vehicle_trip_length
    ghg_reduction = -1 * numerator/denominator
    return max(ghg_reduction,-.005)
