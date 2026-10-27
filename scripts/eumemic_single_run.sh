#!/usr/bin/env bash
# First re-search of eumemic's stars (Josh, 2026-10-26): the 559 where one strong, mostly single-transit first
# signal ended their search by signal 2 (scripts/eumemic_stop_counts.py on their tables at d3daa0f). These are
# the stars most like the ones our n5 fix recovers. Own database and outputs in search/eumemic_single/, so the
# pilot is untouched. About 15 h on 6 workers at the n5 cost (~560 s per star); faint stars may run faster.
#   tmux new -d -s single 'scripts/eumemic_single_run.sh 2>&1 | tee logs/eumemic_single.log'
set -euo pipefail
source "$(dirname "$0")/_env.sh"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "checkout has uncommitted edits, so the stamps would not name a real commit; stopping"; exit 1
fi
mkdir -p logs
echo "== $(date) eumemic single-stop re-search at $(git rev-parse --short HEAD)"
$NICE "$PY" - <<'EOF'
import csv, os
from tesshunt import config as cfgmod, db, pipeline, report, negatives
out = os.path.join(cfgmod.ROOT, "search", "eumemic_single")
os.makedirs(out, exist_ok=True)
cfg = cfgmod.with_overrides(cfgmod.load(), db=os.path.join(out, "results.db"),
                            candidates_dir=os.path.join(out, "candidates"), report=os.path.join(out, "report.html"))
tics = [int(r["tic"]) for r in csv.DictReader(open("search/eumemic_single_tics.csv"))]
db.add_targets(db.connect(cfg["paths"]["db"]), [{"tic": t} for t in tics], "esingle")
pipeline.run(cfg, ["esingle"])
report.build(cfg, title="tess-hunt: eumemic single-stop re-search, survivors")
negatives.write(cfg, title="tess-hunt: eumemic single-stop re-search, negatives")
EOF
echo "== $(date) done"
