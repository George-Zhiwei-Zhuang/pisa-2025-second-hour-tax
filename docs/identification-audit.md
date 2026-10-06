# Identification audit

## Bottom line

The public files pass the feasibility and internal-validity gates for a paper on
**randomized test order and measured performance**. They do not support a claim
that the design isolates pure fatigue, nor do they yet expose the complete LDW
self-regulation event logs needed to identify strategy switching or feedback use.

The defensible headline estimand is the intention-to-treat effect of assignment
to a mirrored form that places LDW in hour 2 rather than hour 1, conditional on
school × paired-domain strata.

## Gate-by-gate audit

| Gate | Evidence | Status |
|---|---|---|
| Individual-level data exist | Student, cognitive, and LDW PUFs download and merge by `CNTSTUID` | Pass |
| Treatment is recoverable | `BOOKID` deterministically maps books 5/6, 9/10, and 11/12 into three mirrored orders | Pass |
| Assignment has an official design basis | OECD states that domains and test positions are rotated across students at random | Pass |
| Within-school overlap exists | 205,114 of 228,833 eligible students (89.63%) remain in mixed school × pair strata | Pass |
| Baseline observables balance | All six fixed-effect meta balance tests have p-values above 0.44 | Pass |
| Outcomes support survey inference | Ten LDW and conventional-domain plausible values plus 80 BRR-Fay weights are available | Pass |
| Effect is large and repeatable | Random-effects LDW estimate is −0.093 SD; 78/84 system estimates are negative | Pass |
| Cross-system synthesis is influential-observation robust | Modified Hartung–Knapp CI excludes zero; leave-one-system-out random effects range from −9.18 to −8.62 points | Pass for the mean |
| Mirrored implication appears | LDW moves down while the domain moved to hour 1 moves up in all three pairs | Pass |
| Process evidence is directionally informative | Lower credit/time/actions and more disengaged codes; unchanged item exposure | Partial pass |
| Complete LDW event logs are public | Public file has item summaries, not the full tutorial/feedback/strategy sequence anticipated in later reporting | Fail / future data |
| Pure fatigue is isolated | Order also changes domain sequence, warm-up, priming, and possibly response/scaling behavior | Fail as a narrow mechanism claim |
| Generic test-position novelty remains | OECD and prior studies already estimate conventional-domain/item-position effects | Fail; contribution must be LDW-specific |
| Adaptive science changes inequality | Average and `adaptive × ESCS` estimates are statistically indistinguishable from zero | No evidence |

## Assignment and sample construction

The eligible population consists of students assigned to books 5, 6, 9, 10,
11, or 12. Within each pair, the two books reverse whether LDW is administered in
the first or second hour. The analysis defines

\[
Z_i=\mathbf{1}\{BOOKID_i\in\{5,9,11\}\}.
\]

To avoid comparing across different local form supports, the strict sample keeps
only strata defined by system, school, and paired domain in which both values of
\(Z_i\) are observed. Dropping an unmixed stratum uses assignment support, not
outcomes or covariates. It changes the target population to students in schools
with within-pair overlap; it does not manufacture within-stratum outcome balance.

| Sample step | Students | Systems |
|---|---:|---:|
| Eligible mirrored LDW books | 228,833 | 84 |
| Strict mixed-stratum main sample | 205,114 | 84 |
| Main sample with active LDW item records | 202,879 | 84 |
| Strict adaptive-science appendix | 454,324 | 84 |
| Adaptive × ESCS complete/mixed sample | 397,502 | 82 |

Strict main sample by pair: science 137,579; reading 33,856; mathematics 33,679.

The raw-design audit finds no duplicate eligible or strict-sample student IDs,
no nonpositive final weights, complete LDW plausible values for every strict-
sample student, and a 98.91 percent match to active LDW item records. Across
systems, the unweighted treated share in the strict sample ranges from 0.466 to
0.523.

## Balance evidence

Treatment-control differences are estimated with the same weights and absorbed
strata as the outcome model and synthesized across systems.

| Predetermined variable | Difference | SE | p-value |
|---|---:|---:|---:|
| Age | 0.0007 years | 0.0014 | 0.616 |
| Female | −0.0002 | 0.0008 | 0.842 |
| ESCS | 0.0004 | 0.0045 | 0.928 |
| Parental education | 0.0080 years | 0.0124 | 0.518 |
| Home possessions | 0.0035 | 0.0045 | 0.440 |
| Immigrant | −0.0002 | 0.0007 | 0.772 |

