# Round 3: Larderello provenance, Geysers and flash radon, peat ash, wood and ash Cs-137 (paper-by-paper findings)

Written 2026-11-02. PROPOSALS ONLY. No file in `data/`, `docs/`, `pipeline/` or existing `research/` was edited. Companion file: `research/other/sources_round3.csv` (corrections to S1404, S1405, S1408 to S1412, S1415 to S1419; no new IDs needed, because S1404 already registers George 1980 / LBL-11555).

Conventions: Bq/a throughout, no dose quantities (dose results in the papers are ignored). Pages are printed page numbers unless "PDF p." is given. "Derived" = my arithmetic on cited numbers. "Inference" = my reasoning. Independence tag against UNSCEAR 2016 Annex B (S0001): **I** independent, **P** partly, **D** dependent or upstream of UNSCEAR.

Unit conversions used. $1\ \mathrm{Ci}=3.7\times10^{10}$ Bq, so $1\ \mathrm{nCi/kg}=37$ Bq/kg. Radon per GW a of electricity from a wellhead concentration $c$ (nCi/kg of steam) and a steam rate $s$ (kg steam per kWh generated):

$$\frac{\text{Rn}}{\text{GW a}}=c\times 37\times s\times 8.766\times10^{9}\ \text{kWh}\times10^{-12}=0.3243\,c\,s\ \text{TBq/(GW a)}$$

---

## 1. Answers in brief

