# Task 1.1 — UNSCEAR evidence base: notes

Outputs: `unscear_extraction.csv` (1,380 rows), `sources_task11.csv` (S0001–S0010). Generator script: `/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task11/scripts/build.py` (not a deliverable).

## 0. Correction to the brief

The electricity-generation evaluation (reference year 2010) is **UNSCEAR 2016 Report, Annex B** ("Radiation exposures from electricity generation", printed pp. 135–231), not Annex A. Annex A is the discharge-dose methodology (S0002). All "2016" rows cite Annex B (S0001). Printed page numbers are used (Annex B Table 1 is p. 142, matching the corrigendum).

## 1. Method

- Downloaded the open PDFs from unscear.org (URLs in `sources_task11.csv`); text via `pdftotext -layout`.
- 2016 Annex B, 2008 Annex B and 2000 Annex C were read table by table. The two reactor tables (2008 Table 17, 2000 Table 37) were parsed by script (336 and 287 values) and spot-checked against the text.
- Rotated or OCR-failed tables (2000 Annex B Table 28; 1988 Annex A Table 27; 1988 Annex B Table 13) were read from page images. Their column assignments are flagged in `basis_note`.
- Units are as UNSCEAR prints them ("TBq/(GW a)", "MBq/(GW a)", "GBq/a", "Bq/s", "PBq" converted to TBq and noted). Quantities:
  - `normalised_release`: per GW a of electricity (reprocessing: per GW a of fuel reprocessed).
  - `annual_release`: absolute release as printed.
  - `annual_release_derived`: **extractor's product of an UNSCEAR factor and UNSCEAR 2010 generation. Not an UNSCEAR figure.** Exclude it if you want strict UNSCEAR-only values.
  - `activity_parameter`: basis parameters (grades, t/GW a and so on).
  - `ore_mass_per_electricity` and `metal_mass_per_electricity`.
  - `electricity_generated`.
  - `collective_dose_validation_only`: 128 rows. All carry "VALIDATION ONLY" in `basis_note`. Filter them out of anything feeding the page (D1).
- Group mapping: UNSCEAR's parent-only nuclides are mapped to the head group (e.g. Ra-226 to `Ra226+`, Cs-137 to `Cs137+`). **UNSCEAR values are head activities, so the METHODS §3.2 multiplier must be applied in the pipeline, not here.** Aggregates with no group (noble gases, "particulates", "other liquid", S-35) are `UNMAPPED:<label>`. Th-234 in the 1988 conversion table is mapped to `U238+` (it is a member, not a head).

Row counts by stream: nuclear 1,188; coal 82; construction (all-technology parameters) 31; solar 28; natural gas 11; oil and gas extraction 12; geothermal 11; oil 8; wind 3; biomass 3; hydro 1; all-technology total 1; peat 1.

## 2. Coverage (release factors only; dose rows excluded)

