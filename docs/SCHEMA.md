# Radiopassive — Data Schema (v2)

> **Status:** SIGNED OFF by Steve, 2026-10-20; **v2.2 additions (2026-10-25, D36, D43–D48) approved by Steve.** **v2.3 additions (2026-10-26, D55–D57: per-group seepage table §4.12, pre-1950 stream files) approved by Steve 2026-10-26.** Task 0.2, revision v2.1 (re-review fixes) of v2 after the independent schema review (2026-10-20). Governs every CSV under `data/` and every input table of the pipeline. Rules trace to `docs/METHODS.md`, cited as "METHODS §n"; a bare "§n" refers to this document. Derived outputs under `build/` are specified provisionally in §8.

---

## 1. General conventions

- **Format:** UTF-8 CSV, comma-separated, header row, `.` as the decimal separator, no thousands separators. Numbers may use exponent notation (`3.7e10`).
- **Missing values:** empty cell. Never `0` for "unknown", never `NA` or `-`.
- **Booleans:** `true` / `false`.
- **Lists inside a cell:** `;`-separated with no spaces (e.g. `S0012;S0040`).
- **Identifiers:** lower_snake_case for controlled vocabularies; prefixed IDs for records (`S0001` sources, `E001` events, `B01` baselines, `RB01` reference bands, `<stream>:0001` factors).
- **Activity is stored as head activity, as reported** (METHODS §3.2, D24). The group multiplier $m_k$ is applied in the pipeline, never in stored data.
- **No dose quantities anywhere** (D1). The forbidden tokens are listed in `vocab.json` → `dose_tokens` (`dose`, `sv`, `msv`, `usv`, `nsv`, `sievert`, `rem`, `mrem`, `mansv` and variants). A token is matched as a **whole word**: names and values are lower-cased and split on every character that is not a letter or a digit (`_`, `-`, `/`, space, …). The rule applies to:
  - every column name of every table the validator reads (`F02`);
  - the cell values of the columns `series`, `unit`, `name`, `description` and `quantity_class` in every table that has them (`D01`).

---

## 2. Files

| File | Purpose | Required by validator | Written by |
|---|---|---|---|
| `data/reference/vocab.json` | Controlled vocabularies, matrices and parameters (§5) | yes | Task 0.2 |
| `data/reference/countries.csv` | Country codes (§4.8) | yes | Task 0.2 |
| `data/reference/nuclides.csv` | Physical constants per nuclide (§4.1) | yes | Task 0.3 |
| `data/reference/groups.csv` | Nuclide groups (§4.2) | yes | Task 0.3 |
| `data/reference/residue_types.csv` | Per-residue engine parameters: ε for radon and thoron, seepage (§4.10) | yes | Tasks 0.2 (codes), 1.3–1.6 (values) |
| `data/reference/residue_seepage_by_group.csv` | Per-group seepage overrides of the residue-type triple (§4.12, D56) | yes (when present) | Seepage research, 2026-10-26 |
| `data/reference/reference_bands.csv` | Inter-evaluation uncertainty bands for nuclide data (§4.11, D27) | yes | Task 0.3 |
| `data/reference/commodity_factors.csv` | Per-tonne commodity footprints (§4.7, METHODS §6.2) | no | Tasks 1.5, 1.9 |
| `data/sources.csv` | Bibliography registry (§4.3) | yes | All tasks |
| `data/events.csv` | Event catalogue (§4.4) | no | Task 1.8 |
| `data/baselines.csv` | Natural and fallout baselines (§4.5) | no | Task 1.7 |
| `data/activity/*.csv` | Activity spine (§4.6) | no | Task 1.9 |
| `data/factors/*.csv` | Factor registry, one file per stream (§4.9) | no | Tasks 2.1–2.5 |
| `data/streams/*.csv` | Master-format rows, one file per stream (§3) | no | Tasks 2.1–2.5 |
| `data/streams_pre1950/<stream>.csv` | Pre-1950 undecayed flows, master columns (§3.2, D31, D57) | no (not validated by the master schema) | Phase 2 |
| `build/master.csv` | Merge of the stream files and nothing else (§3) | no | Task 3.1 |
| `schema/*.json` | Row schemas for every table above: `master`, `sources`, `events`, `countries`, `activity`, `baselines`, `commodity_factors`, `factors`, `residue_types`, `reference_bands` | yes (all ten) | Task 0.2 |

---

## 3. Master table (`data/streams/*.csv`, `build/master.csv`)

One row = one quantity of one nuclide group, in one tier, from one stage (and product, residue type and release route where they apply), in one country and year, under one allocation variant.

