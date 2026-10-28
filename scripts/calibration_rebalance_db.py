"""Queue helper for the calibration rebalance watchers (copied to the machine, run from ~/dev/tess-hunt).
  DB state         print the stars still queued, the rate in stars per hour since the run's first start, and
                   the rate over the last two hours (a run can slow down as it reaches bigger stars)
  DB move N OUT    take the last N queued stars, deleting each only while it is still queued, and list them in OUT
Workers claim stars in rowid order with a single UPDATE, so the last queued stars are the last a run would reach.
"""
import sqlite3
import sys
import time

c = sqlite3.connect(sys.argv[1], timeout=60)
if sys.argv[2] == "state":
    now = time.time()
    q = c.execute("select count(*) from targets where status='queued'").fetchone()[0]
    d, t0 = c.execute("select count(*), min(started) from targets where status in ('done','nodata','error')").fetchone()
    recent = c.execute("select count(*) from targets where finished > ?", (now - 7200,)).fetchone()[0]
    print(q, d / max((now - t0) / 3600, 0.1), recent / 2)
elif sys.argv[2] == "move":
    with c:
        tics = [r[0] for r in c.execute("select tic from targets where status='queued' order by rowid desc limit ?",
                                        (int(sys.argv[3]),))]
        moved = [t for t in tics if c.execute("delete from targets where tic=? and status='queued'", (t,)).rowcount]
    with open(sys.argv[4], "w") as fh:
        fh.write("".join(f"{t}\n" for t in moved))
    print(len(moved), "moved")
