# Task 1.6: Other energy (geothermal, biomass and peat, hydro): notes

Files: `bibliography.md`, `availability.csv` (133 rows), `sources_task16.csv` (S0500 to S0526, 27 sources). UNSCEAR background is in `research/unscear_notes.md` (S0001, S0008, S0010).

## 1. Method and limits

- Searched the web, then read the papers and reports through a summarising fetch tool. Numbers marked "read" were taken from that summary. Spot-check them against the originals before they enter the factor registry.
- Direct downloads from `pangea.stanford.edu` failed on a TLS certificate chain, and the fetch tool hit a usage limit part-way through. That is why several entries are abstract-only. Certificate verification was not disabled.
- Derived numbers below are my arithmetic on sourced values and are labelled "derived".
- Dose figures are not used.

## 2. Geothermal

### 2.1 Radon-222 in non-condensable gas (stage `geothermal`, tier `liberated`, route `air_vented_gas`)

| Item | Value | Source |
|---|---|---|
| UNSCEAR adopted | 150 TBq/(GW a) (1988, 1993, 2016); 400 in 1982 | S0001, S0008, S0010 |
| Larderello | 260 TBq/(GW a) (300 GBq/d at about 420 MW; UNSCEAR 2016 ¶157 first attaches "38.5" to Larderello, then "260"; the arithmetic shows 260 is Larderello and 38.5 The Geysers); 110 TBq/a at 400 MW (1988) | S0001, S0008 |
| The Geysers | 38.5 TBq/(GW a); 19.3 to 21 TBq/a at 502 MW (1970s to 1980) | S0001, S0008 |
| Larderello, independent | about 8 Ci/day = 108 TBq/a (derived: $8\times3.7\times10^{10}\times365.25$) | S0509 (citing George et al. 1980) |
| RSE (2013) model | $1.9\times10^{5}$ Bq/s for 20 MW and $4.8\times10^{5}$ Bq/s for 50 MW, i.e. about $9.5\times10^{3}$ Bq/s per MW. Derived: $9.5\times10^{3}\times3.156\times10^{7}\approx3.0\times10^{11}$ Bq/(MW a), about 300 TBq per GW installed running continuously. Modelled, not measured | S0509 |
| Vapour- vs liquid-dominated | Rn in Cerro Prieto and Wairakei reservoirs about 40 times lower than the Geysers | S0505 |

Reading: the Larderello figure (260 to 300 TBq/(GW a)) is repeated by three routes (UNSCEAR, 8 Ci/d, RSE model). The Geysers is about 7 times lower per GW. UNSCEAR's 150 is a two-plant mean. Proposed bounds 20 to 400 TBq/(GW a), central 150, to be set by field type: dry steam high; flash lower; binary near zero (closed loop, no venting; inference).

Rn-220: only S0508 (present in all 23 NZ wells tested, plus a fumarole). No ratio. Inference: the 55.6 s half-life means little reaches the stack. Keep the `Rn220+` group with wide bounds, flagged, until the S0508 full text is read.

Countries with no plant-level radon found: Iceland, NZ, Turkey, Indonesia, Philippines, Kenya, Mexico. Those with data are Italy (S0509) and the USA (via UNSCEAR). Everything else must be modelled from field type (S0505) times generation (S0510).

### 2.2 Scale and sludge NORM (stage `geothermal`, tier `impounded`, residue `geothermal_scale`)

| Site (year) | Ra-226 | Ra-228 | Pb-210 | Other | Source |
|---|---|---|---|---|---|
| Netherlands scale (2020s) | 3.4 to 3,300 | <5 to 630 | $2.5\times10^{3}$ to $1.8\times10^{5}$ | Th-228 and Po-210 main in scale | S0500 |
| Netherlands sludge | 52 to 90 | 61 to 112 | 770 to 7,700 | | S0500 |
| Larderello (2021) | U chain 1 to 60 | Th chain 1 to 47 | 10 to 1,900 | Po-210 9 to 2,070; K-40 10 to 640 | S0501 |
| Amiata (2021) | U chain 1 to 25 | Th chain 1 to 27 | 5 to 134 (ENEL 80) | Po-210 315; K-40 5 to 450 | S0501 |
| Turkey, one plant (2013) | 40 to 2,694 | Th-232 33 to 2,388 | not measured | K-40 <MDA to 967 | S0503 |

