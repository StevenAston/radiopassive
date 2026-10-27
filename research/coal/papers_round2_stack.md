# Coal stack release, enrichment and era fractions: round 2 paper reading

Prepared 2026-10-27. PROPOSALS ONLY: nothing in `data/`, `docs/`, `pipeline/` or existing `research/` files was edited. New and corrected source records are in `sources_round2_stack.csv` (same columns as `data/sources.csv`; new IDs S0981-S0982).

Method. All eleven staged PDFs had a text layer and were read with `pdftotext` (full text); scanned/garbled tables (Tadmor Table 8, Kaakinen Table I and Fig. 5, Zeevaert Table 3) were read from page images. Page numbers are the printed journal pages unless "PDF p." is given. SI throughout; $1\ \mathrm{GBq}=10^{-3}$ TBq; "per GWa" means per gigawatt-year of electricity.

Stream reference values (from `factors_notes.md`, `benchmarks.md`, `coal.csv`): ash-borne Ra-226 $0.092$ TBq/GWa (2010); Po-210 stack $2.4\times10^{-3}$, Pb-210 stack $1.06$-$1.08\times10^{-3}$, Ra-226 stack $3.1\times10^{-4}$ TBq/GWa. Reconstruction (mine, checks to 1%): $0.092\times0.00310\ (\text{coal:0053 centre})\times8.485\ (\text{coal:0057})=2.42\times10^{-3}$, and $\times3.795$ (coal:0056) $=1.08\times10^{-3}$. So the 2010 stream values use the 2010-25 era centre only, and Po/Pb $=8.485/3.795=2.24$.

---

## 0. Identity of the unknown and the corrected files

| File | Identity | Action |
|---|---|---|
| `li2019.pdf` | **Li, J., Wang, C., Pan, Z., Jiang, Z., Chen, L., Zhang, Y., Pan, J., Wang, C., Li, J., Liu, R. (2019). Analysis of 210Pb and 210Po emissions from coal-fired power plants. Fuel 236: 278-283.** Review article, China Institute of Atomic Energy. Same journal, volume, pages and DOI (10.1016/j.fuel.2018.08.075) as registry S0980; first author is **Li (Jinfeng)**, not "Liu". Liu (Ruirui) is the last author. | Correct S0980 author list. |
| `2825.pdf` | **NRPB-W48 (Crockett, Smith, Oatway, Mobbs, 2003), Radiological Impact on the UK Population of Industries which Use or Produce Materials Containing Enhanced Levels of NORM, Part II: The Steel Production Industry.** 126 pp. It is NOT NRPB-R327 (S0206; Part I, coal). Nothing on coal-plant stack release; it only cites R327. | New record S0982 (steel; for any steel/sinter stream). Its reference list gives the full R327 author list: Smith, Crockett, Oatway, Harvey, Penfold, Mobbs (2001); S0206 corrected, still NOT READ. |
| `Assessment-of-hazardous-...pdf` | **Mishra, M., Sahu, S.K., Mangaraj, P., Beig, G. (2023). Assessment of hazardous radionuclide emission due to fly ash from fossil fuel combustion in industrial activities in India and its impact on public. J. Environ. Manage. 328: 116908** (online 7 Dec 2022; doi 10.1016/j.jenvman.2022.116908). Registered as new S0981. | See section 10: "emission" there means ash-borne inventory, not stack release. |

---

## 1. Findings per paper

### 1.1 Li et al. 2019, Fuel 236 (S0980). The only direct Po-210/Pb-210 stack paper. Very useful.

Content: flue-gas sampling at five Chinese units (2014-15), plus compilation of 17 units (China, USA, Slovenia) for emission ratios, plus stable Pb.

- Headline (abstract and p.281 Table 6): capacity-weighted share of coal-input activity released to atmosphere, flue-gas basis: **Pb-210 2.1%, Po-210 3.7%**; unit range 0.01-8.3% (Pb) and 0.05-25% (Po). Mass-balance basis: Pb $-8.1\%$ (individual units from $-164\%$ to $+58\%$), Po 38% (14.7-70%). Authors say the two methods disagree badly; mass balance is unusable (negative closures) and flue-gas capture misses vapour-phase Po (PoO2 penetrates filters into the absorbent, p.279-280).
- Which units drive 3.7%: US 1978-81 units (M-1: 25%; 2.1%, 0.9%, 0.05% for others; 1978 units 0.6-2.6%). Post-2000 units: China 2013-15 Po 0.06-0.6% (8 units, Table 6; from ref. [12]/[18]); Šoštanj (Slovenia 2003) 0.17%. So the weighted 3.7% is an old-plant/high-outlier mean; modern-plant Po fraction is 0.06-0.6% (central about 0.2-0.3%).
- Table 4 (p.281): annual emissions GBq/a. Po-210: SH-4 China 0.0127; USA 1981 M-1 3.70, M-15 0.0026, M-33 0.0814, M-34 0.0104; UK 1998-2001 Drax 0.596, Eggborough 0.322, Aberthaw 0.112, High Marnham 0.111, Drakelow 0.0552, West Burton 0.411; Šoštanj 0.123. Pb-210: China 0.0029-0.022 (all below detection, $\tfrac14$ DL substituted); US 12.58 (M-1), 0.111, 0.0888; UK 0.654, 0.288, 0.172, 0.312, 0.132, 0.754.
- Table 1 (p.279): China plant generation in GWa (XSS-1 0.18, XSS-3 0.39, JJ-5 0.21, JJ-7 0.39, SH-4 0.21). Table 4 capacities: UK 3730/1990/1360/932/910/1920 MW; US 874/56/593/800 MW.
- Table 5 (p.281): coal, ash, slag, gypsum Bq/kg and kt/a; dust emission kg/a (last column; Table 4 caption block).

Conversions to per GWa (my arithmetic). Capacity factor not given for UK/US; **assumed 0.65 (range 0.5-0.8, effect shown)**.

