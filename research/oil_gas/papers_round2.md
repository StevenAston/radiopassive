# Oil and gas factor gaps: round-2 paper extraction (PROPOSALS ONLY)

Researcher notes, 27 October 2026. Nothing in `data/`, `docs/`, `pipeline/` or existing research files was edited. Companion: `research/oil_gas/sources_round2.csv` (new S1210-S1215; corrections to S0315, S0325, S1204, S0429, S0246). Activities in Bq or Bq/(GW a). Unit conversion used throughout: 1 pCi/L = 37 Bq/m$^3$; 1 GW a(th) = 31.54 PJ; at $0.286$ m$^3$ gas per kWh(th) (assumed from the existing factor note) and $8.766\times10^{9}$ kWh per GW a, gas volume is $2.507\times10^{9}$ m$^3$/(GW a), so each 100 Bq/m$^3$ of delivered gas is 0.2507 TBq/(GW a).

## 1. File identities

| File | Identity | Use |
|---|---|---|
| `412.pdf` | IOGP Report 412 (Feb 2025), *Managing NORM in the oil and gas industry* (S1210) | ranges, produced water, scale |
| `gesell1975.pdf` | Gesell (1975), *Health Phys.* 29(5):681-687 (S1211) | gas-plant radon partition |
| `tasker2018.pdf` | Tasker et al. 2018, ES&T 52:7081 (S0325), confirmed | road spreading |
| `1-s2.0-S0048969720305957-main.pdf` | Scanlon et al. 2020, STOTEN 717:137085 (S0315), confirmed, open access | produced-water volumes and Ra |
| `Global-Gas-Flaring-Tracker-Report-June-20-2024.pdf` | World Bank GGFR tracker 2024 (S1204) | flaring intensity only |
| `TRS419_web.pdf` | IAEA TRS-419 (S1212) | solids per well; gas Rn range |
| `epa402r93078.pdf` | EPA 402-R-93-078 *Radon Mitigation Standards* (scan; OCR confirmed). NOT the diffuse-NORM report | none |
| `homes_protocols.pdf` | EPA 402-R-93-003 *Protocols for Radon and Radon Decay Product Measurements in Homes* | none |
| `SPERA_2012_final abstract_book.pdf` | SPERA 2012 abstracts | S0429 text only |

Johnson 1973 (EPA-520/1-73-004) and Bell et al. are NOT among the supplied files under any name. Steve's belief that they are in `homes_protocols.pdf` or `epa402r93078.pdf` is not borne out: both are house-radon documents with no natural-gas content. The primary EPA 1993 diffuse-NORM report (402-R-93-083) is also not in hand; both EPA files are siblings by number only.

## 2. Gap-by-gap

### G-1 EPA 1993 solids fraction (1 %) and scale/sludge split (40/60)
- No new primary evidence. The EPA file supplied is the wrong report. IOGP 412 gives activity ranges only: scale Ra-226eq 0.1-15,000 Bq/g (Table 1.4); sludge 0.05-800 Bq/g (Table 1.5); Pb-210 films to 1,000 Bq/g; no mass split.
- IAEA TRS-419 (p.16, Table V) gives mass scales that conflict with the EPA 25,000 t/a: about 100 t scale per well per year (about 400 t per NORM-generating well) and an API estimate of more than 140,000 drums (about 28,000 m$^3$) per year above about 3,300 Bq/kg. Scope is unreconciled (per well versus national; accumulation versus annual).
- Proposal: no change to 1 % or 40/60; widen the uncertainty (solids fraction low/high $\times0.3$ and $\times3$ if currently narrower). Confidence: low (no evidence either way). Flag the TRS-419 conflict as unresolved.

### G-2 Produced-water radium
- Scanlon (Sect. 3.4, p.7; Fig. S31 not supplied): total Ra (Ra-226 + Ra-228) medians Marcellus 1,980, Bakken 1,200, Permian 535, Eagle Ford 284 pCi/L = 73.3, 44.4, 19.8, 10.5 Bq/L.
- Scanlon Table 1 (p.5), 2017 produced water, $10^{9}$ L: Permian 264.4, Oklahoma area 195.3, Bakken 54.6, Eagle Ford 35.1, Niobrara 6.7, Barnett 42.5, Marcellus 5.3, Haynesville 2.2; eight shale plays 606 in total; CBM 46.2; US total about 3.4 trillion L (2012, Veil 2015).
- Volume-weighted over the four plays with Ra medians (Permian, Bakken, Eagle Ford, Marcellus; 359.4 $\times10^{9}$ L): $(264.4\times19.8+54.6\times44.4+35.1\times10.5+5.3\times73.3)/359.4 = 24.8$ Bq/L (my calculation; Permian-dominated). Applied to the unmeasured Oklahoma, Barnett, Niobrara and Haynesville the figure is an extrapolation.
- Tasker (Table 1): 14 NW-Pennsylvania conventional brines, total Ra median 1,230 pCi/L = 45.5 Bq/L, maximum 84 Bq/L. The NPWGD 17 Bq/L noted earlier is probably Ra-226 only; a different quantity, not a conflict.
- IOGP Table 1.3: Ra-226eq 0.002-1,200 Bq/L, Ra-228eq 0.3-180; unconventional about 1.5 times conventional; TRS-419: some wells above 1.85 Bq/L, up to 111 Bq/L.
- Proposal: central total Ra in US produced water 20-25 Bq/L (volume-weighted from Scanlon); conventional Appalachian 45 Bq/L; keep existing low/high if they span 2-110 Bq/L. Confidence: medium for the shale-weighted figure; low for the national mean (Oklahoma/Barnett/other conventional are proxies). Report whether the factor is Ra-226 only or total Ra: Scanlon and Tasker are totals, so Ra-226 alone is perhaps half.

