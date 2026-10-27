# Coal round 2: radon emanation, coal radionuclide content, mine water (PROPOSALS ONLY)

Scope: seven staged papers (S0242, S0243, S0244, S0250, S0251, S0252, S0253), read in full from `/mnt/user-data/uploads/radiopassive/import/` (pdftotext plus page images for Barton Table 2 and Figs 2-3). Nothing in `data/`, `docs/`, `pipeline/` or existing research files was edited. Bq/a flows only; no dose quantities are used (dose figures that appear in the papers are ignored).

Conversions used (natural isotopic composition, secular equilibrium): 1 mg/kg U = 12.35 Bq/kg U-238; 1 mg/kg Th = 4.06 Bq/kg Th-232 (as in coal:0021 note); 1 % K = about 310 Bq/kg K-40 (31 Bq/g K); 1 % K2O = 0.830 % K = about 257 Bq/kg. dpm/g / 60 x 1000 = Bq/kg.

---

## 1. Findings per paper

### S0242 Sakoda, Ishimori & Yamaoka (2011), Appl. Radiat. Isot. 69(10): 1422-1435 (READ, 14 pp.)
- Review of Rn-222 emanation fractions from 47 references. Table 3 (p.1426): mean emanation fraction mineral 0.03 (n=75), rock 0.13 (113), soil 0.20 (1025), mill tailing 0.17 (77, mostly U), **fly ash 0.03 (n=46)**. Range for fly ash 0.00-0.35 (p.1435, conclusion). Fly ash and minerals have the narrowest spread.
- Table 3 note (p.1426): moisture differs between samples, and where one sample was measured at several moistures, the **maximum** was used. So 0.03 is a moist-condition (upper) mean, not a dry value.
- Moist samples are "likely higher by a factor of 5 or less" than dry, all materials (p.1426, Fig. 5). Water in pores cuts diffusion (D about 1e-10 m2/s in water versus 1e-5 m2/s in air), so a thick wet sample gives only an "effective" emanation fraction below the "true" one (p.1426).
- Sakoda's ranking of Ra uniformity in grains: mineral ~ fly ash > rock > mill tailing ~ soil (p.1426): fly ash behaves like mineral, not soil.
- Table A5 (p.1434), fly ash: Netherlands 0.005-0.007 (VA85, dry, 87-290 Bq/kg Ra-226); Greece <0.01 (ST04, 10 samples, dry); Greece 0.005-0.032 by size fraction (MA87, Ra-226 200-880 Bq/kg; coarse 25-40 mm 0.005-0.010, fine 0-8.5 mm 0.024-0.032); USA KA85 0.007-0.098 (fine fractions 0.064-0.098, coarse 11-15 mm 0.007-0.045; moisture about 0.1 wt%); USA BA86 (= Barton & Ziemer) 0.001-0.15; USA GU04 0.35 (single, 80 Bq/kg, the top of the range). Ra-226 in these ashes 80-880 Bq/kg.
- Fly ash grain size: coarser fractions have lower emanation (Greek, KA85 data); Sakoda says size effect "could affect a little" below 1 mm (p.1427).
- **Rn-220: nothing.** Thoron appears only as a reference title.
- Contribution: confirms the central 0.03 and gives the first citable range (0.00-0.35) and the coarse-versus-fine pattern needed for bottom ash. No data on sludge, barite or domestic ash.

