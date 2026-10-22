# Stream 3, oil and gas: notes (Task 1.4)

## 1. Method

Sources were found for each stage in SCHEMA §5.2 (drilling, production, oil_sands_mining, processing_transport, abandonment_scrap, construction), preferring regulators and agencies. USGS NPWGD v2.3 and v3.0 were downloaded and the Ra-226/Ra-228 columns summarised by play by the task (scratchpad scripts, not deliverables). PA DEP table values were recomputed from the tables, not the tracked-changes prose. All pCi conversions are mine. UNSCEAR coverage (S0001, S0005, S0008) is cited, not repeated.

Status definitions used in `availability.csv`:
- **measured**: directly reported annual activity (only OSPAR offshore discharges, 2000s and 2010s).
- **compiled**: an authoritative driver plus a period- and region-matched factor.
- **modelled_possible**: a driver exists but the factor is extrapolated.
- **no_data**: neither exists, or the driver is negligible (the method then states a zero or proxy).

Counts: 234 rows; 2 measured, 17 compiled, 91 modelled_possible, 124 no_data (most no_data rows are construction, which needs no O&G-specific factor, and pre-2000 unconventional cells).

Coverage by decade (summary): 2010s is the best covered (Appalachia, Bakken, US volumes, PA gas radon). 2000s and 1990s are compiled for conventional production only. 1950s–1980s rely on extrapolated water-oil ratios and the SRS 34 ranges. Pre-1950 is a modelled opening stock anchored on Gott and Hill 1953. 2020s is carried forward from 2017–18 data (no national report obtained).

## 2. Key factor ranges (full list in `factor_ranges.csv`)

Produced water, Bq/L (median; p95; max), from task statistics of NPWGD v3.0 (S0303):

| Play | Ra-226 | Ra-228 |
|---|---|---|
| Marcellus (n=100/96) | 46.6; 378; 626 | 4.7; 41; 114 |
| Utica (43/17) | 48.5; max 134 | 44.7; max 53.5 |
| Appalachian conventional (101/65) | 16.7; 75; 196 | 18.5; 81; 888 (outlier) |
| Bakken/Three Forks (17) | 73.4; 135; 157 | 63.8; 72; 73 |
| Gulf Coast, Mississippi 1984 (17/12) | 18.6; 38.6 | 22.7; 48 |
| Fayetteville (5) | 5.2; 9.6 | 0.9 |
| Permian, NM (46; S0316) | mean 1.6 (0.03–4.1) | mean 5.6 (0.09–10.8) |
| Norwegian shelf (S0304, S0308) | mean 4.1 (0.5–10) | mean 2.1 (0.5–8.7) |

PA DEP 2016 (S0301): unconventional Ra-226 63–984 Bq/L (n=9, mean about 309), conventional ≤3–30 Bq/L; flowback Ra-226 20–944 Bq/L. Global range SRS 34 (S0304): Ra-226 0.002–1,200, Ra-228 0.3–180, Pb-210 0.05–190 Bq/L.

Scale, Bq/g Ra-226: global 0.1–15,000 (S0304); US average 17.8 (S0328); Norway typical 10–300 (S0309); US pipe scale site means 15–76 (S0321). Sludge: global 0.05–800; US average 2.8; Norway 0.1–20 typical, company means 19–40 (S0304, S0328, S0309, S0310).

Gas radon, Bq/m³: UNSCEAR mean 625 wellhead, 300 sales gas (S0001); PA DEP median 1,547 (111–5,476) (S0301); USGS PA median 1,369 (S0317); Marcellus pipelines 1,983 weighted (S0318); historical US conventional mean 1,370, range 7–54,000 (S0318 citing Johnson 1973). Pb-210 on propanizer filters 132 Bq/g (S0301).

Drill cuttings, U-238: PA vertical 0.054 Bq/g; Marcellus horizontal mean 0.31, max 1.0 Bq/g (S0301); Marcellus core 0.10–0.65 Bq/g (S0330); Bakken within soil range (S0331).

Volumes and routes (S0311): US 20.2, 21.2, 24.4 Gbbl (2007, 2012, 2017). 2017 routes: EOR 44.0%, disposal 37.9%, commercial 9.9%, discharge 5.5%, reuse 2.3%, evaporation 0.4%. Unconventional share about 16% in 2017 (my inference from S0315 and S0311, mixed sources). IOGP 2018: 58% re-injected.

Offshore (S0307): Ra-226 0.73–1.1 TBq/a in 2005–2018.

## 3. Radon exhalation inputs for residue_types.csv

