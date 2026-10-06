#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${PISA_SKIP_DOWNLOAD:-0}" != "1" ]]; then
  if [[ "${PISA_ACCEPT_TERMS:-0}" != "1" ]]; then
    echo "Review OECD's PISA PUF access terms, then run with PISA_ACCEPT_TERMS=1." >&2
    echo "Access page: https://survey.oecd.org/index.php?r=survey/index&sid=197663" >&2
    exit 2
  fi
  python code/00_download/download_data.py --accept-oecd-terms
fi

python code/00_download/verify_data.py
python code/01_clean/prepare_all.py
python code/02_construct/construct_analysis_samples.py
python code/02_construct/design_diagnostics.py
python code/03_analyze/main_effects.py
python code/03_analyze/meta_robustness.py
python code/03_analyze/support_sensitivity.py
python code/03_analyze/comparative_advantage.py
python code/03_analyze/balance.py
python code/03_analyze/process_outcomes.py
python code/03_analyze/heterogeneity.py
python code/03_analyze/adaptive_appendix.py
python code/04_tables/make_tables.py
python code/05_figures/make_figures.py
python code/06_diagnostics/test_estimators.py
python code/06_diagnostics/validate_outputs.py
python code/06_diagnostics/make_manifest.py

echo "Replication complete. See output/tables, output/figures, and output/logs."
