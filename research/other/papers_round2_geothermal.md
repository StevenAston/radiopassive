# Round 2: geothermal radon, Rn-220, Cs-137 in wood (paper-by-paper findings)

Written 2026-10-27. PROPOSALS ONLY. No file in `data/`, `docs/`, `pipeline/` or existing `research/` was edited. Companion file: `research/other/sources_round2.csv` (new IDs S1402 to S1415; corrections to S0505, S0508, S0509, S0513, S1401).

Conventions: Bq/a throughout; no dose quantities. Pages are printed page numbers of the PDF. "Derived" = my arithmetic on the cited numbers. "Inference" = my reasoning, not in the source. Independence tag on every benchmark-type value: **I** = independent of UNSCEAR 2016 Annex B (S0001); **P** = partly (shares an upstream dataset or may); **D** = dependent / reproduces UNSCEAR.

## 0. Identity of 31058925.pdf

**STUK-A143 (June 2000): Helariutta K., Rantavaara A., Lehtovaara J., "Turvesoiden ja polttoturpeen radionuklidit" (Radionuclides in peat bogs and energy peat), Säteilyturvakeskus / STUK, ISBN 951-712-221-7, ISSN 0781-1705, 58 p. + tables, in Finnish with English abstract (p.5).** It is the full text of S1401, which the registry holds as "abstract only, report series not verified". Peat, not geothermal. See section 6 for what it changes. The `-1` copy of the Italian report is byte-identical (same size, 2,216,065 bytes) and was ignored.

## 1. Answers in brief

1. **Independent Rn-222 per GW a.**
   - Italy (vapour-dominated), independent of UNSCEAR 2016 as a dataset: 257 to 290 TBq/(GW a) (George et al. 1980 plant table via S0509 Tab. 3, p.6; derived per-steam route 227 to 340). The 260 in other:0002 is well supported.
   - NZ (liquid-dominated flash), new, derived: about 40 to 200, centre about 80 TBq/(GW a) (Whitehead 1980, p.283, with an assumed CO2 intensity). Low-medium confidence.
   - USA: nothing new. Geysers 38.5 stays UNSCEAR-only (Whitehead 1980, p.282, quotes "a few nCi/L" for The Geysers from Kruger & Umana 1975, 3 to 5 times lower than the 17 nCi/L of S0502 Table 4).
   - **Is the world default 150 supportable? Not as a default for the countries that actually use it.** 150 is the mean of two dry-steam fields. Because ITA and USA have their own rows, other:0001 only applies to the rest of the world, which is a flash/liquid-dominated fleet (NZ, Mexico, Philippines, Kenya, Turkey, Iceland, Japan, most of Indonesia). The independent flash estimate is about half of 150. Proposal P1.
2. **Rn-220.** Yes, full data in Whitehead & Ditchburn 1996, Table 1 (p.319): 22 wells (20 Wairakei, 2 Ohaaki) plus one fumarole, activity ratio Rn-220/Rn-222 at the wellhead: geometric mean 0.34, median 0.47, ratio of sums 0.20, range 0.02 to 3.5 (fumarole 1.34). Half-life 55.6 s means most decays before release; inference: stack ratio about 0.01 to 0.15. Proposal P5 (new ratio row, centre 0.05).
3. **Wairakei vs Geysers.** The "40x lower" and the "630 vs 620 Bq/L" are on different bases and do not contradict. See section 4.
4. **Scale/sludge mass per GW a.** None of the six PDFs gives it. other:0004 stays the weakest factor. Two small qualitative gains (section 5).
5. **Cs-137.** Pepin et al. gives no stove or stack release fraction. It gives wood-to-ash concentration factors (50 assumed generic; 100 to 200 pellets) and Finnish and Belgian ash levels. The 0.19 central is not contradicted and not tested (section 7).
6. **Italian report.** Larderello per-plant radon table (Tab. 3), 22-well Serrazzano radon table (Tab. 2), RSE 2013 plant release, and Sesta-6bisA rock U/Th/K (Tab. 5). Useful for Rn; marginal for scale (section 8).

## 2. Whitehead (1980), Geothermics 9, 279 to 286 (new ID S1402)

Radon-222 in steam at Wairakei, Broadlands, Ngawha (NZ), 1976 to 1979. Radiochemical Bi-214 method.

Key numbers (nCi = 37 Bq):