### S0243 Barton & Ziemer (1986), Health Phys. 50(5): 581-588 (READ, 8 pp.)
- Rn-222 only. Four stoker-fired ash fractions (PSPP1-4: 421-891, 151-420, 76-150, 0-75 um; Ra-226 11.8-16.8 dpm/g = 197-280 Bq/kg, rising as size falls) and four pulverised-coal fly ashes (S, J, W, C; Ra-226 6.44-7.59 dpm/g = 107-127 Bq/kg). Table 1, p.583.
- **Table 2 (p.585), stoker ash emanation coefficient by moisture (wt%)**, PSPP1 (coarsest) / PSPP4 (finest): 0%: 9.6e-4 / 1.21e-3 (PSPP2-3: 1.35e-3, 1.52e-3); 1%: 4.8e-3 / 1.84e-2; 10%: 1.58e-2 / 3.55e-2; 20%: 2.01e-2 / 4.13e-2; 40%: 2.31e-2 / 3.11e-2.
- **Fig. 3 (p.586), pulverised fly ash (graph read, +/- 0.005)**: 0%: about 0.003 (S) to 0.009 (C); 10%: 0.035 (S) to 0.11 (C); peak at 20%: 0.035 (S), 0.088 (J), 0.15 (W, C); 40%: 0.025 (S) to 0.09 (C). Emanation rises with moisture to about 20 wt% then falls (p.587), the fall attributed to the low diffusivity of Rn in interstitial water. Dry-to-peak factor is about 15-20 (stoker) and 5-40 (pulverised), larger than Sakoda's "5 or less".
- Emanation rises as particle size falls (diffusion-length argument, p.587). Depth (2-20 cm) not significant at <=10 % moisture (p.585). Intro (p.582) quotes earlier ash values: Beck et al. <0.01; Styron et al. 0.0022-0.0046 (oven-dried, ambient-equilibrated).
- Authors stress emanation (escape from the grain) is not the same as what is measured in a gas atmosphere (emanation plus diffusion) (p.582).
- Contribution: the best published moisture dependence; it traces the dry end (about 0.001-0.009) and the wet peak (0.04 stoker, 0.15 pulverised). Coarse stoker ash is the nearest analogue to bottom ash/domestic grate ash that exists in this set (caveat: PSPP is a mixed stoker ash, not strictly "bottom ash").

### S0244 Kovler, Perevalov, Steiner & Metzger (2005), J. Environ. Radioact. 82(3): 321-334 (READ, 14 pp.)
- Israeli (Hadera) fly ash powder versus Portland cement, closed-chamber RAD7 tests, 7 d, 21 +/- 2 C. **Fly ash emanation coefficient 0.52 % (0.0052)**; cement 7.65 %; normalised mass exhalation 0.01 versus 0.14 mBq kg-1 s-1 per Bq kg-1 (p.332, p.333 conclusions). Moisture of the exhalation test not stated (samples dried at 105 C for the gamma work, p.330), so treat as dry/air-dry. Authors warn mass exhalation depends on compaction and layer thickness, so it is comparative only (p.333).
- Cites Karamdoust & Durrani (1991): fly ash emanation about 100x lower than soil (p.324). Smith et al. (2001, NRPB) used 5 % (range 1-15 %) for concrete containing coal ash (p.325, Table 1 p.326). Table 1 shows the Rn-220 and Rn-222 results scaling with one emanation coefficient (Rn-220:Rn-222 ratio constant at 0.0435), i.e. NRPB assumed equal Rn-220 and Rn-222 emanation. That is an assumption, not a measurement, and the figures are dose-based so not used.
- Contribution: a measured dry-ash value of 0.0052. This is the closest citable trace for the "untraced" Phase 1 low of 0.005 (with Sakoda VA85 and Barton dry). Concrete values (5 %, 7.65 % cement paste) belong to the Dispersed route only. No Rn-220 measurement.

### S0252 Ketris & Yudovich (2009), Int. J. Coal Geol. 78(2): 135-148 (READ, 14 pp.)
- Table 3 (p.145), coal Clarke values (mg/kg, whole coal; ash basis in brackets). **U: brown 2.9 +/- 0.3 (ash 16), hard 1.9 +/- 0.1 (ash 15), all 2.4 (ash 16).** **Th: brown 3.3 (19), hard 3.2 (23), all 3.3 (21).** Table 4 (p.146): U from 63 brown and 110 hard sets (N=7561 and 19,282 analyses); Th 52 and 97 sets (N=3586 and 18,356).
- Bq/kg: U-238 world 29.6 (brown 35.8, hard 23.5); Th-232 world 13.4 (hard 13.0). On the ash basis U 16 mg/kg = 198 Bq/kg ash, Th 21 mg/kg = 85 Bq/kg ash; the whole-coal/ash ratio implies an ash yield of about 15 % (U 2.4/16, Th 3.3/21) against the 12 % in the activity builder (N099).
- **No K, no Ra, no Pb-210/Po-210.** (Table 1 in the paper is black shales, not coal; do not confuse.)
- Contribution: confirms world U 2.4 and adds Th 3.3 and the brown/hard split (previously unverified in S0252 notes). Directly read now.

