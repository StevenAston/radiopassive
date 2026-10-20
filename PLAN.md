# Project: Radiopassive — Energy Edition (v1)

> **Status:** CONFIRMED by Steve, 2026-10-20 (all open-question defaults accepted). Execution has begun.
> **Last revised:** 2026-10-20

---

## Overview

Radiopassive is an interactive web page charting the radioactivity that energy industries have brought into, created in, or released to the human environment between 1950 and the present: the civil nuclear fuel cycle, coal, oil and gas (fracked wells especially), the mineral supply chains of wind and solar, and a small group of other energy sources. The page shows annual releases and accumulated stocks, with decay. Every number is drawn against natural reservoirs of radioactivity at the same scale. It never turns radiation into bodily harm.

**Framing thesis — radiation is like water.** It is everywhere, almost all of it is unremarkable, and it collects in reservoirs of very different depth and containment. Some of that water is deep, dark and dangerous, but almost nobody ever goes near it. The page's job is to show how big each reservoir is, how well it is contained, and how fast it drains (decays), not to count casualties.

---

## Approach

The work runs in seven phases:

1. **Specification (Phase 0)** — fix the methodology, data schema and nuclide reference table before any data is collected.
2. **Source inventory (Phase 1)** — for each stream, identify the activity data (how much was produced, mined or burned each year) and the factors that turn it into activity (Bq per tonne, per GW·a, per m³), and record which years are measured and which have to be modelled.
3. **Stream datasets (Phase 2)** — build each stream's annual series of Bq by nuclide, by containment tier, with low/central/high bounds. Streams are independent, so they can be built in parallel.
4. **Harmonise and model (Phase 3)** — merge the streams, run the stock-and-flow decay and daughter-ingrowth model, convert to radioactive power (W), normalise per TWh, propagate uncertainty, and check against UNSCEAR's 2010 snapshot using dose internally only.
5. **Independent verification (Phase 4)** — a verifier that has not seen the build checks the dataset and every claim the page will make.
6. **Design and build (Phase 5)** — narrative, concepts and interactive build using the user's **Neobrutalism** design system.
7. **Publish (Phase 6)**.

### Settled decisions (decision log)

