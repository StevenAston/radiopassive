# Radiopassive — Methods Specification (v1, Energy Edition)

> **Status:** DRAFT for sign-off (Task 0.1). Sections marked **PROPOSED** introduce rules beyond the confirmed plan and need Steve's approval.
> **Governs:** every dataset, script and chart in this project. If anything here conflicts with `PLAN.md`, the plan wins until this document is updated.

---

## 1. Purpose and framing

This document turns the confirmed decisions (D1–D20 in `PLAN.md` and `docs/DECISIONS.md`) into operational rules that a person or agent can apply without further judgement.

The framing thesis governs presentation, not calculation: **radiation is like water.** The calculations are deliberately neutral physical accounting (decays per second, watts, tonnes, containment), never bodily harm.

---

## 2. Scope

### 2.1 Time

- Annual resolution, **1950 to the latest year with data** (D14). The target end year is 2025; streams whose data stop earlier are extrapolated to 2025 with `basis = extrapolated`.
- Years are calendar years. Where a source reports fiscal years, it is mapped to the calendar year containing most of its months, and this is noted.

### 2.2 Geography

- Global totals on the page; **country-level rows are kept** wherever a source provides them (D10). The country is coded ISO 3166-1 alpha-3; `WLD` for global aggregates; `XXX` for unallocated remainders. Historical states (USSR, Czechoslovakia, Yugoslavia, East/West Germany) use ISO 3166-3 codes (`SUN`, `CSK`, `YUG`, `DDR`, `DEU` for West Germany before 1990).
- **No double counting:** global totals are calculated as the sum of country rows plus an explicit `XXX` remainder, never as a separate global figure added on top.

### 2.3 Streams

| # | Stream | Colour token | Sub-streams |
|---|---|---|---|
| ① | Nuclear (civil fuel cycle) | `chart-1` | by fuel-cycle stage; reactor type where relevant |
| ② | Coal | `chart-2` | by stage; power vs non-power use |
| ③ | Oil and gas | `chart-3` | **conventional** and **unconventional** (D4); oil vs gas |
| ④ | Wind and solar materials | `chart-4` | **wind** and **solar**; by commodity |
| ⑤ | Other energy | `chart-5` | geothermal; biomass and peat; hydro |

Non-energy sources (phosphate, mineral sands, metals for non-energy uses) are **out of scope** for v1 and left for the sequel. Military activity is out of scope except as a baseline (D9).

---

## 3. Quantities, units and conventions

### 3.1 Core quantities

| Symbol | Quantity | SI unit | Meaning |
|---|---|---|---|
| $F_{k,j}(y)$ | Flow | Bq·a⁻¹ | Activity of nuclide group $k$ **added** to tier $j$ during year $y$, valued at the moment it is added |
| $S_{k,j}(y)$ | Stock | Bq | Activity of group $k$ in tier $j$ on 31 December of year $y$, after decay and ingrowth |
| $P$ | Radioactive power | W | Energy emitted per second by a stock or flow (§7) |
| $E$ | Generation | TWh | Electricity generated (for normalisation, §8) |

The becquerel is already a rate (1 Bq = 1 decay·s⁻¹). A flow is therefore "becquerels added per year", and a stock is "how fast the accumulated material is decaying right now".

### 3.2 Counting convention — all decays counted (**PROPOSED, PD4**)

Activity is reported as the **total decays per second of every member of a nuclide group**, at the equilibrium assumed for that group (§4). For example, 1 Bq of U-238 in full secular equilibrium with its daughters is reported as 14 Bq of U-238 series activity, because 14 decays (8 α, 6 β) happen for each U-238 decay.

- *Why:* the becquerel counts decays; reporting only the parent understates the material's activity by a factor of 10–14 and hides the real effect of breaking the chain.
- *Consequence:* our NORM figures will be ~10–14× higher than regulatory figures quoted "per parent". The page states this convention prominently, and the dataset also keeps head-of-group activity so either convention can be shown.

### 3.3 Display units

- Bq with SI prefixes (GBq, TBq, PBq, EBq, ZBq); W with prefixes (mW to TW).
- Customary equivalent in tooltips: curies, with 1 Ci = 3.7 × 10¹⁰ Bq exactly (so 1 PBq ≈ 27.0 kCi).
- Mass in t (tonnes); volume in m³; energy in TWh; time in a (Julian year = 3.155 76 × 10⁷ s).

