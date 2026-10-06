# Variable dictionary

This dictionary lists every source or derived variable used by the released
analysis. Source labels and value coding should be checked against the OECD PISA
2025 codebook if the OECD republishes the PUF.

## Identifiers and design variables

| Variable | Source | Definition / use |
|---|---|---|
| `CNT` | Student PUF | Three-character participating-system code; analyses are run separately by this field |
| `CNTRYID` | PUFs | Numeric country/economy identifier retained for audit |
| `CNTSCHID` | Student PUF | International school identifier |
| `CNTSTUID` | All three PUFs | International student identifier and one-to-one merge key |
| `BOOKID` | Student PUF | Test-book/form identifier |
| `paired_domain` | Derived | `science` for books 5/6, `reading` for 9/10, `math` for 11/12 |
| `paired_domain_code` | Derived | PISA suffix `SCIE`, `READ`, or `MATH` |
| `ldw_second` | Derived | 1 for books 5, 9, 11; 0 for books 6, 10, 12 |
| `design_stratum` | Derived | Main: `CNT × CNTSCHID × paired_domain`; adaptive appendix: `CNT × CNTSCHID × BOOKID` |
| `SPATH` | Cognitive PUF | Science path: `1.0` linear/non-adaptive; `2.0` adaptive |
| `adaptive` | Derived | 1 if `SPATH == 2.0`; 0 if `SPATH == 1.0` |

The exact mapping is also released as `docs/booklet-map.csv` and declared in
`config/config.yml`.

## Survey weights and latent outcomes

| Variable family | Count | Definition / use |
|---|---:|---|
| `W_FSTUWT` | 1 | Final student survey weight |
| `W_FSTURWT1`–`W_FSTURWT80` | 80 | BRR-Fay replicate weights |
| `PV1CMPS`–`PV10CMPS` | 10 | LDW/computational problem-solving plausible values |
| `PV1SCIE`–`PV10SCIE` | 10 | Science plausible values |
| `PV1READ`–`PV10READ` | 10 | Reading plausible values |
| `PV1MATH`–`PV10MATH` | 10 | Mathematics plausible values |

The SD specifications standardize each plausible value within participating
system using `W_FSTUWT` before estimation. No single plausible value is treated
as an observed student test score.

## Balance variables

| Analysis name | PUF / derived variable | Coding |
|---|---|---|
| Age | `AGE` | Years |
| Female | `female` from `ST004D01T` | 1 when source code is 1; 0 when code is 2; missing otherwise |
| Socioeconomic status | `ESCS` | OECD index of economic, social, and cultural status |
| Parental education | `PAREDINT` | Years-equivalent index in the PUF |
| Home possessions | `HOMEPOS` | OECD home-possession index |
| Immigrant | `immigrant` from `IMMIG` | 1 for first- or second-generation immigrant (codes 2/3); 0 for native (code 1) |

## Learner-type moderators

| Analysis label | PUF / derived variable | Transformation | Direction in the package |
|---|---|---|---|
| Perseverance | `PERSEV` | None before within-system standardization | Higher = more perseverance per OECD scale |
| Test effort | `EFFORT1` | None | Higher = more reported effort; post-treatment |
| Digital distraction | `digital_distraction` from `ST097Q06DA` | `5 − source item` | Higher = more distraction |
| Curiosity | `CURIO` | None | Higher = more curiosity per OECD scale |
| Socioeconomic status | `ESCS` | None | Higher = more advantaged |
| Family support | `FAMSUP` | None | Higher = more support per OECD scale |
| Help seeking | `help_seeking` from `ST433Q02DA`, `ST433Q04DA`, `ST433Q06DA` | Reverse each item as `5 − item`; average when at least two are observed | Higher = more help seeking |
| Self regulation | `SELFREG` | None | Higher = more self-regulation per OECD scale |
| AI for learning | `ai_for_learning` from `ST438Q04DA` | None | Retains documented item direction |
| Feedback seeking | `feedback_seeking` from `ST434Q03DA` | None | Retains documented item direction |
| ICT feedback | `ICTFEED` | None | Retains documented OECD scale direction |
| AI use at school | `AIUSESCH` | None | Retains documented OECD scale direction |

Every moderator is centered and scaled by its final-weighted mean and SD within
system. The reported interaction is the change in the LDW second-hour effect per
one within-system moderator SD.

## LDW response and process-summary variables

The LDW file contains 48 scored fields matching `P[0-9]+M[0-9]+S`. For each
score field, the same stem supplies:

| Suffix | Meaning in the package |
|---|---|
| `S` | Scored response/status |
| `TT` | Time summary |
| `A` | Number-of-actions summary |
| `F` | First-action-time summary |

The score variable's OECD label is parsed to classify an item as `learn`,
`apply`, `show`, or `other`. Its maximum valid credit code is read from the PUF
metadata rather than hard-coded.

| Derived outcome | Construction |
|---|---|
| `n_items` | Count of item records with status `0`, `1`–`5`, `9`, or `r` |
| `credit_share` | Mean of awarded numeric score divided by that item's maximum score; status `0`, `9`, and `r` contribute zero |
| `any_credit_share` | Share with a credit code `1`–`5`; retained in processed data but not a released table outcome |
| `learn_credit_share` | `credit_share` restricted to items whose label contains “learn” |
| `apply_credit_share` | Same, for “apply” items |
| `show_credit_share` | Same, for “show” items |
| `not_reached_share` | Share coded `r` |
| `disengaged_share` | Share coded `9` |
| `no_credit_share` | Share coded `0` |
| `total_time` | Sum of valid item time summaries |
| `total_actions` | Sum of valid item action summaries |
| `total_first_action_time` | Sum of valid first-action-time summaries |
| `mean_first_action_time` | `total_first_action_time / n_items` |
| `log1p_total_time` | `ln(1 + total_time)` |
| `log1p_total_actions` | `ln(1 + total_actions)` |
| `log1p_mean_first_action_time` | `ln(1 + mean_first_action_time)`; released first-action specification |
| `log1p_total_first_action_time` | Retained for audit but not used in a released regression |

Status code `7` (“not applicable”) is excluded from both the item count and the
outcome denominators. User-missing timing/action sentinels at or above 99,000,000
are set to missing. A student enters the process analysis if `n_items > 0`; each
outcome then uses its own nonmissing subset and reuses the strict design strata.

## Missing-data rules

- SPSS user-missing values are converted to missing for the student and cognitive
  files. LDW response status codes are intentionally retained and interpreted.
- Main score specifications rely on the PUF plausible values and do not impute
  covariates.
- Balance, heterogeneity, and adaptive-interaction models use complete cases for
  the variable involved, then require both treatment states again within each
  estimation stratum.
- No derived index is used when fewer than two of the three help-seeking items are
  observed.
