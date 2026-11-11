# `pipeline/lib` — contract (Phase 2, step 1)

Status: draft for the test-writer and the code-writer, 2026-10-25. **Current version v1.6 (2026-11-11, D74): §12 adds the `ore_type` match key.** Derived from METHODS §10–§11 and SCHEMA §3–§6. Where this file and METHODS disagree, METHODS wins and this file is a bug.

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

## 9. v1.3 (2026-10-27, Steve approved): mass factors in `apply`

Needed by Task 2.5 (geothermal scale per GW·a, wood fuel per m³) and likely by later streams.

1. **New factor-unit form `t/<driver_unit>`** (tonnes per driver unit). `apply` returns the driver times the factor in **tonnes**, so `result_unit(driver_unit, "t/<u>")` is `"t"`. Example: driver 70 GWa, factor `t/GWa` 1/10/100 → result in t. Example: driver m³, factor `t/m3` → t.
2. The same driver conversion as the Bq forms applies: only `TWh` ↔ `GWa` is converted automatically (so a `t/GWa` factor accepts a `TWh` driver and vice versa). Any other mismatch raises `LibError`.
3. Parsing: the unit string, stripped, starting with `t/` followed by a non-empty driver unit. `t/` alone, `t` alone, `kg/<u>`, `Mt/<u>` and `t per <u>` are **unsupported** and raise `LibError` (one mass unit only, to keep units unambiguous).
4. `master_unit("t", kind)` returns `"t"` unchanged (revised 2026-10-27 after test review: v1.2 passes every non-Bq unit through, and a special case for `t` would be inconsistent with `GWa`, `TWh` and `1`). Keeping masses out of master rows is the stream script's job, backstopped by the validator.
5. Everything else in `apply` is unchanged: flags, `below_detection`, bounds arithmetic via `product`.
6. Clarifications (test review): surrounding whitespace is stripped before parsing; whitespace after the slash (`t/ GWa`) is unsupported; `t/t` is unsupported (a mass ratio is written as unit `1`).

## 10. v1.4 (2026-10-27, Steve approved): `substream` match key

Needed by Task 2.3 (conventional / unconventional / oil_sands rows share every other key) and available to every stream.

1. `select` accepts `substream` as a match key (added to the allowed set). Semantics are those of every other key: **exact equality** with the row's `substream` cell. A row with an empty `substream` matches only `substream=""` (or a call that does not pass `substream` at all). There is no wildcard.
2. Precedence is unchanged: exact region beats `XWL`; ambiguity at the winning level raises `LibError`.
3. `read_table` reads the factor-file `substream` column as a string (empty cell → `""`, never `None` or NaN), like `group`, `tier`, `route`, `residue_type`.
4. Nothing else changes; a call that does not pass `substream` behaves exactly as in v1.3, whatever the rows hold.

## 11. v1.5, approved (D72; drafted 2026-11-05, approved by Steve 2026-11-06): gzipped stream outputs

Steve approved storing the stream outputs gzipped (2026-11-05). This section fixes how. It **overrides** §4.3 and §5 where they differ, and it goes with SCHEMA v2.5 (text in §11.9). Decision D72 (confirmed). Every choice marked **Recommended** below is the adopted one; the alternatives are kept for the record. The validator code `F04` is confirmed. The second half of D72, a zpaqfranz snapshot of the untracked raw inputs, is specified in `docs/DATA_ARCHIVE.md`; Steve rejected DVC.

**Why.** The committed master files are 3.7 / 17 / 47 / 60 MB raw (coal / nuclear / oil_gas / other). GitHub warns above 50 MB per file and refuses above 100 MB. `other.csv` is already over the warning, and `oil_gas.csv` is close. Gzipped, all eight stream files (master plus pre-1950) total 7.8 MB, against 132.3 MB raw (16.9×).

### 11.1 Measurements (2026-11-05)

Measured on the 2-core x86_64 sandbox with Python 3.13.16 and zlib 1.3, single process. The scripts are in the session scratchpad, not in the repo.

| File | Raw bytes | gzip -6 | gzip -9 | Ratio at 9 |
|---|---:|---:|---:|---:|
| `data/streams/coal.csv` | 3,709,408 | 291,921 | 279,674 | 13.3× |
| `data/streams/nuclear.csv` | 17,465,942 | 1,492,695 | 1,414,078 | 12.4× |
| `data/streams/oil_gas.csv` | 46,737,887 | 2,116,914 | 2,054,709 | 22.7× |
| `data/streams/other.csv` | 60,110,017 | 3,955,360 | 3,786,125 | 15.9× |
| `data/streams_pre1950/coal.csv` | 3,589,361 | 244,214 | 227,822 | 15.8× |
| `data/streams_pre1950/nuclear.csv` | 18,516 | 1,170 | 1,110 | 16.7× |
| `data/streams_pre1950/oil_gas.csv` | 563,678 | 45,968 | 43,165 | 13.1× |
| `data/streams_pre1950/other.csv` | 79,183 | 5,569 | 5,288 | 15.0× |
| **Total** | **132,273,992** | **8,153,811** | **7,811,971** | **16.9×** |

