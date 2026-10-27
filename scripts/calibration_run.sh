#!/usr/bin/env bash
# Run the kill-test calibration set (calibration/README.md) on one machine's share of the stars.
# The 698 stars are split by position in a fixed order: every third star to Cortex, the other two to kcfgamer
# (about its share of the speed). Each machine writes its own database in calibration/out/<machine>/;
# scripts/calibration_report.py merges them. CACHE_DIR points the run at a fresh cache: MAST replaces files in place
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
num = lambda v: float(v) if v not in ("", None) else None
rows = {}
for r in csv.DictReader(open("calibration/planets.csv")):
    rows.setdefault(int(r["tic"]), ({"tic": int(r["tic"]), "teff": num(r["st_teff"]), "rad": num(r["st_rad"]),
                                     "mass": num(r["st_mass"]), "tmag": num(r["sy_tmag"]), "dist": num(r["sy_dist"])}, "cal_planet"))
for r in csv.DictReader(open("calibration/false_positives.csv")):
    rows.setdefault(int(r["tic"]), ({"tic": int(r["tic"]), "teff": num(r["Stellar Eff Temp (K)"]),
                                     "rad": num(r["Stellar Radius (R_Sun)"]), "tmag": num(r["TESS Mag"]),
                                     "dist": num(r["Stellar Distance (pc)"])}, "cal_fp"))
for r in csv.DictReader(open("calibration/ebs.csv")):
    rows.setdefault(int(r["tic"]), ({"tic": int(r["tic"]), "teff": num(r["teff"]), "rad": num(r["rad"]),
                                     "tmag": num(r["Tmag"])}, "cal_eb"))
order = sorted(rows)
mine = [t for i, t in enumerate(order) if (i % 3 == 0) == (machine == "cortex")]
con = db.connect(cfg["paths"]["db"])
for label in ("cal_planet", "cal_fp", "cal_eb"):
    db.add_targets(con, [rows[t][0] for t in mine if rows[t][1] == label], label)
print(f"{machine}: {len(mine)} of {len(order)} stars")
pipeline.run(cfg, workers=int(os.environ["WORKERS"]))
report.build(cfg, title=f"tess-hunt calibration survivors ({machine} share)")
negatives.write(cfg, title=f"tess-hunt calibration negatives ({machine} share)")
EOF
echo "== $(date) done"
