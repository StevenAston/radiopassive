# `pipeline/streams/nuclear.py` — stream script contract (Task 2.1, nuclear)

Status: v1.2 DRAFT (2026-11-04), for the test-writer and the code-writer. All thirteen open questions of v1.0 are resolved per D64 (Steve, 2026-11-02; §11) and the decided rules are written into the body sections. v1.2 brings the spec into line with the registry as revised under D65 and D67 (Steve, 2026-11-04; `research/nuclear/factors_notes.md` §10): the uranium overburden memo series (§4.4), the TMI-2 release rows (§7), the split ISL default shares (§4.1), the PWR/BWR noble-gas era split at 2014/2015 (§6.1), the CANDU 19.3 kg U value change and the Grand Junction exclusion (§10). The registry rows and activity changes that must exist before the tests can run are listed in §12, with the items already done marked. Changes from v1.0 are marked "(v1.1)" and changes from v1.1 "(v1.2)" where they alter a rule. Derived from METHODS §3, §5 (incl. §5.4), §6.3, §9, SCHEMA §3–§5 (v2.4), `docs/LIB_SPEC.md` (v1.4, §10 `substream` match key), `data/factors/nuclear.csv` (factors `nuclear:0001`–`nuclear:1727`), `research/nuclear/factors_notes.md`, `data/events.csv` and the activity files (including `data/activity/nuclear_cycle.csv`; `research/activity/notes.md` §9). Modelled on `docs/COAL_SPEC.md` v1.2, with its §11–§12.17 lessons built in from the start. Where this file and METHODS disagree, METHODS wins and this file is a bug. Decisions in force: D6 (no co-products at any nuclear stage, so `allocation_rule` is `none` except for the civil tokens), D9, D14, D15, D16, D22, D24, D31, D36, D42, D49, D52, D57, D58 (coal lessons), D63 (factor `substream` column), D64 (resolutions), D65 (round-2 literature revisions, including the overburden memo series) and D67 (Grand Junction excluded as military). D53–D56, D59 and D60 concern coal enrichment and seepage and are not used here. Steve's registry approvals of 2026-10-27 (all 13 choices in `factors_notes.md` §4; choice 10 settled in §7.4 below) are in force.

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
| `data/streams_pre1950/nuclear.csv` | Master columns, years 1800–1949, `quantity = flow` only; outside the master schema (SCHEMA §3.2, D57). **(v1.1)** Holds the 1946–49 civil sea-disposal flows (liberated half only, §5.3, §4.6); nothing else is non-empty today |
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
| `nuc_reprocessed_gwa` | `nuclear_cycle.csv` | **site country rows** `FRA` (1966–2025), `GBR` (1994–2022: THORP 1994–2018, Sellafield B205 civil 1995–2022 per D64), `JPN` (1977–2008), `DEU` (1971–90), `BEL` (1966–74); `XWL` 1950–2025 is their sum (check only) | 1950–2025 | `GWa` | §5.2 |
| `nuc_sea_dumped_tbq` | `nuclear_cycle.csv` | **dumping country rows** `BEL`, `CHE`, `DEU`, `FRA`, `GBR` (1949–82), `ITA`, `JPN`, `NLD`, `NZL`, `SWE`, `USA` (1946–70); `XWL` 1946–2025 (zeros after 1982) is their sum (check only) | 1946–2025 | `TBq` (activity at packaging) | §5.3 |
| `unit_capacity` (E002, E013) | **factor rows** of `data/factors/nuclear.csv`, not an activity series (§7.2) | event country | event year | `GW` | §7.2 |

with $t\in\{\texttt{pwr},\texttt{bwr},\texttt{phwr},\texttt{gcr},\texttt{lwgr},\texttt{fbr}\}$. The series `nuc_gen_htgr`, `nuc_gen_other`, `nuc_cap_htgr`, `nuc_cap_other`, `nuc_cap_total`, `nuc_spent_fuel_discharged_thm` and `u_requirements_civil` exist but are **not** used by the script (no factor rows reference them; the last two are benchmark cross-checks only, §9(e)). **(v1.1)** The names `nuc_reprocessed_gwa` and `nuc_sea_dumped_tbq` and their units are final (D64) and the series exist in `data/activity/nuclear_cycle.csv` (`research/activity/notes.md` §9.1, §9.2). The two series are used **by country**: the script reads the country rows and never the `XWL` rows of these two series, because `XWL` is the sum of the country rows and using both would count the activity twice. `XWL` is read for one consistency check only: the sum of the country centrals equals the `XWL` central within relative $10^{-5}$ in every year, else `LibError`. (The uranium and generation series keep the world-driver convention of §3.1.) A series that is absent from `data/activity/` (in a fixture) gives no rows and one aggregated `no_driver` entry (§8); the script must not raise.

All series keys are (`series`, `year`, `country`); a duplicate key raises `LibError` naming it (§3.7). `source_ids` of the activity rows used are collected into the output rows' `source_ids`.

### 2.2 Other inputs

- **Factors** (`data/factors/nuclear.csv`), looked up with `pipeline.lib.factors.select` and applied with `apply` (§3.4).
- **Events** (`data/events.csv`), read for accident handling only (§7): `event_id`, `date_start` (year), `country`, `stream`, `stage`, `is_accident`, `from_tier`, `to_tiers`, `activity_central_bq`, `source_ids`. **`events.csv` stays the source of truth for event totals, dates, toggles and markers** (Steve, 2026-10-27); the factor rows give the per-group composition (§7.4, §7.6) and, for E002 and E013, the destroyed units' capacity (§7.2).
- **`substream` (D63, schema v2.4, LIB_SPEC §10).** `data/factors/nuclear.csv` carries the `substream` column (directly after `stage`). **Nuclear keeps the reactor type in `driver_series`** (`nuc_gen_<t>`, `nuc_cap_<t>`; approved registry choice 3), so **the `substream` cell is left empty on every nuclear factor row**, including the rows added under §12. The script therefore does **not** pass `substream` to `select` (a call without the key behaves as before, LIB_SPEC §10 item 4). A premise assertion (§9(i)) checks that every nuclear registry `substream` cell is empty, so that a later filled cell fails loudly instead of being silently ignored. The `substream` of the **output rows** is a separate matter (§3.1).
- `data/reference/residue_types.csv` and `groups.csv` are not read by the script (the engine uses them). The residue type `u_tailings` must exist (it does).
- A year with no driver value gives no row for that quantity; that is recorded in the log, not an error.

## 3. Conventions (all rows)

### 3.1 Row columns