| Item | Value | Page / table |
|---|---|---|
| Wairakei bores, Rn-222 per kg total discharge (steam + water) | 0.0175 to 132 nCi/kg (0.65 to 4,900 Bq/kg); four orders of magnitude. Per-bore means (derived): arithmetic mean of 7 bores 39 nCi/kg = 1.4 kBq/kg, geometric mean 3.4 nCi/kg = 124 Bq/kg | Table 1, p.281 |
| Broadlands bores | 0.39 to 2.6 nCi/kg total discharge (14 to 95 Bq/kg; range one order) | Table 2, p.281 |
| Wairakei power-station stack gas | 4.18 to 13.4 nCi (per L of CO2 in the sample, as I read it; stack gas is diluted about 1:2 with air) | Table 3, p.282 |
| Station condensate | mostly 0 to 0.3 nCi/kg; one outlier 6.7. Condensate Rn about 0.022 of gas-phase Rn: radon stays in the non-condensable gas | Table 3, p.282; text p.283 |
| Bore-field waste water, Waikato River, stream | not significantly above zero: radon is lost to air | Table 3, p.282; p.283 |
| Stack mean | 8.23 nCi/L CO2; gas entering the station about 12 nCi/L (assuming all radon but only half the CO2 goes to the gas phase) | p.283 |
| Wairakei bore gas mean | 6.2 nCi/L gas (SD 6.1), "not statistically different" from the stack figure | p.283 |
| Per litre of steam condensate, other fields | D'Amore 1977: 7.8 to 161 nCi/L; Belin 1959 fumaroles 7 to 340; **The Geysers "a few nCi/L"** (Kruger & Umana 1975); **Larderello 18 to 63 nCi/L**; NZ **Wairakei 0.12 to 190, Broadlands 1.3 to 11 nCi/L** | p.282 to 283 |
| Rn-220 | "potentially measurable by this technique ... none was detected, no figures are given" | p.281 |
| Origin | radon from rock, deep, not from dissolved Ra-226; no local radium or thorium deposits at the silica-rich Wairakei and Broadlands fields (not calcite) | p.285 to 286 |

Independent NZ estimate (derived, inference-laden), route A:

- Rn per tonne of CO2 in the gas: 8.23 to 12 nCi/L; CO2 density 1.84 to 1.98 g/L gives 1.5e8 to 2.4e8 Bq per t CO2. Wellhead means in Whitehead's own units are not self-consistent (Robertson column "nCi per L CO2" mean 37; his own per-L-gas mean 6.2); using the 37 would raise the result about 4 times. I take the stack-integrated value.
- CO2 per GWh: no 1970s figure found. Wairakei lifecycle intensity 29 gCO2e/kWh in 2021 and 2022 (NZGA 2023, S1413; lifecycle, includes more than stack CO2); NZ fleet median 64, MW-weighted 73. Fields lose gas over time, so 1976 was probably higher. I bracket 29 to 150 t/GWh.
- Result: $1.5\times10^{8}\ \text{Bq/t}\times(29\ \text{to}\ 150)\ \text{t/GWh}\times8766\ \text{GWh/(GW a)}\approx4\times10^{13}$ to $2\times10^{14}$ Bq/(GW a). Centre about $8\times10^{13}$. **Independence: I** (UNSCEAR 2016 uses no NZ data as far as I can tell). Confidence low-medium.
- Route B (wellhead Bq/kg times discharge mass per GW a) cannot be closed: no flow-weighted well data and no discharge mass per MWe in the six PDFs. Unweighted 1996 Wairakei mean is 3.1 kBq/kg, geometric mean 0.55 kBq/kg.

## 3. Whitehead & Ditchburn (1996), J. Radioanal. Nucl. Chem. 207(2), 313 to 324 (S0508, full text now read)

Alpha spectrometry of Pb-214 and Po-212 daughters on a PbS layer: first reliable Rn-220 measurement in steam.

Table 1 (p.319), Bq per kg total discharge, 1-sigma counting errors only. Rn-222 / Rn-220:

- Wairakei (WK): WK19 6956/141; WK24 121.5/72.0; WK25 6117/363; WK26B 421.6/577.7; WK30 30.38/22.7; WK52 19544/6610; WK59 941/1024; WK65 13284/1044; WK71 18.52/49; WK74 11.11/39.2; WK80 149.1/16.3; WK81 7928/327; WK86 1613/793; WK101 158.4/93; WK107 142.1/62.8; WK108 1039/47.7 (Rn-222 printed "1039 +- 372", probable misprint); WK116 29.09/75; WK118 1342.5/714; WK216 2016.8/466; WK234 577.9/112.
- Ohaaki (OH): OH21 213.3/60.0; OH22 68.0/24.7. Fumarole Karapiti KP22 12491/16680.

