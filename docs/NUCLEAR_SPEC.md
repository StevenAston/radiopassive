# `pipeline/streams/nuclear.py` — stream script contract (Task 2.1, nuclear)

Status: v1.0 DRAFT (2026-10-27), for the test-writer and the code-writer; open questions in §11 need Steve's answers before sign-off. Derived from METHODS §3, §5 (incl. §5.4), §6.3, §9, SCHEMA §3–§5, `docs/LIB_SPEC.md` (v1.3), `data/factors/nuclear.csv` (factors `nuclear:0001`–`nuclear:1666`), `research/nuclear/factors_notes.md`, `data/events.csv` and the activity files. Modelled on `docs/COAL_SPEC.md` v1.2, with its §11–§12.17 lessons built in from the start. Where this file and METHODS disagree, METHODS wins and this file is a bug. Decisions in force: D6 (no co-products at any nuclear stage, so `allocation_rule` is `none` except for the civil tokens), D9, D14, D15, D16, D22, D24, D31, D36, D42, D49, D52, D57, D58 (coal lessons). D53–D56, D59 and D60 concern coal enrichment and seepage and are not used here. Steve's registry approvals of 2026-10-27 (all 13 choices in `factors_notes.md` §4; choice 10 settled in §7.4 below) are in force.

The script is a pure function of the files under `data/` (and `research/unscear_extraction.csv` is **not** read by the script; tests read it, §9(e)). It uses only `pipeline.lib` and the standard library plus pandas/numpy if needed. It never reads the network and never decays anything: decay, ingrowth, radon exhalation from tailings, seepage, the accident toggle and the post-accident removal of a destroyed unit's baseline in-core inventory all belong to the Phase 3 engine (METHODS §5.2, §5.4, §9.1).

---

## 1. Interface

```
python -m pipeline.streams.nuclear [--root PATH] [--write]
```

- Without `--write`, outputs go to a scratch directory and are diffed against the committed files; the exit status is non-zero if **any of the three** files below differs.
- With `--write`, the three output files are overwritten.
- `build(root: Path) -> BuildResult` is the importable entry point. `BuildResult` has three attributes: `rows` (master-row dicts, 1950–2025), `rows_pre1950` (master-row dicts, 1800–1949) and `log` (list of dicts, §8). `root` is the repository root, so tests can build a miniature tree in `tmp_path` with the same file names and columns.

| File | Content |
|---|---|
| `data/streams/nuclear.csv` | Master rows, years 1950–2025. Must pass `python -m pipeline.validate --root .` |
| `data/streams_pre1950/nuclear.csv` | Master columns, years 1800–1949, `quantity = flow` only; outside the master schema (SCHEMA §3.2, D57). **Header-only for nuclear today** (§4.6) |
| `research/nuclear/build_log.csv` | The full log (§8). Not a master file and not validated |

Master files are written with `pipeline.lib.rows.write_master` (deterministic, sorted by the SCHEMA §3 key; `write_master([])` writes a header-only file).

## 2. Inputs

### 2.1 Activity series (read with `read_table`; values are `Bounds(value_low, value_central, value_high)`)

| Series | File | Country | Years today | Unit | Used for |
|---|---|---|---|---|---|
| `u_production` | `uranium.csv` | 38 producing countries plus `XWL` | 1945–2024 | `t` (t U) | §4 (all uranium front-end rows) |
| `phi_civil` | `uranium.csv` | `XWL` only | 1945–2024 | `1` | §4 (civil share, METHODS §9.2) |
| `elec_gen_nuclear` | `electricity_generation.csv` | `XWL` (and 30 countries) | 1900–2025 | `TWh` | §5.1 (conversion, enrichment, fabrication); §9(e) denominator |
| `nuc_gen_<t>` | `nuclear.csv` | `XWL` | 1956/57–2024 | `TWh` | §6.1, §6.3 |
| `nuc_cap_<t>` | `nuclear.csv` | `XWL` | 1954–2024 | `GW` | §6.2 |
| `nuc_reprocessed_gwa` | **to be built** (another agent) | `XWL` | not yet | `GWa` (a `TWh` series is also accepted, lib converts) | §5.2 |
| `nuc_sea_dumped_tbq` | **to be built** (another agent) | `XWL` | not yet | `TBq` (or `Bq`) | §5.3 |
| unit capacity for E002 and E013 | **not defined yet** (§11 Q1) | event country | event year | `GW` | §7.2 |

with $t\in\{\texttt{pwr},\texttt{bwr},\texttt{phwr},\texttt{gcr},\texttt{lwgr},\texttt{fbr}\}$. The series `nuc_gen_htgr`, `nuc_gen_other`, `nuc_cap_htgr`, `nuc_cap_other`, `nuc_cap_total`, `nuc_spent_fuel_discharged_thm` and `u_requirements_civil` exist but are **not** used by the script (no factor rows reference them; the last two are benchmark cross-checks only, §9(e)). The new series' **names may change**; this spec uses the names above and the dependency is listed in §11 Q9. Until a new series exists in `data/activity/`, its family writes no rows and the build records one aggregated `no_driver` entry (§8); the script must not raise.

All series keys are (`series`, `year`, `country`); a duplicate key raises `LibError` naming it (§3.7). `source_ids` of the activity rows used are collected into the output rows' `source_ids`.

### 2.2 Other inputs

- **Factors** (`data/factors/nuclear.csv`), looked up with `pipeline.lib.factors.select` and applied with `apply` (§3.4).
- **Events** (`data/events.csv`), read for accident handling only (§7): `event_id`, `date_start` (year), `country`, `stream`, `stage`, `is_accident`, `from_tier`, `to_tiers`, `activity_central_bq`, `source_ids`. **`events.csv` stays the source of truth for event totals, dates, toggles and markers** (Steve, 2026-10-27); the factor rows give the per-group composition (§7.4).
- `data/reference/residue_types.csv` and `groups.csv` are not read by the script (the engine uses them). The residue type `u_tailings` must exist (it does).
- A year with no driver value gives no row for that quantity; that is recorded in the log, not an error.

## 3. Conventions (all rows)

### 3.1 Row columns

