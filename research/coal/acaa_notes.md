# ACAA archive: extraction notes and proposed revision of the US ash route shares

Prepared 2026-11-05 from `import/acaa/` (72 PDFs, gitignored, not committed). Nothing in `data/`, `pipeline/`, `docs/` has been edited. Outputs of this task:

- `research/coal/acaa_series.csv` (360 rows: year, `ccp_type`, produced and used in short tons and tonnes, `use_fraction`, source file, page, `extraction_method`, `status`, notes)
- `research/coal/acaa_uses.csv` (1,067 rows: year, `ccp_type`, normalised use category, short tons used; complete for 1999–2017 where the table was readable, key categories only elsewhere)
- `research/coal/acaa_build_series.py` (rebuilds both CSVs; text-layer years are parsed from the PDFs, scanned years are transcribed dictionaries with arithmetic checks)

Units: ACAA reports **short tons** (1 short ton = 2,000 lb = 0.90718474 t). Both columns are in the CSV; this note quotes short tons (Mst = million short tons) unless it says "t". Percentages are unitless and unaffected.

Two columns were added to the requested set: `status` (`adopted` or `superseded`) and the tonne columns. `extraction_method` is `table` for every row (all figures come from survey tables; scans were read visually or by OCR and then checked, see §2). No `chart_read` values were needed: every year has an exact table. The chart PDFs were used only as a consistency check.

---

## 1. Coverage

### 1.1 What is in the 72 files

| Group | Files | Years | Use |
|---|---|---|---|
| Annual survey sheets, scans | `ACAA-CCP-Svy-1966-1976` (one history table), `-1977` to `-1999` (23 sheets), `2000_CCP_Production_and_Use_Survey`, `2016`–`2020-Survey-Results`, `2022-…-Results-FINAL`, `2024-…-Results-FINAL` | 1966–2000, 2016–2020, 2022, 2024 | Adopted (hand-read; see §2) |
| Annual survey sheets, text layer | `2001_rev_svy_11-02`, `acaa_2002…`, `2003`…`2006`, `2007`…`2010`, `Final2011`, `revisedFINAL2012`, `2013ReportFINAL`, `2014ReportFinal`, `2015-Survey_Results_Table`, `2021-…-FINAL`, `2023-…-FINAL` | 2001–2015, 2021, 2023 | Adopted (parsed) |
| Fly-ash table compilations | `1966-2009`, `…2010`, `…2011`, `…2012`, `…2013_FlyAsh_Prod_and_Use_Charts` | fly ash 1966–2013 (million short tons, 2 dp) | Cross-check only (the 2013 edition, page 5, is the longest) |
| Chart PDFs | `1966-2006_CCP_Svy_Prod_and_Use_Chart`, `2014CCPProdandUseCharts`, `2015-Survey_Results_Charts`, `2016`–`2019-Charts`, `2022`/`2023`/`2024-…-Charts`, `Production-and-Use-Charts`, `…Charts.1` | all-CCP 1991–2024, fly ash 2000–2024, bottom ash 2000–2024, 1966–2006 comparison | Not extracted (tables exist); the 2024 chart was inspected and agrees with the tables |
| EPA-region breakdowns | `2005_CCP_Svy_Production_by_EPA_Regions`, `…Utilization_by_EPA_Regions`, `Charts_Ash_Production_EPA_Rgns_1-10`, `Charts_Ash_Use-EPA_Rgns_1-10` | 2004 and 2005 only, 10 regions | Not extracted (single years; no time series); useful later if a regional mine-fill share is wanted |
| Narrative | `26-ACAA-Brochure-12-8_v2`, `News-Release-Coal-Ash-Production-and-Use-2024` | 2024 | Read for definitions and the harvested-ash caveat (§5) |

### 1.2 What the series covers

| Quantity | Years | Notes |
|---|---|---|
| Fly ash and bottom ash, produced and used | 1966–2024 (every year) | 1966–1976 from the history table; 1977–86 from the sheets' comparative tables (million short tons, 0.1 Mt precision in 1977–79, 0.01 Mt 1980–85, 0.001 Mt 1986); 1987 onward in exact short tons |
| Boiler slag | 1968–2024 | Not collected in 1966–67 (shown as "-0-" in later sheets) |
| FGD material, one undivided column (`fgd_material_all`) | 1987–2001 | Called "sludge" in 1987 and 1989 |
| FGD gypsum and other FGD (wet, dry, other summed) | 2002–2024 | `other_fgd` notes give the three components |
| FBC ash | 2002–2024 | 2007 ambiguity, see §2.4 |
| Fly + bottom + slag subtotal (`fa_ba_bs_subtotal`) | 1966–2024 | The "ash" base the US route shares (coal:0074–0079) claim to describe |
| All-CCP total | 1987–2024 | Not available before FGD was surveyed |
| Use by category | 1999–2017, 2019–2024 (key categories only 2016–2024; 2018 totals only); 1994–95 key categories | See `acaa_uses.csv` |