### S0253 Dai, Ren, Chou, Finkelman, Seredin & Zhou (2012), Int. J. Coal Geol. 94: 3-21 (READ, 19 pp.)
- Table 1 (p.7), whole-coal content, China: **U 2.43 mg/kg (Dai et al., n=1383); Th 5.84 (Dai et al., n=1052)**. Other estimates in the same table: U Bai 2.33 (n=1123), Tang & Huang 3.0 (n=1383), Ren 2.41 (n=1317); Th Bai 5.88 (1123), Tang & Huang 6.0 (658), Ren 5.81 (1011). (The "n=1,883" quoted in S0220 is not what Table 1 prints for U; Table 1 gives 1383. Flag for the sources note.) USA (Finkelman 1993): U 2.1 arithmetic / 1.1 geometric (n=6923); Th 3.2 / 1.7 (n=6866). World (Ketris & Yudovich): U 2.4, Th 3.3.
- Bq/kg: China U-238 about 30.0 (28.8-37.1 across the four estimates), Th-232 about 23.7 (23.6-24.4). Chinese Th is 1.8x the world Clarke (Dai attributes to ash yield and Zr/Nb-rich tonsteins, p.4); U matches the world.
- **K2O (Table 1, p.7): China 0.19 % (n=1322, Dai et al. 2007b, 2008a and unpublished); USA 0.22 % arithmetic, 0.12 % geometric (n=7830); world not given.** Whole coal (basis not otherwise stated). That is K about 0.158 % = **about 49 Bq/kg K-40 (China)**, US 57 (arithmetic) and 31 (geometric) Bq/kg.
- Hot spots (Table 2 p.9; text p.14): marine-carbonate coals (Guiding, Heshan, Yanshan) U 21-288 mg/kg (about 260-3560 Bq/kg), Ad 17-45 %; Yili lignite U-rich; small reserves, not representative.
- **No Ra-226, no ash yield mean, no Rn.**
- Contribution: China Th and U; the only K-40 evidence in the set; it contradicts "China 104 Bq/kg K-40 (S0006)" (see 3.2).

### S0251 Michalik, Wysocka, Chałupnik, Skubacz, Mielnikow & Trząski (2005), Radioprotection 40 Suppl. 1: S503-S509 (READ, 7 pp.; file p379.pdf)
- Upper Silesian Coal Basin (USCB): up to 65 mines, total outflow 900,000 m3/d (S503). Ra-226 up to 110 kBq/m3 and Ra-228 up to 70 kBq/m3 in raw waters; above 1 kBq/m3 in 43 of 65 mines (S504).
- **Inflow balance (S504):** Ra-226 650 MBq/d (240 GBq/a), Ra-228 about 700 MBq/d (255 GBq/a), "cannot be very precise".
- **Release to surface (S503 abstract, S504-S505):** peak 225 MBq/d Ra-226 and 400 MBq/d Ra-228; "by 1987 up to 400 MBq per day both isotopes" (S505, ambiguous: could mean either isotope or the sum); falling 1987-1995 through treatment of type A waters and reduced dewatering. One colliery's treatment cut release by 150 MBq/d (60 Ra-226 + 90 Ra-228).
- **Retention underground:** abstract "at least 70 %"; body (S505) "nowadays up to 80 % of Ra-226 and 60 % of Ra-228" stay underground as deposits. Both figures are internally consistent with the inflow/outflow numbers: 1 - 225/650 = 0.65 and 1 - 400/700 = 0.43 for the peak-release era; the later and lower releases give higher retention. So the 70 % (S0222) versus 40 % (S0225) conflict recorded for coal:0005/0006 is a time/treatment effect plus different isotopes, not a true contradiction.
- Water types (S504): type A (Ba up to 2 kg/m3, Ra co-precipitates with BaSO4 on contact with sulphate; precipitates 400 kBq/kg underground, 270 kBq/kg on surface); type B (no Ba, Ra stays dissolved and travels up to 100 km).
- Surface settling ponds (S505-S506): 25 ponds with sediments >200 Bq/kg, total capacity 5 Mm3. Pond B-type waters (227 Mm3 over 19 a, inflow Ra-226 3.6 kBq/m3, Ra-228 6.2, total 124 GBq/a): only 2.9 % Ra-226 and 3.3 % Ra-228 retained in the pond (about 7 %/a), outflow 3.5 and 6.0 kBq/m3. Pond A-type (72 Mm3 since 1977, 9.5 GBq/a input): deposition 39 % by the sediment method (810 GBq) versus a much lower figure by the inflow method (350 GBq); the text's "90 %" comparison is garbled (as printed, not resolved). Sediments Ra-226 95-950 Bq/kg, Ra-228 124-1705 Bq/kg (B); up to 55 kBq/kg combined (A, outlet).
- **Radon exhalation (S507-S508), "exhalation coefficient" in mBq m-2 s-1 (a flux):** pond A dried sediment (Ra-226 up to 3.0 kBq/kg) about 12; covered under >10 m waste rock <=2; old waste-rock dump 3.4. Pond B (Ra-226 2.0 and Ra-228 4.0 kBq/kg): 2 to >200, up to 300 on the driest sites, about 100 after rain; wet sediments emit only from the top 0.1-0.2 m. Pond C bank about 20, waste-rock cover <=2. A rough order-of-magnitude inference (not in the paper; semi-infinite slab, bulk density 1500 kg/m3, effective diffusion coefficient 1e-6 m2/s, J = epsilon rho C sqrt(lambda D)) gives an effective exhalation fraction of about 0.002 (pond A, 12 mBq m-2 s-1 at 3 kBq/kg) to about 0.07 (pond B, 300 at 2 kBq/kg). Treat as plausibility only.
- Cites German coal-mine radium waters (Gans 1981; Wiegand 2004, NORM IV, refs [2], [3]) with no numbers.
- Contribution: the inflow/outflow balance, isotope-specific retention, pond retention, and exhalation fluxes. It does not give Bq per tonne of coal or per m3 of coal, only MBq/d (per m3 can be derived: peak Ra-226 225 MBq/d / 900,000 m3/d = 250 Bq/m3; Ra-228 about 440 Bq/m3; inference from two unrelated totals).