| Column | Value |
|---|---|
| `stream` | `nuclear` |
| `substream` | per family (§4–§7): `fuel_cycle` for every non-reactor family; the reactor type (`pwr`, `bwr`, `phwr`, `gcr`, `lwgr`, `fbr`) for effluents, standing inventory and spent fuel; the destroyed unit's type for accident rows |
| `quantity`, `unit` | per family. `flow` has unit `master_unit(result_unit(driver_unit, factor_unit), "flow")`, which is `Bq/a`. `transfer_out`, `transfer_in` and `standing_inventory` have unit `master_unit(result_unit(...), "stock")`, which is `Bq` (a transfer's value is the activity moved during the year) |
| `basis` | `modelled` for every row (every value is a script product of factor and driver, or a registry row used as given). The factor's own basis (`compiled`, `extrapolated`) stays in the registry (§11 Q7) |
| `allocation_variant` | `default`; `allocation_rule` per family: `civil:pre1965` or `civil:ratio` (§4), `civil:throughput` (§5.2), otherwise `none` |
| `embedded_fuel` | `False` |
| `product`, `technology` | empty |
| `event_id` | empty except on accident rows (§7), where it is the event ID; never empty on a row at stage `accident` |
| `residue_type` | `u_tailings` on the impounded tailings rows; empty everywhere else |
| `route` | the registry route on `liberated` rows (flows and `transfer_in`); empty on every other tier |
| `factor_ids` | every factor used to compute the row, in the order applied |
| `source_ids` | union of the factors' `source_ids`, the driver rows' `source_ids` (and, on accident rows, the event's `source_ids`), sorted |
| `below_detection` | from the bounds (`nd_floored`), set by `make_row` |
| `notes` | rule text, then suffixes (§3.3) |

**Country rule.** Global series are looked up with country **`XWL`** (activity and factor region) and written with country **`XXX`** (SCHEMA §3, V10). Rows of a producing country carry that country's code (§4). Accident rows carry the event's country (`SUN`, `JPN`, `USA`; real countries, valid for the event year). `XXX` is also used for the rest-of-world residual of uranium production (§4.2); that row is distinguished by its notes text `rest of world (world aggregate minus listed countries)`.

**Quantities are head-nuclide activity** of the group (METHODS §3.2, D24, D42); the engine applies the group multiplier. `Pu239` rows are Pu-239 only (the multiplier 1.9994 is applied by the engine to that share).

### 3.2 Groups, families and the registry

The script never hard-codes a group list. A **family** is a set of registry rows sharing the keys in the selection tables below. The groups of a family are the distinct `group` values (with route, where the family has two routes) among its registry rows, over all years and regions. For each year the script calls `select` once per (group, route); the winner is used. A failed `select` is handled by §3.6. The expected group sets are listed in §4–§7 for orientation; tests read the actual sets from the file (§9(i)).

`select` match keys are passed exactly as the registry strings, with `None` for an empty registry cell where the table says "none". Keys omitted from a table are not passed.

### 3.3 Flag cause and driver basis in `notes` (coal §12.3, §12.4, §12.15, §12.16)

- Every output row with `below_detection = true` ends its `notes` with `; below_detection cause: <causes>`, a `+`-joined subset, in this fixed order, of: `zero_central_factor`, `exact_zero`, `clipped_difference`, `floor_dominance`, `inherited_flag`. The script tracks the causes of its own inputs and carries them through products and sums; it does not parse lib log text. Rows with `below_detection = false` carry no cause text.
  - `floor_dominance`: the lib's zero-low floor rule fired in a product with no other cause. In this stream it is expected on uranium rows whose ISL complement $1-s$ has a zero low bound (§4.1) and is **not** a defect.
  - `clipped_difference`: a difference (§3.4) had a raw low or central below 0 and was clipped.
  - `exact_zero`: a difference whose raw central and raw high are exactly 0 (raw low $\ge 0$). Not used by the accident remainder, which omits such rows (§7.3).
  - `zero_central_factor`: an input factor with central 0 and high $>0$. None exists in the registry today; the cause is kept for completeness.
- Structural-zero factors (ISL share before ISL existed, `0/0/0`, `below_detection` false) and a civil share $\phi_{\mathrm{civil}}=0$ give rows with value `0/0/0` and `below_detection = false`, no cause text.
- If any activity driver row used has basis `interpolated` or `extrapolated`, the row's `notes` gain `; driver basis: interpolated` (or `extrapolated`, or both joined by `+`). The row's own `basis` stays `modelled`.
- **Suffix order:** rule text first, then `; driver basis: …`, then `; below_detection cause: …` last.

### 3.4 Arithmetic rules

- **Applying a factor.** `apply(driver, driver_unit, factor_row)`, with `result_unit` and `master_unit` for the row unit. Factor units in this registry: `Bq/t` (driver `t`), `Bq/GWa` (driver `TWh`: the lib converts 1 GW·a = 8.766 TWh), `Bq/GW` (driver `GW`), `1` (shares) and `Bq` (event rows, no driver). **`apply` does not accept the unit `Bq`:** event rows are turned into `Bounds(low, central, high)` directly (§7); the script first checks that the row's unit is exactly `Bq`, else raises `LibError`.
- **Products** use `product`. A result with an exact-zero term is `Bounds.exact(0)`.
- **ISL complement.** For a share row with bounds $(s_l,s_c,s_h)$, the conventional fraction is $\mathrm{Bounds}(1-s_h,\,1-s_c,\,1-s_l)$ (anti-correlated with $s$; exact for the structural zeros). A share with $s_h>1$ raises `LibError`.
- **Independent difference** (private helper, tested; same as COAL_SPEC §7): for $a-b$, central $c=c_a-c_b$; $\mathrm{low}=c-\sqrt{(c_a-l_a)^2+(h_b-c_b)^2}$, $\mathrm{high}=c+\sqrt{(h_a-c_a)^2+(c_b-l_b)^2}$; each bound clipped to $\ge0$; a negative central is set to 0 before the bounds are built and logged. When the low bound is clipped to 0, `nd_floored` is set (cause `clipped_difference`). A difference whose low is positive is unflagged. **Used only** for the rest-of-world production residual (§4.2).
- **Sums.** $\sum_c P_{c,y}$ in the rest-of-world residual uses `sum_independent`. The sum of the two routes of one routine transfer (§5) and the sum of the liberated releases of one group at one accident (§7.3) use **`sum_correlated`**: SCHEMA §3.3 rule 1 requires the `transfer_out` row to balance the `transfer_in` rows bound by bound (low, central and high each, to $10^{-6}$), which only a linear (correlated) sum guarantees. This is a deliberate conservatism and is stated in §10.
- **Correlated difference** (coal §12.1) is **not** used in the nuclear stream; the accident remainder is defined bound-wise in §7.3.

### 3.5 Predecessor and successor states

Where `u_production` has a `CSK` value for a year, any `CZE` value for that year is dropped (rows and residual sum); each dropped value is logged (`predecessor_dropped`, country `CZE`, detail names `CSK`). The current data have no such overlap (CSK 1945–1992, CZE 1993–2014), so the rule is inert today and is kept for the shared code path. `DDR` and `DEU` are separate regions (West Germany to 1990) and are not touched. No other predecessor rule is applied.

### 3.6 Missing and ambiguous factors; the `LibError` rule (coal §12.6)

A failed `select` is "no factor" **only** when the `LibError` message starts with `no factor row`; the script then writes no row for that (group, route, year) and logs `no_factor`. Any other `LibError` (including `ambiguous factor rows`) propagates. A family with **no registry rows at all** is logged once as `no_family` (not `no_factor`). Where this spec says a factor must exist (the ISL share for any country-year with a production value; the mill, mine and radon rows for $1950\le y\le2024$), a `no factor row` error is a registry error and also propagates; those lookups are not wrapped. Each family's section states which lookups are optional.

### 3.7 Duplicates and warnings (coal §12.5, §12.7)

- Two activity rows with the same (`series`, `country`, `year`) raise `LibError` naming the key. Nothing is silently first-wins.
- `build()` emits nothing on stderr. The lib's floor-dominance warnings are captured, counted and recorded as one log entry per build (`kind = lib_warning`, year and country empty, `detail` = the count and the message type).

---

## 4. Uranium front end: `u_mining_conv`, `u_mining_isl`, `u_milling` (substream `fuel_cycle`)

### 4.1 Tonnages

For each producing country $c$ in `u_production` **except `XWL`** and each year $1950\le y\le2025$ with a production value $P_{c,y}$:

- A country-year with $P=(0,0,0)$ gives no rows.
- **ISL share** $s_{c,y}$: `select(factors, year=y, region=c, stage="u_mining_isl", group=None, tier=None, route=None, residue_type=None, driver_series=None)`. Exact-region rows exist for `KAZ`, `UZB` and `USA` (`nuclear:0027`–`0037`); every other country takes the `XWL` default (`nuclear:0024`–`0026`) through `select`'s fallback. Unit `1`; the lookup is mandatory.
- **Civil share** $\phi_y$: the `phi_civil` row for `XWL`, year $y$ (a single world series applied to every country; §11 Q10).
- Tonnages (all in t U, as `Bounds`), computed in this order:

$$T^{\mathrm{all}}_{c,y}=\mathrm{product}(P_{c,y},\phi_y),\quad T^{\mathrm{isl}}_{c,y}=\mathrm{product}(P_{c,y},\,s_{c,y},\,\phi_y),\quad T^{\mathrm{conv}}_{c,y}=\mathrm{product}(P_{c,y},\,1-s_{c,y},\,\phi_y)$$

  with $1-s$ the ISL complement (§3.4). (`apply(P, "t", share_row)` may be used for the $s$ factor; the result is identical.)
- **Allocation rule** (D16, SCHEMA §3.3 rule 4): `civil:pre1965` for $y\le1964$ (then $\phi=0$ exactly, so every value is `0/0/0` and `value_high = 0`), `civil:ratio` for $y\ge1965$. `civil:doc` is never emitted, because no per-country documented-end-use series exists (§11 Q10).
- Rows whose value is exactly `0/0/0` **are written** (the pre-1965 rows carry the recorded civil rule; the structural-zero ISL rows keep the row set regular across years). Exceptions are the zero-production country-years above, the zero rest-of-world residual (§4.2) and nothing else (§11 Q5).

### 4.2 Rest of world

The residual driver for year $y$ is the independent difference (§3.4) $P_{\mathrm{XWL},y}-\sum_c P_{c,y}$, with $\sum_c$ by `sum_independent` over the listed countries after the §3.5 rule. If the residual central is $<0$, use 0, log `negative_residual` with the magnitude and write no rest-of-world rows. A residual central of exactly 0 gives no rows. A positive residual gives rows for country `XXX` with the notes text `rest of world (world aggregate minus listed countries)`, run through §4.1 with the **`XWL`** ISL share (the default rows) and the same $\phi_y$. The residual is 0 in most years (`XWL` equals the sum of the listed countries); in 2020 it is 131 t U and in 2024 155 t U.

### 4.3 Rows

Each row family below is computed for every producing country and for the rest-of-world residual. $T$ is the tonnage named in the table; values are `apply(T, "t", factor)`. `select` keys not shown are not passed.

| Family | Stage | Tonnage | Group set (registry, orientation) | Tier | Route | Residue | Quantity | Factors (select keys) |
|---|---|---|---|---|---|---|---|---|
| F1 mine radon | `u_mining_conv` | $T^{\mathrm{conv}}$ | `Rn222+` | `liberated` | `air_ventilation` | none | `flow` | stage, group, tier, route, `driver_series="u_production"`; `nuclear:0001` (1950–79), `0002` (1980–2025) |
| F2 ISL radon | `u_mining_isl` | $T^{\mathrm{isl}}$ | `Rn222+` | `liberated` | `air_process_vent` | none | `flow` | stage `u_mining_isl`, group, tier, route, `driver_series="u_production"`; `nuclear:0003` |
| F3 mill radon | `u_milling` | $T^{\mathrm{all}}$ | `Rn222+` | `liberated` | `air_process_vent` | none | `flow` | stage `u_milling`, group, tier, route; `nuclear:0004` |
| F4 mill dust | `u_milling` | $T^{\mathrm{all}}$ | `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+` (7) | `liberated` | `air_dust` | none | `flow` | stage, group, tier, route; `nuclear:0005`–`0011` |
| F5 U product | `u_milling` | $T^{\mathrm{all}}$ | `U238+`, `U234`, `U235+` (3) | `sealed_fuel_cycle` | none | none | `flow` | stage, group, tier; `nuclear:0012`–`0014` |
| F6 tailings | `u_milling` | $T^{\mathrm{conv}}$ | `Th230`, `Ra226+`, `Pb210+`, `Po210`, `Pa231`, `Ac227+`, `U238+`, `U234`, `U235+` (9) | `impounded` | none | `u_tailings` | `flow` | stage, group, tier, `residue_type="u_tailings"`; `nuclear:0015`–`0023` |

Rules specific to these families:

- **F1 and F2 are process radon** (ventilation, ISL wellfield) entered under their routes (SCHEMA §3.2). Chronic radon from the tailings and waste rock is an engine process: **no row** exists for it.
- **F3–F5 use all civil tonnage** (ISL production is milled or recovered to the same product; UNSCEAR applies milling radon and dust to total production, `nuclear:0004` notes).
- **F6 uses conventional tonnage only.** The factor-row notes state that ISL production has no tailings; this follows them and not the outline in `factors_notes.md` §5.3 ("all civil tonnage") (§11 Q3).
- The U product rows are the single entry of mobilised uranium into `sealed_fuel_cycle` (METHODS §5.2, §6.3); the later conversion, enrichment and fabrication transfers (§5.1) draw on it.
- The mill dust rows are not subtracted from product or tailings (about $10^{-4}$ of the product activity; `nuclear:0005` notes).
- The ISL evaporation-pond residue, mine water, above-threshold waste rock and the dispersed tailings fill are gaps with no rows (§10).

### 4.4 `memo_earth_moved`

No rows: the registry has no earth-moved factor (gap G4).

### 4.5 Years

Mining and milling rows are written for $1950\le y\le2024$; both `u_production` and `phi_civil` end in 2024, so 2025 gives one aggregated `no_driver` entry per series (§11 Q2).

### 4.6 Pre-1950

`u_production` and `phi_civil` start in 1945, but every nuclear factor row has `year_from` $\ge 1950$ and $\phi=0$ before 1965. Years 1800–1949 therefore yield no rows, and `data/streams_pre1950/nuclear.csv` is header-only. The script still walks those years through the same code path and logs the absent factors as aggregated `no_factor` runs, so the omission is visible (§8, §11 Q6).

---

## 5. Routine transfers (Sealed → Liberated): `conv_enrich_fab`, `reprocessing`, `sea_disposal`

METHODS §5.2 and SCHEMA §3.1: at these three stages a plain Liberated `flow` is forbidden (V15). Every release is a **pair**: `transfer_in` into `liberated` (with the route) and `transfer_out` from `sealed_fuel_cycle`. No `event_id`. Country `XXX`, substream `fuel_cycle`, unit `Bq`.

### 5.0 The pair

For stage $s$, year $y$ and group $g$ with release rows $\rho\in\mathcal{R}_{s,g}$ (the routes the registry has for $g$ in year $y$):

- one `transfer_in` row per route $\rho$: tier `liberated`, route $\rho$, value $X_{\rho}$ (the applied factor, §5.1–§5.3);
- one `transfer_out` row: tier `sealed_fuel_cycle`, route empty, value $\mathrm{sum\_correlated}(\{X_\rho\})$, with `factor_ids` the union of the routes' factor IDs in order applied.

With one route the `transfer_out` triple equals the `transfer_in` triple. The balance key is (`stage`, `country`, `year`, `group`, `allocation_variant`); the pair balances at low, central and high to $10^{-6}$ relative (the script asserts $10^{-9}$ and raises `LibError` otherwise).

### 5.1 `conv_enrich_fab`

- Driver: `elec_gen_nuclear`, `XWL`, year $y$ (TWh), applied to the electricity of the country that burns the fuel (G11).
- Allocation rule `none`. Selection: stage `conv_enrich_fab`, group, tier `liberated`, route, `driver_series="elec_gen_nuclear"`.
- Routes and groups (orientation): `air_stack` — `U238+`, `U234`, `U235+`, `Th230`, `Th232`, `Th228+` (`nuclear:0038`–`0043`, 1950–2025, no era scaling); `water_liquid_effluent` — `U238+`, `U234`, `U235+` in four eras (to 1988; 1989–99; 2000–09; 2010–25: `0044`–`0055`) and `Ra226+` (`0056`–`0059`). So `U238+`, `U234` and `U235+` have two routes and a summed `transfer_out`; `Th230`, `Th232`, `Th228+` have one (air) and `Ra226+` has one (liquid).

### 5.2 `reprocessing`

- Driver: **`nuc_reprocessed_gwa`**, `XWL` (civil fuel reprocessed, GW·a; new series, G1). The script uses this series name whatever the registry's `driver_series` cell says (it is empty today). If a registry row names a non-empty `driver_series` that differs from the series used here, the script raises `LibError` ("driver mismatch"). `select` is called **without** a `driver_series` key.
- Allocation rule `civil:throughput` (the series is civil by construction; SCHEMA §3.3 rule 4 requires a `civil:` token at this stage; G9).
- Selection: stage `reprocessing`, group, tier `liberated`, route. Routes: `air_stack` and `water_liquid_effluent`. Groups (orientation): `C14`, `H3`, `I129`, `Kr85`, `Cs137+`, `I131`, `Co60`, `Cs134`, `Pu239`, `Pu240`, `Ru106+` (air); `C14`, `H3`, `I129`, `Cs137+`, `Ru106+`, `Sr90+`, `Am241`, `Co58`, `Co60`, `Cs134`, `I131`, `Mn54`, `Pu239`, `Pu240` (liquid). The era structure is 1950–69, then 1970–79, 1980–84, 1985–89, 1990–94, 1995–97, 1998–2002 and 2003–2025.
- `I131` air has no 1998–2002 row (UNSCEAR 2008 gave none); that gap is a `no_factor` run, not an error. The `Co60`, `Cs134`, `Pu239`, `Pu240`, `Ru106+` (air) and the `Am241`, `Co58`, `Co60`, `Cs134`, `I131`, `Mn54`, `Pu239`, `Pu240` (liquid) rows exist from 2003 only.
- **Pu D49 rows are used as given.** `Pu239` and `Pu240` (2003–2025) are already split from the combined Pu-239+240 report by the activity ratio 1.59 (Pu-239 share 0.386, Pu-240 share 0.614). The script does **not** re-split, re-sum or apply the group multiplier. The output ratio $\mathrm{Pu240}/\mathrm{Pu239}$ at central equals the factor ratio (a test, §9(f)).

### 5.3 `sea_disposal`

- Driver: **`nuc_sea_dumped_tbq`**, `XWL` (activity of civil packaged waste dumped at sea in year $y$; Soviet Arctic dumps are excluded as naval, so the series must contain civil dumping only; G2). Same driver-mismatch rule as §5.2; `select` without `driver_series`.
- The factors are **shares of dumped activity** (unit `1`, route `sea_disposal_package`, 1950–1993): `H3` 0.344; alpha 0.0149 split over `Pu239`, `Pu240`, `Am241`, `Pu238` (placeholder split); non-tritium beta-gamma 0.641 split equally over `Sr90+`, `Cs134`, `Cs137+`, `Fe55`, `Co58`, `Co60`, `C14`, `I125` (placeholder). The 13 central shares sum to $1\pm10^{-3}$ (premise assertion, §9(i)).
- **Unit step.** `apply` has no TBq-to-Bq conversion, so the script converts the driver first: if its unit is `TBq`, $D_{\mathrm{Bq}}=D.\mathrm{scale}(10^{12})$ exactly; if `Bq`, no scaling; any other unit raises `LibError`. Then `apply(D_Bq, "Bq", share_row)`; the result unit is `Bq` and the kind is `stock` (a transfer).
- Allocation rule `none` (the stage is not a civil-rule stage). One route, so `transfer_out` equals `transfer_in`.
- Years with a driver value and no factor (the series may run before 1950 or after 1993) are `no_factor` runs: the registry ends in 1993, and dumping in 1946–49 has no factor (§4.6, §11 Q6).

---

## 6. `reactor_operation` and `spent_fuel` (substream = reactor type)

For each type $t\in\{\texttt{pwr},\texttt{bwr},\texttt{phwr},\texttt{gcr},\texttt{lwgr},\texttt{fbr}\}$, the driver series are `nuc_gen_<t>` (TWh) and `nuc_cap_<t>` (GW), `XWL`; country of the rows `XXX`; allocation rule `none`; substream $t$. A family with no registry rows for a type is logged once as `no_family`.

### 6.1 Effluents (plain Liberated flows)

- Stage `reactor_operation`, quantity `flow`, tier `liberated`, routes `air_stack` and `water_liquid_effluent`, `driver_series="nuc_gen_<t>"`. Value `apply(G_{t,y}, "TWh", factor)`, unit `Bq/a`.
- Selection: stage, group, tier, route, `driver_series`. Groups per route and type are the registry's (orientation: `pwr` 18 air and 9 liquid groups; `bwr` 19 and 9; `phwr` 18 and 9; `lwgr` 19 and 9; `gcr` 17 and 6; `fbr` 8 and 1). Composition into noble gases, particulates and other liquid is **baked into per-group rows** by the registry (choice 1); the script does not split a total.
- `Kr88+` and `Xe138+` are flow-only released-gas groups; they appear here as `flow` rows only, which is allowed.
- Era steps (1950–79, 1980–89, 1990–2002, 2003–09, 2010–25, and GCR 2010–14 / 2015–25) are real discontinuities in the source data. They are **not smoothed** (coal §12.13).
- Reactor effluents are not routine transfers (stage `reactor_operation` is not in `routine_transfers`).

### 6.2 Standing in-core inventory

- Stage `reactor_operation`, quantity `standing_inventory`, tier `sealed_in_core`, route empty, unit `Bq`, `driver_series="nuc_cap_<t>"`. Value `apply(C_{t,y}, "GW", factor)` with factor unit `Bq/GW` (kind `stock`).
- Selection: stage, group, tier `sealed_in_core`, `driver_series`. Groups: LWR types (`pwr`, `bwr`) about 51 groups each (long-lived by Carter batch mean, short-lived by ENDF saturation; four burnup eras 1956–69, 1970–83, 1984–98, 1999–2025 for the burnup-dependent groups); `phwr`, `lwgr`, `gcr` 25 fission-product groups. `fbr` has no in-core rows (`no_family`).
- This is the **no-accident baseline** (METHODS §5.4). Rows continue in and after an accident year exactly as the capacity series gives them. Removing a destroyed unit's inventory afterwards is an engine rule.
- The multiplier is never applied to a stock (METHODS §4.1a); no released-gas group has an in-core row.

### 6.3 Spent-fuel arisings

- Stage `spent_fuel`, quantity `flow`, tier `sealed_fuel_cycle`, route empty, `driver_series="nuc_gen_<t>"`, unit `Bq/a`. Value `apply(G_{t,y}, "TWh", factor)` (factor `Bq/GWa`: arisings per GW·a of electricity at discharge; `nuc_spent_fuel_discharged_thm` is not used).
- Groups: `pwr`, `bwr` 35 groups (actinides, activation and fission products); `phwr`, `lwgr`, `gcr` 13 fission-product groups. `fbr` has no rows (`no_family`). Actinides and activation products for PHWR, LWGR and GCR are a gap (G3).
- This is a **flow into the spent-fuel and waste sub-tier** (METHODS §5.4), not a transfer within Sealed; it never meets the in-core rows.

### 6.4 Years

Rows start in the first year the driver has a value (1956 or 1957 for the LWR types, 1962 for `phwr`, `fbr`; see §2.1), and the factors' `year_from` is 1950 or 1956; both limits are respected. The driver ends in 2024, so 2025 gives aggregated `no_driver` entries (§11 Q2).

---

## 7. Accidents (stage `accident`, event transfers)

### 7.1 Which events

The script reads `data/events.csv` and takes every event with `stream = nuclear`. For each:

- If `stage = accident` **and** the registry has `accident` rows with `tier = liberated` for the event's country and year, the event is modelled (§7.2–§7.4). Today these are **E002** (Three Mile Island 2, 1979, `USA`), **E004** (Chernobyl 4, 1986, `SUN`) and **E013** (Fukushima Daiichi 1–3, 2011, `JPN`). The modelled event must have `is_accident = true`, `from_tier = sealed_in_core` and `to_tiers` containing `liberated` and `sealed_damaged_core`; otherwise the script raises `LibError`.
- Any other nuclear event (E003 Church Rock, E008 Tokaimura) gets no rows and one `event_not_modelled` log entry.
- The reactor type of a modelled event comes from a fixed table in the script: E002 `pwr`, E004 `lwgr`, E013 `bwr`. A modelled event not in the table raises `LibError`.
- The event year is the year of `date_start`. A multi-year or continuing release (the Fukushima ocean release) is booked entirely in that year. Timing within the year (mid-year, METHODS §12.2) belongs to the engine.

### 7.2 Inventory $I_g$ and release $R_{g,\rho}$

- **Release rows.** The `accident` registry rows with tier `liberated`, region = the event's country, validity window containing the event year. Selection: stage `accident`, group, tier `liberated`, route (`air_accident_release` or `water_accident_release`), region = event country. Each is turned into `Bounds(low, central, high)` (unit `Bq`).
- **Inventory.**
  - If the registry has `accident` rows with tier `sealed_in_core` for the event's country and year (E004: 34 groups, UNSCEAR 2000 Annex J Table 1, `nuclear:1596`–`1629`), they give $I_g$ directly (event-specific inventory of the destroyed unit; factor notes: use instead of the generic `nuc_cap_lwgr` rows).
  - Otherwise (E002, E013) the generic in-core rows of §6.2 for the event's type and year, times the destroyed unit's capacity $C_e$ in GW: $I_g=\texttt{apply}(C_e,\ \texttt{"GW"},\ \text{row})$ with row selected for stage `reactor_operation`, tier `sealed_in_core`, `driver_series="nuc_cap_<t>"`, year = event year, group $g$. $C_e$ is a unit capacity input that **does not exist yet** (§11 Q1). **Until it is defined, E002 and E013 write no rows** and one `event_not_modelled` entry with detail `no unit capacity input`; done conditions that name E002 or E013 are then deferred.
- The inventory groups are the groups of the inventory source (34 for E004; the type's in-core groups for generic events). The release groups are the release rows' groups.

### 7.3 Rows per event and group

For each group $g$ in the union of inventory and release groups, with total release $R_g=\mathrm{sum\_correlated}$ over routes (zero if none) and inventory $I_g$ (exact zero if none):

1. **Damaged-core remainder**, bound by bound ($b\in\{\mathrm{low},\mathrm{central},\mathrm{high}\}$):
$$D_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}}-R_{g,\mathrm{c}},\,0),\quad D_{g,\mathrm{low}}=\min\!\big(\max(I_{g,\mathrm{low}}-R_{g,\mathrm{low}},0),\,D_{g,\mathrm{c}}\big),\quad D_{g,\mathrm{high}}=\max\!\big(\max(I_{g,\mathrm{high}}-R_{g,\mathrm{high}},0),\,D_{g,\mathrm{c}}\big)$$
   This is *not* the independent difference of §3.4: it is bound-wise, so that the transfer balances exactly (SCHEMA §3.3 rule 1).
