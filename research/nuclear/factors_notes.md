# Nuclear factor registry: notes (Task 2.1, step 1)

Producer draft, 27 October 2026. Companion to `data/factors/nuclear.csv` (1,685 rows, `nuclear:0001`-`nuclear:1685` after round 3, section 9) and `research/nuclear/sources_factors.csv` (S1000, S1001, S1003, S1004, S1005; S1002 was not needed because NUREG/CR-2907 is already S0121). Mirrors `research/coal/factors_notes.md`. The generator lives outside the repo (scratchpad) and is deterministic; row order is mining, ISL, conversion, reactor effluents, spent fuel and in-core, reprocessing, sea disposal, accidents.

## 0. Engine reading (conventions used)

- Values are for the HEAD nuclide of each group; the pipeline applies the multiplier (D24/D42). Pu239 rows are Pu-239 only (multiplier 1.9994 applies there).
- Unit `Bq/t` (driver `u_production`, t U), `Bq/GWa` (driver a TWh series; 1 GWa = 8.766 TWh converts automatically), `Bq/GW` (driver `nuc_cap_*`, giving a stock for `standing_inventory`), `Bq` (event rows, no driver) and `1` (shares).
- Reactor type is carried by `driver_series` (`nuc_gen_<type>`, `nuc_cap_<type>`), because factor rows have no substream column. Types: pwr, bwr, phwr, gcr, lwgr, fbr.
- Low/central/high are about the 5th/50th/95th percentiles (METHODS 11). Spread factors are stated per row and combined in log-quadrature. Structural zeros (ISL before it existed) are stored as 0/0/0 with `below_detection` false.
- Routine transfers (`conv_enrich_fab`, `reprocessing`, `sea_disposal`): the row is the liberated amount; the script writes the transfer_out/transfer_in pair. Reactor effluents and milling dust/process radon are plain Liberated flows with a route.
- Chronic radon from tailings and seepage are engine processes: no rows. Process radon (mine ventilation, ISL, mill) is entered under its route.
- Validation: see section 6.

## 1. Factor table (by family; full values in the CSV)

### 1.1 Row counts by stage
| Stage | Rows |
|---|---|
| u_mining_conv | 2 |
| u_mining_isl | 15 (1 radon row + 14 ISL-share rows, unit 1) |
| u_milling | 20 (process radon, 7 dust, 3 product, 9 tailings) |
| conv_enrich_fab | 22 |
| reactor_operation | 1,126 (effluents about 729, in-core standing inventory about 397) |
| spent_fuel | 296 |
| reprocessing | 101 |
| sea_disposal | 13 |
| accident | 71 |

### 1.2 Mining, milling (driver `u_production`, Bq per t U, region XWL unless stated)
| Item | Group, route | Low / central / high | Basis |
|---|---|---|---|
| Mine radon 1950-79 | Rn222+, air_ventilation | 1e11 / 3.8e11 / 1.5e12 | extrapolated |
| Mine radon 1980-2025 | same | 1e11 / 3.0e11 / 9e11 | compiled (66 TBq/GWa at 220 tU/GWa) |
| ISL radon (ISL tonnage only) | Rn222+, air_process_vent | 3.4e9 / 1.36e10 / 5.4e10 | modelled |
| Mill process radon (all tonnage) | Rn222+, air_process_vent | same | modelled |
| Mill dust | U238+, U234 1.8e6; Th230, Ra226+, Pb210+, Po210 9.1e4; U235+ derived 8.4e4 | factor 3 | modelled |
| U product (sealed_fuel_cycle) | U238+ 1.2347e10, U234 1.2347e10, U235+ 5.69e8 | +-3 % | modelled |
| Tailings (impounded, u_tailings) | Ra226+ 1.2e10 (retention 0.98), Th230 1.2e10 (0.95), Pb210+ and Po210 (0.90), Pa231 and Ac227+ (0.95 x 0.0461), residual U (1-R)/R with R 0.95 | see CSV | modelled |
| ISL share (unit 1) | KAZ, UZB, USA, XWL default by era | see CSV | extrapolated / compiled |

