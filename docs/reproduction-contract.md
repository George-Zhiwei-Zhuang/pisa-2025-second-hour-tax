# Reproduction contract

## Objective

Starting from the three pinned OECD PISA 2025 archives and this repository,
`PISA_ACCEPT_TERMS=1 ./run_all.sh` must reconstruct the strict analysis samples,
system-level estimates, ten final table families, six final figure families, and
a passing release-validation report without manual data manipulation.

## Inputs

| Input | Required state |
|---|---|
| Student PUF | Exact size/hash in `docs/data-source-ledger.md` |
| Cognitive PUF | Exact size/hash in `docs/data-source-ledger.md` |
| LDW PUF | Exact size/hash in `docs/data-source-ledger.md` |
| Software | Python 3.12 plus `environment/requirements.txt` |
| User action | Review and accept the OECD PUF terms |

## Pipeline stages

| Stage | Entrypoint | Contracted product |
|---|---|---|
| Acquire | `code/00_download/download_data.py` | Three complete archives and local download manifest |
| Verify | `code/00_download/verify_data.py` | Exact hashes plus archive-member tests |
| Clean | `code/01_clean/prepare_all.py` | Typed student, cognitive, and LDW Parquet datasets |
| Construct | `code/02_construct/*.py` | Strict main/adaptive samples, frozen counts, and design-support audit |
| Analyze | `code/03_analyze/*.py` | System estimates, meta-analytic summaries, influence and support sensitivity |
| Present | `code/04_tables/make_tables.py`, `code/05_figures/make_figures.py` | Ten table and six figure families |
| Diagnose | `code/06_diagnostics/*.py` | Five unit tests, 54 release checks, manifest |

## Frozen release targets

The validator intentionally uses tight ranges rather than exact floating-point
equality so that harmless numerical-library variation does not create false
failures. Release 1.1.0 must satisfy at least:

- strict main sample: 205,114 students and 84 systems;
- strict adaptive sample: 454,324 students;
- fixed-effect LDW order effect: between −8.5 and −8.1 points;
- fixed-effect LDW order effect: between −0.095 and −0.091 SD;
- 78 negative system estimates, 39 individually significant and negative;
- negative LDW and positive paired-domain effects in all three mirrored pairs;
- no balance-test p-value below 0.10;
- adaptive main and ESCS-interaction p-values above 0.10;
- random-effects normalized-credit effect between −2.0 and −1.7 pp;
- random-effects total-time effect between −18 and −15 percent; and
- 12 released moderator estimates with the expected multiplicity pattern;
- zero duplicate IDs and nonpositive final weights in the audited design sample;
- a modified Hartung–Knapp interval that excludes zero;
- leave-one-system-out random-effects estimates between −9.3 and −8.5 points;
- all 84 systems retained at a two-student-per-order threshold, with an effect
  between −8.6 and −8.0 points; and
- explicit attrition to 32 and 11 systems at thresholds of five and ten.

## Clean-room acceptance test

A handoff copy passes if it contains no `.sav`, `.parquet`, or OECD `.zip` files,
yet the following commands succeed before any data download:

```bash
python code/06_diagnostics/test_estimators.py
python code/06_diagnostics/validate_outputs.py
sha256sum -c MANIFEST.sha256
```

After the user supplies the PUFs through the documented downloader, the complete
`run_all.sh` path must pass. Logs may differ in timestamps, and PNG/PDF bytes may
vary across graphics backends; the underlying CSV/JSON estimates are the
scientific objects of record.

## Failure policy

- Hash mismatch: stop; do not silently analyze a changed OECD release.
- Missing treatment support: stop for the affected system/outcome rather than
  extrapolating across schools or booklet pairs.
- Missing required PV or replicate-weight family: stop the corresponding main
  analysis.
- Release assertion failure: inspect upstream data/version changes before
  relaxing any threshold.
- New analysis decision: record it in `docs/deviations.md` and increment the
  package version.
