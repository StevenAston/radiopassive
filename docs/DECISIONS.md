# Radiopassive — Decision Log

Each decision records what was decided, when, and where it is made operational. Rationales are in `PLAN.md` (D1–D20) and `docs/METHODS.md`.

| ID | Date | Decision | Operational in |
|---|---|---|---|
| D1 | 2026-10-20 | Display metric: Bq by default, W toggle; collective dose internal only (UNSCEAR check), never displayed. | METHODS §3, §7, §14 |
| D2 | 2026-10-20 | Containment tiers Sealed / Impounded / Dispersed / Liberated; Inventory ↔ Liberated toggle. | METHODS §5 |
| D3 | 2026-10-20 | Stock and flow with Bateman decay and ingrowth; separate flow and stock charts. | METHODS §12 |
| D4 | 2026-10-20 | Five streams (nuclear, coal, oil and gas, wind and solar materials, other energy) on `chart-1`…`chart-5`. | METHODS §2.3 |
| D5 | 2026-10-20 | Same Tier 1 boundary for every stream incl. construction materials; Tier 2 excluded from v1 but measured. | METHODS §6 |
| D6 | 2026-10-20 | Value-based split for mines with several products by default; both extremes shown as bounds. | METHODS §10.1 |
| D7 | 2026-10-20 | Low/central/high on every value; basis flag on every row. | METHODS §11 |
| D8 | 2026-10-20 | Absolute and per-TWh views. | METHODS §8 |
| D9 | 2026-10-20 | Civil accidents and events included; military excluded; weapons fallout as baseline only. | METHODS §9 |
| D10 | 2026-10-20 | Global totals on page; country-level detail kept in data. | METHODS §2.2 |
| D11 | 2026-10-20 | Baselines incl. Earth radiogenic heat, ocean K-40, radon exhalation, cosmogenic H-3/C-14, soil (candidate), weapons fallout. | METHODS §13 |
| D12 | 2026-10-20 | SI units; curies in tooltips. | METHODS §3.3 |
| D13 | 2026-10-20 | Git-tracked folder; Python pipeline; Artifact page with Neobrutalism; capped parallelism. | PLAN |
| D14 | 2026-10-20 | Timeline 1950 for every stream. | METHODS §2.1 |
| D15 | 2026-10-20 | Accidents shown by default, exclude toggle. | METHODS §9.1 |
| D16 | 2026-10-20 | Civil/military by documented end use; uranium mined before 1965 military by default. | METHODS §9.2 |
| D17 | 2026-10-20 | Deep-well injection = "Re-isolated" sub-tier of Impounded. | METHODS §5.1 |
| D18 | 2026-10-20 | Uncertainty as bounds for v1; Monte Carlo only if needed. | METHODS §11.1 |
| D19 | 2026-10-20 | Hosting: Artifact only for v1. | PLAN |
| D20 | 2026-10-20 | Downloadable CSV where licences permit. | PLAN, Task 5.4 |
| D21 | 2026-10-20 | (was PD1) Processing residues counted; overburden/waste rock as memo series unless any U/Th-chain nuclide > 1 Bq/g or K-40 > 10 Bq/g. | METHODS §5.3 |
| D22 | 2026-10-20 | (was PD2) Industry view (default, absolute) and electricity lifecycle view (per-TWh, UNSCEAR check); stacked totals only within one view. | METHODS §6.1 |
| D23 | 2026-10-20 | (was PD3) Construction-phase releases levelised over expected lifetime generation for per-TWh; annual ratio kept as secondary. | METHODS §8 |
| D24 | 2026-10-20 | (was PD4) Count all decays in each nuclide group; head-only activity kept as an alternative. | METHODS §3.2 |
| D25 | 2026-10-20 | (was PD5) Per-TWh chronic residue flows committed over 100 a (500 a, 10 000 a kept) and charged to the creating generation; stocks not normalised per TWh. | METHODS §8 |
| D26 | 2026-10-20 | (was PD6) Oil and gas sub-streams: conventional, unconventional, oil sands / extra-heavy oil. | METHODS §2.3 |
| D27 | 2026-10-20 | Task 0.3 done condition amended: a spot-check mismatch passes if documented as an inter-evaluation difference (not a transcription error); inter-evaluation spreads become uncertainty bands. | PLAN Task 0.3; research/task0.3_notes.md §11.4 |
| D28 | 2026-10-20 | Radiopassive is non-commercial; ICRP 107 data used under ICRP's educational/research/not-for-profit terms. Revisit if the project ever becomes commercial. Reference tables derived from ICRP data are not offered in the page's CSV download. | sources S9001–S9003 |
| D29 | 2026-10-20 | Environment: pixi (Steve's `pixi.toml`), platforms `win-64` + `linux-64`, Python 3.15; Claude's Linux environment is detached outside the project folder. | pixi.toml |
| D30 | 2026-10-20 | (was PD7) Decommissioning releases levelised like construction: over the plant's actual lifetime generation, or expected lifetime generation if not yet retired. | METHODS §8 |
| D31 | 2026-10-20 | (was PD8) Opening stock at 1 January 1950 for residues created before 1950, estimated from pre-1950 production with the same factors, decayed to 1950, flagged `modelled`, shown as a distinct band. | METHODS §2.1; SCHEMA §3.2 |
| D32 | 2026-10-25 | Events catalogue accepted with 3 streams (nuclear, coal, wind and solar materials): no civil oil and gas or other-energy event meets §9.1; the negative search is recorded and is itself a finding. | PLAN Task 1.8; research/events/notes.md |
| D33 | 2026-10-25 | Event mass criterion counts gross released mass including entrained water or process liquor; activity always computed on solids. Keeps Dan River, Partizansk and Obed Mountain. | METHODS §9.1 |
| D34 | 2026-10-25 | Chalk River NRX 1952 excluded as military (plutonium to the US weapons programme; military clean-up). Steve's reading, recorded as such. | METHODS §9.2 |
| D35 | 2026-10-25 | Nuclide reference addendum approved (additions only): Ni-59, Zr-93, Nb-93m, Nb-94, Sn-126, Am-242m, Zr-95, Nb-95, Cm-242, Sr-89, Te-129m, Cs-136, Ce-141. | data/reference/nuclides.csv, groups.csv |
| D36 | 2026-10-25 | Stage tiers: `coal_mining` gains `dispersed`; `accident` gains `sealed_fuel_cycle` (Tokaimura refiled to `accident`). | vocab.json; SCHEMA §5; METHODS §6.3 |
| D37 | 2026-10-25 | Household (domestic) biomass heating is in scope for stream ⑤, consistent with coal including non-power use. | METHODS §2.3 / §6.3 (to be written with the addendum) |
| D38 | 2026-10-25 | Steve's local USGS DS140 mirror may be read but never written; all outputs go to the radiopassive folder. | research/activity |
| D39 | 2026-10-25 | Commodity prices stored as USD/t (nominal) and USD1998/t (constant 1998 dollars), US-market unit values from DS140; a documented non-SI exception. | data/activity/commodity_prices.csv; SCHEMA §4.6 |

No proposals outstanding.

**Phase 0 closed 2026-10-20.** Task 0.1 (methods), Task 0.2 (schema v2.1, validator, 556 spec-blind tests) and Task 0.3 (nuclide reference table) signed off by Steve.
