# Events catalogue: notes (Task 1.8)

Files: `data/events.csv` (21 events, E001-E021), `research/events/sources_task18.csv` (30 new sources, S0700-S0729), this file. Validation on a scratch root (data, schema and pipeline copied; new sources merged; events.csv copied in): `python3 -m pipeline.validate --root <scratch>` returns **OK: no issues** (E01, E02, E03 clean). `data/sources.csv` was not edited.

Generator script (throwaway): `/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/t18/build.py`.

## 1. Conventions used

- **What `activity_*_bq` means.** Head activity (no D24 multipliers) moved by the event **into `liberated` or `dispersed`** (the quantity the METHODS 9.1 threshold counts). For accidents this excludes the part that stays in `sealed_damaged_core`; Phase 2 derives that from the in-core inventory. Dose is not used anywhere (D1).
- **Date convention.** All dates are day-exact as sourced except where noted in `notes`. `date_end` is the end of the main release for accidents (a convention for Fukushima) and empty for instantaneous failures.
- **Low/central/high.** Taken from published alternatives where they exist (Chernobyl, Fukushima, TMI). Otherwise they are judgement spreads, stated in each row's `notes`: ash and refuse coefficients x0.5 / x2; mass from density and solids-fraction ranges; Tokaimura /10 and x10. These are not statistical intervals.
- **Mass events: basis of `mass_t` (each row's notes start with a MASS BASIS statement).** Activity is always computed on **solids**.
  - **Gross mass** (solids plus entrained water or liquor): E001, E003, E005, E007, E009, E010, E012, E015, E016, E019. The slurry fraction that is solids (0.12-0.35, judgement) is applied before the coefficient.
  - **Dry solids**: E006, E014, E017, E018, E020, E021. Tailings volume x a settled dry-bulk density (Cu-Au 1.5, range 1.2-1.8; Fe 1.8, range 1.5-2.1 t/m3), so mass already represents solids; free water (e.g. Mount Polley's 17 million m3) is not counted. E014 is a reported tailings mass (20.6 Mt).
  - **Ash at bulk density**: E011, 1.36 t/m3 as removed (some moisture), all treated as solids.
  - The two bases are not identical in kind, and the mass criterion is applied to the stated mass_t. See "Pending decision (Steve)".
  - Basis for all activities is `modelled`.
- **Coefficients for mass events** (Bq per tonne of solids, head activity of U-238, Ra-226, Th-232 and Ra-228 where relevant; K-40 and Pb-210/Po-210 excluded):

| Residue | Low | Central | High | Basis |
|---|---|---|---|---|
| Coal ash | 2.8e5 | 5.6e5 | 1.1e6 | Ra-226 163 and Ra-228 115 Bq/kg (TVA/TDEC means 4.4 and 3.1 pCi/g, Ruhl 2009, S0702); U-238 and Th-232 assumed equal to Ra-226 and Ra-228; x0.5 / x2 |
| Coal washery refuse | 1.1e5 | 2.3e5 | 4.6e5 | Ra-226 53 and Th-232 61 Bq/kg (China gangue, IAEA TRS 419 Table VIII, S0202; also S0225); U-238, Ra-228 assumed equal to neighbours; x0.5 / x2 |
| Metal-mine tailings (Cu, Fe, Zn-Pb) | 8.3e4 | 2.8e5 | 9.3e5 | Low: 30+30+23 Bq/kg (US copper ore, UNSCEAR 1988 Table 46, S0008). High: 370+190+370 Bq/kg ("large-volume metal wastes", TRS 419 Table XX, S0202). Central: geometric mean. Same set as Task 1.5 copper rows |
| Bauxite residue (red mud) | 3.0e5 | 9.8e5 | 2.2e6 | Th-232 100-550 (400), Ra-226 100-1000 (300), U-238 100-600 (280) Bq/kg (S0409 Table 2, S0008, S0202) |

  The metal-tailings set is generic and is probably **high for iron-ore tailings** (itabirite has very low U and Th). The low bound is the better guess for E018 and E021.
- **Stream for commodity-chain events.** All are filed `wind_solar` / `commodity_supply`; the commodity is stated in `notes`. The share that belongs to wind and solar (and to the construction stages of other streams) is an allocation step in the master transfer rows (METHODS 10), not an events.csv attribute.

## 2. Events table (central values)

| ID | Event | Date | Stream / stage | Tiers | Central | Inclusion |
|---|---|---|---|---|---|---|
| E001 | Buffalo Creek coal-waste slurry dam | 1972-02-26 | coal / coal_mining | impounded > liberated | 5.8e5 t; 3.3e10 Bq | mass |
| E002 | Three Mile Island 2 | 1979-03-28 | nuclear / accident | in_core > liberated; damaged_core | 9.3e16 Bq | activity |
| E003 | Church Rock mill spill | 1979-07-16 | nuclear / u_milling | impounded > liberated; dispersed | 3.6e5 t; 1.7e12 Bq (gross alpha) | mass |
| E004 | Chernobyl Unit 4 | 1986-04-26 | nuclear / accident | in_core > liberated; damaged_core | 1.21e19 Bq | activity |
| E005 | Maritsa Iztok-1 ash dam (BGR) | 1992-03-01 | coal / combustion_power | impounded > liberated; dispersed | 6.0e5 t; 1.2e11 Bq | mass |
| E006 | Marcopper (Cu) | 1996-03-24 | wind_solar / commodity_supply | impounded > liberated; dispersed | 2.4e6 t; 6.7e11 Bq | mass |
| E007 | Los Frailes / Aznalcollar (Zn-Pb-Cu-Ag) | 1998-04-25 | wind_solar / commodity_supply | same | 5.4e6 t; 5.3e11 Bq | mass |
| E008 | Tokaimura JCO | 1999-09-30 | nuclear / conv_enrich_fab | fuel_cycle > liberated | 1.6e13 Bq (judgement; high 1.6e14) | activity (uncertain) |
| E009 | Martin County coal slurry | 2000-10-11 | coal / coal_mining | impounded > liberated | 1.3e6 t; 7.4e10 Bq | mass |
| E010 | Partizansk ash dump (RUS) | 2004-05-22 | coal / combustion_power | impounded > liberated; dispersed | 1.9e5 t gross; 3.7e10 Bq | mass (marginal) |
| E011 | TVA Kingston ash | 2008-12-22 | coal / combustion_power | impounded > liberated; dispersed | 5.6e6 t; 3.1e12 Bq | mass |
| E012 | Ajka / Kolontar red mud (Al) | 2010-10-04 | wind_solar / commodity_supply | same | 8.8e5 t; 2.6e11 Bq | mass |
| E013 | Fukushima Daiichi 1-3 | 2011-03-11 | nuclear / accident | in_core > liberated; damaged_core | 7.49e18 Bq | activity |
| E014 | Padcal (Cu-Au) | 2012-08-01 | wind_solar / commodity_supply | same | 2.1e7 t; 5.7e12 Bq | mass |
| E015 | Obed Mountain wash plant (coal) | 2013-10-31 | coal / coal_mining | impounded > liberated | 7.6e5 t gross (9e4 t solids); 2.0e10 Bq | mass (marginal) |
| E016 | Dan River ash pond | 2014-02-02 | coal / combustion_power | impounded > liberated; dispersed | 1.4e5 t; 2.0e10 Bq | mass (marginal) |
| E017 | Mount Polley (Cu-Au) | 2014-08-04 | wind_solar / commodity_supply | same | 1.2e7 t; 3.3e12 Bq | mass |
| E018 | Fundao / Samarco (Fe) | 2015-11-05 | wind_solar / commodity_supply | same | 5.8e7 t; 1.6e13 Bq | mass |
| E019 | Dahegou red mud (Al) | 2016-08-08 | wind_solar / commodity_supply | same | 2.5e6 t; 7.4e11 Bq | mass |
| E020 | Cadia (Cu-Au) | 2018-03-09 | wind_solar / commodity_supply | same | 2.0e6 t; 5.6e11 Bq | mass |
| E021 | Brumadinho / Corrego do Feijao (Fe) | 2019-01-25 | wind_solar / commodity_supply | same | 1.7e7 t; 4.9e12 Bq | mass |

Low and high bounds are in the CSV. Six mass events also reach 1 TBq of central head activity (E003 if its 46 Ci is right, E011, E014, E017, E018, E021); the rest pass on mass alone (the threshold is either/or).

## 3. Derivations and expected master-row group breakdowns

### Nuclear accidents (activity criterion)

**E004 Chernobyl** (S0105 UNSCEAR 2008 Annex D Table 1; S0104; S0710; S0711). Central is the sum of the Table 1 nuclides (PBq): Xe-133 6,500; I-131 ~1,760; Te-132 ~1,150; I-133 910; Te-129m 240; Ba-140 240; Np-239 400; Sr-89 ~115; Cs-137 ~85; Zr-95 84; Ce-141 84; Cs-134 ~47; Mo-99 >72; Ru-103 >168; Ru-106 >73; Ce-144 ~50; Cs-136 36; Kr-85 33; Sr-90 ~10; Pu-241 ~2.6; Cm-242 ~0.4; Pu-238/239/240/242 about 0.05 in total. Sum 1.206e19 Bq. Low 1.09e19 (NEA table sum, S0710). High 1.4e19: the UN Chernobyl Forum quotes about 14 EBq including all noble gases (S0728, via a GreenFacts digest; the Forum report itself is Pub1239_web.pdf). For reference, substituting S0104's higher refractory values into the central gives 1.29e19. IAEA (S0711) says about 12 EBq.
- Master groups: Xe133, Kr85, I131, I133, Te132+, Cs134, Cs137+, Sr90+, Ru103+, Ru106+, Ba140, Zr95, Mo99+, Ce144+, Np239, Pu238-242, Cm242 are in `groups.csv`. **Missing groups** that carry non-trivial activity: Te-129m (240 PBq), Sr-89 (115), Cs-136 (36), Ce-141 (84). Add them (Task 0.3 addendum) or the transfer rows will not sum to the event total.
- Route `air_accident_release`. `transfer_out` from `sealed_in_core`; `transfer_in` to `liberated`. The `sealed_damaged_core` share is the unreleased core: use S0104 Table 1 inventory decayed to 1986-05-06 minus the release.
- Country coded `SUN` (valid to 1991). Deposition fell in UKR, BLR, RUS and Europe; master rows may need a different country convention (flag).

**E013 Fukushima Daiichi** (S0106, S0107, S0701). Air (UNSCEAR 2013 Table 2): Xe-133 7,300; I-131 120; I-133 9.6; Te-132 29; Cs-137 8.8; Cs-134 9.0; Cs-136 1.8 PBq. **I-132 (29 PBq) is deliberately left out**: it is the Te-132 daughter and sits inside the `Te132+` group multiplier. Ocean (S0107, midpoints): Cs-137 4.5, I-131 11, H-3 0.5 PBq. Central 7.49e18 Bq. Low 7.3e18 (Xe-133 only). High 1.62e19: Stohl 2012 Xe-133 15.3 EBq and Cs-137 36.6 PBq, I-131 754 PBq (S0107 upper), plus upper ocean values. Note that UNSCEAR 2013 Appendix B Table B4 (a nuclide-by-nuclide list in Bq) was not reached through the fetch tool; the nuclear notes quote I-131 1.24e17 from it, against 1.20e17 in Table 2 used here.
- Master groups: Xe133, I131, I133, Te132+, Cs134, Cs137+ present; **missing**: Cs-136. Kr-85, Sr-89/90, Ba-140 are in Table B4 (not read).
- Routes: `air_accident_release` for the atmosphere; `water_accident_release` for the ocean (Cs-137, I-131, H-3, and Cs-134 not quantified).

**E002 Three Mile Island** (S0108, S0138, S0139). Noble gases (mainly Xe-133) central 2.5 MCi = 9.25e16 Bq; range 1-40 MCi (NRC letter); consultants gave about 10 MCi and one alternative 2.4 MCi. I-131 about 14 Ci (5.2e11 Bq). Master groups: Xe133 (bulk), Kr85, Xe133m, Xe135, I131. The 2.5 MCi central is a **judgement**: it rests on the Rogovin report (S0138), which was not retrieved, while the NRC letter ML19210E952 (S0108) gives about 10 MCi from licensee consultants, 2.4 MCi as an alternative and 1-40 MCi as its range. The unreleased core remains in TMI-2 (later defuelled to INL, a separate spent-fuel matter).

**E008 Tokaimura** (S0708 grey, S0727 IAEA mission, S0726). WNA: about 160 TBq noble gases and 2 TBq gaseous iodine "apparently released", with little escaping the building. The IAEA mission report (S0727, Section 4, p. 23 and Section 9, p. 33) gives no release total, says definitive data were unavailable, and that only trace amounts of noble gases and gaseous iodine escaped the building; it estimates 5e17-5e18 fissions. No JNSC or JAERI release table was found. So 1.62e14 Bq is the **high** case; central 1.62e13 (10 % of WNA) and low 1.62e12 are judgement, not sourced. **Inclusion rests on one grey source and is uncertain**; if the true release is below 1 TBq the event drops out. Filed at `conv_enrich_fab` (a routine-transfer stage) as an **event** transfer `sealed_fuel_cycle` > `liberated` (SCHEMA 3.1); the `accident` stage has no `sealed_fuel_cycle` tier. Groups: Kr/Xe isotopes and I131/I133; split not published.

### Church Rock (E003)

Liquor 94 million US gal = 3.56e5 m3; solids about 1,100 short tons (1.0e3 t). Total 3.57e5 t, so it meets the mass criterion by itself. Activity: a table row in a New Mexico Environment Department slide (S0709) reads "1.5 (1,100 MT tailings) / U 4.5-6.4 mg/l / Ra total 210 pCi/l / 46"; I read the last figure as 46 Ci gross alpha (1.7e12 Bq). Cross-checks: 1.5 t U matches 4.5-6.4 mg/L x 3.56e8 L (1.6-2.3 t); 46 Ci over 3.56e8 L is 1.3e5 pCi/L, matching the 1.28e5 pCi/L river peak in S0109. **Not verified against the original slide.** The 46 Ci is **unverified gross alpha**, mostly Th-230 and progeny, and is **not head activity**. **Inclusion stands on mass**. Low is U-nat only (3.8e10 Bq).
- Expected groups: U238+, U234, Th230 (dominant in the liquor and solids per S0109 sediment data: Th-230 27 pCi/g in Puerco sediments vs 0.75 background), Ra226+, Pb210+. Split is not published; Phase 2 should model from the liquor chemistry or ask NMED.
- Civil: yes (United Nuclear commercial mill; 1979).

### Coal ash and slurry (mass criterion)

- **E011 Kingston.** 5.4 million cy (4.13e6 m3, S0704, S0702). Density 1.36 t/m3 from S0703 (3.5 million cy = 4.0 million short tons shipped; assumes both figures describe the same material). Mass 5.6e6 t (range 4.1e6-6.2e6). Activity 3.1e12 Bq (1.1e12-6.9e12): the only coal event over 1 TBq. Groups: U238+, Ra226+, Th232, Ra228+; Pb210+/Po210 enriched in fly ash (Task 1.3 factors) would raise this. Residue type `coal_fly_ash` (and some bottom ash). Ash went to the Emory/Clinch Rivers (liberated) and about 120 ha of adjacent land (dispersed): split unpublished.
- **E016 Dan River.** Marginal. Ash 39,000 short tons (35,400 t; revised from 82,000 short tons; 30,000-39,000 short tons in S0707; WISE 74,400 t) plus 27 million gal (1.02e5 m3) of pond water = 1.38e5 t. Ash alone is below 1e5 t. It passes only if pond water counts. **Orchestrator decision needed.** Activity counts ash only (2.0e10 Bq).
- **E009 Martin County.** 300 million gal (S0705) = 1.14e6 m3; range 0.95e6 (WISE, 250 million gal) to 1.16e6 (306 million gal). Gross 1.3e6 t at 1.15 t/m3; solids 25 % (judgement) = 3.3e5 t. 7.4e10 Bq. Coal washery slurry, `coal_mining`.
- **E001 Buffalo Creek.** 500,000 m3 (132 million gal), coal-preparation refuse slurry.
- **E005 Maritsa Iztok-1** (lignite ash and cinder, 500,000 m3, WISE only) and **E010 Partizansk** (160,000 m3, WISE only). Both secondary-only; E010 is marginal on mass (gross 1.9e5 t). The generic ash coefficient is a US value and likely understates Bulgarian lignite ash.
- **E015 Obed Mountain.** 670,000 m3 wastewater + 90,000 t sediment (WISE); filed `coal_mining`.
- **Tier note.** `coal_mining` allows only impounded, liberated and memo_earth_moved (vocab.json), so E001, E009 and E015 list `liberated` only. If Phase 2 wants the land-deposited share counted as `dispersed`, `coal_mining` needs `dispersed` added to `stage_tiers`.

### Commodity-chain tailings (stream wind_solar, stage commodity_supply)

All volumes from WISE (S0700) unless noted. Densities and solids fractions are judgement: Cu-Au tailings 1.5 t/m3 (1.2-1.8); iron-ore tailings 1.8 (1.5-2.1); slurries 1.2-1.25; solids fraction 0.3-0.35. Expected master rows: groups U238+, Ra226+, Th232 (and Ra228+/Th228+ for red mud); residue types `metal_tailings` and `red_mud`; `product` = the commodity.

| ID | Commodity (product token) | Notes |
|---|---|---|
| E006 Marcopper 1996 | copper | 1.6e6 m3 from pit storage via drainage tunnel |
| E007 Los Frailes 1998 | zinc, lead, copper, silver | 4-5e6 m3 water plus slurry; commodity split is an allocation issue |
| E012 Ajka 2010 | aluminium | 7e5 m3 red mud; S0409 for concentrations |
| E014 Padcal 2012 | copper (gold) | 20.6 Mt reported as a mass |
| E017 Mount Polley 2014 | copper (gold) | Central 8e6 m3 tailings and other material (BC Government primary, S0721; plus 17e6 m3 water, not counted); WISE 7.3e6 m3 is the low bound. About 1.2e7 t, 3.3e12 Bq |
| E018 Fundao 2015 | iron ore (steel) | 32e6 m3 (BHP, S0723); early estimates over 50e6 |
| E019 Dahegou 2016 | aluminium | 2e6 m3, single secondary source |
| E020 Cadia 2018 | copper (gold) | 1.33e6 m3; mostly retained on site, so the figure is an upper bound |
| E021 Brumadinho 2019 | iron ore (steel) | 9.7e6 m3 (ASDSO, S0722) to 12e6 (WISE) |

Gold-only failures (Merriespruit 1994, Baia Mare 2000) are outside the commodity vocabulary and were not entered (see rejected list).

## 4. Findings against the done condition

| Condition | Result |
|---|---|
| At least 15 events | **Met: 21** |
| At least 4 streams | **Not met: 3 streams** (nuclear 5, coal 7, wind_solar 9). No qualifying event was found for `oil_gas` or `other`. See section 5 |
| Date, location, stream, tiers, low/central/high, at least 1 source | Met for all 21 (coordinates blank where not confidently known) |
| Inclusion threshold stated and met | Met under METHODS 9.1; two marginal on mass (E010, E016) |
| Military excluded (D9) | Met: `military=false` for all; excluded candidates listed in section 5 |

Counts: nuclear E002, E003, E004, E008, E013 = 5; coal E001, E005, E009, E010, E011, E015, E016 = 7; wind_solar E006, E007, E012, E014, E017-E021 = 9; total 21.

## 5. Candidates assessed and not entered

### Oil and gas (confirmed: none qualifies)
- Produced-water spills: the largest found is Blacktail Creek, North Dakota, January 2015, nearly 3 million US gal (S0719; about 11 million L, S0322). At about 137 Bq/L total radium that is about 1.5 GBq and 1.1e4 t, three orders of magnitude below 1 TBq and one below 1e5 t (Task 1.4 arithmetic, S0322). Reaching 1e5 t would need about 26 million US gal of produced water in one event; none found. The Bakken total of about 3,900 spills (2007-14) is chronic, not an event.
- Gas blowout radon: Aliso Canyon 2015 released 97,100 t methane (S0715), about 1.4e8 m3 of gas. At the US wellhead median of about 1,400 Bq/m3 radon (S0317, S0318) that is at most 0.2 TBq, before decay in storage (the gas had been stored for weeks, radon half-life 3.8 d). Rejected by this bounding argument. Larger blowouts (e.g. Soviet 1960s gas fountains) were not pursued: no radon content for the gas, and Urtabulak was ended with a nuclear device.
- Oil sands: Kearl 2023 release about 5,300 m3 (the roughly 670 million L seepage figure is cumulative, not one event); Suncor Fort Hills 2023 about 5,900 m3; no oil-sands tailings-pond breach found. All far below 1e5 t.
- Blacktail Creek 2015: about 1.1e4 t, about 1.5 GBq. Even a 10 kBq/L brine at 1e7 L gives only about 1e11 Bq.
- Deepwater Horizon (2010) is not radiological (oil carries little radium); not an event for this catalogue.
- Net: negative result for `oil_gas` (figures from the independent verification).

### Other (hydro, geothermal, biomass/peat)
No event found. Hydro reservoirs hold no residue; no geothermal or peat event with a radiological signature was found. Forest fires re-releasing Chernobyl Cs-137 move activity within the Liberated tier, not between tiers, and are not energy-sector events (Task 1.6 notes reach the same conclusion).

### Nuclear
| Candidate | Decision | Reason |
|---|---|---|
| Saint-Laurent A1 1969 and A2 1980 (INES 4) | Rejected | No environmental release quantity; 1980 discharges stayed within authorised limits (S0712) |
| Lucens 1969 (INES 4) | Rejected | Most activity retained in the cavern; no release figure (S0712) |
| Windscale 1957, Kyshtym 1957, SL-1 1961, Hanford, Tomsk-7 1993 | Excluded | Military (METHODS 9.2, D9) |
| Mailuu-Suu (Kyrgyzstan) tailings | Excluded | Soviet uranium output 1946-67 (S0720) falls in the pre-1965 zero-civil-share era (D16 rule 2); the page does not state the weapons purpose, so this is an inference. No 1958 failure volume was retrievable; a 1958 failure and the 23 tailings dams (1.9e6 m3) remain a legacy stock, not an event |
| Bellezane (France) | Rejected | No failure event found; concerns long-term mobility of residues (seepage is an engine process) |
| Sequoyah Fuels UF6 1986 | Rejected | Bound: a 48Y cylinder holds at most about 12.5 t UF6 = 8.4 t U; natural U is 25.4 kBq/g, so at most 2.1e11 Bq = 0.2 TBq (my arithmetic; NUREG-1189 not retrieved, S0725 qualitative only) |
| Milan NM 1977 mill pipeline rupture (30,000 m3) | Rejected | Below the mass threshold; activity not found (listed by WISE) |
| Roxby Downs 1994 (up to 5e6 m3 leakage over years) | Rejected | Seepage, an engine process, not a discrete failure |
| Goiania 1987 (Cs-137 source) | Rejected | Not energy-related |
| Leningrad NPP unit 1, 1975 | **Deferred** | Bellona (S0713) cites "varying estimates" of 137,000 to 1.5 million Ci (5e15-5.5e16 Bq) with no source and low evidence. Would pass the threshold if true. Needs a primary or peer-reviewed source before entry |
| Chalk River NRX 1952, NRU 1958 | **Pending Steve's scope decision** | NRX figures now sourced (Cross 1980, S0729; see Pending decision); NRX also made plutonium for the US, so civil status is uncertain (D16). NRU 1958 has no quantity (S0714) |
| Jaslovske Bohunice A1 1977, Buenos Aires 1983 | Not examined | INES 4; no release data located |

### Coal
| Candidate | Decision | Reason |
|---|---|---|
| Hurricane Florence 2018 (Duke, Sutton) | Rejected | More than 2,000 cy (about 1,500 m3) released (S0718), far below 1e5 t |
| Sasan, Singrauli 2020 (India) | **Deferred** | Breach on 10 April 2020 but no volume reported (S0716, S0717); filings in the National Green Tribunal (OA 148/2020) may hold one |
| Mae Moh lignite mine waste dump 2018 (70e6 m3) | Rejected | Overburden dump, not a processing residue (D21: memo series) |
| Aberfan 1966 | Not entered | Colliery spoil tip failure (about 1.1e5 m3); borderline mass and a tip rather than an impoundment; not assessed further |
| Chinese ash-pond failures | Not found | No dated, quantified Chinese ash failure located in this pass |

### Commodity chains
| Candidate | Decision | Reason |
|---|---|---|
| Baia Mare 2000 (gold, 1e5 m3 liquid) | Rejected | Gold is not in the commodity vocabulary; mass marginal |
| Merriespruit 1994 (gold, 6e5 m3) | Rejected | Gold; outside commodity vocabulary |
| Bayan Obo / Baotou tailings dam | Rejected | No dam failure found; seepage from the Baotou tailings dam is an engine process (S0404, S0405 in Task 1.5) |
| Tonglvshan 2017 (Cu, 2e5 m3), Bloom Lake 2011 (Fe, >2e5 m3), Shanxi Daoer 2022 (Al, 2.24e5 m3), Jharsuguda 2017 (Al, 2.5e6 m3, material unclear), Muri 2019, Barcarena 2018 (red mud, volumes not stated) | **Eligible but deferred** | All appear in WISE (S0700) and would pass or probably pass on mass; not entered to keep this pass to the better-documented events. Adding them is routine if Phase 2 wants a fuller list |
| Zijin Ting River 2010, other small Cu spills | Rejected | Below threshold |

## 6. Issues to resolve (for the orchestrator)

1. **Streams.** Only three streams have qualifying events. The condition "at least 4 streams" cannot be met honestly with the current streams: oil_gas has none (confirmed), `other` has none. Options: accept three and record the negative result as the finding for those streams; or re-file the iron-ore events (E018, E021) under a construction stage of another stream, which I did not do because the stream of an event row should match where its master rows will sit.
2. **Dan River (E016) and Partizansk (E010)** pass the 1e5 t mass test only marginally, and Dan River only if pond water counts as NORM-bearing. Keep or drop.
3. **Church Rock activity** rests on a garbled slide column. If 46 Ci is not gross alpha, the central activity falls to about the U and Ra figures (about 5e10 Bq); the mass criterion still holds.
4. **Missing groups** (Sr-89, Te-129m, Cs-136, Ce-141): needed for Chernobyl and Fukushima rows (see section 3).
5. **Stage and tier fit.** `coal_mining` lacks `dispersed`; `accident` lacks `sealed_fuel_cycle` (hence Tokaimura at `conv_enrich_fab`).
6. **Country for Chernobyl.** `SUN` used because 1986 is within its validity; `UKR` is the alternative.
7. **Generic tailings coefficient** likely overstates iron-ore tailings (E018, E021).
8. **Single-source volumes** (WISE) for E001, E005, E007, E010, E014, E015, E019, E020. Primary regulator or company reports were not obtained; the verifier should treat these as lower confidence.

9. **Verifier opinions on structure.** Adding Sr-89, Te-129m, Cs-136 and Ce-141 is low priority (about 4 % of Chernobyl's total, no effect on end-year stocks) but needed for ledger sums. Adding `dispersed` to `coal_mining` is recommended. Tokaimura at `conv_enrich_fab` is acceptable provided the exclude-accidents run keys on `is_accident` (not on stage).

## Pending decision (Steve)

- **E010 Partizansk, E015 Obed Mountain and E016 Dan River** pass the 1e5 t test only if METHODS 9.1's mass criterion means **gross released mass including entrained water**. On solids alone they fall below it: E015 about 9e4 t sediment, E016 about 3.5e4 t ash (3.5e4 to 7.4e4 t across estimates), E010 about 6.7e4 t at 35 % solids. METHODS 9.2 names Dan River explicitly as an included event. All three are kept in events.csv for now.
- The slurry events (gross basis) and tailings events (dry basis) are measured differently; a consistent rule would change which events qualify.
- **Chalk River NRX, 1952** (candidate, not in events.csv): a civil research reactor that also supplied plutonium to the US, so the D16 civil/military call is Steve's. Cross (1980, AECL, S0729): 8,000-30,000 Ci of fresh fission products from the stack (3.0e14-1.1e15 Bq) and about 1 million gal carrying about 10,000 Ci of long-lived fission products to ground disposal. The stack release passes the 1 TBq threshold. If admitted: stream nuclear, stage `accident`, from `sealed_in_core`, to `liberated` and `sealed_damaged_core`, date 1952-12-12 (not checked in the source read).
- Tokaimura (E008) inclusion rests on one grey source (see section 3).

## 7. Inaccessible or unverified URLs (for Steve to try)

- Rogovin report (TMI offsite release, S0138): https://tmi2kml.inl.gov/Documents/Common/NUREGCR-1250V1,%20TMI,%20A%20Report%20To%20The%20Commissioners%20And%20To%20The%20Public%20(Rogovin%20Report)%20(1980-01).pdf
- NMEID 1983 Church Rock report (S0110): cited via https://pmc.ncbi.nlm.nih.gov/articles/PMC3915248
- NMED slide deck with the Church Rock table (verify the 46 Ci column): https://animas.nmwrri.nmsu.edu/wp-content/uploads/2017Presentations/D1_08_Dennis_McQuillan.pdf
- UNSCEAR 2013 Vol. I Appendix B Table B4 (Fukushima release by nuclide): https://www.unscear.org/unscear/uploads/documents/unscear-reports/UNSCEAR_2013_Report_Vol.I.pdf (the fetch stopped before the appendix)
- UNSCEAR 2000 Annex J (fetch failed this session): https://www.unscear.org/unscear/uploads/documents/publications/UNSCEAR_2000_Annex-J.pdf
- NRC Church Rock document: https://www.nrc.gov/docs/ML2003/ML20039F060.pdf (fetch failed)
- NUREG-1189 Vol. 1 (Sequoyah Fuels release quantities): not located. PMC article that returned a reCAPTCHA: https://pmc.ncbi.nlm.nih.gov/articles/PMC1963288
- FHWA fly-ash density page (fetch failed): https://www.fhwa.dot.gov/pavement/recycling/faf/ch02.cfm
- Japan Nuclear Safety Commission Tokaimura investigation report (not found); WNA page used instead: https://www.world-nuclear.org/information-library/safety-and-security/safety-of-plants/tokaimura-criticality-accident
- Indian NGT Sasan filings: https://www.greentribunal.gov.in/sites/default/files/news_updates/Affidavit%20bY%20Sasan%20Power%20Limited%20-%20Respondent%20No.%201%20%26%202%20IN%20OA%20NO.%20148%20of%202020%20EARLIER%20OA%20NO.%2031%20of%202020%20CZ%20(HIRALAL%20BAIS%20VS%20RELIANCE%20SASAN%20POWER%20P.%20Ltd.%20%26%20ORS.).pdf (not read)

All fetches except those above succeeded, but many were read through a summarising tool; page numbers were not available. Figures from those pages should be re-read on the original before the verifier's spot checks.