The script applies: non-ISL tonnage = `u_production` x (1 - ISL share) x `phi_civil`.

### 1.3 Reactor effluents (driver `nuc_gen_<type>`, Bq/GWa, tier liberated, stage reactor_operation)
- Source: UNSCEAR 2008 Table 17 (1970-2002 periods), 2000 Table 37, 2016 Table 11 (2010; AGR separate). Eras: 1950-79, 1980-89, 1990-2002, 2003-09 (interpolated, geometric mean of the 1998-2002 and 2010 values), 2010-25 (2010 value carried; GCR split 2010-14 and 2015-25 by AGR share).
- Direct groups: H3 (air and liquid), C14, I131, S35 (GCR/AGR only).
- Mixed UNSCEAR categories (noble gases, particulates, other liquid) are baked per group as total x composition share. The shares are JUDGEMENT:
  - PWR noble: Xe133 .35, Xe135 .20, Kr85 .12, Kr88+ .10, Kr87 .06, Kr85m .06, Xe138+ .05 (shifted from the GRS-8 design spectrum, S1004, towards Xe-133 and Kr-85 for holdup).
  - BWR noble: Xe138+ .55, Xe133 .10, Xe135 .10, Kr87 .08, Kr88+ .06, Ar41 .06, Kr85m .03, Kr85 .02 (anchored on Quad Cities 2018, S1003, with Xe-135m redistributed).
  - GCR noble: Ar41 .80 (assumed, Ar-41 from air activation), remainder Xe/Kr. PHWR: Ar41 .45. LWGR and FBR: generic.
  - Particulates: Co60 .30, Cs137+ .25, Cs134 .12, Co58 .10, Mn54 .08, Sr90+ .06, Zr95+ .05, Ru106+ .04 (GCR: Cs137+ .35, Sr90+ .20, Co60 .20 ...).
  - Other liquid: Co58 .22, Co60 .20, Cs137+ .12, Fe55 .12, Cs134 .08, Mn54 .08, Ni63 .05, Sr90+ .04 (GCR pond effluent: Cs137+ .40, Sr90+ .35, Co60 .10, Cs134 .08, Fe55 .07).
  - Shares are renormalised over the groups listed. Minor groups (Sb125, Tc99, Ag110m, Xe131m, Xe133m and others) are omitted. FBR particulates and liquids are omitted.
- Spread: 2.0 (plant-to-plant) x period variation x share spread 1.6/2.0. For PWR/BWR noble gases the 2010-25 low bound is the US 2021 median per reactor (S0121), which is 70-100 times below the UNSCEAR mean.

### 1.4 Spent fuel and in-core inventory
- Spent-fuel arisings (stage spent_fuel, tier sealed_fuel_cycle, Bq/GWa) are per GWa of electricity, so the driver follows the fleet mix and the thm series is a cross-check only.
  - LWR (PWR, BWR): 35 groups from the Carter/JRC table (`spent_fuel_inventory_derived.csv`), back-decayed to cooling time 0 (Nb-95 = Zr-95 at discharge; Am-241 and Pu-238 ingrowth removed by Bateman), log-log interpolated to era burnup 18/28/39/47 GWd/t, times 365.25/(0.33 B) tHM per GWa. Adjacent equal eras are merged.
  - PHWR, LWGR, GCR: 13 fission-product groups from ENDF/B-VIII.0 yields (S0141) and a fission mix. Actinides and activation products are a gap.
