# Nuclear factor gaps: round-2 paper extraction (PROPOSALS ONLY)

Researcher notes, 27 October 2026. Nothing in `data/`, `docs/`, `pipeline/` or existing research files was edited. Companion: `research/nuclear/sources_round2.csv` (corrections to S0121, S0138, S1005; new S1006-S1012). All activities are Bq or Bq/(GW a); 1 Ci = $3.7\times10^{10}$ Bq; 1 GW a of electricity = 8.766 TWh.

## 1. File identities

| File | Identity | Use here |
|---|---|---|
| `20031111.pdf` | Rouben B. (AECL, March 1999), *CANDU Fuel-Management Course*, chapter 1 only (47 slides, CANTEACH library). This is the "second document" named in S1005. | PHWR core data |
| `ML24134A119.pdf` | NRC NUREG/CR-2907 Vol. 27, *Radioactive Effluents from Nuclear Power Plants, Annual Report 2021* (98 pp) = S0121 | US effluent totals |
| `document.pdf` | US DOE Office of Legacy Management fact sheet, Grand Junction, CO, Disposal and Processing Sites, Sept 2026 (4 pp) | tailings-as-fill |
| `rogovin.tmi.2.vol1.pdf`, `vol2.p1/p2/p3.pdf` | Rogovin report, NUREG/CR-1250 (S0138), Vol. I and Vol. II Part 2 in three scans | TMI-2 release |
| `Uranium 2003_...pdf`, `Uranium 2026_...pdf` | NEA/IAEA Red Books 2003 and 2026 | ISL shares |
| `SPERA_2012_final abstract_book.pdf` | 12th SPERA conference abstract book, Sydney 2012 (72 pp) | marginal |
| `Global-Gas-Flaring-Tracker-Report-June-20-2024.pdf` | World Bank GGFR tracker 2024 | nothing nuclear; see oil and gas file |
| `epa402r93078.pdf` | EPA 402-R-93-078 *Radon Mitigation Standards* (scan, OCR checked) | not relevant |
| `homes_protocols.pdf` | EPA 402-R-93-003 *Protocols for Radon and Radon Decay Product Measurements in Homes* | not relevant |

Johnson 1973 (EPA-520/1-73-004) and Bell et al. are NOT in any staged file. I screened the first pages and the "natural gas" hits of every PDF in the import folder: the only gas-radon texts are Gesell 1975, IOGP 412, IAEA TRS-419 and Hedvall and Erlandsson 1996 (see the oil and gas file).

## 2. NUREG/CR-2907 Vol. 27: US 2021 fleet totals (closes the "totals" gap)

Method: parsed Tables 3-1 to 3-14 (per reactor, significant nuclides) and 3-15 to 3-18 (all noble gases; all mixed fission and activation products, MFAP) by column position; checked by hand for BWR noble gas 3,177.0 Ci. 93 reactors (31 BWR, 62 PWR). Multi-unit sites are split equally between units by the NRC, so unit values repeat; sums are unaffected. Blank cells (not detected) are counted as zero, so totals are lower bounds.

Conversion to per GW a: US generation 778 TWh in 2021 (EIA, S1011) = 88.75 GW a; split BWR 29.6 and PWR 59.2 GW a by reactor count (assumption; real BWR share is probably 34 %, shifting BWR values by about 3 %).