Timings for `other.csv` (60 MB, 164,912 rows):

- **Compression.** Level 9 takes 1.00–1.03 s (one run under load took 2.1 s). Level 6 takes 0.68–0.79 s.
- **Decompression.** 0.12–0.15 s.
- **The rest of the pipeline is slower.** `read_table` on the plain file takes 5.0 s, and plain `write_master` of the same rows takes 5.5 s. `csv.reader` over a gzip text stream runs as fast as over the plain file (1.00 s vs 1.02 s).
- **Round trip.** `read_table` → `write_master` of the committed `other.csv` gives byte-identical output.

Determinism findings:

1. **Fixed header.** `gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=BytesIO(), mtime=0)` and `gzip.compress(data, 9, mtime=0)` give identical bytes. Both start with the header `1f 8b 08 00 00 00 00 00 02 ff`: no FNAME flag, MTIME 0, XFL 2, OS 255.
2. **Unsafe options.** `mtime=None` (the current time) changes the bytes. So does a non-empty `filename`, and `gzip.open(path, "wb")` takes the filename from the path. With either, writing to scratch `0.csv.gz` and to the committed `coal.csv.gz` would give different bytes.
3. **Chunking is safe.** Feeding the same bytes in 8 KiB, 64 KiB or 1 MiB `write()` calls gives the same output as one call.
4. **Wrapping is not.** A `csv.writer` → `io.TextIOWrapper` → `GzipFile` chain gives output 6 bytes longer than the one-shot form. Closing the wrapper triggers a `Z_SYNC_FLUSH`, which adds an empty stored block. The output is still deterministic, but whether a flush happens depends on how the code is written.
5. **zlib versions differ.** Compressed bytes are guaranteed only for the same zlib implementation and version. zlib-ng, or a different zlib release, can produce different but equally valid streams. Nothing may therefore depend on compressed bytes matching across machines (see 11.5).

### 11.2 Which files are gzipped

| Files | Form | |
|---|---|---|
| `data/streams/<stream>.csv` (master) | gzipped | **Recommended.** These are the large files (up to 60 MB). Nobody reads them by eye in a diff. |
| `data/streams_pre1950/<stream>.csv` | gzipped | **Recommended.** `coal` is 3.6 MB raw. One rule for every stream output is simpler than a size threshold. The other three are small, but treating them differently would only add a rule. |
| `research/<stream>/build_log.csv` | **plain** | **Recommended.** These are small (0.7–137 kB) and reviewed by people in diffs. They stay plain CSV, written by each stream's unchanged `write_log`. |
| `data/factors/*`, `data/activity/*`, `data/reference/*`, `data/*.csv` | plain | Unchanged. These are hand-curated inputs. |
| `build/master.csv` (Task 3.1) | not decided here | It is a derived output under `build/`. When Task 3.1 specifies it, the reader and validator already accept either form (11.3, 11.6). |

*Alternatives considered.*

- **Gzip master files only.** This was rejected: coal pre-1950 would stay at 3.6 MB, and there would be two conventions for one kind of file.
- **Git LFS.** This was rejected because it needs extra tooling and remote quota, and it breaks plain `git clone` reproducibility.
- **Splitting files by decade.** This was rejected: it changes the SCHEMA §3 "one file per stream" contract and still grows linearly.

### 11.3 Naming, and accepting both forms

1. **Name.** A gzipped stream output is named `<stream>.csv.gz`, for example `data/streams/coal.csv.gz` and `data/streams_pre1950/coal.csv.gz`.
2. **Detection by suffix only.** A path whose final suffix is `.gz` (case-sensitive) is read and written as gzip. Any other path is plain. The library does not sniff file contents.
   - A `.gz` path that is not valid gzip raises `LibError` in `read_table`, and is reported as `F03` by the validator.
   - A gzip file named `.csv` fails UTF-8 decoding and is reported the same way.
   - *Alternative:* magic-byte sniffing. This was rejected because the format would then not be visible from the name.
3. **Both forms stay supported permanently.** `read_table`, `write_master` and the validator accept both `.csv` and `.csv.gz` with no deprecation date.
   - The validator's test fixtures (`pipeline/tests/conftest.py`, `test_validate.py`, `test_schema_v22.py`), the stream test fixtures (`written`) and `build/master.csv` are plain, and should stay plain.
   - Only the stream CLIs' **committed** outputs switch to `.csv.gz`.
4. **Both forms present raises.** If `<dir>/<stream>.csv` and `<dir>/<stream>.csv.gz` both exist, the stream file is ambiguous:
   - `resolve_stream_file` raises `LibError` (11.4);
   - the stream CLI exits 2 in diff mode (11.5);
   - default discovery in the validator reports `F04` (11.6).

   Nothing silently prefers one form. The usual cause is an old-code `--write` run on a branch after migration.

### 11.4 Library changes (`pipeline/lib/io.py`, `pipeline/lib/rows.py`)

New in `io.py`:

- **`GZIP_LEVEL = 9`.** **Recommended over 6.** Level 9 is 4.2% smaller (7.81 vs 8.15 MB in total; 3.79 vs 3.96 MB for `other`), and it costs about 0.3 s more per `other` write, next to a stream build of tens of seconds or more. The constant is part of the format: changing it changes every committed byte, so it needs a spec change.
- **`gzip_bytes(data: bytes) -> bytes`.** Returns `gzip.compress(data, compresslevel=GZIP_LEVEL, mtime=0)`, or the equivalent single `GzipFile(filename="", mode="wb", compresslevel=GZIP_LEVEL, fileobj=io.BytesIO(), mtime=0)` write with no explicit `flush()`.
  - The output starts with `1f 8b 08 00 00 00 00 00 02 ff`.
  - It does not depend on the wall clock or on any path.
  - `gzip.open(<path>, ...)` and a `TextIOWrapper` over `GzipFile` are **not** allowed for writing (11.1, findings 2 and 4).
  - A non-`bytes` argument raises `LibError`.
- **`read_bytes(path) -> bytes`.** Returns the file's **content**: the decompressed bytes for a `.gz` path, the raw bytes otherwise.
  - A missing or unreadable file, or a corrupt or truncated gzip stream, raises `LibError` naming the path. This covers `gzip.BadGzipFile`, `EOFError`, `zlib.error` and `OSError`.
  - Path type checks are as for `read_table` (§8.8.4).
- **`first_difference(a: bytes, b: bytes) -> int | None`.** Splits both arguments into lines, keeping the `\n`. It returns the 1-based number of the first line that differs, where line 1 is the header, or `None` when `a == b`.
  - When one input is a strict line-prefix of the other, it returns the number of the first line the shorter one lacks.
  - A missing final newline counts as a difference on that line.
  - Raises `LibError` for non-`bytes` input.
- **`resolve_stream_file(directory, stream) -> Path | None`.** Looks for `<directory>/<stream>.csv.gz` and `<directory>/<stream>.csv`.
  - If only one exists, it returns that path.
  - If neither exists, it returns `None`.
  - If both exist, it raises `LibError` naming both.
  - Only regular files count; a directory with either name raises `LibError`.

Changed:

- **`read_table(path)`.** For a `.gz` path, it decompresses the file and then parses exactly as for a plain file, with `utf-8-sig` decoding, the same coercion and the same errors. A gzip-level failure raises `LibError` naming the path. For the same content, the result is identical to reading the plain file.
- **`write_master(rows, path)`.** All the §4.3 / §8.3 / §8.8 rules stand. The change is the order of work:
  1. Format the whole file in memory as before: header plus body, `csv.writer` with `lineterminator="\n"`, encoded UTF-8 with no BOM.
  2. Write the bytes. A plain path gets them unchanged, so plain output is byte-identical to v1.4. A `.gz` path gets `gzip_bytes(those bytes)`.

  The decompressed content of a `.gz` output equals the plain output for the same rows, byte for byte. Files are opened in binary mode, so the line endings are LF on every platform. The existing rule that formatting happens before the file is opened (no partial output on a bad cell) also covers compression.

Unchanged: LF line endings, UTF-8 encoding, header first, sort order, float formatting and every error condition. Gzip is only a container around the same bytes.

*Not required (optional hardening).* `write_master` may write to a temporary file in the same directory and then call `os.replace`, so an interrupted write never leaves a truncated `.gz`. A truncated gzip is detected on read anyway (`LibError` / `F03`).

### 11.5 Stream CLIs (`pipeline/streams/{coal,nuclear,oil_gas,other}.py`, `main`)

1. **Constants.** `MAIN_OUTPUT = Path("data") / "streams" / "<stream>.csv.gz"` and `PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "<stream>.csv.gz"`. `LOG_OUTPUT` is unchanged and stays plain.
2. **Diff mode (default).** The CLI builds into a scratch directory as now, writing the fresh master and pre-1950 files as `.csv.gz` with `write_master` and the log with `write_log`. It then compares each target by **content**, never by compressed bytes:
   - **Master and pre-1950 targets.** The CLI calls `resolve_stream_file` on the target's directory.
     - Both forms present: it prints an error naming both files and exits **2**, whatever the other targets show.
     - Neither present: the difference is "missing".
     - Only the plain `.csv`: the difference is "legacy plain form, run --write to migrate". This counts even when the content matches, so an unmigrated tree never reports "identical".
     - Only the `.csv.gz`: the CLI compares `read_bytes(committed)` with `read_bytes(fresh)`. An unreadable gzip is a difference ("unreadable: <reason>").
   - **Build log.** Compared as plain bytes, as now. A missing file is a difference.
   - **Output.** For each differing target, the CLI prints one stderr line: `<rel path>: first difference at line N`, `<rel path>: missing`, or the legacy or unreadable message. It then prints the existing summary line, `differs from the committed file(s): ...`, and exits 1.
   - Diff mode never writes, deletes or touches a committed file.
   - Exit 0 and `outputs identical to the committed files` only when every target matches.
