# Stream ① Nuclear (civil fuel cycle): annotated bibliography (Task 1.2)

New sources: **S0100–S0140** (41 entries, all in `sources_task12.csv`). The ten UNSCEAR sources S0001–S0010 from Task 1.1 are reused by ID and not repeated here (S0001 = 2016 Annex B, S0003 = 2008 Annex B, S0004 = 2000 Annex C, S0007 = 1993 Annex B, S0009 = 1988 Annex B). S9004 (radioactivedecay) was used for the spent-fuel calculation.

Quality codes follow METHODS §11.3: 1 regulator, 2 compilation, 3 peer reviewed, 4 agency, 5 grey. "Read" means the cited tables were read in full text; "summary only" means the content came from a summarising fetch and should be checked on the original.

---

## A. Spent fuel and in-core inventory

| ID | Source | What it gives (stage, nuclides, years, geography) | Quality and caveats |
|---|---|---|---|
| **S0100** | Carter et al. 2012, *Fuel Cycle Potential Waste Inventory for Disposition* (US DOE FCR&D, Rev 5) | **Primary spent-fuel inventory.** Appendix C Tables C-1 to C-4: about 450 nuclides in g/MTIHM, PWR 20/40/60 and BWR 15/30/50 GWd/MTIHM, at 5, 30, 100, 500 a cooling (ORIGEN 2.2 via the RW Characteristic Data Base). Tables 3-11 to 3-15: decay heat by element group at 1, 10, 30, 50, 70, 100, 300, 500 a. US UO2 fleet. | Rank 4, read. Fuel-matrix inventory only (hardware activation not separated). **Defect:** Table C-2 Fe-55 at 500 a is 24,500 g/MTIHM for every burnup (impossible; excluded). No 1 a nuclide table and nothing beyond 500 a: later times are my decay of the 500 a column. Enrichments 2.44/3.72/4.73% (PWR), 1.79/2.93/3.74% (BWR). |
| **S0101** | SKB TR-10-13, *Spent nuclear fuel for disposal in the KBS-3 repository* (2010) | ORIGEN-S activity (Bq per canister) for 12 canister types, split into fuel matrix, **construction material, crud, control rods**: Nb-93m, Ni-63, Ni-59, Nb-94, Ag-108m, Cd-113m, Sn-121m, C-14, Cl-36, Mo-93. Swedish BWR/PWR/MOX, burnup 30–57 MWd/kgU, ages 20–60 a. | Rank 4, read. Per canister (4 PWR or 12 BWR assemblies), not per tHM. Only source found that quantifies hardware activation. Cross-check on S0100 (Cs-137 3.85e15 Bq and Sr-90 2.39e15 Bq per 3-assembly PWR canister at 57 MWd/kgU). |
| **S0102** | JRC EUR 29301 (Žerovnik et al. 2018) | Number densities of 25 key nuclides and the decay-heat contributors of a UO2 and a MOX pin at 0 (end of irradiation), 1, 10, 20, 30 a cooling. Fills the **1 a** gap. At 1 a the heat is led by Ce-144/Pr-144, Ru-106/Rh-106, Cs-134, Sr-90/Y-90, Cs-137, Cm-242, Nb-95, Zr-95. | Rank 4, read. One burnup, pin-level model, not per tHM. |
| **S0104** | UNSCEAR 2000 Annex J (Chernobyl) | Table 1: **RBMK-1000 Unit 4 core inventory** (PBq, decay-corrected to 6 May 1986): Cs-137 260, Sr-90 220, I-131 3,200, Xe-133 6,500, Ce-144 3,920, Pu-241 190, Pu-239 0.96 … Table 2: releases (four sets). | Rank 2, read. Only direct in-core inventory for an RBMK. Estimates "used in the Annex" are the right-hand column. |
| **S0106** | UNSCEAR 2013 Vol. I (Fukushima) | Table 3: inventory in Units 1–3 at shutdown (I-131 6,000 PBq, Cs-137 700 PBq); Table B3: inventory ratios; Table B4: release by nuclide. | Rank 2, read. BWR core inventories for 2,028 MW(e) (Unit 1 460 + Units 2–3 784 each; the unit ratings are my addition, not in the extract). |
| **S0112** | Nishihara et al. 2012 (JAEA) | ORIGEN2 inventories for Fukushima Units 1–4 cores and pools. | Rank 4, **not retrieved** (connection reset). URL in sources file. |
| **S0111** | NUREG-1465 (Soffer et al. 1995) | Tables 3.12/3.13: BWR/PWR release fractions **into containment** by group and phase (noble gases 1.0; halogens 0.40–0.66; alkali metals 0.30–0.65; Te 0.30; Ba/Sr 0.12; noble metals 0.005; Ce 0.0055; lanthanides 0.0052). | Rank 1, read by OCR. Fractions of core inventory, design-basis "representative", not environmental releases. |