| Stream / stage | Periods with factors | Source |
|---|---|---|
| Nuclear: U mining (radon) | ~1980s 70; 1985–89/1990s 75; 2010 66 (ISL 3) TBq/(GW a) | 1988B ¶27; 1993B ¶83; 2000C T29; 2008B ¶159; 2016B T5 |
| Nuclear: milling (radon; nuclides) | 3 TBq/(GW a) throughout; nuclides 2010 (from 1993) | 2000C T29; 2016B T5–6 |
| Nuclear: mill tailings (radon) | 1 TBq/ha·a (1988); 3 op / 0.3 closed (2000); 3 op / 1 abandoned (2008); 3 / 0.1 (2016, closed ×100 y) | as above |
| Nuclear: conversion, enrichment, fabrication | c.1980–85 only, MBq/(GW a) by nuclide | 1988B T13 (reused 1993) |
| Nuclear: reactor operation, by type (PWR, BWR, GCR/AGR, HWR, LWGR, FBR) | 1970–74, 75–79, 80–84, 85–89, 90–94, 95–97, 1998–2002 (7 groups) and 2010 (AGR split out, plus S-35) | 2008B T17; 2000C T37; 2016B T11 |
| Nuclear: reprocessing | 1970–1997 by period (6 nuclides each, air and liquid); 1998–2002 5-y totals; 2010 La Hague per GW a, three sites Bq/s | 2000C T41; 2008B T20; 2016B T13 |
| Nuclear: globally dispersed H-3, C-14, Kr-85, I-129 (absolute) | pre-1970–1997 | 2000C T42–43 |
| Nuclear: spent fuel / LLW arisings | 1998–2002 (Bq/MW(e) by type) | 2008B T21 |
| Nuclear: decommissioning, waste disposal, transport, accidents | **no release factors** (dose only) | 2016B ¶77, T23 |
| Coal: mining radon | 2010 2.8 TBq/(GW a) (China); 1980s crude 0.036 or 0.6 | 2016B T26; 1988A ¶178 |
| Coal: power-plant stack (old/modern) | c.1980 MBq/(GW a) (1982, 1988); 2010 TBq/(GW a) | 1982C T4; 1988A T27; 2016B T27 |
| Coal: ash radon | 2010 only (0.03 annual; 1.8 100-y convention) | 2016B ¶114–117 |
| Natural gas (Rn-222) | 1980s 2; 2010 0.75 | 1988A ¶209; 2016B ¶137 |
| Oil (Rn-222; U/Ra/Th) | 1980 (France); 2010 0.002 | 1988A ¶205; 2016B ¶148 |
| Oil and gas extraction (air and produced water) | 1990s per installation, GBq/a | 2000B T28 |
| Geothermal (Rn-222) | 400 (1982); 150 (1988, 1993, 2016) | 1982C ¶34; 1988A ¶203; 2016B ¶158 |
| Peat | no release factor, only 5e9 kg/(GW a) and 40 Bq/kg U-238 | 1988A ¶213 |
| Solar PV / wind / biomass | **no release factors**; only ore-mass and material intensity for 2010 | 2016B T43–45 |
| Hydro | not assessed (negligible), ¶27 | 2016B |
| Biofuels | biomass: construction mining only; Cs-137 in ash deliberately excluded (¶191) | 2016B ¶191–193 |

## 3. "Why solar" — what drives the high solar/wind occupational dose

**Answer: total mass of low-grade ore, not rare earths.** UNSCEAR applies one uniform dose factor per kilogram of ore to every metal. Rare earths are not in the PV calculation at all.

Direct quotes (S0001):

- Conclusions ¶234, p. 228: "Regarding the mining of rare earth metals needed for construction, by far the largest collective dose to workers per unit of electricity generated assessed in this study came from solar power, followed by wind power. This is because the workers are exposed to natural radionuclides during mining, and the amount of low-grade ore required to be mined for these technologies is high."
- ¶218, p. 221: "These differences come from the different metal requirements for solar PV and wind power technologies, discussed in chapter VII."
- ¶194, p. 210: differences "are connected to various plant facilities using different types and amounts of steel and metals", plus capacity factor and lifetime (PV capacity factor 9.4%, wind 24%, Table 41).

Supporting evidence from the method (S0001 ¶173, pp. 205–206, Table 40):

- ¶173(d): collective dose per unit mass of ore mined = 1 × 10⁻⁹ man Sv/kg ore (3 kt ore per worker-year × 3.0 mSv), applied to all metals.
- ¶173(f): a Chinese rare-earth value of about 150 × 10⁻⁹ man Sv per kg of **metal** was found but **not used**; the Committee used the ore-mass value "to account for the different metal requirements with associated metal ore grades of each electricity-generating technology".
- Table 43 (p. 209, per kW h of PV electricity) lists 13 metals (Al, Cr, Cu, Fe, Pb, Mg, Mn, Mo, Ni, Ag, Ta, Sn, Zn). **There is no rare-earth row**, and Table 39 (ore grades) has none either.
- ¶182, ¶185 and ¶187 do mention that c-Si PV cells contain "small amounts of rare earth elements" and call them "of particular interest", but nothing quantitative follows.

Extractor's check (my inference, not UNSCEAR's text):

- Summing the Table 43 ore column gives 0.0851 kg ore/kW h. With 8.76 × 10⁹ kW h per GW a and 1 × 10⁻⁹ man Sv/kg, this gives 0.75 man Sv/(GW a), which matches Table 45's 0.8 (p. 210).
- Shares of that ore mass: Cu 35%, Ag 34% (0.01% grade), Al 18%, Mo 10%, Fe 3%.
- Table 43's Mo ore figure (8.3 × 10⁻³ kg/kW h) is inconsistent with its own metal figure (4.2 × 10⁻⁶ kg at 0.18% grade gives 2.3 × 10⁻³). Using 2.3 × 10⁻³ gives 0.69. This is immaterial to the conclusion but worth noting.
- Wind (0.1 man Sv/(GW a)) rests on 85,000 t of steel per GW(e) (Table 44) at 24% capacity factor and 20 y life, with no ore table shown (ore at the 46% iron grade plus alloy metals).