### 3.4 Physical constants

- 1 eV = 1.602 176 634 × 10⁻¹⁹ J (exact, SI 2019).
- Half-lives, branching ratios and decay energies come from ICRP Publication 107, cross-checked against ENSDF/NNDC (Task 0.3).

---

## 4. Nuclide groups

To keep the decay engine tractable, short-lived daughters are folded into a long-lived **head** and assumed to be in equilibrium with it ("+" groups, following the convention used in Euratom Directive 2013/59 and IAEA GSR Part 3). The engine tracks heads only; activity is reported by multiplying by the group's **decay multiplier** $m_k$ (decays per head decay, branching-weighted).

### 4.1 Primordial chains

| Chain | Group (head+) | Members | $m_k$ |
|---|---|---|---|
| U-238 | `U238+` | U-238, Th-234, Pa-234m | 3 |
| | `U234` | U-234 | 1 |
| | `Th230` | Th-230 | 1 |
| | `Ra226+` | Ra-226, Rn-222, Po-218, Pb-214, Bi-214, Po-214 | 6 |
| | `Pb210+` | Pb-210, Bi-210 | 2 |
| | `Po210` | Po-210 (tracked separately because its 138 d half-life is often out of equilibrium) | 1 |
| | **U-238 series total** | | **14** |
| U-235 | `U235+` | U-235, Th-231 | 2 |
| | `Pa231` | Pa-231 | 1 |
| | `Ac227+` | Ac-227, Th-227/Fr-223, Ra-223, Rn-219, Po-215, Pb-211, Bi-211, Tl-207 | 8 |
| | **U-235 series total** | | **11** |
| Th-232 | `Th232` | Th-232 | 1 |
| | `Ra228+` | Ra-228, Ac-228 | 2 |
| | `Th228+` | Th-228, Ra-224, Rn-220, Po-216, Pb-212, Bi-212, Po-212 (64.06%) / Tl-208 (35.94%) | 7 |
| | **Th-232 series total** | | **10** |
| Radon released to air | `Rn222+` | Rn-222, Po-218, Pb-214, Bi-214, Po-214 | 5 |
| | `Rn220+` | Rn-220 and short-lived progeny (geothermal, thoron-rich residues) | 4 (to verify in Task 0.3) |
| Potassium | `K40` | K-40 | 1 |

Natural uranium: the U-235 series head activity is 0.046 × that of U-238 (Task 0.3 to confirm to three significant figures).

The members, $m_k$ and branching ratios in this table are provisional until Task 0.3 verifies them against ICRP 107.

### 4.2 Artificial nuclides (nuclear stream)

| Class | Groups |
|---|---|
| Noble gases | Ar-41, Kr-85, Kr-85m, Kr-87, Kr-88, Xe-131m, Xe-133, Xe-133m, Xe-135, Xe-138 |
| Light / activation | H-3, C-14, Co-58, Co-60, Mn-54, Fe-55, Ni-63, Sb-125 |
| Fission products | `Sr90+` (Sr-90, Y-90; $m$=2), `Cs137+` (Cs-137, Ba-137m; $m$=1.944), Cs-134, `Ru106+` (Ru-106, Rh-106; $m$=2), `Ce144+` (Ce-144, Pr-144; $m$=2), Tc-99, I-129, I-131, I-133, Te-132, Pm-147, Sm-151, Eu-154, Eu-155 |
| Actinides | Pu-238, Pu-239, Pu-240, Pu-241, Pu-242, Am-241, Cm-242, Cm-244, Np-237 |

For spent-fuel **inventory**, a reduced set of ~20 nuclides is used that together account for ≥ 99% of activity and ≥ 99% of decay heat at every cooling time from 1 to 10⁴ years (to be confirmed against a published per-tHM inventory in Task 1.2).

### 4.3 Candidate nuclides per stream (done condition (b))

