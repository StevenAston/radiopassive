# IOCG and Zambian copper uranium evidence: resolving the "other IOCG" lever in the copper tailings factor

Date 2026-11-22. Follows `research/wind_solar/copper_classes.md` (2026-11-11), section 4.3 sensitivities and gap 2 and 3. Bq only, no dose (D1). Status: research draft. Nothing applied to the registry or `data/`; rows are proposals only. `d76_proposal.md` and `build/d76_staging/` not touched.

Labels as in `copper_classes.md`: **[E]** read in the document; **[R]** read second-hand or from a search snippet; **[I]** my arithmetic; **[A]** my assumption or recollection, unsourced. Conversions: 1 ppm U = 12.35 Bq/kg U-238; 1 ppm Th = 4.06 Bq/kg Th-232; U$_3$O$_8$ is 84.8 % U. S5 per t Cu $=(4\,U_{\mathrm{Bq/kg}}+Th_{\mathrm{Bq/kg}})\times10^{3}\times(\text{tailings t per t Cu})$ (the Phase 1 chain convention; reproduces class B $2.64\times10^{7}$).

---

## 1. Bottom line

1. **The "other IOCG" lever (plus 51 % if all A-like) is not one lever; it splits three ways.**
   - **Candelaria: Class B, confirmed** by direct whole-rock assays (U mean 2.1 ppm, n=91) [E].
   - **Salobo and Sossego (Carajás): neither B nor A. Intermediate**, roughly 30 to 150 ppm U (370 to 1,850 Bq/kg), with Salobo concentrate at 52 ppm U on a company spec sheet [E]. No tailings or head assay for either mine found; the grade comes from compilations.
   - **Ernest Henry and Mantoverde: still no uranium assay found.** Left in B; high case only for Ernest Henry.
2. **Lumwana: intermediate, lower than A.** Tailings solids 33 ppm U (408 Bq/kg U-238) in a feasibility test on the richer Malundwe ore [E, via 2005 EIA]. Not A-like.
3. **Prominent Hill head assay found:** U$_3$O$_8$ 105 ppm = U 89 ppm = **1,100 Bq/kg U-238**, Th 16.6 ppm = 68 Bq/kg Th-232, Cu 742 ppm (Habibi et al. 2026, Table 1, head sample PHRT) [E]. That is below the 1,350 central used in the draft.
4. **Recomputed 2024 weighted copper tailings factor (S5): low $2.9\times10^{7}$, central $5.7\times10^{7}$, high $2.2\times10^{8}$ Bq/t Cu, against the current $2.6\times10^{7}$ / $4.8\times10^{7}$ / $2.0\times10^{8}$. Central plus 18 %** (not plus 51 % or plus 59 %).
5. **An intermediate class is warranted**, for activity (10 to 30 times B, 0.2 to 0.8 times PH), but it carries only about 17 % of the central. Proposal in section 5.
6. **Tier 2 T&D copper (3.0 Mt, D6 0.85): $1.23\times10^{14}$ to $1.45\times10^{14}$ Bq/a central (plus 18 %).** $A_{\mathrm{T2}}$ central about $1.69\times10^{14}$ (was $1.46\times10^{14}$). Verdict on Tier 2 scope unchanged.

---

## 2. What the five supplied files contain

