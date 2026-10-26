# `pipeline/lib` — contract (Phase 2, step 1)

Status: draft for the test-writer and the code-writer, 2026-10-25. Derived from METHODS §10–§11 and SCHEMA §3–§6. Where this file and METHODS disagree, METHODS wins and this file is a bug.

Each module listed here is a pure function library. None of them reads files implicitly, uses the network, or keeps global state. Errors raise `LibError`, a subclass of `ValueError` defined in `pipeline/lib/__init__.py`, with a message naming the offending input.

---

## 1. `bounds.py` — low / central / high arithmetic (METHODS §11.1)

### 1.1 `Bounds`

`Bounds(low: float, central: float, high: float, nd_floored: bool = False)` is a frozen dataclass.

- **Construction:**
  - Raise `LibError` unless `0 ≤ low ≤ central ≤ high` and all three values are finite.
  - `nd_floored` records that a "not detected" floor dominated the low side (§1.4).
- **Equality:** exact (dataclass default). The tests use `pytest.approx` on the fields.
- `Bounds.exact(x)` returns `Bounds(x, x, x)`.
- `Bounds.not_detected(dl)` returns `Bounds(0.0, dl/2, dl, nd_floored=True)`. A non-detect's central value is half the detection limit, its low bound is 0, and its high bound is the limit.
- `b.scale(k)` multiplies all three values by a constant `k ≥ 0`. It keeps `nd_floored` and raises if `k < 0`.

### 1.2 `product(*terms: Bounds) -> Bounds`

These are independent multiplicative terms: activity × factor × fraction, and so on.

- **Central** is the product of the centrals.
- **Zero central.** If any central is 0, return `Bounds(0, 0, h)`. Here `h` is the product of every term's `high` (a conservative upper bound), and `nd_floored` is `True`.
- **High side:**

$$\ln\frac{x_h}{x_c}=\sqrt{\sum_i \ln^2\frac{h_i}{c_i}}$$

- **Low side:**

$$\ln\frac{x_c}{x_l}=\sqrt{\sum_i \ln^2\frac{c_i}{l_i^{*}}}$$

  where $l_i^{*}=l_i$ if $l_i>0$, and $l_i^{*}=10^{-3}c_i$ (the **floor**) if $l_i=0$.
- **Floor dominance.** If floored terms contribute more than half of $\sum_i\ln^2(c_i/l_i^{*})$, set the result's `low` to 0 and `nd_floored=True`. Also set `nd_floored=True` if any input has `nd_floored`.
- **Exact terms.** Terms with `low = central = high` contribute 0 to both sums.
- **Single term.** With one term the result equals that term, apart from the floor rule.
- **No terms.** `product()` with no arguments raises `LibError`.

### 1.3 Sums

- **`sum_independent(terms) -> Bounds`:**
  - central = $\sum c_i$
  - high = $c + \sqrt{\sum (h_i-c_i)^2}$
  - low = $c - \sqrt{\sum (c_i-l_i)^2}$
  - `nd_floored` is the OR of the inputs.
- **`sum_correlated(terms) -> Bounds`:** fully correlated terms, so the deviations add linearly. low = $\sum l_i$ and high = $\sum h_i$.
- **`sum_grouped(terms, keys) -> Bounds`:**
  - Terms that share a key (the same `factor_id`) are summed with `sum_correlated` inside each key.
  - The per-key results are then combined with `sum_independent`.
  - `len(terms) == len(keys)`, otherwise raise.
- **Empty inputs.** An empty sum returns `Bounds.exact(0.0)`.

### 1.4 Invariants (tests must check these)

- low ≤ central ≤ high holds for every output.
- `product(a, Bounds.exact(k))` equals `a.scale(k)`, apart from rounding.
- `product` is order-independent.
- `sum_independent` low ≥ $\sum l_i$ and high ≤ $\sum h_i$. Quadrature is never wider than the linear sum.

---

## 2. `allocation.py` — D6 split of multi-product outputs (METHODS §10)

### 2.1 `shares(products, variant, *, main=None, radio=None) -> dict[str, float]`

- **Input.** `products` maps each product name to `(quantity_t, unit_value)`. `unit_value` is in USD/t or USD1998/t (D39); it is only needed for `alloc:value`.
- **Variants:**

| `variant` | Share of product $p$ |
|---|---|
| `alloc:value` | $q_p v_p / \sum q v$ |
| `alloc:mass` | $q_p / \sum q$ |
| `alloc:main` | 1 for `main`, 0 for the others |
| `alloc:radio` | 1 for `radio`, 0 for the others |