These tests do not prove random assignment, but the joint pattern is consistent
with the official rotation statement and provides no sign of sorting on the
audited observables.

## What the design identifies

The design identifies how **measured scores and observed response behavior under
the PISA protocol** change when a domain is moved between testing hours. This is
the relevant estimand for claims about score comparability, rank ordering, and
measured cross-domain comparative advantage.

The design does not identify:

- a permanent reduction in knowledge or skill;
- a classroom or educational-technology treatment effect;
- the effect of elapsed minutes holding preceding content fixed;
- a single psychological fatigue channel;
- tutorial use, feedback use, or strategy switching from full process logs; or
- the effect on students or schools without mirrored-order support.

## Main threats and safeguards

### Compound treatment

Changing LDW from hour 1 to hour 2 changes elapsed test time and which domain is
encountered first. Fatigue, warm-up, domain priming, motivation, and position
effects are inseparable. All paper language should use “order/position effect” or
“second-hour placement effect”; “second-hour tax” is a descriptive title.

### Latent-score construction

Plausible values are model-based draws, not individual test scores. The package
uses all ten draws and propagates plausible-value uncertainty. Nevertheless, the
estimated effect concerns the released measurement scale, so it can reflect both
behavioral changes and any position-sensitive properties of scoring or scaling.

### Survey inference

Naive OLS standard errors are inappropriate. The package applies final student
weights, all 80 BRR-Fay replicate weights, and the Fay factor specified for the
release. Estimates are obtained within systems before meta-analysis, avoiding a
single pooled coefficient that silently treats systems as one sampling frame.

### Cross-system heterogeneity

The fixed-effect and random-effects estimates are nearly identical for the LDW
main effect, but heterogeneity is material (random-effects \(I^2=0.55\) on the
SD scale). The paper reports both and releases every system estimate. A global
average should not be interpreted as a universal country-specific effect.

Alternative synthesis rules are tightly clustered: modified Hartung–Knapp
inference gives −9.00 points with a 95 percent CI of [−10.58, −7.42], the
equal-system mean is −9.49, and every leave-one-system-out random-effects estimate
lies between −9.18 and −8.62. At the same time, the random-effects prediction
interval reaches slightly above zero. The evidence is therefore strong for a
negative cross-system average, not for a negative effect in literally every
setting.

### Thin-stratum support and estimand drift

Many school × pair strata are small: the median eligible stratum contains two
students. Raising the minimum from one to two students in each order retains all
84 systems and produces −8.30 points, close to the −9.00-point main random-effects
estimate. Thresholds of five and ten retain only 32 and 11 systems, respectively,
and estimates no longer move monotonically. Those restrictions select different
schools and systems and hence change the estimand; they are reported as a scope
diagnostic rather than privileged as more credible estimates.

### Prior literature and contribution boundary

OECD's PISA 2025 Volume I already uses randomized booklet assignment to report
first- versus second-hour effects for science, mathematics, and reading. Earlier
psychometric and economics work also studies PISA item position and cognitive
endurance. The defensible contribution is the newly released LDW domain, its
mirrored cross-domain comparative-advantage contrast, and LDW-specific response
and process summaries. See `docs/novelty-map.md`.

### Missing outcomes and changing support

Each analysis re-establishes mixed treatment support after complete-case
restriction. Conventional reading and mathematics plausible values are not
available for one participating system in these booklet subsamples, so those
pair-specific meta-analyses contain 83 rather than 84 systems. Moderator coverage
also varies; `ICTFEED`, for example, is available in 44 systems.

### Multiple testing and post-treatment measures

The 12 learner-type interactions are a prespecified exploratory family and use
Benjamini–Hochberg q-values. Test effort is measured after assignment and is
explicitly labelled descriptive rather than a causal moderator.

### Public process-data boundary

The LDW PUF provides item scores, stage labels, status codes, total time, actions,
and first-action summaries. It does not presently provide the full chronological
stream of tutorial, worked-example, feedback, and strategy-change events described
in the LDW framework. The process table therefore triangulates engagement; it
does not estimate a structural mechanism.

## Decision

**Proceed as a secondary measurement paper.** The randomization basis, recoverable mirrored
forms, within-school overlap, clean balance, large main effect, and three-domain
replication support a polished empirical writing sample. Generic position effects
are not novel, and thin-stratum sensitivity limits broader claims. Stop short of
claims about pure fatigue or autonomous-learning mechanisms until richer process
data become public. The adaptive-science result belongs in an appendix as a
well-powered null, not as a co-equal headline.
