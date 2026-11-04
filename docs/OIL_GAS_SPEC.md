# `pipeline/streams/oil_gas.py` — stream script contract (Task 2.3, oil and gas)

Status: v0.1 DRAFT (2026-11-04), for the test-writer and the code-writer. The items that could not be settled from the documents are collected in §11 (open questions for Steve); **each has a recommended default and the default is already written into the body**, so the contract can be read and built as it stands. If Steve answers differently, only the section named in the question changes. Derived from METHODS §2.3, §3, §5, §6.3, §10 (D6), §11, SCHEMA §3–§5 (v2.4a) and `data/reference/vocab.json`, `docs/LIB_SPEC.md` (v1.4, §10 `substream` match key), `data/factors/oil_gas.csv` (factors `oil_gas:0001`–`oil_gas:0110`), `research/oil_gas/factors_notes.md` (incl. §8 D65 and §9 D66), `research/oil_gas/papers_round2.md` and `papers_round3.md`, and the activity files `data/activity/oil_gas.csv` and `data/activity/oil_gas_drivers.csv`. Modelled on `docs/NUCLEAR_SPEC.md` v1.2 (structure) with the `docs/COAL_SPEC.md` §11–§12 lessons built in from the start: `XXX` for world rows and `XWL` for factor and activity lookups, correlated versus independent differences, flag-cause and driver-basis suffixes in `notes`, aggregated log runs, strict `no factor row` handling, a raise on duplicate activity rows, a CLI that diffs the log as well as the outputs, a pre-1950 file, tests that read factor values from the files behind explicit PREMISE assertions, benchmarks with independent estimates, and known misses documented rather than hidden. Where this file and METHODS disagree, METHODS wins and this file is a bug. Decisions in force: D6 (allocation), D14, D17 (re-isolated sub-tier), D21 (counted residues; no above-threshold waste rock here), D22, D24, D26 (sub-streams), D31 (opening stock), D42, D52, D54 (release cap), D57 (pre-1950 files), D58 (coal lessons), D62 (residue parameters), D63 (factor `substream`), D65 and D66 (oil and gas revisions) and D68 (10⁻⁵ balance and closure tolerance).

The script is a pure function of the files under `data/`. It uses only `pipeline.lib` and the standard library plus pandas/numpy if needed. It never reads the network and never decays anything: decay, ingrowth of Pb-210, Po-210 and Th-228 in scale, radon and thoron exhalation from impounded and dispersed residues, and seepage all belong to the Phase 3 engine (METHODS §5.2). It does not read `data/events.csv`: no civil oil and gas event meets METHODS §9.1 (D32), so the stream has no event rows and no `event_id`.

---

## 1. Interface

```
python -m pipeline.streams.oil_gas [--root PATH] [--write]
```

- Without `--write`, outputs go to a scratch directory and are diffed against the committed files; the exit status is non-zero if **any of the three** files below differs.
- With `--write`, the three output files are overwritten.
- The CLI prints one line per log kind, `log <kind>: <count>`.
- `build(root: Path) -> BuildResult` is the importable entry point. `BuildResult` has three attributes: `rows` (master-row dicts, 1950–2025), `rows_pre1950` (master-row dicts, 1900–1949) and `log` (list of dicts, §8). `root` is the repository root, so tests can build a miniature tree in `tmp_path` with the same file names and columns.

| File | Content |
|---|---|
| `data/streams/oil_gas.csv` | Master rows, years 1950–2025. Must pass `python -m pipeline.validate --root .` |
| `data/streams_pre1950/oil_gas.csv` | Master columns, years 1900–1949, `quantity = flow` only; outside the master schema (SCHEMA §3.2, D57). Non-empty: gas and oil radon and the Pb-210 plate-out in the gas system (§6), which have drivers from 1900. Nothing else is non-empty today (§3.8) |
| `research/oil_gas/build_log.csv` | The full log (§8). Not a master file and not validated |

Master files are written with `pipeline.lib.rows.write_master` (deterministic, sorted by the SCHEMA §3 key; `write_master([])` writes a header-only file).

## 2. Inputs

### 2.1 Activity series (read with `read_table` from **both** files; values are `Bounds(value_low, value_central, value_high)`)

All series keys are (`series`, `year`, `country`) across both files. A duplicate key raises `LibError` naming it (§3.7).

| Series | File | Country rows | Years | Unit | Used for |
|---|---|---|---|---|---|
| `produced_water_m3` | `oil_gas.csv` | `USA`, `XWL` | 1950–2025 | `m3` | §5 (all production, scale, sludge and abandonment rows) |
| `gas_production_m3` | `oil_gas.csv` | 42 countries plus `XWL` | 1900–2025 | `m3` | §6.2 (gas radon, NGL radon, vented gas, Pb-210 plate-out); §4 (allocation quantity, `USA` and `XWL` only) |
| `oil_production_t` | `oil_gas.csv` | the same 42 plus `XWL` | 1900–2025 | `t` | §6.3 (oil radon) |
| `oil_production_m3` | `oil_gas.csv` | the same 42 plus `XWL` | 1900–2025 | `m3` | §4 only (allocation quantity, `USA` and `XWL` only) |
| `ngl_production_m3` | `oil_gas_drivers.csv` | 215 countries plus `XWL` | 1949–2025 | `m3` | §4 only (`USA` and `XWL` only; the other rows are never read, see §10) |
| `unit_value_oil_usd_per_m3`, `unit_value_gas_usd_per_m3` | `oil_gas_drivers.csv` | `USA`, `XWL` | 1950–2025 | `USD/m3` | §4 |
| `unit_value_ngl_usd_per_m3` | `oil_gas_drivers.csv` | `XWL` | 1950–2025 | `USD/m3` | §4 |
| `gas_flared_m3` | `oil_gas_drivers.csv` | `XWL` 1950–2025; 103–104 country rows 2012–2025 | 1950–2025 | `m3` | §6.4 |
| `oil_sands_ore_processed_t` | `oil_gas_drivers.csv` | `CAN` | 1967–2025 | `t` | §7.3 |
| `us_wells_drilled_vertical` | `oil_gas_drivers.csv` | `USA` | 1949–2025 | `1` | §7.2 |
| `us_wells_drilled_horizontal` | `oil_gas_drivers.csv` | `USA` | 1980–2025 | `1` | §7.2 |
| `elec_gen_gas`, `elec_gen_oil` | `electricity_generation.csv` | `XWL` | 1900–2025 | `TWh` | §9(e) denominators only |
| `gas_power_share`, `oil_power_share` | `oil_gas.csv` | `XWL` | 1920–2024, 1903–2024 | `1` | §9(e) only |
| `gas_flared_reported_m3` | `oil_gas_drivers.csv` | 219 countries plus `XWL` | 1980–2017 | `m3` | §9(e) cross-check only (EIA national submissions, vented and flared, a different basis) |

**Not used by the script:** `produced_water_unconv_share` (USA 2017 only, 0.16; a cross-check of registry row `oil_gas:0014`, §9(i)); `us_wells_drilled_total`, `_oil`, `_gas`, `_dry` (retired for drilling by D66); `gas_production_twh`, `oil_production_twh`, `gas_burn_power_twh`, `oil_burn_power_twh`.

A series (or country row) that is absent from `data/activity/` in a fixture gives no rows and one aggregated `no_driver` entry (§8); the script must not raise. A year with a driver of exactly `0/0/0` gives no rows (a structural zero factor result is still written, §3.4). Country-years absent from a country series are silent.

### 2.2 Other inputs

- **Factors** (`data/factors/oil_gas.csv`), looked up with `pipeline.lib.factors.select` and applied with `apply` (§3.4). The registry carries the `substream` column (directly after `stage`).
- **Residue types, groups, vocabulary** are not read by the script. The validator and the engine use them. The residue types the stream uses all exist in `residue_types.csv` (`og_scale`, `og_sludge`, `og_produced_water`, `og_scaled_scrap`, `og_drill_cuttings`, `og_processing_residue`, `oil_sands_tailings`); their engine parameters are discussed in §7.4.
- **Events** are not read (no oil and gas events, D32). A premise assertion (§9(i)) checks that `events.csv` has no `oil_gas` row, so a later event fails loudly.

### 2.3 Factor selection keys (the registry strings exactly)

`select(factors, year=y, region=R, **keys)`. **Empty registry cells are passed as `""`, never `None`** (NUCLEAR_SPEC §13 item 8, LIB_SPEC §10 item 3). The script passes `substream` on every call: the value shown in the table, or `""` where the registry cell is empty, which with exact-equality semantics excludes the `conventional` and `unconventional` rows (LIB_SPEC §10 item 1). `stream` is not passed (the file is one stream). The registry was checked with an independent emulation of `select`: every call below yields **exactly one** row for every year it is used, and the winning ids are listed for orientation.

| Key | `stage` | `substream` | `group` | `tier` | `route` | `residue_type` | `driver_series` | Region `R` | Winning ids (orientation) |
|---|---|---|---|---|---|---|---|---|---|
| C (conventional concentration) | `production` | `conventional` | $g\in\{$`Ra226+`, `Ra228+`, `K40`, `Pb210+`$\}$ | `""` | `""` | `""` | not passed | `USA` or `XWL` | `0002`/`0001` (Ra226+), `0005`/`0004` (Ra228+), `0007` (K40), `0009` (Pb210+); exact `USA` beats `XWL` for the two Ra groups only |
| C′ (unconventional concentration) | `production` | `unconventional` | same four groups | `""` | `""` | `""` | not passed | `USA` or `XWL` | `0003`, `0006`, `0008`, `0010` (region `XWL` for both, by fallback) |
| U (unconventional share) | `production` | `""` | `""` | `""` | `""` | `""` | `produced_water_unconv_share` | `USA` or `XWL` | USA `0011` (1950–2005), `0012` (2006–10), `0013` (2011–16), `0014` (2017), `0015` (2018–25); XWL `0016` (1950–2005), `0017` (2006–15), `0018` (2016–25) |
| T (fate of water activity) | `production` | `""` | `""` | $t\in\{$`reisolated`, `impounded`, `liberated`, `dispersed`$\}$ | `water_produced_discharge` for `liberated`, else `""` | `og_produced_water` (reisolated, dispersed), `og_sludge` (impounded), `""` (liberated) | `produced_water_m3` | `USA` or `XWL` | USA `0019`–`0038` (eras 1950–69, 1970–99, 2000–09, 2010–14, 2015–25), XWL `0039`–`0046` (1950–69, 1970–2025) |
| Σ (solids-bound fraction) | `production` | `""` | `Ra226+`, `Ra228+` | `""` | `""` | `og_scale` or `og_sludge` | not passed | `XWL` | `0047`–`0050` |
| Π (Pb-210 at formation) | `production` | `""` | `Pb210+` | `""` | `""` | `og_scale` or `og_sludge` | not passed | `XWL` | `0051`, `0052` |
| R (fate of removed solids) | `production` | `""` | `""` | `impounded`, `dispersed`, `liberated` | `water_produced_discharge` for `liberated`, else `""` | `og_scale` or `og_sludge` | **`""`** | `XWL` | scale `0053`–`0061`, sludge `0062`–`0070` (eras 1950–84, 1985–99, 2000–25) |
| Φ (retained-scale fraction) | `abandonment_scrap` | `""` | `""` | `""` | `""` | `og_scale` | `""` | `XWL` | `0078` |
| A (fate of retained scale) | `abandonment_scrap` | `""` | `""` | `impounded` with `og_scale`; `dispersed` with `og_scaled_scrap` | `""` | as tier | not passed | `XWL` | `0079`–`0084` (creation-year eras 1950–64, 1965–79, 1980–25) |
| GD (delivered gas Rn) | `processing_transport` | `""` | `Rn222+` | `liberated` | `air_delivered_gas` | `""` | not passed | country or `XWL` | `0074` |
| GN (NGL Rn) | `processing_transport` | `""` | `Rn222+` | `liberated` | `air_delivered_gas` | **`og_processing_residue`** | not passed | country or `XWL` | `0110` |
| GV (vented gas Rn) | `processing_transport` | `""` | `Rn222+` | `liberated` | `air_vented_gas` | `""` | not passed | country or `XWL` | `0075` |
| GP (Pb-210 plate-out) | `processing_transport` | `""` | `Pb210+` | `impounded` | `""` | `og_processing_residue` | not passed | country or `XWL` | `0076` |
| OR (oil Rn) | `processing_transport` | `""` | `Rn222+` | `liberated` | `air_stack` | `""` | not passed | country or `XWL` | `0077` |
| FL (flaring; §6.4, §12 R1) | `production` | `""` | `Rn222+` | `liberated` | `air_stack` | `""` | **`gas_flared_m3`** | country or `XWL` | the new row (R1) |
| OS (oil sands) | `oil_sands_mining` | `""` | `Th232`, `Ra228+`, `Th228+` | `impounded` | `""` | `oil_sands_tailings` | not passed (§7.3) | `CAN` | `0085`–`0087` |
| DV (vertical cuttings) | `drilling` | `conventional` | the 11 groups of §7.2 | `impounded` | `""` | `og_drill_cuttings` | not passed | `USA` | `0088`–`0098` |
| DH (horizontal cuttings) | `drilling` | `unconventional` | the same 11 groups | `impounded` | `""` | `og_drill_cuttings` | not passed | `USA` | `0099`–`0109` |

