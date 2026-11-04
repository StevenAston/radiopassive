# Nuclear factor registry: notes (Task 2.1, step 1)

Producer draft, 27 October 2026. Companion to `data/factors/nuclear.csv` (1,727 rows, `nuclear:0001`-`nuclear:1727` after D65, section 10; 1,685 rows after round 3, section 9) and `research/nuclear/sources_factors.csv` (S1000, S1001, S1003, S1004, S1005; S1002 was not needed because NUREG/CR-2907 is already S0121). Mirrors `research/coal/factors_notes.md`. The generator lives outside the repo (scratchpad) and is deterministic; row order is mining, ISL, conversion, reactor effluents, spent fuel and in-core, reprocessing, sea disposal, accidents.

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
- Spread: 2.0 (plant-to-plant) x period variation x share spread 1.6/2.0. For PWR/BWR noble gases the 2010-25 low bound is the US 2021 median per reactor (S0121), which is 70-100 times below the UNSCEAR mean (D65: the median used here is now the all-nuclide median, section 10.2; the old statement compared UNSCEAR with the three-nuclide median).

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
| Same, noble gases BWR | 0.18 TBq (CORRECTED D65: 0.18 TBq is the three-nuclide median; the all-nuclide median is 21.0 Ci = 0.78 TBq, 4.3 times higher; PWR 1.0 Ci = 0.037 TBq vs 0.2 Ci, 4.6 times higher; fleet means are about 23 (BWR) and 15 (PWR) times below UNSCEAR, not 70-100) | 18 TBq/GWa |

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
| G4 | Mine water, ISL pond residue; (D65: US waste rock memo series and Grand Junction fill now have rows, sections 10.6-10.7) | no quantitative source found for the rest | no |
| G5 | Conversion and enrichment beta discharges (Tc-99, Th-234) and air trends | not decomposed | no |
| G6 | Th-230, Pa-231, Ac-227 tailings retention | judgement; USGS gives only 30-90 % Th dissolution | no |
| G7 | Operational LLW and decommissioning waste, construction | composition unknown; decommissioning has no residue type | no |
| G8 | Pu split for Magnox reprocessing | extrapolated ratio 0.68 is unreliable at 5 GWd/t | no |
| G9 | Civil fractions: Sellafield B205, Marcoule, Mayak RT-1, Soviet Arctic dumps | rr05 is qualitative; undocumented throughput means exclusion | yes, for these sites |
| G10 | ISL ponds | see G4 | no |
| G11 | Facility country for conversion, enrichment and fabrication | applied to the burner's electricity | no |
| G12 | Np-239 Chernobyl inventory (58,100 vs 27,000 PBq), Fukushima Cs-134 ocean (D65: TMI Xe-133m now a row; Kr-85 was not released) | ambiguous or missing | no |
| G13 | GCR noble-gas inconsistency | see section 2 | no |
| G14 | S-35 before 2010; I-131 liquid; Sb-125, Tc-99 effluents | not reported by UNSCEAR | no |

## 4. Choices for Steve to confirm

1. Bake composition into per-group rows (about 400 judgement-based rows) rather than a total-plus-share scheme, because `select` cannot separate noble gases from particulates (same keys).
2. Composition shares (1.3) and the omitted minor groups; Ar-41 dominance for gas-cooled and heavy-water reactors.
3. Reactor type is carried by `driver_series`; GCR is left as reported by UNSCEAR to 2002, then split Magnox/AGR from the RDS-2 capacity weights.
4. The 2010 UNSCEAR value is carried to 2025 (extrapolated), with the US median as the low bound for PWR/BWR noble gases.
5. Spent fuel as arisings per GWa electricity at discharge, with the thm series as a cross-check only. LWR burnup eras 18/28/39/47; LWGR 21.8.
6. In-core inventory: Carter batch mean for long-lived groups, ENDF saturation for short-lived ones, assumed 24 MWth/t and 4 batches for BWR, 19.3 kg U/bundle for PHWR (D65; was an assumed 19 kg U).
7. Reprocessing: per GWa of civil fuel reprocessed with a NEW driver. The 1998-2002 throughput is implied from Kr-85 (G1). The 2003-25 values extend the La Hague 2010 figures.
8. Mill balance: R 0.95, retention 0.98/0.95/0.90, and the Pu-239+240 split ratio of 1.59.
9. ISL shares by country (judgement outside the WNA statements); D65 replaced them from the Red Books 2003 and 2026 (there is no Table 7.3 in the 2003 edition; section 10.4).
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
- u_waste_rock, u_process_residue, isl_pond_residue: ε/seepage gaps. Tentative: waste rock reuses the generic M1 triple 7e-7 / 5e-6 / 6e-5. (D65: u_waste_rock ε222 is now 0.1 / 0.3 / 0.5 in `residue_types.csv`, section 10.6.)
- New type needed: `nuclear_decom_waste` (decommissioning).