| Column | Value |
|---|---|
| `stream` | `nuclear` |
| `substream` | per family (§4–§7): `fuel_cycle` for every non-reactor family; the reactor type (`pwr`, `bwr`, `phwr`, `gcr`, `lwgr`, `fbr`) for effluents, standing inventory and spent fuel; the destroyed unit's type for accident rows; `fuel_cycle` for the Church Rock rows (§7.6) |
| `quantity`, `unit` | per family. `flow` has unit `master_unit(result_unit(driver_unit, factor_unit), "flow")`, which is `Bq/a`. `transfer_out`, `transfer_in` and `standing_inventory` have unit `master_unit(result_unit(...), "stock")`, which is `Bq` (a transfer's value is the activity moved during the year) |
| `basis` | `modelled` for every row (every value is a script product of factor and driver, or a registry row used as given). The factor's own basis (`compiled`, `extrapolated`) stays in the registry and the **driver** basis goes into `notes` (§3.3) (D64, §11 item 7) |
| `allocation_variant` | `default`; `allocation_rule` per family: `civil:pre1965` or `civil:ratio` (§4), `civil:throughput` (§5.2), `civil:doc` on the Church Rock rows (§7.6), otherwise `none` |
| `embedded_fuel` | `False` |
| `product`, `technology` | empty |
| `event_id` | empty except on event rows (§7: accident rows and the Church Rock rows), where it is the event ID; never empty on a row at stage `accident` |
| `residue_type` | `u_tailings` on the impounded tailings rows and on the Church Rock `impounded` and `dispersed` rows (§7.6); empty everywhere else |
| `route` | the registry route on `liberated` rows (flows and `transfer_in`); empty on every other tier |
| `factor_ids` | every factor used to compute the row, in the order applied |
| `source_ids` | union of the factors' `source_ids`, the driver rows' `source_ids` (and, on accident rows, the event's `source_ids`), sorted |
| `below_detection` | from the bounds (`nd_floored`), set by `make_row` |
| `notes` | rule text, then suffixes (§3.3) |

**Country rule (v1.1).** Global series are looked up with country **`XWL`** (activity and factor region) and written with country **`XXX`** (SCHEMA §3, V10): this holds for `elec_gen_nuclear`, `nuc_gen_<t>` and `nuc_cap_<t>`. Rows of a producing country carry that country's code (§4). **Reprocessing rows carry the site country** (`FRA`, `GBR`, `JPN`, `DEU`, `BEL`) and **sea-disposal rows the dumping country** (§5.2, §5.3); the factor region is still `XWL` (the factors are generic, so `select` falls back to them). `XXX` is not used for these two stages. Accident rows carry the event's country (`SUN`, `JPN`, `USA`; real countries, valid for the event year). `XXX` is also used for the rest-of-world residual of uranium production (§4.2); that row is distinguished by its notes text `rest of world (world aggregate minus listed countries)`.

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
- **(v1.1) Civil-share flag.** US sea-disposal rows (1946–70) end their rule text with `; civil share undocumented (D64)`: the AEC, Navy and contractor waste has no documented civil share (D16). Sea-disposal rows of other countries and all other rows carry no such text.
- **Suffix order:** rule text first, then the civil-share flag where it applies, then `; driver basis: …`, then `; below_detection cause: …` last.

### 3.4 Arithmetic rules

- **Applying a factor.** `apply(driver, driver_unit, factor_row)`, with `result_unit` and `master_unit` for the row unit. Factor units in this registry: `Bq/t` (driver `t`), `Bq/GWa` (driver `TWh`: the lib converts 1 GW·a = 8.766 TWh), `Bq/GW` (driver `GW`), `1` (shares) and `Bq` (event rows, no driver). **`apply` does not accept the unit `Bq`:** event rows are turned into `Bounds(low, central, high)` directly (§7); the script first checks that the row's unit is exactly `Bq`, else raises `LibError`. The unit-`GW` capacity rows of §7.2 are likewise turned into `Bounds` directly (unit checked to be exactly `GW`) and then multiplied with `apply(C, "GW", in_core_row)`.
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
- **ISL share** $s_{c,y}$: `select(factors, year=y, region=c, stage="u_mining_isl", group=None, tier=None, route=None, residue_type=None, driver_series=None)`. Exact-region rows exist for `KAZ`, `UZB` and `USA` (`nuclear:0027`–`0037`); every other country takes the `XWL` default through `select`'s fallback. **(v1.2, D65)** The `XWL` default is split into five eras: `nuclear:0024` (1950–66, structural zero), `0025` (1967–99), `0026` (2000–09), `1701` (2010–19) and `1702` (2020–25), contiguous with no gap or overlap, so each country-year has exactly one candidate row. `XWL` is read as the **rest of the world** (the default for every country without its own row), not the world total. **Known limit (v1.2):** the default is low for countries with a large ISL share that have no row of their own, namely Australia, Russia and China (own ISL shares about 0.37–0.42, 0.6 and 0.9 in 2023–24 per the Red Books); their 2020–25 conventional tonnage $T^{\mathrm{conv}}$, and so the F1 and F6 rows (F2 is understated correspondingly), is overstated for those countries. The ISL share of the `XWL` rest-of-world row (§4.2) is correct by construction. The country rows for `AUS`, `RUS`, `CZE`, `CHN` and `BGR` proposed in round 2 were not added (values by era not available; medium-low confidence). Unit `1`; the lookup is mandatory.
- **Civil share** $\phi_y$: the `phi_civil` row for `XWL`, year $y$ (a single world series applied to every country; this is accepted as a **limit**, D64, §10, §11 item 10).
- Tonnages (all in t U, as `Bounds`), computed in this order:

$$T^{\mathrm{all}}_{c,y}=\mathrm{product}(P_{c,y},\phi_y),\quad T^{\mathrm{isl}}_{c,y}=\mathrm{product}(P_{c,y},\,s_{c,y},\,\phi_y),\quad T^{\mathrm{conv}}_{c,y}=\mathrm{product}(P_{c,y},\,1-s_{c,y},\,\phi_y)$$

  with $1-s$ the ISL complement (§3.4). (`apply(P, "t", share_row)` may be used for the $s$ factor; the result is identical.)
- **Allocation rule** (D16, SCHEMA §3.3 rule 4): `civil:pre1965` for $y\le1964$ (then $\phi=0$ exactly, so every value is `0/0/0` and `value_high = 0`), `civil:ratio` for $y\ge1965$. `civil:doc` is never emitted on production rows, because no per-country documented-end-use series exists (D64); its only use is on the Church Rock rows (§7.6).
- Rows whose value is exactly `0/0/0` **are written** (the pre-1965 rows carry the recorded civil rule; the structural-zero ISL rows keep the row set regular across years). Exceptions are the zero-production country-years above, the zero rest-of-world residual (§4.2) and nothing else (D64, §11 item 5). The same rule holds for every family: an activity driver of exactly zero for a country-year gives no rows, a structural `0/0/0` factor result is written.

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
| F7 overburden memo (v1.2, **USA only**) | `u_mining_conv` | $T^{\mathrm{conv}}$ | `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+` (7) | `memo_earth_moved` | none | none | `flow` | stage `u_mining_conv`, group, tier `memo_earth_moved`, `driver_series="u_production"`, region `USA`; `nuclear:1707`–`1727` (§4.4) |

Rules specific to these families:

- **F1 and F2 are process radon** (ventilation, ISL wellfield) entered under their routes (SCHEMA §3.2). Chronic radon from the tailings and waste rock is an engine process: **no row** exists for it.
- **F3–F5 use all civil tonnage** (ISL production is milled or recovered to the same product; UNSCEAR applies milling radon and dust to total production, `nuclear:0004` notes).
- **F6 uses conventional tonnage only.** The factor-row notes state that ISL production has no tailings; this follows them and not the outline in `factors_notes.md` §5.3 ("all civil tonnage") (D64, §11 item 3).
- The U product rows are the single entry of mobilised uranium into `sealed_fuel_cycle` (METHODS §5.2, §6.3); the later conversion, enrichment and fabrication transfers (§5.1) draw on it.
- The mill dust rows are not subtracted from product or tailings (about $10^{-4}$ of the product activity; `nuclear:0005` notes).
- The ISL evaporation-pond residue, mine water and above-threshold waste rock are gaps with no rows (§10). The below-threshold overburden is the memo series of §4.4 (US only). The Grand Junction tailings fill is **not** a gap in this sense: it is excluded as military (D67, §10) and has no row.

### 4.4 `memo_earth_moved` (v1.2, D65)

The registry now holds a uranium overburden memo series, `nuclear:1707`–`1727` (21 rows; EPA 1991 chapter B.1, S1250; D21 below-threshold overburden and waste rock moved to reach the deposit, kept as a memo, METHODS §6.3). The earlier statement that the family has no rows (gap G4) is withdrawn.

- **Registry rows.** Stage `u_mining_conv`, tier `memo_earth_moved`, route and residue empty, region `USA`, `driver_series` `u_production`, unit `Bq/t` (Bq per t U produced), basis `modelled`. Seven groups times three eras: `U238+`, `U234`, `Th230`, `Ra226+` (877 Bq/kg overburden concentration), `Pb210+`, `Po210` (614 Bq/kg) and `U235+` (44.4 Bq/kg); eras **1950–68, 1969–78, 1979–88**. The per-tonne-U overburden is the EPA Table B.1-3 overburden tonnage of the era divided by US `u_production` of the era (3,123, 15,022 and 22,546 t per t U), so the `Ra226+` centrals are about $2.7\times10^{9}$, $1.3\times10^{10}$ and $2.0\times10^{10}$ Bq per t U. The eras are contiguous, so each (group, year) has one candidate row.
- **How the script writes them.** For country `USA` only, each year $1950\le y\le1988$ with a `u_production` value, each of the seven groups: `select(factors, year=y, region="USA", stage="u_mining_conv", group=g, tier="memo_earth_moved", route=None, residue_type=None, driver_series="u_production")`, and `apply(T_conv, "t", factor)` with $T^{\mathrm{conv}}_{\mathrm{USA},y}$ of the next bullet. Row columns: country `USA`, substream `fuel_cycle`, stage `u_mining_conv`, **quantity `flow`**, tier **`memo_earth_moved`** (outside the tier totals, SCHEMA §3.1 and §5.3; flow only, never `opening_stock`), unit `Bq/a`, route and `residue_type` empty, `event_id` empty, basis `modelled`. `factor_ids`: the USA ISL-share factor, then the memo factor (order applied). The family is not run for any other country or for the `XXX` rest-of-world residual (the factors have region `USA` only and a fallback to another region is not wanted), and a non-USA country-year gives neither a row nor a log entry.
- **The civil rule applies (explicit).** The tonnage is the conventional civil tonnage of §4.1, $T^{\mathrm{conv}}_{\mathrm{USA},y}=\mathrm{product}(P_{\mathrm{USA},y},\,1-s_{\mathrm{USA},y},\,\phi_y)$, i.e. **conventional US tonnage $\times(1-\text{ISL share})\times\phi_{\mathrm{civil}}$**. The allocation rule is therefore `civil:pre1965` for $y\le1964$, where $\phi=0$ exactly and every value is `0/0/0` with `value_high = 0` (written, not omitted, §4.1), and `civil:ratio` for $y\ge1965$ (SCHEMA X04 and R02 hold for these rows). **Consequence: the memo series is zero for 1950–64**, although the EPA overburden tonnage for 1950–68 includes those years, and it is also reduced by the ISL share (central 0.05 in 1974–88, `nuclear:0035`); this is the ruling asked for in `factors_notes.md` §10.6 and is accepted as a limit (§10). The rows count only civil-attributed earth moved and are not a complete record of US uranium overburden.
- **No rows after 1988.** There is no EPA tonnage after 1988, so no factor row covers 1989–2025. This is a stated limit, not an error: the failed `select` is a `no factor row` error and is logged as aggregated `no_factor` runs (one per group, 1989–2025), which the done conditions expect (§9(b)).
- **`u_waste_rock`.** The Rn-222 emanation coefficient for the residue type `u_waste_rock` (0.1 / 0.3 / 0.5, D65) is a `residue_types.csv` change used by the engine; the script reads no residue-type file and writes no `u_waste_rock` row.

### 4.5 Years

Mining and milling rows are written for $1950\le y\le2025$ (v1.1, D64): the activity builder carries `u_production` and `phi_civil` forward from 2024 to 2025 with basis `extrapolated` (§12 item A1), so the 2025 rows carry `; driver basis: extrapolated` (§3.3). Until that change exists the script still runs and 2025 gives one aggregated `no_driver` entry per series; the done conditions that name 2025 are then deferred. The script itself does no extrapolation.

### 4.6 Pre-1950

`u_production` and `phi_civil` start in 1945, but every uranium factor row has `year_from` $\ge 1950$ and $\phi=0$ before 1965. Years 1800–1949 therefore yield no uranium, reactor or reprocessing rows; the script still walks those years through the same code path and logs the absent factors as aggregated `no_factor` runs, so the omission is visible (§8). **(v1.1, D64)** The one non-empty pre-1950 family is civil sea disposal, 1946–49 (§5.3): `data/streams_pre1950/nuclear.csv` holds its liberated half as `flow` rows. It is empty only in a fixture without `nuc_sea_dumped_tbq` or without the extended factor rows (§12 item R1).

---

## 5. Routine transfers (Sealed → Liberated): `conv_enrich_fab`, `reprocessing`, `sea_disposal`

METHODS §5.2 and SCHEMA §3.1: at these three stages a plain Liberated `flow` is forbidden (V15). Every release is a **pair**: `transfer_in` into `liberated` (with the route) and `transfer_out` from `sealed_fuel_cycle`. No `event_id`. Substream `fuel_cycle`, unit `Bq`. Country: `XXX` for `conv_enrich_fab`; the **site country** for `reprocessing`; the **dumping country** for `sea_disposal` (v1.1, §3.1).

### 5.0 The pair

For stage $s$, year $y$ and group $g$ with release rows $\rho\in\mathcal{R}_{s,g}$ (the routes the registry has for $g$ in year $y$):

- one `transfer_in` row per route $\rho$: tier `liberated`, route $\rho$, value $X_{\rho}$ (the applied factor, §5.1–§5.3);
- one `transfer_out` row: tier `sealed_fuel_cycle`, route empty, value $\mathrm{sum\_correlated}(\{X_\rho\})$, with `factor_ids` the union of the routes' factor IDs in order applied.

With one route the `transfer_out` triple equals the `transfer_in` triple. The balance key is (`stage`, `country`, `year`, `group`, `allocation_variant`), so at `reprocessing` and `sea_disposal` each country balances on its own; the pair balances at low, central and high to $10^{-6}$ relative (the script asserts $10^{-9}$ and raises `LibError` otherwise).

### 5.1 `conv_enrich_fab`

- Driver: `elec_gen_nuclear`, `XWL`, year $y$ (TWh), applied to the electricity of the country that burns the fuel (G11).
- Allocation rule `none`. Selection: stage `conv_enrich_fab`, group, tier `liberated`, route, `driver_series="elec_gen_nuclear"`.
- Routes and groups (orientation): `air_stack` — `U238+`, `U234`, `U235+`, `Th230`, `Th232`, `Th228+` (`nuclear:0038`–`0043`, 1950–2025, no era scaling); `water_liquid_effluent` — `U238+`, `U234`, `U235+` in four eras (to 1988; 1989–99; 2000–09; 2010–25: `0044`–`0055`) and `Ra226+` (`0056`–`0059`). So `U238+`, `U234` and `U235+` have two routes and a summed `transfer_out`; `Th230`, `Th232`, `Th228+` have one (air) and `Ra226+` has one (liquid).

### 5.2 `reprocessing`

- **Driver (v1.1): `nuc_reprocessed_gwa` by site country** (civil spent fuel reprocessed, GW·a, electrical-energy equivalent; `research/activity/notes.md` §9.1). For each country $c$ with a row in year $y$ (today `FRA`, `GBR`, `JPN`, `DEU`, `BEL`; the set is read from the file, not listed in the script) the pair of §5.0 is written for country $c$ with driver $G^{\mathrm{rep}}_{c,y}$ (`apply(G, "GWa", factor)`; a `TWh` unit would be converted by the lib). The `XWL` rows of the series are **not** used for rows (they are the sum of the country rows) and serve only the closure check of §2.1. A country-year with a driver of exactly `0/0/0` gives no rows. Country-years with no row are silent (a country that is not reprocessing is not a missing driver). The factor region is `XWL`: `select` is called with `region="XWL"` and the generic rows apply to every site (the UNSCEAR model facility, La Hague-derived; a limit, §10).
- The script uses the series name `nuc_reprocessed_gwa` whatever the registry's `driver_series` cell says (it is empty today and stays so, §12 item R7). If a registry row names a non-empty `driver_series` that differs from the series used here, the script raises `LibError` ("driver mismatch"). `select` is called **without** a `driver_series` key.
- Allocation rule `civil:throughput` (the series is civil by construction; SCHEMA §3.3 rule 4 requires a `civil:` token at this stage; G9). **Civil coverage (D64, D16):** Sellafield B205 (Magnox) is included **from 1995 only** (military feed before); Marcoule UP1, Mayak RT-1, West Valley, India and China remain excluded and are not scaled (§10). The B205 rows are now in the `GBR` series (§12 item A2, done); the script is unaffected either way, because it reads whatever the series holds.
- Selection: stage `reprocessing`, group, tier `liberated`, route. Routes: `air_stack` and `water_liquid_effluent`. Groups (orientation): `C14`, `H3`, `I129`, `Kr85`, `Cs137+`, `I131`, `Co60`, `Cs134`, `Pu239`, `Pu240`, `Ru106+` (air); `C14`, `H3`, `I129`, `Cs137+`, `Ru106+`, `Sr90+`, `Am241`, `Co58`, `Co60`, `Cs134`, `I131`, `Mn54`, `Pu239`, `Pu240` (liquid). The era structure is 1950–69, then 1970–79, 1980–84, 1985–89, 1990–94, 1995–97, 1998–2002 and 2003–2025.
- `I131` air has no 1998–2002 row (UNSCEAR 2008 gave none); that gap is a `no_factor` run, not an error, now logged per country. The `Co60`, `Cs134`, `Pu239`, `Pu240`, `Ru106+` (air) and the `Am241`, `Co58`, `Co60`, `Cs134`, `I131`, `Mn54`, `Pu239`, `Pu240` (liquid) rows exist from 2003 only.
- **Pu D49 rows are used as given.** `Pu239` and `Pu240` (2003–2025) are already split from the combined Pu-239+240 report by the activity ratio 1.59 (Pu-239 share 0.386, Pu-240 share 0.614). The script does **not** re-split, re-sum or apply the group multiplier. The output ratio $\mathrm{Pu240}/\mathrm{Pu239}$ at central equals the factor ratio (a test, §9(f)).

### 5.3 `sea_disposal`

- **Driver (v1.1): `nuc_sea_dumped_tbq` by dumping country** (total activity at packaging, TBq; `research/activity/notes.md` §9.2): `BEL`, `CHE`, `DEU`, `FRA`, `GBR`, `ITA`, `JPN`, `NLD`, `NZL`, `SWE`, `USA`, read from the file. As in §5.2 the `XWL` rows are used for the closure check only, not for rows; a country-year with a driver of exactly `0/0/0` gives no rows; absent country-years are silent. The series excludes the former Soviet Union and Russian Federation (Arctic dumps, mostly naval; Pacific FSU) and the naval reactor shell of USS Seawolf; **US dumps 1946–70 are kept and flagged** (D64): their civil share is undocumented (AEC, Navy and contractor waste; the annual values are spread over site date ranges, basis `interpolated`, band −60 % to +100 %), so the US rows carry the civil-share flag of §3.3. Same driver-mismatch rule as §5.2; `select` without `driver_series`.
- The factors are **shares of dumped activity** (unit `1`, route `sea_disposal_package`, region `XWL`): `H3` 0.344; alpha 0.0149 split over `Pu239`, `Pu240`, `Am241`, `Pu238` (placeholder split); non-tritium beta-gamma 0.641 split equally over `Sr90+`, `Cs134`, `Cs137+`, `Fe55`, `Co58`, `Co60`, `C14`, `I125` (placeholder). The 13 central shares sum to $1\pm10^{-3}$ (premise assertion, §9(i)). **Limit (D64):** the composition shares are derived from the **Atlantic** dump table (IAEA-TECDOC-1105) but are applied to **every** dump, including the Pacific US and Japanese dumps (`research/activity/notes.md` §9.2). The split of activity between nuclides at other sites is unknown; the rows carry this in their `notes` text and in §10.
- **Unit step.** `apply` has no TBq-to-Bq conversion, so the script converts the driver first: if its unit is `TBq`, $D_{\mathrm{Bq}}=D.\mathrm{scale}(10^{12})$ exactly; if `Bq`, no scaling; any other unit raises `LibError`. Then `apply(D_Bq, "Bq", share_row)`; the result unit is `Bq` and the kind is `stock` (a transfer).
- **Years 1950–1993 (master file).** The pair of §5.0 per country and group. Allocation rule `none` (the stage is not a civil-rule stage). One route, so `transfer_out` equals `transfer_in`. Years with a driver value and no factor (after 1993) are `no_factor` runs.
- **Years 1946–49 (pre-1950 file; v1.1, D64).** Driver values for these years (`USA` 1946–49, `GBR` 1949, and any other country row that falls before 1950) are written to `data/streams_pre1950/nuclear.csv` as the **liberated half only**, with the same shares: stage `sea_disposal`, `quantity = flow`, tier `liberated`, route `sea_disposal_package`, substream `fuel_cycle`, country = dumping country, unit `Bq/a` (the value is the activity dumped in the year, $D_{\mathrm{Bq}}\times$ share), allocation rule `none`, no `event_id`, basis `modelled`. There is **no `transfer_out` and no `transfer_in`** in that file (it holds flows only, SCHEMA §3.2). The debit from `sealed_fuel_cycle` is not represented there: the sealed fuel-cycle stock before 1950 is not modelled in the opening stock, so the engine treats these flows as additions to the liberated stock (a limit, §10). SCHEMA `V15` and `X05` are not applied to this file (it is never validated by the master schema), which is what makes a Liberated flow at `sea_disposal` permissible there. The factor rows must be valid from 1946 (§12 item R1). The 1946–49 dumps are USA and GBR rows from `research/activity/notes.md` §9.2 (US rows civil-flagged as above).

---

## 6. `reactor_operation` and `spent_fuel` (substream = reactor type)

For each type $t\in\{\texttt{pwr},\texttt{bwr},\texttt{phwr},\texttt{gcr},\texttt{lwgr},\texttt{fbr}\}$, the driver series are `nuc_gen_<t>` (TWh) and `nuc_cap_<t>` (GW), `XWL`; country of the rows `XXX`; allocation rule `none`; substream $t$. A family with no registry rows for a type is logged once as `no_family`.

### 6.1 Effluents (plain Liberated flows)

- Stage `reactor_operation`, quantity `flow`, tier `liberated`, routes `air_stack` and `water_liquid_effluent`, `driver_series="nuc_gen_<t>"`. Value `apply(G_{t,y}, "TWh", factor)`, unit `Bq/a`.
- Selection: stage, group, tier, route, `driver_series`. Groups per route and type are the registry's (orientation: `pwr` 18 air and 9 liquid groups; `bwr` 19 and 9; `phwr` 18 and 9; `lwgr` 19 and 9; `gcr` 17 and 6; `fbr` 8 and 1). Composition into noble gases, particulates and other liquid is **baked into per-group rows** by the registry (choice 1); the script does not split a total.
- `Kr88+` and `Xe138+` are flow-only released-gas groups; they appear here as `flow` rows only, which is allowed.
- Era steps (1950–79, 1980–89, 1990–2002, 2003–09, 2010–25, and GCR 2010–14 / 2015–25) are real discontinuities in the source data. They are **not smoothed** (coal §12.13). **(v1.2, D65)** The `pwr` and `bwr` **noble-gas air groups** are split at **2014/2015**: the 2010–25 row ends in 2014 (`pwr` `nuclear:0084`, `0089`, … `0114`, seven rows; `bwr` `nuclear:0219`, `0224`, … `0254`, eight rows; all carrying the new low bound and shares with the old central total) and a new 2015–25 row carries the revised central (`pwr` `nuclear:1686`–`1692`, groups `Xe133`, `Xe135`, `Kr85`, `Kr88+`, `Kr87`, `Kr85m`, `Xe138+`; `bwr` `nuclear:1693`–`1700`, groups `Xe138+`, `Xe133`, `Xe135`, `Kr87`, `Kr88+`, `Ar41`, `Kr85m`, `Kr85`). All other PWR/BWR effluent groups keep a single 2010–25 row; the other D65 effluent revisions (N4–N16: noble-gas shares, C-14, H-3, I-131, Co-60, Cs, liquid composition) are **value changes only** on existing rows, with no change of validity window.
- **Selection rule at the era edges (v1.2).** The unchanged call (stage, group, tier, route, `driver_series="nuc_gen_<t>"`, year) yields exactly one row for every (type, group, route, year) in 1950–2025: the windows of a family tile 1950–2025 with no gap and no overlap, and the edges are 2009/2010 and **2014/2015** for the split groups (year 2014 selects the 2010–14 row, 2015 the 2015–25 row). The registry was checked at this edge: no overlap or gap exists for any PWR/BWR liberated effluent family. A premise assertion (§9(i)) repeats the check, so a window left open on both rows (two candidates, `ambiguous factor rows`) or a missing window (`no factor row`, which §3.6 would log as a `no_factor` run and which is therefore a registry error here) fails loudly. The script does not special-case 2014/2015.
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

Rows start in the first year the driver has a value (1956 or 1957 for the LWR types, 1962 for `phwr`, `fbr`; see §2.1), and the factors' `year_from` is 1950 or 1956; both limits are respected. **(v1.1, D64)** The drivers `nuc_gen_<t>` and `nuc_cap_<t>` are carried forward from 2024 to 2025 by the activity builder with basis `extrapolated` (§12 item A1), so 2025 rows exist and carry `; driver basis: extrapolated` (§3.3). Without that change 2025 gives aggregated `no_driver` entries and the 2025 done conditions are deferred. The script does no extrapolation.

---

## 7. Accidents (stage `accident`, event transfers)

### 7.1 Which events

The script reads `data/events.csv` and takes every event with `stream = nuclear`. For each:

- If `stage = accident` **and** the registry has `accident` rows with `tier = liberated` for the event's country and year, the event is an **accident event** and is modelled (§7.2–§7.5). Today these are **E002** (Three Mile Island 2, 1979, `USA`; `events.csv` central $9.25\times10^{16}$ Bq, **high $4.81\times10^{17}$ Bq = 13 MCi, Rogovin TLD, Xe-133 equivalent, D65**; the former NRC-range high of 40 MCi is withdrawn), **E004** (Chernobyl 4, 1986, `SUN`) and **E013** (Fukushima Daiichi 1–3, 2011, `JPN`). The event must have `is_accident = true`, `from_tier = sealed_in_core` and `to_tiers` containing `liberated` and `sealed_damaged_core`; otherwise the script raises `LibError`.
- **(v1.1, D64)** An event with `stage = u_milling` and `event_type = impoundment_failure` is an **impoundment event** and is modelled by §7.6 when the registry has its composition rows. Today this is **E003** (Church Rock, 1979, `USA`). It must have `is_accident = false`, `from_tier = impounded` and `to_tiers` containing `liberated` and `dispersed`; otherwise the script raises `LibError`.
- **E008** (Tokaimura, `stage = accident`, no registry rows) is a **marker only** (D64): `events.csv` carries it for the engine and the page, the script writes no rows, and one `event_not_modelled` log entry is written (detail `marker only`). Any other nuclear event without registry rows is handled the same way.
- The reactor type of an accident event comes from a fixed table in the script: E002 `pwr`, E004 `lwgr`, E013 `bwr`. A modelled accident event not in the table raises `LibError`.
- The event year is the year of `date_start`. A multi-year or continuing release (the Fukushima ocean release) is booked entirely in that year. Timing within the year (mid-year, METHODS §12.2) belongs to the engine.

### 7.2 Inventory $I_g$ and release $R_{g,\rho}$

- **Release rows.** The `accident` registry rows with tier `liberated`, region = the event's country, validity window containing the event year. Selection: stage `accident`, group, tier `liberated`, route (`air_accident_release` or `water_accident_release`), region = event country. Each is turned into `Bounds(low, central, high)` (unit `Bq`). **(v1.2, D65) E002 (TMI-2)** now has five release rows, all `air_accident_release`: `Xe133` (`nuclear:1665`), `Kr88+` (`1703`), `Xe135` (`1704`, including Xe-135m, folded into Xe-135 as its decay daughter), `Xe133m` (`1705`) and `I131` (`1666`). The four noble-gas rows are the Rogovin Table II-1 shares (0.63, 0.15, 0.13, 0.09 of the as-released split) applied to the `events.csv` E002 bounds, so their centrals sum to $9.25\times10^{16}$ Bq; I-131 is added to that ($5.4\times10^{11}$ Bq central, range $10^{11}$–$1.2\times10^{12}$). There is no `Kr85` release row for E002: Kr-85 was not released in significant quantity (Rogovin), and the `events.csv` mention of "some Kr-85" is removed. `Kr88+` is a flow-only group and `Xe133m` has no generic in-core row, so for these two groups there is no inventory: $I=0$, $O=R$, no damaged-core row, and one `no_inventory` entry each (§7.3). `Kr88+` therefore appears as `transfer_in` to `liberated` and `transfer_out` from `sealed_in_core` only, the uses V09 allows.
- **Inventory, event-specific.** If the registry has `accident` rows with tier `sealed_in_core` for the event's country and year (E004: UNSCEAR 2000 Annex J Table 1, `nuclear:1596`–`1629` plus the `Np239` row added under §12 item R5), they give $I_g$ directly (factor notes: use instead of the generic `nuc_cap_lwgr` rows).
- **Inventory, generic (E002, E013; v1.1, D64).** Otherwise $I_g=\texttt{apply}(C_e,\ \texttt{"GW"},\ \text{row})$ with $C_e$ the destroyed units' capacity from the **per-event unit capacity factor row** below, and `row` the generic in-core row of §6.2 selected for stage `reactor_operation`, tier `sealed_in_core`, `driver_series="nuc_cap_<t>"`, year = event year, group $g$.
- **Per-event unit capacity row (the decided form).** One factor row per event in `data/factors/nuclear.csv`:

  | Column | Value |
  |---|---|
  | `stream`, `stage` | `nuclear`, `accident` |
  | `substream` | empty (D63; §2.2) |
  | `driver_series`, `group`, `tier`, `route`, `residue_type` | all empty (SCHEMA §4.9 requires a non-empty `driver_series` to exist in `data/activity/`, so no pseudo-series is used) |
  | `region` | the event's country (E002 `USA`, E013 `JPN`) |
  | `year_from` = `year_to` | the event year (1979, 2011) |
  | `value_low`, `value_central`, `value_high` | the destroyed units' summed net electrical capacity in GW(e); **supplied by the registry, never hard-coded in the script or the tests** (in the registry today: E013 Fukushima 1–3 `nuclear:1668`, 1.959 GW(e), S0106; E002 TMI-2 `nuclear:1669`, 0.880 GW(e) net, range 0.872–0.892, verified against PRIS and Rogovin, S1013, S1017, S0138) |
  | `unit` | `GW` |
  | `basis`, `source_ids`, `notes` | `compiled`; the capacity source; `description` begins with the event ID (for example `E013 unit capacity: …`) |

  **Key.** The row is selected with `select(factors, year=event_year, region=event_country, stage="accident", group=None, tier=None, route=None, residue_type=None, driver_series=None)`. Rows with a group or tier (all release and inventory rows) cannot match, so the capacity row is the only candidate. The registry has no event-ID column, so the key is (event country, event year): two modelled events in one country and year would be `ambiguous factor rows` and raise (none exists today). After selection the script checks that the unit is exactly `GW` and that `description` starts with the event ID, else raises `LibError`. The capacity row's ID is the **first** entry of `factor_ids` of the event's inventory-derived rows (§7.3 item 4).
- **Missing capacity row.** If an accident event needs the generic inventory and the capacity row is absent, the `no factor row` `LibError` propagates (§3.6: a registry error; §12 item R3). There is no deferral and no silent skip.
- The inventory groups are the groups of the inventory source (E004: the Annex J groups; generic events: the type's in-core groups). The release groups are the release rows' groups.

### 7.3 Rows per event and group

For each group $g$ in the union of inventory and release groups, with total release $R_g=\mathrm{sum\_correlated}$ over routes (zero if none) and inventory $I_g$ (exact zero if none):

1. **Damaged-core remainder**, bound by bound ($b\in\{\mathrm{low},\mathrm{central},\mathrm{high}\}$):
$$D_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}}-R_{g,\mathrm{c}},\,0),\quad D_{g,\mathrm{low}}=\min\!\big(\max(I_{g,\mathrm{low}}-R_{g,\mathrm{low}},0),\,D_{g,\mathrm{c}}\big),\quad D_{g,\mathrm{high}}=\max\!\big(\max(I_{g,\mathrm{high}}-R_{g,\mathrm{high}},0),\,D_{g,\mathrm{c}}\big)$$
   This is *not* the independent difference of §3.4: it is bound-wise, so that the transfer balances exactly (SCHEMA §3.3 rule 1).
