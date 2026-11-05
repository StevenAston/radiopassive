# `pipeline/streams/other.py` — stream script contract (Task 2.5, other energy: geothermal, biomass incl. household biomass, peat, hydro)

Status: v1.1 (2026-11-05), for the test-writer and the code-writer. v1.0 FINAL (2026-11-04): the eleven open questions of the draft were settled by Steve on 2026-11-04 (D70, "defaults as recommended"); the last section records the resolutions, and the body states each as a rule. **v1.1 (D71, approved by Steve 2026-11-05, "as recommended")** settles the spec-defect list A1–A16 of the spec-blind test review (header of `pipeline/tests/streams/test_other.py`): §13.9–§13.19 state the clarifications, and §1, §2.1, §3.1, §3.4, §3.9, §5.1–§5.3, §6.1–§6.3, §8 and §9(f)–(h) were edited to agree. Where §13.9–§13.19 and older text differ, §13.9–§13.19 win. Derived from METHODS §3, §4.3, §5 (incl. §5.2 re-released fallout D43, biosphere memo D44, radon branching), §6.3, §10.3, §11, SCHEMA §3–§5 (v2.4a; vocab tiers `memo_biosphere` D47, route `air_rerelease` D48, substream `biomass_domestic` D45), `docs/LIB_SPEC.md` (v1.4, incl. the mass factor units `t/<driver unit>`, §9, and the `substream` match key, §10), `data/factors/other.csv` (factors `other:0001`–`other:0073` and `other:0075`; `other:0074` does not exist; 74 rows), `research/other/factors_notes.md` (incl. its §8 D65 revisions), `research/other/papers_round2_geothermal.md`, `research/other/papers_round3.md`, the activity files `electricity_generation.csv` (`elec_gen_geothermal`), `biomass.csv` and `peat.csv`, and `docs/DECISIONS.md`. Modelled on `docs/NUCLEAR_SPEC.md` v1.2, with the coal lessons of `docs/COAL_SPEC.md` §11–§12.17 built in from the start (world code `XXX` against factor region `XWL`; row conventions; correlated against independent differences; flag-cause and driver-basis suffixes in `notes`; aggregated log runs; strict `no factor row` handling; duplicate-activity raise; CLI diff covering the log; tests read factor values from the files under explicit premise assertions; benchmarks with independent estimates; known misses documented, not hidden). Peat combustion mirrors the coal ash chain (COAL_SPEC §5–§6) wherever it applies. Where this file and METHODS disagree, METHODS wins and this file is a bug.

Decisions in force: D14 (years from 1950), D22 (industry view), D24 and D42 (head-nuclide activity, all decays counted by the engine), D31 and D57 (pre-1950 file), D37 and D45 (household biomass is substream `biomass_domestic` at stage `biomass_peat`), D43 (re-released fallout Cs-137 is a Liberated flow shown separately), D44 (natural nuclides in wood are a memo, peat stays a flow), D47 (tier `memo_biosphere`), D48 (route `air_rerelease`), D51 (benchmarks), D52 (non-detect flag), D58 (coal v1.2 lessons), D61 (choices 1–9 of `factors_notes.md` §5 and the round-2 geothermal changes), D62 (ε and seepage for `peat_ash` and `geothermal_scale`), D63 (factor `substream` column), D65 (round-2 and round-3 revisions of the `other` registry), D68 (10⁻⁵ tolerance for stored six-digit values), D69 (documented known misses), D70 (the eleven open questions settled; wood, charcoal and peat carried forward to 2025) and D71 (the A1–A16 clarifications, §13.9–§13.19). D43/D44 and D61 choice 6 are the basis of §3.3.

The script is a pure function of the files under `data/`; `research/unscear_extraction.csv` is **not** read by the script (tests read it, §9(e)). It uses only `pipeline.lib` and the standard library plus pandas/numpy if needed. It never reads the network and never decays anything: decay and ingrowth, radon and thoron exhalation from `peat_ash` and `geothermal_scale`, seepage and all memo-series handling belong to the Phase 3 engine (METHODS §5.2). Parallelism, if any, is capped at 2 processes.

---

## 1. Interface

```
python -m pipeline.streams.other [--root PATH] [--write]
```

- Without `--write`, outputs go to a scratch directory and are diffed against the committed files; the exit status is non-zero if **any of the three** files below differs (the build log is part of the diff, COAL_SPEC §12.8).
- With `--write`, the three output files are overwritten.
- `build(root: Path) -> BuildResult` is the importable entry point. `BuildResult` has three attributes: `rows` (master-row dicts, 1950–2025), `rows_pre1950` (master-row dicts, 1800–1949) and `log` (list of dicts, §8). `root` is the repository root, so tests can build a miniature tree in `tmp_path` with the same file names and columns.
- The CLI prints one line per log kind, `log <kind>: <count>`, as the coal and nuclear CLIs do.

| File | Content |
|---|---|
| `data/streams/other.csv` | Master rows, years 1950–2025. Must pass `python -m pipeline.validate --root .` |
| `data/streams_pre1950/other.csv` | Master columns, years 1800–1949, `quantity = flow` only, no `memo_*` tier; outside the master schema (SCHEMA §3.2, D57). Today it holds the **geothermal** rows for 1916–1949 (the electricity series starts in 1916); nothing else is non-empty (wood fuel starts in 1961, peat in 1990). Wood and peat rows **cannot** exist before 1950 by construction: every Cs-137 factor starts in 1950 and those families write memo rows, which this file may not hold (§9(h), §13.17) |
| `research/other/build_log.csv` | The full log (§8). Not a master file and not validated |

Master files are written with `pipeline.lib.rows.write_master` (deterministic, sorted by the SCHEMA §3 key; `write_master([])` writes a header-only file).

## 2. Inputs

### 2.1 Activity series (read with `read_table`; values are `Bounds(value_low, value_central, value_high)`)

| Series | File | Country rows | Years today | Unit | Used for |
|---|---|---|---|---|---|
| `elec_gen_geothermal` | `electricity_generation.csv` | 34 countries and `XWL` | `XWL` 1916–2025 (basis `modelled` to 1979, `compiled`/`measured` after; **2025 `extrapolated`**); country rows start in 1980 (some later) | `TWh` | §4 |
| `peat_power_heat_t` | `peat.csv` | 11 countries, **no `XWL`** | 1990–2025 (former USSR from 1992; ends 2023 for most; **2025 `extrapolated`**, one country, `RWA`) | `t` | §5 (plants) |
| `peat_household_t` | `peat.csv` | 16 countries, no `XWL` | 1990–2025 (**2025 `extrapolated`**, 4 countries) | `t` | §5 (household peat) |
| `peat_supply_t` | `peat.csv` | 29 countries, no `XWL` | 1990–2025 (**2025 `extrapolated`**, 11 countries) | `t` | §5 ("other peat use" residual) |
| `wood_fuel_t` | `biomass.csv` | about 204 countries and `XWL` | 1961–2025 (**2025 `extrapolated`**) | `t` | §6 |
| `household_fuelwood_m3` | `biomass.csv` | about 194 countries and `XWL`; **China is absent** | 1990–2023 (the UNSD source ends in 2023, so there is no 2024 value to carry: **no 2025 row**) | `m3` | §6 (household wood) |
| `charcoal_production_t` | `biomass.csv` | about 199 countries and `XWL` | 1961–2025 (**2025 `extrapolated`**) | `t` | §6 (charcoal chain) |

The 2025 values of the wood, charcoal and peat series are the 2024 central carried forward by the activity builders' common rule (`carry_2025`, D70; basis `extrapolated`, bands widened by the 2024 half-width and the largest year-on-year change in quadrature; exact-zero 2024 values stay exact zeros). Series that exist but are **not read** by the script: `wood_fuel_m3` (also carried to 2025) and `household_charcoal_t` (they appear only as `driver_series` selection keys of `other:0050` and `other:0070`, which the factor registry requires to exist, SCHEMA §4.9), `wood_fuel_energy_twh`, `household_fuelwood_energy_twh`, `household_charcoal_energy_twh`, `peat_production_t`, `peat_production_twh`, `peat_supply_twh`, `elec_gen_biomass`, `elec_gen_hydro`, and the USGS `prod_peat`. `elec_gen_peat` (`XWL`, `TWh`) is a benchmark denominator only (§9(e)); `elec_gen_biomass` and `elec_gen_hydro` are not used at all (biomass and waste, including biogas and MSW, is not a wood or peat tonnage; hydro has no rows, §7).

Facts the rules below rely on (tests assert them as premises, §9(i)): (1) for geothermal, `XWL` equals the sum of the country rows within relative $2.7\times10^{-6}$ in every year 1980–2025, and before 1980 there are no country rows; (2) peat has **no** `XWL` series, so no rest-of-world rows exist for peat; (3) for wood fuel and charcoal, the world-minus-countries residual $(X_{\mathrm{XWL}}-\sum_cX_c)/X_{\mathrm{XWL}}$ at the centre is, from `data/activity/biomass.csv` (checked 2026-11-05, D71): **wood fuel** 3.2–5.2 % in 1961–1992, about 1.0 % (0.98–1.07 %) in 1993–2011, about 0 in 2012–2023 (between $-3.1\times10^{-6}$ and $+3.0\times10^{-6}$, inside the $10^{-5}$ tolerance, so no rest-of-world unit and no `negative_residual`), and 0.32 % in 2024 and 2025 (the carried-forward 2024 residual repeats); **charcoal** 7.0–10.5 % in 1961–1992, 1.7–2.2 % in 1993–2011, about 0 in 2012–2023 (within $\pm1.1\times10^{-6}$) and 0.027 % in 2024 and 2025; (4) the UNSD household series starts in 1990 and ends in 2023, and exceeds the FAOSTAT wood-fuel total for 71 of about 182 countries in 2010 (for example the USA).

All series keys are (`series`, `year`, `country`); a duplicate key raises `LibError` naming it (§3.9). `source_ids` of the activity rows used are collected into the output rows' `source_ids`. A series that is absent from `data/activity/` (in a fixture) gives no rows and one aggregated `no_driver` entry (§8); the script must not raise.

### 2.2 Other inputs

- **Factors** (`data/factors/other.csv`, 74 rows), looked up with `pipeline.lib.factors.select` and applied with `apply` (§3.5).
- **`substream` (D63, LIB_SPEC §10).** The registry's `substream` cell is **empty on every row**: most rows serve both `biomass_peat` and `biomass_domestic`, so one value cannot describe them, and the descriptions carry the substream label in words instead. The script therefore does **not** pass `substream` to `select`. A premise assertion (§9(i)) checks that every `other` registry `substream` cell is empty, so that a later filled cell fails loudly instead of being ignored. The `substream` of the **output rows** is a separate matter (§3.1).
- **Events** (`data/events.csv`) are not read: D32 found no civil other-energy event, and the file holds no `other` row. A premise assertion checks this; the script raises `LibError` if an `other` event appears (this spec has no event rules).
- `data/reference/residue_types.csv` and `groups.csv` are not read by the script (the engine uses them). The residue types `peat_ash` and `geothermal_scale` must exist with ε and seepage filled (D62); the residue types `biomass_ash`, `biomass_domestic_ash` and `geothermal_brine` receive **no** rows (§3.3).
- `data/reference/commodity_factors.csv` does not exist (§7).
- A year with no driver value gives no row for that quantity; that is recorded in the log, not an error.

## 3. Conventions (all rows)

### 3.1 Row columns

| Column | Value |
|---|---|
| `stream` | `other` |
| `substream` | `geothermal` for §4; `biomass_peat` for plant-type peat and plant wood (§5.2, §6); `biomass_domestic` for household peat, household wood and the charcoal chain (§5.3, §6). `hydro` is never written (§7) |
| `stage` | `geothermal` for §4; **`biomass_peat` for both biomass substreams** (D45: no new stage) |
| `quantity`, `unit` | `flow` with unit `master_unit(result_unit(driver_unit, factor_unit), "flow")`, which is `Bq/a`, for every row. No `transfer_*`, `standing_inventory` or `opening_stock` row exists in this stream; masses never appear in master rows (LIB_SPEC §9.4) |
| `basis` | `modelled` for every row (all values are products of factor and driver). The factor's own basis (`compiled`, `extrapolated`) stays in the registry and the **driver** basis goes into `notes` (§3.4) |
| `allocation_variant` | `default`; `allocation_rule` `none` on every row (single-product streams; no civil-rule stage) |
| `embedded_fuel` | `False` |
| `product`, `technology`, `event_id` | empty (resolution 10, D70, for `technology`) |
| `residue_type` | `geothermal_scale` on geothermal scale rows; `peat_ash` on peat ash rows at tiers `impounded` and `dispersed`; empty everywhere else (V-rule: required exactly when tier is `impounded`, `reisolated` or `dispersed`) |
| `route` | on `liberated` rows: `air_vented_gas` (geothermal), `air_stack` (peat natural nuclides), `air_rerelease` (fallout Cs-137 only); empty on every other tier |
| `factor_ids` | every factor used to compute the row, in the order applied (§3.6 for aggregated rows); the exact list per term is §13.13 |
| `source_ids` | union of the factors' `source_ids` and the driver rows' `source_ids`, sorted and de-duplicated; which driver rows count is §13.14 |
| `below_detection` | from the bounds (`nd_floored`), set by `make_row` |
| `notes` | rule text, then suffixes (§3.4) |

**Country rule.** Global series are looked up with country **`XWL`** (activity and factor region) and written with country **`XXX`** (SCHEMA §3, V10). In this stream `XXX` appears in two cases, told apart by `notes` (§3.4): (a) geothermal years before the country series begin (1916–1979), where the whole world aggregate is `XXX`; (b) the rest-of-world residual of §3.5 (geothermal and wood fuel). Rows of a listed country carry that country's code. The factor region passed to `select` is the country code for listed countries (an exact-region row beats `XWL`, §4.2, §6.4) and `XWL` for `XXX` rows.

**Quantities are head-nuclide activity** of the group (METHODS §3.2, D24, D42); the engine applies the group multiplier. `Rn222+` and `Rn220+` are flow-only released-gas groups and appear only as Liberated flows (V09).

### 3.2 Groups, families and the registry

The script never hard-codes a group list. A **family** is a set of registry rows sharing the select keys of the tables in §4–§6. The groups of a family are the distinct `group` values among its registry rows, over all years and regions. For each (country, year) the script calls `select` once per (role, group); the winner is used. A failed `select` is handled by §3.8. The expected group sets are listed for orientation:

| Set | Groups |
|---|---|
| Geothermal gas | `Rn222+`, `Rn220+` |
| Geothermal scale | `Ra226+`, `Ra228+`, `Pb210+`, `Po210`, `K40` (5) |
| Peat natural (11) | `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Th232`, `Ra228+`, `Th228+`, `K40` (`U234` and `Th230` are kept so that Ra-226 stays supported, as in coal) |
| Wood natural memo (5) | `K40`, `Pb210+`, `Po210`, `Ra226+`, `Ra228+` (D44 extended to the two radium groups, D61 choice 5) |
| Fallout | `Cs137+` |