## 7. Validation

- Scratch copy with `sources_factors.csv` merged into `data/sources.csv`: nuclear.csv raises no issues; the only remaining errors are oil_gas.csv ones (S12xx sources pending from another task).
- Real tree: nuclear.csv has only T04 unresolved-source errors for the five S10xx IDs, which the orchestrator must merge.

## 8. Inaccessible or unretrieved (most important first)

(Status after D65 / round 2: items 1-4 and 6 are now retrieved or closed, section 10; only Magnox/AGR core data (item 5) remains unresolved.) 1. Rogovin TMI report (S0138; 16-byte stub). 2. Red Book Table 7.3 ISL split (S0113). 3. NUREG/CR-2907 totals (per-plant only). 4. CANDU bundle mass (not stated in the CANTEACH documents). 5. Magnox/AGR core data. 6. Grand Junction tailings fill (found only energy.gov fact sheets; no number).

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

## 10. D65 revisions (Steve, 2026-11-04; proposals in `research/nuclear/papers_round2.md`, `research/oil_gas/papers_round3.md` section 7)

Every changed row carries a notes prefix `REVISION D65 (Steve, 2026-11-04): ...` with the old low/central/high where it is not in the table below. Sources S1006-S1012 merged into `data/sources.csv`; S0121, S0138 and S1005 replaced by their corrected round-2 rows. Rows now run `nuclear:0001`-`nuclear:1727` (42 new rows, `nuclear:1686`-`1727`). Validation: see the orchestrator report.

### 10.1 CANDU bundle mass (19 kg U assumed -> 19.3 kg U, S1008)
- Core mass $4560\times19.3\ \text{kg}=88.0$ tU; specific power $2061/88.0=23.4$ MWth/tU (was 23.8); residence $T=7250/23.4=309.8$ d $=0.848$ a (was $7250/23.8=304.6$ d $=0.834$ a), +1.6 %.
- Applied to every PHWR row derived from bundle mass: the 13 spent-fuel arisings rows `nuclear:1046`-`1058` and the 25 in-core standing-inventory rows `nuclear:1407`-`1431` (38 rows; the PHWR effluent rows do not depend on it). Each of low, central and high is multiplied by the ratio for the group's head nuclide (decay constant $\lambda$ from `nuclides.csv`): arisings $f(T)=(1-e^{-\lambda T})/T$; in-core inventory (uniform ages 0 to $T$, also used for the saturation groups) $g(T)=1-(1-e^{-\lambda T})/(\lambda T)$; ratio $f(0.8476)/f(0.8340)$ or $g(0.8476)/g(0.8340)$. Ratios: arisings 0.984 (Nb-95) to 1.000; in-core 1.00003 to 1.0166 (Cs-135, Tc-99, Sr-90 largest; the in-core mean age rises with $T$ for long-lived groups). Cs-137 arisings 0.99984, Kr-85 0.99957. Every row moves by under 2 %.
- Limits: the ratio treats each group as its head nuclide (chain ingrowth for Zr95+, Ru106+, Ce144+ is ignored); the fission mix, yields and eta are unchanged. Bundle mass is 37-element; the Pickering 28-element bundle (20.2 kg U) is not separated. Basis stays `modelled`; sources S1008 added.

