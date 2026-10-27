#!/usr/bin/env bash
# Everything we have reported, re-run on freshly downloaded light curves (2026-10-27, on kcfgamer).
# MAST replaced the sector 23-25 SPOC files with a 2023 reprocessing after Cortex cached them on 10/10,
# and the pipeline reuses its cache, so Cortex's results for 22 stars used the old files. This runs on a
# machine with an empty cache, so every file is today's MAST version:
#   0. the 21 stars we know used old files (quick answer)  -> search/mast_affected/
#   1. the validation set (known planets and binaries)      -> validation/out/
#   2. eumemic's 16 re-vet stars                             -> revet/n5/
#   3. the 200-star pilot (search/pilot_tics.csv: Cortex's pilot rows, stellar fields included) -> results.db
# Same paths as Cortex, so scripts/fresh_data_compare.py can set the two side by side.
# The worker count is passed to the run, not written in config.yaml, so the config hash matches Cortex's.
#   tmux new -d -s fresh 'WORKERS=14 scripts/fresh_data_check.sh 2>&1 | tee logs/fresh_data_check.log'
set -euo pipefail
source "$(dirname "$0")/_env.sh"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "checkout has uncommitted edits, so the stamps would not name a real commit; stopping"; exit 1
fi
export WORKERS="${WORKERS:-6}"
mkdir -p logs
echo "== $(date) fresh-data check at $(git rev-parse --short HEAD), $WORKERS workers"

echo "== $(date) 0/3 the 21 stars that used old sector 23-25 files"
$NICE "$PY" - <<'EOF'
import csv, os
from tesshunt import config as cfgmod, db, pipeline
out = os.path.join(cfgmod.ROOT, "search", "mast_affected")
os.makedirs(out, exist_ok=True)
cfg = cfgmod.with_overrides(cfgmod.load(), db=os.path.join(out, "results.db"),
                            candidates_dir=os.path.join(out, "candidates"), report=os.path.join(out, "report.html"))
pilot = [103221268, 219104885, 219495254, 229480400, 233530909, 236740165, 237205427, 257493470, 264304554,
         274944164, 289564998, 417986483, 418206247, 458483074, 459934092, 461408984, 470148871]
val = [57256934, 284441182, 357501308, 377293776]
num = lambda v: float(v) if v not in ("", None) else None
rows = [{k: (int(v) if k == "tic" else num(v)) for k, v in r.items()}
        for r in csv.DictReader(open("search/pilot_tics.csv")) if int(r["tic"]) in pilot]
for r in csv.DictReader(open("validation/known_planets.csv")):  # same fields validate.queue uses
    if int(r["tic"]) in val:
        rows.append({"tic": int(r["tic"]), "teff": num(r["st_teff"]), "rad": num(r["st_rad"]), "mass": num(r["st_mass"]),
                     "tmag": num(r["sy_tmag"]), "dist": num(r["sy_dist"])})
for r in csv.DictReader(open("validation/known_ebs.csv")):
    if int(r["tic"]) in val:
        rows.append({"tic": int(r["tic"]), "tmag": num(r["Tmag"])})
rows = list({r["tic"]: r for r in rows}.values())
assert len(rows) == 21, len(rows)
db.add_targets(db.connect(cfg["paths"]["db"]), rows, "affected")
pipeline.run(cfg, ["affected"], workers=int(os.environ["WORKERS"]))
EOF

echo "== $(date) 1/3 validation set (known planets and binaries)"
$NICE "$PY" - <<'EOF'
import os
from tesshunt import config as cfgmod, pipeline, report, validate
c = validate.queue(cfgmod.load())
pipeline.run(c, workers=int(os.environ["WORKERS"]))
report.build(c, title="tess-hunt VALIDATION survivors")
from tesshunt import negatives
negatives.write(c, title="tess-hunt VALIDATION negatives")
EOF
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
pipeline.run(cfg, ["ecn"], workers=int(os.environ["WORKERS"]))
report.build(cfg, title="tess-hunt n5 re-vet survivors")
negatives.write(cfg, title="tess-hunt n5 re-vet negatives")
EOF

echo "== $(date) 3/3 the 200-star pilot"
$NICE "$PY" - <<'EOF'
import csv, os
from tesshunt import config as cfgmod, db, pipeline, report, negatives
cfg = cfgmod.load()
num = lambda v: float(v) if v not in ("", None) else None   # Cortex's pilot rows, stellar fields included
rows = [{k: (int(v) if k == "tic" else num(v)) for k, v in r.items()} for r in csv.DictReader(open("search/pilot_tics.csv"))]
db.add_targets(db.connect(cfg["paths"]["db"]), rows, "pilot")
pipeline.run(cfg, ["pilot"], workers=int(os.environ["WORKERS"]))
report.build(cfg)
negatives.write(cfg)
EOF
echo "== $(date) done"