3. **`--write`.** For each master and pre-1950 target:
   - If the committed `.csv.gz` exists and its decompressed content equals the fresh content, the CLI **leaves it untouched**: same bytes, same mtime. This is **Recommended**: a machine with a different zlib (11.1, finding 5) then never rewrites an unchanged file, so git diffs only on real content changes.
   - Otherwise it writes the file with `write_master`, which is byte-stable on a given zlib.
   - If a plain sibling `<stream>.csv` exists, the CLI deletes it after the `.gz` is in place. This is how the migration works, and it is also the repair for the both-present state.
   - The log is written as now.
   - The `written:` line names the `.gz` paths and flags `(unchanged)` / `(removed legacy <stream>.csv)` where those apply.
   - Exit 0.

   *Alternative:* always rewrite. This is simpler, but it causes git churn across zlib builds.
4. **Optional refactor.** The four `main` functions are identical apart from their constants. The code-writer may move the compare/write logic into one shared helper, for example `pipeline/streams/_outputs.py`. Tests exercise the CLIs, so behaviour is what matters.

### 11.6 Validator (`pipeline/validate.py`)

1. **Discovery.** With `master_files=None`, `_resolve_master_files` collects `data/streams/*.csv` and `data/streams/*.csv.gz`, sorted by file name.
   - **Both present.** If both forms of the same stream exist, the validator reports **`F04`** once per pair, with `row = None` and `file` set to the `.csv.gz` display name. The message names both files. **Neither** file of the pair is read, which is consistent with "a file with an F-code is not validated".
     - *Recommended* over raising: the validator's contract is to report issues, and `FileNotFoundError` is reserved for missing required files.
     - *Alternative:* raise `FileExistsError` and exit 2.
   - **Explicit lists.** An explicit `master_files` list (or CLI `FILE` list) is taken literally, with no pairing check: the caller named the files.
2. **Reading.** `_read_csv` opens a `.gz` path with `gzip.open(path, "rt", encoding="utf-8", newline="")`. Reading is not byte-sensitive, so `gzip.open` is fine here.
   - A gzip failure (`OSError` including `BadGzipFile`, `EOFError`, `zlib.error`) or a decode failure is reported as `F03`, `cannot read as gzip-compressed UTF-8 CSV: <reason>`.
   - The BOM strip, `F01`, `F02` and `D01` behave as for plain files.
   - Plain-file behaviour is unchanged.
   - The suffix rule applies to every table `_read_csv` reads, but only stream outputs are expected to use it.
3. **Display names.** These keep the suffix, for example `Issue.file == "data/streams/coal.csv.gz"`.
4. **Row checks.** These do not change. Every check that reads master rows (`_coerce_master`, `_check_master_row`, `_check_product`, `_check_cross_rows`) sees the same `_Table` whichever form the file is in. `X01`–`X05` treat rows from `.csv` and `.csv.gz` files alike. Processing order is sorted file name.
5. **Pre-1950 files.** `data/streams_pre1950/` files are still never read, in either form.
6. **CLI help text.** The `main()` help (`default: data/streams/*.csv`) and the module docstring become `data/streams/*.csv and *.csv.gz`.
7. **No import cycle.** `pipeline/lib/io.py` imports from `pipeline/validate.py`, so the validator must not import from `pipeline.lib`. It uses `gzip` directly.

### 11.7 Repository and migration

1. **`.gitattributes`** (new, at the repo root), with the single line `*.csv.gz binary`. This stops text diffs, merges and EOL conversion on the gzipped files. A merge conflict on a `.csv.gz` file is resolved by re-running the stream CLI with `--write`.
   - **Optional, not required: readable diffs.** A clone that wants `git diff` and `git log -p` to show decompressed CSV can use the line `*.csv.gz binary diff=gzip` in `.gitattributes` and run, once per clone, `git config diff.gzip.textconv "gzip -dc"`. A `diff=gzip` attribute with no matching config is harmless (git falls back to binary), so the committed `.gitattributes` may carry either form. The committed default is `*.csv.gz binary`. No test, CLI or tool may depend on the textconv setting. On Windows, `gzip` must be on the `PATH` that git uses (Git for Windows ships one in its `usr\bin`); check with `gzip --version` in Git Bash.
2. **One commit for everything.** **Recommended.** The commit contains the code (lib, validator, four CLIs), the test updates, the docs (SCHEMA v2.5, this section, the per-stream SPEC output tables, D72), `.gitattributes`, the eight `.csv.gz` files produced by `python -m pipeline.streams.<s> --write` for each stream, and the deletion of the eight plain `.csv` files (`git add -A data/streams data/streams_pre1950`).
   - Before committing: run each CLI once more without `--write`, which must exit 0, then run `python -m pipeline.validate --root .`, which must report no issues.
   - *Alternative:* one commit per stream. This works because the reader accepts both forms, but between the commits the code expects `.gz` while three streams are still plain, so their diff mode exits 1 (legacy). There is no benefit, because the data does not change.
3. **History (growth accepted by Steve, 2026-11-06).** The old plain blobs stay in history. That is acceptable: `.git` is about 24 MB, and nothing needs rewriting.
   - **Cost to note:** git already zlib-compresses blobs and delta-compresses similar plain-text versions in packs. Gzip blobs do not delta.
   - So from now on, every content change to a stream adds roughly its full gzipped size to history: about 3.8 MB for `other`, 7.8 MB if all streams change.
   - A plain-text change touching few lines would have added only a small delta. A factor change usually rewrites most of a stream's rows anyway, so the practical difference is modest. It does argue against committing rebuilds without content changes, which 11.5.3 already prevents.