| Stream | Candidate groups |
|---|---|
| ① Nuclear | Mining/milling: `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Pa231`, `Ac227+`, `Rn222+`. Effluents: noble gases, H-3, C-14, I-129, I-131, `Cs137+`, Cs-134, `Sr90+`, Co-60, Co-58, Mn-54, Sb-125, Tc-99, `Ru106+`, Pu/Am. Spent fuel: §4.2 reduced inventory set. Accidents: I-131, Te-132, Cs-134, `Cs137+`, `Sr90+`, Xe-133, Kr-85, Pu-isotopes, `Ce144+`, `Ru106+`. |
| ② Coal | `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+` group set, `Th232`, `Ra228+`, `Th228+`, `K40`, `Rn222+` (mines, ash). |
| ③ Oil and gas | `Ra226+`, `Ra228+`, `Th228+` (ingrowth in scale), `Pb210+`, `Po210` (gas processing, scale), `Rn222+` (gas, processing), `K40` (produced water). |
| ④ Wind and solar materials | `Th232` series groups (monazite, Bayan Obo, ionic clays), U-238 and U-235 series groups (REE ores, copper-uranium ores, bauxite red mud), `Pb210+` and `Po210` (smelter off-gas), `Rn222+` (tailings), `K40`. |
| ⑤ Other energy | Geothermal: `Rn222+`, `Rn220+`, `Ra226+`, `Ra228+`, `Pb210+`. Biomass/peat: `K40`, `Cs137+` (re-released fallout), `Pb210+`, `Po210`, U-series heads in peat. Hydro: none (negligible, §10). |

---

## 5. Containment tiers (D2, D17)

### 5.1 Definitions

| Tier | Water analogue | Definition |
|---|---|---|
| **Sealed** | Tank | Material in engineered, licensed containment whose design purpose is radiological isolation: spent fuel (pools, dry casks), vitrified high-level waste, licensed LLW/ILW facilities, uranium products and depleted-uranium stocks in licensed storage. |
| **Impounded** | Reservoir behind a dam | Solid or liquid residue held in a surface or near-surface deposit whose primary purpose is holding material, not radiological isolation: tailings dams, ash ponds and landfills, scale/sludge disposal sites, evaporation ponds. |
| ↳ **Re-isolated** (sub-tier) | Water pumped back into the aquifer | Material returned to deep geological formations: deep-well injection of produced water, backfill into deep mines. Shown inside Impounded, distinguished by pattern. |
| **Dispersed** | Spread on the fields | Material deliberately spread on land or built into products or the landscape in solid or adsorbed form: fly ash in concrete and fill, FGD gypsum in wallboard, produced brine spread on roads, land-farmed sludge, ash spread on soil. |
| **Liberated** | In the river or sky | Emitted to the atmosphere, surface water or sea, by routine discharge or accident. |

### 5.2 Transfer rules

- **Routine flows** enter a tier directly at the stage that produces them (§6).
- **Events** (§9) move activity *between* tiers: the activity is subtracted from the source tier's stock and added to the destination's in the event year, with no double counting.
- **Chronic leakage from Impounded:** radon exhaled from tailings or ash, and seepage, are recorded as Liberated flows. The impounded stock is *not* reduced for these, because the escaping radon is replaced by decay of the Ra-226 that stays behind. The small double count this introduces (the escaping radon progeny are counted in both tiers) is ≤ 20% of the `Ra226+` group for typical emanation coefficients, and is absorbed into the uncertainty bounds. *(Rationale: a full emanation model would add a great deal of complexity for a correction smaller than the data uncertainty.)*
- Once liberated, material **stays in the Liberated stock and decays there**. Dispersal reduces concentration, not activity.

### 5.3 Moved earth vs processed residue (**PROPOSED, PD1**)

Mining moves enormous masses of rock. To keep the accounting meaningful:

- **Counted in tiers:** every residue **generated by processing** (tailings, slag, ash, scale, sludge, red mud, refuse from coal washing, drill cuttings, mine water) regardless of its concentration, and all products.
- **Recorded as a memo series, outside the tier totals:** overburden and waste rock moved only to *reach* a deposit, *unless* its activity concentration exceeds **1 Bq·g⁻¹ for any U-238 or Th-232 series head, or 10 Bq·g⁻¹ for K-40** (the NORM scope thresholds in IAEA GSR Part 3). Above-threshold waste rock is counted in Impounded.
- The memo series ("earth moved", in t and Bq) is kept, so a "total earth displacement" view can be added later.
- *Why:* moving ordinary rock from 10 m down to a spoil heap doesn't change its radioactivity or containment in any meaningful way; processing (concentration, chemical mobilisation, breaking decay chains) does.

---

## 6. System boundary and stage map (D5)

### 6.1 Two accounting views (**PROPOSED, PD2**)