### S0250 Wanke, Ritzel, Sachse & Michel (2008), Kerntechnik 73(3): 101-107 (READ, 7 pp.)
- Lower Rhine hard coal (Fossa Eugeniana, Rheinberger Altrhein; pits Rossenray, Friedrich Heinrich, Hoerstgen). A dose-rate and sediment/soil survey and a dose model (ignored here).
- Ra-226 in Altrhein soils 35-1495 Bq/kg (0-20 cm), 183-1576 Bq/kg (0-10 cm); meadow bank 945 Bq/kg; two samples under the Fossa bridge 2500 Bq/kg; contaminated protected area about 8000 m2 (§3.1-3.2, pp.103-104). Pb-210/Ra-226 = 0.4-0.5, implying deposit ages 10-45 a; Ra-228 and Th-228 correlate strongly with Ra-226 (ratios in the cited LINEG report only). Mechanism stated as BaSO4/RaSO4 co-precipitation when sulphate and Ba-Ra-chloride waters mix (p.101).
- **No discharge rate (no Bq/a, MBq/d, m3 or coal tonnage).** Inference only: 945 Bq/kg x 0.2 m x 8000 m2 x an assumed 1300 kg/m3 is about 2 GBq of Ra-226 in the main patch, deposited over 10-45 a, so at most about 0.05-0.2 GBq/a, one to two orders of magnitude below the Polish release (77 MBq/d = 28 GBq/a in 2006). That is a downstream-sink observation, not a source term.
- Contribution: confirms the German phenomenon and its mechanism only; **cannot support a DEU per-tonne factor.**

---

## 2. Answers to the three questions

### Q1. Emanation coefficients (Rn-222 and Rn-220)

Evidence base for Rn-222, all in the set: Sakoda Table 3 and A5, Barton Table 2/Fig. 3, Kovler p.332; external supplement: Idaho National Engineering Lab (INEL-96/00005, OSTI 659017/205694): 20 NORM barite pipe-scale samples, emanation 0.020-0.063 (abstract only read; new ID S0991).