Derived statistics, 20 Wairakei wells (Rn-222 mean 3,122, median 759, geometric mean 551 Bq/kg; Rn-220 mean 632, median 127, geometric mean 185 Bq/kg):

| Statistic of Rn-220/Rn-222 | Value |
|---|---|
| Geometric mean of well ratios | 0.34 |
| Median of well ratios | 0.47 |
| Sum Rn-220 over sum Rn-222 (flow-unweighted, dominated by high-radon wells) | 0.20 |
| Range | 0.02 (WK19) to 3.5 (WK74) |
| Ohaaki OH21, OH22 | 0.28, 0.36 |
| Karapiti fumarole | 1.34 |

Other points: Rn-220 detected in every sample, including wells where the 1994 gamma method failed (p.316, 317); earlier gamma method detected it in 9 of 16 wells (p.315 to 316); Rn-220 "ratio to Rn-222 may be an indicator of conditions near the feed zone" (p.313); a blank membrane caught 400 Bq/m3 Rn-222 from the Wairakei plume on a misty day, "atypical", long-term monitoring much lower (p.317); no radiological hazard identified (p.313, citing Robertson & Matthews 1978, NRL 1978/5).

Decay in transit (inference): $^{220}$Rn half-life 55.6 s (paper says 54 s). Survival after transit time $t$ is $2^{-t/55.6}$: 0.47 at 60 s, 0.22 at 120 s, 0.024 at 300 s. Transit from wellhead through the turbine, gas ejector and stack or cooling tower is not given in the paper; I assume 1 to 5 min. Stack-level Rn-220/Rn-222 is then about $0.34\times(0.02\ \text{to}\ 0.47)$, i.e. 0.01 to 0.16. **Independence: I.** Confidence: wellhead ratio medium (n=23, two fields); stack ratio low (transit time assumed). The Rn-220 progeny Pb-212 (10.6 h) is a separate chain-ingrowth question for the engine and is not in any of these papers.

## 4. Wairakei vs The Geysers: reconciliation

Claims in the existing notes: (a) "Rn in liquid-dominated reservoirs (Cerro Prieto, Wairakei) about 40 times lower than the vapour-dominated Geysers" (S0505 p.6 citing Semprini 1981); (b) S0502 Table 4, Wairakei steam 630 Bq/L, Geysers 620 Bq/L.

1. **Different bases.** I re-read S0505 p.6 with the fetch tool: no unit or basis is given for the 40x, and Semprini attributes the difference to pore-fluid density, steam versus water. Steam tables (my arithmetic): saturated vapour density about 17 to 20 kg/m3 at 240 to 250 C against liquid about 800 kg/m3, a ratio of about 40 to 50. So the 40x is most plausibly a per-unit-volume reservoir concentration effect. It does not apply per kg of steam condensate, nor per GW a.
2. **Per litre of condensate** (the basis of S0502 Table 4, not verified by me because the paper is not in hand), Whitehead 1980 p.282 to 283 gives Wairakei 0.12 to 190 nCi/L (4 to 7,000 Bq/L), Geysers "a few" nCi/L (about 110 to 190 Bq/L), Larderello 18 to 63 nCi/L (670 to 2,300 Bq/L). The 630 Bq/L (17 nCi/L) of S0502 lies inside the Wairakei range and about 3 to 5 times above Kruger & Umana's Geysers figure. So the sources disagree on The Geysers by a small factor; there is no 40x gap between the fields on this basis.
3. **Wairakei is not homogeneous.** Per-well Rn-222 varies over four orders of magnitude (Whitehead 1980, p.283; 1996 Table 1). A single "Wairakei steam" value is not meaningful; the plant release depends on the flow weighting, which is what the stack sample (section 2) integrates.
4. **Recommended wording change** for other:0001 notes and notes.md: replace "40x lower reservoir radon at Cerro Prieto and Wairakei" with "per-unit-volume reservoir concentration, consistent with the steam/liquid density ratio; not a per-kg-steam or per-GW a ratio". Residual: Wairakei per GW a is probably below the dry-steam fields (CO2-route estimate above), but by a factor about 2 to 4, not 40.

## 5. Layton & Anspaugh (1981), UCRL-85334 / IAEA-SM-254/38 (new ID S1403)

"Health impacts of geothermal energy", Nashville, 22 to 26 June 1981. Preprint, 20 pages, scanned. **No radon quantity anywhere**: radon is named only as a trace gas (p.3). It is about H2S, benzene and arsenic. Usable content:

- Table I (p.10): installed MWe 1979: China 1, El Salvador 60, Iceland 32, Italy 420.6, Japan 165, Mexico 150, NZ 202.6, Philippines 59.2, Turkey 0.5, USSR 5, USA 663 (+255 on line), total 1,758.9. Footnote p.3: Wairakei installed 192.6 MWe, output 150 MWe (1974). Useful for 1979 fleet weighting (ITA+USA about 62%).
- Table II (p.11), uncontrolled H2S, g/(MWe h): Geysers 1,800; Larderello 14,300; Wairakei 570; Cerro Prieto 32,000; Salton Sea 160; East Mesa 55; Ahuachapan 1,580; Otake 542. Cross-check (inference, low weight): Larderello/Geysers H2S ratio 7.9 versus Rn per GW a ratio 6.7 (260/38.5), so non-condensable gas flux and radon release scale together between the two dry-steam fields; Wairakei H2S is 0.32 of the Geysers, consistent with a lower radon release per MWh. Rn/H2S is not constant across field types, so this is an ordering check, not a factor.
- No solid-waste or scale figures (Q4). Report number confirmed: UCRL-85334 (preprint dated 15 June 1981), authors D.W. Layton and L.R. Anspaugh.
- Whitehead 1996 cites Anspaugh & Hahn 1979 (UCRL-83382) and George et al. 1980 (LBL-11555) as the US radon studies; neither is in hand (S1404, S1416 leads).

## 6. Helariutta et al. (2000), STUK-A143 (S1401, corrected)

- **Correction to the registry.** The S1401 note says "Cs-137 16/622, U-238 11/140, Ra-226 6/35, Pb-210 13/190, Po-210 9/200, Th-232 6/31, K-40 13/213 Bq/kg, 119 samples, 14 bogs". These are STUK-A143 **Table III (p.19 to 20): 119 depth-slice samples from 14 bogs, all depths**, not the fuel. The 1994 energy-peat production samples (68 bogs, Table IV p.21 and Table VII) are: Th-232 3.3 (max 14), U-238 4.9 (max 51), Ra-226 gamma 4.6 (max 18), Cs-137 **46** (max 620, Pollarinneva), Cs-134 1.7, K-40 16 (max 52), all Bq/kg dry weight; Pb-210, Po-210, Ra-226 radiochemical (n about 20, Table VIII): Pb-210 mean 18.2 (median 14.1, max 62.9), Po-210 mean 15.8 (median 12.7), Ra-226 5.9. Table IV prints a Pb-210 mean of 34, which does not match Table VIII; I take Table VIII (the OCR of Table IV may be faulty).
- Peat ash Cs-137 (Fig. 17, p.40): per-bog calculated ash Cs-137 for 1994 production up to about 14,000 Bq/kg; "under a quarter" of bogs above 1,000 Bq/kg ash (p.38). Implied ash yield about $620/14{,}000=4.4\%$ for the maximum bog, consistent with other:0013 (0.05).
- Check of rows 0046 and 0047 (derived): 1994 mean fuel 46 Bq/kg dry, ash yield 0.044 to 0.05, gives 920 to 1,050 Bq/kg ash. Decayed to 2025 (half-life 30.1 a): about 450 Bq/kg ash. Rows: other:0046 central 1e6 Bq/t (1,000 Bq/kg) and other:0047 central 5e5 Bq/t (500 Bq/kg). **Both supported**; the existing evidence text for 0046 ("Finland peat 1994 mean 16 Bq/kg x 20 = 320") should say 46 and ash yield 0.044 to 0.05. Independence: I for UNSCEAR (UNSCEAR excludes Cs-137 in fuel).
- Check of rows 0015 to 0025 (derived): production Pb-210 18 Bq/kg over ash yield 0.05 gives about 360 Bq/kg ash against other:0019 central 800; Po-210 16 gives about 320 against 500 (other:0020); U-238 4.9 gives about 98 against 400 (other:0015, based on Swedish ash median 420 from S0519; Sweden has uranium-richer peat). The Finnish production values are lower than the registry centres by 1.4 to 4 times. Not proposed as changes (the registry centres are Swedish ash measurements); flagged for the peat reviewer.
- Pb-210 and Po-210 surface enrichment and Pb-210 above Ra-226 (p.34 to 35, 37): supports not deriving Pb-210 from Ra-226. Hedvall et al. (1992, Swedish peat plant) is the cited source for enrichment in fly ash; it is not in this file.