| Quantity (2021) | BWR | PWR | Source |
|---|---|---|---|
| All noble gases, Bq | $1.175\times10^{14}$ (3,177 Ci) | $2.33\times10^{13}$ (629.5 Ci) | Tables 3-15, 3-16 |
| per GW a | $3.97\times10^{12}$ | $3.94\times10^{11}$ | |
| Median per reactor, all noble gas | 21.0 Ci = $7.8\times10^{11}$ Bq | 1.0 Ci = $3.7\times10^{10}$ Bq | text p.3-38 |
| Kr-85, Xe-133, Xe-135 only (Tables 3-1/3-6) | 69.2 / 507.9 / 484.3 Ci | 24.7 / 387 / 4.8 Ci | |
| H-3 gaseous, Bq (per GW a) | $6.46\times10^{13}$ ($2.18\times10^{12}$) | $1.89\times10^{14}$ ($3.20\times10^{12}$) | Tables 3-4, 3-9 |
| C-14 gaseous, Bq (per GW a) | $1.78\times10^{13}$ ($6.0\times10^{11}$) | $2.02\times10^{13}$ ($3.4\times10^{11}$) | Tables 3-5, 3-10 |
| I-131 gaseous, Bq (per GW a) | $2.7\times10^{9}$ ($9.2\times10^{7}$) | $1.4\times10^{7}$ ($2.4\times10^{5}$) | Tables 3-2, 3-7 |
| Particulates Co-58+Co-60+Cs-134+Cs-137 gaseous, Bq (per GW a) | $5.3\times10^{8}$ ($1.8\times10^{7}$) | $8.3\times10^{7}$ ($1.4\times10^{6}$) | Tables 3-3, 3-8 |
| of which Co-60 / Cs-137, per GW a | $1.3\times10^{7}$ / $3.1\times10^{5}$ | $3.9\times10^{5}$ / $1.3\times10^{4}$ | |
| H-3 liquid, Bq (per GW a) | $2.09\times10^{13}$ ($7.1\times10^{11}$) | $1.68\times10^{15}$ ($2.85\times10^{13}$) | Tables 3-12, 3-14 |
| Liquid, six significant nuclides (Co-58, Co-60, Cs-134, Cs-137, Fe-55, I-131), Bq | $6.1\times10^{9}$ | $1.95\times10^{10}$ | Tables 3-11, 3-13 |
| Liquid, ALL MFAP, Bq (per GW a) | $1.10\times10^{10}$ ($3.7\times10^{8}$) | $3.31\times10^{10}$ ($5.6\times10^{8}$) | Tables 3-17, 3-18 |
| Liquid per GW a: Co-60 / Fe-55 / Cs-137 | $1.2\times10^{8}$ / $5.5\times10^{7}$ / $8.7\times10^{6}$ | $1.2\times10^{8}$ / $5.6\times10^{7}$ / $1.2\times10^{7}$ | |

Shares in the reported liquid MFAP total (all nuclides): Co-60 33 % (BWR), 22 % (PWR); Co-58 3 %, 25 %; Fe-55 15 %, 10 %; Cs-137 2.3 %, 2.1 %; Cs-134 under 1 %; the rest (about 45 % of the total) is unlisted (Mn-54, Cr-51, Ni-63, Zr-95, Nb-95 etc.).
Gaseous noble-gas composition 2021 (share of all-noble total): BWR Xe-133 0.16, Xe-135 0.15, Kr-85 0.022 (the three listed nuclides are only 33 % of the total); PWR Xe-133 0.615, Xe-135 0.008, Kr-85 0.039 (66 % listed).
Particulate shares (of the four listed): BWR Co-60 0.74, Co-58 0.25, Cs-137 0.017; PWR Co-58 0.71, Co-60 0.28, Cs-137 0.009.
Trend (Figs 3-15, 3-16, text pp.3-42, 3-47): median BWR noble gas more than 40,000 Ci (1.5 PBq) per reactor in 1975, 21.0 Ci in 2021; median BWR liquid MFAP more than 1,500 mCi in 1975, 1.5 mCi in 2021. This supports a large 1970s-to-2010s fall in the US era factors (a cross-check on the 1950-79 and 1980-89 rows).

### Correction to the existing cross-check
`factors_notes.md` section 2 compares "US median noble gases BWR 0.18 TBq" with UNSCEAR. 0.18 TBq is the median of the THREE listed nuclides (4.94 Ci, Table 3-1). The all-nuclide median (Table 3-15) is 21.0 Ci = 0.78 TBq, 4.3 times higher; the PWR figure is 1.0 Ci = 0.037 TBq against 0.2 Ci (Table 3-6) used for the PWR low bound (4.6 times higher). The "70 to 100 times below UNSCEAR" statement becomes about 23 (BWR fleet mean) and 15 (PWR fleet mean).