2. **Rows** (stage `accident`, substream = the event's type, country = event country, `event_id`, allocation `none`, `Bq`):
   - `transfer_in`, tier `liberated`, one per release route: value = the release row's bounds;
   - `transfer_in`, tier `sealed_damaged_core`, residue and route empty: value $D_g$, **omitted if exactly `0/0/0`** (for example Chernobyl Kr-85, where inventory equals release);
   - `transfer_out`, tier `sealed_in_core`: value $O_g$ with $O_{g,b}=R_{g,b}+D_{g,b}$ at each bound, so that $O_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}},R_{g,\mathrm{c}})$ and the pair balances to rounding.
3. **Flags.** A remainder bound clipped from a negative raw value sets `nd_floored` when the resulting low is 0 (cause `clipped_difference`). `release_exceeds_inventory` is logged whenever a *central* raw difference is negative (detail names the group and the excess). A group with a release row but no inventory row (E004 `Np239`, `nuclear:1648`, since the inventory value is ambiguous, G12) has $I=0$: $O=R$, no damaged-core row, and `no_inventory` is logged. A group with an inventory row and no release row (for example E004 `La140`, `Nb95`) has $R=0$ and $D=I$.
4. `factor_ids`: the inventory factor ID (and, for generic events, nothing for the capacity series, whose sources go to `source_ids`) plus the release factor IDs, in the order applied. `source_ids`: factors' sources, the capacity row's sources where used and the event's `source_ids`.
5. **No `flow` row exists at stage `accident`**, and no row at that stage lacks an `event_id`.