- In-core standing inventory (stage reactor_operation, tier sealed_in_core, Bq/GW, driver `nuc_cap_<type>`):
  - LWR long-lived groups: mean over batches (3 PWR, 4 BWR assumed) at burnups B(i-0.5)/n, times core mass (PWR 89.9 t/GWe from S0100; BWR 126 t/GWe from an assumed 24 MWth/t).
  - Short-lived groups (I131, I133, Te132+, Xe133, Xe135, Ba140, La140, Mo99+, Cs136, Ce141, Te129m+, Ru103+, Zr95+, Nb95, Sr89, Y91): ENDF saturation model, $A = Y F\left[1-\frac{1-e^{-\lambda T}}{\lambda T}\right]$.
  - PHWR, LWGR, GCR: fission products only.

### 1.5 Conversion, enrichment, fabrication (driver `elec_gen_nuclear`, Bq/GWa)
UNSCEAR 1988 Table 13 model facility summed over the three steps (U238+/U234 air 131.6 MBq/GWa, aquatic 274; U235+ 6.16 and 6.2; Th230 air 0.4; Th232 and Th228+ 0.022; Ra226+ aquatic 0.11). The duplicate Th-234 rows in the extraction are not added. Aquatic rows are scaled by OSPAR fabrication/enrichment alpha ratios to 1989: 1.0 (to 1988), 0.384 (1989-99), 0.223 (2000-09), 0.032 (2010-25). Air is not scaled.

### 1.6 Reprocessing (no driver yet; Bq per GWa of civil fuel reprocessed)
- 1950-69 UNSCEAR 2000 Table 42 (extrapolated). 1970-97 Table 41, 5 periods, 6 air and 6 liquid nuclides. 1998-2002 UNSCEAR 2008 Table 20 totals divided by an implied throughput of 62.6 GWa/a (from Kr-85). 2003-2025 UNSCEAR 2016 Table 13, La Hague per GWa, extended to Co60, Mn54, Co58, Cs134, I131, Am241.
- D49 split for the Pu-239+240 report (2003-25): Pu-240/Pu-239 activity ratio 1.59 for LWR fuel at about 45 GWd/t (range 1.31-1.85 at 30-55), so Pu239 share 0.386 and Pu240 share 0.614.

### 1.7 Sea disposal (unit 1 shares of dumped activity; Atlantic, TECDOC-1105 Table IV)
H3 0.344; alpha 0.0149 (placeholder split Pu239, Pu240, Am241, Pu238); non-tritium beta-gamma 0.641 split equally over Sr90+, Cs134, Cs137+, Fe55, Co58, Co60, C14, I125 (placeholder).

### 1.8 Accidents (Bq, region of the event, no driver)
- Chernobyl-4: 34 core-inventory rows (UNSCEAR 2000 Annex J Table 1) and 25 release rows (UNSCEAR 2008 Annex D Table 1, summing to the events.csv 1.206e19 Bq).
- Fukushima 1-3: 7 atmospheric rows and 3 ocean rows.
- TMI-2: Xe133 and I131.
- Generic in-core rows (section 1.4) supply the inventory for TMI and Fukushima.

## 2. Cross-checks

| Check | Model | Reference |
|---|---|---|
| Fukushima 1-3 (2.03 GWe BWR), Cs137 | 685 PBq | 700 PBq (S0106) |
| Same, I131 | 6,127 PBq | 6,000 PBq (S0106) |
| Chernobyl-4 Cs137 (3,200 MWth, B 21.8 GWd/t, T 3.55 y) | about 250 PBq | 260 PBq (S0104) |
| PWR Cs137, Carter batch mean vs ENDF at B 47 | 2.44e17 | 2.55e17 Bq/GWe (4 % apart) |
| LWR Cs137 arisings: ENDF vs Carter (B 47) | 1.3e17 | 1.2e17 Bq/GWa |
| Mine radon: 1993, 2000 and 2016 normalisations | 0.30 TBq/t each | 4.7e11 Bq/t in 1988 (inside bounds) |
| Reprocessing 2010 La Hague Kr-85 | 4,700 TBq/GWa | 6,900 (1995-97) |
| US 2021 medians (S0121) per reactor, H3 air BWR/PWR | 1.4 and 1.2 TBq | 1.3 and 1.5 TBq/GWa UNSCEAR |
| Same, liquid H3 PWR | 19.9 TBq | 18 TBq/GWa |
| Same, C-14 BWR and PWR | 0.57 and 0.34 | 0.13 and 0.083 (US is 4 times higher) |
| Same, noble gases BWR | 0.18 TBq | 18 TBq/GWa (100 times lower) |