### 10.2 US effluent revisions N1-N16 (NUREG/CR-2907 v27, S0121; 2010-25 rows; US-versus-UNSCEAR population caveat applies: UNSCEAR centrals are world means, the US is one low-effluent fleet)
| # | Row(s) | Old (low / central / high) | New |
|---|---|---|---|
| N1 | PWR noble total low; BWR noble total low | $8.0\times10^{9}$; $1.83\times10^{11}$ | $3.7\times10^{10}$; $7.8\times10^{11}$ (distributed over the groups by share) |
| N2 | PWR noble central 2015-25 | $5.8\times10^{12}$ | $1.5\times10^{12}$ (new rows `1686`-`1692`; 2010-14 rows keep $5.8\times10^{12}$) |
| N3 | BWR noble central 2015-25 | $1.8\times10^{13}$ | $8.5\times10^{12}$ (new rows `1693`-`1700`) |
| N4 | PWR noble shares (raw, renormalised) | Xe133 .35, Xe135 .20, Kr85 .12, others Kr88+ .10, Kr87 .06, Kr85m .06, Xe138+ .05 | Xe133 .55, Xe135 .05, Kr85 .05, others unchanged (sum .92 renormalised) |
| N5 | BWR noble shares | Xe138+ .55, Xe133 .10, Xe135 .10, Kr85 .02 (others Kr87 .08, Kr88+ .06, Ar41 .06, Kr85m .03) | Xe138+ .45, Xe133 .16, Xe135 .15, Kr85 .02 (sum 1.01 renormalised) |
| N6 | `0209` C-14 air BWR | $6.5\times10^{10}$ / $1.3\times10^{11}$ / $2.6\times10^{11}$ | $1.3\times10^{11}$ / $3.0\times10^{11}$ / $6.0\times10^{11}$ |
| N7 | `0074` C-14 air PWR | $4.15\times10^{10}$ / $8.3\times10^{10}$ / $1.66\times10^{11}$ | $8.3\times10^{10}$ / $1.7\times10^{11}$ / $3.4\times10^{11}$ |
| N8 | `0064` H-3 air PWR; `0199` H-3 air BWR | central $1.5\times10^{12}$, high $3.0\times10^{12}$; central $1.3\times10^{12}$, high $2.6\times10^{12}$ | central $2.2\times10^{12}$, high $5\times10^{12}$; central $1.7\times10^{12}$, high $3.5\times10^{12}$ (lows unchanged) |
| N9 | `0069` H-3 liquid PWR | central $1.8\times10^{13}$ | $2.3\times10^{13}$ |
| N10 | `0079` I-131 air PWR | $4\times10^{7}$ / $8\times10^{7}$ / $1.6\times10^{8}$ | $1\times10^{5}$ / $1\times10^{7}$ / $1\times10^{8}$ |
| N11 | `0214` I-131 air BWR | $2.1\times10^{8}$ / $4.2\times10^{8}$ / $8.4\times10^{8}$ | $5\times10^{7}$ / $2\times10^{8}$ / $8.4\times10^{8}$ |
| N12 | `0119` Co-60 air PWR; `0259` BWR | low $4.05\times10^{6}$, central $1.08\times10^{7}$; low $2.03\times10^{8}$, central $5.4\times10^{8}$ | low $4\times10^{5}$, central $2\times10^{6}$; low $1.3\times10^{7}$, central $8\times10^{7}$ (highs unchanged) |
| N13 | `0124`, `0264` Cs-137+ air | share .25 of particulates | share .03 (rows scaled by 0.12; other groups not renormalised) |
| N14 | Cs-137+ and Cs-134 liquid, PWR and BWR 2010-25 | shares .12 and .08 | .03 and .01 |
| N15 | other liquid total PWR / BWR | central $3.8\times10^{9}$ / $2.1\times10^{9}$ | central $1.5\times10^{9}$ / $9\times10^{8}$; low total $5.6\times10^{8}$ / $3.7\times10^{8}$ |
| N16 | liquid composition | Co58 .22, Co60 .20, Fe55 .12 | PWR Co58 .25, Co60 .22, Fe55 .10; BWR Co60 .33, Fe55 .15, Co58 .03 |

Implementation choices (not in the table): N2/N3 apply to 2015-25, so the 2010-25 noble-gas rows (`0084`-`0114`, `0219`-`0254`) now end in 2014 and carry the new low bound and shares with the old central total, and fifteen new 2015-25 rows hold the new central; the high total of both is the old high total, so the band is wide (high is 9.8 times the PWR and 5.2 times the BWR new central). N14-N16 rows `0159`-`0194` and `0299`-`0334` are rebuilt as total times share, with shares renormalised over the eight listed groups (convention of section 1.3); the high total is unchanged.

