#!/usr/bin/env bash
# The other direction of scripts/calibration_rebalance.sh, run from the Mac. On 10/28 kcfgamer slowed overnight
# (62 stars in its first hour, about 15 an hour after 1am) while Cortex kept its pace, so Cortex ends first.
# This waits for Cortex's calibration chain to end, then, if kcfgamer has more than an hour of queued stars, moves
# the tail of kcfgamer's queue to Cortex, sized by Cortex's rate and kcfgamer's rate over the last two hours, and
# runs it on Cortex into calibration/out/cortex2/ on the fresh cache. The list is kept on kcfgamer at
# C:\Users\kille-ssh\moved_to_cortex.txt and on Cortex at /tmp/moved_to_cortex.txt.
# (Josh, 10/27: move stars when one machine finishes hours early.)
#   scripts/calibration_rebalance_reverse.sh   (this commit as a bundle at /tmp/tess2.bundle on Cortex)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
WIN=/mnt/c/Users/kille-ssh
KDB=calibration/out/kcfgamer/results.db
quiet() { tr -d '\000\r' | grep -v -iE "post-quantum|store now|upgraded"; }
# no quotes or pipes in kcfgamer commands: they pass through Windows' cmd, which mangles both
kcf() { ssh -o ConnectTimeout=20 kcfgamer "wsl -d Ubuntu-26.04 --cd /home/killercatfish/dev/tess-hunt -- $*" 2>&1 | quiet; }
cx() { ssh -o ConnectTimeout=20 cortex "cd ~/dev/tess-hunt && $*" 2>&1 | quiet; }
scp -q "$HERE/calibration_rebalance_db.py" kcfgamer:rb_db.py 2>&1 | quiet
scp -q "$HERE/calibration_rebalance_db.py" cortex:/tmp/rb_db.py 2>&1 | quiet

echo "== $(date) waiting for Cortex's calibration chain to end"
while :; do
  out=$(cx 'tmux has-session -t chain 2>/dev/null && echo RUNNING || echo ENDED')
  [ "$out" = ENDED ] && break
  sleep 300
done
if ! cx 'grep -c Traceback logs/calibration.log' | grep -qx 0; then echo "Cortex's run had a Traceback; not moving anything"; exit 1; fi
read -r _ RC _ <<< "$(cx '.venv/bin/python /tmp/rb_db.py calibration/out/cortex/results.db state')"
read -r Q _ RK <<< "$(kcf ".venv/bin/python $WIN/rb_db.py $KDB state")"
M=$(python3 -c "q, rc, rk = $Q, $RC, max($RK, 1); print(round(q * rc / (rc + rk)) if q / rk > 1 else 0)")
echo "== $(date) kcfgamer: $Q queued at $RK stars/h (last 2 h); Cortex ran $RC stars/h; moving $M"
[ "$M" -gt 0 ] || { echo "under an hour left on kcfgamer; nothing to move"; exit 0; }
kcf ".venv/bin/python $WIN/rb_db.py $KDB move $M $WIN/moved_to_cortex.txt"
scp -q kcfgamer:moved_to_cortex.txt "$TMP/moved.txt" 2>&1 | quiet
scp -q "$TMP/moved.txt" cortex:/tmp/moved_to_cortex.txt 2>&1 | quiet
cx 'git fetch -q /tmp/tess2.bundle HEAD && git merge -q --ff-only FETCH_HEAD && git log --oneline -1'
cx "tmux new -d -s calib2 'MACHINE=cortex2 TICS_FILE=/tmp/moved_to_cortex.txt WORKERS=6 CACHE_DIR=data/cache_2026-10-27 scripts/calibration_run.sh 2>&1 | tee logs/calibration2.log'; sleep 30; tmux ls; grep stars logs/calibration2.log"
echo "== $(date) rebalance done: $(wc -l < "$TMP/moved.txt" | tr -d ' ') stars moved to Cortex"
