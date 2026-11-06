# Raw-input archive (D72, zpaqfranz part)

Status: approved by Steve 2026-11-06 as the second half of D72 (the first half, gzipped stream outputs, is LIB_SPEC §11). DVC was considered and rejected. This file is the contract for the code-writer of `research/activity/scripts/raw_manifest.py`, for the spec-blind test-writer, and the runbook Steve follows on Windows.

**Problem.** Two inputs are not versioned by git: the large downloads in `research/activity/raw/` (about 580 MB, listed in `research/activity/raw/.gitignore`, fetched by `research/activity/scripts/fetch_inputs.py`), and `import/` (Steve's PDFs and spreadsheets, about 17 MB). Upstream sources revise or remove files, so a commit cannot be rebuilt unless the exact raw files it used can be recovered.

**Solution.** Two parts:

1. **A tracked manifest** pins the exact bytes. `research/activity/raw/MANIFEST.csv` lists every untracked input file with its size and SHA-256. Any commit therefore names the raw files it was built from.
2. **An append-only zpaqfranz archive** on Steve's Google Drive holds every version of those files. zpaq archives are journalling: each `add` appends a new dated version and never rewrites earlier ones, and identical content is deduplicated.

**`zpaq` means zpaqfranz.** On Steve's Windows machine zpaqfranz is installed and aliased as `zpaq`, and every command in this file is written that way. Original zpaq 7.15 and zpaqfranz differ in some commands and flags, so before relying on the commands, confirm which binary the alias runs: `zpaq` with no arguments must print the **zpaqfranz** banner and its version. If it prints the original zpaq banner instead (`zpaq v7.15 ...`), fix the alias before going further. Write the version into §5.3 when confirming the flags. If the alias is a `doskey` macro, it only works when typed at the prompt, not inside `.bat` files. Scripts should call `zpaqfranz.exe` by name.

---

## 1. What is archived

| Included | Excluded |
|---|---|
| Every file under `research/activity/raw/` that is **ignored and untracked** by git: today `INTL.txt`, `INTL.zip`, `eia_annual.json`, `eta_us.json`, `owid-energy.csv`, `fao/forestry.zip`, `fao/x/*` and any other `*.zip`. `ember.csv` is listed in `.gitignore` but absent on 2026-11-05; it is archived whenever it exists. | Every **tracked** file, including tracked files that happen to match an ignore pattern. Git already stores them. |
| Every file under `import/` that is ignored and untracked. | `MANIFEST.csv` itself (tracked), `.gitignore` files, and anything outside the two roots. |
| | Untracked files that are **not** ignored (they are meant to be committed; `check` reports them, see 4.3). |

Measured 2026-11-05: 11 ignored files in `research/activity/raw/`, 580.6 MB, SHA-256 of all of them in 5.5 s on the 2-core sandbox; `import/` holds 72 files, 17 MB.

**Repo check (do once).** No root `.gitignore` was found in the working copy reviewed on 2026-11-06. If `import/` is not already ignored in the real repo (`git check-ignore -v import/x` prints nothing), add the line `import/` to the root `.gitignore`. Otherwise the helper will treat `import/` files as "untracked, not ignored" and leave them out of the manifest.

---

## 2. Archive location and naming

- **One archive file**, for example `G:\My Drive\Radiopassive\radiopassive_raw.zpaq`. It is never hard-coded. Every command and script takes it from the environment variable `RADIOPASSIVE_ARCHIVE` or an explicit argument.
  - Set it once on Windows: `setx RADIOPASSIVE_ARCHIVE "G:\My Drive\Radiopassive\radiopassive_raw.zpaq"`. Open a new terminal afterwards; `setx` does not affect the current one.
- **Google Drive settings.** Mark the folder **"Available offline"** in Google Drive for desktop. An online-only placeholder forces a download before every append.
- **Upload size per update.** Drive for desktop uploads the whole changed file, not only the appended bytes. A small update to a large archive therefore re-uploads all of it.
  - *Alternative (not adopted; worth it once the archive passes about 1 GB):* zpaq **multi-part** naming, `radiopassive_raw_????.zpaq`. Each `add` writes a new numbered part and earlier parts never change, so Drive uploads only the new part. All parts must stay together, and they are read as one archive.
  - **Not certain:** that zpaqfranz handles `????` exactly like zpaq 7.15. Check with `zpaq h a` and a throwaway test before switching.
- **Don't run an `add` while Drive is still uploading the previous version.** Wait until Drive shows the file as synced. Never edit the archive from two machines.

---

## 3. When to archive

Run the procedure in 5.1 after any of these:

1. A `fetch_inputs.py` run (or any other fetch script writing to `research/activity/raw/`) that **changes** files. `raw_manifest.py check` exits 1 when anything changed. If it exits 0, there is nothing to archive.
2. Files added to, changed in or removed from `import/`.
3. Before a commit that changes `MANIFEST.csv`. The archive version must exist before the commit that pins it (see 5.2).

`add` is cheap when nothing changed (deduplication), so running it unnecessarily is harmless.

---

## 4. The manifest and its helper

### 4.1 `research/activity/raw/MANIFEST.csv` (tracked)

- **Format:** UTF-8 without BOM, LF line endings, comma-separated, written with Python `csv.writer(lineterminator="\n")`, header first.
- **Columns, in this order:** `path,size,sha256,fetched`
  - `path`: repo-relative POSIX path, such as `research/activity/raw/fao/x/Forestry_E_Flags.csv` or `import/acaa/2019.pdf`.
  - `size`: the size in bytes, as a decimal integer.
  - `sha256`: 64 lowercase hex characters.
  - `fetched`: `YYYY-MM-DD`, the UTC date on which `write` first recorded this exact `(path, sha256)` pair (4.2).
- **Order:** rows are sorted by `path` in Python string order, which is code-point order. This equals the byte order of the UTF-8 path.
- **One row per file.** There are no rows for directories, and duplicate paths are not allowed.
- The manifest covers **both** roots. It lives under `research/activity/raw/` only because that folder is tracked; `import/` is not.

### 4.2 `research/activity/scripts/raw_manifest.py`

The helper uses the Python 3.11+ standard library only, plus the `git` executable. It runs on Windows, macOS and Linux and makes no network calls. It never runs zpaqfranz.

```
python research/activity/scripts/raw_manifest.py write [--root DIR] [--manifest PATH] [--include DIR ...] [--date YYYY-MM-DD]
python research/activity/scripts/raw_manifest.py check [--root DIR] [--manifest PATH] [--include DIR ...]
```

**Options:**

- `--root`: the git work tree. The default is the repository that contains the script.
- `--manifest`: the manifest path. The default is `<root>/research/activity/raw/MANIFEST.csv`.
- `--include`: a repo-relative directory, and the option can be repeated. The default is the two directories `research/activity/raw` and `import`. A missing included directory contributes no files and is not an error.
- `--date`: overrides "today (UTC)". It exists for tests and for back-filling.

**File set.** Run `git -C <root> ls-files --others --ignored --exclude-standard -z -- <include dirs>`. This gives the files that are untracked and ignored. Then drop the manifest file itself.

- Tracked files are never in this set, even if they match an ignore pattern. This is how git behaves, and it is what "excluded because git already has them" means.
- Symbolic links are skipped and listed on stderr as `skipped symlink <path>`.
- `--root` not being a git work tree, or `git` not being found, is a usage error (exit 2).

**Hashing.** SHA-256 over the file's bytes, read in 1 MiB chunks. Line endings are not converted, so the same file hashes the same on every OS.

**`write`:**

1. Build the rows for the current file set.
2. **`fetched`.**
   - If the existing manifest has a row with the same `path` **and** the same `sha256`, keep that row's `fetched`.
   - Otherwise (a new file, or changed content) set it to `--date`, or to today's UTC date if `--date` is not given.
3. Write the manifest atomically: to a temporary file in the same directory, then `os.replace`.
4. Print one line per added, changed or removed path (format as in `check`), then a summary line `N files, M bytes`.
5. Exit 0.

Two consequences:

- Running `write` twice with no file changes gives **byte-identical** output, whatever the date.
- An unreadable existing manifest is an error (exit 2). It is not silently replaced. To start over, delete the manifest file.

**`check`:**

1. Compare the current file set with the manifest by `path`, `size` and `sha256`. `fetched` is ignored.
2. Print one line per difference to stdout, sorted by path, in the form `<kind> <path>`:
   - `added`: the file is on disk but not in the manifest.
   - `changed`: the file is in both, but the size or sha256 differs.
   - `missing`: the file is in the manifest but not on disk.
3. Print a summary line: `check: A added, C changed, M missing` or `check: OK (N files)`.
4. Also print, as information that does not affect the exit code, one stderr line `untracked-not-ignored <path>` for each untracked file under the include directories that is **not** ignored.
5. **Exit codes:**
   - 0: no differences.
   - 1: one or more differences.
   - 2: a usage error, no git work tree, or a missing or malformed manifest (wrong header, bad row, duplicate path, or rows out of order).

`check` never writes anything.

### 4.3 Commands Steve runs (Windows, from the repo root)

**Initial snapshot (once):**

```bat
python research\activity\scripts\raw_manifest.py write
zpaq a "%RADIOPASSIVE_ARCHIVE%" research\activity\raw import -m3
zpaq l "%RADIOPASSIVE_ARCHIVE%" -all
git add research/activity/raw/MANIFEST.csv
git commit -m "D72: raw-input manifest"
```

**After a fetch or `import/` change:**

```bat
python research\activity\scripts\raw_manifest.py check
python research\activity\scripts\raw_manifest.py write
zpaq a "%RADIOPASSIVE_ARCHIVE%" research\activity\raw import -m3
git add research/activity/raw/MANIFEST.csv
git commit -m "Raw inputs refreshed (MANIFEST)"
```

- The `check` run is there to see what changed. Exit 1 is expected.
- The archive also captures tracked files under `research/activity/raw`, which is harmless: zpaq deduplicates them and they are small. Run the commands from the repo root, so that stored paths are relative and a restore lands in the right place.

---

## 5. Recording and restoring a snapshot

### 5.1 Order of operations (this is the rule that makes restore work)

1. Fetch.
2. Run `raw_manifest.py write`.
3. Run `zpaq a`.
4. Commit `MANIFEST.csv` (together with the build that used the files, or before it).

The archive version that holds the files is therefore always dated **at or before** the commit that pins them.

### 5.2 Restore the raw inputs of commit `<C>`

1. Check out the commit with `git checkout <C>`.
2. Find its commit date (UTC):
   ```bat
   git log -1 --format=%cd --date=format-local:"%Y-%m-%d %H:%M:%S" <C>
   ```
   Run `set TZ=UTC` first, so that `format-local` prints UTC.
3. List the archive versions with their dates:
   ```bat
   zpaq i "%RADIOPASSIVE_ARCHIVE%"
   ```
   Pick the **last version dated at or before** the commit date.
4. Extract that version into an empty scratch folder (`zpaq x` command below). Never extract straight over the work tree.
5. Copy the extracted `research\activity\raw\*` and `import\*` into the work tree.
6. Prove the files match:
   ```bat
   python research\activity\scripts\raw_manifest.py check
   ```
   Exit 0 means every byte matches the commit's manifest.
   - If `check` reports `changed` or `missing`, extract the previous or next version and try again.
   - If you have the manifest but not the date, compare a file's SHA-256 against the candidates directly (`certutil -hashfile <file> SHA256` on Windows) to find the right version.

The extract command:

```bat
zpaq x "%RADIOPASSIVE_ARCHIVE%" -until "2026-11-06 23:59:59" -to C:\scratch\raw_restore
```

`-until` also accepts a version number from the `i` listing, such as `-until 7`.

### 5.3 zpaqfranz commands and flags

Flags marked **check** come from zpaq 7.15 and zpaqfranz documentation as recalled on 2026-11-06, and have not been run here. Before first use, confirm the binary (no-argument banner, see the top of this file), then confirm each flag with `zpaq h <command>` (for example `zpaq h a`, `zpaq h x`) or `zpaq h h` for the full help, and do a throwaway add/extract on a small folder.

| Purpose | Command | Confidence |
|---|---|---|
| Append a version | `zpaq a <arch> <paths...>` | certain (zpaq `a` = add, append-only) |
| Compression level | `-m3` (`-m1` fastest … `-m5` best; the zpaqfranz default is `-m1`) | **check** the default. `-m3` is a suggestion: most of the bytes (`INTL.txt`, `eia_annual.json`, the FAO CSV) are text; the zips are already compressed. |
| List the versions with dates | `zpaq i <arch>` | **check**. Some versions use `l <arch> -all` for a per-version file list. |
| List the files of every version | `zpaq l <arch> -all` | **check** |
| Extract as of a date or version | `zpaq x <arch> -until <date or N> -to <dir>` | **check** the date syntax (zpaq takes `YYYY-MM-DD HH:MM:SS`, and partial dates like `2026-11-06` mean the start of that day, so use the next day or a full timestamp to include versions added that day) and how `-to` maps stored relative paths. |
| Test archive integrity | `zpaq t <arch>` | **check** |
| SHA-256 of files on disk, to cross-check the manifest | `zpaq sum <paths> -sha256` | **check** (the flag name may differ); `certutil -hashfile <file> SHA256` is the built-in fallback. |

**Not used:** encryption (`-key`). If it is ever added, losing the password loses every version.

---

## 6. Done conditions and test items (for the spec-blind test-writer)

Tests go in `research/activity/tests/test_raw_manifest.py`, or in `pipeline/tests/test_raw_manifest.py` if research scripts have no test folder. They are written from §4 only. Each test builds a throwaway git repository in `tmp_path` with `git init`, a `.gitignore` and committed files, and runs the script as a subprocess with `--root tmp_path`. The tests are skipped if `git` is not on PATH. No network, and nothing outside `tmp_path`.

**A. File set.**

1. Ignored, untracked files under the include directories are listed. This includes files in ignored subdirectories (`fao/x/a.csv`).
2. A **tracked** file that matches an ignore pattern (force-added with `git add -f`) is not listed.
3. Untracked files that are not ignored are not listed, and `check` mentions them on stderr only (exit code unaffected).
4. Files outside the include directories, the manifest itself and `.gitignore` are not listed.
5. `--include` replaces the default roots, and a missing included directory is not an error.
6. A non-git `--root` gives exit 2.

**B. Content.**

1. The header is exactly `path,size,sha256,fetched`.
2. `size` equals `os.path.getsize`. `sha256` equals `hashlib.sha256(bytes).hexdigest()`. Check this with a known file, for example `b"abc\n"` gives `edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb`, and an empty file gives `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
3. Paths are POSIX and repo-relative, even on Windows.
4. Rows are sorted by code-point order. A test includes `B.csv`, `a.csv` and `fao/x.csv`, which gives `B` < `a` < `fao/...`.
5. The file has LF endings, no BOM and valid UTF-8, including a non-ASCII file name.
6. A CRLF text file hashes its raw bytes (no newline conversion).

**C. Determinism and `fetched`.**

1. Two `write` runs with no file changes and different `--date` values give byte-identical manifests.
2. A changed file gets the new `--date` while the other rows keep theirs.
3. A file that changes and then changes back to an earlier hash gets the current `--date`. Only the hash recorded in the existing manifest counts.
4. A deleted file's row disappears.
5. Creation order and mtimes do not affect the output.

**D. `check`.**

1. A clean tree gives exit 0 and `check: OK (N files)`.
2. A new ignored file gives `added <path>` and exit 1.
3. A modified byte, same size, gives `changed <path>`.
4. A deleted file gives `missing <path>`.
5. Several differences are printed sorted by path, one line each, and the summary counts are correct.
6. A changed `fetched` value only gives exit 0.
7. `check` never modifies the manifest (bytes and mtime unchanged).
8. A missing manifest, a wrong header, a malformed row, a duplicate path or rows out of order give exit 2.

**E. Safety.**

1. `write` over an unreadable or malformed manifest exits 2 and leaves it unchanged.
2. A symlink under an include directory is skipped with a stderr note (skip this test where symlinks cannot be created).

**Done when:**

- items A–E pass;
- `raw_manifest.py write` has been run on Steve's machine and `MANIFEST.csv` is committed;
- the first `zpaq a` has been made to `%RADIOPASSIVE_ARCHIVE%`;
- a test restore (5.2) of that version into a scratch folder makes `raw_manifest.py check` exit 0;
- the flags marked **check** in 5.3 have been confirmed or corrected in this file;
- `import/` is confirmed ignored in the real repo (§1).

## 7. Clarifications after the test round (orchestrator, 2026-11-06)
1. Self-exclusion: the manifest never lists **the manifest file in use** (the `--manifest` path when given) **nor the default `research/activity/raw/MANIFEST.csv`**.
2. `write` prints removed files with the kind `missing`, in the same format as `check`.
3. A malformed manifest (wrong header or field count, CRLF, uppercase or wrong-length sha256, unparseable `fetched` date, negative size) makes `check` and `write` exit 2 with a message naming the line.
4. `import/` is confirmed git-ignored in the real repository (`.gitignore` line `import/`).