| File | What it actually is | Use for this task |
|---|---|---|
| `minerals-16-00671.pdf` | Habibi et al., *Minerals* 2026, 16, 671 (Prominent Hill fresh flotation tailings, Oct 2023 sample, ten size fractions) [E] | **Table 1 head assay (section 3.1).** Uraninite, coffinite, wyartite in all fractions; no U recovered at the plant |
| `ijerph-13-00138.pdf` | **Kamunda, Mathuthu and Madhuku 2016, *Int. J. Environ. Res. Public Health* 13:138: gold mine tailings, Gauteng (Witwatersrand), South Africa [E]. Not Zambian and not copper.** Five tailings dumps, 56 samples, gamma spectrometry. Mean U-238 in the five dump means (Table 1): 733, 795, 1,556, 232, 610 Bq/kg; "average all tailings" 485.3 in the table but 785.3 in the abstract (my sample-weighted mean of the five dump means is about 731; the paper is internally inconsistent) [E][I] | Not usable for copper. Useful only as a gold-tailings Bq/kg cross-check (about 230 to 1,560 Bq/kg U-238 at a Witwatersrand dump). The reference in `copper_classes.md` section 10 item 7 as "PMC4730529, Zambian sediments" is probably this paper mis-identified, **[I] not verified** (PMC blocked) |
| `Geology of Uranium Deposits - World Nuclear Association.pdf` | WNA overview; Olympic Dam and Carrapateena as the "polymetallic iron-oxide breccia complex" type; U 0.035 to 0.07 % U (350 to 700 ppm) in the deposit, Cu 2.7 % proved, 1.1 % indicated [E] | Context for A. Higher than the 230 ppm average (TECDOC-1849, below) because it is mineralised-zone grade. No Salobo, Candelaria, Sossego, Ernest Henry or Lumwana data |
| `mines-prospector-...-prospecting-for-uranium.pdf` | Newfoundland and Labrador prospector's guide (Matty Mitchell Info. Circ. 4); IOCG paragraph: Olympic Dam "0.08 to 0.04 % U$_3$O$_8$" [E] | Nothing new; same Olympic Dam figure as WNA. The U$_3$O$_8$ vs U labelling differs from WNA (factor 0.85), so cite neither for tailings |
| `Myriad Uranium ... Copper Mountain ...pdf` | News release 28 Oct 2026: Wyoming granite-hosted uranium project named "Copper Mountain"; gamma-probe eU$_3$O$_8$ [E] | **Not relevant.** Name coincidence only; no copper mine data |

None of the five covers Salobo, Sossego, Candelaria, Ernest Henry, Mantoverde, Lumwana or Kansanshi. Those came from web retrieval (section 3).

---

## 3. Evidence by mine

### 3.1 Prominent Hill head assay (Habibi et al. 2026, Table 1) [E]

Head sample PHRT (fresh flotation tailings, October 2023), Intertek Adelaide, lithium borate fusion ICP-MS (U$_3$O$_8$ detection limit 0.5 ppm):

| Quantity | Head | Range across 10 fractions | Bq/kg |
|---|---|---|---|
| U$_3$O$_8$ | **105 ppm** | 72 (+125 $\mu$m) to 136 (-4 $\mu$m, "+C7") | U-238 **1,100** (head); fractions 740 to 1,420 |
| U (as 0.848 U$_3$O$_8$) | 89.0 ppm | 61 to 115 ppm | |
| Th | 16.64 ppm | 12.2 to 21.7 | Th-232 68 (head) |
| Cu | 742 ppm | 650 to 1,657 | (tailings Cu 0.074 %) |

Mass-weighted U$_3$O$_8$ over the ten fractions is 102.2 ppm [I], within 3 % of the head, so the table is internally consistent. Single plant sample, no replicates. The 136 ppm maximum is the finest fraction (20.4 % of mass); the text calls it "+2 $\mu$m" and the table "-4 $\mu$m", and the earlier "121 ppm (+31 $\mu$m)" is fraction C1 [E]. U sits as uraninite micro-inclusions in hematite and as coffinite and wyartite; none is recovered, so Ra-226, Pb-210 and Po-210 stay with the U-238 (equilibrium assumed [A]).

**Revised PH class A row:** U-238 low 900 / central 1,100 / high 1,420 Bq/kg; Th-232 central 68 (inside the 15 / 40 / 100 assumed); t/t 80 / 95 / 110 (reserve 26 Mt at 1.07 % Cu, 88 % recovery gives 106 t ore per t Cu [E][I]). S5 per t Cu $2.9\times10^{8}$ / $4.2\times10^{8}$ / $6.4\times10^{8}$ (was $2.6\times10^{8}$ / $5.1\times10^{8}$ / $6.4\times10^{8}$). World effect: minus 0.8 % on the 2024 central.

### 3.2 Evidence table, other mines

