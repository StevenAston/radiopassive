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
- Dominant: Cs-137+, Sr-90+, Pu-241 (5–100 a); Am-241 68% at 500 a; Pu-239 and Pu-240 at 10⁴ a (BWR 15 GWd/t: Pu-239 63%, Pu-240 31%; BWR 30 GWd/t: Pu-239 54%, Pu-240 36%; BWR 50 GWd/t: Pu-239 47%, Pu-240 39%; PWR 20 GWd/t: Pu-239 61%, Pu-240 32%; PWR 40 GWd/t: Pu-239 53%, Pu-240 36%; PWR 60 GWd/t: Pu-239 45%, Pu-240 42%; corrected after verification).

**Per-head radioactive power (added 2026-10-25).** `spent_fuel_inventory_derived.csv` now carries, for every head and cooling time:
- `activity_head_bq_per_thm`: the head nuclide only (source convention, METHODS §3.2);
- `activity_all_decays_bq_per_thm`: head activity times the `groups.csv` multiplier (D24);
- `power_w_per_thm_head_only`: head activity times the head nuclide's own `e_total_mev` (ICRP-107, antineutrino excluded), so it ignores progeny;
- `power_w_per_thm_group_all_decays`: head activity times `e_per_head_decay_mev` from `groups.csv`, i.e. $P_k=A_k\bar E_k$ (METHODS §7), which already includes the progeny. **Do not multiply the all-decays activity by $\bar E_k$ as well: that would double count.**
- Example, PWR 40 GWd/t at 5 a: Cs-137+ 123 W (head only) and 530 W (group); Sr-90+ 90 W and 517 W; Ru-106+ 1 W and 171 W; Ce-144+ 8 W and 97 W; Cs-134 406 W; Pu-238 145 W; Cm-244 122 W; Eu-154 77 W; Co-60 76 W. Total 2,268 W/tHM (ICRP-107 energies for every nuclide in the table).
- Total rows use the energy of every listed nuclide from ICRP-107 (same sum as `nuclides.csv`; identical for all 122 rows there), not only nuclides in `nuclides.csv`. The earlier "known energies only" total is superseded; the 5 a PWR 40 value changes from 2,266 to 2,268 W/tHM.
- The old `activity_bq_per_thm` column (daughters collapsed into heads, Np-239 inside Am-243) was dropped because it duplicated the new columns under a different counting rule.

**Reduced-set coverage test (METHODS §4.2), re-run 2026-10-25 at 1, 2, 3, 4, 5, 30, 100, 500, 1,000, 2,000, 5,000 and 10⁴ a** (`reduced_set_coverage.csv`). Group-based: covered activity is $\sum_k m_kA_k$ and covered power $\sum_kA_k\bar E_k$ over the groups in the set, against the sum over every nuclide in the inventory (all listed nuclides and their listed progeny). Worst case of the six burnup cases at each time:

| Cooling (a) | 33-head set: activity / heat | + 10 addendum heads: activity / heat | + Np-239: activity / heat |
|---|---|---|---|
| 1 | 93.6% / 85.0% | 98.3% / 98.8% | 98.3% / 98.8% |
| 2 | 99.0% / 95.4% | 99.5% / 99.7% | 99.5% / 99.7% |
| 3 | 99.6% / 98.5% | 99.6% / 99.8% | 99.6% / 99.8% |
| 4 | 99.7% / 99.5% | 99.7% / 99.9% | 99.7% / 99.9% |
| 5 | 99.7% / 99.7% | 99.7% / 99.8% | 99.7% / 99.8% |
| 30 | 99.9% / 99.8% | 99.9% / 99.9% | 99.9% / 99.9% |
| 100 | 99.8% / 99.8% | 99.9% / 100.0% | 100.0% / 100.0% |
| 500 | 98.3% / 99.8% | 98.7% / 99.9% | 99.9% / 100.0% |
| 1,000 | 97.8% / 99.8% | 97.9% / 99.8% | 99.9% / 100.0% |
| 2,000 | 96.4% / 99.6% | 96.5% / 99.7% | 99.8% / 99.9% |
| 5,000 | 95.7% / 99.5% | 95.8% / 99.5% | 99.7% / 99.9% |
| 10,000 | 95.8% / 99.2% | 96.0% / 99.3% | 99.3% / 99.6% |