2. **Rows** (stage `accident`, substream = the event's type, country = event country, `event_id`, allocation `none`, `Bq`):
   - `transfer_in`, tier `liberated`, one per release route: value = the release row's bounds;
   - `transfer_in`, tier `sealed_damaged_core`, residue and route empty: value $D_g$, **omitted if exactly `0/0/0`** (for example Chernobyl Kr-85, where inventory equals release);
   - `transfer_out`, tier `sealed_in_core`: value $O_g$ with $O_{g,b}=R_{g,b}+D_{g,b}$ at each bound, so that $O_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}},R_{g,\mathrm{c}})$ and the pair balances to rounding.
3. **Flags.** A remainder bound clipped from a negative raw value sets `nd_floored` when the resulting low is 0 (cause `clipped_difference`). `release_exceeds_inventory` is logged whenever a *central* raw difference is negative (detail names the group and the excess). A group with a release row but no inventory row has $I=0$: $O=R$, no damaged-core row, and `no_inventory` is logged (no such group exists after §12 item R5 for E004; for E002 (v1.2) it fires for `Kr88+` and `Xe133m`, which have no generic in-core row, and it stays for the generic events). A group with an inventory row and no release row (E004 `La140`, `Nb95`) has $R=0$ and $D=I$: **the whole inventory goes to `sealed_damaged_core`** (D64, §7.5).
4. `factor_ids`: for generic events the capacity factor ID, then the in-core factor ID; for E004 the inventory factor ID; then the release factor IDs, in the order applied. `source_ids`: the union of those factors' sources and the event's `source_ids`.
5. **No `flow` row exists at stage `accident`**, and no row at that stage lacks an `event_id`.

