# The Second-Hour Tax

## Randomized Test Order and Measured Comparative Advantage in PISA 2025

This repository is the complete, data-free replication package for an empirical
study of whether placing the PISA 2025 *Learning in the Digital World* (LDW)
assessment in the second rather than the first testing hour changes measured LDW
performance and students' measured comparative advantage across domains.

The design compares three mirrored booklet pairs:

| Mirrored pair | LDW in hour 2 | LDW in hour 1 | Other domain |
|---|---:|---:|---|
| Science–LDW | Book 5 | Book 6 | Science |
| Reading–LDW | Book 9 | Book 10 | Reading |
| Mathematics–LDW | Book 11 | Book 12 | Mathematics |

The headline analysis contains 205,114 students in 84 participating systems and
retains only school × paired-domain strata in which both booklet orders occur.
All estimates are calculated separately by system using final student weights,
80 BRR-Fay replicate weights, and all ten plausible values. System estimates are
then synthesized using fixed- and random-effects meta-analysis, with modified
Hartung–Knapp, equal-system, trimmed-mean, sign-test, prediction-interval, and
leave-one-system-out checks.

## Headline findings

- Moving LDW to hour 2 lowers measured LDW performance by **8.32 PISA points**
  (SE 0.45) in the fixed-effect synthesis and **9.00 points** (SE 0.76) in the
  random-effects synthesis.
- The standardized random-effects estimate is **−0.093 SD** (SE 0.007); 78 of
  84 system estimates are negative and 39 are individually negative at the
  5 percent level.
- The conclusion is unchanged under modified Hartung–Knapp inference, alternative
  cross-system weighting rules, and every leave-one-system-out re-estimation.
- Requiring two students in each order within every retained stratum preserves
  all 84 systems and yields −8.30 points. Thresholds of five or ten sharply alter
  system composition and are reported as estimand-scope diagnostics, not as
  preferred specifications.
- The mirrored design moves both sides of measured comparative advantage. When
  LDW is second, its paired conventional domain is first: the LDW effect is
  negative while the paired-domain effect is positive for science, reading, and
  mathematics.
- Second-hour placement is associated with lower normalized credit, less time,
  fewer actions, and more responses coded as disengaged. Item exposure itself is
  unchanged.
- The adaptive-versus-linear science appendix finds neither a detectable average
  effect nor a detectable interaction with socioeconomic status.

These are effects of the **randomized order/position bundle**. They should not be
described as pure biological fatigue effects: position, warm-up, cross-domain
priming, and any position-sensitive scaling or engagement response move together.

## Data

The pipeline downloads three official OECD PISA 2025 public-use archives:

1. student questionnaire and plausible-value data;
2. cognitive-design data; and
3. LDW cognitive-item/process-summary data.

The raw files are not redistributed. Users must review and accept the OECD PUF
terms before running the downloader. The release used for this package was pinned
on 12 September 2026 by exact byte count and SHA-256 checksum. See
[`docs/data-source-ledger.md`](docs/data-source-ledger.md).

## One-command reproduction

### Requirements

- Python 3.12;
- approximately 22 GB of free disk space during conversion;
- at least 8 GB RAM recommended;
- `unzip` available on the system path as a fallback for ZIP compression methods
  not supported by the local Python build; and
- internet access for the first run.

Create an isolated environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
```

Review the OECD PUF access terms at
<https://survey.oecd.org/index.php?r=survey/index&sid=197663>. Then run:

```bash
PISA_ACCEPT_TERMS=1 ./run_all.sh
```

The command downloads and verifies the three archives, extracts one large SPSS
file at a time in a temporary directory, builds compact Parquet datasets,
constructs the analysis samples, reruns every analysis, creates all tables and
figures, executes unit tests, and checks the reproduced estimates against the
audited release.

If verified archives are already present in `data/raw/`, skip the network step:

```bash
PISA_SKIP_DOWNLOAD=1 ./run_all.sh
```

The complete run may take tens of minutes, depending mainly on download speed,
disk throughput, and CPU. It is safe to rerun: generated processed datasets and
outputs are rebuilt deterministically from the pinned archives.

## Validate the archived results without downloading data

The released outputs can be checked immediately:

```bash
python code/06_diagnostics/test_estimators.py
python code/06_diagnostics/validate_outputs.py
```

The first command exercises the custom fixed-effect, meta-analysis,
Hartung–Knapp, and multiple-testing routines on synthetic data. The second checks
sample counts, headline coefficient ranges, design support, meta-analytic
robustness, balance, appendix conclusions, and the presence of all final table
and figure families.

## Repository map

```text
code/00_download/    terms gate, resumable downloader, hashes, archive tests
code/01_clean/       SPSS-to-Parquet conversion and derived variables
code/02_construct/   mirrored-order/adaptive samples and design audit
code/03_analyze/     survey/PV estimators and eight empirical analyses
code/04_tables/      CSV, Markdown, and LaTeX tables
code/05_figures/     PNG and PDF figures
code/06_diagnostics/ unit tests, release validation, package manifest
config/              explicit design map and survey settings
data/                empty data directories; all microdata are ignored
docs/                source ledger, identification audit, variable dictionary
paper/               formal methodology and concise empirical results
output/              released tables, figures, and non-sensitive logs
environment/         pinned Python dependencies and as-run session information
```

## Output index

Main tables:

- `table_01_main_effect`: LDW second-hour effect;
- `table_02_comparative_advantage`: mirrored LDW and conventional-domain effects;
- `table_03_balance`: predetermined-covariate balance;
- `table_04_process`: response and process-summary outcomes;
- `table_05_heterogeneity`: learner-type interactions with BH adjustment;
- `table_a1_adaptive_science`: adaptive-versus-linear science appendix;
- `table_a2_meta_robustness`: alternative cross-system summaries and inference;
- `table_a3_support_sensitivity`: stricter within-stratum overlap thresholds;
- `table_a4_design_audit`: identifiers, weights, merges, and allocation support;
  and
- `table_a5_booklet_counts`: eligible-form counts by mirrored pair and order.

Every table is released in CSV, Markdown, and LaTeX. Figures are released in PNG
and vector PDF. The machine-readable JSON inputs and system-level estimates used
to create them are also included. Appendix Figure A1 reports leave-one-system-out
estimates; Appendix Figure A2 reports support-threshold sensitivity.

## Interpretation and scope

The package supports a measurement claim: a student's measured proficiency and
cross-domain ranking depend materially on where the domain appears in the test.
It does not identify a persistent loss of human capital, a classroom treatment
effect, or a pure fatigue mechanism. The public LDW file exposes scored responses
and item-level summary fields, not the complete tutorial/feedback/strategy event
logs anticipated in future OECD LDW reporting. Process analyses are therefore
mechanism-consistent diagnostics rather than a decomposition of self-regulated
learning.

See [`paper/methodology.md`](paper/methodology.md) for the estimands and equations,
[`docs/identification-audit.md`](docs/identification-audit.md) for the claim audit,
[`docs/novelty-map.md`](docs/novelty-map.md) for the nearest-neighbour literature,
and [`docs/deviations.md`](docs/deviations.md) for changes from the feasibility
blueprint.

## Citation and license

Before public circulation, replace the clearly marked author placeholder in
`CITATION.cff`. Code and original documentation are released under the MIT License.
OECD data are not covered by that license and remain governed by the OECD PUF
terms of use.