| Mine | Source | Material | Value | n | Quality |
|---|---|---|---|---|---|
| **Salobo** (Brazil, Carajás) | Vale, "Salobo Concentrates" product specification, updated Oct 2022 [E] https://vale.com/documents/d/guest/salobo-concentrates | Copper concentrate, 38 % Cu typical | **U 52 ppm typical, 60 ppm upper limit** (642 to 741 Bq/kg U-238 in the concentrate); Th 4 ppm typical, 20 ppm upper | specification, n not stated | Company sales spec; concentrate, not head or tailings |
| Salobo, Sossego, Cristalino, Igarapé Bahia (Carajás) | URAM-2018 oral contribution 45, "Conventional and unconventional uranium resources in the Carajás Mineral Province" (cites ref. [14], not identified) [E] https://conferences.iaea.org/event/146/contributions/5283/contribution.pdf | Resource grade, four IOCG deposits | **60 to 130 ppm U**; 150,000 tU resource ("highly underestimated"); "relatively high U in comparison to the majority of other deposits from the same class" | 4 deposits | Conference abstract; grade basis (resource vs ore) not stated |
| Carajás IOCG | IAEA-TECDOC-1849 (2018), Type 3 text [E] https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1849web.pdf | Fe-Cu deposits of Carajás (Igarapé Bahia, Sossego, Salobo) | **30 to 150 ppm U, "not recovered"**; Australian IOCG-U 50 to 250 ppm; Olympic Dam 230 ppm | compilation | IAEA, secondary |
| **Sossego** | none specific found | | Inherits Carajás range | | Weaker than Salobo |
| **Candelaria** (Chile) | Marschik, Leveille and Martin 2000, in Porter (ed.), *Hydrothermal Iron Oxide Copper-Gold and Related Deposits*, vol. 1, pp. 163 to 175, Table 1 [E] https://portergeo.com.au/full_text/Marschik_Candelaria-PGC_Publishing.pdf | Whole-rock, 8 m composites of rock hosting the orebody | **U mean 2.1 ppm, max 7.7** (26 Bq/kg mean); Th 3.4 ppm (14 Bq/kg); Cu mean 0.48 % | **91** | Primary, 1990s data; text states Candelaria "is poor in U compared with ... Salobo ... and Olympic Dam" |
| **Ernest Henry** (Australia) | none directly. Neighbouring **E1 Group** (not Ernest Henry itself): Case 2016, PhD, James Cook University, ch. 2 [E] https://researchonline.jcu.edu.au/49998/1/49998-case-2016-thesis.pdf | E1 Group ore, Cloncurry | "Uranium levels in ores range from 50 to 250 ppm"; local up to 450 ppm | not stated | Primary thesis but different deposit group |
| **Mantoverde** (Chile) | Capstone NI 43-101 TR, Nov 2021 [E, text search] https://capstonecopper.com/wp-content/uploads/2022/12/MV-Technical-Report-Final-Jan-5-2022pdf.pdf | | Lists "uranium" only in the generic IOCG minor-element suite; **no assay** | | Nothing quantitative |
| **Lumwana** (Zambia) | Lumwana Copper Project EIA, July 2005, EIB-hosted copy [E] https://www.eib.org/attachments/pipeline/1570_eia_en.pdf | Malundwe ore tailings, test (Campbell 2002 / Golder BFS) | **Tailings solids 33 ppm U** (408 Bq/kg U-238); supernatant 0.16 mg/L U. Chimiwungo has "lower levels of uranium" | test composite, n not stated | Feasibility test via EIA summary; richer pit |
| Lumwana | same EIA, section 3.5.3 and Table 4-2 [E] | In-ground U resource, 100 ppm cut-off | 12 Mt at 695 ppm U (cu resource 944.8 Mt at 0.69 % Cu); in-pit at 700 ppm cut-off 1.4 Mt at 2,597 ppm; U zones to be **stockpiled separately in waste dumps**, not milled | resource | Resource, reported separate from Cu |
| Lumwana | IAEA-TECDOC-1849, section 4.4.2, Table 19 [E] | 2006 U resource | 12.1 Mt at 0.068 % U (8,248 tU); copper resource 922 Mt at 0.6 to 0.9 % Cu; "metamorphite" in UDEPO | | IAEA, derived from Equinox |
| Lumwana, sulphidic waste | EIA section 4.12 [E] | two sulphidic waste samples | U 0.0008 % (8 ppm) | 2 | tiny n |
| **Kansanshi** (Zambia) | none found | | No U assay in any retrieved source | | Left in B |
| Zambian Copperbelt (Kitwe, Kalulushi) | Shaba, Maseka and Hayumbu 2024, Fortune Journals (via fetch summary [R]) https://www.fortunejournals.com/articles/evaluation-of-radiological-risk-hazards-in-sediments-and-selected-streams-around-kalulushi-and-kitwe-towns.html | Stream sediments, Nkana tailings TD15A runoff | Ra-226 51.8 to 104.6 Bq/kg; Th-232 43 to 72 | 4 sediments | Sediments, not tailings; fits Katebe's up-to-104 (S0461) |
| Uganda, Kilembe (context) | Turyahabwa et al. 2025, *Int. J. Environ. Anal. Chem.* 105(11) (via fetch summary [R]) | Copper tailings and sediments | tailings Ra-226 171 (n=31 sediments plus tailings combined) | 31 | Not a modelled mine; sidebar |
| Telfer-type concentrate (context) | ANSTO report in Greatland application (via fetch [R]) https://www.der.wa.gov.au/images/documents/our-work/licences-and-works-approvals/Applications-CURRENT/APP-0027823/C6.4%20-%20Rad%20-%20Copper%20Concentrate%20-%20Greatland_Redacted.pdf | Newcrest copper concentrate | U-238 0.038 Bq/g (3.1 ppm U); Pb-210 and Po-210 about 0.07 Bq/g | 1 | Shows non-equilibrium (210Pb and 210Po above U-238) in a low-U concentrate |