`select` match keys are passed exactly as the registry strings, and an **empty registry cell is matched with `""`** (never `None`; LIB_SPEC §10.3, NUCLEAR_SPEC §13.8). Keys omitted from a table are not passed. **The same `driver_series` string selects different rows for different stages of use** (for example `wood_fuel_t` selects the dry fraction, the memo factors, the Cs-137 concentrations and a stack share), so every call states group, tier, route and residue type explicitly, as the tables give them.

### 3.3 Counted rows, memo rows and re-release rows — the complete table

This table is exhaustive: the script writes **no other row**. "Tier totals" are the stream's tier totals as the engine and page form them (METHODS §6); "cross-stream sums" are sums that add stream ⑤ to streams ①–④.

| # | Substream | Material | Groups | Tier | Route | Residue type | In tier totals | In cross-stream sums |
|---|---|---|---|---|---|---|---|---|
| G1 | `geothermal` | non-condensable gas radon | `Rn222+`, `Rn220+` | `liberated` | `air_vented_gas` | — | yes | yes |
| G2 | `geothermal` | scale and sludge | `Ra226+`, `Ra228+`, `Pb210+`, `Po210`, `K40` | `impounded` | — | `geothermal_scale` | yes | yes |
| P1 | `biomass_peat` | peat natural nuclides to the stack | 11 natural | `liberated` | `air_stack` | — | yes | yes |
| P2 | `biomass_peat` | peat ash | 11 natural | `impounded`, `dispersed` | — | `peat_ash` | yes | yes |
| P3 | `biomass_peat` | **fallout Cs-137 re-emitted to air** (peat plants and other peat use, plus plant wood) | `Cs137+` | `liberated` | **`air_rerelease`** | — | **yes** (the stream's Liberated tier, D61 choice 6) | **no**: shown as a separate series |
| P4 | `biomass_peat` | fallout Cs-137 not released (left in ash) from the same fuels | `Cs137+` | **`memo_biosphere`** | — | — | **no** | **no** |
| P5 | `biomass_peat` | natural nuclides in plant wood (whole burned content; ash and smoke are not split) | 5 wood | **`memo_biosphere`** | — | — | **no** | **no** |
| D1 | `biomass_domestic` | household peat natural nuclides to the chimney | 11 natural | `liberated` | `air_stack` | — | yes | yes |
| D2 | `biomass_domestic` | household peat ash | 11 natural | `impounded`, `dispersed` | — | `peat_ash` | yes | yes |
| D3 | `biomass_domestic` | **fallout Cs-137 re-emitted to air** (household peat, household wood, charcoal kiln and charcoal stove) | `Cs137+` | `liberated` | **`air_rerelease`** | — | **yes** | **no** |
| D4 | `biomass_domestic` | fallout Cs-137 not released (household peat, household wood, charcoal) | `Cs137+` | **`memo_biosphere`** | — | — | **no** | **no** |
| D5 | `biomass_domestic` | natural nuclides in household wood and in charcoal wood (the whole content; **household wood ash is memo for every nuclide**, including the share that is landfilled or spread) | 5 wood | **`memo_biosphere`** | — | — | **no** | **no** |

**Written nowhere:** any `impounded`, `dispersed` or `reisolated` row for wood or charcoal; any `Cs137+` row at tier `impounded` or `dispersed` (peat or wood); any natural-nuclide **flow** row for wood (D44 makes it memo); any wood natural group beyond the five; geothermal `reisolated` rows (brine, G4); any `hydro` or `construction` row (§7); any radon or thoron from peat, peat ash or scale (engine processes, METHODS §5.2; peat radon is about $10^{-5}$ of geothermal, gap G7). The residue types `biomass_ash`, `biomass_domestic_ash` and `geothermal_brine` therefore receive no data rows and need no ε or seepage. The disposal split of household wood ash has no factor and is not needed; the same prior is used only for household peat ash (`other:0041`, `0042`).

**Memo rows** carry no `residue_type`, no `route`, are `flow` only, never `opening_stock`, and are outside every tier total (SCHEMA §3). The decision on **peat**: natural nuclides in peat stay flows (accumulation over $10^{3}$–$10^{4}$ a, D44); **only** fallout Cs-137 on peat is split into re-release (P3, D3) and memo (P4, D4).

**How the `air_rerelease` rows are kept out of cross-stream sums (D48, D61 choice 6).** The script cannot enforce a sum that other code forms, so it makes the rows unmistakable and tests that the marking holds:

1. every re-release row has route `air_rerelease`, stage `biomass_peat`, group `Cs137+`, quantity `flow`, tier `liberated` (the schema conditional of SCHEMA §5.7 restricts the route to exactly this combination), and **its `notes` begin with the text `re-release`** (§3.4);
2. no `Cs137+` Liberated row of this stream has any other route, and no other group has route `air_rerelease`;
3. the **consumer rule** (engine, page, any assembler): a cross-stream total of the Liberated tier is formed from rows with route $\neq$ `air_rerelease`; the re-release rows are drawn as their own series, so the same atoms are not added to the weapons-test baseline or to the accident events of stream ① (METHODS §5.2). The stream's own Liberated total may include them, labelled;
4. §9(c) item 7 tests the marking and the arithmetic of this filter with a reference implementation of the consumer rule.

### 3.4 Flag cause, rule text, components and driver basis in `notes`

- **Rule text** is fixed per family (the second column of the table below). **Every rule text is an exact string** (D71, §13.9): `notes` equals the rule text when nothing is appended, and otherwise begins with the rule text followed immediately by `; ` and the appended texts and suffixes. The last three rows of the table are **appended texts**, each preceded by `; `, in the order of the table (§13.10).

| Family | Rule text |
|---|---|
| Geothermal Rn-222 | `geothermal non-condensable gas radon` |
| Geothermal Rn-220 | `geothermal thoron: Rn-222 flow times Rn-220 ratio` |
| Geothermal scale | `geothermal scale: mass per GW a times activity per tonne` |
| Peat stack, plant type | `peat plant stack release: escape fraction times enrichment, capped at fly ash` |
| Peat ash, plant type | `peat ash route share` |
| Peat chimney, household | `household peat chimney smoke: smoke fraction times enrichment, capped at ash-borne activity` |
| Peat ash, household | `household peat ash route share` |
| Re-release (P3, D3) | **`re-release: fallout Cs-137 in fuel emitted to air by combustion (D43)`** (exact prefix `re-release`) |
| Memo, Cs-137 (P4, D4) | `memo: fallout Cs-137 not released, left in ash (D43)` |
| Memo, natural wood (P5, D5) | `memo: natural nuclides in burned wood, biosphere cycling (D44)` |
| World aggregate (case a of §3.1) | `world aggregate (no country series before 1980)` appended to the rule text of the family |
| Rest-of-world residual (case b) | `rest of world (world aggregate minus listed countries)` appended to the rule text of the family |
| Household share fallback (§6.2) | `household share fallback (other:0050)` appended to the rule text of the rows that depend on it |

- **Components suffix.** Rows of the families that can combine several materials into one key (§3.6) end their rule text (and appended texts) with `; components: <tags>`, a `+`-joined subset in this fixed order, of: for `biomass_peat` rows `peat_plant`, `peat_other`, `wood_plant`; for `biomass_domestic` rows `peat_household`, `wood_household`, `charcoal`. Only tags of terms that contribute (not exactly `0/0/0`) are listed; a zero-central term $(0,0,h)$ contributes and is listed (§13.15). **Every P1–P5 and D3–D5 row carries the suffix, even when it has one tag**; in particular every P5 row reads `; components: wood_plant` (confirmed, D71). Geothermal rows and `biomass_domestic` peat natural rows (D1, D2; single material) carry no components suffix.
- **Below-detection cause.** Every output row with `below_detection = true` ends its `notes` with `; below_detection cause: <causes>`, a `+`-joined subset, in this fixed order, of `zero_central_factor`, `exact_zero`, `clipped_difference`, `floor_dominance`, `inherited_flag`. The script tracks the causes of its own inputs and carries them through products and sums; it does not parse lib log text. Rows with `below_detection = false` carry no cause text.
  - `exact_zero`: a correlated difference (§3.5) whose result is exactly $(0,0,0)$ without any clipping (COAL_SPEC §12.16): its raw central and raw high are exactly 0 and its raw low is $\ge0$. It would stay flagged (D52 zero-central rule), with cause `exact_zero`. In this stream such a remainder **writes no rows** (resolution 8, D70; D71, §13.15): a cap that binds at every bound (§5.2, §5.3, §6.2) leaves an exact `0/0/0` remainder, which is omitted. The cause therefore never appears on a written row here; it is kept in the fixed order for consistency with coal.
  - `clipped_difference`: a difference had a raw low or central below 0 and was clipped; **and also** (D71, §13.15) a correlated difference whose result has central exactly 0 and high $>0$ (a cap that binds at the low and central but not at the high, so the remainder is $(0,0,h)$): such a result is flagged under the D52 zero-central rule with this cause. The cause is carried through every later product, cap, difference and sum. `floor_dominance`: the lib's zero-low floor rule fired in a product with no other cause. `zero_central_factor`: an input factor with central 0 and high $>0$ (none exists in the registry today). `inherited_flag`: an input was flagged and no other cause applies.
  - The registry has no factor with a zero low bound, so in practice only `exact_zero` and `clipped_difference` can occur; the others are kept for completeness and are exercised by fixtures (§9(g)).
- **Driver basis.** If any activity driver row used (the same driver rows that feed `source_ids`, §13.14) has basis `interpolated` or `extrapolated`, the row's `notes` gain `; driver basis: interpolated` (or `extrapolated`, or both joined by `+`). The row's own `basis` stays `modelled`. Today this arises for 2025 only (`extrapolated`): geothermal, and every wood, charcoal and peat row of 2025 (D70); `wood_fuel_t` and `household_fuelwood_m3` are otherwise `compiled`/`modelled`.
- **Suffix order:** rule text, then the appended texts in table order (`; world aggregate …`, `; rest of world …`, `; household share fallback (other:0050)`), then `; components: …`, then `; driver basis: …`, then `; below_detection cause: …` last. The separator is always `; ` (§13.9–§13.10).

### 3.5 Arithmetic rules

- **Applying a factor.** `apply(driver, driver_unit, factor_row)`, with `result_unit` and `master_unit` for the row unit. Factor units in this registry: `Bq/GWa` (driver `TWh`: the lib converts 1 GW·a = 8.766 TWh), `Bq/t` (driver `t`), **`t/GWa` and `t/m3` (LIB_SPEC §9: the result is a mass in `t`)**, and `1` (shares, ratios, fractions). The mass factors go **through `apply`**: `apply(G, "TWh", other:0004)` gives tonnes, `apply(m, "m3", other:0049)` gives tonnes. (The registry descriptions of `other:0004` and `other:0049` still say these units cannot go through `apply`; that text predates LIB_SPEC v1.3 and is stale, §11 item 3.) A factor row whose unit is not one of these raises `LibError`. Shares are applied as `apply(X, X_unit, share_row)` with `X_unit` `Bq` (an activity) or `t` (a mass), or with `product`.
- **Products** use `product`. A result with an exact-zero term is `Bounds.exact(0)` (LIB_SPEC §7.7).
- **Complement.** For a share row with bounds $(s_l,s_c,s_h)$ the conventional complement is $\mathrm{Bounds}(1-s_h,\,1-s_c,\,1-s_l)$ (anti-correlated with $s$); a share with $s_h>1$ raises `LibError`. Used for the unreleased fraction of fallout Cs-137 (§6.4–§6.5).
- **Independent difference** (private helper, tested; COAL_SPEC §7): for $a-b$, central $c=c_a-c_b$; $\mathrm{low}=c-\sqrt{(c_a-l_a)^2+(h_b-c_b)^2}$, $\mathrm{high}=c+\sqrt{(h_a-c_a)^2+(c_b-l_b)^2}$; each bound clipped to $\ge0$; a negative central is set to 0 before the bounds are built and logged; when the low is clipped to 0, `nd_floored` is set (cause `clipped_difference`). **Used for** the two rest-of-world residuals (geothermal, wood and charcoal; §4.1, §6.1) and for the peat "other use" residual (§5.1).
- **Correlated difference** (private helper `_correlated_difference(a: Bounds, b: Bounds) -> Bounds`, COAL_SPEC §12.1 and §12.15): central $c=c_a-c_b$; $\mathrm{low}=\min(l_a-l_b,\,c)$ and $\mathrm{high}=\max(h_a-h_b,\,c)$; then each bound is clipped to $\ge0$ and a negative central is set to 0 (logged). **Used where the subtrahend is a capped fraction of, or a part of, the minuend**, so that the two move together: the peat ash residue $A_g-S_g$ and $A_g-M_g$ (§5.2–§5.3), the wood partition $D_{\mathrm{tot}}-D_{\mathrm{ch}}$ and $R_1-D_{\mathrm{hh}}$ (§6.2). (Resolution 2 (D70): `factors_notes.md` §1 proposed the independent form for the wood partition; Steve chose the correlated form.)
- **Cap** (private helper, tested; COAL_SPEC §5 step 2, D54): $\mathrm{cap}(x,L)=\mathrm{Bounds}(\min(x_l,L_l),\,\min(x_c,L_c),\,\min(x_h,L_h))$, applied bound by bound; the flag follows the `Bounds` rules. Each bound that the cap changes is logged (`cap_applied` for the peat caps; `household_wood_capped` and `charcoal_wood_capped` for the wood caps; the detail names the capped bound(s), `low`, `central` and/or `high`).
- **Sums.** $\sum_c X_c$ in a rest-of-world residual uses `sum_independent`. Every sum that combines **terms into one output key** (§3.6), and the peat and wood mass sums named in §5–§6, uses **`sum_correlated`**: the terms share their factor (for example `other:0067` or `other:0068`) or are parts of one partition, and the sum is deliberately conservative where they do not (stated in §10). A sum with a term that is exactly `0/0/0` omits that term.
- **Rest-of-world residual** (shared helper). For a series with country rows $X_c$ and a world row $X_{\mathrm{XWL}}$, the residual is the independent difference $X_{\mathrm{XWL}}-\sum_c X_c$. **Tolerance (new; the nuclear stream used exact zero):** because stored values carry six significant digits, the sum of the country rows differs from the world row by up to $2.7\times10^{-6}$ relative for geothermal and $2.3\times10^{-6}$ for wood in the clean years. A residual whose central magnitude is at most $10^{-5}\,X_{\mathrm{XWL},\mathrm{central}}$ (the D68 tolerance) is treated as exactly zero: no rows, no log entry. A central below $-10^{-5}X_{\mathrm{XWL}}$ is set to 0, logged `negative_residual` with the magnitude, and gives no rows. A residual central above the tolerance gives rows for country `XXX` with the rest-of-world notes text (§3.4). Where the series has no country row for a year but has a world row (geothermal 1916–1979), the residual equals the world row and the rows carry the world-aggregate text instead.

### 3.6 One row per key: aggregation of materials

The master unique key contains neither the material nor the factor, and `product` must be empty here. Wherever two materials land on the same (`year`, `substream`, `stage`, `residue_type`, `country`, `group`, `tier`, `route`) the script writes **one row**, the `sum_correlated` of the contributions, never two. This affects: P1/P2 (plants and "other peat use"; they are merged before the chain, §5.2), P3 and P4 (peat and plant wood), D3 and D4 (household peat, household wood, charcoal kiln and charcoal stove) and D5 (household wood and charcoal wood; their dry masses are summed before the memo factor is applied, §6.3). `factor_ids` of an aggregated row is the concatenation of the contributions' `factor_ids` in the fixed contribution order of §6.6, each factor listed once (first occurrence kept); `source_ids` is the sorted union. The per-term lists are fixed in §13.13 (D71), so the order is determined for every row; tests may compare ordered lists (comparing aggregated rows as sets remains acceptable).

### 3.7 Predecessor and successor states

Where a country-level series has a `CSK` value for a year, any `CZE` value for that year is dropped (rows and residual sum); each dropped value is logged (`predecessor_dropped`, country `CZE`, detail names `CSK`). The rule applies to `wood_fuel_t`, `household_fuelwood_m3`, `charcoal_production_t` and the peat series. The current data have no overlap (`wood_fuel_t`: CSK 1961–1992, CZE 1993–2024), so it is inert today and is kept for the shared code path. `SUN`/`RUS`/`UKR`/`BLR`, `YUG`/`SRB` and `DDR`/`DEU` are separate regions and are not touched; the residual absorbs any gap.

### 3.8 Missing and ambiguous factors; the `LibError` rule (coal §12.6)

A failed `select` is "no factor" **only** when the `LibError` message starts with `no factor row`. **Every lookup in this stream is mandatory:** the registry windows cover 1800–2025 or the stated sub-ranges for every (country, year) with a driver, and an exact-region row always has an `XWL` fallback. A `no factor row` error is therefore a registry error and **propagates** (`LibError`); the log kind `no_factor` (§8) is declared for forward compatibility and is never written for the real registry. `ambiguous factor rows` also propagates. A family with **no registry rows at all** is logged once as `no_family` (not `no_factor`): in this stream only the `hydro` and `construction` stages (§7). Fixtures that need a missing factor remove it from a copy of the registry and expect the raise.

### 3.9 Duplicates and warnings (coal §12.5, §12.7)

- Two activity rows with the same (`series`, `country`, `year`) raise `LibError` naming the key. Nothing is silently first-wins.
- `build()` emits nothing on stderr. The lib's warnings (floor dominance, zero central value in product) are captured, counted and recorded as one log entry per build (`kind = lib_warning`, year and country empty, `detail` = the count and the message types, §13.16). The entry is written only when at least one warning was captured; the real tree captures warnings, so it has **exactly one** `lib_warning` entry; a fixture build has at most one.
- `write_master` raises on a duplicate master key; the script has no tie-break, so a duplicate key is a defect of §3.6 (tests: the unique-key check, §9(c) item 6).

---

## 4. Geothermal (substream `geothermal`, stage `geothermal`)

### 4.1 Drivers and country set

The driver is `elec_gen_geothermal` (TWh of electricity). For each year $1916\le y\le2025$ (1916–1949 go to the pre-1950 file) the script forms:

- one row set per country $c$ with a country value $G_{c,y}$ (country code on the row, factor region $c$); a country-year with an exact `0/0/0` driver gives no rows; absent country-years are silent;
- the rest of the world by §3.5: for 1980–2025 the residual is zero within tolerance, so no `XXX` rows exist; for 1916–1979 there are no country rows and the **whole world aggregate** $G_{\mathrm{XWL},y}$ is written as country `XXX` with factor region `XWL` and the world-aggregate text (§3.4). The change of country structure at 1979/1980 is a data-coverage step and is not smoothed (§4.2 gives its size).

The set of countries is read from the file, not listed in the script. Years 1800–1915 have no driver: one aggregated `no_driver` entry (series `elec_gen_geothermal`, country `XXX`, run 1800–1915). 2025 has genuine (`extrapolated`, widened-band) country and world rows: **2025 rows are written** and carry `; driver basis: extrapolated`. (The earlier 2025 zero of the world series was a defect of the activity builder, repaired on 2026-11-02; the script does not special-case 2025, but a fixture with a zero world row for the last year must give no rows, not zero-valued rows, §9(g).)

### 4.2 Rn-222 and Rn-220 in non-condensable gas

For each (country or `XXX`, year), with $G$ the driver in `TWh`:

- **Rn-222 flow.** `select(factors, year=y, region=r, stage="geothermal", group="Rn222+", tier="liberated", route="air_vented_gas", driver_series="elec_gen_geothermal")`, region $r$ the country code (or `XWL` for `XXX`); value $F^{222}=\mathrm{apply}(G,\text{"TWh"},\text{row})$ (factor unit `Bq/GWa`). Row: group `Rn222+`, tier `liberated`, route `air_vented_gas`.
- **Country overrides against the rest of the world** (exact region beats `XWL`):

| Region | Factor | Years | Central (TBq per GW·a) | Low–high | Role |
|---|---|---|---|---|---|
| `ITA` | `other:0002` | 1913–2025 | 260 | 100–400 | Larderello and Tuscan vapour-dominated fields |
| `USA` | `other:0003` | 1960–2025 | 38.5 | 5–150 | The Geysers value applied to US generation |
| `NZL` | `other:0072` | 1958–2025 | 80 | 30–300 | flash/liquid-dominated; NZ estimate (Whitehead 1980) |
| every other country, and `XXX` | `other:0001` | 1900–2025 | 80 | 5–400 | rest of the world (flash, liquid-dominated, binary); the UNSCEAR default of 150 was replaced by D61/D65 |

  Every country absent from the table (31 of the 34 listed countries, including `SUN` 1989–1991) takes `other:0001` through `select`'s fallback. Before the country series begin (1916–1979) every `XXX` row takes `other:0001`: Larderello and The Geysers were most of the world output then (gap G5), and the override rows cannot apply. The resulting step is real and is documented, not smoothed: the generation-weighted mean factor is 80 TBq per GW·a to 1979 and 98.9 in 1980, then 78.3 (1990), 84.6 (2000), 83.5 (2010), 83.2 (2020) and 82.6 (2024) (spec author's arithmetic, §9(e) indicative values).
