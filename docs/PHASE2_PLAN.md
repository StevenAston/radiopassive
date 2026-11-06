# Phase 2 plan: stream datasets

Status: **APPROVED by Steve, 2026-10-25.** Progress in §6. Section 4 decisions recorded as D47 (memo_biosphere), D48 (air_rerelease), D49 (Pu-239/240 split), D50 (Pu239 ID kept), D51 (benchmarks). Schema v2.2 carries D47/D48 (now v2.5).

## 1. What Phase 2 produces

For each stream ①–⑤:
- `data/factors/<stream>.csv`: emission and residue factors (SCHEMA §4.8), compiled from the Phase 1 research notes. Each row has a source and low/central/high bounds.
- `data/reference/commodity_factors.csv`: per-tonne commodity footprints (SCHEMA §4.7), for ④ and for construction in every stream.
- `data/reference/residue_types.csv`: the ε (radon escape) and seepage columns, one value set per residue type, from the Phase 1 proposals.
- `pipeline/streams/<stream>.py`: multiplies activity series × factors, applies the D6 allocation and writes master rows.
- `data/streams/<stream>.csv.gz`: annual master rows, as Bq by group × tier × stage × country, with low/central/high (gzipped since D72; pre-1950 rows in `data/streams_pre1950/<stream>.csv.gz`).
- Tests for each stream, plus a benchmark comparison (PLAN done condition (e): two benchmark years, two independent estimates, within a factor of 3).
- Task 2.6: `research/tier2_memo.md` (transmission, storage and firming). This is research only, with no code.

Decay, ingrowth, chronic exhalation, seepage, W conversion and normalisation are **not** in Phase 2. They belong to the Phase 3 engine. Phase 2 rows are the raw inputs to that engine.

## 2. Code structure

```
pipeline/
  validate.py
  lib/        io.py  bounds.py  allocation.py  factors.py  rows.py
  streams/    _outputs.py  coal.py  nuclear.py  oil_gas.py  other.py  (wind_solar.py to come)
  tests/      validator, lib, research and per-stream spec-blind suites
```

- Pure standard library + pandas + numpy.
- No network access at build time. Everything reads from `data/` and `research/activity/raw/` (untracked raw downloads are pinned by `research/activity/raw/MANIFEST.csv` and archived with zpaqfranz, `docs/DATA_ARCHIVE.md`).
- Each stream script supports `--write`. Without it, it builds to a scratch folder and diffs (decompressed) against the committed files.
- Parallelism is capped at 2 processes.

## 3. Order and agents

| Step | Task | Why this order |
|---|---|---|
| 1 | `pipeline/lib/` + its tests | Shared by every stream. The bounds and allocation arithmetic must be right once. |
| 2 | **2.2 Coal** (pilot) | Richest data, simplest stages. It proves the pattern. |
| 3 | 2.1 Nuclear, 2.3 Oil and gas, 2.5 Other energy | In parallel (up to 4 agents), each following the coal pattern. |
| 4 | 2.4 Wind and solar materials | Depends on `commodity_factors.csv` and on 2.2/2.3 for embedded fuel (lifecycle view only, D22). |
| any | 2.6 Tier 2 memo | Research only. |

Each step follows the agreed workflow:
1. A test-writer writes spec-blind tests from the done condition. It never reads the implementation.
2. A code-writer implements the step.
3. A linter checks it.
4. An independent verifier rebuilds the outputs independently, checks done conditions and runs mutation tests.
5. Sync, commit, and Steve's sign-off.

## 4. Decisions needed before building

(All resolved: D47–D51.)

## 5. Known data limits carried into Phase 2

These are stated on the rows, not hidden:
- **Spent fuel:** discharge sits 36% above the commonly quoted 7,000 tHM/a, and the IAEA's own figures disagree with each other.
- **Coal power share:** only two anchors (2012 and 2023). Before 2012 it is interpolated.
- **1 a in-core coverage:** marginal (99.1%). Pu-239 fission yields are unverified.
- **Biomass:** no stack measurements for household stoves; no radionuclide data for charcoal anywhere.
- **Fly-ash utilisation:** US shares now rest on the full ACAA archive 1966–2024 (D73, coal:0080–0094, five eras). They are inert until a US ash branch exists. Outside the US, the world shares (coal:0040–0048) still rest on literature and must span India, China and the EU.

## 6. Progress

| Step | Status |
|---|---|
| 1 `pipeline/lib/` | v1.2 signed off (D52, commit 9efe386); v1.4 substream key (D63); **v1.5 gzipped stream outputs (D72, 2026-11-06, commit 6bad906)**: 132.3 MB → 7.8 MB, byte-identical content; raw-input manifest + zpaqfranz archive (commit 84e1557, 184 files, 837 MB pinned). |
| 2 Coal pilot (2.2) | **Signed off by Steve, 2026-10-27.** COAL_SPEC v1.3 (D52–D60, D73). D73 (2026-11-06, commit 67b00c8): ACAA US ash route shares, no output change. Benchmarks pass the ×3 rule against UNSCEAR 2016 Annex B and independent estimates; the stream sits 2–3.5× above the UK 1998 figures (COAL_SPEC §12.17). |
| 3a Nuclear (2.1) | **Signed off by Steve 2026-11-04** (independent verification PASS; 69,048 rows; NUCLEAR_SPEC v1.2; D64–D69; commit d12e715). |
| 3b Oil and gas (2.3) | **Signed off by Steve 2026-11-06.** OIL_GAS_SPEC v1.1 (D70, D71). 112,231 rows + 2,291 pre-1950 (commit 84c2c10). Independent rebuild 100 % match; 34/40 mutants killed, real gaps closed; 1 known miss (Ra-228:Ra-226 in US solids, ×4.7). Gas radon 0.75 / 0.73 TBq/GW·a (2010/2020), within ×3 of Johnson, the bottom-up chain and Dixon. |
| 3c Other energy (2.5) | **Signed off by Steve 2026-11-06.** OTHER_SPEC v1.1 (D70, D71). 164,912 rows + 238 pre-1950 (commit 84c2c10). Independent rebuild byte-identical; 29/32 mutants killed, gaps closed; known misses ITA ×3.4, rest-of-world geothermal default ×8, stove Cs-137 ×0.24. World geothermal 83.5 TBq/GW·a. |
| 4 Wind and solar (2.4) | Not started. Needs `data/reference/commodity_factors.csv` first. |
| 2.6 Tier 2 memo | Not started |

Lessons from the pilot, applied to step 3: write the stream spec only after the factor registry exists; tests read factor values from the files rather than hard-coding them, with explicit premise assertions; a second independent benchmark is required from the start; the below_detection flag carries its cause in the notes. Added in step 3: a spec-gap round after the first tests (the test-writers' ambiguity lists became D71), and mutation testing by the verifier.