Other cross-checks and discrepancies:
- UNSCEAR 2008 GCR noble gases 1998-2002 (28 TBq/GWa) are inconsistent with 2016 Magnox (1,700) and AGR (19) at the RDS-2 capacity weights; the series has a step in 2010 (G13).
- Operational LLW (UNSCEAR 2008 Table 21, about 1e10 Bq/MWe a) is about 1e-4 of the spent-fuel activity per GWa and is not entered (G7).
- The thm series is not used. Its LWGR burnup of 12 GWd/t before 1990 conflicts with the 21.8 GWd/t equilibrium discharge burnup implied by S0104.
- Site-level 2010 absolute rates (Sellafield, La Hague, Mayak) are not entered and are cross-checks only.

## 3. Gap register

| # | Item | Why no row | Blocks the engine? |
|---|---|---|---|
| G1 | Civil reprocessing throughput series (GWa/a) | does not exist; proposed `nuc_reprocessed_gwa` (UNSCEAR 2000 Table 43 periods, implied 62.6 GWa/a for 1998-2002, none after 2002) | yes, for reprocessing |
| G2 | Annual sea-dumped activity by country | TECDOC-1105 gives only country totals, 1946-1993; proposed `nuc_sea_dumped_tbq` | yes, for sea disposal |
| G3 | Actinides and activation products for PHWR, LWGR, GCR, FBR; any HTGR/other | no inventory data | no, a known undercount |
| G4 | Mine water, waste rock (memo), ISL pond residue, dispersed tailings fill (Grand Junction share) | no quantitative source found | no |
| G5 | Conversion and enrichment beta discharges (Tc-99, Th-234) and air trends | not decomposed | no |
| G6 | Th-230, Pa-231, Ac-227 tailings retention | judgement; USGS gives only 30-90 % Th dissolution | no |
| G7 | Operational LLW and decommissioning waste, construction | composition unknown; decommissioning has no residue type | no |
| G8 | Pu split for Magnox reprocessing | extrapolated ratio 0.68 is unreliable at 5 GWd/t | no |
| G9 | Civil fractions: Sellafield B205, Marcoule, Mayak RT-1, Soviet Arctic dumps | rr05 is qualitative; undocumented throughput means exclusion | yes, for these sites |
| G10 | ISL ponds | see G4 | no |
| G11 | Facility country for conversion, enrichment and fabrication | applied to the burner's electricity | no |
| G12 | Np-239 Chernobyl inventory (58,100 vs 27,000 PBq), TMI Kr-85/Xe-133m, Fukushima Cs-134 ocean | ambiguous or missing | no |
| G13 | GCR noble-gas inconsistency | see section 2 | no |
| G14 | S-35 before 2010; I-131 liquid; Sb-125, Tc-99 effluents | not reported by UNSCEAR | no |

## 4. Choices for Steve to confirm