Implications for METHODS §10.2 and Tasks 1.5/1.9:

- The UNSCEAR figure does not support attributing solar's burden to REE tailings.
- Two things in UNSCEAR's own method differ from the project's approach:
  - UNSCEAR assumes underground mining for everything (¶173(a); acknowledged to overstate).
  - It ignores co-product allocation and recycling (¶172: overstated by about 2× on average, 5× in some regions).
- For the project, the relevant quantity would be Ag, Cu and Al ore and processing residues per kW h, not REE.

## 4. 2010 reference values (for Task 3.5; source S0001 unless stated)

**Electricity, GW a (Table 2, p. 144):** nuclear 314.3 (IAEA basis 300.21, Table 9), coal 991.6, gas 543.8, oil 112.6, geothermal 7.77, solar 3.86, wind 38.5, biomass 37.8, hydro 400.8; total 2,452. Nuclear by type (Table 9): PWR 204.88, BWR 63.72, HWR 17.09, LWGR 8.15, AGR 5.01, GCR 0.93, FBR 0.42.

**Normalised releases, TBq/(GW a):**

- U mining 66 (non-ISL), ISL 3, milling 3, operational tailings 3, closed tailings 0.1 (×100 y).
- Reactors, Table 11 (all 7 types × 8 categories in CSV). PWR: noble gases 5.8, H-3 1.5 air and 18 liquid, C-14 0.083. BWR: noble gases 18. HWR: H-3 200 air and 170 liquid. LWGR: noble gases 460. GCR: noble gases 1,700.
- Reprocessing (La Hague): Kr-85 1.5 × 10⁸, H-3 3.8 × 10⁴ air and 6.7 × 10⁶ liquid, C-14 1.1 × 10⁴ air. **Unit caveat (verifier):** UNSCEAR prints these as TBq/(GW a), but they are Bq s⁻¹ per GW a (the Bq/s column ÷ 47 GW a). In true TBq/(GW a): Kr-85 ≈ 4.7 × 10³, H-3 air ≈ 1.2, H-3 liquid ≈ 2.1 × 10², C-14 air ≈ 0.35 (× 3.156 × 10⁻⁵).
- Coal: mining Rn-222 2.8; stack Rn-222 0.07; older plants Po-210 and Pb-210 1.4 × 10⁻³ each, modern plants 9.3 × 10⁻⁵; ash radon 0.03/yr (1.8 under the 100-y convention). Th-232 series and K-40 were **not assessed**.
- Gas 0.75; oil 0.002; geothermal 150 (all Rn-222).

**Derived annual releases (extractor, `annual_release_derived`):**

- Coal mining Rn about 2,780 TBq/a.
- Gas Rn about 408 TBq/a.
- Geothermal Rn about 1,166 TBq/a.
- Oil Rn about 0.23 TBq/a.
- Coal ash radon about 17.9 TBq/a (flow year).

**Collective dose, validation only (full list in CSV):**

- Nuclear public, first pass 130 man Sv (0.43 man Sv/(GW a)), made up of mining and milling 53, plant operation 68, reprocessing 7.6. Including global components: 910 (100 y; 3.0), 1,700 (500 y; 5.5), 7,600 (10,000 y; 25).
- Coal public: 1,400 man Sv (older plants) or 670 (modern); 1.4 or 0.7 man Sv/(GW a).
- Gas 55 (0.10); oil 0.03 (0.0003); geothermal 5–160 (1–20).
- Occupational: nuclear 788 man Sv (reactor operation 628); coal mining ~11,000 (alternative simple scaling 23,000); gas 7; oil 17; geothermal 0.4–0.8; decommissioning 1.80 man Sv/(GW a).
- Construction-mining occupational: PV 0.8 man Sv/(GW a), wind 0.1, nuclear 0.02, coal, gas and biomass 0.01.

## 5. UNSCEAR boundaries and assumptions versus METHODS