| Column | Type | Required | Rule |
|---|---|---|---|
| `year` | int | yes | 1950 ≤ year ≤ 2025 (D14) |
| `stream` | enum | yes | `nuclear`, `coal`, `oil_gas`, `wind_solar`, `other` |
| `substream` | code | yes | Allowed per stream (§5.1) |
| `stage` | code | yes | Allowed per stream (§5.2) |
| `product` | code | conditional | Oil/gas product, or commodity, per the product rules (§5.5); otherwise empty |
| `residue_type` | code | conditional | In `residue_types.csv`; **required** when `tier` is `impounded`, `reisolated` or `dispersed`, **empty** otherwise |
| `country` | code | yes | In `countries.csv`; **not** `XWL` (global data without a country breakdown go in `XXX`) |
| `group` | code | yes | In `groups.csv` (head code, e.g. `Ra226+`, `Cs137+`, `H3`) |
| `tier` | enum | yes | `sealed_in_core`, `sealed_fuel_cycle`, `sealed_damaged_core`, `impounded`, `reisolated`, `dispersed`, `liberated`, `memo_earth_moved`, `memo_biosphere`; allowed for the stage (§5.3). Both memo tiers are outside the tier totals, `flow` only, and never `opening_stock` |
| `quantity` | enum | yes | `flow` (Bq/a added), `transfer_out`, `transfer_in` (Bq moved between tiers in the year), `standing_inventory` (Bq present in `sealed_in_core`; the no-accident baseline, METHODS §5.4), `opening_stock` (Bq present on 1 January 1950; D31, §3.2) |
| `unit` | enum | yes | `Bq/a` for `flow`; `Bq` for every other quantity |
| `value_low` | float ≥ 0 | yes | |
| `value_central` | float ≥ 0 | yes | low ≤ central ≤ high |
| `value_high` | float ≥ 0 | yes | |
| `below_detection` | bool | yes | `true` if the central value is half a detection limit (METHODS §11.1); then `value_low` must be 0 |
| `basis` | enum | yes | `measured`, `compiled`, `modelled`, `interpolated`, `extrapolated` (METHODS §11.2) |
| `source_ids` | list | yes | Every ID in `sources.csv`; at least one |
| `factor_ids` | list | conditional | Every ID in the factor registry (§4.9); **required** when `basis = modelled` |
| `allocation_variant` | enum | yes | `default`, `bound_main`, `bound_radio` (METHODS §10.1); `default` where no split applies |
| `allocation_rule` | list | yes | Tokens from §5.6, e.g. `none`, `alloc:value`, `civil:doc;alloc:value` |
| `embedded_fuel` | bool | yes | `true` only for embedded coal/O&G contributions in `wind_solar` or `construction*` stages (METHODS §6.1–6.2, D22) |
| `technology` | enum | no | Lifecycle attribution (§5.4); empty = attributed in the pipeline by electricity share |
| `route` | enum | conditional | Release route (§5.7); **required** when `tier = liberated`, **empty** otherwise |
| `event_id` | code | no | In `events.csv`; empty for routine transfers (§3.1) |
| `notes` | string | no | Free text |

**Unique key:** (`year`, `stream`, `substream`, `stage`, `product`, `residue_type`, `country`, `group`, `tier`, `quantity`, `allocation_variant`, `embedded_fuel`, `technology`, `route`, `event_id`).

### 3.1 Transfers

A transfer is a pair of rows, `transfer_out` from a source tier and `transfer_in` to a destination tier, that must balance.
- **Event transfers** carry an `event_id`. The `transfer_out` tier must be the event's `from_tier`, and every `transfer_in` tier must be one of the event's `to_tiers`.
- **Routine transfers** have no `event_id` and are allowed only at the stages in `vocab.json` → `routine_transfers` (`sea_disposal`, `reprocessing`, `conv_enrich_fab`: `sealed_fuel_cycle` → `liberated`). At these stages a Liberated row must be a routine transfer, never a `flow` (`V15`).
- **Balance key:** (`event_id`, `year`, `group`, `allocation_variant`) for event transfers; (`stage`, `country`, `year`, `group`, `allocation_variant`) for routine transfers.

### 3.2 What is never a data row

The decay engine generates these from parameters, so data rows for them would double count (METHODS §5.2):
- **chronic radon and thoron exhalation** from Impounded and Dispersed residues, from ε in `residue_types.csv`;
- **seepage** from impoundments, from the seepage fraction in `residue_types.csv`.

They are kept out by **convention**, which the route list supports. Every Liberated row must name a `route` (§5.7). No route describes exhalation from residues or seepage, and there is no general "other" route. The accident routes may be used only on event `transfer_in` rows (`V14`). The validator cannot tell a mis-entered tailings-radon row filed under, say, `air_ventilation` from a genuine mine-vent release, so the convention is restated in the factor registry and checked in the Task 4.1 audit. Radon released by an operating process (mine ventilation, vented and delivered gas, stack) is entered under its route.

**`opening_stock` (D31).** Residues created before 1950 enter as `opening_stock` rows: year 1950 only, any stock tier except `sealed_in_core` and the memo tiers (`memo_earth_moved`, `memo_biosphere`), the activity present on 1 January 1950 after decay, usually `basis = modelled` from pre-1950 activity series (which `data/activity/` allows back to 1800). The decay engine starts each stock from these values.

**Pre-1950 stream files (v2.3, D31 Option A, D57).** `data/streams_pre1950/<stream>.csv` has the master columns, years 1800–1949 and `quantity = flow` only. The flows are undecayed. The files are **not validated by the master schema** (its year range is 1950–2025, D14); the engine decays them to the 1950 opening stock. They are written by the stream scripts alongside `data/streams/<stream>.csv`.

### 3.3 Cross-row rules

1. **Transfers balance** (§3.1), central, low and high each, within a relative tolerance of 10⁻⁶.
2. **Transfers are legitimate**: event tiers match the event; routine transfers only at routine stages with the stated tiers (§3.1).
3. **Allocation completeness.** If any row for a key (the unique key without `allocation_variant`) has `allocation_variant` ≠ `default`, rows for all three variants exist for that key, and the `default` row's rule contains `alloc:value` or `alloc:mass` (`X03`). That the `bound_main` row carries `alloc:main` and the `bound_radio` row `alloc:radio` is a row-level schema rule (`R02`).
4. **Civil rule recorded.** Every `nuclear` row at a stage in `vocab.json` → `civil_rule_stages` (`u_mining_conv`, `u_mining_isl`, `u_milling`, `reprocessing`) has an `allocation_rule` with a `civil:` token. `civil:pre1965` is allowed only for years ≤ 1964, with `value_high = 0`; `civil:ratio` only for years ≥ 1965.

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
| `daughters` | list | Daughter nuclides, same order as `branching` (may include stable nuclides and `SF`) |
| `branching` | list of floats | Sums to 1 (within 10⁻⁴) |
| `e_alpha_mev` | float | Mean α kinetic energy per decay (MeV) |
| `e_recoil_mev` | float | Mean recoil energy per decay (MeV) |
| `e_beta_mev` | float | Mean β⁻/β⁺ kinetic energy per decay, antineutrino/neutrino **excluded** (MeV) |
| `e_photon_mev` | float | Mean γ + X-ray energy per decay (MeV) |
| `e_electron_mev` | float | Mean conversion + Auger electron energy per decay (MeV) |
| `e_total_mev` | float | Sum of the five above |
| `source_ids` | list | |
| `notes` | string | |

