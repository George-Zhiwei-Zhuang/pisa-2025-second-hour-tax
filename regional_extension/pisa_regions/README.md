# PISA LDW second-hour effects by geographic region

This supplement answers whether the archived system-level randomized LDW test-order
effects differ across geographic regions. It reuses the complete system estimates
from `pisa_2025_second_hour_tax_replication_v1.1.0.zip`, retrieved on 10 October 2026.
It does not change the original paper or original replication archive.

## Run

From this directory, with the listed Python dependencies available:

```bash
python3 code/analyze_regions.py
python3 code/make_deliverables.py
```

The first command recreates every analytical table from the small archived inputs.
The second creates the report and the regional forest plot. It does not fetch
external data, submit information, or accept any data agreement.

## How to read the outputs

- `config/regions.json`: fixed M49 geographic classification and documented PISA overrides.
- `output/tables/system_region_crosswalk.csv`: all 84 systems, names, geographic
  groups, sample sizes, and the original estimates and variances.
- `output/tables/regional_main_sd.csv`: primary REML/mKH means and 95% confidence intervals.
- `output/tables/regional_pairwise_sd.csv`: all 66 pairwise comparisons, including raw
  p values, BH FDR q values and Holm familywise-adjusted p values.
- `output/tables/all_contrasts_alternative_methods.csv`: common-variance REML,
  separate-region DL/mKH, and equal-system Welch comparisons. Correction is applied
  within each method's family of 66 tests.
- `output/tables/regional_robustness_omnibus.csv` and
  `equal_system_welch_omnibus.csv`: omnibus regional-equality tests under the
  documented specifications.
- `output/tables/regional_mirrored_pairs*.csv`: independent regional syntheses
  within each conventional-domain pair. Direct point gaps retain their original
  joint variance. A standardized-gap confidence interval is not constructed from
  the two marginal standard errors because their covariance is unavailable.
- `output/tables/regional_process*.csv`: five secondary process outcomes.
- `docs/analysis_plan.md`: decisions, estimands and transparent analytic refinements.

Regional effects use standard deviations computed **inside each system** in the
original analysis. A positive `difference_a_minus_b` means the LDW-second effect
is less negative in A, i.e., a smaller second-hour penalty. Effects are causal
contrasts of assigned test order within systems. Geography is not randomized.
The difference between regions does not identify a causal cultural mechanism.

## Result boundaries

The original 84-system summary is reproduced exactly: 205,114 students, 78 negative
system effects, fixed-effect mean -0.093103 SD and DL random-effect mean -0.092595 SD.
The regional REML omnibus rejects equality (p=0.00178). Equal-system Welch inference
over all 12 groups is borderline (p=0.0510); the planned restriction to the nine
regions with at least three systems gives p=0.00161. The sparse two-system groups
are Northern America, Australia/New Zealand, and Africa.

East Asia versus Western Europe is positive but does not survive BH across 66
comparisons under the primary, separate-region, or equal-system approaches.
East Asia versus Southern Europe survives BH in the main sample under all three
approaches. The latter is weakened under smaller science-only and stricter-overlap
samples and does not pass their 66-test correction. All leave-one-system-out point
contrasts remain positive, but some lose corrected significance.

Western Asia includes Armenia, Azerbaijan, Georgia and Turkiye under M49. Armenia
and Lebanon raise its average penalty and dispersion. They are retained in the
primary analysis, with influence checks reported separately.

## Provenance and reproducibility

Raw student-level OECD public-use files are not included or newly downloaded.
Archived estimates preserve their original ten-plausible-value and 80-Fay-BRR
sampling and measurement uncertainty. This supplement is independently rerunnable
from the archived **estimate-level** inputs. Re-estimating student-level regressions
requires the original microdata pipeline and authorized OECD public-use access.
The original raw-data source ledger and estimator scripts are retained for audit.
New code contains integrity checks against the original international summaries,
sample totals, unique geographic assignment, and total-variance identities.

Geographic source: https://unstats.un.org/unsd/methodology/m49/

PISA system-code source:
https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en/full-report/reader-s-guide_0364240f.html

The report records inference assumptions and avoids interpreting a nonsignificant
regional penalty as a zero effect or as evidence of no fatigue.
