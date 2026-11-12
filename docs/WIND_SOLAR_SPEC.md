# `pipeline/streams/wind_solar.py`: stream script contract (Task 2.4, wind and solar materials)

Status: **v1.1 (2026-11-11): v1.0 FINAL (approved by Steve as D74) plus the clarifications after the spec-blind test round (§13.9–§13.20, S1–S11), written into the body.** For the test-writer and the code-writer. Steve approved every resolution of §0 on 2026-11-11 (Q1: a fourth copper ore type `iocg_olympic_dam`; Q2: a `factor_id` column `commodity:NNNN`; Q3–Q18 as recommended, including the housekeeping of Q14). The schema (v2.6), library (v1.6), vocabulary, registry, engine-parameter, source and activity changes this contract depends on are built and staged under `build/d74_staging/` (manifest `build/d74_staging/APPLY.md`, generator `research/wind_solar/build_d74_staging.py`); they enter `data/` in one commit after the v2.6 validator and LIB v1.6 pass their spec-blind tests, because the current validator rejects the new columns (§12). The Tier 2 `grid` stage (`research/tier2_memo.md`) is **not** in scope; it is named only as a possible later extension (§7.4).

Derived from METHODS §2.3, §3, §5, §6.1–§6.3, §8, §10 (D6, §10.2 attribution, §10.3 negligibility), §11; SCHEMA v2.5 and **v2.6** (D74); `docs/LIB_SPEC.md` v1.6 (§3.1 `select`, §10 and §12: exact-equality `substream` and `ore_type` keys); `docs/DECISIONS.md` D1–D74; `PLAN.md` Task 2.4; `research/wind_solar/commodity_notes.md`, `copper_classes.md`, `commodity_factors_draft.csv` (208 rows), `material_intensity_v2.csv` (222 rows), `copper_class_shares.csv`, `co_product_inputs.csv`, `sources_task24_proposed.csv`; `research/tier2_memo.md`; `data/activity/capacity_additions.csv`. Modelled on `docs/OIL_GAS_SPEC.md` v1.1 and `docs/OTHER_SPEC.md` v1.1 (structure, the coal lessons of COAL_SPEC §11–§12, the D71 clarifications), so where a convention is not restated here it is the oil and gas one. Where this file and METHODS disagree, METHODS wins and this file is a bug.

Labels used for evidence: **[E]** read in the source; **[R]** read through a summary or second-hand; **[I]** author arithmetic; **[A]** assumption, no source. Grades A–D as `commodity_notes.md` §3 (A measured at several sites, B one site or one documented model, C analogy, D assumption).

---

## 0. Resolutions (D74)

Steve, 2026-11-11: "approved everything". Each question of the v0.1 draft is listed with its resolution; the body states each rule in full.

| # | Question | Resolution (D74) | Where |
|---|---|---|---|
| Q1 | Olympic Dam (OD) rows separable from Prominent Hill (PH) and Carrapateena (CP); the draft `iocg_high_u` rows were era mixes | **Fourth copper ore type `iocg_olympic_dam`** (OD only, `AUS`, 1988–2025, the un-mixed 1988–2008 rows extended; S5 $1.22\times10^{9}$ / $1.37\times10^{9}$ / $2.67\times10^{9}$ Bq per t Cu). **`iocg_high_u` = PH and CP only** (`AUS`, 2009–18 PH; 2019–25 PH 0.61 + CP 0.39 by copper tonnage; S5 $2.6\times10^{8}$/$5.2\times10^{8}$/$6.4\times10^{8}$ and $3.3\times10^{8}$/$6.0\times10^{8}$/$7.6\times10^{8}$) | §2.1, §2.3, §5.1, §12 |
| Q2 | Commodity rows need ids for V13 | **`factor_id` column, `commodity:NNNN`**, first column of `commodity_factors.csv`, unique across all factor files, resolvable by V13 (SCHEMA v2.6) | §2.2, §3.5 |
| Q3 | `bound_radio` where no product is radioactive | **D70 rule R3**: radio = second product by value; the wind/solar commodity gets 0 under `bound_radio` where it is the main product | §6.1 |
| Q4 | D6 value shares without by-product price and grade series | **Placeholder value-share series** (`d6_value_share_*`, `od_value_share_u` = 0.12), flagged `PLACEHOLDER` | §2.1 group S, §6 |
| Q5 | REE charge factor | **Second D6 layer inside `ree_oxide`**: default `ree_charge_factor` 2.5 (placeholder), `bound_main` 1, `bound_radio` 5.9 | §6.2 |
| Q6 | REE ore types | **`ree_bayan_obo`, `ree_ionic_clay`, `ree_monazite`, `ree_mt_weld`** under the same `ore_type` key | §2.3, §5.2 |
| Q7 | `technology` on ④ rows | **`wind` or `solar`**, equal to the substream | §3.1 |
| Q8 | Radon ε convention for new triples | **Tailings copy `u_tailings` (D62); all other residues D60 (emanation as upper bound)**; red mud 0.076/0.13/0.20 | Appendix A |
| Q9 | PV before 2001, thin film, CSP | **PV rows 2001–2025, all c-Si; thin film negligible; CSP no rows (`no_intensity`)** | §4, §7.3, §10 |
| Q10 | BF-route steel share | **Placeholder `steel_bf_route_share`** 0.90/0.80/0.68/0.71 by era, premise against `prod_pig_iron/prod_steel` | §2.1 group S |
| Q11 | Wind permanent-magnet shares | **Placeholders** onshore 0/0.10/0.25/0.30, offshore 0/0.20/0.50/0.75 by era | §2.1 group S |
| Q12 | PV utility share and rooftop intensity | **Placeholder `pv_utility_share`** 0.30/0.55/0.60; rooftop = utility intensities with concrete 0 and steel × 0.5 [A] | §2.1 groups I, S |
| Q13 | Benchmarks without a stream-level reference | **Component benchmarks** B1–B4 accepted as done condition (e); absence of a stream-level estimate documented as a structural known miss | §9(e) |
| Q14 | Housekeeping | **Approved:** vocabulary `tio2_pigment`, `cast_iron`; ε and seepage for the eight residue types (Appendix A); region codes `AUS;MYS` → `MYS`, `CHN;MMR` → `CHN` | §12, Appendix A |
| Q15 | Ionic-clay leached ore; Th in REO product | **Leached ore is a counted processing residue** (`other_commodity_residue`, `CHN`); Th in oxide product not counted | §2.3 |
| Q16 | Grade-D commodities under 0.1 % | **Rows kept**; §9(b) report lists those under 0.1 % in every decade | §9(b) |
| Q17 | SRS-49 as S0448 and S1800 | **S0448 is the single ID**; S1800 (Tier 2 memo proposal) is a duplicate and is not added | §12 |
| Q18 | The nine `wind_solar` impoundment-failure events | **Markers only**; no transfer rows in ④ | §2.2 |

Not decided and not in scope: the Tier 2 `grid` stage (§7.4).

### D74 as recorded (Steve, 2026-11-11)

- **(a)** Olympic Dam: **one pool, two ledgers** (`copper_classes.md` §6). Default by value: $w_U$ (about 0.12) of the OD tailings pool to nuclear, $1-w_U$ to copper (with gold and silver inside the copper ledger); bounds all-copper (`bound_main`) and all-nuclear (`bound_radio`). Two new activity series, `prod_copper_od` (t Cu) and `u_production_od` (t U), carve OD's uranium out of `AUS` in the nuclear stream (NUCLEAR_SPEC §14, v1.3 draft).
- **(b)** DRC cobalt–uranium (Manzuk and Philippe 2026, S1806): **page callout only**, no data rows in any stream.
- **(c)** Copper ore types `porphyry_stratiform`, `iocg_high_u` (PH, CP) and `cu_co_stratiform`, plus `iocg_olympic_dam` (Q1), with `ore_type` a key column of `commodity_factors.csv`: **schema v2.6**, analogous to the `substream` key (D63). REE routes use the same key (Q6).
- **(d)** Embedded fuel moves to a companion file `data/reference/commodity_fuel_inputs.csv`: reference only, **never** added to stream totals (D22).

---

## 1. Interface

```
python -m pipeline.streams.wind_solar [--root PATH] [--write]
```

- Without `--write`, outputs go to a scratch directory and are diffed (decompressed content) against the committed files; non-zero exit if **any of the three** files differs. With `--write` all three are written (D72 gzip rules, LIB_SPEC §11).
- The CLI prints one line per log kind, `log <kind>: <count>` (zero-count lines optional).
- `build(root: Path) -> BuildResult` with `rows` (1950–2025), `rows_pre1950` and `log`. `build()` reads `data/activity/`, `data/factors/wind_solar.csv` and `data/reference/commodity_factors.csv` only; it must not need any other file under `data/reference/` (a fixture tree may omit them). It never reads `commodity_fuel_inputs.csv` (§7.1).

| File | Content |
|---|---|
| `data/streams/wind_solar.csv.gz` | Master rows, 1982–2025 (first year with a capacity driver). Must pass `python -m pipeline.validate --root .` |
| `data/streams_pre1950/wind_solar.csv.gz` | Header only (`write_master([])`): no wind or solar capacity before 1950, so no D31 opening stock from this stream |
| `research/wind_solar/build_log.csv` | The full log (§8) |

## 2. Inputs

### 2.1 Activity series

All keys are (`series`, `year`, `country`); a duplicate key raises `LibError` naming it. Values are `Bounds(value_low, value_central, value_high)`.

**Group C: capacity (exists).**