### 7.4 Choice 10 settled: events are the totals, factors the composition (Steve, 2026-10-27)

- `events.csv` is the source of truth for each event's total, date, country, tiers, `is_accident` toggle flag and marker. For **accident events** the script reads the totals only to check the registry (below); it never writes a row from an `events.csv` total. **(v1.1)** The one exception is the impoundment event E003, whose rows are the `events.csv` activity times composition shares from the registry (§7.6).
- **Required sum.** For each modelled accident event, the sum over all release rows $\sum_{g,\rho}R_{g,\rho,\mathrm{central}}$ (Bq, head activity, all routes, the same rows the script writes as `transfer_in` into `liberated`) must equal `activity_central_bq` within a **relative tolerance of $10^{-4}$**. The script raises `LibError` if it does not (the registry and the catalogue are inconsistent), and a done-condition test repeats the check on the output rows (§9(c)). Registry check today: E004 $3.8\times10^{-6}$, E013 $3.3\times10^{-5}$, E002 $5.8\times10^{-6}$ relative (v1.2: the four Rogovin noble-gas rows sum to the `events.csv` central exactly and the I-131 row adds $5.4\times10^{11}$ Bq); the tolerance has a factor 3 margin over the worst case.
- Low and high are **not** required to sum: `events.csv` low and high are scenario bounds (for example E013 low $7.3\times10^{18}$ Bq is Xe-133 only, against a row-sum low of $5.0\times10^{18}$ Bq). **(v1.2)** For E002 the sum check stays on the **central** only: the noble-gas rows are share times the `events.csv` bounds, so their low and high do sum to the `events.csv` low and high, but the I-131 row has its own range and the check does not use it.
- **No accident activity is counted twice.** (1) Accident activity enters the stream only as event transfers carrying an `event_id`, so the "exclude accidents" run (D15) can zero it. (2) Reactor effluents (§6.1) are routine UNSCEAR rates and are not adjusted in an accident year. (3) The in-core baseline (§6.2) is not reduced by the script. (4) Each (event, group, route) appears once. (5) `events.csv` totals are turned into rows only for E003, and there once (§7.6).
- Pre-event: the baseline in-core rows of the destroyed unit continue in the stream (METHODS §5.4); the engine removes them after the accident year in the with-accidents run.