## B. Uranium supply, civil share and fleet

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0113** | NEA/IAEA *Forty Years of Uranium Resources, Production and Demand in Perspective* (Red Book retrospective, 2006) | Appendix 7.1: **annual uranium production by country 1945–2003** (tU), about 35 countries, OECD/WOCA/non-WOCA subtotals. Appendix 3.1: **annual reactor-related requirements by country 1956–2003** (tU). Cumulative requirements 1956–2003 1,513,327 tU; production 1945–2003 2,204,732 tU. | Rank 2, read (tables are images; pages checked: 1945–54, 1965–74 production; 1956–74 requirements). Soviet/GDR/Bulgaria/China/Hungary figures are estimates. "Requirements" are acquisitions, not consumption. Erratum page inserted after printed p. 256: use the corrected production table. |
| **S0114** | NEA/IAEA Red Book 2022 (and 2024, 2026) | 2004 onward production and requirements by country. | Rank 2, **inaccessible** (proxy 502). URL in sources file. |
| **S0115** | WNA, World Uranium Mining Production | Mine production by country 2015–2024: world 60,342 (2015), 47,731 (2020), 60,213 tU (2024); Kazakhstan 23,270, Canada 14,309, Namibia 7,333 (2024). | Rank 5, read. Some entries are WNA estimates; depends on the Red Book. |
| **S0116** | IAEA RDS-2 No. 45 (2025 edition) | Operational reactors and net MW(e) 1995–2024 (Table 5), generation and share 1995–2024 (Table 6), construction starts and grid connections 1954–2024 (Table 7), every reactor with type, capacity and dates (Tables 14–17). | Rank 2, read (contents list and tables located; not transcribed). Fleet by type and year before 1995 must be rebuilt from the dated reactor tables. |
| **S0117** | IAEA PRIS online | Per-reactor annual electricity, load factors, outages. | Rank 2, **inaccessible** (JavaScript application; redirects to pris-stats.iaea.org). |
| **S0130, S0131, S0132, S0133, S0134** | IPFM RR5 (Forwood 2008, UK), RR4 (Schneider and Marignac 2008, France), GFMR 2013, Russia page and 2025 RT-1 blog, UK MoD 2000 | Reprocessing history and capacity: B205 1964–, military and civil campaigns; UP1 Marcoule 1958–1997 (13,330 t), military plutonium to 1993; RT-1 from 1976, 100–130 t/a, VVER-440 plus production-reactor, naval and research fuel; MoD plutonium accounting. | Rank 5 (S0134 rank 4), read. **None gives civil/military throughput by year.** B205 throughput only as a chart. |