No use-category tables were transcribed for 1966–1993 or 1996–1998 (the totals by type are all in the series). The 1992–93 and 1996–98 category tables are legible in the scans if a later task needs them.

---

## 2. Extraction QA

### 2.1 Method by year

- **Text-layer years (2001–2015, 2021, 2023):** `pdfplumber` words assigned to header columns by right-edge x position. Page numbers are in the CSV (page 2 for the 2002 and 2006 files, page 1 otherwise).
- **Scans:** 2016–2020, 2022 and 2024 (fully formatted spreadsheets), 1999 and 2000, 1987–1995, the 1966–76 history table and the comparative tables of the 1977–86 sheets were read visually from 300 dpi renders. 1996–1998 production lines were read visually; the use totals for those three years come from OCR and were verified by arithmetic (see 2.2) and by the printed utilisation percentages. 2018 is rotated 90° in the file and was rotated before reading.
- **2007 blasting grit row** is missing from the text layer (garbled); its bottom ash and slag values (71,903 and 1,377,658 short tons) were read from the rendered page and agree with the arithmetic residual.

### 2.2 Automated cross-checks (all run in the build script or reproduced here)

1. **Total = sum of types.** Production and use totals equal the sum of all type columns for every year 1987–2024 within 3 short tons, with one exception: 1991, where the sheet rounds each type to the nearest 50,000 short tons (production sums to 50,000 less than the printed total). Fly, bottom and slag subtotals match the printed subtotals where the sheet prints one (1987–2001).
2. **Use categories sum to the type totals.** For every text-layer year and for 1999–2001 the category columns sum to the "Total CCPs Used by Category" within 0.05 % (the build script raises on a larger gap).
3. **Printed use-to-production percentages reproduced.** For the 15 text-layer years with a printed rate row (2002–2013, 2015, 2021, 2023) the printed fly ash and bottom ash percentages equal use ÷ production to ±0.01 point, except 2009 bottom ash and 2010 (see 2.3). Printed percentages on the scanned sheets I read also match (for example 1993 fly ash 22.003 %, 1995 25.0 %, 1996 27.4 %, 1997 32.1 %, 1998 33.5 %, 2016 59.85 %, 2017 63.09 %, 2019 60.60 %, 2020 64.52 %, 2022 59.63 %, 2024 78 %).
4. **Fly-ash table compilation (1966–2013, 48 years) against the adopted series.** 38 of 48 years agree within 0.005 Mst on both production and use. Differences are listed in 2.3.

### 2.3 Discrepancies between editions (and which value is adopted)

Rule used: the latest survey **sheet** wins; the fly-ash table compilation (an unofficial roll-up) is only a check. Where I could not decide, the sheet is adopted and the case flagged.

| Year | Item | Edition A | Edition B | Adopted |
|---|---|---|---|---|
| 1983 | Production of fly, bottom, total ash | 1983 own sheet: 52.35 / 14.0 / total 70.29 Mst | 1984–86 sheets: 47.15 / 12.73 / total 63.82 Mst (slag 3.94 both) | **B** (revised); A kept as `superseded` rows. Use unchanged (7.52 / 2.76 / 2.53), so the 1983 utilisation of all ash is 20.1 % (B) not 18.2 % (A). |
| 1992 | Fly ash used | sheet 13.071 Mst (27.20 %) | compilation 13.10 Mst (27.26 %) | Sheet (difference 0.2 % of use) |
| 1995 | Fly ash used | sheet 13.563 | compilation 13.60 | Sheet |
| 1996, 1997 | Fly ash produced | sheet 59.355 and 60.265 | compilation 59.30 and 60.20 | Sheet (printed subtotals and totals close on the sheet values) |
| 2002 | Fly ash used | sheet 26.629 Mst (34.81 %) | compilation 26.45 (34.58 %); the 2002 press paragraph rounds to 26.5 | Sheet |
| 2007 | Utilisation rate | file 40.55 % (survey respondents only) / 42.74 % with ARIPPA FBC | 2008 sheet: "2007 should have been 44.81 %" after under-reporting was found | Not re-tabulated by ACAA; the 2007 row uses the ARIPPA-combined FBC and total; 44.81 % is **not** reproduced by any table I could rebuild, so the corrected 2007 total is unknown (flag) |
| 2008 | Fly ash produced | sheet 72,454,230 | compilation 72.50 | Sheet |
| 2009 | Fly ash produced | revised sheet (file dated 10/5/11): 63,000,000 | compilation: 62.00 (its printed 39.87 % uses 62.0) | **Revised sheet.** The compilation was never updated. |
| 2009 | Bottom ash rate | printed 43.7 % | production 16,600,000 gives 42.2 % (a 16.0 Mst production would give 43.7 %); the sheet's total (125.48 Mst) closes only with 16.6 Mst | Production 16.6 Mst adopted; the printed rate looks like a typo (flag) |
| 2010 | Fly and bottom rates | printed 37.9 and 42.3 % | computed 38.0 and 42.4 % | Computed (rounding in the sheet) |
| 2007 | FBC | survey respondents only 1,273,061 produced, 323,741 used | ARIPPA-combined 6,092,756 produced, 5,143,436 used | ARIPPA-combined (the 2008 format folds it in); other kept as `superseded` |

