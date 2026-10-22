# Stream ① Nuclear (civil fuel cycle): notes (Task 1.2)

New sources S0100–S0140 (41). Reused: S0001, S0003, S0004, S0009 (UNSCEAR), S9004 (radioactivedecay). Companion files: `bibliography.md`, `availability.csv`, `sources_task12.csv`, plus two derived tables, `ospar_liquid_discharges_1989_2023.csv` and `spent_fuel_inventory_derived.csv`. Throwaway scripts are in the scratchpad (`.../scratchpad/task12/`), not in outputs.

## 1. Method

1. Started from the METHODS §15 deferred list and the stage codes in SCHEMA §5.2. Searched primary and agency sources first (UNSCEAR, IAEA, NEA, regulators), then compilations.
2. Read the tables directly (OCR with tesseract for scans). Anything seen only through a summarising fetch is marked "summary only" in the bibliography.
3. Spent-fuel inventory: parsed Carter 2012 Appendix C (S0100), grouped daughters into heads (all-decays convention, D24), decayed the 500 a column forward to 1,000, 2,000, 5,000 and 10,000 a with `radioactivedecay` (S9004, ICRP-107). Basis for all post-500 a values is **modelled**. Decay power uses only nuclides with energies in `nuclides.csv`.
4. Radon epsilon: my own **modelled** derivation from S0119 Annex I parameters (section 3.4).
5. Availability status follows the brief: measured, compiled, modelled_possible, no_data.

## 2. Coverage summary (availability.csv)

| Stage | 1950s | 1960s | 1970s | 1980s | 1990s | 2000s | 2010s | 2020s |
|---|---|---|---|---|---|---|---|---|
| reactor_operation (effluent) | modelled | modelled | compiled | compiled | compiled | compiled | compiled | measured |
| reactor_operation (in-core inventory) | modelled | modelled | modelled | modelled | modelled | modelled | modelled | modelled |
| reprocessing | modelled | modelled | compiled | compiled | measured | measured | measured | measured |
| sea_disposal | compiled | compiled | compiled | compiled | compiled (to 1993, zero after) | zero | zero | zero |
| conv_enrich_fab | modelled | modelled | modelled | modelled | compiled (OSPAR, partial geography) | compiled | compiled | compiled |
| u_mining/milling/spent_fuel/construction | modelled_possible from 1950s | | | | | | | |
| decommissioning | no_data | no_data | modelled | modelled | modelled | compiled | compiled | compiled |
| accident | no_data (Windscale 1957 and Kyshtym are military) | no_data | compiled (TMI; Church Rock modelled) | compiled (Chernobyl) | no_data | no_data | compiled (Fukushima) | no_data |

Pre-1950: radium era only; qualitative (S0119); `no_data` for quantities. Red Book production starts 1945 (507 tU).

## 3. Key factor ranges (with source IDs)

### 3.1 Spent fuel per tHM (S0100, modelled beyond 500 a)

Total activity of PWR 40 GWd/t, Bq/tHM: 2.48e16 (5 a), 9.46e15 (30 a), 1.83e15 (100 a), 1.35e14 (500 a), 7.85e13 (1,000 a), 4.29e13 (2,000 a), 2.84e13 (5,000 a), 2.09e13 (10⁴ a).
- PWR 20/60 at 5 a: 1.40e16 / 3.40e16. BWR 15/30/50 at 5 a: 1.12e16 / 1.89e16 / 2.87e16.
- Decay power, W/tHM (PWR 40, same eight times): 2266, 930, 373, 117, 67, 35, 23, 16. PWR 60 at 5 a: 3711; BWR 30 at 5 a: 1601.
- Dominant: Cs-137+, Sr-90+, Pu-241 (5–100 a); Am-241 68% at 500 a; Pu-239 (~35%) and Pu-240 (~24%) at 10⁴ a.

**Reduced set (33 heads)**: H-3, C-14, Ni-59, Ni-63, Co-60, Kr-85, Sr-90, Zr-93, Tc-99, Ru-106, Sb-125, I-129, Cs-134, Cs-135, Cs-137, Ce-144, Pm-147, Sm-151, Eu-154, Eu-155, U-234, U-236, Np-237, Pu-238, Pu-239, Pu-240, Pu-241, Pu-242, Am-241, Am-243, Cm-244, Cm-245, Cm-246 (daughters in head activity as reported).
- Covers at least 99.02% of activity (PWR 60, 10⁴ a) and 99.58% of known-energy decay power, in all six burnup cases for 5 a to 10⁴ a.
- Add Nb-94, Sn-126, Am-242m, Cm-242 to reach at least 99.30% everywhere. Hardware activation (S0101) makes Nb-94 about 1% at 10⁴ a.
- **1–5 a gap**: Carter tables start at 5 a. At 1 a also need Zr-95, Nb-95, Cm-242 (S0102 Table B.1). The set above is valid only from 5 a.