- The 33 heads are those listed above (H-3 to Cm-246); "addendum heads" are Zr-95, Nb-95, Cm-242, Ce-141, Sr-89, Te-129m, Cs-136, Nb-94, Sn-126 and Am-242m, all now in `groups.csv` (D35).
- **This supersedes the earlier "≥ 99.02% activity" claim.** That figure collapsed Np-239 into the Am-243 head and used a denominator of Carter-listed nuclides only; under the `groups.csv` definitions Np-239 is its own group (Am-243's group does not carry it), and its activity equals Am-243's: 1.2% of total at 500 a, 3.4% at 10⁴ a (BWR 50).
- **Result: the set passes at every cooling time from 2 a to 10⁴ a once the ten addendum heads and Np-239 (already a group) are in it; it does not pass at 1 a** (98.3% of activity, 98.8% of heat in the worst case, BWR 15).
- **What closes the 1 a gap:** Y-91 (0.7–0.9% of activity, 0.6–0.8% of heat; **not in `nuclides.csv`**), then Pr-144m (0.2–0.3% of activity; not in a group), Ag-110m (0.2–0.3% of heat; not in `nuclides.csv`), Ru-103 (0.1%; group `Ru103+` exists) and Fe-55 (0.1%; group `Fe55` exists). Y-91 alone lifts the worst case to 99.2% (activity) and 99.6% (heat). I have not added anything.
- **How reliable the 1–4 a rows are:** Carter's tables start at 5 a, so these rows are modelled, not tabulated.
  - Nuclides with half-life of 100 d or more are reconstructed from the 5 a column by exact back-decay with in-growth correction; short-lived progeny are set at the `groups.csv` equilibrium weight.
  - Zr-95, Nb-95 and Cm-242 are scaled to Ce-144 and Cm-244 using the 1 a decay-heat table of the JRC pin model (S0102, Table B.1, UO2, 1,000 d at 250 W/cm). The ratios come from one burnup, so treat them as ±30% (my judgement).
  - **Ce-141, Sr-89, Te-129m, Cs-136, Y-91 and Ru-103 are upper bounds**, set by assuming the same cumulative fission yield as Zr-95 and the same irradiation saturation. This is conservative for the coverage test (it overstates what the set misses). The assumption is textbook, not verified here: the ENDF/B fission-yield files could not be downloaded (see section 5).
  - Check against Carter Table 3-11 to 3-14 totals at 1 a (W/tHM, modelled vs tabulated): PWR 40 10,272 vs 10,444 (−1.6%); PWR 60 14,486 vs 13,936 (+3.9%); BWR 30 7,359 vs 7,603 (−3.2%); BWR 50 11,435 vs 11,008 (+3.9%).
  - Decay-heat shares at 1 a agree with the JRC table within a few percentage points (Ce-144+ 33% vs 36.5%; Ru-106+ about 25% vs 25.6%; Cs-134 15% vs 14.6%).
- **Convention issue for Task 0.3/METHODS owner:** under strict D24 counting, Pu-239 decays through U-235m (26 min), so every Pu-239 decay carries a second decay that no group counts (D35 omitted U-235m for its negligible energy). Counting it would lower the activity coverage (not the heat coverage) to 98.8% at 100 a, 88.5% at 500 a, 82% at 10³ a and 61% at 10⁴ a (last column of `reduced_set_coverage.csv`). Either `Pu239` needs a multiplier of about 2, or METHODS §3.2 needs a stated exemption for sub-hour isomeric transitions. Pr-144m (1.8% branch of Ce-144, 7 min) is the same kind of case.
- Hardware activation (S0101) is not in these numbers (Carter is fuel-only). Nb-94 from hardware is about 1% of activity at 10⁴ a in the SKB data.

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
- **Per-residue ε proposal for Task 3 review (not a decision).** For uranium mill tailings (stages `u_milling`, `u_mining_conv`) and uranium-bearing impoundments:
  - **0.01–0.14 for deep covered piles** ($h\approx5$–$10$ m, $E=0.2$–$0.35$, $L=0.5$–$2$ m; rows above), **0.2 kept as the upper bound** (thin or uncovered layers approach $E$); suggest a central value of about 0.03 (E = 0.35, L = 0.47 m, h = 5 m gives 0.033).
  - Cross-check with Task 1.5 (`research/wind_solar/notes.md` §8): the same slab form $\varepsilon\approx E\,L/H$ with a measured effective diffusion coefficient $D\approx1.4\times10^{-7}$ m²/s (western US tailings; WISE calculator page after Nielson 1986, which that task did not read) gives $L=0.26$ m. With that $L$: $E=0.2$–$0.35$ gives $\varepsilon=0.010$–$0.018$ at $H=5$ m, 0.005–0.009 at 10 m and 0.002–0.003 at 30 m.
  - The two analyses agree on the form; they differ on $L$ (0.26 m there, 0.47 m from S0119 here, and S0119's 200 cm "relaxation length" gives the 0.14 corner). Because $L=0.26$–$0.47$ m gives 0.002–0.033 for $H=5$–$30$ m, the **0.14 end is the least supported number**; the range for Task 3 to test is 0.002–0.14 with 0.2 as a ceiling, not 0.01–0.14.
  - Basis flag `modelled`; no uranium-tailings ε has been calibrated against a measured flux and inventory (Task 1.5 did that arithmetic only for Olympic Dam, with an unsourced inventory).
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
- ENDF/B-VIII.0 and VIII.1 neutron-induced fission yields (wanted for Y-91, Ce-141, Sr-89 and Te-129m cumulative yields): https://www.nndc.bnl.gov/endf-b8.0/zips/ENDF-B-VIII.0_nfy.zip (TLS certificate failure through the proxy), https://www-nds.iaea.org/public/download-endf/ENDF-B-VIII.0/nfpy/ and https://www.oecd-nea.org/dbdata/jeff/jeff33/downloads/JEFF33-nfy.asc (both HTTP 403). Not used; the 1–4 a bounds use an equal-yield assumption instead.
- CNSC Appendix H: fetch truncated; not read (see S0127 URL in sources file)
- Carried over from Task 1.1: UNSCEAR 2016 Annex A attachments; UNSCEAR 1982 Annex F and 1993 Annex B scans.

## 6. Derived files

- `ospar_liquid_discharges_1989_2023.csv`: year, sub_sector, quantity, value_tbq_per_a (S0122).
- `spent_fuel_inventory_derived.csv` (rewritten 2026-10-25): reactor, burnup, cooling time, group, group_head, set_membership, head and all-decays activity, head-only and group power (W/tHM), shares, basis. PWR 20/40/60 and BWR 15/30/50 GWd/t at 1, 2, 3, 4, 5, 30, 100, 500, 1,000, 2,000, 5,000, 10,000 a; 44 heads (33 base, 10 addendum, Np-239) plus `UNCOVERED_BY_SET` and `TOTAL_ALL_NUCLIDES` rows. Basis: modelled (Carter tables at 5, 30, 100, 500 a; decay of the 500 a column for 10³–10⁴ a; reconstruction for 1–4 a). Tools: S9004.
- `reduced_set_coverage.csv` (new): activity and decay-heat coverage by set (33 heads; plus the 10 addendum heads; plus Np-239), cooling time and case, with the U-235m-inclusive activity coverage.


## Verification note (2026-10-22; updated 2026-10-25)
The independent check passes with fixes. The external spot-checks that could not run on 2026-10-22 were re-run on 2026-10-25 with WebFetch, which worked. **I do not have the verifier's own list of spot-checks, so I chose these**, and I removed the "provisional" label on that basis. Re-checked against the originals:
- S0115 (WNA): world production 60,342 (2015), 47,731 (2020), 60,213 tU (2024); Kazakhstan 23,270, Canada 14,309, Namibia 7,333 tU (2024). All agree.
- S0105 (UNSCEAR 2008 Annex D, Table 1): Xe-133 6,500; Kr-85 33; I-131 about 1,760; Te-132 about 1,150; Cs-134 about 47; Cs-137 about 85; Sr-90 about 10; Ru-106 above 73; Ce-144 about 50; Pu-241 about 2.6 PBq. All agree.
- S0103 (TECDOC-1105): Atlantic 45,263.5, Arctic 38,369.1, Pacific 1,445.4, total 85,078.0 TBq (Table V); UK 35,087.5, Switzerland 4,419.3, USA 2,942, Belgium 2,120 TBq (Table IV). All agree.
- S0122 (OSPAR 2023): reprocessing tritium 5,800 (1989), 17,000 (2004 peak), 9,500 TBq (2023); all-facility beta 930 (1989) and 10 TBq (2023), consistent with the 690 and 3.6 TBq reprocessing-only values in the derived CSV.
- S0118 (TECDOC-1952): WebFetch could not reach the global tailings section, so the 938 Mm³ (Table 24) and 8,718 Mt figures were re-checked in my local text of the PDF instead.
- Not re-checked externally: S0106 Table B4, S0107, S0116, S0113 (image tables), S0121 and the NRC/CNSC documents that block download.

Confirmed internally:
- the decay from 500 a to 10⁴ a (Pu-239, Pu-240, Pu-242, Cm-245 and Am-241 recomputed);
- the ε derivation, $\varepsilon = E\,(L/h)\tanh(h/L)$.

The four open items of 2026-10-22 are closed or restated:
1. **Decay-power coverage:** closed. Per-head power is now in the CSV (section 3.1) and the coverage is recomputed from it. The earlier 99.58% figure is superseded by the table in section 3.1.
2. **Short cooling times:** closed for 1–5 a, with the 1 a result a shortfall (98.3% / 98.8%) and Y-91 as the closer; the 1–4 a rows are modelled.
3. **Missing nuclides:** Ni-59, Zr-93, Nb-93m, Nb-94, Sn-126 and Am-242m were added by the Task 0.3 addendum (D35). U-235m is deliberately omitted there; see the convention issue in section 3.1.
4. **ε for uranium tailings:** recorded as a per-residue proposal in section 3.4; it needs no METHODS change since ε is set per residue type in Phase 1.
5. **availability.csv "None" methods:** rows whose method is "None" mean *not applicable / zero by construction* (e.g. ISL before the 1960s, civil reprocessing pre-1950).