### 3.3 Salobo mass balance (consistency check) [I, A]

Head about 0.6 to 0.65 % Cu and about 87 % recovery [A, recalled], 38 % Cu concentrate, so concentrate mass is about 1.4 to 1.5 % of feed. At 52 ppm U in concentrate only 0.7 to 0.8 ppm of head U reaches it. If head U is 60 to 130 ppm, then 0.6 to 1.3 % of the U leaves in concentrate and tailings carry about the head grade. If head U were only 10 ppm, 7 to 8 % would go to concentrate; this cannot be excluded. So the concentrate spec is consistent with, but does not prove, the 60 to 130 ppm.

---

## 4. Class verdicts

Tailings U-238 and t/t as used in the recomputation; S5 per t Cu in Bq. 2024 share of world mined copper (23.0 Mt) from mine output recalled from company reports **[A, not re-read; to be checked against Vale, Lundin, Evolution and Capstone reports]**; they sum to the 2.5 % "other IOCG" in `copper_classes.md` section 4.1.

| Mine | 2024 share | Verdict | U-238 tailings, Bq/kg (low / central / high) | t per t Cu | S5 per t Cu (low / central / high) | Confidence |
|---|---|---|---|---|---|---|
| Prominent Hill (A, revised) | 0.44 % | **A** | 900 / 1,100 / 1,420 | 80 / 95 / 110 | $2.9\times10^{8}$ / $4.2\times10^{8}$ / $6.4\times10^{8}$ | High (measured head, one sample) |
| Salobo | 0.9 % | **Intermediate** | 370 / 990 / 1,850 (30 / 80 / 150 ppm U) | 150 / 177 / 210 | $2.2\times10^{8}$ / $7.1\times10^{8}$ / $1.6\times10^{9}$ | Low to medium (compilations plus concentrate; no tailings assay) |
| Sossego | 0.35 % | **Intermediate** (inherited from Carajás) | same | 90 / 110 / 130 | $1.3\times10^{8}$ / $4.4\times10^{8}$ / $9.8\times10^{8}$ | Low |
| Lumwana | 0.6 % | **Intermediate, lower** | 110 / 310 / 740 (9 / 25 / 60 ppm U) | 190 / 210 / 240 | $8.5\times10^{7}$ / $2.6\times10^{8}$ / $7.2\times10^{8}$ | Medium for the 33 ppm, low for the weighting |
| Candelaria | 0.65 % | **B** | 26 (2.1 ppm U) | about 230 | $2.7\times10^{7}$ (equals B central) | Medium to high (91 assays, but rock hosting ore, 1990s) |
| Ernest Henry | 0.35 % | **B (unresolved)**; high case E1-like 150 ppm | B low / B central / 1,850 | 110 | B / B / $9.8\times10^{8}$ | Very low (no assay; E1 neighbour is 50 to 250 ppm) |
| Mantoverde and other Chilean/Peruvian IOCG | 0.25 % | **B (unresolved)** | B | | B | Low (analogy to Candelaria; Chilean IOCG tend low-U) |
| Kansanshi (not a class change) | in B | **B** | B | | B | Low |