None are entered (all ε parameters in `data/reference/residue_types.csv` are empty and I did not touch that file). Proposed (modelled; from S0321, S0306):
- og_scale: ε low 0.01, central 0.05, high 0.14.
- og_sludge: ε low 0.05, central 0.15, high 0.25.
- og_processing_residue: mostly Pb-210/Po-210 with little Ra parent; apply sludge values only where Ra-226 is present.
- Th-220 emanation: minerals about 0.01, rocks about 0.11 (S0306); no oil-field data.
- og_drill_cuttings, og_produced_water, og_scaled_scrap, oil_sands_tailings, oil_sands_coke: no oil-field specific data; use generic soil/rock values from Task 1.7.

Caution: S0321 measures emanation fractions, not the effective exhalation fraction, which also depends on diffusion length and cover.

## 4. Event candidates for Task 1.8

- Bakken brine spills: North Dakota about 3,900 spills 2007–2014; Blacktail Creek (January 2015) about 11 million L; Bear Den Bay (July 2014) 3.8 million L (S0322).
- At Bakken radium levels (about 137 Bq/L total Ra), 11 million L carries about 1.5 GBq and about 1.1e4 t, far below the 1 TBq and 1e5 t thresholds. Reaching 1 TBq needs about 7e9 L at Bakken levels, about 2e10 L at Marcellus levels (my arithmetic). No produced-water spill found qualifies.
- Better candidates are chronic, not events: Pennsylvania CWT discharge to streams (peaked 2009, S0323) and road-spreading (about 11.8 GBq Ra in 2008–14, S0325). Treat as route flows.

## 5. Open issues and contradictions

1. Rowan 2011 non-Marcellus median: 734 pCi/L (abstract) vs 1,011 (text).
2. PA DEP track-change file: prose numbers unreliable; obtain the final clean version.
3. Bakken: NPWGD v3 gives Ra-226 plus Ra-228 median about 137 Bq/L; Scanlon (via S0316) total Ra median 1,200 pCi/L (44 Bq/L).
4. OSPAR 2018 Ra-228: 0.66 TBq (text) vs 0.749 (Table 3.1).
5. TRS 419 and EPA page: "100 t of scale per well per year" is inconsistent with the 140,000 drums (28,000 m³) per year API figure and SRS 34; not used. EPA page has an internal volume inconsistency.
6. Xhixha Table 1: Saudi row and one Egyptian row look like unit errors.
7. Côté abstract says gallons where the data are litres; litres used.
8. Pb-210 in Norwegian produced water is reported from detection limits (S0308).
9. No radium data for the Permian beyond New Mexico, Eagle Ford, Haynesville, Gulf of Mexico, Middle East, Russia, China.
10. No data: oil-sands tailings and coke activity; the only quantified item is monazite in froth treatment tailings (S0326). Illustrative Th-232 about 8–26 TBq/a assumes 5–10 wt% ThO₂, which is unsourced: modelled, to be sourced by Task 1.5.
11. Scale and sludge mass per unit production has no authoritative series. Calibration idea: Norway retains about 0.1–4% of discharged Ra as waste (NORM waste 0.3–30 GBq/a vs 807 GBq/a discharged; inference).
12. Drill-cuttings tonnage per well not found (modelled from borehole geometry).
13. Disposal-route shares exist only for 2007, 2012 and 2017 (US); earlier shares and non-US shares are assumptions.
14. Per D6, oil/gas/NGL allocation is by value; no radiological data differ by product except gas-side radon and NGL Pb-210.
15. Unconventional water shares mix sources (Scanlon vs Veil).
16. Tasker 2018 and Van Sice figures were taken from press coverage or abstracts; verify.

## 6. Inaccessible or unverified URLs for Steve

- S0312 GWPC 2020 report: https://www.gwpc.org/publications/u-s-produced-water-volumes-and-management-practices-in-2017/ (landing page has no PDF link).
- S0313 ANL/EVS/R-09/1: https://www.osti.gov/biblio/1007397 (PDF returned 403).
- S0315 Scanlon et al. 2020, paywalled: https://doi.org/10.1016/j.scitotenv.2020.137085
- S0325 Tasker et al. 2018, paywalled: https://doi.org/10.1021/acs.est.8b00716
- IOGP Report 412 (2016), not obtained: https://www.iogp.org/bookstore/product/412/
- Not fetchable by my tools (bot walls): PMC, DukeSpace and ResearchGate pages. S0322's DukeSpace link was reached via an alternate route; test it.
- S0311 slides were read through a summarising tool: confirm the numbers by opening https://www.gwpc.org/uploads/documents/2019_Annual_Forum/Veil_John.pdf.