A single stacked total cannot be both "what each industry did" and "what each kind of electricity costs", because some flows sit in both places (e.g. coking coal for wind-tower steel is part of the coal industry *and* of wind's supply chain). Two views are therefore defined; **totals are only stacked within one view**.

| View | Question it answers | Streams | Used for |
|---|---|---|---|
| **Industry view** (default for absolute charts) | What did each industry bring up, create or release? | ① civil fuel cycle; ② all coal mined and burned; ③ all oil and gas produced; ④ materials for wind and solar **excluding** contributions already inside ② or ③ (embedded coal, gas, oil); ⑤ other energy | Absolute flow and stock charts |
| **Electricity lifecycle view** | What does each kind of electricity carry with it per TWh? | Coal power, gas power, oil power, nuclear, wind, solar, geothermal, biomass, hydro — each with its full Tier 1 supply chain, **including** embedded coal and O&G | Per-TWh charts (§8); the UNSCEAR check (§11) |

In the industry view, streams ② and ③ cover the **whole industry** (as originally asked: "mining and burning coal"; "oil and gas wells"), not only fuel for power.

### 6.2 Construction materials — shared commodity footprint table

Every generating technology's plant materials (steel, concrete/cement, copper, aluminium, glass, silicon, silver, rare earths, tellurium, indium, etc.) are accounted for through **one shared table**, `data/reference/commodity_factors.csv`. It gives, per tonne of refined commodity, the activity by group and tier of:

- (i) **own residues**: mining and processing waste of that commodity (e.g. REE tailings, red mud, copper tailings, smelter off-gas);
- (ii) **embedded fuel**: residues from the coal, oil and gas used to make it (coking coal, coal-fired smelting power, carbothermic silicon reduction).

The industry view uses (i) only (since (ii) is already in ② and ③); the lifecycle view uses (i) + (ii). Material intensity per MW comes from Task 1.9.

The same table serves **every** stream's construction materials, which satisfies D5 symmetrically: nuclear, coal and gas plants are charged for their steel and concrete exactly as wind and solar are.

### 6.3 Stage map and tier assignment

| Stream | Stage | Sealed | Impounded (↳ Re-isolated) | Dispersed | Liberated |
|---|---|---|---|---|---|
| ① | U mining (open pit, underground) | — | mineralised waste rock > threshold | — | mine radon, mine water |
| ① | U mining (in-situ leach) | — | evaporation-pond residue (↳ deep-well injected ISL waste) | — | radon, wellfield excursions |
| ① | Milling | U product → Sealed | tailings | — | tailings radon, dust, seepage |
| ① | Conversion, enrichment, fabrication | product, depleted U | process residues | — | stack and liquid discharges |
| ① | Reactor operation | operational LLW/ILW | — | — | airborne and liquid effluents |
| ① | Spent fuel | spent fuel inventory (created activity) | — | — | — |
| ① | Reprocessing | HLW, ILW | — | — | discharges to air and sea |
| ① | Plant construction & decommissioning | decommissioning waste | commodity own-residues | — | commodity off-gas |
| ① | Civil accidents | — | — | — | event releases (§9) |
| ② | Coal mining | — | washery refuse; above-threshold waste | — | mine radon, mine water (radium) |
| ② | Combustion | — | fly ash, bottom ash, FGD residue landfilled/ponded | ash and FGD gypsum used in products or fill | stack fly ash and volatiles (Pb-210, Po-210), ash-pond radon |
| ② | Plant construction | — | commodity own-residues | — | commodity off-gas |
| ③ | Drilling | — | drill cuttings | — | — |
| ③ | Production | — | scale, sludge at disposal sites (↳ deep-well injected produced water) | brine spread on roads; land-farmed sludge | surface-discharged produced water; spills |
| ③ | Gas processing & distribution | — | Pb-210/Po-210 scale and sludge from processing plants | — | radon in vented and delivered gas |
| ③ | Plant & well construction | — | commodity own-residues | — | commodity off-gas |
| ④ | Commodity supply (REE, Cu, Al, Fe, Si, Ag, Te, In, glass, concrete…) | — | own-residues (tailings, red mud, slag) | residues used in products | off-gas, dust, seepage, discharges |
| ⑤ | Geothermal | — | scale and sludge (↳ reinjected brine) | — | non-condensable gas radon |
| ⑤ | Biomass / peat | — | ash landfilled | ash spread on soil | stack emissions incl. re-released Cs-137 |
| ⑤ | Hydro | — | — | — | negligible (§10) |

Task 1.2–1.6 may add stages; any addition must be recorded here before data is built for it.

---

## 7. Radioactive power (D1)

For each group $k$, the mean energy **emitted** per head decay is

$$\bar{E}_k=\sum_{i\in k} b_i\left(E_{\alpha,i}+E_{\mathrm{recoil},i}+\bar{E}_{\beta,i}+E_{\gamma X,i}+E_{e,i}\right)$$

where $b_i$ is member $i$'s branching-weighted decays per head decay, $\bar{E}_{\beta}$ is the mean β energy (the antineutrino share is **excluded**, because it escapes the planet without depositing heat), $E_{\gamma X}$ covers γ and X-rays, and $E_e$ conversion and Auger electrons. The radioactive power of an activity $A_k$ (head activity) is then

$$P_k=A_k\,\bar{E}_k$$

with $\bar{E}_k$ in joules. The calculation is reproduced by hand for H-3, `Cs137+` and Po-210 in Task 3.3.

---

## 8. Normalisation (D8)

- Per-TWh values are calculated **only in the lifecycle view** (§6.1).
- **Fuel-cycle and operating flows** (mining, combustion, effluents, spent fuel) are divided by the same year's generation from that technology.
- **Construction-phase flows — levelised (PROPOSED, PD3):** releases from building capacity in year $y$ are divided by the **expected lifetime generation** of that capacity, not by year $y$'s generation:

$$\text{intensity}_{\mathrm{constr}}(y)=\frac{F_{\mathrm{constr}}(y)}{C(y)\,\mathrm{CF}\,L\times 8.766\ \mathrm{TWh\,GW^{-1}a^{-1}}}$$

where $C(y)$ is capacity added (GW), $\mathrm{CF}$ the expected capacity factor and $L$ the expected lifetime (a). *Why:* dividing up-front construction releases by the current year's output penalises any fast-growing fleet (wind and solar now, nuclear in the 1970s–80s) and flatters any shrinking one. A simple "annual ratio" variant is kept in the data as a secondary series.
- Years with zero generation are marked `n/a`, never zero.
- **Electricity share of coal and O&G (lifecycle view):** the share of coal (by energy) and of gas and oil going to power generation each year, from IEA/EI balances, allocates mining and production stages to the power technologies.

---

## 9. Events and accidents (D9, D15, D16)

### 9.1 Inclusion threshold

An event is included if its central estimate meets **either**:
- ≥ 1 TBq moved into the Liberated or Dispersed tier; **or**
- ≥ 10⁵ t of NORM-bearing material released from impoundment.

Each event records: date, location, stream, source and destination tiers, activity by group (low/central/high) and ≥ 1 source. Events appear as markers on the timeline and their activity is included in the tier stocks (accidents can be excluded with a toggle, D15).

### 9.2 Civil/military rule (D16)

- **Uranium production:** the civil share of production in year $y$ is
  $$\phi_{\mathrm{civil}}(y)=\min\left(1,\ \frac{R_{\mathrm{civil}}(y)}{U_{\mathrm{prod}}(y)}\right)\ \text{for}\ y\ge 1965,\qquad \phi_{\mathrm{civil}}(y)=0\ \text{for}\ y<1965$$
  where $R_{\mathrm{civil}}$ is civil reactor uranium requirements and $U_{\mathrm{prod}}$ is world production, unless a documented contract or end use says otherwise (e.g. production sold to weapons programmes after 1965 → military).
- **Dual-use reprocessing sites** (e.g. Sellafield, Marcoule, and Mayak's RT-1, which reprocessed civil VVER fuel from the late 1970s): discharges are split by the civil fraction of documented throughput. Where throughput is undocumented, the site-year is excluded and flagged.
- **Excluded military events:** Windscale 1957, Kyshtym 1957, SL-1 1961, Hanford releases, and all weapons testing (which appears as a baseline only).
- **Included civil events (indicative):** Chernobyl 1986, Fukushima Daiichi 2011, Three Mile Island 1979, Church Rock 1979; coal ash and slurry failures (e.g. TVA Kingston 2008, Dan River 2014, Martin County 2000); large produced-water spills; tailings failures in commodity chains attributable to ④ (e.g. Mount Polley 2014, copper; Brumadinho 2019, iron ore), each attributed by the allocation rules in §10.

---

## 10. Allocation (D6) and negligibility

### 10.1 Split points with several products

At every split point that yields several products (e.g. Bayan Obo: iron, REE, niobium; Olympic Dam: copper, uranium, gold, silver; oil and gas wells: oil, gas, NGLs), residues are allocated:

- **Default — economic value:** in proportion to each product's share of the output's market value in that year, using unit-value series (USGS DS140 unit values where available; otherwise price series with a cited source).
- **Bound A — all to main product:** the full residue goes to the product that defines the mine (iron at Bayan Obo, copper at Olympic Dam).
- **Bound B — all to the radioactivity-bearing product:** the full residue goes to REE at Bayan Obo, uranium at Olympic Dam.

The page toggle switches among default, A and B; the uncertainty band shows only the default's own data uncertainty.

### 10.2 Attribution to wind and solar

- The share of a commodity attributed to ④ in year $y$ is
  $$\sigma_{c}(y)=\frac{\sum_{t} C_{t}(y)\,I_{t,c}(y)}{Q_{c}(y)}$$
  where $C_t(y)$ is capacity added (incl. repowering and replacement) of technology $t$, $I_{t,c}$ its intensity of commodity $c$ (t·GW⁻¹), and $Q_c$ world production of $c$.
- Within one commodity, the split between end uses is by **mass**, because value per tonne is the same.
- REE: attribution follows NdFeB (and Dy/Tb) demand for wind generators; solar's REE intensity is taken as reported (expected to be near zero), pending Task 1.1's answer to the "why solar" question.

### 10.3 Negligibility rule

A stage may be marked **negligible** (shown, not modelled in detail) if its central estimate is < 0.1% of its stream's total in both Bq and W in every decade, with the estimate and source recorded. Hydro is expected to qualify (its only radiological link is construction materials, which are counted via §6.2).

---

## 11. Uncertainty and data basis (D7, D18)

### 11.1 Bounds

Every factor and every activity datum carries low/central/high. Bounds are interpreted as approximately the 5th/95th percentiles of a log-normal distribution about the central value.

- **Products** (activity × factor × fraction): combined in log space by quadrature,
  $$\ln\frac{x_{\mathrm{high}}}{x_{\mathrm{c}}}=\sqrt{\sum_i\ln^2\frac{x_{i,\mathrm{high}}}{x_{i,\mathrm{c}}}}$$
  and the same for the low side.
- **Sums** of independent terms: absolute half-widths combined by quadrature. Terms that share a factor (e.g. one emission factor applied to several countries) are treated as fully correlated and summed linearly.
- The invariant low ≤ central ≤ high is checked everywhere (Task 3.6).
- Monte Carlo is considered only if the bounds prove too crude (D18).

### 11.2 Basis flags

Each row carries `basis` ∈ {`measured`, `compiled` (an authoritative compilation of measurements, e.g. UNSCEAR/RADD), `modelled` (activity × factor), `interpolated`, `extrapolated`}. The page draws measured and compiled values solid and the rest hatched or lighter.

### 11.3 Source hierarchy

1. Regulator-reported measurements (NRC, CNSC, RADD, OSPAR, DIRATA, national NORM surveys).
2. UNSCEAR and IAEA compilations.
3. Peer-reviewed literature.
4. Government and agency reports (USGS, EIA, JRC, IEA).
5. Industry and grey literature (used only where nothing better exists; flagged).

**Excluded entirely:** Grokipedia. Wikipedia only as a lead to primary sources, never cited. Inaccessible sources are listed with their URL for Steve to try himself.

---

## 12. Decay and ingrowth model (D3)

### 12.1 Formulation

The engine tracks **atoms** of each head $k$ per tier, $N_{k,j}$, with decay constants $\lambda_k=\ln 2/T_{1/2,k}$ (a⁻¹). Within a chain,

$$\frac{dN_k}{dt}=-\lambda_k N_k+\sum_{p\to k}\beta_{p\to k}\lambda_p N_p+q_k(t)$$

where $\beta_{p\to k}$ is the branching from parent head $p$ and $q_k$ the source. Activity is $A_k=\lambda_k N_k$; reported group activity is $m_k A_k$ (§4).

### 12.2 Annual step

Each year is stepped exactly by the matrix exponential of the chain's decay matrix, with the year's flow treated as a **uniform source over the year** (the augmented-matrix method). For a single nuclide with no parent this reduces to

$$S(y)=S(y-1)\,e^{-\lambda}+F(y)\,\frac{1-e^{-\lambda}}{\lambda}$$

with $\lambda$ in a⁻¹, so very short-lived releases (noble gases, I-131) contribute to the flow chart but leave almost nothing in the stock. Events are applied as instantaneous transfers at mid-year.

### 12.3 Disequilibrium at entry

Each stage records the **activity of each head** entering a tier, so broken chains are explicit. For example:
- Mill tailings carry `Th230`, `Ra226+`, `Pb210+`, `Po210` with only ~5–10% of the ore's uranium heads.
- Oil-field scale carries `Ra226+` and `Ra228+` with essentially no Th-232 or U-238; `Th228+` then grows in from Ra-228 over a few years and dies away with it.
- Fly ash fines may carry `Pb210+` and `Po210` enriched relative to `Ra226+`.

### 12.4 Required tests (Task 3.2)

Single-nuclide decay; a two-member analytic Bateman case; secular equilibrium of the U-238 chain; Ra-226 grow-in from separated Th-230; and conservation of atoms across a ten-member chain.

---

## 13. Baselines (D11)

All baselines are given in both Bq and W wherever meaningful, with the derivation shown and sourced in Task 1.7.

| Baseline | Quantity | Note |
|---|---|---|
| Earth's radiogenic heat | W (~20 TW) | Geoneutrino estimates; W only (a Bq equivalent would be a derived quantity) |
| K-40 in the oceans | Bq, W | Seawater K concentration × ocean volume × K-40 specific activity |
| Natural radon exhalation from land | Bq·a⁻¹ | Global mean exhalation flux × land area |
| Cosmogenic H-3 and C-14 | Bq·a⁻¹ production; Bq standing inventory | Direct comparator for nuclear's H-3 and C-14 releases |
| Top metre of global soil (candidate) | Bq | Mean soil activity × mass of the top metre of land soil; kept only if a defensible soil-activity mean is sourced |
| Atmospheric weapons-test fallout | Bq by group (I-131, `Cs137+`, `Sr90+`, C-14, H-3) | Baseline only (D9) |

---

## 14. Internal dose check (D1; Task 3.5)

Collective dose is calculated **for the 2010 reference year only**, in the lifecycle view, using UNSCEAR 2016 Annex A's own release-to-dose methodology, to check that our release estimates are of the right size. Tolerance: each stream within a factor of 3 of UNSCEAR's value, or the gap explained here. **No dose quantity is exported to the page data**; an automated check enforces this.

---

## 15. Inputs deferred to Phase 1

| Item | Task |
|---|---|
| Per-tHM spent-fuel inventory vs burnup and cooling time; choice of the reduced nuclide set | 1.2 |
| Civil fraction of Sellafield, Marcoule and RT-1 throughput by year | 1.2 |
| Reactor-type normalised effluent factors by period (UNSCEAR) | 1.1, 1.2 |
| U and Th content of coal by basin, and ash partitioning and enrichment factors | 1.3 |
| Global fly-ash production and utilisation by year | 1.3 |
| Produced-water volumes and Ra-226/Ra-228 concentrations by play; disposal-route shares | 1.4 |
| Material intensity by technology and year; commodity footprint factors (§6.2) | 1.5, 1.9 |
| Bayan Obo product split and unit values; Olympic Dam product split | 1.5, 1.9 |
| Geothermal non-condensable gas radon factors; biomass-ash Cs-137 | 1.6 |
| Electricity shares of coal, gas and oil by year | 1.9 |
| Emanation coefficients to bound the §5.2 double count | 1.3, 1.5 |

---

## 16. Proposed decisions needing sign-off

| ID | Section | Proposal |
|---|---|---|
| **PD1** | §5.3 | Count all processing residues; record overburden and waste rock as a memo series unless > 1 Bq·g⁻¹ (U/Th heads) or > 10 Bq·g⁻¹ (K-40). |
| **PD2** | §6.1 | Two accounting views: **industry** (default for absolute charts; ② and ③ are whole industries) and **electricity lifecycle** (per-TWh and UNSCEAR check); totals stacked only within a view. |
| **PD3** | §8 | Levelise construction-phase releases over expected lifetime generation for per-TWh charts; keep the simple annual ratio as a secondary series. |
| **PD4** | §3.2 | Count all decays in each group (e.g. ×14 for U-238 in equilibrium), keeping head-only activity in the data as an alternative. |

---

## Change log

| Date | Change |
|---|---|
| 2026-10-20 | First draft (Task 0.1). |