| Series | File | Country used | Years | Unit | Use |
|---|---|---|---|---|---|
| `cap_add_wind_onshore` | `capacity_additions.csv` | **`XWL` only** (the country rows are never read: the file note says "sum countries or use XWL, not both") | 1982–2025 | `GW` | §4 |
| `cap_add_wind_offshore` | same | `XWL` | 2001–2025 | `GW` | §4 |
| `cap_add_solar_pv` | same | `XWL` | 2001–2025 | `GW` | §4 |
| `cap_add_solar_csp` | same | `XWL` | 2001–2025 | `GW` | none in v0.1: no intensity; logged `no_intensity` (§8) |
| `pv_share_thin_film` | same | `XWL` | 2025 | `1` | not used in v0.1 (Q9); premise only |

**Group I: material intensity (new file, §12 item A1).** `data/activity/material_intensity.csv`, series `mi_<class>_<commodity>`, country `XWL`, unit `t/GW`, one row per year 1982–2025 built from `research/wind_solar/material_intensity_v2.csv` by vintage (linear between vintages, flat outside, basis `interpolated`/`extrapolated` accordingly). Technology classes $k$:

| Class $k$ | Capacity driver | Share series | Intensity source (sub-technology in `material_intensity_v2.csv`) |
|---|---|---|---|
| `wind_on_nopm` | onshore | $1-$`wind_pm_share_onshore` | JRC GB-DFIG (2018), NREL land-based (2022), Bonou onshore (2014), White–Kulcinski steel (2010) |
| `wind_on_pm` | onshore | `wind_pm_share_onshore` | JRC GB-PMSG (2018), NREL land-based REE (2022) |
| `wind_off_nopm` | offshore | $1-$`wind_pm_share_offshore` | JRC GB-DFIG for the drivetrain; NREL and Bonou offshore for steel, concrete, copper |
| `wind_off_pm` | offshore | `wind_pm_share_offshore` | JRC DD-PMSG (2018), NREL offshore (2022), Bonou offshore |
| `pv_utility` | PV | `pv_utility_share` | JRC 2018 BOS + module, Qinghai LCA (2013–23), IEA PVPS; c-Si silicon and silver by vintage (2004–2050) |
| `pv_rooftop` | PV | $1-$`pv_utility_share` | as `pv_utility`, except concrete (cement) 0 and steel × 0.5 [A] (Q12); the Jungbluth 3 kWp inventory (2010) is per kWh and is cited as context only |

Commodities $c$ written per class (others in `material_intensity_v2.csv` are dropped and listed in §7.3): `copper`, `aluminium`, `steel` (steel + electrical steel + iron), `cast_iron`, `cement` (concrete × 0.12 t cement per t concrete [A], and the aggregate fraction is product, not residue), `ree_oxide` (Nd + Pr + Dy + Tb as oxide), `zinc`, `tin`, `silver`, `silicon_mg`, `glass`, `glass_fibre`, `tio2_pigment` (50/75/100 t/GW [A], `commodity_notes.md` §3.10). The intensity rows carry the conflicts of `commodity_notes.md` §7 in their bounds (offshore concrete 17–243 t/MW, offshore steel 120–419 t/MW, wind zinc 0.03–5.5 t/MW) and say so in `notes`.

**Group S: named share series (Steve may supply; placeholders otherwise).** File `data/activity/wind_solar_shares.csv` (new, §12 item A2). Each row with no supplied data is a **placeholder**: basis `modelled`, `notes` start `PLACEHOLDER (D74 orchestrator default; replace):`, `source_ids` the nearest context source (stated per row). The script treats placeholder and supplied rows alike; it adds `; share basis: placeholder` to `notes` and logs one aggregated `placeholder_share` entry per series and year run (§8). Tests read the values from the file.

| Series | Country | Years | Placeholder (low / central / high where different) | Context source |
|---|---|---|---|---|
| `wind_pm_share_onshore` | `XWL` | 1982–2025 | Q11 eras | S0400, S0413 |
| `wind_pm_share_offshore` | `XWL` | 2001–2025 | Q11 eras | S0400 |
| `pv_utility_share` | `XWL` | 2001–2025 | Q12 eras | S0444 |
| `steel_bf_route_share` | `XWL` | 1950–2025 | Q10 eras | S0421 |
| `ree_route_share_bayan_obo` | `XWL` | 1982–2025 | 0.60 (to 2011), 0.55 (2012–25) | S0403, S0411, S0404 |
| `ree_route_share_ionic_clay` | `XWL` | 1982–2025 | 0.35, 0.30 | S0403 |
| `ree_route_share_monazite` | `XWL` | 1982–2025 | 0.05, 0.05 | S0404 |
| `ree_route_share_mt_weld` | `XWL` | 1982–2025 | 0 (to 2011), 0.10 | S0406 |
| `ree_charge_factor` | `XWL` | 1982–2025 | 2.5 (default variant; bounds by rule, §6.2) | `commodity_notes.md` §3.1 |
| `cu_class_share_porphyry_stratiform` | `XWL` | 1950–2025 | from `copper_class_shares.csv` (B share); **not** a placeholder | S0826, S0807 |
| `cu_class_share_iocg_high_u` | `XWL` | 1950–2025 | from `copper_class_shares.csv` A share **minus** OD share (Q1); estimates [A] | S0407 |
| `cu_class_share_cu_co_stratiform` | `XWL` | 1950–2025 | from `copper_class_shares.csv` (C = DRC `prod_copper` / XWL) | S0826 |
| `d6_value_share_copper_porphyry` | `XWL` | 1950–2025 | 0.85 | S0410 |
| `d6_value_share_copper_iocg_ph_cp` | `AUS` | 2009–2025 | 0.70 | S0407 (analogy) |
| `d6_value_share_copper_cu_co` | `COD` | 1950–2025 | 0.85 | S1814 |
| `d6_value_share_ree_bayan_obo` | `CHN` | 1982–2025 | 0.70 (REE against iron and niobium) | `co_product_inputs.csv`, S0405 |
| `d6_value_share_ree_monazite` | `XWL` | 1982–2025 | 0.10 (monazite against ilmenite, rutile, zircon) | S0404 |
| `d6_value_share_zinc` | `XWL` | 1950–2025 | 0.60 (zinc against lead, silver) | S0410 |
| `d6_value_share_silver` | `XWL` | 1950–2025 | 0.15 (by-product silver) | `commodity_notes.md` §3.8 |

The three `cu_class_share_*` series plus `prod_copper_od / prod_copper` sum to 1 at central in every year (premise, §9(i)).

**Group D: D74(a) (new, §12 item A3).**

| Series | File | Country | Years | Unit | Use |
|---|---|---|---|---|---|
| `prod_copper_od` | `commodity_production.csv` | `AUS` | 1988–2025 | `t` | OD share of world copper (§5.1); nuclear F8 driver (NUCLEAR_SPEC §14) |
| `u_production_od` | `uranium.csv` | `AUS` | 1988–2025 | `t` (t U) | nuclear carve-out only; premise here |
| `od_value_share_u` ($w_U$) | `wind_solar_shares.csv` | `AUS` | 1988–2025 | `1` | §6.3, both streams; placeholder 0.12 (S0407) |

OD copper: FY2021–23 read (S0407: 205.3, 138.4, 212.5 kt); other years mine-level estimates [A, ±20 %] from `copper_classes.md` §4.1, except **2024–25 = 215 kt [A]** (the 322 / 330 kt there are BHP Copper South Australia totals including PH and CP, so the PH+CP class share keeps its `copper_classes.md` tonnage and OD is held at the FY2023 level). OD uranium follows the NUCLEAR_SPEC §14.2 rule (BHP FY2021–23; 2024–25 = AUS × 0.6154; earlier years Cu × 0.01359; every bound capped at the AUS conventional tonnage).

**Group Q: world production (exists, `commodity_production.csv`, `XWL`).** `prod_copper`, `prod_aluminium`, `prod_steel`, `prod_pig_iron`, `prod_ree_oxide`, `prod_silver`, `prod_zinc`, `prod_tin`, `prod_cement`: used only for the §4.3 attribution check $\sigma_c\le1$ and the OD share.

### 2.2 Other inputs

- **Commodity footprints** `data/reference/commodity_factors.csv` (SCHEMA §4.7 **v2.6**: `factor_id` and `ore_type` columns). Values are head activity per tonne of refined commodity, **before D6** (OQ-2 of the notes, adopted), `component = own_residue` only (the embedded rows leave the table, D74(d)).
- **Stream registry** `data/factors/wind_solar.csv`: in v0.1 it holds **no value rows**; it exists (header only) so that the factor-id universe and the validator see the stream. (Shares are activity series, §2.1 group S, because §4.9 factor rows have no key that can name a commodity, an ore type or a variant.)
- **Not read:** `commodity_fuel_inputs.csv` (§7.1), `residue_types.csv`, `groups.csv`.
- **Events** (`data/events.csv`): nine `wind_solar` events exist, all stage `commodity_supply`, type `impoundment_failure`, impounded → liberated/dispersed (E006 Marcopper, E007 Los Frailes, E012 Ajka red mud, E014 Padcal, E017 Mount Polley, E018 Fundão, E019 Dahegou red mud, E020 Cadia, E021 Brumadinho). Each released the stock of a **whole facility**, of which stream ④'s attributed share is small ($\sigma_c$ about 0.05–0.10 in the 2010s). **v0.1 (Q18 default): the script reads no event and writes no transfer rows; the events stay page markers and catalogue entries (whole-industry totals), as Tokaimura is a marker in nuclear.** A premise (§9(i)) asserts the event set, so a new ④ event fails loudly.

### 2.3 Factor selection keys