### Fleet means against current central values (2010-25 rows, head-nuclide sums)
| Item | Factor central (Bq/GW a) | US 2021 fleet mean (Bq/GW a) | Ratio factor / US |
|---|---|---|---|
| BWR noble gas | $1.8\times10^{13}$ | $4.0\times10^{12}$ | 4.5 |
| PWR noble gas | $5.8\times10^{12}$ | $3.9\times10^{11}$ | 15 |
| H-3 air BWR / PWR | $1.3\times10^{12}$ / $1.5\times10^{12}$ | $2.2\times10^{12}$ / $3.2\times10^{12}$ | 0.6 / 0.5 |
| H-3 liquid BWR / PWR | $8.2\times10^{11}$ / $1.8\times10^{13}$ | $7.1\times10^{11}$ / $2.9\times10^{13}$ | 1.2 / 0.6 |
| C-14 air BWR / PWR | $1.3\times10^{11}$ / $8.3\times10^{10}$ | $6.0\times10^{11}$ / $3.4\times10^{11}$ | 0.22 / 0.24 |
| I-131 air BWR / PWR | $4.2\times10^{8}$ / $8\times10^{7}$ | $9.2\times10^{7}$ / $2.4\times10^{5}$ | 4.6 / 330 |
| Particulates air BWR / PWR | $1.8\times10^{9}$ / $3.6\times10^{7}$ | $1.8\times10^{7}$ / $1.4\times10^{6}$ (4 nuclides; understated) | 100 / 26 |
| Other liquid BWR / PWR | $2.1\times10^{9}$ / $3.8\times10^{9}$ | $3.7\times10^{8}$ / $5.6\times10^{8}$ | 5.7 / 6.8 |

Caveat: UNSCEAR centrals (S0001) are world means including WWER, older and non-US plants; the US fleet is one regulated, low-effluent fleet (about 30 % of world PWR+BWR output). The two are different populations, so I propose widening bounds and moving centrals only part of the way (log-midpoint), not replacing UNSCEAR.

## 3. Gap-by-gap

### G-A CANDU bundle uranium mass (assumed 19 kg U)
- `20031111.pdf` (slides 10, 34-39, 46) does NOT state it (Figure 1.6 absent). It gives 4,560 bundles, 2,061 MWth, burnup 7,500 MWd/Mg(U) (175-180 MWh/kg), 935 kW maximum bundle power. Average bundle power 2,061 MW / 4,560 = 452 kW.
- Closed externally by Palleck, Sejnoha and Wong 1997 (S1008, p.2): 37-element 18.8 kg U (late 1970s) to 19.3 kg U (late 1980s); Pickering 28-element 20.2 kg U; fleet 19.3 kg U.
- Proposal: 19 kg U (ASSUMED) to 19.3 kg U (compiled). Core mass 4,560 x 19.3 kg = 88.0 tU; specific power 2,061/88.0 = 23.4 MWth/tU (was 23.8); residence $T$ = 7,250 MWd/tU / 23.4 = 310 d = 0.85 a (was 0.83), +2 %. Effect on rows 1046 and the in-core rows: under 2 % on short-lived groups, nil on long-lived. Confidence high; change `basis` to compiled and source S1008 + S1005.
- Not available from the supplied papers: electrical output per CANDU 6 (needed to turn 88 tU into tU per GWe; at roughly 0.67 GWe net it is about 130 tU/GWe, against 89.9 for the PWR core).

### G-B Magnox and AGR core masses and specific power
Not in any supplied file. Web check found only AGR discharge burnup 18 GWd/t (stainless-clad original), 27 (type 2) and up to 34 GWd/t (Wikipedia, tertiary) and 1,500 MWth per reactor; no core mass. UNRESOLVED; keep as G3. Suggested primary: IAEA graphite knowledge-base station tables or EDF/NNL AGR data sheets.

### G-C US effluent totals
Done, section 2. Proposed changes (old to new, 2010-25 rows, Bq/GW a), all with the US-vs-UNSCEAR population caveat:

| # | Row(s) | Old (low / central / high) | New | Justification | Confidence |
|---|---|---|---|---|---|
| N1 | PWR and BWR noble gas low bound (Xe-133 rows 0084, 0224 and companions) | PWR total low $8.0\times10^{9}$; BWR $1.83\times10^{11}$ | PWR $3.7\times10^{10}$; BWR $7.8\times10^{11}$ (US all-nuclide medians, Tables 3-15/3-16) | existing low bound used the three-nuclide median | high |
| N2 | PWR noble central | $5.8\times10^{12}$ | $1.5\times10^{12}$ for 2015-25 (log-midpoint of UNSCEAR 2010 and US 2021 mean) | US fleet mean 15 times lower; improved fuel integrity | low-medium (option; keep old if UNSCEAR world mean is wanted) |
| N3 | BWR noble central | $1.8\times10^{13}$ | $8.5\times10^{12}$ for 2015-25 | as N2, 4.5 times | low-medium |
| N4 | Noble composition PWR (shares) | Xe-133 .35, Xe-135 .20, Kr-85 .12 | Xe-133 .55, Xe-135 .05, Kr-85 .05 (renormalise others) | US 2021 .615/.008/.039; GRS design spectrum (Xe-135 .32) is not an operating spectrum | medium-low |
| N5 | Noble composition BWR | Xe-133 .10, Xe-135 .10, Kr-85 .02, Xe-138+ .55 | Xe-133 .16, Xe-135 .15, Kr-85 .02, Xe-138+ .45 | US 2021 .16/.15/.022 | medium-low |
| N6 | C-14 air BWR | $6.5\times10^{10}$ / $1.3\times10^{11}$ / $2.6\times10^{11}$ | $1.3\times10^{11}$ / $3.0\times10^{11}$ / $6.0\times10^{11}$ | US $6.0\times10^{11}$; UNSCEAR 2008 $5.2\times10^{11}$; UNSCEAR 2016 $1.3\times10^{11}$. US values are licensee estimates | low-medium |
| N7 | C-14 air PWR | $4.2\times10^{10}$ / $8.3\times10^{10}$ / $1.7\times10^{11}$ | $8.3\times10^{10}$ / $1.7\times10^{11}$ / $3.4\times10^{11}$ | US $3.4\times10^{11}$; UNSCEAR 2008 $2.2\times10^{11}$ | low-medium |
| N8 | H-3 air PWR / BWR | high $3.0\times10^{12}$ / $2.6\times10^{12}$ | high $5\times10^{12}$ / $3.5\times10^{12}$; centrals to $2.2\times10^{12}$ / $1.7\times10^{12}$ | US fleet means $3.2$ and $2.2\times10^{12}$ exceed the highs/centrals; the earlier check used medians (1.2, 1.4 TBq per reactor) | medium |
| N9 | H-3 liquid PWR | central $1.8\times10^{13}$ | $2.3\times10^{13}$ | US $2.85\times10^{13}$ | medium |
| N10 | I-131 air PWR | $4\times10^{7}$ / $8\times10^{7}$ / $1.6\times10^{8}$ | $1\times10^{5}$ / $1\times10^{7}$ / $1\times10^{8}$ | US $2.4\times10^{5}$ (many non-detects) | low-medium |
| N11 | I-131 air BWR | $2.1\times10^{8}$ / $4.2\times10^{8}$ / $8.4\times10^{8}$ | $5\times10^{7}$ / $2\times10^{8}$ / $8.4\times10^{8}$ | US $9.2\times10^{7}$ | low-medium |
| N12 | Co-60 air PWR / BWR | central $1.08\times10^{7}$ / $5.4\times10^{8}$ | low to $4\times10^{5}$ / $1.3\times10^{7}$; central $2\times10^{6}$ / $8\times10^{7}$ | US $3.9\times10^{5}$ / $1.3\times10^{7}$ (28 and 41 times below) | low-medium |
| N13 | Cs-137+ air share in particulates | .25 (GCR .35) for LWR | .03 for PWR/BWR | US Cs-137 is 1-2 % of the four-nuclide total; fleet Cs-137 $1.3\times10^{4}$ (PWR), $3.1\times10^{5}$ (BWR) vs factor $9\times10^{6}$, $4.5\times10^{8}$ | medium-low |
| N14 | Cs-137+ and Cs-134 liquid shares | .12 and .08 | .03 and .01 | US 2.1-2.3 % and under 1 % of all MFAP; fleet Cs-137 $8.7\times10^{6}$-$1.2\times10^{7}$ vs factor $2.8$-$5.0\times10^{8}$ (23-31 times) | medium |
| N15 | Other liquid total PWR / BWR (heads) | $3.8\times10^{9}$ / $2.1\times10^{9}$ | $1.5\times10^{9}$ / $9\times10^{8}$ (log-midpoint); low to $5.6\times10^{8}$ / $3.7\times10^{8}$ | US all-MFAP | low-medium |
| N16 | Liquid composition | Co-58 .22, Co-60 .20, Fe-55 .12 | PWR Co-58 .25, Co-60 .22, Fe-55 .10; BWR Co-60 .33, Fe-55 .15, Co-58 .03 | US all-MFAP shares | medium-low |