1. Bake composition into per-group rows (about 400 judgement-based rows) rather than a total-plus-share scheme, because `select` cannot separate noble gases from particulates (same keys).
2. Composition shares (1.3) and the omitted minor groups; Ar-41 dominance for gas-cooled and heavy-water reactors.
3. Reactor type is carried by `driver_series`; GCR is left as reported by UNSCEAR to 2002, then split Magnox/AGR from the RDS-2 capacity weights.
4. The 2010 UNSCEAR value is carried to 2025 (extrapolated), with the US median as the low bound for PWR/BWR noble gases.
5. Spent fuel as arisings per GWa electricity at discharge, with the thm series as a cross-check only. LWR burnup eras 18/28/39/47; LWGR 21.8.
6. In-core inventory: Carter batch mean for long-lived groups, ENDF saturation for short-lived ones, assumed 24 MWth/t and 4 batches for BWR, assumed 19 kg U/bundle for PHWR.
7. Reprocessing: per GWa of civil fuel reprocessed with a NEW driver. The 1998-2002 throughput is implied from Kr-85 (G1). The 2003-25 values extend the La Hague 2010 figures.
8. Mill balance: R 0.95, retention 0.98/0.95/0.90, and the Pu-239+240 split ratio of 1.59.
9. ISL shares by country (judgement outside the WNA statements); replace from Red Book Table 7.3 if extracted.
10. Accident event data (inventory and releases) carried as factor rows.
11. Sea disposal: placeholder shares; Soviet Arctic dumps excluded (naval).
12. Conversion, enrichment and fabrication driven by `elec_gen_nuclear`, with the OSPAR aquatic scaling.
13. Spread classes (FCLASS in the generator): 1.25-3.0 by group type, judgement.

## 5. Proposed stream-script outline (for `docs/NUCLEAR_SPEC.md`)

1. u_mining_conv (country c, year y): $T_{c,y} = $ `u_production` x (1 - ISL share) x `phi_civil`. Rows: Rn222+ ventilation.
2. u_mining_isl: ISL tonnage = production x ISL share x phi. Rows: ISL radon. The pond residue is a gap.
3. u_milling: all civil tonnage. Rows: process radon, dust, U product (sealed_fuel_cycle), tailings (impounded, residue u_tailings). Civil tokens `civil:*`.
4. conv_enrich_fab: `elec_gen_nuclear` x factor as a routine transfer (sealed_fuel_cycle to liberated). Country rows: none, XWL applies.
5. reactor_operation: effluents, `nuc_gen_<type>` x rows (XXX country; the type series are XWL only); standing inventory, `nuc_cap_<type>` x rows (GW). Reactor shutdown follows the capacity series.
6. spent_fuel: `nuc_gen_<type>` x arisings, tier sealed_fuel_cycle.
7. reprocessing: needs `nuc_reprocessed_gwa`, then as 4. `civil:throughput`.
8. sea_disposal: needs `nuc_sea_dumped_tbq` x shares.
9. accident: for E002, E004 and E013, take the transfer_out from sealed_in_core = event inventory (Chernobyl rows; otherwise generic rows x unit capacity), release rows to liberated, and the remainder to sealed_damaged_core.
10. Pu D49: use the Pu239/Pu240 rows as given; do not re-split.

## 6. Residue-type proposals (not applied to `residue_types.csv`)

- u_tailings: ε222 low/central/high 0.002 / 0.03 / 0.14, below the 0.2 ceiling (judgement, from dry tailings emanation of about 0.2 and moisture and cover reducing exhalation). ε220 about 0 (little thorium). Seepage already present.
- u_waste_rock, u_process_residue, isl_pond_residue: ε/seepage gaps. Tentative: waste rock reuses the generic M1 triple 7e-7 / 5e-6 / 6e-5.
- New type needed: `nuclear_decom_waste` (decommissioning).

## 7. Validation

- Scratch copy with `sources_factors.csv` merged into `data/sources.csv`: nuclear.csv raises no issues; the only remaining errors are oil_gas.csv ones (S12xx sources pending from another task).
- Real tree: nuclear.csv has only T04 unresolved-source errors for the five S10xx IDs, which the orchestrator must merge.

## 8. Inaccessible or unretrieved (most important first)

1. Rogovin TMI report (S0138; 16-byte stub). 2. Red Book Table 7.3 ISL split (S0113). 3. NUREG/CR-2907 totals (per-plant only). 4. CANDU bundle mass (not stated in the CANTEACH documents). 5. Magnox/AGR core data. 6. Grand Junction tailings fill (found only energy.gov fact sheets; no number).

