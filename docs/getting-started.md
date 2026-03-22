# Getting Started

`tdm_ghg` is a Python library that implements the transportation section of the [CAPCOA 2024 Handbook](https://www.caleemod.com/handbook/index.html) for analyzing GHG emission reductions from Transportation Demand Management (TDM) strategies.

## Installation

Clone the repository and ensure you have Python 3.6+:

```bash
git clone https://github.com/<org>/tdm-ghg-calculator.git
cd tdm-ghg-calculator
```

The library depends on `pandas`. Install it with:

```bash
pip install pandas
```

## Core Concepts

### Negative Value Convention

All GHG reductions are expressed as **negative decimal fractions**:

| Value   | Meaning            |
|---------|--------------------|
| `-0.14` | 14% GHG reduction  |
| `-0.30` | 30% GHG reduction  |
| `0.0`   | No change          |

### Scales

CAPCOA defines two analysis scales. Measures from different scales **must never be combined**:

| Scale              | Description                              |
|--------------------|------------------------------------------|
| `PROJECT_SITE`     | Individual development projects or sites |
| `PLAN_COMMUNITY`   | Area-wide plans or community programs    |

### Location Types

Based on Salon (2014) census-tract-level neighborhood typology:

| Location   | Description                                     |
|------------|-------------------------------------------------|
| `URBAN`    | Urban areas (low transit, central city, high transit) |
| `SUBURBAN` | Suburbs (multifamily, single-family)            |
| `RURAL`    | Rural and rural-in-urban areas                  |

### Land Use Types

| Land Use      | Description            |
|---------------|------------------------|
| `RESIDENTIAL` | Residential projects   |
| `COMMERCIAL`  | Commercial projects    |
| `MIXED`       | Mixed-use development  |
| `SCHOOL`      | School facilities      |

### Subsectors and Caps

Each subsector has a maximum combined reduction cap per CAPCOA guidance:

| Scale            | Subsector            | Cap   | Measures                     |
|------------------|----------------------|-------|------------------------------|
| Project/Site     | Land Use             | 65%   | T-1, T-2, T-3, T-4, T-55    |
| Project/Site     | Trip Reduction       | 45%   | T-10 (commute VMT)          |
| Project/Site     | Parking Management   | 35%   | (not yet implemented)        |
| Project/Site     | School Programs      | 72%   | T-40, T-56 (school VMT)     |
| Plan/Community   | Land Use             | 30%   | (not yet implemented)        |
| Plan/Community   | Neighborhood Design  | 10%   | T-20, T-22-A, T-22-B, T-22-D|
| Plan/Community   | Trip Reduction       | 2.3%  | (commute VMT)               |
| Plan/Community   | Parking Management   | 30%   | (not yet implemented)        |
| Plan/Community   | Transit              | 15%   | T-26, T-27, T-28, T-46      |

A **multi-subsector cap of 70%** applies when combining Land Use + Neighborhood Design + Parking + Transit.

### Multiplicative Dampening

When multiple measures are combined, the library uses multiplicative dampening rather than simple addition:

```
Combined reduction = min(cap, 1 - ∏(1 - rᵢ))
```

This accounts for overlapping effectiveness across measures. For example, two 20% reductions combine to 36% (not 40%).

## Quick Start

Create a `TDMContext` to set the analysis context, then call strategies as methods. The context validates that each strategy is applicable (correct scale, location type, and land use) before running it.

```python
from tdm_ghg import TDMContext, Scale, LocationType, LandUseType

ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.RESIDENTIAL,
)

# Call strategies as methods — parameters are passed directly
t1 = ctx.t1_increase_residential_density(proposed_residential_density=25.0)
t3 = ctx.t3_provide_transit_oriented_development(
    transit_mode_share=0.05,
    vehicle_mode_share=0.80,
)

print(f"T-1 reduction: {t1:.2%}")   # -30.00% (capped at measure max)
print(f"T-3 reduction: {t3:.2%}")   # -30.69%

# Combine at the subsector level (multiplicative dampening, capped at 65%)
land_use = ctx.combine_land_use([t1, t3])
print(f"Combined land use: {land_use:.2%}")
```

Calling a strategy in the wrong context raises an error:

```python
# T-1 is residential-only — this raises ValueError on a commercial context
commercial_ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.COMMERCIAL,
)
commercial_ctx.t1_increase_residential_density(proposed_residential_density=25.0)
# ValueError: T-1 (Increase Residential Density) is not applicable to COMMERCIAL land use
```

## Next Steps

- [Usage Examples](usage-examples.md) — end-to-end scenarios for common analyses
- [Measures Reference](measures-reference.md) — detailed docs for all 16 measures
- [Architecture](architecture.md) — how the library is structured