The explicit `driver_series` on U, T, R and Φ is what separates rows that share every other key (the water-fate rows from the removed-solids fate rows, which carry the same tier and residue type; the unconventional share from everything else). The `residue_type` on GN is **only a key device**: the registry carries `og_processing_residue` on `oil_gas:0110` so that its key differs from `oil_gas:0074`; **the master row for a liberated tier has no residue type** (SCHEMA §3). The same device is used by the removed-solids liberated rows (`0055`, `0058`, `0061`, `0064`, `0067`, `0070`).

---

## 3. Conventions (all rows)

### 3.1 Row columns

| Column | Value |
|---|---|
| `stream` | `oil_gas` |
| `substream` | `conventional` or `unconventional` for every family that comes from produced water or from cuttings (§5, §7.1, §7.2: the two substreams are separate rows); `oil_sands` for §7.3; **`conventional` for the families that cannot be split by sub-stream** (§6: gas and oil radon, NGL radon, Pb-210 plate-out, flaring), with a notes flag, see §11 Q3 |
| `stage` | per family (§5–§7) |
| `product` | required at every stage of this stream (SCHEMA §5.5, V11): `oil`, `gas`, `ngl` or `bitumen`. Joint residues carry each of `oil`, `gas`, `ngl` (§4); single-driver families carry the product named in their table; oil sands carry `bitumen` |
| `quantity`, `unit` | `flow`, unit `master_unit(result_unit(driver_unit, factor_unit), "flow")`, which is `Bq/a` for every row. The stream has **no transfers, no inventories and no opening stock** (METHODS §5.2: no routine-transfer stage, no event) |
| `basis` | `modelled` for every row. The factor's own basis (`compiled`, `measured`, `extrapolated`, …) stays in the registry; the driver basis goes into `notes` (§3.3) |
| `allocation_variant`, `allocation_rule` | single-driver families: `default` and `none`. Joint families: all three variants for every product, §4 |
| `embedded_fuel` | `False`. `technology` empty (the pipeline attributes by electricity share, SCHEMA §3) |
| `residue_type` | present exactly when the tier is `impounded`, `reisolated` or `dispersed`; empty on `liberated` (SCHEMA §3, R02) |
| `route` | present exactly when the tier is `liberated` (the registry route) |
| `event_id` | empty on every row |
| `factor_ids` | every factor used to compute the row, in the order applied (§3.9) |
| `source_ids` | union of the factors' `source_ids` and the driver rows' `source_ids` (and, on joint families, of the quantity and unit-value rows used for the allocation), sorted |
| `below_detection` | from the bounds (`nd_floored`), set by `make_row` |
| `notes` | rule text starting with the family code of §3.10, then suffixes (§3.3) |

**Country rule.** Global series and registry rows are looked up with country **`XWL`** (activity and factor region) and written with **`XXX`** (SCHEMA §3, V10). Rows of a producing country carry its code. `XXX` is also the rest-of-world residual (§5.1, §6.1, §6.4); those rows are distinguished by their notes text (the exact fragments are in the sections named). Water-borne, solids and abandonment rows are written for the two geographies `USA` and `XXX` (the rest of the world) because `produced_water_m3` exists for `USA` and `XWL` only. Drilling and oil sands rows are written for `USA` and `CAN` only (§7).

**Quantities are head-nuclide activity** of the group (METHODS §3.2, D24, D42); the engine applies the group multiplier. `Rn222+` rows are released-gas groups and appear only as liberated flows (SCHEMA V09).

### 3.2 Groups, families and the registry

The script never hard-codes a group list. A **family** is a set of registry rows that share the selection keys of §2.3. The groups of a family are the distinct `group` values among its registry rows over all years and regions. For each year the script calls `select` once per (group, tier, route, residue, substream) combination; a failed `select` is handled by §3.6. The expected group sets are listed in §5–§7 for orientation; tests read the actual sets from the file (§9(i)). The tier set of the produced-water fate (four tiers) and the residues of the removed-solids fate are likewise read from the registry rows, not listed in the script.

### 3.3 Flag cause and driver basis in `notes` (coal §12.3, §12.4, §12.15, §12.16)

- Every output row with `below_detection = true` ends its `notes` with `; below_detection cause: <causes>`, a `+`-joined subset, in this fixed order, of: `zero_central_factor`, `exact_zero`, `clipped_difference`, `floor_dominance`, `inherited_flag`. The script tracks the causes of its own inputs and carries them through products, sums and merges; it does not parse lib log text. Rows with `below_detection = false` carry no cause text.
  - `zero_central_factor`: an input factor with central 0 and high $>0$. **Expected in this stream:** the `XWL` unconventional share is `0/0/0.01` for 1950–2005 (`oil_gas:0016`), so every rest-of-world unconventional water row in 1950–2005 is flagged (the lib zero-central rule returns $(0,0,h)$).
  - `floor_dominance`: the lib's zero-low floor rule fired with no other cause. Expected on the USA unconventional rows of 1950–2005 (share low bound 0, central 0.005) and on the horizontal cuttings rows only if a future registry row has a zero low bound. Not a defect.
  - `clipped_difference`: a difference (§3.4) had a raw low or central below 0 and was clipped. **Expected on the rest-of-world rows of §6.1 and §6.4** (the `XWL` aggregate minus the sum of the listed countries has raw low below 0 in the years checked, e.g. gas 2010 raw low $-1.8\times10^{9}$ m³ against a central of $1.39\times10^{11}$ m³).
  - `exact_zero`: a difference whose raw central and raw high are exactly 0 (raw low $\ge0$).
  - `inherited_flag`: an input row was flagged and none of the above applies.
- A **structural zero** is not flagged: a joint-residue product whose D6 share is exactly 0 is written as `Bounds.exact(0.0)`, `below_detection = false`, no cause text, whatever the flag of the unallocated value (§4.3).
- If any **driver** activity row used for the value (the water volume, gas, oil, flared gas, ore tonnage or well count, and for a rest-of-world residual both the aggregate and the listed rows) has basis `interpolated` or `extrapolated`, the row's `notes` gain `; driver basis: interpolated` (or `extrapolated`, or both joined by `+`). The row's own `basis` stays `modelled`. Expected: horizontal-well rows 1980–1990 (`interpolated`), ore rows before 1972 and after the last measured year (`extrapolated`).
- **(Joint families only) allocation basis.** The `default`-variant rows of the joint families also carry `; allocation basis: <b>` where $b$ is the `+`-joined subset, in alphabetical order, of {`extrapolated`, `interpolated`, `modelled`} among the bases of the quantity and unit-value rows used for that geography-year's shares; omitted when the subset is empty. The bound variants do not carry it.
- **Suffix order:** rule text first, then `; driver basis: …`, then `; allocation basis: …`, then `; below_detection cause: …` last.

### 3.4 Arithmetic rules

- **Applying a factor.** `apply(driver, driver_unit, factor_row)` with `result_unit` and `master_unit` for the row unit. Factor units in this registry: `Bq/m3` (driver `m3`), `Bq/t` (driver `t`), `Bq/1` (driver `1`, well counts), `1` (shares). **A factor of unit `1`** is turned into `Bounds(low, central, high)` (the script first checks that the unit is exactly `1`, else raises `LibError`) and multiplied with `product`. A share with high $>1$ raises `LibError`.
- **Products** use `product`. A result with an exact-zero term is `Bounds.exact(0)`.
- **Complement** of a share row $(s_l,s_c,s_h)$: $\mathrm{Bounds}(1-s_h,\,1-s_c,\,1-s_l)$ (anti-correlated with $s$; used for the conventional fraction $1-u$ and the removed fraction $1-\varphi$). When the complement has central 0 the lib zero-central rule applies and the cause is `zero_central_factor` (none exists today).
- **Independent difference** (private helper, tested; COAL_SPEC §7): for $a-b$, central $c=c_a-c_b$; $\mathrm{low}=c-\sqrt{(c_a-l_a)^2+(h_b-c_b)^2}$, $\mathrm{high}=c+\sqrt{(h_a-c_a)^2+(c_b-l_b)^2}$; each bound clipped to $\ge0$; a negative central is set to 0 before the bounds are built and logged. A clipped low sets `nd_floored` (cause `clipped_difference`). **Used for** the rest-of-world residual of production, gas and oil (§6.1), of flaring (§6.4) and of the allocation quantities (§4.2), where the aggregate and the listed countries are separately compiled.
- **Correlated difference** (COAL_SPEC §12.1; private helper `_correlated_difference(a: Bounds, b: Bounds) -> Bounds`): central $c=c_a-c_b$, $\mathrm{low}=\min(l_a-l_b,\,c)$, $\mathrm{high}=\max(h_a-h_b,\,c)$, then clipped to $\ge0$; a negative central is set to 0 and logged; clipping sets `nd_floored`. **Used for** the rest-of-world produced-water volume $V_{\mathrm{XWL}}-V_{\mathrm{USA}}$ (§5.1): both come from one builder (`XWL` is modelled as `USA` plus the rest of the world before 2010, with the rule world $\ge$ USA at every bound), so the pair moves together. This departs from `factors_notes.md` §0, which says "independent difference, as coal"; see §11 Q7.
- **Sums.** The merge of the contributions that share one master key at the `production` stage (§5.5) uses **`sum_correlated`**: every contribution is proportional to the same water activity $A$, which is a deliberate conservatism (stated in §10). $\sum_c$ in a rest-of-world residual uses `sum_independent` over the listed countries.
- **Residual tolerance (new, D68 analogue).** A rest-of-world residual (aggregate minus the sum of listed rows) whose central magnitude is at most $10^{-5}$ of the aggregate central is treated as exactly 0: no rows, no `negative_residual` entry. This matters for `gas_flared_m3`, where the 2012–2025 `XWL` row equals the sum of the country rows to within $4\times10^{-6}$ (rounding) and seven years have a tiny negative raw residual.
- **Release cap (D54).** Each produced-water tier row $W_{g,t}$ of §5.3 is capped bound by bound at the water activity $A_g$ it splits: $\mathrm{Bounds}(\min(W.l,A.l),\min(W.c,A.c),\min(W.h,A.h))$, flag following `Bounds` rules; each bound the cap changes is logged (`cap_applied`, detail names the bound(s) `low`, `central` and/or `high`). With the registry as it stands the cap is not expected to fire.