Uncertainty bands for these values are in `reference_bands.csv` (§4.11), not in this table.

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
| `multiplier_scope` | enum | `stock_and_flow` or `flow_only`; `flow_only` iff `role = released_gas` |
| `parent_group` | code | Next group up the chain; empty for chain heads and artificial groups. **For a released-gas group that escapes from a residue, the group it escapes from** (`Rn222+` → `Ra226+`, `Rn220+` → `Th228+`): the gas group's members are the members that escape (METHODS §5.2). Released gases from reactors (`Kr88+`, `Xe138+`) have no parent |
| `parent_branching` | float | Branching from `parent_group` to this group |
| `notes` | string | Includes the equilibrium convention used (METHODS §4.1) |

**Flow-only groups in the master table** may be used only as: `flow` rows; `transfer_in` rows into `liberated`; `transfer_out` rows from `sealed_in_core`; and `standing_inventory` rows. The multiplier of a flow-only group is applied only on the Liberated side, never to a stock (METHODS §4.1a).

### 4.3 `sources.csv`

| Column | Type | Rule |
|---|---|---|
| `source_id` | code | `S` + 4 digits, unique |
| `short_cite` | string | e.g. `UNSCEAR 2016 Annex A` |
| `full_citation` | string | |
| `url` | string | Optional, **but required when `access` is `paywalled` or `inaccessible`** (so Steve can try it); must not be on a banned domain (`grokipedia.com`, `wikipedia.org`, or a subdomain) |
| `doi` | string | Optional |
| `year` | int | Publication year |
| `type` | enum | `regulator`, `compilation`, `peer_reviewed`, `agency`, `grey` |
| `rank` | int | 1–5, matching `type` (regulator 1, compilation 2, peer_reviewed 3, agency 4, grey 5) (METHODS §11.3) |
| `access` | enum | `open`, `paywalled`, `inaccessible` |
| `licence` | enum | `open`, `restricted`, `unknown` (D20) |
| `notes` | string | |

`short_cite` and `full_citation` must not contain the banned citation terms in `vocab.json` (`grokipedia`, `wikipedia`).

### 4.4 `events.csv`

| Column | Type | Rule |
|---|---|---|
| `event_id` | code | `E` + 3 digits, unique |
| `name` | string | |
| `date_start` | date | A real calendar date, `YYYY-MM-DD` (use the first of the month or year when only the month or year is known, and say so in `notes`) |
| `date_end` | date | Optional; ≥ `date_start` |
| `country` | code | In `countries.csv` |
| `location`, `lat`, `lon` | string, float, float | Optional |
| `stream`, `stage` | enum, code | Stage allowed for the stream |
| `event_type` | enum | `accident`, `impoundment_failure`, `spill`, `other` |
| `is_accident` | bool | Drives the "exclude accidents" toggle (METHODS §9.1); `true` iff `event_type = accident` |
| `from_tier` | enum | The source tier |
| `to_tiers` | list of enums | One or more destination tiers, not including `from_tier` |
| `mass_t` | float | Material released (t); required for `inclusion = mass` |
| `activity_low_bq`, `activity_central_bq`, `activity_high_bq` | float | **Total** activity moved by the event (all streams, head activity); required for `inclusion = activity`; low ≤ central ≤ high. Detail by group and the attribution to streams live in master transfer rows |
| `inclusion` | enum | `activity` or `mass` (METHODS §9.1): `activity` needs `activity_central_bq` ≥ `vocab.event_inclusion.activity_bq_min` and at least one of `to_tiers` in {`liberated`, `dispersed`}; `mass` needs `mass_t` ≥ `vocab.event_inclusion.mass_t_min` and `from_tier = impounded` |
| `military` | bool | Must be `false` (D9) |
| `source_ids` | list | At least one; all in `sources.csv` |
| `notes` | string | |

### 4.5 `baselines.csv`

| Column | Type | Rule |
|---|---|---|
| `baseline_id` | code | `B` + 2 digits, unique |
| `name` | string | |
| `quantity` | enum | `stock` (unit `Bq`), `flow` (`Bq/a`), `power` (`W`) |
| `group` | code | Optional; in `groups.csv` if given |
| `year` | int | Optional (empty = time-invariant) |
| `value_low`, `value_central`, `value_high` | float ≥ 0 | low ≤ central ≤ high |
| `unit` | enum | Matches `quantity` |
| `basis` | enum | As master |
| `derivation` | string | Formula or reference to the calculation note |
| `source_ids` | list | All in `sources.csv` |
| `notes` | string | |

Baselines are **not** merged into `build/master.csv`; they are exported alongside it (Task 3.7).

### 4.6 `data/activity/*.csv`

