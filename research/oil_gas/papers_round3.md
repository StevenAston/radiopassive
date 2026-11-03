# Oil and gas factor gaps: round-3 paper extraction (PROPOSALS ONLY)

Researcher notes, 2 November 2026. Nothing in `data/`, `docs/`, `pipeline/` or existing research files was edited. Companion: `research/oil_gas/sources_round3.csv` (new S1250-S1263; corrections to S1209 and S1211). Activity only (Bq, Bq/t, Bq/m$^3$, TBq/(GW a)); every EPA and Johnson dose, risk, exposure-rate and health-effect result was ignored. Unit conversions used throughout: 1 pCi = 0.037 Bq, so 1 pCi/g = 0.037 Bq/g = $3.7\times10^{4}$ Bq/kg = $3.7\times10^{7}$ Bq/t and 1 pCi/L = 37 Bq/m$^3$; 1 ft$^3$ = 0.0283168 m$^3$; 1 bbl = 0.158987 m$^3$; at $0.286$ m$^3$ gas per kWh(th) each 100 Bq/m$^3$ delivered is 0.2507 TBq/(GW a) (round-2 convention). All arithmetic marked "mine" is my calculation; "inference" means it is not stated in the source.

## 0. Headline findings (read this first)

1. **The EPA file is the May 1991 DRAFT, not the 1993 report that S1209 cites, and its numbers differ.** The 1991 draft gives a national scale-plus-sludge generation of $8.3$ Mt per 20 years ($\approx0.41$ Mt/a), weighted Ra-226 155 and Ra-228 55 pCi/g (5.7 and 2.0 Bq/g), and **no scale/sludge mass split and no disposal-route percentages anywhere**. OGJ's 25,000 t/a scale and 225,000 t/a sludge come from a later 1993 draft that was not obtained; **OGJ does not state any concentration** (the 17.76 and 2.775 Bq/g in the old S1209 note are not on the page: unverified).
2. **Total solids Ra in the 1991 draft is 3.2 TBq/a (Ra-226 2.4, Ra-228 0.84), against 0.64 TBq/a (Ra-226 0.24 + Ra-228 0.40) from the current 1 % solids fraction at the 1990 US water volume.** The implied solids fraction is 10 % for Ra-226 and 2.1 % for Ra-228 (5 % for total Ra); the 1993 figure via OGJ is 1.7 %. The 1 % anchor sits below both EPA estimates. Proposal: central 1 % to 2 % (section 2.8).
3. **The 40/60 scale/sludge split is the 1993 activity split, not a mass split**: $25{,}000\times17.76=0.444$ TBq against $227{,}500\times2.775=0.631$ TBq gives 41 %/59 % (if the unverified concentrations are right). The 1991 draft points the other way (scale 63 % of bulk volume; scale-dominated activity, 70-90 %, under its own assumptions). Keep 0.4 as the central scale share but widen the band to 0.2-0.9.
4. **Johnson 1973 does not contain the "34 % retention" and does not support lowering delivered gas radon to 125 Bq/m$^3$.** Direct 1970s measurements at points of use average 23 pCi/L (851 Bq/m$^3$); Johnson adopts 20 pCi/L (740 Bq/m$^3$) for the US. Consumption-weighted over regions (my mapping) the burner concentration is about 410-860 Bq/m$^3$ (central about 550). A bottom-up chain (wellhead $\times$ Gesell retention $\times$ transit decay) gives about 170 Bq/m$^3$. The existing 300 Bq/m$^3$ sits at the geometric mean of the two (about 305). Recommendation: keep the central 300, extend the high to 1,000, mark confidence low-medium.
5. **The 0.48 "delivered fraction" has a plausible origin**: Johnson p.9 (citing Fries and Kilgren 1972) says LPG stripping removes 30-75 % of the radon, so 25-70 % is retained, midpoint 0.475 (inference; no source states 0.48).
6. **Gas-plant radon partition (Gesell Table 2-3) says most radon leaves the gas stream with NGL** (plant 1: 5 % methane, 74 % ethane, 18 % propane). The model has no NGL radon row (gap G3); a proposed row (section 5.3) would add roughly two-thirds of the delivered-gas radon again. Low confidence.
7. **Coal and uranium**: EPA 1991 fly-ash Ra-226 (3.9 pCi/g = 1.44e5 Bq/t) is 0.62 of the current central 2.33e5 Bq/t and inside the band; the US 1966-1987 ash-use series (12.1 % to 26.5 %) fills the 1966-1990 gap before coal:0074-0079; US uranium overburden (Ra-226 23.7 pCi/g = 877 Bq/kg, 3.1 Gt unreclaimed, 1949-88 total 3.97 Gt) sits just below the 1 Bq/g D21 threshold.

## 1. File identities, page mapping and OCR problems

| File | Identity | Notes |
|---|---|---|
| `Diffuse NORM Wastes Waste Characterization and Risk Assessment Draft.PDF` | S1250. SC&A, Rogers & Associates, Roy F. Weston for EPA ORP, **May 1991 DRAFT**, 478 PDF pages | OCR text `epa_diffuse_norm_1991.txt`: `=== PAGE nnn` is the PDF page number and starts the page. B.5 report page B-5-$n$ = PDF page $141+n$. |
| `EPA-520-1-73-004 - ...pdf` | S1251. Johnson, Bernhardt, Nelson, Galley, November 1973, 72 PDF pages | printed page = PDF page $-10$. Text layer good. |
| `gesell1975-OCCUPATIONAL...pdf` | identical file to `gesell1975.pdf` (same size, same text; S1211) | already read in round 2; Table 3 re-read here. |

**OCR and scan problems found (every number used was checked against the page image unless stated):**

| Where | Fault | Resolved value |
|---|---|---|
| p.B-5-16/17 (PDF 157-158) | Table title OCR'd "B.5-6" (it is B.5-5; real B.5-6 is the API exposure table) | Table B.5-5 |
| p.B-5-17 (PDF 158) TOTAL row | scale volume OCR "1,656" | **1,855 ft$^3$** (rows sum to 1,854.4); sludge 472; disposal volume as-is 35,004; equipment volume 6,964 ft$^3$ |
| p.B-5-20 (PDF 161) | right margin clipped in the scan ("Est mates", "ludge", "m (9,000 ft3)") | numbers readable on the image: 250 m$^3$ (9,000 ft$^3$) per 10-well facility, 620,000 wells, 30 %, 4.6 million m$^3$, 8.3 million MT, 1.8 MT/m$^3$ |
| p.B-5-4 | footer "B-6-4" | printing error for B-5-4 |
| Table B.5-4 (PDF 150) | column header says "Billion Cubic Feet" but 17,155,162 is **million** ft$^3$ (= 17.16 Tcf; Table B.5-2 says 17,150 Bcf for 1987) | 4.86e11 m$^3$ |
| Table B.4-2 (PDF 119) | "1990 17.0" | **77.0** Mt (image) |
| Table B.4-4 (PDF 124-125) | header reads "Percent of Production" but the columns sum to 100 % of the **used** tonnage (fly ash external 70.1 % + internal 29.8 %) | shares of utilised ash |
| Table B.1-2 (PDF 43-44) | "TAE+6" (1983), "1,.9E+6", "4,.7E+3" | 1983 surface 3.4E+6 (B.1-3 image) |
| Table D.2-2 (PDF 303) | uranium pile mass OCR 6.6E+07; O&G Th-228 and Ra-228 OCR "65 / 660" | image: 5.6E+07 MT; Th-228 55 and Ra-228 55 pCi/g |
| Gesell Table 3 | OCR scrambles rows | re-read from the page image (S1211 update) |

