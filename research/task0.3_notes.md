# Task 0.3 — Nuclide reference table: method, provenance, judgement calls, checks

Date: 2026-10-20. Outputs: `data/reference/nuclides.csv` (107 rows: the 103 required plus Rh-103m, Te-125m, Rb-88, Cs-138 added in the follow-up, §11), `data/reference/groups.csv` (69 rows), `data/reference/sources_nuclides.csv` (S9001–S9006). Governing text: METHODS §3, §4, §7; SCHEMA §4.1–4.3.

---

## 1. Method and data provenance

| Item | Source | Route |
|---|---|---|
| Half-life, decay mode, daughters, branching | ICRP Publication 107 (S9001), `ICRP-07.NDX` | Downloaded directly from icrp.org (`https://www.icrp.org/docs/ICRP-07.zip`, contains only the corrected 2021 `.NDX`). Parsed from the fixed-width file and compared field-by-field with the RadData copy: **identical for all 107 nuclides** (S9002). |
| Emission energies and yields by radiation type | ICRP-07.RAD (S9001) | The `.RAD` file is not on icrp.org's public pages (the publication page links only the corrigenda zip and the SAGE supplement). Obtained through the CRAN package RadData 1.0.2 (S9003), which holds a tidy conversion of the ICRP files. |
| Cross-check of half-lives | `radioactivedecay` 0.6.1 (S9004) | Carries ICRP-107 half-lives and branching but **no emission energies**. All 103 half-lives agree with S9002 to ≤ 2.1 × 10⁻⁵ (the residual is the year definition). Not an independent check. |
| Independent check | IAEA LiveChart API (S9005, ENSDF/NUBASE2020) and DDEP/LNHB (S9006) | API fetched with `curl` (works from the shell); DDEP PDFs downloaded and read directly (§11.3). |

**Energy categories** (all from ICRP-07.RAD; mean energy per decay = Σ yield × energy over the lines):

| Column | ICRP radiation codes summed |
|---|---|
| `e_alpha_mev` | `A` |
| `e_recoil_mev` | `AR` (alpha recoil) **plus** spontaneous-fission `FF` (fragment kinetic energy) and `N` (neutron kinetic energy), for the 8 nuclides that have an SF branch — see J4 |
| `e_beta_mev` | `B-`, `B+`, `DB` (delayed beta from SF). ICRP lists the **mean** electron/positron energy per branch, so neutrinos are already excluded. |
| `e_photon_mev` | `G`, `X`, `AQ` (annihilation photons), `PG`, `DG` (SF prompt/delayed gammas) |
| `e_electron_mev` | `IE` (internal conversion), `AE` (Auger) |
| `e_total_mev` | Sum of the five (written to 10 significant figures; the sum of the five stored values equals it to < 10⁻⁸) |

**Internal consistency check of the RAD sums against ICRP's own NDX columns** (the NDX holds aggregate alpha, electron and photon energy per decay): alpha + recoil from `.RAD` agrees with NDX `E_alpha` to ≤ 0.10% for all 38 alpha emitters (so the NDX alpha column *includes* recoil, and my `A` and `AR` split is consistent with it); electron and photon sums agree to within the 5-decimal rounding of the NDX columns (worst 0.8%, on values of ~0.001 MeV).

**Half-life conversion.** `half_life_value`/`half_life_unit` are ICRP's own (ICRP `m` → `min`, `y` → `a`; no ms/µs units occur in this set). `half_life_a` converts with the Julian year (365.25 d); `lambda_per_a` = ln 2 / `half_life_a`. ICRP's own decay constants use a slightly shorter year (ratio 0.9999826), so our λ differs from the ICRP λ by 1.7 × 10⁻⁵ — immaterial.

**Rounding.** Energies to 7 significant figures, `half_life_a` and `lambda_per_a` to 8.

Throwaway scripts (parse, build, validate, cross-check) are in `/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task03/`; none is in `outputs/`.

---

## 2. Judgement calls

| # | Call | Reason / effect |
|---|---|---|
| J1 | **Minor branches are members with exact weights.** `U238+` includes Pa-234 (weight 0.0016); `Ra226+` and `Rn222+` include At-218 (0.0002) and Tl-210 (0.00021); `Ac227+` includes Po-211 (0.00276). | These nuclides are on the required list, and D24 says all decays are counted. Because the branches rejoin the main line, only `U238+` moves off its integer: **3.0016**. All others stay at the integer to < 10⁻⁶. |
| J2 | **Primordial groups use secular-equilibrium weights** (pure branching propagation). **Artificial "+" groups use the transient factor** $\lambda_d/(\lambda_d-\lambda_h)$ on each daughter, as instructed. | A fresh fission product has no parent supply, so transient equilibrium is the right limit. Applying the factor to primordial groups would change them by up to +0.49% (see §4), against METHODS' integers. |
| J3 | **Ce144+: the Pr-144m branch is folded into Pr-144.** Pr-144 weight = 0.99023 + 0.0097699 × 0.9993 = 0.99999 (× transient factor 1.0000352). | Ce-144 → Pr-144m (0.977%, 7.2 min IT) → Pr-144. Leaving it out gives m = 1.990 instead of 2.000. Pr-144m's own 0.0098 decays (0.04% of energy) are omitted. |
| J4 | **SF fragments and neutrons go into `e_recoil_mev`** (U-238, Pu-238/240/242, Cm-242/244/245/246). No column exists for them. | Only matters for Cm-246 (FF 0.0479 MeV = 0.9% of total, neutrons 0.0017 MeV = 0.03%) and Pu-242 (0.02%). Flagged in each row's `notes`. If you would rather keep `e_recoil_mev` as pure alpha recoil, subtract the amounts in those notes. |
| J5 | **`daughters` follows ICRP, not the table.** Entries may be stable nuclides (Pb-206, Ca-40…), radioactive nuclides outside the required list (§6), or the token `SF` for the spontaneous-fission branch. | Branching then sums to 1 within 3 × 10⁻⁶ everywhere (worst: Cm-246, 1.000003). Dropping `SF` would put Cm-246 at 0.99974. |
| J6 | **`parent_group` is filled only for the three natural chains**, as SCHEMA says (empty for artificial groups). Artificial links (Pu-241 → Am-241 → Np-237 → Pa-233 → U-233; Mo-99 → Tc-99; Cm → Pu; etc.) can be built from `nuclides.csv` `daughters`. | If the engine needs group-level actinide ingrowth, populate `parent_group` for those; I did not change the schema's rule. |
| J7 | **`parent_branching` = decay flux from the parent group's members into the child head, per parent-head decay** (so it conserves atoms; it is *not* multiplied by the transient factor). | All natural-chain links come out at 1 (0.9999998 for Ra226+ → Pb210+ because the Rn-218 route is dropped; printed as 1). |
| J8 | **Released-gas groups** (`Rn222+`, `Rn220+`, and since the follow-up `Kr88+`, `Xe138+`) have `role = released_gas` and `multiplier_scope = flow_only` (new columns, §11). `Rn222+`/`Rn220+` have `parent_group` = `Ra226+` / `Th228+`, branching 1; they are excluded from the series totals. | The engine must use ε (METHODS §5.2) to choose between the tail inside `Ra226+` and `Rn222+`. |
| J9 | **Cs137+ uses ICRP-107's Ba-137m branching** (0.94399), giving m = 1.94399. | See §3. METHODS quoted ~1.946 from DDEP. |
| J10 | **Pa-234m keeps ICRP's name**; Pa-234 is the 6.7 h ground state. | Matches the task list. |