- **Rn-220 flow** (D61 P5, D65 round-3 P9). The registry holds a **unit-1 ratio** of Rn-220 to Rn-222 released: `other:0075` for region `ITA` (1913–2025; 0.0005 / 0.01 / 0.05, from the non-detection of Rn-220 at Larderello wellheads) and `other:0071` for every other region (`XWL`, 1900–2025; 0.005 / 0.05 / 0.35, from the Wairakei wellhead ratio and decay in transit). `select(factors, year=y, region=r, stage="geothermal", group="Rn220+", tier="liberated", route="air_vented_gas", driver_series="elec_gen_geothermal")` with the same region as the Rn-222 call. The script checks that the row's unit is exactly `1` (else `LibError`) and forms $F^{220}=\mathrm{product}(F^{222},\ \text{ratio})$ (the Rn-222 flow bounds times the ratio bounds, as independent terms; unit `Bq/a`). Row: group `Rn220+`, tier `liberated`, route `air_vented_gas`. **The ratio region follows the Rn-222 region only for `ITA`**: `USA`, `NZL` and the rest of the world use the `XWL` ratio `other:0071` together with their own Rn-222 factor. `factor_ids` of the Rn-220 row: the Rn-222 factor, then the ratio factor.
- Neither group is an exhalation from a residue (SCHEMA §3.2): this is radon vented with the gas through the plant, a process route.

### 4.3 Scale and sludge

Mass of scale in tonnes (an intermediate, never written): $M=\mathrm{apply}(G,\text{"TWh"},\text{row})$ with the mass row `select(factors, year=y, region=r, stage="geothermal", tier="impounded", residue_type="geothermal_scale", driver_series="elec_gen_geothermal", group="", route="")`, which is `other:0004` (unit `t/GWa`; 1 / 250 / 260,000 t per GW·a; the weakest factor in the file, gap G3). The region is always `XWL` in the registry, so the same factor applies to every country and the rows of all countries are fully correlated through `other:0004`. Then for each group $g$ of the family, with the concentration row `select(…, stage="geothermal", group=g, tier="impounded", residue_type="geothermal_scale", driver_series="", route="")` (`other:0005` `Ra226+`, `0006` `Ra228+`, `0007` `Pb210+`, `0008` `Po210`, `0009` `K40`; unit `Bq/t`): value $\mathrm{apply}(M,\text{"t"},\text{row})$ in Bq, written as `Bq/a` (the scale made in the year). Row: stage `geothermal`, tier `impounded`, `residue_type` `geothermal_scale`, no route. `factor_ids`: `other:0004`, then the concentration factor.

Scale is **counted** (D21: processing residues count whatever their concentration; D61 choice 3 kept the rows). At the centre it is about $10^{-6}$ of the Rn-222 flow; at the joint high bound it is about 1.3 % (`factors_notes.md` §2), which is why it is not marked negligible under METHODS §10.3 (§10).

### 4.4 No rows

Reinjected brine (`reisolated`, `geothermal_brine`, G4), heat-only geothermal (G21), radon from the scale (engine), and `construction` (§7).

---

## 5. Peat (UNSD energy peat; countries from the peat series)

Peat has **no world series**, so the unit of work is the country. The chain mirrors COAL_SPEC §5–§6: dry mass, ash, ash-borne activity, stack release against a fly-ash cap, residue, route shares. All quantities are head-nuclide activity of the 11 natural groups.

### 5.1 Tonnages by country and year

For each country $c$ in the union of the three peat series and each year $y$ with at least one of them:

- $P^{\mathrm{pl}}_{c,y}$ = `peat_power_heat_t` (plants: electricity and CHP transformation, **including the heat share of CHP**), $P^{\mathrm{hh}}_{c,y}$ = `peat_household_t`, $S_{c,y}$ = `peat_supply_t`. An absent row is an exact zero for $P^{\mathrm{pl}}$ and $P^{\mathrm{hh}}$ (a country that burns no peat in plants is not a missing driver; silent).
- **Other peat use** $P^{\mathrm{oth}}=S\ominus_{\mathrm{indep}}\mathrm{sum\_independent}(P^{\mathrm{pl}},P^{\mathrm{hh}})$ (independent difference, §3.5): industry, district-heat plants outside the electricity statistics, and all other energy use. If $S$ is absent while a plant or household row exists, the residual is not formed and an aggregated `no_driver` entry for `peat_supply_t` (country $c$) is written (none today). A central $<0$ (supply below plants plus household, which occurs in four country-years: `ARM` 2012, `DEU` 1993, `ROU` 1998, `UKR` 1997) is set to 0 and logged `negative_residual` with the magnitude (format §13.16). The clipped residual is the zero-central term $(0,0,h)$ with $h>0$ (the independent difference builds the bounds around the zeroed central and clips the low); it **is** a contributing plant-type term: it writes rows (alone, or merged with $P^{\mathrm{pl}}$), is listed as `peat_other` in `components`, and every row whose `below_detection` it makes true carries cause `clipped_difference` (D71, §13.15). A residual within $10^{-5}S_{\mathrm{central}}$ of zero is silently zero (§3.5 tolerance). Other peat use is treated as **plant-type** (substream `biomass_peat`) and uses the plant parameters (§5.2); this is settled (resolution 4, D70): it is merged into the plant rows, not a separate row set.
- A country-year with all three drivers exactly `0/0/0` gives no rows. More generally (D71, §13.15): **an empty plant-type peat chain writes no rows**. When $P^{\mathrm{pl}}$ is absent or exactly `0/0/0` and $P^{\mathrm{oth}}$ is exactly zero (for example supply equal to household within the tolerance), $D$ is empty: no P1 or P2 row and no plant-type peat term in P3/P4 for that country-year. The household chain (§5.3) is independent of this and runs whenever $P^{\mathrm{hh}}$ is not exactly zero.
- **Peat before 1990 is absent.** The UNSD series start in 1990 (1992 for the former USSR states), so years 1800–1989 give one aggregated `no_driver` entry (series `peat_supply_t`, country `XXX`, run 1800–1989), and there is no pre-1950 peat row. This is an understatement of unknown size (gap G6), carried in §10. The USGS series `prod_peat` is **not** used as a back-extension: it is gross weight for all uses including horticulture, and its world series falls from 170 Mt (1991) to 29 Mt (1992) because the Soviet Union leaves the aggregate (the activity rows flag this as a **coverage break**, not a production change), so no energy share can be derived from it. The UNSD peat series has an analogous coverage step: the world sum of `peat_supply_t` rises from 12.6 Mt in 1991 to 27.6 Mt in 1992 because Belarus, Russia and Ukraine enter in 1992 (their 1990–91 values do not exist). Rows rise in 1992 for coverage reasons; the step is not smoothed or filled.
- **2025 peat rows exist but are thin (D70).** The activity builder carries the 2024 values forward (`extrapolated`, widened bands, very wide where the series is short or erratic), so 2025 rows are written with `; driver basis: extrapolated`. The UNSD 2024 coverage is partial (supply 11 countries, household 4, plants one, `RWA`; most countries end in 2023), so 2024 and 2025 peat are understated against 2023 and the "other peat use" residual of a country with supply but no plant row is the whole of supply minus household. The step is a coverage effect, not a trend (§10). No `no_driver` entry is written for 2025.

### 5.2 Plant-type peat (substream `biomass_peat`): plants plus other peat use

All factors have region `XWL`. Selection keys (stage `biomass_peat` throughout; `""` = empty cell):

| Role | Factor | `driver_series` | `group` | `tier` | `route` | `residue_type` |
|---|---|---|---|---|---|---|
| dry fraction, plants | `other:0010` | `peat_power_heat_t` | `""` | `""` | `""` | `""` |
| dry fraction, other use | `other:0012` | `peat_supply_t` | `""` | `""` | `""` | `""` |
| ash yield | `other:0013` | `""` | `""` | `""` | `""` | `peat_ash` |
| fly-ash share $f_{\mathrm{fly}}$ | `other:0014` | `peat_power_heat_t` | `""` | `""` | `""` | `peat_ash` |
| ash-borne concentration $a_g$ | `other:0015`–`0025` | `""` | $g$ | `""` | `""` | `peat_ash` |
| escape fraction $p_y$ | `other:0026` (≤1989), `0027` (≥1990) | `peat_power_heat_t` | `""` | `liberated` | `air_stack` | `""` |
| enrichment $e_g$ | `other:0028`–`0038` | `peat_power_heat_t` | $g$ | `liberated` | `air_stack` | `""` |
| route share to impounded | `other:0039` | `peat_power_heat_t` | `""` | `impounded` | `""` | `peat_ash` |
| route share to dispersed | `other:0040` | `peat_power_heat_t` | `""` | `dispersed` | `""` | `peat_ash` |

