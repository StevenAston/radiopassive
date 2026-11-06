# `pipeline/streams/coal.py` — stream script contract (Task 2.2, coal pilot)

Status: v1.3 (2026-11-06; v1.1 resolutions in §11, v1.2 resolutions in §12; §12 overrides §11 and the sections above; v1.3 is the D73 registry change of §12.18, no change to outputs), for the test-writer and the code-writer. Derived from METHODS §3, §5.2, §6.3, §10–11, SCHEMA §3–§4.9, `docs/LIB_SPEC.md` (v1.2), `data/factors/coal.csv` (factors `coal:0001`–`coal:0094`) and `research/coal/factors_notes.md`. Where this file and METHODS disagree, METHODS wins and this file is a bug. Decisions in force: D6 (allocation), D14 (years from 1950), D22 (industry view), D24 (all decays counted), D31 (pre-1950 opening stock), D42, D52, D53 (enrichment rebase), D54 (release cap), D73 (USA ash-route shares).

The script is a pure function of the files under `data/`. It uses only `pipeline.lib` and the standard library plus pandas/numpy if needed. It never reads the network and never decays anything (decay, ingrowth, radon exhalation and seepage belong to the Phase 3 engine).

---

## 1. Interface

```
python -m pipeline.streams.coal [--root PATH] [--write]
```

- Without `--write`, outputs go to a scratch directory and are diffed against the committed files; the exit status is non-zero if they differ.
- With `--write`, the two output files below are overwritten.
- `build(root: Path) -> BuildResult` is the importable entry point. `BuildResult` has three attributes: `rows` (list of master-row dicts for 1950–2025), `rows_pre1950` (list of master-row dicts for 1800–1949) and `log` (list of dicts, §8). `root` is the repository root, so tests can build a miniature tree in `tmp_path` with the same file names and columns.

Outputs:

| File | Content |
|---|---|
| `data/streams/coal.csv` | Master rows, years 1950–2025. Must pass `python -m pipeline.validate --root .` |
| `data/streams_pre1950/coal.csv` | Master columns, years 1800–1949, `quantity = flow` only. **Not part of the master schema** (its year range is 1950–2025); it is the undecayed input to the opening-stock estimate (D31, Option A). The Phase 3 engine decays it. Tests validate it against `schema/master.json` with only the `year` bounds relaxed. |

Both files are written with `pipeline.lib.rows.write_master` (deterministic, sorted by the SCHEMA §3 key).

## 2. Inputs

- **Activity** (`data/activity/coal.csv`, read with `read_table`): `coal_production_t` (by country; includes a country `XWL` world aggregate, which is larger than the sum of the listed countries), `coal_consumption_t` (by country, with `XWL`), `coal_ash_power_t` (`XWL`, from 1900), `coal_fly_ash_t` (`XWL`, from 1900). `coal_burn_power_twh` is used only for the benchmark (§9). Values are `Bounds(value_low, value_central, value_high)`; `source_ids` of the activity rows are collected into the output rows' `source_ids`.
- **Factors** (`data/factors/coal.csv`), looked up with `pipeline.lib.factors.select` and applied with `apply`.
- **Residue types** (`data/reference/residue_types.csv`) are not read by the script; the engine uses them.
- A year with no driver value gives no row for that quantity (for example, ash-based rows before 1900). This is recorded in the log, not an error.

## 3. Row conventions (all rows)

| Column | Value |
|---|---|
| `stream` | `coal` |
| `quantity` | `flow` |
| `unit` | `master_unit(result_unit(driver_unit, factor_unit), "flow")`, which is `Bq/a` for every row here |
| `basis` | `modelled` |
| `allocation_variant` | `default`; `allocation_rule` = `none` (coal is a single product, D6) |
| `embedded_fuel` | `False` |
| `product`, `technology`, `event_id` | empty |
| `factor_ids` | every factor used to compute the row, in the order applied |
| `source_ids` | union of the factors' `source_ids` and the driver rows' `source_ids`, sorted |
| `below_detection` | from the bounds (`nd_floored`), set by `make_row` |
| `notes` | Short text naming the rule (for example `ash route share; fly ash after stack release`) |