## C. Measured effluents

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0122** | OSPAR 2023 liquid discharges report (2025) | **Liquid discharges 1989–2023** in TBq/a: total alpha, tritium, total beta (excl. tritium) by sub-sector (reprocessing, nuclear power, fuel fabrication and enrichment, R&D; decommissioning from about 2005) for the OSPAR states. Extracted to `ospar_liquid_discharges_1989_2023.csv`. | Rank 1, read. Aggregate by sub-sector; nuclide detail only in ODIMS (URL in file). Liquid only; no airborne. Decommissioning series start year ambiguous (19 values; text says 2006). |
| **S0121** | NRC NUREG/CR-2907 annual effluent reports and summary reports 2007–2021 | Per-reactor gaseous and liquid releases (Ci), all US plants: Kr-85, Xe-133, Xe-135, I-131, Co-58, Co-60, Cs-134, Cs-137, H-3, C-14, Fe-55. Vol. 27 = 2021 data (2024). Per-year report URLs in `notes.md`. | Rank 1, summary only (nrc.gov blocks programmatic download). Earlier volumes not located. |
| **S0123** | EC RADD | EU Member State gaseous and liquid discharges of power stations and reprocessing sites from 1995; reports RP-127, 143, 164. | Rank 1, site read, **data not pulled**. Public query builder. |
| **S0124** | IAEA DIRATA | Annual discharges from about 25 reporting countries, with UNSCEAR/EC history. | Rank 1, **inaccessible**. |
| **S0125** | RIFE 24 (2018 data) and series | UK site chapters with gaseous and liquid discharge trends for Sellafield, Springfields (fabrication), Capenhurst (enrichment) and all power stations; Tc-99, U, Th-234, Kr-85, C-14, H-3. | Rank 1, read (structure and Springfields section). Trends as figures; about 10 years per issue. |
| **S0126** | Gray, Jones and Smith 1995, J. Radiol. Prot. 15 | Annual Sellafield discharges 1951–1992 by nuclide (alpha and beta-gamma, liquid and airborne). | Rank 3, **paywalled**; only an AMAP figure (image) was reached. |
| **S0127** | CNSC NPGS regulatory oversight reports 2017–2023 | CANDU tritium and other emissions by site versus derived release limits (Appendix H). | Rank 1, appendix **not read** (page truncated by the fetch). Pre-2017 not located. |
| **S0128, S0129, S0140** | Korea C-14 paper (2024); JNC Tokai FY2001; Japan MOE tritium page | Fragments only: Korean PWR C-14 about 3% of gaseous effluent (2012–21); one Japanese reprocessing site-year; ALPS 22 TBq/a tritium target. | Ranks 3–4. **No national Japanese or Korean effluent dataset found.** |

## D. Mining, milling, waste

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0118** | IAEA-TECDOC-1952 (2021) | Global uranium mill tailings: 938 Mm³ (2004, no Africa), 8,718 Mt (2019; South Africa 7,000 Mt gold tailings; Canada 202, USA 235, Namibia 350, Kazakhstan 165, Germany 240 Mt). Rössing 2010–2018 tailings and **waste rock** by year. Global mine waste 20,000–25,000 Mt/a (all commodities). | Rank 2, read. Both global estimates are incomplete; the 8,718 Mt is dominated by gold-mine tailings that carry uranium but were not milled for it. |
| **S0119** | IAEA-TECDOC-1403 (2004) | History (pre-1940s radium era, hand-sorted ore, no tailings; 1940s–60s military rush). Annex I Table I-7: RADON-model parameter set for tailings (Ra-226 3.7 Bq/g, dry density 1.89 g/cm³, E = 0.35, D = 4.67e-3 cm²/s, relaxation length 200 cm). | Rank 2, read. A single case-study parameter set, not a survey. |
| **S0120** | EPA TENORM Vol. 2 (2008) | 40 CFR 192 radon flux standard 20 pCi/m²/s (0.74 Bq/m²/s); overburden flux comparable to tailings. | Rank 4, read. Regulatory cap, not a measurement. |
| **S0109, S0110** | CDC 1980 memo; NM EID 1983 | Church Rock 16 Jul 1979: about 1,100 t tailings and 94 million gallons (about 356,000 m³) liquor. | S0109 rank 4, read (OCR poor); S0110 **inaccessible**. No activity totals in S0109. |

## E. Sea disposal

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0103** | IAEA-TECDOC-1105 (1999) | Annexes A.1–A.22: waste by country, site and year, 1946–1993 (GBq alpha, beta-gamma, H-3; package counts and weights). Total about 85 PBq (Atlantic 45.3, Arctic 38.4, Pacific 1.4). Kara Sea reactors 10 without fuel plus 6.6 with: 37.0 PBq at dumping (IASAP) or 88.8 PBq (White Book). | Rank 2, read. **No civil/military flag by producer.** Soviet solid LLW in Sr-90 equivalents; Korea no data; internal inconsistencies noted in `sources_task12.csv`. |