## 9. Round 3 additions (NUCLEAR_SPEC section 12 items R1-R8, 2 November 2026)

Rows `nuclear:1667`-`nuclear:1685` appended (19 rows); `nuclear:1583`-`1595` changed (year_from only). New sources S1013-S1017 are in `research/nuclear/sources_round3.csv` (to be merged into `data/sources.csv`; until then validation reports T04 for them). `substream` is empty on every new row.

### 9.1 R1: sea-disposal shares from 1946
`year_from` 1950 to 1946 on the 13 share rows `nuclear:1583`-`1595` (H3; Pu239, Pu240, Am241, Pu238; Sr90+, Cs134, Cs137+, Fe55, Co58, Co60, C14, I125). `year_to` (1993), values, notes and sources unchanged. The descriptions already said "1946-1993". The 1946-49 extension is **extrapolated** in the sense that the Atlantic composition of TECDOC-1105 Table IV is applied to the earliest US and UK dumps; the `basis` cell is not changed (it stays `compiled`; the extrapolation is stated here and in NUCLEAR_SPEC 5.3).

### 9.2 R2/R3: per-event unit capacity rows (NUCLEAR_SPEC 7.2)
| Row | Event | Region, year | Low / central / high (GW) | Sources |
|---|---|---|---|---|
| `nuclear:1668` | E013 Fukushima Daiichi 1-3 | JPN, 2011 | 1.959 / 1.959 / 2.028 | S1014, S1015, S1016, S0106 |
| `nuclear:1669` | E002 TMI-2 | USA, 1979 | 0.872 / 0.880 / 0.892 | S1013, S1017, S0138 |

- **Fukushima.** Net reference unit power (IAEA PRIS via WNA database): 439 + 760 + 760 = 1,959 MWe. The 2.03 GW(e) of the spec is the **gross** sum (460 + 784 + 784 = 2,028 MWe); the spec's "net 460+784+784" is a mislabel. Central is the net sum as the spec requires; high is the gross sum. Low = central (no published alternative net rating).
- **TMI-2.** The indicative 0.906 GW(e) could **not** be verified and no source found gives it. Sources found: PRIS reference unit power net 880 MWe (gross 959); Rogovin Vol. 2: 872 MWe at 97.928 % power on 28 March 1979, "authorized net MWe (892 MWe)", and the licensee's 880 MWe statement of 26 October 1978. Central 0.880, bounds 0.872 and 0.892. The Rogovin staged copy was searched as text (Vol. 1 and the three parts of Vol. 2); nothing else gives a net rating.
- Key and description rule (NUCLEAR_SPEC 7.2): unit `GW`, tier/group/route/residue empty, description begins with the event ID.