### 7.4 Choice 10 settled: events are the totals, factors the composition (Steve, 2026-10-27)

- `events.csv` is the source of truth for each event's total, date, country, tiers, `is_accident` toggle flag and marker. The script reads the totals only to check the registry (below); it never writes a row from an `events.csv` total.
- **Required sum.** For each modelled event, the sum over all release rows $\sum_{g,\rho}R_{g,\rho,\mathrm{central}}$ (Bq, head activity, all routes, the same rows the script writes as `transfer_in` into `liberated`) must equal `activity_central_bq` within a **relative tolerance of $10^{-4}$**. The script raises `LibError` if it does not (the registry and the catalogue are inconsistent), and a done-condition test repeats the check on the output rows (§9(c)). Registry check today: E004 $3.8\times10^{-6}$, E013 $3.3\times10^{-5}$, E002 $5.6\times10^{-6}$ relative; the tolerance has a factor 3 margin over the worst case.
- Low and high are **not** required to sum: `events.csv` low and high are scenario bounds (for example E013 low $7.3\times10^{18}$ Bq is Xe-133 only, against a row-sum low of $5.0\times10^{18}$ Bq).
- **No accident activity is counted twice.** (1) Accident activity enters the stream only as event transfers carrying an `event_id`, so the "exclude accidents" run (D15) can zero it. (2) Reactor effluents (§6.1) are routine UNSCEAR rates and are not adjusted in an accident year. (3) The in-core baseline (§6.2) is not reduced by the script. (4) Each (event, group, route) appears once. (5) `events.csv` totals are never turned into rows.
- Pre-event: the baseline in-core rows of the destroyed unit continue in the stream (METHODS §5.4); the engine removes them after the accident year in the with-accidents run.