---

## 3. Group-rule outcomes (daughter half-life < 1/10 of head's)

| Candidate | Daughter | T½(d)/T½(h) | Outcome | m | Notes |
|---|---|---|---|---|---|
| `Ru103+` | Rh-103m | 0.00099 | **Forms** (follow-up). | 1.988531 | Rh-103m weight 0.98755 × 1.000993 |
| `Sb125+` | Te-125m | 0.0570 | **Forms** (follow-up). | 1.245337 | Te-125m weight 0.23136 × 1.0604 = 0.24534 |
| `Ba140+` | La-140 | 0.1316 | **Fails.** Separate groups `Ba140`, `La140`. | — | 1.678 d vs 12.752 d |
| `Zr95+` | Nb-95 | 0.5465 | **Fails.** Separate groups `Zr95`, `Nb95`. | — | 35.0 d vs 64.0 d |
| `Te132+` | I-132 | 0.0298 | **Forms.** | 2.030764 | I-132 weight 1.030764 (= 1/(1 − 0.0298)) |
| `Mo99+` | Tc-99m | 0.0912 | **Forms (marginally).** | 1.965359 | Tc-99m weight = 0.8773 × 1.10039 = 0.96536. Mo-99 also feeds Tc-99 directly (12.27%); Tc-99 is its own group. |
| `Np237+` | Pa-233 | 3.4 × 10⁻⁸ | **Forms.** | 2.000000 | |

Pre-defined artificial groups, now with the transient factor: `Sr90+` 2.000254, `Cs137+` **1.943990**, `Ru106+` 2.000001, `Ce144+` 2.000035.

**Cs137+.** METHODS gave ~1.946 (DDEP: 94.57% to Ba-137m, which I confirmed on the DDEP table, S9006). ICRP-107 gives 94.399% → 1.94399; ENSDF (IAEA, 2006 evaluation) gives 94.7% → 1.947. The spread is 0.17%; I used ICRP for consistency with every other row. The METHODS text should say 1.944.

---

## 4. Multipliers and series totals (all verified; exact value = sum of `member_weights`)

| Group | METHODS | Computed | Group | METHODS | Computed |
|---|---|---|---|---|---|
| `U238+` | 3 | **3.0016** | `Th228+` | 7 | 7 |
| `Ra226+` | 6 | 6 (6 − 2 × 10⁻⁷) | `Rn222+` | 5 | 5 |
| `Pb210+` | 2 | 2 | `Rn220+` | 5 | 5 |
| `U235+` | 2 | 2 | `Cs137+` | ~1.946 | 1.94399 |
| `Ac227+` | 8 | 8 | `Ra228+` | 2 | 2 |

Series totals: U-238 **14.0016** (nominal 14), U-235 **11**, Th-232 **10**. The 0.0016 is the Pa-234m IT branch. If an integer 14 is wanted, drop Pa-234 from `U238+` (energy change 0.0016 × 1.8755 = 0.003 MeV, 0.06%).

Energies per head decay (MeV): `U238+` 5.17825; `U234` 4.85871; `Th230` 4.77018; `Ra226+` 27.1010; `Pb210+` 0.434643; `Po210` 5.40750; `U235+` 4.87822; `Pa231` 5.15799; `Ac227+` 34.4316; `Th232` 4.08291; `Ra228+` 1.33286; `Th228+` 34.9304; `Rn222+` 22.2294; `Rn220+` 23.6208; `K40` 0.678471; `Cs137+` 0.812968. All 69 values are in `groups.csv`.

**Hand-calculation values for Task 3.3** (1 MeV = 1.602 176 634 × 10⁻¹³ J): H-3 0.00567977 MeV → 9.100 × 10⁻¹⁶ W Bq⁻¹; `Cs137+` 0.812968 MeV → 1.3025 × 10⁻¹³ W Bq⁻¹ (per Bq of Cs-137); Po-210 5.407497 MeV → 8.664 × 10⁻¹³ W Bq⁻¹.

**Sensitivity to the equilibrium convention** (what the transient factor would add to the primordial groups, for a freshly separated head with no supply): `Th228+` +0.48%, `Rn222+` +0.49%, `Ac227+` +0.31%, `Pb210+` +0.03%, `Ra228+` +0.006%, `Ra226+` +0.001%, `U238+`/`U235+` 0. Not applied (J2).

**Rule check for primordial groups.** Every member's half-life is < 1/10 of its head's in all primordial "+" groups, including `Rn222+` (longest progeny 26.8 min vs 3.82 d). **`Rn220+` fails the rule**: Pb-212 (10.6 h) and Bi-212 (1.0 h) outlive Rn-220 (55.6 s). Its 5 is therefore a *flow-basis count* (eventual decays per Rn-220 atom released), not a standing-activity ratio. METHODS §4.1 already calls this a counting convention for Rn-222+; the same wording is needed, with this stronger caveat, for `Rn220+`. The engine should not multiply a stock of Rn-220 by 5.

**Natural uranium ratio** (METHODS §4.1): 0.7204/99.2742 × (4.468 × 10⁹ / 7.04 × 10⁸) = **0.04606**, so the 0.0461 in METHODS is confirmed (ICRP half-lives).

**Bi-212 branching** 64.06% Po-212 / 35.94% Tl-208 — confirmed in ICRP-107 (0.6406 / 0.3594).

---

## 5. 10-value independent spot-check

**Selection.** Pool = every (nuclide, field) pair with field ∈ {`half_life_a`, `e_alpha_mev`, `e_beta_mev`, `e_photon_mev`, `e_electron_mev`} and, for energies, value ≥ 10⁻³ MeV (below that a 1% test measures line-list completeness, not data quality). `e_recoil_mev` and `e_total_mev` are excluded because they have no independent source (recoil follows from the alpha energy; the total is a sum). Pool size 358, ordered by the task's nuclide order then field order. Draw: `random.Random(20261020).sample(pool, 10)`, made once and not repeated.

**Independent source.** IAEA LiveChart API (ENSDF/NUBASE2020, extracted 2026-10-20). Half-lives are compared in the source's own unit (years, hours, days), because the API's year is 365.2422 d. Energies: Σ (energy × intensity) over the API's radiation lines for the parent level (α; β⁻ mean energies; γ + X lines, with the 2 × 511 keV annihilation term for β⁺; Auger + conversion electrons). Caveat: ICRP-107 was built on ENSDF-lineage evaluations, so agreement is not proof of independence for the γ/α/half-life data; the β and Auger/conversion-electron values are computed by ICRP itself, so those are the more independent tests.