4. **Ordering (fixed by Steve, 2026-11-06).** The D73 coal revision (factor changes in `data/factors/coal.csv`, which leave the coal outputs identical) lands **before** the D72 migration commit. The migration commit is then built on top of it, and its pre-commit checks (11.7.2) confirm that the coal diff run still exits 0. More generally, land or rebase any concurrent work that writes stream outputs before migrating. A branch built with the old code writes `coal.csv` next to `coal.csv.gz`, which is exactly the both-present case (11.3.4). It is repaired by re-running `--write` with the new code.

### 11.8 Done conditions and test items (for the spec-blind test-writer)

Tests are written from this section, §4.3/§5/§8, and SCHEMA §6 as amended by v2.5. They go in `pipeline/tests/lib/test_io_gz.py` (library), `pipeline/tests/test_validate_gz.py` (validator), and the existing stream suites (CLI). They use only `tmp_path`. Never hard-code a compressed digest or a compressed length (11.1, finding 5). Assert on the header bytes and on decompressed content instead.

**A. Round trip (lib).**

1. `write_master(rows, p.csv.gz)` followed by `read_table(p.csv.gz)` returns the same records as writing to `p.csv` and reading that back. Cover the empty list, header-only output, `None` cells, lists, booleans, non-ASCII text and floats.
2. `gzip.decompress(p.csv.gz bytes)` equals the bytes of `p.csv`.
3. The decompressed content uses LF only, has no CR and no BOM, and is valid UTF-8.
4. Plain output is unchanged from v1.4. A fixed row set, written plain, matches a hand-written expected byte string.

**B. Determinism (lib).**

1. Two `write_master` calls to `.gz` paths give byte-identical files. This also holds for different file names and directories (`a.csv.gz` vs `sub/coal.csv.gz`).
2. The result does not depend on the clock. Patch `time.time` to two different values (for example 0 and 2e9), or write twice more than one second apart: the bytes are identical, and bytes 4–7 (MTIME) are zero.
3. Header bytes 0–9 equal `1f 8b 08 00 00 00 00 00 02 ff`. The FLG byte has no FNAME, FCOMMENT or FEXTRA bit.
4. `gzip_bytes(b"")` and `gzip_bytes(x)` both decompress to their input, and `gzip_bytes(x)` equals `gzip.compress(x, 9, mtime=0)`. The second comparison is same-process, so the same zlib is used.
5. `gzip_bytes` of a non-`bytes` argument raises `LibError`.

**C. Reading either form (lib).**

1. For the same content, `read_table` on a `.csv` file and on a `.csv.gz` file gives equal results.
2. `read_bytes` returns decompressed content for a `.gz` path and raw bytes otherwise.
3. Each of these raises `LibError` naming the path, for both `read_table` and `read_bytes`: a `.gz` file holding plain text, a truncated `.gz` (last 10 bytes cut), a `.gz` with a corrupted CRC, and an empty `.gz` file.
4. `first_difference` cases:
   - equal input gives `None`;
   - a difference in the header gives 1;
   - a difference at line k gives k;
   - extra trailing lines give the first extra line;
   - a missing final newline gives that line;
   - non-`bytes` input raises `LibError`.

**D. Both forms present.**

1. `resolve_stream_file` returns the `.gz` path, the plain path or `None` in the three single-form cases. It raises `LibError` naming both files when both exist, and also when either name is a directory.
2. The CLI diff run with both forms present exits 2 and leaves both files untouched.
3. `--write` with both present exits 0, leaves only the `.csv.gz`, and that file's content equals a fresh build.

**E. CLI diff on tampered content (each stream suite, adapted).**

1. After `--write`, a diff run exits 0.
2. Decompress the committed `.csv.gz`, change one cell on data line k, and recompress with `gzip_bytes`. The diff run then exits 1, its stderr names the file and `first difference at line k`, and the tampered file is left byte-for-byte as it was.
3. The same holds for the pre-1950 file.
4. A copy with the same content but **different compressed bytes** (recompressed at level 1, or with a non-zero mtime) gives exit 0 in diff mode. After `--write`, the copy is left untouched (same bytes), because the content is unchanged.
5. A plain committed `.csv` with correct content and no `.gz` gives exit 1 with the legacy message. `--write` then creates the `.gz` and removes the `.csv`.
6. A missing `.gz` gives exit 1. A corrupt `.gz` gives exit 1 and is not overwritten by the diff run.
7. The build-log checks are unchanged (still plain).

**F. Validator on gz trees.**

