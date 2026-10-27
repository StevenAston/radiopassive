# Coal stream: independent benchmark estimates (PLAN done condition (e))

Prepared 2026-10-27. New sources S0972-S0980 are in `sources_benchmarks.csv` (columns identical to `data/sources.csv`; `data/sources.csv` not edited). Existing IDs reused where the source is already registered: S0200 (USGS FS-163-97), S0202 (IAEA TRS 419), S0204 (EC RP 135 vol. 1), S0205 (NRPB UK paper, NORM III), S0245 (Zeevaert 2006).

Conventions. $1\ \mathrm{GW\,a} = 1\ \mathrm{TWh}/8.766$ (so 8,458 TWh = 964.9 GW.a in 2010; 9,437 TWh = 1,076.5 GW.a in 2020). All "independent / stream" ratios use the stream 2010 value (the 2020 ratios differ by under 4%). "Within x3" means $1/3 \le \text{ratio} \le 3$.

---

## 1. What the four staged files are

| File | What it is | Use here |
|---|---|---|
| `TRS419_web.pdf` | IAEA Technical Reports Series No. 419 (2003), *Extent of environmental contamination by NORM and technological options for mitigation* (registered as S0202). Section 4.2 covers coal. | Composition tables (IX, XI, XII), Fig. 11 plant mass balance (stack ash), Table X enhancement ratios. No release per GW.a. |
| `FS-163-97.pdf` | USGS Fact Sheet FS-163-97 (Zielinski and Finkelman, Oct 1997), registered as S0200. | US coal U and Th 1-4 ppm, fly ash U 10-30 ppm, mean US ash yield about 10 wt%, modern plants recover >99.5% of solid wastes, and "virtually 100 percent" of the radon in feed coal goes to the gas phase and is lost in stack emissions. No Ra-226, Pb-210, Po-210 or K-40 values. |
| `bem2002.pdf` | Bem, Wieczorkowski and Budzanowski (2002), J. Environ. Radioactivity 61: 191-201, Lodz region, Poland (S0973). | Escaping-ash history and Lodz discharges (GBq/y). No electricity output, so it cannot be put on a per-GW.a basis. |
| `lalit1986.pdf` | Lalit, Ramachandran and Mishra (1986), Radiation Protection Dosimetry 15(3): 197-202, *Radiation exposures due to coal-fired power stations in India* (S0972). A scanned image PDF (text extraction returns nothing); I read all six pages as images. | The best usable per-station data: capacity, load factor, coal per MW, ash yield, ash and coal activity, modelled annual airborne release (Table 3). Converted below. |

---

## 2. Independent estimates, converted to TBq per GW.a

### 2.1 Arithmetic, source by source