### 9.3 R5: Chernobyl Np-239 inventory (`nuclear:1667`)
Stage `accident`, tier `sealed_in_core`, group `Np239`, region `SUN`, 1986, unit `Bq`: low 2.7e19, central 5.81e19, high 7.55e19. Central: UNSCEAR 2000 Annex J Table 1, "values used in this Annex" column, 58,100 PBq (S0104; read directly from the PDF: the table also shows 49,600 PBq in the burnup-corrected B1/I2 set and 140 PBq in the decay-corrected first column). Low: OECD-NEA 2002 Table 1, 27,000 PBq (S0710; 3.5 % released = 945 PBq, the UNSCEAR 2000 release value; the NEA table's own "95" release is the typo already noted in events.csv). High: central x 1.3, the spread used on the other 34 E004 inventory rows; **no source gives a value above the central**, so the high bound is a judgement. Closes the Np-239 part of G12; the note on `nuclear:1596` ("Np-239 is NOT entered") is now stale (row left unedited).

### 9.4 R6: Church Rock composition (`nuclear:1670`-`1685`)
Sixteen unit-`1` rows, `u_milling`, `USA`, 1979, residue `u_tailings`, basis `modelled`, low = central = high (the event's own bounds carry the uncertainty). Seven liquor rows (tier `liberated`, route `water_spill`: U238+, U234, U235+, Th230, Ra226+, Pb210+, Po210) and nine solids rows (tier `dispersed`, route empty: the same seven plus Pa231, Ac227+). Central shares sum to 1.00000 (the sum of the printed values is 1 to better than 1e-6).

- **Liquor.** CDC memo (S0109) Table 1, "typical UNC tailings liquid" concentration (pCi/L): U-238 5.4e3, U-234 5.4e3, Th-230 1.5e5, Ra-226 4.0e2, Pb-210 4.0e2, Po-210 4.0e2, Bi-210 4.0e2 (OCR is poor; Po-210 reads "4.0x50 2" and is taken as 4.0e2). U-235 is not given: 0.0461 x U-238. Activity = concentration x 3.56e8 L x 0.037 Bq/pCi; sum over the seven groups 2.137e12 Bq (Th-230 92.5 % of it).
- **Solids.** Registry tailings factors `nuclear:0015`-`0023` (Bq per t U) x 0.998 t U (1,100 short tons of tailings at an assumed 0.1 % U; the grade is a judgement and not verified). Sum 5.08e10 Bq.
- **Shares** = each activity / (liquor + solids) = 2.188e12 Bq. Liquor 97.7 %, solids 2.3 %. Halving or doubling the assumed grade moves the solids share between about 1.2 % and 4.5 %.
- **Gross alpha to head activity.** events.csv E003's 46 Ci (1.702e12 Bq) is a gross-alpha figure. In acidic liquor the listed alpha emitters (U-238, U-234, U-235, Th-230, Ra-226, Po-210) are all measured as separate nuclides and ingrown short-lived progeny are not present in equilibrium, so gross alpha is approximately the sum of the alpha *heads*. The only non-alpha group is Pb210+ (0.25 % of the liquor total), which is kept so that the rows sum to the event central. The rows therefore equal the event central to better than 1e-4 by construction (share x A_e), and the head sum is within 0.5 % of the gross alpha. Limit: the engine applies group multipliers (U238+ 3, Ra226+ 6) that assume secular-equilibrium progeny, which the liquor does not have, so the engine total overstates alpha progeny slightly (U238+ and Ra226+ are 3.3 % and 0.2 % of the activity).
- **Unverified column reading.** The 46 Ci equals 3.56e8 L x 1.29e5 pCi/L, i.e. the liquor volume times the river gross-alpha peak (1.28e5 pCi/L, S0109), and the typical liquor gives 58 Ci. So the 46 Ci looks like **liquor** gross alpha, which contradicts the events.csv statement that activity "is on the solids fraction only". The composition above follows the arithmetic (liquor dominant). Flag for the events owner.
- Pa231 and Ac227+ have no liquor row (no data); U-235 series members other than the natural ratio are not otherwise constrained.

### 9.5 R8: validity to 2025
Checked per family (stage, driver_series, group, tier, route, residue_type, region) over `u_mining_conv`, `u_mining_isl`, `u_milling`, `reactor_operation`, `spent_fuel`, `conv_enrich_fab` and `reprocessing` (502 families including `sea_disposal`): every family has a row with `year_to` = 2025, so **no `year_to` was extended and nothing is extrapolated**. Only one internal gap: `reprocessing` I131 `air_stack` has no row 1998-2002 (known; UNSCEAR 2008 gave none).

### 9.6 R4 and R7
R4: sources S1013-S1016 (WNA reactor database pages, PRIS data) and S1017 (Rogovin Vol. 2) are new; S0104, S0710, S0109, S0709, S0724, S1000, S0106 and S0138 already exist. The Np-239 source is S0104/S0710 (existing); the Church Rock source is S0109 (existing). R7: left as is (`driver_series` cells of the reprocessing and sea-disposal rows stay empty, which the spec allows).