| Quantity | Value (TBq/GWa) | Notes |
|---|---|---|
| UK 6 plants, Po-210 (1998-2001) | $2.3\times10^{-4}$ (LF 0.8: $1.9\times10^{-4}$; 0.5: $3.0\times10^{-4}$) | per plant $0.9$-$3.3\times10^{-4}$; NRPB assumed $4.3\times10^{-4}$ |
| UK 6 plants, Pb-210 | $3.3\times10^{-4}$ ($2.7$-$4.3\times10^{-4}$) | per plant $1.9$-$6.0\times10^{-4}$ |
| UK Po/Pb ratio, per plant | 0.36-1.12, mean about 0.7 | Po is not above Pb |
| China 2015 SH-4 (wet ESP, "near-zero"), Po-210 | $6.0\times10^{-5}$ | single unit |
| China 2014, Pb-210 (4 units, all below DL) | $0.7$-$5.6\times10^{-5}$ | upper bound only |
| USA 1981 Po-210: M-1 / M-33 / M-34 / M-15 | $6.5\times10^{-3}$ / $2.1\times10^{-4}$ / $2.0\times10^{-5}$ / $7\times10^{-5}$ | M-1 had a venturi scrubber with low dedusting efficiency (p.280) |
| USA 1981 Pb-210: M-1 / M-33 / M-34 | $2.2\times10^{-2}$ / $2.9\times10^{-4}$ / $1.7\times10^{-4}$ | |

Ash-escape ratios from Li Table 5 (my arithmetic, dust emission over fly ash + slag): XSS-1 0.10%, XSS-3 0.10%, JJ-5 0.073%, JJ-7 0.059%, SH-4 0.003% of total ash (China 2014-15; dust also includes sulphate aerosol, so this is an upper bound on ash).

Bearing on question 1 (below, section 2): the stream's $2.4\times10^{-3}$ is 10x the UK measured Po-210 and 40x the Chinese wet-ESP unit, but within the 1981 US spread and the 1970s-80s models.