| Column | Type | Rule |
|---|---|---|
| `series` | code | lower_snake_case, e.g. `elec_gen_coal`, `coal_production`, `produced_water`, `ree_production`, `cap_add_wind_dd`, `earth_moved_t_coal`, `phi_civil` |
| `year` | int | 1800 ≤ year ≤ 2025 (pre-1950 allowed for the opening-stock estimate) |
| `country` | code | In `countries.csv` (`XWL` allowed here) |
| `value_low`, `value_central`, `value_high` | float ≥ 0 | low ≤ central ≤ high |
| `unit` | string | SI or SI-derived (e.g. `TWh`, `t`, `m3`, `GW`, `t/GW`, `1` for dimensionless) |
| `below_detection` | bool | As master |
| `basis`, `source_ids`, `notes` | | As master |

**Key:** (`series`, `year`, `country`) across all activity files. The **mass of earth moved** (the D21 memo series in tonnes) is stored here as `earth_moved_t_<stream>`; the Bq side is in master rows with tier `memo_earth_moved`.

### 4.7 `commodity_factors.csv`

| Column | Type | Rule |
|---|---|---|
| `commodity` | enum | `vocab.json` → `commodities` |
| `component` | enum | `own_residue`, `embedded_fuel` (METHODS §6.2) |
| `group` | code | In `groups.csv` |
| `tier` | enum | Any non-Sealed tier |
| `route` | enum | Required when `tier = liberated`, else empty |
| `residue_type` | code | In `residue_types.csv`; required for residue tiers, else empty |
| `region` | code | In `countries.csv` (`XWL` allowed) |
| `year_from`, `year_to` | int | Validity window, `year_from ≤ year_to` |
| `allocation_variant`, `allocation_rule` | enum, list | As master; variant completeness and token coupling as master (§3.3 rule 3) |
| `value_low`, `value_central`, `value_high` | float ≥ 0 | Activity per tonne of refined commodity; low ≤ central ≤ high |
| `unit` | const | `Bq/t` |
| `below_detection` | bool | As master |
| `basis`, `source_ids`, `notes` | | As master |

**Key:** (`commodity`, `component`, `group`, `tier`, `route`, `residue_type`, `region`, `year_from`, `allocation_variant`).

### 4.8 `countries.csv`

| Column | Type | Rule |
|---|---|---|
| `code` | code | Three capital letters, unique |
| `name` | string | |
| `kind` | enum | `iso3166_1`, `iso3166_3_former`, `user_assigned` |
| `valid_from`, `valid_to` | int | Optional validity window, inclusive |
| `notes` | string | |

### 4.9 `data/factors/*.csv` — factor registry

Every modelled master row cites the factor(s) it was computed from. The registry is what makes correlated uncertainty (METHODS §11.1) and the Task 4.1 audit possible.

| Column | Type | Rule |
|---|---|---|
| `factor_id` | code | `<stream>:<4 digits>`, e.g. `coal:0012`; unique across all factor files |
| `description` | string | What the factor is |
| `stream`, `stage` | enum, code | Stage allowed for the stream |
| `driver_series` | code | The activity series it multiplies, if any; must exist in `data/activity/` |
| `group`, `tier`, `route`, `residue_type` | | Optional; as master where given |
| `region` | code | In `countries.csv` (`XWL` allowed) |
| `year_from`, `year_to` | int | Validity window, `year_from ≤ year_to` |
| `value_low`, `value_central`, `value_high` | float ≥ 0 | low ≤ central ≤ high |
| `unit` | string | e.g. `Bq/t`, `Bq/m3`, `Bq/GWa`, `1` |
| `below_detection` | bool | As master |
| `basis`, `source_ids`, `notes` | | As master |

Master rows that share a `factor_id` are treated as fully correlated in that factor's uncertainty.

### 4.10 `residue_types.csv` — engine parameters

| Column | Type | Rule |
|---|---|---|
| `residue_type` | code | Unique |
| `description` | string | |
| `streams` | list | Streams that use it |
| `epsilon_rn222_low/central/high` | float in [0, 1] | Effective radon exhalation fraction (METHODS §5.2) |
| `epsilon_rn220_low/central/high` | float in [0, 1] | Effective thoron exhalation fraction |
| `seepage_per_a_low/central/high` | float in [0, 1] | Annual fraction of the impounded stock that seeps to Liberated |
| `basis`, `source_ids` | | Required if any parameter set is filled |
| `notes` | string | |

Each parameter set (the three ε-Rn222 values, the three ε-Rn220 values, the three seepage values) is either **all empty** (not yet set, Phase 1) or **all filled** with low ≤ central ≤ high. The pipeline refuses to run on an empty set for a residue type that has data rows; the validator only checks consistency.

### 4.11 `reference_bands.csv` — nuclide-data uncertainty (D27)

| Column | Type | Rule |
|---|---|---|
| `band_id` | code | `RB` + 2 digits, unique |
| `quantity_class` | enum | `half_life`, `e_alpha`, `e_beta`, `e_beta_forbidden`, `e_photon`, `e_photon_low`, `e_electron`, `e_electron_low`, `e_total_alpha_dominated`, `e_total_other`, `group_e_chain`, `group_e_k40`, `group_e_artificial` |
| `applies_to` | list | `*` (the class default) or named nuclides/groups, all in `nuclides.csv` or `groups.csv` |
| `rel_low`, `rel_high` | float | Relative band, −1 ≤ `rel_low` ≤ 0 ≤ `rel_high` |
| `basis`, `source_ids`, `notes` | | As master |

**Precedence:** a row naming a nuclide or group overrides the class's `*` row. **Key:** (`quantity_class`, each entry of `applies_to`): a nuclide may appear only once per class.

### 4.12 `residue_seepage_by_group.csv` — per-group seepage overrides (v2.3, D56)

The residue-type triple in §4.10 applies one seepage fraction to every nuclide group in an impounded stock, but the groups differ by up to a factor of about 30 (U against Ra) and about 1500 (soluble K-40). This table holds group-specific triples.