`select(commodity_factors, year=y, region=R, commodity=c, component="own_residue", ore_type=o, group=g, tier=t, route=r, residue_type=s, allocation_variant="default")`. Empty registry cells are passed as `""`, never `None` (LIB_SPEC §10.3). **`ore_type` is a LIB v1.6 match key** (LIB_SPEC §12): exact equality, exactly as `substream` in LIB_SPEC §10. A row with an empty `ore_type` matches only `ore_type=""`.

| Family | `commodity` | `ore_type` | Region `R` | Groups (orientation; tests read the registry) | Tiers / residue / route |
|---|---|---|---|---|---|
| CU-B | `copper` | `porphyry_stratiform` | `XWL` | U238+, U234, Th230, U235+, Ra226+, Pb210+, Po210, Th232, Ra228+, Th228+ | impounded / `metal_tailings` |
| CU-OD | `copper` | `iocg_olympic_dam` (Q1) | `AUS` | as CU-B | impounded / `metal_tailings` |
| CU-A | `copper` | `iocg_high_u` (PH, CP) | `AUS` | as CU-B | impounded / `metal_tailings` |
| CU-C | `copper` | `cu_co_stratiform` | `COD` | as CU-B | impounded / `metal_tailings` |
| CU-SM | `copper` | `all` | `XWL` | Ra226+ (slag), Pb210+, Po210 (off-gas) | impounded and dispersed / `smelter_slag`; liberated / `air_stack` |
| RE-BO | `ree_oxide` | `ree_bayan_obo` (Q6) | `CHN` | Th232, Ra228+, Th228+, U-series | impounded / `ree_tailings`, `ree_process_residue` |
| RE-IC | `ree_oxide` | `ree_ionic_clay` | `CHN` | as registry | impounded / `other_commodity_residue` (Q15) |
| RE-MZ | `ree_oxide` | `ree_monazite` | `XWL` | as registry | impounded and dispersed / `ree_process_residue` |
| RE-MW | `ree_oxide` | `ree_mt_weld` | `MYS` | as registry | impounded / `ree_process_residue` |
| ST | `steel` | `""` | `XWL` | stack Pb210+, Po210, Rn222+; slag U/Th series; dust; iron-ore tailings | liberated `air_stack`; impounded/dispersed `smelter_slag`; impounded `other_commodity_residue`, `iron_ore_tailings` |
| CI | `cast_iron` | `""` | `XWL` | zircon foundry sand | impounded / `other_commodity_residue` |
| AL | `aluminium` | `""` | `XWL` | Th232, Ra228+, Th228+, U-series | impounded and dispersed / `red_mud` |
| CE | `cement` | `""` | `XWL` | Pb210+, Po210, Rn222+ | liberated / `air_stack` |
| ZN, AG, SN, TI, SI, GL, GF | `zinc`, `silver`, `tin`, `tio2_pigment`, `silicon_mg`, `glass`, `glass_fibre` | `""` | `XWL` | as registry | as registry (`metal_tailings`, `smelter_slag`, `other_commodity_residue`; `air_stack`) |

A **family** is the set of registry rows sharing (`commodity`, `ore_type`, region); its (group, tier, route, residue) combinations are read from the registry, never hard-coded (OIL_GAS_SPEC §3.2). `superseded` copper rows are **not** applied to `data/` (§12 item R1), so no selection can hit them.

---

## 3. Conventions (all rows)

### 3.1 Row columns

| Column | Value |
|---|---|
| `stream` | `wind_solar` |
| `substream` | `wind` or `solar` (SCHEMA §5.1) |
| `stage` | `commodity_supply` for every row; `end_of_life` has no rows (§7.3) |
| `product` | the commodity (SCHEMA §5.5, required at commodity stages): one of `vocab.json` → `commodities` (with `cast_iron`, `tio2_pigment` added, Q14) |
| `country` | `XXX` for `XWL` families; `AUS` (CU-OD, CU-A), `COD` (CU-C), `CHN` (RE-BO, RE-IC), `MYS` (RE-MW): the **place where the residue lies**, not the place of installation |
| `quantity`, `unit` | `flow`, `Bq/a` |
| `basis` | `modelled`; the drivers' bases go into `notes` (§3.3) |
| `allocation_variant`, `allocation_rule` | single-product families: `default`, `none`; joint families: all three variants, §6 |
| `embedded_fuel` | **`False` on every row** (D74(d)) |
| `technology` | `wind` or `solar` (Q7) |
| `residue_type`, `route` | from the registry row; residue present exactly for impounded/reisolated/dispersed, route exactly for liberated (R02) |
| `event_id` | empty |
| `factor_ids` | §3.5 |
| `source_ids` | union of the commodity factor's `source_ids` and every activity row used (capacity, intensity, share, class share, D6 share, OD series), sorted |
| `notes` | family code (§3.6), then suffixes (§3.3) |

**Quantities are head-nuclide activity** of the group (METHODS §3.2, D24, D42). `Rn222+` appears only as a liberated flow (cement and steel stacks; V09).

### 3.2 Aggregation: one row per master key

Several technology classes $k$ contribute to the same master key (e.g. copper tailings at `XXX` from `wind_on_nopm`, `wind_on_pm`, `wind_off_*` all land in substream `wind`). **The factor is applied per class and the class contributions are summed afterwards** (v1.1, S4): each contribution is computed stepwise (§4.2 steps 1–5), then the contributions that share a master key and variant are summed with **`sum_correlated`** (the same factor row multiplies every contribution, so they are fully correlated in it), listing the union of `factor_ids` and `source_ids`. No summed tonnage is formed before the factor. Wind and solar never merge (different `substream`). **Ore types that share a master key** (CU-OD and CU-A: both `AUS`, `metal_tailings`, same groups) are merged the same way **after** the D6 split, variant by variant (OD default $1-w_U$, PH/CP default `d6_value_share_copper_iocg_ph_cp`); the merged row's `notes` name both ore types and `factor_ids` lists both factor ids. Master rows have no `ore_type` column (SCHEMA §5.5); the §9(f) hand case recomputes both parts.

### 3.3 Notes suffixes (OIL_GAS_SPEC §3.3 grammar)

Order: rule text; `; driver basis: <b>` (interpolated/extrapolated among capacity and intensity rows only, per §13.20; production and share rows do not count; `modelled` does not count) [corrected 2026-11-11 to match §13.20]; `; share basis: placeholder` (any group S row used is a placeholder); `; allocation basis: placeholder` (default-variant joint rows whose D6 share is a placeholder); `; below_detection cause: <causes>` last (causes as OIL_GAS_SPEC §3.3).

### 3.4 Arithmetic

- **Products** use `product`; shares of unit `1` with high $>1$ raise `LibError` (a charge factor is the one non-share unit-`1` multiplier and is exempt; §6.2).
- **Capacity × intensity:** `product(C, I)` with a unit check in the script: `GW` × `t/GW` → `t`; any other pair raises `LibError`.
- **Complement** of a share $(s_l,s_c,s_h)$ is $(1-s_h,\,1-s_c,\,1-s_l)$.
- **Commodity factor:** `apply(M, "t", factor_row)` (`Bq/t`).
- **D6 split:** `split(R, shares)` with exact shares (LIB_SPEC §2.2); a share of exactly 0 gives `Bounds.exact(0.0)`, `below_detection = false`.
- **Release cap (D54) not needed:** no row splits a measured release into tiers.

### 3.5 `factor_ids` order

The commodity factor id(s) of the row (one per contributing class after the §3.2 merge, deduplicated, registry order). Activity rows are cited in `source_ids` only, as in every other stream.

### 3.6 Family codes

`CU:` copper (all copper families, with the ore type next: `CU: porphyry_stratiform`), `RE:` REE (with route), `ST:`, `CI:`, `AL:`, `CE:`, `ZN:`, `AG:`, `SN:`, `TI:`, `SI:`, `GL:`, `GF:`. Joint rows continue `D6 <variant>, commodity <c>` (§6). Tests check prefixes and suffix grammar only.

### 3.7 Missing factors, duplicates, warnings

As OIL_GAS_SPEC §3.6–§3.7: `no factor row` → `no_factor` (logged, not raised; the committed log must have none for a family whose windows cover the driver years); any other `LibError` propagates; `lib_warning` aggregated per build; duplicate activity rows raise.

---

## 4. Activity: commodity tonnes

### 4.1 Capacity by class

For year $y$ and class $k$ (table in §2.1 group I):

$$C_k(y)=\mathrm{product}\big(C_{\mathrm{tech}(k)}(y),\,\pi_k(y)\big)$$

with $\pi_k$ the drivetrain or utility share or its complement. A year with no capacity value gives no rows and an aggregated `no_driver` entry; CSP gives one `no_intensity` run per year range.

### 4.2 Commodity tonnes

Named intermediates, in this order, one `product`, `apply` or `split` per step (stepwise nesting as coal, nuclear and oil and gas; D71 C4):

1. $C_k=\mathrm{product}(C_{\mathrm{tech}(k)},\,\pi_k)$ (§4.1), in GW.
2. $M_{k,c}=\mathrm{product}(C_k,\,I_{k,c})$, in t.
3. $T_{k,c,o}=\mathrm{product}(M_{k,c},\,\mathrm{sh}_{c,o})$, in t. $\mathrm{sh}_{c,o}$ is the family's one tonnage share:
   - the copper class share $s_o$ (§5.1);
   - for REE, route share × charge factor of the variant, multiplied as exact scalars first (§5.2, §6.2);
   - `steel_bf_route_share` for steel;
   - otherwise 1, and the step is skipped.
4. $A_{k,o,g,\tau}=\mathrm{apply}(T_{k,c,o},\ \text{"t"},\ F_{o,g,\tau})$, in Bq/a.
5. For joint families, $\mathrm{split}(A,\ \text{shares of the variant})$ (§6); otherwise $A$ is the `default` value.
6. Sum over classes $k$ (and over ore types sharing a key) per master key and variant with `sum_correlated` (§3.2).

