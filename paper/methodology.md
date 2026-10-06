# Empirical Strategy

## 1. Design and estimand

PISA 2025 administered two one-hour assessment blocks and randomly rotated test
domains and positions across students. We exploit six test forms that create three
mirrored comparisons between *Learning in the Digital World* (LDW) and a
conventional domain. Books 5 and 6 pair LDW with science, books 9 and 10 pair LDW
with reading, and books 11 and 12 pair LDW with mathematics. Within each pair, one
form places LDW in the first hour and the other places it in the second hour.

For student \(i\) in school \(s\), participating system \(c\), and mirrored-domain
pair \(d\), define

\[
Z_{iscd}=\mathbf{1}\{\text{LDW is administered in hour 2}\}.
\]

Thus \(Z=1\) for books 5, 9, and 11 and \(Z=0\) for books 6, 10, and 12. Because
the other domain necessarily appears in the opposite hour, \(Z\) is simultaneously
an indicator that the paired conventional domain is administered first.

Our primary estimand is the intention-to-treat effect of assignment to an
LDW-second form on measured LDW proficiency. It is an effect of the complete
order/position bundle under the PISA protocol. The design does not separately
identify fatigue from warm-up, domain priming, time-on-test, motivation, or any
position-sensitive feature of measurement.

## 2. Analysis sample and overlap

We begin with all students assigned to books 5, 6, 9, 10, 11, or 12. We define a
design stratum as a participating system × school × mirrored-domain pair. The
strict analysis sample retains only strata containing at least one student in
each order:

\[
0 < \sum_{i\in g} Z_i < N_g,
\qquad g=(c,s,d).
\]

This restriction yields 205,114 students in 84 systems, or 89.63 percent of the
228,833 students assigned to an eligible form. The strict sample contains 137,579
science–LDW observations, 33,856 reading–LDW observations, and 33,679
mathematics–LDW observations. Because the restriction is based only on realized
assignment support, the estimand pertains to students in schools where both
orders occur.

## 3. Outcomes

The primary outcome is LDW proficiency, represented by the ten released
plausible values `PV1CMPS`–`PV10CMPS`. We report effects in PISA points and in
within-system standard-deviation units. For the standardized specification, each
plausible value is centered and scaled using its final-student-weighted mean and
standard deviation within system.

The mirrored-domain analysis uses the ten science, reading, or mathematics
plausible values corresponding to the student's form pair. For each pair, we
estimate the effect of \(Z\) on (i) LDW proficiency, (ii) conventional-domain
proficiency, and (iii) their difference. Because \(Z=1\) places the conventional
domain first, a negative LDW coefficient and a positive conventional-domain
coefficient imply that order changes measured comparative advantage. The
standardized component effects are the preferred comparison because domain scales
are constructed separately; the point-scale difference is reported as a readily
interpretable auxiliary contrast.

## 4. Within-system specification

We estimate all models separately by participating system. For plausible-value
draw \(m\), the main specification is

\[
Y^{(m)}_{iscd}=\alpha^{(m)}_{csd}+\beta^{(m)}_c Z_{iscd}
 +\varepsilon^{(m)}_{iscd},
\tag{1}
\]

where \(\alpha_{csd}\) denotes school × mirrored-domain fixed effects. Equation
(1) therefore compares students assigned to opposite orders within the same
school and form pair. No covariates are required for identification and none are
included in the main outcome specification.

For conventional-domain outcome \(C^{(m)}\) and LDW outcome \(L^{(m)}\), we also
estimate Equation (1) with

\[
Y^{(m)}=C^{(m)},\qquad
Y^{(m)}=L^{(m)},\qquad
Y^{(m)}=L^{(m)}-C^{(m)}.
\tag{2}
\]

The final contrast in (2) equals the difference between the two order effects
when evaluated on the released point scales.

## 5. Survey weights, replicate variance, and plausible values

Within each system, Equation (1) is estimated by weighted least squares using the
final student weight `W_FSTUWT`. Fixed effects are absorbed by subtracting
final-weighted stratum means from the outcome and regressors.

Sampling variance is computed with all \(R=80\) BRR-Fay replicate weights. Let
\(\hat\beta_m\) be the full-sample estimate for plausible value \(m\) and
\(\hat\beta_{mr}\) its estimate under replicate \(r\). With Fay coefficient
\(f=0.5\), the sampling variance for draw \(m\) is

\[
U_m=\frac{1}{R(1-f)^2}
\sum_{r=1}^{R}(\hat\beta_{mr}-\hat\beta_m)^2
=0.05\sum_{r=1}^{80}(\hat\beta_{mr}-\hat\beta_m)^2.
\tag{3}
\]

We then combine the \(M=10\) plausible-value estimates. Define

\[
\bar\beta=\frac{1}{M}\sum_{m=1}^{M}\hat\beta_m,
\qquad
\bar U=\frac{1}{M}\sum_{m=1}^{M}U_m,
\]

and

\[
B=\frac{1}{M-1}\sum_{m=1}^{M}(\hat\beta_m-\bar\beta)^2.
\]

The total variance is

\[
T=\bar U+\left(1+\frac{1}{M}\right)B.
\tag{4}
\]

For observed covariates and process outcomes, \(B=0\) and the same BRR-Fay
sampling-variance calculation is used.

## 6. Cross-system synthesis

Let \(\hat\beta_c\) and \(V_c\) denote a system estimate and its total variance.
We report two syntheses. The fixed-effect estimator is