## 2. EPA 1991 draft, chapter B.5 (oil and gas scale and sludge)

### 2.1 Scope and definitions (p.B-5-1 to B-5-4, PDF 142-145)
- Covers scale, sludge, and contaminated equipment from **onshore US oil production equipment**; produced water and **offshore** solids are expressly excluded (p.B-5-3); gas-plant NORM is "described but not included" because it is Pb-210 plate-out with weak radon/gamma emission.
- The sizing rests on **crude-oil wells only** (620,181 in 1987, Table B.5-3, p.B-5-7 image-checked), although the sector is titled oil and gas. Gas wells (253,856; 17,155,162 MMcf in 1987, Table B.5-4) are not used for the volume.
- First US discovery: spring 1986, Mississippi workover, BaSO$_4$ scale with 6,000 pCi/g Ra-226 and 1,000 pCi/g Th-232 (p.B-5-2). This supports the project's 1985 era boundary in the fate rows 0053-0070.

### 2.2 Production rates, per-well and per-volume generation

| Quantity | Value | Page | Note |
|---|---|---|---|
| US oil production 1987 | 8.349 Mbbl/d (3.05e9 bbl/a = 4.84e8 m$^3$ = 4.16e8 t at 7.33 bbl/t) | Table B.5-1, p.B-5-5 | 1970 9.637, peak; EIA via Petroleum Independent |
| US marketed gas 1987 | 17,150 Bcf (4.86e11 m$^3$) | Table B.5-2, p.B-5-6 | peak 22,648 Bcf in 1973 |
| Producing wells 1987 | 620,181 oil; 253,856 gas | Tables B.5-3/4 | Texas 198,163 oil wells; stripper wells "may produce more water and bring more radium" (p.B-5-11) |
| Share of wells with NORM scale | "as many as one-third"; **30 %** used; Mississippi: half of wells, 10 % of those elevated | pp.B-5-15, B-5-20 | |
| Reference facility | 10 wells, 30-year life, tubing replaced every 7 y (three replacements), sludge emptied every 3 y | pp.B-5-15, B-5-16 | |
| Volume per reference facility | scale 1,855 ft$^3$ + sludge 472 ft$^3$ = 2,327 ft$^3$ (65.9 m$^3$) per cleaning/replacement cycle; **about 250 m$^3$ (9,000 ft$^3$) over 20 y** (p.B-5-20); "over 250 m$^3$ in a 30-year life" (p.B-5-16) | Table B.5-5 | 20 vs 30 years is inconsistent between p.B-5-16 and p.B-5-20 |
| Per contaminated well | $250/10/20=1.25$ m$^3$/(well a) = **2.25 t/(well a)** at 1.8 t/m$^3$; over all 620,000 wells 0.675 t/(well a) | mine | |
| National scale+sludge | $620{,}000\times0.30/10\times250/20=2.3\times10^{5}$ m$^3$/a = **0.42 Mt/a** | mine from p.B-5-20 | ES-5 (PDF 18) says "about **360,000 m$^3$ yearly**" (0.65 Mt/a): not reproducible from the chapter (see 2.9) |
| Per tonne of crude (1987) | 0.42 Mt/a / 4.16e8 t = **1.0 kg per t crude**; per m$^3$ oil 0.86 kg | mine | |
| UK analogue | 2 t scale/a for a 10,000 ft, 5.5 in well at 3,000 bbl/d; 850 UK wells give 1,000 t/a; scaled by oil output to the US gives **about 6,000 t/a** (scale only) | p.B-5-15 | roughly 70 times lower than the API-based figure |
| Retained-in-equipment character | about 96 % of the scale volume (1,783 of 1,855 ft$^3$) is in oil-line piping 1,228, water lines 263, production tubing 161, injection tubing 131; 94 % of the sludge volume (442 of 472 ft$^3$) is in the two oil stock tanks | Table B.5-5 | mine from the table |