Caveats the executor must carry:
1. Emanation coefficient (fraction of Rn atoms leaving the grain) is not the effective exhalation fraction (fraction reaching the atmosphere). Moisture raises the former by up to 5x (Sakoda) or 15-40x (Barton, dry to 20 wt%) and lowers the latter once pores are saturated: Barton sees a decline above 20 wt%, Sakoda notes the 10^5 difference in diffusivity between air and water (p.1426). So an ash pond under water has near-zero effective release; the 0.03 mean applies to damp, drained ash and is an upper-side central for dry beaches or landfill. The engine's use of emanation as an effective fraction is therefore an upper bound for Rn-222, and a much stronger one for Rn-220 (below).
2. Sakoda's means use the maximum over moisture contents (Table 3 note), so they sit toward the wet end.
3. Michalik's measured fluxes show 2 to 300 mBq m-2 s-1 depending on wet/dry/cover for the same sediment, so the real range from one residue is 2 orders of magnitude.

Rn-222 proposals (emanation basis):

| residue type | low | central | high | evidence |
|---|---|---|---|---|
| coal_fly_ash | 0.005 | 0.03 | 0.15 | Low = Kovler 0.0052, Sakoda A5 VA85 0.005-0.007, Barton dry pulverised about 0.003-0.009. Central = Sakoda mean 0.03 (n=46). High: Barton peak at 20 wt% 0.15 (Fig. 3), Sakoda range top 0.35 (single sample GU04) not used |
| coal_bottom_ash | 0.001 | 0.02 | 0.05 | Barton coarse stoker ash 9.6e-4 dry, 0.016-0.020 at 10-20 wt%, max 0.041 (Table 2); Sakoda A5 coarse fractions 0.005-0.045; coarse about 0.3-0.7x fine |
| coal_domestic_ash | 0.001 | 0.02 | 0.05 | Analogue: grate/stoker ash = bottom ash. No domestic-ash measurement exists. The 0.2 default (0.05-0.35) is soil-like; Sakoda ranks fly/bottom ash with minerals (0.03), not soils (0.20), so 0.2 is not supported for coal ashes |
| coal_mine_water_sludge | 0.02 | 0.07 | 0.25 | Type A (BaSO4-RaSO4): INEL barite scale 0.020-0.063, Sakoda mineral 0.03; type B (Ra adsorbed on sediment, soil-like): Sakoda soil 0.20. Central about the geometric mean of 0.04 and 0.2 (matches the seepage rule for the same residue, 50:50 sludge mix unknown). Michalik's flux-based effective fraction 0.002-0.07 is consistent |

Rn-220 (thoron): **no paper in this set measures it**. Everything below is inference; all rows low confidence.
- Only anchors found: IAEA TRS 474 Table 3 (S0203): minerals 0.01, rocks 0.11, soils 0.14, against Sakoda's Rn-222 0.03/0.13/0.20, i.e. Rn-220/Rn-222 about 0.3 (minerals), 0.85 (rocks), 0.7 (soils); NRPB assumed equality (via Kovler Table 1); Domingos et al. 2021 (granite, abstract) Rn-222 emanation on average higher than Rn-220; Li, Lu & Zhang 2016 (Baotou fly ash, abstract, new S0992) report Rn-220 surface exhalation 15.6-113 mBq m-2 s-1, "notably higher" than Rn-222, which is the expected surface-flux effect of the short half-life, not a higher emanation coefficient.
- Because fly/bottom ash behave as mineral-like grains (Sakoda), I take Rn-220 emanation at 0.3-0.7x the Rn-222 value.

| residue type | Rn-220 low | central | high |
|---|---|---|---|
| coal_fly_ash | 0.002 | 0.01 | 0.10 |
| coal_bottom_ash | 0.001 | 0.01 | 0.04 |
| coal_domestic_ash | 0.001 | 0.01 | 0.04 |
| coal_mine_water_sludge | 0.01 | 0.05 | 0.20 |

Strong caveat on Rn-220: it decays in 55.6 s, so its diffusion length in a bed is about 1 cm (dry, D 1e-6 m2/s) against about 0.7 m for Rn-222. For a thick impounded deposit (H about 1-10 m) the fraction of generated Rn-220 that reaches air is roughly epsilon x L/H, i.e. about 1e-3 to 1e-2 of epsilon. If the engine treats epsilon as an effective share of the inventory, Rn-220 values for impoundments should be the table above times about 0.01 (central), not the table itself. The tables above are emanation, appropriate to airborne/thin-layer cases (stack particles, dust, ash on surface). Decide which meaning the engine uses before adopting any epsilon_rn220; either way this unblocks the all-or-none rule with a documented basis. The same L/H discount applies, less severely, to Rn-222 (L about 0.7 m, ponded ash far less).