1. A valid master file stored as `data/streams/x.csv.gz` gives the same issue list as the same content stored as `x.csv`, apart from the `file` name. This holds for default discovery and for explicit `master_files`.
2. Invalid rows inside a `.gz` give the same row codes with `file` ending in `.csv.gz`.
3. Corrupt or truncated gzip gives `F03`, and the file's rows are not validated.
4. With both `x.csv` and `x.csv.gz`: default discovery gives exactly one `F04` (row `None`, file `data/streams/x.csv.gz`), and neither file's rows are checked. Passing both explicitly gives no `F04`.
5. Cross-file `X01` is reported for a key duplicated between `a.csv` and `b.csv.gz`.
6. `data/streams_pre1950/*.csv.gz` is never read, even if invalid.
7. CLI `FILE` arguments ending in `.csv.gz` work.

**G. Existing stream suites (`pipeline/tests/streams/test_*.py`).** These change only where they name committed output paths or compare committed bytes. Specifically:

- `data/streams/<s>.csv` becomes `.csv.gz`, and the same for `streams_pre1950`.
- Comparisons between a CLI-written `.gz` and the plain `written` fixture use `read_bytes`, that is, content.
- The tamper steps decompress, edit and recompress (E2).
- No assertion about rows, values, logs or validator row codes changes.
- `pipeline/tests/test_seepage_by_group.py::test_real_pre1950_files_cause_no_issues` must glob `*.csv*` (or both patterns). Otherwise its set-up assertion fails once the plain files are gone.
- `test_oil_gas.py::test_committed_tree_cli_matches_when_files_exist` must check for `oil_gas.csv.gz`. Otherwise it **silently skips** after migration.

**H. Performance (budget).**

1. `gzip_bytes` on the committed `other` master content (60 MB) finishes in ≤ 5 s. Measured: 1.0 s, 2.1 s under load.
2. `write_master` of the committed `other` rows to a `.csv.gz` finishes in ≤ 20 s. Measured: 5.5 s plain + 1.0 s compression.
3. `read_table` of `other.csv.gz` takes ≤ 1.5 × `read_table` of the plain file + 2 s, measured in the same test. Measured: 5.0 s plain, with 0.15 s added for decompression.

These run single-process and do not parallelise. They are skipped if the committed `other` stream is absent.

**Done when:**

- items A–H pass;
- all four stream CLIs exit 0 in diff mode on the migrated tree;
- `python -m pipeline.validate --root .` reports no issues;
- no file in the repo exceeds 50 MB (the largest expected is `other.csv.gz`, about 3.8 MB);
- `.gitattributes` holds `*.csv.gz binary`;
- the docs in the impact list (11.10) are updated;
- SCHEMA v2.5 (11.9) is applied to `docs/SCHEMA.md` and the D72 row is in `docs/DECISIONS.md` (both approved 2026-11-06).

### 11.9 SCHEMA v2.5 text (approved with D72; applied in the migration commit)

1. **§1 General conventions.** Add this bullet: "**Compression (v2.5, D72).** Stream outputs (`data/streams/`, `data/streams_pre1950/`) are committed as gzip-compressed CSV, `<stream>.csv.gz`. Inside the gzip container every §1 rule applies unchanged: UTF-8, LF line endings, header row. The gzip header carries no file name and MTIME 0, and the writer uses compression level 9 (LIB_SPEC §11). Readers and the validator accept the plain `.csv` form as well. If both forms of one stream are present, that is an error."
2. **§2 table.**
   - The `data/streams/*.csv` row becomes "`data/streams/<stream>.csv.gz` (or plain `.csv`)".
   - The `data/streams_pre1950/<stream>.csv` row becomes "`data/streams_pre1950/<stream>.csv.gz` (or plain `.csv`)".
   - Add a row: "`.gitattributes` | `*.csv.gz binary` | no | v2.5".
3. **§3 heading.** "Master table (`data/streams/*.csv[.gz]`, `build/master.csv`)". **§3.2:** the pre-1950 file is `data/streams_pre1950/<stream>.csv.gz`.
4. **§6.1.** `master_files` default: "every `data/streams/*.csv` and `data/streams/*.csv.gz` (sorted by file name); if both forms of one stream exist, `F04` and neither is read". The `Issue.file` example becomes `"data/streams/coal.csv.gz"`.
5. **§6.2.** "`FILE`s are master files, plain or `.csv.gz`".
6. **§6.3 file-level codes.**
   - `F03` gains "or a `.gz` file that is not a valid gzip stream".
   - New code: "`F04` | Default discovery found a stream in both forms (`<x>.csv` and `<x>.csv.gz`) in `data/streams/`; reported once per pair against the `.csv.gz`, `row = None`; neither file is validated".
7. **§6.5 behaviour details.** Add a row: "Gzipped files | Selected by the `.gz` suffix only; decompressed and then treated exactly as plain files; display names keep the suffix; an explicit `master_files` list is taken literally (no `F04`)". Extend the `residue_seepage_by_group` row's last sentence to "in either form".
8. **§9 change log.** Add: "2026-11-05 | **v2.5** (Steve, D72): stream outputs committed as `<stream>.csv.gz` (deterministic gzip, level 9, MTIME 0, no file name); readers accept both forms; both present is `F04` in the validator and an error in the stream CLIs; build logs stay plain; `.gitattributes` `*.csv.gz binary` (LIB_SPEC §11)."

