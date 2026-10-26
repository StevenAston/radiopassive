# research/activity: Task 1.9 activity data spine

Builders in `scripts/` write the eleven `data/activity/*.csv` files plus `sources_task19.csv`. Paths are relative to the repository root; nothing is hard-coded.

## Run

    python3 research/activity/scripts/fetch_inputs.py              # large downloads, once (OWID energy, FAOSTAT forestry, EIA INTL)
    python3 research/activity/scripts/run_all.py --mirror /path/to/usgs.140            # writes research/activity/out/
    python3 research/activity/scripts/run_all.py --mirror /path/to/usgs.140 --write    # writes data/activity/ and sources_task19.csv

* Builders never write into `data/activity/` unless `--write` is given.
* `--raw DIR` (or `$RADIO_RAW`) moves the raw folder; default `research/activity/raw/`.
* `--mirror` (or `$USGS_MIRROR`) is the root of Steve's USGS mirror (`usgs.140/`, containing `derived/csv/...` and `files/...`). It lives outside the repository and is needed only by `build_comm`, `build_prices` and `make_sources2`.
* `note_registry.json` holds the long notes that the CSVs abbreviate as `[Nxxx, see research/activity/note_registry.csv]`; it is append-only so N-numbers stay stable (`note_registry.csv` is the readable copy: columns note_id, text). Rewrite the CSV from the JSON after any run that adds notes.
* Verified: a second run without `--write` reproduces every file in `data/activity/` and `sources_task19.csv` byte-identically (checked with `cmp`).

## Builders and outputs

| script | writes | inputs (raw/ unless noted) |
|---|---|---|
| build_elec | electricity_generation | eps.csv (OWID electricity by source), irena_*.csv, EIA geothermal (eia_annual.json) |
| build_coal | coal | coal-production-by-country.csv, owid-energy.csv, eia_annual.json, T02.06 / T07.02A / t0602 (EIA MER), coal1853.xls (DESNZ), eps.csv; writes eta_us.json |
| build_og | oil_gas | oil/gas-production-by-country.csv, owid-energy.csv, eta_us.json (from build_coal), T04.03, wells_*.xls, eia_annual.json |
| build_u | uranium | min/Uranium__Mine.csv, wna.html, `redbook_u.py` (hand-transcribed Red Book 2006 table) |
| build_nuc | nuclear | rds2_rows.json (from `rds2_parse.py` on RDS-2 No. 45), eps.csv |
| build_cap | capacity_additions, planning_parameters | irena_*.csv, eia_annual.json, rds2_rows.json, reads nuclear.csv from the output folder (run after build_nuc) |
| build_comm | commodity_production | min/*.csv (OWID minerals), DS140 and Minerals Yearbook files from the mirror |
| build_prices | commodity_prices | DS140 from the mirror |
| build_bio | biomass | fao/x/Forestry_E_All_Data_(Normalized).csv, un/undata.csv |
| build_peat | peat | un/undata.csv |
| make_sources, make_sources2 | sources_task19.csv | DS140 workbooks (mirror) for the compiler lines |

Helpers: `lib.py` (Out class, paths, note registry), `common.py`, `ds140.py` (DS140 CSV reader), `ds140_comm.py`, `ree_myb.py` (Minerals Yearbook rare-earth tables), `eia_extract.py` (INTL.txt to eia_annual.json), `irena_fetch.py`, `fetch_minerals.py`, `rds2_parse.py`.

## Raw inputs

Stored in `raw/` (each below 5 MB): EIA MER tables T02.06, T04.03, T07.02A, t0602 (= Table 6.2; https://www.eia.gov/totalenergy/data/browser/?tbl=T06.02 and siblings); OWID grapher CSVs `eps.csv` (https://ourworldindata.org/grapher/electricity-production-by-source), `coal-/oil-/gas-production-by-country.csv`; DESNZ `coal1853.xls`; EIA wells tables; WNA table `wna.html`; IRENA PxWeb extracts `irena_*.csv` (re-fetch with `irena_fetch.py`) and `irena_meta.json`; OWID minerals `min/*.csv` (re-fetch with `fetch_minerals.py`); UN energy statistics `un/undata.csv` (SDMX, query in `notes.md` section 7); `RDS-2-45_web.pdf`, `rds2.txt` (pdftotext -layout of it) and `rds2_rows.json`; `fao/x/Forestry_E_AreaCodes.csv`.

Not stored (see `fetch_inputs.py`, ignored by git): `owid-energy.csv`, FAOSTAT `Forestry_E_All_Data_(Normalized).csv`, EIA `INTL.zip` and the derived `eia_annual.json`. Not downloadable by script: the NEA Red Book 2006 page images (transcribed into `redbook_u.py`) and the licence-restricted or 403 sources listed in `notes.md` section 5 (Energy Institute Statistical Review).

Mirror files used: `derived/csv/s3fs-public/media/files/ds140-*.xlsx/*.csv` (25 workbooks) and `files/mineral-pubs/rare-earth/{740494.pdf,740499.pdf,rareemyb03.xls,myb1-2008-raree.xls,myb1-2013-raree.xls}`, `files/s3fs-public/atoms/files/myb1-2018-raree-adv.xlsx`, `files/s3fs-public/media/files/myb1-2022-raree-ert.xlsx`.