### Q2. Coal U, Th, K (Ra) versus coal:0029-0039 and the ash rows

Whole-coal comparison (Bq/kg):

| nuclide | factor range now (low / central / high) | Ketris world (all; brown; hard) | Dai China | US (Finkelman via Dai) | reading |
|---|---|---|---|---|---|
| U-238 (U-234, Th-230 follow) | 7 / 20 / 36 | 29.6; 35.8; 23.5 | 30.0 (28.8-37.1) | 25.9 arith; 13.6 geom | Centre is about 30 % below world, China and US. Production mix (China about half) gives about 28. High 36 matches brown coal (35.8) and Tang & Huang (37). Low 7 (UK) fine as a country low |
| Th-232 (Ra-228, Th-228) | 4.1 / 20 / 30 | 13.4; 13.4; 13.0 | 23.7 (23.6-24.4) | 13.0 arith; 6.9 geom | Centre 20 sits between China (23.7) and the rest (13); production-weighted about 18.5. No change needed |
| K-40 | 50 / 50 / 144 | no data | 49 (K2O 0.19 %, n=1322) | 57 arith; 31 geom (K2O 0.22 %, 0.12 %; n=7830) | China is 49, not 104. See 3.2 |
| Ra-226 | 8.9 / 20 / 59 | no data | no data | no data | Only equilibrium with U; Barton ash Ra-226 107-127 (pulverised) and 197-280 (stoker) Bq/kg ash; Sakoda A5 80-880 Bq/kg ash |

Ash-basis check: coal factors divide by 0.12. Ketris ash-basis Clarke for U (16 mg/kg ash = 198 Bq/kg ash) is below the 233 Bq/kg ash a coal centre of 28 would give, because Ketris implies a 15 % ash yield; Th 21 mg/kg ash = 85 Bq/kg ash versus 167 now (and about 150 at 18 Bq/kg coal): the ash-basis Clarkes indicate ash Th about half of the current ash central if the actual ash yield is 15 %. Yield (N099) matters more than the nuclide factor here; the executor should check the builder yield against Ketris's implied 15 %.

### Q3. Mine water

Poland (Michalik, S0251). Released to rivers: peak 225 MBq/d Ra-226 and 400 MBq/d Ra-228 (S503, S505), 400 MBq/d in 1987 (ambiguous in this paper). Inflow 650 and 700 MBq/d. Underground retention up to 80 % (Ra-226) and 60 % (Ra-228) (S505; abstract: at least 70 %). Surface pond retention 2.9-3.3 % (B), about 39 % (A). Per m3: about 250 Bq/m3 Ra-226 and 440 Bq/m3 Ra-228 in average discharge (inference from 900,000 m3/d total). Per tonne of coal: not given anywhere in this set; derivation is from S0222 flow divided by S0804 production (existing method).

Support for coal:0003-0006:
- coal:0003/0004 (Bq/t): Michalik confirms the order of magnitude of the release (225/400 MBq/d, consistent with the 219/380 of S0222 in 1995), so the rows are supported. One risk: the 1987 anchor (400 MBq/d, coal:0003 high 548 Bq/t) is attributed by S0222 to Ra-226, but Michalik's text can be read as "both isotopes" (sum) in 1987. If that were the sum, 1987 Ra-226 would be roughly 150 MBq/d and the high anchor would fall by a factor of about 2-3. Recheck S0222 for the 1987 row before keeping 548.
- coal:0005/0006: the inflow balance gives retention r = 1 - release/inflow: Ra-226 0.65 (peak, 225/650) to 0.88 (2006, 77/650); Ra-228 0.43 (peak, 400/700) to 0.76 (2006, 170/700). Michalik's "nowadays 80 %/60 %" agrees. Ra-228 retention is systematically lower than Ra-226, so a single value for both rows is not supported.
- **Formulation warning:** the engine's retained = released x r/(1-r) amplifies strongly (r 0.4 -> 0.67; 0.55 -> 1.22; 0.7 -> 2.3; 0.88 -> 7.3). Using inflow minus release directly (650 minus 77 = 573 MBq/d in 2006, i.e. 209 GBq/a) is more stable than any r, and the formula with r=0.55 would give only 94 MBq/d (a factor of 6 low). Suggest the stream spec consider a direct "inflow retained" form for POL, or a date-dependent r.

