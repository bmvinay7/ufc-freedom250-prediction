#!/usr/bin/env bash
# End-to-end pipeline: data -> features -> train -> predict -> simulate -> web export
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
cd src
echo "==> [1/5] build feature matrix";  python build_dataset.py
echo "==> [2/5] train models";          python train.py
echo "==> [3/5] predict the card";      python predict.py
echo "==> [4/5] monte carlo";           python simulate.py
echo "==> [5/5] export web data";       python export_web.py
echo
echo "Done. Open docs/index.html in a browser (or enable GitHub Pages on /docs)."