1. **Collective-dose truncation.** 100 y standard; ×100 for tailings and ash radon (100 y of continued emission); 500 and 10,000 y for H-3/C-14/Kr-85/I-129. METHODS has no truncation, since the project works in Bq and W. Do not compare dose across the integration choices.
2. **Mill tailings.** Treated as 1 ha/(GW a) at an emission flux (3→1→0.1 TBq/(GW a)). Their radon is a continuing 100–10,000 y release, counted in 2016 as a per-year-of-practice multiple. METHODS §5.2 instead treats it as an exhalation process from an Impounded Ra-226 stock. Do not enter UNSCEAR's 100-year multiple as a flow.
3. **Radon from mining.** Modelled as ventilation air radon (66 TBq/(GW a)), not as moved earth or waste rock. Waste-rock radon was acknowledged but never quantified (2008 ¶155–156). METHODS §5.3 counts waste rock above thresholds in Impounded.
4. **ISL radon.** Assumed equal to milling (3 TBq/(GW a)); 2016 ¶224 says data are inconclusive.
5. **System boundary.**
   - UNSCEAR excludes storage, transmission and distribution, hydro, accidents (¶10), non-electric uses of coal, oil and gas (heat, coking, domestic), and non-power NORM.
   - Public releases of radionuclides other than Rn-222 and the U-238 series are not assessed for fossil fuels (Th-232 series and K-40 excluded, ¶105).
   - Aquatic coal and oil releases are excluded. Oil and gas production NORM (scale, produced water) is only occupational (¶138–150) and in 2000B T28.
   - Coal washery refuse and coal mine tailings are dismissed as soil-like (¶100).
6. **Coal-plant mix.** Older versus modern plants are bounds, not an actual world split (older and modern plants differ only in Po-210/Pb-210 and the other U-series stack nuclides; Rn-222 is identical).
7. **Rare-earth attribution.** UNSCEAR does no allocation or co-product accounting (¶173(b): one metal per ore). METHODS §10.1 allocates by value.
8. **Upstream nuclear liberated activity.** UNSCEAR "discharges" are net airborne and liquid effluents. They exclude in-core inventory (§5.4), spent-fuel and waste arisings, and reprocessing throughput. Reprocessing discharges are normalised to French PWR fuel only (47 GW a). Sellafield and Mayak could not be related to electricity (¶65).
9. **Activity convention.** Parent-only reporting (Cs-137, Ra-226, U-238); METHODS §3.2 applies a multiplier on ingestion.
10. **Reactor groups.** WWER inside PWR; AGR inside GCR (2000, 2008 tables) but split in 2016 Table 11.
11. **Period basis.** 2008 and 2000 tables are five-year normalised averages (reactor releases divided by electricity from reporting reactors). "Total" columns are energy-weighted.

## 6. Contradictions and quality flags

- 2008 Table 17: H-3 "Total" 1970–74 is printed as 448; 2000 Table 37 prints 48. The 2000 value is consistent with the other columns, so 448 is probably a typo. Both are in the CSV.
- 2008 versus 2000 differences for the same period: GCR noble gases 1990–94 (2,050 vs 1,600), GCR 1995–97 (252 vs 1,200), HWR noble gases 1985–89 (190 vs 170), PWR I-131 1990–94 (0.00033 vs 0.0003). Prefer 2008 (the later revision).
- 2008 Table 18: GCR noble gas "148 × 10⁻¹ PBq" printed. I recorded 14.8 PBq; it looks inconsistent with a GCR share of only about 2% of energy.
- UNSCEAR 1993 ¶83 says 75 TBq/(GW a) is "a factor of almost 4" above the 1982/1988 value, but 1988B ¶27 says ~70 TBq/(GW a), the same as 1982.
- 2016 Table 43: Mo ore figure is inconsistent with its metal figure (§3). Table 45 solar 0.8 versus my sum 0.75.
- 2016 Table 13: the Bq/s block's column assignment was read from linearised text; the verifier checked all 51 values against the p. 163 page image and they match.
- 2000B Table 28 oil extraction water-release column (Th-228 217 > Ra-226 174) is as printed.
- Reactor tables from 1993 and 1988 were not transcribed because their scans are unreadable and 2000/2008 restate them. Original 1970–89 values therefore equal the 2000 Table 37 values.

## 7. Gaps for Tasks 1.2–1.6

