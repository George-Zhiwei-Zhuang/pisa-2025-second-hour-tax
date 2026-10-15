# Completed validation

- All 84 system codes map to exactly one region. Region counts sum to 84 and students to 205,114.
- Archived international fixed-effect and DL random-effect point and SD summaries reproduce to numerical tolerance 1e-11.
- Original total-variance identities match the released sampling plus plausible-value variances.
- An independent full-matrix REML implementation matches the regional-intercept solution to 1e-8.
- All 66 equal-system Welch contrast p values agree with scipy.stats.ttest_ind(equal_var=False).
- BH adjustments match an independent scalar step-up implementation.
- All five report pages and the forest plot were rendered and visually reviewed. A wrapped table header was corrected.
- Narrower-sample, variance-model, influence, and multiple-comparison limitations are reported explicitly.

This validates the estimate-level supplement. It is not a fresh student-level re-estimation.
