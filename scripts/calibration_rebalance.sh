#!/usr/bin/env bash
# Run from the Mac (Josh, 10/27 11pm: "if kcfgamer finishes with hours to go for Cortex, move some").
# Waits for kcfgamer's calibration share to end, then, if Cortex still has more than an hour of queued stars,
# moves the tail of Cortex's queue to kcfgamer so both end near the same time. Workers claim stars in rowid
# order with a single UPDATE, so the stars taken from the end of the queue are the last Cortex would reach;
# each is deleted from Cortex's database only while still queued, and kcfgamer runs exactly that list into
# calibration/out/kcfgamer2/ (scripts/calibration_report.py merges every calibration/out/*/results.db).
# The moved list is kept at calibration/out/cortex/moved_to_kcfgamer.txt on Cortex.
#   scripts/calibration_rebalance.sh   (needs ssh to cortex and kcfgamer, and this commit as a bundle at
#                                       C:\Users\kille-ssh\tess2.bundle for kcfgamer to fast-forward to)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
WIN=/mnt/c/Users/kille-ssh
quiet() { tr -d '\000\r' | grep -v -iE "post-quantum|store now|upgraded"; }
kcf() { ssh -o ConnectTimeout=20 kcfgamer "wsl -d Ubuntu-26.04 -- bash $WIN/$1" 2>&1 | quiet; }
cortex() { ssh -o ConnectTimeout=20 cortex "cd ~/dev/tess-hunt && .venv/bin/python /tmp/rb_cortex.py $*" 2>&1 | quiet; }
scp -q "$HERE/calibration_rebalance_kcf.sh" kcfgamer:rb_state.sh 2>&1 | quiet
scp -q "$HERE/calibration_rebalance_cortex.py" cortex:/tmp/rb_cortex.py 2>&1 | quiet

echo "== $(date) waiting for kcfgamer's calibration share to end"
while :; do
  out=$(kcf "rb_state.sh state")
  echo "$out" | grep -q '^ENDED' && break
  sleep 300
done
echo "$out"
if ! echo "$out" | grep -q '^TRACEBACKS 0$'; then echo "kcfgamer's run had a Traceback; not moving anything"; exit 1; fi
RK=$(echo "$out" | awk '/^RATE/{print $2}')

read -r Q RC <<< "$(cortex state)"
M=$(python3 -c "q, rc, rk = $Q, $RC, $RK; print(round(q * rk / (rc + rk)) if q / rc > 1 else 0)")
echo "== $(date) Cortex: $Q queued at $RC stars/h; kcfgamer ran $RK stars/h; moving $M"
[ "$M" -gt 0 ] || { echo "under an hour left on Cortex; nothing to move"; exit 0; }
cortex move "$M"
scp -q cortex:dev/tess-hunt/calibration/out/cortex/moved_to_kcfgamer.txt "$TMP/moved.txt" 2>&1 | quiet
scp -q "$TMP/moved.txt" kcfgamer:moved.txt 2>&1 | quiet
kcf "rb_state.sh start"
echo "== $(date) rebalance done: $(wc -l < "$TMP/moved.txt" | tr -d ' ') stars moved to kcfgamer"