Units Bq/kg. Caveat: the Dutch plants are low-temperature heat installations, so they bound the scale but are not power plants.

- Pb-210 exceeding Ra-226 by 10 to 500 times (S0500) means the activity is not radium-supported. Pb-210 and Po-210 come from radon progeny and brine. Do not enter Pb-210 as a Ra-226 multiple.
- Scale mass per MW a is **not sourced**. Without it only the concentration side is done. Gap.
- Brine reinjection (tier `reisolated`, residue `geothermal_brine`): no Ra, Pb-210 or Rn concentration in reinjected brine found. S0500 gives TDS only (114,500 mg/L). S0507 says Ra-226 is low in NZ waters. Gap.
- Disposal: Iceland stores scale sealed on site (S0512); Italy treats residues under NORM rules (S0501, S0502).
- Regional gaps: Indonesia, Philippines, Kenya, Mexico. FNCA and IAEA NORM posters checked contain no geothermal scale data (Indonesia and Philippines entries concern oil, gas, coal fly ash). Kenya has only Magadi natural-system background (S0523).

### 2.3 Capacity and generation

- 2010 world: 7.77 GW a (S0001). 2015: 12,284 MWe, 73,550 GWh/a. 2020: 15,950 MWe, 95,098 GWh/a (S0510, 2020 includes plants under construction). Country values (2015 / 2020, GWh): USA 16,600 / 18,366; Indonesia 9,600 / 15,315; Philippines 9,646 / 9,893; Turkey 3,127 / 8,168; NZ 7,000 / 7,728; Mexico 6,071 / 5,375; Italy 5,660 / 6,100; Kenya 2,848 / 9,930; Iceland 5,245 / 6,010.
- Milestones: Larderello 1913 (0.25 MW), Geysers 1960 (12 MW), Wairakei 1958 (69 MW), 2005 country table (S0511).
- Decadal series 1950s to 2000s not obtained. Leads for Task 1.9: Bertani (2005, 2012, 2016 world updates, Geothermics / WGC) and Huttrer (2001).

### 2.4 Epsilon for `geothermal_scale`

- No measured Rn-222 emanation or exhalation from geothermal scale found.
- Evidence that points down: S0500 shows Ra-226 in scale is often low, so little radon is produced in situ.
- Recommendation: keep the METHODS provisional default $\varepsilon=0.2$ (0.05 to 0.35). Scale Ra-226 is small, so the sensitivity is low. Refine from barite and oil and gas scale emanation work (Task 1.4 ranges) if wanted. This is an inference and a placeholder.
- Rn-220 from Th-228-bearing scale (S0500) is a separate, unquantified path.

## 3. Biomass and peat

### 3.1 Factor ranges (Bq/kg unless stated)

