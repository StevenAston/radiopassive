# Copper tailings classes: evidence, shares, weighted factor (Task 2.4 revision)

Date 2026-11-11. Responds to Steve's proposal of 2026-11-11 (Class A high-U IOCG 1,000 to 3,500+ Bq/kg; Class B porphyry and stratiform 20 to 100 Bq/kg). Bq only, no dose (D1). Status: research draft, nothing applied to `data/`.

Files changed or created:
- `research/wind_solar/commodity_factors_draft.csv`: new column `ore_type` (after `region`); 50 new copper rows; 21 old copper rows kept (17 marked `SUPERSEDED`, 4 smelter rows reviewed, `ore_type = all`).
- `research/wind_solar/copper_class_shares.csv`: annual class tonnages and shares 1950 to 2025.
- `research/wind_solar/sources_task24_proposed.csv`: S0449 to S0461 appended (S0449 Chau 2008 ... S0461 Katebe).
- `research/wind_solar/commodity_notes.md` section 3.5 and `research/tier2_memo.md` (revision box, section 0 items 3 and 5, section 4 and 7 figures).

Labels: **[E]** read in the document; **[R]** read only through a fetch-tool summary or second-hand; **[I]** my arithmetic; **[A]** my assumption, unsourced. Conversions: 1 ppm U = 12.35 Bq/kg U-238 (from $1.235\times10^{7}$ Bq per kg U); 1 ppm Th = 4.06 Bq/kg Th-232; 1 pCi/g = 37 Bq/kg; U$_3$O$_8$ is 84.8 % U.

---

## 1. Bottom line

1. **Class B (porphyry and standard stratiform): supported, but narrower at the bottom than proposed.** Measured copper tailings and ore sit at about 8 to 65 Bq/kg per nuclide (Poland, Arizona, Australia). I use 15 / 30 / 100 Bq/kg (low / central / high), not 20 to 100, with a heavy right tail that the class bounds only partly cover.
2. **Class A (high-U IOCG): supported at the low end, understated at the top, and far more important than its production share suggests.** Prominent Hill and Carrapateena land at 1,300 to 2,950 Bq/kg U-238, inside your range. Olympic Dam itself has tailings U-238 of about 2,000 to 5,800 Bq/kg and Ra-226, Pb-210 and Po-210 of about 7,000 Bq/kg each, so the type case sits above the "3,500+" band for the radium series. Class A is only 2.2 % of world mined copper in 2024 but carries **about half** of the production-weighted Bq.
3. **The old generic central (S5 $1.35\times10^{8}$ Bq per tonne Cu) was too high by about 3x. New 2024 world factor: $4.8\times10^{7}$ (low $2.6\times10^{7}$, high $2.0\times10^{8}$), a spread of 8x instead of 43x.** The low bound rises (class A is always in the mix) and the high bound falls to a third.
4. **DRC Katanga is not a Bq/kg outlier.** On Manzuk and Philippe's own numbers its ore is 50 to 210 Bq/kg U-238 in the background case, and per tonne of copper it is about half of Class B because DRC ore carries 2 to 3 % Cu. What is unusual is the **fate** of the uranium (exported in cobalt hydroxide). I keep `cu_co_stratiform` as a third `ore_type` only so that fate can be attached; it changes the world factor by under 5 %. Recommendation: **page callout only** (section 7).
5. **Olympic Dam is double counted** between copper and nuclear as things stand (about 36 % of the Olympic Dam pool in 2023). Proposal in section 6.

Disagreements with the proposal, as requested:
- Your A range is stated per head nuclide and misses the radium series at Olympic Dam (about 7,000, not 1,000 to 3,500).
- "Porphyry is low in general" holds for tailings bulk, but **no Chilean tailings measurement was found** (Chile is 23 to 35 % of world copper since 2000), so Class B for Chile rests on analogy from Arizona, Poland and Australia.
- Bq/kg alone does not define the classes: the metric is Bq per tonne of Cu, so tailings tonnage per tonne Cu (40 to 400) matters as much as activity.

---

## 2. Evidence table

Material, nuclides, Bq/kg and n as measured. "Class" is the class it informs.