| # | Nuclide | Quantity | ICRP-107 (S9001) | Second source value | Second source | Diff | Result |
|---|---|---|---|---|---|---|---|
| 1 | Sb-125 | `e_photon_mev` | 0.4373133 | 0.436051 | IAEA/ENSDF (Katakura, cut-off 1-Jan-2010) | −0.29% | pass |
| 2 | Am-241 | half-life | 432.2 a | 432.6 a | IAEA/ENSDF (Nesaraja, cut-off 30-Sep-2015) | +0.09% | pass |
| 3 | Kr-85m | `e_beta_mev` | 0.228102 | 0.228672 | IAEA/ENSDF (Singh & Chen, 31-Dec-2013) | +0.25% | pass |
| 4 | Th-232 | `e_alpha_mev` | 3.99861 | 3.99679 | IAEA/ENSDF (Abusaleem, 31-Dec-2012) | −0.05% | pass |
| 5 | I-129 | `e_beta_mev` | 0.0502689 | 0.04003 (DDEP: 0.037) | IAEA/ENSDF (Timar et al., 31-May-2014); DDEP/LNHB | **−20.4%** (DDEP −26%) | **FAIL** |
| 6 | Po-218 | `e_alpha_mev` | 6.0012 | 6.00134 | IAEA/ENSDF (Zhu & McCutchan, 1-May-2021) | +0.002% | pass |
| 7 | I-133 | half-life | 20.8 h | 20.83 h | IAEA/ENSDF (cut-off 31-Oct-2010) | +0.14% | pass |
| 8 | Bi-214 | `e_beta_mev` | 0.6412019 | 0.641135 | IAEA/ENSDF (Zhu & McCutchan, 1-May-2021) | −0.01% | pass |
| 9 | Th-227 | half-life | 18.68 d | 18.697 d | IAEA/ENSDF (ICTP-2014, 15-Jan-2016) | +0.09% | pass |
| 10 | U-234 | half-life | 245 500 a | 245 500 a | IAEA/ENSDF (Ota, 1-Dec-2023) | 0.00% | pass |