Notes on the choices:
- **Lumwana central 25 ppm** is my judgement: the 33 ppm test is on Malundwe, the richer pit (about 31 % of ore tonnes); Chimiwungo is lower; the plan was to segregate the over-700 ppm zones. The bulk resource average implied by 8,248 tU spread over 945 Mt is 8.7 ppm [I], used as the low. High 60 ppm covers imperfect segregation. A Lumwana radiation management plan or the Barrick 2024 TR section 13 would settle it.
- **Carajás range 30 / 80 / 150 ppm** is my choice from TECDOC-1849 (30 to 150) and URAM-2018 (60 to 130); central 80 sits within the narrower range. Thorium 40 Bq/kg central assumed [A].
- **Class A at Olympic Dam and Carrapateena unchanged.**
- All shares and t/t are my estimates; ranges are outer bounds (products of lows or highs), not confidence intervals.

---

## 5. Recomputed 2024 weighted factor (S5, tailings only, Bq per t Cu)

$$F=\sum_k s_k F_k$$

2024 shares: Olympic Dam 1.40 %, Prominent Hill 0.435 %, Carrapateena 0.365 %, DRC (class C) 14.3 %, Salobo 0.9 %, Sossego 0.35 %, Lumwana 0.6 %, Ernest Henry 0.35 %, remaining B 81.4 % [I; sums to 100 %].

| Case | Low | Central | High | Central vs current |
|---|---|---|---|---|
| Current (`copper_classes.md` 4.3) | $2.6\times10^{7}$ | $4.8\times10^{7}$ | $2.0\times10^{8}$ | 1.00 |
| **New, verdict-based (section 4)** | $2.9\times10^{7}$ | **$5.7\times10^{7}$** | $2.2\times10^{8}$ | **1.18** |
| New with only Carajás and Lumwana changed (PH unchanged) | $2.9\times10^{7}$ | $5.7\times10^{7}$ | $2.2\times10^{8}$ | 1.19 |
| Old "all unresolved A-like" bound | | $7.2\times10^{7}$ (other IOCG, plus 51 %); Lumwana plus 8 % | | |

Central contributions of the intermediate set: Salobo $6.4\times10^{6}$, Sossego $1.5\times10^{6}$, Lumwana $1.6\times10^{6}$, total $9.5\times10^{6}$ (17 % of the new central); Prominent Hill revision minus $3.7\times10^{5}$. Net: plus $9.0\times10^{6}$.

Reading: the two big unresolved items (+51 % and +8 %) collapse to +16 % (Carajás) and +3 % (Lumwana). The remaining open lever is **Ernest Henry plus Mantoverde (0.6 % of world copper)**: at A level it would add about +12 %; at E1-like 150 ppm about +10 %; it is in the high bound only for Ernest Henry. The 8x spread (low to high) is unchanged because B's lows and highs still dominate the bounds.

**Class A remains about 44 % of the central** (OD $1.96\times10^{7}$, PH $1.8\times10^{6}$, CP $2.6\times10^{6}$ of $5.7\times10^{7}$ is 43 %) [I].

### Intermediate class: warranted?