The 2001 file is labelled "rev" (revised 11-02); no earlier 2001 edition was supplied. The 1966–76 history table disagrees with nothing in the later sheets.

### 2.4 Spot checks of individual values against the PDFs (19 values; read in the PDF image or text layer at transcription time, then re-confirmed by the tie-outs above)

2008 fly ash produced 72,454,230; 2013 bottom ash used 5,640,693; 2015 FBC used 11,723,843; 2021 fly ash produced 28,004,916; 2023 FGD gypsum used 17,144,903; 2016 all-CCP produced 107,427,866; 2017 FBC used 14,134,477; 2019 FGD gypsum produced 22,975,581; 2020 boiler slag used 369,729; 2022 wet-scrubber FGD produced 4,576,313; 2024 fly ash used 19,386,568; 2018 fly ash produced 36,178,427; 2000 bottom ash used 4,937,908; 1999 fly ash produced 62,699,947; 1998 fly ash produced 62,995,872; 1995 FGD material used 1,476,662; 1994 bottom ash produced 14,827,165; 1990 boiler slag produced 5,234,316; 1989 fly ash used 10,153,399; 1986 boiler slag produced 4.13 Mst; 1971 boiler slag used 3.7 Mst (history table). All agree with the CSV.

### 2.5 Comparison with the 2024 numbers in `factors_notes.md` (§5)

All agree: fly ash 24.72 Mst produced, 19.39 used (78 %); bottom ash 7.67 / 2.72 (35 %); boiler slag 1.58 / 0.89 (56 %); FGD gypsum 16.86 / 17.14 (102 %); FBC 5.89 / 5.89 (100 %, of which 5.44 Mst "mining applications"); total 63.57 / 46.04 (72 %). The 2024 survey table gives wet-scrubber FGD used 0 and dry-scrubber 6,388 short tons, "FGD other" 52,602 produced / 7,255 used. The factors-notes statement "fly ash fraction of fly + bottom + slag ash is 0.73 in 2024" is confirmed (0.728).

---

## 3. What the series says: utilisation 1966–2024