## 7. Pepin et al. (2023), Radiat. Prot. Dosim. 199(8 to 9), 759 to 766 (S0513, full text now read)

Review of regulatory handling of Cs-137 in firewood, pellets and ash. **It contains no stove, chimney, or stack release fraction, and no emission measurement.** What it does give:

| Item | Value | Page |
|---|---|---|
| Wood Cs-137, Finland (pine, spruce, birch, no bark; Vetikko et al. 2015) | 0.1 to 97 Bq/kg, average 13 | p.762 |
| Bark, Finland | average 400 (pine), 170 (spruce), 43 (birch) Bq/kg; bark/wood 3 to 6 (birch), 5 to 15 (conifers) | p.762 |
| Ash, Finland biofuel plants (Kämäräinen et al. 2018) | fly ash mean 1,270; bottom ash 310; grate ash 1,940 Bq/kg (half of grate samples from the top fallout zone); overall mean about 1,000, max 6,000 | p.762; p.764 |
| Austrian pellet ash (Grill 2021) | 195 to 867 Bq/kg; concentration factor 100 to 200 | p.759 |
| Belgian biomass power plant ash | about 200 Bq/kg | p.759 |
| Belgian imported firewood (FANC campaign) | about one sample in five above 100 Bq/kg, none above 1,000 | p.763 |
| IAEA TECDOC-1376 dose model | wood-to-ash concentration factor **50 assumed** (generic); "may not be relevant for pellets, up to 200 reported" | p.763 to 764 |

Implications for other:0057 to 0070 (inference):

- **Stove share (other:0068), Steve's approved 0.19.** The file currently shows central 0.25 (low 0.05, high 0.70); 0.19 is the geometric mean of the bounds, as the existing note says. Pepin does not test it. A retention argument bounds only what stays in collected ash: retention $R=\text{CF}\times a$ with ash fraction $a$. For $\text{CF}=50$ and $a=0.011$ to $0.012$ (S0515), $R\approx0.55$ to $0.60$, i.e. at most about 0.4 to 0.45 leaves; for the Swedish 90x it is about 1.0, i.e. about zero leaves (that is S0515's own "Sweden about 0"). For pellets $\text{CF}\times a=100\text{ to }200\times0.005\approx0.5$ to $1$. So the ash-based constraint is 0 to 0.45 and does not conflict with 0.19, but it is weak: CF 50 is an assumption, and ash left in a stove excludes soot that deposits in the flue. **Keep 0.19 as approved; no evidence in Pepin to move it.** Row note should cite this CF argument and say pellet stoves probably sit nearer the low bound.
- **Plant share (other:0067), centre 0.005.** Consistent: Belgian and Austrian plant ash retains almost all fuel Cs ($\text{CF}\times a\approx0.5$ to $1$). No change.
- **Wood rows (other:0057 to 0066).** Finnish wood mean 13 Bq/kg (13,000 Bq/t) is above the Swedish centres 0061/0062 (8,000 and 5,000 Bq/t) and well above the XWL 2001 to 2025 centre (1,000), as expected for a high-fallout country; no country row for Finland exists. Optional new FIN row: centre 1.3e4 Bq/t dry wood (low 1e2, high 9.7e4 per Pepin range; basis "fresh or dry weight not stated in Pepin" is a caveat).
- **B4** (implied Cs-137 in wood ash): independent range points **I**: Finland 2018 ash 310 to 1,940 by fraction (mean about 1,000); Austria pellet ash 195 to 867; Belgian plant about 200 Bq/kg. All above the world-default implied 75 to 112 Bq/kg ash, as expected, since the world default is a fuel-weighted global mean and these are fallout-region measurements. Range test only.

## 8. Italian report, Castelnuovo pilot plant (S0509, full text now read)

Rete Geotermica Toscana (Enel Green Power), "Rapporto sulla radioattivita' delle rocce e da radon", 14 pp., undated (cites RSE 2013 and Directive 2013/59).