### G-3 Road spreading (Tasker)
Radium spread in Pennsylvania 52 mCi (1.92 GBq) in 2016; 320 mCi (11.8 GBq) over 2008-2014; Ohio roughly 5 million L/a against 35 million L/a in Pennsylvania (42 million L in 2016). Treatment-plant discharge 83 mCi (7 yr) and 2.6 mCi (2016); spills 0.3 mCi. Lab: about 45 % of applied Ra leaches in one application, about 50 % stays on aggregate, tending to about 2 pCi/g after four applications. Thirteen states permit spreading.
Proposal: add or keep a floor of about 2 GBq/a for Pennsylvania (2016) and scale by volume (about 40 million L/a $\times$ 45.5 Bq/L = 1.8 GBq/a, consistent); US total at 13 permitting states is not quantified, so report Pennsylvania as a lower bound only. Confidence: high for Pennsylvania, low for national.

### G-4 Gas radon: wellhead 625 Bq/m$^3$ and delivered fraction 0.48
- Gesell (Table 1, p.682): wellhead literature 1918-1969, US averages not above about 100 pCi/L (3,700 Bq/m$^3$), maximum 1,450 pCi/L (53,650 Bq/m$^3$), Canadian average up to 473 pCi/L (17,500 Bq/m$^3$). The 625 Bq/m$^3$ wellhead is therefore well below the old US averages (about a factor 6) and above the plant inlet means below: it is a modern, processed-and-blended value, not a wellhead survey.
- Gesell (Table 3, p.683; nine plants, 805 US plants in 1972): inlet 1.0-119 pCi/L (37-4,400 Bq/m$^3$); sales methane 0.5-93.6 pCi/L (18.5-3,460 Bq/m$^3$); ethane 97.7-368; propane 9.0-1,120 pCi/L. Mean sales/inlet ratio 0.29 (median 0.17). Plant-1 balance (Table 2): 53.3 mCi/d in, 51.8 out (97 % closure), methane 2.9 (5.4 %), ethane 39.2 (73 %), propane 9.6 (18 %), butane 0.06 mCi/d. Propane Rn about 8.2 times inlet ($r = 0.94$).
- The "34 % retention" quoted in the factor note is not in this paper. The paper supports instead a sales-gas fraction in plant 1 of 5 %, a mean ratio 0.29 and a median 0.17. The 0.48 delivered fraction is not reproduced by Gesell; transit decay adds a factor $\exp(-0.693\,t/3.82\,\mathrm{d})$ (0.8 for 1.2 d; 0.5 for 3.8 d), which IOGP (p.14) confirms qualitatively.
- Proposal: delivered fraction central 0.29 (Gesell mean, before pipeline decay; 0.17 median) times transit decay 0.7 (about 2 d) = 0.20; range 0.1-0.5. Equivalent change in the wellhead-to-delivered chain: 625 Bq/m$^3$ $\times$ 0.48 = 300 Bq/m$^3$ (old) to about 125 Bq/m$^3$ (new). Confidence: low-medium (single 1970s nine-plant sample).

### G-5 Flaring
GGFR (S1204): global flaring 148 bcm (2023), 139 bcm (2022); intensity 4.7 m$^3$/bbl (2022) to 5.0 m$^3$/bbl (2023), about 36.7 m$^3$ per tonne crude (7.33 bbl/t). No radionuclide or radon data: nothing to change in radon factors; flared radon is a pure inference. The notes' 4.7 should be 5.0 for 2023.

### G-6 Benchmarks (independent of UNSCEAR 2016 Annex B?)
All TBq/(GW a) values use 0.2507 TBq per 100 Bq/m$^3$ and are my calculations.