| Quantity | Value | Source |
|---|---|---|
| Cs-137 in wood fuel, Sweden 1997 (deposition 5 to 110 kBq/m2) | 3 to 280 | S0515 |
| Cs-137 in wood fuel, Lithuania 2010 | pellets <=14; briquettes <=1.4; imports: Ukraine <=156, Belarus 30, Poland 4, Kaliningrad 1 | S0514 |
| Cs-137 in wood ash, Sweden houses 1997 | 2,000 to 21,000; soot 2,000 to 23,000 | S0515 |
| Cs-137 in wood ash, Lithuania 2010 | up to 7,201 (results) or 2,340 (abstract); Ukrainian pellet ash 9,800 | S0514 |
| Cs-137 in household wood ash, Zhytomyr 2017 | 170 to 32,900 | S0516 |
| Cs-137 in US wood ash (weapons fallout) | 2.9 to 780; New England mean about 440 | S0520 |
| Cs-137 in peat | Finland mean 16, max 622 | S0519 |
| Cs-137 in peat ash, Sweden | 43 to 34,480; mean about 10,000 (1986 to 89); 1,000 to 43,500 (36 samples from fallout counties). Reference 1,000 normal, 10,000 high | S0519 |
| Ash concentration factor (dry fuel mass to ash mass; S0514 terminology) | wood: 95 to 370 (Lithuania), 14 to 368 (Ukraine, S0514 Table 1), about 50 to 100 (Ukraine, S0516), about 90 (Sweden); peat about 20 | S0514, S0516, S0515, S0519 |
| Fraction of fuel Cs-137 to flue gas | 0.10 assumed (not measured) | S0515 |
| Peat U-238 | 5 to 140 (Finland mean 11); UNSCEAR 40 sits inside | S0519, S0008 |
| Peat ash U-238 | mean 865, median 420, max 9,260 (146 Swedish bogs); reference 420 and 4,500 | S0519 |
| Peat Ra-226, Pb-210, Po-210 | Ra-226 up to 35; Pb-210 mean 13, max 190; Po-210 mean 9, max 200 | S0519 |
| Peat ash Pb-210, Po-210 | Pb-210 139 to 1,267; Po-210 1,200; reference 1,000 and 4,000 | S0519 |
| Swedish peat ash arisings | 30 to 60 kt/a at 3.5 TWh/a | S0519 |

Cs-137 ash re-release is what UNSCEAR deliberately excluded (S0001 para 191). It is by far the largest artificial item in this stream. Swedish house ash (typically 10,000 Bq/kg) is roughly 20 times the US weapons-fallout ash mean (about 440 Bq/kg), consistent with Chernobyl deposition (inference).

Contradictions and flags:
- S0514 reports Lithuanian ash both as 2,340 and 7,201 Bq/kg. Use the range.
- Ash enrichment spans over an order of magnitude (14 to 370), partly soil in the fuel (S0514). Do not compute ash activity from fuel activity without a spread. The product method in METHODS 11.1 handles it, with wide bounds.
- 10% flue-gas fraction comes from larger-plant studies cited in a house-heating report. Treat as an assumption. Cs, Pb-210 and Po-210 volatilise and condense on fine fly ash (S0519). UNSCEAR assumed 99% dust control for peat. Stack release is then fraction volatilised times (1 minus dust-control efficiency).
- S0517 gives only dust: 3.76 mg/Nm3 against a 4 mg/m3 limit with cyclone plus bag filter.

### 3.2 Ash disposal routes

Peat ash: landfilling, landscaping and handling in Sweden (S0519). Wood ash: recycled to forest in Finland (S0518), fertiliser in Austria (S0521), household ash to gardens in Ukraine (S0516), with some Ukrainian ash classed as low-level waste (about 9%, S0516). No country-year split found. Propose a modelled split (landfill = `impounded`, spreading = `dispersed`) with wide bounds. Tier matrix allows impounded, dispersed, liberated for `biomass_peat`.

### 3.3 Not found

- K-40 and Pb-210/Po-210 in wood ash (lead: AGES final report, S0521).
- Belarus power or heating plant ash data, Estonia, Finland power-plant ash Cs-137 (only via S0518 abstract). Belarus appears only as fuel imports in S0514.
- Peat power series for Finland, Ireland, Russia, Belarus. Leads for Task 1.9: Statistics Finland (S0526; values in image only), Bord na Mona / ESB (Irish peat stations closed 2020; only news pages seen), IEA energy balances, Eurostat.
- Weapons-fallout-era biomass ash: one US survey (S0520).

### 3.4 Pre-1950