| Column | Type | Rule |
|---|---|---|
| `residue_type` | code | In `residue_types.csv` |
| `group` | code | In `groups.csv` (head code, e.g. `U238+`, `Th230`, `K40`) |
| `seepage_low/central/high` | float in [0, 1] | Annual fraction of the group's impounded stock that seeps to Liberated; low ≤ central ≤ high; all three required |
| `basis` | enum | Required; as master (`modelled` for the first release) |
| `source_ids` | list | Required; every ID in `sources.csv` |
| `notes` | string | States the derivation |

**Key:** (`residue_type`, `group`) is unique.

**Fallback rule:** for a given residue type and group, the engine uses the row here if one exists; otherwise it uses the residue-type triple in `residue_types.csv` (§4.10). A row is useful only where the residue type has a filled seepage set, and the validator does not require one for the other residue types. Rows are added only where research supports a group-specific number; absence of a row means "same as the residue-type triple", not "zero".

---

## 5. Controlled vocabularies (`data/reference/vocab.json`)

### 5.1 Substreams

| Stream | Substreams |
|---|---|
| `nuclear` | `pwr`, `bwr`, `phwr`, `gcr`, `lwgr`, `fbr`, `other_reactor`, `fuel_cycle` (for stages not tied to a reactor type) |
| `coal` | `power`, `non_power`, `all` (stages not split by end use, e.g. mining) |
| `oil_gas` | `conventional`, `unconventional`, `oil_sands` (D26) |
| `wind_solar` | `wind`, `solar` |
| `other` | `geothermal`, `biomass_peat`, `hydro`, `biomass_domestic` (household heating, D45; uses stage `biomass_peat`) |

### 5.2 Stages (from METHODS §6.3)

| Stream | Stages |
|---|---|
| `nuclear` | `u_mining_conv`, `u_mining_isl`, `u_milling`, `conv_enrich_fab`, `reactor_operation`, `spent_fuel`, `reprocessing`, `sea_disposal`, `construction`, `decommissioning`, `accident` |
| `coal` | `coal_mining`, `combustion_power`, `combustion_nonpower`, `construction` |
| `oil_gas` | `drilling`, `production`, `oil_sands_mining`, `processing_transport`, `abandonment_scrap`, `construction` |
| `wind_solar` | `commodity_supply`, `end_of_life` |
| `other` | `geothermal`, `biomass_peat`, `hydro`, `construction` |

### 5.3 Stage–tier matrix

Allowed tiers per stage for non-transfer rows, as in METHODS §6.3 (`memo_earth_moved` is allowed only at the mining stages `u_mining_conv`, `coal_mining`, `oil_sands_mining` and `commodity_supply`).

| Stage | Allowed tiers |
|---|---|
| `u_mining_conv` | impounded, reisolated, liberated, memo_earth_moved |
| `u_mining_isl` | impounded, reisolated, liberated |
| `u_milling` | sealed_fuel_cycle, impounded, dispersed, liberated |
| `conv_enrich_fab` | sealed_fuel_cycle, impounded, liberated |
| `reactor_operation` | sealed_in_core, sealed_fuel_cycle, liberated |
| `spent_fuel` | sealed_fuel_cycle |
| `reprocessing` | sealed_fuel_cycle, liberated |
| `sea_disposal` | sealed_fuel_cycle, liberated |
| `decommissioning` | sealed_fuel_cycle, impounded, dispersed, liberated |
| `accident` | sealed_in_core, sealed_fuel_cycle, sealed_damaged_core, liberated |
| `coal_mining` | impounded, dispersed, liberated, memo_earth_moved |
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
| `biomass_peat` | impounded, dispersed, liberated, memo_biosphere |
| `hydro` | liberated |

Transfer rows follow §3.1 instead of this matrix.

### 5.4 Technologies (lifecycle view, D22)

`coal_power`, `gas_power`, `oil_power`, `nuclear`, `wind`, `solar`, `geothermal`, `biomass`, `hydro`.

### 5.5 Products and commodities

- **Precedence:** the commodity-stage rule is applied first, then the oil-and-gas rule. So an `oil_gas` row at `construction` takes a commodity (building materials), not an oil or gas product.
- **Oil and gas** (`stream = oil_gas`, every stage except `construction`): `product` is **required**, one of `oil`, `gas`, `ngl`, `bitumen`. Residues shared between products are split by value (D6, `alloc:value`).
- **Commodity stages** (`commodity_supply`, `end_of_life`, `construction`): `product` is **required**, one of `vocab.json` → `commodities`.
- **`decommissioning`** (nuclear): `product` must be empty. Decommissioning waste and releases are not commodities.
- **Every other row:** `product` must be empty.

### 5.6 Allocation-rule tokens

`none`; `alloc:value`, `alloc:mass` (the default split); `alloc:main`, `alloc:radio` (the two bounds, METHODS §10.1); `elec_share` (electricity-share attribution, METHODS §8); `civil:doc`, `civil:pre1965`, `civil:ratio` (uranium, METHODS §9.2); `civil:throughput` (dual-use reprocessing, METHODS §9.2). A rule is one or more tokens, `;`-separated.

### 5.7 Release routes (Liberated rows only)

`air_stack`, `air_ventilation`, `air_process_vent`, `air_vented_gas`, `air_delivered_gas`, `air_dust`, `water_liquid_effluent`, `water_mine_drainage`, `water_produced_discharge`, `water_spill`, `sea_disposal_package`, `air_rerelease` (fallout Cs-137 re-emitted by biomass combustion, D43/D48: allowed only with `stage = biomass_peat`, `group = Cs137+`, `quantity = flow`; such rows are reported separately in cross-stream totals); and, **for event `transfer_in` rows only**, `air_accident_release` and `water_accident_release` (`vocab.json` → `accident_routes`). There is deliberately no general "other" route, and none for exhalation from residues or for seepage (§3.2).