### 2.3 Scale versus sludge split
- **The 1991 draft gives no mass split.** By bulk volume per cycle: scale 1,855 ($79\%$), sludge 472 (21 %). Over 20 years with 7-year and 3-year intervals (mine: $1{,}855\times20/7=5{,}300$ ft$^3$ and $472\times20/3=3{,}140$ ft$^3$; total 8,440 ft$^3$ against EPA's 9,000) scale is **63 %** and sludge 37 % of volume. One density (1.8 t/m$^3$) is applied to both, so the mass split equals the volume split.
- Concentration of sludge: "generally around 50 pCi/g" in heater-treaters and tanks (p.B-5-22). If the 210 pCi/g weighted total holds, scale would average $(210-0.37\times50)/0.63=304$ pCi/g and carry **about 91 %** of the Ra (inference; wide).
- **OGJ (1993 draft) activity split**: $25{,}000$ t $\times17.76$ Bq/g $=0.444$ TBq (scale) and $227{,}500$ t $\times2.775$ Bq/g $=0.631$ TBq (sludge): **41 % / 59 %**, which reproduces the project's 40/60. The two sources disagree on both mass (scale 10 % of mass in 1993, 63 % of volume in 1991) and activity (41 % against about 91 %). The 40/60 is therefore single-source and secondary.

### 2.4 Radionuclide concentrations (all pCi/g in the report; Bq/g in brackets)

| Statistic | Value (pCi/g; Bq/g in brackets) | Page | Quality |
|---|---|---|---|
| **Adopted generic (weighted)** | total Ra 210 (7.8); **Ra-226 155 (5.7)**, **Ra-228 55 (2.0)**; Pb-210 155, Po-210 155 (assumed equilibrium with Ra-226), Th-228 55 | p.B-5-23/24, ES-5, Table D.2-2 (PDF 303, image-checked) | derived by weighting gamma surveys by equipment and scale/sludge volume (Table B.5-5), conversion 1-5 pCi/g per $\mu$R/h above background; EPA itself says the data favour high sites |
| Gamma-survey distribution (6,274 readings; SCA88) | median **6 (0.22)**; mean **125 (4.6)**; 90th 250 (9.3); 99th 2,615 (97); maximum 37,500 (1,388) | p.B-5-23/24 | the only distribution; median is 20 times below the weighted value |
| 125 scale samples (Miller 1988) | 50-30,000, mean 5,484 (203) | p.B-5-22 | biased high (suspect areas) |
| UK scale | 10 to over 100,000; downhole 1,000-410,000 | p.B-5-22 | biased high |
| E&P Forum, 25 facilities | $<27$ to $>27{,}000$ | p.B-5-22 | |
| Industry guesses | Exxon 800-900 "may be common"; Chevron 20-25 more common, tank bottoms to 100, separators and heater-treaters to 600 | p.B-5-22 | speculation |
| Position in system | wellhead and nearby piping highest (up to tens of thousands); separators about 10 times lower; heater-treaters and sludge up to another factor 10 lower; separator granular deposits 1-1,000; sludge about 50 | pp.B-5-21/22 | |
| Ra-226:Ra-228 ratio | "nominal activity ratio about 3:1", Ra-228 not in equilibrium with daughters | p.B-5-14 | assumption, not a measurement |
| Maximum quoted | pipe scale "up to 40,000 pCi/g" (ES-5); 1986 Mississippi 6,000 Ra-226 plus 1,000 Th-232 | ES-5, p.B-5-2 | |
| Gas-plant deposits | Pb-210 plate-out, "invisible", on ethane/propane equipment | p.B-5-14 | qualitative |

In Bq per tonne of solids: weighted Ra-226 $5.7\times10^{6}$, Ra-228 $2.0\times10^{6}$; mean $4.6\times10^{6}$; median $2.2\times10^{5}$.

### 2.5 Handling and disposal: fate shares
No percentages exist in the 1991 draft. Qualitative content, usable only to support era boundaries:
- **Pre-1986**: pipes sent to cleaning yards, scale "stored on the ground at pipe cleaning yards or washed into the nearest pond or drainage basin", sludge placed in pits or lagoons, pipe given to schools (pp.B-5-18/19). EPA ERF surveys found soil above 1,000 pCi/g Ra-226 at yards.
- **After about 1986-89**: pipes measured; NORM piping and equipment "generally retained in controlled storage pending ... disposal regulations"; removed scale and sludge drummed and stored (p.B-5-19). Texas, Louisiana and CRCPD Part N rules drafted 1987-89.
- Generic future disposal: six regional facilities, 767,000 m$^3$ each (6 $\times$ 767,000 = 4.6 million m$^3$), 160,000 m$^2$, 4.8 m deep (p.B-5-30). Table D.2-2 gives instead 400 $\times$ 400 m, 4.5 m, 1.3 Mt per pile and **10** piles: internally inconsistent with 6 $\times$ 767,000 m$^3$.
- API/RAE (S1253) twelve disposal alternatives: not obtained.
- Supports the existing rows 0053-0070 qualitatively (dispersed before 1985, impounded storage after). No number changes.

### 2.6 Twenty-year volumes (p.B-5-20)
4.6 million m$^3$ = 8.3 million t over 20 years (about 1988-2008), **assuming constant well numbers**. By the 6-facility case 767,000 m$^3$ each. This is a generation projection, not an inventory; the equipment-retained part is included.

### 2.7 Radon emanation (p.B-5-24)
"No readily available information"; emanation coefficient **0.1** assumed (RAE88), lower than soils (0.2-0.4). The project's proposals (scale 0.088 from White and Rood; sludge 0.15) bracket this. No flux data. Table D.2-2: 4.5 m thick unvegetated pile, density 1.8 g/cm$^3$.

### 2.8 Mass balance against the current factors (US, about 1987-90) and solids-fraction proposal

US 1990 produced water (project value) $3.96\times10^{9}$ m$^3$: Ra-226 $3.96\times10^{9}\times6{,}000=23.8$ TBq; Ra-228 $\times10^{4}=39.6$ TBq. Solids at the current 1 % total: Ra-226 0.24 TBq, Ra-228 0.40 TBq.

| Estimate | Ra-226 (TBq/a) | Ra-228 (TBq/a) | Total Ra | As fraction of outlet-water Ra |
|---|---|---|---|---|
| EPA 1991 draft, $8.3\text{ Mt}/20$ at 5.74 / 2.04 Bq/g | 2.38 | 0.84 | 3.22 | **10.0 %** Ra-226; **2.1 %** Ra-228; **5.1 %** total |
| EPA 1991 ES-5 volume (360,000 m$^3$/a, 0.65 Mt) | 3.72 | 1.32 | 5.03 | 15.6 %; 3.3 %; 7.9 % |
| EPA 1993 via OGJ (S1209; concentrations unverified) | n/a | n/a | 1.07 | 1.7 % total |
| Current factors (1 %) | 0.24 | 0.40 | 0.64 | 1.0 % |

Caveats: EPA concentrations come from gamma surveys at sites chosen for elevated readings (EPA's own warning, pp.B-5-22, B-5-29); the generation rate is scaled from a hypothetical 10-well facility; the base year is about 1987, the water value is 1990; solids include sludge from tank cleaning, which can carry non-radium-bound activity. Because the solids fraction is relative to **outlet** water (post-precipitation), a value above 1 is physically possible.

**Proposed change (O1).** Rows oil_gas:0047-0050.

| Row | old low / central / high | new low / central / high | Confidence | Independence from UNSCEAR 2016 Annex B |
|---|---|---|---|---|
| 0047, 0049 scale, Ra-226 and Ra-228 | 0.0004 / 0.004 / 0.016 | 0.0004 / **0.008** / 0.04 | low-medium | independent (UNSCEAR gives no solids fraction); NOT independent of the 1993 anchor already in the 1 % |
| 0048, 0050 sludge | 0.0006 / 0.006 / 0.024 | 0.0006 / **0.012** / 0.06 | low-medium | as above |
| total | 0.001 / 0.01 / 0.04 | 0.001 / **0.02** / 0.10 | | geometric mean of 1.7 % (1993) and 5.1 % (1991), shaded down for site bias; the 1991 Ra-226 value (10 %) is the new high |

If the orchestrator prefers to keep the 1993-anchored 1 %, the minimum change is to raise the highs to 0.04 and 0.06.

**O2 scale share.** Keep the central 0.4 scale / 0.6 sludge split of the total; add a band of scale share 0.2-0.9 (1993: 0.41; 1991 implied 0.9). Confidence: low.

**O3 Ra-228:Ra-226 in solids.** EPA's solids ratio is 0.35 (55/155, the nominal "3:1" is an assumption, not an assay), whereas the model's equal solids-bound fractions carry the water ratio (USA 1.67, world 0.8), i.e. 2.3-4.8 times higher. In the totals above the model's Ra-228 (0.40 TBq/a) is 0.47 of the EPA 1991 figure (0.84), while its Ra-226 (0.24) is only 0.10 of EPA (2.38): the 1991 draft implies a far lower Ra-228:Ra-226 in solids than the model. No change proposed (EPA ratio unmeasured); flag for the produced-water Ra-228 centre (rows 0004-0005).

**O4 retained-scale fraction $\phi$ (row 0078).** The EPA table puts 96 % of scale volume in piping, tubing and lines that stay in place until replaced (about every 7 years) and 94 % of sludge in tanks that are emptied every 3 years, so scale is mostly retained on equipment and sludge is all removed (consistent with the model's $S(1-\phi)$ for scale and $S$ for sludge). Proposal: $\phi$ from 0.2 / 0.5 / 0.8 to **0.6 / 0.9 / 0.97**; confidence low-medium (volume of deposit, not activity; 7-year interval is a US 1980s practice). Independence: independent.

**O5 Pb-210 at formation (0051-0052).** EPA assumes Pb-210 = Ra-226 (equilibrium) for aged scale; that describes the 20-year inventory after ingrowth, not formation. No change.

**O6 emanation.** EPA 0.1 supports the proposed og_scale 0.037 / 0.088 / 0.14 and og_sludge 0.05 / 0.15 / 0.25 (both bracket 0.1). No change; confidence high that no measured flux exists in EPA.

### 2.9 Contradictions inside the 1991 draft (for the orchestrator)
1. ES-5 annual 360,000 m$^3$ versus chapter-derived 230,000 m$^3$/a (4.6e6/20). The ratio 4.6e6/360,000 = 12.8 years has no stated meaning.
2. 250 m$^3$ per facility is "30-year life" on p.B-5-16 and "20-year period" on p.B-5-20; my reconstruction (8,440 ft$^3$) fits the 20-year reading.
3. Six regional disposal facilities (p.B-5-30) versus ten reference piles (Table D.2-2).
4. 6,000 t/a (UK analogy, scale only, p.B-5-15) versus 0.42 Mt/a (API-based): a factor 70, unreconciled in the text.
5. IAEA TRS-419 (round 2): about 100 t scale per NORM well per year, which is 44 times the EPA 2.25 t per contaminated well per year. Unresolved; scope differs.

## 3. Johnson et al. 1973 (EPA-520/1-73-004): radon in natural gas by region

All Bq/m$^3$ = pCi/L $\times$ 37; values at STP as published.

### 3.1 Wellhead (Table 1, p.5; PDF 15)
| Area | Average (pCi/L) | Range | Bq/m$^3$ (average) |
|---|---|---|---|
| SW Colorado and NW New Mexico (San Juan) | 25 | 0.2-160 (Bunce and Sattler, over 300 wells) | 925 |
| Texas, Kansas, Oklahoma | $<100$ | 5-1,450 (1,250 wells, Barton) | $<3{,}700$ |
| Texas Panhandle | n/a | 10-520 (about 500 wells, Faul) | n/a |
| Colorado (Rulison) | 25.4 | 11-45 | 940 |
| Gasbuggy area | 15.8-19.4; trunk lines 29.4 | 12-59 | 585-720; 1,090 |
| California | n/a | 1-100 | n/a |
| Gulf Coast (Louisiana, Texas) | **5** | n/a | **185** |
| Kansas | **100** | n/a | **3,700** |
| Wyoming | 10 | n/a | 370 |
| **Overall (unweighted)** | **37** | | **1,369** |

Johnson states that a production-weighted national average **cannot be computed** (p.7): the Gulf Coast (about 5 pCi/L) supplies 40-60 % of US gas, and the high-radon regions (Texas, Kansas, Oklahoma, California at up to about 100 pCi/L) only 15-20 %. My bounds: $0.15\times100+0.85\times5=19$ pCi/L to $0.20\times100+0.80\times25=40$ pCi/L, i.e. **710-1,480 Bq/m$^3$, central about 800** (inference). The existing 625 Bq/m$^3$ (16.9 pCi/L) is a little below this.

### 3.2 Processing, transmission, storage (pp.7-11)
- 55-98 % methane at inlet; LPG stripping "can remove **30 to 75 %** of the radon" (Fries and Kilgren 1972); radon boils between ethane and propane and follows the LPG (Table 3, p.9).
- LPG data: Houston retail annual means **25-180 pCi/L** (six retailers); maximum 287-1,288 pCi/L (Texas, California) and 1.9-119 (other southern states); a New Mexico plant: inlet **56** to propane **1,100 pCi/L** (ratio 19.6; Gesell's slope is 8.2). Units for LPG are as printed; liquid or vapour basis not stated.
- Transit 10-12 miles/h; 1,500 miles = 1-2 half-lives (3.83 d); mixing: San Juan gas from over 6,000 wells; storage 330 reservoirs with 5.6 Tcf (29 % of 1971 marketed production); LNG 0.34 %. Radon decay and dilution before the burner are acknowledged but not quantified; "farm taps" take unprocessed gas.

### 3.3 Distribution lines near points of use (Table 4, p.14; PDF 24)
| Area | Average (pCi/L) | Range | Bq/m$^3$ |
|---|---|---|---|
| Chicago | 14.4 | 2.3-31.3 | 533 |
| New York City | 1.5 | 0.5-3.8 | 56 |
| Denver | 50.5 | 1.2-119 | 1,869 |
| West Coast | 15 | 1-100 | 555 |
| Colorado | 25 | 6.5-43 | 925 |
| Nevada | 8 | 5.8-10.4 | 296 |
| New Mexico | 45 | 10-53 | 1,665 |
| Houston | 8 | 1.4-14.3 | 296 |
| **Overall** | **23** | | **851** |

Johnson's choices for the US at point of use: **20 pCi/L (740 Bq/m$^3$)**, possible variation 10-100; Barton et al. suggested 10 (370 Bq/m$^3$); 50 pCi/L (1,850 Bq/m$^3$) for users near the Kansas, Colorado, New Mexico and Texas Panhandle fields (pp.13, 36).

### 3.4 Consumption-weighted radon at the burner (1971 US; my inference)
Division shares of 1971 consumption (Table 2, p.6; image-checked; total 20,268,303 MMcf): New England 1.11 %, Middle Atlantic 8.28, East North Central 18.14, West North Central 8.96, South Atlantic 6.79, East South Central 5.19, West South Central 34.83, Mountain 5.71, Pacific 10.97.

| Mapping of Table 4 to divisions (assumption) | Weighted mean (pCi/L) | Bq/m$^3$ |
|---|---|---|
| A: NE, MA, SA = New York 1.5; ENC = Chicago 14.4; WNC = mean(Chicago, Denver) 32.5; ESC, WSC = Houston 8; Mountain = mean(Denver, Colorado, NM, Nevada) 32.1; Pacific = West Coast 15 | 12.4 | 460 |
| B: as A but South Atlantic = mean(NY, Houston), WNC = Chicago | 11.0 | 410 |
| C (high): WSC 25, WNC 50.5, SA, ESC, MA 14.4, NE 8 | 22.3 | 826 |
| Johnson's own two-level rule (50 near-field in Kansas, Colorado, NM = 5.55 % of consumption plus 0-5 % for the Panhandle, 20 elsewhere) | 21.7-23.2 | 800-860 |

Result: **410-860 Bq/m$^3$, central about 550 Bq/m$^3$ (15 pCi/L)** for 1971. National delivered radon at 20 pCi/L on 1971 consumption ($5.74\times10^{11}$ m$^3$) is $425$ TBq; at 15 pCi/L 320 TBq; at 11 pCi/L 235 TBq. Per GW a: 550 Bq/m$^3$ is 1.38 TBq/(GW a).

### 3.5 Time and scope caveat
All of Johnson's measurements are 1964-1973. US gas supply has since shifted to Gulf offshore, Rockies, and Marcellus; the existing single 1900-2025 factor row cannot represent that. Johnson's "20 pCi/L" is a conservative dose-assessment assumption, so the direct Table 4 data (average 23, median region 15) are the better evidence.

## 4. Gesell 1975: gas-plant partition (S1211; Table 3 re-read from the page image)

| Plant | Inlet (pCi/L) | Sales methane | Ratio sales/inlet |
|---|---|---|---|
| 1 | 10.5 | 0.6 | 0.057 |
| 2 | 26.3 | 13.6 | 0.517 |
| 3 | 78.4 | 3.2 | 0.041 |
| 4 | 119 | 93.6 | 0.787 |
| 5 | 35.4 | 3.1 | 0.088 |
| 6 | 18.4 | 0.9 | 0.049 |
| 7 | 4.3 (mean of 2.9, 5.0, 5.0) | 1.1 | 0.256 |
| 8 | 1.25 (1.0, 1.5) | 0.7 | 0.560 |
| 9 | 28.6, 41.3, 17.3, 28.6 | no sample | n/a |

Over eight plants: **mean 0.29, median 0.17, concentration-weighted 0.40** (sum of sales over sum of inlet; mine), range 0.04-0.79. Ratios are of concentrations, ignoring shrink (volume lost to NGL), so they slightly overstate the activity fraction left in sales gas. Plants 2 and 4 (ratio 0.5-0.8) appear not to strip radon efficiently.

**Plant 1 activity balance (Table 2; p.683):** inlet 53.3 mCi/d (498,298 lb-mol/d at 10.5 pCi/L); methane 2.9 (**5.4 %**), ethane 39.2 (**73.5 %**), propane 9.6 (**18.0 %**), butane 0.06 (0.1 %); sum 51.8 mCi/d (97.2 % closure). Propane radon $\approx8.2\times$ inlet (r = 0.94, eight plants). US had 805 processing plants in 1972 (Cannon).

Gesell's wellhead Table 1 (p.682): Ontario mean 169, Alberta 62, British Columbia 473 pCi/L (1918); Texas Panhandle about 100 (maximum 1,450); San Juan 24.6 and 16.4 pCi/L. US means "do not exceed about 100 pCi/L".

## 5. Gas radon proposals and benchmarks

### 5.1 Chain and direct estimates compared
| Route | Calculation | Bq/m$^3$ |
|---|---|---|
| Existing | 625 (wellhead) $\times$ 0.48 | 300 |
| Round-2 proposal | 625 $\times$ 0.29 $\times$ 0.7 | 125 |
| Bottom-up, Johnson wellhead 1,369 (unweighted) | $\times$ retention 0.29 / 0.40 / 0.475 (Gesell mean, conc.-weighted, Johnson midpoint) $\times$ transit and storage 0.6 | 238 / 329 / 390 |
| Bottom-up, my production-weighted wellhead 800 | $\times$ 0.35 $\times$ 0.6 | 168 |
| Top-down direct, Johnson Table 4 overall | 23 pCi/L | 851 |
| Top-down direct, Johnson recommended | 20 pCi/L | 740 |
| Top-down direct, consumption-weighted (3.4) | 11-23 pCi/L | 410-860 (central 550) |
| Houston (Gesell/Johnson) | 8 pCi/L | 296 |

The round-2 proposal of 0.20 delivered fraction survives as a **bottom-up** estimate ($0.35\times0.6=0.21$), but applied to the lower 625 wellhead it gives 125-130 Bq/m$^3$, 2-4 times below every direct 1970s end-use measurement outside the Gulf coast and New York. The two routes differ by a factor 3.2 (170 against 550); the geometric mean is 306 Bq/m$^3$, which is the existing central value.

### 5.2 Factor proposals (old to new)
| ID | Factor | Old low / central / high | New | Confidence | Independence from UNSCEAR 2016 Annex B | Basis |
|---|---|---|---|---|---|---|
| G1 | oil_gas:0074 delivered Rn-222, Bq/m$^3$ of gas produced | 47.6 / 300 / 779 | **50 / 300 / 1,000** (centre unchanged; high raised to cover Johnson Table 4 average 851 and Denver 1,869 only as a site, not a mean) | low-medium | partial: UNSCEAR 2016 draws on the same 1970s US surveys; Johnson/Gesell were read there only via S0001/S0318 before | Johnson Table 4, p.36; Gesell Table 3 |
| G2 | wellhead Rn (gap register; 625 Bq/m$^3$) | 625 | **800** (low 185 Gulf Coast, high 3,700 Kansas mean) | low | partial | Johnson Table 1, p.7 (my production weighting) |
| G3 | delivered fraction (0.48) | 0.48 | do not replace by 0.20 alone; report as **0.2 (bottom-up) to 0.7 (top-down, 550/800)**, central 0.375 (= 300/800; the geometric mean of 0.21 bottom-up and 0.69 top-down is 0.38) | low | partial | sections 5.1 |
| G4 | benchmark B1 (existing: Gesell 34 % $\times$ Johnson 1,370 = 466 Bq/m$^3$ = 1.17 TBq/(GW a)) | 466; 1.17 | **replace**: the 34 % is not in either paper. New independent benchmark: Johnson direct delivery 410-860 Bq/m$^3$ = 1.0-2.2 TBq/(GW a); bottom-up 238-390 Bq/m$^3$ = 0.6-1.0 TBq/(GW a). Stream 0.75 TBq/(GW a) lies inside the combined range 0.6-2.2, ratio 0.35-1.25 | low-medium | independent in method and era; shares the US 1970s data root with UNSCEAR | sections 3.4, 5.1 |
| G5 | national check, US 1971 delivered Rn | none | 235-490 TBq (at 11-23 pCi/L) against stream-equivalent $300\times5.74\times10^{11}=172$ TBq: ratio 0.35-0.73 | low | partial | Johnson Table 2 and 4 |

### 5.3 New row proposal: radon in NGL/LPG (closes gap G3 of the factor notes)
Gesell plant 1 sends 91.5 % of the inlet radon activity to ethane and propane and 5.4 % to methane; mean sales/inlet concentration ratio is 0.29, so on average about 70 % of the radon is diverted from the sales gas. NGL radon is not in the model. Proposal (inference, low confidence):

$$A_{\mathrm{NGL}}=C_{\mathrm{wh}}\,f_{\mathrm{div}}\,f_{\mathrm{surv}}$$

per m$^3$ of gas produced, with $C_{\mathrm{wh}}=800$ (185-1,480) Bq/m$^3$, $f_{\mathrm{div}}=0.5$ (0.25-0.8; Gesell conc.-weighted 0.60, Johnson 0.25-0.70, shrink ignored) and $f_{\mathrm{surv}}=0.5$ (0.2-0.9; decay in plant, storage and distribution of LPG; Houston retail means 25-180 pCi/L show survival to the retailer). Central about **200 Bq/m$^3$** (low 10, high 1,000), tier liberated, `air_delivered_gas` or a new `air_delivered_ngl`; that is about two-thirds of the delivered-gas row and would raise the total radon at burners by 67 %. Requires no NGL volume series if expressed per m$^3$ of gas produced. Independence: independent of UNSCEAR 2016 (not covered there).

### 5.4 Gas-plant Pb-210 (row 0076) and equipment
Gesell and EPA give only qualitative evidence (plate-out on pump and reflux-line interiors; EPA Table B.5-6 exposure rates: reflux pumps median 76 $\mu$R/h, propane pumps 31, production lines 35; no Bq). No change to oil_gas:0076.

## 6. EPA 1991, chapter B.4 (coal ash) against the coal factors

### 6.1 US ash production, utilisation and disposal (pp.B-4-1 to B-4-16, PDF 114-130)
- **1987**: ash (fly + bottom + slag) **62.55 Mt**: fly 45.0, bottom 13.0, boiler slag 3.7; FGD sludge 12.89 Mt (separate) (p.B-4-7 image-checked). Type split of the 1984 base case 74 / 20 / 6 % (EPA88). Average ash content of coal burned 10.5 % (1985), down from about 14 % in 1975; range 5.9-29.4 %. 20-year projection 2,000 Mt (fly 1,480, bottom 400, slag 120); 1990 projection 77 Mt, 2000 100 Mt, 2010 120 Mt.
- **Disposal**: "70-80 % of ash is disposed in impoundments and landfills on or off site" (p.B-4-8); 305 off-site and about 900 on-site facilities (EEI 1989).
- **Utilisation 1987 (Table B.4-4, p.B-4-11/12, image-checked)**: 16.6 Mt of ash used = **26.5 %** (fly 10.0 of 45.0 = 22.2 %; bottom 4.3 of 13.0 = 33 %; slag 2.2 of 3.7 = 59 %); sludge 0.926 Mt of 12.89 = 7.2 %. **External markets 11.2 Mt (17.9 % of production)**; **internal utility use 5.4 Mt (8.7 %)**: "miscellaneous" 17.3 % of used fly ash and 29.7 % of used bottom ash plus structural fills. Cement/concrete uses 57.3 % of used fly ash (5.7 Mt, 9.2 % of production). **Mine application: fly 0.7 %, bottom 7.8 % of used (0.07 + 0.34 = 0.41 Mt = 0.65 % of production)**, so reisolated by mine backfill is about 0.007 of ash in 1987.
- **Utilisation series, % of production (Table B.4-5, p.B-4-16):** 1966 12.1; 1967 13.5; 1968 17.6; 1969 15.3; 1970 13.0; 1971 20.1; 1972 16.3; 1973 16.3; 1974 14.6; 1975 16.4; 1976 20.0; 1977 20.7; 1978 24.1; 1979 21.0; 1980 18.7; 1981 24.0; 1982 20.7; 1983 20.0; 1984 23.1; 1985 27.4; 1986 21.7; 1987 26.5. **Production series, Mt (Table B.4-2, p.B-4-6):** 1966 22.9; 1970 35.6; 1975 54.4; 1980 60.2; 1985 59.1; 1987 62.5 (full series in the file). Regional 1984 utilisation of fly ash 15.8-35.8 % (Table B.4-3). Mean 1966-87 utilisation about 19.5 % (mine).

### 6.2 Radionuclide concentrations (p.B-4-18/19; weighted 80 % fly, 20 % bottom/slag)

| Nuclide | EPA 1991 weighted (pCi/g) | Bq/t | Current coal factor (fly ash, low / central / high Bq/t) | EPA / central |
|---|---|---|---|---|
| Ra-226 | 3.7 (fly 3.9; bottom/slag 3.1; ES-1 table) | 1.37e5 (fly 1.44e5) | 7.42e4 / 2.33e5 / 4.92e5 (coal:0013) | **0.59-0.62** |
| U-238 and U-234 | 3.3 | 1.22e5 | 5.83e4 / 2.33e5 / 3e5 (coal:0007, 0009) | 0.52 |
| Th-230 | 2.3 | 8.5e4 | 5.83e4 / 2.33e5 / 3e5 (coal:0011) | 0.37 |
| Th-232 | 2.1 | 7.8e4 | 3.42e4 / 1.67e5 / 2.5e5 (coal:0021) | 0.47 |
| Ra-228 | 1.8 | 6.7e4 | 3.42e4 / 1.67e5 / 2.5e5 (coal:0023) | 0.40 |
| Th-228 | 3.2 | 1.18e5 | 3.42e4 / 1.67e5 / 2.5e5 (coal:0025) | 0.71 |
| Pb-210 | 6.8 | 2.52e5 | 1e5 / 1.67e5 / 6.5e5 (coal:0015) | 1.5 |
| Po-210 | 7.0 | 2.59e5 | 2.75e4 / 1.67e5 / 4.33e5 (coal:0017) | 1.6 |
| U-235 | 0.16 | 5.9e3 | 2.69e3 / 7.68e3 / 1.38e4 (coal:0019) | 0.77 |
| K-40 | not given | n/a | 2.5e5 / 4.17e5 / 1.2e6 | n/a |

EPA inputs: Beck 1980 (1,000 US coals, arithmetic mean U-238 0.6, Th-232 0.5 pCi/g; geometric means 0.34, 0.26), UNSCEAR 1982 (fly ash U-238 5.4, Th-232 1.9 pCi/g; enrichment 1.3-1.4 for U and Th, up to 2 for Ra-226 and 5-11 for Po-210 and Pb-210 in escaping fly ash), and others. These are US 1970s-80s data and derive partly from UNSCEAR 1982, so they are **partially independent of UNSCEAR 2016**. Radon: emanation coefficient **4 %** (0.7-9.8 %, Kalkwarf; fly ash about 2 % in Beck, soil 15 %; p.B-4-20), which supports the current coal_fly_ash $\varepsilon_{\mathrm{Rn222}}$ 0.005 / 0.03 / 0.15 (no change). Cross-check of the US ash Ra-226 inventory: $62.55\text{ Mt}\times1.37\times10^{5}$ Bq/t = 8.6 TBq in 1987 against the factor central $62.55\times2.33\times10^{5}=14.6$ TBq (ratio 0.59).

### 6.3 Proposals (coal stream; for the coal owner to adopt or reject)
| ID | Item | Old | New | Confidence | Independence |
|---|---|---|---|---|---|
| C1 | US-specific ash Ra-226 (a cross-check or USA override) | XWL fly ash 7.42e4 / 2.33e5 / 4.92e5 | USA 1980s central 1.44e5 (fly) and 1.15e5 (bottom/slag); keep the XWL band; no change to XWL | medium for US 1980s coals; low for world | partial (UNSCEAR 1982 root) |
| C2 | USA route shares before 1991 (coal:0074-0079 start in 1991) | none | USA 1966-1990 dispersed (utilised) share = EPA series above, central linear 0.12 (1966) to 0.27 (1987), held 0.25 for 1988-90, band $\pm0.05$; impounded = 1 - dispersed - reisolated; reisolated 0.005 (0-0.01) | medium | independent (ACAA 1966-87 data via EPA; S1258) |
| C3 | reisolated (mine backfill) USA 1987 | coal:0075 0 / 0 / 0.06 | central 0.005 | low | independent |
| C4 | dispersed versus on-site internal use | single dispersed row | note: 33 % of 1987 "utilised" ash (5.4 of 16.6 Mt) was internal utility use (fills, misc.), which behaves like impounded/near-site placement; if the model counts only external markets, USA 1987 dispersed is 0.18 not 0.265 | low | independent |
| C5 | US ash tonnage cross-check for the ash drivers | none | 1987 62.55 Mt (fly 45.0); series above (S1258/S1250) | medium | independent |

Existing coal:0074 (1991-2009 impounded 0.67) is consistent with the 1987 disposal share of 0.735 and the ACAA 22 % (1992-93) noted in the coal notes.

## 7. EPA 1991, chapter B.1 (uranium mining overburden): input to the nuclear G4 memo

### 7.1 Tonnage (pp.B-1-2 to B-1-11, PDF 41-50)
- **Ore production** (EIA, Table B.1-2): peak 1980 **15.2 Mt** (9.4 surface, 5.8 underground); 1988 1.1 Mt (0.63 + 0.47). U$_3$O$_8$ from these mines 1980 18.1 kt. Ore grade 1978-87 mean **0.162 %** U$_3$O$_8$ (0.112-0.336 %); modern mining targets 0.03 % cut-off. Heap leach, in-situ and mine-water methods about 20 % of production by 1988 and generate little overburden. 3,592 mines in 18 states (1,305 surface, 2,287 underground).
- **Overburden ratios** (Table B.1-3 notes): surface mines 10:1 (1948-60), 25:1 (1961-70), 40:1 (1971-80), 60:1 (1981-88); range 10:1 to 80:1 (EPA 1983 assumed 50:1; reference mine 50:1, 1.1 Mt ore gives 55 Mt waste). Underground 1:3 (1948-70) and 1:1 (1971-88); range 1:20 to 1:1.
- **Overburden generated** (Table B.1-3, image-checked totals): 1949-88 **3.9E+9 t surface + 6.9E+7 t underground = 3.97 Gt**; 1969-88 3.5E+9 + 5.3E+7; 1979-88 2.0E+9 + 2.5E+7. Peak year 1981: 4.6E+8 t surface + 4.7E+6 underground. 1985-88 average about 37 Mt/a (ES-2). Years 1987-88 ore in B.1-3 (7.4E+5, 5.6E+5; 6.3E+5, 4.7E+5) differ from B.1-2 (9.3E+5, 6.8E+5; 6.4E+5, 6.0E+5): internal inconsistency of 20-30 % in the last two years.
- **Unreclaimed inventory 3.1 Gt** (80 % of all overburden since 1948; Class II reclamation counted as half); 20-year projection **740 Mt**; reference pile 5.6E+7 t (28 million m$^3$ at 2.0 g/cm$^3$). Only 6 % of mining land reclaimed by 1971.

### 7.2 Concentrations and radon (pp.B-1-19 to B-1-21, PDF 58-60; SCA89 field data, five states, 25 mines)
- **Ra-226 23.7 pCi/g = 0.877 Bq/g = 877 Bq/kg** (area-weighted; range about 3 to several hundred pCi/g at the ore-overburden interface; background 1-7). In the 58-sample EPA study 69 % of samples were $\ge5$ pCi/g and 50 % $\ge20$ pCi/g. U-238, U-234, Th-230 in equilibrium with Ra-226 (23.7 each); U-235 1.2; **Pb-210 = Po-210 = 16.6 pCi/g** (0.7 $\times$ Ra, from emanation 0.3); Th-232 chain 1.0 pCi/g (background). Older EPA 1983 figure: waste rock U-238 6.0 and Th-232 1.0 pCi/g.
- **Radon**: emanation coefficient 0.1-0.5 (0.3 adopted, sandstone); field flux averaged over 25 mines **11.1 pCi/m$^2$/s = 0.41 Bq/m$^2$/s** (range 2-60 pCi/m$^2$/s = 0.07-2.2 Bq/m$^2$/s; low-grade ore to a few hundred); background 0.6-5.0 pCi/m$^2$/s (0.02-0.19 Bq/m$^2$/s).

### 7.3 Activity arithmetic (mine; all at 877 Bq/kg Ra-226 unless noted)
| Quantity | Tonnes | Ra-226 (TBq) |
|---|---|---|
| 1985-88 annual rate | 3.7e7 t/a | 32 TBq/a |
| 1981 peak year | 4.65e8 t | 407 TBq |
| 1949-88 total | 3.97e9 t | 3,480 TBq (3.5 PBq) |
| Unreclaimed inventory | 3.1e9 t | 2,720 TBq |
| 20-year (1969-88) | 3.55e9 t | 3,120 TBq |

### 7.4 Proposals for nuclear gap G4 (waste rock memo) and the residue parameters
| ID | Item | Proposal | Confidence | Independence |
|---|---|---|---|---|
| N1 | u_waste_rock Rn-222 $\varepsilon$ (blank in residue_types.csv) | **0.1 / 0.3 / 0.5** (emanation coefficient, D60 convention; EPA/NRC84 sandstone) | medium | independent of UNSCEAR |
| N2 | u_waste_rock Rn-220 $\varepsilon$ | no proposal: Th-232 chain at background 1 pCi/g (0.037 Bq/g) | low | |
| N3 | Ra-226 in overburden (memo activity) | low 185 Bq/kg (5 pCi/g) / central **877** / high 7,400 (200 pCi/g interface material; EPA says "several hundred") | medium for the central (US, five states) | independent |
| N4 | tonnage per tonne of ore | surface 10 / 25 / 40 / 60 t per t ore by era; underground 0.33 then 1.0; US-only; no world analogue | medium (US), none (world) | independent |
| N5 | D21 classification | the EPA mean (0.877 Bq/g) is just **below** the 1 Bq/g threshold (27 pCi/g); 50 % of samples were at or above 20 pCi/g (0.74 Bq/g), so some overburden exceeds it. Recommend the orchestrator rule that US overburden stays in the memo series unless the mineralised fraction is quantified | n/a | |
| N6 | radon flux check | field mean 0.41 Bq/m$^2$/s sits below the 40 CFR 192 cap of 0.74 Bq/m$^2$/s; use as an ex-post check of $\varepsilon$ and H, not as a flux input | high | |

Seepage: no uranium-overburden leach data in EPA 1991. The generic M1 triple remains the only value.

## 8. Other material directly usable by other streams

- **Geothermal (EPA B.8, pp.B-8-15 to B-8-20; for the `other` stream).** Imperial Valley (flash/binary, hypersaline) filter cake about **20,000 m$^3$/a** (ERC 1990; assumed to double to 40,000 for the 20-year 800,000 m$^3$ = 1.4 Mt, density 1.75 t/m$^3$). Concentrations from six samples at four plants: **Ra-226 10-254, volume-weighted 160 pCi/g (5.9e6 Bq/t); Ra-228 9-193, weighted 110 pCi/g (4.1e6 Bq/t)**; Pb-210 and Po-210 about 110 (4.1e6 Bq/t); Th-228 about 30 (1.1e6 Bq/t); Ra-226 emanation about 25 %. Mass: $20{,}000\times1.75=3.5\times10^{4}$ t/a, giving Ra-226 0.21 TBq/a and Ra-228 0.14 TBq/a (mine). Compare other:0004-0006 (central 250 t/(GW a); Ra-226 3.7e5 Bq/t, Ra-228 1.1e5 Bq/t): EPA Ra-226 is 16 times and Ra-228 37 times the centre but inside the band (high 1.34e7); the Imperial plants (about 190 MW listed 1987, Table B.8-2) give roughly $3.5\times10^{4}/(0.19\times0.7)\approx2.6\times10^{5}$ t/(GW a), above the current high of 6.1e4 t/(GW a) (capacity factor 0.7 assumed; filter cake is wet). Radon flux from an uncovered cell 160 pCi/m$^2$/s (5.9 Bq/m$^2$/s), 80 with interim cover, under 20 with a 3 m cover (RAE model, not measurement). Confidence low (single EIR, hypersaline field only); the EIR may be the same data as S1400. Flag for the `other` owner; I recommend adding the filter-cake mass per GW a as a second high-side point rather than changing the centre.
- **Phosphate and fertiliser (EPA ES, B.2-B.3; not an energy stream, for baselines only):** phosphogypsum about 40 Mt/a since 1984, stock 8 Gt, Ra-226 33 pCi/g (1.2 Bq/g); fertiliser 4.8 Mt/a, 8.2 pCi/g (0.30 Bq/g); water-treatment waste 3.1 Mt/a; metal mining waste about 1 Gt/a (B.7). Not extracted further.
- **API NORM survey statistics (Table B.5-6)**: exposure rates only; no Bq. Ignored.

## 9. Gaps, discrepancies and where to look

| # | Item | Status | URL or action |
|---|---|---|---|
| E1 | EPA 1993 final/draft report (402-R-93-083) behind OGJ's 25,000 + 225,000 t/a | not obtained; web search found no copy | EPA NEPIS (https://nepis.epa.gov, search "Diffuse NORM Wastes" or 402R93083); EPA TENORM O&G page snapshot https://19january2021snapshot.epa.gov/radiation/tenorm-oil-and-gas-production-wastes_.html |
| E2 | OGJ concentrations 17.76 and 2.775 Bq/g | not on the OGJ page (re-read 2 Nov 2026); unverified | S1209 corrected in `sources_round3.csv` |
| E3 | "34 % retention" | in neither Gesell nor Johnson (only a ventilation multiplier 0.34, Johnson p.44) | originate from S0001/S0318? check S0318 text |
| E4 | Johnson refs 10, 12, 19 (Fries and Kilgren; Jacobs et al.; Barton et al.) | not obtained (S1255, S1256) | OSTI for ORNL-TM-4154 |
| E5 | API 1989 survey and RAE 1990 | not obtained (S1252, S1253) | API library |
| E6 | Disposal-route shares for scale and sludge | no source in hand; EPA has none | RAE-8837/2-2 may have a use-and-disposal split |
| E7 | World (non-US) solids tonnage | none | IAEA TRS-419 (round 2) conflicts by a factor 44 |
| E8 | SCA89 uranium mine report and EIA Uranium Industry Annual 1988 | not obtained (S1260, S1262) | EPA 520/1-89-006; EIA archive |
| E9 | S1210 type in `sources_round2.csv` is `industry_body`, not in the schema enum (regulator, compilation, peer_reviewed, agency, grey) | housekeeping | fix when merging |

## 10. Summary of proposals (old to new)

| Tag | Row or item | Old | New | Confidence | Independence from UNSCEAR 2016 |
|---|---|---|---|---|---|
| O1 | oil_gas:0047-0050 solids-bound fraction (total) | 0.001 / 0.01 / 0.04 | 0.001 / 0.02 / 0.10 | low-medium | independent |
| O2 | scale share | 0.4 (no band) | 0.4 (0.2-0.9) | low | independent |
| O3 | Ra-228:Ra-226 in solids | model equal fractions | no change; flag | low | independent |
| O4 | oil_gas:0078 $\phi$ | 0.2 / 0.5 / 0.8 | 0.6 / 0.9 / 0.97 | low-medium | independent |
| O6 | og_scale/og_sludge $\varepsilon$ | proposed 0.088 / 0.15 | confirmed by EPA 0.1; no change | high (no data) | independent |
| G1 | oil_gas:0074 delivered Rn | 47.6 / 300 / 779 | 50 / 300 / 1,000 | low-medium | partial |
| G2 | wellhead Rn | 625 | 800 (185-3,700) | low | partial |
| G3 | delivered fraction | 0.48 (proposal 0.20) | 0.2-0.7, central 0.375; do not apply 0.20 to 625 alone | low | partial |
| G4 | benchmark B1 | 1.17 TBq/(GW a) via unverified 34 % | 0.6-2.2 TBq/(GW a) from Johnson direct and bottom-up | low-medium | partial |
| G6 | NGL/LPG radon row | none | 10 / 200 / 1,000 Bq per m$^3$ gas produced | low | independent |
| C1-C5 | coal | see 6.3 | see 6.3 | medium / low | partial / independent |
| N1-N6 | nuclear G4 | see 7.4 | see 7.4 | medium | independent |