**9 of 10 pass; I-129 beta fails, and the failure is real, not a transcription error.** Investigation:
- ICRP's I-129 beta line is a single branch at 0.050269 MeV (yield 1.0). The mean of ICRP's own BET spectrum (`ICRP-07.BET`, 89 points, E_max 0.1544 MeV) is 0.050228 MeV, so ICRP is internally consistent.
- ENSDF gives 0.04003 MeV and DDEP 37(1) keV for the 99.5% branch (E_max 151.2 keV; "2nd forbidden"). Both apply the forbidden spectrum shape, which lowers the mean; ICRP's spectrum is closer to allowed-shape (mean ≈ 0.33 E_max).
- The same pattern shows in other forbidden emitters (§7): Tc-99 −16%, Cs-135 −15%, Te-132 −11%. I have **not** verified the cause for those three.
- **Decision:** keep the ICRP value (the task names ICRP-107 as authoritative and the energy is consistent with ICRP's own spectrum), note the discrepancy in the row, and flag it here. If the project would rather use the evaluated forbidden-shape mean for I-129, Tc-99 and Cs-135, the swap is simple: the effect on radioactive power is −20%, −16% and −15% for those nuclides alone. These are tiny contributors to total power, but I-129 and Tc-99 are long-lived and appear in the effluent list.

---

## 6. Wider cross-check against IAEA (all 103 nuclides, same method)

Counted only where the ICRP value ≥ 10⁻³ MeV (half-life: all 103):

| Quantity | Within 1% | Outside 1% | Median |difference| |
|---|---|---|---|
| Half-life | 100 of 103 | 2 (Po-212 −1.6%, Cm-246 −1.1%); At-218 −14.7% (ICRP 1.5 s vs ENSDF 1.28 s) falls out of the automated count because my level-matching rule (±10%) rejects it | 0.01% |
| α energy | 35 of 39 | U-235 +1.2%, Np-237 +1.9%, Ac-227 +3.3%; At-218 (no ENSDF lines matched, same cause) | 0.04% |
| β energy | 45 of 63 | 18, listed below | 0.25% |
| γ + X energy | 36 of 81 | 45 | 1.8% |
| Conversion + Auger energy | 11 of 72 | 61 | 9% |

β differences > 1% (IAEA/ICRP − 1): I-129 −20.4%, Tc-99 −16.4%, Cs-135 −15.3%, Te-132 −10.8%, Ac-228 −6.9%, Th-234 +5.9%, Pa-233 +4.4%, K-40 −4.1%, Ba-140 −3.2%, Np-239 −3.0%, Pb-214 +3.0%, Tl-210 +2.7%, Th-231 −1.6%, I-133 −1.2%, plus Xe-138 +24.8% and Pa-234 +46.5%, which were later traced to unnormalised ENSDF intensities (§11.2; +10.9% and +9.8% after normalising).

**Interpretation of the γ/X and electron columns.** Large differences here are expected and I do not treat them as ICRP errors: ENSDF-derived Auger and X-ray line lists are computed by a different procedure (and may overlap or double count; e.g. Fe-55 totals 0.0094 MeV from the API against ICRP's 0.0058 MeV, where a hand estimate from the K-capture Auger and Mn-Kα yields gives ~0.006 MeV, supporting ICRP), and ENSDF decay datasets attribute daughter-isomer γ's to the parent (Cs-137 shows 0.57 MeV of photons against ICRP's 1.7 × 10⁻⁶ MeV, because ICRP assigns the 661.7 keV γ to Ba-137m, and so does this table). Photon and electron energies therefore carry roughly ±10% (electrons ±10–20%) systematic uncertainty between evaluation systems, but they are small parts of most totals. On whole-nuclide totals (ICRP total vs ICRP α + recoil + IAEA β + γ/X + e): 77/103 within 1%, 86/103 within 5%; the outliers are dominated by the Cs-137/Ba-137m convention, Auger-rich EC emitters (Fe-55, Co-58) and the forbidden-β cases above.

Two bugs in my first automated pass (isomer selection for Xe-133m and Cs-135 picking the wrong level) were fixed by requiring the level's half-life to match within 10%; the results above are from the corrected run.

---

## 7. Discrepancies between sources (summary)

| Item | ICRP-107 (used) | Other | Note |
|---|---|---|---|
| Cs-137 branching to Ba-137m | 94.399% | DDEP 94.57%; ENSDF 94.7% | Cs137+ m = 1.94399 / 1.9457 / 1.947 |
| Cs-137 half-life | 30.1671 a | ENSDF 30.08 a; DDEP 30.018 a | within 0.5% |
| C-14 half-life | 5700 a | IAEA/ENSDF 5700 a; METHODS text 5730 a | METHODS should quote 5700 (or note the older 5730) |
| I-129 mean β | 0.0503 MeV | ENSDF 0.0400; DDEP 0.037 | fails 1% check (§5) |
| Tc-99, Cs-135, Te-132 mean β | 0.1013, 0.0894, 0.0670 | ENSDF 0.0846, 0.0757, 0.0598 | forbidden-shape suspected, unverified |
| At-218 half-life | 1.5 s | ENSDF/NUBASE2020 1.28 s | weight 0.0002, negligible |
| Po-212, Cm-246 half-life | 0.299 µs; 4760 a | 0.2943 µs; 4706 a | −1.6%, −1.1% |
| Ac-227, U-235, Np-237 α energy | — | +3.3%, +1.2%, +1.9% (IAEA higher) | not investigated |
| Fr-223 branching | sums to 1.00006 (ICRP lists At-219 6 × 10⁻⁵ on top of Ra-223 = 1) | — | ICRP's own rounding; kept as published (within 1 × 10⁻⁴ tolerance) |

---

## 8. Known omissions: radioactive daughters not in the table

The required list stops at the nuclides below, so their radiations are **not** in any group. Per decay of the parent, the energy omitted and its size relative to the parent's `e_total_mev`:

| Parent → daughter | Branching | Daughter T½ | Omitted energy (MeV per parent decay) | Relative |
|---|---|---|---|---|
| Ru-103 → Rh-103m | 0.98755 | 56.1 min | 0.0389 | **+6.9%** |
| Sb-125 → Te-125m | 0.23136 | 57.4 d | 0.0336 | **+6.2%** |
| Kr-88 → Rb-88 | 1 | 17.8 min | 2.709 | +117% |
| Xe-138 → Cs-138 | 1 | 33.4 min | 3.607 | +202% |
| Kr-87 → Rb-87 | 1 | 4.9 × 10¹⁰ a | negligible rate | — |
| Zr-95 → Nb-95m | 0.0108 | 3.61 d | 0.0027 | +0.32% |
| Ce-144 → Pr-144m | 0.00977 | 7.2 min | 0.0006 | +0.04% (the Pr-144 route is folded in, J3) |
| At-218 → Rn-218; Fr-223 → At-219; Pu-241 → U-237; Pu-239 → U-235m | ≤ 0.001 | — | < 0.01 | ≤ 0.1% |
| U-233 → Th-229 | 1 | 7340 a | 5.18 | the tail of the U-233 chain |
| Pr-144 → Nd-144; Pm-147 → Sm-147 | 1 | 10¹⁵ a; 10¹¹ a | negligible rate | — |

**Update (§11):** Rh-103m, Te-125m, Rb-88 and Cs-138 have now been added and are counted in `Ru103+`, `Sb125+`, `Kr88+` and `Xe138+`. The Ru-103, Sb-125, Kr-88 and Xe-138 rows still show only their own emissions, as ICRP defines them. The remaining rows above are still omitted (Th-229 in particular, if the engine follows the U-233 chain).

---

## 9. Recommended METHODS updates

1. §4.1: `U238+` m = 3.0016 (Pa-234 IT branch), series total 14.0016; or state that the integers are nominal. Add At-218, Tl-210 (`Ra226+`, `Rn222+`) and Po-211 (`Ac227+`) as members.
2. §4.1: `Rn220+` is a flow-basis count only (fails the 1/10 half-life rule).
3. §4.2: `Ba140+` and `Zr95+` are **not formed** (La-140/Ba-140 = 0.13; Nb-95/Zr-95 = 0.55). Add `Te132+` (2.0308), `Mo99+` (1.9654), `Np237+` (2.0000).
4. §4.2: `Cs137+` m = 1.944 (ICRP-107); note that DDEP gives 1.946.
5. §4.2: `Sr90+`, `Ru106+`, `Ce144+` are 2.00025, 2.000001, 2.000035 with the transient factor.
6. §3.4 / §4.1: C-14 half-life is 5700 a in ICRP-107 (and ENSDF), not 5730 a.
7. §4.1: the "provisional" sentence can go; the 0.0461 uranium ratio is confirmed (0.04606).

---

## 10. Open issues for the orchestrator

1. **Licence.** ICRP-07 data files are free "for educational, research and not-for-profit purposes" under their copyright notice, provided the notice is reproduced. Recorded as `licence = restricted` for S9001–S9003. If Radiopassive is published commercially, the data may need permission. Notice text (from the RadData package): "Copyright (C) 2008 A. Endo and K.F. Eckerman. All Rights Reserved." The notice should be reproduced alongside the data if it is redistributed.
2. **ICRP-07.RAD not obtained from icrp.org.** Used the RadData tidy copy; verified against the icrp.org `.NDX` (§1). If a primary `.RAD` copy is wanted, the CD supplied with the publication is the source; `https://www.icrp.org/publication.asp?id=ICRP%20Publication%20107` does not link it.
3. ~~DDEP values came through a web-fetch summariser.~~ **Resolved in §11.3:** both PDFs were read directly and the figures confirmed.
4. **I-129 / Tc-99 / Cs-135 / Te-132 beta energies** differ from ENSDF by 11–20%; a decision is needed on whether to override ICRP (§5). Xe-138 and Pa-234 are no longer in this list (§11.2).
5. ~~Rh-103m, Te-125m, Rb-88, Cs-138~~: added (§11).
6. **Schema points**: `daughters` can contain `SF`, stable nuclides and out-of-table radionuclides (J5); `parent_group` is empty for artificial groups (J6); `role` and `multiplier_scope` are new `groups.csv` columns (after `chain`) that SCHEMA §4.2 does not yet list; SCHEMA needs updating to match (§11).
7. **Source type for RadData** is `grey` (rank 5) because it is a redistribution; its content is ICRP's. If the validator forbids rank-5 sources for primary data, relabel it as an access route for S9001.

---

## 11. Follow-up changes (coordinator request, 2026-10-20)

### 11.1 Added nuclides, groups and columns

**Nuclides added** (ICRP-107, same method; 107 rows now). All four are marked "Supplementary nuclide" in `notes`; each decays to a stable nuclide.

| Nuclide | T½ | Mode | e_total (MeV) | Used in |
|---|---|---|---|---|
| Rh-103m | 56.114 min | IT | 0.039409 | `Ru103+` |
| Te-125m | 57.4 d | IT | 0.145062 | `Sb125+` |
| Rb-88 | 17.78 min | β⁻ | 2.708925 | `Kr88+` |
| Cs-138 | 33.41 min | β⁻ | 3.607335 | `Xe138+` |

The 107 rows still match the icrp.org `.NDX` field-by-field. The spot-check pool (§5) was drawn on the original 103 and is not redrawn.

**Groups** (69 rows; four singles replaced by four new groups):

| Group | Outcome | m | e per head decay (MeV) | Rule detail |
|---|---|---|---|---|
| `Ru103+` | Forms (transient weights) | 1.988531 | 0.601169 | Rh-103m / Ru-103 = 0.00099 |
| `Sb125+` | Forms (transient weights) | 1.245337 | 0.573883 | Te-125m / Sb-125 = 0.0570 |
| `Kr88+` | **Released gas, flow only** | 2 | 5.031633 | Rb-88 / Kr-88 = 0.1043: fails the 1/10 rule narrowly |
| `Xe138+` | **Released gas, flow only** | 2 | 5.389159 | Cs-138 / Xe-138 = 2.37: the daughter outlives the head |

The released-gas weights are branching only (eventual decays per head decay, no transient factor). The old single groups `Ru103`, `Sb125`, `Kr88`, `Xe138` no longer exist.

**New `groups.csv` columns**, placed immediately after `chain`, replacing the `[released_radon]` note tag (now removed):
- `role` ∈ {`chain`, `released_gas`, `artificial`}: 13 `chain` (the natural-chain groups and `K40`), 4 `released_gas` (`Rn222+`, `Rn220+`, `Kr88+`, `Xe138+`), 52 `artificial`.
- `multiplier_scope` ∈ {`stock_and_flow`, `flow_only`}: `flow_only` for exactly the four released-gas groups; 65 are `stock_and_flow`.

**Other groups whose daughters outlive, or nearly match, the head.** I checked every group's longest member half-life against its head's. No other group has a member with ratio ≥ 0.1, so none needed `flow_only`. Closest cases, flagged for the engine: `Mo99+` at 0.0912 (just inside the rule; transient factor 1.100, so the standing-activity multiplier is only reached after about 5 half-lives of Tc-99m, about 30 h) and `Rn222+` (passes, but the radon-in-air case is still flow-only because progeny deposit rather than stay with the gas). `Sb125+` (0.057) and `Te132+` (0.030) are comfortably inside.

### 11.2 Xe-138 (+24.8%) and Pa-234 (+46.5%) beta differences

**Cause: partly an error on my side, partly genuine.** No extra fetches were needed; the cached IAEA files showed it.
- ENSDF's β⁻ intensities for these two decays do not sum to 100%: **Xe-138 sums to 112.45%, Pa-234 (ground state) to 133.5%**. My comparison summed energy × intensity without normalising, so it was inflated by those factors. This is a method error in my cross-check, not an error in either database.
- Level matching was correct (Pa-234 ground state, p_energy 0, T½ 6.7 h; Pa-234m rows, sum 99.84%, give 0.8124 MeV against ICRP's 0.8125, an excellent match).
- After scaling each decay's β intensities to the ENSDF branch (100% for Xe-138, 100% for Pa-234): **Xe-138 +10.9%, Pa-234 +9.8%**. These residuals are genuine differences between evaluations (the ENSDF feeding patterns for these complex decays are unnormalised and uncertain), not parsing faults. Tl-210 (sum 103%) and Pa-233 (101.9%) were also affected by smaller amounts (+2.7% → −0.3%, +4.4% → +2.4%).
- Normalised β comparison, all 63 nuclides ≥ 10⁻³ MeV: 46 within 1% (was 45). The notes in §6 and §7 now point here; rows for Xe-138 and Pa-234 in `nuclides.csv` carry this explanation.

### 11.3 DDEP PDFs re-read directly

Both PDFs were downloaded and read as images (not through the summariser): `http://www.lnhb.fr/nuclides/Cs-137_tables.pdf` and `http://www.lnhb.fr/nuclides/I-129_tables.pdf`.

| Quantity | Summariser said | PDF says | Change |
|---|---|---|---|
| Cs-137 T½ | 30.018 a | 30.018 (22) a | none |
| Cs-137 β → Ba-137m (β₀,₂) | 94.57% | 94.57 (26)% | none; evaluation dated 02/12/2021 – 18/07/2023 (S. Leblond, LNE-LNHB; cite Mougeot et al., Metrologia 62 (2025) 029002) |
| Cs-137 mean β energies | — | 173.67 keV (94.57%), 332.51 keV (0.0006%), 284.90 keV (5.43%) | new detail |
| I-129 T½ | 16.1 (7) × 10⁶ a | 16.1 (7) × 10⁶ a | none; **+2.5% above ICRP's 15.7 × 10⁶ a** (IAEA/ENSDF matches ICRP) |
| I-129 β⁻ to 39.58 keV level | 99.5%, mean 37 keV | 99.5 (5)%, avg 37 (1) keV, E_max 151.2 (11) keV, "2nd Forbidden" | none |
| I-129 β⁻ to ground state | not given | 0.5 (5)%, 2nd unique forbidden, no mean given | new detail |

**Correction to the notes:** the DDEP I-129 evaluation is old (Chechev & Sergeev, 10/12/2001 – 18/6/2004), so the 37 keV is a 2004 value, not a recent one. The qualitative conclusion stands: both ENSDF (2014) and DDEP give a lower mean than ICRP. Source S9006's notes were updated to say the PDFs were read directly.

### 11.4 Proposed uncertainty bands for the pipeline (from the IAEA cross-check, §6)

Basis: the 103-nuclide IAEA comparison, with β intensities normalised as in §11.2. METHODS §11.1 reads low and high as about the 5th and 95th percentiles, so each band below is set from the **95th percentile of |ICRP − IAEA|**, rounded up. They describe the **spread between two evaluation systems**, not a sampling error, and the IAEA side is itself imperfect for Auger and X-ray sums (§6). Treat them as conservative. They apply to `nuclides.csv` values; apply them symmetrically unless a direction is given.

| Quantity | n | Median |Δ| | 95th pct | Max (nuclide) | **Proposed band** | Outliers to treat separately |
|---|---|---|---|---|---|---|
| Half-life | 103 | 0.01% | 0.94% | 14.7% (At-218) | **±1%** | At-218 ±15% (weight 0.0002, irrelevant); Po-212 and Cm-246 ±2% |
| α energy | 38 | 0.03% | 1.3% | 3.3% (Ac-227) | **±1.5%** | Ac-227 ±3.5% (α is 80% of a very small total, 0.085 MeV) |
| β energy, excluding the four forbidden nuclides | 57 | 0.21% | 6.1% | 10.9% (Xe-138) | **±7%** | Xe-138 and Pa-234 ±11% |
| β energy, forbidden nuclides | 4 | — | — | 20.4% (I-129) | **−25% / +5%** (ICRP is the high side) | I-129 −20%, Tc-99 −16%, Cs-135 −15%, Te-132 −11% (ENSDF values given in §7) |
| γ + X energy, nuclide photon energy ≥ 0.01 MeV | 59 | 0.6% | 13.8% | 25.7% (Th-234) | **±15%** | below 0.01 MeV use ±30%; Ra-228 (photon energy 0.003 MeV) −82% |
| γ + X energy, ≥ 0.1 MeV | 40 | 0.3% | 8.0% | 15.6% (Co-58) | ±8% (optional tighter band) | |
| Conversion + Auger electrons, ≥ 0.01 MeV | 43 | 10% | 34% | 38% | **±35%** | below 0.01 MeV use ±90% or wider; Auger-rich EC emitters (Fe-55, Co-58) at the top of the range |
| `e_total_mev`, α-dominated nuclides (α + recoil > 90% of total; 36 nuclides) | 35 | 0.04% | 0.9% | 1.5% (Np-237) | **±1.5%** | |
| `e_total_mev`, all other nuclides | 66 | 0.25% | 16% | 61% (Fe-55) | **±15%** | Fe-55 +60%, Co-58 +15%, Xe-133m −16%, Tc-99 −16%, Cs-135 −15% (IAEA − ICRP; Cs-137 excluded as a convention case) |

**Group-level `e_per_head_decay_mev`** (IAEA-based vs ICRP, members weighted): natural-chain groups agree to within 1.3% (U238+ −0.2%, U235+ +0.6%, Ra226+ −0.1%, Ac227+ −0.1%, Th228+ +0.02%, Ra228+ −1.1%, Pb210+ −1.3%); `K40` −3.3%. Proposed **±1.5% for the U/Th-chain groups (`K40` ±3.5%)**. For the 52 artificial groups the median difference is 0.2% and the 95th percentile 16% (largest: Fe-55 +61%, Co-58 +15%, Xe-133m, Tc-99, Cs-135 about −16%). Proposed **±15% by default for artificial groups**, with the individual outliers listed above. The new groups `Ru103+`, `Sb125+`, `Kr88+`, `Xe138+` were not cross-checked: IAEA data were not fetched for the four added nuclides, so use ±15% for them.

**Caveats.** (a) ICRP-107 and ENSDF share lineage, so for half-life, α and γ the real uncertainty could exceed these bands; the bands capture only the disagreement that remains after that shared ancestry. (b) The photon and electron bands reflect different X-ray/Auger procedures more than measurement error. (c) None of these bands include the uncertainty in the source activity data, which will dominate in the pipeline. (d) No change has been made to `nuclides.csv` or `groups.csv` for these bands (no uncertainty columns exist in SCHEMA §4.1–4.2); they are recommendations for the pipeline's factor tables.

---

## 12. Addendum D35 (2026-10-25): additions only

Source: ICRP-107 via S9001–S9003, same method as §1 (energies = Σ yield × energy by ICRP radiation code; half-lives in ICRP units, Julian-year conversion; weights as in §2 J1/J2). Existing rows are byte-identical (new rows appended; checked by prefix comparison). Scratch scripts: `/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/addendum03/`.

### 12.1 Nuclides added (15 rows; 107 → 122)

Requested: Ni-59, Zr-93, Nb-93m, Nb-94, Sn-126, Am-242m, Sr-89, Te-129m, Cs-136, Ce-141. Progeny needed by the chains: **Sb-126m, Sb-126** (Sn-126), **Am-242, Np-238** (Am-242m), **Te-129** (Te-129m). **Zr-95, Nb-95 and Cm-242 were already present** (original 103-row list and their groups `Zr95`, `Nb95`, `Cm242`), so nothing was added or changed for them.

| Nuclide | T½ | Mode → daughters (branching) | e_total (MeV) |
|---|---|---|---|
| Ni-59 | 1.01e5 a | EC/β⁺ → Co-59 | 0.006903 |
| Zr-93 | 1.53e6 a | β⁻ → Nb-93m 0.975, Nb-93 0.025 | 0.019420 |
| Nb-93m | 16.13 a | IT → Nb-93 | 0.031446 |
| Nb-94 | 2.03e4 a | β⁻ → Mo-94 | 1.726542 |
| Sn-126 | 2.3e5 a | β⁻ → Sb-126m | 0.194884 |
| Sb-126m | 19.15 min | β⁻/IT → Te-126 0.86, Sb-126 0.14 | 2.180453 |
| Sb-126 | 12.35 d | β⁻ → Te-126 | 3.109745 |
| Am-242m | 141 a | IT/α → Am-242 0.9955, Np-238 0.0045 | 0.073350 |
| Am-242 | 16.02 h | β⁻/EC → Cm-242 0.827, Pu-242 0.173 | 0.199434 |
| Np-238 | 2.117 d | β⁻ → Pu-238 | 0.839812 |
| Sr-89 | 50.53 d | β⁻ → Y-89 | 0.584626 |
| Te-129m | 33.6 d | IT/β⁻ → Te-129 0.63, I-129 0.37 | 0.308461 |
| Te-129 | 69.6 min | β⁻ → I-129 | 0.606108 |
| Cs-136 | 13.16 d | β⁻ → Ba-136 | 2.273211 |
| Ce-141 | 32.508 d | β⁻ → Pr-141 | 0.247832 |

### 12.2 Groups added (9 rows; 69 → 78)

All have `role = artificial`, `multiplier_scope = stock_and_flow`, empty `parent_group` (SCHEMA: artificial groups carry none; G05 concerns released-gas groups only and is untouched). Weights follow the existing artificial convention: daughter weight = Σ over parent paths of weight × branching × $\lambda_d/(\lambda_d-\lambda_h)$ (with $\lambda_h$ the head's decay constant), and $\bar E_k=\sum_i w_i\,\bar E_{\text{tot},i}$.

| Group | Members and weights | m | $\bar E_k$ (MeV) | Derivation of $\bar E_k$ |
|---|---|---|---|---|
| `Ni59` | Ni-59 (1) | 1 | 0.0069032 | single nuclide |
| `Zr93+` | Zr-93 (1); Nb-93m (0.97501028) | 1.97501028 | 0.050080183 | 0.01941981 + 0.97501028 × 0.031446205. Nb-93m / Zr-93 half-life ratio 1.05 × 10⁻⁵; weight = 0.975 × 1.0000105. |
| `Nb94` | Nb-94 (1) | 1 | 1.7265416 | single |
| `Sn126+` | Sn-126 (1); Sb-126m (1.0000000); Sb-126 (0.14000002) | 2.14000002 | 2.8107017 | 0.19488447 + 2.1804529 + 0.14 × 3.10974474. Ratios 1.6 × 10⁻¹¹ and 1.5 × 10⁻⁷. |
| `Am242m+` | Am-242m (1); Am-242 (0.9955129); Np-238 (0.004500185) | 2.00001308 | 0.2756685 | 0.0733503 + 0.9955129 × 0.19943376 + 0.004500185 × 0.83981159. Cm-242 and Pu-242 (Am-242 products) and Pu-238 (Np-238 product) are separate heads. |
| `Sr89` | Sr-89 (1) | 1 | 0.58462585 | single |
| `Te129m+` | Te-129m (1); Te-129 (0.63090756) | 1.63090756 | 0.69085958 | 0.30846145 + 0.63090756 × 0.60610802. Te-129 / Te-129m ratio 1.44 × 10⁻³ (factor 1.001442). I-129 (existing head) takes the other 37% and Te-129's decays. |
| `Cs136` | Cs-136 (1) | 1 | 2.2732111 | single |
| `Ce141` | Ce-141 (1) | 1 | 0.2478322 | single |

**Independent recomputation** (script `verify.py`; parses the raw icrp.org `ICRP-07.NDX`, not the RadData copy used for the build): `Te129m+` m = 1.630908 (table 1.63090756); `Sn126+` m = 2.140000 (2.14000002); `Am242m+` m = 2.000013 (2.00001308); Cs-136 e_total summed straight from the `.RAD` lines = 2.273211 (table 2.27321114). All agree to the stated rounding.

### 12.3 Judgement calls

1. **Zr-95 / Nb-95 stay separate** (precedent: `Zr95`, `Nb95`, §3). Nb-95 (35.0 d) / Zr-95 (64.0 d) = 0.546, far above 1/10, so Nb-95 is not in equilibrium with its parent; unchanged. Likewise Ba-140/La-140. The Zr-95 → Nb-95m branch (1.08%, 0.32% of energy) remains omitted, as before.
2. **Zr93+ includes Nb-93m as progeny** although Nb-93m (16 a) is long enough to matter on century timescales. The 1/10 rule is met by five orders of magnitude, so a head-only engine with a fixed multiplier is consistent: Nb-93m is in equilibrium with Zr-93 whenever Zr-93 is old enough to matter (≫ 16 a). For *young* Zr-93 (< ~50 a, e.g. fresh in-core inventory) the Nb-93m activity is still building up and the multiplier overstates the Nb-93m part; the effect on $\bar E_k$ is small (Nb-93m is 0.031 MeV against Zr-93's 0.019 MeV, so up to ~0.03 MeV of 0.05).
3. **Am242m+ does not absorb Cm-242**, although Cm-242 (162.8 d) is < 1/10 of Am-242m's half-life. Cm-242 is an existing independent head fed from other sources (Am-241 neutron capture via Am-242, not only Am-242m), and the schema has no parent link for artificial groups. The Am-242 → Cm-242 (0.827) and Pu-242 (0.173) flows are available from `nuclides.csv` `daughters`. Np-238 (0.45%) is included for completeness (D24).
4. **Te129m+ weight for Te-129 is 0.6309**, not 1: only the IT branch passes through Te-129; the β⁻ branch goes straight to I-129. I-129 is not folded in (T½ 1.57e7 a).
5. **Sb-126m and Sb-126 are not heads of their own groups**; they appear only inside `Sn126+`. Sb-126m → Sb-126 is 14%.
6. **Nb-93m, Sb-126m, Sb-126, Am-242, Np-238 and Te-129 have no single-nuclide groups** (not heads), as for other progeny.

### 12.4 Possible issues in existing rows (reported, not changed)

- None found that affect values. Observations only: (a) METHODS §4.2's table does not yet list the new groups; (b) `Zr95` still omits its Nb-95m branch (0.32%), already noted in §8; (c) `Cm242` and `Am242m+` are not linked at group level (artificial groups carry no parent links by design, §2 J6).

### 12.5 Checks run

`python3 -m pipeline.validate --root /mnt/user-data/outputs` → `OK: no issues`. `cd pipeline && python3 -m pytest -q` → 556 passed.

## 13. D40 second addendum and D42 isomer rule (2026-10-25)

Before-copies: `scratchpad/addendum03b/{nuclides,groups,notes}.before`. `nuclides.csv` grew from 122 to 195 data rows (73 added, old bytes unchanged). `groups.csv` grew from 78 to 131 data rows (53 added, 3 existing rows changed). All values from ICRP-107 (S9001–S9003) with the same method as §§2–12. Generator: `scratchpad/addendum03b/make2.py`; independent recompute: `verify2.py` (raw NDX zip and RadData `.rda`).

### 13.1 Rule change (D42)

D41 (1 keV exemption) is superseded: every ICRP-107 branch with branching >= 1e-3 is counted, whatever its energy (precedent Pa-234 in `U238+`). Scan (`d42scan.py`) of every non-gas group, every member, every daughter with branching >= 1e-3 that is radioactive, shorter-lived than head/10 and not a member:

- Omitted and fixed: Ce-144 -> Pr-144m (0.977%), Zr-95 -> Nb-95m (1.08%), Pu-239 -> U-235m (99.94%).
- Radioactive daughters that are longer-lived or independent heads with their own group are not omissions: Pa-234m/Pa-234 -> U-234, Th-231 -> Pa-231, Th-232 -> Ra-228, Pa-233 -> U-233, Am-243 -> Np-239, Cm-245 -> Pu-241, Am-242 -> Cm-242 (all have their own groups, or are intentionally separate as in §12).
- **Gap found:** U-233 -> Th-229 (100%, 7340 a) had no Th-229 group. Closed by the new `Th229+` (9 members). `U233` is unchanged (Th-229 is a long-lived independent head, not folded in).
- Not changed, weight below threshold: At-218 -> Rn-218 (branching 0.001, but At-218 weight is 2e-4, so the Rn-218 weight is 2e-7).
- Stable-in-practice daughters ignored: Kr-87 -> Rb-87 (4.9e10 a), Pm-147 -> Sm-147 (1.1e11 a), Pr-144 -> Nd-144 (2.3e15 a).
- New groups: only `U232` (U-232 -> Th-228 100%) trips the scan; Th-228 is the independent head of `Th228+` (as U-234 and Th-230 are for their parents), so it is deliberately not folded in.

### 13.2 Changed existing rows (old -> new)

| Group | Members | Weights | Multiplier | Ē per head decay (MeV) |
|---|---|---|---|---|
| `Ce144+` | `Ce-144;Pr-144` -> `Ce-144;Pr-144;Pr-144m` | `1;1.0000352` -> `1;1.0000354;0.0097700715` | 2.0000352 -> **2.00980547** | 1.3483273 -> **1.3489218** |
| `Zr95` (ID kept, see below) -> `Zr95+` | `Zr-95` -> `Zr-95;Nb-95m` | `1` -> `1;0.011447381` | 1 -> **1.01144738** | 0.85064814 -> **0.85350609** |
| `Pu239` (ID kept) | `Pu-239` -> `Pu-239;U-235m` | `1` -> `1;0.9994` | 1 -> **1.9994** | 5.2442411 -> **5.2443176** |

Group IDs: `Zr95` was renamed to `Zr95+` (passes all 556 tests). **`Pu239` was NOT renamed to `Pu239+`**: renaming it makes 28 spec-blind tests in `tests/test_validate.py` fail (the fixture `tests/fixtures/valid_rows.csv` uses nuclide ID `Pu239`; the failures are the X01, X02, X05, V15, routine-transfer, CLI and real-project tests that load it). Tests were not edited. Decision for Steve: keep `Pu239` and treat it as meaning "Pu-239 + U-235m", or rename and update the fixture. Other references to the old ID `Zr95` (METHODS, `research/nuclear/spent_fuel_inventory_derived.csv`, `research/events/notes.md`) are outside this task and need the coordinator.

Changed notes on the three rows describe the D42 change and the old values. Ē for Pr-144m uses ICRP-107 (0.0608 MeV per decay); U-235m is 7.65e-5 MeV; Nb-95m is 0.2497 MeV. New nuclide rows: Pr-144m, U-235m, Nb-95m (the last two are required by the changes above). Pr-144 weight is 1.0000354 vs 1.0000352 only because Pr-144m now carries its own transient factor.

### 13.3 Sweep result by criterion

Presence scan of the extracted text of UNSCEAR 2016 Annex B, 2000 Annexes C and J, 2008 Annexes B and D, 2013 Annex A, 2020/21 Vol. II, UNSCEAR 1988 Annex B, OSPAR 2022/2023 discharge reports, RIFE-24, NEA 7201 and the other task 1.2 texts (`pres2.py`, `pres3.py`; nuclide-symbol regex, ICRP nuclides only, so tables that are images are not seen) plus the spent-fuel model (`sweep_a.py`, `res.pkl`, 72 cases).

- **(a) >= 0.1% of activity or heat at 1 to 1e4 a** (maximum over the 72 cases; added): Y-91 (0.81% / 0.75%), Ag-110m (0.12% / 0.40%), Pr-144m (0.27% activity, row only, now in `Ce144+`), Sn-119m (0.12%), Cm-243 (0.105% heat at 30 a), Te-127m and Te-127 (0.075%). Also added below the threshold, since "exhaustive": Ir-192n, Sn-123, Pd-107, Gd-153, Se-79, Rh-102, Sn-113 with In-113m, Cd-113m. All already-present nuclides were skipped.
  - **Ir-192m mapping:** the ORIGEN/Carter "Ir-192m" (241 a) is ICRP-107's `Ir-192n`; ICRP's `Ir-192m` is the 1.45 min isomer. Row `Ir-192n` and group `Ir192n+` (with Ir-192, multiplier 2.0008) are used; mapping inferred from the half-life, not stated in any source.
- **(b) Effluent tables (UNSCEAR 2016B, 2000C, OSPAR, RIFE, UNSCEAR 1988/2008B) not yet present, added:** Ag-110m, Zn-65, Cr-51, Co-57, Sb-124, Eu-152, Cl-36, Kr-81, I-125, S-35, P-32, Na-24, Fe-59, Ca-45, Cd-109, W-185, Be-7, N-16, U-232, Y-91, Sr-91 (Y-91m), Ce-143, Nd-147, Kr-89, Rb-89, Xe-137, Ba-139, Zr-97 (Nb-97). Already present from the coordinator's list: I-133, Te-132, Ru-106, Cs-134, La-140, Pm-147, Sm-151, Eu-154, Eu-155, Tc-99, Mn-54, Cs-135, I-129, Ni-63 and the others in §§2 to 12.
- **(c) Chernobyl, Fukushima and TMI source terms:** added I-135 (Xe-135m), I-134, Te-131m (Te-131), Sr-91, Zr-97, Ba-139, Ce-143, Nd-147, Te-127m, Ag-110m, Kr-89, Rb-89, Xe-137. Not found in any scanned source text (so not added): Sr-92, Y-92, Y-93, Ru-105, Rh-105, Sb-127, Sb-129, Pr-143. Check the PDFs if Steve wants those.
- **(d) Decommissioning and disposal long-lived products:** added Ho-166m, Ca-41, Mo-93 (`Mo93+` with Nb-93m), Be-10, Ar-39, Se-79, Pd-107, Eu-150, Ba-133, Nb-92, Mn-53, Ag-108m (+ Ag-108). Present from D35 and earlier: C-14, Ni-59, Ni-63, Zr-93, Nb-94, Tc-99, Sn-126, I-129, Cs-135, Sm-151.
- **Judged out of scope, not added** (positron emitters, medical or accelerator-only, found in UNSCEAR 2008 Annex B or 2020 texts): C-10, C-11, N-13, O-14, O-15, O-19, F-17, F-18, Al-28, P-30, S-37, S-38, K-38 to K-46, Mn-56, Ga-67, Tl-201, I-121, I-123, I-124, Re-186, Er-169, Na-22, Ir-192, Pd-103, Cs-131, Rb-86. Say if you want them (all exist in ICRP-107).
- **Absent from ICRP-107:** Nb-97m (so `Zr97+` carries no Nb-97m); no other requested nuclide is missing. Nothing was invented.

New groups (53): `Y91`, `Sr91+`, `Ag110m+`, `Sn119m`, `Cm243`, `Te127m+`, `Ir192n+`, `Sn123`, `Pd107`, `Gd153`, `Se79`, `Rh102`, `Sn113+`, `Cd113m`, `I135+`, `I134`, `Sb124`, `Zn65`, `Cr51`, `Co57`, `Ce143`, `Nd147`, `Eu152`, `Ho166m`, `Cl36`, `Ca41`, `Mo93+`, `Be10`, `Ar39`, `Kr81`, `Na24`, `S35`, `P32`, `Fe59`, `Ca45`, `I125`, `Cd109`, `W185`, `Be7`, `Zr97+`, `Ba139`, `Te131m+`, `Kr89`, `Rb89`, `Xe137`, `N16`, `U232`, `Ba133`, `Nb92`, `Mn53`, `Eu150`, `Ag108m+`, `Th229+`. Multipliers: `Sr91+` 1.63729888, `Ag110m+` 1.01360002, `Te127m+` 1.97950089, `Ir192n+` 2.0008394, `Sn113+` 2.0005806, `I135+` 1.17236562, `Mo93+` 1.88356297, `Zr97+` 2.0773157, `Te131m+` 1.22512676, `Ag108m+` 1.087, `Th229+` 7.99970145; all others 1. Convention as before: daughters folded only if half-life < head/10 (asserted in the generator); independent long-lived heads (Y-91, Xe-135, I-131, Pm-147, Pu-239, Am-243, Th-228, Cs-137, Sr-89) are not folded. Short-lived progeny with no head role (Y-91m, Ag-110, Te-127, Ir-192, In-113m, Xe-135m, Nb-97, Te-131, Ag-108, Ra-225 to Pb-209) are table nuclides only. Every new nuclide row has its criterion tag in `notes`.

Edge cases: ICRP-107 lists At-217 -> Bi-213 at 0.99988 only (the 0.012% beta branch is not tabulated); stored as 1 so `N01` passes (effect 1.2e-4, below 1e-3). Po-213 (4.2 microseconds) is stored in seconds like Po-212.

Effect on the 1 a spent-fuel coverage (§4.2 of METHODS): Y-91, Ag-110m and Pr-144m (now in `Ce144+`) are the three closers named in `research/nuclear/notes.md`; the coverage table was not recomputed in this task.

### 13.4 Natural-series completeness

For U-238, U-235 and Th-232, all members with cumulative branching weight >= 1e-3 (`series.py`, from ICRP-107 `.NDX`) are in some group, including Pa-234 (0.16%, `U238+`), At-218 (0.02%, `Ra226+`/`Rn222+`), Tl-210 (0.021%), Bi-210, Po-211 (0.276%), Fr-223 (1.38%) and Tl-208 (35.9%). No gap. Not covered, each below 1e-3: Rn-218 (2e-7), Hg-206 (1.9e-8), Tl-206 (1.3e-6), At-219 (8e-7), Bi-215 (8e-7). The end products Pb-206, Pb-207 and Pb-208 are stable.

### 13.5 Checks run

- `python3 -m pipeline.validate --root /mnt/user-data/outputs`: `OK: no issues` (data/reference clean).
- `cd pipeline && python3 -m pytest -q`: 556 passed (with `Zr95+` renamed and `Pu239` kept). With `Pu239` also renamed to `Pu239+`: 528 passed, 28 failed (fixture use of `Pu239`; reverted).
- Independent recompute from the raw `ICRP-07.NDX` zip and RadData `.rda` (`verify2.py`) matches: `Ce144+` 2.0098054 / 1.3489219 MeV, `Zr95+` 1.0114474 / 0.8535061, `Pu239` 1.9994000 / 5.2443171, `Sr91+` 1.6372989 / 1.7165671, `Th229+` 7.9997014 / 34.200467.
