# Radiopassive — Data Schema (v1)

> **Status:** DRAFT (Task 0.2). Governs every CSV under `data/` and `build/`. Rules trace to `docs/METHODS.md`, cited as "METHODS §n"; a bare "§n" refers to this document.

---

## 1. General conventions

- **Format:** UTF-8 CSV, comma-separated, header row, `.` as the decimal separator, no thousands separators. Numbers may use exponent notation (`3.7e10`).
- **Missing values:** empty cell. Never `0` for "unknown", never `NA` or `-`.
- **Booleans:** `true` / `false`.
- **Lists inside a cell:** `;`-separated with no spaces (e.g. `S0012;S0040`).
- **Identifiers:** lower_snake_case for controlled vocabularies; prefixed IDs for records (`S0001` sources, `E001` events, `B01` baselines).
- **Activity is stored as head activity, as reported** (METHODS §3.2, D24). The group multiplier $m_k$ is applied in the pipeline, never in stored data.
- **No dose quantities anywhere** (D1). Any column whose name contains `dose`, `sv`, `sievert` or `rem` is rejected by the validator.

---

## 2. Files

| File | Purpose | Written by |
|---|---|---|
| `data/reference/nuclides.csv` | Physical constants per nuclide | Task 0.3 |
| `data/reference/groups.csv` | Nuclide groups, heads, members, multipliers, mean energy per head decay | Task 0.3 |
| `data/reference/countries.csv` | Allowed country codes (ISO alpha-3 + `XWL`, `XXX`, historical codes) | Task 0.2 |
| `data/reference/vocab.json` | Controlled vocabularies and the stage–tier matrix (§5 below) | Task 0.2 |
| `data/reference/commodity_factors.csv` | Per-tonne commodity footprints (METHODS §6.2) | Tasks 1.5, 1.9 |
| `data/sources.csv` | Bibliography registry | All tasks |
| `data/events.csv` | Event catalogue (one row per event) | Task 1.8 |
| `data/baselines.csv` | Natural and fallout baselines | Task 1.7 |
| `data/activity/<series>.csv` | Activity spine (generation, production, capacity, intensity) | Task 1.9 |
| `data/streams/<stream>.csv` | Master-format rows for one stream | Tasks 2.1–2.5 |
| `build/master.csv` | Merge of all stream files | Task 3.1 |

---

## 3. Master table (`data/streams/*.csv`, `build/master.csv`)

One row = one quantity of one nuclide group, in one tier, from one stage, in one country and year, under one allocation variant.

| Column | Type | Required | Rule |
|---|---|---|---|
| `year` | int | yes | 1950 ≤ year ≤ 2025 (D14) |
| `stream` | enum | yes | `nuclear`, `coal`, `oil_gas`, `wind_solar`, `other` |
| `substream` | enum | yes | Allowed per stream (§5.1) |
| `stage` | enum | yes | Allowed per stream (§5.2) |
| `country` | code | yes | In `countries.csv` |
| `group` | code | yes | In `groups.csv` (head code, e.g. `Ra226+`, `Cs137+`, `H3`) |
| `tier` | enum | yes | `sealed_in_core`, `sealed_fuel_cycle`, `sealed_damaged_core`, `impounded`, `reisolated`, `dispersed`, `liberated`, `memo_earth_moved`; must be allowed for the stage (§5.3) |
| `quantity` | enum | yes | `flow` (Bq/a added), `transfer_out`, `transfer_in` (Bq moved between tiers in the year), `standing_inventory` (Bq present, for `sealed_in_core` only, METHODS §5.4) |
| `unit` | enum | yes | `Bq/a` for `flow`; `Bq` for the others |
| `value_low` | float ≥ 0 | yes | |
| `value_central` | float ≥ 0 | yes | low ≤ central ≤ high |
| `value_high` | float ≥ 0 | yes | |
| `below_detection` | bool | yes | `true` if the central value is half a detection limit (METHODS §11.1); then `value_low` must be 0 |
| `basis` | enum | yes | `measured`, `compiled`, `modelled`, `interpolated`, `extrapolated` (METHODS §11.2) |
| `source_ids` | list | yes | Every ID exists in `sources.csv`; at least one |
| `allocation_variant` | enum | yes | `default`, `bound_main`, `bound_radio` (METHODS §10.1); `default` where no split applies |
| `allocation_rule` | string | yes | Short code of the rule applied, e.g. `none`, `value`, `mass`, `civil:doc`, `civil:pre1965`, `civil:ratio`, `elec_share` |
| `embedded_fuel` | bool | yes | `true` only for embedded coal/O&G contributions in `wind_solar` or `construction*` stages (METHODS §6.1–6.2, D22) |
| `technology` | enum | no | Lifecycle attribution (§5.4); empty = attributed in the pipeline by electricity share |
| `event_id` | code | no | In `events.csv`; required when `quantity` is a transfer |
| `notes` | string | no | Free text |