### 10.3 TMI-2 (Rogovin, S0138): nuclear:1665, 1666, 1703-1705 and E002
- Table II-1 split (as released): Xe-133 0.63, Kr-88 0.15, Xe-135 0.12, Xe-133m 0.09, Xe-135m 0.01. The shares are applied to the E002 bounds ($3.7\times10^{16}$ / $9.25\times10^{16}$ / $4.81\times10^{17}$ Bq), so the five release central values sum to $9.25\times10^{16}$ Bq exactly (Rogovin's own table sums to 2.505 MCi). Xe-135m is not a group of its own (a member of `I135+`) and is folded into Xe135 (decay daughter): Xe135 share 0.13.
- `1665` Xe133 $9.25\times10^{16}$ (central) -> $5.8275\times10^{16}$; `1703` Kr88+ $1.39\times10^{16}$; `1704` Xe135 $1.20\times10^{16}$; `1705` Xe133m $8.3\times10^{15}$. Low and high are the share times the E002 low and high. The researcher's table gave a Xe-133 high of $1.9\times10^{17}$ "by 0.63 times the E002 bounds"; 0.63 times $4.81\times10^{17}$ is $3.0\times10^{17}$, which is what is entered (the stated rule over the stated number).
- `1666` I-131 $5.2\times10^{11}$ (range $10^{11}$-$2\times10^{12}$) -> $5.4\times10^{11}$ (14.56 Ci), low $10^{11}$ kept, high $1.2\times10^{12}$ (32 Ci). Sum with I-131 is within $6\times10^{-6}$ relative of E002 (tolerance $10^{-4}$, NUCLEAR_SPEC 7.4).
- E002: central unchanged and now retrieved; high $1.48\times10^{18}$ (40 MCi, NRC range) -> $4.81\times10^{17}$ (13 MCi, Rogovin TLD, Xe-133 equivalent); the NRC 1-40 MCi and consultants' about 10 MCi stay in the notes; "some Kr-85" removed (Rogovin: Kr-85 not released in significant quantity; about 50,000 Ci remained in containment after six months). The Table II-1 exponents come from OCR text and should be eyeballed once (printed p.344).

### 10.4 ISL shares (Red Books 2003 and 2026, S1006, S1007)
| Row | Old | New |
|---|---|---|
| `0029` KAZ 1978-99 | 0.25 / 0.5 / 0.8 | 0.30 / 0.40 / 0.55 (cumulative 0.315) |
| `0030` KAZ 2000-25 | 0.9 / 0.97 / 1 | 0.95 / 0.99 / 1.0 |
| `0032` UZB 1963-99 | 0.3 / 0.7 / 1 | 0.30 / 0.40 / 0.55 (cumulative 0.403) |
| `0033` UZB 2000-25 | 0.9 / 0.97 / 1 | 0.97 / 1.0 / 1.0 |
| `0036` USA 1990-99 | 0.2 / 0.4 / 0.8 | 0.5 / 0.7 / 0.9 |
| `0037` USA 2000-25 | 0.8 / 0.95 / 1 | 0.74 / 0.93 / 1.0 |
| `0025` XWL 1967-99 | 0.05 / 0.15 / 0.35 | 0.01 / 0.03 / 0.08 |
| `0026` XWL (was 2000-25) | 0.05 / 0.2 / 0.45 | 2000-09: 0.02 / 0.04 / 0.08 |
| `1701` XWL 2010-19 (new) | none | 0.05 / 0.10 / 0.18 (interpolated, not sourced) |
| `1702` XWL 2020-25 (new) | none | 0.12 / 0.165 / 0.22 |
Reading of XWL: NUCLEAR_SPEC 4.1 uses the XWL rows as the default for every country without its own row, so XWL is the rest of the world (the "rest of world" proposals), not the world total. The rest-of-world rows are therefore low for Australia, Russia and China, whose own ISL shares are 0.37-0.42, 0.6 and 0.9 in 2023-24; the proposed country rows for AUS, RUS, CZE, CHN and BGR were NOT added (the table gave only ranges, no values by era; medium-low confidence). Note that the 2003 Red Book country tables were identified by position (papers_round2.md, section 5 item 4).

### 10.5 Grand Junction fill (`nuclear:1706`, flagged low confidence)
`u_milling`, tier `dispersed`, residue `u_tailings`, USA, 1950-1966, Ra226+, unit Bq (total, event-like, no driver, no route because `fill` is not in the route vocabulary): $3\times10^{11}$ / $1\times10^{12}$ / $6\times10^{12}$ Bq. Grand Junction only (not scaled by 1.3 for the US). The assumed 22 Bq/g Ra-226 is the researcher's, not the fact sheet's. How the engine treats a Bq row without an event or driver at `u_milling` has not been tested (the stream script does not yet exist).

### 10.6 Uranium overburden memo series and u_waste_rock (EPA 1991 chapter B.1, S1250)
- `residue_types.csv` `u_waste_rock`: Rn-222 $\varepsilon$ empty -> 0.1 / 0.3 / 0.5 (emanation coefficient, D60); Rn-220 stays empty; source S1250 added.
- `vocab.json` allows `memo_earth_moved` at `u_mining_conv`, so 21 rows were added (`nuclear:1707`-`1727`): 7 groups (U238+, U234, Th230, Ra226+ at 877 Bq/kg; Pb210+, Po210 at 614 Bq/kg; U235+ at 44.4 Bq/kg) times 3 eras, region USA, driver `u_production`, unit Bq per t U. Tonnage per t U = Table B.1-3 overburden per era / US `u_production` in that era (1950-68: $4.17\times10^{8}$ t over 133,527 t U = 3,123 t/t U; 1969-78: $1.528\times10^{9}$ t over 101,719 t U = 15,022; 1979-88: $2.025\times10^{9}$ t over 89,815 t U = 22,546). Ra-226 central is 877 Bq/kg times those: $2.7\times10^{9}$, $1.3\times10^{10}$ and $2.0\times10^{10}$ Bq per t U. Bounds: concentration 185 to 7,400 Bq/kg combined with a factor 1.25 on tonnage. US only; nothing after 1988 (no EPA tonnage). Open issue for the engine: the F1 rule multiplies by (1 - ISL share) and the world `phi_civil` (zero before 1965), which would shrink the memo series; a ruling is needed. `docs/NUCLEAR_SPEC.md` 4.4 and 10 still say "no rows" and are not edited here.