### 7.5 Groups with missing halves (D64)

- **Chernobyl `La140` and `Nb95`** have an inventory row and no release row: the whole inventory goes to `sealed_damaged_core` (`R=0`, `D=I`, §7.3). Confirmed.
- **Chernobyl `Np239`** now has an inventory row: **58,100 PBq central, 27,000 PBq low** (D64; the high bound to be supplied with the row, §12 item R5), which replaces the v1.0 treatment (no inventory, `O=R`). Its release row `nuclear:1648` (central $4\times10^{17}$ Bq) is unchanged, so the damaged-core remainder is $I-R>0$ at central. `no_inventory` is no longer logged for E004. A `release_exceeds_inventory` entry is logged only if a central raw difference is negative (§7.3).

### 7.6 Impoundment event E003 (Church Rock, `u_milling`; v1.1, D64)

Church Rock (16 July 1979, commercial mill, United Nuclear) is an impoundment failure: the tailings dam released acidic mill liquor and solids. It is modelled as a transfer from `impounded` to `liberated` and `dispersed`, with `events.csv` giving the activity and the registry the composition.

- **Activity.** $A_e=\mathrm{Bounds}(\texttt{activity\_low\_bq},\ \texttt{activity\_central\_bq},\ \texttt{activity\_high\_bq})$ from `events.csv` (currently $3.8\times10^{10}$, $1.702\times10^{12}$, $5.106\times10^{12}$ Bq). The catalogue notes that the central value is an **unverified gross alpha** figure (mostly Th-230 and progeny), not a head-activity sum. D64 asks for rows from the event activity, so the script treats $A_e$ as the head-activity total to be split by the composition shares; the limit is carried in §10.
- **Composition rows (to be supplied, §12 item R6).** Factor rows of unit `1`, stream `nuclear`, stage `u_milling`, region `USA`, `year_from` = `year_to` = 1979, `driver_series` and `substream` empty, `residue_type` `u_tailings`, one row per (group, receiving tier, route): tier `liberated` with route `water_spill` (liquor and entrained activity reaching the Puerco River) and tier `dispersed` with route empty (solids spread on the ground and in the river bed). The shares are fractions of $A_e$; the central shares over **all** rows sum to $1\pm10^{-4}$ (premise assertion, §9(i)). Each `description` begins with `E003`. Groups are those of the tailings family F6 where the registry supplies them (`Th230`, `Ra226+`, `Pb210+`, `Po210`, `U238+`, `U234`, `U235+`, `Pa231`, `Ac227+`). Selection: stage `u_milling`, group, tier, route, `residue_type="u_tailings"`, region `USA`, event year, `driver_series=None`; the unit must be exactly `1`.
- **Rows** (stage `u_milling`, substream `fuel_cycle`, country `USA`, `event_id` `E003`, allocation rule `civil:doc` — the event's own `military = false` is the documented civil end use, so this is the one legitimate use of that token — `Bq`):
  - `transfer_in` per receiving row: value $\mathrm{product}(A_e,\ \text{share})$; tier `liberated` (route `water_spill`) or `dispersed` (residue `u_tailings`, route empty);
  - `transfer_out`, tier `impounded`, residue `u_tailings`, route empty, per group: value `sum_correlated` of that group's `transfer_in` rows, so the pair balances at all three bounds (SCHEMA §3.3 rule 1). The tiers satisfy SCHEMA X05 (`from_tier = impounded`, `to_tiers` ∋ `liberated`, `dispersed`).
  - `factor_ids`: the share factors, in order applied; `source_ids`: the factors' sources and the event's.
- **Check.** Over all `transfer_in` rows the central sum equals `activity_central_bq` within relative $10^{-4}$, else `LibError` (the same rule as §7.4; it tests the shares sum to 1). Low and high are products of bounds and are not required to sum.
- **Not double counted.** The baseline tailings rows (F6, `impounded`) are a `flow` into the tier and are not reduced by the script; removing the released part from the impounded stock after the event year belongs to the engine.
- **Gaps.** Radon from the spilled solids and the long-term fate of the river-bed activity are engine processes, not rows.

---

## 8. Log

`BuildResult.log` is a list of dicts with keys `kind`, `year`, `country`, `group` (may be empty) and `detail`. Kinds:

| Kind | When |
|---|---|
| `no_factor` | a `select` failed with `no factor row` (§3.6). **Aggregated**: one entry per contiguous year run per (stage, family/route, country, group); `year` = the first year, `detail` = `first-last (n years)` |
| `no_driver` | a driver series has no value for a year (including the whole run when `nuc_reprocessed_gwa` or `nuc_sea_dumped_tbq` is absent, or a 2025 not yet carried forward, §12 item A1). **Aggregated** as `no_factor`, per (series, country). Not written for the country-level series of §5.2 and §5.3 in years where a country has no row |
| `no_family` | a family has no registry rows at all (`fbr` in-core and spent fuel); once per build |
| `negative_residual` | §4.2; one entry per year |
| `predecessor_dropped` | §3.5 |
| `event_not_modelled` | §7.1 (E008 and any other nuclear event without registry rows; detail `marker only`). Not written for E002, E003, E004 or E013 |
| `no_inventory` | §7.3 (a release group with no inventory row; today E002 `Kr88+` and `Xe133m`, v1.2) |
| `release_exceeds_inventory` | §7.3 |
| `lib_warning` | §3.7; one per build |

Aggregated entries carry the output-row country convention (`XXX` for world series, otherwise the country code; the site or dumping country for §5.2 and §5.3). Country-years absent from `u_production` are silent (a country that is not producing is not a missing driver); only years in which neither a country list nor `XWL` has a value are logged. The CLI prints counts by kind and, with `--write`, writes the full log to `research/nuclear/build_log.csv`.

---

## 9. Done conditions and tests

Tests read factor and activity values from the files (never hard-coded), with explicit **premise assertions** (§9(i)) so that a changed registry fails loudly instead of passing silently.

- **(a) Schema.** `data/streams/nuclear.csv` passes `python -m pipeline.validate --root .`: no tier or route outside the stage's matrix (V03), no V15 on `conv_enrich_fab`, `reprocessing` or `sea_disposal`, no V09 on `Kr88+`/`Xe138+`, X02 transfers balance, X04 civil tokens on `u_mining_conv`, `u_mining_isl`, `u_milling` and `reprocessing` rows, X05 event tiers legitimate, R02 civil year rules (`civil:pre1965` only for $y\le1964$ with `value_high = 0`; `civil:ratio` only for $y\ge1965$); **(v1.2)** the memo rows (`memo_earth_moved` at `u_mining_conv`, `flow`, never `opening_stock`) pass the tier matrix and X04/R02, and are outside the tier totals.
- **(b) Candidate nuclides and coverage** (METHODS §4.3 ①). For each family in §4–§7 and each year $y$ with a driver value and a registry row valid in $y$, a row exists for every (group, route) of the family. The test enumerates the registry; a missing row without a matching `no_factor` or `no_driver` log run is a failure. Group coverage is also checked against the METHODS §4.3 list: mining and milling (`U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Pa231`, `Ac227+`, `Rn222+`) each appear in some 2010 row; effluent and reprocessing groups (`H3`, `C14`, `I129`, `I131`, `Cs137+`, `Cs134`, `Sr90+`, `Co60`, `Co58`, `Mn54`, `Ru106+`, `Pu239`, `Pu240`, `Am241`, and the noble gases) appear in the 2010 flows; `Sb125+` and `Tc99` appear in the 2010 spent-fuel flows and standing inventory. **(v1.2)** The memo family is checked separately: for every year 1950–1988 with a USA `u_production` value, one row per each of the seven groups (273 rows); none for any other country; none after 1988 (the 1989–2025 `no_factor` runs are present in the log). Listed groups **absent from the registry** are reported, not failed: the accident list's `La140` and `Nb95` have inventory but no release row (§7.5, §10). Reprocessing and sea-disposal coverage is checked per country row of the driver.
- **(c) Conservation and events.**
  1. *Transfer balance.* For every balance key (§3.1, SCHEMA) the `transfer_out` equals the sum of the `transfer_in` rows at low, central and high (relative $10^{-6}$). Includes the two-route case (`U238+` at `conv_enrich_fab`, 2010) and the one-route case.
  2. *Event totals (choice 10).* For each modelled event, the output `transfer_in` rows into `liberated` sum (central, Bq, all groups and routes) to `activity_central_bq` of `events.csv` within relative $10^{-4}$. Run for E002, E004, E013 and (with its own tolerance rule, §7.6) E003.
  3. *Remainder.* Per accident event and group: $O_{g,\mathrm{c}}=R_{g,\mathrm{c}}+D_{g,\mathrm{c}}$; $O_{g,\mathrm{c}}\ge I_{g,\mathrm{c}}$; $D_{g,\mathrm{c}}=\max(I_{g,\mathrm{c}}-R_{g,\mathrm{c}},0)$; E004 `Kr85` has no damaged-core row; E004 `La140` and `Nb95` have `transfer_out` = inventory and the whole inventory as damaged-core remainder; E004 `Np239` has a damaged-core row equal to $I-R$ (central $\approx5.77\times10^{19}$ Bq, read from the registry, not hard-coded). For E002 and E013 the inventory test recomputes $I_g=C_e\times$ in-core factor from the capacity row and the §6.2 rows.
   3a. *TMI-2 (v1.2).* E002 has release `transfer_in` rows for exactly `Xe133`, `Kr88+`, `Xe135`, `Xe133m` and `I131` (all `air_accident_release`) and no `Kr85` row; the five-group central sum matches `events.csv` within $10^{-4}$; the four noble-gas centrals sum to the `events.csv` central; `Kr88+` and `Xe133m` have `transfer_out` equal to the release and no damaged-core row, with one `no_inventory` entry each.
   3b. *Church Rock.* For each E003 group the `transfer_out` (`impounded`) equals the sum of its `transfer_in` rows (`liberated` and `dispersed`) at all three bounds; each `transfer_in` central equals the `events.csv` central times the share; all shares sum to 1 within $10^{-4}$; every E003 row has `event_id` `E003`, `civil:doc`, country `USA`, stage `u_milling`.
  4. *No double counting.* No `flow` row at stage `accident`; every accident-stage row has an `event_id`; no row with an `event_id` outside the accident stage **except the E003 rows at `u_milling`**; (event, group, route, quantity, tier) unique; the 2011 `reactor_operation` effluent rows equal driver × factor recomputed from the files (no accident adjustment).
  4b. *Overburden memo (v1.2).* Each memo row equals $T^{\mathrm{conv}}_{\mathrm{USA},y}\times$ factor recomputed from the files, with $T^{\mathrm{conv}}=P\times(1-s)\times\phi$; rows for $y\le1964$ are `0/0/0` with rule `civil:pre1965` and `value_high = 0`; rows for $1965\le y\le1988$ have `civil:ratio`; the memo rows are not counted in any tier total.
  5. *Tonnage partition.* For every uranium country-year at central: $T^{\mathrm{conv}}+T^{\mathrm{isl}}=T^{\mathrm{all}}$ (to $10^{-9}$ relative), checked through F1 + F2-derived tonnage ($\text{row}/\text{factor}$) where the factors are positive.
  6. *Mill balance.* For $y$ with $\phi>0$ and a conventional country: F5 `U238+` : F6 `U238+` residual $=R:(1-R)$ with $R=0.95$, i.e. tailings residual / product $=0.0526$ times $T^{\mathrm{conv}}/T^{\mathrm{all}}$ (premise: `nuclear:0012`, `0021`).
- **(d) Determinism.** Two builds write byte-identical files (all three); row order is the SCHEMA key order; the log order is stable.
- **(e) Benchmarks (D51).** Two years, **2010 and 2020**. Denominators: $W_y=\texttt{elec\_gen\_nuclear}_{\mathrm{XWL},y}/8.766$ GW·a; $W_{t,y}=\texttt{nuc\_gen\_}t/8.766$. Quantities are summed from output rows (central, Bq) and expressed in TBq per GW·a. A value passes when $\tfrac13\le x/x_{\mathrm{ref}}\le3$. The Annex B table is the first estimate; a second, **independent** estimate is required per quantity where one exists.

  **First estimate: UNSCEAR 2016 Annex B, 2010 (S0001; tests read the values from `research/unscear_extraction.csv`, rows `U…`).** The reference values are those of 2010; the same values are used for 2020. **(v1.2, D65)** The stream's 2010–25 factors are no longer the plain UNSCEAR 2010 values for the PWR/BWR effluent rows: the US-based revisions N1–N16 (`factors_notes.md` §10.2) changed centrals on those rows, and from 2015 the PWR and BWR noble-gas centrals are lower (stream sums, central, TBq per GW·a: PWR noble gases 5.80 in 2010 and 1.50 in 2020, against 5.8; BWR 18.0 and 8.5, against 18). Tests read the stream values from the output; the pass/fail rule is unchanged (factor 3). On that basis three comparisons fall outside a factor of 3 and are **documented known misses, not test failures, pending Steve's confirmation**: PWR noble gases in 2020 (ratio 0.26) and PWR `I131` air in both years ($10^{-5}$ against $8\times10^{-5}$ TBq per GW·a, ratio 0.125; N10). The other comparisons pass (PWR `H3` air 2.2 against 1.5, `H3` liquid 23 against 18, `C14` 0.17 against 0.083; BWR noble gases 8.5 against 18, `H3` air 1.7, `H3` liquid 0.82, `C14` 0.30, `I131` $2\times10^{-4}$ against 1.3, 0.82, 0.13, $4.2\times10^{-4}$). The UNSCEAR-population caveat applies: the Annex B values are world means and the revisions rest on one low-effluent fleet (the US).

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

  The reprocessing per-GW·a comparison tests the unit chain (the stream value divided by $G^{\mathrm{rep}}_{c,y}$ equals the registry value, per site country) and is therefore partly circular. It is run now that `nuc_reprocessed_gwa` exists (the series is read by country, §5.2).

  **Second, independent estimate, per quantity.** "Independent" means independent of UNSCEAR Annex B 2016 and of the registry's own derivation. Where several independent values are given, the stream central must lie within a factor of 3 of **at least one** of them (coal §12.17). "Lie between" is an alternative pass, not a requirement.

  | Quantity | Independent value | Source | Status |
  |---|---|---|---|
  | Mine radon (F1) | none | — | **No independent value exists** in the research notes. The 1982/88 (70 TBq/GW·a), 1993 (300 GBq/t), 2000 and 2016 values are all UNSCEAR (earlier editions; family cross-check only). Excluded from the independent test and documented (§10) |
  | ISL radon (F2), mill radon (F3), mill dust (F4) | none | — | No independent value exists (UNSCEAR 2016 itself says the ISL value is assumed equal to milling and inconclusive). Excluded and documented |
  | Reactor `H3` air, `PWR` and `BWR` | 1.2 and 1.4 TBq per reactor-year | US 2021 medians, NUREG/CR-2907 Vol. 27 (S0121) | Per reactor; a US reactor-year is taken as 1 GW·a (the factor notes' own comparison; state this in the test). Required to pass |
  | Reactor `H3` liquid, `PWR` | 19.9 TBq per reactor-year | S0121 | Required to pass |
  | Reactor `C14`, `PWR` and `BWR` | 0.34 and 0.57 TBq per reactor-year | S0121 | **(v1.2)** After N6/N7 the stream (0.17, 0.30) is 2.0 and 1.9 times lower, inside a factor of 3: now a **required pass** (it was a known miss at 0.083 and 0.13) |
  | Reactor noble gases, `BWR` | 0.18 TBq per reactor-year | S0121 | The stream (18 in 2010, 8.5 in 2020) is about 100 and 47 times higher: **known miss**. **(v1.2)** N1 raised the BWR noble-gas low total to $7.8\times10^{11}$ Bq (0.78 TBq per GW·a), so the independent value now lies **below** the row-sum low and the former band test fails: no test is run on this quantity (documented) |
  | Reactor `H3` liquid, all types, absolute (regional lower bound) | 2,800 TBq/a OSPAR nuclear power plants, 2010 and 2020 | OSPAR 2023 (S0122), `research/nuclear/ospar_liquid_discharges_1989_2023.csv` | North-west Europe only. The global stream sum must be $\ge$ the OSPAR value and at most 10 times it |
  | `PHWR`, `LWGR`, `GCR`, `FBR` effluents | none | — | CNSC Appendix H (S0127) was not read; no independent value. Excluded and documented |
  | Reprocessing, absolute `H3` liquid | 11,000 TBq/a (2010), 12,000 TBq/a (2020) | OSPAR (S0122), reprocessing tritium | Stream value $=211\ \text{TBq/GW·a}\times\sum_{c\in\{\texttt{FRA},\texttt{GBR}\}}G^{\mathrm{rep}}_{c,y}$ (country rows, not `XWL`); the OSPAR values imply about 52 and 57 GW·a. Required (the series exists). OSPAR covers the UK and France only. The GBR rows change when Sellafield B205 is added from 1995 (§12 item A2): the test reads the series as it stands and its premise assertion records the GBR coverage |
  | Reprocessing `Kr85` per GW·a | 6,900 TBq/GW·a (1995–97) | UNSCEAR 2000 Table 41 | Earlier edition of the same family: **not independent**; recorded as a cross-check |
  | In-core inventory, `BWR` `Cs137+`, `I131` | 345 and 2,960 PBq per GW(e) | Fukushima 1–3, 2,028 MW(e), 700 and 6,000 PBq (S0106) | Independent. Stream 2010 and 2020 (1999–2025 era): 338 and 3,018 PBq/GW. Required to pass |
  | In-core inventory, `LWGR` `Cs137+`, `Sr90+`, `I131` | 260, 220 and 3,200 PBq per RBMK-1000 (1 GW(e)) | UNSCEAR 2000 Annex J (S0104) | Independent of the generic rows. Stream: 252, 191 and 3,166 PBq/GW. Required to pass |
  | In-core inventory, `PWR`, `PHWR`, `GCR` | none | — | No independent value. The producer's own Carter-versus-ENDF cross-check (4 % apart) is internal. Excluded and documented |
  | Spent-fuel arisings | none | — | UNSCEAR Annex B has no quantity; the Carter (S0100) and ENDF/B-VIII.0 (S0141) routes are both the producer's own. Excluded and documented |
  | Conversion, enrichment, fabrication | none | — | Annex B has no release factor (the registry uses UNSCEAR 1988). OSPAR fabrication-and-enrichment alpha (0.021 and 0.011 TBq/a, 2010 and 2020) calibrated the registry's aquatic scaling, so it is **not independent**. Diagnostic only: the stream's global alpha sum (about 0.0055 and 0.0053 TBq/a, indicative) is below the north-west-Europe total |
  | Sea disposal | 85,078 TBq total, 1946–93 (the series total is 44,602 TBq: naval and Arctic dumps excluded) | IAEA-TECDOC-1105 (S0103) | The driver series comes from this source: not independent. Closure check only: the sum of the stream's liberated rows (1946–93, master plus pre-1950 file) equals the series total |

  **Indicative stream values** (spec author's own central-value arithmetic from the files, no bounds; *not* test expectations): $W_{2010}=311.0$, $W_{2020}=302.1$ GW·a; tonnage 172 and 158 t U/GW·a; F1 27.7 and 20.7 TBq/GW·a (ratio to 66: 0.42 and **0.31**); F2 1.2 and 1.2; F3 2.3 and 2.2; F4 `U238+` 3.1×10⁻⁴ and 2.9×10⁻⁴. **F1 in 2020 falls outside a factor of 3 of Annex B on the plain per-GW·a basis** because UNSCEAR assumes 220 t U/GW·a all mined conventionally while the stream has 158 t U/GW·a and about 57 % ISL (D64, §11 item 4). **Decided (D64):** the F1 pass/fail test is on the Annex B-equivalent per-tonne basis: Annex B radon per t U $=66/220=0.30$ TBq per t U conventionally mined (U0021/U0032) against the stream's F1 $/\,T^{\mathrm{conv}}$; the plain per-GW·a ratio is reported for both years and the 2020 shortfall on that basis is a documented known miss (not a test failure).
- **(f) Hand-computed cases.** At least twelve rows of one year (2010, plus the cases that need another year) are recomputed independently from the factor and activity values, including: an F1 row for a country with its own ISL share (`KAZ`: 3 % conventional, low bound flagged `floor_dominance`); an F1 row for `CAN` using the `XWL` ISL default, and `AUS` 2020 taking `nuclear:1702` (the known-understated default, §4.1); a pre-1965 zero row (`civil:pre1965`, `value_high = 0`) and a 1965 row (`civil:ratio`); a rest-of-world residual row (2020: 131 t U); an F6 tailings row (conventional tonnage only); an F5 product row; a `conv_enrich_fab` pair with two routes (`U238+`, 2010) and one with a single route (`Th230`); a `reactor_operation` PWR noble-gas flow showing the TWh→GW·a conversion, and the same group in 2014 and 2015 (`nuclear:0084` against `1686`, the era edge, §6.1); an overburden memo row (`Ra226+`, `USA`, 1975, `civil:ratio`) and a 1960 memo row (`civil:pre1965`, `0/0/0`); a PWR standing-inventory row (`Bq/GW` × `GW`); a spent-fuel row; a reprocessing `Pu239`/`Pu240` pair showing the ratio is not re-split (2010); and for E004 one released-and-retained group, one `Kr85` with no damaged-core row, `Np239` with its added inventory and damaged-core remainder, `La140` with no release row, and the `Cs137+` damaged remainder; for E002 or E013 one generic-inventory group computed as capacity row × in-core row; one E003 pair (`Th230` or the largest-share group); one reprocessing pair for a site country (for example `FRA`, 2010) showing the country code on the row; one sea-disposal pair for a country (for example `BEL`, 1970) and one US row (flag text in `notes`); one 1946–49 pre-1950 sea-disposal flow row.
- **(g) Fixture tests** on a miniature tree in `tmp_path` that copies the full real factor file and events file and shrinks only the activity files: the negative-residual rule; the rest-of-world zero residual; CSK/CZE `predecessor_dropped`; a missing driver year (aggregated `no_driver` run); the real `I131` reprocessing gap as a `no_factor` run (when `nuc_reprocessed_gwa` is supplied in the fixture); duplicate activity rows raise `LibError`; an ambiguous factor (duplicated registry row) propagates; an absent `nuc_reprocessed_gwa` or `nuc_sea_dumped_tbq` gives one aggregated `no_driver` and no exception; the `XWL` closure check of §2.1 raises when a country row is altered; an accident event with no capacity row raises `no factor row`; two capacity rows for one country and year raise (`ambiguous factor rows`); a capacity row whose unit is not `GW` or whose description lacks the event ID raises; an E003 whose shares sum to 0.9 raises; E008 gives no rows and one `event_not_modelled` entry; the `TBq` driver is scaled by $10^{12}$; a wrong driver unit raises; a driver-series mismatch in the registry raises; an event whose registry sum differs from `events.csv` by more than $10^{-4}$ raises; release above inventory logs `release_exceeds_inventory` and keeps the pair balanced; an ISL share with high above 1 raises.
- **(h) Pre-1950 file.** (v1.1) Non-empty once the 1946 factor extension exists (§12 item R1): only the sea-disposal rows of §5.3 for 1946–49, with `quantity = flow`, tier `liberated`, route `sea_disposal_package`, no `memo_*` tier, no `transfer_*` rows, years 1946–49 only, and each passes `schema/master.json` with the `year` bounds relaxed. Their values equal driver × share recomputed from the files. It is produced by the same code path as the post-1950 rows. Without the extension (a fixture) the file is header-only.
- **(i) Premise assertions.** Before comparing any value, a test asserts the registry premises it uses, failing with a message that names the changed premise: for example `nuclear:0002` unit `Bq/t` and central $3\times10^{11}$ valid in 2010; `nuclear:0004` and `nuclear:0003` both present; the 13 sea-disposal central shares sum to $1\pm10^{-3}$; `nuclear:1565` is $4.734\times10^{15}$ Bq/GW·a, equal to $1.5\times10^{8}$ Bq/s $\times3.156\times10^{7}$ s (UNSCEAR 2016 Table 13, `Kr85`, La Hague, 47 GW·a); the Pu-240/Pu-239 central ratio of the 2003–25 reprocessing rows is $1.59\pm0.01$; the registry's release sums for E002/E004/E013 equal `activity_central_bq` within $10^{-4}$ (E002 over its five groups, v1.2); the `events.csv` E002 high is $4.81\times10^{17}$ Bq; for every PWR/BWR liberated effluent (group, route) the validity windows tile 1950–2025 with no gap and no overlap, including the edge 2014/2015 (v1.2, §6.1); the `XWL` ISL rows `0024`, `0025`, `0026`, `1701`, `1702` tile 1950–2025 without gap or overlap, and so do the `KAZ`, `UZB` and `USA` rows; the 21 memo rows have region `USA`, tier `memo_earth_moved`, unit `Bq/t`, eras 1950–68, 1969–78, 1979–88; `nuclear:1706` does not exist (D67); no registry row has `below_detection` true; every nuclear registry `substream` cell is empty (§2.2); the capacity rows exist for E002 and E013, have unit `GW`, one row per (country, year), `description` starting with the event ID; the E003 composition shares sum to $1\pm10^{-4}$; the sea-disposal share rows are valid from 1946; the `XWL` rows of the two country-level series equal the sum of their country rows (§2.1); the E004 `Np239` inventory row exists.
- **(j) CLI.** Without `--write` the CLI compares both master outputs **and** `research/nuclear/build_log.csv` with a fresh build and exits non-zero if any differs; with `--write` all three are written.

## 10. Known limits carried onto the rows (not hidden)

- **UNSCEAR 2016 Table 13 units.** The block headed "TBq/(GW a)" is in fact Bq/s per GW·a. Check: La Hague Kr-85 $7.1\times10^{9}$ Bq/s divided by $1.5\times10^{8}$ gives the 47 GW·a normalisation, and $1.5\times10^{8}\times3.156\times10^{7}/10^{12}=4{,}734$ TBq/GW·a, which is factor `nuclear:1565`. The extraction file already carries the unit "Bq/s per GW a" (U0140–U0162). Any benchmark that reads Table 13 must convert.
- Hard era steps in the effluent, in-core and reprocessing series (1950–69, 1970–79, 1980–84, 1985–89, 1990–94, 1995–97, 1998–2002, 2003–09, 2010–25) are real source discontinuities, not smoothed. The 2010 UNSCEAR values are carried unchanged to 2025; the GCR series has a step at 2010 and 2015 (G13).
- The composition shares that split UNSCEAR's mixed categories (noble gases, particulates, other liquid) into per-group rows are judgement (about 400 rows). The PWR/BWR noble-gas 2010–14 central is the UNSCEAR mean; from 2015 (D65, N2/N3) it is 1.5 and 8.5 TBq per GW·a, still far above the US 2021 median per reactor (BWR 0.18 TBq), and the high bound of both eras is the old UNSCEAR-based high (9.8 and 5.2 times the new 2015–25 central), so the band is wide. The N1–N16 revisions rest on one low-effluent fleet (the US, NUREG/CR-2907 v27), while the UNSCEAR centrals they sit beside are world means.
- Reprocessing throughput is an implied or new series; 1998–2002 factors use an implied 62.6 GW·a/a from Kr-85. Marcoule UP1 and Mayak RT-1 civil fractions are not available (G9); their discharges are excluded, not scaled. Sellafield B205 is included from 1995 only (D64; in the activity series, §12 item A2), so reprocessed throughput before 1995 omits Magnox and sits far below UNSCEAR world totals. The generic reprocessing factors (La Hague-derived) are applied to every site country.
- Sea disposal is placeholder-split (alpha and beta-gamma shares). **The composition shares are derived from the Atlantic dump table but applied to all dumps**, including the Pacific US and Japanese dumps (D64). Soviet/Russian Arctic and Pacific dumps are excluded as naval or of undocumented civil share; US dumps (1946–70) are included with an undocumented civil share and flagged in `notes`; the US annual values are spread over site date ranges (basis `interpolated`, band −60 % to +100 %). Dumps before 1950 enter only as liberated flows with no debit from the sealed fuel-cycle stock (§5.3).
- Mine radon, ISL radon, mill radon and dust have **no independent estimate**; F1 in 2020 misses Annex B on the per-GW·a basis, a documented known miss (§9(e), D64).
- Conventional-only tailings; the ISL pond residue, mine water, above-threshold waste rock, dispersed tailings fill, operational LLW, decommissioning and construction have no rows (G7, G10); the below-threshold overburden has a **memo series for the USA only, 1950–88** (§4.4, `nuclear:1707`–`1727`), and no memo rows exist for other countries or after 1988 (no EPA tonnage). Because the civil rule applies to it ($T^{\mathrm{conv}}$ with $1-s$ and $\phi_{\mathrm{civil}}$), it is zero for 1950–64 and reduced by the ISL share afterwards, so it understates total US uranium earth moved; its bounds combine the 185–7,400 Bq/kg concentration range with a factor 1.25 on tonnage; `decommissioning` and `construction` stages are empty.
- Reactor types without rows: `htgr` and `other` have activity series but no factors; `fbr` has effluents (air: `Ar41`, `C14`, `H3`, `I131`, `Kr85`, `Kr88+`, `Xe133`, `Xe135`; liquid: `H3`) but no in-core or spent-fuel rows. PHWR, LWGR, GCR in-core and spent-fuel rows are fission products only (G3).
- Conversion, enrichment and fabrication use a 1980–85 UNSCEAR model facility, applied to the burner's electricity; aquatic rows are scaled by an OSPAR trend (north-west Europe only); the stream's alpha sum is below the OSPAR regional total.
- The `transfer_out` of a two-route routine transfer is the **correlated** sum of its `transfer_in` rows (needed for the SCHEMA balance rule); this is wider than an independent sum.
- Accidents: `La140` and `Nb95` have inventory but no release row, so their damaged-core remainder equals the whole inventory; Chernobyl `Np239` has the 58,100 PBq inventory (low 27,000 PBq) of D64; Fukushima `Cs134` (ocean) is missing (G12). E002 rests on Rogovin (S0138; the Table II-1 split was adopted in D65): five release groups (`Xe133`, `Kr88+`, `Xe135` including Xe-135m, `Xe133m`, `I131`), no `Kr85`, `events.csv` high 13 MCi (the NRC 1–40 MCi range and the consultants' about 10 MCi are in the notes only); the Table II-1 exponents come from OCR text and were not eyeballed against the printed page (p. 344). `Kr88+` and `Xe133m` have no in-core inventory (`no_inventory`). The TMI-2 unit capacity is 0.880 GW(e) net (nuclear:1669, verified against Rogovin and PRIS). E008 Tokaimura is a marker only (no rows). E003 Church Rock: the `events.csv` activity (46 Ci) is an unverified gross-alpha figure including progeny, not a head-activity sum, and is split by judgement composition shares; the rows are order-of-magnitude. The 46 Ci matches 3.56e8 L of liquor × the river gross-alpha peak, so it most likely describes the liquor, not the solids as the events.csv note says (to be checked).
- **Excluded military sources (v1.2, D67).** The Grand Junction tailings fill (1950–66) is excluded from the civil record because the Climax mill processed ore for AEC weapons procurement: no row exists (the earlier fill row `nuclear:1706` is removed) and the script writes none. It is listed with the other excluded military events (Windscale 1957, Kyshtym 1957, SL-1 1961, Hanford releases, Chalk River NRX 1952) in METHODS §9.2 and `research/events/notes.md`, not in `events.csv` (whose `military` flag must be false). The other exclusions (Marcoule UP1, Mayak RT-1, Soviet naval and Arctic dumps, the USS Seawolf shell) are in §5.2 and §5.3.
- **CANDU bundle mass (v1.2, D65).** The PHWR spent-fuel arisings (`nuclear:1046`–`1058`) and in-core standing-inventory rows (`nuclear:1407`–`1431`) now assume a bundle of **19.3 kg U** (S1008; 4,560 bundles, 88.0 t U, residence 0.848 a), where 19 kg U was assumed before. This is a **value change only** (every row moves by under 2 %), with no change to groups, windows or selection rules. It treats each group as its head nuclide (chain ingrowth for `Zr95+`, `Ru106+`, `Ce144+` is ignored) and the 37-element bundle; the Pickering 28-element bundle (20.2 kg U) is not separated. PHWR effluent rows do not depend on it.
- **ISL default shares (v1.2, D65).** The `XWL` ISL rows are the rest-of-world default; the 2010–19 value (`nuclear:1701`) is interpolated, not sourced. The default is too low for Australia, Russia and China in 2020–25 (§4.1). The Red Book country-table identification for 2003 was by position.
- Row `basis` is `modelled` everywhere, whatever the factor's own basis; the driver basis (`interpolated`, `extrapolated`) is in `notes` (D64, §11 item 7). Rule 1 of METHODS §9.2 (documented end use) is not implemented for production; the world $\phi_{\mathrm{civil}}$ series is applied to every country and is **accepted as a limit** (D64). Dual-use reprocessing and the US sea-disposal share are handled by the inclusion rules above, not by a country $\phi$.
- The 2025 uranium, `nuc_gen` and `nuc_cap` rows rest on a **2024 carry-forward** (basis `extrapolated`, D64); `conv_enrich_fab` and reprocessing have genuine 2025 drivers. The activity builder change exists (§12 item A1, done), so those 2025 rows are present and carry the driver-basis suffix.

---

## 11. Resolutions (D64)

The thirteen open questions of v1.0 were settled by Steve on 2026-11-02 (D64) as recommended. Each resolution is written into the body section named.

1. **Unit capacity for E002 and E013.** Per-event **unit capacity factor rows** in `data/factors/nuclear.csv` (unit `GW`, stage `accident`, region = event country, `year_from` = `year_to` = event year, one row per event, keyed by country and year with the event ID at the start of `description`; `driver_series` and `substream` empty). Fukushima 1–3 about 1.959 GW(e); TMI-2 about 0.880 GW(e) net, to be verified against Rogovin (S0138); values come from the registry, never from the script (§7.2; §12 items R2, R3).
2. **2025.** The activity builder carries `u_production`, `phi_civil`, `nuc_gen_<t>` and `nuc_cap_<t>` forward from 2024 to 2025, basis `extrapolated`; 2025 rows carry the driver-basis suffix (§4.5, §6.4; §12 item A1).
3. **Tailings tonnage.** Conventional tonnage only (§4.3).
4. **Mine-radon benchmark.** Pass/fail per tonne conventionally mined; the per-GW·a ratio is reported and the 2020 shortfall on that basis is a documented known miss (§9(e), §10).
5. **Exact-zero rows.** Structural `0/0/0` rows (pre-1965 civil share, pre-ISL shares) are written; zero-driver country-years and a zero rest-of-world residual give no rows (§4.1, §5.2, §5.3).
6. **Pre-1950.** The 1946–49 civil sea dumping is written to `data/streams_pre1950/nuclear.csv` as the liberated half, `flow` (§5.3, §4.6; §12 item R1).
7. **Row `basis`.** `modelled` on every row; the driver basis is in `notes` (§3.1, §3.3).
8. **Event tolerance.** Relative $10^{-4}$ on the central release sum; a mismatch raises `LibError` (§7.4).
9. **New series.** `nuc_reprocessed_gwa` (GWa) and `nuc_sea_dumped_tbq` (TBq) are the final names; both exist in `nuclear_cycle.csv` and are read by country (§2.1, §5.2, §5.3). The registry `driver_series` cells stay empty (§12 item R7).
10. **Civil share.** The world $\phi_{\mathrm{civil}}$ is applied to every country and accepted as a limit; `civil:doc` is not emitted on production rows (§4.1, §10).
11. **Accident groups with missing halves.** Chernobyl `La140` and `Nb95` go wholly to `sealed_damaged_core`; `Np239` gets an inventory of 58,100 PBq (low 27,000 PBq) (§7.5; §12 item R5).
12. **`technology`.** Empty on every row (§3.1).
13. **Which events are modelled.** Church Rock (E003) gets rows from `events.csv` activity and registry composition (§7.6; §12 item R6); Tokaimura (E008) is a marker only (§7.1).

Also decided in D64 and written into the body: Sellafield B205 included from 1995 only (§5.2; §12 item A2); US 1946–70 sea dumps kept and flagged (§5.3, §3.3).

**D65 and D67 (Steve, 2026-11-04; v1.2), written into the body:** the overburden memo series is a USA-only `memo_earth_moved` `flow` family with the civil rule applied and no rows after 1988 (§4.4); TMI-2 releases are `Xe133`, `Kr88+`, `Xe135`, `Xe133m`, `I131` with `events.csv` high 13 MCi (§7.2, §7.4); the `XWL` ISL default is the rest of the world in five eras (§4.1); PWR/BWR noble-gas rows split at 2014/2015 (§6.1); CANDU bundle 19.3 kg U (§10); Grand Junction is military and excluded, `nuclear:1706` removed (D67, §10). The earlier resolutions above are unchanged.

---

## 12. Work required before tests

Status at v1.2 (2026-11-04): every registry and activity prerequisite below is **done** except the optional R7. What remains is the stream script `pipeline/streams/nuclear.py` and its tests, which this spec does not provide (the registry now runs `nuclear:0001`–`nuclear:1727`; `nuclear:1706` does not exist, D67). Registry rows were added with empty `substream`, and sources to `data/sources.csv`.

**Registry rows (`data/factors/nuclear.csv`)**

- **R1. Sea-disposal shares from 1946. DONE.** All 13 share rows have `year_from` 1946. Needed for the 1946–49 pre-1950 flows (§5.3).
- **R2. Unit capacity rows. DONE.** E013 `nuclear:1668` (region `JPN`, 2011, 1.959 GW) and E002 `nuclear:1669` (region `USA`, 1979, 0.880 GW net, range 0.872–0.892, verified against PRIS and Rogovin, S1013, S1017, S0138).
- **R3. Registry error if absent. DONE** (consequence of R2): with either row missing, the stream raises (§7.2).
- **R4. Sources. DONE.** S1013 and S1017 (TMI-2) and S1006, S1007 (Red Books), S1250 (EPA 1991), S1260–S1262 (overburden tonnage and period data) are in `data/sources.csv`; every `source_ids` entry must resolve (`T04`).
- **R5. Chernobyl `Np239` inventory. DONE.** `nuclear:1667`, `SUN`, 1986: low $2.7\times10^{19}$, central $5.81\times10^{19}$, high $7.55\times10^{19}$ Bq.
- **R6. Church Rock composition shares (E003). DONE.** `nuclear:1670`–`1685` (16 rows, unit `1`, `liberated`/`water_spill` and `dispersed`); the shares are judgement and must sum to $1\pm10^{-4}$ (§9(i)).
- **R7. `driver_series` cells. NOT DONE, optional.** The cells of the `reprocessing` and `sea_disposal` rows are empty; if filled they must match `nuc_reprocessed_gwa` and `nuc_sea_dumped_tbq` exactly (§5.2). Leaving them empty is valid.
- **R8. Validity to 2025. DONE** (checked at v1.2: every uranium, `reactor_operation`, `spent_fuel`, `conv_enrich_fab` and `reprocessing` family has a row valid in 2025).
- **R9 (v1.2, D65). Revised and new rows. DONE.** ISL shares `0025`, `0026`, `1701`, `1702` and the KAZ/UZB/USA revisions (§4.1); noble-gas rows `1686`–`1700` (§6.1); TMI-2 rows `1665`, `1666`, `1703`–`1705` (§7.2); overburden memo rows `1707`–`1727` (§4.4); value changes N4–N16 and CANDU 19.3 kg U (§10). Grand Junction `1706` removed (D67).

**Activity changes (`data/activity/`, builders under `research/activity/`)**

- **A1. 2024 to 2025 carry-forward. DONE.** `u_production`, `phi_civil`, `nuc_gen_<t>` and `nuc_cap_<t>` run to 2025 with basis `extrapolated`.
- **A2. Sellafield B205 from 1995. DONE.** The `GBR` rows of `nuc_reprocessed_gwa` include B205 from 1995 and `XWL` was updated. The §9(e) tests that use GBR are rerun against the series as it stands. **Open point (v1.2):** the stored values are rounded to six significant digits, and in 24 years the `XWL` central differs from the country sum by up to about $4\times10^{-6}$ relative, which exceeds the $10^{-6}$ tolerance of the §2.1 closure check, so the check as written would raise `LibError` for those years. **Resolved (orchestrator, 2026-11-04):** the §2.1 closure tolerance is $10^{-5}$ relative, because every stored value is rounded to six significant digits (up to $5\times10^{-6}$ per value).
- **A3. Series sources. DONE** (S1600–S1611 are in `data/sources.csv`; `research/activity/notes.md` §9 is out of date on this).

**Contingent:** none. The earlier dependence on R6 for E003 is satisfied.

## 13. v1.2 clarifications after the spec-blind test review (orchestrator, 2026-11-04)

These settle the test-writer's points; where a test already encodes the reading below, it stands.

1. **Transfer balance and rounding (D68).** `transfer_out` is the correlated (linear) sum of its `transfer_in` rows as computed, before writing. The validator's X02 tolerance and the §2.1 closure check are both $10^{-5}$ relative, because files store six significant digits.
2. **Hand-computed cases.** §9(f)'s "KAZ 3 % conventional" and "BEL 1970" are illustrative; the tests use the registry/driver values as they stand (KAZ central ISL 0.99; BEL 1971).
3. **Zero-central complements.** When `1 − ISL share` has central 0 (UZB 2000–25), the product follows the lib zero-central rule `(0, 0, high)`, flagged, cause `zero_central_factor`.
4. **Groups with inventory but no release** (e.g. Kr85 at E002): the whole inventory is the transfer out and goes to `sealed_damaged_core`; no liberated row. **Release without inventory** (I = 0, e.g. Kr88+, Xe133m at E002): log `no_inventory`, write the liberated release with no damaged-core row. `release_exceeds_inventory` is logged only when I > 0 and the central raw difference is negative.
5. **`factor_ids` order.** The ISL-share factor comes first on rows that use it (F1, F2, F6, F7); the family factor comes last. Rows without the ISL factor list only their own factors.
6. **Routes in §9(e).** C14 and I131 PWR/BWR comparisons use route `air_stack`.
7. **Log runs.** A run of `no_factor` / `no_driver` covers consecutive years in which the condition holds; a year in which the driver is exactly 0/0/0 (no rows, no log) ends the run.
8. **Empty select keys** are passed as `""` (LIB_SPEC §10.3), never `None`.
9. **CLI output.** One line per log kind, `log <kind>: <count>`, as the coal CLI prints.
10. **Effluent windows.** The tiling premise applies to PWR and BWR families; other types may start later (e.g. GCR S35 from 2010).
11. **Accident `transfer_in` rows (verification, 2026-11-04).** Liberated `transfer_in` rows list only their release factor(s) in `factor_ids` and those factors' sources; inventory and capacity factors appear on `transfer_out` and damaged-core rows (§7.3 item 4 reads this way). `factor_ids` order on E003 `transfer_out` follows (group, tier, route) sort.
12. **Indicative F1 values** in §9(e) updated to the built stream: 27.7 (2010) and 20.7 (2020) TBq/GW·a; ratios to Annex B 0.42 and 0.31 (the 2020 value a known miss, D64).

