#!/usr/bin/env bash
# Run the kill-test calibration set (calibration/README.md) on one machine's share of the stars.
# The 698 stars are split by position in a fixed order: every fifth star to Cortex, the rest to kcfgamer
# (kcfgamer runs about 1.8x Cortex and starts some 9 h earlier on 10/27, so both should end near the same
# time). Each machine writes its own database in calibration/out/<machine>/; scripts/calibration_report.py
# merges them. CACHE_DIR points the run at a fresh cache: MAST replaces files in place
# (CHANGELOG 2026-10-27), and Cortex's cache holds some from before the sector 23-25 reprocessing.
#   tmux new -d -s calib 'MACHINE=cortex WORKERS=6 CACHE_DIR=data/cache_2026-10-27 scripts/calibration_run.sh 2>&1 | tee logs/calibration.log'
#   tmux new -d -s calib 'MACHINE=kcfgamer WORKERS=14 scripts/calibration_run.sh 2>&1 | tee logs/calibration.log'
set -euo pipefail
source "$(dirname "$0")/_env.sh"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "checkout has uncommitted edits, so the stamps would not name a real commit; stopping"; exit 1
fi
: "${MACHINE:?set MACHINE=cortex or MACHINE=kcfgamer}"
export WORKERS="${WORKERS:-6}"
mkdir -p logs
echo "== $(date) calibration run, $MACHINE share, at $(git rev-parse --short HEAD), $WORKERS workers"
$NICE "$PY" - <<'EOF'
import csv, os
from tesshunt import config as cfgmod, db, pipeline, report, negatives
machine = os.environ["MACHINE"]
out = os.path.join(cfgmod.ROOT, "calibration", "out", machine)
os.makedirs(out, exist_ok=True)
cfg = cfgmod.with_overrides(cfgmod.load(), db=os.path.join(out, "results.db"),
                            candidates_dir=os.path.join(out, "candidates"), report=os.path.join(out, "report.html"))
if os.environ.get("CACHE_DIR"):          # a fresh cache, so no file predates MAST's latest reprocessing
    cfg["paths"]["cache_dir"] = os.path.abspath(os.environ["CACHE_DIR"])
    os.makedirs(cfg["paths"]["cache_dir"], exist_ok=True)
cfg["search"]["plot_rejected"] = True   # as validation does: we want to see why a known planet was killed
# Queued by TIC number alone, so every star gets its radius, mass and Teff from the TIC exactly as a search
# would. The archive's published values are better and would make the size and duration tests look kinder.
rows = {}
for f, label in (("planets.csv", "cal_planet"), ("false_positives.csv", "cal_fp"), ("ebs.csv", "cal_eb")):
    for r in csv.DictReader(open(os.path.join("calibration", f))):
        rows.setdefault(int(float(r["tic"])), label)
order = sorted(rows)
mine = [t for i, t in enumerate(order) if (i % 5 == 0) == (machine == "cortex")]
con = db.connect(cfg["paths"]["db"])
for label in ("cal_planet", "cal_fp", "cal_eb"):
    db.add_targets(con, [{"tic": t} for t in mine if rows[t] == label], label)
print(f"{machine}: {len(mine)} of {len(order)} stars")
pipeline.run(cfg, workers=int(os.environ["WORKERS"]))
report.build(cfg, title=f"tess-hunt calibration survivors ({machine} share)")
negatives.write(cfg, title=f"tess-hunt calibration negatives ({machine} share)")
EOF
echo "== $(date) done"