- **Output.** The shares sum to 1 (within 1e-12) and every share is ≥ 0.
- **Raise `LibError`** if:
  - the denominator is 0;
  - any quantity or value is negative;
  - `alloc:main` / `alloc:radio` is used without its named product, or the named product isn't in `products`;
  - the variant is unknown.
- **Missing `unit_value`.** If a product's `unit_value` is `None` and the variant is `alloc:value`, raise `LibError`. Never assume a price.

### 2.2 `split(bounds, shares) -> dict[str, Bounds]`

Applies `Bounds.scale(share)` to each product. Shares are treated as exact; their uncertainty is carried by the D6 bound variants, not by the band.

### 2.3 `attribution_share(cap_added, intensity, production) -> float` (METHODS §10.2)

$$\sigma_c=\frac{\sum_t C_t I_{t,c}}{Q_c}$$

- `cap_added` maps technology to GW. `intensity` maps technology to t/GW. `production` is a float in t.
- Technologies missing from `intensity` contribute 0.
- Raise if `production ≤ 0`.
- If σ > 1, raise `LibError`. Demand cannot exceed world production, so a value above 1 is a data error.

---

## 3. `factors.py` — factor lookup (SCHEMA §4.7, §4.9)

### 3.1 `select(factors, *, year, region, **match) -> dict`

- **Input.** `factors` is an iterable of factor-row dicts (coerced as in §5). `match` gives equality filters on any columns: `stream`, `stage`, `group`, `tier`, `route`, `residue_type`, `driver_series`, `commodity`, `component`, `allocation_variant`.
- **Candidates:**
  - Rows whose `year_from ≤ year ≤ year_to`.
  - Rows that match every key in `match`. A row value of `None` matches only a `None` filter.
  - Rows whose `region` is either `region` itself or `XWL`.
- **Precedence.** An exact-region row beats an `XWL` row.
- **Errors.** Raise `LibError` if no candidate is left, or if more than one row remains at the winning precedence level (ambiguous registry).
- **Return** the selected row.

### 3.2 `apply(driver_value, driver_unit, factor_row) -> Bounds`

- `driver_value` is a `Bounds`. The factor becomes `Bounds(value_low, value_central, value_high)`, using `not_detected` if `below_detection`.
- **Units.**
  - The factor's `unit` must be `Bq/<driver_unit>`, `Bq/a per <driver_unit>`, or `1`. Their products are Bq, Bq/a, and the driver unit respectively.
  - The only allowed conversion is between `TWh` and `GWa` (1 GW·a = 8.766 TWh exactly, using a = 365.25 d). It is applied automatically when needed.
  - Any other unit mismatch raises `LibError`.
- **Return** `product(driver_value, factor)`.

---

## 4. `rows.py` — master rows (SCHEMA §3)

### 4.1 `MASTER_COLUMNS`

The 25 master column names, in SCHEMA order:

`year, stream, substream, stage, product, residue_type, country, group, tier, quantity, unit, value_low, value_central, value_high, below_detection, basis, source_ids, factor_ids, allocation_variant, allocation_rule, embedded_fuel, technology, route, event_id, notes`

### 4.2 `make_row(*, bounds: Bounds, **fields) -> dict`

- Returns a dict with exactly `MASTER_COLUMNS` as keys.
- **Values.** `value_*` come from `bounds`. `below_detection` is `bounds.nd_floored` unless given explicitly.
- **Defaults.** Nullable columns default to `None`. `allocation_variant` defaults to `default`. `embedded_fuel` defaults to `false`.
- **Required fields.** Raise `LibError` if any required field is missing: `year`, `stream`, `substream`, `stage`, `country`, `group`, `tier`, `quantity`, `unit`, `basis`, `source_ids`.
- **List fields.** `source_ids` and `factor_ids` may be given as lists and are joined with `;`.

### 4.3 `write_master(rows, path)`

- **Order.** Rows are sorted by the SCHEMA §3 unique key, in column order, with `None` sorting first.
- **Duplicate keys** raise `LibError`.
- **Floats** are written with `format(x, '.6g')`.
- **Other values.** Booleans are written `true`/`false`. `None` is an empty cell.
- **File format.** UTF-8, `\n` line endings, header row first.
- The output must be **byte-identical** across runs given the same input.

---

## 5. `io.py` — reading tables

`read_table(path) -> list[dict]` reads a CSV and coerces types exactly as the validator does (SCHEMA §6.5: empty cell becomes `None`, typed columns are parsed). The code-writer may import and reuse the validator's coercion helpers. The tests only check the resulting types and values.

---

## 6. Tests

