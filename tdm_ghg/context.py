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
"""Context classes for TDM GHG calculations.

A TDMContext captures the three dimensions that determine which CAPCOA
transportation measures are applicable to a given analysis:

- Scale: Project/Site vs. Plan/Community (measures from different scales
  must never be combined per CAPCOA guidance).
- LocationType: Urban, Suburban, or Rural (census-tract-level development
  context per Salon 2014 neighborhood typology).
- LandUseType: The primary land use being analyzed.

The ``params`` dict maps parameter names (matching function argument names
in mitigations.py) to their values. The subsector orchestrators use
``inspect`` to pull only the relevant parameters for each measure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Scale(str, Enum):
    """Geographic scale of the TDM analysis."""
    PROJECT_SITE = "project_site"
    PLAN_COMMUNITY = "plan_community"


class LocationType(str, Enum):
    """Locational context based on census-tract development level.

    Derived from Salon (2014) eight neighborhood types:
      - SUBURBAN: suburb with multifamily housing; suburb with single-family homes
      - URBAN: urban low transit; central city urban; urban high transit
      - RURAL: rural; rural-in-urban
    """
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"


class LandUseType(str, Enum):
    """Primary land use type being analyzed.

    Used to filter measures that are restricted to specific land uses
    (e.g., T-1 residential density only applies to RESIDENTIAL projects;
    T-2 job density only applies to COMMERCIAL projects).
    """
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED = "mixed"
    SCHOOL = "school"


@dataclass
class TDMContext:
    """Context for a TDM GHG reduction analysis.

    Parameters
    ----------
    scale : Scale
        Whether this is a Project/Site or Plan/Community analysis.
        Measures from different scales must never be combined.
    location_type : LocationType
        Urban, suburban, or rural development context.
    land_use_type : LandUseType
        Primary land use type. Measures restricted to specific land uses
        (e.g., residential-only T-1) will be filtered out when the
        context land use does not match.
    params : dict[str, Any]
        Flat dictionary mapping parameter names to values. Keys must
        match the argument names of the measure functions in
        mitigations.py exactly. Measures whose required parameters are
        absent from this dict will be skipped by the orchestrators.

    Notes
    -----
    Mutual exclusivity between measures (e.g., T-55 cannot be combined
    with T-1 or T-3; T-28 excludes T-26/T-27/T-46) is not enforced
    automatically. Use the ``excluded_measure_ids`` argument on subsector
    orchestration functions to handle these constraints explicitly.
    """
    scale: Scale
    location_type: LocationType
    land_use_type: LandUseType
    params: dict[str, Any] = field(default_factory=dict)