### 3.2 In-core inventory per GW(e)

- RBMK-1000 Unit 4 (S0104): Cs-137 260 PBq, Sr-90 220 PBq, I-131 3,200 PBq, Pu-241 190 PBq.
- Fukushima Units 1–3, 2,028 MW(e) (S0106): I-131 6,000 PBq, Cs-137 700 PBq, so about 2,960 and 345 PBq per GW(e). Rating figures are mine.
- No published inventories for PHWR, GCR or FBR. Core mass per GW(e) not sourced: model by scaling S0100 per-tHM inventory (short irradiation times, so use burnup-appropriate equilibrium, not discharge).

### 3.3 Uranium production and civil share (S0113, S0115)

- World production, tU: 1950 4,804; 1954 15,085; 1965 31,564; 1970 37,736; 1974 40,875; 1980 69,692 (peak); 2003 35,492; 2015 60,342; 2020 47,731; 2024 60,213. Cumulative 1945–2003 2,204,732 tU.
- World civil requirements, tU: 1956 770; 1960 1,655; 1965 4,928; 1970 13,964; 1974 18,499. Ratio to production: 1965 0.156, 1970 0.370, 1974 0.453. Requirements are acquisitions, not consumption; use as an upper bound for the D16 default civil share φ.
- Estimates (not statistics) for USSR, GDR, Bulgaria, China, Hungary. Red Book 2022 (2004 onward) was inaccessible; WNA (S0115) covers 2015–2024 only, so 2004–2014 is a gap.
- Red Book App. 7.1 is image tables (PDF pp. 257–262); App. 3.1 PDF pp. 177–179. Needs transcription (Task 1.9).

### 3.4 Mining, milling and radon epsilon

- Radon release from mining and milling: UNSCEAR 66–75 TBq/(GW a) (S0001, S0003).
- **Radon escape fraction, modelled.** Exhalation flux $J = E\,\rho\,A\sqrt{\lambda D_e}$; atoms emitted per second per unit area $=J/\lambda$. For a pile of thickness $h$ and diffusion length $L=\sqrt{D/\lambda}$,
$$\varepsilon = \frac{J/\lambda}{\rho A h} = E\,\frac{L}{h}\tanh\!\left(\frac{h}{L}\right)$$
  Parameters from S0119 Table I-7: $E=0.35$, $\rho=1.89$ g/cm³, $A=3.7$ Bq/g, $D=4.67\times10^{-3}$ cm²/s, giving $L=0.47$ m and $J=2.4$ Bq m⁻² s⁻¹. The same table quotes a "relaxation length" of 200 cm, which I treat as a moisture-dependent alternative.

| E | L (m) | h = 1 m | 2 m | 5 m | 10 m |
|---|---|---|---|---|---|
| 0.20 | 0.47 | 0.092 | 0.047 | 0.019 | 0.009 |
| 0.20 | 1.0 | 0.152 | 0.096 | 0.040 | 0.020 |
| 0.20 | 2.0 | 0.185 | 0.152 | 0.079 | 0.040 |
| 0.35 | 0.47 | 0.160 | 0.083 | 0.033 | 0.017 |
| 0.35 | 1.0 | 0.267 | 0.169 | 0.070 | 0.035 |
| 0.35 | 2.0 | 0.323 | 0.267 | 0.138 | 0.070 |

  Deep dry piles (5–10 m) give $\varepsilon\approx0.01$–$0.14$; only thin covers approach $E$. **The METHODS provisional default of 0.2 (bounds 0.05–0.35) looks high for deep impoundments** and is a candidate for revision (flag to Task 0.3/METHODS owner). Caveat: one parameter set, uniform pile, no moisture or cover effects, no temporal drying.