Production-weighted share of production **used** (ACAA's own definition, all uses counted), with the range of annual values in brackets.

| Period | Fly ash | Bottom ash | Bottom ash + boiler slag | Fly + bottom + slag | All CCPs |
|---|---|---|---|---|---|
| 1966–69 | 8.6 % (7.6–9.6) | 24.3 % (21.0–26.3) | 27.4 % | 14.8 % (12.3–17.5) | n/a |
| 1970s | 12.8 % (8.3–17.4) | 25.8 % (15.8–34.0) | 32.4 % | 18.6 % (13.0–24.1) | n/a |
| 1980s | 19.0 % (13.3–23.6) | 29.6 % (21.7–38.1) | 36.0 % | 23.5 % (18.7–28.0) | 22.6 % (1987–89) |
| 1990s | 27.8 % (22.0–33.5) | 32.4 % (27.8–39.1) | 40.9 % | 31.2 % (26.6–34.7) | 26.0 % (21.8–30.8) |
| 2000s | 38.9 % (31.9–44.8) | 40.5 % (29.2–47.4) | 45.3 % | 40.3 % (33.0–45.7) | 39.2 % (29.7–44.5) |
| 2010s | 48.4 % (38.0–63.1) | 41.1 % (31.9–50.1) | 44.7 % | 47.5 % (38.8–60.5) | 50.5 % (42.5–64.4) |
| 2020–24 | 68.4 % (59.6–78.4) | 41.7 % (35.5–61.2) | 40.8 % | 61.1 % (55.0–67.7) | 64.3 % (59.0–72.4) |
| 1991–2009 (existing USA era) | 34.4 % | 36.7 % | 43.0 % | 36.4 % (26.6–45.7) | 33.9 % (21.8–44.5) |
| 2010–2024 (existing USA era) | 52.7 % (38.0–78.4) | 41.2 % (31.9–61.2) | 43.8 % | 50.5 % (38.8–67.7) | 53.8 % (42.5–72.4) |

Key points.

- **Fly ash use rose roughly ninefold in fraction, from 8 % (1966) to 78 % (2024)**; the steepest rise is 1995–2006 (25 % to 45 %) and again after 2014 (46 % to 78 %). The post-2014 rise comes with a collapse of production (fly ash 50.4 Mst in 2014, 21.4 Mst in 2023) as coal plants closed; the used tonnage has been flat at about 16–24 Mst since 2009.
- **Bottom ash use has been nearly flat at 36–46 % since 2002** and shows no trend after 2005. Boiler slag is used heavily (typically 55–95 %) but is a small stream (1.6–6 Mst).
- Fly ash was used *less* than bottom ash until the mid-1990s, stayed within about 8 points of it in 1996–2014, and has been far above it since 2015 (2024: 78 % against 35 %, a 43-point gap). A single share for both is therefore misleading from 2015 on.
- Fly ash is 70 % of fly + bottom + slag production in 1968–79, 73.5 % in the 1980s, 74 % in the 1990s, 78 % in the 2000s, and 70–77 % since 2010 (0.704 in 2023). The activity builder fixes it at 0.80 (`coal_fly_ash_t / coal_ash_power_t` = 0.800 for 1970–2024), a little above any US decade.
- The all-CCP series is *not* the ash utilisation: it includes gypsum (use 57–102 %) and FBC ash (about 90–100 %, almost all "mining applications"). In 2010–24 the all-CCP simple mean is 55.5 % but the fly + bottom + slag simple mean is 53.1 % (production-weighted 50.5 %).

### 3.1 Comparison with the existing USA rows (coal:0074–0079)

| Existing row set | Stated basis | Central dispersed | ACAA table, same period | Comment |
|---|---|---|---|---|
| 1991–2009 | "all-CCP used fraction 22 % (1992–93) to 30 % (2000) to 40 % (2009); fly ash 32–44 % (2000–09)" | 0.33 (0.22–0.44) | Fly + bottom + slag 0.364 (0.266–0.457); all-CCP 0.339 (0.218–0.445) | Chart reading of the all-CCP series; 2009 was read as 40 %, the table gives 44.3 % (all-CCP) and 41.0 % (ash only). Central is within 0.04 of the ash-only value, but the base is all-CCP, not ash. |
| 2010–2025 | "fly ash 38 % (2011) to 80 % (2024), bottom ash 28–56 %; period mean about 55 %" | 0.55 (0.38–0.68) | Fly + bottom + slag 0.505 production-weighted, 0.531 simple mean (0.388–0.677) | The 0.55 equals the **all-CCP** simple mean (0.555). Ash-only is 0.03–0.05 lower. More importantly, one era hides a trend from 0.39 (2010–11) to 0.68 (2024). |
| Reisolated 0 / 0 / 0.06 | "mining applications only 11.6 kt bottom ash in 2024; high 0.06 from India" | 0 | Mining applications of fly + bottom + slag 0.8–3.7 % of production over 1999–2017, about 0 since 2019 | Central 0 is too low for 1999–2017 under ACAA's own categories (see §4). |

---

## 4. Mapping ACAA uses to the project tiers

The project tiers for ash residues are `dispersed` (in products or spread on land), `impounded` (contained disposal: pond, landfill, dyke) and `reisolated` (deliberately placed back underground, here mine backfill). The present rows treat *all* ACAA "beneficial use" as dispersed and the unused remainder as impounded. ACAA's use categories include several that are disposal-like, so that mapping is generous to `dispersed`.

| ACAA use category (survey labels) | Proposed tier | Justification |
|---|---|---|
| Concrete/concrete products/grout; blended cement/raw feed for clinker; flowable fill | dispersed | Ash incorporated in manufactured products in commerce; matches the existing tier definition |
| Road base/sub-base; soil modification/stabilisation; mineral filler in asphalt; aggregate | dispersed | Spread or built into infrastructure, no containment |
| Snow and ice control; blasting grit/roofing granules | dispersed | Abrasive/consumable, widely and non-recoverably spread (mostly boiler slag and bottom ash) |
| Agriculture; gypsum panel products (wallboard); miscellaneous/other | dispersed | Soil amendment, products; mostly FGD gypsum, not part of power ash |
| **Structural fills/embankments** | dispersed (central); disposal-like (low bound) | Bulk placement in the ground; the largest ambiguous use (3–13 % of production; 13–15 % of bottom ash production in the 2000s). It is uncontained but engineered and capped; I keep it dispersed in the central case (ACAA treats it as beneficial) and subtract it in the low bound |
| **Waste stabilisation/solidification** | impounded | Ash is used to solidify other wastes that are then landfilled (fly ash 2–4 % of production) |
| **CCR pond closure activities** (separate category from 2016; first seen in the 2016 sheet, 2021 and 2023 sheets also) | impounded | Ash used to cap or regrade an existing impoundment stays in place (fly 0.7–8 % of production, bottom ash up to 27 % in 2023). Not a flow into commerce |
| **Mining applications** | reisolated (all of it, as an upper bound for underground placement) | Mine reclamation, minefill and acid-drainage control. ACAA does not separate underground from surface placement; 2002 is peak for fly ash (1.9 Mst); FBC ash is 100 % "mining" in 2021–24 (5–14 Mst) but FBC is outside the fly + bottom + slag base |
| Oil/gas field services (from 2012) | impounded (central; arguably reisolated) |  Ash placed downhole (cement, drilling uses); 0.3–9 % of fly ash used; small; folded into impounded in the central case (conservative on dispersal) |
| Unused remainder (production − use) | impounded | Ponds, landfills, dyke raising; unchanged |

Disposal-like uses as a share of **production** (fly + bottom + slag; from `acaa_uses.csv`):

| Year | Structural fill | Waste stabilisation | Mining | Pond closure | Total used (for reference) |
|---|---|---|---|---|---|
| 1999–2000 | 5.2 % | 2.4 % | 2.0 % | 0 | 34 % |
| 2005 | 9.1 % | 3.0 % | 0.8 % | 0 | 42.5 % |
| 2010 | 9.0 % | 3.8 % | 3.3 % | 0 | 39.5 % |
| 2015 | 5.4 % | 1.9 % | 2.1 % | 0 | 52.5 % |
| 2017 | 2.7 % | 2.2 % | 2.2 % | 4.4 % | 60.5 % |
| 2020 | 2.3 % | 3.3 % | 0.2 % | 7.3 % | 57.8 % |
| 2023 | 0.1 % | 1.2 % | 0 | 5.0 % | 65.3 % |
| 2024 | 0.8 % | 0 | 0 | 0 | 67.7 % |

Three mappings follow. **L (liberal, current rows):** dispersed = all ACAA use. **S1 (proposed central):** L less waste stabilisation, pond closure, mining and oil/gas services. **S2 (proposed low bound):** S1 less structural fills. S1 is 0.02–0.06 below L in each era; S2 is a further 0.03–0.09 below S1 before 2016.

---

## 5. Caveats on the ACAA data (apply to any use of it)

1. **Survey, not census.** Respondents cover 30–68 % of generating capacity (2008: 68 %; 2021: 49 % of coal burn; 2023: 30 %); the rest is extrapolated. In the early 2000s fly ash, bottom ash, FGD gypsum and wet FGD are "extrapolated estimates rounded to the nearest 50,000 tons". From 2024 production comes from EIA through the "Ash Mart"; boiler slag and the FGD splits are 10-year averages (derived, not surveyed).
2. **Use can exceed production.** FGD gypsum 102 % (2024), FBC 100 %. ACAA's 2024 release says its survey tracks "fresh" ash only and that "harvesting" of previously landfilled ash into concrete, cement kilns and pond-closure uses is growing; a separate harvesting study was due in early 2026. The use fraction therefore overstates the fraction of *new* ash that is diverted from disposal by an amount ACAA calls "several million tons" (2024, unquantified).
3. **Pond-closure reporting is inconsistent.** The category is large in 2017–2023 (1.5–3.4 Mst) and almost zero in 2024 (7,364 short tons of bottom ash), which probably reflects a change in how closure ash is counted rather than practice. The 2024 use fraction (67.7 %) is therefore not comparable with 2020–23 under the S1 mapping.
4. **Definitions drift.** "Wallboard" became "Gypsum Panel Products"; "CCB/byproduct" became "CCP" (1996 to 1997); 1993–95 sheets split external-market and internal-producer applications (structural fill is reported in both; I summed them for 1994); the survey has never separated underground from surface mining applications.
5. **Pre-1987 values are in million short tons to 0.1 or 0.01** (1977–86), so use fractions for 1977–79 carry about ±0.5 point rounding.

---

## 6. Proposed revision (D72 draft)

Nothing below has been applied. `data/factors/coal.csv`, `pipeline/streams/coal.py`, the specs and `docs/DECISIONS.md` are untouched.

### 6.1 Verification that the US rows are inert today

- `data/activity/coal.csv` holds `coal_ash_power_t` and `coal_fly_ash_t` for `XWL` only (checked: no `USA` rows for either series).
- `pipeline/streams/coal.py` selects the route share with `WORLD_ACTIVITY = "XWL"` hard-wired (lines 589–600) and `residue_type=None`, `route=None`; the output country for these rows is the world row.
- Three existing tests guard this: `test_no_usa_route_shares_in_world_rows`, `test_usa_shares_not_used_for_world_rows` (both hard-code coal:0074–0079) and `test_usa_share_edit_does_not_change_world_rows` (edits coal:0077).
- Consequence: **any change confined to the USA rows (new rows, new bounds, new IDs) changes no output row** (values, `factor_ids`, `source_ids`).

### 6.2 Option A (recommended): replace the six two-era USA rows with five era rows built from the yearly series

Keep the present structure (one unit-1 share per tier, ash fly + bottom + slag combined, region `USA`), but derive the values from the survey tables and the mapping of §4, in five eras that follow the data rather than the old two-era chart reading. New IDs coal:0080–0094 (5 eras × 3 tiers); coal:0074–0079 are kept in the registry and marked RETIRED (D72) in their notes, following D70, because documents cite them by id and the tests reference the numbers.

Rule for each era: dispersed central = S1 production-weighted mean over the years with category detail; dispersed low = lowest annual S2; dispersed high = highest annual L; reisolated central = mining as a share of production, low 0, high = highest annual value (placeholder 0.003 / 0.02 before 1990, where no category data were read); impounded central = 1 − dispersed − reisolated (so central values sum to 1.000), impounded low/high = 1 − dispersed high − reisolated high and 1 − dispersed low.

| Era | Dispersed low / central / high | Reisolated low / central / high | Impounded low / central / high | Basis |
|---|---|---|---|---|
| 1966–1989 | 0.09 / 0.21 / 0.28 | 0 / 0.003 / 0.02 | 0.70 / 0.790 / 0.91 | L only (no category detail read before 1990), low lowered 0.03 for undetected disposal-like uses; reisolated placeholder |
| 1990–1999 | 0.25 / 0.29 / 0.35 | 0 / 0.010 / 0.02 | 0.63 / 0.703 / 0.75 | S1 from three detail years (1994, 1995, 1999) plus 2000 not in era |
| 2000–2009 | 0.24 / 0.36 / 0.46 | 0 / 0.017 / 0.03 | 0.51 / 0.628 / 0.76 | S1 from ten detail years |
| 2010–2015 | 0.23 / 0.38 / 0.52 | 0 / 0.030 / 0.04 | 0.44 / 0.592 / 0.77 | S1 from six years |
| 2016–2025 | 0.45 / 0.53 / 0.68 | 0 / 0.008 / 0.03 | 0.30 / 0.467 / 0.55 | S1 from eight years (2018 has no category table; 2025 carries 2024) |

Compared with the present rows: 1991–2009 central 0.33 becomes 0.29 (1990s) and 0.36 (2000s); 2010–2025 central 0.55 becomes 0.38 (2010–15) and 0.53 (2016–25); reisolated central 0 becomes 0.008–0.030 (it was an unsupported zero). Uncertainty: the bounds above combine year-to-year variation, mapping choice (L, S1, S2) and the survey's extrapolation. I did not add an extra margin for the extrapolation error (ACAA states none). The low bound for 2016–2025 assumes 2023–24 pond-closure reporting is right; if the 2024 figure is incomplete (§5.3) the central is about 0.03 too high.

Sources for the `source_ids` column: S0214 (series umbrella), S0255–S0259 (§6.7), S0213 and S0215 as now.

### 6.3 Option B: also split fly from bottom ash + slag

The residue types allow it: `residue_types.csv` has `coal_fly_ash` and `coal_bottom_ash` (the latter is "bottom ash and slag"), and the concentration factors already differ by residue. But the share selector in `coal.py` matches `residue_type=None`, so a split row set (residue_type filled) is invisible to the code and a split can only become active after `coal.py` selects shares by residue and the spec step 3 (§5) is changed. The values, ready if wanted (same rule):

| Stream and era | Dispersed low / central / high | Reisolated central (high) | Impounded central |
|---|---|---|---|
| Fly 1966–1989 | 0.05 / 0.16 / 0.24 | 0.003 (0.02) | 0.841 |
| Fly 1990–1999 | 0.20 / 0.25 / 0.34 | 0.012 (0.02) | 0.742 |
| Fly 2000–2009 | 0.23 / 0.33 / 0.45 | 0.017 (0.03) | 0.650 |
| Fly 2010–2015 | 0.23 / 0.36 / 0.54 | 0.035 (0.04) | 0.603 |
| Fly 2016–2025 | 0.49 / 0.59 / 0.78 | 0.009 (0.03) | 0.406 |
| Bottom + slag 1966–1989 | 0.18 / 0.34 / 0.43 | 0.003 (0.02) | 0.661 |
| Bottom + slag 1990–1999 | 0.31 / 0.41 / 0.45 | 0.004 (0.01) | 0.583 |
| Bottom + slag 2000–2009 | 0.28 / 0.43 / 0.52 | 0.017 (0.06) | 0.551 |
| Bottom + slag 2010–2015 | 0.26 / 0.43 / 0.51 | 0.016 (0.03) | 0.557 |
| Bottom + slag 2016–2025 | 0.20 / 0.35 / 0.52 | 0.006 (0.02) | 0.642 |

This is 30 rows and the practical value is nil until the US branch (option C) exists. I recommend writing the split only when the code is ready.

### 6.4 Option C: make the US rows active (not recommended now)

Two parts: (i) a US ash tonnage driver from ACAA production (fly + bottom + slag, 1966–2024, exact) as `coal_ash_power_t` and `coal_fly_ash_t` for `USA`; (ii) a `USA` branch in `coal.py` with the world rows becoming a rest-of-world residual (the stream already uses a rest-of-world residual for production and mining, D58). This is a real model change (new activity rows, spec section, tests, benchmark re-baselining) and the ACAA production is partly EIA-derived, so it should be its own decision, after A. A side result for that decision: ACAA fly + bottom + slag production divided by the model's US coal consumption is 7–9 % (1970: 6.9 %, 1980: 9.2 %, 1990: 7.5 %, 2000: 7.6 %, 2010: 8.4 %, 2020: 7.4 %), and divided by the "total coal burn by domestic utilities" printed on the 1987–93 sheets (717.9–814.0 Mst) it is 8.4–9.6 %. This is below the 12 % ash yield used in the activity builder (`coal_ash_power_t`), and it bears on the open flag G18 (15 % vs 12 %). It is one country with low-ash Powder River coal and **does not** transfer to the world. It is noted here because it is the only independent US check the archive offers.

### 6.5 Should the US series tighten or inform the world bounds (coal:0040–0048)? No numeric change.

Every proposed US era band lies inside the corresponding XWL band, so the data are consistent with the world rows but cannot narrow them:

| Era | XWL dispersed low / central / high | US dispersed (option A) | XWL reisolated (central, high) | US reisolated |
|---|---|---|---|---|
| 1800–1989 | 0.05 / 0.141 / 0.40 | 0.09 / 0.21 / 0.28 (1966–89) | 0 / 0.4 | 0.003 (0.02) |
| 1990–2009 | 0.096 / 0.40 / 0.66 | 0.25 / 0.29 and 0.24 / 0.36 | 0 / 0.062 | 0.010–0.017 |
| 2010–2025 | 0.14 / 0.47 / 0.92 | 0.23 / 0.38 and 0.45 / 0.53 | 0.062 / 0.40 | 0.008–0.030 |

Reasons not to tighten: the world lows (India 9.6 % in 1996–97, 14 % in 2010) and highs (China 66–68 %, India 92 %, EU-15 91 %) come from other fleets that ACAA does not cover; the US share of world power ash fell from 27 % (1970) through 20 % (2000), 15 % (2010) and 9 % (2015) to about 5 % (2020–24) on the activity builder's tonnage (so the "about 10 % of world power ash" in the notes of coal:0043–0048 is true only around 2015). A weighted US + rest-of-world decomposition would need the rest-of-world shares, which this archive does not supply.

What the notes of coal:0040–0048 should change (text only; **do not** add S0214 or the new S-numbers to the `source_ids` of these rows, because `coal.py` copies `source_ids` onto the output rows and that would alter output):

1. Remove the stale "ACAA (S0214) unreachable" clause (it is now read).
2. 1800–1989: say that the ACAA table gives US total-ash use of 12–28 % (1966–89) and 31 % in 1990, so the 0.40 high is not a US value (it is the S0001 Fig. VII graph reading) and is kept only for non-US practice; the 0.05 low is below every US observation and kept for non-US fleets.
3. Replace "about 10 % of world power ash" with the era figures above.
4. 2010–2025: replace the sentence "US ACAA 2024: 67.7 % used" with the series (fly + bottom + slag 39 % in 2010–11 to 68 % in 2024) and the pond-closure/harvested-ash caveat.

I could not source an independent estimate of European or Indian utilisation before 1990 from this archive, so the question of whether the pre-1990 world high of 0.40 is too low for Europe is not answered here (it is likely not too high).

### 6.6 Option D (activity series for the use fraction): not recommended

A series such as `us_fly_ash_use_fraction` (annual, 1966–2024, unit `1`) would give smooth annual shares without era steps, but (i) every driver is still world-only so it would be equally inert; (ii) factor rows sharing a `factor_id` are treated as fully correlated in the factor uncertainty (SCHEMA §4.9), which is the right treatment of a shared mapping error, while 59 independent annual activity values would not carry it; (iii) the registry's role is to hold shares with provenance, and activity series hold quantities; (iv) the step artefacts of era rows are already documented and accepted (COAL_SPEC §12.13). The one ACAA quantity that is a proper activity series is US production (option C).

### 6.7 Impact on current outputs, tests and specs

- **Current outputs:** none. No `data/streams/coal.csv` row, `factor_ids` or `source_ids` changes under A or B (US rows inert, XWL rows untouched). The notes-only edit to coal:0040–0048 changes `data/factors/coal.csv` text, not outputs.
- **Tests that would change (to be confirmed by running the suite):** the ID ranges 74–79 hard-coded in `test_no_usa_route_shares_in_world_rows` and `test_usa_shares_not_used_for_world_rows` become 74–94 (or all `region == USA` rows); `test_usa_share_edit_does_not_change_world_rows` edits coal:0077, which is still valid if the row is retained (RETIRED) but should be pointed at a live row such as coal:0088; any registry/validator count or "all rows used" checks keyed to the old six (none found in `test_coal.py` by search; the oracle file `coal_oracle.py` does not mention coal:0074–0079). Validator rules for factors (low ≤ central ≤ high; years in order; unit-1) are met by the proposed rows.
- **Spec sections:** COAL_SPEC §5 step 3 (the sentence "The `USA` shares (`coal:0074`–`0079`) are inert…" becomes `coal:0074`–`0094`); §10 (bullet "The US route shares and the ACAA series are not applied to the world"); the factor notes (`research/coal/factors_notes.md`, item 15 of the choices list and gap G13, which says ACAA gave no pre-1991 years: now it does). D72 itself, one line, plus a pointer from COAL_SPEC §12.17. With option B, §5 steps 3 and the test oracle would also change (residue-keyed share selection).
- **Benchmarks (§9 / `research/coal/benchmarks.md`):** none use the US shares.

### 6.8 Proposed `data/sources.csv` entries (not applied; IDs S0255–S0259 are unused anywhere in the repository)

URLs: all documents were supplied as files; the public page is the ACAA reports page already used for S0214, so it is repeated and `access` is `open` with a copy held.

| source_id | short_cite | full_citation | url | year | type / rank | access | licence | notes |
|---|---|---|---|---|---|---|---|---|
| S0255 | ACAA 1966–1976 byproduct history | American Coal Ash Association (n.d.; c. 1978). Ash collection and utilization, 1966–1976: history of the coal combustion byproduct survey (fly ash, bottom ash, boiler slag, millions of short tons produced and used). ACAA. | https://acaa-usa.org/publications/production-and-use-reports/ | 1978 | grey / 5 | open | restricted | Date of issue not printed; single-page table. First year with data 1966 (boiler slag from 1968). Read visually. |
| S0256 | ACAA 1977–1986 ash collection and utilization sheets | National Ash Association / American Coal Ash Association (1978–1987). Ash Collection & Utilization, annual sheets 1977–1986 (with Comparative Results tables). | same | 1987 | grey / 5 | open | restricted | Compiled by the National Ash Association (and Edison Electric Institute 1977–79). Million short tons, 0.1–0.001 precision. 1983 production revised in the 1984+ sheets. |
| S0257 | ACAA 1987–2001 CCB/CCP production and use sheets | American Coal Ash Association (1988–2002). Coal Combustion By-product / Product (CCB/CCP) Production and Use, annual sheets 1987–2001. | same | 2002 | grey / 5 | open | restricted | Exact short tons by type; FGD material undivided; 1991 rounded to 50,000 short tons; 1996–1998 use totals by OCR with arithmetic check. |
| S0258 | ACAA 2002–2024 CCP Production and Use Survey Reports | American Coal Ash Association (2003–2025). Coal Combustion Product (CCP) Production & Use Survey Report, annual, 2002–2024, with use by application (15–17 categories). | same | 2025 | grey / 5 | open | restricted | Respondent coverage 30–68 %, rest extrapolated (EIA); 2024 production from the Ash Mart. 2007 and 2009 revised; 2018 rotated in the file. |
| S0259 | ACAA 2024 release and 1966–2013 fly-ash compilations | American Coal Ash Association (2025-12-04). Coal ash recycling rate increased in 2024 as ash harvesting continued rapid growth (news release); and ACAA fly ash production and use 1966–20xx compilation tables (2009–2013 editions). | same | 2025 | grey / 5 | open | restricted | Release: 72 % recycled in 2024; harvested-ash caveat. Compilations used only as cross-checks (2002, 2009 differences, §2.3). |

Also to update (not applied): **S1258** ("ACAA 1987 data sheet", currently `inaccessible`) is now held in substance (the 1987 sheet is `ACAA-CCP-Svy-1987.pdf`; the 1966–1987 series is in S0255–S0257): set `access` to `open` and say the 1966–1987 series is now read from the sheets directly (the S1250 Tables B.4-2 to B.4-5 figures quoted in its notes, 22.9 Mt in 1966 to 62.5 Mt in 1987 and 12.1 % to 26.5 % utilised, agree with the ACAA sheets once converted: 25.2 Mst = 22.9 Mt in 1966, 68.9 Mst = 62.5 Mt in 1987, 12.1 % printed for 1966 (12.3 % computed) and 26.5 % for 1987). **S0214** notes: replace "Not provided: pre-1991 years…" with the actual coverage in §1.2.

---

## 7. Inaccessible, unreadable or unverified items

- No file was wholly unreadable. Every PDF opened.
- **Text-layer defect:** `2007_ACAA_CCP_Survey_Report_Form(09-15-08).pdf` page 1, use row 9 (blasting grit/roofing granules): numbers missing from the text layer; read from the rendered page.
- **Rotated:** `2018-Survey-Results.pdf` page 1 is rotated 90°; production and use totals were read after rotation. The 2018 category rows were not transcribed.
- **OCR only (numbers verified by arithmetic and printed percentages, not digit by digit):** use totals in `ACAA-CCP-Svy-1996.pdf`, `-1997.pdf`, `-1998.pdf` (page 1). Production figures of the same sheets were read visually.
- **Rounded at source:** `ACAA-CCP-Svy-1991.pdf` (nearest 50,000 short tons); 1977–1979 to 0.1 Mst.
- **Not transcribed:** use-category tables for 1966–1993 and 1996–1998, and for 2018; internal/external splits other than the 1994–95 key rows; EPA-region PDFs; all chart data.
- **Unresolved:** the 2007 corrected utilisation rate (44.81 %, §2.3); the 2009 bottom ash production/percentage inconsistency; whether the 2024 pond-closure near-zero is a reporting change (§5.3); the harvested-ash volumes (ACAA study due 2026, not yet in the archive); the 2025 survey (not in the archive; `S0215` as cited in the repository is a trade-press summary of the 2024 figures).

## 8. Items for the main session's memory (from this task, for your decision)

- ACAA series files and the rebuild script live in `research/coal/` (`acaa_series.csv`, `acaa_uses.csv`, `acaa_build_series.py`), source of truth for any US ash route-share work.
- Steve's decision is pending on D72 (option A recommended; B and C deferred).
