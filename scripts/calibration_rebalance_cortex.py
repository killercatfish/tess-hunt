"""Cortex side of scripts/calibration_rebalance.sh (copied to /tmp/rb_cortex.py, run from ~/dev/tess-hunt).
  state    print the stars still queued and the rate in stars per hour since the run's first start
  move N   take the last N queued stars, deleting each only while it is still queued, and list them in
           calibration/out/cortex/moved_to_kcfgamer.txt
"""
import sqlite3
import sys
import time

c = sqlite3.connect("calibration/out/cortex/results.db", timeout=60)
if sys.argv[1] == "state":
    q = c.execute("select count(*) from targets where status='queued'").fetchone()[0]
    d, t0 = c.execute("select count(*), min(started) from targets where status in ('done','nodata','error')").fetchone()
    print(q, d / max((time.time() - t0) / 3600, 0.1))
elif sys.argv[1] == "move":
    with c:
        tics = [r[0] for r in c.execute("select tic from targets where status='queued' order by rowid desc limit ?",
                                        (int(sys.argv[2]),))]
        moved = [t for t in tics if c.execute("delete from targets where tic=? and status='queued'", (t,)).rowcount]
    with open("calibration/out/cortex/moved_to_kcfgamer.txt", "w") as fh:
        fh.write("".join(f"{t}\n" for t in moved))
    print(len(moved), "moved")