(Only `other:0027` is reachable today because the peat drivers start in 1990; `other:0026` is exercised by a fixture, §9(g).) The "dry fraction" factors `0010`, `0011` and `0012` hold the same value (0.45 / 0.52 / 0.60) and are **one fully correlated factor repeated per driver** so that `select` can tell the drivers apart.

Per country and year, with $P^{\mathrm{pl}}$ and $P^{\mathrm{oth}}$ from §5.1:

1. **Dry peat** (t): $D^{\mathrm{pl}}=\mathrm{apply}(P^{\mathrm{pl}},\text{"t"},\text{0010})$ and $D^{\mathrm{oth}}=\mathrm{apply}(P^{\mathrm{oth}},\text{"t"},\text{0012})$; $D=\mathrm{sum\_correlated}(D^{\mathrm{pl}},D^{\mathrm{oth}})$.
2. **Ash** (t): $\mathcal A=\mathrm{apply}(D,\text{"t"},\text{0013})$ (5 % of dry peat, range 2–8 %).
3. **Ash-borne activity** per group: $A_g=\mathrm{apply}(\mathcal A,\text{"t"},a_g)$.
4. **Stack release (P1)**, tier `liberated`, route `air_stack`:
$$S_g=\mathrm{cap}\big(\mathrm{product}(A_g,\,p_y,\,e_g),\ \mathrm{product}(A_g,\,f_{\mathrm{fly}})\big)$$
   the D54-style cap of COAL_SPEC §5 (released activity cannot exceed the fly-ash activity). The cap does not bind at any bound for the current data ($p_y\le0.025$, $e_g\le12$, $f_{\mathrm{fly}}\ge0.6$); the helper and its `cap_applied` log are exercised by a fixture. When it binds, $S_g$ is at most $A_g f_{\mathrm{fly}}$, so with $f_{\mathrm{fly}}<1$ the residue $R_g$ stays positive (at least $A_g(1-f_{\mathrm{fly}})$ at each capped bound) and is written unflagged. Only a fly-ash share of 1 at every bound would make the cap use up the whole remainder; that case, like the household one (§5.3), writes no residue rows (§13.15).
5. **Residue and route shares (P2).** $R_g=A_g\ominus_{\mathrm{corr}}S_g$ (correlated difference). Rows: tier `impounded`, `residue_type` `peat_ash`, value $\mathrm{product}(R_g,\sigma^{\mathrm{imp}})$ with $\sigma^{\mathrm{imp}}$ = `other:0039` (0.30 / 0.60 / 0.90); tier `dispersed`, `peat_ash`, $\mathrm{product}(R_g,\sigma^{\mathrm{disp}})$ with `other:0040` (0.10 / 0.40 / 0.70). The two central shares sum to 1.
6. **Fallout Cs-137** on the same ash is handled in §6.5 and not here.

`factor_ids`: stack row — `0010` and/or `0012` (the dry-fraction factors of the contributing tonnages, plant first), `0013`, `a_g`'s factor, `p_y`'s factor, `e_g`'s factor, `0014`; residue rows — the same chain, then the share factor. `notes`: P1/P2 rule texts; the components suffix lists `peat_plant` and/or `peat_other`.

### 5.3 Household peat (substream `biomass_domestic`)