- UNSCEAR flux convention: 10 Bq m⁻² s⁻¹ operating, 1 abandoned, 0.1 closed (S0003). 1 TBq/ha/a = 3.17 Bq m⁻² s⁻¹. Regulatory cap 0.74 Bq m⁻² s⁻¹ (40 CFR 192, S0120).
- Tailings: 938 Mm³ (2004, no Africa); 8,718 Mt (2019), of which 7,000 Mt is South African gold tailings, leaving about 1,718 Mt uranium-mill tailings (S0118).
- Waste rock: Rössing 2010–2018 11.5–40.0 Mt/a against 6.9–12.2 Mt/a tailings, i.e. 1.3–3.5 times tailings mass (S0118). Single mine; open-pit.
- Church Rock 16 Jul 1979: about 1,100 t tailings, 94 million gallons (about 356,000 m³) liquor (S0109). No activity total found; model from tailings Ra-226 and liquor concentrations.
- ISL: no source found with radiological factors (availability.csv: 1950s no_data, then modelled_possible from production by country).

### 3.5 Effluents

- OSPAR totals, TBq/a (S0122): reprocessing beta 690 (1989) to 3.6 (2023); reprocessing H-3 5,800 (1989), peak 17,000 (2004), 9,500 (2023); fabrication and enrichment beta 110 (1989) to 0.00433 (2023), a factor of about 2.5e4; fabrication and enrichment alpha 0.41 to 0.006; decommissioning 2023 alpha 0.068, H-3 8.63, beta 4.8.
- US reactors (S0121): per-reactor Ci, median PWR liquid H-3 538 Ci (2021). Summary reports list 2007–2021 only.
- UK: RIFE trends are graphical (S0125). Sellafield 1951–92 only in S0126 (paywalled).
- Conversion, enrichment and fabrication after 1985: the only measured series are OSPAR (UK, France, Netherlands, Germany partly) and RIFE. UNSCEAR has none.
- **Carter vs OSPAR/UNSCEAR**: not reconciled; they measure different things (inventory vs releases) and no direct comparison is intended.

### 3.6 Sea disposal (S0103)

- Total about 85 PBq, 1946–1993: Atlantic 45.26 (UK 35.09, Switzerland 4.42, USA 2.94, Belgium 2.12), Arctic 38.37 (former USSR reactors 36.9), Pacific 1.45. NE Atlantic peak about 7 PBq in 1980.
- Inconsistency: 36,876 TBq (Table V) vs 37,019 TBq (Table III) for Soviet reactors. White Book gives 88.8 PBq for the same Kara Sea reactors, using a different reference date.
- No civil/military flag by producer. Lenin icebreaker (civil, 1967) is the only clearly civil Soviet item; the rest need a D16-style default.

### 3.7 Accidents

- Chernobyl, PBq (S0105, UNSCEAR 2008): Xe-133 6,500; Kr-85 33; I-131 ~1,760; Te-132 ~1,150; Cs-137 ~85; Cs-134 ~47; Sr-90 ~10; Ru-103 >168; Ru-106 >73; Ba-140 240; Zr-95 84; Ce-144 ~50; Np-239 400; Pu-241 ~2.6. **The 2000 edition (S0104) gives higher refractory values** (Ce-144 ~116, Zr-95 196, Np-239 945). Recommend 2008 values as base, 2000 as upper bound.
- Fukushima air release, Bq (S0106): I-131 1.24e17; Cs-137 8.83e15; Cs-134 9.01e15; Te-132 2.85e16; Xe-133 7.32e18 (61% of inventory). Later ranges (S0107): I-131 120–754 PBq (100–500 in 2013); Cs-137 6–29 PBq. Direct ocean: Cs-137 3.5–5.6 PBq; I-131 9–13; H-3 0.3–0.7 (S0107).
- TMI-2 (S0108): noble gases 1–40 MCi (alternative 2.4; consultants ~10), I-131 ~14 Ci. Usually quoted 2.5 MCi and 13–17 Ci come from the Rogovin report (S0138, not retrieved). Spread of an order of magnitude or more on noble gases; treat as a range, not a point.
- NUREG-1465 (S0111) gives release fractions into containment, not to the environment.

### 3.8 Construction and decommissioning

- Construction (S0136): 40 t steel and 90 m³ concrete per average MW(e), 1970s US LWR; about 36,000 t steel and 81,000 m³ concrete per GW rated at capacity factor 0.9 (my conversion). Gen III +25% steel, +70% concrete. Multi-metal intensities (Hertwich, S0137) not read.
- Decommissioning waste volume (S0135; 1 ft³ = 0.0283 m³): US PWR 5,100–11,300 m³; US BWR 11,300–19,800 m³; no proportionality to capacity. Activity not given.

### 3.9 Civil/military split at dual-use reprocessing