### 5.8 Other entries

`quantities` (with units), `basis`, `allocation_variants`, `residue_tiers`, `civil_rule_stages`, `routine_transfers`, `opening_stock_year`, `event_types`, `event_inclusion`, `source_types`, `source_access`, `source_licence`, `source_url_required_access`, `banned_domains`, `banned_citation_terms`, `dose_tokens`, `forbidden_column_tokens`, `value_checked_columns`, `year_range`, and `derived` (§8).

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

- `root` is a project root laid out as in §2. Every call validates all the **required** files of §2, plus every **optional** file that exists: `data/events.csv`, `data/baselines.csv`, `data/reference/commodity_factors.csv`, `data/reference/residue_seepage_by_group.csv`, `data/activity/*.csv`, `data/factors/*.csv`.
- `master_files`: paths (absolute, or relative to `root`) of master-format CSVs to check. If `None`, every `data/streams/*.csv` (sorted by name). `build/master.csv` is checked only when passed explicitly. An empty list checks no master files.
- An empty list of issues means everything is valid. Issues are returned sorted by file, then row (`None` first), then rule.
- A missing *required* file raises `FileNotFoundError`. It is not reported as an `Issue`.
- **Cross-row rules (X\*) consider all master files together**, in processing order (§6.5).

### 6.2 Command line

`python -m pipeline.validate [--root DIR] [FILE ...]` (also `pixi run validate`).
- `--root` defaults to the current directory; `FILE`s are master files (default as above).
- Prints one line per issue to stdout, `file:row: RULE message` (`row` printed as `-` when `None`), then a summary line. Errors go to stderr.
- **Exit codes:** 0 = no issues; 1 = one or more issues; 2 = usage error or missing required file.

### 6.3 Rule codes

One row may raise several codes. Each code is raised **only** for the condition stated. Where a condition is expressible in the table's JSON schema it is reported under that table's schema code (`R02`, `S01`, `E01`, `T01`), not under another code.

**File level (any CSV the validator reads)**

| Code | Condition |
|---|---|
| `F01` | Header does not exactly match the specified columns, in order |
| `F02` | A column name contains a dose token as a whole word (§1) |
| `F03` | File cannot be read as UTF-8 CSV, or a listed master file does not exist |
| `D01` | A cell value in a checked column (`series`, `unit`, `name`, `description`, `quantity_class`) contains a dose token as a whole word (§1). Reported once per row |

**Master table**

| Code | Condition |
|---|---|
| `R01` | A cell cannot be coerced to its type (§6.4) |
| `R02` | The coerced row fails `schema/master.json` (types, fixed enums, and the conditionals: unit/quantity, `standing_inventory`/`sealed_in_core`, `opening_stock`, memo flows, `below_detection`, `embedded_fuel`, `residue_type` and `route` by tier, `factor_ids` for modelled rows, bound tokens, civil year rules) |
| `R03` | `value_low ≤ value_central ≤ value_high` does not hold |
| `V01` | `substream` not allowed for `stream` |
| `V02` | `stage` not allowed for `stream` |
| `V03` | `tier` not allowed for `stage` (§5.3); not raised for transfer rows |
| `V04` | `group` not in `groups.csv` |
| `V05` | `country` not in `countries.csv` |
| `V06` | `country` has a validity window and `year` falls outside it |
| `V07` | A `source_ids` entry not in `data/sources.csv` |
| `V08` | `event_id` not in `data/events.csv` |
| `V09` | A flow-only group used other than as allowed in §4.2 |
| `V10` | `country = XWL` |
| `V11` | `product` breaks the product rules (§5.5): missing where required, present where not allowed, or not in the vocabulary that applies |
| `V12` | `residue_type` not in `residue_types.csv` |
| `V13` | A `factor_ids` entry not in the factor registry |
| `V14` | An accident route (`vocab.accident_routes`) on a row that is not an event `transfer_in` |
| `V15` | A `flow` row in `liberated` at a routine-transfer stage (`vocab.routine_transfers`); those discharges must be routine transfers out of Sealed |
| `X01` | Duplicate unique key (§3) |
| `X02` | Transfers do not balance for a balance key (§3.1; relative tolerance 10⁻⁶ for each of low/central/high). Reported once per key, with `row = None`, against the first file containing that key |
| `X03` | Allocation completeness (§3.3 rule 3): a key has a non-default variant but not all three, **or** in a complete key the `default` row's rule lacks `alloc:value`/`alloc:mass`. Reported once per key, on the key's first row. (A bound row lacking its own token is `R02`, not `X03`) |
| `X04` | A `nuclear` row at a civil-rule stage (§3.3 rule 4) with no `civil:` token |
| `X05` | An illegitimate transfer (§3.1): an event transfer whose tier does not match the event (`transfer_out` ≠ `from_tier`, or `transfer_in` ∉ `to_tiers`); or a transfer with no `event_id` at a stage not in `routine_transfers`, or with tiers other than that stage's routine pair |

**Reference and support tables**