**Unique key:** (`year`, `stream`, `substream`, `stage`, `country`, `group`, `tier`, `quantity`, `allocation_variant`, `embedded_fuel`, `technology`, `event_id`).

**Cross-row rules:**
1. **Transfers balance.** For each (`event_id`, `year`, `group`, `allocation_variant`), the sum of `transfer_out` equals the sum of `transfer_in` (central, low and high each, within a relative tolerance of 10⁻⁶).
2. **Allocation completeness.** If any row for a key has `allocation_variant` ≠ `default`, rows for all three variants exist for that key.
3. **Civil rule recorded.** Every `nuclear` row at stages `u_mining_conv`, `u_mining_isl` and `u_milling` has an `allocation_rule` starting `civil:`.
4. **In-core inventory.** `standing_inventory` appears only with tier `sealed_in_core`, and `sealed_in_core` appears only with `standing_inventory` or a transfer.

---

## 4. Other tables

### 4.1 `nuclides.csv` (Task 0.3)

| Column | Type | Rule |
|---|---|---|
| `nuclide` | code | Canonical form `Element-A` with metastable suffix, e.g. `Cs-137`, `Ba-137m`, `Pa-234m` |
| `half_life_value`, `half_life_unit` | float, enum | As in the source (`s`, `min`, `h`, `d`, `a`) |
| `half_life_a` | float | In Julian years (365.25 d) |
| `lambda_per_a` | float | $\ln 2 / T_{1/2}$ in a⁻¹ |
| `decay_modes` | list | e.g. `A`, `B-`, `EC`, `IT`, `B-;A` |
| `daughters` | list | Daughter nuclides, same order as `branching` |
| `branching` | list of floats | Sums to 1 (within 10⁻⁴) |
| `e_alpha_mev` | float | Mean α kinetic energy per decay (MeV) |
| `e_recoil_mev` | float | Mean recoil energy per decay (MeV) |
| `e_beta_mev` | float | Mean β⁻/β⁺ kinetic energy per decay, antineutrino/neutrino **excluded** (MeV) |
| `e_photon_mev` | float | Mean γ + X-ray energy per decay (MeV) |
| `e_electron_mev` | float | Mean conversion + Auger electron energy per decay (MeV) |
| `e_total_mev` | float | Sum of the five above |
| `source_ids` | list | |
| `notes` | string | |

### 4.2 `groups.csv` (Task 0.3)

| Column | Type | Rule |
|---|---|---|
| `group` | code | e.g. `U238+`, `Ra226+`, `Po210`, `Cs137+`, `H3` (single nuclides use the nuclide without hyphen) |
| `head` | nuclide | In `nuclides.csv` |
| `members` | list | Head first; all in `nuclides.csv` |
| `member_weights` | list | Decays of each member per head decay (branching-weighted) |
| `multiplier` | float | $m_k$ = sum of `member_weights` (METHODS §4) |
| `e_per_head_decay_mev` | float | $\bar{E}_k$ (METHODS §7) |
| `chain` | enum | `U238`, `U235`, `Th232`, `K40`, `artificial` |
| `role` | enum | `chain`, `released_gas`, `artificial` (METHODS §4.1a) |
| `multiplier_scope` | enum | `stock_and_flow` or `flow_only`; `flow_only` iff `role = released_gas`. The validator rejects any master row in a stock tier that would apply a `flow_only` multiplier (i.e. a `flow_only` group with `quantity` ≠ `flow`) |
| `parent_group` | code | Next group up the chain; empty for chain heads and artificial groups |
| `parent_branching` | float | Branching from `parent_group` to this group |
| `notes` | string | Includes the equilibrium convention used (METHODS §4.1) |

### 4.3 `sources.csv`