---

## 8. Log

`BuildResult.log` is a list of dicts with keys `kind`, `year`, `country`, `group` (may be empty) and `detail`. Kinds:

| Kind | When |
|---|---|
| `no_factor` | a `select` failed with `no factor row` (§3.6). **Aggregated**: one entry per contiguous year run per (stage, family/route, country, group); `year` = the first year, `detail` = `first-last (n years)` |
| `no_driver` | a driver series has no value for a year (including the whole run when `nuc_reprocessed_gwa` or `nuc_sea_dumped_tbq` is absent). **Aggregated** as `no_factor`, per (series, country) |
| `no_family` | a family has no registry rows at all (`fbr` in-core and spent fuel); once per build |
| `negative_residual` | §4.2; one entry per year |
| `predecessor_dropped` | §3.5 |
| `event_not_modelled` | §7.1, §7.2 (E003, E008, and E002/E013 until Q1) |
| `no_inventory` | §7.3 (a release group with no inventory row) |
| `release_exceeds_inventory` | §7.3 |
| `lib_warning` | §3.7; one per build |

Aggregated entries carry the output-row country convention (`XXX` for world series, otherwise the country code). Country-years absent from `u_production` are silent (a country that is not producing is not a missing driver); only years in which neither a country list nor `XWL` has a value are logged. The CLI prints counts by kind and, with `--write`, writes the full log to `research/nuclear/build_log.csv`.

---

## 9. Done conditions and tests

Tests read factor and activity values from the files (never hard-coded), with explicit **premise assertions** (§9(i)) so that a changed registry fails loudly instead of passing silently.