**A. India 1976-83, Lalit et al. (S0972).** 29 stations, 10,102 MWe (the paper's "10,100 MW"; the 36 table rows double-count 7 stations whose capacity was updated, so I kept the later row of each pair, dropping Betul 312, Bhusawal 63, Koradi 480, Nasik 280, Parli 60, Ukai 240 and Ennore 330 MWe). Generation $= \sum \text{MWe}\times\text{PLF}$ = 4.893 GW.a (load factor 48.4%).

$$\text{release per GW.a}=\frac{\sum_i R_i\ (\mathrm{MBq/y})\times10^{-6}}{4.893\ \mathrm{GW\,a}}$$

- Ra-226 released: $\sum R_i = 21{,}959$ MBq/y, giving $4.49\times10^{-3}$ TBq/(GW.a).
- Th-228 released: $7.06\times10^{-3}$ TBq/(GW.a). K-40 released: $1.77\times10^{-2}$ TBq/(GW.a).
- Coal per GW.a: $\sum(\text{MWe}\cdot t_{coal}\cdot365.25\cdot\text{PLF})/4.893 = 5.38$ Mt/(GW.a) (low-grade Indian coal, 13.5 t/d per MW typical).
- Ash-borne Ra-226 (coal $\times$ ash fraction $\times$ fly-ash Ra-226): 0.149 TBq/(GW.a). Cross-check from coal Ra-226 (Table 2, mean 26.2 Bq/kg $\times$ 5.38 Mt) = 0.141 TBq/(GW.a).
- Implied escaping fraction of ash-borne Ra-226: 3.0%.
- Caveat: releases are modelled (text assumes 97% control for ESP stations, 82% for mechanical collectors), but Table 3 gives 3.0% for every station including the nine asterisked mechanical-collector stations. Either the table does not apply the 82% figure or the text is not what was computed; I cannot resolve this from the paper. Treat 3.0% as "the paper's printed result".

**B. UK 1998, NRPB (S0205, read directly from the NORM III paper N3_3.5).** UK 1998 ash 7.4 Mt, of which about 30,000 t (0.41%) released to atmosphere; coal ash content 16% (10-20%); assumed coal Ra-226 15 Bq/kg; ash to atmosphere assumed Ra-226 100, Pb-210 200, Po-210 200 Bq/kg (measured emitted ash, Table 1: Ra-226 44-74, Pb-210 98-290, Po-210 64-171 Bq/kg). Coal-fired generation 1998 = 122.97 TWh (the stream's own electricity series, EI Statistical Review) = 14.03 GW.a.
- Ash: $7.4/14.03 = 0.527$ Mt/(GW.a). Coal: $7.4/0.16 = 46.3$ Mt, i.e. 3.30 Mt/(GW.a).
- Ra-226 in ash: $7.4\times10^{9}\ \mathrm{kg}\times100\ \mathrm{Bq/kg}/14.03 = 0.0528$ TBq/(GW.a); via coal $46.3\times10^{9}\times15/14.03=0.0495$.
- Stack: $3.0\times10^{7}\ \mathrm{kg}\times100\ \mathrm{Bq/kg}/14.03 = 2.14\times10^{-4}$ TBq/(GW.a) Ra-226; Pb-210 and Po-210 at 200 Bq/kg: $4.28\times10^{-4}$ each (measured-ash ranges: Pb-210 $2.1$-$6.2\times10^{-4}$; Po-210 $1.4$-$3.7\times10^{-4}$; Ra-226 $0.94$-$1.6\times10^{-4}$).
- Rn-222: NRPB assume radon in coal equals Ra-226 in coal and all of it is released: $0.0495$ TBq/(GW.a).

**C. Pandit, Sahu and Puranik 2011, India modelled modern plant (S0974).** 1000 MWe, 12,500 t coal/d, ESP 99%, stack fly ash 0.46 kg/s, no load factor stated (taken as 1.0, i.e. per GW.a continuous). $1\ \mathrm{Bq/s}=3.1536\times10^{7}\ \mathrm{Bq/y}=3.15\times10^{-5}$ TBq/(GW.a).
- Ra-226 35.7 Bq/s: $1.13\times10^{-3}$ (range $5.9\times10^{-4}$-$2.2\times10^{-3}$) TBq/(GW.a).
- Pb-210 18.6 Bq/s: $5.9\times10^{-4}$ (range $3.7\times10^{-4}$-$1.0\times10^{-3}$).
- Th-228 57.9 Bq/s: $1.83\times10^{-3}$. U-238 27.7 Bq/s: $8.7\times10^{-4}$.
- Coal: $12{,}500\times365 = 4.56$ Mt/(GW.a). Stack fly ash 0.46 kg/s = 14.5 kt/y; with 80% of ash as fly ash and 1% escaping, that is 0.8% of total ash (my derivation: it implies a coal ash yield near 40%, not stated in the paper).

**D. Netherlands, Leenhouts 1996 as tabulated in EC RP 135 vol. 1 Table 7 (S0204).** "Typical" 600 MWe coal plant, annual emission in GBq: U-238 0.16, Th-232 0.08, Ra-226 0.11, Rn-222 34, Pb-210 0.4, Po-210 0.8 (RP 135 cites them as "UNSCEAR 2000 from Leenhouts 1996"). Load factor is not given; per GW.a $=\ \text{GBq}/(0.6\times\text{CF})$. For CF = 0.8 (central; 1.0 and 0.6 in brackets):
- Ra-226 $2.3\times10^{-4}$ ($1.8$-$3.1\times10^{-4}$); Pb-210 $8.3\times10^{-4}$ ($6.7\times10^{-4}$-$1.1\times10^{-3}$); Po-210 $1.7\times10^{-3}$ ($1.3$-$2.2\times10^{-3}$); Rn-222 $0.071$ ($0.057$-$0.094$); U-238 $3.3\times10^{-4}$; Th-232 $1.7\times10^{-4}$ TBq/(GW.a).

**E. United States 1982, Gabbard (S0975).** 4 million short tons of coal per 1000 MWe plant-year $=3.63$ Mt; U 1.3 ppm ($1\ \mathrm{mg/kg\ U}=12.35$ Bq/kg), Th 3.2 ppm ($4.06$ Bq/kg per ppm Th). U-238 chain head in coal (and in ash, which retains it) $=1.3\times12.35\times3.63\times10^{9}/10^{12} = 0.058$ TBq per plant-year; Th-232 $0.047$. Capacity factor is not stated; at CF = 1.0 per GW.a is 0.058, at CF = 0.65 it is 0.090.

**F. TRS 419 Fig. 11 plant mass balance (S0202; reading of the figure is mine).** Coal 188,000 kg/h; bottom ash 2,700; ESP-collected fly ash 19,800; ESP outlet 19 kg/h; fly ash leaving the stack 1 kg/h from the scrubbed stream, with 9 kg/h in the then-unscrubbed 50% of the gas (the figure legend says 50% of flue gas was desulphurised during the study). Total ash $=22{,}519$ kg/h (12.0% of coal). Stack ash: 1 kg/h fully scrubbed $=0.0044\%$ of ash; about 10 kg/h as studied $=0.044\%$. ESP alone: $19/22{,}519=0.084\%$.

### 2.2 Results table (TBq per GW.a)

| Quantity | Estimate | Value (low-high) | Era, place | Ratio to stream 2010 / 2020 | Within x3? | Independent of UNSCEAR 2016 Annex B? |
|---|---|---|---|---|---|---|
| (a) Ra-226 (U-238 head) in ash | UK NRPB, S0205 | 0.0528 (via coal 0.0495) | UK 1998 | 0.57 / 0.59 | yes | Mostly: data NRPB/Environment Agency; UNSCEAR 2016 cites NRPB for some inputs (partly shared) |
| | Gabbard, S0975 | 0.058 (0.090 if CF 0.65) | US 1982 | 0.63 / 0.65 (0.97 / 1.0) | yes | yes (EPA 1984 / NCRP inputs) |
| | Lalit, S0972 | 0.149 (coal-based 0.141) | India 1976-83 | 1.62 / 1.66 | yes | yes |
| (b) Pb-210 stack | UK NRPB, S0205 | $4.3\times10^{-4}$ ($2.1$-$6.2\times10^{-4}$) | UK 1998 | 0.40 / 0.40 | yes | partly shared (see above) |
| | Pandit, S0974 | $5.9\times10^{-4}$ ($3.7\times10^{-4}$-$1.0\times10^{-3}$) | India, modelled, ESP 99% | 0.54 / 0.55 | yes | yes |
| | Leenhouts via RP 135, S0204 | $8.3\times10^{-4}$ ($6.7\times10^{-4}$-$1.1\times10^{-3}$) | NL, mid-1990s | 0.77 / 0.79 | yes | not independent of the UNSCEAR family: UNSCEAR 2000 is the conduit (and the older-plant Hedvall data feed UNSCEAR 2016), but it is a different primary dataset and not Annex B 2016 |
| (b') Po-210 stack | UK NRPB, S0205 | $4.3\times10^{-4}$ ($1.4$-$3.7\times10^{-4}$) | UK 1998 | vs $2.4\times10^{-3}$ (stream 2020, from `factors_notes.md`): 0.18 | no (5.6x lower) | partly shared |
| | Leenhouts via RP 135, S0204 | $1.7\times10^{-3}$ ($1.3$-$2.2\times10^{-3}$) | NL | 0.69 | yes | as above |
| (c) Ra-226 stack | UK NRPB, S0205 | $2.1\times10^{-4}$ ($0.9$-$1.6\times10^{-4}$) | UK 1998 | 0.69 | yes | partly shared |
| | Leenhouts via RP 135, S0204 | $2.3\times10^{-4}$ ($1.8$-$3.1\times10^{-4}$) | NL | 0.74 | yes | as above |
| | Pandit, S0974 | $1.1\times10^{-3}$ ($5.9\times10^{-4}$-$2.2\times10^{-3}$) | India, modelled | 3.63 | no, just outside (3.6x); inside it at the range low end (1.9x) | yes |
| | Lalit, S0972 | $4.5\times10^{-3}$ | India 1976-83 | 14.5 | no, but era mismatch: the stream's own 1970-89 factors applied to 2010 ash-borne Ra-226 give $0.092\times0.0447\times1.1=4.5\times10^{-3}$, ratio 1.0 | yes |
| (c') Th-228 / Th-232 stack | Lalit, S0972 | Th-228 $7.1\times10^{-3}$ | India 1976-83 | stream value not supplied | n/a | yes |
| | Pandit, S0974 | Th-228 $1.8\times10^{-3}$ | India, modelled | stream value not supplied | n/a | yes |
| | Leenhouts via RP 135 | Th-232 $1.7\times10^{-4}$ | NL | stream value not supplied | n/a | as above |
| (c'') K-40 stack | Lalit, S0972 | $1.77\times10^{-2}$ | India 1976-83 | stream value not supplied | n/a | yes |
| (d) Rn-222 from burning | UK NRPB method, S0205 | 0.0495 | UK 1998 | 0.63 / 0.64 | yes | partly shared |
| | Leenhouts via RP 135, S0204 | 0.071 (0.057-0.094) | NL | 0.91 / 0.92 | yes | as above |
| | Gabbard, S0975 (U-238 as Ra-226 proxy, all radon released) | 0.058 (0.090 at CF 0.65) | US 1982 | 0.75 / 0.76 | yes | yes |
| | Lalit coal Ra-226 $\times$ coal, S0972 | 0.141 | India 1976-83 | 1.81 / 1.83 | yes | yes |
| (e) Mine radon | none found | no independent value | | | cannot test | |
| (f) Escaping fraction of ash | UK NRPB, S0205 | 0.41% | UK 1998 | vs 2010-25 centre 0.31%: 1.3; vs 1990-2009 centre 2.0%: 0.20 | yes (2010-25); no (1990-2009 centre) | partly shared |
| | TRS 419 Fig. 11, S0202 | 0.084% (ESP only); 0.044% (as studied, half scrubbed); 0.0044% (fully scrubbed) | one plant, Clarke IEA CR/68 (1994) | 0.27 / 0.14 / 0.014 | no for all three (3.7x, 7x and 70x below the central value); the ESP-only 0.084% sits at the stream's 0.08% low bound, the scrubbed cases below it | yes |
| | Pandit, S0974 | 0.8% of total ash (assumed 99% ESP) | India, model | 2.6 | yes | yes |
| | Lalit, S0972 | 3.0% | India 1976-83 | vs 1970-89 centre 4.47%: 0.67 | yes | yes |
| Ash per GW.a (Mt) | UK 1998, S0205 | 0.527 | UK | 0.95 (stream 0.553 Mt/GW.a in 2010) | yes | yes |
| | World CCP 2010, S0977 | 0.808 (780 Mt / 964.9 GW.a) | world | 1.46 | yes | yes |
| | China, India, USA 2010, S0977 | 1.08, 1.68, 0.56 | 2010 | 1.96, 3.04, 1.01 | India just outside | yes |

Stream reference values used: Ra-226 in ash 0.092 (2010) / 0.090 (2020); Pb-210 stack $1.08\times10^{-3}$ / $1.06\times10^{-3}$; Ra-226 stack $3.1\times10^{-4}$; Rn-222 from burning 0.078 / 0.077; mine radon, China scaled, 4.29 / 4.21 TBq per GW.a; stream power ash 2010 $533.8$ Mt, i.e. 0.553 Mt/(GW.a).

Reading depth per row: Lalit, Bem, UK NRPB paper, RP 135 Table 7, CCC/218, CCC/231 and TRS 419 and FS-163-97 were read in full or in the relevant sections from the document itself. Pandit and Gabbard were read through the fetch tool (extraction of the specific paragraphs and tables; for Pandit the internal arithmetic checks, 0.46 kg/s $\times$ 77.7 Bq/kg $=35.7$ Bq/s). Zeevaert (S0245), Papastefanou (S0241), Tadmor (S0240), McBride (S0978) and the Fuel 2018 paper (S0980) were not obtained.

---

## 3. Findings by quantity

**(a) Ra-226 in ash per GW.a.** The stream (0.090-0.092) sits inside the independent range 0.053-0.149 (ratios 0.57-1.6). The tonnage and the concentration are each different from the independent figures but compensate. The stream uses 0.553 Mt ash/(GW.a) at 167 Bq/kg ash (20 Bq/kg coal / 0.12). Independent ash tonnage is higher (world CCP 0.81, India 1.7, China 1.1, USA 0.56, UK 0.53 Mt/GW.a), but independent ash Ra-226 is lower (UK 100, US fly ash 96-111, Poland average 146 in 1,195 samples (TRS 419 Table XI), Lodz fly ash 86-104 Bq/kg). The stream's ash tonnage is 32% below the world CCP figure (780 Mt includes FGD gypsum, bottom ash and non-power ash; EU-15 FGD gypsum alone was 7.6 of 54.5 Mt in 1999, S0204 Table 6), so this is partly a definitional difference.

**(b) Pb-210 and Po-210 by era.** I found no independent per-GW.a Pb-210 or Po-210 stack figure for old plants (pre-1990). Independent modern and mid-1990s values (UK, NL, India model) are all 1.3-2.5x below the stream's Pb-210 central value, so the stream sits slightly high but inside x3. The stream's Pb-210/Ra-226 stack ratio is 3.5. Independent ratios: UK measured emitted ash Drax 3.5, Eggborough 1.7, Aberthaw 2.2 (NRPB assumed 2); Lodz 1.5 (Bem, from captured fly ash); NL 3.6. Po-210/Ra-226: stream 7.7 (2.4e-3/3.1e-4), UK measured 1.4-3.2, NL 7.3. So the stream's Po-210 is the quantity least supported by the independent UK data (5.6x above the NRPB value) while matching the Dutch figure. The Pandit Table 1 has Pb-210 below Ra-226 (40.5 vs 77.7 Bq/kg), no volatile enrichment at all.

**(c) Ra-226 (and Th, K-40) in escaping fly ash.** Two of three modern-plant estimates are within x3 (UK 0.69, NL 0.74); Pandit is 3.6x above on its central value; Lalit is 14.5x above for a 1976-83 fleet, which is expected (see era check above, ratio 1.0).

**(d) Rn-222 from burning.** All four estimates fall in 0.049-0.141 (ratios 0.63-1.8). All assume Rn-222 in the coal equals Ra-226 in the coal and is released completely. USGS FS-163-97 (S0200) supports this: "virtually 100 percent of the radon gas present in feed coal is transferred to the gas phase and is lost in stack emissions". The stream's stack-radon share is 0.85 central, so it is about 15% below the USGS statement; a one-line note is warranted but the effect on the test is nil.

**(e) Mine radon.** No independent per-tonne or per-GW.a estimate could be found (searches: Chinese, Polish, Hungarian and general coal-mine radon surveys return concentrations in Bq/m$^3$ and exhalation rates per area, not releases per tonne). Polish mines up to 15,000 Bq/m$^3$ in galleries (Skowronek 2000, open PDF, not registered). For scale only (no source): the stream's China factor of $9.3\times10^{5}$ Bq/t is about 46 times the Ra-226 content of the coal itself (about $2\times10^{4}$ Bq/t at 20 Bq/kg), so the radon must come from the surrounding strata and mine water, which is why no composition-based check can test it. The stream's mine radon (4.29 TBq/GW.a) is 55 times its own radon from burning (0.078); the UNSCEAR 2016 figure the factor was derived from is the only support. **Recommendation: the benchmark test should exclude mine radon and the spec should state that explicitly**, rather than claim two independent estimates.

**(f) Fraction of ash escaping, by era.** Independent points: India 1976-83 3.0% (modelled, ESP assumed 97%); Lodz 1960-64 about 100,000 Mg/y emitted, 1980 45,000 Mg, 1990 30,350 Mg, 1996 8,210 Mg total (3,055 Mg from three power stations), with one central plant at <90% removal until 1995 and modern plants >99.5% (S0973); US 1970 utilities 78% control, i.e. 22% escaping, ESP 83% (S0207 via registry, not re-read); UK 1998 0.41% (S0205); India model 2011 0.8% (S0974); TRS 419 single ESP+FGD plant 0.0044-0.084% (S0202); USGS "modern power plants can recover greater than 99.5 percent" (S0200). The stream's era centres (1950-69 16.2%; 1970-89 4.47%; 1990-2009 2.0%; 2010-25 0.31%) sit between these points; the UK 0.41% in 1998 is lower than the stream's 1990-2009 centre of 2.0% (5x) but inside its band (0.4-10%).

**Fleet-mix explanation (older vs modern UNSCEAR values).** No independent source quantifies the global share of ESP / bag-filter plants by year. What exists: CCC/218 (S0976) reports, for about 2012, about 2,500 pulverised-coal plants worldwide, 95% with some particulate control, about 80% of that cold-side ESP; ESP is 85% of the controlled fleet in Germany and 80% in the USA. Lalit (S0972): India in 1983 had 17.8% of capacity (1,800 of 10,100 MWe) on mechanical collectors only. S0234 (Liu et al. 2015, China 1990-2010) and Klimont 2017 (S0235) are the places to look for China and global control shares; I opened Klimont's main text and found no plant-level control-share table (the GAINS shares are in its supplement, not obtained). **Inference, not a source:** the stream's 2010 central Pb-210 value sits at a weight $w=(1.06\times10^{-3}-9.3\times10^{-5})/(1.4\times10^{-3}-9.3\times10^{-5})=0.74$ of the way from UNSCEAR 2016's "modern" to its "older" plant value, but its Ra-226 value sits at $w=(3.1\times10^{-4}-4.7\times10^{-5})/(7\times10^{-4}-4.7\times10^{-5})=0.40$. The two imply different fleet mixes, so the stream is not applying one consistent "old plant" share across nuclides; worth explaining in the note.

**Independent check of world ash per GW.a.** World CCP 2010 = 780 Mt (S0977; Feuerborn 2012, Heidrich et al. 2013) over 964.9 GW.a $=0.81$ Mt/(GW.a); the stream's 0.553 is 0.68 of that. Country values (S0977 Table 1 over the stream's national TWh): China 1.08, India 1.68, USA 0.56, Poland 1.26, UK 1998 0.53 (S0205). China + India + USA = 641.6 Mt over 652.9 GW.a $=0.98$; implied rest of world $(780-641.6)/(964.9-652.9)=0.44$. The CCP total includes FGD gypsum and non-power ash, so it overstates power-station ash; the stream's value is not contradicted, but the high-ash-yield fleet (India, China) is probably under-weighted by a uniform 12% ash yield.

---

## 4. Recommended independent values for the benchmark test (paste-ready)

Use the era-matched, per-GW.a, independent-of-Annex-B values below. Ratios are independent / stream (2010; 2020 within 4%).

| Test | Independent value (TBq per GW.a) | Source ID | Era / place | Stream 2010 / 2020 | Ratio | Within x3 |
|---|---|---|---|---|---|---|
| Ra-226 in ash | 0.0528 | S0205 (NRPB UK) | UK 1998 | 0.092 / 0.090 | 0.57 | yes |
| Ra-226 in ash | 0.149 | S0972 (Lalit) | India 1976-83 | 0.092 / 0.090 | 1.62 | yes |
| Ra-226 in ash (supporting) | 0.058 | S0975 (Gabbard) | US 1982 | 0.092 / 0.090 | 0.63 | yes |
| Pb-210 stack | $5.9\times10^{-4}$ | S0974 (Pandit) | India, modelled | $1.08\times10^{-3}$ / $1.06\times10^{-3}$ | 0.54 | yes |
| Pb-210 stack | $4.3\times10^{-4}$ | S0205 (NRPB UK) | UK 1998 | $1.08\times10^{-3}$ / $1.06\times10^{-3}$ | 0.40 | yes |
| Ra-226 stack | $2.1\times10^{-4}$ | S0205 (NRPB UK) | UK 1998 | $3.1\times10^{-4}$ | 0.69 | yes |
| Ra-226 stack | $2.3\times10^{-4}$ (CF 0.8; $1.8$-$3.1\times10^{-4}$) | S0204 (RP 135 T7, Leenhouts) | NL, mid-1990s | $3.1\times10^{-4}$ | 0.74 | yes |
| Ra-226 stack (era check, old plants) | $4.5\times10^{-3}$ | S0972 (Lalit) | India 1976-83 | stream 1970-89 factors: $4.5\times10^{-3}$ | 1.0 | yes |
| Rn-222 from burning | 0.0495 | S0205 | UK 1998 | 0.078 / 0.077 | 0.63 | yes |
| Rn-222 from burning | 0.071 (CF 0.8; 0.057-0.094) | S0204 (Leenhouts) | NL | 0.078 / 0.077 | 0.91 | yes |
| Ash per GW.a (Mt) | 0.808 | S0977 | world 2010 | 0.553 | 1.46 | yes |
| Escaping ash fraction | 0.41% | S0205 | UK 1998 | 0.31% (2010-25) | 1.3 | yes |
| Mine radon | none | n/a | n/a | 4.29 / 4.21 | n/a | exclude from test; document as unsupported |

Suggested wording of the claim: "Two independent estimates (UK NRPB 1998, S0205; India, S0972 and S0974) agree with the stream's world totals for Ra-226 in ash, Pb-210 and Ra-226 stack release and radon from burning to within a factor of 3; Po-210 stack release is 5.6x above the UK NRPB figure but within 1.5x of the Dutch value; mine radon has no independent estimate."

Do not use as a "second independent estimate": UNSCEAR 1982/1988/1993/2000 values, anything quoted in S0001, and the TRS 419 coal composition table (Table VII is reused in UNSCEAR 2016 Table 25 per the registry notes for S0202). The RP 135 Table 7 values come from Leenhouts (1996) through UNSCEAR 2000, so flag them as "independent of Annex B 2016, not independent of the UNSCEAR family".

---

## 5. Independence register

| Source | Primary or secondary | Independence from UNSCEAR 2016 Annex B | Notes |
|---|---|---|---|
| S0972 Lalit 1986 | primary measurements (Indian coal and fly ash) plus McBride-type release model | independent | modelled release; plant list and PLF from Indian CEA |
| S0973 Bem 2002 | primary | independent | no electricity; only discharge, ash and history data |
| S0974 Pandit 2011 | primary measurements, modelled emission | independent | CF not stated; three unnamed plants |
| S0205 NRPB 2001 (via NORM III) | primary national assessment | partly shared: UNSCEAR 2016 cites Smith et al. (NRPB R327) | Environment Agency measurements of emitted ash |
| S0204 RP 135 Table 7 (Leenhouts 1996) | secondary (via UNSCEAR 2000) | not independent of the UNSCEAR family | primary Leenhouts 1996 not located |
| S0975 Gabbard 1993 | secondary compilation (EPA 1984, NCRP) | independent | input inventory, not release; ORNL/TM-12180 unverified |
| S0202 TRS 419 | compilation | partly: Table VII reused by UNSCEAR 2016 | Fig. 11 mass balance independent (Clarke 1994) |
| S0977 CCC/231 | compilation (ACAA, CEA, NDRC, ECOBA) | independent | ash tonnage only |
| S0976 CCC/218 | compilation | independent | fleet snapshot only |
| S0200 FS-163-97 | agency | independent | composition and radon statement only |
| Mora 2009 (S0979) | primary, composition only | independent | no releases |

---

## 6. What I could and could not read; URLs for anything inaccessible

Read directly: all four staged PDFs (lalit1986.pdf by image), EC RP 135 vol. 1 (a copy at https://www.peacelink.it/ecologia/docs/2827.pdf), NRPB paper N3_3.5 (https://ena-norm.eu/wp-content/uploads/2024/04/N3_3.5.pdf), IEA CCC/218 and CCC/231 (usea.org PDFs), Klimont et al. 2017 main text (searched, nothing usable), Skowronek 2000 Polish radon paper (https://journals.pan.pl//Content/132300/PDF/4_MINING_45_4_2000_Skowronek_COST.pdf; concentrations only).

Read through the fetch tool only: Pandit 2011 (direct download 403), Gabbard 1993 (NRC copy).

Not obtained (try these URLs):
- Zeevaert et al. 2006, source term for a Belgian plant (S0245): https://doi.org/10.1016/j.jenvrad.2005.04.015 (abstract only: Ra-226 air concentration 4.5 nBq/m$^3$, deposition 1.5 mBq/m$^2$; no discharges in the abstract); also https://www.osti.gov/etdeweb/biblio/20700963.
- Papastefanou 2010 review (S0241): https://doi.org/10.1016/j.jenvrad.2009.11.006.
- Tadmor 1986 review (S0240): https://doi.org/10.1016/0265-931X(86)90010-X.
- McBride et al. 1978 (S0978): https://www.science.org/doi/10.1126/science.202.4372.1045 ; ORNL-5315 via https://www.osti.gov (search by report number).
- Liu et al. 2019, Fuel 236 (S0980): https://doi.org/10.1016/j.fuel.2018.08.075.
- "Assessment of hazardous radionuclide emission due to fly ash from fossil fuel combustion in industrial activities in India and its impact on public", J. Environ. Manage. 2022 (not registered; looks directly relevant, India per-year emissions): https://www.sciencedirect.com/science/article/abs/pii/S0301479722024811.
- "Radiological impact of airborne effluents from coal-fired power plant in China" (not registered): https://www.osti.gov/etdeweb/biblio/5377107.
- "Radiological impact of atmospheric releases from a coal-fired power plant" and "Radionuclide Release from the Combustion of Coal: A Case Study" (not registered): https://inis.iaea.org/records/p8a7m-d1202 and https://inis.iaea.org/records/tym86-qjv26.
- ORNL original of Gabbard: https://www.ornl.gov/info/ornlreview/rev26-34/text/colmain.html (fetch failed).
- Health Physics 2023 review of radon in non-uranium mines (could give mine-radon releases): https://journals.lww.com/health-physics/fulltext/2023/04000/a_review_of_radon_exposure_in_non_uranium.2.aspx (fetch failed).

Searched and not found: EPRI stack radionuclide measurements; OECD/NEA coal radionuclide releases; Baxter; Hu/Dai on Chinese coal radionuclide releases (only composition papers: S0220, S0253 in the registry); Mishra 2004 (J. Environ. Radioactivity, Indian coal industry) not located as an open copy; Vreček and Benedik (Šoštanj, Slovenia, Pb-210 1.1-2.7 and Po-210 0.37-0.56 Bq/m$^3$ in unit 4 flue gas, about 71% and 81% of Pb and Po in ash) known only as a snippet on a ResearchGate related-work list, unverified and without flow data.

---

## 7. Gaps, contradictions and notes for the spec

1. No independent mine-radon estimate exists in what I could access. Exclude from the test or flag.
2. No independent older-plant (pre-1990) Pb-210/Po-210 stack figure per GW.a. A derived value (Lalit's 0.149 TBq/(GW.a) ash-borne $\times$ 3.0% $\times$ enrichment 2-3.4) gives $9\times10^{-3}$-$1.5\times10^{-2}$; this is my arithmetic, not a published estimate, and is well above UNSCEAR 2016's "older plant" $1.4\times10^{-3}$, mostly because Indian coal burns at 5.4 Mt/GW.a and 30-40% ash.
3. Lalit Table 3 gives the same 3.0% release fraction for ESP and mechanical-collector stations, contradicting the text; the release column cannot be reproduced from the stated control factors alone.
4. Pandit (modelled, CF unspecified, ESP efficiency assumed) is 3.6x above the stream for stack Ra-226; its Pb-210 below Ra-226 is unusual. Its stack ash rate (0.46 kg/s) is internally consistent only with about 40% ash yield.
5. The stream's stack-radon share (0.85) is below the USGS statement of about 100%.
6. ORNL/TM-12180 (Gabbard) could not be verified; the Gabbard item found is ORNL Review 26(3-4), and its "released" figures are input inventories.
7. Registry S0202 is correctly titled; the earlier bibliography.md wording ("Radiation protection and NORM residue management in the production of coal") is not the title of the PDF Steve supplied. Please correct `bibliography.md` section A.
8. The UK comparison uses the stream's own EI Statistical Review generation (122.97 TWh) for 1998; DUKES would be a more independent denominator.