### 3.5 Predecessor and successor states

None is needed. `SUN` oil and gas rows end in 1984 and `RUS`, `KAZ`, `AZE`, `TKM`, `UZB` start in 1985; `UKR` gas rows before 1985 are exact zeros and its oil rows start in 1992. A premise assertion (§9(i)) checks that no listed predecessor/successor pair has overlapping non-zero years. The 1985–91 shortfall (the other Soviet republics) falls into the rest-of-world residual.

### 3.6 Missing and ambiguous factors; the `LibError` rule (coal §12.6)

A failed `select` is "no factor" **only** when the `LibError` message starts with `no factor row`; the script then writes no row for that (family, group, tier, year, geography) and logs `no_factor`. Any other `LibError` (including `ambiguous factor rows`) propagates. A family with **no registry rows at all** is logged once as `no_family`. **Unlike the nuclear stream, every lookup of §5–§7 is mandatory for every year in which its driver has a value:** the registry windows tile the driver windows (checked: 1950–2025 for water and gas, 1900–2025 for gas and oil radon, 1949–2025 vertical wells, 1980–2025 horizontal wells, 1967–2025 oil sands). A `no factor row` for such a year is a registry error and propagates; `no_factor` entries therefore arise only in fixtures, and the committed log must contain none (§9(b)).

### 3.7 Duplicates and warnings (coal §12.5, §12.7)

- Two activity rows with the same (`series`, `country`, `year`) raise `LibError` naming the key. Nothing is silently first-wins.
- `build()` emits nothing on stderr. The lib's floor-dominance warnings are captured, counted and recorded as one log entry per build (`kind = lib_warning`, year and country empty, `detail` = the count and the message type).

### 3.8 Pre-1950

The script walks 1900–1949 through the same code path (the earliest activity year is 1900). Rows for 1900–1949 go to `data/streams_pre1950/oil_gas.csv`. In practice:

- **Written:** gas radon, NGL radon, vented gas radon, Pb-210 plate-out (§6.2) and oil radon (§6.3), 1900–1949, because `gas_production_m3` and `oil_production_t` start in 1900 and the factors are valid from 1900. These are single-driver families (product `gas`, `ngl` or `oil`, variant `default`, rule `none`).
- **Not written, logged as aggregated `no_driver` runs:** produced water and everything derived from it (the driver starts in 1950; so there is no pre-1950 scale or sludge, and the D31 opening stock omits oil and gas scale before 1950, gap G13 of the factor notes); flaring (the volume series starts in 1950, §6.4); oil sands (1967).
- **Not written, logged as `no_unit_value`:** vertical drilling cuttings for 1949 (`us_wells_drilled_vertical` has 1949, the factors are valid from 1949, but the D6 allocation needs unit values and `unit_value_*` starts in 1950; the script never assumes a price, LIB_SPEC §2.1). One entry per series, `detail` `1949-1949 (1 years)`.

The pre-1950 rows have `quantity = flow`, no `memo_*` tier and are produced by the same code as the post-1950 rows. Each passes `schema/master.json` with the `year` bounds relaxed (§9(h)).

### 3.9 `factor_ids` order

The order applied. Production and abandonment rows: concentration factor, share factor (unconventional share or its complement), tier-fate factor, then (for solids contributions) the solids-bound factor, the Pb-210 ratio where used, Φ where used, and the removed-solids or retained-scale fate factor; merged rows list the union in the order of the contributions of §5.5. Gas rows list the single factor. Drilling rows list the single cuttings factor. All nine rows (three products × three variants) of one joint key carry **identical** `factor_ids` and `source_ids`.

### 3.10 Family codes (start of every `notes` text)

`PW:` production-stage water, scale and sludge rows (§5); `AB:` abandonment rows (§7.1); `DR:` drilling (§7.2); `OS:` oil sands (§7.3); `GD:`, `GN:`, `GV:`, `GP:` delivered gas, NGL, vented gas, plate-out (§6.2); `OR:` oil radon (§6.3); `FL:` flaring (§6.4). Joint-family rows continue with `D6 <variant>, product <p>`. The rest-of-world fragments are exactly `rest of world (world aggregate minus listed countries)` (gas, oil, flaring residuals), `rest of world (world aggregate minus USA)` (water), and `world aggregate (no country split before 2012)` (flaring, 1950–2011). Tests check the prefix, the fragments and the suffix grammar, not the rest of the text.

---

## 4. Joint residues and the D6 allocation

### 4.1 Which rows are joint

D6 (METHODS §10.1) applies where one process yields several products. SCHEMA §5.5 requires `product` on every oil and gas row and says residues shared between products are split by value. This stream has two kinds of rows:

| Kind | Rows | Product | `allocation_variant` / `allocation_rule` |
|---|---|---|---|
| **Single-driver** | gas radon `GD` (`gas`), NGL radon `GN` (`ngl`), vented gas `GV` (`gas`), Pb-210 plate-out `GP` (`gas`), oil radon `OR` (`oil`), flaring `FL` (`oil`, see §11 Q2), oil sands `OS` (`bitumen`) | the product of the driver | `default` / `none` |
| **Joint** | everything at stages `production` (water, scale, sludge), `abandonment_scrap` and `drilling` | each of `oil`, `gas`, `ngl` | all three variants, §4.3 |

The single-driver rows are not split: their activity scales with the volume of one product by construction (a radon concentration per m³ of gas, per tonne of crude, per m³ flared, per tonne of ore). The produced water, the scale and sludge it forms, the retained scale and the cuttings are formed by the wells as a whole and cannot be traced to one product.

### 4.2 Quantities, unit values and geographies

Shares are computed from **central values only** (LIB_SPEC §2.2: shares are exact; their uncertainty is carried by the bound variants, METHODS §10.1) for the geography-year of the row being allocated:

- **`USA`**: quantities $q_p$ from `oil_production_m3`, `gas_production_m3`, `ngl_production_m3` of country `USA`; unit values $v_p$ from `unit_value_oil_usd_per_m3` and `unit_value_gas_usd_per_m3` of `USA` (an exact-country row beats `XWL`), and from `unit_value_ngl_usd_per_m3` of `XWL` (no `USA` row exists).
- **`XXX` (rest of world)**: $q_p=q_p^{\mathrm{XWL}}-q_p^{\mathrm{USA}}$ at central, $v_p$ from `XWL`. A residual $\le0$ at central for a product is set to 0 and logged `negative_residual` (none today: the smallest `ngl` difference is $2.5\times10^{6}$ m³ in 1950).

Value $q_pv_p$ is in USD (m³ × USD/m³; the `shares` function of LIB_SPEC §2.1 is unit-agnostic, although its text says t and USD/t). The mapping from the master variant to the `shares` token is `variant_token(allocation_variant, default_token="alloc:value")` (LIB_SPEC §7.3): `default` → `alloc:value`, `bound_main` → `alloc:main`, `bound_radio` → `alloc:radio`. The script uses `shares` and `split` from `pipeline.lib.allocation`. A product with $q>0$ and no unit value for the year raises `LibError` (never assume a price). The three series cover every year 1950–2025 for `XWL`, and the two oil and gas series also for `USA` (checked); the premise assertions of §9(i) repeat the check.

Indicative shares by value (author arithmetic from the files, central; **not test expectations**):

| Year | Geography | oil | gas | ngl |
|---|---|---|---|---|
| 1950 | `USA` / `XXX` | 0.874 / 0.977 | 0.099 / 0.020 | 0.027 / 0.004 |
| 1990 | `USA` / `XXX` | 0.597 / 0.812 | 0.338 / 0.168 | 0.065 / 0.021 |
| 2010 | `USA` / `XXX` | 0.552 / 0.804 | 0.352 / 0.166 | 0.096 / 0.030 |
| 2020 | `USA` / `XXX` | 0.632 / 0.809 | 0.261 / 0.162 | 0.107 / 0.029 |

The gas unit value for `XWL` is a US wellhead price used as a proxy (band 0.5–3 times), and the NGL value is 0.7 of the propane price; neither band enters the shares. Sensitivity (diagnostic): at the `XWL` gas unit-value low and high of 2010 the rest-of-world gas share is 0.091 and 0.374 (central 0.166). On an energy basis (`alloc:mass` on `oil_production_twh` and `gas_production_twh`, which have no NGL counterpart) the 2010 gas share would be 0.60 (`USA`) and 0.38 (`XXX`), against 0.35 and 0.17 by value. The choice of basis therefore matters; the METHODS default (value) is kept (§11 Q1).

### 4.3 The three variants and the rows they make

For every unallocated joint value $R$ (a `Bounds`, one per master key *without* product and variant, after the §5.5 merge) the script writes **nine rows**: for each product $p\in\{\texttt{oil},\texttt{gas},\texttt{ngl}\}$ and each variant:

| Variant | `allocation_rule` | Share of product $p$ |
|---|---|---|
| `default` | `alloc:value` | $q_pv_p/\sum q v$ |
| `bound_main` | `alloc:main` | 1 for the main product, 0 for the others |
| `bound_radio` | `alloc:radio` | 1 for the radio product, 0 for the others |

- Value $=$ `split(R, shares)[p]` for a positive share; a share of exactly 0 gives `Bounds.exact(0.0)`, `below_detection = false`, no cause text (a structural zero; X03 needs all three variants for every product key, so the zero rows are written).
- The `default` row's rule contains `alloc:value`; the bound rows carry their own token (SCHEMA X03, R02). The three products' values sum back to $R$ at low, central and high in each variant (the split is linear; §9(c) tests it).
- The nine rows share `factor_ids` and `source_ids` (§3.9). Their `notes` differ in the `D6 <variant>, product <p>` fragment.
- The row set is complete for every geography-year of every joint key; it is not conditional on whether a bound is "used" on the page.

### 4.4 The main product

$\mathrm{main}$ is the product with the **largest value $q_pv_p$** in the geography-year, ties broken in the order `oil`, `gas`, `ngl`. In every geography-year of the files it is `oil`. It is passed to `shares` as `main`.

### 4.5 The radioactivity-bearing product: options (Steve asked to see this; recommended default R1)

METHODS §10.1 defines Bound B as "all to the radioactivity-bearing product" (REE at Bayan Obo, uranium at Olympic Dam) and gives no definition for oil and gas wells. The registry notes (`factors_notes.md` §5 choice 13) propose "the product with the larger share of the mobilised radium in the joint residue (water-borne radium: oil and NGL by volume of water produced; gas Pb-210 films: gas)" and ask for Steve's decision. The options, in terms of what each needs from the unit-value, quantity and NGL series and what the toggle then shows:

| Option | Meaning | Data it needs | Available? | Consequence |
|---|---|---|---|---|
| **R1 (recommended)** liquids-carry-the-water | `radio` = `oil` in every geography-year. Produced water is co-produced chiefly with the liquid hydrocarbon (world ratio of water to crude about 3 m³ per m³; gas wells make roughly an order of magnitude less water per unit of product value), and the radium is in the water, so the residue follows the oil | none beyond the quantities and unit values already used for `main` | yes | `bound_radio` is **identical to `bound_main`** whenever `main` is `oil`, which is every year today. The toggle then shows `default` against "all to oil" only: oil-fired electricity gets 100 % of the joint residue, gas-fired and NGL get 0 %. Honest but uninformative as an upper bound for gas |
| **R2** gas-carries-the-radon | `radio` = `gas` | none | yes | The toggle brackets gas-fired electricity from above (0 % under main, 17–35 % by value, 100 % under radio) and oil-fired from below. Physically weak for water-borne radium: it charges gas with the radium of oil-field water |
| **R3** second-ranked by value | `radio` = the product with the second-largest value (the largest value among those other than `main`) | quantities and unit values | yes | Same result as R2 today (gas is second in every year, NGL third), but defined by a data rule so that B differs from A by construction. Flips to `ngl` if NGL ever outranks gas |
| **R4** water-volume weighted | each product's share of the *produced-water volume* it brings up (oil wells, gas wells, NGL-plant condensate), proportionally split (not all-or-nothing) | produced water by product (oil-well water, gas-well water), by country | **no** (not in the activity files; the US oil-well and gas-well split exists in the literature, ANL 2009, but not as a series) | The physically best rule. Cannot be built now; with R4 the variant would no longer be a bound but a second allocation. A new series would be a Phase 2 activity task |
| Alternative **default basis** (not an option for `radio`) | `alloc:mass` on energy (TWh) instead of `alloc:value` | `oil_production_twh`, `gas_production_twh` exist; **no NGL energy series** | partly | Moves the gas share to 38–60 % (§4.2); would need an NGL energy series or the NGL share folded into oil. Not recommended: the METHODS default is value |

**Recommended default: R1**, because it is the only option with a physical basis in the registry's own water chain, and because the unit-value and NGL series are not needed to define it. The cost is stated above: with R1 the two bounds coincide. If Steve wants the toggle to bracket gas-fired electricity from above, R3 (or R2) is the choice, and it is a one-function change: the script isolates the rule in a private helper `_radio_product(geography, year, quantities, values) -> str`; only that function and §4.4–§4.5 of this file differ. Under R1 the helper returns `oil`.

The premise assertion for tests (§9(i)): `main = oil` and `radio = oil` in every geography-year, and the `bound_main` and `bound_radio` rows of a key are equal (value, bounds, flags) except for `allocation_variant`, `allocation_rule` and the notes fragment. If a later change makes `main` differ, the tests recompute both from the files.

---

## 5. Stage `production`: produced water, scale and sludge (substreams `conventional` and `unconventional`)

All rows of this section are joint (§4). They are made for two geographies and for years 1950–2025.

### 5.1 Geographies and the water volume

- **`USA`**: $V_{\mathrm{USA},y}$ = `produced_water_m3`, country `USA`; select region `USA`.
- **Rest of world (`XXX`)**: $V_{\mathrm{ROW},y}$ = the correlated difference (§3.4) $V_{\mathrm{XWL},y}-V_{\mathrm{USA},y}$; select region `XWL`; notes fragment `rest of world (world aggregate minus USA)`. The premise (§9(i)): `XWL` $\ge$ `USA` at low, central and high in every year (checked: smallest central gap $3.05\times10^{8}$ m³ in 1950).
- A year with no value for the relevant series gives no rows and an aggregated `no_driver` entry.

### 5.2 Water-borne activity by substream

For geography $G$, year $y$ and each concentration group $g$ (the four groups `Ra226+`, `Ra228+`, `K40`, `Pb210+`):

$$u_{G,y}=\text{select }U,\qquad A^{\mathrm{conv}}_{g}=\mathrm{product}\big(V_G,\;1-u_{G,y},\;C^{\mathrm{conv}}_{g}\big),\qquad A^{\mathrm{unc}}_{g}=\mathrm{product}\big(V_G,\;u_{G,y},\;C^{\mathrm{unc}}_{g}\big)$$

with $C^{\mathrm{conv}}_g$ the C selection and $C^{\mathrm{unc}}_g$ the C′ selection (`apply(V, "m3", factor)` for the products with $V$; the unit-1 share is a separate `product` term). $A^{\mathrm{conv}}$ feeds substream `conventional` and $A^{\mathrm{unc}}$ substream `unconventional`: the two are **separate rows, never summed**. (This replaces the blended form $V[(1-u)C^{\mathrm{conv}}+uC^{\mathrm{unc}}]$ of `factors_notes.md` §0 by its two terms; the page sums them if it wants the blend. The totals are identical at the central values.) Concentrations are in Bq/m³ of outlet water after radium precipitation. The unconventional concentration rows have region `XWL` only, so the `USA` geography uses them by fallback.

### 5.3 Tier split of the water-borne activity (stage `production`)

For substream $s$, group $g$ and each of four tiers $t$, with $f_t$ the T selection for that tier:

$$W^{s}_{g,t}=\mathrm{cap}\big(\mathrm{product}(A^{s}_{g},\,f_t),\;A^{s}_{g}\big)$$

| Tier | Route | Residue type | Meaning (registry) |
|---|---|---|---|
| `reisolated` | — | `og_produced_water` | re-injected, disposed down-hole, used for EOR or commercially disposed (D17); permanent by construction |
| `impounded` | — | `og_sludge` | evaporation pits and ponds |
| `liberated` | `water_produced_discharge` | — | discharged to surface water or the sea |
| `dispersed` | — | `og_produced_water` | spread on roads or land |

The shares of one region and era sum to 1 at central within $10^{-3}$ (worst case $5\times10^{-4}$; premise, §9(i)): `USA` 1950–69, 1970–99, 2000–09, 2010–14, 2015–25 and `XWL` 1950–69, 1970–2025. The shares are the same for both substreams and for all four groups (including K-40 and Pb-210). Rest-of-world rows use the `XWL` shares; the USA is the only exact-region case. The cap is §3.4.

### 5.4 Solids: scale and sludge

For the groups with a solids-bound fraction ($g\in\{$`Ra226+`, `Ra228+`$\}$ from the Σ selection, residue $r\in\{$`og_scale`, `og_sludge`$\}$):

$$S^{s}_{g,r}=\mathrm{product}\big(A^{s}_{g},\;\sigma_{g,r}\big),\qquad S^{s}_{\mathrm{Pb210+},r}=\mathrm{product}\big(S^{s}_{\mathrm{Ra226+},r},\;\pi_{r}\big)$$

