# Phase 2 plan: stream datasets (proposal for Steve's approval)

Status: **proposal, 2026-10-25**. Nothing in here is built yet. Per Steve's standing rule, no pipeline code is written until this plan is approved.

## 1. What Phase 2 produces

For each stream ①–⑤:
- `data/factors/<stream>.csv`: emission and residue factors (SCHEMA §4.8), compiled from the Phase 1 research notes. Each row has a source and low/central/high bounds.
- `data/reference/commodity_factors.csv`: per-tonne commodity footprints (SCHEMA §4.7), for ④ and for construction in every stream.
- `data/reference/residue_types.csv`: the empty ε (radon escape) and seepage columns get values, one per residue type, from the Phase 1 proposals.
- `pipeline/streams/<stream>.py`: multiplies activity series × factors, applies the D6 allocation and writes master rows.
- `data/streams/<stream>.csv`: annual master rows, as Bq by group × tier × stage × country, with low/central/high.
- Tests for each stream, plus a benchmark comparison (PLAN done condition (e): two benchmark years, two independent estimates, within a factor of 3).
- Task 2.6: `research/tier2_memo.md` (transmission, storage and firming). This is research only, with no code.

Decay, ingrowth, chronic exhalation, seepage, W conversion and normalisation are **not** in Phase 2. They belong to the Phase 3 engine. Phase 2 rows are the raw inputs to that engine.

## 2. Proposed code structure

```
pipeline/
  validate.py            (exists)
  lib/
    io.py                load/save CSV tables with the schema coercion validate.py already uses
    bounds.py            low/central/high arithmetic: products by log quadrature, sums side by side, zero floors (METHODS §11)
    allocation.py        D6 value/mass/main/radio splits, from commodity_prices.csv and co-product data
    factors.py           factor lookup by (stream, stage, product, group, technology, era)
    rows.py              build master rows with key, basis, source_ids, factor_ids and allocation tokens
  streams/
    coal.py  nuclear.py  oil_gas.py  wind_solar.py  other.py
  tests/
    (existing 556 spec-blind validator tests)
    streams/test_<stream>.py   new spec-blind tests per stream
```

- Pure standard library + pandas (already in the pixi environment) + numpy.
- No network access at build time. Everything reads from `data/` and `research/activity/raw/`.
- Each stream script supports `--write`. Without it, it writes to a scratch folder and diffs against the committed file, the same pattern as `research/baselines/compute_baselines.py` and `research/activity/scripts/run_all.py`.
- Parallelism is capped at 2 processes.

## 3. Order and agents

| Step | Task | Why this order |
|---|---|---|
| 1 | `pipeline/lib/` + its tests | Shared by every stream. The bounds and allocation arithmetic must be right once. |
| 2 | **2.2 Coal** (pilot) | Richest data, simplest stages (mining, power and non-power combustion, ash fate). It proves the pattern. |
| 3 | 2.1 Nuclear, 2.3 Oil and gas, 2.5 Other energy | In parallel (3 agents max), each following the coal pattern. |
| 4 | 2.4 Wind and solar materials | Depends on `commodity_factors.csv` and on 2.2/2.3 for embedded fuel (lifecycle view only, D22). |
| any | 2.6 Tier 2 memo | Research only. It can run alongside step 2 or 3. |

Each step follows the agreed workflow:
1. A test-writer writes spec-blind tests from the done condition. It never reads the implementation.
2. A code-writer implements the step.
3. A linter checks it.
4. An independent verifier checks done conditions (b), (d) and (e).
5. Sync, commit, and your sign-off.

## 4. Decisions needed before building

1. **Storage of memo series (D43/D44).** Wood-ash fallout Cs-137 and wood natural nuclides are memo series, but the schema only has `memo_earth_moved`. Options:
   - **(a)** Add a tier value `memo_biosphere`. It would sit outside tier totals like `memo_earth_moved`, and the change is one vocab line plus validator support. *(recommended)*
   - **(b)** Keep a separate `data/streams/memo.csv` with the same columns.
2. **Marking re-release rows (D43).** METHODS identifies them by group + stage, which needs no schema change. The alternative is an explicit route value, `air_rerelease`. I recommend the explicit route, because it can't be misread.
3. **Pu-239 + Pu-240 combined reports (D42).** OSPAR and others report the two together. Proposed split rule: use activity ratios by facility type from the literature (e.g. reprocessing discharges ≈ the spent-fuel Pu-240/Pu-239 activity ratio), with bounds. The multiplier then applies to the Pu-239 share.
4. **Pu239 group ID.** Keep `Pu239` (recommended), or rename it `Pu239+` and have the test-writer update one fixture.
5. **Benchmark sources for done condition (e).** Proposed: the UNSCEAR 2016 Annex B per-GW·a figures for ①②③⑤, and IAEA SRS-68/TRS-419 plus the Task 1.5 references for ④. Any you'd add?

## 5. Known data limits carried into Phase 2

These are stated on the rows, not hidden:
- **Spent fuel:** discharge sits 36% above the commonly quoted 7,000 tHM/a, and the IAEA's own figures disagree with each other.
- **Coal power share:** only two anchors (2012 and 2023). Before 2012 it is interpolated.
- **1 a in-core coverage:** marginal (99.1%). Pu-239 fission yields are unverified.
- **Biomass:** no stack measurements for household stoves; no radionuclide data for charcoal anywhere.
- **Fly-ash utilisation:** missing (ACAA unreachable), so the impounded/dispersed ash split uses literature shares.