| Column | Type | Rule |
|---|---|---|
| `source_id` | code | `S` + 4 digits, unique |
| `short_cite` | string | e.g. `UNSCEAR 2016 Annex A` |
| `full_citation` | string | |
| `url` | string | Optional; domains `grokipedia.com` and `wikipedia.org` rejected (METHODS §11.3) |
| `doi` | string | Optional |
| `year` | int | Publication year |
| `type` | enum | `regulator`, `compilation`, `peer_reviewed`, `agency`, `grey` |
| `rank` | int | 1–5 per the source hierarchy (METHODS §11.3); must match `type` (regulator 1, compilation 2, peer_reviewed 3, agency 4, grey 5) |
| `access` | enum | `open`, `paywalled`, `inaccessible` |
| `licence` | enum | `open`, `restricted`, `unknown` (D20) |
| `notes` | string | |

### 4.4 `events.csv`

| Column | Type | Rule |
|---|---|---|
| `event_id` | code | `E` + 3 digits |
| `name` | string | |
| `date_start` | date | ISO 8601 |
| `date_end` | date | Optional |
| `country` | code | In `countries.csv` |
| `location`, `lat`, `lon` | string, float, float | lat/lon optional |
| `stream`, `stage` | enum | As in the master table |
| `event_type` | enum | `accident`, `impoundment_failure`, `spill`, `other` |
| `is_accident` | bool | Drives the "exclude accidents" toggle (METHODS §9.1); `true` iff `event_type = accident` |
| `from_tier`, `to_tier` | enum | Master tiers |
| `mass_t` | float | Optional; material released |
| `activity_central_bq` | float | Summary only; detail by group lives in master rows with this `event_id` |
| `inclusion` | enum | `activity` (≥ 1 TBq) or `mass` (≥ 10⁵ t) (METHODS §9.1); the stated criterion must be met by the row's own values |
| `military` | bool | Must be `false` (D9); military events never enter the dataset |
| `source_ids` | list | At least one |
| `notes` | string | |

### 4.5 `baselines.csv`

| Column | Type | Rule |
|---|---|---|
| `baseline_id` | code | `B` + 2 digits |
| `name` | string | |
| `quantity` | enum | `stock` (Bq), `flow` (Bq/a), `power` (W) |
| `group` | code | Optional |
| `year` | int | Optional (empty = time-invariant) |
| `value_low`, `value_central`, `value_high` | float | |
| `unit` | enum | `Bq`, `Bq/a`, `W` |
| `basis` | enum | As master |
| `derivation` | string | Formula or reference to the calculation note |
| `source_ids` | list | |

### 4.6 `data/activity/<series>.csv`

| Column | Type | Rule |
|---|---|---|
| `series` | code | e.g. `elec_gen_coal`, `coal_production`, `produced_water`, `ree_production`, `cap_add_wind_dd` |
| `year` | int | |
| `country` | code | |
| `value_low`, `value_central`, `value_high` | float | |
| `unit` | string | SI or SI-derived (e.g. `TWh`, `t`, `m3`, `GW`, `t/GW`) |
| `basis`, `source_ids`, `notes` | | As master |

### 4.7 `commodity_factors.csv`

| Column | Type | Rule |
|---|---|---|
| `commodity` | enum | e.g. `ree_oxide`, `copper`, `aluminium`, `steel`, `cement`, `silicon_mg`, `silver`, `tellurium`, `indium`, `glass` |
| `component` | enum | `own_residue`, `embedded_fuel` (METHODS §6.2) |
| `group`, `tier` | code, enum | As master |
| `value_low`, `value_central`, `value_high` | float | Bq per t of refined commodity |
| `region` | code | Country or `XWL` |
| `year_from`, `year_to` | int | Validity window |
| `basis`, `source_ids`, `notes` | | As master |

---

## 5. Controlled vocabularies (`data/reference/vocab.json`)

### 5.1 Substreams

| Stream | Substreams |
|---|---|
| `nuclear` | `pwr`, `bwr`, `phwr`, `gcr`, `lwgr`, `fbr`, `other_reactor`, `fuel_cycle` (for stages not tied to a reactor type) |
| `coal` | `power`, `non_power`, `all` (stages not split by end use, e.g. mining) |
| `oil_gas` | `conventional`, `unconventional`, `oil_sands` (D26) |
| `wind_solar` | `wind`, `solar` |
| `other` | `geothermal`, `biomass_peat`, `hydro` |

### 5.2 Stages (from METHODS §6.3)