- **(a) Schema.** `data/streams/nuclear.csv` passes `python -m pipeline.validate --root .`: no tier or route outside the stage's matrix (V03), no V15 on `conv_enrich_fab`, `reprocessing` or `sea_disposal`, no V09 on `Kr88+`/`Xe138+`, X02 transfers balance, X04 civil tokens on `u_mining_conv`, `u_mining_isl`, `u_milling` and `reprocessing` rows, X05 event tiers legitimate, R02 civil year rules (`civil:pre1965` only for $y\le1964$ with `value_high = 0`; `civil:ratio` only for $y\ge1965$).
- **(b) Candidate nuclides and coverage** (METHODS §4.3 ①). For each family in §4–§7 and each year $y$ with a driver value and a registry row valid in $y$, a row exists for every (group, route) of the family. The test enumerates the registry; a missing row without a matching `no_factor` or `no_driver` log run is a failure. Group coverage is also checked against the METHODS §4.3 list: mining and milling (`U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Pa231`, `Ac227+`, `Rn222+`) each appear in some 2010 row; effluent and reprocessing groups (`H3`, `C14`, `I129`, `I131`, `Cs137+`, `Cs134`, `Sr90+`, `Co60`, `Co58`, `Mn54`, `Ru106+`, `Pu239`, `Pu240`, `Am241`, and the noble gases) appear in the 2010 flows; `Sb125+` and `Tc99` appear in the 2010 spent-fuel flows and standing inventory. Listed groups **absent from the registry** are reported, not failed: the accident list's `La140` and `Nb95` have inventory but no release row (§10).
- **(c) Conservation and events.**
  1. *Transfer balance.* For every balance key (§3.1, SCHEMA) the `transfer_out` equals the sum of the `transfer_in` rows at low, central and high (relative $10^{-6}$). Includes the two-route case (`U238+` at `conv_enrich_fab`, 2010) and the one-route case.
  2. *Event totals (choice 10).* For each modelled event, the output `transfer_in` rows into `liberated` sum (central, Bq, all groups and routes) to `activity_central_bq` of `events.csv` within relative $10^{-4}$. Run for E004 always; for E013 and E002 once Q1 is settled (the release rows themselves do not depend on it, but the pair does).
  3. *Remainder.* Per event and group: $O_{g,\mathrm{c}}=R_{g,\mathrm{c}}+D_{g,\mathrm{c}}$; $O_{g,\mathrm{c}}\ge I_{g,\mathrm{c}}$; $D_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}}-R_{g,\mathrm{c}},0)$; E004 `Kr85` has no damaged-core row; E004 `Np239` has `transfer_out` = release and no damaged-core row.
  4. *No double counting.* No `flow` row at stage `accident`; every accident-stage row has an `event_id`; no row with an `event_id` outside the accident stage; (event, group, route, quantity, tier) unique; the 2011 `reactor_operation` effluent rows equal driver × factor recomputed from the files (no accident adjustment).
  5. *Tonnage partition.* For every uranium country-year at central: $T^{\mathrm{conv}}+T^{\mathrm{isl}}=T^{\mathrm{all}}$ (to $10^{-9}$ relative), checked through F1 + F2-derived tonnage ($\text{row}/\text{factor}$) where the factors are positive.
  6. *Mill balance.* For $y$ with $\phi>0$ and a conventional country: F5 `U238+` : F6 `U238+` residual $=R:(1-R)$ with $R=0.95$, i.e. tailings residual / product $=0.0526$ times $T^{\mathrm{conv}}/T^{\mathrm{all}}$ (premise: `nuclear:0012`, `0021`).