Quantities are the **head-nuclide activity** of the group (METHODS §3.2, D24, D42); the engine applies the group multipliers.

Groups: the ash and coal-content groups are `G = {U238+, U234, Th230, Ra226+, Pb210+, Po210, U235+, Th232, Ra228+, Th228+, K40}` (11 groups; `U234` and `Th230` are kept at equilibrium with U-238 so that the Ra-226 stock is supported). Radon groups are `Rn222+` and `Rn220+`.

If a required `select` fails where the spec says a factor must exist, the script raises `LibError` (the registry is wrong). Where this spec says a factor may be absent (the Polish mine-water factors, §4.2), the script catches the `LibError` from `select`, writes no row and records `no_factor` in the log.

## 4. `coal_mining` (substream `all`)

### 4.1 Mine radon

For each producing country $c$ in `coal_production_t` **except `XWL`**, and each year $y$ with a production value:

- Driver $P_{c,y}$ (t). Factor: `select(factors, year=y, region=c, stage="coal_mining", group="Rn222+", route="air_ventilation")`. The exact-region row (China, `coal:0002`, 2000–2025) beats the world default (`coal:0001`).
- Row: country $c$, group `Rn222+`, tier `liberated`, route `air_ventilation`, value `apply(P, "t", factor)`.

**Rest of world.** The residual driver is $P_{\mathrm{XWL},y}-\sum_c P_{c,y}$ using the independent difference in §7. If the residual central is $<0$, use 0 and log `negative_residual` with the magnitude. A positive residual gives rows with country `XWL`, the notes text `rest of world (world aggregate minus listed countries)`, and the XWL factor. A residual of exactly zero gives no row.

Successor and predecessor states (SUN/RUS/UKR/KAZ…, CSK/CZE, YUG/SRB) appear in different years in the data, so listed countries are used as they stand. The script checks nothing about overlaps beyond the negative-residual rule.

### 4.2 Mine-water radium (Poland only)

For country `POL`, years where `select` succeeds (`coal:0003` 1985–2025 for Ra-226, `coal:0004` 1992–2025 for Ra-228):

- Released: group $g\in\{\mathrm{Ra226+},\mathrm{Ra228+}\}$, tier `liberated`, route `water_mine_drainage`, value `apply(P_{POL}, "t", factor)`.
- Retained underground: group $g$, tier `impounded`, residue type `coal_mine_water_sludge`, value
$$A_{\mathrm{retained}}=A_{\mathrm{released}}\times\frac{r}{1-r}$$
where $r$ is `coal:0005` (Ra-226+) or `coal:0006` (Ra-228+). The ratio is applied bound by bound ($r_{\mathrm{low}}/(1-r_{\mathrm{low}})$ and so on), then multiplied with `product`. `factor_ids` lists the release factor and the retention factor.
- No other country and no earlier year has a mine-water factor: no row, logged as `no_factor`.

There are no other `coal_mining` rows. Washery refuse is below the D21 threshold and the overburden memo has no data; both are gaps listed in the factor notes.

## 5. `combustion_power` (substream `power`, country `XWL`)

Let $A_{\mathrm{tot}}$ = `coal_ash_power_t`, $A_{\mathrm{fly}}$ = `coal_fly_ash_t` and $A_{\mathrm{bot}}=A_{\mathrm{tot}}-A_{\mathrm{fly}}$ (independent difference, §7). Both series start in 1900.

For each group $g\in G$ and year $y$:

1. **Ash-borne activity.**
   - $F_g$ = `apply(A_fly, "t", f)` with the fly-ash concentration factor for $g$ (`residue_type = coal_fly_ash`, `coal:0007`, `0009`, …).
   - $B_g$ = `apply(A_bot, "t", f)` with the bottom-ash factor (`residue_type = coal_bottom_ash`).