| Code | Table | Condition |
|---|---|---|
| `S01` | sources | Row fails `schema/sources.json` (incl. coercion failure, and a missing `url` for paywalled/inaccessible), or a duplicate `source_id` |
| `S02` | sources | `url` host on a banned domain or a subdomain of one; or `short_cite`/`full_citation` containing a banned citation term (case-insensitive) |
| `E01` | events | Row fails `schema/events.json` (incl. coercion failure); or a date that is not a real calendar date; or `date_end` < `date_start`; or activity low ≤ central ≤ high fails; or `from_tier` ∈ `to_tiers`; or a duplicate `event_id` |
| `E02` | events | `stage` not allowed for `stream`, `country` unknown, or a `source_ids` entry unknown |
| `E03` | events | The inclusion criterion (§4.4) is not met: threshold or destination/source tier |
| `N01` | nuclides | `branching` does not sum to 1 within 10⁻⁴, or `daughters` and `branching` lengths differ |
| `N02` | nuclides | `e_total_mev` ≠ the sum of the five components (relative 10⁻⁶) |
| `N03` | nuclides | `lambda_per_a` ≠ ln 2 / `half_life_a` (relative 10⁻⁶) |
| `G01` | groups | A head or member not in `nuclides.csv`, or the head is not the first member |
| `G02` | groups | `multiplier` ≠ the sum of `member_weights` (relative 10⁻⁶), or the lengths of `members` and `member_weights` differ |
| `G03` | groups | `multiplier_scope = flow_only` but `role ≠ released_gas`, or the reverse |
| `G04` | groups | `chain`, `role` or `multiplier_scope` not in its enum; a `parent_group` not in `groups.csv`; or a duplicate `group` |
| `G05` | groups | A released-gas group that names a `parent_group`, where that parent is not a `chain` group containing the gas group's head as a member (released gases with no parent, e.g. `Kr88+`, are not escape groups and are not checked) |
| `T01` | countries, activity, baselines, commodity_factors, factors, residue_types, residue_seepage_by_group, reference_bands | Row fails the table's JSON schema (incl. coercion failure) |
| `T02` | same | Duplicate key (§4.5–4.11) |
| `T03` | same | Bounds out of order (low ≤ central ≤ high, including `seepage_low/central/high` in `residue_seepage_by_group`; `year_from ≤ year_to`; residue parameter sets all-or-none and ordered; residue parameters filled without `basis` and `source_ids`) |
| `T04` | same | A reference that does not resolve: `source_ids` (sources), `country`/`region` (countries), `group` (groups), `residue_type` (residue types; also `residue_seepage_by_group`), `driver_series` (activity series), `stage` for the stream (factors), `applies_to` (nuclides or groups) |
| `T05` | commodity_factors | Allocation completeness, as `X03` (bound-row tokens are `T01`) |

**Membership vs schema.** The JSON schemas check types, fixed enums and conditional rules. They do **not** check whether a substream, stage, product, residue type, country, group, source, factor or event ID exists; those are V-, E02- and T04-codes only. If `stream` itself is invalid (`R02`), `V01`–`V03` and `V11` are skipped for that row; if `tier` is invalid, `V03` is skipped.

### 6.4 Coercion rules

Applied before schema validation, in every table:
- integers (`year`, `rank`, `year_from`, `year_to`, `valid_from`, `valid_to`) from digit strings; floats (`value_*`, `mass_t`, `activity_*`, `lat`, `lon`, `rel_*`, `epsilon_*`, `seepage_*`, energies, branching) accept exponent notation; NaN and infinities are coercion failures;
- booleans from `true` / `false` only;
- lists (`source_ids`, `factor_ids`, `allocation_rule`, `to_tiers`, `streams`, `applies_to`, and the `;`-lists in nuclides and groups) split on `;`;
- an empty cell in a nullable column → `null`. In the master table the nullable columns are `product`, `residue_type`, `factor_ids`, `technology`, `route`, `event_id` and `notes`; any other empty master cell → `R01`. In the other tables an empty cell becomes `null` and the schema decides whether that is allowed (so a missing required value is `S01`, `E01` or `T01`).
- In the master table, `allocation_rule` is stored as its token string for the schema check (pattern), and also split into tokens for the cross-row rules.

### 6.5 Behaviour details

| Case | Behaviour |
|---|---|
| A master file outside `root` | `Issue.file` is its absolute POSIX path |
| "Later" and "first" across files | Processing order: the order of `master_files` (or sorted names by default), then row order. `X01` is reported on the later occurrence; `X03` on the key's first row |
| Duplicate IDs in sources, events, groups, support tables | Reported on the later row |
| A master row with `R01` | `R02` and `R03` are skipped for that row; V-checks still run on the cells that coerced; `X01` and `X05` still run; `X02` skips the whole balance key; `X03` and `X04` skip the row |
| A file with `F01`, `F02` or `F03` | Its data rows are not validated (nor used for lookups) |
| Country validity window | Inclusive: valid if `valid_from ≤ year ≤ valid_to` |
| CLI paths | Relative `FILE` arguments are taken relative to `--root` |
| Unknown or missing event | `V08` only; `X05` is skipped for that row |
| Unknown stage | `V02` only; `V03` and `V11` are skipped |
| Banned domains | Matched on the URL's host only: the domain itself or any subdomain |
| A header-only CSV | Valid |
| Nuclear `construction` | Has no Sealed tier (construction materials are never in licensed isolation), so every row carries a commodity |
| Accident routes on non-accident events | Allowed: the accident routes mean "released by an event" (accident, impoundment failure or spill), whatever the event type |
| `V15` scope | Only `flow` rows are barred; event transfers into `liberated` at routine stages are legitimate, and `opening_stock` never sits in a routine stage's Liberated tier in practice (not checked) |
| An event row with `E01` | `E03` is skipped for that row (its inputs may be missing or invalid); `E02` still runs |
| Flow-only groups (V09) | Every use not listed in §4.2 is `V09`, including `opening_stock`, `transfer_in` to a non-Liberated tier and `transfer_out` from a tier other than `sealed_in_core` |
| T04 in the factor registry | Resolves `source_ids`, `region`, `group`, `residue_type`, `driver_series` and the stage for the stream (`tier` and `route` are enums, so `T01`) |
| Countries | `valid_from > valid_to` is `T03`; countries have no `T04` |
| Dose tokens | `F02` uses `vocab.forbidden_column_tokens`, `D01` uses `vocab.dose_tokens` (identical lists by default, kept separate so either can be tuned). Matching is whole-word on lower-cased text split on every non-alphanumeric character; `µ` and `μ` count as letters. `D01` is one issue per row, listing the offending column=value pairs |
| `reference_bands` keys | Each named nuclide or group at most once per `quantity_class`, and the `*` default at most once per class |
| `residue_seepage_by_group` | Optional (absent = no issue; header-only is valid). `T01`: all three `seepage_*` values, `basis` and `source_ids` required, values in [0, 1]. `T02`: duplicate (`residue_type`, `group`), on the later row. `T03`: low ≤ central ≤ high. `T04`: `residue_type` in `residue_types.csv`, `group` a head code in `groups.csv`, every `source_ids` entry in `sources.csv`. The residue type need not have a filled seepage set in `residue_types.csv`. `data/streams_pre1950/` files are never read |
| `residue_types` with only `basis`/`source_ids` filled | Allowed (no issue): recording a source before the values is harmless |
| Sources for reference tables | `reference_bands.csv` and `residue_types.csv` cite sources that must be in `data/sources.csv` (`T04`); `nuclides.csv` and `groups.csv` `source_ids` are not resolved in v2 |
| Issue order | Sorted by `file` (string), then `row` (`None` first), then `rule` |