| ID | Decision | Rationale |
|---|---|---|
| D1 | **Display metric: activity (Bq) by default, with a radioactive power (W) toggle.** Collective dose is calculated **internally only**, to check against UNSCEAR; it never appears on the page. | Keeps the page away from the body and from projections that depend on LNT. Watts weight by decay energy (tritium ≈ 5.7 keV mean β against Po-210 ≈ 5.3 MeV α) without any biology. |
| D2 | **Containment tiers:** Sealed (tank) · Impounded (reservoir behind a dam) · Dispersed (spread on the fields) · Liberated (in the river or sky). A toggle switches between **Inventory** (stacked by tier) and **Liberated**. | Separates material that was *mobilised* from material that was *released*. The water metaphor carries through. |
| D3 | **Persistence by stock and flow.** Each year's additions decay and grow their daughters (Bateman equations); separate charts show **newly released per year** and **total accumulated** (surviving stock). | Fission products drain away; primordial nuclides (U-238, Th-232 chains) are effectively permanent. That contrast is central to the story. |
| D4 | **Streams (5 = `chart-1`…`chart-5`):** ① Nuclear (civil fuel cycle) · ② Coal · ③ Oil and gas (conventional and unconventional shown separately) · ④ Wind and solar materials (wind and solar as sub-series) · ⑤ Other energy (geothermal, biomass/peat, hydro). | Energy only for v1; non-energy sources (phosphate, mineral sands, metals) are left for a sequel. |
| D5 | **Same system boundary for every stream.** Tier 1 (v1) = generating plant + fuel cycle / material supply chain, including construction materials. Tier 2 (transmission, storage, firming) is excluded from v1, but its likely size is measured (Task 2.6). | No stream gets special treatment. Material intensity, including how far materials travel, is part of the story. |
| D6 | **Mines with several products split by economic value at each split point by default**, with both extremes shown as bounds: *all to main product* (e.g. iron at Bayan Obo, copper at Olympic Dam) and *all to the radioactivity-bearing product* (rare earths, uranium). | Standard LCA fallback (ISO 14044); showing both extremes removes any suspicion that the split was chosen to suit a conclusion. |
| D7 | **Uncertainty:** every value carries low/central/high; every data point carries a basis flag (measured / modelled / extrapolated). Bands are drawn on all charts. | Pre-1990 series are mostly modelled as production × factor. |
| D8 | **Normalisation:** absolute and per TWh (per TWh of that stream's own generation). | The ranking changes with the view. |
| D9 | **Accidents and events:** civil accidents and discrete releases (e.g. Chernobyl, Fukushima Daiichi, TMI, Church Rock 1979, TVA Kingston 2008) are part of the dataset and appear as **event markers** that move inventory into the Liberated tier. Military sites and events (e.g. Windscale 1957, Kyshtym/Mayak, Hanford) are **excluded**; atmospheric weapons-test fallout appears **only as a baseline**. | Keeps weapons out of the analysis while still giving scale. |
| D10 | **Geography:** global totals on the page; country-level detail **kept in the dataset** wherever a source provides it. | Don't throw data away. |
| D11 | **Baselines (drawn in the same units):** Earth's radiogenic heat (~20 TW, geoneutrino estimates); K-40 in the oceans; natural radon exhalation from land; cosmogenic production of H-3 and C-14; activity of the top metre of global soil (candidate); atmospheric weapons-test fallout. | Every industrial number is seen next to the natural water table. |
| D12 | **Units:** SI throughout — Bq with prefixes (TBq, PBq, EBq), W, t, m³; curies (Ci) shown in tooltips as the customary equivalent (1 PBq ≈ 27.0 kCi). | House style. |
| D13 | **Working setup:** this folder under git; Python data pipeline (pixi environment, `win-64` + `linux-64`, Python 3.15; `pixi run validate`, `pixi run test`) writing tidy CSV + page-ready JSON; the finished page published as an Artifact using the Neobrutalism design system. Parallel work is capped below the machine's capacity. | Recoverable history; reproducible data. |

---

## Deliverables & Structure

| Artefact | Purpose |
|---|---|
| `PLAN.md` | This document — the single source of truth. |
| `docs/METHODS.md` | Full methodology: definitions, tiers, boundary, allocation, decay model, uncertainty, normalisation, civil/military rule, accident handling. |
| `docs/SCHEMA.md` + `schema/*.json` | Data schema for the master table, sources registry and events table. |
| `docs/DECISIONS.md` | Running decision log (extends D1–D13). |
| `data/reference/nuclides.csv` | Half-lives, decay constants, mean emitted energy per decay, daughters and branching ratios. |
| `data/activity/*.csv` | Activity spine: generation, production, produced water, capacity additions, material intensities (1950–present). |
| `data/streams/<stream>.csv` | Per-stream annual Bq by nuclide × tier × process stage, low/central/high. |
| `data/events.csv` | Catalogue of discrete events. |
| `data/baselines.csv` | Natural and weapons-fallout baselines. |
| `data/sources.csv` | Bibliography registry; every factor links to a source ID. |
| `pipeline/` | Python scripts: build, validate, decay model, power conversion, normalisation, export. |
| `build/radiopassive.json` | Page-ready data export. |
| `site/` | The interactive page source. |
| Published Artifact | The public-facing page. |

---

## Inputs & Resources

- **Design:** Neobrutalism design system — https://claude.ai/artifact/P9xxwLW1LjV8APXFw8Hb6u (DM Sans; `chart-1`…`chart-5`; `border`/`shadow` signature; dark mode via `.dark`; 62 live React 19 components; 40 star shapes).
- **Anchor/validation:** UNSCEAR 2016 Report, Annex A (public exposure from electricity generation, 2010 reference year), plus the earlier UNSCEAR fuel-cycle and natural-source annexes (1982, 1988, 1993, 2000, 2008).
- **Nuclear:** IAEA DIRATA; EU RADD; US NRC annual effluent reports; CNSC (CANDU tritium); OSPAR (Sellafield, La Hague); OECD-NEA/IAEA *Uranium* "Red Book"; WNA; IAEA PRIS (reactor fleet).
- **Coal:** USGS COALQUAL; UNSCEAR coal annexes; published U/Th-in-coal literature (e.g. Finkelman); fly-ash production and use statistics (ACAA and international equivalents); Energy Institute Statistical Review.
- **Oil and gas:** USGS National Produced Waters Geochemical Database; IAEA Safety Reports Series No. 34 (NORM in oil and gas); Pennsylvania DEP 2016 TENORM study; produced-water volume studies (e.g. Veil); EIA/EI production data.
- **Wind and solar materials:** USGS Mineral Commodity Summaries and the user's **USGS Data Series 140 mirror** (historical REE, thorium and other commodity statistics); IAEA Safety Reports Series No. 68 (NORM in rare-earth production); JRC material-intensity studies (Carrara et al.); IEA Critical Minerals Outlook; IRENA capacity statistics.
- **Other energy:** UNSCEAR 2016 (geothermal); geothermal non-condensable gas and scale literature; biomass-ash and fallout-caesium literature.
- **Electricity generation 1950–present:** Energy Institute Statistical Review, Ember, UN Energy Statistics, IEA; Our World in Data for compiled series (traced back to primary sources).
- **Research tools:** web search, Consensus, Valyu, Semantic Scholar, PubMed, Jina, Firecrawl.
- **Compute:** Python 3.10 on the linked machine (Linux shell), plus the cloud workspace for steps that need it.
- **Agents:** `researcher` (sourcing), `executor` (production), `verifier` (independent checks); the main session handles methodology design and resolving contradictions.

---

## Open Questions

None outstanding. OQ1–OQ7 were resolved on 2026-10-20 (the proposed defaults were accepted) and are now decisions:

| ID | Was | Decision |
|---|---|---|
| D14 | OQ1 | **Timeline starts 1950 for every stream**; nuclear reads near zero until ~1956. |
| D15 | OQ2 | **Accidents shown by default**, with an "exclude accidents" toggle. |
| D16 | OQ3 | **Civil/military split by documented end use**; where none is documented, uranium mined before 1965 counts as military. Operational rule in METHODS.md. |
| D17 | OQ4 | **Deep-well injection is "Re-isolated"**, a sub-tier of Impounded. |
| D18 | OQ5 | **Uncertainty as low/central/high bounds for v1**; Monte Carlo only if bounds prove too crude. |
| D19 | OQ6 | **Hosting: Artifact only for v1**; revisit at publish. |
| D20 | OQ7 | **Downloadable CSV on the page**, for sources whose licences permit redistribution. |

Further decisions D21–D26 (from the methods spec) are recorded in `docs/DECISIONS.md`.

Additions accepted with the plan: cosmogenic H-3 and C-14 as a baseline (D11); a factor-of-3 tolerance for the UNSCEAR check (Task 3.5); a findings review before design (Task 4.2).

---

## Tasks

### Phase 0 — Specification

#### Task 0.1: Methods specification

| Field | Detail |
|---|---|
| Description | Write the full methodology, extending D1–D13 into operational rules. |
| Input | This plan; UNSCEAR 2016 Annex A; ISO 14044 allocation guidance; open questions OQ1–OQ5. |
| Output / Effect | `docs/METHODS.md`, `docs/DECISIONS.md`. |
| Done condition | (a) Every decision D1–D13 has an operational rule and a rationale; (b) each stream lists its process stages and candidate nuclides; (c) tier assignment rules cover every process stage, including OQ4; (d) the civil/military rule (OQ3) and the accident rule are stated; (e) the decay, power and normalisation formulas are written in LaTeX; (f) OQ1–OQ5 are resolved and recorded; (g) the user has signed off. |
| Verification | `verifier` checks completeness against (a)–(f); user sign-off for (g). |

#### Task 0.2: Data schema

| Field | Detail |
|---|---|
| Description | Define the long-format master table, sources registry and events table. |
| Input | Task 0.1. |
| Output / Effect | `docs/SCHEMA.md`, `schema/master.json`, `schema/sources.json`, `schema/events.json`, `pipeline/validate.py`. |
| Done condition | The master schema includes at least: `year, stream, substream, process_stage, country, nuclide, tier, quantity, unit, value_low, value_central, value_high, basis, source_id, allocation_rule, notes`; `validate.py` accepts 10 hand-written valid example rows and rejects 10 deliberately invalid rows (wrong unit, missing source, low > high, unknown nuclide, etc.). |
| Verification | Run the validator on both example sets; `verifier` reviews the schema against METHODS.md. |

#### Task 0.3: Nuclide reference table

| Field | Detail |
|---|---|
| Description | Build the physical constants table used by the decay and power models. |
| Input | ICRP Publication 107; ENSDF/NNDC; the nuclide lists from Task 0.1. |
| Output / Effect | `data/reference/nuclides.csv`. |
| Done condition | Every nuclide named in METHODS.md is present, with half-life, decay constant, mean energy per decay excluding antineutrinos (split α / β / γ+X), daughters and branching ratios; the full U-238, U-235 and Th-232 chains are present; every row has a source; 10 randomly chosen values match an independent source to within 1%, **or** any mismatch is shown to be a documented difference between evaluations rather than a transcription error, with inter-evaluation spreads carried into the pipeline as uncertainty bands *(amended 2026-10-20, D27)*. |
| Verification | `verifier` spot-checks 10 random rows against a second source. |

---

### Phase 1 — Source inventory & research

#### Task 1.1: UNSCEAR extraction and the "why solar" question

| Field | Detail |
|---|---|
| Description | Read UNSCEAR 2016 Annex A (and the earlier fuel-cycle annexes); extract normalised release factors per stream and period, and find out what drives the solar/wind occupational-dose finding. |
| Input | UNSCEAR reports. |
| Output / Effect | `research/unscear_extraction.csv` + `research/unscear_notes.md`. |
| Done condition | Release factors for every stream UNSCEAR covers, each with a page reference; a direct quote or table reference answering what drives the high solar/wind worker dose (rare earths vs total earth moved by low-grade ore mining); the 2010 reference values recorded for later validation (Task 3.5). |
| Verification | `verifier` checks every extracted value against the cited page. |

#### Tasks 1.2–1.6: Source inventory per stream

One task per stream: **1.2 Nuclear · 1.3 Coal · 1.4 Oil and gas · 1.5 Wind and solar materials · 1.6 Other energy.**

| Field | Detail |
|---|---|
| Description | Build an annotated bibliography and data-availability matrix for the stream. |
| Input | Task 0.1 process stages; Inputs & Resources list. |
| Output / Effect | `research/<stream>/bibliography.md`, `research/<stream>/availability.csv`. |
| Done condition | ≥ 10 primary sources (≥ 5 for Other energy), each entered in `data/sources.csv`; a matrix of process stage × decade (1950s–2020s) marking measured / modelled / no data; for every gap, a proposed modelling approach (factor + activity proxy); any inaccessible sources listed with their URLs for the user to try. |
| Verification | `verifier` confirms the matrix covers every process stage in METHODS.md and that ≥ 3 random sources say what the annotations claim. |

#### Task 1.7: Baselines

| Field | Detail |
|---|---|
| Description | Source and calculate the natural and weapons-fallout baselines in Bq and W. |
| Input | UNSCEAR natural-sources and fallout annexes; geoneutrino literature; ocean chemistry; cosmogenic production literature. |
| Output / Effect | `data/baselines.csv` + a short calculation note. |
| Done condition | All D11 baselines present, each with value, unit, derivation shown in LaTeX and ≥ 1 source; any baseline with a calculated value is reproduced by a script. |
| Verification | `verifier` recalculates each derived baseline independently. |

#### Task 1.8: Events catalogue

| Field | Detail |
|---|---|
| Description | Catalogue discrete events that move inventory between tiers. |
| Input | Literature, regulator reports. |
| Output / Effect | `data/events.csv`. |
| Done condition | ≥ 15 events across ≥ 4 streams, each with date, location, stream, tier movement, activity estimate (low/central/high) and ≥ 1 source; the inclusion threshold is stated in METHODS.md; military events excluded per D9. |
| Verification | `verifier` checks 5 random events against sources. |

#### Task 1.9: Activity data spine

| Field | Detail |
|---|---|
| Description | Assemble the annual driver series that factors are multiplied against. |
| Input | Generation and production statistics; USGS DS140 mirror; IRENA; material-intensity studies. |
| Output / Effect | `data/activity/*.csv` + sanity plots. |
| Done condition | Annual series 1950–present (or from the series' natural start) for: electricity by source; coal production and consumption; oil and gas production; produced-water volumes (with the unconventional share); uranium production; REE production by country; wind and solar capacity additions by technology; material intensity by technology and year. Every series has source and basis flags, and any gap is filled by a stated method. |
| Verification | `verifier` compares 3 random years per series against an independent source. |

---

### Phase 2 — Stream datasets (parallel)

#### Tasks 2.1–2.5: Build stream dataset

One task per stream: **2.1 Nuclear · 2.2 Coal · 2.3 Oil and gas · 2.4 Wind and solar materials · 2.5 Other energy.**

Process stages to cover (from METHODS.md; indicative):
- **Nuclear:** mining and milling (tailings inventory, radon); conversion and enrichment; fuel fabrication; reactor effluents by reactor type (PWR, BWR, PHWR/CANDU, GCR, RBMK); reprocessing; spent fuel and high-level waste (Sealed); civil accidents.
- **Coal:** mining (radon, mine water); combustion stack emissions by control-technology era; ash and FGD gypsum inventory (Impounded / Dispersed via utilisation).
- **Oil and gas:** produced water by disposal route (injection, surface discharge, road spreading); scale and sludge; gas processing (Rn-222, Pb-210, Po-210); radon in delivered gas; conventional and unconventional separately.
- **Wind and solar materials:** material intensity per MW by technology (c-Si, CdTe, CIGS; geared and direct-drive wind) mapped to commodity supply chains (REE, Cu, Al/bauxite, Fe + coking coal, Ag, metallurgical Si via coal/coke, Te, In, glass, concrete); radioactivity per tonne of each commodity; D6 allocation with bounds. Embedded-fuel contributions (coking coal, coal/coke for metallurgical Si, coal-fired smelting power) are counted in ④ **in the electricity lifecycle view only**; in the industry view they are already inside ② and ③ (D22).
- **Other energy:** geothermal (non-condensable gas Rn-222, scale); biomass and peat (K-40, re-released fallout Cs-137); hydro (shown as negligible, with the basis stated).

| Field | Detail |
|---|---|
| Description | Turn activity data × factors into annual Bq by nuclide × tier × process stage, with low/central/high. |
| Input | Tasks 0.1–0.3, 1.1, the relevant 1.2–1.6, 1.8, 1.9. |
| Output / Effect | `data/streams/<stream>.csv`; `pipeline/streams/<stream>.py`. |
| Done condition | (a) The dataset passes `validate.py`; (b) every factor traces to a `source_id`; (c) the script reproduces the CSV from raw inputs; (d) every process stage in METHODS.md is present or explicitly marked negligible with justification; (e) totals for ≥ 2 benchmark years agree with ≥ 2 independent published estimates to within a factor of 3, or the discrepancy is explained in a note. |
| Verification | Rerun the script and diff the output; `verifier` checks (b), (d), (e). |

#### Task 2.6: Tier 2 magnitude estimate

| Field | Detail |
|---|---|
| Description | Estimate whether transmission, storage and firming would change any stream's Tier 1 total by a meaningful amount. |
| Input | Grid material-intensity literature; Task 2.4 commodity factors. |
| Output / Effect | `research/tier2_memo.md`. |
| Done condition | For each stream, a bounded estimate (low/high) of Tier 2 as a % of Tier 1 for a benchmark year, with sources; a recommendation on whether v2 should include Tier 2 (threshold: > 5% of any stream's total). |
| Verification | `verifier` recalculates the estimate for one stream. |

---

### Phase 3 — Harmonise & model

#### Task 3.1: Master dataset merge

| Field | Detail |
|---|---|
| Description | Merge all stream datasets into one validated master table; events and baselines are validated alongside it and exported separately (baselines are not master rows; SCHEMA §4.5). *(Amended 2026-10-20 after the schema review.)* |
| Input | Tasks 2.1–2.5, 1.7, 1.8. |
| Output / Effect | `build/master.csv`. |
| Done condition | `build/master.csv` passes `validate.py` together with every reference and support table; units harmonised to Bq; no duplicate keys; the sum of per-stream totals equals the master total for every year (exact). |
| Verification | Automated checks in `pipeline/tests/`. |

#### Task 3.2: Decay and ingrowth engine

| Field | Detail |
|---|---|
| Description | Stock-and-flow model using Bateman equations: each year's additions decay and grow daughters, by tier. |
| Input | Task 3.1; `nuclides.csv`. |
| Output / Effect | `pipeline/decay.py`; `build/stocks.csv`. |
| Done condition | Unit tests pass for: (i) single-nuclide decay matching $A(t)=A_0e^{-\lambda t}$ to within 0.1%; (ii) a parent–daughter pair matching the analytic two-member Bateman solution; (iii) the U-238 chain reaching secular equilibrium; (iv) Ra-226 grow-in from separated Th-230; (v) atoms conserved across a 10-member chain. The stock series is generated for all streams. |
| Verification | Test suite; `verifier` reviews the test cases against the textbook solutions. |

#### Task 3.3: Radioactive power conversion

| Field | Detail |
|---|---|
| Description | Convert Bq to W using mean emitted energy per decay (antineutrinos excluded). |
| Input | Task 3.2; `nuclides.csv`. |
| Output / Effect | W columns in `build/stocks.csv` and in the flow tables. |
| Done condition | Hand calculations for 3 nuclides (H-3, Cs-137, Po-210) match the pipeline to within 0.1%; the derivation is in METHODS.md. |
| Verification | Automated test against the hand calculations. |

#### Task 3.4: Normalisation

| Field | Detail |
|---|---|
| Description | Express every series per TWh of the stream's own generation. |
| Input | Task 3.3; Task 1.9 electricity series. |
| Output / Effect | Per-TWh series. |
| Done condition | Every stream-year with generation > 0 has a per-TWh value; years with no generation are marked, not set to zero; spot-checks for 3 stream-years match hand calculations. |
| Verification | Automated test. |

#### Task 3.5: Internal dose check (never displayed)

| Field | Detail |
|---|---|
| Description | Calculate the 2010 collective dose per stream using UNSCEAR's own release-to-dose factors, purely to check our release estimates. |
| Input | Task 3.1; Task 1.1 reference values. |
| Output / Effect | `research/validation_2010.md` (internal). |
| Done condition | Each stream UNSCEAR covers is within a factor of 3 of UNSCEAR's 2010 value, or the discrepancy is explained and recorded in METHODS.md. No dose quantity is exported to `build/radiopassive.json`. |
| Verification | `verifier` reviews the comparison; an automated check confirms no dose fields are in the export. |

#### Task 3.6: Uncertainty propagation

| Field | Detail |
|---|---|
| Description | Propagate low/central/high through decay, power and normalisation (method per OQ5). |
| Input | Tasks 3.2–3.4. |
| Output / Effect | Banded series in all outputs. |
| Done condition | low ≤ central ≤ high holds for every row; the method is documented; the measured/modelled flag survives into the export. |
| Verification | Automated invariant checks. |

#### Task 3.7: Page-ready export

| Field | Detail |
|---|---|
| Description | Export compact JSON for the page. |
| Input | Tasks 3.1–3.6. |
| Output / Effect | `build/radiopassive.json`. |
| Done condition | Contains every series each chart needs (flow, stock, tiers, Bq/W, absolute/per-TWh, allocation bounds, accidents in/out, baselines, events); ≤ 2 MB; a JSON schema validates it. |
| Verification | Schema validation; size check. |

---

### Phase 4 — Independent verification

#### Task 4.1: Blind dataset audit

| Field | Detail |
|---|---|
| Description | A `verifier` that has not seen the build process audits the dataset. |
| Input | `build/master.csv`, `data/sources.csv`, METHODS.md. |
| Output / Effect | `research/audit.md`. |
| Done condition | 100% of factors contributing > 1% of any stream's total, plus a random 20% of the rest, checked against their sources; every finding fixed or accepted with a recorded reason. |
| Verification | The audit report itself; the user reviews unresolved findings. |

#### Task 4.2: Findings review

| Field | Detail |
|---|---|
| Description | Present the headline numbers and charts (plain, unstyled) to the user before any design work. |
| Input | Task 3.7. |
| Output / Effect | A findings brief with draft charts. |
| Done condition | The user has reviewed and accepted the headline findings, or requested changes that have been made. |
| Verification | User sign-off. |

---

### Phase 5 — Design & build

#### Task 5.1: Narrative and page structure

| Field | Detail |
|---|---|
| Description | Story outline built on the water metaphor; list of charts and controls; draft copy. |
| Input | Task 4.2 findings; the Neobrutalism README (voice: short, declarative). |
| Output / Effect | `site/OUTLINE.md` (+ an optional Whimsical wireframe). |
| Done condition | Every chart from D1–D11 is placed in the narrative; every claim in the copy traces to a dataset field or source; the user approves the outline. |
| Verification | `verifier` checks every claim against the data; user sign-off. |

#### Task 5.2: Visual concepts

| Field | Detail |
|---|---|
| Description | 2–3 static concepts of the key views using Neobrutalism tokens. |
| Input | Task 5.1; the Neobrutalism design system. |
| Output / Effect | Concept mockups. |
| Done condition | Each concept uses only system tokens (colours, type scale, border/shadow, radius); streams mapped to `chart-1`…`chart-5` in order; text contrast ≥ 4.5:1 in light and dark; the user picks one. |
| Verification | Contrast check; user choice. |

#### Task 5.3: Interactive build

| Field | Detail |
|---|---|
| Description | Build the page and its controls. |
| Input | Tasks 3.7, 5.1, 5.2. |
| Output / Effect | `site/` source; a single self-contained page. |
| Done condition | Working controls: Inventory/Liberated; Bq/W; absolute/per-TWh; allocation bounds (value / main product / radioactive product); accidents on/off; baselines overlay; events markers with detail; uncertainty bands; measured/modelled styling. Flow and stock charts are separate. All controls pass an end-to-end browser test. |
| Verification | `webapp-tester` Playwright suite; `verifier` checks the rendered numbers against the JSON for 10 random points. |

#### Task 5.4: Methods and sources section

| Field | Detail |
|---|---|
| Description | A readable methods summary and full source list on the page; downloadable data where licences permit (OQ7). |
| Input | METHODS.md; `sources.csv`. |
| Output / Effect | Page section + CSV download. |
| Done condition | Every source in `sources.csv` is listed with a working link or citation; the key decisions D1–D9 are explained in plain language; the licence status of the download is recorded. |
| Verification | Link check; `verifier` review. |

#### Task 5.5: Responsive, dark mode and accessibility pass

| Field | Detail |
|---|---|
| Description | Make sure the page works at phone width, in dark mode and with a keyboard. |
| Input | Task 5.3. |
| Output / Effect | Fixes merged. |
| Done condition | No horizontal scroll at 360 px width; every control keyboard-operable with a visible focus ring; dark mode correct per the Neobrutalism rules; series distinguishable without relying on hue alone. |
| Verification | `webapp-tester` at 360 / 768 / 1300 px in light and dark. |

---

### Phase 6 — Publish

#### Task 6.1: Publish and record

| Field | Detail |
|---|---|
| Description | Publish the page as an Artifact; write a project summary doc. |
| Input | Phase 5 outputs. |
| Output / Effect | Published Artifact; project summary. |
| Done condition | The published page renders with every control working; the final git tag `v1.0` is created; the summary lists the findings, the known limitations and the sequel scope (non-energy sources, Tier 2). |
| Verification | Final check of the live page; user sign-off. |

---

## Task Ordering

**Mixed.**

- **Phase 0:** sequential (0.1 → 0.2 → 0.3; 0.3 may start once 0.1's nuclide lists exist).
- **Phase 1:** 1.1 first (it informs the factors); then **1.2–1.9 in parallel** (capped at 3 concurrent agents).
- **Phase 2:** **2.1–2.5 in parallel** (capped at 3 concurrent); each stream needs its own Phase 1 task plus 1.8 and 1.9. 2.6 runs after 2.4.
- **Phase 3:** sequential (3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7).
- **Phase 4:** 4.1 → 4.2.
- **Phase 5:** sequential (5.1 → 5.2 → 5.3 → 5.4 → 5.5).
- **Phase 6:** after everything else.

Every task goes through produce → verify → record (git commit) → run past the user before the next dependent task starts.