EAF scrap steel carries no ore residue (a stated simplification). A contribution whose step-3 tonnage is exactly 0 at central is **skipped**: no lookup, no row, no log (§13.13).

### 4.3 Attribution check (METHODS §10.2)

For every commodity with a world series: $\sigma_c(y)=\big(\sum_k M_{k,c}(y)\big)/Q_c(y)$ (central $M_{k,c}$ of §4.2 step 2) at central must satisfy $\sigma_c\le1$, else `LibError` (LIB_SPEC §2.3 semantics). The script records $\sigma_c$ in the log (`attribution`, one entry per commodity and decade, detail the maximum). Indicative 2024 (author arithmetic, not a test): copper about 2.3 Mt of 23 Mt ($\sigma\approx0.10$), aluminium 3.6 Mt of 72 Mt (0.05), REE about 0.03 (wind magnets only).

---

## 5. Families

### 5.1 Copper (ore types; D74(a), (c))

For each class share $s_o(y)$, $o\in\{$`porphyry_stratiform`, `iocg_olympic_dam`, `iocg_high_u`, `cu_co_stratiform`$\}$, with $s_{\mathrm{OD}}(y)=$ `prod_copper_od`$_{\mathrm{AUS}}$ / `prod_copper`$_{\mathrm{XWL}}$ (central ratio, exact; zero before 1988):

$$A^{\mathrm{Cu}}_{k,o,g,\tau}(y)=\mathrm{apply}\big(\mathrm{product}(M_{k,\mathrm{Cu}}(y),\,s_o(y)),\ \text{"t"},\ F_{o,g,\tau}\big)$$

per class $k$ (§4.2 steps 3–4), split by D6 (step 5) and summed over $k$ (step 6)

then D6 (§6.1, §6.3). The smelter family CU-SM applies to the whole copper tonnage (no class split) with the porphyry D6 shares. **Indicative** (copper_classes.md §4.3, 2024): world S5 tailings factor $2.6\times10^{7}$ / $4.8\times10^{7}$ / $2.0\times10^{8}$ Bq per t Cu before D6; smelter terms add $2.3\times10^{6}$.

### 5.2 Rare earths

$M_{s,\mathrm{REE}}$ is wind REO (Nd, Pr, Dy, Tb oxides, about 0.28 t/MW for direct-drive PM); solar REE is reported as 0 (METHODS §10.2; Phase 1 §6). For each class $k$, route $r$ and variant $v$: $T=\mathrm{product}(M_{k,\mathrm{REE}},\ \text{route share}_r\times\text{charge factor}_v)$ (§4.2 step 3), then the RE-* factor. Because the charge factor differs by variant, REE contributions are computed per variant from step 3 on. The four route shares sum to 1 at central (premise). Dy and Tb come mainly from ionic clays, so a single route split for all four oxides is a stated simplification (§10).

### 5.3 Steel, cast iron, aluminium, cement and the rest

Single-product families (`default` / `none`), except zinc and silver (joint, §6). Steel rows include the stack (Pb-210, Po-210, Rn-222 liberated), slag (impounded and dispersed; the dispersed share is in the registry rows, world 0.5/0.8/0.95 [judgement]), sinter/BF dust to landfill and iron-ore tailings (grade D). The fuel-derived part of stack and slag activity is already subtracted in the registry (`commodity_notes.md` §1 item 2), so own-residue rows never contain coke-ash activity. Cement rows are the kiln stack only (`cement_kiln_residue` has no rows: no tonnage per t cement, `commodity_notes.md` §3.4).

---

## 6. D6 allocation

### 6.1 Which families are joint, and main and radio products

| Family | Products at the source | `main` (bound A) | `radio` (bound B) | Share of the wind/solar commodity: default / bound_main / bound_radio |
|---|---|---|---|---|
| CU-B | Cu, Mo, Au, Ag | Cu | second by value (Q3; Mo or Au) | `d6_value_share_copper_porphyry` / 1 / 0 |
| CU-SM | as CU-B | Cu | as CU-B | as CU-B |
| CU-A (PH, CP) | Cu, Au, Ag | Cu | Au (second by value, Q3) | `d6_value_share_copper_iocg_ph_cp` / 1 / 0 |
| CU-C | Cu, Co | Cu | **Co** (the uranium leaves in cobalt hydroxide, D74(b)) | `d6_value_share_copper_cu_co` / 1 / 0 |
| CU-OD | Cu (+ Au, Ag), U₃O₈ | Cu | U | $1-w_U$ / 1 / 0 (§6.3) |
| RE-BO | Fe, REE, Nb | Fe (METHODS §10.1) | REE | `d6_value_share_ree_bayan_obo` / 0 / 1 |
| RE-MZ | ilmenite, rutile, zircon, monazite | ilmenite (by value) | monazite (REE) | `d6_value_share_ree_monazite` / 0 / 1 |
| ZN | Zn, Pb, Ag | Zn | Pb (second by value, Q3) | `d6_value_share_zinc` / 1 / 0 |
| AG | Pb/Zn/Cu, Ag | the host metal | Ag only if second by value; v0.1 treats Ag as `radio` [A] | `d6_value_share_silver` / 0 / 1 |
| all others (RE-IC, RE-MW, ST, CI, AL, CE, SN, TI, SI, GL, GF) | single product | — | — | not joint: one `default` row, rule `none` |

Rules: for each joint key the script writes **three rows** (the wind/solar commodity under each variant); the other products of the mine are not stream ④ products and get no rows. SCHEMA §3.3 rule 3 needs only the three variants of the key, which these are. `default` carries `alloc:value`, the bounds `alloc:main` and `alloc:radio` (R02). A bound share of 0 is a structural zero (`Bounds.exact(0.0)`, no flag).

### 6.2 REE charge factor (Q5)

Inside `ree_oxide` the oxides needed by magnets (Nd, Pr, Dy, Tb) carry the residue of the whole REO mined with them. Multiplier on REE tonnes: `default` = `ree_charge_factor` (placeholder 2.5, value split), `bound_main` = 1 (mass split), `bound_radio` = 5.9 (all REO to Nd). It is applied **with** the §6.1 share of the same variant (RE-BO default = $0.70\times2.5$; bound_main = $0\times1$; bound_radio = $1\times5.9$). The bounds 1 and 5.9 are rule constants in this spec (`commodity_notes.md` §3.1) and are premises in §9(i).

### 6.3 Olympic Dam: one pool, two ledgers (D74(a))

$P_{\mathrm{OD}}(y)=$ `prod_copper_od`$(y)\times F_{\mathrm{OD}}$ (Bq/a by group) is the whole tailings pool. Ledger shares, which sum to 1 in every variant:

| Variant | Copper ledger (Cu with Au, Ag) | Nuclear ledger (NUCLEAR_SPEC §14) |
|---|---|---|
| `default` (`alloc:value`) | $1-w_U(y)$ | $w_U(y)$ (times $\phi_{\mathrm{civil}}$, see §14 there) |
| `bound_main` (`alloc:main`) | 1 | 0 |
| `bound_radio` (`alloc:radio`) | 0 | 1 |

Stream ④ books only its own copper's part of the copper ledger: $M_{s,\mathrm{Cu}}\,s_{\mathrm{OD}}\,F_{\mathrm{OD}}\times(1-w_U)$ in the default. The rest of the copper ledger belongs to copper's other end uses (outside the energy streams; non-energy sequel). Consistency test (§9(c)4): for every year and variant, nuclear F8 + copper ledger = $P_{\mathrm{OD}}$ at low, central and high (relative $10^{-5}$), computed from the files. **Not in either ledger:** the military share $a_v(1-\phi)P_{\mathrm{OD}}$ per variant (D16; non-zero only 1988–90; logged by the nuclear stream); the OD mine-ventilation and mill radon (stay in nuclear F1/F3 on full `AUS` tonnage, NUCLEAR_SPEC §14.3).

---

## 7. Embedded fuel, double counting, stages

### 7.1 Embedded fuel: lifecycle view only (D22, D74(d))

The five `embedded_fuel` draft rows (steel U238+/Th232, cement U238+, silicon U238+/Th232) are **not** footprint rows: they are fuel inputs times the coal registry's per-tonne activity. They leave `commodity_factors.csv` and become **fuel-input rows** in `data/reference/commodity_fuel_inputs.csv` (SCHEMA v2.6 §4.13 proposal):

| commodity | fuel | unit | low / central / high | Source |
|---|---|---|---|---|
| `steel` | `coal` (coking coal and PCI, as coal) | `t/t` | 0.6 / 0.8 / 1.0 per t BF-route steel | S0421 |
| `cement` | `coal` (coal-equivalent kiln fuel; petcoke and waste fuels not separated) | `t/t` | 0.06 / 0.10 / 0.15 | S0432 [I] |
| `silicon_mg` | `coal` (reductants; charcoal share is biomass, other stream) | `t/t` | 1.0 / 1.7 / 2.5 | S0422 [A] |
| `aluminium` | `electricity` | `MWh/t` | 14 / 14.5 / 15 | `commodity_notes.md` §1 item 4 |
| `silicon_mg` | `electricity` | `MWh/t` | 11 / 12 / 13 | same |

**Rules.** (1) The stream script never reads this file and never writes `embedded_fuel = true` rows; the industry view therefore cannot contain them. (2) The Phase 3 lifecycle code multiplies the ④ commodity tonnes by these inputs and by the **coal and oil and gas streams' own per-tonne footprints** (coal:0029–0048 and the coking/non-power families; electricity by the generation mix), adds them to ④ **in the lifecycle (per-TWh) view only**, and never to any stack in the industry view (D22, METHODS §6.1). (3) Electricity rows are reference only even in the lifecycle view until the Phase 3 design says how a generation mix is charged (it would otherwise charge ④ with part of ①②③⑤).