### 11.10 Impact list: everything that hard-codes a stream output path

Code:

- `pipeline/lib/io.py`:
  - `read_table` gains `.gz`;
  - new: `GZIP_LEVEL`, `gzip_bytes`, `read_bytes`, `first_difference`, `resolve_stream_file`.
- `pipeline/lib/rows.py`:
  - `write_master` formats in memory, then writes plain or gzip.
- `pipeline/validate.py`:
  - `_resolve_master_files` (line ~1058): globs both forms and adds the `F04` pairing;
  - `_read_csv` (line ~268): gzip path and `F03`;
  - `validate` (line ~1072): the master loop and `F04`;
  - `main` help string (line ~1143) and the module docstring.
- `pipeline/streams/coal.py`:
  - `MAIN_OUTPUT`, `PRE1950_OUTPUT` (lines 75–76);
  - `main` (lines 891–937).
- `pipeline/streams/nuclear.py`:
  - constants (lines 74–75);
  - `main` (from line 1226).
- `pipeline/streams/oil_gas.py`:
  - constants (lines 106–107);
  - `main` (from line 1215).
- `pipeline/streams/other.py`:
  - constants (lines 100–101);
  - `main` (from line 1316).
- `write_log` in all four streams is **unchanged**.

Tests:

- `pipeline/tests/streams/test_coal.py`:
  - 385–391: `issues` fixture. It may keep copying the plain `written` file as `coal.csv`, or switch to `.gz`. Its file filter must match whatever name it uses.
  - 889–910: `test_cli_write_and_diff`. Change the paths, compare content, use the E2 tamper.
  - 1870–1895: change the paths and the pre-1950 tamper.
  - Unchanged: 246–251 (`written`, plain in `tmp`), 257–263 (`_copy_tree` ignore patterns still match the directories) and 866–872 (determinism on plain files).
- `pipeline/tests/streams/test_nuclear.py`:
  - 537–546: `issues` fixture;
  - 2013–2038: paths, content comparison, byte tamper at 2028–2038;
  - 2049–2055: paths.
- `pipeline/tests/streams/test_oil_gas.py`:
  - 537–546;
  - 1858–1897: paths, comparison, byte tamper at 1879–1890;
  - 1909–1914: silent-skip risk.
  - Unchanged: 1976–1977 (directory creation only).
- `pipeline/tests/streams/test_other.py`:
  - 1033–1043;
  - 3298–3307;
  - 3355–3356;
  - 3401–3402.
  - Unchanged, unless the fixtures switch to `.gz`: 359–363, 1461, 2001, 2419–2437 and 3178–3179, which only touch plain `written` files or directories.
- `pipeline/tests/streams/{nuclear,oil_gas,other}_oracle.py`: docstrings only (lines 12–14).
- `pipeline/tests/test_seepage_by_group.py:328`: the glob.
- No change: `pipeline/tests/conftest.py:93` (creates the directory only), `pipeline/tests/test_schema_v22.py:75` (a plain fixture name), `pipeline/tests/test_validate.py` and `pipeline/tests/lib/*` (plain fixtures; new gz tests are added beside them).

Docs:

- `docs/SCHEMA.md`: §1, §2 (lines 38–39), §3 heading (line 45), §3.2 (line 96), §6.1 (lines 411, 420), §6.2, §6.3, §6.5 (line 531), §9, as in 11.9.
- Output tables and acceptance lines in the stream specs:
  - `docs/COAL_SPEC.md`: lines 23–24, 124;
  - `docs/NUCLEAR_SPEC.md`: lines 21–22, 357, 445;
  - `docs/OIL_GAS_SPEC.md`: lines 22–23, 159, 442;
  - `docs/OTHER_SPEC.md`: lines 24–25, 413.
- `docs/PHASE2_PLAN.md`: line 12, and line 62 (the proposed `data/streams/memo.csv` would become `.csv.gz` if adopted).
- `PLAN.md`: lines 58, 214.
- `docs/DECISIONS.md`: D57 (wording) and new D72.

Data and repo:

- Remove the 8 files `data/streams/{coal,nuclear,oil_gas,other}.csv` and `data/streams_pre1950/{coal,nuclear,oil_gas,other}.csv`, and add their `.csv.gz` counterparts.
- Add `.gitattributes`.
- `research/*/build_log.csv` is untouched.