1. **Larderello provenance (explicit).** Every Larderello radon number in the registry traces to ONE field dataset: D'Amore's wellhead survey of **March to June 1976, 193 wells** (S1418). George et al. 1980 (S1404) state in the text (LBL-11555 p.7, superscript 1 = their reference 1 = D'Amore) that their Table 1 "lists measurements of radon and steam released from the geothermal plants obtained in an earlier study". S0509 Tab. 3 copies George Table 1 verbatim. UNSCEAR's Larderello figure (300 GBq/d) is numerically George's 8.0 Ci/d = 296 GBq/d. **No Larderello number I hold is independent of the others.** The only separately measured data are the Stanford lab values (Kruger et al. 1977; Semprini et al. 1982 re-measurements), and they read about 1.4 to 2.8 times LOWER than D'Amore's field method for the same wells.
2. **Correction to the brief.** The "Oct 1977 to Nov 1978" period belongs to George's own ambient radon/working-level network (TLD monitors), not to Table 1. Table 1's radon data date from 1976. The 3.9 Ci/d soil exhalation over 150 km² is George's own calculation (18 pCi m⁻² min⁻¹ × 150 km² = 3.9 Ci/d, verified) and is background, not a release.
3. **Geysers (the 38.5 that rested on UNSCEAR alone).** Two sources now. (a) Anspaugh & Hahn (S1416): 1.4 Ci/d at 502 MWe = **37.7 TBq/(GW a)**, which is almost certainly UNSCEAR's own source (**D**). (b) Kruger et al. 1977 (S1415): 16.7 nCi/L in condensate (wells 16 to 31), typical 10 kg steam/kWh gives **54 TBq/(GW a)** (43 at 8 kg/kWh; wells up to about 100) (**I**, different method). So 38.5 is supported, within a factor 1.4. The round-2 suspicion that it may be 3 to 5 times too high is **withdrawn**: the "few nCi/L" quoted by Whitehead is most probably the 3.07 nCi/L drawdown-test value, which Kruger labels The Geysers but which matches the Salton Sea entry (3.1).
4. **Flash fields.** Independent Salton Sea figure (Kruger 1977): separated steam 3.8 nCi/L, derived **about 7 to 15 (centre 10) TBq/(GW a)** at an assumed 6 to 12 kg steam/kWh. This is 8 times below the NZ-derived centre of 80 (Whitehead). Both are low-confidence; the spread across flash fields is about 1 to 200.
5. **Peat ash.** The Finnish-versus-registry gap is a Swedish-versus-Finnish peat difference, not an error: Hedvall's Swedish plant peat (Ra-226 14, Pb-210 53 Bq/kg dry) is 2.4 to 3 times the Finnish production means (4.6 to 5.9; 18). Only the uranium rows sit outside the Finnish evidence; proposal P6.
6. **Wood-to-ash factor 50** is an unsupported IAEA default (TECDOC-1376 pp.32, 38, 55). Measured paired factors: pellets 88 to 580 (n 13, mean 228), chips 24 to 99 (mean 61), power-plant fly ash 86 to 705. With the ash yields stated by Grill, ash retains roughly 0.6 to 1.1 of fuel Cs-137, so the "at most 0.45 leaves" bound in the note on other:0068 does not hold; proposal P8.
7. **Cs-137 stack release.** One primary mass balance exists (Hedvall, Sandviken peat plant): particulate stack escape 0.66%, with 12 ± 2% unaccounted for (assumed gaseous by the authors). No stove measurement anywhere. Proposal P7 widens the high bound of other:0067.
8. **Finland and Austria.** Finnish stemwood Cs-137 mean 13 Bq/kg **at 80% dry matter** = 16 Bq/kg dry (resolves the open basis question for other:0073). Finnish fly ash 1,260, bottom ash 309, grate ash 1,936 Bq/kg. Austrian commercial wood fuel 0.33 to 8.4 Bq/kg (pellet mean 2.2), ash 11 to 867.
9. **Not found in this set:** geothermal scale mass (no source), Rn-220 at stacks (only a Larderello wellhead non-detection), any Cs-137 stove emission measurement.

---

## 2. Larderello provenance chain and independence

| Step | Item | What it is | Independent of the previous step? |
|---|---|---|---|
| 1 | D'Amore, Geothermics 4 (nos 1-4), pp.96-108 (S1418) | **Primary.** Wellhead survey, 193 wells, about 200 km², March to June 1976; Rn per L gas, per kg fluid, per well (mCi/h) | root |
| 2 | George, Scandiffio & Breslin, LBL-11555 pp.3-13, Table 1 p.8 (S1404) | Plant-level Rn (Ci/d) and steam (t/d) for 7 areas; stated to come from "an earlier study" = ref. 1 = step 1; the area names equal the field areas of D'Amore's Fig. 7 | **No** (George's own data are the 1977-78 ambient monitors, a different quantity) |
| 3 | Semprini, Kruger & D'Amore 1982 (S1405) Table 1 | 22 Serrazzano wells, 41 to 302 nCi/kg, field method (D'Amore's) + Stanford lab re-measurement of 15 wells; says 1976 and 1982 agree; maximum 302 equals D'Amore well 53 | **Partly** (same field method, possibly the same values; lab data not tabulated) |
| 4 | Italian report S0509 (≥2013, EGP Castelnuovo) | Tab. 3 = George Table 1 verbatim, Tab. 2 = Semprini 22 wells, RSE 2013 model 1.9e5 Bq/s (20 MW) | **No** (copy of steps 2 and 3) |
| 5 | UNSCEAR 2016 Annex B Larderello 300 GBq/d (S0001) | 300 GBq/d vs George 8.0 Ci/d = 296 GBq/d | **No** (inference from numerical identity; Annex not re-read) |
| 6 | Kruger, Stoker & Umana 1977, Table 1-2 (S1415) | **Separate measurement** (Stanford lab, evacuated cylinders, nCi per L of condensate): Larderello mean 34.6; wells 85 = 57.7, 89 = 18.9 | **Yes**, but 2.2 to 2.8 times below D'Amore for the same wells 85 and 89 (162 and about 42 nCi/kg), and about 1.4 below in Semprini's 15-well regression (field = 21.1 + 1.24 lab). Cause unresolved: method, date, or condensate-only basis |

**Cross-check of steps 1 and 2 (derived).**
- George per area, Bq per t steam (nCi/kg): Larderello 4.2e6 (112), Castelnuovo 7.6e6 (205), Sasso 3.1e6 (83), Serrazzano 6.7e6 (181), Lagoni Rossi 2.8e6 (75), Lago 3.0e6 (80), Monterotondo 1.4e6 (38); total 8.0 Ci/d over 68,600 t/d = $4.31\times10^{6}$ Bq/t = 117 nCi/kg.
- D'Amore wellhead: 36 cleanly OCR'd rows mean 138, median 125 nCi/kg; Semprini's 22 wells mean 134.6, median 134, geometric mean 124. So the plant-level mean is inside the well-level spread.
- D'Amore per-well flux (mCi/h column): the 61 readable rows average about 2.4 mCi/h, so roughly 10 Ci/d (range 8 to 12) for 193 wells, with about 80,000 t/d of steam (mean flow 17 to 18 t/h per well); George's 8.0 Ci/d and 68,600 t/d are 0.8 and 0.85 of that. This is a rough extrapolation (scan OCR poor); a full transcription of Table 1 (PDF pp.7 to 12) would settle it. Conclusion: George's table is consistent with being an aggregation of the 1976 survey with ENEL steam flows.
- George's pCi/L column (54,000 to 163,000 pCi/L) does not match D'Amore's 1 to 20 nCi/L of gas; implied gas yields from Ci/d divided by pCi/L are 0.5 to 2.6 L per kg steam against 12 to 60 Nl/kg measured. Ignore the pCi/L column.

**Per GW a, all routes (derived at 6.8 t steam/MWh = 68,600 t/d over 420 MWe at full load):**

| Route | TBq/(GW a) | Independence |
|---|---|---|
| George Table 1 (8.0 Ci/d; 420 MWe; capacity factor 0.9 to 1.0) | 257 to 286 | D (step 2) |
| D'Amore wellhead mean 125 to 138 nCi/kg × 6.8 t/MWh | 276 to 304 | root dataset |
| RSE 2013 model 9.5e3 Bq/s per MW | 300 | D |
| UNSCEAR 2016 (300 GBq/d, 420 MW) | 261 | D |
| Stanford lab, Kruger 1977 Table 1 (34.6 nCi/L × 6.8) | 76 | **I** (5 wells, different method) |

So other:0002 (260) holds as the field-method value; the registry's low bound 1e14 (100 TBq/(GW a)) is roughly the Stanford-method value (76) and is therefore justified. Later Italian units use less steam per kWh (not in these papers).

---

## 3. Per-paper findings

### 3.1 D'Amore (1975/76), Geothermics 4, 96-108 (S1418)
- **Gives:** the primary well-by-well Larderello dataset (Section 2). Columns: T, P, flow, gas/steam, Rn nCi/L gas (σ), nCi/kg fluid, mCi/h. Typical well 40 to 300 nCi/kg (4.5 to 11 MBq/t). Method accuracy about 10%. Condensate holds a small fraction (Fig. 5, p.100).
- **Pattern:** highest Rn in shallow wells near recharge areas (Castelnuovo, Sasso, Lago, Lagoni Rossi); central zones about 10 times lower; deepest wells 0.2 to 2.0 nCi/L gas (pp.105-107). Supports a 10× spread.
- **Rn-220:** upstream vs downstream decay-tank test (Fabiani well, 24 March 1976): 6.42, 6.30, 6.42 vs 6.67, 6.48, 6.36 nCi/L, no upstream excess, so no thoron detected (no limit stated). Supports a lower Rn-220/Rn-222 ratio for vapour-dominated Italy than the flash default (P9).
- **Corrections:** single author; pp.96-108 (not "1-4"); data 1976. See CSV.
- **Independence:** root of the Larderello chain (D for benchmarking).

### 3.2 George, Scandiffio & Breslin 1980, LBL-11555 pp.3-13 (S1404)
- **Gives:** Table 1 p.8 (per area Ci/d, pCi/L, t/d; total 8.0 Ci/d, 68,600 t/d; verified on the page image); soil Ra-226 0.9 pCi/g (33 Bq/kg), flux 18 pCi m⁻² min⁻¹ (world mean 25.5); natural release 3.9 Ci/d = 52.7 TBq/a over 150 km², about half the plant total; 27 condensing units; gas content 1 to 5% by weight, CO₂ 95%.
- **Factor use:** supports other:0002 only as a copy of D'Amore. Soil exhalation is background.
- **Provenance statement:** p.7 and ref. 1. **Independence:** D.

### 3.3 Semprini, Kruger & D'Amore 1982, SGP-TR-60 (S1405)
- **Gives:** 22 Serrazzano wells, 41 to 302 nCi/kg, mean 134.6 (derived 5.0 MBq/t); field vs Stanford lab regression slope 1.24 (r = 0.90, 15 wells); 1976 and 1982 values agree; Rn tracks steam specific volume (r = 0.65); average emanating power about 3%.
- **Independence:** P. **Use:** confirms S0509 Tab. 2 and the field-vs-lab bias (field about 25 to 45% higher).

### 3.4 Kruger, Stoker & Umana 1977, Geothermics 5, 13-19 (S1415)
- **Gives (nCi per L condensate; ×37 = Bq/kg):** Larderello 34.6, Geysers 16.7, Salton Sea flashing brine 3.1 (wellhead 1.4, separated steam 3.8), East Mesa hot water 0.03 (0.034 to 0.069). Geysers wells 16.3 to 31.4 (mean 23.2). 55 MWe plant at 10 kg steam/kWh and 16.7 nCi/L: 0.2 Ci/d.
- **Derived (formula above):** Geysers 16.7 × 10 = 54 TBq/(GW a) (0.2 Ci/d over 55 MWe gives 49); at 8 kg/kWh 43; well range 53 to 102. Salton Sea separated steam 3.8 × (6 to 12) = 7 to 15. East Mesa about 0.7 even if all radon were released (hot-water binary plants vent none, inference).
- **Anomaly:** Table 3 (3.07 nCi/L) labelled The Geysers in the text, equals the Salton Sea mean; probable mislabel.
- **Independence:** I (Stanford lab dataset).

### 3.5 Anspaugh & Hahn 1979, UCRL-83382 (S1416)
- **Gives:** Geysers measured Rn-222 emission 1.4 Ci/d at 502 MWe (p.11, Table 3 p.26), i.e. $1.4\times3.7\times10^{10}\times365.25/10^{12}=18.9$ TBq/a, or 37.7 TBq/(GW a). Same table: CO₂ 313 t/d (26 t/GWh), H₂S 21.7 t/d. Rn per L CO₂ = 1.4 Ci / (313,000 kg × 505 L/kg) = 8.9 nCi/L, equal to Wairakei stack gas 8.2 (S1402).
- **Factor use:** the evidence for other:0003 (USA 38.5). It is the UNSCEAR source (**D**).
- **Gaps:** no scale or sludge activity, no other fields.

### 3.6 Batini et al. 2002, SGP-TR-171 (S1417)
- Confirms Sesta 6 bis Table 3 (K 1.1 to 2.4%, Th 2.8 to 12.7 ppm, U 2.0 to 4.4 ppm; conversion to Bq/kg: U-238 25 to 54, Th-232 11 to 52, K-40 340 to 750). Ordinary crustal rock; no factor changes; no scale mass.

### 3.7 Hedvall & Erlandsson 1992, J. Environ. Radioact. 16, 205-228 (S1419)
- **Gives:** Sandviken plant (one plant, six bogs within 40 km). Peat (Bq/kg dry): Ra-226 10 to 14, Pb-210 53, Cs-137 1,150. Fly ash: Ra-226 170 to 192, Pb-210 139 to 1,000 (mixed 358), U-238 (alpha) 268 and 1,048, Cs-137 9,110 to 31,740 (mixed 16,790). Mass balance (Table 5): Cs-137 emitted 63 of 9,604 MBq (0.66%), unaccounted 12 ± 2%; Pb-210 61% unaccounted; Ra-226 21%.
- **Enrichment (textile ash/mixed ash, derived):** Pb-210 2.8, Cs-137 1.9, Ra-226 0.94, U-238 1.26, K-40 0.67. Supports other:0028 (1.2; 0.7 to 3), 0030 (3.8; 1 to 8), 0032 (1.3), 0038 (1.05; 0.9 to 1.2: Hedvall 0.67 is below the low bound, minor).
- **Pre-loss bulk ash check (derived):** peat Pb-210 53 / ash yield 0.056 = 950 Bq/kg ash against other:0019 central 800; Ra-226 14 / 0.056 = 250 against other:0018 central 130. Registry centres are consistent with the Swedish plant.
- **Cs-137 in peat ash:** about 20,000 Bq/kg ash (1,150 / 0.056) in a 20 to 80 kBq/m² fallout area equals the high bound of other:0046 (2e7 Bq/t): supports the bound, no change.
- **Independence:** I. This is the "Swedish data via Hedvall" the earlier note wondered about.

### 3.8 Kämäräinen, Kallio & Turunen 2018, STUK (S1409)
- Table 4 p.16-17 numbers are in the CSV. Key (Bq/kg dry; n): fly ash Cs-137 mean 1,260 (78), bottom 309 (69), grate 1,936 (40); fly/bottom median ratio 4.9 (Cs-137), 30 (Pb-210), 2.9 (Ra-226), 4.1 (U-238).
- Plant 5 (53 to 84% milled peat) fly ash: Ra-226 83, U-238 85, Pb-210 225, Th-232 56 Bq/kg: a peat-dominated Finnish ash, 1.5 to 5 times below the registry peat-ash centres (Section 4).
- Fuel not measured, so concentration factors cannot be formed. **Independence:** I.

### 3.9 Vetikko et al. 2015, STUK (S1410)
- Debarked wood Cs-137, n = 83, 59 municipalities (mostly the high-fallout south): mean 13, median 8.1, range 0.1 to 97 Bq/kg **at 80% DM**, i.e. per kg dry matter 16 (mean), 10 (median), up to 121. Bark 10 to 766 (80% DM), 3 to 15 times wood. Species not significant (p = 0.07); fallout class significant (p < 0.0001).
- S0513 (Pepin) quotes this paper's 0.1 to 97 and 13; so S0513 is **not independent** of S1410 for Finland.
- **Independence:** I.

### 3.10 Grill 2021, AGES (S1411)
- Fuels (n 64; 62 above detection): 0.33 to 8.36 Bq/kg; pellet mean 2.17 (n 55). Ash: 11 to 867 Bq/kg; pellet ash 195 to 867 (n 13), chips ash 11.8 to 219. Paired ash/fuel factors: pellets 88 to 580 (derived mean 228, median 198), chips 24 to 99 (mean 61), log 348, briquette 232. Ash yield assumed 0.5% (pellets), 1% (chips).
- Fuel basis (fresh/dry) not stated; pellets partly imported. **Independence:** I.

### 3.11 Radulovic, Pepin & Wiegers 2022 (S1412), slides
- Two Belgian plants, Cs-137 in pellets about 1 Bq/kg; fly-ash factors 86 to 705, bottom 4 to 105; 31-sample firewood campaign (max 710 Bq/kg, 84% below 100). No emissions. **Independence:** I (shares authors with S0513).

### 3.12 IAEA-TECDOC-1376 (S1408)
- CFash = 50 is an assumed default (pp.32, 38, 55); no basis, no release fraction. The registry's note on other:0068 relied on it. Measured factors above exceed 50.

---

## 4. Proposed factor changes (PROPOSALS ONLY, old to new)

| # | factor_id | Field | Old | Proposed | Justification | Confidence |
|---|---|---|---|---|---|---|
| P1 | other:0002 (ITA) | evidence text only | "Three routes agree but two are not independent" | Replace by: all Larderello routes derive from D'Amore 1976 (193 wells), George 1980 Table 1 stated to be from it; UNSCEAR 300 GBq/d = 8.0 Ci/d; sole separate dataset Stanford lab (Kruger 1977) is 1.4 to 2.8 times lower (76 TBq/(GW a)). Values unchanged: 1e14 / 2.6e14 / 4e14 | Section 2 | High that the chain is single-source; medium for the value |
| P2 | other:0003 (USA) | value_central (optional) | 3.85e13 | **Keep 3.85e13** (or 4.5e13, geometric mean of 37.7 and 54). Delete the round-2 note that 38.5 "may be high"; replace by: Anspaugh 1.4 Ci/d at 502 MWe = 37.7 (D) and Kruger 16.7 nCi/L at 10 kg/kWh = 54 (I) | Section 3.4 and 3.5 | Low-medium |
| P3 | other:0003 | value_low | 5e12 | unchanged (allows a flash/binary share) | | n/a |
| P4 | other:0001 (XWL) | value_central | 8e13 | **Option B: 4e13** (low 5e12, high 4e14). Evidence: NZ 40 to 200 (S1402, I, CO₂-scaled, hinges on assumed 29 to 150 t CO₂/GWh) vs Salton Sea 7 to 15 (S1415, I, assumed 6 to 12 kg steam/kWh) vs Cerro Prieto about 40× below The Geysers per unit volume (S0505, unit unclear). Option A: keep 8e13 and only lower value_low from 2e13 to 5e12. World mean (2020 weights 6.4% ITA 260, 19.3% USA 45, 74.3% XWL): option A 85 TBq/(GW a) (0.57 of UNSCEAR 150), option B 55 (0.37, at the edge of the factor-3 test) | Section 3.4 | Low |
| P5 | other:0067 | value_high | 0.05 | **0.13** (low 0.0005 and central 0.005 unchanged) | Hedvall: particulate stack escape 0.66% (supports central); 12 ± 2% unaccounted, authors assume gaseous (upper bound 0.12 to 0.13). The unaccounted fraction is within the peat-input scatter (CV 14%), so it may be sampling error | Low |
| P6 | other:0015 (U-238+), 0016 (U-234), 0021 (U-235+) | value_low and central | U-238 and U-234: low 1.2e5, central 4e5; U-235+: low 5.5e3, central 1.84e4 Bq/t | U-238 and U-234: low **5e4**, central **2.5e5**; U-235+: low **2.3e3**, central **1.15e4** (0.046 × U-238); high unchanged | Finnish production peat U-238 4.9 Bq/kg / 0.05 = 98 Bq/kg ash (STUK-A143, round 2) and peat-dominated plant 5 fly ash U-238 85 (S1409) lie below the old low bound; Swedish evidence stays 268 to 1,048 (Hedvall alpha), median 420 (SSI). 2.5e5 is about the geometric mean of 420 and about 100 weighted towards Sweden. Ireland, Russia, Belarus, Baltics unmeasured | Low-medium |
| P7 | other:0018, 0019, 0020, 0022 to 0025 | none | | **No change.** Ra-226 central 130 vs Hedvall 170 to 190 (fly) and Finnish 83 to 118; Pb-210 800 vs Hedvall 950 pre-loss and Finnish 360; all inside the low-high ranges. Finnish values are 1.5 to 4 times below centre, Swedish at or above | Hedvall, S1409 | n/a |
| P8 | other:0068 (stove share) | evidence text only | "CF 50 ... at most 0.4 to 0.45 leaves" | Value unchanged (central 0.19). Replace the CF-50 upper-bound argument: measured paired factors pellets 228 (88 to 580) and chips 61 (24 to 99), times ash yields 0.5% and 1% (Grill) give ash retention about 1.1 (0.44 to 2.9) and 0.6 (0.25 to 1.0): no upper bound on release can be drawn, and pellet appliances look close to full retention (supports the low bound 0.05 for pellets). Still no stove stack measurement | S1411, S1408 | Low |
| P9 | new ratio row or evidence on Rn220+ geothermal (round-2 P5) | Rn-220/Rn-222, ITA | none | ITA: low 0.0005, central 0.01, high 0.05 (non-detection at Larderello wellheads, D'Amore p.102-105, no limit stated, my limit about 5% from the equality of up- and downstream counts); keep XWL 0.005 / 0.05 / 0.35 | S1418 | Low |
| P10 | other:0073 (FIN wood, 2001 to 2025) | value_low, central, high | 100 / 13,000 / 97,000 Bq/t | **125 / 16,000 / 121,000 Bq/t dry** (13 and 97 Bq/kg are at 80% DM, ÷ 0.8). Source becomes S1410 (primary) with S0513 as secondary. Stemwood only; bark is 3 to 15 times higher; sampling biased to high-fallout south | S1410 p.8-9 | Medium |
| P11 | optional new row AUT, 2001 to 2025 | Cs-137 per t dry wood | falls to XWL row other:0060 (100 / 1,000 / 10,000 Bq/t) | AUT: low 3e2, central 2.4e3, high 8.4e3 Bq/t (pellet mean 2.17 Bq/kg ÷ about 0.92 DM; range 0.33 to 8.36), basis assumed dry. Commercial pellets, partly imported; low value for a national forest row | S1411 | Low |
| P12 | other:0046 | evidence text | "Finland peat 1994 mean 16 Bq/kg x 20" (round-2 P9 already corrects to 46) | add Hedvall: Sandviken peat 1,150 Bq/kg dry, ash about 20,000 Bq/kg (high fallout 20 to 80 kBq/m²), equal to the high bound 2e7 Bq/t | S1419 | Medium |
| P13 | S1404 to S1419 (sources) | corrections | | see `sources_round3.csv` | | High |

---

## 5. Benchmarks (independence from UNSCEAR 2016 Annex B)

| Quantity | Value | Source | Tag |
|---|---|---|---|
| Larderello Rn-222, per t steam (plant) | 4.3e6 Bq/t | S1404 T1 | D (upstream of UNSCEAR) |
| Larderello wells, 193 (field method) | about 125 to 138 nCi/kg = 4.6 to 5.1 MBq/t | S1418, S1405 | D |
| Larderello Stanford lab | 34.6 nCi/L = 1.3 MBq/t (76 TBq/(GW a)) | S1415 | **I** |
| Geysers per GW a | 37.7 (emission) | S1416 | D |
| Geysers per GW a | 43 to 54 (up to about 100) | S1415 | **I** |
| Salton Sea flash per GW a | 7 to 15 | S1415 | **I** (assumed steam rate) |
| Peat Cs-137 / ash, Sweden | fuel 1,150, fly ash 9,110 to 31,740 Bq/kg | S1419 | I |
| Wood stem Cs-137 Finland | 16 Bq/kg dry (13 at 80% DM) | S1410 | I |
| Bio-ash Cs-137 Finland | fly 1,260; bottom 309; grate 1,936 Bq/kg | S1409 | I |
| Wood fuel and ash Austria | 0.33 to 8.4; ash 11 to 867 Bq/kg | S1411 | I |
| Plant fly-ash/fuel factor Belgium | 86 to 705 | S1412 | I |

---

## 6. Gaps and contradictions

1. **No independent Larderello value** exists in the papers supplied. The Stanford lab method gives 1.4 to 2.8 times lower values than D'Amore's field method; which is right is unresolved. Kruger Table 2 (wells 85 and 89 versus D'Amore 162 and about 42 nCi/kg) mixes dates and bases.
2. **D'Amore Table 1 is a poor scan.** The 10 Ci/d survey total is a rough extrapolation from 61 of 193 rows. Transcribe PDF pp.7 to 12 if an exact survey total matters.
3. **George pCi/L column** is inconsistent with the Ci/d column by 10 to 50 times; cause unknown.
4. **Kruger Table 3** (3.07 nCi/L) labelled The Geysers appears to be Salton Sea.
5. **Geysers steam rate**: 10 kg/kWh is Kruger's "average"; actual 1970s Geysers rates 8 to 10 (inference). That sets 43 to 54.
6. **Flash fields**: the two independent estimates differ by a factor of about 8 and both rest on assumed steam or CO₂ rates. Cerro Prieto has no per-GW a figure.
7. **Hedvall**: U-238 by gamma (65 to 87 Bq/kg in peat) is overestimated by the authors' own admission; use only the alpha numbers. The 12% Cs-137 "missing" fraction is assumed gaseous but is within closure uncertainty.
8. **Grill**: paired chips minimum 21.5 in the text versus 24.5 from the raw pairs (my recomputation); fuel basis (fresh or dry) not stated; ash yields are assumptions.
9. **Vetikko**: the 13 Bq/kg is at 80% DM; the registry row 0073 used 13,000 Bq/t as if dry (resolved by P10).
10. **Still missing:** geothermal scale and sludge mass (no source in any of these papers, the weakest factor other:0004 stays unchanged), any stove or small-boiler Cs-137 emission measurement, Irish/Russian/Belarusian peat ash.

---

## 7. Per-paper contribution summary

| PDF (ID) | Contribution to the done condition |
|---|---|
| Radon-222 survey Larderello (S1418) | Primary 1976 dataset; root of provenance chain; Rn-220 non-detection |
| LBL11555.pdf (S1404) | Table 1 source statement (ref. 1 = D'Amore); 150 km² soil calculation verified; Oct 1977 to Nov 1978 period belongs to ambient monitors |
| Interpretation of Radon Concentration (S1405) | 22 wells, field vs lab bias slope 1.24 |
| Kruger 1977 (S1415) | Independent Stanford radon data: Geysers 16.7 (54 TBq/(GW a)), Salton Sea, East Mesa, Larderello 34.6 |
| Anspaugh & Hahn (S1416) | Geysers 1.4 Ci/d = UNSCEAR source; CO₂ 26 t/GWh |
| Batini (S1417) | Confirms rock U, Th, K; no factor change |
| Hedvall & Erlandsson (S1419) | Swedish peat plant: ash and fuel concentrations, enrichment, Cs-137 mass balance (0.66% stack, 12% unaccounted) |
| Kämäräinen (S1409) | Finnish bio-ash natural and Cs-137 levels; peat-dominated plant 5 |
| Vetikko (S1410) | Finnish stemwood and bark Cs-137; 80% DM basis |
| Grill (S1411) | Austrian fuel and ash Cs-137; measured wood-to-ash factors |
| Radulovic (S1412) | Belgian plant fly-ash factors; firewood campaign |
| IAEA TECDOC-1376 (S1408) | CF 50 shown to be an assumed default |