Cross-check use: the 2021 totals ($1.4\times10^{14}$ Bq noble gas, $2.5\times10^{14}$ Bq gaseous H-3, $1.7\times10^{15}$ Bq liquid H-3 for the US) can be added as validation targets for a US-only run of `nuc_gen_pwr/bwr`.

### G-D Grand Junction tailings used as fill
Fact sheet (S1009): mill 1950-1970 produced 2.2 million tons of tailings (about $2.0\times10^{9}$ kg); 1950-1966 sandy tailings were free to the public as fill, concrete and mortar, at more than 4,000 properties; about 300,000 tons (about $2.7\times10^{8}$ kg) had left the site by 1966; cell 4.4 million yd$^3$ ($3.4\times10^{6}$ m$^3$); 228,000 yd$^3$ ($1.7\times10^{5}$ m$^3$) spare for unremediated tailings under roads and utilities (so not all fill has been recovered). No activity concentration is given.
- Mass share dispersed: 300,000 / 2,200,000 = 13.6 %.
- Activity share: Landa 1980 (S1000) says the slime fraction (25-27 % by mass) holds 77-94 % of the Ra, so a "predominantly sandy" fill carries roughly 0.08-0.31 times the average Ra concentration: Ra share 1.1-4.2 % (mass-uniform upper 13.6 %).
- Context: 26 million tons of tailings at the 24 Title I sites (EPA 60 FR 2855, S1010); Grand Junction = 8.5 % of that, and about 4,000 of the roughly 5,200 UMTRCA vicinity properties (the 5,200 is from Wikipedia, tertiary).
- Proposal (new row, no existing row to change): `u_tailings`, tier dispersed, route as fill, region USA, years 1950-1966, Ra-226+ (head): Grand Junction only, low / central / high = $3\times10^{11}$ / $1\times10^{12}$ / $6\times10^{12}$ Bq (Bq total, event-like; assumes 22 Bq/g Ra-226 in 0.25 % U$_3$O$_8$ ore tailings, which is MY assumption, not in the fact sheet; the S0119 worked-example 3.7 Bq/g would give 5-6 times less). Scale the same amount by 1.3 for the US (Grand Junction is about 77 % of vicinity properties). Confidence low. Alternatively keep it as a gap note: the amount is about 0.1-0.5 % of US milling Ra-226.

### G-E ISL shares (Red Book)
There is no Table 7.3 in the 2003 edition (the S0113 reference is the 2006 retrospective). The data are the global method split (2003 Table 16; 2026 Table 1.22) and country "Historical uranium production by production method" tables (cumulative pre-2000, then annual). Derived shares (ISL / total, tU):

| Country, period | ISL share | Basis |
|---|---|---|
| Kazakhstan, pre-2000 cumulative | 0.315 (27,801 / 88,272) | 2003, includes pre-1978 non-ISL output |
| Kazakhstan 2000, 2001, 2002 | 0.947, 0.954, 1.00 | 2003 |
| Kazakhstan 2003-2022 | 0.99 (325,119 / 328,618) | 2026 minus 2003 cumulatives |
| Kazakhstan 2023, 2024 | 1.00 | 2026 |
| Uzbekistan pre-2000 cumulative | 0.403 (37,762 / 93,730) | 2003 |
| Uzbekistan 2000-2002, 2003-2022, 2023-24 | 1.00 | 2003, 2026 |
| USA 2000, 2001 | 0.74, 0.93 | 2003 (ISL; in-place leaching withheld) |
| USA since 1991 | "non-conventional dominant" (more than 0.5) | 2003 p.US text; later by-method data withheld (W) in 2026 |
| Australia to 2000 / 2001 / 2002 / 2023 / 2024 | 0 / 0.06 / 0.08 / 0.37 / 0.42 | 2003, 2026 (cumulative to 2022: 0.085) |
| Russia cumulative to 2002; 2003-2022; 2023-24 | 0.028; 0.29; 0.61-0.62 | 2003, 2026 |
| Czech Republic cumulative to 2002 | 0.157 (16,712 / 106,769); 2000-2002 about 0.25-0.33 | 2003 |
| China 2023, 2024 | 0.91, 0.92 | 2026 (pre-2010 not available) |
| Bulgaria, Ukraine cumulative | 0.26, 0.029 | 2026 |
| World | 0.13 (1998), 0.17, 0.15, 0.155, 0.183 (2002), 0.207 (2003 exp.); 0.598 (2022), 0.554, 0.552 (2024), 0.577 (2025 prelim.) | Tables 16, 1.22 |
| World excluding Kazakhstan, Uzbekistan, USA ("rest of world"), 2023 / 2024 | 0.17 / 0.164 | computed from Table 1.18 and country tables |