\[
\hat\beta_{FE}=\frac{\sum_c V_c^{-1}\hat\beta_c}
{\sum_c V_c^{-1}},
\qquad
\operatorname{Var}(\hat\beta_{FE})=\left(\sum_c V_c^{-1}\right)^{-1}.
\tag{5}
\]

The random-effects estimator replaces \(V_c^{-1}\) with
\((V_c+\hat\tau^2)^{-1}\), where \(\hat\tau^2\) is the
DerSimonian–Laird moment estimator. We also report Cochran's \(Q\) and \(I^2\).
The fixed-effect estimate is the precision-weighted common-effect summary; the
random-effects estimate permits genuine effect dispersion. Neither should be
read as a student-population-weighted “world” average. System-level estimates are
released so that alternative equal-system or region-specific summaries can be
constructed transparently.

We stress-test this synthesis in six ways. First, we report modified
Hartung–Knapp inference around the random-effects mean, using (t_{C-1})
critical values and bounding the residual variance scale below by one. Second,
we report an unweighted equal-system mean. Third and fourth, we report the median
system effect and a 10 percent trimmed mean. Fifth, we weight system estimates by
their analysis-sample size as a descriptive alternative. Sixth, we report a
one-sided sign test and re-estimate both meta-analytic summaries after omitting
each system in turn. A random-effects prediction interval describes estimated
cross-system dispersion and is not a confidence interval for the mean.

## 7. Randomization diagnostics

We replace \(Y\) in Equation (1) with six predetermined variables: age, sex,
socioeconomic status, parental education, home possessions, and immigrant status.
For each outcome, we apply its own complete-case restriction, require mixed order
support again within the design stratum, and synthesize system estimates as above.
The balance table is a diagnostic of the implemented assignment, not a substitute
for the official randomization documentation.

We additionally audit the assignment and merge architecture before using any
outcome. The audit reports duplicate identifiers, nonpositive weights,
plausible-value completeness, LDW process-file match rates, booklet counts,
treatment shares by system, and design-stratum sizes. To test whether singleton
support drives the result, we reconstruct the sample at minimum per-order cell
sizes of 1, 2, 5, and 10 students within each school × pair stratum and rerun the
complete ten-plausible-value, 80-replicate estimator at every threshold.

## 8. Response and process-summary outcomes

The public LDW file contains 48 scored item fields and associated time, action,
and first-action summaries. For item \(j\), let \(S_{ij}\) be awarded numeric
credit and \(S_j^{max}\) its maximum code read from the SPSS metadata. Normalized
credit is

\[
Credit_i=\frac{1}{J_i}\sum_{j\in\mathcal J_i}
\frac{S_{ij}}{S_j^{max}},
\tag{6}
\]

where \(\mathcal J_i\) includes records coded 0, 1–5, 9, or not reached and
excludes code 7 (not applicable). Codes 9 and not reached contribute zero credit
and also enter separate share outcomes. We construct analogous credit means for
items whose metadata labels identify learn, apply, and show phases.

We additionally analyze the number of applicable item records, summed item time,
summed actions, and the student's mean first-action time across applicable items.
The three process measures are estimated as \(\log(1+x)\) outcomes and transformed
for presentation as
\(100[\exp(\hat\beta)-1]\). We estimate the same stratum-fixed-effect model and
BRR-Fay variance for each observed outcome. These fields are summary measures,
not full event sequences; they cannot identify tutorial or feedback choices.

## 9. Learner-type heterogeneity

For moderator \(M_i\), standardized by its final-weighted mean and SD within
system, we estimate

\[
Y^{(m)}_{iscd}=\alpha^{(m)}_{csd}
+\beta_c Z_i+\gamma_c M_i+\delta_c(Z_i\times M_i)
+\varepsilon^{(m)}_{iscd}.
\tag{7}
\]

LDW plausible values are also standardized within system, so \(\delta_c\) is the
change in the second-hour effect, in outcome SDs, per moderator SD. We examine 12
moderators: perseverance, test effort, digital distraction, curiosity, ESCS,
family support, help seeking, self-regulation, AI for learning, feedback seeking,
ICT feedback, and AI use at school. Benjamini–Hochberg q-values control the false
discovery rate across the family. Test effort is post-assignment and is reported
only as a descriptive correlate of treatment-effect variation.

## 10. Adaptive-science appendix

The appendix uses science books 1–6 and the cognitive-file path indicator:
`SPATH=2` denotes adaptive science and `SPATH=1` denotes the linear version. It
retains system × school × booklet strata containing both paths, yielding 454,324
students in 84 systems. We estimate a science-SD specification with school ×
booklet fixed effects and then add standardized ESCS and `adaptive × ESCS`. The
interaction sample contains 397,502 students in 82 systems. The same ten-PV,
80-replicate, system-first inference is used.

## 11. Missing data, multiplicity, and interpretation

The main LDW model requires no questionnaire covariates. Secondary analyses use
outcome-specific complete cases and re-establish treatment overlap after the
restriction. No covariate or moderator is imputed. Pair-specific conventional
outcomes are estimated only where all ten released plausible values are present.

The primary hypothesis is the LDW order effect. The three mirrored pairs provide
structured replications. Process outcomes, learner-type interactions, and the
adaptive comparison are secondary; only the moderator family receives formal BH
adjustment in this release.

Finally, all coefficients should be interpreted as changes in *measured PISA
performance under the assigned test sequence*. The design is highly informative
about score comparability and measured comparative advantage, but it does not
show that students permanently lose competence during the second hour.