2. **Stack release** (tier `liberated`, route `air_stack`, no residue type):
$$S_g=\min\!\big(p_y\,e_g\,(F_g+B_g),\;F_g\big)$$
   where $p_y$ is the era base fraction (`select` on stage `combustion_power`, tier `liberated`, route `air_stack`, group empty; `coal:0049`–`0053`) and $e_g$ is the group enrichment (same selection with `group = g`; `coal:0054`–`0064`). The product uses `product` with the two unit-1 factors. **The cap (D54)** is applied bound by bound: `Bounds(min(S.low, F.low), min(S.central, F.central), min(S.high, F.high))`, with the flag following `Bounds` rules. Each bound that the cap changes is logged (`cap_applied`, group, year, bound).
3. **Residues.** The fly-ash residue is $F_g-S_g$ (independent difference, §7). For each residue stream $R\in\{(\texttt{coal\_fly\_ash},\;F_g-S_g),\;(\texttt{coal\_bottom\_ash},\;B_g)\}$ and each tier $t\in\{\texttt{impounded},\texttt{reisolated},\texttt{dispersed}\}$: row with residue type, tier $t$, value `product(R, share_t)`, where `share_t` is the unit-1 route share selected for stage `combustion_power`, tier $t$, group empty, residue empty, route empty, region `XWL`, year $y$ (`coal:0040`–`0048`). The `USA` shares (`coal:0074`–`0094`: `0074`–`0079` retired under D73, `0080`–`0094` live) are inert here because the country is `XWL`; the script must not use them (§12.18).
4. **Radon at the stack.**
   - Group `Rn222+`: tier `liberated`, route `air_stack`, value $=\,$`product((F_{Ra226+}+B_{Ra226+}),\;f_{65})$` (`coal:0065`).
   - Group `Rn220+`: $(F_{Th228+}+B_{Th228+})\times f_{66}$ (`coal:0066`).