### 11.11 Clarifications after the test round (orchestrator, 2026-11-06)
1. Line numbers in diff messages are **file lines** (header = line 1), matching `first_difference`; in §11.8 E2, "data line k" means file line k.
2. A zero-byte `.csv.gz` is a corrupt gzip: validator `F03`, library `LibError`.
3. `gzip_bytes` accepts `bytes` only; `bytearray`/`memoryview` raise `LibError` (callers pass `bytes`).
4. Detection is by suffix only: a gzip file named `.csv` is read as text and fails as a malformed CSV (`F01`/`F03` as today); no sniffing.
5. `first_difference` splits on LF only; a lone CR is ordinary content.
6. `resolve_stream_file` on a missing directory returns "neither present" (the caller's existing error), not a different exception.

## 12. v1.6 (2026-11-11, approved by Steve as D74): `ore_type` match key

Needed by Task 2.4 (`docs/WIND_SOLAR_SPEC.md` v1.0) and by the nuclear Olympic Dam family F8 (`docs/NUCLEAR_SPEC.md` §14): the copper and rare-earth rows of `data/reference/commodity_factors.csv` share every other key and differ only by ore type (SCHEMA §4.7, v2.6). The rule mirrors §10 (v1.4, `substream`) exactly.

1. **`select` accepts `ore_type` as a match key** (added to `MATCH_KEYS`). Semantics are those of every other key: **exact equality** with the row's `ore_type` cell. A row with an empty `ore_type` matches only `ore_type=""` (or a call that does not pass `ore_type` at all). There is **no wildcard**: `ore_type=""` does not match a row whose cell is `porphyry_stratiform`, and `ore_type="all"` matches only rows whose cell is the literal value `all` (a copper ore type meaning "smelter rows not split by ore type", not a wildcard).
2. **Precedence is unchanged:** an exact-region row beats an `XWL` row; ambiguity at the winning level raises `LibError` (`ambiguous factor rows`); no candidate raises `LibError` (`no factor row`). `ore_type` takes no part in precedence: it filters candidates before the region rule, like every other key.
3. **`read_table` reads the `ore_type` column as a string**: an empty cell becomes `""`, never `None` or NaN, as `substream` (§10 item 3). Non-empty cells are stripped of surrounding whitespace like every string cell. This applies to any file that has an `ore_type` column (in v2.6 only `commodity_factors.csv`).
4. **Backward compatibility:** a call that does not pass `ore_type` behaves exactly as in v1.5, whatever the rows hold (so a call on a file with several ore types for the same other keys raises `ambiguous factor rows`, which is the intended loud failure). Factor files without an `ore_type` column are unaffected; passing `ore_type` against rows that lack the key: a row dict without the key matches only `ore_type=""` (missing is treated as empty).
5. **`factor_id` on commodity rows:** `select` returns the row dict unchanged, including `factor_id`; no other function changes. `apply` needs no change (unit `Bq/t`).
6. Nothing else changes: `MATCH_KEYS` gains one member; the `unknown match key(s)` error lists it among the allowed keys.

### 12.1 Done conditions and test items (for the spec-blind test-writer)

Tests go in `pipeline/tests/lib/test_select_ore_type.py`; they use in-memory row dicts and `tmp_path` CSVs only, and do not read the implementation.

- **T1 exact match.** Rows A (`ore_type="porphyry_stratiform"`) and B (`ore_type="iocg_high_u"`), otherwise identical (commodity `copper`, component `own_residue`, group `Ra226+`, tier `impounded`, residue `metal_tailings`, region `XWL`, window 1950–2025): `ore_type="porphyry_stratiform"` returns A; `ore_type="iocg_high_u"` returns B.
- **T2 empty matches only empty.** Add row C with `ore_type=""`: `ore_type=""` returns C; `ore_type="porphyry_stratiform"` never returns C.
- **T3 no wildcard.** With only rows A and B present, `ore_type=""` raises `LibError` whose message starts with `no factor row`; so does `ore_type="cu_co_stratiform"`.
- **T4 `all` is a literal.** Row D `ore_type="all"`: `ore_type="all"` returns D; `ore_type="porphyry_stratiform"` does not return D.
- **T5 omitted key.** With rows A and B (same other keys), a call without `ore_type` raises `LibError` starting `ambiguous factor rows`; with A alone, a call without `ore_type` returns A (v1.5 behaviour).
- **T6 region precedence unchanged.** Rows E (`iocg_olympic_dam`, region `AUS`) and F (`iocg_olympic_dam`, region `XWL`): `region="AUS"` returns E; `region="CHN"` returns F. Rows G (`iocg_high_u`, `AUS`) and H (`porphyry_stratiform`, `XWL`): `region="AUS", ore_type="porphyry_stratiform"` returns H (the exact-region row G does not match the key, so precedence never sees it).
- **T7 ambiguity at the winning level.** Two rows identical in every key including `ore_type` and region raise `ambiguous factor rows`.
- **T8 year window.** `ore_type` filtering combines with the window: an OD row valid 1988–2025 is not returned for 1987 (`no factor row`).
- **T9 `read_table`.** A CSV with an `ore_type` column and one empty and one non-empty cell (with surrounding spaces) reads as `""` and the stripped string; the empty cell is never `None`.
- **T10 missing key in a row dict.** A row dict without an `ore_type` key matches `ore_type=""` and does not match `ore_type="all"`.
- **T11 key set.** `"ore_type" in MATCH_KEYS`; an unknown key (e.g. `oretype`) still raises `unknown match key(s)` and the message lists `ore_type` among the allowed keys.
- **T12 regression.** The existing v1.4 `substream` tests and every other `pipeline/tests/lib` test pass unchanged.

Verification: the verifier runs the suite, then mutation-tests `select` (drop `ore_type` from `MATCH_KEYS`; treat empty as wildcard; read empty `ore_type` as `None`): each mutant must be killed by at least one of T1–T11.