- **1.2 Nuclear.**
  - No stage-level data on conversion, enrichment or fabrication after 1985; UNSCEAR only reuses a dose factor of 0.003 man Sv/(GW a).
  - No in-core or spent-fuel activity (only Table 21's Bq/MW(e) LLW).
  - 2000C Table 40 (annual releases by plant 1970–97) and 2008 Tables A-6 to A-14 (country/site level) are available but not extracted.
  - No civil/military split for Sellafield, Mayak or Marcoule.
  - Sea dumping and accidents are covered in other reports.
  - The 1982 Annex F fuel-cycle annex was not read.
- **1.3 Coal.**
  - No Th-232 series, K-40 or aquatic releases.
  - Ash and fly-ash tonnages are only in 1988A/1993A text (about 280 Mt/a).
  - Coal activity by basin is only in 2016B Table 25 (country ranges, not extracted) and older reports.
  - No factors before about 1980; before that need modelling.
- **1.4 Oil and gas.**
  - Only Rn-222 in gas and oil as burned. Scale/produced-water NORM has no quantified release (Table 28 of 2000B gives one typical installation).
  - No unconventional, oil-sands or flaring factors.
- **1.5 Wind and solar.**
  - Only ore-mass for 2010 (one Swiss c-Si roof system; wind from White and Kulcinski); no activity or Bq at all. CdTe, CSP and offshore wind not covered.
  - The rare-earth route is absent from UNSCEAR's calculation.
  - Table 43 is the only ore-per-kW h source for solar; Task 1.9 needs independent material intensities.
- **1.6 Other energy.**
  - Geothermal: only two plants (Geysers, Larderello); no binary-plant data.
  - Biomass and peat: no radiological release factors (Cs-137 excluded, peat U-238 40 Bq/kg only).
  - Hydro: not assessed.
- **Task 3.5.**
  - Needs Annex A (S0002) dose-per-unit-release tables (Tables 22–31) to convert our releases to collective dose. Not extracted here.
  - Characteristic individual doses (Tables 14, 28, 33) and per-nuclide dose tables (18, 49, 51) are not extracted.
  - No pre-2010 reference year exists for the non-nuclear streams in dose terms beyond the crude 1982–1993 values in Table 1.
- All stream factors from UNSCEAR are single-point or 5-year averages. No uncertainty ranges except bounds (older/modern coal; geothermal two population densities).

## 8. Inaccessible or partially accessible sources

All ten documents were downloaded (open). Items not obtainable or not machine-readable:

- UNSCEAR 1982 Annex F, "Environmental exposures from nuclear power production" (not downloaded): https://www.unscear.org/unscear/uploads/documents/publications/UNSCEAR_1982_Annex-F.pdf
- UNSCEAR 1993 Annex B reactor/fuel-cycle tables (scanned; OCR unusable). Page images only: https://www.unscear.org/unscear/uploads/documents/publications/UNSCEAR_1993_Annex-B.pdf
- UNSCEAR 2016 Annex A electronic attachments 1–5, for Task 3.5 (zip not downloaded): https://www.unscear.org/unscear/uploads/documents/publications/UNSCEAR_2016_Annex-A_Attach_5.zip
- UNSCEAR 2008 Annex A tables A-4 to A-14 (site-level effluents), possibly in the same Vol. I PDF appendix: https://www.unscear.org/unscear/uploads/documents/publications/UNSCEAR_2008_Annex-B-CORR2.pdf
- Direct guessed URL `www.unscear.org/docs/publications/2016/UNSCEAR_2016_Annex-A.pdf` and the 2017/2020 corrigendum PDFs under `/docs/publications/2016/` return 404. The corrigenda are already incorporated in the CORR2 PDF.


## 9. Independent verification (2026-10-20)

Verdict: passes with fixes. All high-value rows (every 2010 reference value, the "why solar" quotes and tables) match the PDFs. Stratified random sample (seed 1101, 70 rows): 0 value or unit errors; 3 page-reference errors (U0018–U0020, Table 7 is on p. 157), now corrected. Fixes applied: unit corrected on U0140–U0162; in-row "printed value suspect" flags on U0442 (use 48) and U1020 (~0.14 PBq implied); U0300–U0301 flagged as dose coefficients (validation only); U0302–U0308 marked non-numeric. GCR noble gases 1990–97: prefer the 2008 series (monotonic, later revision), with 2000 as the alternative.