with $\sigma$ the Σ factor (`oil_gas:0047`–`0050`: the Ra-226 or Ra-228 activity in scale or sludge formed per unit of outlet-water activity, central 0.008 for scale and 0.012 for sludge, from a total solids fraction of 2 % with a scale share of 0.4) and $\pi_r$ the Π factor (`0051`, `0052`: reservoir-derived Pb-210 at formation, 0.05 of the Ra-226 head activity in the same solids; Pb-210 supported by radium decay inside the solids is the engine's ingrowth, not a row). **The solids are additive to the water, not subtracted from it** (registry decision; the fraction is relative to outlet water, post-precipitation). `K40` has no solids row. Th-228 and Po-210 in scale are engine ingrowth.

**Scale** is split into the part removed in operation and the part retained on equipment until retirement, with $\varphi$ the Φ selection (`oil_gas:0078`, central 0.9, 0.6–0.97; 96 % of scale volume sits in piping and tubing that stays until replacement, papers_round3 O4):

$$S^{s,\mathrm{ret}}_{g}=\mathrm{product}(S^{s}_{g,\mathrm{og\_scale}},\;\varphi),\qquad S^{s,\mathrm{rem}}_{g,\mathrm{og\_scale}}=\mathrm{product}\big(S^{s}_{g,\mathrm{og\_scale}},\;1-\varphi\big)$$

**Sludge** is assumed removed in operation entirely: $S^{s,\mathrm{rem}}_{g,\mathrm{og\_sludge}}=S^{s}_{g,\mathrm{og\_sludge}}$ (gap: sludge retained at decommissioning, G16).

**Removed solids** are booked at stage `production` in the creation year, split by tier with the R selection ($\rho_t^{r}$; eras 1950–84, 1985–99, 2000–25):

$$X^{s}_{g,r,t}=\mathrm{product}\big(S^{s,\mathrm{rem}}_{g,r},\;\rho^{r}_{t}\big),\qquad t\in\{\texttt{impounded},\texttt{dispersed},\texttt{liberated}\}$$

with residue type $r$ for the impounded and dispersed tiers, and route `water_produced_discharge` and no residue for the liberated tier (the registry residue on those rows is a key device).

**Retained scale** is booked at stage `abandonment_scrap` (§7.1) in the **same year** as it forms; its fate shares are the A selection by *creation year*: `impounded` with `og_scale` and `dispersed` with `og_scaled_scrap`, three eras (1950–64, 1965–79, 1980–2025) with the roughly 20-year retirement lag built into the era boundaries and **no decay survival factor** (decay of unmoved activity is the engine's job; a second factor would double count it).

### 5.5 Master rows at `production` and the merge

The contributions of §5.3 and §5.4 land on only seven master keys (tier, route, residue). Several contributions share one key, so **they are merged before writing** (a duplicate key would be `X01`):

| Tier | Route | `residue_type` | Groups | Contributions (summed with `sum_correlated`, in this order) |
|---|---|---|---|---|
| `reisolated` | — | `og_produced_water` | the four water groups | $W_{\mathrm{reisolated}}$ |
| `impounded` | — | `og_sludge` | four water groups; solids groups `Ra226+`, `Ra228+`, `Pb210+` also receive solids | $W_{\mathrm{impounded}}$ (evaporation pits), then $X_{g,\mathrm{og\_sludge},\mathrm{impounded}}$ (removed sludge) |
| `impounded` | — | `og_scale` | `Ra226+`, `Ra228+`, `Pb210+` | $X_{g,\mathrm{og\_scale},\mathrm{impounded}}$ |
| `dispersed` | — | `og_produced_water` | the four water groups | $W_{\mathrm{dispersed}}$ |
| `dispersed` | — | `og_scale` | `Ra226+`, `Ra228+`, `Pb210+` | $X_{g,\mathrm{og\_scale},\mathrm{dispersed}}$ |
| `dispersed` | — | `og_sludge` | `Ra226+`, `Ra228+`, `Pb210+` | $X_{g,\mathrm{og\_sludge},\mathrm{dispersed}}$ |
| `liberated` | `water_produced_discharge` | — | four water groups; solids groups also receive solids | $W_{\mathrm{liberated}}$, then $X_{g,\mathrm{og\_scale},\mathrm{liberated}}$, then $X_{g,\mathrm{og\_sludge},\mathrm{liberated}}$ |

The `Pb210+` rows therefore combine water-borne Pb-210 (concentration row) and solids-bound Pb-210 (ratio row). Rows exist for each substream. The merged value is the unallocated $R$ of §4.3, and each merged key is written as nine rows. Because the merge hides the solids inside the impounded-sludge and liberated rows, tests recompute the components from the files (§9(c), §9(e)).

---

## 6. Stage `processing_transport` and flaring (single-driver rows)

### 6.1 Countries and the rest of world

For each production-driven family below, rows are written for every listed country $c$ (every country in the driver series except `XWL`) and each year with a non-zero driver. The rest-of-world residual is the independent difference (§3.4) $P_{\mathrm{XWL},y}-\sum_cP_{c,y}$ (`sum_independent` over the listed countries), written for country `XXX` with the notes fragment `rest of world (world aggregate minus listed countries)` and the `XWL` factor. A residual central $<0$ becomes 0 and is logged `negative_residual` (magnitude in the detail); a residual of magnitude $\le10^{-5}$ of the aggregate is 0 (§3.4); an exactly zero residual gives no rows. In the oil and gas files the residual is 2–7 % of the world (gas 2010: $1.39\times10^{11}$ m³ of $3.22\times10^{12}$ m³) and its raw low bound is negative in the years checked, so the `XXX` rows are expected to carry `below_detection = true` with cause `clipped_difference`. The factor region is the country code, so an exact country row would beat `XWL`; none exists today (premise, §9(i)).

### 6.2 Gas system: rows `GD`, `GN`, `GV`, `GP` (driver `gas_production_m3`, product as shown)

All four are single-driver rows with variant `default`, rule `none`, substream `conventional` (§11 Q3), stage `processing_transport`.

| Code | Group | Tier | Route | Residue | Product | Select | Factor unit |
|---|---|---|---|---|---|---|---|
| `GD` | `Rn222+` | `liberated` | `air_delivered_gas` | — | `gas` | GD | `Bq/m3` |
| `GN` | `Rn222+` | `liberated` | `air_delivered_gas` | — | `ngl` | GN | `Bq/m3` |
| `GV` | `Rn222+` | `liberated` | `air_vented_gas` | — | `gas` | GV | `Bq/m3` |
| `GP` | `Pb210+` | `impounded` | — | `og_processing_residue` | `gas` | GP | `Bq/m3` |

Value $=\texttt{apply}(P^{\mathrm{gas}}_{c,y},\ \texttt{"m3"},\ \text{row})$, unit `Bq/a`.

**Radon in delivered gas versus the NGL row: what is and is not a double count.**

- **Different atoms, different keys.** `GD` (`oil_gas:0074`, central 300 Bq/m³) is the Rn-222 that stays in the *sales gas* and reaches burners; `GN` (`0110`, central 200 Bq/m³) is the Rn-222 diverted with the *natural gas liquids and LPG* at gas plants and released at their handling and end use (wellhead 800 Bq/m³ × diverted fraction 0.5 × survival 0.5). They are additive in the registry (the NGL row "raises total radon at burners by about 67 %") and the master rows are kept apart by `product` (`gas` against `ngl`), so there is no key clash and no duplicate: the unique key differs although route, group, tier and country are equal.
- **Both are per m³ of gas produced, not per m³ of NGL.** No NGL volume series is used for rows (the `ngl_production_m3` series is used for the D6 shares only), so the two rows cannot both be driven by the NGL volume.
- **What the script must not do:** apply `GN` to `GD`'s output, scale `GD` down by the diverted fraction, or add an NGL row for the Pb-210 plate-out.
- **A known closure limit (not fixed here).** The wellhead budget of 800 Bq/m³ is exceeded: delivered 300 + NGL 200 + vented 16 = 516 Bq/m³ (central) leave the system as Rn-222, while the Pb-210 plate-out row (`0076`, central 0.189 Bq/m³ head Pb-210) assumes a decayed share $(1-r)=0.625$, i.e. 500 Bq/m³ of the wellhead decaying inside the system. 300 + 500 already uses the whole wellhead, so the NGL and vented radon are not subtracted from the in-system decay and the budget closes at 127 %. If they were, the Pb-210 row would be about 0.107 instead of 0.189 Bq/m³ (a factor 1.8, inside its 0.019–0.356 band). The registry is unchanged; this is recorded in §10 and in §11 Q4.
- **Gas power uses sales gas.** The §9(e) gas benchmark uses `GD` rows only; `GN` goes to LPG users, not to gas-fired generation.

### 6.3 Oil radon: row `OR` (driver `oil_production_t`)

Stage `processing_transport`, product `oil`, group `Rn222+`, tier `liberated`, route `air_stack`, select OR (`oil_gas:0077`, 1,000 Bq/t central: 1 Bq/kg Ra-226 in crude in equilibrium, all crude treated as processed). Value $\texttt{apply}(P^{\mathrm{oil}}_{c,y},\texttt{"t"},\text{row})$, countries and rest of world as §6.1. Refinery sludge, Pb-210 fouling of fractionation units and refinery residues have no rows (gap G3, choice 14).

### 6.4 Flaring: row `FL` (driver `gas_flared_m3`; recommended option, needs registry item R1 of §12)

Flaring has no stage of its own in the vocabulary; it is booked at stage **`production`**, route `air_stack`, group `Rn222+`, tier `liberated`, product `oil` (flared gas is predominantly associated gas from oil wells; §11 Q2), substream `conventional`. The factor is the wellhead Rn-222 concentration per m³ flared (the registry row to be added, §12 R1, proposed 150 / 800 / 1,400 Bq/m³, the same wellhead parameter as in `oil_gas:0071`–`0073`; radon is not destroyed in the flame). Value $\texttt{apply}(F_{c,y},\texttt{"m3"},\text{row})$.

**How the series is used.**

- **1950–2011:** only the `XWL` row exists (the World Bank GGFR satellite record is not available before 1994 and the 2012–2025 release starts in 2012; the world values are back-cast from Global Carbon Project flaring CO₂ × 388 m³ per t CO₂, the 2012–2023 mean ratio, basis `modelled`, band +30 % from 1994 and +40 % before, assumed). It is written as country **`XXX`**, notes fragment `world aggregate (no country split before 2012)`. No country split is made before 2012: the EIA-reported country breakdown (`gas_flared_reported_m3`) is a different basis (national reports include venting and differ from the satellite estimates by factors 0.2–3 in 2012–15) and is **not** used to apportion the back-cast.
- **2012–2025:** the country rows (GGFR satellite, 103–104 countries, basis `compiled`) give one row per country with a non-zero value, and the rest-of-world residual `XWL` minus $\sum_c$ is the independent difference of §3.4 with the $10^{-5}$ tolerance (so, in practice, no `XXX` rows in these years).
- **Rule.** For a year, if `gas_flared_m3` has at least one non-`XWL` country row, use the country rows and the residual; otherwise use the `XWL` row as `XXX`. Never both (that would count the world twice).
- **Pre-1950:** no flared-volume series, so no flaring rows (logged `no_driver`).
- **The legacy per-tonne rows `oil_gas:0071`–`0073`** (driver `oil_production_t`, "a workaround for the missing flared-gas driver", blocker B3 now closed) are **not read** by the script. If they are still present when the new row exists, a premise assertion (§9(i)) records it and a test checks that no output row cites `0071`, `0072` or `0073` in `factor_ids`; the registry owner may delete or close them (§12 R2). The two approaches agree to 4 % at 2010 (stream 106 TBq against 111 TBq for the per-tonne form), so the choice affects the country detail and the traceability rather than the total.
- The wellhead radon, not the vented fugitive 2 % (`GV`), applies to flared gas; flared gas is not in `gas_production_m3` (dry marketed gas), so `FL` does not double count `GD`, `GN` or `GV`.

---

## 7. Stages `abandonment_scrap`, `drilling`, `oil_sands_mining`

### 7.1 `abandonment_scrap` (joint; retained scale, substreams `conventional`, `unconventional`)

Rows from the retained-scale contribution of §5.4, same geographies (`USA`, `XXX`) and years 1950–2025, booked in the creation year:

| Tier | Route | `residue_type` | Groups | Value |
|---|---|---|---|---|
| `impounded` | — | `og_scale` | `Ra226+`, `Ra228+`, `Pb210+` | $\mathrm{product}(S^{s,\mathrm{ret}}_g,\ a^{\mathrm{imp}})$ with $a$ the A selection |
| `dispersed` | — | `og_scaled_scrap` | same | $\mathrm{product}(S^{s,\mathrm{ret}}_g,\ a^{\mathrm{disp}})$ |

No liberated tier (cutting and descaling dust: gap). Each is a joint key, written as nine rows (§4.3). The two fate shares of one creation era sum to 1 at central (premise; 1950–64: 0.15 + 0.85, 1965–79: 0.5 + 0.5, 1980–2025: 0.85 + 0.15).

**What the registry encodes about φ and timing (item for the benchmark reader).** $\varphi=0.9$ (0.6–0.97) is the share of newly formed scale that stays on tubulars and equipment until retirement; it is booked at `abandonment_scrap` in the *creation* year, not the retirement year. The roughly 20-year retirement lag (10–35) is built into the era boundaries of the fate shares, so scale created in 1950–64 is assumed to retire in about 1970–84, when scrap was sold on with little control (0.85 dispersed), and scale created from 1980 retires after 2000 under controlled disposal (0.85 impounded). Consequences: the tier assignment is anticipatory by about 20 years; decay is applied from the booking year, which is physically right for unmoved activity; the Ra-228 and Pb-210 content therefore decays on the tier it will end up in rather than in an unbooked "on equipment" state; and the tonnage of retired scrap is not modelled (gap G10).

### 7.2 `drilling` (joint; USA only)

Stage `drilling`, tier `impounded`, residue `og_drill_cuttings` (the stage allows no other tier), group set the 11 groups of the registry (`U238+`, `U234`, `Th230`, `U235+`, `Ra226+`, `Pb210+`, `Po210`, `Th232`, `Ra228+`, `Th228+`, `K40`), country **`USA`** only.

| Substream | Driver | Select | Years | Factor unit |
|---|---|---|---|---|
| `conventional` (vertical wells) | `us_wells_drilled_vertical` (1949–2025) | DV (`0088`–`0098`) | 1950–2025 (1949 in the pre-1950 file is dropped, §3.8) | `Bq/1` |
| `unconventional` (horizontal wells) | `us_wells_drilled_horizontal` (1980–2025) | DH (`0099`–`0109`) | 1980–2025 | `Bq/1` |

Value $\texttt{apply}(N_{y},\texttt{"1"},\text{row})$. The per-well factors are cuttings mass per well (vertical 100 / 250 / 450 t, horizontal 330 / 600 / 1,000 t) times a Pennsylvania DEP TENORM concentration; none divides a total by a well count (D66), so replacing `us_wells_drilled_total` by the split series changes how many wells the factors multiply, not the factors. In 2010 the 36,611 wells of the retired total include 5,953 that the split series (20,478 vertical + 10,180 horizontal) does not count; those carry no cuttings. **There are no world rows**: the registry is US only (region `USA`), the world has no well-count series (gap G7), and the script runs the family for `USA` only; it does not fall back to `XWL` for another country and a non-US country-year gives neither a row nor a log entry. Horizontal wells of 1980–2004 take the 2–3 km lateral cuttings mass, probably an overstatement for short laterals (D66 note). Joint keys: nine rows each (§4.3), shares from the `USA` geography.

### 7.3 `oil_sands_mining` (single driver; Canada, substream `oil_sands`)

Stage `oil_sands_mining`, product **`bitumen`**, variant `default`, rule `none` (one product). Groups `Th232`, `Ra228+`, `Th228+` (equal head activity: secular equilibrium in monazite), tier `impounded`, residue `oil_sands_tailings`, country **`CAN`** only, years 1967–2025. Value $\texttt{apply}(O_{y},\texttt{"t"},\text{row})$ with $O$ = `oil_sands_ore_processed_t` (mined ore processed, t) and unit `Bq/t`. **The registry rows `0085`–`0087` still have an empty `driver_series`** (the series did not exist when they were written). The script uses `oil_sands_ore_processed_t` whatever the cell says; if a registry row names a non-empty `driver_series` that differs, the script raises `LibError` ("driver mismatch"). `select` is called without a `driver_series` key. Only the monazite thorium chain is carried: the sand, clay and coke background (K-40, U, Th) is left out (choice 9; placeholders would add hundreds of TBq of K-40), there is no `oil_sands_coke` row, and the overburden memo series is a gap (G15). The memo tier `memo_earth_moved` is therefore **not used by this stream**: no row has a `memo_*` tier. Canadian crude (including oil sands output) also remains in `oil_production_t`, so the produced-water, flaring and oil-radon rows apply to oil sands volumes as if conventional (§10).

### 7.4 Residue types the stream uses, and the engine parameters they need (item for Phase 3, not for the script)

The engine applies $\varepsilon$ (Rn-222 and Rn-220) to impounded and dispersed residues and seepage to impounded residues; `reisolated` rows need neither (permanent by construction). The state of `data/reference/residue_types.csv` for the types this stream uses:

| Residue type | Tiers used | $\varepsilon$ needed | Seepage needed | State in the file |
|---|---|---|---|---|
| `og_produced_water` | `reisolated`, `dispersed` | dispersed only | no | $\varepsilon_{222}$ 0.1/0.2/0.3 and $\varepsilon_{220}$ 0 filled; seepage empty (not needed) |
| `og_sludge` | `impounded`, `dispersed` | yes | impounded | seepage filled; **$\varepsilon$ empty** |
| `og_scale` | `impounded` | yes | yes | seepage filled; **$\varepsilon$ empty** |
| `og_scaled_scrap` | `dispersed` | yes | no | $\varepsilon$ and seepage filled (as `og_scale`) |
| `og_drill_cuttings` | `impounded` | yes | yes | all filled |
| `og_processing_residue` | `impounded` | the Rn parent is absent (Pb-210 films) | yes | seepage filled; **$\varepsilon$ empty** (D62 "left empty") |
| `oil_sands_tailings` | `impounded` | yes | yes | all filled (the Rn-220 triple uses H 4–15 m, D64) |
| `oil_sands_coke` | none | — | — | no rows, empty |

The pipeline refuses to run on an empty parameter set for a residue type that has data rows (SCHEMA §4.10). Three types therefore block the engine: see §11 Q6. Counted versus memo: every residue of this stream is a processing residue counted in the tiers (D21); there are no memo rows and no above-threshold waste rock.

---

## 8. Log

`BuildResult.log` is a list of dicts with keys `kind`, `year`, `country`, `group` (may be empty) and `detail`. Kinds:

| Kind | When |
|---|---|
| `no_factor` | a `select` failed with `no factor row` (§3.6). Aggregated: one entry per contiguous year run per (family, country, group, tier); `year` = first year, `detail` = `first-last (n years)`. None is expected in the committed build |
| `no_driver` | a driver series (or the relevant country row) has no value for a year, including the whole run when a series is absent from the files. Aggregated as `no_factor`, per (series, country). Expected today for the pre-1950 walk (produced water, flaring, oil sands, horizontal wells) and for a missing series in a fixture. Not written for a country with no row in a country-level series |
| `no_unit_value` | a joint residue needs the D6 shares and a product with $q>0$ has no unit value for the year (today the 1949 vertical-well rows). Aggregated per series |
| `no_family` | a family has no registry rows at all; once per build |
| `negative_residual` | a rest-of-world residual or a §4.2 quantity difference had a negative central; one entry per year and series |
| `cap_applied` | the D54 cap changed a bound of a water tier row; one entry per (year, geography, substream, group, tier); `detail` names the bound(s) |
| `lib_warning` | §3.7; one per build |

Aggregated entries carry the output-row country convention (`XXX` for world series, otherwise the country code). The CLI prints counts by kind and, with `--write`, writes the full log to `research/oil_gas/build_log.csv`. A **run** of `no_factor`/`no_driver` covers consecutive years in which the condition holds; a year in which the driver is exactly `0/0/0` (no rows, no log) ends the run (NUCLEAR_SPEC §13 item 7).

---

## 9. Done conditions and tests

Tests read factor and activity values from the files (never hard-coded), with explicit **premise assertions** (§9(i)) so that a changed registry fails loudly instead of passing silently.

- **(a) Schema.** `data/streams/oil_gas.csv` passes `python -m pipeline.validate --root .`. In particular: `product` present and in {`oil`, `gas`, `ngl`, `bitumen`} on every row (V11); tier allowed for the stage (V03); `residue_type` present exactly for `impounded`, `reisolated`, `dispersed` and absent for `liberated`, `route` present exactly for `liberated` (R02); no routine-transfer stage and no `transfer_*` row (V15, X02, X05 not triggered); no accident route; `Rn222+` only as a liberated `flow` (V09); allocation completeness (X03): for every key without variant that has a non-default row, all three variants exist and the `default` rule contains `alloc:value`; `bound_main` rows carry `alloc:main` and `bound_radio` rows `alloc:radio` (R02); no duplicate key (X01), which the §5.5 merge exists to prevent; `factor_ids` present (modelled rows) and resolvable (V13); all `source_ids` resolve (V07); residue types resolve (V12).
- **(b) Candidate nuclides and coverage** (METHODS §4.3 ①). For each family in §5–§7 and each year with a driver value and a registry row valid in that year, a row exists for every (group, tier, route, residue, substream) of the family, and for the joint families for every product and variant (nine rows per key). The test enumerates the registry. The committed log contains **no** `no_factor` entry. METHODS §4.3 lists for ③: `Ra226+`, `Ra228+`, `Th228+`, `Pb210+`, `Po210`, `Rn222+`, `K40`. `Ra226+`, `Ra228+`, `Pb210+`, `K40` and `Rn222+` each appear in some 2010 production or processing flow row; **`Th228+` and `Po210` appear only in drilling cuttings (and `Th228+` in oil sands tailings)**: at `production` and `processing_transport` they are engine ingrowth from `Ra228+` and `Pb210+` and the registry has no rows for them. This is reported, not failed (§10). Coverage by geography: `USA` and `XXX` rows for every water, solids and abandonment key 1950–2025; `USA` rows only for drilling; `CAN` only for oil sands.
- **(c) Conservation.**
  1. *Water tier split.* For each geography, substream, group and year, the four water tier rows (recomputed before the merge) sum at central to $A^s_g$ within $10^{-3}$ relative (the share premise), and no tier value exceeds $A$ at any bound.
  2. *Solids.* For each geography, substream and year: removed scale (impounded + dispersed + liberated contributions) $=S^{\mathrm{rem}}$ and the abandonment rows (impounded + dispersed) $=S^{\mathrm{ret}}$, each within $10^{-3}$ at central; $S^{\mathrm{rem}}+S^{\mathrm{ret}}=S_{g,\mathrm{og\_scale}}$ (to $10^{-9}$ relative, exact complement at central); removed sludge tiers sum to $S_{g,\mathrm{og\_sludge}}$; Pb-210 solids $=\pi\times$ Ra-226 solids per residue (central, $10^{-9}$).
  3. *Merge.* Each merged production row equals the `sum_correlated` of its recomputed contributions (§5.5), and its `factor_ids` is their union.
  4. *Allocation.* For every joint key and variant, the three product rows sum to the unallocated value at low, central and high (relative $10^{-5}$); `default` shares equal $q_pv_p/\sum qv$ recomputed from the files; `bound_main` has exactly one non-zero product (the argmax value, ties `oil`, `gas`, `ngl`); `bound_radio` has exactly one non-zero product (§4.5); structural-zero rows have `below_detection = false`.
  5. *Rest of world.* For `gas_production_m3` and `oil_production_t`, $\sum_c\text{rows}+\text{rest-of-world row}$ at central equals $P_{\mathrm{XWL}}\times$ factor for `GD`, `GV`, `GP`, `OR` (relative $10^{-6}$); the same for flaring (country rows plus residual, or the `XWL` row).
  6. *No double counting.* Unique keys (including the `GD`/`GN` pair that differs only by product); `GN` is driven by `gas_production_m3`, not `ngl_production_m3`; the output has no row at routes other than the registry's, none for exhalation or seepage (METHODS §5.2), no `memo_*` tier and no `transfer_*` or `opening_stock` row; no output row cites `oil_gas:0071`–`0073` (§6.4); `FL` is written from exactly one source per year (country rows or `XWL`, never both).
- **(d) Determinism.** Two builds write byte-identical files (all three); row order is the SCHEMA key order; the log order is stable.
- **(e) Benchmarks (D51).** Two years, **2010 and 2020**. Quantities are summed from output rows (central, Bq) unless stated, and a value passes when $\tfrac13\le x/x_{\mathrm{ref}}\le3$. The Annex B values are read from `research/unscear_extraction.csv`; the independence of every estimate from UNSCEAR 2016 Annex B (S0001) is stated.

  **Gas radon per GW·a of gas-fired electricity (B1).** $x_{\mathrm{gas}}=\sum_c\texttt{GD}_{c,y}\times\texttt{gas\_power\_share}_{\mathrm{XWL},y}\big/\big(\texttt{elec\_gen\_gas}_{\mathrm{XWL},y}/8.766\big)$, in TBq per GW·a, **product `gas` rows only** (the `GN` NGL rows go to LPG users, not to gas-fired generation; see §11 Q4).

  | Estimate | Value (TBq/GW·a) | Source | Independent of Annex B 2016? | Status |
  |---|---|---|---|---|
  | Annex B 2016, first estimate | 0.75 | S0001, U0240 (0.286 m³/kWh × 300 Bq/m³) | — | Stream 0.750 (2010), 0.727 (2020): ratio 1.00 and 0.97. **Near-circular in value** (same 300 Bq/m³ centre); independent in method (activity-spine gas volume and power share against UNSCEAR's per-kWh gas use) |
  | Johnson 1973, direct burner measurements, consumption-weighted | 1.38 (range 1.03–2.16; 550, 410–860 Bq/m³) | papers_round3 §3.4 (EPA-520/1-73-004 read via secondaries) | **Partly**: independent measurements, but the same 1970s US data root as UNSCEAR | Stream/ref 0.54. Required: stream within ×3 of at least one of the three values in this block |
  | Bottom-up chain (wellhead × Gesell retention × transit decay) | 0.42 (168 Bq/m³) | papers_round3 §5.1 | Partly (wellhead from Johnson) | Ratio 1.8 |
  | Dixon 2001 (UK-use study, about 200 Bq/m³) | 0.50 | papers_round2 G-6 (abstract only) | **Yes** | Ratio 1.5 |
  | Gesell 1975, sales gas, nine plants | 0.05–8.7 (18.5–3,460 Bq/m³) | papers_round2 G-6 | Yes | Range test only: stream inside the range |

  Conversion of an independent concentration $c$ (Bq/m³) to TBq per GW·a: $0.2507\times c/100$ (the round-2 convention, 0.286 m³ of gas per kWh of electricity; the stream's own implied intensity is 0.285 m³/kWh). The "0.3–0.5 TBq/GW·a" band of `factors_notes.md` §2 (UK-type 170 Bq/m³ and the round-2 chain 125 Bq/m³) rests on **unverified** UK and Netherlands values that round 2 itself says "do not use" (Dixon is the nearest); it is reported, not tested, and the stream sits at 1.5–2.5 times its top. The round-3 reading (0.6–2.2 for Johnson direct and bottom-up) is the one the pass rule uses. **Known limit, not a miss:** including the NGL rows the same quantity would be 1.25 and 1.21 TBq/GW·a (2.5 times Dixon and 3.0 times the bottom-up value); the test is not run on that value.

  **Oil radon per GW·a of oil-fired electricity (B2).** $x_{\mathrm{oil}}=\sum\texttt{OR}\times\texttt{oil\_power\_share}_{\mathrm{XWL},y}\big/\big(\texttt{elec\_gen\_oil}_{\mathrm{XWL},y}/8.766\big)$, `OR` rows only (not flaring). Stream 0.00243 (2010) and 0.00262 (2020). Annex B 2016: **0.002** (S0001, U0241; 0.278 L/kWh × 0.95 kg/L × 1 Bq/kg). Independent: Bell et al. mean 0.7 Bq/kg → **0.0017** (weakly independent: same Ra-226 order of magnitude, read through UNSCEAR and secondary papers). Required: within ×3 of each.

  **US scale and sludge radium, about 1990 (B3).** Recomputed from the files: $V_{\mathrm{USA},1990}\times[(1-u)C^{\mathrm{conv}}+uC^{\mathrm{unc}}]\times(\sigma_{\mathrm{scale}}+\sigma_{\mathrm{sludge}})$ for Ra-226 and Ra-228 (the identity of §9(c)2 ties it to the rows). Stream (author arithmetic): Ra-226 0.48, Ra-228 0.79, total 1.27 TBq/a (2 % of 63.4 TBq of outlet-water radium). References: EPA 1991 draft (8.3 Mt per 20 years at 5.74 and 2.04 Bq/g): Ra-226 2.38, Ra-228 0.84, total **3.22** TBq/a (S1250); EPA 1993 via OGJ: total **1.07** TBq/a (S1209; the concentrations 17.76 and 2.775 Bq/g are unverified, the primary report EPA 402-R-93-083 was not obtained, S1263). Total within ×3 of at least one: ratios 0.39 and 1.19. **Independence:** independent of Annex B (it has no solids quantity), but **not independent of the registry's own fraction**, which was set at 2 % from these two anchors (D65): a consistency check, not an independent test.

  **Produced-water radium, factor level (B4).** The rest-of-world effective Ra-226 concentration (total rest-of-world water-borne Ra-226 divided by $V_{\mathrm{ROW}}$) lies between **3.5 Bq/L** (Norway: 451 GBq of Ra-226 in 129 Mm³, 2011, S0308) and **10 Bq/L** (RP 135 reference, S0204): stream about 5.1 Bq/L in 2010 and 5.3 Bq/L in 2020. Independent of Annex B. Range test (required). Regional lower bound: the stream's rest-of-world liberated Ra-226 (the `liberated` water row, `Ra226+`, summed over substreams and products at central, 2010: about 12.6 TBq/a) must be at least the OSPAR offshore north-east Atlantic figure of **0.73–1.1 TBq/a** (S0307) and at most 100 times it (the 100 is the spec author's deliberately wide tolerance: the OSPAR area is a small fraction of world offshore production). Independent of Annex B. The `liberated` water row also contains the liberated solids (§5.5); the test recomputes the water term from the files.

  **Flared gas volume (B5).** The flaring rows divided by the flaring factor equal `gas_flared_m3` (identity, relative $10^{-6}$). The series itself: 132.3 bcm (2010; 4.67 trillion ft³) against 134 bcm (World Bank press release for 2010, quoted in the activity note; independent of the construction) and against the EIA-reported 128.8 bcm (`gas_flared_reported_m3`, a national-submission basis, includes venting): both within ×1.1. For 2020 only the GGFR value exists (149.5 bcm; 139 bcm for 2022 and 148 bcm for 2023 in the GGFR report, S1204). Independent of Annex B. The Annex B tables carry no flaring quantity.

  **Oil sands (B6, consistency).** 2024: $1{,}019$ Mt of ore × the Th-232 factor $=5.8$ TBq/a, inside the AER-based range of 2.2–20.6 TBq/a (the two readings of the monazite mass: 7.6–25 kt/a as heavy-mineral fraction, or 43.6–72.5 kt/a on the whole tailings, × 7 % Th × 4.06 kBq/g). The factor was derived from these inputs, so this is a consistency check, not an independent test.

  **Drilling (B7, consistency).** US 2010 cuttings Ra-226 $\approx0.53+1.18=1.7$ TBq/a (vertical 20,478 wells, horizontal 10,180 wells) against $\approx20$ TBq/a of Ra-226 in US produced water (`USA` 2010 water-borne Ra-226 19.6 TBq): ratio about 0.09. The factor note quotes 1.4 TBq/a from the retired total well count; the figure now follows the split series. No pass/fail.

  **Known misses and unresolved conflicts (documented, not tests).**
  1. *Ra-228 : Ra-226 in US solids.* The stream's solids carry the water ratio (about 1.67 for `USA`, 0.8 for `XWL`); EPA's 1991 solids ratio is 0.35 (55 / 155 pCi/g). The stream is about 4.8 times EPA, outside ×3 (papers_round3 O3, no change proposed because the EPA ratio is an assumption, not an assay).
  2. *B1 including NGL* (above).
  3. *Gas radon in 1900–1949 and flaring before 1994* have no independent data.
  4. *Solids mass.* EPA's 25,000 t/a of scale and IAEA TRS-419's 100 t per NORM well per year conflict by orders of magnitude; no solids tonnage is used, only activity fractions; no truly independent solids benchmark exists.
- **(f) Hand-computed cases.** At least fourteen rows of one year (2010, plus the cases that need another year) recomputed independently from the factor and activity values, including: a `USA` 2010 conventional `Ra226+` water row in the `liberated` tier before the merge ($V\times(1-u)\times C\times f$); the same group's merged `liberated` row with the removed-scale and removed-sludge contributions; the merged `impounded`/`og_sludge` row (pit water plus removed sludge); a rest-of-world 2010 unconventional `Ra228+` row; a rest-of-world unconventional row in 1960 (share central 0, flagged `zero_central_factor`); a `USA` unconventional row in 1960 (share low 0, flagged `floor_dominance`); a `Pb210+` solids row (0.05 of the Ra-226 solids); an `abandonment_scrap` retained-scale row for 1970 (creation era 1965–79) and one for 1955 and 1990; the nine allocation rows of one joint key (all three variants, three products, with the zero rows) for `USA` 2010 and for `XXX` 2010; a `GD` row for `USA` 2010 and the `GN` row for the same country-year (product `ngl`); a `GV` and a `GP` row; the rest-of-world `GD` row (`clipped_difference`, notes fragment); an `OR` row; the `FL` rows in 2011 (`XXX`, world aggregate) and 2012 (a country row, e.g. `RUS`); a vertical and a horizontal `U238+` drilling row for 2010 with the same allocation shares; an oil sands row for 2024; a pre-1950 `GD` row for 1930; a 1949 drilling omission with its `no_unit_value` entry.
- **(g) Fixture tests** on a miniature tree in `tmp_path` that copies the full real factor file and shrinks only the activity files: the negative-residual rule (production and the §4.2 quantity difference); the $10^{-5}$ residual tolerance for flaring; the zero-residual case giving no rows; a missing driver year (aggregated `no_driver` run); a missing unit value raising `LibError` (and 1949 logging `no_unit_value`); duplicate activity rows (also across the two files) raise `LibError`; an ambiguous factor (duplicated registry row) propagates; a registry-window gap logs `no_factor` (the only way it can appear); a share with high above 1 raises; a factor of unit `1` with another unit raises; a driver-series mismatch on `0085`–`0087` raises; flaring with both country rows and an `XWL` row writes the country rows and the residual only; flaring in a year with only the `XWL` row writes `XXX`; the D54 cap logs `cap_applied` when forced; an absent series gives one aggregated `no_driver` and no exception; the correlated-difference helper (clipped low sets the flag); `bound_radio` under R1 equals `bound_main`; a fixture where `main` is `gas` (changed unit values) produces the argmax and still three variants; an absent country row gives silence; the merge yields one row for a colliding key (no `X01`).
- **(h) Pre-1950 file.** Rows only for years 1900–1949, `quantity = flow`, no `memo_*` tier, each passing `schema/master.json` with the `year` bounds relaxed; produced by the same code path; only the single-driver gas and oil families of §6.2 and §6.3 are present (`GD`, `GN`, `GV`, `GP`, `OR`), with values equal driver × factor recomputed from the files; no joint-family row and no flaring row exists in it.
- **(i) Premise assertions.** Before comparing any value, tests assert the registry and activity premises they use, with a message naming the changed premise. For example: the factor file has `stage`, `substream` columns and the ids `oil_gas:0001`–`0110` (plus the §12 additions); every registry `substream` cell is `conventional` (`0001`, `0002`, `0004`, `0005`, `0007`, `0009`, `0088`–`0098`), `unconventional` (`0003`, `0006`, `0008`, `0010`, `0099`–`0109`) or empty; every call of §2.3 returns exactly one row for every year 1950–2025 of its window (the windows tile with no gap or overlap, for `USA` and `XWL` where both are used); the water-fate shares (`0019`–`0046`), the removed-scale and removed-sludge shares (`0053`–`0070`) and the retained-scale shares (`0079`–`0084`) sum to 1 at central within $10^{-3}$ per region and era; `0016` has central 0 and high 0.01 (the source of the flagged 1950–2005 rows); `0014` central equals the 2017 `produced_water_unconv_share` series value (0.16); `0078` central 0.9; the solids fractions `0047`–`0050` and ratios `0051`/`0052` have the units, groups and residues of §2.3; `0110` has `residue_type = og_processing_residue` and the same stage, group, tier, route and driver as `0074`; no factor row uses `us_wells_drilled_total`; `0088`–`0098` use `us_wells_drilled_vertical` and `0099`–`0109` `us_wells_drilled_horizontal`; `0085`–`0087` have an empty or matching `driver_series`; no registry row has a region other than `XWL`, `USA` or `CAN`; the new flaring row exists with driver `gas_flared_m3` and unit `Bq/m3` (§12 R1), and rows `0071`–`0073` are reported if still present; every residue type used exists in `residue_types.csv`; `events.csv` has no `oil_gas` row; `produced_water_m3` has `XWL` $\ge$ `USA` at all three bounds in every year; for `oil_production_m3`, `gas_production_m3`, `ngl_production_m3` the `XWL` central exceeds the `USA` central in every year 1950–2025; the three `unit_value_*` series (and `USA` oil and gas) have a value for every year 1950–2025; for `oil_production_t`, `gas_production_m3` and `gas_flared_m3` the `XWL` central minus the sum of the other countries is not below $-10^{-5}$ of the aggregate except where the §3.4 tolerance applies; `gas_flared_m3` has only an `XWL` row before 2012 and country rows plus `XWL` from 2012; no country pair among `SUN`/`RUS`/`KAZ`/`AZE`/`TKM`/`UZB`/`UKR` overlaps in non-zero years; the delivered, NGL and vented radon centrals are recorded (300, 200 and 16 Bq/m³ at the time of writing) with their sum below 1,000 Bq/m³.
- **(j) CLI.** Without `--write` the CLI compares both master outputs **and** `research/oil_gas/build_log.csv` with a fresh build and exits non-zero if any differs; with `--write` all three are written.

**Indicative stream values** (spec author's own central-value arithmetic from the files; *not test expectations*): `USA` 2010 water volume $3.09\times10^{9}$ m³, unconventional share 0.04; `USA` Ra-226 water-borne 19.6 TBq/a (conventional 17.8, unconventional 1.84), of which re-isolated 17.9, impounded 0.67, liberated 1.06, dispersed 0.010; rest of world 2010 water $9.88\times10^{9}$ m³, Ra-226 50.4 TBq/a, liberated 12.6; US scale and sludge Ra-226 solids $0.16$ and $0.24$ TBq/a (2010); gas radon delivered 967 TBq/a, NGL 645, vented 52, Pb-210 plate-out 0.61; oil radon 3.74 TBq/a; flaring 106 TBq/a ($1.32\times10^{11}$ m³); oil sands 2024 5.8 TBq/a; vertical and horizontal cuttings Ra-226 0.53 and 1.18 TBq/a.

## 10. Known limits carried onto the rows (not hidden)

- **Hard era steps** in the fate shares (water, removed scale and sludge, retained scale) and in the unconventional share are real source discontinuities, assumptions anchored on few data points, and are **not smoothed** (coal §12.13). The unconventional fraction (0.5 % to 2005, 4 % 2006–10, 12 % 2011–16, 16 % in 2017, 20 % from 2018) rests on the single 2017 point.
- **Rows by substream.** Only produced-water-derived rows and cuttings are genuinely split between `conventional` and `unconventional`. All other families are booked under `conventional` because no production-by-substream series exists (§11 Q3), so the page will show unconventional gas and oil radon as conventional.
- **Produced water exists for two geographies.** No country series exists, so the rest of the world is one `XXX` row set; country-level water comparisons (OSPAR region by region) are not possible. Radium in produced water outside the US and Norway has no measurements (G1): the `XWL` centre is extrapolated.
- **The `XXX` water volume** is a correlated difference of two modelled series, and its relation to the compiled oil production is a model ratio (about 3 m³ of water per m³ of crude from 2010).
- **Solids.** The solids fraction (2 %, 0.1–10 %) and the scale/sludge split (0.4, 0.2–0.9) rest on two US documents (EPA 1991 draft, EPA 1993 via OGJ), partly circular with the benchmark; the 1993 primary was not obtained. Scale and sludge are anticorrelated; the `sum_correlated` merge ignores that and the row bounds already combine the parameters in log-quadrature, so they must not be recombined. The Ra-228 : Ra-226 ratio in solids is about 4.8 times the EPA figure. Merged production rows hide the solids inside the liberated and impounded-sludge rows.
- **Retained scale (φ = 0.9) and timing:** booked in the creation year with the 20-year retirement lag in the era boundaries (§7.1); the abandoned tubular tonnage and the sludge retained at decommissioning are gaps (G10, G16).
- **Gas radon:** the delivered centre (300 Bq/m³) sits at the geometric mean of a top-down Johnson reading (410–860) and a bottom-up chain (170); confidence low to medium. The NGL row is an inference (low confidence). The radon budget closes at 127 % of the wellhead value (§6.2). Only Rn that leaves the system is `Rn222+`; Rn that decays in pipes appears as plated Pb-210 (choice 3). Po-210 films and refinery sludge are not covered (G3, G4). Rows are flat from 1900 although the gas supply mix changed.
- **Flaring** is placed at `production`/`air_stack` and attributed to `oil`; 1950–2011 is a world back-cast from CO₂ with a +30 to +40 % assumed upper band; there is no country split before 2012; the 2005 value (135 bcm) sits below Elvidge's 172 bcm.
- **Drilling** is US only. Cuttings are Pennsylvania measurements; the 1980–2004 horizontal wells use the long-lateral cuttings mass; 1949 vertical drilling is omitted (no unit value); the retired total well series differs from the split series by 5,953 wells in 2010.
- **Oil sands:** monazite thorium chain only; no sand, clay or coke background, no overburden memo; the oil and produced-water families also run on Canadian oil sands volumes.
- **Allocation:** shares from central values only; gas and NGL unit values are proxies with wide bands that are not propagated; the `bound_radio` definition is a decision (§4.5); under R1 the two bounds coincide.
- **NGL series.** The `XWL` `ngl_production_m3` is less than the sum of its country rows in many years of 1984–2002 (by up to 20 %), so the country rows are never used and NGL enters only as `USA` and `XWL`.
- **Engine parameters:** $\varepsilon$ is empty for `og_scale`, `og_sludge` and `og_processing_residue` (§7.4, §11 Q6).
- **No decay, no exhalation, no seepage** in the stream; no memo tier; no pre-1950 produced water, solids or flaring (D31: the opening stock omits oil and gas scale before 1950).
- Row `basis` is `modelled` everywhere, whatever the factor's own basis; the driver basis is in `notes`.

---

## 11. Open questions for Steve (recommended defaults are already in the body)

1. **Q1. D6: the `bound_radio` product, `bound_main`, and the default basis (asked for by Steve).** Options and consequences are in §4.5. *Recommended default:* default allocation by value (METHODS); `bound_main` = the product with the largest value share (`oil` throughout); `bound_radio` = `oil` (R1: the liquid carries the water that carries the radium). Consequence to confirm: `bound_radio` equals `bound_main`, so the toggle shows only default against all-to-oil. *If you would rather the toggle bracket gas-fired electricity from above,* choose R3 (second-ranked product by value, which is `gas` today) or R2 (`gas`); one helper changes. R4 (water by product) needs a new activity series.
2. **Q2. Flaring driver (§6.4).** *Recommended default:* the satellite and back-cast volume series `gas_flared_m3` as the driver with a new per-m³ factor row (§12 R1: 150 / 800 / 1,400 Bq/m³, the D65 wellhead Rn parameter), the 1950–2011 GCP-scaled world series written as `XXX` and 2012–2025 by country, the legacy per-tonne rows `0071`–`0073` not read (§12 R2), product `oil`. *Fallback if you decline the new row:* keep the crude-tonnage proxy: select `0071`–`0073` with `driver_series="oil_production_t"` by country and rest of world exactly as §6.3; the rest of §6.4 is then dropped, the volume series becomes a benchmark only, and the pre-1950 file gains flaring rows for 1900–1949 (the per-tonne factors are valid from 1900). Totals agree to 4 % at 2010. Also confirm product `oil` (alternative `gas`).
3. **Q3. Sub-stream of families that cannot be split.** The vocabulary has no oil and gas "all" value (coal has `all`). *Recommended default:* `conventional` for gas radon, NGL radon, vented gas, Pb-210 plate-out, oil radon and flaring, with a notes flag. *Alternative:* add `all` to `vocab.json` → `substreams.oil_gas` (a schema/vocabulary change, D63-style), or apply a production share by sub-stream (none exists: the unconventional fraction in the registry is a produced-water share, 0.2 in the US from 2018, against a far larger unconventional share of US gas output).
4. **Q4. NGL radon.** *Recommended default:* keep the NGL row additive to the delivered-gas row, product `ngl`, excluded from the gas-fired benchmark; accept the 127 % radon-budget closure and the unchanged Pb-210 plate-out row (§6.2). *Alternative:* lower the Pb-210 plate-out by subtracting the NGL and vented radon from the in-system decay (about 0.107 instead of 0.189 Bq/m³), or drop the NGL row.
5. **Q5. Drilling.** *Recommended default:* USA only (no world well series); 1949 omitted and logged; horizontal rows 1980–2004 kept with the long-lateral cuttings mass. *Alternative:* cap the horizontal factor at 2005 (about 700–2,000 wells a year in 1995–2004 then get no cuttings) or add a world well-count series.
6. **Q6. Residue-type parameters (engine blockers, not script).** `og_scale` and `og_sludge` have no $\varepsilon$ although the factor notes §2 propose 0.037/0.088/0.14 and 0.05/0.15/0.25 (D62 filled the other types and omitted these two, or the entry was lost), and D62 left `og_processing_residue` $\varepsilon$ empty ("not applicable") although the pipeline refuses an empty set for a type with data rows. *Recommended default:* fill the two proposed triples with the D60 meaning, and fill `og_processing_residue` with an explicit 0 / 0 / 0 for Rn-222 and Rn-220 (no radium parent). Needs a `residue_types.csv` change and a decision record.
7. **Q7. Rest-of-world produced water.** *Recommended default:* correlated difference (§3.4), because `XWL` is modelled as `USA` plus the rest of the world before 2010 and the activity builder enforces world $\ge$ USA at every bound. This departs from `factors_notes.md` §0 ("independent difference, as coal"). *Alternative:* the independent difference (wider bands).
8. **Q8. B1 benchmark band.** `factors_notes.md` §2 states "0.3–0.5 TBq/GW·a" (UK-type and bottom-up) with two unverified figures (UK 170, Netherlands 74 Bq/m³) that papers_round2 says not to use; papers_round3 G4 states 0.6–2.2 (Johnson direct and bottom-up). *Recommended default:* the pass rule of §9(e) (within ×3 of at least one of Johnson-direct 1.38, bottom-up 0.42 and Dixon 0.50), with 0.3–0.5 reported and the stream recorded as 1.5–2.5 times its top. Confirm.
9. **Q9. Solids visibility.** The merge (§5.5) hides the solids inside the liberated and impounded-sludge rows. *Recommended default:* accept (no route in the vocabulary separates solids discharge from water discharge), recompute components in tests. *Alternative:* a new route (for example `water_solids_discharge`) in `vocab.json`.

## 12. Work required before tests

Registry rows, activity changes and vocabulary items needed. Nothing else in `data/` has to change for the tests to run.

**Registry (`data/factors/oil_gas.csv`)**

- **R1. Flaring factor per m³ flared (needed for §6.4; Q2).** New row: stage `production`, `substream` empty, `driver_series` `gas_flared_m3`, group `Rn222+`, tier `liberated`, route `air_stack`, residue empty, region `XWL`, `year_from` 1950, `year_to` 2025, unit `Bq/m3`, basis `modelled`, proposed 150 / 800 / 1,400 (wellhead Rn-222, D65), sources `S1203;S1204;S0001` as for `0071`–`0073`, next free id `oil_gas:0111`. **NOT DONE.** Until it exists the flaring family is `no_family` and the flaring tests are deferred.
- **R2. Retire `0071`–`0073` (hygiene).** Delete them or set `year_to` so that none is valid in 1950–2025. **NOT DONE, optional**; the script ignores them either way (§6.4).
- **R3. Fill `driver_series` of `0085`–`0087`** with `oil_sands_ore_processed_t` (the series now exists). **NOT DONE, optional**; an empty cell is valid and the script uses the series regardless (§7.3).
- **R4. Sources.** Every `source_ids` entry of added rows resolves in `data/sources.csv` (`T04`).

**Vocabulary and engine parameters (only if Steve changes the defaults)**

- `vocab.json` `substreams.oil_gas` gains `all` (Q3, alternative); a new route (Q9, alternative).
- `data/reference/residue_types.csv`: $\varepsilon$ for `og_scale`, `og_sludge`, `og_processing_residue` (Q6). Not needed by the script or the validator; needed by Phase 3.

**Activity (`data/activity/`)**: none required. (Possible later additions: produced water by product for R4; world well counts.) `us_wells_drilled_total` and `produced_water_unconv_share` stay in `oil_gas.csv` unused.

**Contingent:** the flaring tests and the §9(e) flared-volume benchmark wait for R1.

## 13. Clarifications after the spec-blind test review

Reserved. This section will hold the orchestrator's settlements of the test-writer's points after the first review, as in NUCLEAR_SPEC §13.