---

## 7. Field-name mapping to PLAN Task 0.2

PLAN Task 0.2 listed indicative columns. The schema uses the following, for the reasons given:

| PLAN name | Schema name | Why |
|---|---|---|
| `process_stage` | `stage` | Shorter; the vocabulary is "stages" throughout METHODS |
| `nuclide` | `group` | D24: data are stored per nuclide group (a single nuclide is a one-member group) |
| `source_id` | `source_ids` | A value often rests on more than one source |

---

## 8. Derived outputs (provisional; settled in Tasks 3.2–3.7)

The pipeline's outputs under `build/` are not inputs and are not validated by `validate.py` in v1. Their dimensions, recorded so that Phase 2 data carry everything Phase 3 needs:

| Output | Dimensions |
|---|---|
| `build/stocks.csv` (Task 3.2) | year × stream × substream × stage × product × tier × group × `view` (`industry`/`lifecycle`) × `run` (`with_accidents`/`without_accidents`) × allocation variant; values in Bq (both `convention`s: `group` and `head`) and W; low/central/high |
| `build/flows.csv` (Tasks 3.1–3.3) | As stocks, for flows (Bq/a, W), plus engine-generated exhalation and seepage flows marked `engine` |
| `build/per_twh.csv` (Task 3.4) | lifecycle view only; technology × year × tier × group; per-TWh variants `levelised`/`annual` for construction and decommissioning; chronic horizons 100 / 500 / 10 000 a (D25) |
| `build/radiopassive.json` (Task 3.7) | Page export; its own JSON schema is written in Task 3.7 |

The vocabularies for these (`views`, `runs`, `conventions`, `horizons_a`, the tier roll-up to the four D2 tiers, and the stage-to-phase map used for levelising) are in `vocab.json` → `derived`.

---

## 9. Change log

| Date | Change |
|---|---|
| 2026-10-20 | **v2.1** from the schema re-review: nuclear `construction_decom` split into `construction` and `decommissioning` (no product on decommissioning); `conv_enrich_fab` added to routine transfers; `V15` bars Liberated flows at routine stages; catch-all routes `air_other`/`water_other` replaced by event-only accident routes (`V14`); §3.2 claim reworded. |
| 2026-10-20 | First draft (Task 0.2). |
| 2026-10-20 | Added `role` and `multiplier_scope` to groups.csv (from Task 0.3). |
| 2026-10-20 | Added the validator contract (API, CLI, rule codes, coercion) and behaviour details from the spec-blind test ambiguities. |
| 2026-10-20 | v2 behaviour details from the second spec-blind test pass (B1–B11); bound-token coupling is `R02` only; `E03` skipped after `E01`; commodity-stage product rule takes precedence. |
| 2026-10-20 | **v2** after the independent schema review: master gains `product`, `residue_type`, `factor_ids`, `route`; routine vs event transfers; events gain `to_tiers` and activity bounds; `opening_stock` (D31); new tables `residue_types.csv`, `reference_bands.csv`, factor registry; JSON schemas and rule codes (`T01`–`T05`, `D01`) for every support table; `V10`–`V13`, `E03`, `G04`, `G05`; dose tokens checked in values; URL required for inaccessible sources; field-name mapping; provisional derived-output dimensions. |
| 2026-10-25 | **v2.2** (Steve): tier `memo_biosphere` (D47; biosphere-cycling memo for wood ash and wood natural nuclides, D43/D44; allowed at `biomass_peat`; flow only; not in tier totals); route `air_rerelease` (D48; schema conditional ties it to `biomass_peat`/`Cs137+`/flow); substream `biomass_domestic` and residue type `biomass_domestic_ash` (D45); `dispersed` at `coal_mining` and `sealed_fuel_cycle` at `accident` (D36). |
| 2026-10-26 | **v2.3** (Steve): new table `residue_seepage_by_group.csv` (§4.12, D56), with fallback to the residue-type triple; seepage triples filled for 15 residue types (D55); sources S0950–S0971 added; pre-1950 stream file convention `data/streams_pre1950/<stream>.csv` documented (§3, D57). |