Same factors for ash yield (`0013`), concentrations ($a_g$) and enrichment ($e_g$, keyed to `peat_power_heat_t`; coal's household smoke uses the power-plant enrichment in the same way). Household-specific keys:

| Role | Factor | `driver_series` | `group` | `tier` | `route` | `residue_type` |
|---|---|---|---|---|---|---|
| dry fraction | `other:0011` | `peat_household_t` | `""` | `""` | `""` | `""` |
| smoke fraction $s$ | `other:0043` | `peat_household_t` | `""` | `liberated` | `air_stack` | `""` |
| share to impounded | `other:0041` | `peat_household_t` | `""` | `impounded` | `""` | `peat_ash` |
| share to dispersed | `other:0042` | `peat_household_t` | `""` | `dispersed` | `""` | `peat_ash` |

1. $D^{\mathrm{hh}}=\mathrm{apply}(P^{\mathrm{hh}},\text{"t"},\text{0011})$; ash $\mathcal A^{\mathrm{hh}}=\mathrm{apply}(D^{\mathrm{hh}},\text{"t"},\text{0013})$; $H_g=\mathrm{apply}(\mathcal A^{\mathrm{hh}},\text{"t"},a_g)$.
2. **Chimney smoke (D1)**, tier `liberated`, route `air_stack`: $M_g=\mathrm{cap}\big(\mathrm{product}(H_g,\,s,\,e_g),\ H_g\big)$ (COAL_SPEC §6 step 3), with $s$ = `other:0043` (0.003 / 0.0102 / 0.035, an analogue of coal:0071; no peat-stove measurement exists).
3. **Household ash (D2).** $R^{\mathrm{hh}}_g=H_g\ominus_{\mathrm{corr}}M_g$; tier `impounded` with `other:0041` (0.2 / 0.5 / 0.8) and tier `dispersed` with `other:0042` (0.2 / 0.5 / 0.8), residue `peat_ash` (D61 choice 7), rows $\mathrm{product}(R^{\mathrm{hh}}_g,\text{share})$. **When the smoke cap uses up the whole remainder** ($M_g=H_g$ at every bound, so $R^{\mathrm{hh}}_g$ is exactly `0/0/0`), **no** impounded or dispersed row is written for that group (resolution 8, D70, wins; D71, §13.15); the D1 row is written and `cap_applied` is logged. When the cap binds at the low and central but not the high, $R^{\mathrm{hh}}_g=(0,0,h)$ and the two rows are written, flagged, cause `clipped_difference` (§13.15). Neither occurs with the current data.
4. Household fallout Cs-137: §6.5.

(Coal's household and industrial ash used the independent difference in COAL_SPEC §12.15 and flagged it for revisiting; this stream uses the correlated form because the smoke is a capped fraction of the same ash-borne activity, §3.5.)

### 5.4 Peat limits that become rows' meaning

The peat tonnage is the UNSD energy-supply tonnage converted at 9.76 GJ/t; moisture is not stated by UNSD, so the dry fraction 0.52 is derived (SSI heating value, `factors_notes.md` §5 item 16). The plant tonnage includes the CHP heat share, so it overstates fuel per GW·a of **electricity** (§9(e) B3). Pre-1990 escape fraction `other:0026` is a coal analogue with no peat measurement. The concentrations are Swedish-ash based (D65 lowered the U-238 and U-234 centres to $2.5\times10^{5}$ Bq/t of ash, after Finnish production peat gave about $10^{5}$); Finnish values sit 1.4–4 times below the centres, Swedish at or above.

---

## 6. Wood, charcoal and fallout Cs-137 (memo and re-release rows)

### 6.1 Drivers and rest of the world

Wood fuel $W_{c,y}$ = `wood_fuel_t` (t, FAOSTAT item 1864 converted at 0.725 t/m³ by the activity builder; fresh basis), household fuelwood $m_{c,y}$ = `household_fuelwood_m3` (m³, UNSD), charcoal $C_{c,y}$ = `charcoal_production_t` (t charcoal). The unit of work is the **wood unit**: a listed country-year, or the rest of the world.

- For each country $c$ with $W_{c,y}$ not exactly `0/0/0` and $1961\le y\le2025$, one wood unit with country code $c$ and factor region $c$.
- **Rest of world (`XXX`).** By §3.5, residuals are formed for $W$ and for $C$ ($W_{\mathrm{XWL}}\ominus\sum_cW_c$, $C_{\mathrm{XWL}}\ominus\sum_cC_c$) with the §3.5 tolerance, so the wood unit for `XXX` exists in years with a real residual and not otherwise. From the data (§2.1 fact 3, checked 2026-11-05): wood fuel 3.2–5.2 % of the world total in 1961–1992 and about 1.0 % in 1993–2011 (unit exists, 1961–2011); about 0 in 2012–2023, inside the $10^{-5}$ tolerance (no unit, no log); 0.32 % in 2024 and 2025 (unit exists). The charcoal residual is 7.0–10.5 %, 1.7–2.2 %, about 0 and 0.027 % in the same periods. Factor region `XWL`. **No household series is formed for `XXX`: the household fallback (§6.2) always applies there.** The residual $W$ must be non-zero for the unit to exist; $C$ may be zero.
- Years 1800–1960 have no driver: one aggregated `no_driver` entry for `wood_fuel_t` (country `XXX`; run 1800–1960). 2025 has a carried-forward driver (D70) and is processed like any year, with `; driver basis: extrapolated` and the household fallback (there is no 2024 or 2025 UNSD household row). `charcoal_production_t` and `household_fuelwood_m3` are optional: an absent charcoal row is $C=0$ (silent); an absent household row triggers the fallback (§6.2).

### 6.2 Dry-wood partition

All masses are **dry wood in tonnes**. Selection keys (stage `biomass_peat`):

| Role | Factor | `driver_series` | `group` | `tier` | `route` | `residue_type` |
|---|---|---|---|---|---|---|
| dry fraction $d$ | `other:0048` | `wood_fuel_t` | `""` | `""` | `""` | `""` |
| density $\rho$ (unit `t/m3`) | `other:0049` | `household_fuelwood_m3` | `""` | `""` | `""` | `""` |
| household share, fallback | `other:0050` | `wood_fuel_m3` | `""` | `""` | `""` | `""` |
| dry wood per t charcoal $k$ | `other:0051` | `charcoal_production_t` | `""` | `""` | `""` | `""` |

The dry fraction $d$ (0.60 / 0.75 / 0.85; moisture basis of the FAO density not stated) is the **only** dry-fraction row; it serves total, household and (not charcoal, whose factor is already dry) wood alike. Per wood unit:

1. **Total dry wood.** $D_{\mathrm{tot}}=\mathrm{apply}(W,\text{"t"},d)$.
2. **Charcoal wood.** $D_{\mathrm{ch}}=\mathrm{cap}\big(\mathrm{apply}(C,\text{"t"},k),\ D_{\mathrm{tot}}\big)$, with $k$ = `other:0051` (3.23 / 3.85 / 5.26 t dry wood per t charcoal, the inverse of the 0.26 mass yield). FAOSTAT 1864 includes charcoal wood from 1997 (compliance unknown), so the charcoal feedstock is **subtracted from direct-burn wood in every year** and capped at the total; a bound changed by the cap is logged `charcoal_wood_capped`.
3. **Direct-burn wood.** $R_1=D_{\mathrm{tot}}\ominus_{\mathrm{corr}}D_{\mathrm{ch}}$ (correlated difference; charcoal wood is part of the total).
4. **Household wood.**
   - *UNSD path* (the country has a `household_fuelwood_m3` row for the year, 1990–2023): $D_{\mathrm{hh}}=\mathrm{cap}\big(\mathrm{apply}(\mathrm{apply}(m,\text{"m3"},\rho),\text{"t"},d),\ R_1\big)$, i.e. $m\times\rho\times d$ (the density row converts the reported m³ to fresh tonnes through the `t/m3` unit; the dry fraction then converts to dry tonnes) capped at $R_1$. A bound changed by the cap is logged `household_wood_capped`. This is the mass form of the household share; it avoids a ratio of two `Bounds`, which the library does not provide.
   - *Fallback path* (no UNSD row: the year is before 1990 or after 2023, the country is absent from UNSD such as China, or the unit is `XXX`): $D_{\mathrm{hh}}=\mathrm{apply}(R_1,\text{"t"},\text{other:0050})$ (0.55 / 0.75 / 0.90 of direct-burn wood). The affected rows end their rule text with `household share fallback (other:0050)` and the log gets an aggregated `household_fallback` run per country.
   - An UNSD row that is exactly `0/0/0` gives $D_{\mathrm{hh}}=0$ (data), not a fallback.
5. **Plant wood.** $D_{\mathrm{pl}}=R_1\ominus_{\mathrm{corr}}D_{\mathrm{hh}}$ (correlated difference, $\ge0$). When the household cap binds at every bound, $D_{\mathrm{pl}}$ is exactly $(0,0,0)$ (cause `exact_zero` if it were written); **a plant-wood term that is exactly `0/0/0` writes no rows** (the cap log records why; resolution 8, D70: no `0/0/0` rows flagged `exact_zero` are written for a derived remainder). When the household cap binds at the low and central but not at the high (a **partly capped** plant wood), $D_{\mathrm{pl}}=(0,0,h)$ with $h>0$: it is a contributing term and **writes** P5 rows and plant-wood terms in P3/P4, flagged under the zero-central rule with cause `clipped_difference`, tag `wood_plant` (D71, §13.15).
6. **Partition identity.** At the centre, $D_{\mathrm{pl}}+D_{\mathrm{hh}}+D_{\mathrm{ch}}=D_{\mathrm{tot}}$ to $10^{-9}$ relative (§9(c)); at the bounds it holds where no clipping occurred.

Plant wood is a **residual** and is small (0.03–0.05 Gt in 2010–2020 against 1.01 Gt total); the real plant, CHP, pellet and black-liquor fuel is mostly outside FAOSTAT item 1864 (gap G11), so plant-wood memo and re-release rows are understated. The UNSD household total exceeds the FAOSTAT total for about 40 % of countries (71 of about 182 in 2010; the USA's household wood is 1.3 times its FAOSTAT wood fuel), so the cap binds there and plant wood is zero.

### 6.3 Natural nuclides in wood: memo rows (P5, D5)

Selection: stage `biomass_peat`, group $g$ of the five wood groups, tier `memo_biosphere`, `driver_series="wood_fuel_t"`, route `""`, residue `""`: `other:0052` `K40`, `0053` `Pb210+`, `0054` `Po210`, `0055` `Ra226+`, `0056` `Ra228+` (unit `Bq/t` of **dry wood burned**; time-invariant; no U-238 or Th-228 factor exists, gap G10). The whole burned content is one memo flow: no ash and smoke split (D44).

- `biomass_peat` (P5): $\mathrm{apply}(D_{\mathrm{pl}},\text{"t"},\text{factor}_g)$.
- `biomass_domestic` (D5): $\mathrm{apply}\big(\mathrm{sum\_correlated}(D_{\mathrm{hh}},D_{\mathrm{ch}}),\text{"t"},\text{factor}_g\big)$.

Rows: tier `memo_biosphere`, no route, no residue type, `flow`, notes per §3.4 with components `wood_plant` (P5; always present although P5 is single-material, confirmed by D71) or `wood_household` and/or `charcoal` (D5).

### 6.4 Fallout Cs-137 in wood

Fuel concentration $\kappa$ (Bq per tonne of dry wood): `select(factors, year=y, region=r, stage="biomass_peat", group="Cs137+", tier="", route="", residue_type="", driver_series="wood_fuel_t")`, region $r$ the country code (`XWL` for `XXX`). The XWL default has four eras: `other:0057` (1950–62), `0058` (1963–85), `0059` (1986–2000), `0060` (2001–25); exact-region rows exist for `SWE` (`0061` 1986–2000, `0062` 2001–25), `UKR` (`0063`, `0064`), `BLR` (`0065`, `0066`) and `FIN` (`0073`, 2001–25). A country outside those years (for example `SWE` before 1986, `FIN` before 2001) takes the XWL era row. The 1950–62 and 1963–85 rows are extrapolations (scaled by cumulative deposition); the BLR and UKR rows are extrapolations with the hygienic limit (740 Bq/kg) as the high bound.

Fuel Cs-137 per material (Bq, via `apply` with the `Bq/t` row): $Q_{\mathrm{pl}}=\mathrm{apply}(D_{\mathrm{pl}},\text{"t"},\kappa)$, $Q_{\mathrm{hh}}=\mathrm{apply}(D_{\mathrm{hh}},\text{"t"},\kappa)$, $Q_{\mathrm{ch}}=\mathrm{apply}(D_{\mathrm{ch}},\text{"t"},\kappa)$. Release shares (all unit `1`, group `Cs137+`, tier `liberated`, route `air_rerelease`, region `XWL`, 1950–2025; keys differ only in `driver_series`):

| Share | Factor | `driver_series` | Central (low–high) | Applies to |
|---|---|---|---|---|
| plant stack | `other:0067` | `wood_fuel_t` | 0.005 (0.0005–0.13) | plant wood and plant-type peat |
| stove or chimney | `other:0068` | `household_fuelwood_m3` | **0.19** (0.05–0.70; D61 choice 4, the geometric mean of the bounds) | household wood and household peat |
| kiln, carbonisation | `other:0069` | `charcoal_production_t` | 0.25 (0.02–0.35) | charcoal wood |
| charcoal stove | `other:0070` | `household_charcoal_t` | 0.12 (0.05–0.30) | the Cs-137 retained in charcoal |

Per material, with $\bar s=$ the complement (§3.5):

- plants: release $L_{\mathrm{pl}}=\mathrm{apply}(Q_{\mathrm{pl}},\text{"Bq"},\text{0067})$, memo $N_{\mathrm{pl}}=\mathrm{product}(Q_{\mathrm{pl}},\bar s_{0067})$;
- household: $L_{\mathrm{hh}}=\mathrm{apply}(Q_{\mathrm{hh}},\text{"Bq"},\text{0068})$, $N_{\mathrm{hh}}=\mathrm{product}(Q_{\mathrm{hh}},\bar s_{0068})$;
- charcoal chain: kiln $K=\mathrm{apply}(Q_{\mathrm{ch}},\text{"Bq"},\text{0069})$; stove $T=\mathrm{product}(Q_{\mathrm{ch}},\bar s_{0069},y_{0070})$ (the retained share $1-x_k$ times the stove share $y$); unreleased $N_{\mathrm{ch}}=\mathrm{product}(Q_{\mathrm{ch}},\bar s_{0069},\bar y_{0070})$. All charcoal made in a country-year is taken as burned in that country-year (§10; resolution 3, D70); the series `household_charcoal_t` is a selection key only. Kiln release uses `air_rerelease`, the only route the vocabulary allows for Cs-137 at `biomass_peat`; there is no kiln-specific route, and kiln natural nuclides are memo.

The ash side of wood fallout is **memo** (D43): there is no Cs-137 tier row at `impounded` or `dispersed`. At the centre, per material, release plus memo equals the fuel Cs-137 exactly (the shares and their complements sum to 1).

### 6.5 Fallout Cs-137 in peat

Ash-borne Cs-137 on peat ash: concentration `select(…, stage="biomass_peat", group="Cs137+", tier="", route="", residue_type="peat_ash", driver_series="")`, `other:0044` (1950–62), `0045` (1963–85), `0046` (1986–2000), `0047` (2001–25), unit `Bq/t` of **ash**. Plant-type peat: $Q^{\mathrm{peat}}_{\mathrm{pl}}=\mathrm{apply}(\mathcal A,\text{"t"},\text{conc})$ (the same ash $\mathcal A$ as §5.2), release $L^{\mathrm{peat}}_{\mathrm{pl}}=\mathrm{apply}(Q^{\mathrm{peat}}_{\mathrm{pl}},\text{"Bq"},\text{0067})$, memo $N^{\mathrm{peat}}_{\mathrm{pl}}=\mathrm{product}(Q^{\mathrm{peat}}_{\mathrm{pl}},\bar s_{0067})$. Household peat: $Q^{\mathrm{peat}}_{\mathrm{hh}}$ from $\mathcal A^{\mathrm{hh}}$ with `0068` in place of `0067`. (The registry's `driver_series` of `0067` and `0068` are wood keys, `wood_fuel_t` and `household_fuelwood_m3`; the shares apply to peat Cs-137 by their descriptions, and the script selects them by those keys, not by the peat series.)

### 6.6 Final Cs-137 rows and contribution order

| Row | Substream | Value | Contribution order (for `factor_ids`) |
|---|---|---|---|
| P3 re-release | `biomass_peat` | `sum_correlated`$(L^{\mathrm{peat}}_{\mathrm{pl}},\,L_{\mathrm{pl}})$ | peat (plants, other use), plant wood |
| P4 memo | `biomass_peat` | `sum_correlated`$(N^{\mathrm{peat}}_{\mathrm{pl}},\,N_{\mathrm{pl}})$ | same |
| D3 re-release | `biomass_domestic` | `sum_correlated`$(L^{\mathrm{peat}}_{\mathrm{hh}},\,L_{\mathrm{hh}},\,K,\,T)$ | household peat, household wood, charcoal kiln, charcoal stove |
| D4 memo | `biomass_domestic` | `sum_correlated`$(N^{\mathrm{peat}}_{\mathrm{hh}},\,N_{\mathrm{hh}},\,N_{\mathrm{ch}})$ | same |

Tier, route and notes per §3.3–§3.4; stage `biomass_peat`, group `Cs137+`, quantity `flow`. Terms exactly `0/0/0` are omitted; a key with no contributing term gets no row.

---

## 7. Hydro and construction: no rows

- **Hydro (`substream` and stage `hydro`).** There is no operational release by process (UNSCEAR excludes hydro, paragraph 27; METHODS §10.3 expects it to qualify as negligible: shown, not modelled). The registry has **no row** for stage `hydro`, SCHEMA allows only `liberated` there, and the script writes none. `elec_gen_hydro` is not read.
- **Construction (stage `construction`, all `other` substreams).** Construction materials for geothermal, biomass and hydro plants wait for `data/reference/commodity_factors.csv`, which does not exist (gap G19; METHODS §6.2, D23). The registry has no `construction` row. The script writes none, as the coal stream does.
- **How the script handles both.** It contains no code for either stage. It writes one `no_family` log entry for each (stage `hydro`, stage `construction`; detail `no registry rows; construction waits for commodity_factors.csv` for the latter). It **raises `LibError`** if the registry gains a row at stage `hydro` or `construction`, or if `data/reference/commodity_factors.csv` exists, because rows for those stages would then be silently ignored by a script written without them; the spec must be revised first (§12, H1; resolution 11, D70: raise, do not log and ignore). A premise assertion in the tests states the same.
- **Negligibility.** The hydro stage's contribution through construction commodities will be formed by the construction machinery (METHODS §10.2) once the table exists; the radiological hydro link is construction only. No benchmark exists (UNSCEAR gives none; §9(e)).

---

## 8. Log

`BuildResult.log` is a list of dicts with exactly the keys `kind`, `year`, `country`, `group` (may be empty) and `detail`; there is no `series` key (the series is named in `detail`). Field values and `detail` formats are fixed in §13.16 (D71). Kinds:

| Kind | When |
|---|---|
| `no_factor` | declared (§3.8); **never written** for the real registry |
| `no_driver` | a required driver is absent for a run of years (§2.1, §4.1, §5.1, §6.1). **Aggregated**: one entry per contiguous year run per (series, country); `year` = the first year, `detail` = `first-last (n years)`. Required series: `elec_gen_geothermal` (world row), `wood_fuel_t` (world row), and the union of the three peat series (no world row: country `XXX`, run in which none of the three has a value). Not written for optional series (charcoal, household), nor for country-years absent from a country list. The expected runs today: `elec_gen_geothermal` 1800–1915; `wood_fuel_t` 1800–1960; peat 1800–1989 (2025 is covered by the carried-forward rows, D70) |
| `no_family` | a family has no registry rows at all (stages `hydro` and `construction`, §7); once per build each |
| `negative_residual` | §3.5 (geothermal, wood, charcoal) and §5.1 (peat other use); one entry per country-year, detail the magnitude |
| `household_fallback` | §6.2; aggregated per country run (`first-last (n years)`); written for `XXX` too, whose wood unit always falls back (§13.18) |
| `household_wood_capped` | §6.2 item 4; aggregated per country run; detail names the capped bound(s) |
| `charcoal_wood_capped` | §6.2 item 2; aggregated per country run |
| `cap_applied` | the peat stack or smoke cap (§5.2 step 4, §5.3 step 2); one entry per group-year with the capped bound(s) (none today) |
| `predecessor_dropped` | §3.7 |
| `lib_warning` | §3.9; one per build |

Aggregated entries carry the output-row country convention (`XXX` for world series, otherwise the country code). Country-years absent from a country list are silent; only years in which neither a country list nor the world row has a value are logged as `no_driver`. The CLI prints counts by kind and, with `--write`, writes the full log to `research/other/build_log.csv`.

---

## 9. Done conditions and tests

Tests read factor and activity values from the files (never hard-coded), with explicit **premise assertions** (§9(i)) so that a changed registry fails loudly instead of passing silently.

- **(a) Schema.** `data/streams/other.csv` passes `python -m pipeline.validate --root .`: tier matrix (V03: `geothermal` allows `impounded`, `liberated`; `biomass_peat` allows `impounded`, `dispersed`, `liberated`, `memo_biosphere`), `residue_type` exactly at `impounded`/`dispersed` rows, `route` exactly at `liberated` rows, V09 (`Rn222+`, `Rn220+` appear only as `flow`), V10 (no `XWL` country), the R02 conditionals (`memo_biosphere` is `flow` only, no residue, no route; `air_rerelease` only with stage `biomass_peat`, group `Cs137+`, `flow`), T04 (every `source_ids` entry resolves) and unique master keys.
- **(b) Candidate nuclides and coverage** (METHODS §4.3 ①, row ⑤). For every year with a driver: every geothermal (country, year) with a value has `Rn222+` and `Rn220+` Liberated rows and the five scale groups; every peat (country, year) with a non-zero chain has all 11 natural groups in each of its tiers (`liberated`/`air_stack`, `impounded`, `dispersed`) in the substreams it applies to; every wood unit with $D_{\mathrm{pl}}>0$ has the five wood memo groups under `biomass_peat`, and with $D_{\mathrm{hh}}+D_{\mathrm{ch}}>0$ under `biomass_domestic`. A missing row without a matching `no_driver` run or cap/zero rule is a failure. Group coverage against METHODS §4.3: geothermal `Rn222+`, `Rn220+`, `Ra226+`, `Ra228+`, `Pb210+` (plus `Po210`, `K40`) in 2010; biomass/peat `K40`, `Cs137+`, `Pb210+`, `Po210`, the U-series heads in 2010. Hydro: none, as designed (§7).
- **(c) Conservation and structure.**
  1. *Peat chain.* For each (country, year, group): stack $S_g$ + impounded + dispersed rows $=A_g$ recomputed from the files, at the centre, to $10^{-9}$ relative on `BuildResult.rows` (relative $10^{-5}$ on the written files, D68); the two route shares sum to 1 at the centre; likewise for household peat ($M_g$ + the two ash tiers $=H_g$).
  2. *Wood partition.* At the centre $D_{\mathrm{pl}}+D_{\mathrm{hh}}+D_{\mathrm{ch}}=D_{\mathrm{tot}}$ to $10^{-9}$, recomputed from the files; the `biomass_domestic` K40 memo row equals $(D_{\mathrm{hh}}+D_{\mathrm{ch}})\times$ `other:0052`.
  3. *Cs-137 conservation.* For each (substream, country, year), re-release row + memo row $=$ the fuel Cs-137 of the contributing materials, recomputed from the files, at the centre (relative $10^{-9}$ in memory). The pair is checked for an aggregated key and for a single-material key.
  4. *Geothermal.* The `Rn220+` row equals the `Rn222+` row times the ratio of the right region (`ITA` uses `other:0075`, all others `other:0071`) at the centre; scale rows equal mass$\times$concentration recomputed through the `t/GWa` unit.
  5. *Tier structure.* The set of (stage, substream, tier, route, residue, group) combinations equals the table of §3.3 and nothing else; no `Cs137+` row at `impounded`/`dispersed`; no wood row at `impounded`/`dispersed`/`reisolated`; no `hydro` or `construction` row; no `transfer_*`, `standing_inventory` or `opening_stock` row.
  6. *Unique keys.* The master key is unique (§3.6): in particular one `Cs137+` re-release row and one memo row per (substream, country, year), and one row per peat (country, year, group, tier).
  7. *Re-release marking and the cross-stream filter.* Every `air_rerelease` row satisfies §3.3 items 1–2 and its `notes` begin with `re-release`. A reference implementation of the consumer rule (tier `liberated`, route $\neq$ `air_rerelease`) applied to the output gives a biomass Liberated total that equals the unfiltered total minus the sum of the `air_rerelease` rows (central), and `memo_biosphere` rows enter neither total.
- **(d) Determinism.** Two builds write byte-identical files (all three); row order is the SCHEMA key order; the log order is stable.
- **(e) Benchmarks (D51).** Two years, **2010 and 2020**. Quantities are summed from output rows (central, Bq) and expressed in TBq per GW·a. A value passes when $\tfrac13\le x/x_{\mathrm{ref}}\le3$ (or a range test where stated). Where several independent values are given, the stream central must lie within a factor of 3 of **at least one** of them (COAL_SPEC §12.17); "lie between" is an alternative pass. A **known miss** is computed and recorded (the ratio goes into the test output) but is not a test failure (D69, D70). **Test treatment (as NUCLEAR_SPEC §9(e)):** the test computes the ratio, and when it lies outside the factor-3 window it calls `pytest.xfail("documented known miss (OTHER_SPEC 9(e)): <name>: stream <x>, reference <ref>, ratio <r>. <reason>")`; when it lies inside, the test passes (so a repaired factor is noticed); its premise assertions (§9(i)) pin the factor values so that a change is noticed. Known misses: B1 `ITA` Rn-222 against the Stanford laboratory value (×3.4), B1 rest-of-world default against the Salton Sea estimate (×8), B5. No known miss is an unconditional skip. The first estimates come from `research/unscear_extraction.csv` (rows `U…`); the independent estimates are from the papers named.

  **B1 — geothermal Rn-222 per GW·a** ($W_y=\texttt{elec\_gen\_geothermal}_{\mathrm{XWL},y}/8.766$ GW·a, 7.81 in 2010 and 10.89 in 2020). First estimate: UNSCEAR 2016 Annex B, para 158, **150** TBq per GW·a (U0242; the mean of Larderello 260, U0243, and The Geysers 38.5, U0244; extraction row U0250 gives 1,165.5 TBq/a derived at 7.77 GW·a). Stream (indicative, central): 651.7 TBq/a in 2010 and 905.7 in 2020, i.e. **83.5 and 83.2** TBq per GW·a (ratios to 150: 0.56 and 0.55; pass).

  **Circularity.** This first estimate is *not independent*: 150 is the mean of the very values (260 and 38.5) that the stream carries as its `ITA` and `USA` override rows, and the rest-of-world default (80) was built from the NZ estimate. The Annex B comparison therefore tests the weighting arithmetic, not the physics. The independent tests are:

  | Quantity | Independent value | Source | Tag | Test |
  |---|---|---|---|---|
  | `USA` Rn-222 per GW·a | 43–54 (16.7 nCi per L of condensate at 8–10 kg steam per kWh; wells up to about 100) | Kruger, Stoker and Umana 1977 (S1415) | I | **Required:** the `USA` row's central factor (38.5) within ×3 of 54 (ratio 0.71). The 37.7 of Anspaugh and Hahn (S1416) is the UNSCEAR source (D) and is a cross-check only |
  | `ITA` Rn-222 per GW·a | 76 (Stanford laboratory value, 34.6 nCi/L at 6.8 t steam/MWh) | S1415 | I | The `ITA` row (260) is **3.4 times** the Stanford value: outside ×3, a **documented known miss** (D70; xfail treatment above). The field-method values 257–304 (D'Amore 1976 wells, George 1980 plant table, RSE 2013 model) are the registry's own provenance chain (single root dataset, `papers_round3.md` §2) and are recorded, not counted as independent. The unresolved 1.4–2.8 times difference between field and laboratory methods is the cause |
  | rest-of-world default (`other:0001`, `0072`) | NZ flash 40–200, centre 80 (Whitehead 1980, S1402, with an assumed 29–150 t CO₂/GWh, S1413); Salton Sea flash 7–15, centre 10 (S1415, at an assumed 6–12 kg steam/kWh) | S1402, S1413, S1415 | I, but the NZ value is the **basis** of `0001` and `0072`, so it is circular for those rows | **Range test (required):** the Salton Sea centre (10) and the NZ centre (80) both lie inside the `other:0001` band (5–400), and the NZ range lies inside the `0072` band (30–300). The `0001` central (80) against the Salton Sea centre is a factor **8 above**: a documented known miss (D70; xfail treatment above; the weakest and most important geothermal number, gap G2) |
  | world mean | none independent | — | — | The generation-weighted mean (83) is reported against 150 only |

  `Rn220+` has no Annex B value and no stack measurement (only the Wairakei wellhead ratio and the Larderello non-detection): not benchmarked. The geothermal scale has no per-GW·a figure in any source: not benchmarked (indicative stream values: mass 1,952 t in 2010 and 2,722 t in 2020 at the centre; `Ra226+` $7.2\times10^{-4}$ and $1.0\times10^{-3}$ TBq/a; the five groups $1.9\times10^{-3}$ and $2.7\times10^{-3}$ TBq/a).

  **B2 — peat U-238 per GW·a of peat electricity** ($W_y=\texttt{elec\_gen\_peat}_{\mathrm{XWL},y}/8.766$, 1.065 and 0.358 GW·a). First estimate: UNSCEAR **1988** (S0008, U1351; **not Annex B 2016**, which has no peat factor): $5\times10^{9}$ kg of dry peat per GW·a at 40 Bq/kg U-238, i.e. **0.20** TBq per GW·a. Stream: the ash-borne U-238 of plant-type peat, $\sum$ of the `U238+` rows in tiers `liberated`/`air_stack`, `impounded` and `dispersed` of substream `biomass_peat` (which equal $A_g$ by §9(c) item 1), **times the plant share** $\varphi=\sum_cP^{\mathrm{pl}}_c/\sum_c(P^{\mathrm{pl}}_c+P^{\mathrm{oth}}_c)$ (the rows merge plants and other peat use, §5.2, and at the centre both have the same per-tonne chain, so the plant-only value is the row total times $\varphi$; the benchmark denominator, electricity from plants, matches the plant tonnage only). Indicative: **0.0735** (2010) and **0.0872** (2020) TBq per GW·a (ratios to 0.20: 0.37 and 0.44; pass); without the plant-share correction the values would be 0.112 and 0.166. Independent concentrations (UNSCEAR's mass, others' concentration): Finland production peat 11 Bq/kg, giving 0.055 (S0519 via S1401; Helariutta et al.); Finland, Mustonen 1984, 15 Bq/kg, 0.075; Sweden, ash median 420 Bq/kg over 20, 0.105 (S0519). Required: within ×3 of at least one (ratios 1.3, 1.0, 0.7 in 2010 and 1.6, 1.2, 0.83 in 2020).

  **B3 — dry peat per GW·a of peat electricity** (a driver-and-factor arithmetic test; the mass never appears in rows): plant tonnage $\times$ `other:0010` per $W_y$. UNSCEAR 1988: $5\times10^{9}$ kg. Indicative stream: $5.9\times10^{9}$ kg (2010) and $7.0\times10^{9}$ kg (2020), plant tonnage only. Independent: SSI 100 MW reference plant, 5.8 kWh per kg of dry peat, giving $1.51\times10^{9}$ kg per GW·a thermal, i.e. $4.3$–$5.0\times10^{9}$ kg per GW·a(e) at an efficiency of 0.30–0.35 (efficiency is the spec author's assumption; S0519). Required pass; the stream is 1.2–1.6 times the independent value, and the CHP heat share inflates the stream side. Including other peat use the stream would be $9.0\times10^{9}$ and $13.3\times10^{9}$ kg, which is why the plant-only basis is required.

  **B4 — wood-ash Cs-137, a range test** (D61 choice 9; no factor-3 test). There is no Annex B value (UNSCEAR excludes Cs-137 in fuel, para 191). The stream value is **factor-implied** (the row aggregation of §3.6 prevents isolating wood from peat and charcoal rows in a real country): $x=\kappa_y\,(1-s)/a_{\mathrm{ash}}$ with $\kappa_y$ the XWL fuel concentration row of the year, $s=$ `other:0068` central (so $1-s$ is the share that stays in the ash), and $a_{\mathrm{ash}}=0.01$ t ash per t dry wood (the US value of S0520; wood ash yield has no registry factor, so this is a stated test constant, fixed by D70). For 1991 ($\kappa=1.5\times10^{3}$ Bq/t) $x=121$ Bq per kg of ash; for 2021 ($\kappa=1.0\times10^{3}$) $x=81$. **Pass** when $x$ lies inside the measured ranges: for 1991 the US 1990–92 range, 2.9–780 Bq/kg (mean 444; S0520); for 2021 both the Austria 2020–22 range, 11.8–867 (S1411, S0530), and the Greece 2013 range, 25–499 (S0531). The high-fallout points Finland 2018 ash 310–1,940 (mean about 1,000; S1409), the Belgian plant ash of about 200 (S0513) and the US mean of 444 are recorded in the test output but are **not** pass criteria: fallout-region measurements lie above the world default by design (81 lies below the Finnish range), so a factor-3 test on the US mean would fail (4× low). That is why this is a range test. A fixture round trip confirms that, for a single-country wood-only unit, the memo row divided by dry household wood equals $\kappa(1-s)$ (§9(f)).

  **B5 — stove Cs-137 emission per kg of wood: diagnostic, not a test.** Thessaloniki winter 2013, air-derived 0.8–6.5 Bq per kg of wood burned (S0531). Stream (XWL default, 2013): $\kappa\times s=1.0\times0.19=0.19$ Bq/kg (the earlier notes' 0.25 used the superseded centre 0.25), 4–34 times below Greece, whose wood is higher in Cs-137 (beech 8–11 Bq/kg). Order-of-magnitude consistency only; recorded as a **known miss** (xfail treatment above).

  **B6 — wood K-40 in ash: diagnostic, not a test.** US typical 2,960 Bq/kg ash (S0520) against $30\ \text{Bq/kg}\,/\,1\,\%=3{,}000$; not independent (S0520 is one input to the 30).

  **Not benchmarkable:** geothermal scale, `Rn220+`, peat Cs-137 (no independent per-GW·a value), charcoal, hydro (UNSCEAR excludes it, para 27).

  **Indicative peat share (METHODS §10.3, not a test).** `factors_notes.md` §2 estimated counted peat at 0.02–0.07 % of the stream's counted decays in 1990–2020 (pre-D65 U-series centres), below the 0.1 % negligibility rule at the centre. The verifier recomputes it; the choice to keep peat modelled (D44 makes it a flow, and the data exist) stands whatever the result. Geothermal Rn-222 is about 99.9 % of the counted stream at the centre. *Verifier result (2026-11-05, on the committed build):* geothermal 99.862 / 99.881 / 99.903 / 99.960 % and peat 0.107 / 0.098 / 0.085 / 0.031 % in 1990 / 2000 / 2010 / 2020 (head activity × group multiplier over counted tiers), so peat is just above the 0.1 % rule in 1990 only and geothermal is below 99.9 % in 1990 and 2000; Cs-137 re-release rows are 0.009–0.031 %. Informational; peat stays modelled.

- **(f) Hand-computed cases.** At least sixteen rows (2010, plus the years that need another) are recomputed independently from the factor and activity values, including: `ITA` 2010 Rn-222 (`other:0002`), `USA` 2010 (`0003`), `NZL` 2010 (`0072`) and one rest-of-world country (`JPN`, `0001`), showing the TWh→GW·a conversion; `ITA` 2010 Rn-220 with `other:0075` and `USA` 2010 Rn-220 with the XWL ratio `0071`; a `XXX` world-aggregate row for 1970 and the 1979/1980 step; a scale row (mass through the `t/GWa` unit, then `Ra226+`); a 2025 geothermal row with `; driver basis: extrapolated`; a 2025 wood row (for example `IND` `K40` memo, `biomass_domestic`, household fallback) and a 2025 peat row (for example `FIN` supply-based plant-type `Pb210+` stack row), each with `; driver basis: extrapolated`; a peat plant stack row (`FIN` 2010, `Pb210+`: dry fraction, ash, concentration, $p_y\times e_g$); a peat ash impounded/dispersed pair with the correlated residue; a household peat row set (`IRL` or `FIN`); a merged plants-plus-other-use peat row (a country where $P^{\mathrm{oth}}>0$) and a `negative_residual` country-year (`DEU` 1993); a household-wood memo row (`K40`) for a country on the UNSD path; the capped case (`USA` 2010: $D_{\mathrm{hh}}=R_1$, no `biomass_peat` wood rows, aggregated `household_wood_capped`); the fallback case (`CHN` 2010, `other:0050`) with the fallback text; a rest-of-world wood unit (`XXX` in 1961–2011, for example 2010, or 2024; §6.1) showing the fallback; the Sweden override (`SWE` 2005, `other:0062`) and the Finland override (`FIN` 2010, `other:0073`) for Cs-137; a re-release and memo pair for an aggregated key (`biomass_domestic`, a country-year with household peat, household wood and non-zero charcoal, for example `FIN` or `IRL` 2010 if the charcoal series is non-zero there, else the nearest such country); a charcoal-chain row (kiln plus stove terms); a pre-1950 geothermal row (1930).
- **(g) Fixture tests** on a miniature tree in `tmp_path` that copies the full real factor file and shrinks only the activity files: the geothermal rest-of-world tolerance (a world row differing from the country sum by $5\times10^{-6}$ gives no `XXX` rows; by $5\times10^{-5}$ gives rows; a negative residual beyond tolerance gives `negative_residual` and no rows); a world row of zero in the last year gives no rows, not zero rows; the peat other-use negative residual; wood `charcoal_wood_capped` and `household_wood_capped` (the cap changes only the bounds it must; the exact-zero plant wood writes no rows); the household fallback for a year without a UNSD row; an UNSD row of exact zero gives no household wood and no fallback; CSK/CZE `predecessor_dropped`; a missing driver year (aggregated `no_driver`); duplicate activity rows raise `LibError`; an ambiguous factor (duplicated registry row) propagates; a missing factor raises (`no factor row` is not logged, §3.8); a registry row at stage `hydro` or `construction` raises, and so does a `commodity_factors.csv`; a filled `substream` cell is detected by the premise check (§9(i)) run on a registry copy with one filled cell: this tests the **premise function**, not the script, which does not read the cell and is not required to raise (D71, §13.18); the peat stack cap (a modified `other:0027` with a high escape fraction triggers `cap_applied`; with the real $f_{\mathrm{fly}}<1$ the residue rows are still written, unflagged, equal to $\mathrm{product}(A_g\ominus_{\mathrm{corr}}S_g,\sigma)$ with the capped $S_g$); **the cap using up the whole remainder** (a modified `other:0043`, or `other:0014` set to 1 at every bound, so that the remainder is exactly `0/0/0` at every bound): `cap_applied` is logged, the stack or smoke row is written, and **no** impounded or dispersed row is written for that group (resolution 8 wins, D71, §13.15); a partial cap leaving a $(0,0,h)$ remainder writes the residue rows flagged with cause `clipped_difference`; an empty plant-type peat chain (supply equal to household, no plant row) writes no plant-type rows; the pre-1990 `other:0026` row selected for a fixture year before 1990; a factor with a unit outside §3.5 raises; a share with high above 1 raises in the complement; an `other` event in `events.csv` raises; a `1 − s` complement round trip.
- **(h) Pre-1950 file.** Non-empty: the geothermal rows of 1916–1949 only (country `XXX`, `Rn222+`, `Rn220+` Liberated flows and the five scale groups), `quantity = flow`, no `memo_*` tier, no `transfer_*`, years 1916–1949 only, each valid against `schema/master.json` with the `year` bounds relaxed; produced by the same code path as the post-1950 rows. Wood and peat rows are absent because their drivers start in 1961 and 1990, and they **cannot** be built before 1950: every Cs-137 factor starts in 1950 (`other:0044`, `0057`, `0067`–`0070`; also `0050`), and the pre-1950 file has no `memo_*` tier, while the wood families are memo rows. A pre-1950 wood or peat driver value would make a mandatory lookup fail and raise (`no factor row`, §3.8); no test requires this. **The pre-1950 fixture is geothermal only** (D71, §13.17): a fixture with an earlier geothermal world value (for example 1910; the geothermal factors start in 1900) gives `XXX` world-aggregate rows in the pre-1950 file by the same code path.
- **(i) Premise assertions.** Before comparing any value a test asserts the registry premises it uses, failing with a message that names the changed premise: the factor IDs are `other:0001`–`0073` and `0075` (74 rows; `0074` does not exist); every `substream` cell is empty (§2.2); `other:0001` unit `Bq/GWa`, central $8\times10^{13}$, low $5\times10^{12}$; `other:0002` 260 TBq/GW·a, `0003` 38.5, `0072` 80; `0071` and `0075` unit `1` with the stated centres 0.05 and 0.01; `other:0004` unit `t/GWa` (centre 250) and `0049` unit `t/m3` (centre 0.725); the `XWL`, `ITA`, `USA` and `NZL` Rn-222 and Rn-220 windows tile as §4.2 states (`ITA` 1913–2025, `USA` 1960–2025, `NZL` 1958–2025); the eras of `0057`–`0060` and `0044`–`0047` tile 1950–2025 without gap or overlap, and so do `0061`/`0062`, `0063`/`0064`, `0065`/`0066` and `0073` where they exist; `0026`/`0027` tile 1800–2025; `0010`, `0011` and `0012` carry identical bounds; the two peat route shares `0039`+`0040` and the two household shares `0041`+`0042` sum to 1 at the centre; `0068` central is 0.19 (D61); `0067` high is 0.13 (D65); `0015`/`0016` central $2.5\times10^{5}$ (D65); no registry row has `below_detection` true; no registry row has stage `hydro` or `construction`, and `data/reference/commodity_factors.csv` is absent; `events.csv` has no `other` event; `residue_types.csv` has `peat_ash` and `geothermal_scale` with ε and seepage filled; the activity facts of §2.1 (no peat `XWL`; geothermal `XWL` equals the country sum within $10^{-5}$; no `CSK`/`CZE` overlap in the wood series; the 2025 rows of `wood_fuel_t`, `wood_fuel_m3`, `charcoal_production_t` and the peat series have basis `extrapolated`, and `household_fuelwood_m3` has no row after 2023); every geothermal country code is valid for its years in `countries.csv`; every `source_ids` entry resolves.
- **(j) CLI.** Without `--write` the CLI compares both master outputs **and** `research/other/build_log.csv` with a fresh build and exits non-zero if any differs; with `--write` all three are written.

## 10. Known limits carried onto the rows (not hidden)

- **Geothermal Rn-222 is the stream** (99.86–99.96 % of the counted decays at the centre, 1990–2020) **and its world value rests on a handful of fields.** Every Larderello number traces to one 1976 wellhead survey; the Stanford laboratory value is 1.4–2.8 times lower than the field method (B1). The rest-of-world default (80) is the NZ flash estimate, itself an inference from stack CO₂ and an assumed CO₂ intensity, and is 8 times the Salton Sea estimate; no plant-level data exist for Iceland, Turkey, Indonesia, the Philippines, Kenya or Mexico. Binary and closed-loop plants vent nothing (inference), covered only by the low bound.
- The step at 1979/1980 (country overrides begin; 80 to 98.9 TBq per GW·a, +24 %) is a data-coverage effect, not smoothed (gap G5). The Annex B comparison is circular (B1).
- Rn-220 (`other:0071`, `0075`) rests on a wellhead ratio at two fields and an assumed transit time; the stack ratio is low-confidence; Pb-212 ingrowth is an engine question.
- **Geothermal scale mass** is one hypothetical hypersaline plant and one filter-cake point (1 / 250 / 260,000 t per GW·a; the low is an assumption). Joint-high scale is about 1.3 % of the Rn-222 flow; the centre is $10^{-6}$. Brine reinjection, heat-only plants and the radon from scale have no rows.
- **Peat is absent before 1990** (UN series; G6), by an unknown amount. The UNSD series has a coverage step at 1991/92 (Belarus, Russia and Ukraine enter), and the USGS peat series, unused, has a documented coverage break at the same point. Peat 2024 and 2025 are thin: the UNSD 2024 coverage is partial and the 2025 values are the carried-forward 2024 values (`extrapolated`, very wide bands where the series is erratic), so the two years understate peat against 2023. The UNSD tonnage is a heating-value conversion with an unstated moisture basis, and it includes the CHP heat share. "Other peat use" is a residual of three UNSD quantities and is treated as plant-type; plant-type rows merge plants and other use.
- Peat factors are analogues: the escape fraction before 1990 and the household smoke fraction are coal analogues; the group enrichments are coal's; no peat-stove or peat-plant stack measurement exists. The concentrations are Swedish-ash based (Finnish peat is 1.4–4 times lower).
- **Wood**: plant wood is a residual (0.03–0.05 Gt) and the real plant, CHP, pellet and black-liquor fuel is outside FAOSTAT item 1864 (G11); pellets and briquettes are not separate (G12); no radionuclide data exist for charcoal (G13); U-238 and Th-228 in wood are not found (G10); wood before 1961 is absent (G17); other biomass fuels (crop residues, dung, bagasse, MSW) have no driver (G16). UNSD household wood exceeds FAOSTAT for about 40 % of countries and China is absent from UNSD, so the household/plant split is country-by-country unreliable and the cap binds often. The step from the UNSD path (to 2023) to the fallback share (2024 and 2025) is a method change, not a trend; the 2025 wood and charcoal values are the 2024 values carried forward, not data. The rest-of-world wood unit always uses the fallback share.
- **Fallout Cs-137**: the time shape is four era rows (G14); the 1950–85 values and the BLR/UKR rows are extrapolations; the stove share 0.19 is the geometric mean of 0.05 and 0.70 with no stove measurement behind it (G9), and measured paired factors show that pellet appliances retain nearly all Cs-137 in ash; the plant share 0.005 rests on one peat-plant mass balance (Hedvall: 0.66 % particulate, 12 % unaccounted); charcoal rows assume all charcoal is burned in the year and country of production; the household stove share is applied to peat as well as wood.
- **Re-release rows are counted in the stream's Liberated tier and excluded from cross-stream sums**; the exclusion is a consumer rule (§3.3). Memo rows are outside every total.
- **Aggregation conservatism.** Terms combined into one key use `sum_correlated` (§3.6), wider than an independent sum; the partition differences are correlated, narrower than independent ones (§3.5).
- **Hard era steps** (peat Cs-137 at 1963, 1986, 2001; wood Cs-137 at the same years; escape fraction at 1990) are real discontinuities of the factor data and are **not smoothed** (coal §12.13).
- Sums of `Bounds` across countries share factors (SCHEMA §4.9): the engine treats rows with one `factor_id` as fully correlated.
- The rest-of-world tolerance of $10^{-5}$ discards a real residual smaller than $10^{-5}$ of the world row; for geothermal this is below the stored precision.
- Hydro and construction have no rows (§7). The biomass families, per country, are by far the largest part of the file (resolution 9, D70).

---

## 11. Resolutions in force, and inconsistencies found while writing

### 11.1 Resolutions taken as given (Steve, D61 and D65; no question is open on these)

1. **Geothermal radon structure** (D61 choice 1): `ITA` and `USA` overrides over a rest-of-world default; `NZL` row; Rn-220 as a ratio of the Rn-222 flow (`ITA` own ratio) (§4.2).
2. **Scale rows kept** (D61 choice 3); no reinjected-brine rows.
3. **Household stove share centre 0.19** (D61 choice 4, P7; unchanged by D65).
4. **Wood natural nuclides: memo, with `Ra226+` and `Ra228+` added** (D61 choice 5; D44 extension).
5. **Re-release rows counted in the stream's Liberated tier and excluded from cross-stream sums** (D61 choice 6; §3.3).
6. **Household peat ash uses `peat_ash`** (D61 choice 7).
7. **Cs-137 in wood: world default by era plus `SWE`, `UKR`, `BLR` rows and the `FIN` row** (D61 choice 8; D65 revised `FIN`).
8. **B4 is a range test** (D61 choice 9; §9(e)).
9. **Peat stays a modelled flow** (choice 15 left to the recommendation; D44), **`technology` empty** (nuclear D64 item 12; the choice 17 default; resolution 10, D70).
10. **D65 values** on the rows: `other:0001` low $5\times10^{12}$; `0075` ITA ratio; `0004` high $2.6\times10^{5}$; `0006` high; `0015`/`0016`/`0021` lowered; `0067` high 0.13; `0073` 125 / 16,000 / 121,000.

### 11.2 Inconsistencies found in the inputs (and what this spec rules)

1. **Registry size.** `factors_notes.md` header says 73 rows (`0001`–`0073`); the file has **74**: `other:0075` was added by D65 and `other:0074` does not exist (it was reserved for the optional Austria wood row, round-3 P11, not adopted). This spec uses `0001`–`0073` and `0075` and asserts `0074` absent (§9(i)).
2. **2025 geothermal.** `factors_notes.md` §7 and §9 item 1 say the `XWL` 2025 value is 0; the activity builder replaced it on 2026-11-02 with an `extrapolated` 97.68 TWh. This spec writes 2025 rows with the driver-basis suffix.
3. **Mass units and `apply`.** The descriptions of `other:0004` ("cannot go through lib apply(); the script multiplies Bounds directly with lib product") and `other:0049` ("outside lib apply(); use lib product directly") predate LIB_SPEC v1.3, which accepts `t/<driver unit>` in `apply`. The spec uses `apply` (§3.5). The registry text was refreshed on 2026-11-04 (D70, text only, no value change; §12 item R1).
4. **Household share.** The note on `other:0050` says the script uses $\min(\text{UNSD household}/\text{FAOSTAT},1)$; the outline of `factors_notes.md` §7 and its "drivers needing a helper" paragraph use the mass form with the cap, avoiding a ratio of two `Bounds`. This spec follows the mass form (§6.2) and uses `0050` only as the fallback share. The 0049 description calls the 0.725 t/m³ "dry-wood tonnes per m³" while its own note says to multiply by the dry-matter fraction; the spec follows the note (the density gives as-reported tonnes, `0048` makes them dry).
5. **Wood partition differences.** `factors_notes.md` §1 says plant wood is an independent difference; this spec uses the correlated form (§3.5) so the capped partition closes bound by bound (resolution 2, D70).
6. **Benchmark B2 values.** `factors_notes.md` §2 (0.147, 0.118, 0.139 TBq per GW·a) predates D65 (U-238 centre $4\times10^{5}\to2.5\times10^{5}$ Bq/t); the current values are 0.0735 (2010) and 0.0872 (2020). B1 in §2 of the notes ("130, 135", "about 83 after P1") is superseded by the D65 row `other:0001` low and the NZL row: 83.5 and 83.2. B4 used a retention of 0.75 (stove share 0.25); with 0.19 the implied ash values are 121 and 81 Bq/kg (not 112 and 75), and B5's stove emission is 0.19 (not 0.25) Bq/kg.
7. **USGS coverage break.** `factors_notes.md` §9 item 4 says the activity notes do not mention the break in `prod_peat`; the activity rows for 1991–92 now carry a `COVERAGE BREAK` note. The series is still not used (§5.1).
8. **No peat world series.** The outline of `factors_notes.md` §7 does not say that `peat.csv` has no `XWL`; the rest-of-world rule therefore applies to geothermal and wood only.
9. **Duplicate keys by construction.** The outline lists plant peat, "other peat use", plant wood, household peat, household wood and charcoal as separate row families, but several land on identical master keys (same substream, stage, group, tier, route, country, year). This spec aggregates them into one row per key (§3.6) and tags the components in `notes`.
10. **Stale text elsewhere.** METHODS §5.2 said the memo series' storage "is set in Phase 2 (SCHEMA has only `memo_earth_moved` today)": D47 and SCHEMA v2.2 added `memo_biosphere`; the sentence was corrected on 2026-11-04 (D70, minimal edit). SCHEMA §5.7 (not edited, out of scope) says re-release rows are "reported separately in cross-stream totals" while D61 choice 6 says "excluded from cross-stream sums"; read together: shown as a separate series, never added (§3.3).

## 12. Work required before tests

Status at v1.0 final (2026-11-04). The validator passes over the whole tree (`python -m pipeline.validate --root .`: `OK: no issues`). Registry and activity prerequisites are in place except the optional items below; what remains is the stream script `pipeline/streams/other.py` and its tests, which this spec does not provide.

- **R1. Refresh stale registry text (text only).** DONE for `other:0004` and `other:0049` (mass units go through `apply`), `other:0049` wording (as-reported tonnes, not dry), the `other:0050` note (fallback share; mass form with cap), marked `REVISION D70 (text only)`; `research/other/factors_notes.md` row count, 2025 geothermal and B1/B2/B4/B5 values corrected. The remaining 0.25 mentions in other:0068's notes are the revision history (D61 changed 0.25 → 0.19) and are kept deliberately (orchestrator, 2026-11-04). The script does not depend on any of it.
- **R2. Sources.** Every `source_ids` entry of `other.csv` must resolve in `data/sources.csv` (T04). DONE (validator `OK`).
- **R3. `driver_series` existence.** Every non-empty `driver_series` of `other.csv` exists in `data/activity/` (SCHEMA §4.9), including the key-only series `wood_fuel_m3` and `household_charcoal_t`. DONE.
- **R4. Residue parameters.** `peat_ash` and `geothermal_scale` have ε and seepage filled (D62). DONE.
- **A1. 2025 carry-forward for wood, charcoal and peat (D70).** DONE (2026-11-04): `wood_fuel_m3`, `wood_fuel_t`, `wood_fuel_energy_twh`, `charcoal_production_t` (800 rows in `biomass.csv`) and the six peat series (47 rows in `peat.csv`), basis `extrapolated`, by the same rule as coal, electricity, uranium and nuclear (note N2825). The UNSD household series end in 2023 and are not carried. The script does no extrapolation.
- **A2. Geothermal 2025.** DONE (`extrapolated`, 2026-11-02).
- **H1. Hydro and construction.** Waits for `data/reference/commodity_factors.csv` and the construction-materials machinery (METHODS §6.2). The script raises if such rows or the file appear before this spec is revised (§7).
- **S1. Spec-blind test-writer and code-writer** follow the coal pattern (PHASE2_PLAN §3): tests from this file only; independent verification of done conditions (b), (d), (e) before sign-off.

## 13. Interpretations settled in advance, and Clarifications (D71)

### 13.1–13.8 Interpretations settled in advance (v1.0; from the nuclear review, NUCLEAR_SPEC §13, and the coal lessons)

These apply here exactly as written for the nuclear stream; they are listed so the test-writer need not guess.

1. **Rounding (D68).** The validator's X02 tolerance, the written-file comparisons and the rest-of-world tolerance are $10^{-5}$ relative, because files store six significant digits. In-memory `BuildResult.rows` checks use $10^{-9}$.
2. **Empty select keys** are passed as `""` (LIB_SPEC §10.3), never `None`.
3. **`factor_ids` order.** Applied order, concatenated and de-duplicated for aggregated rows (§3.6). For geothermal Rn-220 the Rn-222 factor comes first, then the ratio; for scale the mass factor first.
4. **Zero-central factors** follow the lib rule ($\mathrm{Bounds}(0,0,h)$, flagged, cause `zero_central_factor`); none exists in the registry today.
5. **Log runs.** A run of `no_driver` covers consecutive years in which the condition holds; a year in which the driver is exactly `0/0/0` (no rows, no log) ends the run.
6. **Hand-computed cases** use the registry and driver values as they stand; country and year names in §9(f) are illustrative where the data have changed.
7. **Indicative values** in §9(e) are the spec author's arithmetic from the files at the centre, not test expectations.
8. **Notes text** is as §3.4 gives it; changing the wording of a rule text is a spec change.

### §13 Clarifications (D71)

Steve approved D71 on 2026-11-05 ("as recommended"). Items 9–19 settle the spec-defect list A1–A16 in the header of `pipeline/tests/streams/test_other.py` (the test-writer's labels are given in brackets). They override §1–§12 where they differ; the body has been edited to agree. Where an item says *orchestrator default*, the reading was chosen to be most consistent with NUCLEAR_SPEC §13 and COAL_SPEC §12 and is listed for Steve to see.

9. **Rule text is exact; the separator is `; `** [A1, A2]. Every rule text of §3.4 is an exact string. `notes` is assembled as

   `<rule text>[; <appended text>]…[; components: <tags>][; driver basis: <bases>][; below_detection cause: <causes>]`

   with exactly `; ` (semicolon, one space) before each appended text and each suffix, and nothing else in between (the coal and nuclear rest-of-world rows use the same separator). A row with no appended text and no suffix has `notes` equal to its rule text; every row's `notes` begins with its rule text. *(A1: orchestrator default; A2: approved.)*
10. **Order of appended texts and suffixes** [A2, A16]. The appended texts follow in §3.4 table order: `world aggregate (no country series before 1980)`, `rest of world (world aggregate minus listed countries)`, `household share fallback (other:0050)`; then the fixed suffix order `components`, `driver basis`, `below_detection cause`. The world-aggregate and rest-of-world texts never occur on the same row. Example, a rest-of-world wood memo row in 2010: `memo: natural nuclides in burned wood, biosphere cycling (D44); rest of world (world aggregate minus listed countries); household share fallback (other:0050); components: wood_household+charcoal`. **Which rows carry the fallback text** *(orchestrator default)*: every row with a contributing plant-wood or household-wood term computed on the fallback path (plant wood is $R_1\ominus D_{\mathrm{hh}}$ and depends on the fallback share); not a row whose only wood contribution is charcoal, and not a peat-only row. The rest-of-world text is carried by every row of an `XXX` unit.
11. **Driver-basis and cause suffixes** keep the §3.4 definitions: `; driver basis: ` then `interpolated`, `extrapolated` or `interpolated+extrapolated`; `; below_detection cause: ` then the `+`-joined causes in the order `zero_central_factor`, `exact_zero`, `clipped_difference`, `floor_dominance`, `inherited_flag`.
12. **Components** [A15]. Confirmed: every P1–P5 and D3–D5 row carries `; components: …`, also with a single tag; the P5 rows carry `; components: wood_plant`. D1, D2 and geothermal rows carry none (§3.4).
13. **`factor_ids`** [A8] *(approved: the stated set, in applied order, as NUCLEAR_SPEC §13 item 5 and §13.3 above; not sorted)*. A row's `factor_ids` is the concatenation of its terms' lists in the contribution order of §6.6 (§5.2 for P1/P2: plants first), each factor listed once (first occurrence kept). Tests may compare every row's `factor_ids` as an **ordered list**. The lists per term:

   | Term | `factor_ids`, in this order |
   |---|---|
   | Geothermal | §4.2–§4.3 (Rn-222 factor; Rn-222 factor, ratio; `0004`, concentration) |
   | Plant-type peat, natural (P1, P2) | §5.2: `0010` and/or `0012`, `0013`, $a_g$, $p_y$, $e_g$, `0014`; P2 adds the share `0039` or `0040` |
   | Household peat, natural (D1) | `0011`, `0013`, $a_g$, `0043`, $e_g$ |
   | Household peat, ash (D2) | `0011`, `0013`, $a_g$, `0043`, $e_g$, then `0041` (impounded) or `0042` (dispersed) |
   | Plant-type peat Cs-137 (in P3, P4) | `0010` and/or `0012`, `0013`, the peat-ash Cs-137 era factor (`0044`–`0047`), `0067` |
   | Household peat Cs-137 (in D3, D4) | `0011`, `0013`, the era factor (`0044`–`0047`), `0068` |
   | Wood partition subset | in the fixed order `0048`, `0051`, `0049`, `0050`: **plant wood and household wood** take `0048`; `0051` when $C$ is not exactly `0/0/0`; `0049` on the UNSD path with a UNSD row that is not exactly `0/0/0`, or `0050` on the fallback path (neither when the UNSD row is exactly `0/0/0`); **charcoal wood** takes `0048`, `0051` |
   | Wood natural memo (P5) | the plant-wood partition subset, then the memo factor (`0052`–`0056`) |
   | Wood natural memo (D5) | the union of the partition subsets of the contributing household-wood and charcoal terms, in the fixed partition order, then the memo factor |
   | Wood Cs-137, plant (P3, P4) | the plant-wood partition subset, the fuel concentration $\kappa$ (`0057`–`0066`, `0073`), `0067` |
   | Wood Cs-137, household (D3, D4) | the household-wood partition subset, $\kappa$, `0068` |
   | Charcoal kiln (D3) | `0048`, `0051`, $\kappa$, `0069` |
   | Charcoal stove (D3) and charcoal unreleased (D4) | `0048`, `0051`, $\kappa$, `0069`, `0070` |

   A memo row (P4, D4) lists the same factors as the release of the same material (the complement uses the same share row). A term that is exactly `0/0/0` contributes no factors.
14. **`source_ids` and the driver-basis suffix** [A9] *(approved; the driver set follows NUCLEAR_SPEC §4.1, whose rest-of-world rows use the world row and every listed country row)*. `source_ids` is the sorted, de-duplicated union of the `source_ids` of every factor in `factor_ids` and of every driver row of the contributing terms; **the same driver rows** decide the `; driver basis:` suffix. Driver rows per term:
   - geothermal, country $c$: its `elec_gen_geothermal` row; `XXX` world aggregate (1916–1979): the `XWL` row; `XXX` rest-of-world residual: the `XWL` row and every listed country row of the year;
   - plant-type peat: the `peat_power_heat_t` row when $P^{\mathrm{pl}}$ contributes; when $P^{\mathrm{oth}}$ contributes (including the clipped $(0,0,h)$ case), the `peat_supply_t` row and whichever `peat_power_heat_t` and `peat_household_t` rows exist for the country-year (the residual reads all three);
   - household peat: the `peat_household_t` row;
   - plant wood and household wood: the unit's `wood_fuel_t` row(s); the `charcoal_production_t` row(s) when $C$ is not exactly `0/0/0`; on the UNSD path the `household_fuelwood_m3` row (also when it is exactly `0/0/0`, since it decides the path). For `XXX` "row(s)" means the `XWL` row and every listed country row summed in the residual;
   - charcoal wood: the `wood_fuel_t` row(s) (the cap limit) and the `charcoal_production_t` row(s).

   A term that is exactly `0/0/0` contributes no driver rows; values dropped by §3.7 never count.
15. **Exact-zero and zero-central remainders** [A5, A6, A7, A12].
   - *(approved (c))* **No row with bounds exactly $(0,0,0)$ is written.** A term exactly `0/0/0` is omitted from every sum and a key with no contributing term writes no row (§6.6). This covers: an exact-zero plant wood (§6.2 item 5); a peat residue $A_g\ominus_{\mathrm{corr}}S_g$ or $H_g\ominus_{\mathrm{corr}}M_g$ when the cap uses up the whole remainder (no impounded or dispersed row for that group; the stack or smoke row is written and `cap_applied` is logged; resolution 8 wins over the earlier §9(g) wording); and **an empty plant-type peat chain**, which writes no rows (§5.1). Consequently the cause `exact_zero` never appears on a written row of this stream [A12, *orchestrator default*: kept in the order for consistency with COAL_SPEC §12.16].
   - *(approved (d))* **Zero-central remainders $(0,0,h)$, $h>0$, write rows.** They arise from the clipped peat other-use residual (§5.1) and from partly capped plant wood (§6.2 item 5; and, by the same rule, a partly capped household smoke remainder, §5.3, *orchestrator default*). The correlated difference flags a result with central 0 and high $>0$ under the D52 zero-central rule; the cause of the term is `clipped_difference`, and it is carried through every product, cap, difference and sum (it is not replaced by `inherited_flag` or `floor_dominance`). Every row whose `below_detection` is true because of such a term ends with exactly `; below_detection cause: clipped_difference` (after any `; driver basis: …`). The term is listed in `components` (`peat_other`, `wood_plant`). Examples: `peat plant stack release: escape fraction times enrichment, capped at fly ash; components: peat_other; below_detection cause: clipped_difference` (a country-year whose only plant-type term is the clipped residual); `memo: natural nuclides in burned wood, biosphere cycling (D44); components: wood_plant; below_detection cause: clipped_difference`. A merged row whose other term is positive has low $>0$ and is not flagged (LIB_SPEC §8.1), so it carries no cause text.
16. **Log entries** [A3, A13, A14] *(approved; formats follow the nuclear and coal build logs)*.
   - Keys exactly `kind`, `year`, `country`, `group`, `detail`; no `series` key [A3, *orchestrator default*]. `year` is an integer (the first year for an aggregated run) and is empty only for `lib_warning` and `no_family`; `country` follows §8 (`XXX` for world series and for the peat union run, otherwise the country code; empty for `lib_warning` and `no_family`; never `XWL`); `group` is empty except on `cap_applied`.
   - `detail` formats:

   | Kind | `detail` |
   |---|---|
   | `no_driver` | `<first>-<last> (<n> years): <series> has no value` (as the nuclear log); the peat union run names `peat_supply_t` |
   | `household_fallback` | `<first>-<last> (<n> years): no household_fuelwood_m3 row; household share other:0050 used` |
   | `household_wood_capped`, `charcoal_wood_capped` | `<first>-<last> (<n> years): capped <bounds>`, where `<bounds>` is the `+`-joined union over the run of the capped bounds, in the order `low`, `central`, `high`; one run per contiguous years per (kind, country) |
   | `cap_applied` | `plant stack cap: capped <bounds>` or `household smoke cap: capped <bounds>` (one entry per country, year and group) |
   | `negative_residual` | rest of world (geothermal, wood, charcoal): `world aggregate is below the listed countries by <m> <unit>; treated as 0`; peat: `peat supply is below plants plus household by <m> t; treated as 0`. `<m>` is the magnitude of the negative raw central, formatted with Python `{:.6g}` (six significant digits, as the coal and nuclear logs); `<unit>` is the series unit (`TWh` or `t`) |
   | `predecessor_dropped` | `<series>: CZE value dropped, CSK value used` |
   | `no_family` | `stage hydro: no registry rows` and `stage construction: no registry rows; construction waits for commodity_factors.csv` |
   | `lib_warning` | `<total> pipeline.lib warnings captured: <n> x <message>; …`, the message types sorted (as the nuclear log) |

   - **`lib_warning`** [A13, approved]: one entry per build when at least one warning was captured, none otherwise; **exactly one on the real tree**, at most one on a fixture.
17. **Pre-1950 file** [A10, approved (b)]: the §9(h) fixture is **geothermal only**. Every Cs-137 factor starts in 1950, and the pre-1950 file has no `memo_*` tier, so wood and peat cannot have pre-1950 rows; a pre-1950 wood or peat driver raises through §3.8 and is not tested.
18. **Other test-review items** *(orchestrator defaults)*.
   - [A11] The "filled `substream` cell" check of §9(g) is a test of the premise function of §9(i) on a modified registry copy; the script never reads the cell and is not required to raise.
   - [A4] `household_fallback` runs are written for `XXX` (its wood unit always falls back); `charcoal_wood_capped` can occur for `XXX`; `household_wood_capped` never does (no UNSD path for `XXX`).
   - [A6] covered by item 15 (an empty plant-type chain writes no rows).
19. **Data check behind §2.1 fact 3 and §6.1** [approved (a)]: the wood-fuel residual was recomputed from `data/activity/biomass.csv` on 2026-11-05; the old "before 2010" boundary was wrong (the residual is about 1.0 % to 2011 and inside the tolerance from 2012). The data also show that 1961–1992 carries a larger residual (3.2–5.2 % for wood, 7.0–10.5 % for charcoal) than 1993–2011; the spec states both.
20. **Test-review notes** *(orchestrator, 2026-11-05)*. (i) The item 10 example string is illustrative of order only: with the real bands an `XXX` residual usually has a clipped low, so the real row also ends `; below_detection cause: clipped_difference`. (ii) One-year runs in log `detail` read `(1 year)`, otherwise `(<n> years)`. (iii) A partly capped household smoke remainder $(0,0,h)$ cannot arise with the current parameters (the smoke product bounds are wider than $H_g$, so a cap binding at the central also binds at the high); the rule in item 15 stays as a guard and is not fixture-tested. (iv) The order of bounds named in `cap_applied` is low, central, high.

---

## §X Resolutions (D70)

Steve settled all eleven questions of the draft on 2026-11-04 ("defaults as recommended"; D70). Each resolution is already applied in the body; this list is the index.

1. **2025 for wood, charcoal and peat.** Carried forward by the activity builders (`build_bio.py`, `build_peat.py`) with the existing rule (`carry_2025`, note N2825): `wood_fuel_t`, `wood_fuel_m3`, `wood_fuel_energy_twh`, `charcoal_production_t` and the six peat series, basis `extrapolated`; 2025 rows are written with `; driver basis: extrapolated` (§2.1, §3.4, §5.1, §6.1, §12 A1). The UNSD household series end in 2023 and have no 2024 value to carry, so 2024 and 2025 use the household fallback (§6.2).
2. **Wood partition: correlated differences** (§3.5, §6.2).
3. **Charcoal burned in the year and country of production** (kiln share, then stove share on the retained Cs-137); `household_charcoal_t` is a selection key only (§6.4, §10).
4. **"Other peat use" is merged with the plant rows** under `biomass_peat` with the `peat_other` component tag and the plant-share correction in B2 (§5.1, §5.2, §9(e)).
5. **Geothermal known misses documented, not hidden.** `ITA` Rn-222 (260 TBq per GW·a) is 3.4 times the Stanford laboratory value (76), and the rest-of-world default (80) is 8 times the Salton Sea estimate (10). Both are known misses with the same test treatment as NUCLEAR_SPEC §9(e): the ratio is computed and recorded, the test calls `pytest.xfail(...)` with the ratio and the reason when it is outside ×3, and the premise assertions pin the factor values (§9(e), §9(i), §10). B5 is a known miss on the same footing. The `USA` row and the range tests are the required passes. The `ITA` centre is not lowered.
6. **B4 uses a test-side 1 % wood ash yield** (S0520) and the stream's own $1-s$ retention; no registry row is added (§9(e)).
7. **Rest-of-world tolerance $10^{-5}$** of the world row; a smaller residual is exactly zero, with no rows and no log entry (§3.5).
8. **No exact-zero partition rows**: a plant-wood term that is exactly `0/0/0` writes no rows; the cap is logged (§6.2).
9. **Wood per country** (about 200 countries), not as one world aggregate, so that the regional Cs-137 rows apply (§6.1, §10).
10. **`technology` empty** on every row (§3.1).
11. **Hydro and construction guard raises** `LibError` when the registry gains a row at either stage or `commodity_factors.csv` exists (§7, §9(g)).