Where a share has central 0 and high $>0$ (reisolated), the row is written with `below_detection = true` (the lib's zero-central rule, D52).

## 6. `combustion_nonpower` (substream `non_power`, country `XWL`)

1. **Non-power coal** $C_{\mathrm{np}}=C_{\mathrm{XWL}}-A_{\mathrm{tot}}/0.12$, where $C_{\mathrm{XWL}}$ is `coal_consumption_t` for `XWL` and $A_{\mathrm{tot}}/0.12$ is power-station coal (0.12 exact; the ash-yield uncertainty is already in $A_{\mathrm{tot}}$, which comes from the activity builder). Difference as in §7; central $<0$ becomes 0 and is logged (`negative_nonpower_coal`). Before 1900 there is no ash series, so power coal is taken as 0 and $C_{\mathrm{np}}=C_{\mathrm{XWL}}$ (logged `no_power_ash`).
2. **Coal activity** $N_g$ = `apply(C_np, "t", f)` with the non-power content factors (`coal:0029`–`0039`).
3. **Household share** $h_y$ (`coal:0068`, `0069`, by era; unit 1) and **smoke fraction** $s_y$ (`coal:0070`, `0071`).
   - $H_g=\mathrm{product}(N_g,h_y)$.
   - Smoke: $M_g=\min(s_y\,e_g\,H_g,\;H_g)$ with $e_g$ the `combustion_power` enrichment for $g$ (D53; same bound-wise cap and the same logging as §5). Row: tier `liberated`, route `air_stack`.
   - Household ash: $H_g-M_g$, tier `dispersed`, residue `coal_domestic_ash`.
   - Industrial ash: $N_g-H_g$, tier `impounded`, residue `coal_bottom_ash`. Industrial stack release has no factor (a gap), so all industrial activity is booked to ash.
4. **Radon**: `Rn222+` = $N_{Ra226+}\times f_{65}$ and `Rn220+` = $N_{Th228+}\times f_{66}$, both `liberated`, route `air_stack`.

The ash mass factor `coal:0067` and the measured household-ash anchors `coal:0072`, `0073` are **not** applied to any driver (the latter two are cross-checks).

## 7. Independent difference (private helper, tested)

For $a-b$ with independent errors, central $c=c_a-c_b$; $\mathrm{low}=c-\sqrt{(c_a-l_a)^2+(h_b-c_b)^2}$ and $\mathrm{high}=c+\sqrt{(h_a-c_a)^2+(c_b-l_b)^2}$. Each bound is clipped to $\ge 0$ and ordered ($\mathrm{low}\le c\le\mathrm{high}$); a negative central is set to 0 before the bounds are built and logged. This is conservative for strongly correlated pairs (production and consumption) and is stated as a limitation.

## 8. Log

`BuildResult.log` is a list of dicts with keys `kind`, `year`, `country`, `group` (may be empty) and `detail`. Kinds: `no_factor`, `no_driver`, `negative_residual`, `negative_nonpower_coal`, `no_power_ash`, `cap_applied`. The CLI prints counts by kind and, with `--write`, writes the full log to `research/coal/build_log.csv`. The log is not a master file and is not validated.

## 9. Done conditions and tests

- **(a) Schema.** `data/streams/coal.csv` passes `python -m pipeline.validate --root .`; no row has a tier or route that the stage does not allow (V09/V15 etc.).
- **(b) Candidate nuclides.** Every group in §3 appears in the ash tiers for every year 1950–2025.
- **(c) Conservation.** For each year and group: stack release + fly-ash residue rows = fly-ash-borne activity $F_g$ (bound-wise, to rounding), and the three tier shares of each residue sum back to the residue (central values; within 1e-9 relative).
- **(d) Determinism.** Two builds write byte-identical files; row order is the SCHEMA key order.
- **(e) Benchmarks (D51).** For the years 2010 and 2020 compute, from the output rows, activity per GW·a of coal electricity generated. The denominator is $\mathrm{GW\,a}=E/8.766$, where $E$ is coal electricity in TWh. The activity series holds the thermal energy of coal burned, so $E$ is taken from `data/activity/electricity_generation.csv` (coal, `XWL`) if that file has a coal-generation series; otherwise the test-writer reports the ambiguity and the benchmark uses $E=\eta\,$`coal_burn_power_twh` with $\eta=0.35$ and says so:

| Quantity (from rows) | UNSCEAR 2016 Annex B value (TBq per GW·a) | Source id |
|---|---|---|
| Ra-226 in power-station ash (all residue tiers) | 0.060 | S0001 |
| Pb-210 stack release | 1.4×10⁻³ (older plants), 9.3×10⁻⁵ (modern) | S0001 |
| Ra-226 stack release | 7×10⁻⁴ (older), 4.7×10⁻⁵ (modern) | S0001 |
| Rn-222 released from coal burning | 0.07 | S0001 |
| Mine radon (China, scaled to power coal) | 2.8 | S0001 |

  The central value must lie within a factor of 3 of the quoted value, or, for a two-valued row, within a factor of 3 of the older value or between the two values. The test table cites these numbers from `research/coal/factors_notes.md` (cross-checks) and states the denominator used.
- **(f) Hand-computed cases.** At least ten rows of one year are recomputed independently (own arithmetic from the factor and activity values) and compared with the output, including one cap case, one reisolated zero-central row, one POL mine-water row with retention, one China-versus-world radon row and one rest-of-world residual.
- **(g) Fixture tests.** On a miniature tree in `tmp_path` (a few years, two countries, two groups): the negative-residual rule, the negative non-power coal rule, a missing Polish factor, a missing driver year, and the cap logging.
- **(h) Pre-1950 file.** Rows only for years 1800–1949, `quantity = flow`, no `memo_*` tier; the same code path as post-1950 rows; ash-based rows begin in 1900.

## 10. Known limits carried onto the rows (not hidden)

- Fly/bottom concentration is the same for all groups (no partition data for Pb-210/Po-210).
- The US route shares (`coal:0080`–`0094`, five eras 1966–2025 from the yearly ACAA survey sheets, D73) and the ACAA series are not applied to the world; the XWL shares carry that uncertainty. The US series lies inside every XWL band, so it is consistent with the world rows but cannot narrow them.
- Industrial stack release, FGD residue, coke ovens, gasworks, washery refuse and the overburden memo have no rows.
- The pre-1950 stack fraction (`coal:0049`, centre 0.25) is a judgement with no source.
- The independent difference in §7 overstates the uncertainty of $A_{\mathrm{bot}}$ and $C_{\mathrm{np}}$.
- Seepage and radon exhalation parameters for the coal residue types are set in Phase 3 (seepage research under way).

---

## 11. v1.1 resolutions (2026-10-26, after the spec-blind test review)

These **override** the sections above where they differ.

1. **World country code.** SCHEMA §3 and rule V10 forbid `XWL` as a master-row country; global data without a country breakdown go in `XXX`. Every place above that says an output row has country `XWL` (the rest-of-world mining row, all `combustion_power` rows, all `combustion_nonpower` rows) means country **`XXX`** in the output. The **factor region** and the **activity series country** stay `XWL`; the script looks those up with `XWL` and writes `XXX`. The rest-of-world mining row is distinguished from the other `XXX` rows by its stage, substream and notes text.
2. **Conservation is tested at the central value.** §9(c) says "bound-wise"; read it as "at the central value, to rounding". The low and high bounds of an independent difference are not the differences of the bounds.
3. **Sums.**
   - $F_g+B_g$ (§5 steps 2 and 4, and §6 where two ash terms are added) uses `sum_correlated`: the two terms share the same concentration uncertainty (`coal:0007`/`0008` are fully correlated, see the factor notes).
   - $\sum_c P_{c,y}$ in the rest-of-world residual (§4.1) uses `sum_independent`; the residual is then the independent difference of §7.
4. **Flag on a clipped difference.** When §7 clips a low bound to 0, the result's `nd_floored` is set to `True` (the clipping is a floor rule in the sense of D52). A difference whose low is positive is unflagged.
5. **Benchmark series.** The generating-electricity denominator is the activity series `elec_gen_coal` for `XWL` in `data/activity/electricity_generation.csv` (TWh of electricity); GW·a = TWh / 8.766. The thermal fallback (η = 0.35) is not used. "Mine radon, China scaled to power coal" means $(\text{China mine-radon rows}/\text{China production})\times(A_{\mathrm{tot}}/0.12)$ per GW·a.
6. **Log.** The `cap_applied` log entry's `detail` names the capped bound(s) (`low`, `central` and/or `high`).
7. **Negative residual.** A residual whose central is $<0$ is treated as 0, logged `negative_residual`, and gives no rest-of-world row.
8. **Mini trees in tests** copy the full real factor file and shrink only the activity file; the 11 groups are fixed by §3.

---

## 12. v1.2 resolutions (2026-10-27, after the independent verification and Steve's decisions of 2026-10-26)

These **override** §1–§11 where they differ. Decisions: D58 (this section).

1. **Correlated difference (new private helper `_correlated_difference`).** For $a-b$ where $a$ and $b$ share their driver uncertainty, central $c=c_a-c_b$, $\mathrm{low}=l_a-l_b$ and $\mathrm{high}=h_a-h_b$ (the two quantities move together). The three values are then ordered ($\mathrm{low}\le c\le\mathrm{high}$), each bound is clipped to $\ge 0$, and a negative central is set to 0 (logged as before). A clipped low sets `nd_floored` (§11.4). It is used for:
   - $A_{\mathrm{bot}}=A_{\mathrm{tot}}-A_{\mathrm{fly}}$ (§5): bottom ash is a correlated difference of two series from one activity builder;
   - the fly-ash residue $F_g-S_g$ (§5 step 3), since $S_g$ is a fraction of $F_g+B_g$.

   The **independent** difference of §7 is kept for the rest-of-world mining residual (§4.1) and for $C_{\mathrm{np}}=C_{\mathrm{XWL}}-A_{\mathrm{tot}}/0.12$ (§6). $C_{\mathrm{np}}$ keeps the independent form because $A_{\mathrm{tot}}/0.12$ and $C_{\mathrm{XWL}}$ come from different builders; the limitation stays in §10.
2. **Predecessor and successor states.** Where `coal_production_t` has a `CSK` value for a year, any `CZE` value for that year is **dropped**, for the mining rows and for the sum in the rest-of-world residual (CSK is the larger, whole-country series; the activity data overlap in 1981–1992 by about 66–93 Mt per year, a double count if both are used). Each dropped value is logged (`predecessor_dropped`, country `CZE`, detail names `CSK`). There is no overlap for `SUN` with `RUS`/`UKR`/`KAZ` or for `YUG` with `SRB`; no rule is applied. `SUN` has no 1980 production row; the rest-of-world residual (world aggregate minus listed countries) absorbs 1980 automatically, which is the intended behaviour, and the rest-of-world row's notes name it only as the residual.
3. **Flag cause in notes.** Every output row with `below_detection = true` ends its `notes` with `; below_detection cause: <causes>` where `<causes>` is a `+`-joined subset of, in this fixed order: `zero_central_factor` (an input factor has central 0, for example the reisolated share), `clipped_difference` (a §7/§12.1 low was clipped to 0), `floor_dominance` (the lib's zero-low floor rule fired in a product with no other cause), `inherited_flag` (an input row was flagged and none of the above applies). The script tracks the causes of its own inputs and carries them through products and sums; it does not parse lib log text. Rows with `below_detection = false` carry no cause text.
4. **Driver basis in notes.** If any activity driver row used has basis `interpolated` or `extrapolated` (pre-1900 decadal series interpolated annually; 2024 consumption carried to 2025), the row's `notes` gain `; driver basis: interpolated` (or `extrapolated`, or both joined by `+`). The row's own `basis` stays `modelled`.
5. **Library warnings and the log.** `build()` emits nothing on stderr. The lib's floor-dominance warnings are captured, counted, and recorded as a single log entry per build (`kind = lib_warning`, year and country empty, `detail` = the count and the message type). Aggregation of repetitive pre-1900 entries: the kinds `no_driver` and `no_power_ash` are written as **one entry per contiguous year run per (kind, stage/series, country, group)**, with `year` = the first year and `detail` = `first-last (n years)`; they are not written once per year. All other kinds keep one entry per event. The kind list in §8 gains `predecessor_dropped` and `lib_warning`.
6. **Missing versus ambiguous factors.** The script treats a failed `select` as "no factor" only when the `LibError` message starts with `no factor row`; it then writes no row and logs `no_factor`. Any other `LibError` (including `ambiguous factor rows`) propagates. Exception: none.
7. **Duplicate activity rows.** If two activity rows share (`quantity`/series, country, year) the script raises `LibError` naming the key. Nothing is silently first-wins.
8. **CLI diff covers the log.** Without `--write` the CLI compares the two master outputs **and** `research/coal/build_log.csv`; the exit status is non-zero if any differs. With `--write` all three are written.
9. **2025 non-power rows.** 2025 consumption now exists for 33 countries (`extrapolated`, widened bounds), including `XWL`; non-power rows for 2025 are therefore written, and the old expectation that 2025 logs `no_driver` for `coal_consumption_t` no longer holds. Pre-1900 `XWL` series are annual (`interpolated`), so mining and non-power rows exist for 1801–1899; ash-based rows still begin in 1900.
10. **Benchmarks (§9(e)).** The Annex B table is kept as the first estimate. A second, **independent** estimate is added from `research/coal/benchmarks.md` §4. Each stream value must lie within a factor of 3 of the independent value (or lie between the two where two are given), for 2010 and 2020:

| Quantity (TBq per GW·a) | Independent value | Source id | Note |
|---|---|---|---|
| Ra-226 in ash | 0.0528 and 0.149 | S0205, S0972 | UK 1998; India 1976–83; must be within ×3 of at least one of them |
| Pb-210 stack | 5.9×10⁻⁴ and 4.3×10⁻⁴ | S0974, S0205 | India (modelled); UK 1998 |
| Ra-226 stack | 2.1×10⁻⁴ | S0205 | UK 1998 (S0204 gives 2.3×10⁻⁴, same family) |
| Ra-226 stack, era check | 4.5×10⁻³ | S0972 | compare with the stream's 1970–89 factors applied to 2010 ash activity |
| Rn-222 from burning | 0.0495 and 0.071 | S0205, S0204 | UK 1998; NL |
| Ash per GW·a (Mt) | 0.808 | S0977 | world 2010 combustion products; includes FGD gypsum and non-power ash, so an upper bound |
| Escaping ash fraction | 0.41 % | S0205 | UK 1998 |

   - **Mine radon** has no independent estimate; it is excluded from the independent test and documented as unsupported (§10).
   - Independence: S0205 (UK NRPB R327) and S0204 (Leenhouts via UNSCEAR 2000) are independent of Annex B 2016 only, not of the UNSCEAR family. S0972, S0974 and S0977 are independent. The TRS 419 coal composition table and anything quoted in S0001 are not used as independent estimates.
   - **Known miss, documented not hidden:** Po-210 stack release is above the UK figure (stream 2.4×10⁻³ against UK 4.3×10⁻⁴) but within ×3 of the Dutch value; the TRS 419 single-plant escaping fraction (0.0044–0.084 %) is at least 3.7× below the stream's 0.31 %. Neither is a test; both go in §10.
11. **Fleet-mix inconsistency noted.** The stream's 2010 Pb-210 stack value implies about 74 % weighting toward the older-plant UNSCEAR value, the Ra-226 value about 40 %. The era fractions are not a single fleet mix across nuclides (§10).
12. **Pa-231 and Ac-227+.** These groups are not carried (factor-notes gap G15). They sit below `U235+` in the chain; U-235 is about 4.6 % of U-238 head activity before multipliers, and Pa-231 ($T_{1/2}=32\,760$ a) builds up only slowly, so ingrowth over 1950–2025 is small relative to the stated uncertainty. They are omitted on that justification, not by oversight.
13. **Hard era steps are real.** The era base fractions $p_y$ (`coal:0049`–`0053`, 1800–1949, 1950–69, 1970–89, 1990–2009, 2010–2025) and the household share and smoke fraction (`coal:0068`–`0071`, step at 1950) change in steps. The output series therefore has discontinuities at 1950, 1970, 1990 and 2010 (and at 1950 for the household terms). They are **not smoothed** (Steve's decision, 2026-10-26); the discontinuity is in the source data and is documented in the factor notes.
14. **Tests.** The test that expected a 2025 `no_driver` entry for `coal_consumption_t` is replaced. New tests cover the survivors of the independent verification's mutation run: the clipped-difference flag, the rest-of-world `sum_independent` convention, the $F+B$ `sum_correlated` convention, era-edge years (1949/1950, 1969/1970, 1989/1990, 2009/2010), the non-power cap, and `factor_ids` on the radon rows.

### §10 additions (limits)

- Mine radon has no independent estimate (§12.10).
- The era fractions imply different fleet mixes for Pb-210 and Ra-226 (§12.11).
- Hard era steps (§12.13).
- Pa-231 and Ac-227+ are not carried (§12.12).
- The smoke fraction assumes coal-average activity; the fly-ash $\varepsilon$ low of 0.005 is untraced; K-40 has no coal-lower bound; the rebased U and Th enrichment centres are below 1, probably an artefact of the rebase.

### §12.15 Clarifications after the v1.2 test review (2026-10-27)

- **Ordering in §12.1** means clamping around the central: $\mathrm{low}=\min(l_a-l_b,\,c)$, $\mathrm{high}=\max(h_a-h_b,\,c)$, then clip to $\ge 0$. It does not mean sorting the three values.
- **Helper signature:** `_correlated_difference(a: Bounds, b: Bounds) -> Bounds`.
- **Household and industrial ash** ($H_g-M_g$, $N_g-H_g$, §6) keep the §7 independent difference in v1.2. This overstates their uncertainty (stated limitation, §10) and is to be revisited.
- **Notes suffix order:** the rule text first, then `; driver basis: …` if present, then `; below_detection cause: …` last.
- **Aggregated log entries** (§12.5) carry the output-row country convention (`XXX` for world series, otherwise the country code).

### §12.16 Exact-zero cause (Steve, 2026-10-27)

- A correlated difference (§12.1) whose result is exactly $(0,0,0)$ **without any clipping** (for example the fly-ash residue $F_g-S_g$ when the cap makes $S_g=F_g$ at all three bounds) is a true zero. It stays flagged (`below_detection = true`, D52 zero-central rule), but its cause is `exact_zero`, **not** `clipped_difference`.
- The fixed cause order becomes: `zero_central_factor`, `exact_zero`, `clipped_difference`, `floor_dominance`, `inherited_flag`. A reisolated tier row of such a residue therefore reads `zero_central_factor+exact_zero`.
- `clipped_difference` is used only when a raw low (or central) was actually below 0 and was clipped.
- Precisely: `exact_zero` applies when the raw central and raw high differences are exactly 0 and the raw low is $\ge 0$. A positive raw low is clamped down to the central (§12.15), which is not clipping, so the result is still a true zero.

### §12.17 After the D59 factor revision (2026-10-27)

- **Benchmark rule (§12.10), stated explicitly:** where two independent values are given, the stream central must lie within a factor of 3 of **at least one** of them (this is what the tests implement). "Lie between the two" is an alternative pass, not a requirement.
- **Margins after D59/D59a (2010; 2020 within 2 %):** Ra-226 in ash 0.129 TBq/GW·a (×2.4 UK, ×0.86 India); Pb-210 stack 1.52×10⁻³ (×2.6 India, **×3.5 UK, outside on that value**); Ra-226 stack 4.8×10⁻⁴ (×2.3 UK); Rn-222 from burning 0.110 (×2.2 UK, ×1.5 NL); Po-210 stack 1.80×10⁻³ (×4.2 UK, known miss; ×1.06 NL). Values rose about 1.4× with the coal U-series centre 20 → 28 Bq/kg (D59, D59a). The stream now sits systematically 2–3.5× above the UK 1998 figures; UK coal and UK particulate control are both better than the world mean, so this is expected in direction, but it is recorded as a limit.
- **Superseded text:** §12.10's "Po-210 stream 2.4×10⁻³" is now 1.80×10⁻³. In §10 additions, the fly-ash ε low (0.005) is now traced (Kovler, S0244; D59), K-40 has a coal lower bound (31 Bq/kg; D59), and the U/Th enrichment centres below 1 are resolved (D59). The 2010+ era centre (0.31 %) is unchanged; its low is now 0.02 %.
- **Open flags (not changed):** ash yield 15 % (Ketris & Yudovich) vs 12 % used (a US check from the ACAA series, §12.18, points the other way for the US); coal:0003 high possibly 2–3× high (S0222 check); China K-40 104 (S0006) vs 49 (Dai); Ra-226 retained sludge is 7.3× the release at the 0.88 high, so it is sensitive to that bound.

### §12.18 USA ash-route shares rebuilt from the ACAA series (D73, Steve, 2026-11-06)

- **Registry only; outputs unchanged.** Option A of `research/coal/acaa_notes.md` §6: the two-era USA rows `coal:0074`–`0079` are **retired** (kept in the registry with values unchanged and marked `RETIRED (D73)`, because documents cite them by id) and replaced by fifteen rows `coal:0080`–`0094`: five eras (1966–1989, 1990–1999, 2000–2009, 2010–2015, 2016–2025) × three tiers (impounded, reisolated, dispersed), region `USA`, built from the yearly ACAA survey sheets (S0255–S0259) with the tier mapping of `acaa_notes.md` §4. The world rows `coal:0040`–`0048` keep their values and `source_ids` (notes only).
- **Why a retired row is never selected.** Step 3 of §5 calls `select` with region `XWL`; `select` (LIB §3) keeps only rows whose region is the requested one or `XWL`, so no `USA` row, retired or live, is a candidate, and the windows and match keys of the retired rows need no change. If a `USA` branch is ever added (option C, not decided), the retired rows overlap the live ones in 1991–2025, so `select` would raise `ambiguous` rather than pick one; that branch must first exclude or remove `coal:0074`–`0079`.
- **Side finding, open (G18, not changed).** ACAA fly + bottom + slag production divided by the model's US coal consumption is 7–9 % (1970–2020), and 8.4–9.6 % of the utility coal burn printed on the 1987–93 sheets: below the 12 % yield of `coal_ash_power_t`. One country with low-ash Powder River coal; it does not transfer to the world and changes nothing here.
- **Tests.** The guards of §9 that no output row cites a USA share cover `coal:0074`–`0094`; the edit-invariance test edits the live rows `coal:0080`–`0094`.