Germany (Wanke, S0250): sediments and soil concentrations only; no discharge, no m3, no coal tonnes. **There is no basis for a DEU Bq/t factor in these papers.** Leads (not read): Gans et al. (1981), Wiegand (2004, NORM IV) and Schmid & Wiegand (Górnictwo i Środowisko abstract p.86: Ruhr sediments up to 750x Ra-226 enrichment, no numbers), and Gellermann et al. (2006) LINEG final report (full source of Wanke's data). If Steve insists on a German row before those are obtained, the only defensible route is a Polish transfer with a wide band and basis=assumed, and Ra-228 flagged as unmeasured; I do not recommend it.

---

## 3. Proposed changes (old to new) — PROPOSALS, none applied

### 3.1 data/reference/residue_types.csv

| id | field | old | new | justification | confidence |
|---|---|---|---|---|---|
| coal_fly_ash | eps_rn222 low | 0.005 (untraced) | 0.005 (keep) | Now traced: Kovler p.332 0.0052; Sakoda A5 VA85 0.005-0.007; Barton dry pulverised about 0.003-0.009 (Fig. 3) | medium |
| coal_fly_ash | eps_rn222 central | 0.03 | 0.03 (keep) | Sakoda Table 3, n=46 (max-moisture mean; effective for ponded ash is lower) | medium |
| coal_fly_ash | eps_rn222 high | 0.13 | 0.15 | Barton Fig. 3 peak (20 wt%, units W, C); Sakoda range top 0.35 is a single sample, not adopted | low-medium |
| coal_bottom_ash | eps_rn222 low/central/high | 0.0025 / 0.0225 / 0.13 | 0.001 / 0.02 / 0.05 | Coarse stoker ash Barton Table 2 (9.6e-4 dry; 0.016-0.020 at 10-20 %; max 0.041); Sakoda A5 coarse fractions. Replaces the "0.5/0.75/1.0 x fly ash" Phase 1 rule | low-medium |
| coal_mine_water_sludge | eps_rn222 (empty; default 0.2, 0.05-0.35) | 0.02 / 0.07 / 0.25 | Barite scale 0.020-0.063 (INEL, S0991, abstract); Sakoda mineral 0.03, soil 0.20 for type B; geometric blend. Default 0.2 is the soil value | low |
| coal_domestic_ash | eps_rn222 (empty; default 0.2) | 0.001 / 0.02 / 0.05 | Analogue grate ash; Sakoda puts ash with minerals, not soils | low |
| coal_fly_ash | eps_rn220 (BLOCKER) | empty | 0.002 / 0.01 / 0.10 | Inference: 0.3-0.7x Rn-222 using TRS 474 Table 3 versus Sakoda Table 3; emanation basis; apply about x0.01 if epsilon must be effective for thick deposits | low |
| coal_bottom_ash | eps_rn220 | empty | 0.001 / 0.01 / 0.04 | As above | low |
| coal_domestic_ash | eps_rn220 | empty | 0.001 / 0.01 / 0.04 | As above | low |
| coal_mine_water_sludge | eps_rn220 | empty | 0.01 / 0.05 / 0.20 | As above | low |

### 3.2 data/factors/coal.csv

| id | field | old | new | justification | confidence |
|---|---|---|---|---|---|
| coal:0027, coal:0028 (K-40 ash) | low | 416,667 (= centre) | 250,000 Bq/t ash | K-40 low from 31 Bq/kg coal (US geometric mean K2O 0.12 %, Dai Table 1, p.7) / 0.12 | medium |
| coal:0039 (K-40 non-power coal) | low | 50,000 | 31,000 Bq/t | Same | medium |
| coal:0027/0028/0039 | note | "China 104 (S0006)" says centre probably an underestimate | State that Dai 2012 gives China 0.19 % K2O = 49 Bq/kg (n=1322), US 57 arithmetic; centre 50 is confirmed, the 104 is not supported (re-read S0006 for what 104 was) | Dai Table 1 p.7 | medium |
| coal:0029, 0030, 0031 (U-238, U-234, Th-230 coal) | central | 20,000 | 28,000 Bq/t | Ketris world 29.6 (p.145), Dai China 30.0 (p.7), US 25.9; production-weighted about 28. Keep low 7,000, high 36,000 | medium |
| coal:0007-0012 (U-238, U-234, Th-230 ash) | central | 166,667 | 233,333 Bq/t ash | Same /0.12; check against builder yield (Ketris implies 15 %, 198 Bq/kg ash) | medium-low |
| coal:0032 (Ra-226 coal), coal:0013/0014 (ash) | central | 20,000 / 166,667 | 28,000 / 233,333 | Equilibrium with U-238 (existing rule; Barton intro p.581 cites Casella 17 western US coals); no Ra-226 coal data in these papers | low |
| coal:0036-0038, 0021-0026 (Th-232 chain) | central | 20,000 / 166,667 | no change (optional 18,000) | China 23.7, rest about 13; weighted about 18.5 | medium |
| coal:0005 (Ra-226 retained) | low / central / high | 0.4 / 0.55 / 0.7 | 0.4 / 0.55 / 0.88 | Michalik S505 "up to 80 %"; 2006 release 77 vs inflow 650 gives 0.88; peak 225/650 gives 0.65 | medium |
| coal:0006 (Ra-228 retained) | low / central / high | 0.4 / 0.55 / 0.7 | 0.43 / 0.50 / 0.76 | Inflow 700: peak 400 out gives 0.43; 2006 170 out gives 0.76; Michalik S505 60 %. Ra-228 is lower than Ra-226 | medium-low |
| coal:0003 | high | 548.8 Bq/t (1987, 400 MBq/d) | keep, but verify | Michalik S505 "up to 400 MBq/d both isotopes" for 1987 is ambiguous; if a sum, high falls about 2-3x. Check S0222 | flag |
| coal:0003-0004 | note | none | Add Michalik S503-S505 inflow 650/700 MBq/d (retained = inflow - release is the stable anchor) | S0251 | medium |
| new DEU factor | none | none | **No row proposed** | Wanke gives no discharge; see Q3 | high (that nothing usable exists) |

---

## 4. Source strength, gaps and contradictions

Strength: Sakoda (review, peer-reviewed, 2011) and Ketris & Yudovich (2009), Dai (2012) are strong secondary compilations; Barton (1986) and Kovler (2005) are primary measurements of one-to-few ashes (US 1980s, Israel); Michalik (2005) is a conference-quality paper from the Central Mining Institute with approximate balances ("cannot be very precise"); Wanke (2008) is a primary sediment survey with no flux.

Gaps (not closable from the set):
- Rn-220 emanation for any coal residue (blocker): none of the seven papers; the proposals are analogies. Targets: Li, Lu & Zhang 2016 full text (NT&RP 31(3): 282-290, doi in S0992 row) for fly ash Rn-220 and perhaps coefficients; TRS 474 section for thoron.
- Sludge/barite from coal mines: no direct emanation; barite scale from oil/gas (INEL, abstract only) is the proxy. Full text and sample data needed.
- Ra-226 and K-40 whole-coal means: absent in Ketris; Ra-226 absent in Dai.
- German discharge: Gans 1981; Wiegand 2004; Gellermann et al. 2006.
- Domestic ash emanation: none.

Contradictions and flags:
1. "China K-40 104 Bq/kg (S0006)" versus Dai 49. Dai is the larger, newer dataset (n=1322).
2. Michalik abstract (at least 70 % retained) versus body (80 % Ra-226, 60 % Ra-228) versus S0225 (about 40 %): resolved as isotope and date effects.
3. Michalik 1987 "400 MBq/d both isotopes" versus S0222 400 MBq/d Ra-226 alone.
4. Michalik pond A deposition 39 % versus "90 %" statement is garbled in the paper; the 39 % comes with two inconsistent methods (350 versus 810 GBq).
5. Moisture factor: Sakoda "5 or less" versus Barton 15-40; probably because Barton went to 0 wt% (truly dry).
6. S0220 gives n=1,883 for Chinese U; Dai Table 1 prints n=1383 (Dai column) and 1123/1383/1317 for the three earlier sets. Probably a transcription difference; correct the S0220 note if desired.
7. Ketris implied ash yield about 15 % versus 12 % in the builder (N099): affects all ash-basis rows.