- **Tab. 3 (p.6, George et al. 1980, secondary).** Radon released by Larderello-area plants: Larderello (3 plants) 3.6 Ci/d, steam 32,000 t/d; Castelnuovo 1.5, 7,300; Sasso 0.5, 6,000; Serrazzano 1.3, 7,200; Lagoni Rossi 0.4, 5,300; Lago 0.7, 8,700; Monterotondo 0.08, 2,100; **total 8.0 Ci/d (checked: items sum to 8.08), 68,600 t steam/d**. Derived: 8 Ci/d = $2.96\times10^{11}$ Bq/d = 108 TBq/a; per tonne steam $4.3\times10^{6}$ Bq/t (per plant 1.4e6 to 7.6e6); the 54,000 to 163,000 pCi/L column does not reproduce the Ci/d column (ratios 1.5 to 2.6; basis of the pCi/L column unclear); I use the Ci/d column. Per GW a: at 420 MWe installed (Layton Table I) and capacity factor 0.9 to 1.0, 257 to 286 TBq/(GW a); via per-steam route with 6 to 9 t steam/MWh (68,600 t/d over 420 MWe is 6.8 t/MWh at full load; the range is my assumption) 227 to 340. **Independence: P.** UNSCEAR 1988 (110 TBq/a at 400 MW) and 2016 (300 GBq/d at 420 MW) are probably from the same George/ENEL data; I cannot verify that. Treat as a second look at the same measurements, not a separate dataset.
- **Tab. 2 (p.6, Semprini, Kruger & D'Amore 1982, Serrazzano wells, 22 wells).** Rn 41 to 302 nCi/kg (steam basis not stated); mean 134.6, median 134, geometric mean 124 nCi/kg = 4.98e3 Bq/kg = $5.0\times10^{6}$ Bq/t, within 15% of the plant-level $4.3\times10^{6}$ Bq/t. Well data are reported as consistent over 35 years (p.5). **Independence: I** relative to the 8 Ci/d plant table, and to UNSCEAR as far as known.
- **RSE 2013 (p.7).** 1.9e5 Bq/s (20 MW plant), 4.8e5 Bq/s (50 MW): 9.5e3 Bq/s per MW = 300 TBq/(GW a) (derived, as in the existing note). Modelled from the same literature: **D/P**. Gaussian dispersion: below 30 Bq/m3 at about 200 m, below 15 Bq/m3 at about 1 km (p.7).
- **D'Amore 1975** 193 wells, shallow wells near the recharge zone have the highest Rn; deep wells up to an order of magnitude lower (p.5). Supports a spread of at least 10x between Larderello wells and a low bound below the mean.
- **Soil radon** (p.6, George 1980): Ra-226 in soil 0.9 pCi/g (33 Bq/kg), natural flux 18 pCi m-2 min-1, world mean 25.5; plants equivalent 28 pCi m-2 min-1 over 200 km2 (not an activity release; background comparison only).
- **Rock (Sesta-6bisA well near Castelnuovo, Tab. 5, p.12; Batini et al. 2002):** neogene sediments K 1.1%, Th 3.9 ppm, U 2.0 ppm; flysch 1.9%, 2.8, 2.8; tectonic wedges 1.92, 6.7, 2.5; phyllites (1,900 to 2,220 m) 2.38, 11.7, 3.2; micaschists (2,220 to 3,800 m) 2.40, 12.7, 4.4. Ranges p.8: K 1.1 to 2.4%, U 2 to 4.4 ppm, Th 2.8 to 12.7 ppm, 98 to 244 Bq/kg total gamma. Conversion (my arithmetic, 12.35 Bq/kg per ppm U-238, 4.06 per ppm Th-232, 313 per % K): U-238 25 to 54, Th-232 11 to 52, K-40 340 to 750 Bq/kg. Elba comparison (granite, Monte Capanne 1,500 to 3,000 Bq/kg total; U to 25.3, Th to 34.8 ppm; p.9 to 11). Use: ordinary crustal rock, not enriched; no scale or sludge data. Castelnuovo is closed-loop, "no atmospheric emissions" (p.8): an example of the binary/closed class with zero release, supporting a low bound near zero (inference).
- **Drilling tests** only a few tens of t/h for 2 to 3 days (p.7, 12); negligible.

## 9. Scale and sludge (Q4)

- None of Whitehead 1980/1996, Layton & Anspaugh, Pepin, the Italian report or STUK-A143 gives scale mass per MW or GW a. Rockwell 1982 (S1400) remains the only source: other:0004 unchanged; **no proposal**; the 1 to 61,000 t/(GW a) range stays "WEAKEST FACTOR".
- Qualitative: Whitehead 1980 p.285 says Wairakei and Broadlands are silica-rich, not calcite-rich, so no radium-bearing calcite deposits; the Rn source is rock, not dissolved Ra-226 (p.285 to 286); Ngawha hot springs and the Waikato system have no radium deposits. This supports the low end of Ra-226/Pb-210 per tonne for NZ-type sinters, but it is not a value.
- Whitehead 1980 p.285: for hot springs in the western USA mean Rn-222 1,170 pCi/L but Ra-226 only 24 pCi/L (O'Connell & Kaufman 1976, Cadigan & Felmlee 1977): radon is far in excess of dissolved Ra. Supports "Pb-210 and Po-210 are radon-progeny-supported, not Ra-226-supported" in notes for other:0007 and 0008 (already stated there).

## 10. Proposed factor changes (PROPOSALS ONLY, old to new)

| # | factor_id | Field | Old | Proposed | Justification | Confidence |
|---|---|---|---|---|---|---|
| P1 | other:0001 (XWL, Rn222+, air_vented_gas) | value_central | 1.5e14 Bq/GWa | 8e13 (low 2e13 and high 4e14 unchanged). Description: "default for countries without own factor; applies to the flash/liquid-dominated rest of the world" | 150 is the mean of two dry-steam fields (Larderello 260, Geysers 38.5) but ITA and USA are overridden, so XWL only serves flash and binary fleets. Independent NZ flash estimate 40 to 200, centre 80 (section 2, **I**). Rest-of-world share about 74% of 2020 generation; resulting world mean about 83 TBq/(GW a) (6.4% ITA at 260, 19.3% USA at 38.5, 74.3% at 80; my arithmetic) versus UNSCEAR 150: ratio 0.56, still within a factor of 2 of the B1 benchmark. Alternative if Steve prefers UNSCEAR fidelity: keep 150 and label as "UNSCEAR convention". | Low-medium |
| P2 | new row, region NZL, 1958 to 2025 | Rn222+, air_vented_gas | none (NZ falls in XXX remainder) | low 3e13, central 8e13, high 3e14 Bq/GWa, basis "derived" | Whitehead 1980 p.283 Rn per L CO2 times assumed CO2 intensity. The 3e14 high includes the 4x higher Robertson-column interpretation. NZ is about 8% of world geothermal generation (7,728 of 95,098 GWh, 2020, S0510), so P2 mostly documents; P1 carries the weight. | Low |
| P3 | other:0002 (ITA) | none to value | 1e14 / 2.6e14 / 4e14 | **No change.** Add evidence: S0509 Tab. 3 (4.3e6 Bq/t steam; 257 to 286 TBq/GWa), Tab. 2 (22 wells, mean 134 nCi/kg = 5.0e6 Bq/t), per-plant range 1.4e6 to 7.6e6 Bq/t steam (about 92 to 500 TBq/GWa); low 1e14 and high 4e14 bracket it | Three routes agree; two are not independent of UNSCEAR | High for 1980s. Later Italian efficiency changes could lower steam per MWh (new units about 5.5 to 6 t/MWh, not in the six PDFs) |
| P4 | other:0003 (USA) | none | 5e12 / 3.85e13 / 1.5e14 | **No change.** Note: The Geysers is a high-radon US field; Kruger & Umana "a few nCi/L" (Whitehead p.282) hints The Geysers may be lower than 38.5. Optional central 2.5e13 (low confidence, not recommended without a US generation split) | | Low |
| P5 | new ratio row (or two Rn220+ rows), geothermal, XWL | Rn-220 released per Rn-222 released (unit 1) | none exist (no Rn220+ geothermal row in the file) | low 0.005, central 0.05, high 0.35 | Wellhead ratio GM 0.34, median 0.47, range 0.02 to 3.5 (S0508 Table 1, p.319); decay in transit factor 0.02 to 0.47 (assumed 1 to 5 min, half-life 55.6 s). High = no decay. Implement as a product of the Rn-222 factor and this ratio, or give Rn220+ rows directly: central 4e12 Bq/GWa for XWL, 1.3e13 for ITA | Wellhead medium; stack low |
| P6 | other:0004 to 0009 | none | unchanged | **No change.** No source of scale mass in this round. | | n/a |
| P7 | other:0068 (stove share) | value_central | 0.25 file value; Steve approved 0.19 | **0.19** (low 0.05, high 0.70 unchanged). Cite Pepin p.763 to 764 only as a weak upper-bound check (retention argument, 0 to 0.45) | Geometric mean of bounds $\sqrt{0.05\times0.70}=0.187$ | Low; no stove measurement exists anywhere |
| P8 | other:0067 | none | 0.005 | **No change**; Pepin supports near-complete capture in plant ash | | Low-medium |
| P9 | other:0046, 0047 | evidence text only | "Finland peat 1994 mean 16 Bq/kg x 20 = 320" | "Finland 1994 production peat 46 Bq/kg dry (68 bogs, max 620; STUK-A143 Table IV); ash 920 to 1,050 Bq/kg at ash yield 0.044 to 0.05; decayed to 2025 about 450" | Section 6. Central values stay (1e6, 5e5 Bq/t). | Medium |
| P10 | S1401 registry row | corrections | see CSV | see sources_round2.csv | | High |

Not proposed (flagged): peat rows 0015 to 0025 sit 1.4 to 4 times above Finnish production values (section 6); the registry's Swedish ash basis is a valid alternative.

## 11. Benchmark values (independence from UNSCEAR 2016 Annex B)

| Quantity | Value | Source | Tag |
|---|---|---|---|
| Larderello Rn-222 per GW a | 257 to 286 TBq (Ci/d table) | S0509 Tab. 3 | P (same measurements UNSCEAR likely used) |
| Larderello per tonne steam | 4.3e6 Bq/t plant-level; 5.0e6 Bq/t wells (n=22) | S0509 Tab. 3; Tab. 2 | plant-level P; wells I |
| Larderello model | 300 TBq/GWa | RSE 2013 via S0509 p.7 | D/P |
| NZ flash Rn-222 per GW a | 40 to 200, centre 80 TBq | Whitehead 1980 + NZGA 2023 | I |
| Rn-220/Rn-222 wellhead | 0.34 GM, 0.47 median | Whitehead & Ditchburn 1996 Table 1 | I |
| Peat Cs-137 in fuel, Finland 1994 | 46 Bq/kg dry; ash up to about 14,000 Bq/kg | STUK-A143 | I |
| Wood ash Cs-137 | Finland mean about 1,000; Austria pellets 195 to 867; Belgian plant about 200 Bq/kg | Pepin via 2018 STUK, Grill 2021, Radulovic 2022 | I (secondary) |
| World geothermal Rn-222 default 150 TBq | UNSCEAR own value | S0001 | **D (circular)**: do not use as an independent benchmark. Proposed new B1 test: compare the registry world total with the sum of Larderello (I/P), NZ (I) and Geysers (UNSCEAR-only) by field class |

## 12. Gaps and contradictions

1. Whitehead 1980 internal inconsistency: Robertson & Matthews column (nCi/L CO2 mean 37) versus stack/gas 6.2 to 12 nCi/L. Not resolved; NRL 1978/5 (Robertson & Matthews) would settle it; not found online.
2. No NZ CO2 per GWh for the 1970s; no discharge mass per MWe. NZ estimate hinges on the 29 to 150 t/GWh bracket.
3. Geysers: only UNSCEAR (38.5) plus a "few nCi/L" (Whitehead, Kruger & Umana 1975) versus 17 nCi/L (S0502 T4). Primary Geysers radon papers (Kruger & Umana 1975; Stoker & Kruger; George 1980 LBL-11555 p.3) not obtained.
4. S0502 Table 4 full text not in hand: the 630/620 basis is unconfirmed.
5. S0509 Tab. 3: pCi/L column does not reproduce the Ci/d column.
6. STUK-A143 Table IV Pb-210 mean 34 versus Table VIII 18.2. OCR of a scanned Finnish table; taken from Table VIII.
7. No scale mass, no stove emission measurement, no Cs-137 flue measurement anywhere in this set.
8. Pepin: ash concentration factor 50 is an assumption (IAEA TECDOC-1376), not data.

## 13. Per-paper contribution summary

| PDF | Contribution |
|---|---|
| whitehead1980.pdf (S1402) | NZ Rn-222 per bore and stack gas; Rn-220 not detected; per-litre field comparison; 0.022 condensate fraction; no Ra deposits. Basis of the NZ estimate and the Wairakei/Geysers reconciliation |
| whitehead1996.pdf (S0508) | Full Rn-222/Rn-220 table for 23 samples; ratio statistics |
| HEALTH.IMPACTS.OF.GEOTHERMAL.ENERGY.pdf (S1403, UCRL-85334) | 1979 capacity by country; H2S emission rates; no radon or solids; low value for these questions |
| The-issue-of-Cs-137... (S0513) | Ash concentration factors and Finnish/Austrian/Belgian ash and wood levels; no release fraction |
| CAS_02_..._RADON.pdf (S0509) | Larderello per-plant radon (Tab. 3), 22 wells (Tab. 2), RSE 2013, rock U/Th/K (Tab. 5) |
| 31058925.pdf (S1401) | STUK-A143: peat production Cs-137 and natural nuclides; corrects the S1401 numbers |