- **(d) Determinism.** Two builds write byte-identical files (all three); row order is the SCHEMA key order; the log order is stable.
- **(e) Benchmarks (D51).** Two years, **2010 and 2020**. Denominators: $W_y=\texttt{elec\_gen\_nuclear}_{\mathrm{XWL},y}/8.766$ GW·a; $W_{t,y}=\texttt{nuc\_gen\_}t/8.766$. Quantities are summed from output rows (central, Bq) and expressed in TBq per GW·a. A value passes when $\tfrac13\le x/x_{\mathrm{ref}}\le3$. The Annex B table is the first estimate; a second, **independent** estimate is required per quantity where one exists.

  **First estimate: UNSCEAR 2016 Annex B, 2010 (S0001; tests read the values from `research/unscear_extraction.csv`, rows `U…`).** The reference values are those of 2010; the same values are used for 2020 (the stream's 2010–25 factors are the 2010 values carried).

  | Quantity (stream rows) | Annex B (TBq per GW·a) | Extraction rows |
  |---|---|---|
  | F1 mine radon, per GW·a of nuclear electricity | 66 | U0021 (denominator 220 t U/GW·a, U0032) |
  | F2 ISL radon | 3 | U0022 |
  | F3 mill radon | 3 | U0023 |
  | F4 mill dust: `U238+`, `U234` | 4×10⁻⁴ | U0030, U0029 |
  | F4 mill dust: `Th230`, `Ra226+`, `Pb210+`, `Po210` | 2×10⁻⁵ each | U0031, U0028, U0027, U0026 |
  | §6.1, per type $t$, per $W_{t,y}$: noble-gas groups $\{$`Ar41`, `Kr85`, `Kr85m`, `Kr87`, `Kr88+`, `Xe133`, `Xe135`, `Xe138+`$\}$ summed; `H3` air; `H3` liquid; `C14`; `I131` | PWR 5.8, 1.5, 18, 0.083, 8×10⁻⁵; BWR 18, 1.3, 0.82, 0.13, 4.2×10⁻⁴; HWR (`phwr`) 35, 200, 170, 0.6, 2.3×10⁻⁵; LWGR 460, 26, 0.78, 1.3, 0.0099; FBR 44, 49, 1.7, 0.12, 2×10⁻⁴ | U0034–U0138 (PWR U0034/36/45/40/38; BWR U0049/51/60/55/53; HWR U0064/66/75/70/68; LWGR U0079/81/90/85/83; FBR U0125/127/136/131/129) |
  | §6.1, `gcr`: the same five quantities against the $W$-weighted mean of the GCR and AGR columns for 2010 (weights 0.93 and 5.01 GW·a, U0016/U0015); for 2020 against the AGR column alone (the stream's 2015–25 factors are AGR-only) | GCR 1,700, 5.0, 4.7, 5.5, 0; AGR 19, 4.0, 410, 1.4, 3.2×10⁻⁵ | U0110/112/121/115/114; U0094/96/106/100/98 |
  | §5.2 reprocessing, per GW·a of fuel reprocessed, La Hague (**Table 13 values are Bq/s per GW·a, not TBq/(GW·a)**; convert $\times3.15576\times10^{7}/10^{12}$): `Kr85` 4.73×10³ (from 1.5×10⁸ Bq/s), `H3` air 1.2, `H3` liquid 211, `C14` air 0.35, `Pu239` (as the combined Pu-239+240 report) 4.1×10⁻⁸ | as listed | U0143, U0140, U0150, U0141, U0149 |

  The reprocessing per-GW·a comparison tests the unit chain (the stream value divided by $G^{\mathrm{rep}}$ equals the registry value) and is therefore partly circular. It is run once `nuc_reprocessed_gwa` exists.

  **Second, independent estimate, per quantity.** "Independent" means independent of UNSCEAR Annex B 2016 and of the registry's own derivation. Where several independent values are given, the stream central must lie within a factor of 3 of **at least one** of them (coal §12.17). "Lie between" is an alternative pass, not a requirement.

  | Quantity | Independent value | Source | Status |
  |---|---|---|---|
  | Mine radon (F1) | none | — | **No independent value exists** in the research notes. The 1982/88 (70 TBq/GW·a), 1993 (300 GBq/t), 2000 and 2016 values are all UNSCEAR (earlier editions; family cross-check only). Excluded from the independent test and documented (§10) |
  | ISL radon (F2), mill radon (F3), mill dust (F4) | none | — | No independent value exists (UNSCEAR 2016 itself says the ISL value is assumed equal to milling and inconclusive). Excluded and documented |
  | Reactor `H3` air, `PWR` and `BWR` | 1.2 and 1.4 TBq per reactor-year | US 2021 medians, NUREG/CR-2907 Vol. 27 (S0121) | Per reactor; a US reactor-year is taken as 1 GW·a (the factor notes' own comparison; state this in the test). Required to pass |
  | Reactor `H3` liquid, `PWR` | 19.9 TBq per reactor-year | S0121 | Required to pass |
  | Reactor `C14`, `PWR` and `BWR` | 0.34 and 0.57 TBq per reactor-year | S0121 | The stream (0.083, 0.13) is 4.1–4.4 times lower: **known miss**, documented, not a test |
  | Reactor noble gases, `BWR` | 0.18 TBq per reactor-year | S0121 | The stream (18) is about 100 times higher: **known miss** (the 2010–25 low bound of PWR/BWR noble gases is this US median, so the independent value sits at the stream's low edge). Test instead that the independent value lies inside the row-sum [low, high] band |
  | Reactor `H3` liquid, all types, absolute (regional lower bound) | 2,800 TBq/a OSPAR nuclear power plants, 2010 and 2020 | OSPAR 2023 (S0122), `research/nuclear/ospar_liquid_discharges_1989_2023.csv` | North-west Europe only. The global stream sum must be $\ge$ the OSPAR value and at most 10 times it |
  | `PHWR`, `LWGR`, `GCR`, `FBR` effluents | none | — | CNSC Appendix H (S0127) was not read; no independent value. Excluded and documented |
  | Reprocessing, absolute `H3` liquid | 11,000 TBq/a (2010), 12,000 TBq/a (2020) | OSPAR (S0122), reprocessing tritium | Stream value $=211\ \text{TBq/GW·a}\times G^{\mathrm{rep}}_y$; the OSPAR values imply about 52 and 57 GW·a. Required once `nuc_reprocessed_gwa` exists. OSPAR covers the UK and France only |
  | Reprocessing `Kr85` per GW·a | 6,900 TBq/GW·a (1995–97) | UNSCEAR 2000 Table 41 | Earlier edition of the same family: **not independent**; recorded as a cross-check |
  | In-core inventory, `BWR` `Cs137+`, `I131` | 345 and 2,960 PBq per GW(e) | Fukushima 1–3, 2,028 MW(e), 700 and 6,000 PBq (S0106) | Independent. Stream 2010 and 2020 (1999–2025 era): 338 and 3,018 PBq/GW. Required to pass |
  | In-core inventory, `LWGR` `Cs137+`, `Sr90+`, `I131` | 260, 220 and 3,200 PBq per RBMK-1000 (1 GW(e)) | UNSCEAR 2000 Annex J (S0104) | Independent of the generic rows. Stream: 252, 191 and 3,166 PBq/GW. Required to pass |
  | In-core inventory, `PWR`, `PHWR`, `GCR` | none | — | No independent value. The producer's own Carter-versus-ENDF cross-check (4 % apart) is internal. Excluded and documented |
  | Spent-fuel arisings | none | — | UNSCEAR Annex B has no quantity; the Carter (S0100) and ENDF/B-VIII.0 (S0141) routes are both the producer's own. Excluded and documented |
  | Conversion, enrichment, fabrication | none | — | Annex B has no release factor (the registry uses UNSCEAR 1988). OSPAR fabrication-and-enrichment alpha (0.021 and 0.011 TBq/a, 2010 and 2020) calibrated the registry's aquatic scaling, so it is **not independent**. Diagnostic only: the stream's global alpha sum (about 0.0055 and 0.0053 TBq/a, indicative) is below the north-west-Europe total |
  | Sea disposal | 85,078 TBq total, 1946–93 | IAEA-TECDOC-1105 (S0103) | The driver series comes from this source: not independent |

  **Indicative stream values** (spec author's own central-value arithmetic from the files, no bounds; *not* test expectations): $W_{2010}=311.0$, $W_{2020}=302.1$ GW·a; tonnage 172 and 158 t U/GW·a; F1 25.1 and 20.3 TBq/GW·a (ratio to 66: 0.38 and **0.31**); F2 1.2 and 1.2; F3 2.3 and 2.2; F4 `U238+` 3.1×10⁻⁴ and 2.9×10⁻⁴. **F1 in 2020 falls outside a factor of 3 of Annex B on the plain per-GW·a basis** because UNSCEAR assumes 220 t U/GW·a all mined conventionally while the stream has 158 t U/GW·a and about 57 % ISL (§11 Q4). Until Steve decides, the F1 pass/fail test is on the Annex B-equivalent per-tonne basis: Annex B radon per t U $=66/220=0.30$ TBq per t U conventionally mined (U0021/U0032) against the stream's F1 $/\,T^{\mathrm{conv}}$; the plain per-GW·a ratio is reported for both years and the 2020 shortfall is a documented known miss.
- **(f) Hand-computed cases.** At least twelve rows of one year (2010, plus the cases that need another year) are recomputed independently from the factor and activity values, including: an F1 row for a country with its own ISL share (`KAZ`: 3 % conventional, low bound flagged `floor_dominance`); an F1 row for `CAN` using the `XWL` ISL default; a pre-1965 zero row (`civil:pre1965`, `value_high = 0`) and a 1965 row (`civil:ratio`); a rest-of-world residual row (2020: 131 t U); an F6 tailings row (conventional tonnage only); an F5 product row; a `conv_enrich_fab` pair with two routes (`U238+`, 2010) and one with a single route (`Th230`); a `reactor_operation` PWR noble-gas flow showing the TWh→GW·a conversion; a PWR standing-inventory row (`Bq/GW` × `GW`); a spent-fuel row; a reprocessing `Pu239`/`Pu240` pair showing the ratio is not re-split (2010); and for E004 one released-and-retained group, one `Kr85` with no damaged-core row, `Np239` with no inventory, and the `Cs137+` damaged remainder.
- **(g) Fixture tests** on a miniature tree in `tmp_path` that copies the full real factor file and events file and shrinks only the activity files: the negative-residual rule; the rest-of-world zero residual; CSK/CZE `predecessor_dropped`; a missing driver year (aggregated `no_driver` run); the real `I131` reprocessing gap as a `no_factor` run (when `nuc_reprocessed_gwa` is supplied in the fixture); duplicate activity rows raise `LibError`; an ambiguous factor (duplicated registry row) propagates; an absent `nuc_reprocessed_gwa` or `nuc_sea_dumped_tbq` gives one aggregated `no_driver` and no exception; the `TBq` driver is scaled by $10^{12}$; a wrong driver unit raises; a driver-series mismatch in the registry raises; an event whose registry sum differs from `events.csv` by more than $10^{-4}$ raises; release above inventory logs `release_exceeds_inventory` and keeps the pair balanced; an ISL share with high above 1 raises.
- **(h) Pre-1950 file.** Header-only today; if non-empty it has only years 1800–1949, `quantity = flow`, no `memo_*` tier, and passes `schema/master.json` with the `year` bounds relaxed. It is produced by the same code path as the post-1950 rows.
- **(i) Premise assertions.** Before comparing any value, a test asserts the registry premises it uses, failing with a message that names the changed premise: for example `nuclear:0002` unit `Bq/t` and central $3\times10^{11}$ valid in 2010; `nuclear:0004` and `nuclear:0003` both present; the 13 sea-disposal central shares sum to $1\pm10^{-3}$; `nuclear:1565` is $4.734\times10^{15}$ Bq/GW·a, equal to $1.5\times10^{8}$ Bq/s $\times3.156\times10^{7}$ s (UNSCEAR 2016 Table 13, `Kr85`, La Hague, 47 GW·a); the Pu-240/Pu-239 central ratio of the 2003–25 reprocessing rows is $1.59\pm0.01$; the registry's release sums for E002/E004/E013 equal `activity_central_bq` within $10^{-4}$; no registry row has `below_detection` true.
- **(j) CLI.** Without `--write` the CLI compares both master outputs **and** `research/nuclear/build_log.csv` with a fresh build and exits non-zero if any differs; with `--write` all three are written.

## 10. Known limits carried onto the rows (not hidden)

- **UNSCEAR 2016 Table 13 units.** The block headed "TBq/(GW a)" is in fact Bq/s per GW·a. Check: La Hague Kr-85 $7.1\times10^{9}$ Bq/s divided by $1.5\times10^{8}$ gives the 47 GW·a normalisation, and $1.5\times10^{8}\times3.156\times10^{7}/10^{12}=4{,}734$ TBq/GW·a, which is factor `nuclear:1565`. The extraction file already carries the unit "Bq/s per GW a" (U0140–U0162). Any benchmark that reads Table 13 must convert.
- Hard era steps in the effluent, in-core and reprocessing series (1950–69, 1970–79, 1980–84, 1985–89, 1990–94, 1995–97, 1998–2002, 2003–09, 2010–25) are real source discontinuities, not smoothed. The 2010 UNSCEAR values are carried unchanged to 2025; the GCR series has a step at 2010 and 2015 (G13).
- The composition shares that split UNSCEAR's mixed categories (noble gases, particulates, other liquid) into per-group rows are judgement (about 400 rows). The PWR/BWR noble-gas 2010–25 central is the UNSCEAR mean, 70–100 times the US 2021 median per reactor, which is the row's low bound.
- Reprocessing throughput is an implied or new series; 1998–2002 factors use an implied 62.6 GW·a/a from Kr-85. Sellafield B205, Marcoule UP1 and Mayak RT-1 civil fractions are not available (G9); their discharges are excluded, not scaled.
- Sea disposal is placeholder-split (alpha and beta-gamma shares), Atlantic table only; Soviet Arctic dumps are excluded as naval.
- Mine radon, ISL radon, mill radon and dust have **no independent estimate**; F1 in 2020 misses Annex B on the per-GW·a basis (§9(e), §11 Q4).
- Conventional-only tailings; the ISL pond residue, mine water, waste rock, dispersed tailings fill, operational LLW, decommissioning and construction have no rows (G4, G7, G10); `decommissioning` and `construction` stages are empty.
- Reactor types without rows: `htgr` and `other` have activity series but no factors; `fbr` has effluents (air: `Ar41`, `C14`, `H3`, `I131`, `Kr85`, `Kr88+`, `Xe133`, `Xe135`; liquid: `H3`) but no in-core or spent-fuel rows. PHWR, LWGR, GCR in-core and spent-fuel rows are fission products only (G3).
- Conversion, enrichment and fabrication use a 1980–85 UNSCEAR model facility, applied to the burner's electricity; aquatic rows are scaled by an OSPAR trend (north-west Europe only); the stream's alpha sum is below the OSPAR regional total.
- The `transfer_out` of a two-route routine transfer is the **correlated** sum of its `transfer_in` rows (needed for the SCHEMA balance rule); this is wider than an independent sum.
- Accidents: Chernobyl `Np239` has no inventory (58,100 against 27,000 PBq, G12) so the whole release is the transfer out; `La140` and `Nb95` have inventory but no release row, so their damaged-core remainder equals the whole inventory; TMI-2 `Kr85`/`Xe133m` and Fukushima `Cs134` (ocean) are missing (G12). E002 `Xe133` central is a judgement from a source not retrieved (Rogovin, S0138). E008 Tokaimura has no factor rows.
- Row `basis` is `modelled` everywhere, whatever the factor's own basis (§11 Q7). Rule 1 of METHODS §9.2 (documented end use) is not implemented; the world $\phi_{\mathrm{civil}}$ series is applied to every country.
- 2025 has no uranium, `nuc_gen` or `nuc_cap` rows (the series end in 2024); only `conv_enrich_fab` has a 2025 driver (§11 Q2).

---

## 11. Open questions for Steve

These could not be settled from the documents; the spec's default is stated so the tests can be written.

1. **Unit capacity for E002 and E013.** The generic-inventory route (`factors_notes.md` §5, item 9) needs the destroyed units' capacity in GW(e). No activity series or registry row has it. The documents give only Fukushima 1–3 at 2.03 GW(e) (2,028 MW(e), S0106; "rating figures are mine") and nothing for TMI-2. *Default in this spec:* E002 and E013 write no rows until an input exists. Please say where it should live (a new activity series keyed by event country and year, a registry row with unit `GW`, or a constant in the script) and give the TMI-2 value and its source. Without it the two events' releases (about 7.5×10¹⁸ and 9.3×10¹⁶ Bq) are missing from the stream.
2. **2025.** `u_production`, `phi_civil`, `nuc_gen_*` and `nuc_cap_*` end in 2024, while `elec_gen_nuclear` has 2025. *Default:* no 2025 rows for those families (logged). Do you want the activity builder to extrapolate 2024 to 2025 (basis `extrapolated`), as was done for coal consumption?
3. **Tailings tonnage.** `factors_notes.md` §5.3 says tailings on all civil tonnage; the tailings factor notes say ISL has no tailings. *Default:* conventional tonnage ($T^{\mathrm{conv}}$) only. Confirm.
4. **Mine-radon benchmark in 2020.** On the plain per-GW·a basis F1 is 0.31 times Annex B in 2020 (0.38 in 2010) because Annex B assumes 220 t U/GW·a all mined conventionally. *Default:* pass/fail on the per-tonne basis, per-GW·a ratio reported, 2020 shortfall a documented known miss. Alternatives: accept the known miss on the plain basis, or adjust the factor.
5. **Exact-zero rows.** *Default:* write `0/0/0` rows for $\phi=0$ (pre-1965) and for structural-zero ISL shares, but not for zero-production country-years or a zero rest-of-world residual. Alternative: write none, which would leave `civil:pre1965` unused.
6. **Pre-1950 nuclear and 1946–49 sea disposal.** METHODS §2.1 and §6.3 expect civil sea disposal from 1946 to enter the opening stock, but the sea-disposal factors start in 1950 and a routine transfer cannot be a `flow` in the (flow-only) pre-1950 file. *Default:* header-only `data/streams_pre1950/nuclear.csv`, 1946–49 dumping unrecorded. Do you want the registry extended to 1946 and a rule for how pre-1950 sea disposal enters the opening stock?
7. **Row `basis`.** *Default:* `modelled` on every row. Alternative: the weakest of the factor and driver bases (so that the 2003–25 reprocessing rows read `extrapolated`), which would let the page hatch them.
8. **Event tolerance and failure mode.** *Default:* relative $10^{-4}$ on the central release sum, `LibError` on failure. Confirm, or ask for a log entry instead of an exception.
9. **New series names and units.** `nuc_reprocessed_gwa` (unit `GWa`) and `nuc_sea_dumped_tbq` (unit `TBq`) are being built by another agent and the names may change; the registry's `driver_series` cells for reprocessing and sea disposal are empty. *Default:* this spec's names, the script ignores the registry cell unless it is non-empty and different (then raises). Please confirm final names and units, and whether the registry cells will be filled.
10. **Civil rule 1 (documented end use).** METHODS §9.2 orders rules per country-year, but `phi_civil` is a single world series. *Default:* the world $\phi$ for every country; `civil:doc` never emitted. Confirm.
11. **Accident groups with missing halves.** Chernobyl `La140` and `Nb95` have no release row, and `Np239` has no inventory. *Default:* as in §7.3. Confirm, or supply the missing values.
12. **`technology`.** *Default:* empty, as for coal. Alternative: `nuclear` on every row.
13. **Which event types count as modelled.** E003 (Church Rock, `u_milling`) and E008 (Tokaimura, `sealed_fuel_cycle` source) have no factor rows. *Default:* no rows, one log entry each. Do you want factor rows for either?