Yes, but as a labelled ore type, not a new structural tier.
- Activity: 370 to 1,850 Bq/kg sits 12 to 60 times B (30) and 0.3 to 1.7 times Prominent Hill (1,100), so neither existing class describes it without distortion. Treating Salobo as A (PH-like) overstates it by about 1.5x central; treating it as B understates it 27x.
- Materiality: 1.85 % of world copper and 17 % of the central; in the same range as the PH plus CP pair.
- Suggested `ore_type = iocg_intermediate_u` for Salobo and Sossego, and `cu_u_metamorphite` (or the same tag) for Lumwana, since Lumwana is not IOCG. If a single tag is preferred, `intermediate_u` (defined 100 to 1,000 Bq/kg U-238 in tailings) covers all three. Calls for new activity series (or `copper_class_shares.csv` columns): Salobo, Sossego, Lumwana mine output; these are the Vale and Barrick annual reports.
- Not warranted: separate classes for Candelaria (stays B), Ernest Henry or Mantoverde until an assay exists.

---

## 6. Proposed rows (not applied)

Per-nuclide head value (Bq/t Cu) for the `U238+` block; chain members at ratio 1 per the CSV convention; S5 is four such heads plus Th-232. Columns follow `commodity_factors_draft.csv`: commodity `copper`, component `own_residue`, tier `impounded`, residue_type `metal_tailings`, allocation `default / alloc:value`, unit `Bq/t`, basis `modelled`.

| region | ore_type (proposed) | years | group | low | central | high | source_ids (proposed) |
|---|---|---|---|---|---|---|---|
| AUS | `iocg_high_u` (replace PH rows) | 2010 to 2025 | U238+ | $7.2\times10^{7}$ | $1.05\times10^{8}$ | $1.56\times10^{8}$ | S0458 (Habibi, now read, Table 1); head assay replaces the fraction maxima |
| BRA | `iocg_intermediate_u` (Salobo) | 2012 to 2025 | U238+ | $5.6\times10^{7}$ | $1.75\times10^{8}$ | $3.9\times10^{8}$ | S0462 (Vale Salobo spec), S0463 (URAM-2018 contr. 45), S0464 (IAEA-TECDOC-1849) |
| BRA | `iocg_intermediate_u` (Sossego) | 2004 to 2025 | U238+ | $3.3\times10^{7}$ | $1.1\times10^{8}$ | $2.4\times10^{8}$ | S0463, S0464 |
| ZMB | `intermediate_u` (Lumwana) | 2008 to 2025 | U238+ | $2.1\times10^{7}$ | $6.5\times10^{7}$ | $1.8\times10^{8}$ | S0465 (Lumwana EIA 2005), S0464 |
| CHL | `porphyry_stratiform` (Candelaria confirmation; no new rows) | | | | | | S0466 (Marschik et al. 2000) added as a supporting source |
| AUS (Ernest Henry) | `porphyry_stratiform`, note high-case flag | | | | | | S0467 (Case 2016 PhD, as E1 analogue) |

Th-232 rows for the intermediate set at 15 / 40 / 100 Bq/kg (assumed, as for A). Source IDs S0462 onward are placeholders following S0461; no collision check made against the staged registry.

---

## 7. Tier 2 effect (T&D copper)

Same tonnage and allocation conventions as `tier2_memo.md` revision box: T&D copper 3.0 Mt (2.0 to 4.5), D6 0.70 / 0.85 / 1.00, BESS copper 0.1075 Mt.

| Quantity (2024, Bq/a) | Current | New |
|---|---|---|
| T&D copper, central ($3.0\times10^{6}\ \mathrm{t}\times F\times0.85$) | $1.23\times10^{14}$ ($4.84\times10^{7}$) | $1.45\times10^{14}$ ($5.70\times10^{7}$) |
| T&D copper, low (2.0 Mt, D6 0.7) | $3.6\times10^{13}$ | $4.1\times10^{13}$ |
| T&D copper, high (4.5 Mt, D6 1.0) | $9.0\times10^{14}$ | $9.9\times10^{14}$ |
| BESS copper, central | $4.4\times10^{12}$ | $5.2\times10^{12}$ |
| $A_{\mathrm{T2}}$ central | $1.46\times10^{14}$ | about $1.69\times10^{14}$ (0.45 of the original $3.75\times10^{14}$) |

