# Architecture

## Module Overview

```
tdm_ghg/
├── __init__.py       Public API — re-exports everything below
├── context.py        Scale, LocationType, LandUseType, TDMContext
├── registry.py       MeasureMetadata, MeasureRegistry, @register_measure
├── mitigations.py    16 CAPCOA measure functions (decorated with @register_measure)
├── subsectors.py     Subsector caps, multiplicative dampening constants
└── utils.py          multiplicative_dampening utility
```

## Design Principles

1. **Context validates, methods execute.** `TDMContext` holds the analysis context (scale, location, land use) and exposes every strategy as a method. When you call a strategy method, the context checks applicability (scale, location type, land use type) before delegating to the underlying function. Strategy parameters are passed directly to the method call — the context never stores them.

2. **Explicit combination.** The user calls individual strategy methods and collects results, then passes them to a `combine_*` method that applies multiplicative dampening with the correct CAPCOA subsector cap. This makes the set of strategies being combined visible and controllable.

3. **Mutual exclusivity is the caller's responsibility.** Since you choose which methods to call, you naturally avoid combining mutually exclusive strategies (e.g., calling T-55 means you simply don't call T-1 or T-3).

## Data Flow

```
TDMContext(scale, location_type, land_use_type)
    │
    ├─ ctx.t1_increase_residential_density(...)
    │      → validates context (scale, location, land use)
    │      → calls underlying measure function
    │      → returns GHG reduction (negative fraction)
    │
    ├─ ctx.t3_provide_transit_oriented_development(...)
    │      → validates and returns reduction
    │
    └─ ctx.combine_land_use([t1, t3])
           → multiplicative_dampening(reductions, -subsector_cap)
           → combined subsector GHG reduction
```

## Module Details

### `context.py`

Defines the three dimensions that determine which CAPCOA measures apply:

- **`Scale`** — `PROJECT_SITE` or `PLAN_COMMUNITY` (enum, str mixin)
- **`LocationType`** — `URBAN`, `SUBURBAN`, or `RURAL` (enum, str mixin)
- **`LandUseType`** — `RESIDENTIAL`, `COMMERCIAL`, `MIXED`, or `SCHOOL` (enum, str mixin)
- **`TDMContext`** — holds the three enums above; exposes strategy methods and combine methods

```python
ctx = TDMContext(
    scale=Scale.PROJECT_SITE,
    location_type=LocationType.URBAN,
    land_use_type=LandUseType.RESIDENTIAL,
)
```

**Strategy methods** on `TDMContext`:

Each registered measure becomes a method on the context (e.g., `ctx.t1_increase_residential_density(...)`). Before calling the underlying function, the method checks:
- Is the context's `scale` correct for this measure?
- Is the context's `location_type` in the measure's allowed set?
- Is the context's `land_use_type` in the measure's allowed set (if restricted)?

If any check fails, a `ValueError` is raised with a descriptive message.

**Combine methods** on `TDMContext`:

| Method                        | Subsector            | Cap applied |
|-------------------------------|----------------------|-------------|
| `combine_land_use()`          | Land Use             | Per scale   |
| `combine_trip_reduction()`    | Trip Reduction       | Per scale   |
| `combine_neighborhood_design()` | Neighborhood Design | 10%        |
| `combine_transit()`           | Transit              | 15%         |
| `combine_school_programs()`   | School Programs      | 72%         |
| `combine_parking_management()`| Parking Management   | Per scale   |
| `combine_multi_subsector()`   | Cross-subsector      | 70%         |

Each takes a list of reduction values and applies `multiplicative_dampening` with the appropriate cap from `SUBSECTOR_CAPS`.

### `registry.py`

Provides the `@register_measure` decorator and the global `registry` singleton.

**`MeasureMetadata`** stores:

| Field                    | Type                       | Description                              |
|--------------------------|----------------------------|------------------------------------------|
| `measure_id`             | `str`                      | CAPCOA ID (e.g., `"T-1"`)               |
| `name`                   | `str`                      | Human-readable name                      |
| `subsector`              | `str`                      | Subsector key (e.g., `"land_use"`)       |
| `scale`                  | `Scale`                    | `PROJECT_SITE` or `PLAN_COMMUNITY`       |
| `location_types`         | `frozenset[LocationType]`  | Where the measure applies                |
| `land_use_types`         | `frozenset[LandUseType]?`  | Land uses (None = all)                   |
| `measure_max`            | `float`                    | Individual cap (positive fraction)       |
| `mutually_exclusive_with`| `frozenset[str]`           | Conflicting measure IDs                  |
| `func`                   | `Callable`                 | The underlying measure function          |

**`MeasureRegistry`** methods:

| Method         | Description                                                    |
|----------------|----------------------------------------------------------------|
| `register()`   | Add a measure (called automatically by `@register_measure`)    |
| `get(id)`      | Look up a single measure by ID                                 |
| `measures`     | Property returning all registered measures                     |
| `filter()`     | Return measures matching a context, subsector, and exclusions  |

The registry populates at import time when `mitigations.py` is loaded.

### `mitigations.py`

Contains 16 CAPCOA measure functions, each decorated with `@register_measure`. Functions are organized by subsector:

| Subsector            | Measures                                             |
|----------------------|------------------------------------------------------|
| Land Use             | T-1, T-2, T-3, T-4, T-55                            |
| Trip Reduction       | T-10                                                 |
| Neighborhood Design  | T-20, T-22-A, T-22-B, T-22-D                        |
| Transit              | T-26, T-27, T-28, T-46                              |
| School Programs      | T-40, T-56                                           |

Each function:
- Takes project-specific inputs plus CAPCOA default values as optional parameters
- Returns a negative decimal fraction representing GHG reduction
- Enforces its individual measure cap internally via `max(result, -cap)`

### `subsectors.py`

Defines the CAPCOA subsector caps:

| Scale            | Subsector            | Cap   |
|------------------|----------------------|-------|
| Project/Site     | Land Use             | 65%   |
| Project/Site     | Trip Reduction       | 45%   |
| Project/Site     | Parking Management   | 35%   |
| Project/Site     | School Programs      | 72%   |
| Plan/Community   | Land Use             | 30%   |
| Plan/Community   | Neighborhood Design  | 10%   |
| Plan/Community   | Trip Reduction       | 2.3%  |
| Plan/Community   | Parking Management   | 30%   |
| Plan/Community   | Transit              | 15%   |

Cross-subsector cap (Land Use + Neighborhood Design + Parking + Transit): **70%**

### `utils.py`

**`multiplicative_dampening(reduction_values, max_reduction_percentage=None)`**

Combines multiple reductions using:

```
result = min(|cap|, 1 - ∏(1 - rᵢ))
```

Preserves sign (negative values remain negative). Uses `pandas.Series` for the product calculation.

## Mutual Exclusivity

Some measures cannot be combined per CAPCOA guidance:

| Measure | Cannot combine with  | Reason                                     |
|---------|----------------------|--------------------------------------------|
| T-1     | T-55                 | Both address residential density/location  |
| T-3     | T-55                 | Both address residential location benefits |
| T-26    | T-28                 | BRT subsumes frequency improvements        |
| T-27    | T-28                 | BRT subsumes roadway treatments            |
| T-46    | T-28                 | BRT subsumes shelter improvements          |

Since strategies are called as explicit methods, mutual exclusivity is managed by the caller — simply choose which strategies to call. The `mutually_exclusive_with` field on `MeasureMetadata` documents these constraints for reference, and `ctx.applicable_measures()` can be used to check them programmatically.
