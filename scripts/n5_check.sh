#!/usr/bin/env bash
# Overnight check of the n5 search change (2026-10-23): validation set, then eumemic's 16 re-vet stars,
# then the 197-star pilot, all on the new search. The old results are kept beside the new ones
# (*_pre_n5) and scripts/n5_compare.py prints old against new at the end. Expect 4-8 h.
#   tmux new -d -s n5 'scripts/n5_check.sh 2>&1 | tee logs/n5_check.log'
set -euo pipefail
source "$(dirname "$0")/_env.sh"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "checkout has uncommitted edits, so the stamps would not name a real commit; stopping"; exit 1
fi
mkdir -p logs
echo "== $(date) n5 check at $(git rev-parse --short HEAD)"

# keep today's results to compare against (each copy made once, never overwritten)
[ -e results_pre_n5.db ] || "$PY" -c "import sqlite3; sqlite3.connect('results.db').backup(sqlite3.connect('results_pre_n5.db'))"
[ -e candidates_pre_n5 ] || cp -a candidates candidates_pre_n5
[ -e validation/out_pre_n5 ] || mv validation/out validation/out_pre_n5

echo "== $(date) 1/3 validation set (known planets and binaries)"
$NICE "$PY" -m tesshunt validate-run
"$PY" -m tesshunt validate-report > /dev/null

echo "== $(date) 2/3 eumemic's 16 re-vet stars"
$NICE "$PY" - <<'EOF'
import csv, os
from tesshunt import config as cfgmod, db, pipeline, report, negatives
out = os.path.join(cfgmod.ROOT, "revet", "n5")
os.makedirs(out, exist_ok=True)
cfg = cfgmod.with_overrides(cfgmod.load(), db=os.path.join(out, "results.db"),
                            candidates_dir=os.path.join(out, "candidates"), report=os.path.join(out, "report.html"))
tics = sorted({int(r["TIC"]) for r in csv.DictReader(open("revet/eumemic_close_neighbour/cortex/signals.csv"))})
db.add_targets(db.connect(cfg["paths"]["db"]), [{"tic": t} for t in tics], "ecn")
pipeline.run(cfg, ["ecn"])
report.build(cfg, title="tess-hunt n5 re-vet survivors")
negatives.write(cfg, title="tess-hunt n5 re-vet negatives")
EOF

echo "== $(date) 3/3 pilot, re-run"
"$PY" -m tesshunt requeue --status done
$NICE "$PY" -m tesshunt run

echo "== $(date) comparison"
"$PY" scripts/n5_compare.py | tee logs/n5_compare.txt
echo "== $(date) done"