| Stream | Stages |
|---|---|
| `nuclear` | `u_mining_conv`, `u_mining_isl`, `u_milling`, `conv_enrich_fab`, `reactor_operation`, `spent_fuel`, `reprocessing`, `sea_disposal`, `construction_decom`, `accident` |
| `coal` | `coal_mining`, `combustion_power`, `combustion_nonpower`, `construction` |
| `oil_gas` | `drilling`, `production`, `oil_sands_mining`, `processing_transport`, `abandonment_scrap`, `construction` |
| `wind_solar` | `commodity_supply`, `end_of_life` |
| `other` | `geothermal`, `biomass_peat`, `hydro`, `construction` |

### 5.3 Stage–tier matrix

Allowed tiers per stage, as in METHODS §6.3 (`memo_earth_moved` is allowed only at mining stages: `u_mining_conv`, `coal_mining`, `oil_sands_mining`, `commodity_supply`).

| Stage | Allowed tiers |
|---|---|
| `u_mining_conv` | impounded, reisolated, liberated, memo_earth_moved |
| `u_mining_isl` | impounded, reisolated, liberated |
| `u_milling` | sealed_fuel_cycle, impounded, dispersed, liberated |
| `conv_enrich_fab` | sealed_fuel_cycle, impounded, liberated |
| `reactor_operation` | sealed_in_core, sealed_fuel_cycle, liberated |
| `spent_fuel` | sealed_in_core, sealed_fuel_cycle |
| `reprocessing` | sealed_fuel_cycle, liberated |
| `sea_disposal` | sealed_fuel_cycle, liberated |
| `construction_decom` | sealed_fuel_cycle, impounded, dispersed, liberated |
| `accident` | sealed_in_core, sealed_damaged_core, liberated |
| `coal_mining` | impounded, liberated, memo_earth_moved |
| `combustion_power` | impounded, reisolated, dispersed, liberated |
| `combustion_nonpower` | impounded, dispersed, liberated |
| `construction` | impounded, dispersed, liberated |
| `drilling` | impounded |
| `production` | impounded, reisolated, dispersed, liberated |
| `oil_sands_mining` | impounded, liberated, memo_earth_moved |
| `processing_transport` | impounded, liberated |
| `abandonment_scrap` | impounded, dispersed, liberated |
| `commodity_supply` | impounded, dispersed, liberated, memo_earth_moved |
| `end_of_life` | impounded, liberated |
| `geothermal` | impounded, reisolated, liberated |
| `biomass_peat` | impounded, dispersed, liberated |
| `hydro` | liberated |

Event rows (`quantity` = `transfer_out`/`transfer_in`) may use any tier pair; the event's `from_tier`/`to_tier` must match.

### 5.4 Technologies (lifecycle view, D22)

`coal_power`, `gas_power`, `oil_power`, `nuclear`, `wind`, `solar`, `geothermal`, `biomass`, `hydro`.

---

## 6. Validator contract (`pipeline/validate.py`)

This section is the interface the validator implements and its tests are written against. The tests are written from this section alone (spec-blind), so the implementation must match it exactly.

### 6.1 Python API

```python
from pipeline.validate import Issue, validate

@dataclass(frozen=True)
class Issue:
    file: str          # path relative to root, POSIX separators, e.g. "data/streams/coal.csv"
    row: int | None    # 1-based data-row number (header excluded); None for file-level issues
    rule: str          # rule code from §6.3, e.g. "V03"
    message: str       # human-readable explanation

def validate(root: str | os.PathLike, master_files: Iterable[str | os.PathLike] | None = None) -> list[Issue]: ...
```

- `root` is a project root laid out as in §2. The validator reads:
  - `data/reference/vocab.json`, `countries.csv`, `nuclides.csv`, `groups.csv` (required);
  - `schema/master.json`, `schema/sources.json`, `schema/events.json` (required);
  - `data/sources.csv` (required);
  - `data/events.csv` (optional: if absent, there are no events).
- `master_files`: paths (absolute, or relative to `root`) of master-format CSVs to check. If `None`, every `data/streams/*.csv` plus `build/master.csv` if it exists.
- Every call also validates `data/sources.csv`, `data/events.csv` (if present), `nuclides.csv` and `groups.csv`.
- An empty list means everything is valid. Issues are returned in a stable order: by file, then row (file-level first), then rule.
- A missing *required* reference file raises `FileNotFoundError`. It is not reported as an `Issue`.
- **Cross-row rules (X\*) consider all master files together.** An `X01` duplicate across two files is reported on the later file's row; an `X02` imbalance is reported once per unbalanced (`event_id`, `year`, `group`, `allocation_variant`) with `row = None`, against the first file containing that event.

### 6.2 Command line