Existing rows and proposals (rows 0024-0037):

| Row | Old (low / central / high) | New | Confidence |
|---|---|---|---|
| 0030 KAZ 2000-25 | 0.9 / 0.97 / 1 | 0.95 / 0.99 / 1.0 | high |
| 0029 KAZ 1978-99 | 0.25 / 0.5 / 0.8 | 0.30 / 0.40 / 0.55 (cumulative 31.5 % to 2000; some output pre-1978) | medium |
| 0033 UZB 2000-25 | 0.9 / 0.97 / 1 | 0.97 / 1.0 / 1.0 | high |
| 0032 UZB 1963-99 | 0.3 / 0.7 / 1 | 0.30 / 0.40 / 0.55 (cumulative 40 %) | medium |
| 0036 USA 1990-99 | 0.2 / 0.4 / 0.8 | 0.5 / 0.7 / 0.9 (dominant since 1991) | medium |
| 0037 USA 2000-25 | 0.8 / 0.95 / 1 | 0.74 / 0.93 / 1.0 (2000-01 data; later withheld) | medium |
| 0025 XWL 1967-99 | 0.05 / 0.15 / 0.35 | if XWL means rest of world: 0.01 / 0.03 / 0.08 (Czech, Bulgaria, Ukraine, Russia ISL only); if XWL is applied to the world total keep 0.15 | medium |
| 0026 XWL 2000-25 | 0.05 / 0.2 / 0.45 | rest of world: split 2000-09 0.02 / 0.04 / 0.08; 2010-19 0.05 / 0.10 / 0.18; 2020-25 0.12 / 0.165 / 0.22 (2023-24 verified). World-total reading: 0.15-0.2 (2000-09), 0.3-0.5 (2010s), 0.55-0.6 (2020s) | medium; the 2010-19 value is interpolated, not sourced |
| new | none | add AUS (2001-25: 0.07 to 0.42), RUS (2003-25 about 0.3, 2023-24 0.6), CZE (0.15-0.3 declining to zero), CHN (2010-25 about 0.9), BGR (to 1990s about 0.26) as country rows if the script supports them | medium-low |

Which reading of XWL the pipeline uses must be confirmed (the notes say "XWL default"); under the world-total reading the current 0.2 is already too low after 2007. Note that the radon row 0003 per tonne is applied to ISL tonnage only.

### G-F TMI-2 (Rogovin)
- Total noble gas 2.5 million Ci confirmed as Rogovin's best estimate (Vol. I ch. 9, Vol. II Table II-1 and sect. II.B.2.f); alternative TLD methods 13 MCi and 10 MCi; I-131 about 15 Ci in the text, 14.56 Ci cumulative (Table 11-3, to 8 May 1979), 32 Ci upper bound (Table 11-4) and 17 Ci (Table 11-5).
- Nuclide split of the 2.5 MCi (Table II-1; Bq = Ci x 3.7e10): Xe-133 $1.58\times10^{6}$ Ci = $5.85\times10^{16}$ Bq (0.63); Kr-88 $3.75\times10^{5}$ = $1.39\times10^{16}$ (0.15); Xe-135 $3.0\times10^{5}$ = $1.11\times10^{16}$ (0.12); Xe-133m $2.25\times10^{5}$ = $8.3\times10^{15}$ (0.09); Xe-135m $2.5\times10^{4}$ = $9.3\times10^{14}$ (0.01). Sum $2.505\times10^{6}$ Ci = $9.27\times10^{16}$ Bq.
- Kr-85: Rogovin says it was NOT released in significant quantities during the accident (small core inventory); the E002 and row 1665 notes say "some Kr-85", which should be dropped. About 50,000 Ci of Kr-85 remained in containment six months later (p.360); any later controlled venting is outside the Rogovin text and not covered.
- Release fractions of core inventory: Xe-133 1.58e6 / 1.42e8 = 1.1 %; I-131 15 / 6.55e7 = $2.3\times10^{-7}$. Core inventory at shutdown Xe-133 $5.25\times10^{18}$ Bq, I-131 $2.42\times10^{18}$ Bq; the generic in-core I-131 row (3.28e18 Bq/GW times about 0.96 GWe = about $3.1\times10^{18}$) is 1.3 times higher, consistent with a core only about three months at power.