- Tests go in `pipeline/tests/lib/test_*.py`.
- They are written from this file and METHODS §10–§11 only. The test-writer never reads the implementation.
- Every formula above gets at least one hand-computed numeric case. Every `LibError` condition gets a case.
- The §1.4 invariants are checked with a property-style sweep over generated `Bounds`.
- There is no network and no file I/O outside `tmp_path`.

---

## 7. v1.1 resolutions (2026-10-25)

These resolutions follow the spec-blind test review and **override** the sections above where they differ.

1. **`nd_floored` propagation.** Every operation that combines `Bounds` sets `nd_floored` to the OR of its inputs: `product`, `sum_independent`, `sum_correlated`, `sum_grouped`. `product` can additionally set the flag itself through the floor rule.
2. **Negative inputs to `shares`.** Raise `LibError` for any negative quantity or unit value, under every variant, including `alloc:mass`. A negative number is a data error, whether or not the variant uses it.
3. **Variant names.** `shares` accepts only the `alloc:*` tokens. The master-row `allocation_variant` values (`default`, `bound_main`, `bound_radio`) are mapped to tokens by the caller, using `variant_token(allocation_variant, default_token="alloc:value")`, a new function in `allocation.py`:
   - `default` maps to `default_token`.
   - `bound_main` maps to `alloc:main`.
   - `bound_radio` maps to `alloc:radio`.
   - Anything else raises.
   
   `shares(..., "default")` raises.
4. **`make_row` defaults.**
   - `embedded_fuel` defaults to Python `False`.
   - `allocation_variant` defaults to `"default"`.
   - `allocation_rule` defaults to `"none"`.
   - `allocation_rule`, `source_ids` and `factor_ids` may each be given as a list; a list is joined with `;`.
   - An unknown field raises `LibError`.
   - So does passing any `value_*` field alongside `bounds`.
5. **`read_table` errors.** A cell that fails coercion raises `LibError`, and so does an empty cell in a non-nullable master column. The message names the file, line and column. `read_table` returns list columns as Python lists. `write_master` accepts either lists or `;`-joined strings for list columns, so a read–write round trip is byte-stable.
6. **`apply` with `below_detection`.** Use the row's own `value_low`, `value_central` and `value_high`, with `nd_floored=True`. Do **not** rebuild the bounds from `value_high`, because the row already records how the source reported the detection limit.
7. **Zero central in `product`:**
   - If any term is exactly zero (`high == 0`), the result is `Bounds.exact(0.0)`, with its flag following rule 1. This resolves the contradiction for `Bounds.exact(0)`.
   - Otherwise, if any term has `central == 0` but `high > 0`, the result is `Bounds(0, 0, ∏ h_i)` with `nd_floored=True`. This is deliberately conservative, and the module logs a warning.
8. **§1.4 equality.** `product(a, Bounds.exact(k))` equals `a.scale(k)` in its three values. The flags may differ, because `product` can apply the floor rule where `scale` cannot.
9. **Output unit.** Add `result_unit(driver_unit, factor_unit) -> str` to `factors.py`. It returns `"Bq"`, `"Bq/a"` or `driver_unit` according to the §3.2 rules, including the TWh↔GWa case, and raises on a mismatch. `apply` is unchanged and returns only `Bounds`. Callers use `result_unit` to set the master `unit`.
10. **`write_master([])`** writes a header-only file.

---

## 8. v1.2 resolutions (2026-10-25, after independent verification; Steve approved Option A)

These **override** sections 1–7 where they differ.

### 8.1 `nd_floored` follows the schema (supersedes 7.1 and 7.7's flag wording)

SCHEMA §3 and `schema/master.json` require `value_low = 0` whenever `below_detection` is true. The flag therefore means "the low bound is zero because of a non-detect or the floor rule", and cannot be true when low > 0.

- **Constructor.** `Bounds(..., nd_floored=True)` raises `LibError` unless `low == 0`.
- **Combining operations** (`product`, `sum_independent`, `sum_correlated`, `sum_grouped`): output `nd_floored = (result.low == 0) AND (any input is nd_floored OR the floor-dominance rule fired OR the zero-central rule fired)`. A sum of a non-detect and a detected term has low > 0, so its flag is false.
- `scale` keeps the flag (low stays 0 or the flag was already false). `product(a, Bounds.exact(k))` follows the same rule as any product.
- `Bounds.exact(0)` has low 0 and flag false. A product containing an exact-zero term returns `Bounds.exact(0.0)`, flagged only if some input was flagged.

### 8.2 `make_row`

- An explicit `below_detection=True` with `bounds.low > 0` raises `LibError`. An explicit `below_detection=False` with `bounds.nd_floored` true raises `LibError`.
- Explicit `None` for `allocation_variant`, `allocation_rule` or `embedded_fuel` takes the default (`"default"`, `"none"`, `False`).
- `source_ids` given as an empty list or empty string raises `LibError`.
- `year` must be an `int` (not `bool`). Range checks belong to the validator.