`python -m pipeline.validate [--root DIR] [FILE ...]` (also `pixi run validate`).
- `--root` defaults to the current directory; `FILE`s are master files (default as above).
- Prints one line per issue, `file:row: RULE message` (`row` printed as `-` when `None`), then a summary line.
- **Exit codes:** 0 = no issues; 1 = one or more issues; 2 = usage error or missing required file.

### 6.3 Rule codes

One row may raise several codes. Each code below is raised **only** for the condition stated. Where a condition is expressible in the JSON schema it is reported as `R02`, not under another code.

| Code | Scope | Condition |
|---|---|---|
| `F01` | any CSV | Header does not exactly match the specified columns, in order |
| `F02` | any CSV | A column name contains a forbidden token (`dose`, `sv`, `sievert`, `rem`) as a whole `_`-separated word, case-insensitive |
| `F03` | any CSV | File cannot be read as UTF-8 CSV |
| `R01` | master | A cell cannot be coerced to its type (int, float, bool, list) |
| `R02` | master | The coerced row fails `schema/master.json` |
| `R03` | master | `value_low ≤ value_central ≤ value_high` does not hold |
| `V01` | master | `substream` not allowed for `stream` |
| `V02` | master | `stage` not allowed for `stream` |
| `V03` | master | `tier` not allowed for `stage` (§5.3); not raised for `transfer_out` / `transfer_in` rows |
| `V04` | master | `group` not in `groups.csv` |
| `V05` | master | `country` not in `countries.csv` |
| `V06` | master | `country` is a code with a validity window (`valid_from`/`valid_to` in `countries.csv`) and `year` falls outside it |
| `V07` | master | A `source_ids` entry not in `data/sources.csv` |
| `V08` | master | `event_id` not in `data/events.csv` |
| `V09` | master | A `flow_only` group with `quantity` ≠ `flow` |
| `X01` | master | Duplicate unique key (§3) |
| `X02` | master | Transfers for an (`event_id`, `year`, `group`, `allocation_variant`) do not balance (relative tolerance 10⁻⁶, each of low/central/high) |
| `X03` | master | A key (all unique-key columns except `allocation_variant`) has some but not all of `default`, `bound_main`, `bound_radio` |
| `X04` | master | A `nuclear` row at `u_mining_conv`, `u_mining_isl` or `u_milling` whose `allocation_rule` has no `civil:` component |
| `X05` | master | A transfer row whose tier does not match its event (`transfer_out` tier ≠ `from_tier`, or `transfer_in` tier ≠ `to_tier`) |
| `S01` | sources | Row fails `schema/sources.json`, or a duplicate `source_id` |
| `S02` | sources | `url` on a banned domain (or any subdomain of one) |
| `E01` | events | Row fails `schema/events.json`, or a duplicate `event_id` |
| `E02` | events | `stage` not allowed for `stream`, `country` unknown, or a `source_ids` entry unknown |
| `N01` | nuclides | `branching` does not sum to 1 within 10⁻⁴, or `daughters` and `branching` lengths differ |
| `N02` | nuclides | `e_total_mev` ≠ the sum of the five components (relative 10⁻⁶) |
| `N03` | nuclides | `lambda_per_a` ≠ ln 2 / `half_life_a` (relative 10⁻⁶) |
| `G01` | groups | A head or member not in `nuclides.csv` |
| `G02` | groups | `multiplier` ≠ the sum of `member_weights` (relative 10⁻⁶) |
| `G03` | groups | `multiplier_scope = flow_only` but `role ≠ released_gas`, or the reverse |

Notes on rules: `below_detection = true` with `value_low ≠ 0`, unit/quantity mismatches, `standing_inventory` outside `sealed_in_core`, and `embedded_fuel = true` outside `wind_solar`/`construction*` are all in `schema/master.json`, so they raise `R02`. `X03` and `X04` are skipped for a row that already has `R01`.

### 6.4 Coercion rules (master)

- `year` → int; `value_*` → float (accepts exponent notation); `below_detection`, `embedded_fuel` → bool from `true`/`false` only (any other text → `R01`).
- `source_ids` → list split on `;` (an empty cell → `R01`).
- `technology`, `event_id` and `notes`: an empty cell → `null`.
- Any other empty required cell → `R01`.

---

## 7. Change log

| Date | Change |
|---|---|
| 2026-10-20 | First draft (Task 0.2). |
| 2026-10-20 | Added `role` and `multiplier_scope` to groups.csv (from Task 0.3). |
| 2026-10-20 | Added §6 validator contract (API, CLI, rule codes, coercion). |
