# Data-source ledger

This ledger freezes the exact inputs used for replication version 1.1.0. The
archives were accessed and verified on **2026-09-12 UTC**. Raw microdata are not
included in the replication archive.

## Machine-readable public-use files

| Key | OECD file | Role | Bytes | SHA-256 |
|---|---|---|---:|---|
| `student` | `CY09_MS_STU_PUF.zip` | IDs, booklet, final and replicate weights, plausible values, covariates, moderators | 992,910,196 | `ef5a76cc20215c09308a541cb3c6ee66583d068ede8535c0b735288e0a71f985` |
| `cognitive` | `CY09_MS_COG_PUF.zip` | science adaptive/linear path variable (`SPATH`) | 224,749,839 | `e16982bba1b3c20f4dff18256bed1ef9be2b551c5b4a552d13cbbe8ecc6a2a1d` |
| `ldw` | `CY09_MS_LDW_PUF.zip` | LDW scored responses and item-level process-summary fields | 93,184,353 | `4ac45bfbbd99bcaa38563c21abd05901c1ab6271d2985c35ccf3029d70641b3e` |

Official download URLs:

- <https://webfs.oecd.org/pisa2022/2025/CY09_MS_STU_PUF.zip>
- <https://webfs.oecd.org/pisa2022/2025/CY09_MS_COG_PUF.zip>
- <https://webfs.oecd.org/pisa2022/2025/CY09_MS_LDW_PUF.zip>

Each archive must satisfy all three checks before analysis begins: exact byte
count, exact SHA-256 digest, and a complete archive-member/CRC test. The checks
are implemented in `code/00_download/verify_data.py`; the as-run report is saved
to `output/logs/data_integrity.json`.

## Documentation sources

| Source | Use in the design audit | Official URL | Authority |
|---|---|---|---|
| PISA 2025 Database | Confirms individual-level student, cognitive-item, timing, questionnaire, codebook, and reproduction resources | <https://www.oecd.org/en/data/datasets/pisa-2025-database.html> | OECD primary source |
| PISA 2025 data-file index | Resolves current public-use filenames and download endpoints | <https://webfs.oecd.org/pisa2022/index.html> | OECD primary source |
| PISA FAQs | States that domains and test positions are rotated across students at random and describes the non-adaptive science allocation | <https://www.oecd.org/en/about/programmes/pisa/pisa-frequently-asked-questions-faqs.html> | OECD primary source |
| PISA 2025 Integrated Design | Documents the two-hour assessment structure and form rotation | <https://www.oecd.org/content/dam/oecd/en/about/programmes/edu/pisa/pisa-database/survey-implementation-tools/pisa-2025/PISA-2025-Integrated-Design.pdf> | OECD design document |
| PISA 2025 Assessment and Analytical Framework | Defines the assessed domains and constructs | <https://doi.org/10.1787/86c36975-en> | OECD official publication |
| LDW assessment framework | Defines LDW as learning/problem solving with computational tools and motivates self-regulated-learning mechanisms | <https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/learning-in-the-digital-world/PISA%202025%20Learning%20in%20the%20Digital%20World%20Assessment%20Framework%20-%20Second%20Draft.pdf> | OECD framework |
| PISA PUF user terms | Governs access and use of the public-use microdata | <https://survey.oecd.org/index.php?r=survey/index&sid=197663> | OECD terms of use |

## Provenance and access rules

- Source tier: all identification-critical claims and all microdata come directly
  from OECD sources.
- Access: the downloader requires the user to pass an explicit terms-acceptance
  flag. The package does not attempt to accept terms on a user's behalf.
- Redistribution: no raw SPSS or ZIP file and no record-level derived dataset is
  included in the archive.
- Version drift: a later OECD replacement will fail the pinned size/hash checks.
  Researchers should treat such a failure as a new data version, record the new
  provenance, and compare estimates before changing the pins.
- Merge key: student, cognitive, and LDW records are joined by `CNTSTUID`; the
  school and system identifiers are retained for audit and estimation.
