# Deviations from blueprint

This file records analytic decisions made between the short feasibility audit and
replication releases 1.0.0–1.1.0. It prevents the exploratory audit from being mistaken
for a preregistration.

## Release 1.1.0 audit additions

1. **Novelty was narrowed after a nearest-neighbour literature audit.** OECD's
   own PISA 2025 Volume I already reports first- versus second-hour effects in
   conventional domains. The paper therefore claims an LDW-specific extension,
   a mirrored comparative-advantage estimand, and LDW response/process evidence—not
   discovery of generic PISA position effects.
2. **Cross-system synthesis received additional stress tests.** Version 1.1.0
   adds modified Hartung–Knapp inference, equal-system and descriptive alternative
   weighting rules, a sign test, prediction intervals, and leave-one-system-out
   re-estimation.
3. **Overlap sensitivity is now estimated rather than only described.** The full
   PV/BRR estimator is rerun after requiring at least 2, 5, or 10 students in each
   order within a design stratum.
4. **First-action timing was clarified.** The released regression now uses the
   log of the student's mean first-action time across applicable items. Version
   1.0.0 used the log of the summed first-action summaries while labeling the
   result too generically. The raw sum remains available in generated processed
   data but is no longer the reported estimand.

## Scope changes

1. **The core project was narrowed to randomized test order.** The initial
   “Hidden Learners” idea relied on richer LDW self-regulation and event-log data.
   The current public release supports a clean mirrored-order study, but not the
   proposed tutorial/feedback/strategy-switching design. AI, curiosity, help
   seeking, and related measures are retained only as a multiplicity-adjusted
   heterogeneity family.
2. **The title's “tax” is descriptive.** The formal estimand is the effect of the
   complete randomized order/position bundle. Pure fatigue is not separately
   identified.
3. **The adaptive-science idea became an appendix.** Its average effect and ESCS
   interaction are both small and statistically indistinguishable from zero.

## Sample and estimator changes

1. **Strict overlap was adopted.** The final main sample requires both orders
   within `CNT × CNTSCHID × paired_domain`, retaining 205,114 of 228,833 eligible
   observations. This was chosen before inspecting the final outcome regressions
   and makes the identifying comparison transparent.
2. **All analyses are system-first.** Instead of a single pooled international
   regression, the package estimates each participating system with its survey
   weights and then synthesizes the estimates. Both fixed- and random-effects
   results are released.
3. **PISA variance machinery is fully implemented.** Early feasibility numbers
   were useful for screening; final numbers use all ten plausible values, all 80
   BRR-Fay replicates, and the multiple-imputation combining rule.
4. **Reading and mathematics have 83-system support in pair-specific results.**
   One system has no usable conventional-domain plausible values in those
   mirrored subsamples and is omitted after re-establishing mixed-stratum support.

## Outcome-definition changes

1. **Credit is normalized partial credit.** The released primary process measure
   divides each awarded item score by its metadata-defined maximum and averages
   across applicable items. The quick audit's any-credit indicator remains in the
   processed dataset but is not the table's primary credit measure.
2. **Timing uses public item summaries.** Total time and number of actions are
   summed from the LDW item-summary fields; first-action time is averaged across
   applicable items. They are not reconstructed from full chronological event
   logs. Log specifications use `ln(1+x)` and are reported as
   `100 × (exp(beta) − 1)`.
3. **Help-seeking direction was corrected for readability.** The final index
   reverse-codes its three source items, so higher values consistently mean more
   help seeking. Its interaction therefore has the opposite algebraic sign from
   any audit output that used the unreversed source scale.
4. **Test effort is explicitly post-treatment.** It remains visible as a
   descriptive interaction but cannot be interpreted as a predetermined effect
   modifier.

## Reproducibility changes

1. Raw and record-level derived PUF data are excluded from distribution.
2. Official archives are pinned by size and SHA-256, and the pipeline stops if
   OECD replaces a file silently.
3. Extraction is sequential to limit temporary disk use and includes an external
   `unzip` fallback for compression methods unsupported by a local Python build.
4. The package includes synthetic unit tests, release-level result assertions,
   an output manifest, and data-free copies of the audited sample counts.

## What remains exploratory

The main randomized order effect and three mirrored-pair contrasts form a tightly
defined family. Learner-type interactions, process decompositions, and the
adaptive-science appendix should be described as secondary. A future manuscript
should date-stamp a formal analysis plan before adding new moderators, alternative
process codings, or country-selection rules.