Inference: Cs-137 did not exist in the environment before the first nuclear tests and fallout. Pre-1950 wood and peat residues carry only natural K-40, U-series (peat) and Pb-210/Po-210. Fuel quantities (fuelwood, peat) back to 1800 would come from Task 1.9, and ash concentrations from S0519.

### 3.5 Forest fires and Task 1.8

Forest fires re-release Cs-137 but are not energy-related. Note for Task 1.8 only if the orchestrator extends events beyond energy. 2020 Chernobyl Exclusion Zone fires: S0524 (inaccessible). Not noted as an energy event.

### 3.6 Scope question for the orchestrator

Household firewood (S0515, S0516, S0521) probably dominates biomass Cs-137 ash. The `biomass_peat` stage has no non-power variant (coal has `combustion_nonpower`). Decide whether domestic heating biomass is in scope for stream 5.

## 4. Hydro

Basis for negligibility (METHODS 10.3):
1. UNSCEAR 2016 omitted hydro (400.8 GW a in 2010) as negligible (S0001, para 27 per Task 1.1). That is a judgement, not a measurement.
2. Operation has no fuel, no residue and no discharge. The `hydro` stage permits only `liberated` flow. The central operational estimate is therefore zero by process, below 0.1% of any stream total in Bq and W in every decade. **Status: provisional.** METHODS §10.3 asks for a recorded numeric estimate; for operation the estimate is zero by process (reservoir radon and sediment arguments are inference, no measurement found), and for construction the numeric test waits on Task 1.9 intensities (point 4). Negligibility is not final until that test is recorded (verification 2026-10-22).
3. Reservoir radon (inference, no measurement found): impoundment does not mobilise crustal Ra-226. Water cover reduces soil exhalation, and dissolved radon degassing from rivers is already in the natural baselines (Task 1.7). Sediment Cs-137 and natural nuclides are catchment fallout and soil redistributed, not an energy-process source. Not additional to baselines.
4. Construction materials are counted through commodity factors, $\sigma_c=\sum_t C_t I_{t,c}/Q_c$ (METHODS 10.2), in the `construction` stage. Hydro's cement and steel per GW are large, so the construction share must be **tested numerically** once Task 1.9 supplies intensities. The negligibility rule is a test, not an assumption, for that stage. No intensity was obtained here (lead S0522).

## 5. Construction

Stage `construction`, substreams geothermal, biomass_peat, hydro. UNSCEAR gives materials only for PV and wind (Tables 39 to 45) and a construction-mining dose for biomass (validation only). No sourced t/GW found. Task 1.9 commodity factors required; availability rows list the method.

## 6. Inaccessible or partial sources (URLs for Steve)

- S0524 PMC article on 2020 Chernobyl-zone fires (reCAPTCHA): https://pmc.ncbi.nlm.nih.gov/articles/PMC7327000
- S0525 INIS peat record (robots disallowed): https://inis.iaea.org/records/sycm0-fd680
- S0504 Stoker & Kruger SGP-TR-4 (read the Chapter 4 Geysers tables): https://pangea.stanford.edu/ERE/research/geoth/publications/techreports/SGP-TR-004.pdf
- S0506 D'Amore 1978: https://link.springer.com/article/10.1007/BF00879751
- S0508 Whitehead & Ditchburn 1996: https://link.springer.com/article/10.1007/BF02071237
- S0507 GNS SR 93/38: https://shop.gns.cri.nz/sr_1993-38-pdf/
- S0513 Pepin 2023 full text: https://doi.org/10.1093/rpd/ncad077
- S0521 AGES final report (linked from the page): https://www.ages.at/en/environment/radioactivity/radioactivity-in-other-media
- George et al. 1980 (primary for Geysers and Larderello radon, cited by UNSCEAR and S0509): not located.

## 7. Open issues

- S0509 has no stated year (left blank in the CSV; `year` is nominally an integer).
- S0511 and S0523 years are inferred.
- S0522 and S0524 citation details unverified.
- The 40 times (S0505) Geysers vs liquid-dominated ratio is for reservoir fluid, not stack emission.