No annual throughput found for Sellafield B205, Marcoule UP1 or Mayak RT-1.
- Sellafield B205: nominal 1,500 t/a; Magnox about 47,000 t in total; military campaigns for Calder Hall/Chapelcross fuel ended after 1995; B204 (1952–64) military; THORP (1994–2018) civil (S0130, S0134).
- Marcoule UP1: 1958–1997, 13,330 t; military plutonium ended 1993 (S0131).
- Mayak RT-1: started 1976, VVER-440 fuel, 100–130 t/a typical (design 400), 993 t over 2016–2024; also naval, research and production-reactor fuel (S0132, S0133).
- Proposed approach (not implemented): exclude and flag site-years (rule from METHODS) or bound by plutonium mass balance (UK MoD net 3.2 t for weapons; French military plutonium about 6 t). Gray 1995 (S0126) may tabulate throughput but is paywalled.

## 4. Open issues

1. `nuclides.csv` lacks Ni-59, Zr-93 and Nb-93m. Under D24 Pu-239 needs U-235m (multiplier about 2) and Am-243 needs Np-239; `groups.csv` currently treats these as single or separate groups. Flag for Task 0.3 and the pipeline.
2. Carter Table C-2 Fe-55 at 500 a (24,500 g/MTIHM for every burnup) is a clear defect; excluded.
3. Fuel-only inventories; hardware activation from SKB only (Swedish fleet).
4. Post-500 a spent-fuel values are my decay calculation, not published.
5. OSPAR decommissioning start year (2005 vs 2006) ambiguous; rows excluded from the derived CSV.
6. No post-1985 UNSCEAR-style factors; modelled before 1990 by extrapolating UNSCEAR (S0001, S0003, S0004, S0009).
7. Production data 2004–2014 gap (Red Book 2006 retrospective to 2003; WNA 2015+).
8. Civil requirements are acquisitions; use as a bound only.
9. No ISL, PHWR, GCR, FBR radiological data.
10. Non-OSPAR geography for effluents (Canada, Japan, Korea, Russia, China, India) mostly missing.

## 5. Inaccessible or unread URLs (for Steve to try)

- Red Book 2022 PDF: https://git2.oecd-nea.org/jcms/pl_28569/upload/docs/application/pdf/2023-04/7634_uranium_-_resources_production_and_demand_2022.pdf (landing page https://www.oecd-nea.org/jcms/pl_28569/uranium-resources-production-and-demand-red-book)
- PRIS: https://pris.iaea.org/PRIS/home.aspx (redirects to pris-stats.iaea.org; JavaScript application)
- DIRATA: https://dirata.iaea.org (contact Dirata.Contact-Point@iaea.org)
- Rogovin report (NUREG/CR-1250): https://tmi2kml.inl.gov/Documents/Common/NUREGCR-1250V1,%20TMI,%20A%20Report%20To%20The%20Commissioners%20And%20To%20The%20Public%20(Rogovin%20Report)%20(1980-01).pdf
- NM EID 1983 Church Rock report (Millard et al.), cited via https://pmc.ncbi.nlm.nih.gov/articles/PMC3915248
- Nishihara 2012 (JAEA): https://f-archive.jaea.go.jp/dspace/handle/faa/211516
- Hertwich 2015 PNAS: https://pmc.ncbi.nlm.nih.gov/articles/PMC4443343/
- Gray et al. 1995 (paywalled): via https://amap.no/work-area/document/678; journal URL not verified
- NRC (blocks programmatic download): NUREG/CR-2907 Vol. 27 https://www.nrc.gov/docs/ML2413/ML24134A119.pdf; series page https://www.nrc.gov/reactors/operating/ops-experience/tritium/plant-info.html; TMI letter https://www.nrc.gov/docs/ML1921/ML19210E952.pdf
- CNSC Appendix H: fetch truncated; not read (see S0127 URL in sources file)
- Carried over from Task 1.1: UNSCEAR 2016 Annex A attachments; UNSCEAR 1982 Annex F and 1993 Annex B scans.

## 6. Derived files

- `ospar_liquid_discharges_1989_2023.csv`: year, sub_sector, quantity, value_tbq_per_a (S0122).
- `spent_fuel_inventory_derived.csv`: reactor, burnup_gwd_per_thm, cooling_time_a, group_head, activity_bq_per_thm, share_of_total. PWR 20/40/60 and BWR 15/30/50 GWd/t at 5, 30, 100, 500, 1,000, 2,000, 5,000, 10,000 a; 33 heads plus other_unlisted and totals (activity and W/tHM). Basis: modelled from S0100 with S9004. Daughters are collapsed into heads.
