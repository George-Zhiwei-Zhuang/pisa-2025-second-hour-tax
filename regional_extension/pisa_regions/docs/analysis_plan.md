# Regional extension: analysis decisions

This is an exploratory, post-manuscript extension requested on 10 October 2026.
It is not a preregistration. The geography is fixed by the external M49 rules,
not by estimated effects. The two sparse African subregions are combined only
to avoid displaying two single-system categories.

## Data and estimand

Reuse the archived, system-level estimates in replication version 1.1.0.
Each is a survey-weighted, school-by-mirrored-domain-pair fixed-effect estimate
with ten plausible values and 80 Fay-BRR weights. The total variance includes
both sampling and plausible-value uncertainty. Microdata are not in the archive
and are not re-downloaded or re-estimated for this extension.

The outcome is the system-specific effect of putting LDW second, expressed in
the system's own LDW standard deviations. Original PISA points are secondary.
The regional mean summarizes causal test-order effects estimated inside systems.
Region itself is not randomized; contrasts cannot identify a causal cultural,
curricular or institutional mechanism. Geographic groups are not income groups.

## Primary regional synthesis and inference

Fit a system-level random-effects meta-regression with one intercept per region:
effect_c = mu_region(c) + u_c + e_c. The released within-system variance is
Var(e_c). The residual between-system variance Var(u_c) is common across regions
and estimated by REML. Use modified Knapp-Hartung covariance, bounding the
residual variance multiplier below by one. Regional means and contrasts use
t inference with K-G degrees of freedom, where K is systems and G is regions.
An omnibus F test evaluates equality of all regional means.

Release all 66 regional contrasts together. Report two-sided p values and both
Benjamini-Hochberg FDR and Holm familywise adjustments within this one family.
Highlight East Asia versus Western Europe because the user explicitly suggested
these regions, and report its adjusted result as well as its unadjusted result.
Display the number of systems and students for every group. Groups with only
two systems borrow residual heterogeneity from the meta-regression and should
be interpreted as sparse sample summaries.

## Checks that can change the interpretation

1. Reproduce the archived international meta-summary and paper sample totals.
2. Report unweighted system means and Welch contrasts, treating systems equally,
   alongside fixed-effect and separate-region DL modified Hartung-Knapp summaries.
3. Repeat the region model on the common science-LDW pair and the support-two
   specification (at least two students in each order within each stratum).
4. Report pair-specific results for science, reading and mathematics separately;
   do not pool their multiple estimates as independent observations.
5. Refit all-system leave-one-system-out models for East Asia versus Western
   Europe. Inspect Western Asia's sensitivity to Armenia and Lebanon and to
   splitting the Caucasus from the other Western Asian systems. Label those
   influence checks as diagnostic, not as changes to the primary geography.
6. Show East Asia without Mongolia and East Asia plus Singapore as transparent
   alternative definitions; keep the original seven-system definition primary.
7. Refit the omnibus model excluding the three groups with only two systems.
8. Secondary process analyses examine normalized credit, disengagement, not
   reached, time and actions. Adjust their five omnibus tests as one family.
   Do not attribute the score effect to mediation or infer mechanisms from
   unadjusted regional comparisons.

## Documented refinement after initial estimates

The primary common-variance model and separately estimated regional DL variances
showed larger dispersion within Western Asia than within most other groups.
For that reason, the extension additionally reports direct contrasts between
independent, separate-region DL modified Hartung-Knapp summaries and an
equal-system Welch omnibus test that allows unequal regional dispersions.
The same 66-contrast correction family is retained. These additional checks
may weaken the common-variance model's findings and are reported in full.

## Deliverables


An auditable geography crosswalk; regional estimates; omnibus tests; all regional
contrasts; robustness and influence tables; a regional forest plot; a concise
English report; a self-contained package runnable from the archived system
estimates. Keep the original student-level replication package unchanged.
