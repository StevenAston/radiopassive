# Phase 1 research brief (shared by Tasks 1.2–1.9)

Read before starting:
- `PLAN.md`: your task's row, done condition and verification.
- `docs/METHODS.md`: in full. §5 tiers, §6.3 stage map, §9 events, §10 allocation and §11 sources matter most.
- `docs/SCHEMA.md`: §4 for the table formats you write, and §5 for the vocabularies.
- `research/unscear_notes.md`: what UNSCEAR already covers, and its gaps. Do not redo it; cite its sources by ID (S0001–S0010).

## Rules

- **Sources**
  - Follow the source hierarchy in METHODS §11.3.
  - Never use Grokipedia. Wikipedia only as a lead to primary sources, never cited.
  - Every new source goes into your `sources_task1X.csv` in SCHEMA §4.3 format, using **only your assigned ID range**.
  - A `url` is required whenever access is `paywalled` or `inaccessible`.
- **Inaccessible sources:** record the URL in your notes so Steve can try it himself. Do not keep hunting for alternatives once one fails.
- **Never invent numbers.** If you estimate, say so, and mark the basis `modelled` with the method.
- **No dose in deliverables (D1).** Dose figures may be noted only as validation context.
- **Style:** SI units in prose, Canadian/UK spelling.
- **Scripts:** throwaway scripts go in `/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/<task>/`, never in outputs. At most 2 concurrent processes.
- **Write only your own task's files.**

## Source-ID ranges

| Task | Range |
|---|---|
| 1.2 Nuclear | S0100–S0199 |
| 1.3 Coal | S0200–S0299 |
| 1.4 Oil and gas | S0300–S0399 |
| 1.5 Wind and solar materials | S0400–S0499 |
| 1.6 Other energy | S0500–S0599 |
| 1.7 Baselines | S0600–S0699 |
| 1.8 Events | S0700–S0799 |
| 1.9 Activity data | S0800–S0999 |

## Deliverables for the per-stream source surveys (Tasks 1.2–1.6)

1. **`research/<stream>/bibliography.md`**: an annotated bibliography with at least 10 primary sources (at least 5 for Other energy). Each entry gives the source ID, what it gives us (which stage, nuclides, years, geography), its quality and any caveats.
2. **`research/<stream>/availability.csv`**, with columns `stage, substream, product_or_commodity, decade, status, best_source_ids, proposed_method, notes`.
   - `stage` uses the stage codes from SCHEMA §5.2.
   - `decade` runs from 1950s to 2020s; add a `pre1950` row where residues predate 1950 (D31).
   - `status` is one of `measured`, `compiled`, `modelled_possible`, `no_data`.
   - For every gap, give a proposed modelling approach (activity proxy × factor).
3. **`research/<stream>/notes.md`**: method, key factor ranges found (with source IDs), open issues, and inaccessible URLs.
4. **`research/<stream>/sources_task1X.csv`**: your new sources, in SCHEMA §4.3 format.