### 8.3 `write_master`

- Numeric value columns (`value_low`, `value_central`, `value_high`) are coerced with `float()` before formatting, so an integer-valued input and the same value read back from CSV produce identical bytes.
- A row with a column not in `MASTER_COLUMNS`, or missing any of them, raises `LibError`.
- A non-finite float raises `LibError`.
- Output uses LF endings on every platform (open with `newline="\n"`).
- None sorts before any value in each key column; this is explicit, not "falsy first".

### 8.4 `read_table` (F7, F8)

- The type maps cover every table the validator knows: master, factors, commodity_factors, activity, baselines, events (`lat`, `lon`, `mass_t`, `activity_*_bq` as float; `is_accident`, `military` as bool; `to_tiers` as list), countries (`valid_from`, `valid_to` as int), sources (`rank` as int), reference bands (`rel_*` as float; `applies_to` as list), residue_types (`streams` as list). The code-writer takes these from `pipeline/validate.py`.
- `allocation_rule`, `source_ids`, `factor_ids` are list columns: `read_table` returns lists; `write_master` accepts lists or `;`-joined strings.
- A data row whose width differs from the header raises `LibError` naming file and line. A duplicate header name raises `LibError`.

### 8.5 `master_unit(result_unit, kind) -> str` (new, in `factors.py`)

`kind` is `"flow"` or `"stock"`. `"flow"` maps `"Bq"` to `"Bq/a"` and leaves `"Bq/a"` unchanged. `"stock"` leaves `"Bq"` unchanged and raises `LibError` for `"Bq/a"`. Any other result unit passes through unchanged. Any other `kind` raises. The caller decides the kind; the library never guesses.

### 8.6 Hardening

- **Overflow and underflow.** Any non-finite result from `product`, `sum_*`, `shares` or `split` raises `LibError` (including `OverflowError` from internals and a non-finite share total). A `product` whose central underflows to 0 while every term's central is > 0 raises `LibError`.
- **Types.** Wrong argument types raise `LibError`, never `TypeError` or `AttributeError`: non-`Bounds` terms, non-numeric or `bool` numbers, non-string units or years, non-mapping `products`, non-iterable inputs, unhashable group keys, non-string variant.
- **Numbers.** `Bounds` rejects `bool` values and normalises `-0.0` to `0.0`.
- **`split`.** Each share must be in `[0, 1 + 1e-12]`, otherwise `LibError`.
- **`apply`.** A factor row's `below_detection` must be `bool` or `None`; any other type (including the string `"false"`) raises `LibError`.
- **`attribution_share`.** Tolerance 1e-12 above 1 is clamped to exactly 1.0; anything larger raises.

### 8.7 Documented limitation

A term built from two factors cannot express two `factor_id` keys in `sum_grouped`. Stream scripts must split such terms so each term has one `factor_id`, or pass the shared key explicitly. This is not an API change.

### 8.8 Verification round 2 (2026-10-25)

Added after the second independent check. These extend 8.6.

1. **Huge integers.** Any Python `int` too large for a float (for example `10**400`) passed as a number to `Bounds`, `shares`, `attribution_share`, `split`, or as a `value_*` cell in `write_master` raises `LibError`, never `OverflowError`.
2. **`source_ids` / `factor_ids` items.** A list item that is empty or whitespace-only raises `LibError` in `make_row` (this extends 8.2's empty-list rule).
3. **`shares` named products.** `main` and `radio` must be `str` (or `None`), otherwise `LibError`.
4. **File I/O.** `read_table` and `write_master` with a path that is not `str` or `os.PathLike`, a directory, or an unreadable or unwritable location raise `LibError` naming the path. `read_table` of an empty file raises `LibError`.
5. **`write_master` value columns.** A `bool` in a `value_*` column raises `LibError`.
6. **`Bounds`** rejects any `nd_floored` that is not a `bool` (including `None`, `"yes"`, `1`) with `LibError`.
7. **`make_row` required string fields.** `stream`, `substream`, `stage`, `country`, `group`, `tier`, `unit`, `basis`, `quantity` must be `str`, and `embedded_fuel` must be `bool`; otherwise `LibError`. Explicit `None` for a required field raises `LibError`.
8. **Documented, not enforced.** `write_master` does not check `below_detection => value_low == 0` for raw dicts (the validator rule R02 is the backstop; `make_row` does enforce it). A factor unit written `Bq/a` without "per" is read as Bq per driver unit `a`; write annual factors as `Bq/a per <driver_unit>`.