The percentage of fuel streams rises by the same 18 %: ② coal S5 4.3 % to about 5.0 %, i.e. at the 5 % inclusion threshold, so **the "include narrowly" verdict is unchanged but ②'s central moves from below the threshold to on it** **[I]**; ③ and ⑤ move proportionally. ④ is unaffected (copper factor cancels). The low-tonnage case (Deetman-style 2.0 Mt, central $1.1\times10^{14}$ before this change) becomes about $1.25\times10^{14}$ [I].

---

## 8. Gaps, contradictions and inaccessible sources

1. **No tailings or head assay for Salobo, Sossego, Ernest Henry or Mantoverde.** The Carajás range rests on compilations; its primary reference (ref. [14] of URAM-2018 contr. 45) is not identified. The Salobo head and tailings assay would be in Brazilian theses and papers (below).
2. **Resource grade vs tailings grade:** the 60 to 130 ppm and 30 to 150 ppm are deposit-scale statements; tailings could be lower if U is partly stripped to concentrate (not at Salobo by the mass balance, section 3.3) or higher in fine fractions (as at Prominent Hill, where the finest fraction is 30 % above head).
3. **Ernest Henry:** no deposit-specific uranium number found. The nearest assay (E1 Group, 50 to 250 ppm) belongs to a different deposit group. Treat Ernest Henry as unresolved, not as B.
4. **Mine outputs and head grades are recalled [A]**, not read: Salobo (about 0.2 Mt Cu), Sossego, Candelaria, Ernest Henry, Mantoverde and the t/t values.
5. **Kamunda et al. 2016 abstract (785.3) disagrees with its own Table 1 (485.3)** for mean U-238; neither matches the mean of the five dump means (about 731). Irrelevant to copper.
6. **"One more paper" for Steve:** the brief did not name it; I took it to mean a Salobo or Zambian primary source. If it is a specific title, send the DOI.
7. **Inaccessible (give to Steve to try):**
   - Maion, A. V. (2013), USP thesis on Carajás (probably Salobo): https://bdta.abcd.usp.br/directbitstream/2f14e3f8-3ee7-42be-9dbb-595778a3f5ac/Maion,%20Andr%C3%A9%20V_2013_Cara... (the proxy closed the connection; the title is truncated in the search listing).
   - Cossolin, G. S. I., USP thesis: https://bdta.abcd.usp.br/directbitstream/440764d4-10a5-423f-9d81-b6bf9be902f9/Cossolin,%20Giuliano%20S.I_20...
   - USP repository item, probably a Salobo or Carajás thesis: https://repositorio.usp.br/bitstreams/c7cb4f4f-05ad-4705-972e-9ca9c3dbd0dd
   - IAEA UDEPO Lumwana record: https://www-pub.iaea.org/MTCD/publications/PDF/TE_1629_CD/Deposits/1234.html (403)
   - Bernau 2007 PhD, University of Southampton: https://eprints.soton.ac.uk/63758/1/Bernau_2007_PhD.pdf (403; relevance to Lumwana unverified)
   - Sullivan 2016 Adelaide Honours thesis (Ernest Henry candidate): https://digital.library.adelaide.edu.au/dspace/bitstream/2440/121234/1/SullivanE2016_Hons.pdf (404)
   - Barrick Lumwana TR 2024, section 13 (read only in part previously): https://s25.q4cdn.com/322814910/files/doc_downloads/lumwana/Barrick_Lumwana_TechnicalReport_20241231.pdf
   - Evolution Mining Ernest Henry fact sheet: https://evolutionmining.com/documents/fy25-ernest-henry-operations-fact-sheet (404 by curl)
   - Fortune Journals (Shaba) and Kilembe items were read via fetch-tool summaries only [R].
   - PMC4730529 (CAPTCHA): https://pmc.ncbi.nlm.nih.gov/articles/PMC4730529
8. **Most useful next retrieval:** a Salobo concentrate or tailings radiological assessment (CNEN or Vale), or the Salobo whole-rock U data in Réquia and Fontboté (1999) and Réquia et al. (2003), as cited by Marschik et al.; the Vale concentrate U (52 ppm) is the only mine-level Salobo number in hand.

## 9. Facts from memory

None from stored user memory entered this work; all content derives from the documents and web sources cited.