### 7.2 Double-counting register (against coal, oil and gas, other, nuclear)

| Overlap | Rule in ④ | Check |
|---|---|---|
| Coking coal, kiln coal, reductants (②), petcoke, kiln gas, furnace gas (③) | Never in ④ rows; lifecycle only via §7.1 | §9(c)6: no `embedded_fuel = true` row; no `coal_bottom_ash` residue in ④ |
| Fuel-derived share of observed stack/slag activity | Subtracted inside the registry (fuel shares 0.05–0.45, `commodity_notes.md` §1 item 2) | premise: the notes of those rows state the subtraction |
| Fly ash and GGBFS used in cement | Counted in ② (dispersed) and in steel slag (dispersed); cement rows are kiln stack only | premise: no cement row with a residue type |
| Steel slag used in cement or roads | Counted once, in steel (dispersed) | as above |
| Steel dust recycled to zinc (Waelz) | Counted in steel (dust row); zinc rows exclude it | premise text in the zinc rows |
| **Olympic Dam tailings** (① and ④) | One pool, two ledgers, shares sum to 1 per variant (§6.3, D74(a)) | §9(c)4 cross-stream identity |
| OD uranium product (F5 of ①) | Nuclear only; never a ④ row | no `u_*` stage in ④ |
| DRC cobalt–uranium | Neither ① nor ④: page callout (D74(b)); CU-C rows carry tailings only | premise: CU-C notes say "U in cobalt hydroxide not counted" |
| Bayan Obo thorium | REE rows only (D6 share); generic steel rows never use Bayan Obo slag | the iron share $(1-w_{\mathrm{REE}})$ of the pool is outside ④ (steel generally; §10) |
| Monazite from mineral sands | REE rows (monazite family); TiO2 rows are chloride-process waste only | — |
| Construction materials of ①②③⑤ (`construction` stages, not yet built) | Same table, different capacity series: no overlap by construction of $\sigma$ (METHODS §6.2, §10.2) | — |
| Polymers, lubricants, carbon fibre, transformer oil (③ feedstock) | No rows (`commodity_notes.md` §5) | — |
| Electricity for Al and Si smelting | Lifecycle reference only (§7.1) | — |
| Tier 2 grid copper and aluminium | Not in v0.1 (§7.4) | — |

### 7.3 Stages and what has no rows

- **`commodity_supply`**: every row of this stream.
- **`end_of_life`**: no rows. Landfilled blades and panels create no new mobilisation, and recycling-smelter off-gas is expected negligible (Phase 1 §7; METHODS §6.3 note). Marked **negligible** under §10.3 with the Phase 1 estimate stated in §9(d).
- **Thin-film PV** (CdTe, CIGS): by-product metals (Te, Cd, In, Ga, Se) about $10^{7}$ Bq/MW × 2.3 % share by value allocation (`commodity_notes.md` §3.13): negligible; no rows (Q9). The result depends on D6 (mass allocation would make Te about $10^{12}$ Bq/t).
- **Dropped intensity materials:** boron, chromium, manganese, molybdenum, nickel, lead (rooftop), germanium, polymers, carbon fibre, aggregate: no footprint in the registry. They were never put into `material_intensity.csv`, so the script never sees them and they are **not logged**. `no_footprint` fires only for an `mi_*` series whose commodity has no registry family. No such series exists in the staged files, so it fires only in fixtures (§13.15).
- **CSP:** capacity exists, intensity does not (`no_intensity`).

### 7.4 Possible later extension (not in v0.1)

A Tier 2 **`grid`** stage (T&D copper and aluminium, BESS balance of plant) driven by the same commodity table (`research/tier2_memo.md` §7). It is pending Steve's decision and would need a vocabulary stage, a stage–tier matrix row and its own tonnage series. Nothing in this spec depends on it.

---

## 8. Log

`BuildResult.log`: dicts with `kind`, `year`, `country`, `group`, `detail`. Kinds: `no_factor`, `no_driver`, `no_family`, `lib_warning` (as OIL_GAS_SPEC §8), and:

| Kind | When |
|---|---|
| `no_intensity` | a capacity class has a value but no intensity series for any commodity (CSP); aggregated per series |
| `no_footprint` | an intensity commodity with no registry family (once per commodity per build) |
| `placeholder_share` | a group S placeholder row was used; aggregated per series and year run |
| `attribution` | the $\sigma_c$ record of §4.3 (one per commodity and decade) |
| `od_military_remainder` | written by the **nuclear** stream only (NUCLEAR_SPEC §14.4), per year and variant with $a_v(1-\phi)>0$; never by this stream |

Aggregated runs are identified by `country`, `group` and the union of years (D71 C9). Field formats: §13.14. The CLI writes the full log with `--write`.

---

## 9. Done conditions and tests

Tests read every factor, intensity and share from the files, behind explicit premise assertions (§9(i)).

