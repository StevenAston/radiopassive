# Task 2.4 step 1: commodity footprint registry, research notes (DRAFT)

Date 2026-11-10. Files in this folder: `commodity_factors_draft.csv` (158 rows, §4.7 layout, NOT validated, uses 19 proposed sources and 2 proposed commodity codes), `material_intensity_v2.csv` (Task 1.5's 157 rows kept unchanged, 65 new rows appended; the original `material_intensity.csv` is untouched), `sources_task24_proposed.csv` (S0430-S0448, not applied). Phase 1 material (notes.md, footprint_inputs.csv, co_product_inputs.csv) is reused and not repeated.

Conventions: all values are **head activities** in Bq per tonne (METHODS 3.2 multiplier applied later); chain members are written at ratio 1 (the coal registry's convention, coal:0029-0039). Where I say "my assumption" the number is unsourced. Bounds follow the project rule (low = product of lows, high = product of highs).

## 1. Double counting: tagging and schema

**§4.7 already has the tag**: `component` = `own_residue` (= "non-fuel process") or `embedded_fuel` (= "embedded fuel, reference only"), and it is in the table key. The master table also has an `embedded_fuel` flag in its unique key. So no new column is strictly required. What I did and propose:

1. Every `own_residue` note starts "non-fuel process (own_residue)." and every `embedded_fuel` note starts "EMBEDDED FUEL (reference only; D22):".
2. **Subtract the fuel part from observed totals, don't add it twice.** Observed emissions and slags contain fuel-derived activity. Own = total x (1 - fuel share), with the share in the note:
   - sinter/BF stack Pb-210 and Po-210: fuel share 0.05/0.15/0.40;
   - BF/BOS slag: coke-ash share 0.10/0.25/0.45 (coke 0.35 t/t iron x 12% ash x 0.23 Bq/g is about 1e4 Bq against 2.2e4-4.8e4 in slag; my estimate);
   - cement kiln Po-210: 0.03/0.10/0.30.
3. **Embedded rows are input-type.** Their value is fuel input (t fuel per t commodity) x the coal registry's Bq per tonne of coal (coal:0029-0039); they are not an output partition, so the tier/residue cells (`impounded`, `coal_bottom_ash`) are placeholders. This is awkward in §4.7. **Recommendation (OQ-1):** move fuel inputs to a small companion table `commodity_fuel_inputs.csv` (commodity, fuel, t/t low/central/high, source) and let the lifecycle code multiply by the coal and oil_gas streams' own per-tonne footprints. Keep the `embedded_fuel` component for completeness, or drop the embedded rows from this table. Either way the industry view sums `own_residue` only.
4. Other overlaps found:
   - Fly ash and GGBFS in cement: coal stream (dispersed) and steel stream (dispersed slag) count them. Never in the cement rows.
   - Steel slag used in cement is counted once, in steel (dispersed).
   - Dust recycled to Zn recovery (Waelz) could be counted in steel and zinc.
   - Olympic Dam tailings are in copper (here) and are also uranium mill tailings in the nuclear stream; NUCLEAR_SPEC has no Olympic Dam treatment, so the nuclear stream probably counts them at the average per-tU tailings factor. **They must share one D6 allocation (OQ-4).**
   - Bayan Obo: Th goes to REE rows; the generic steel rows must not use Bayan Obo slag.
   - Electricity embedded in Al (14-15 MWh/t) and Si (11-13 MWh/t) comes from any source (coal, gas, nuclear fuel cycle, hydro): all reference-only, not rows.
   - Polymers (ethane feedstock) are oil_gas cross-references (section 5).
5. **Pre-allocation convention (OQ-2).** Rows hold per-tonne values BEFORE D6, `allocation_variant = default`, `allocation_rule = alloc:value` where co-products exist. §3.3 rule 3 requires all three variants if any is non-default, so bounds A and B are left to the allocation library. Unit values come from DS140 (no uranium or niobium series).

## 2. Blockers found for the stream script

- **Vocabulary:** `tio2_pigment` and `cast_iron` are missing from `commodities` (and from the JSON schema enum). Polysilicon maps to `silicon_mg` (no separate NORM). Concrete = `cement` + `aggregate` (aggregate is product, not residue, see section 5).
- **Key has no ore-type dimension (OQ-SCHEMA-2).** Bayan Obo, ionic clay, monazite and Mount Weld REE all share (`ree_oxide`, group, tier, residue type, region, year). I worked around it with residue type and year_from for ionic clays. A column such as `ore_type` is cleaner.
- **Region cell** must be one code; the Phase 1 seed's 'AUS;MYS' and 'CHN;MMR' are invalid. Lynas WLP is written as MYS; Myanmar clays not written.
- **Residue types with no epsilon/seepage set** (the engine refuses to run on empty sets): epsilon is empty for `ree_tailings`, `red_mud`, `metal_tailings`, `iron_ore_tailings`; seepage AND epsilon are empty for `ree_process_residue`, `smelter_slag`, `other_commodity_residue`, `cement_kiln_residue`. Phase 1 notes section 8 has epsilon proposals for the first group and for `smelter_slag`.
- **Activity series missing from data/activity:** BF-BOF share of steel (steel rows are per tonne of BF-BOF steel; EAF scrap carries little ore), pig-iron fraction of cast iron, REO route shares (Bayan Obo / other Chinese / ionic clay / Lynas / monazite), and REO-equivalent charge factor.

## 3. Per commodity

Confidence grades: A measured at several sites, B one measured site or one documented model, C analogy, D assumption.

### 3.1 Rare earths (Nd, Pr, Dy, Tb), `ree_oxide`, grade B-C
- Bayan Obo: ore 0.032-0.04% ThO2 (1.4 Bq/g, up to 2.6); tailings 1.0-1.6 Bq/g Th-232, 113 t tailings per t REO (S0404, S0405). Phase 1 rows kept. U-238 only 0.022 Bq/g.
- Monazite (4-12% Th) is 3x-30x worse per tonne REO but a small and shrinking supply; it is a by-product of mineral sands (D6 with ilmenite, rutile, zircon). U-series set at 0.15 of Th (my arithmetic).
- Ionic clays: soil-like but 500-2000 t of leached ore per t REO; D21 status of in-situ leach unresolved.
- **Tonnage basis problem:** wind needs Nd, Pr, Dy, Tb oxides (about 0.28 t REO per MW for direct-drive), but mining one tonne of Nd2O3 also produces about 5.9 t of REO (Nd is about 17% of Bayan Obo REO). Proposed REO-equivalent charge factor: 1 (mass split) / 2.5 (value split, central) / 5.9 (all to Nd). I used 2.5 in the ranking. My estimate; needs price data for the oxides.
- Not done: route shares by year; Dy and Tb come from ionic clays, not Bayan Obo.

### 3.2 Steel, grade A-B for stack, B-C for slag
- Stack (per t BF-BOF steel): Pb-210 total 1.6e3 (Scunthorpe, NRPB-W48 Table 3) to 1e4 (IJmuiden, RP-135 Table 15; UNSCEAR 2000); Po-210 total 1e4 (W48), 1.6e4 (IJmuiden), 1.7e4 (UNSCEAR). **Contradiction:** the older NRPB paper gives Scunthorpe Po-210 4.0e9 Bq/a, W48 3.96e10; I use W48 and put the lower in the low bound. Sinter stack dust is 9.98e4 Bq/kg Po-210 (S0430).
- Slag 0.41 t/t steel (Scunthorpe; RP-135 gives 0.2 t/t iron, so the range is wide); 0.088 Bq/g U-series, 0.049 Th-series; Pb-210 and Po-210 depleted.
- Fate: EU 2022 BF slag 100% used (82.5% cement), steel slag 70% roads; EU 2024 92%; Australia/NZ 60%. World dispersed share 0.5/0.8/0.95 is a judgement.
- Dust to landfill 14.6 kg/t, Pb-210 900 Bq/kg; BF dust 15-25 Bq/g at IJmuiden.
- Iron-ore tailings: grade D (tailings per tonne assumed).
- Gap: sinter-plant measurements outside the UK/NL (China, India are most of world steel and are less abated: the high bounds are not meant to cover them); Rn-222 from UNSCEAR page-image data.

### 3.3 Cast iron and foundry sand, `cast_iron`, grade D
Zircon 2-4 Bq/g U-238, 0.4-1 Th-232 (EPA). Foundry zircon use per tonne casting is my assumption (1.2 kg). Result about 4e3 Bq/t, negligible beside the pig-iron chain (handled by reusing the steel rows). Chromite sand not found.

### 3.4 Cement and concrete, grade C
Kiln Po-210 per t cement spans 2.1e3 (Kunze, German model, 97% filter) to 3.9e4 (UNSCEAR 2000), a factor of 37, unresolved; RP-135 assumes 50% volatilisation. Rn-222 7.9e4. Cement kiln dust (Ra-226 15, Th-232 8-11, K-40 1300-2700 Bq/kg, S0436) has no tonnage per tonne cement or Pb/Po data: gap, `cement_kiln_residue` left empty. Aggregates and sand are product at about 0.02-0.04 Bq/g, not residue (D21 spirit); no rows.

### 3.5 Copper, grade C (generic), B (Olympic Dam)
Phase 1 rows kept and chain-completed. The generic tailings value spans a factor of 60 between sources (UNSCEAR 1988 vs TRS 419). It is the biggest single driver of the ranking. Smelter slag ~2.2 t/t Cu at 0.4-2 Bq/g Ra-226 (training slides); smelter off-gas from one 1980s US plant with assumed capacity. Olympic Dam: 50.8 t ore per t Cu, Ra-226 3.5e8-7.6e8, plus U-238 left in tailings; the uranium product (3.6e13 Bq) goes to the nuclear stream. Uranium co-production elsewhere (Kazakh, Zambian copper-uranium) not researched.

### 3.6 Aluminium, grade B
Red mud 3.2 t/t Al; Th-232 100-550 Bq/kg (range 45-1800), Ra-226 100-1000 (97-1700); I raised the high bounds to the S0409 maximum (1350 Bq/kg). Residue enrichment 1.6-3x over bauxite (S0437). Reuse share 1-10% is my assumption. Gaps: alumina calciner/boiler Pb-210/Po-210 and smelter emissions (UNSCEAR 1988 Table 45, plant capacity unknown); `red_mud` has seepage but no epsilon.

### 3.7 Silicon and polysilicon, grade D
Quartz is nearly inactive; own-residue 2.7e4 Bq/t is an upper estimate. The real content is embedded: reductants 1.0-2.5 t/t (my assumption, S0422 tables unread) plus electricity and electrodes. Polysilicon adds nothing radiological.

### 3.8 Silver, grade D
By-product; row is ore per tonne Ag (about 10,000 t at about 100 g/t, assumed) x 0.03 Bq/g, 3e8 Bq/t BEFORE allocation (silver is about 1% of Olympic Dam value). After D6 it will fall to roughly 1e7-1e8. No smelter data.

### 3.9 Tin, grade C
Tin slag: Malaysia U-238 0.95, Th-232 0.42, Ra-226 4.57 Bq/g; old Dutch/UK slag 4 and 11 Bq/g; hardhead 0.2-11. Slag per tonne tin assumed 1-4 t. Tonnage in wind/PV is tiny (about 0.0003 t/MW wind; solder in PV).

### 3.10 TiO2 pigment, grade B-C
RP-135: rutile 400/600 Bq/kg (U/Th chain), chloride waste about 5,000 t/a at up to 7 and 11 Bq/g. Per t TiO2 about 4.4e5 (U) and 6.7e5 (Th). Uses in wind/PV are my estimate: about 50-100 t/GW (blade and tower paint, white backsheets); no source found. Mineral-sands mining wastes go to the co-products.

### 3.11 Glass (soda-lime) and E-glass fibre, grade D
No measurement found. Analogy to brick firing gives 0-1.2e4 Bq/t Po-210; central 1e3 with filter capture (soda-lime), 2e3 (E-glass). Furnace gas is oil_gas embedded.

### 3.12 Zinc, grade D
10-30 t ore per t Zn at 0.01-0.1 Bq/g; galvanising generates no NORM. Smelter data inaccessible (Poffijn, S0427). **Wind zinc intensity conflict:** JRC 5.5 t/MW vs NREL 0.03-0.11 t/MW; with NREL zinc drops from fourth to negligible.

### 3.13 Thin-film (CdTe, CIGS)
Te, Cd, In, Ga, Se are by-products of Cu, Zn, Al. By value allocation (Te about 0.03% of the Cu chain value, my estimate, price not checked) CdTe at about 52 t Te/GW gives about 1e10 Bq/GW, about 1e7 Bq/MW, times a 2.3% thin-film share (2025 only in data/activity): negligible. Mass allocation would be about 1e12 per t Te, so this depends on D6 default. No rows.

## 4. Top commodities by expected Bq per MW (central, unallocated, decay-weighted using group member weights; one-off construction charge)

| Rank | Commodity | Onshore geared | Offshore DD-PMSG | Utility PV c-Si |
|---|---|---|---|---|
| 1 | copper (generic) | 9e8 | 2e9 | 3e9 |
| 2 | REE (charge factor 2.5) | 7e7 | 1.2e9 | 0 |
| 3 | steel | 1.0e8 | 1.1e8 | 6e7 |
| 4 | aluminium | 4e7 | 1e7 | 2e8 |
| 5 | zinc (JRC; NREL makes it negligible) / silver (PV, 8e7 unallocated, about 1e7 allocated) | 5e7 | 5e7 | 8e7 |

Next: cement (1-2e7), tin, TiO2, silicon (about 2e6). After D6 allocation, copper falls (if Cu is 80% of value) and silver falls tenfold. The Olympic Dam variant of copper is 7x the generic per tonne. Wind and solar are not "REE-dominated" for PV: PV is copper and aluminium.

## 5. Negligible, considered
- **Lubricants** (wind gearbox oil about 0.15 t/MW): base oil from refining; crude NORM sits in oil_gas. Cross-reference only, below 1e5 Bq/MW.
- **PTFE / fluoropolymers / fluorspar:** about 0.1 t/MW fluoropolymer needs about 0.2 t/MW fluorspar at an assumed 0.01-0.1 Bq/g: 2e3-2e4 Bq/MW, under 1e-4 of copper. HF residues not researched.
- **Epoxy, EVA, PET, polyester:** 13 t/MW (wind 4.6, PV 8.6 t/MW). Ethane feedstock: about 800 m3 per tonne ethane x NGL radon (oil_gas:0110, 200 Bq/m3 central) gives about 2e5 Bq per t ethane, so up to 3e6 Bq/MW. That is under 5% of REE or copper, and is in the oil_gas stream (lifecycle only). No rows.
- **Carbon fibre** (0.6-2.3 t/MW, NREL): PAN from propylene/ammonia, no NORM beyond gas cross-reference.
- **End of life:** unchanged from Phase 1 section 7.

## 6. Benchmarks for done condition (e)
UNSCEAR 2016 Annex B has **no** Bq factors for wind/solar (only ore mass and occupational dose), so D51's benchmarks for stream 4 must come from elsewhere. Candidates, two needed in two years:
1. Bayan Obo inventories (S0405): 149 Mt tailings at 1.0-1.6 Bq/g Th-232 (1.5e17-2.4e17 Bq), 55 Mt BF slag, to end 2006; compare cumulative ree_oxide rows x Bayan Obo REO.
2. UK steel (NRPB-W48): four plants 2.1e10 Pb-210 and 1.35e11 Po-210 Bq/a (1999); US/UNSCEAR 2000 Table 28 typical plants.
3. Olympic Dam: tailings radon 520 TBq/a, feed Ra-226 (S0408).
4. IAEA SRS-68 / TRS-419 annual NORM masses (TRS 419 for metals); red mud 150 Mt/a (S0436) at 100-500 Bq/kg gives 1.5e16-7.5e16 Bq/a Ra-226 plus Th, against the aluminium rows.
5. RP-135 and OSPAR: OSPAR is mostly oil/gas; not used. Suggested pairs: 2006 (Bayan Obo) and 1999 (UK steel); a global total for red mud is an independent second for aluminium.
Caveat: these test components (REE, steel, Al), not the stream total; the UNSCEAR ore-mass total is an occupational dose figure, not usable per D1.

## 7. Wind/solar activity side
- `data/activity/capacity_additions.csv` has `cap_add_wind_onshore` (1982-2025), `cap_add_wind_offshore` (2001-2025), `cap_add_solar_pv` (2001-2025), `cap_add_solar_csp` (2001-2025), `pv_share_thin_film` (2025 only), each with 16 country codes incl. XWL (sum countries or use XWL, not both). **Missing:** geared vs direct-drive vs PM penetration series, utility vs rooftop split, PV before 2001, repowering/replacement, thin-film history, CSP intensities.
- Intensities (material_intensity_v2.csv): onshore geared (JRC GB-DFIG, NREL land-based, Bonou onshore); offshore (JRC DD-PMSG proxy, NREL offshore, Bonou offshore); utility PV (JRC 2018 BOS+module, Qinghai LCA, IEA PVPS derived). **Rooftop: not found.** The NREL REMPD figure holds the numbers as an image and the NREL report was blocked.
- Contradictions: offshore concrete 243 t/MW (JRC proxy) vs about 17 (Bonou) vs "minimal" (NREL); offshore steel 120 (JRC) vs 130-419 (NREL) vs 259 (Bonou); wind zinc as above; Pr offshore NREL value probably a typo.
- Era: wind has no vintage series beyond 2010 (White-Kulcinski 85 kt steel/GW), 2012-15 (Bonou), 2018 (JRC), 2022 (NREL). PV silicon 16,000 (2004) to 4,000 t/GW (2018), silver 84 (2010) to 20 (2018) t/GW (Phase 1 rows).

## 8. Open questions for Steve
1. **OQ-1:** embedded fuel as a companion table of fuel inputs (recommended), or keep input-type rows in §4.7?
2. **OQ-2:** registry holds pre-allocation values and the allocation library does the D6 variants (recommended)?
3. **OQ-3:** REO-equivalent charge factor (1 / 2.5 / 5.9): value split among oxides or mass?
4. **OQ-4:** one D6 allocation shared by nuclear and copper for Olympic Dam; confirm the nuclear script's handling.
5. **OQ-vocab:** add `tio2_pigment` and `cast_iron`; add an ore-type key or column.
6. **OQ-5:** Product tonnage in REE rows includes dispersed Th in oxide product (count as Dispersed?).
7. **OQ-6:** D21 status of in-situ leach ionic-clay ore.
8. **OQ-7:** accept grade-D rows (silver, zinc, silicon, glass, TiO2 use) at wide bounds, or mark `negligible` under METHODS 10.3 for the ones under 0.1% of stream total? Silicon, glass, cast iron likely qualify.
9. Epsilon and seepage sets for the eight residue types in section 2.

## 9. Gaps
CKD tonnage and Pb/Po; aluminium smelter and calciner emissions; copper smelter slag measurements; Chinese and Indian sinter-plant data; zinc/lead smelter data; glass furnaces; foundry zircon use; REO route shares; tin slag per tonne; rooftop PV; NREL, RP-135 Section 2 tables (text dropped in extraction); IAEA SRS-49 and the IAEA NORM TECDOC series were not retrieved; OSPAR not consulted.
