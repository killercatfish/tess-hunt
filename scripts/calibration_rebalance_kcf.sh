# kcfgamer side of scripts/calibration_rebalance.sh (copied to C:\Users\kille-ssh\rb_state.sh and run in WSL).
#   state: has the calibration share ended, any Tracebacks, and its rate in stars per hour since its first start
#   start: fast-forward to the bundle, then run the stars in C:\Users\kille-ssh\moved.txt into calibration/out/kcfgamer2/
cd ~/dev/tess-hunt
if [ "$1" = state ]; then
  tmux has-session -t calib 2>/dev/null && echo RUNNING || echo ENDED
  echo "TRACEBACKS $(grep -c Traceback logs/calibration.log)"
  .venv/bin/python -c "
import sqlite3; c = sqlite3.connect('calibration/out/kcfgamer/results.db')
d, t0, t1 = c.execute(\"select count(*), min(started), max(finished) from targets where status in ('done','nodata','error')\").fetchone()
print('RATE', d / max((t1 - t0) / 3600, 0.1))"
elif [ "$1" = start ]; then
  git fetch -q /mnt/c/Users/kille-ssh/tess2.bundle HEAD && git merge -q --ff-only FETCH_HEAD && git log --oneline -1
  tmux new -d -s calib2 'MACHINE=kcfgamer2 TICS_FILE=/mnt/c/Users/kille-ssh/moved.txt WORKERS=14 scripts/calibration_run.sh 2>&1 | tee logs/calibration2.log'
  sleep 30; tmux ls; grep stars logs/calibration2.log
fi