| Benchmark | Value | TBq/(GW a) | Independence from UNSCEAR 2016 | Quality |
|---|---|---|---|---|
| Gesell 1975, sales gas, nine plants | 18.5-3,460 Bq/m$^3$ | 0.05-8.7 | Independent (measurements 1970s) | primary, dated; mean ratio 0.29 |
| Gesell 1975, plant inlet | 37-4,400 Bq/m$^3$ | 0.09-11 | Independent | primary |
| Gesell wellhead US average ceiling | 3,700 Bq/m$^3$ | 9.3 (undecayed, upper bound) | Independent | historical |
| Dixon 2001 (abstract; UK-use study) | about 200 Bq/m$^3$ | 0.50 | Independent of UNSCEAR 2016; derived from UK data (country not stated in abstract) | abstract only |
| Existing model: Gesell $\times$ Johnson | 1.17 TBq/(GW a) (about 470 Bq/m$^3$) | 1.17 | Partly (Johnson via UNSCEAR) | cannot check; Johnson not in hand |
| Proposed new chain | about 125 Bq/m$^3$ | 0.31 | partial | see G-4 |
| IOGP 412 Table 1.2 | 5-200,000 Bq/m$^3$ (NG), 0.01-1,500 Bq/L (NGL) | not a mean | Independent but ranges only | useless for central values |
| TRS-419 | 2-17,000 Bq/m$^3$ (groups), 0.4-54,000 (wells) | not a mean | Secondary to UNSCEAR and Johnson: NOT independent | |
| Hedvall 1996 | up to 50 Bq/L (50,000 Bq/m$^3$) | not a mean | NOT independent (UNSCEAR 1988) | |
| Netherlands 74 Bq/m$^3$ | unverified | 0.19 | unknown | not found; do not use |
| UK about 170 Bq/m$^3$ | unverified; nearest is Dixon about 200 | 0.43 (if 170) | unknown | not found; do not use |

Solids per GW a(th) (inference, order of magnitude only): US oil and gas primary production is about $2\times10^{3}$ GW(th) (about 70 EJ/a, my estimate), so EPA 25,000 t/a scale is about 10 t/(GW a); the API 140,000 drums (28,000 m$^3$, $\approx$ 40,000 t at 1.5 t/m$^3$, my assumption) is about 20 t/(GW a); TRS-419's 100 t per well per year would be orders of magnitude higher and is not credible as a national mean. Independence: EPA/API are the origin of UNSCEAR-era numbers, so NOT independent; no truly independent solids benchmark was found.

## 3. Proposal table

| # | Item | Old | New | Confidence |
|---|---|---|---|---|
| O1 | Solids fraction 1 % and 40/60 split | as is | no change; widen range | low |
| O2 | Produced-water total Ra, US shale-weighted | existing | 20-25 Bq/L central (24.8) | medium |
| O3 | Appalachian conventional Ra | existing | 45 Bq/L (total Ra); keep 17 Bq/L as Ra-226 | medium |
| O4 | Pennsylvania road spreading | existing | about 2 GBq/a (2016) floor | high |
| O5 | Gas delivered fraction | 0.48 | 0.20 (range 0.1-0.5) | low-medium |
| O6 | Wellhead 625 Bq/m$^3$ | 625 | keep as an assumption, but relabel (modern blend, not survey); old US averages 3,700 | low |
| O7 | Flaring intensity | 4.7 m$^3$/bbl | 5.0 (2023) | high |
| O8 | Gesell $\times$ Johnson 1.17 TBq/(GW a) | 1.17 | drop as a benchmark; use 0.3-0.5 (Dixon, Gesell chain) | low-medium |

## 4. Per-paper contribution

| Paper | Contribution |
|---|---|
| Gesell 1975 | plant partition, sales/inlet ratios, wellhead literature; corrects "34 %" |
| Scanlon 2020 | volumes and Ra medians by play |
| Tasker 2018 | conventional brine Ra, spreading totals |
| IOGP 412 | ranges, exemption levels (1 Bq/g, 10 Bq/L), OSPAR discharges (7.6 TBq/a alpha, 5 TBq/a beta, ex tritium) |
| IAEA TRS-419 | per-well solids; conflict with EPA |
| GGFR | flaring intensity only |
| Dixon 2001 | nearest verifiable UK gas Rn |
| EPA 402-R-93-078, -003 | not relevant |
| SPERA 2012 | none for oil and gas |

## 5. Gaps and contradictions
1. Johnson 1973 and Bell et al. not supplied; EPA diffuse-NORM report not supplied.
2. Netherlands 74 and UK 170 Bq/m$^3$ unverified (ScienceDirect, OSTI and WHO fetches blocked). Dixon's about 200 is abstract-only.
3. "34 %" is not in Gesell; 0.48 not reproduced.
4. Solids: EPA vs TRS-419/API conflict by orders of magnitude.
5. Scanlon Ra medians come from Fig. S31 (not supplied); Ra quantity (total vs Ra-226) must be set per factor.
6. Solids per GW a(th) conversion depends on my US energy estimate.