## F. Accidents

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0105** | UNSCEAR 2008 Annex D | Best current Chernobyl release by nuclide (PBq): Xe-133 6,500; Kr-85 33; I-131 ~1,760; Te-132 ~1,150; Cs-137 ~85; Cs-134 ~47; Sr-90 ~10; Ru-103 >168; Ru-106 >73; Ba-140 240; Zr-95 84; Mo-99 >72; Ce-141 84; Ce-144 ~50; Np-239 400; Pu-238 0.015; Pu-239 0.013; Pu-240 0.018; Pu-241 ~2.6; Cm-242 ~0.4. | Rank 2, read. Differs from S0104 for refractory elements. |
| **S0107** | UNSCEAR 2020/2021 Vol. II Annex B | Fukushima: post-2013 air releases (I-131 120–754 PBq; Cs-137 8–29 PBq; Terada 2020: 120 and 10), marine releases (Cs-137 3.5–5.6 PBq direct; I-131 9–13; H-3 0.3–0.7; Sr-90 0.04–1). | Rank 2, read. |
| **S0106** | UNSCEAR 2013 Table B4 | Air release by nuclide (Bq): Xe-133 7.32e18 (61% of inventory), I-131 1.24e17 (2.1%), Cs-137 8.83e15 (1.3%), Cs-134 9.01e15, Te-132 2.85e16, I-133 9.56e15, Cs-136 1.77e15. | Rank 2, read. Eight nuclides only; Kr-85, Sr-90 and Pu not tabulated here. |
| **S0108, S0138, S0139** | NRC 1979 letter; Rogovin report; NRC fact sheet | TMI-2: noble gases 1–40 MCi (NRC), 2.4 MCi (alternative), about 10 MCi (licensee consultants); I-131 about 14 Ci. Rogovin (not retrieved) is the usual source of 2.5 MCi and 13–17 Ci. | S0108 rank 1, summary only; S0138 **inaccessible**; S0139 rank 1. No nuclide table. |

## G. Construction and decommissioning

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0136** | Peterson et al. 2005 (UC Berkeley) | Steel and concrete per average MW(e) for 1970s PWR/BWR (40 t, 90 m³), EPR/ABWR (+25% steel, +70% concrete), ESBWR/AP-1000 (lower), HTGRs; wind, coal, gas comparators. | Rank 5, read. Steel and concrete only; no copper or other metals. |
| **S0137** | Hertwich et al. 2015 PNAS | Candidate for multi-metal intensities per technology. | Rank 3, **inaccessible**; details unverified. |
| **S0135** | NEA 7201 (2016), *Costs of Decommissioning Nuclear Power Plants* | Appendix 3.A4: waste volumes: US PWR 180,000–400,000 ft³ (5,100–11,300 m³), US BWR 400,000–700,000 ft³ (11,300–19,800 m³); no proportionality to capacity. Fig. 3.A3.5: waste tonnes by category for European plants (chart). | Rank 2, read. Volumes only; activity is not given. |

---

## Existing sources reused (Task 1.1)

- **S0001, S0003, S0004, S0009:** release factors by reactor type and period (1970–2010), reprocessing (1970–2010), mining and milling radon, conversion/enrichment/fabrication c.1980–85, material intensities. See `research/unscear_notes.md`.
- Gaps confirmed here: UNSCEAR has no post-1985 conversion, enrichment or fabrication data, no spent-fuel or in-core inventories, no civil/military split, no decommissioning releases, and no accident source terms (these are in S0104–S0107).

## H. Fission-product yields and fission mix (added 2026-10-25)

| ID | Source | What it gives | Quality and caveats |
|---|---|---|---|
| **S0141** | Brown et al. 2018, ENDF/B-VIII.0, *Nucl. Data Sheets* 148, 1-142 (fission-product-yield sublibrary) | Cumulative yields (MF=8, MT=459) for U-235, Pu-239, Pu-241 (thermal) and U-238 (0.5 MeV) used to scale Y-91, Sr-89, Ru-103, Ce-141, Te-129m and Cs-136 from Zr-95 in the 1-4 a spent-fuel rows. | Rank 3, read from Steve's local copy. The sublibrary is unchanged from ENDF/B-VII.1 (England and Rider, 1992). Evaluated, not measured at our burnups. |
| **S0142** | An et al. (Daya Bay) 2017, *Phys. Rev. Lett.* 118, 251801 | Core-average fission fractions U-235 0.571, Pu-239 0.299, Pu-241 0.054, U-238 0.076. | Rank 3. Reactor-simulation averages for Chinese PWR cores, not batch-integrated shares; low and high mixes in notes.md are my assumptions. |