| # | Source (ID) | Material and site | Nuclides | Result (Bq/kg unless stated) | n | Quality | Class and effect on your range |
|---|---|---|---|---|---|---|---|
| 1 | Chau et al. 2008, *Acta Geophys.* 56:505 (S0449) **[E]**, data from Muras and Olszewski 1993 / KGHM | Kupferschiefer copper mines, Poland: flotation waste, ore, concentrate, barren rock, dumps | Ra-226, Th-232 (gamma); no U-238 | Flotation waste Ra-226 30 to 65 (mean 40.3), Th-232 7 to 12.5 (9.4); ore Ra-226 47 to 75 (60.6); concentrate 131 to 145; barren rock 20 to 59; sediments (radium precipitate) 30 to 520, median 150 | 41 gamma results across all solids; n per material not stated | Peer-reviewed, 1993 data, LLD 5 Bq/kg | **B, supports.** Tailings cluster at 30 to 65. Also: the U-rich black shale (62 ppm U, about 770 Bq/kg) does not survive into tailings |
| 2 | IAEA-TECDOC-1952 Table 7 (S0453) **[R]** | Polish copper tailings; Kupferschiefer; Theisen flue sludge; Olympic Dam | U (mass) | Tailings U mean 4.5 ppm (= 56 Bq/kg U-238); Kupferschiefer deposit about 60 ppm; Theisen sludge 22 ppm; Olympic Dam about 230 ppm U (= 2,840 Bq/kg ore average) | not stated | IAEA compilation; read via fetch summary | **B, supports** (56 vs Chau's Ra 40); shows U partitions to smelter sludge. **A**: OD ore average |
| 3 | Duke 2019, Resolution Copper (S0454) **[R]** | Arizona porphyry: exploration ore, development rock, tailings | U and Th (INAA, ppm), Ra-226 (pCi/g) | Ore U median 2.0 ppm (25 Bq/kg), mean 2.6, max 61; Th median 3.0 ppm (12). Ra-226 median 0.69 pCi/g (26), 90th percentile 2.17 (80), **max 102 pCi/g (3,790)**. Tailings U median 1.5 ppm (18.5), range 0.75 to 3.4; locked-cycle tailings Ra-226 0.19 to 1.5 pCi/g (7 to 56) | 5,987 INAA (U detected in 4,622); 224 Ra; 12 tailings composites | Company-commissioned memo, US only | **B, supports, and lowers the floor to about 15 to 20.** Single-sample maximum shows a heavy right tail |
| 4 | ARPANSA TR161, Long et al. 2012 (S0451) **[E]** | 12 Australian "metalliferous and other" mines, tailings (Table B4); commodities anonymised | Po-210, Pb-210, Ra-226, Th-230, U-234, U-238, Th-228, Ra-228, Th-232 | Ra-226 8.7 to 41.8 (mean 23), U-238 8.2 to 36.6, Th-232 10 to 32 (n=5); Pb-210 and Po-210 equal to Ra within error; secular equilibrium in all | 8 tailings (7 with U-238) | Regulator survey, 2011, full radiochemistry | **B, supports ("standard Australia"), but copper cannot be isolated** and Olympic Dam is absent. Floor 8 |
| 5 | Katebe et al. (S0461) **[R]** | Nkana (Zambia, Cu-Co) tailings thickener sediments | Ra-226, Ra-228, K-40 | Ra-226 up to 104 (underflow, Aug 2006) | 3 sites, 3 campaigns | Conference paper, via fetch summary | **B for Zambia, at the top of 20 to 100.** Sediments, not bulk tailings |
| 6 | EPA 402-R-99-002 (S0455) **[R]** | Arizona copper leach sites: sediments and soils (not tailings) | Ra-226, U-238, U-234 | Ra-226 0.7 to 82.6 pCi/g (26 to 3,056, mean 385); U-238 0.7 to 63.3 pCi/g; oxide ore U about 10 ppm | 20 | Regulator study, 1999 | **Contradicts "tightly"** for leach-affected ground (to 3,000). Not bulk tailings |
| 7 | IAEA SRS-49 Table 1, s3.1.9 (S0448) **[E]** | Generic: metal ores (Nb/Ta, Cu, Au), copper slag, smelter dust | various | Ores "up to 10 Bq/g"; copper slag Ra-226 0.4 to 2 Bq/g; Pb-210/Po-210 in precipitator dust up to 200 Bq/g | not stated | IAEA safety report, secondary | Upper bound only (10,000 Bq/kg ceiling); **smelter rows** |
| 8 | BHP Olympic Dam Draft EIS App. S (S0428) and Supp. EIS ch.26 (S0457) **[R]** | Olympic Dam ore, tailings, concentrate, smelter dust | all U-238 series | Ore 500 ppm U (6 Bq/g U-238; 80 Bq/g all series); pit average 100 to 200 ppm; **tailings Ra-226 about 7 Bq/g**; Table 26.10: tailings dust U-238 2 Bq/g, others 8; ore dust 8 each; smelter dust Pb-210 and Po-210 1,000 Bq/g; concentrate 1,000 to 2,000 ppm U-equivalent | not stated | EIS, derived values | **A, type case.** Ra-series 7,000, U-238 about 2,000 |
| 9 | Ehrig et al. 2020 (S0456) **[R]** | Olympic Dam process slide | U$_3$O$_8$ | Mill feed 600 ppm (6.3 Bq/g U-238); flotation tailings 550 ppm (5.8 Bq/g); concentrate 1,500 ppm; sales target 1 Bq/g per nuclide | slide values, approximate | Industry talk | **A.** Upper U-238 value 5,800 Bq/kg; slide mass balance does not reconcile with about 50 % U recovery (simplified flowsheet) |
| 10 | Habibi et al. 2026, *Minerals* 16:671 (S0458) **[R]** | Prominent Hill flotation tailings, size fractions | U$_3$O$_8$ | Max 136 ppm (+2 $\mu$m), 121 ppm (+31 $\mu$m) = 1,270 to 1,420 Bq/kg U-238 | fractions only; head assay not retrieved | Peer-reviewed, 2026 | **A, low end (about 1,300)**, no U recovered so chain in equilibrium |
| 11 | IAEA conference contribution 5110 (S0459) **[R]** | Carrapateena orebody and planned tailings | U | Orebody average 239 ppm U (2,950 Bq/kg); 145 Mt tailings holding over 31,000 t U (about 214 ppm = 2,640 Bq/kg) on a 10 % recovery assumption | resource 134 Mt | Conference, title and authors not retrieved | **A, supports** (2,640 to 2,950) |
| 12 | Manzuk and Philippe 2026 (S1806) **[E]** | DRC Copperbelt Cu-Co oxide and mixed ore | U (ppm), Co | Background U geometric mean 7 ppm (86 Bq/kg), GSD 2.6, 1-sigma 2.7 to 18 ppm; regional radiometric survey 4.2 to 4.4 ppm (52 to 54); artisanal ore 28, 38, 83 ppm; modelled "modestly elevated" mines 30 to 100 ppm (370 to 1,235); seed near deposits 1,000 ppm (12,350) | 134 geometallurgical assays (one mine, Tenke-Fungurume); others from literature | Peer-reviewed; modelled, not measured at plants | **Third class or B?** Background is at the top of B (50 to 210); elevated mines are A-like but are a minority; see section 7 |
| 13 | Barrick Lumwana TR 2024 (S0460) **[R]** | Lumwana (Zambia) | Cu only | 0.52 to 0.55 % Cu, 120 to 140 kt Cu/a; U grade not in the part read; IAEA UDEPO lists 0.05 to 0.10 % U in uranium zones | n/a | Company TR, partial read | **Unresolved**, 0.6 % of world copper |
| 14 | Phase 1 seed: UNSCEAR 1988 Table 46 and TRS 419 Table XX (S0008, S0202) | generic "large-volume metal wastes" | U-238, Ra-226, Pb-210, Th-232 | U-238 30 to 370; Ra-226 190 (0.19 Bq/g), Pb-210 and Po-210 130 each, Th-232 370 | not stated | Older compilations, not re-read today | **Old generic.** Its centre (120 Bq/kg) is 3 to 5 times the measured Class B values. Cause not established (plausibly mixed with U-bearing or leach-affected material) |
| 15 | EC RP-135 Vol. 1 (S0452) **[E]** | Copper smelters (Table 1) | Po-210, Pb-210 emissions | Residues "NK"; no copper concentrations in Tables 11 or 13; EU-15 primary copper 1,044 kt (2000) | n/a | Regulator study, 2003 | **Nothing on tailings or slag.** Confirms smelter gap |
| 16 | Skowronek (S0450) **[E]** | Polish mining NORM, two-page abstract | n/a | Radium in mine waters of copper and coal mines; no tailings numbers | n/a | Abstract | Not usable |
| 17 | `import/EPA-SAB_TENORM_Occurrence-and-Risks_Advisory.pdf`; `import/EPA-SAB_Low-Activity-Mixed-Waste_Release-Modeling_Advisory.pdf` **[E]** | text searched | n/a | No copper concentrations (zero hits for copper; "tailings" appears only for 11e(2) uranium and thorium material) | n/a | Advisory reports | Not usable for copper |

**Reading across.** Rows 1 to 4 agree: bulk copper tailings are 8 to 65 Bq/kg per nuclide, centred near 25 to 40. Row 3 and row 6 show a tail up to thousands of Bq/kg in individual samples (mineralised ore or leach-affected ground), but not in tailings bulk. No source measured tailings from a Chilean, Peruvian, Chinese or Indonesian mine (about 57 % of 2024 production: Chile, Peru, China, Indonesia, Kazakhstan, Russia and Mexico): **gap G-CU-3**.

### 2.1 Verdict on your two ranges

| Range | Verdict | Detail |
|---|---|---|
| Class B, 20 to 100 Bq/kg | **Supported; floor lowered.** | Measured centre about 30, floor about 8 to 19 (rows 3 and 4), ceiling about 65 for tailings and 104 for sediments (rows 1 and 5). Used 15 / 30 / 100. Tight clustering is real for tailings bulk |
| Class A, 1,000 to 3,500+ Bq/kg | **Supported for Prominent Hill and Carrapateena; narrows to a mine list; top end understated.** | U-238: Prominent Hill 1,270 to 1,420, Carrapateena 2,640 to 2,950, Olympic Dam 2,000 to 5,800. Radium series at Olympic Dam about 7,000 each (U extracted, daughters retained) |
| "Porphyry is low in general; Olympic Dam is the high exception" | **Supported for tailings activity** (Arizona, Poland, Australia) but unverified for Chile | Also true that a handful of IOCG mines carry half the Bq (section 4) |

---

## 3. Class definitions (as implemented in the CSV)

All values are head activities per tonne of refined Cu, before D6, S5 groups (U238+, Th232, Ra226+, Pb210+, Po210), tailings only; chain members at ratio 1 (the Phase 1 convention). $S5/t = \text{Bq/kg per nuclide} \times \text{tailings t per t Cu}$ for each of the four U-series heads, plus Th-232.

| `ore_type` | Definition | Region key | Tailings Bq/kg per nuclide (low / central / high) | Tailings t per t Cu | S5, Bq per t Cu (low / central / high) | Grade |
|---|---|---|---|---|---|---|
| `porphyry_stratiform` (B) | Porphyry, skarn and standard stratiform: everything except A and DRC | XWL, 1950 to 2025 | U-series 15 / 30 / 100; Th-232 7 / 12 / 40 | 100 / 200 / 400 | $6.7\times10^{6}$ / $2.6\times10^{7}$ / $1.8\times10^{8}$ | B on activity, C on tonnage |
| `iocg_high_u` (A) | Olympic Dam, Prominent Hill, Carrapateena (verified high U) | AUS, era mixes 1988 to 2008, 2009 to 2018, 2019 to 2025 | OD: U-238 about 4,500, Ra-series about 7,500; PH 800 / 1,350 / 1,420; CP 2,000 / 2,700 / 2,950 | OD 50.8; PH 80 to 110; CP 55 to 80 | OD $1.2\times10^{9}$ / $1.4\times10^{9}$ / $2.7\times10^{9}$; PH $2.6\times10^{8}$ / $5.1\times10^{8}$ / $6.4\times10^{8}$; CP $4.4\times10^{8}$ / $7.0\times10^{8}$ / $9.5\times10^{8}$ | OD B (derived from EIS), PH and CP C |
| `cu_co_stratiform` (C) | DRC Katanga Cu-Co | COD, 1950 to 2025 | Ra-series 52 / 90 / 200; U-238 in tailings 14 / 35 / 57 % of total U | 35 / 45 / 60 | $6.1\times10^{6}$ / $1.4\times10^{7}$ / $4.3\times10^{7}$ | C, modelled |
| `all` | Smelter slag and off-gas, no class split | XWL | unchanged | unchanged | slag $2.2\times10^{6}$ (Ra-226, impounded plus dispersed); off-gas $8\times10^{4}$ | C to D |
| `superseded` | Old generic and old Olympic Dam rows | | | | generic $1.4\times10^{7}$ / $1.35\times10^{8}$ / $6.0\times10^{8}$ | |

Notes on the choices:
- **B tonnage.** The 200 t per t Cu centre is the Phase 1 value kept for comparability. It is not evidence-based; the bounds 100 to 400 correspond to head grades of about 1.0 to 0.25 % Cu. Polish ore at 1.6 % Cu would be about 70 t/t and Lumwana at 0.52 % about 210 t/t. Falling world head grades make t/t rise over the period; I hold it constant (sensitivity: about plus or minus 30 % on every B figure).
- **A is not an activity class alone.** PH and CP numbers are derived from U ppm in tailings fractions or orebody grade, not Bq measurements. Th-232 for A is an assumption (15 / 40 / 100 Bq/kg; under 1 % of class S5).
- **C Ra-226 is assumed equal to ore U**, not measured: no Katanga radium result is in the pack. Sediments downstream of Kolwezi reached U-238 154 to 378 Bq/kg (Atibu et al. 2021, via a citing paper, not read; S1811), which says the tailings could be higher.

---

## 4. Production shares and the weighted factor

### 4.1 Method and sources

- World mined copper and country series: `data/activity/commodity_production.csv`, `prod_copper` (USGS DS140 and Mineral Commodity Summaries via OWID; S0826, S0807). World 23.0 Mt in 2024. The sum of listed countries exceeds the world series by 5 to 8 % in 1970 to 1985 and is 13 % below it in 2024 (several countries stop in 2023), so I use country-over-XWL shares.
- **DRC (C):** `prod_copper` COD over XWL, 1970 to 2024. Before 1970 the repository has no country series; I fix 7 % (1970 data point 6.5 %; Union Minière era from memory, **[A]**). You said about 10 to 15 % of world mined copper now: the series gives **14.3 % in 2024** (3.3 Mt of 23.0), 7.8 % in 2020, 2.3 % in 2010, 0.2 % in 2000. The share was 6 to 7 % in 1970 to 1985 and collapsed to under 1 % in 1995 to 2005.
- **A (iocg_high_u):** my own mine-level estimates (**[A]**, plus or minus 20 %): Olympic Dam 45 kt (1988 to 1989), 60 kt (1990 to 1996), 100 kt (1997 to 1999), 190 kt (2000 to 2022), 213 kt (FY2023, BHP 20-F, S0407), 322 kt (FY2024, press report of BHP result), 330 kt (2025, assumed); Prominent Hill 100 kt from 2010 (2009: 40 kt); Carrapateena 20 to 95 kt, 2019 to 2025. These are not read from company reports; BHP and OZ Minerals annual reports should replace them. One inconsistency: FY2024 322 kt is "39 % up" on the prior year per the press report, but FY2023 in the 20-F is 212.5 kt (+51 %).
- **B** is the remainder. Zambia, Poland, Chile, Peru, China, USA, etc. all fall in B.
- **Other IOCG with unverified U** (Candelaria, Salobo, Sossego, Ernest Henry, Mantoverde, Raúl-Condestable and similar): about 0.5 % of world copper before 1995 rising to about 2.5 % from 2005 (my estimate, **[A]**), left in B. Sensitivity below.

### 4.2 Class shares by era (production-weighted means)

| Era | A iocg_high_u | B porphyry_stratiform | C cu_co_stratiform (DRC) | Memo: Zambia (in B) | Memo: other IOCG, unverified (in B) |
|---|---|---|---|---|---|
| 1950 to 1959 | 0 | 93 % | 7 % | about 12 to 15 % **[A]** | about 0.5 % |
| 1960 to 1969 | 0 | 93 % | 7 % | about 12 to 15 % **[A]** | about 0.5 % |
| 1970 to 1979 | 0 | 93.5 % | 6.5 % | 10 to 12 % | about 0.5 % |
| 1980 to 1989 | 0.1 % | 93.7 % | 6.2 % | 6 to 8 % | about 0.5 % |
| 1990 to 1999 | 0.7 % | 98.3 % | 1.0 % | 3 to 6 % | about 1 % |
| 2000 to 2009 | 1.3 % | 98.0 % | 0.7 % | 2 to 5 % | about 2 % |
| 2010 to 2019 | 1.6 % | 93.5 % | 5.0 % | 4 to 5 % | about 2.5 % |
| 2020 to 2025 | 1.9 % | 89.1 % | 9.0 % | 3 to 4 % | about 2.5 % |
| **2024 alone** | **2.2 %** | **83.5 %** | **14.3 %** | 3.0 % | about 2.5 % |

Annual figures: `research/wind_solar/copper_class_shares.csv`. Zambia 1950 to 1969 is not in the repository; the 12 to 15 % is recalled, not read.

### 4.3 Weighted world factor (S5 tailings, Bq per tonne of Cu)

Formula, for year $y$ with class shares $s_k(y)$ and class S5 factors $F_k$:

$$F(y)=\sum_{k\in\{A,B,C\}} s_k(y)\,F_k(y),\qquad F_{\mathrm{low/high}}=\sum_k s_k\,F_{k,\mathrm{low/high}}$$

Low is the product of lows and high the product of highs, per the project rule (so the bounds are outer bounds, not a confidence interval).

| Era | Low | Central | High | Central / old central | Class A share of the central |
|---|---|---|---|---|---|
| 1950 to 1969 | $6.7\times10^{6}$ | $2.6\times10^{7}$ | $1.7\times10^{8}$ | 0.19 | 0 |
| 1970 to 1979 | $6.7\times10^{6}$ | $2.6\times10^{7}$ | $1.7\times10^{8}$ | 0.19 | 0 |
| 1980 to 1989 | $8.0\times10^{6}$ | $2.7\times10^{7}$ | $1.7\times10^{8}$ | 0.20 | 6 % |
| 1990 to 1999 | $1.5\times10^{7}$ | $3.6\times10^{7}$ | $1.9\times10^{8}$ | 0.26 | 27 % |
| 2000 to 2009 | $2.3\times10^{7}$ | $4.4\times10^{7}$ | $2.1\times10^{8}$ | 0.33 | 41 % |
| 2010 to 2019 | $2.0\times10^{7}$ | $4.2\times10^{7}$ | $2.0\times10^{8}$ | 0.31 | 40 % |
| 2020 to 2025 | $2.2\times10^{7}$ | $4.4\times10^{7}$ | $2.0\times10^{8}$ | 0.33 | 44 % |
| **2024** | **$2.6\times10^{7}$** | **$4.8\times10^{7}$** | **$2.0\times10^{8}$** | **0.35** | **50 %** |
| Cumulative 1950 to 2025 (792 Mt Cu) | $1.7\times10^{7}$ | $3.8\times10^{7}$ | $1.9\times10^{8}$ | 0.28 | |
| **Old generic** | $1.4\times10^{7}$ | $1.35\times10^{8}$ | $6.0\times10^{8}$ | 1 | |

**2024 contributions to the central:** A $2.4\times10^{7}$ (50 %), B $2.2\times10^{7}$ (46 %), C $2.0\times10^{6}$ (4 %). World copper tailings S5 in 2024: new $1.1\times10^{15}$ Bq/a (central), old $3.1\times10^{15}$.

**Sensitivities on the 2024 central ($4.8\times10^{7}$):**
- Remove class A (treat Olympic Dam, PH, CP as B): $2.5\times10^{7}$ (minus 49 %).
- Other IOCG (2.5 % of world) at class A level ($1.0\times10^{9}$): $7.2\times10^{7}$ (plus 51 %). **This is the largest unresolved lever.**
- DRC at class A level: $1.9\times10^{8}$ (plus 295 %); this is what a naive "Katanga override" would do and my reading says it is wrong.
- Apply the D6 default Cu share (0.74) to all of class A: $4.2\times10^{7}$ (minus 13 %).
- Smelter terms add $2.3\times10^{6}$ (slag $2.2\times10^{6}$ plus off-gas $8\times10^{4}$), 4.6 % of the new central, against 1.6 % of the old.

**Unit check:** $0.35\times$ old is robust to the choice of class A tonnage (it is 49 % of the central) and to B's tonnage (200 t/t, plus or minus 30 %); it is **not** robust to the unmeasured Chilean tailings (which would move B).

---

## 5. Edge cases

| Case | Verdict | Evidence and reasoning | Effect |
|---|---|---|---|
| **DRC Katanga Cu-Co** | **Third `ore_type` (`cu_co_stratiform`), valued like B, but a flag for fate.** 14.3 % of world copper in 2024 (USGS series; your 10 to 15 % holds) | Ore U 52 to 210 Bq/kg in background (4 to 17 ppm); minority of mines at 370 to 1,235; per tonne Cu about $1.4\times10^{7}$ vs B $2.6\times10^{7}$ because DRC ore is 2 to 3 % Cu. U-238 per tonne Cu from Manzuk's totals is $2.5\times10^{6}$ to $8.3\times10^{6}$ Bq (about 3 to 4 $\times10^{6}$ central), versus B's U-238 head $6\times10^{6}$ | World factor changes under 5 % either way. Folding C into B is acceptable if the cobalt callout is not built |
| **Zambia (Nkana, Konkola, Mufulira)** | **B**, flagged | Nkana tailings sediments Ra-226 up to 104 (row 5); same Katanga System geology as the DRC, so a U association is likely but not measured | Zambia 3 to 5 % of world; if treated as C the 2024 factor moves by under 1 % |
| **Zambia, Lumwana** (Cu-U, 0.52 % Cu) | **Unresolved; B in the draft** | IAEA UDEPO lists 0.05 to 0.10 % U in uranium zones (5,000 to 10,000 t U), but the bulk copper ore U grade was not found (Barrick TR read only in part). If bulk U were 50 to 100 ppm it would be 620 to 1,235 Bq/kg, i.e. A-like | 0.6 % of world copper; at A level it adds about 0.6 % to world share, about plus 8 % on the 2024 factor. **Read the full Barrick TR section 13 (deleterious elements) and any Lumwana radiation management plan** |
| **Polish Kupferschiefer** | **B, with a smelter flag** | The shale is U-rich (62 ppm, about 770 Bq/kg shale), but flotation waste is Ra-226 30 to 65 and tailings U 4.5 ppm (rows 1 and 2); concentrate is 131 to 145 Bq/kg Ra; Theisen smelter sludge 22 ppm U. So U is diluted in bulk ore and partitions into concentrate and smelter dust, not tailings | Poland 1.8 % of world. Tailings per t Cu about 60 to 70 (1.6 % Cu) so it is below B central. Smelting Kupferschiefer concentrate is a candidate Pb-210/Po-210 and U-in-sludge route not in the tables |
| **Other IOCG** (Carrapateena, Prominent Hill) | **A** (verified) | Section 2 rows 10 and 11; U in tailings 1,270 to 2,950 Bq/kg, no U recovered | 0.8 % of world together in 2024 (Prominent Hill and Carrapateena) |
| **Other IOCG** (Salobo, Candelaria, Sossego, Ernest Henry, Mantoverde) | **B in the central, A-level in the high case; unresolved** | No U assay found for any of them in this pass; IOCG as a type is U-enriched at Olympic Dam, Carrapateena, Prominent Hill, not necessarily elsewhere (Candelaria and Ernest Henry are widely described as low-U, but I have no source in hand) | About 2.5 % of world; plus 51 % on the factor if at A. **Highest-value follow-up** |
| **Smelter slag** | Separate row, no class split | Ra-226 0.4 to 2 Bq/g, now confirmed by SRS-49 Table 1; 2.2 t slag per t Cu is still my assumption; BHP: Pb-210 in flash-furnace slag about 10 times Po-210. At Olympic Dam the concentrate target is about 1 Bq/g per nuclide, consistent with the generic slag range | $2.2\times10^{6}$ per t Cu |
| **Smelter dust and Pb-210/Po-210 volatilisation** | Separate row (liberated, air stack), **unchanged, flagged** | SRS-49: precipitator dust up to 200 Bq/g; BHP Table 26.10: Olympic Dam smelter dust 1,000 Bq/g Pb-210 and Po-210; RP-135 lists copper smelters as emitters with residues "NK". The off-gas row rests on one 1980s US plant with assumed capacity | $8\times10^{4}$ per t Cu; small only because dust mass is small; direction of error is up (older plants, uncontrolled smelters in non-OECD countries). Gap G-CU-2 stays open |
| **Heap leach and SX-EW** | Treated as B; flagged | No flotation tailings but spent ore and raffinate; EPA 1999 shows leach systems can concentrate U and Ra locally; IAEA TECDOC-1952: Chilean heap-leach solutions could carry 1,000 to 2,000 t U/a | SX-EW is a large minority of Chilean copper; not modelled |

---

## 6. Olympic Dam overlap with the nuclear stream and a D6 proposal

### 6.1 What the nuclear stream already counts

- `data/activity/uranium.csv` has `u_production` for `AUS` as a **whole-country** series (Red Book retrospective to 2000, OWID for 2005 to 2010, WNA from 2015): 3,534 tU (1988), 7,579 (2000), 6,203 (2020), 4,693 (2023), 4,598 (2024; 2025 carried forward). Olympic Dam is inside it: FY2023 U$_3$O$_8$ 3,406 t (2,888 tU, S0407) is 62 % of the 2023 figure. Ranger (to 2021), Beverley/Four Mile and Honeymoon make up the rest. The nuclear script (`NUCLEAR_SPEC` section 4.1) runs every producing country at generic per-tU factors, with the `XWL` default ISL share (0.165 for 2020 to 2025). There is **no Olympic Dam treatment** in the spec.
- So F1 to F6 for AUS already include Olympic Dam. F6 books mill tailings per tonne U (conventional tonnage only): Ra-226 $1.27\times10^{10}$, Pb-210 and Po-210 $1.17\times10^{10}$ each, residual U-238 $6.5\times10^{8}$ Bq per tU (S5 members total $3.7\times10^{10}$).
- **Overlap in 2023 [I]:** Olympic Dam pool, S5, $=212.5\ \mathrm{kt\ Cu}\times1.37\times10^{9}=2.9\times10^{14}$ Bq. Nuclear F6 books $2{,}888\ \mathrm{tU}\times3.7\times10^{10}=1.06\times10^{14}$ Bq of it: **36 %** (Ra-226 alone $3.7\times10^{13}$ of $8.1\times10^{13}$, 46 %). Copper (old rows and the new A rows) books the whole pool. The overlap is about 10 % of the new 2023 world copper S5. Generic F6 is lower than the real pool because Olympic Dam recovers only about half to two thirds of its uranium, so it leaves $2.8\times10^{10}$ Bq Ra-226 per tU produced.
- The AUS F6 line also over-books ISL operations (Beverley, Honeymoon) as conventional because `XWL` ISL share is 0.165 against about 0.4 for Australia (known limit, NUCLEAR_SPEC v1.2). That is separate from this issue.

### 6.2 Proposal (no double count, D6 respected)

**Principle:** one physical pool $P_{OD}(y)$ (Bq per year, from the copper OD rows times Olympic Dam copper output); two ledgers; shares sum to one in every D6 variant.

| D6 variant | Copper ledger (and Au, Ag) | Nuclear ledger |
|---|---|---|
| Default (value) | $(1-w_U)\,P_{OD}$, with $w_U$ the U$_3$O$_8$ share of Olympic Dam product value that year (FY2023 indicative 12 %; Cu 74 %, Au 13 %, Ag 1 %) | $w_U\,P_{OD}$ |
| Bound A (all to main product, copper) | $P_{OD}$ | 0 |
| Bound B (all to radioactive product, uranium) | 0 | $P_{OD}$ |

**Implementation I recommend (needs your decision, changes the nuclear spec):**
1. Add two activity series: `prod_copper_od` (t Cu) and `u_production_od` (t U).
2. In the nuclear script, subtract `u_production_od` from `AUS` before F3 to F6 (the same carve-out logic as the rest-of-world residual in section 4.2 of the spec); keep F1 mine radon generic or carve it too.
3. Write an Olympic Dam family in nuclear using the copper OD factor rows times $w_U$ per variant (a cross-stream factor reference). Copper keeps the OD rows with `alloc:value`; the library applies $1-w_U$.
4. Product uranium (F5) is unchanged: 3.6e13 Bq U-238 per FY2023 goes to the sealed fuel-cycle tier once.

**Interim option (no spec change):** leave nuclear unchanged and write the copper OD rows **net of nuclear F6**: subtract $1.06\times10^{14}/212.5\ \mathrm{kt}\approx5\times10^{8}$ Bq S5 per tonne Cu (2023), so the pool is booked once. Drawbacks: the subtraction varies with the year's U to Cu output ratio, D6 bounds A and B are not respected (default would show nuclear 36 % instead of 12 %), and it is wrong for pre-2000 years when Ranger dominated AUS. I do not recommend it except as a stop-gap.

**Not done:** Olympic Dam monthly U output, FY1989 to FY2022 U$_3$O$_8$ and Cu output (needs BHP and WMC annual reports); the $w_U$ series (needs Au, Ag, U$_3$O$_8$ and Cu unit values; DS140 has no uranium series); the Rn-222 exhalation from the pool (engine, not rows).

---

## 7. DRC cobalt and uranium (Manzuk and Philippe 2026), now read in full

**Claim [E].** Uranium is extracted with DRC cobalt, concentrates in crude cobalt hydroxide (over 95 % of DRC cobalt export form), and leaves the country outside nuclear accountancy. Estimates for 2000 to 2024: **2,000 to 5,000 t U exported** in cobalt hydroxide (under 10 % declared; about 65 % to Chinese-owned firms) and **1,000 to 4,000 t** discarded to tailings in mobile forms.

**Method [E].** (a) Eq. (1): $U_{\mathrm{extracted}} = \mathrm{Co}_{\mathrm{exports}}\times(\%U_{\mathrm{ore}}/\%Co_{\mathrm{ore}})/0.9$ (10 % cobalt loss mine to export; 0.4 % Co ore grade). (b) U grade scenarios: background 7 ppm (geometric mean of 134 assays from one mine, Tenke-Fungurume; GSD 2.6; regional 4 to 17 ppm); near-deposit seed of 1,000 ppm, spread along faults by an iterated Gaussian convolution (10 iterations intermediate, 50 high); no assay validation of the spread. (c) Process model: a single low-pH iron-aluminium-manganese precipitation removes under 10 % of U; a second step at pH 5.5 removes about 50 %. (d) Phosphoric-acid and ion-exchange imports used as a proxy for deliberate removal: only about 20 % of cumulative cobalt exports show evidence of it (3 of 31 mines consistently). (e) Sulphide ore: all U assumed to tailings.

**Numbers [E].** Intermediate mobility: more than 7,000 t U extracted over 2000 to 2024, of which exports 2,000 to 5,000 t and unstable tailings 1,000 to 4,000 t. Low mobility: all mines at 4 to 7 ppm, about 2,000 to 3,000 t exported plus a comparable amount to tailings. High mobility: extracted tonnage reaches roughly 10,000 to 22,000 t (read off Fig. 6b, approximate); modelled 2023 exports about 3,500 t U. If all shipments met the 75 ppm shipping limit, about 350 t U would still have been exported. In 2024 about 40 t U would reach China even then.

**My conversion [I]:**
- 1 t natural U $=1.235\times10^{10}$ Bq U-238, and the same again as U-234 (equilibrium).
- Intermediate total 7,000 t U over 22.27 Mt DRC copper (2000 to 2024, `prod_copper`) is $3.9\times10^{6}$ Bq U-238 per tonne Cu (low $2.5\times10^{6}$, high $8.3\times10^{6}$ from 4,500 and 15,000 t).
- Exports of 2,000 to 5,000 t U over 25 years: $1\times10^{12}$ to $2.5\times10^{12}$ Bq U-238 per year averaged, plus the same U-234; recent years higher (2024 about 275 to 680 t U, $3.4\times10^{12}$ to $8.4\times10^{12}$ Bq U-238 **[A]**, scaled by cobalt output in the Tier 2 memo).
- Against about 60 kt U mined globally in 2024 ($7.4\times10^{14}$ Bq U-238): 0.5 to 1.1 %.

**Quality.** Peer-reviewed, code on GitHub (`rmanzuk/DRC_U_estimate`), supplementary data not in the PDF. The U grades are modelled, not assays of hydroxide; the ore-grade spread model is unvalidated; it covers the 2000 to 2024 window only; CMOC disputes it (press, S1808; not re-checked). The Intellinews item of 1,100 ppm U at Tenke Fungurume (Dec 2016) is **not in the paper**.

**What it changes in the copper factor.** Nothing upward. With Katanga ore at 2 to 3 % Cu, U per tonne Cu is below the B level; the uranium is real but its Bq are in the **cobalt hydroxide product**, not the copper tailings. A Katanga "override" in copper (the Tier 2 memo's candidate) would therefore reduce, not raise, the tailings row. I replaced that suggestion with the `cu_co_stratiform` rows (section 3).

**Recommendation: page callout only, with a `memo` figure, not a stream or commodity row in v2.**
- Why not a **cobalt commodity**: it would need a D6 split between copper and cobalt for the same residue, a fate tier for product-embedded uranium (hydroxide is a product, not a residue; no schema tier fits cleanly), and a Chinese-refinery fate we cannot support; the Bq are 0.5 to 1 % of world uranium mining and the Tier 2 storage share is about $3\times10^{11}$ Bq/a (LFP uses no cobalt).
- Why not a **Katanga copper override**: wrong direction and wrong pathway (above).
- Why not a **nuclear stream addition**: not a fuel-cycle flow and mostly undeclared; adding a modelled, contested flux to the stream whose benchmark is UNSCEAR would weaken the benchmark.
- If you want it in the sums later: a `cobalt` commodity, region `COD`, own_residue rows of $2.5\times10^{10}$ Bq per t U exported (U-238 plus U-234) with the Manzuk scenarios as low / central / high, `basis = modelled`, flagged contested. I have not written those rows.

---

## 8. Other new files: relevance elsewhere

- **tr161.pdf** is ARPANSA Technical Report No. 161, Long, Sdraulig, Tate and Martin (2012), *A Survey of Naturally Occurring Radioactive Material Associated with Mining* (29 anonymised Australian mines, 2011). Beyond copper: **coal stream benchmark**: seven collieries, coal product Ra-226 about 6 to 26 Bq/kg and U-238 about 4 to 19 (about 12 samples, Table C2), colliery tailings Ra-226 18 to 42 (n=5), solid waste 19 to 76; **mineral sands** (anonymised mines w and $\alpha$): ore U-238 up to 1,400 and products to 5,230 U-238 and 37,400 Th-228/Ra-228 Bq/kg; relevant to zircon, ilmenite and monazite rows (section 3.1, 3.3, 3.10 of the notes) as an Australian cross-check. No copper identifiable; Olympic Dam absent.
- **1-s2.0-S0921344920305176-main.pdf** is Deetman, de Boer, Van Engelenburg, van der Voet and van Vuuren (2021), *Resources, Conservation and Recycling* 164:105200 (the grid-tonnage paper, S1805), now read. Its Table 2 gives the **whole electricity sector** (generation plus transmission plus storage) copper inflow of **2,086 kt/yr in 2015 (11.9 % of global production)**, 4,256 kt/yr in 2050 baseline and 4,934 in the 2-degree case (24 and 28 %). The split between T&D and generation is in the Supplementary Information, not the paper (HV underground copper 11.7 t/km, MV overhead 1.49, MV underground 0.66 t/km in Table 1). Effect on Tier 2: the 3.0 Mt per year T&D copper (Thunder Said Energy, grey) exceeds the **entire** modelled 2015 sector inflow, and 4.5 Mt (the upper bound) exceeds the 2050 sector figure. Deetman pushes the central down: with T&D at 2.0 Mt in 2024 the new Tier 2 central is $1.06\times10^{14}$ (0.28 of the old) rather than $1.46\times10^{14}$ (0.39). Needs the SI table to settle; I have kept 3.0 Mt as the stated basis.
- **EC RP-135, EPA SABs, SRS-49, Skowronek:** see rows 7, 15, 16 and 17: nothing new on copper tailings; SRS-49 corroborates slag and dust ranges.

---

## 9. Data and schema notes

- The `ore_type` column is placed after `region` in the CSV; it is empty for all non-copper rows (checked: non-copper rows unchanged). It needs to enter the §4.7 key (OQ-SCHEMA-2) before validation; the REE rows could use it too (Bayan Obo, ionic clay, monazite). Vocabulary used: `porphyry_stratiform`, `iocg_high_u`, `cu_co_stratiform`, `all`, `superseded`.
- **New activity series needed (not in `data/activity`):** class tonnage series `prod_copper_iocg_high_u` (A, by era-mix), `prod_copper_cu_co_stratiform` (C, equals DRC `prod_copper`), and B as the XWL remainder; or drive A and C from `copper_class_shares.csv`. Plus `prod_copper_od` and `u_production_od` if the section 6.2 option is adopted.
- **Source ID clash:** IAEA SRS-49 is S0448 in the Task 2.4 proposals and S1800 in the Tier 2 memo. I used S0448 in the CSV; reconcile when sources are applied.
- Epsilon and seepage for `metal_tailings` are unchanged (0.002 / 0.01 / 0.05; the Olympic Dam flux implies about 0.004). A single `metal_tailings` residue type now covers a 100-fold range in Bq/kg, which the engine handles via the rows, not epsilon.

## 10. Gaps and contradictions

1. **G-CU-3:** no tailings measurement from Chile, Peru, China, Indonesia, Kazakhstan, Russia or Mexico (about 57 % of 2024 output). Class B for them is by analogy.
2. **Other IOCG U assays** (Salobo, Candelaria, Sossego, Ernest Henry, Mantoverde): none found. Worth about plus 51 % on the factor if they are Class A.
3. **Lumwana bulk U grade:** not found (0.6 % of world).
4. **Class A tonnages** are my estimates (plus or minus 20 %). Prominent Hill head U$_3$O$_8$ (Table 1 of Habibi et al.) not retrieved; Carrapateena source is a conference file whose title and authors I could not retrieve (event page blocked: https://conferences.iaea.org/event/146/contributions/5110/).
5. **Olympic Dam internal contradiction:** ore 500 ppm U (Draft EIS) vs pit average 100 to 200 ppm vs mill feed 600 ppm U$_3$O$_8$ (Ehrig 2020) vs about 230 ppm average (TECDOC-1952). I used the mill feed values already in the Phase 1 rows (feed Ra-226 6.8 to 8.2 Bq/g); the tailings Ra-226 7 Bq/g of the SEIS agrees. FY2024 Olympic Dam copper (322 kt) versus FY2023 (212.5 kt) and "39 % up" does not reconcile.
6. **Old factor spread (x60) not explained.** I did not re-read TRS 419 Table XX or UNSCEAR 1988 Table 46 today; the new B values are 3 to 5 times lower than the old centre.
7. **Fetch-tool limits:** items marked **[R]** were read through summaries of the first 100,000 characters of long PDFs; numbers should be checked against the originals before they go on the page. Blocked or failed: Katebe full text (ENA-NORM link returns the paper but I saw only a summary), the IAEA event page (permission), the MDPI PDF version (error), and the PMC reference on Zambian sediments (CAPTCHA: https://pmc.ncbi.nlm.nih.gov/articles/PMC4730529). The Habibi paper is at https://www.mdpi.com/2075-163X/16/7/671; the Duke memo at https://www.resolutionmineeis.us/sites/default/files/references/duke-radioactive-material-2019.pdf.
8. **The 50 % result depends on four mines.** If Olympic Dam's tailings are not representative of its pool (for example, if the EIS Ra-226 value is the feed value, not the tailings value) the factor moves by up to 25 %.