- **(a) Schema.** `data/streams/wind_solar.csv.gz` passes the validator **with schema v2.6 applied** (Q1, Q2). In particular: `product` in commodities (V11); stage `commodity_supply`, tiers allowed (V03; `commodity_supply` allows impounded, dispersed, liberated, memo_earth_moved); residue/route rules (R02); X03 for every joint key; `factor_ids` resolve (V13, needs Q2); no `embedded_fuel = true` row.
- **(b) Coverage.** For each family and each year with a driver and a registry row, a row exists for every registry (group, tier, route, residue) combination and, for joint families, all three variants. The committed log has no `no_factor` (v1.1: RE-BO and RE-IC windows start in 1982, S1; every other family's window covers the years in which its tonnage is non-zero). METHODS §4.3 candidates for ④ (U-238 and Th-232 series, Pb-210, Po-210, Rn-222): each appears in some 2020 row. The report lists every commodity under 0.1 % of the stream in every decade (Q16).
- **(c) Conservation and identities.**
  1. Class shares: $\sum_o s_o(y)=1$ at central ($10^{-6}$); each copper family's rows divided by its factor and D6 share equal $M_{s,\mathrm{Cu}}s_o$.
  2. REE routes sum to 1; the charge factor is applied once.
  3. Allocation: for each joint key, `default` equals the unallocated value times the share series; `bound_main`/`bound_radio` are the whole value or exact 0 per §6.1.
  4. **OD identity (cross-stream):** for every year 1988–2025 and variant, NUCLEAR F8 (all groups) + copper ledger + the logged military remainder $w_U(1-\phi)P_{\mathrm{OD}}$ $=P_{\mathrm{OD}}$ (relative $10^{-5}$ at central; at low and high only where $\phi$ has equal bounds, because `product` combines bounds non-linearly), recomputed from `prod_copper_od`, the CU-OD factors and $w_U$. Until NUCLEAR_SPEC §14 is built this test is **contingent** and skipped with a reason.
  5. Merge: each row equals the `sum_correlated` of its class contributions.
  6. No double counting: no `embedded_fuel = true`, no `coal_bottom_ash`, no `end_of_life` row, no `superseded` ore type, no row for cobalt, no Rn exhalation or seepage route (METHODS §5.2).
- **(d) Determinism and negligibility.** Two builds byte-identical; `end_of_life` and thin film stated negligible with their estimates (§7.3).
- **(e) Benchmarks: components, not the stream total.** UNSCEAR 2016 Annex B gives **no** Bq factors for wind or solar (only ore mass and occupational dose), so D51's ④ benchmarks are component tests of the per-tonne footprints times independent tonnages. **They test REE, steel, aluminium and OD copper footprints, not the ④ stream total; no independent published stream-level estimate exists, and that absence is recorded here as a structural known miss (Q13).** Pass rule: $\tfrac13\le x/x_{\mathrm{ref}}\le3$.

  | # | Year | Component | Stream-side quantity | Reference | Independence | Indicative (author arithmetic, not an expectation) |
  |---|---|---|---|---|---|---|
  | B1 | 1990–2006 cumulative | REE, Bayan Obo tailings Th-232 | RE-BO Th232 tailings factor (before D6 and charge factor) × cumulative Bayan Obo REO (CHN `prod_ree_oxide` × `ree_route_share_bayan_obo`, **1990–2006**; the CHN series starts in 1990, so output since the late 1950s before that is outside the sum) | S0405: 149 Mt tailings at 1.0–1.6 Bq/g Th-232 = $1.5$–$2.4\times10^{14}$ Bq to end 2006 | **Partly circular** (the 113 t/t factor comes from the same inventory). Independent upper bound: ore mined to end 2006, 276 Mt at 1.14 Bq/g = $3.1\times10^{14}$ Bq | Stream about 0.31 of the ore bound (about $9.5\times10^{13}$ Bq), 0.40–0.63 of the inventory. **Pass rule (v1.1, S2): stream ≤ ore bound, ≥ 1/10 of it, and within ×3 of the inventory range**: it passes. The shortfall is expected (1958–89 output excluded). v1.0 printed $10^{17}$, a ×1,000 slip |
  | B2 | 1999 | Steel stack Pb-210 and Po-210 | ST stack factors × GBR `prod_steel` 1999 × `steel_bf_route_share` | NRPB-W48 (S0430): four UK plants $2.1\times10^{10}$ Pb-210, $1.35\times10^{11}$ Po-210 Bq/a | **Partly circular** (the factor's low is Scunthorpe, W48); IJmuiden (RP-135 Table 15) and UNSCEAR 2000 Table 28 set the centre and high | 16.28 Mt × 0.68 (`steel_bf_route_share` 1999) gives Pb-210 $5.09\times10^{10}$ (ratio 2.43) and Po-210 $1.33\times10^{11}$ (ratio 0.98) on the committed build [updated 2026-11-11] |
  | B3 | 2017 | Aluminium red mud Ra-226 | AL Ra226+ (impounded + dispersed) × `prod_aluminium` 2017 | S0436: about 150 Mt/a red mud at 100–500 Bq/kg Ra-226: $1.5$–$7.5\times10^{13}$ Bq/a | Independent of the factor's tonnage basis (3.2 t/t, S0409 activities) | $9.6\times10^{5}\times5.94\times10^{7}=5.7\times10^{13}$ (inside the range; range test). `commodity_notes.md` §6 item 4 now reads $1.5$–$7.5\times10^{13}$ (corrected 2026-11-11 from a ×1,000 slip) |
  | B4 | 2010 | OD tailings radon | **Deferred to Phase 3** (radon from residues is an engine flow, SCHEMA §3.2) | S0408: completed tailings facility 520 TBq/a (13.9 MBq/s ≈ 439 TBq/a, source quirk) | Independent | Phase 2 checks only that the implied effective ε (about 0.004, Phase 1 §8) lies inside the `metal_tailings` ε triple (premise) |

  Two benchmark years with independent references are therefore 1999 (B2) and 2017 (B3), with 1990–2006 (B1) as a consistency check. A B2 Pb-210 ratio above 3 is a **documented miss**, not a failure, if the Po-210 ratio passes (the 4.0e9 versus 3.96e10 Bq/a contradiction in the NRPB papers is unresolved, `commodity_notes.md` §3.2).
- **(f) Hand-computed cases** (at least twelve, 2020 unless stated): a CU-B `Ra226+` row (all three variants); a CU-OD row in 2023 with $w_U=0.12$ and the matching nuclear F8 row; a CU-C row (COD); a CU-SM slag dispersed row; RE-BO Th232 in 2015 (default, both bounds, charge factor); RE-MW in 2012 and absence in 2011; an ST stack Po210 row (BF share); an AL red-mud dispersed row; a CE `Rn222+` row; an AG row (joint, radio = silver); a wind row merging three classes; a PV rooftop aluminium row; a placeholder-flagged row's notes.
- **(g) Fixtures** (miniature trees in `tmp_path`): absent share series → `no_driver`, no raise; a share with high > 1 raises; class shares that do not sum to 1 fail the premise; $\sigma_c>1$ raises; duplicate activity rows raise; ambiguous registry rows propagate; `ore_type=""` does not match an `iocg_high_u` row (exact equality); a missing OD series gives no CU-OD rows and logs `no_driver`; CSP-only capacity logs `no_intensity`.
- **(h) Pre-1950 file:** header only.
- **(i) Premise assertions** (examples, each failing with a message naming the premise): `commodity_factors.csv` has columns `factor_id`, `ore_type`; ore types in the registry are exactly {`porphyry_stratiform`, `iocg_olympic_dam`, `iocg_high_u`, `cu_co_stratiform`, `all`, the four REE values, ""}; no `embedded_fuel` row in it; every residue type used has all three parameter sets filled (Appendix A applied); the three copper class shares plus the OD share sum to 1 (central, $10^{-6}$); REE route shares sum to 1; `prod_copper_od` ≤ `prod_copper`$_{\mathrm{AUS}}$; `u_production_od` ≤ `u_production`$_{\mathrm{AUS}}$ in every year; $w_U\in[0,1]$; placeholder rows carry `PLACEHOLDER` in `notes`; `steel_bf_route_share` within ±0.15 of `prod_pig_iron/prod_steel` (`XWL`) where both exist (a drift fails loudly, it does not stop the build); charge-factor bounds 1 and 5.9; the `wind_solar` rows of `events.csv` are exactly E006, E007, E012, E014, E017, E018, E019, E020, E021 (Q18: markers, no rows written); the implied OD effective ε 0.004 lies in the `metal_tailings` ε222 triple.
- **(j) CLI** as OIL_GAS_SPEC §9(j).

## 10. Known limits and misses (carried onto the rows, not hidden)

- **Zero net capacity additions (verifier, 2026-11-11).** The capacity series has net additions of exactly 0 in 1988 and 1992–97 (EIA rounding), so the stream has no rows in those years (rows exist for 1982–87, 1989–91 and from 1998). Zero tonnage is silent by §13 (no row, no log); the effect on totals is negligible.

**Evidence grades by commodity** (`commodity_notes.md` §3, `copper_classes.md` §3):

| Commodity | Grade | Main weakness |
|---|---|---|
| Copper B `porphyry_stratiform` | B (activity), C (tonnage) | No tailings measurement from Chile, Peru, China, Indonesia, Kazakhstan, Russia, Mexico (57 % of 2024 output, G-CU-3); 200 t/t held constant |
| Copper OD | B | EIS-derived; OD ore grade contradictions (100–600 ppm U) |
| Copper PH, CP | C | Derived from U ppm, not Bq; tonnages [A] |
| Copper C (DRC) | C | Modelled (Manzuk); no Katanga radium measurement |
| Copper smelter | C–D | Off-gas row is one 1980s plant (G-CU-2) |
| REE | B–C | Route shares placeholders; Dy/Tb route; charge factor |
| Steel | A–B (stack), B–C (slag), D (iron-ore tailings) | No Chinese or Indian sinter data (most of world steel) |
| Aluminium | B | Calciner and smelter emissions missing |
| Cement | C | Kiln Po-210 spans ×37 (Kunze 2.1e3 vs UNSCEAR 3.9e4) |
| Zinc, silver, silicon, glass, glass fibre, cast iron | D | Assumptions; zinc intensity conflict (JRC 5.5 vs NREL 0.03–0.11 t/MW) |
| Tin, TiO2 | C | Slag per t tin [A]; TiO2 use per GW [A] |

**Structural limits:** no stream-level benchmark (§9(e)); PV before 2001 absent; CSP absent; thin film ignored; rooftop intensity is a 2010 Swiss inventory; no repowering or replacement capacity series (capacity additions only); wind vintage data only 2010–2022; Tier 2 grid excluded; the iron share of the Bayan Obo pool, and copper's non-energy share of every copper pool, are outside the energy streams by design; REE single route split for all oxides; other IOCG mines (Salobo, Candelaria, Sossego, Ernest Henry; about 2.5 % of world copper) left in class B, which would add about 51 % to the 2024 copper factor if they were class A (the largest unresolved lever); D6 shares are placeholders (Q4); all heap-leach/SX-EW copper is treated as class B; no decay, exhalation or seepage in the stream (engine).

## 11. Open questions

None open. All eighteen v0.1 questions are resolved (D74) and indexed in §0. Open data items (not questions): the placeholder series of §2.1 group S, the OD tonnage estimates (`prod_copper_od`, `u_production_od` outside FY2021–23), and the gaps of §10.

## 12. Work required before tests (approved, D74; data staged)

All data items below are **built and staged** under `build/d74_staging/` with the same relative paths as their targets (file list, row counts and per-file changes in `build/d74_staging/APPLY.md`; generator `research/wind_solar/build_d74_staging.py`, deterministic, standard library). They are **not** yet in `data/`: the current validator (v2.5) rejects the two new `commodity_factors.csv` columns. Order of application: (1) spec-blind tests for S1–S3 and L1; (2) validator, JSON schemas and `select` (v2.6, v1.6); (3) copy the staged files into place in one commit and run `python -m pipeline.validate --root .`; (4) stream tests. Every staged file except `commodity_factors.csv` and `commodity_fuel_inputs.csv` already passes the v2.5 validator in a copy of the tree (checked 2026-11-11).

**Schema and library (SCHEMA v2.6, LIB v1.6)**
- S1. `schema/commodity_factors.json` and `pipeline/validate.py` `_check_commodity_factors`: new columns `factor_id` (first, Q2) and `ore_type` (after `region`); key becomes (`commodity`, `component`, `ore_type`, `group`, `tier`, `route`, `residue_type`, `region`, `year_from`, `allocation_variant`); `ore_type` checked against `vocab.json` → `ore_types[<commodity>]`; `commodity:NNNN` ids unique across factor files and added to the V13 universe; commodity enum gains `cast_iron`, `tio2_pigment`.
- S2. New table `data/reference/commodity_fuel_inputs.csv` with `schema/commodity_fuel_inputs.json` and validator checks (SCHEMA §4.13 proposal).
- S3. `vocab.json`: `commodities` += `cast_iron`, `tio2_pigment`; new `ore_types` map (copper: `porphyry_stratiform`, `iocg_olympic_dam` (Q1), `iocg_high_u`, `cu_co_stratiform`, `all`; ree_oxide: `ree_bayan_obo`, `ree_ionic_clay`, `ree_monazite`, `ree_mt_weld` (Q6)); `products.commodity` gains `cast_iron` and `tio2_pigment` too (it must equal `commodities`, SCHEMA §5.5); `commodity_components` becomes `["own_residue"]` (`embedded_fuel` removed: nothing else reads it; the master boolean `embedded_fuel` is unaffected); `fuel_input_fuels` map for §4.13.
- L1. `pipeline/lib/factors.py` `select`: accept `ore_type` (and `commodity`, `component`, already listed) as exact-equality match keys; `read_table` reads `ore_type` as a string (empty → `""`). LIB_SPEC §12 (v1.6) text to be written with S1.
- Spec-blind tests for S1–S3 and L1 first (Phase 2 workflow), then the registry.

**Registry (`data/reference/commodity_factors.csv`, promoted from `research/wind_solar/commodity_factors_draft.csv`)**
- R1. **Staged, 186 rows**: the 208 draft rows minus 17 `superseded` and 5 `embedded_fuel` (186), then the 30 era-mixed `iocg_high_u` rows replaced by 10 `iocg_olympic_dam` rows (1988–2025) and 20 `iocg_high_u` PH+CP rows (two eras) (Q1); REE rows carry their route `ore_type` (Q6); `factor_id` `commodity:0001`–`commodity:0186` in file order (Q2). No region cell holds `;` (the Phase 1 seed `research/wind_solar/footprint_inputs.csv` is corrected in the staged copy, Q14).
- R2. `data/reference/commodity_fuel_inputs.csv`: the five rows of §7.1 (three coal, two electricity).
- R3. `data/factors/wind_solar.csv`: header only (§2.2).
- R4. `data/sources.csv` **staged, 522 rows** (480 + 42): S0430–S0461 (32, with `type`, `rank` and `licence` normalised to `vocab.json` where the proposal used `conference`, `company` or licence strings), S0462–S0470 (9, Appendix A), S1806 (Manzuk, cited by the `cu_co_stratiform` rows) and S1814 (IISD cobalt, cited by a share series). S0448 updated to the read SRS-49 PDF; S1800 not added (Q17).

**Engine parameters (`data/reference/residue_types.csv`, `residue_seepage_by_group.csv`)**, approved (Q14), staged:
- E1. ε triples for 8 residue types and seepage triples for 4 (Appendix A table), basis `modelled`, sources listed there; one per-group seepage override (`cement_kiln_residue`, `K40`).

**Activity (`data/activity/`)**
- A1. `material_intensity.csv` (§2.1 group I) built by a scripted transform of `material_intensity_v2.csv`, committed with the transform under `research/wind_solar/`.
- A2. `wind_solar_shares.csv` (§2.1 group S): placeholders as tabled; the three copper class shares from `copper_class_shares.csv` (OD share removed from A once A3 exists).
- A3. `prod_copper_od`, `u_production_od` (AUS, 1988–2025) after the BHP/WMC annual-report check of `copper_classes.md` §4.1 [A] tonnages; `od_value_share_u` placeholder.

**Docs**: NUCLEAR_SPEC §14 (v1.3, approved); SCHEMA v2.6 (approved text); LIB_SPEC §12 (v1.6); DECISIONS D74 (updated); METHODS §6.2 gains one sentence on the companion fuel table (to write on approval); `commodity_notes.md` §6 red-mud arithmetic (already corrected to $1.5$–$7.5\times10^{13}$ Bq/a).

**Not applied and not proposed:** DRC cobalt rows (D74(b)); Tier 2 grid; superseded copper rows.

## 13. Interpretations settled in advance

1. Empty select keys are `""`; `ore_type` is passed on every call (`""` for families without one).
2. `XWL` for lookups, `XXX` on rows; regional families write the region code.
3. A driver of exactly 0/0/0 gives no rows; a structural 0/0/0 factor result is written; a D6 share of 0 is a structural zero.
4. Run grammar of log entries as coal and oil and gas (`first-last (n years)`).
5. Placeholders are data: the script does not know they are placeholders except by the `PLACEHOLDER` prefix used for the notes suffix and the log.
6. Wind REE uses the offshore and onshore PM classes only; non-PM classes have REE intensity 0 (EESG has no magnets) unless the intensity series says otherwise.
7. The OD ledger shares are read once per year from `od_value_share_u`; both streams use the same row, so the identity of §9(c)4 holds by construction except through rounding.
8. Where this spec says "registry" it means `commodity_factors.csv`; share constants live in activity series because §4.9 factor rows have no key that can name a commodity, ore type or variant (deviation from the D74 wording "placeholder constants in the registry", flagged for Steve).

---

### 13.9–13.20 Clarifications after the spec-blind test round (v1.1, 2026-11-11; orchestrator, within D74)

9. **S1, REE windows.** RE-BO (`ree_bayan_obo`) and RE-IC (`ree_ionic_clay`) rows now start in **1982** (they started in 1990 and 1991). Reasons:
   - wind REE tonnage exists from 1982 (the non-PM classes carry JRC GB-DFIG Nd and Dy);
   - Bayan Obo has produced since the late 1950s, and ionic clays since the 1980s.
   The per-tonne values are carried back unchanged, with a note on each of the 17 rows. `prod_ree_oxide` CHN is **not** extended: the repository has no CHN source before 1990. The stream does not use that series (only B1 does), so its 1990 start limits B1 only.
10. **S2, B1.** The ×1,000 slip is corrected to $10^{14}$ Bq and the period is 1990–2006. The pass rule and result are in §9(e).
11. **S3, steel share.** `steel_bf_route_share` is set to `prod_pig_iron/prod_steel` (`XWL`) in years where the era placeholder lay outside ±0.15 of that ratio. That is 1950–69: the ratio is 0.71–0.75 against the placeholder 0.90, because open-hearth steel was pig iron plus scrap. These rows are flagged in `notes`. 1970–81 (0.80) was inside the band and is kept. The ±0.15 premise is unchanged.
12. **S4, order of operations.** The factor is applied per class, then the classes are summed (§3.2, §4.2 steps 1–6). Bounds are those of the stepwise products. The summed-tonnage form of v1.0 is withdrawn.
13. **Zero tonnage.** A contribution whose step-3 tonnage is exactly 0 at central (a structural zero share or a zero intensity) is skipped: **no row, no `select`, no `no_factor` or `no_driver` entry**. Missing years are treated differently:
    - a capacity year missing **inside** a series' span gives `no_driver`;
    - years **before** a series' first year (wind onshore 1982, offshore and PV 2001) are silent.
14. **S6, log fields.** Every entry has `kind`, `year`, `country`, `group`, `detail`:
    - `no_factor`: `year` first year of the run; `country` the output country (`XXX` or the region); `group` the group; `detail` `<commodity>/<ore_type or ->/<tier>/<residue_type or route>: first-last (n years)`.
    - `no_driver`, `no_intensity`, `placeholder_share`: `year` first year of the run; `country` the series country (`XWL` written as `XXX`); `group` `""`; `detail` `<series>: first-last (n years)`.
    - `no_footprint`: `year`, `country`, `group` all `""`; `detail` `<commodity> (<mi_ series name>)`; once per commodity per build.
    - `attribution`: `year` the first year of the decade (1980, 1990, …); `country` `XXX`; `group` `""`; `detail` `<commodity>: max sigma <value, 4 significant digits> in <year>`.
    - `no_family`, `lib_warning`: as OIL_GAS_SPEC §8 (`year` and `country` empty for `lib_warning`).
15. **S7.** See §7.3: `no_footprint` cannot fire with the staged files.
16. **S8, negligibility.** `end_of_life` and thin film are stated negligible **in this spec only** (§7.3, §9(d)). No log entry and no row or note is written for them.
17. **S9, years walked.** The script walks **1950–2025** only. There is no pre-1950 walk; the pre-1950 file is header-only, and no driver exists before 1982.
18. **S10, φ for the OD identity.** §9(c)4 needs nuclear F8, so it stays contingent until NUCLEAR_SPEC §14 is built.
    - `phi_civil` central is 1 from 1991 (its low bound is 0.85–0.98 through 1991–2025), so the military remainder is zero at central from 1991.
    - The identity is tested at central. It is tested at low and high only where $\phi$ has equal bounds, which is no year today.
19. **S11, exact shares.** These are used at **central value only**, as exact scalars (LIB_SPEC §2.2 does the same for D6 shares): D6 value shares, copper class shares, REE route shares, the charge factor and `od_value_share_u`.
    - In the staged data their low = central = high anyway.
    - Drivetrain, utility and steel-route shares are also low = central = high in the staged data. They enter through `product` as `Bounds`, which gives the same result.
20. **S5, `source_ids` and driver basis.** As OTHER_SPEC §13.14:
    - A row's `source_ids` is the union of its commodity factor's `source_ids` and those of every activity row behind a contribution that was computed (not skipped, §13.13). Those rows are: capacity; drivetrain or utility share; intensity; class, route, charge, steel-route and D6 shares; and `prod_copper_od` and `prod_copper` for CU-OD.
    - The `driver basis` suffix uses only the bases of those contributions' capacity and intensity rows.
    - Share rows give the `share basis` and `allocation basis` suffixes instead (§3.3).

## Appendix A. Engine parameters for the eight residue types (approved, D74 Q14; staged)

Method and conventions as D55–D57, D60 and D62: Rn-222 ε is the emanation coefficient kept as a documented upper bound of the effective exhalation fraction (D60) except for tailings, which copy the D62 `u_tailings` triple (Q8); Rn-220 ε is effective exhalation, emanation × slab factor $f=\frac{L}{H}\tanh\frac{H}{L}$ with $L$ = 0.005 / 0.01 / 0.02 m and the bounds combined as D60 (low = em$_{\mathrm{low}}\,f(L_{\mathrm{low}},H_{\mathrm{high}})$; central = em$_{\mathrm{c}}\,f(L_{\mathrm{c}},\sqrt{H_{\mathrm{low}}H_{\mathrm{high}}})$; high = em$_{\mathrm{high}}\,f(L_{\mathrm{high}},H_{\mathrm{low}})$). Rn-220 emanation is taken as 0.3 / 0.5 / 0.7 of Rn-222 emanation (D60 analogy), now supported by simultaneous measurements on rock powders: Rn emanation 0.055–0.182 against Tn 0.017–0.078 (Sakr et al. 2025, S0467 [R]). Thickness $H$: tailings, red mud, slag heaps and kiln-dust landfills 4–15 m (seepage notes M1 range); process-residue cells and mixed landfill 1–10 m [A]. Seepage methods M1–M4 as `research/seepage/notes.md` §2; no new Monte Carlo was run: triples reuse the sourced M1/M4 distributions or scale them as stated.

| Residue type | ε Rn-222 low / central / high | ε Rn-220 low / central / high | Seepage per a low / central / high | Grade | Sources |
|---|---|---|---|---|---|
| `metal_tailings` | 0.002 / 0.03 / 0.14 | 5.7e-6 / 6.5e-5 / 5.0e-4 | (filled, D55: 7e-7 / 5e-6 / 6e-5) | C | S0242, S0408, S0467; D62 |
| `iron_ore_tailings` | 0.002 / 0.03 / 0.14 | 5.7e-6 / 6.5e-5 / 5.0e-4 | (filled: 7e-7 / 6e-6 / 6e-5) | D | S0242, S0467 |
| `ree_tailings` | 0.002 / 0.03 / 0.14 | 5.7e-6 / 6.5e-5 / 5.0e-4 | (filled: 1e-6 / 1e-5 / 1e-4) | D | S0242, S0404, S0466, S0467 |
| `red_mud` | 0.076 / 0.13 / 0.20 | 7.7e-6 / 8.4e-5 / 7.0e-4 | (filled: 1e-6 / 1e-5 / 1e-4) | B | S0425, S0462, S0463, S0464, S0436 |
| `ree_process_residue` | 0.005 / 0.03 / 0.20 | 7.5e-7 / 4.7e-5 / 2.8e-3 | **7e-7 / 7e-6 / 4e-5** (M4 gypsum analogue) | D | S0242, S0404, S0466, S0970, S0470, S0964 |
| `smelter_slag` | 0.001 / 0.01 / 0.05 | 1.0e-7 / 6.5e-6 / 1.75e-4 | **1e-7 / 1e-6 / 6e-5** | C (ε), D (seepage) | S0436, S0465, S0466, S0202, S0468, S0950, S0954 |
| `cement_kiln_residue` | 0.006 / 0.027 / 0.086 | 6.0e-7 / 1.7e-5 / 3.0e-4 | **7e-7 / 6e-6 / 6e-5** (Ra driver); per-group `K40` override **1.0e-5 / 1.2e-4 / 2.3e-3** | C (ε), D (Ra), C (K) | S0436, S0469, S0950, S0954 |
| `other_commodity_residue` | 0.005 / 0.03 / 0.13 | 7.5e-7 / 4.7e-5 / 1.8e-3 | **7e-7 / 6e-6 / 6e-5** (M1 generic) | D | S0242, S0466, S0950, S0954 |

Bold = newly proposed seepage (the other four types already have seepage from D55).

**Reasoning per row.**
- **Tailings (metal, iron ore, REE).** Sakoda's review (S0242 [E]) gives a representative emanation of 0.17 for mill tailings (n = 77, mostly uranium; maximum over moisture), 0.03 for minerals, 0.13 for rocks. Deep, wet tailings exhale far less than they emanate: the OD field flux (S0408, 0.3–1.27 Bq m⁻² s⁻¹) implies an effective fraction near 0.004 (Phase 1 §8, inventory assumed). The D62 `u_tailings` triple (0.002/0.03/0.14) spans both and is the same physical kind of deposit; using it keeps the OD pool's radon identical in the nuclear and copper ledgers (Q8). REE tailings: monazite grains emanate only 0.002 (S0404 Table 26) and high-melting minerals emanate less (Krupp et al. 2017, 0.083–7 % across 14 minerals, S0466 [R]); kept on the same triple because Bayan Obo tailings are ground carbonate-fluorite ore, not monazite grains; grade D. Rn-220 emanation 0.017 / 0.05 / 0.10 (Sakr range; high 0.6 × 0.17), so Rn-220 is non-zero here unlike `u_tailings` (D62: little thorium); for Bayan Obo, thorium is the point.
- **Red mud.** Dry untreated red mud emanates about 20 % (Jobbágy et al. 2009, S0425/S0463 [R]); Ajka spill red mud 7.6–20 % over 0–28 % moisture (Kovács et al. 2012, S0462 [R]); massic exhalation 75 mBq kg⁻¹ h⁻¹ untreated (Sas et al. 2015, S0464 [R]); highest of 19 residues in Sas et al. 2019 (S0436 [R]). Emanation basis per D60 (Q8 gives the effective alternative 0.003/0.02/0.1). No thoron emanation number exists (Hegedus et al. 2016 report only a qualitative trend), so the D60 analogy applies.
- **REE process residue** (WLP, thorium cakes, cracking residues). No measurement. Emanation from Sakoda mineral (0.03) with soil as the high (0.20) and a low near monazite (0.005). Seepage: Lynas WLP is gypsum-rich and its thorium is refractory (under 5 % recovered even by acid digestion; Al-Areqi et al. 2014, S0470 [E]), so radium leaves with dissolving gypsum: the M4 `coal_fgd_residue` triple (S0964). Thorium seepage is likely lower; no override proposed (conservative).
- **Smelter slag.** High-temperature residues emanate much less (Sas et al. 2019: all 19 residues 0.6–8.6 %, mean 2.7 %, high-temperature ones "significantly lower", S0436 [R]; minerals with melting points ≥ 1400 °C lower, S0466). Porous coal-slag reached 14 % (Somlai et al. 2008, S0465 [R]) but is not vitreous metallurgical slag; it is outside the triple and flagged. Seepage: no slag radium leach data found; Patra et al. 2011 (S0468 [R], 142-day semi-dynamic test) leached 0.05–0.07 % of uranium from copper smelter ("kinker") ash against 0.39–0.59 % from copper tailings, a factor of about 0.13–0.18; applied to the generic M1 Ra centre (6e-6) this gives 1e-6. The high stays at the generic 6e-5 because crushed slag used as aggregate (the dispersed tier) is not vitreous bulk.
- **Cement kiln residue.** Emanation from Sas et al. 2019, whose 19 dry samples include three kiln dusts (0.6–8.6 %, mean 2.7 %; per-sample values only in a figure). Seepage: kiln dust is soluble alkali salts; water removed at least 70 % of potassium at L/S 20 (Seo et al. 2019, S0469 [R]), so by M2 $s_K=\frac{F}{L/S}\times\frac{1000\,I}{H\rho_b}$ with $F/(L/S)$ 0.035 / 0.05 / 0.09 kg/L and the deposit's annual L/S 2.9e-4 / 2.3e-3 / 2.5e-2 L/kg gives 1.0e-5 / 1.2e-4 / 2.3e-3 per a for K-40 (per-group override, SCHEMA §4.12). Radium and uranium keep the generic M1 triple. The table has no rows yet (no CKD tonnage per tonne of cement), so these values matter only once rows exist.
- **Other commodity residue.** An undefined bucket (TiO2 chloride waste, sinter dust, foundry zircon sand, ionic-clay leached ore, silicon residues): Sakoda mineral to rock for emanation; generic M1 for seepage. Grade D. The ionic-clay leached ore (Q15) is the largest user and behaves like soil (emanation about 0.2), so its rows are under-represented by this triple; a separate residue type is a candidate for v2.

**Sources (staged in `build/d74_staging/data/sources.csv`):** S0462 Kovács T., Sas Z., et al. (2012), *Radiation Protection Dosimetry* 152:76–79, doi:10.1093/rpd/ncs192; S0463 Jobbágy V., Somlai J., et al. (2009), *Journal of Hazardous Materials* 172:1258, doi:10.1016/j.jhazmat.2009.07.131 (journal version of S0425); S0464 Sas Z., Szántó J., et al. (2015), *Journal of Environmental Radioactivity*, doi:10.1016/j.jenvrad.2015.06.002; S0465 Somlai J., Jobbágy V., et al. (2008), *Radiation Measurements*, doi:10.1016/j.radmeas.2007.10.028; S0466 Krupp K., Baskaran M., Brownlee S. (2017), *American Mineralogist* 102:1375–1383, doi:10.2138/am-2017-6017; S0467 Sakr S., Sahoo S., et al. (2025), *Environmental Monitoring and Assessment* 197:548, doi:10.1007/s10661-025-13997-5; S0468 Patra A., Sumesh C., et al. (2011), *Journal of Environmental Management*, doi:10.1016/j.jenvman.2010.10.046; S0469 Seo M., Lee S.-Y., et al. (2019), *Environments* 6:113, doi:10.3390/environments6100113; S0470 Al-Areqi W.M., Majid A.Ab., Sarmani S. (2014), *Malaysian Journal of Analytical Sciences* 18(1):221–225. All read through abstracts or search excerpts **[R]** except S0470 **[E]** (full text) and S0242/S0436 (already in the repository). The Sas 2019 per-type values (red mud, slag, CKD) sit only in its Fig. 7; the full text is at https://documentserver.uhasselt.be/bitstream/1942/27647/1/Revised%20manuscript%20R2%20clean.pdf and the figure was not read.

**Not found:** any measured radon or thoron emanation for REE tailings, WLP residue, iron-ore tailings, copper flotation tailings outside uranium mills, or vitreous metallurgical slag; any slag radium leach test; any CKD radium leach test.

## Change log

| Date | Change |
|---|---|
| 2026-11-11 | v0.1 DRAFT. D74 recorded; open questions Q1–Q18; Appendix A residue parameters. |
| 2026-11-11 | **v1.1.** Test-round clarifications S1–S11 (§13.9–§13.20): REE windows from 1982; B1 corrected to $10^{14}$ Bq over 1990–2006, with a pass rule; steel-route share taken from pig iron where out of band; per-class stepwise arithmetic. |
| 2026-11-11 | **v1.0 FINAL.** Steve approved all resolutions (§0). OD-only and PH+CP rows, factor ids, rooftop rule fixed; data staged under `build/d74_staging/` (§12). |
