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

## Proposed — awaiting sign-off

| ID | Proposal | Section |
|---|---|---|
| PD1 | Processing residues counted; overburden/waste rock as memo unless above GSR Part 3 NORM thresholds. | METHODS §5.3 |
| PD2 | Industry view and electricity lifecycle view; stacked totals only within one view. | METHODS §6.1 |
| PD3 | Levelised per-TWh for construction-phase releases. | METHODS §8 |
| PD4 | Count all decays in each nuclide group (head-only kept as alternative). | METHODS §3.2 |