Quality: peer-reviewed review, but most of its "measurements" are 1/4-detection-limit substitutions and secondary data from [5], [6], [12]-[14], [18]. Treat the UK part as partly shared with NRPB-R327 (it cites [6] = UK Environment Agency data). Independent of UNSCEAR 2016 Annex B as a dataset (it criticises UNSCEAR 2016's 1.4 and 0.093 GBq/GWa); not independent of NRPB.

Also quotes UNSCEAR normalised Pb-210 + Po-210 emission: 3.7 GBq/GWa (1977), 5.0 (1982, 97.5% removal), 15 (1988, old, 90% removal), 0.75 (1988, modern, 99.5% removal), 1.4 (2016 old) and 0.093 GBq/GWa (2016 modern) (p.279). The source text says "of 210Pb and 210Po"; whether per nuclide or sum is not stated (Tadmor Table 8 shows 1982 values as per nuclide, 5.0e9 each).

### 1.2 Tadmor 1986, J. Environ. Radioact. 4(3): 177-204 (S0240). Very useful.

- **Table 4 (p.184)**, enrichment/depletion ratio vs mineral matter of coal (computed by Tadmor from Kaakinen 1975 and Klein 1975): Pb-210: bottom ash 0.2, mechanical-collector ash 0.6, ESP ash 2.1, fly ash 3.5. Thorium: 0.8 / 0.8 / 1.0 / 1.3. Uranium: 0.7 / not applicable / 1.5 / not measured.
- **Table 5 (p.185)**, escaping fly ash by particle size (UNSCEAR 1982), vs mineral matter of coal: U-238 2.8 (2 $\mu$m), 1.6 (10 $\mu$m), 1.3 (17 $\mu$m); Ra-226 2, ~3 (as printed), 1.1; Th-232 1-2, 1-1, 1-1; Pb-210 4-8, 2-1(?), 1.4. (Scan quality poor for the 10 $\mu$m row.) Po-210 highest of all: enrichment 11 in fly ash (German studies, Chatterjee et al. 1980; Jacobi 1981; p.185). Ranking: Th lowest, Po-210 highest (p.185).
- **Table 6 (p.186)**: ash in flue gases 80% (pulverised coal), 20-30% (cyclone), about 10-20% (stoker, as printed "-10-20"). Pulverised-coal flue-gas ash: 65% finer than 10 $\mu$m.
- **Table 8 (p.191; PDF p.15, rotated)**, release rates (Bq/y) normalised to 1000 MWe, as read from the page image. Footnote: "modern CFP" = about 1% of the ash released; "old" = about 10%. Po-210 column (Pb-210 identical in every row that has both): McBride 1977 $3.0\times10^{8}$; Beck & Miller 1979 $2.6\times10^{9}$; US EPA 1979 old model $1.6\times10^{10}$, new model $2.6\times10^{9}$; Okamoto 1980 $7.4\times10^{10}$ (low-resolution scan, treat as uncertain); Camplin & Hallam 1980 $10^{9}$; Teknekron 1981 old $4.8\times10^{9}$, new $1.7\times10^{9}$; IAEA/UNSCEAR 1982 average $5.0\times10^{9}$, exceptional $2.6\times10^{10}$; Corbett 1983 modern $8.0\times10^{8}$; Nakaoka 1984 $3.7\times10^{9}$. Other columns: Ra-226 Eisenbud & Petrow 1964 $6.4\times10^{8}$; UNSCEAR 1982 average $1.5\times10^{9}$; Corbett modern $8\times10^{8}$; De Santis & Longo $2.2\times10^{8}$; Mishra 1984 $4.5\times10^{9}$-$2.6\times10^{10}$.
  - Text (p.190): "modern CFP ... release about an order of magnitude less radioactivity ... than older CFP".
  - Every model has Po-210 = Pb-210 (ratio 1). The per-1000 MWe basis does not state a load factor; treat as approximately per GWa (plus or minus 30%).
- Text p.190 also: radon from ash piles; mechanism of volatilisation/condensation (pp.186-190).

Quality: review, primary tables are compilations of 1960s-1984 models; the Po-210 values in Table 8 are modelled, not measured. They are the source lineage of UNSCEAR 1982/1988, so not independent of the UNSCEAR family (but independent of Annex B 2016).

### 1.3 Papastefanou 2010, J. Environ. Radioact. 101(3): 191-200 (S0241). Mixed: useful tables, one unreliable claim.

- Table 1 (p.193): coal activity (Bq/kg); Greek lignite U-238 243 (117-399), Ra-226 266 (44-236, as printed), Pb-210 134 (59-205). Ra-226:Pb-210 = 1.0 plus or minus 0.2 in coal; U-238:Ra-226 = 1.7 plus or minus 0.4 (disequilibrium, p.193).
- Table 2 (p.194): fly ash (Greece, ESP): U-238 356 (263-950), Ra-226 366 (142-605), Pb-210 275 (133-428), Th 50, K-40 297 Bq/kg; "enhancement from coal to fly ash by a factor of about 3" (p.193).
- **Table 4 (p.195)**, enrichment relative to input coal, normalised to K-40 (so on a bulk-ash basis). This work (Greek ESP ash): U-238 0.71 (0.60-0.76) and 0.69; Ra-226 0.87 and 0.86 (range 0.69-1.07); Pb-210 0.68 and 0.66 (0.57-0.75); Ra-228 1.00; K-40 0.98-1.00. Literature rows (Klein 1975; Coles 1978; Corbet 1983) by particle size 18.5/6.0/3.7/2.4 $\mu$m: U-238 1.3/1.6/2.3/2.8; Ra-226 1.1/1.4/1.6/1.9; Pb-210 1.3/3.0/4.1/5.0; Th-232 1.0/1.1/1.1/1.2; Ra-228 1.0/1.2/1.4/1.6. Text: EF range 0.60-0.94 (U), 0.69-1.7 (Ra-226), 0.48-1.00 (Pb-210), 0.89-1.4 (Th-232), 0.86-1.7 (Ra-228), 0.95-1.10 (K-40) (p.195).
- §3 p.195: fly ash escapes in "3 or 1% of the total fly ash, in the better cases" (Vakalis 1979, personal communication, Kardia Ptolemais); 40 t/d fly ash escapes, carrying 18.5 MBq/d Ra-226 ($6.8$ GBq/y) from a plant burning $7\times10^{6}$ t/y of lignite at 12.8% ash (p.196). My check: 40 t/d $=14.6$ kt/y $=1.6\%$ of the 0.90 Mt/y ash; $6.75\ \mathrm{GBq/y}/14.6\ \mathrm{kt}=462$ Bq/kg, matching the ESP stage-B ash (499 Bq/kg, Table 5).
- §4 p.196: **claims 99% of escaping Ra-226 leaves as ultrafine/vapour (1.55 TBq/y from one plant)**, from a coal-minus-ash mass-balance residual. My check: coal Ra-226 $266\ \mathrm{Bq/kg}\times7\times10^{9}\ \mathrm{kg}=1.9$ TBq/y, so the residual says about 80% of the coal Ra-226 escapes the stack. This contradicts Zeevaert, Coles, Kaakinen and the paper's own second laboratory ashing (all Ra and U remained in the ash). **Do not use the 1.48/1.55 TBq/y figure.** (Likely an uncounted-ash-stream closure error.)
- Greek lignite per tonne coal, gross particulate Ra-226 only: $6.75\times10^{9}\ \mathrm{Bq}/7\times10^{6}\ \mathrm{t}\approx960$ Bq per t coal (no electricity given, so no per-GWa).

### 1.4 Zeevaert, Sweeck, Vanmarcke 2006, J. Environ. Radioact. 85(1): 1-22 (S0245). Useful for modern plant.

Langerlo (Belgium), modern plant with ESP (99.5% of fly ash), plus denitrification and desulphurisation (additional 90-95% filtration), p.3.
- Coal Ra-226 20 Bq/kg, Th-232 20 Bq/kg (Table 1, p.3). Ash 10-15% of coal; 15% bottom ash and 85% fly ash.
- Ra-226 in discharged fly ash 590 (1999) and 1100 (2002) Bq/kg, adopted **700 Bq/kg**, versus 160-185 Bq/kg in ESP-captured ash (Table 2, p.3). Enrichment of discharged ash over ESP ash about 4; vs coal-based bulk ash (20/0.125 = 160 Bq/kg) also about 4.4. Authors say "approximately 3 times" (p.4).
- **Table 3 (p.4), Ra-226 airborne discharges (Bq/GW, read as per GW of electrical output per year):** Smith et al. 2001 (NRPB-R327) $3.5\times10^{8}$; Mishra et al. 1984 $4.5\times10^{9}$; UNSCEAR 1982 $1.5\times10^{9}$; Papastefanou 1996 $0.6$-$5.2\times10^{9}$; **this study $6\times10^{7}$** (that is $6\times10^{-5}$ TBq/GWa; 1 to 2 orders of magnitude below others). Ra-226 in fly ash (Bq/g) for those: 0.04-0.07; 0.09-0.18; 0.02-0.05; 0.15-0.6; 0.7.
- **Table 4 (p.5):** Pb and Po assumed 4x Ra-226 in discharged ash ("measurements by Coles (1978) and Tadmor (1986) indicate 2-4 times", p.4); radon 1500x Ra-226 by activity, assumed completely discharged. Po-210 = Pb-210 (both 2800 Bq/kg ash). So the implied Po-210 stack value is $4\times6\times10^{-5}=2.4\times10^{-4}$ TBq/GWa: an assumption, not a measurement.
- Implied ash escape (my arithmetic): $6\times10^{7}\ \mathrm{Bq}/700\ \mathrm{Bq/kg}=86$ t ash/GWa, which is about 0.02% of total ash (at 0.45 Mt ash/GWa); from the control train 0.5% $\times$ (5-10%) of fly ash $=0.025$-$0.05\%$ of fly ash $=0.02$-$0.04\%$ of total ash.

Quality: peer-reviewed, one plant, Ra-226 measured in stack ash twice (SD large), Pb/Po assumed. Independent of Annex B 2016 for the measured Ra-226; Table 3 is a literature compilation.

### 1.5 Hedvall and Erlandsson 1996, J. Environ. Radioact. 32(1-2): 19-31 (S0246). Little usable; confirms lineage.

pp.20-21: coal U-238, Th-232 20 Bq/kg and K-40 50 Bq/kg "on average" (UNSCEAR 1988). **Corbett (1983) assumption: 100% of radon, 10% of lead and polonium, 1% of other radionuclides in coal are released to the atmosphere** (p.21). Escaping fly-ash averages (UNSCEAR 1988; arithmetic): K-40 265, U-238 200, Ra-226 240, Pb-210 930, Po-210 1700, Th-232 70, Th-228 110, Ra-228 130 Bq/kg. Collective dose per GWa about 4 man-Sv (UNSCEAR 1988). No emission per GWa, no era split and no Table 27 data in this paper (the registry note linking it to UNSCEAR 2016 Table 27 is from UNSCEAR's citations, not this text). Nothing else usable for stack per GWa. Confirms Po/Pb in escaping ash = 1700/930 = 1.8 in the UNSCEAR 1988 averages.

### 1.6 McBride et al. 1978, Science 202(4372): 1045-1050 (S0978). Useful for 1970s fleet.

- Model 1000 MWe advanced plant (Allen Steam Plant data), coal 1 ppm U, 2 ppm Th; electrostatic precipitator releasing 1% of total ash ("conforms to EPA standards"); ash split 60% slag/40% fly ash for the cyclone boiler (80-90% fly ash for conventional blower-fed boilers).
- **Table 2:** each U-238-chain nuclide (Ra-226, Pb-210, Po-210 included) $8\times10^{-3}$ Ci/y ($3.0\times10^{8}$ Bq/y) per 1000 MWe; Th-232 chain $5\times10^{-3}$ Ci/y; U-235 chain $3.5\times10^{-4}$; Rn-222 0.8 Ci/y; Rn-220 0.4 Ci/y. No volatile enrichment (secular equilibrium assumed, "released in the same proportions"). Per GWa at their 80% capacity factor: Ra-226 $3.7\times10^{-4}$ TBq/GWa at 1% escape (my division: 7.43e5 short tons coal per year for a 290 MWe unit at 80% CF).
- **Section "Effect of higher fly-ash releases":** FPC 1972 survey of 696 major steam plants: 3,607,000 tons fly ash released from 348,694,000 tons coal at 13.4% ash, i.e. **7.7% of total ash escaped (paper says "8 percent")**. "Releases from most currently operating plants, particularly older plants, are higher than 1 percent."
- Not a global factor: US only. But it is a primary national average for 1972, closely matching the stream's 1970-89 band.

### 1.7 Coles, Ragaini, Ondov 1978, Environ. Sci. Technol. 12(4): 442-446 (S0237). Directly answers question 3.

Two western US plants. Plant A: 9.2% ash coal, cold-side ESP, 0.52% S. Plant B: 23.2% ash coal, 3 units with venturi scrubbers and 2 with cold-side ESP; sized stack fly ash from a cyclone at the outlet of one ESP (mass median diameter 18.5, 6.0, 3.7, 2.4 $\mu$m). ESP efficiency 97%, scrubber 99.2% (p.444).
- Enrichment factor (EF) is defined relative to K-40 in the coal, which is a bulk-ash basis (p.443; checked: coal 1660 ppm K, ash 7400 ppm K; 7400/1660 = 4.46 = 1/0.224). **This is exactly the rebased basis of D53.**
- **Table IV (p.444), EF:** columns Th-228, Ra-228, Pb-210, Ra-226, U-235, U-238.
  - Plant A ESP fly ash: 0.89, 0.90, 0.48, 1.0, 0.71, 0.70. Plant A bottom ash: 0.96, 0.97, 0.24, 0.99, 0.70, 0.64.
  - Plant B ESP fly ash: 0.96, 0.98, 0.74, 1.0, 0.94, 0.85. Bottom ash: 0.91, 0.89, 0.29, 0.90, 0.76, 0.73. Scrubber ash about 0.88-1.1 for all.
  - Plant B post-ESP stack fly ash 18.5 / 6.0 / 3.7 / 2.4 $\mu$m: Th-228 1.0 / 1.1 / 1.1 / 1.2; Ra-228 1.0 / 1.2 / 1.4 / 1.6; Pb-210 1.3 / 3.0 / 4.1 / 5.0; Ra-226 1.1 / 1.4 / 1.6 / 1.9; U-235 1.3 / 1.6 / 2.3 / 2.8; U-238 0.94 / 1.4 / 2.0 / 2.8.
- Table II (p.443): stack ash Pb-210 and others in pCi/g; Po-210 was not measured ("postcombustion behaviour was not studied"). The paper only states Po is more volatile than Pb and "will probably condense onto the extremely small fly ash particles". So Po-210 has no number here.
- Notes: Pb-210 most volatile; U bimodal (organic/uraninite fraction volatilises; coffinite stays in silicate). Plant-by-plant coal/ash in secular equilibrium in coal but not in ash.

### 1.8 Kaakinen et al. 1975, Environ. Sci. Technol. 9(9): 862-869 (S0239). Directly answers Pb/Po.

Valmont Unit 5 (180 MWe, Colorado), 6% ash coal, mechanical collector (86% fly-ash removal) then ESP and wet scrubber in parallel (Fig. 1, p.863). Table I (p.864), specific activity dpm/g: Pb-210: coal 0.61; bottom ash 2.2; mechanical ash 6.3; ESP hopper ash 23; ESP-outlet fly ash (PO) 38. Po-210: BA 0.76; MA 6.6; PA 28; **PO 42**. Ra-226: coal 0.031; BA 1.2; MA 0.76; PA 1.8; PO 0.89. (1 dpm/g = 16.7 Bq/kg: PO Pb-210 633 Bq/kg, Po-210 700 Bq/kg.) **Fig. 5 (p.866)**, enrichment relative to Al and total outlet (bulk-ash basis): at PO, Pb about 6, **Pb-210 about 4.5, Po-210 about 5**, Ra-226 about 1.0 (Group A, non-enriched); bottom ash Pb-210 about 0.25, Po-210 about 0.1. Conclusion (p.866): "enrichment ratios for both 210Pb and 210Po ... nearly the same as those of Pb". So **Po-210/Pb-210 enrichment at the stack-side ash is about 1.1**, not 2.2. Direct measured counter-evidence to the stream's Po/Pb of 2.24. Caveat: Po-210 in coal not measured (secular equilibrium with Pb-210 assumed); one plant; PO sample is below the ESP at this unit's design (bag-filter isokinetic sample).

### 1.9 Eisenbud and Petrow 1964, Science 144(3616): 288-289 (S0238). Anchor for the pre-1970 fleet.

1000 MWe plant burning 2.3 Mt/y semi-bituminous Appalachian coal at 9% ash; six ESP fly-ash samples: Ra-226 3.8 pCi/g (140 Bq/kg), Ra-228 2.6, Th-228 2.4 (Table 1, p.289). **Control: mechanical filters plus ESP, "97.5 percent of the fly ash produced is thus collected when the equipment is properly maintained; the remaining 2.5 percent is discharged"** (Con Edison plants), giving 4.5e9 g fly ash/y (about 2.2% of the 2.07e11 g total ash), Ra-226 17.2 mCi/y $=6.4\times10^{8}$ Bq/y and Ra-228 10.8 mCi/y $=4.0\times10^{8}$ Bq/y (i.e. $6.4\times10^{-4}$ and $4.0\times10^{-4}$ TBq per 1000 MWe-year). **"A power station in which dust collection equipment is not used will discharge about 80 percent of the ash into the atmosphere"**: 350 mCi Ra-228 and 550 mCi Ra-226 per year (Ra-226 $2.0\times10^{10}$ Bq, my conversion; checks against 0.8 $\times$ 207 kt $\times$ 140 Bq/kg $=2.3\times10^{10}$). Assumption stated: escaping ash has the same Ra content as collected ash (EF = 1). Source of the 97.5% in UNSCEAR 1982 (so UNSCEAR "2.5%" is not independent of this).

### 1.10 Mishra et al. 2023, J. Environ. Manage. 328: 116908 (new S0981). Not a stack-release paper.

"Emission" = Indian fly ash generated $\times$ mean activity concentration (Methodology §2.2, p.5-6; $E=\Sigma F_i N_i\times EF_i$ with EF = Bq/kg in fly ash from literature). No capture efficiency, so it is the ash-borne inventory, mislabelled as atmospheric release. Results (Table 3, 2019): thermal power plants 212,329 MW installed; Ra-226 18.4 TBq (TPP), all sectors 27.5 TBq; Th-232 44.4 TBq; U-238 41.1 TBq; K-40 111 TBq; TPP fly ash 207 Mt from 621.6 Mt coal (p.3-5). Stated per GW (p.8): 86 GBq Ra-226, 140 Th-232, 129 U-238, 351 K-40 "released annually" per 1 GW of TPP. In stream terms this is the **ash-borne Ra-226 per GW of installed capacity $=0.087$ TBq/GW (0.15 TBq/GWa at PLF about 0.56; mean 89 Bq/kg fly ash)**. Use only as an independent check on benchmark (a) (stream 0.092): ratio 0.95 per GW installed, 0.6 per GWa. Do NOT use as a stack-release benchmark. Quality: peer-reviewed but methodologically weak (generic literature concentrations; terminology error).

### 1.11 `2825.pdf` (NRPB-W48, steel). Nothing usable for coal.

See section 0.

---

## 2. Answers to the four questions

### Q1. Po-210 stack: stream $2.4\times10^{-3}$ vs UK $4.3\times10^{-4}$ (x5.6). Is Po enrichment (coal:0057 centre 8.49) too high?

Evidence on the Po-210 stack release per GWa (TBq/GWa):

| Source | Po-210 | Era / type | Basis |
|---|---|---|---|
| Li 2019 UK 6 plants (S0980) | $2.3\times10^{-4}$ ($1.9$-$3.0\times10^{-4}$) | 1998-2001, ESP | measured ash/flue gas, LF assumed 0.65 |
| UK NRPB (S0205) | $4.3\times10^{-4}$ | 1998 | assumed 200 Bq/kg ash |
| Li 2019 China SH-4 (S0980) | $6\times10^{-5}$ | 2015, wet ESP | measured |
| Zeevaert (S0245) | $2.4\times10^{-4}$ | modern BE | assumed Po = 4 x Ra; Ra measured |
| Tadmor Table 8, modern/new models (S0240) | $0.8$-$2.6\times10^{-3}$ | 1979-83 models, 1% ash | modelled |
| Tadmor: UNSCEAR 1982 average (2.5% ash) | $5.0\times10^{-3}$ | 1982 model | modelled |
| Tadmor: old plants (US EPA old; Teknekron old; 10% ash) | $1.6\times10^{-2}$; $4.8\times10^{-3}$ | 1979-81 models | modelled |
| Li 2019 US 1981 | $2\times10^{-5}$ to $6.5\times10^{-3}$ | measured, 4 plants | |
| UNSCEAR 1988 via Li (S0980) | $1.5\times10^{-2}$ old / $7.5\times10^{-4}$ modern (Pb + Po, as quoted) | | |
| **Stream 2010** | $2.4\times10^{-3}$ | global fleet | stream |

Po/Pb stack ratios found: Kaakinen measured ESP-outlet ash 1.1 (enrichment 5 vs 4.5); UK six plants measured 0.36-1.12 (mean 0.7); Tadmor Table 8 models: all 1.0; NRPB, Zeevaert: 1.0 (assumed); UNSCEAR 1988 escaping ash 1.8 (1700/930); Jacobi/Chatterjee Po-210 enrichment 11 (Tadmor p.185). **The stream's Po/Pb = 2.24 is above every measured ratio and above all models; it matches only the UNSCEAR 1988 average (1.8) at its upper edge.**

Fraction of coal-input Po-210 leaving the stack (Li, flue-gas basis): post-2000 units 0.06-0.6% (China), 0.17% (Slovenia); old US units 0.05-25%, weighted 3.7%. Stream equivalent: $2.4\times10^{-3}/0.092=2.6\%$ (assuming coal Po-210 equals the Ra-226 chain activity, as the stream does), i.e. 4-40x the post-2000 measurements and within the 1978-81 US range.

Conclusion: **Yes, the Po-210 enrichment centre is too high relative to Pb-210 and relative to measured stack ash.** The data say Po-210 enrichment is about equal to Pb-210 (about 1.0-1.3 x Pb), and Pb-210 enrichment about 3-5 in sized stack ash (Coles 1.3-5.0; Kaakinen 4.5; Tadmor flyash 3.5). Lowering Po centre from 8.49 to about 4.5 reduces the stream's 2010 Po-210 stack to $1.28\times10^{-3}$ TBq/GWa (Po/Pb = 1.2). It remains 3x above the UK value (within factor 3 of the benchmark test), because the stream 2010-25 era fraction (0.31% of total ash) applies to a global fleet that includes ESP-only and older plants, while UK 1998 is 0.41% with ~0.7x Pb Po. The residual gap is fleet, not enrichment. The 5.6x gap to UK is thus about 1.9x enrichment (Po/Pb) and about 3x fleet/other. Caveat: Li notes vapour-phase Po passes filters and flue-gas methods under-count; mass-balance Po emission is 15-70%; so do not cut the high bound hard (proposed high 12, was 24).

### Q2. Era base fractions (coal:0049-0053) (fraction of TOTAL ash escaping the stack)

Data (all fractions of total ash unless stated):

| Era | Datum | Source | Reading |
|---|---|---|---|
| uncontrolled (pre-1950 plants with no collectors) | 0.80 of ash discharged | Eisenbud 1964, p.288 (S0238) | direct anchor of the high bound (0.80), supports |
| 1960s, mechanical + ESP, urban US (Con Ed) | 2.2-2.5% | Eisenbud 1964 | below the stream's 1950-69 low bound (0.08) |
| US 1970 | 78% control, about 18% of ash (stream's own S0207 derivation) | existing | band 0.08-0.33 centre 0.16 |
| **US 1972, 696 plants** | **7.7%** (3.607 Mt of 46.7 Mt ash) | McBride 1978 (FPC survey) | primary national average; inside 1970-89 band 0.01-0.20, above centre 0.045 |
| "old" vs "modern" CFP, 1979-83 models | 10% vs 1% | Tadmor Table 8 footnotes | old 10% inside 1970-89 band |
| UNSCEAR 1982 average | 2.5% (97.5% removal) | via Tadmor/Li; origin Eisenbud | not independent of Eisenbud |
| India 1976-83 | 3.0% | Lalit (S0972) | supports 1970-89 centre 0.045 |
| Greece Kardia Ptolemais, about 1979 | 1.6-2% of fly ash | Papastefanou p.195-196 | inside 1970-89 band |
| UK 1998 | 0.41% | NRPB (S0205) | lower than stream 1990-2009 centre (2%) |
| Belgium modern plant (about 2000) | 0.02-0.04% | Zeevaert (S0245) | far below stream 1990-2009 and 2010+ low bounds |
| China 2014-15 (4 ESP/FGD units + 1 wet-ESP) | 0.003-0.10% (dust/ash, upper bound) | Li Table 5 (S0980) | at/below the stream's 2010+ low bound (0.08%) |
| US 1981 plants (inference from dust and benchmark ash/GWa; assumes 0.527 Mt ash/GWa, LF 0.65) | about 1-2% | Li Table 5 | consistent with 1970-89/1990-2009 |

Proposed changes in section 3. Short form: pre-1950 keep (no new data except the Eisenbud 0.80 anchor, which supports the high bound and does not replace the "JUDGEMENT" centre 0.25; still no source); 1950-69 widen low to 0.025 (Eisenbud); 1970-89 keep (McBride 7.7%, Lalit 3.0%, Tadmor 10%/1% all inside); 1990-2009 lower centre (UK 0.41%, India model 0.8%, Zeevaert 0.03%); 2010+ lower low bound only.

### Q3. U and Th rebased enrichment below 1: artefact?

**Partly an artefact; the U/Th centres are too low, but not everything below 1 is wrong.** Paired same-plant measurements (K-40-normalised, i.e. the D53 bulk-ash basis):

- Th-228/232 and Ra-228 (Coles Table IV, p.444; Tadmor Table 4): ESP fly ash 0.89-0.98 (Th), bottom ash 0.89-0.97; stack ash 1.0-1.2 (Th-228), 1.0-1.6 (Ra-228); Tadmor fly ash 1.3, ESP ash 1.0. Papastefanou Ra-228 1.0, Th 0.89-1.4. **Range 0.9-1.6, centre about 1.1.** The stream's Th 0.38 (0.12-1.2) is not supported.
- U-238/U-235: ESP ash 0.60-0.94 (Coles 0.70, 0.85; Papastefanou 0.60-0.76; Tadmor ESP 1.5); bottom ash 0.64-0.76; escaping stack ash (the stream's quantity) 0.94-2.8 by size (Coles), Tadmor/UNSCEAR 1982 1.3-2.8. **Escaping-ash range 0.9-2.8, mass-weighted about 1.3.** Stream (0.12/0.39/1.3) is too low.
- Ra-226: ESP ash 1.0 (Coles), 0.69-1.07 (Papastefanou); stack ash 1.1-1.9 (Coles), 1.1-2 (Tadmor Table 5); stream 0.6/1.095/2.0 is fine. Zeevaert measured 700 Bq/kg discharged vs 160-185 collected (about 4x) for a modern 99.9% control train; high bound could rise to 3.
- K-40: EF = 1 by construction; stack ash K 8200-8600 ppm vs ESP ash 7400 (1.1-1.16, Coles Table II); Papastefanou 0.95-1.10. Stream 0.69/2.03/6 is not supported at all.

Why the stream is below 1: (i) S0202 Table X ranges are "relative to coal" (ratio ash/coal, which includes the 1/0.12 = 8.33 concentration step); dividing by 8.33 is right only if the Table X ranges are ash-particle/coal ratios, and its lower ends (1 for U/Th) then give 0.12, which is below any measured value (the minimum measured EF is about 0.5-0.6, in bottom ash and ESP ash). (ii) The S0010-derived values (Th 0.45, K 0.69) divide UNSCEAR 1988 average escaping-ash concentrations (Hedvall p.21: Th 70, K 265 Bq/kg) by a global-average coal at 12% ash (20/0.12 = 167, 50/0.12 = 417); these are unpaired averages from different coals, not paired plant data, so they cannot give an enrichment. The paired Coles/Kaakinen/Papastefanou data are the correct basis and say about 1.

### Q4. Independent per-GWa benchmark values to add to benchmarks.md §4

Independence marked against UNSCEAR 2016 Annex B (S0001). Per GWa; conversions mine.

| Test | Value (TBq/GWa) | Source (ID, page/table) | Era / place | Independence | Stream 2010 | Ratio |
|---|---|---|---|---|---|---|
| Po-210 stack | $2.3\times10^{-4}$ ($1.9$-$3.0\times10^{-4}$, LF 0.5-0.8) | S0980, Table 4 (p.281), six UK plants | UK 1998-2001 | measured; shares UK Environment Agency data with NRPB R327 | $2.4\times10^{-3}$ | 0.10 |
| Pb-210 stack | $3.3\times10^{-4}$ ($2.7$-$4.3\times10^{-4}$) | S0980, Table 4 | UK 1998-2001 | as above | $1.06\times10^{-3}$ | 0.31 |
| Po-210 stack | $6.0\times10^{-5}$ | S0980, Tables 1, 4, SH-4 | China 2015 wet ESP, single unit | independent | $2.4\times10^{-3}$ | 0.025 |
| Po-210 stack (model) | $0.8$-$2.6\times10^{-3}$ (modern); $4.8\times10^{-3}$-$1.6\times10^{-2}$ (old) | S0240, Table 8 p.191 | 1979-83 models, per 1000 MWe | independent of Annex B 2016, same lineage as UNSCEAR 1982 | $2.4\times10^{-3}$ | 0.3-1.1 (modern); 2-7 (old) |
| Ra-226 stack | $6\times10^{-5}$ | S0245, Table 3 p.4 | modern BE plant | independent, measured | $3.1\times10^{-4}$ | 0.19 |
| Ra-226 stack | $3.5\times10^{-4}$ | S0245, Table 3 (quoting Smith et al. 2001) | UK | = NRPB R327 value | $3.1\times10^{-4}$ | 1.1 (cf. benchmark's $2.1\times10^{-4}$, ratio 1.7 between the two NRPB-derived numbers) |
| Ra-226 stack | $0.6$-$5.2\times10^{-3}$; $4.5\times10^{-3}$; $1.5\times10^{-3}$ | S0245, Table 3: Papastefanou 1996 (Greek lignite), Mishra 1984 (India), UNSCEAR 1982 | various | Greek/Indian independent; UNSCEAR 1982 not | era-matched 1970-89: $4.5\times10^{-3}$ | about 1 |
| Ra-226 stack | $3.7\times10^{-4}$ at 1% ash; $3.0\times10^{-3}$ at US 1972 average 7.7% | S0978 Table 2 + FPC 1972 | US 1972-77 | independent, primary ORNL | era 1970-89: $4.5\times10^{-3}$ | 1.5 |
| Ra-226 stack | $6.4\times10^{-4}$ per 1000 MWe | S0238 p.289 | US 1960s, 2.5% escape | independent; origin of UNSCEAR 1982 97.5% | 1950-69 stream (0.092 $\times$ 0.162 $\times$ 1.095) $=1.6\times10^{-2}$ | 0.04 (stream is 25x above: stream band too high, see section 3) |
| Ra-226 in ash (ash-borne) | 0.087 per GW installed; 0.15 per GWa at PLF 0.56 | S0981, Table 3 + p.3 | India 2019 | independent; inventory only | 0.090 (2020) | 0.97 (0.6 per GWa basis) |
| Escaping ash fraction | 7.7% (US 1972); 0.003-0.10% (China 2014-15); 0.02-0.04% (BE) | S0978; S0980 Table 5; S0245 | | independent | era centres 0.0447 (1970-89); 0.0031 (2010+) | 1.7; 0.03-32 |
| Po/Pb stack ratio | 1.1 (Kaakinen); 0.7 mean (UK); 1.0 (all models); 1.8 (UNSCEAR 1988) | S0239 Fig. 5; S0980 Table 4; S0240 Table 8 | | mixed | 2.24 | 0.3-0.8 |

Note on the Eisenbud row: stream 1950-69 Ra-226 stack is $0.092\times0.162\times1.095=1.6\times10^{-2}$ TBq/GWa only if the 2010 ash-borne Ra-226 is applied to the 1960s; the 1960s plant is 1000 MWe at 9% ash with Ra-226 coal about 12.6 Bq/kg, so the ash-borne Ra-226 per GWa would be 0.5x the 2010 value. Era-matched stream estimate is therefore about $8\times10^{-3}$ and the ratio 0.08. Either way the Eisenbud datum is a single well-run urban plant and sits at the low end of the era band.

---

## 3. Proposed factor changes (PROPOSALS ONLY, no data files edited)

Era base fractions (unit-1, fraction of total ash escaping; coal:0049-0053)

| Factor | old low / central / high | new low / central / high | Justification | Confidence |
|---|---|---|---|---|
| coal:0049 (1800-1949) | 0.04 / 0.25 / 0.8 | no change to numbers; **add S0238 to source_ids**; change the note to say high 0.80 now has a direct anchor (Eisenbud 1964: uncontrolled plant discharges about 80% of ash) while 0.25 remains JUDGEMENT, NO SOURCE | no pre-1950 plant data in any paper; the 1960s data bracket it (0.8 uncontrolled; 0.022-0.025 collected) | low |
| coal:0050 (1950-69) | 0.08 / 0.162 / 0.33 | 0.025 / 0.15 / 0.33 | low: Eisenbud 2.2-2.5% for 1960s mechanical + ESP plants. Centre: 1970 US 0.18 (S0207) and 1972 US 0.077 (McBride/FPC) imply a US average of 0.08-0.18 across 1960-72, and global fleets (USSR, Poland, India) were worse; 0.15 trims the geometric-mean value only slightly | low |
| coal:0051 (1970-89) | 0.01 / 0.0447 / 0.2 | no change; add S0978 (US 1972 7.7%, EPA 1% standard) and S0240 (old 10%, modern 1%) to source_ids | all inside the band; centre 4.5% vs US 1972 7.7%, India 1976-83 3.0%, Greece 1.6-2% of fly ash, UNSCEAR 1982 2.5% | medium |
| coal:0052 (1990-2009) | 0.004 / 0.02 / 0.1 | 0.0004 / 0.012 / 0.1 | low: Zeevaert BE 0.02-0.04% (rounded to 0.04%); centre: independent points UK 0.41%, India model 0.8% (Pandit), Lalit 3.0% (1983), Poland/Greece 2%, China 1990-2000 ESP-era near 1-2%; median about 1% (arithmetic of fleet shares not available; this is a judgement bracketed by sources) | low-medium |
| coal:0053 (2010-2025) | 0.0008 / 0.0031 / 0.012 | 0.0002 / 0.0031 / 0.012 | low: Zeevaert 0.02-0.04%, Li China 2014-15 0.003-0.10%, TRS 419 Fig.11 0.0044-0.084% all below 0.08%; centre and high unchanged (UK 0.41% in 1998, India model 0.8%, UNSCEAR 2016 older-plant 1.2%) | medium |

Group enrichment factors (unit-1, relative to bulk ash; coal:0054-0064)

| Factor | old low / central / high | new low / central / high | Justification | Confidence |
|---|---|---|---|---|
| coal:0054 Ra226+ | 0.6 / 1.095 / 2 | 0.7 / 1.2 / 3.0 | Coles stack ash 1.1-1.9, ESP 1.0; Papastefanou 0.69-1.7; Tadmor 1.1-2; Zeevaert modern plant discharged vs captured ash about 4 (one plant, high uncertainty) sets the high | medium |
| coal:0055 Ra228+ | 0.6 / 1.095 / 2 | 0.9 / 1.2 / 1.7 | Coles 0.9-1.6 (0.98, 1.0-1.6 stack); Papastefanou 0.86-1.7 | medium |
| coal:0056 Pb210+ | 1 / 3.795 / 14.4 | 1.0 / 3.8 / 8 | centre unchanged: Coles 1.3-5.0 (size-resolved, mass-weighted about 3), Kaakinen PO about 4.5, Tadmor flyash 3.5, UNSCEAR 1988 5.6; high: Tadmor Table 5 (4-8 at 2 $\mu$m); 14.4 (S0202) has no escaping-ash measurement behind it | medium |
| coal:0057 Po210 | 3 / 8.485 / 24 | 2 / 4.5 / 12 | Po/Pb measured 1.1 (Kaakinen), 0.7 (UK), 1.0 (all Tadmor models, Zeevaert, NRPB) vs 2.24 now. High 12 from UNSCEAR 1988 average 10.2 and Chatterjee/Jacobi 11 (Tadmor p.185). Effect on 2010 stream: $2.4\times10^{-3}\to1.3\times10^{-3}$ TBq/GWa | medium |
| coal:0058 U238+, coal:0059 U234, coal:0061 U235+ | 0.12 / 0.395 / 1.3 | 0.6 / 1.3 / 2.8 | escaping-ash EF 0.94-2.8 (Coles by size), Tadmor ESP 1.5 / UNSCEAR 1982 1.3-2.8, UNSCEAR 1988 1.2; low = ESP/bottom-ash minimum 0.6 (Papastefanou, Coles). Old 0.12 is not supported by any measurement | medium |
| coal:0060 Th230 | 0.12 / 0.395 / 1.3 | 0.9 / 1.1 / 1.6 | thorium isotope is refractory like Th-228/232 (Coles, Tadmor); not measured directly | low |
| coal:0062 Th232, coal:0063 Th228+ | 0.12 / 0.379 / 1.2 | 0.9 / 1.1 / 1.6 | Coles Th-228 0.89-1.2; Tadmor ash 0.8-1.3; Papastefanou 0.89-1.4 | medium-high |
| coal:0064 K40 | 0.69 / 2.035 / 6 | 0.9 / 1.05 / 1.2 | K-40 is the EF normaliser; stack ash K 1.1-1.16 vs ESP ash (Coles Table II); Papastefanou 0.95-1.10 | high |

Effects to expect (my arithmetic, 2010 values, 2010-25 era centre): Po-210 stack $2.4\to1.3\times10^{-3}$; Pb-210 unchanged ($1.08\times10^{-3}$); Ra-226 stack up 10% ($3.1\to3.4\times10^{-4}$); K-40 stack about halves. The cap at the fly-ash Bq (D54) will bind less on U/Th with the new centres since centres fall nearer 1.

Not proposed: any change to the Po-210/Pb-210 ash-borne parent quantities (outside this reading), and no change to the cap D54.

---

## 4. Gaps and contradictions to flag

1. **No pre-1950 plant data** in any paper; coal:0049 centre 0.25 stays JUDGEMENT. Eisenbud gives only the uncontrolled endpoint (0.80).
2. **Papastefanou's 99%-escapes-as-fine-particles claim** (1.55 TBq/y Ra-226, §4 p.196) is an unclosed mass balance and conflicts with all other sources; excluded.
3. **Li 2019 internal conflict:** flue-gas basis 2.1% (Pb) and 3.7% (Po) vs mass balance $-8\%$ and 38%; Pb-210 in flue gas was below the detection limit at all five Chinese units (substituted by $\tfrac14$ DL). Vapour-phase Po is probably under-captured, so modern Po stack values from flue-gas measurement are lower bounds.
4. **Tadmor Table 8 per-1000 MWe basis** has no stated load factor, and the scan is rotated and low resolution (Okamoto 1980 $7.4\times10^{10}$ and some Th/U cells uncertain). Verified against McBride Table 2 ($8\times10^{-3}$ Ci $=3.0\times10^{8}$ Bq) and Eisenbud ($17.2$ mCi $=6.4\times10^{8}$ Bq).
5. **UNSCEAR 1982 "97.5%" derives from Eisenbud 1964**, and Hedvall/UNSCEAR 1988 average escaping-ash values underlie the stream's enrichment inputs; these are not independent.
6. **Zeevaert unit**: Table 3 gives "Bq/GW"; read as per GW of electrical output per year. The Pb/Po values there are assumptions (4 x Ra).
7. **Zeevaert vs NRPB:** Smith et al. 2001 Ra-226 stack is $3.5\times10^{8}$ Bq/GW in Zeevaert's Table 3 versus $2.1\times10^{-4}$ TBq/GWa in `benchmarks.md` (my earlier derivation from the NORM III paper). Factor 1.7 between the two readings of the same report; R327 itself is still unread (S0206).
8. **Capacity factors** for the UK and US plants in Li Table 4 are assumed (0.65); results shown with 0.5-0.8.
9. **Mishra 2023** terminology ("emission") is wrong; use only as ash-borne inventory.
10. `2825.pdf` is not R327; R327 (S0206) is still unread. INIS URL in the registry may be tried by Steve.
11. The stream's fleet weighting (0.74 old for Pb-210 vs 0.40 for Ra-226 in §3 of benchmarks.md) is unaffected by this reading; enrichment changes act on the nuclides independently.