Proposals for E002 and rows 1665/1666:
| Item | Old | New | Confidence |
|---|---|---|---|
| E002 central | $9.25\times10^{16}$ (2.5 MCi, "not retrieved") | unchanged; basis note: Rogovin best estimate, retrieved | high |
| E002 high | $1.48\times10^{18}$ (40 MCi, NRC letter) | $4.8\times10^{17}$ (13 MCi, Rogovin's TLD method; NRC 40 MCi kept as a note) | medium |
| E002 low | $3.7\times10^{16}$ (1 MCi) | unchanged | medium |
| Row 1665 Xe133 | all noble gas as Xe-133, $9.25\times10^{16}$ | Xe-133 alone $5.85\times10^{16}$ (low $2.3\times10^{16}$, high $1.9\times10^{17}$ by 0.63 x the E002 bounds); add Kr88+ $1.39\times10^{16}$, Xe135 $1.11\times10^{16}$; Xe-133m $8.3\times10^{15}$ and Xe-135m $9.3\times10^{14}$ need new minor groups (otherwise fold into Xe133, +$9.2\times10^{15}$, flagged as nuclide-mixing) | high on the split |
| Row 1666 I131 | $5.2\times10^{11}$ (14 Ci), $10^{11}$-$2\times10^{12}$ | $5.4\times10^{11}$ (14.56 Ci); low $1\times10^{11}$ kept; high $1.2\times10^{12}$ (32 Ci) | high |
Note the Table II-1 quantities are as released (decay in holdup included); "noble gas as Xe-133" in the TLD totals is an equivalence, not an activity sum.

### G-G Other
- ISL pond residue, mine water, waste rock (G4): no data in any supplied file.
- Reprocessing: SPERA abstract (Bollhofer et al.) states almost all atmospheric Kr-85 is emitted in the Northern Hemisphere from reprocessing (qualitative). Nothing quantitative for G1/G9.
- Hungarian isotope laboratory I-131 624 GBq in 2011 (SPERA abstract): isotope production, outside the nuclear power chain.

## 4. Per-paper contribution

| Paper | Contribution |
|---|---|
| NUREG/CR-2907 v27 | US effluent totals, medians, composition, long-term trend; corrects the noble-gas median cross-check; supports 16 proposals |
| CANTEACH 20031111 | CANDU 6 geometry, power, burnup (confirms 4,560 bundles, 2,061 MWth, 7,500 MWd/tU); not the bundle mass |
| Palleck et al. (external) | closes the bundle mass: 19.3 kg U |
| DOE LM fact sheet | tailings-as-fill quantities (2.2 Mt, 0.3 Mt, more than 4,000 properties); no activities |
| Rogovin | TMI-2 nuclide split, I-131 history, alternative source terms; corrects "some Kr-85" |
| Red Book 2003 and 2026 | ISL shares by country and era; no Table 7.3 exists in 2003 |
| SPERA 2012 | marginal (Kr-85 qualitative; S0429 text confirmed) |
| GGFR, EPA 402-R-93-078, EPA 402-R-93-003 | nothing for nuclear |

## 5. Gaps and contradictions
1. Magnox/AGR core data remain unsourced.
2. NUREG fleet GW a split is an assumption; blank = not detected biases sums low; C-14 values are licensee estimates.
3. The "particulates" US numbers cover four nuclides only; Mn-54, Cr-51, Nb-95 are unlisted, so the US-to-factor ratios (26-100) are minima.
4. Red Book 2003 country tables were identified by position; verify names. US by-method data are withheld after 2001.
5. Grand Junction activity is my assumption (ore grade), not a sourced value; national extrapolation rests on a tertiary count of vicinity properties.
6. TMI-2: the NRC letter figures (10 MCi consultants; 1-40 MCi) are not reconciled with Rogovin's own ranges (2.5, 10, 13 MCi); Rogovin text OCR has spaced digits, so the exponents of Table II-1 were read with care but should be eyeballed once (printed p.344).
7. Not retrievable here: Red Book 2022 (S0114) is superseded by 2026; Figure 1.6 of the CANTEACH deck.
