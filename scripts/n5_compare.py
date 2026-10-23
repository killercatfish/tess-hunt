"""Old search against the n5 search (2026-10-23), after scripts/n5_check.sh. Read-only.

Prints: known planets and binaries in the validation set, eumemic's 17 re-vet signals, the pilot's
survivors gained and lost, and the CPU time each search took.
Usage (on Cortex, repo root): .venv/bin/python scripts/n5_compare.py
"""
import csv
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tesshunt import config as cfgmod  # noqa: E402

ROOT = cfgmod.ROOT
TOL = 0.01


def ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True) if os.path.exists(path) else None


def signals(con, tic):
    return con.execute("SELECT iteration, period, passes_threshold, verdict FROM signals WHERE tic=? ORDER BY iteration",
                       (tic,)).fetchall()


def at(sigs, P, aliases=(1,)):
    """The best signal at P (or an alias): survivor > rejected > below threshold, else None."""
    hits = [s for s in sigs if any(abs(s[1] / (P * a) - 1) < TOL for a in aliases)]
    rank = {"survivor": 0, "rejected": 1, "below_threshold": 2}
    return min(hits, key=lambda s: rank.get(s[3], 3)) if hits else None


def cpu_h(con):
    return (con.execute("SELECT SUM(runtime_s) FROM targets WHERE status='done'").fetchone()[0] or 0) / 3600


def show(s):
    return "missed" if s is None else f"{s[3]} (sig#{s[0]}, P {s[1]:.4f})"


def validation():
    old, new = ro(os.path.join(ROOT, "validation/out_pre_n5/validation.db")), ro(os.path.join(ROOT, "validation/out/validation.db"))
    if not (old and new):
        return print("validation: a database is missing; skipped\n")
    print("## Validation set: known planets (found at the right period, and verdict)")
    tally = {"old": [0, 0], "new": [0, 0]}
    for r in csv.DictReader(open(os.path.join(ROOT, "validation/known_planets.csv"))):
        tic, P = int(r["tic"]), float(r["pl_orbper"])
        o, n = at(signals(old, tic), P), at(signals(new, tic), P)
        for k, s in (("old", o), ("new", n)):
            tally[k][0] += s is not None and s[2] == 1
            tally[k][1] += s is not None and s[3] == "survivor"
        if show(o) != show(n):
            print(f"- {r['pl_name']} {P:.4f} d: {show(o)} -> {show(n)}")
    print(f"Planets found above threshold: {tally['old'][0]} -> {tally['new'][0]}; surviving every hard test: "
          f"{tally['old'][1]} -> {tally['new'][1]}\n")
    print("## Validation set: known binaries (any signal at the binary's period, x2 or x1/2, that survives)")
    bad = {"old": 0, "new": 0}
    for r in csv.DictReader(open(os.path.join(ROOT, "validation/known_ebs.csv"))):
        tic, P = int(r["tic"]), float(r["Per"])
        for k, con in (("old", old), ("new", new)):
            bad[k] += any(s[3] == "survivor" and any(abs(s[1] / (P * a) - 1) < TOL for a in (1, 2, 0.5))
                          for s in signals(con, tic))
    print(f"Binaries with a surviving signal at their period (should stay 0 or fall): {bad['old']} -> {bad['new']}")
    print(f"CPU hours: {cpu_h(old):.1f} -> {cpu_h(new):.1f}\n")


def revet():
    new = ro(os.path.join(ROOT, "revet/n5/results.db"))
    if not new:
        return print("re-vet: database missing; skipped\n")
    # Counted this way (within 1% of their period, no aliases) the 10/12 search found 9 of 17; the 10/12 comment
    # said 10 because it also counted TIC 304655480, where our 26.978 d is 4x their 6.7474 d.
    print("## eumemic's 17 re-vet signals, blind (old search on 10/12, counted the same way: 9 of 17)")
    found = above = 0
    for r in csv.DictReader(open(os.path.join(ROOT, "revet/eumemic_close_neighbour/cortex/signals.csv"))):
        s = at(signals(new, int(r["TIC"])), float(r["P_d"]))
        found += s is not None
        above += s is not None and s[2] == 1
        print(f"- TIC {r['TIC']} {float(r['P_d']):.4f} d (their MES {r['MES']}): {show(s)}")
    print(f"Found at their period: {found} of 17 (above our threshold: {above})")
    print(f"CPU hours: {cpu_h(new):.1f}\n")


def pilot():
    old, new = ro(os.path.join(ROOT, "results_pre_n5.db")), ro(os.path.join(ROOT, "results.db"))
    if not (old and new):
        return print("pilot: a database is missing; skipped\n")
    q = "SELECT tic, period FROM signals WHERE verdict='survivor'"
    so, sn = old.execute(q).fetchall(), new.execute(q).fetchall()

    def has(rows, tic, P):
        return any(t == tic and abs(p / P - 1) < TOL for t, p in rows)
    print("## Pilot (197 stars)")
    print(f"Survivors: {len(so)} -> {len(sn)}")
    for t, p in so:
        if not has(sn, t, p):
            print(f"- LOST TIC {t} {p:.4f} d")
    for t, p in sn:
        if not has(so, t, p):
            print(f"- NEW  TIC {t} {p:.4f} d")
    v = "SELECT verdict, COUNT(*) FROM signals GROUP BY 1"
    print(f"Signals by verdict: {dict(old.execute(v).fetchall())} -> {dict(new.execute(v).fetchall())}")
    print(f"CPU hours: {cpu_h(old):.1f} -> {cpu_h(new):.1f}\n")


if __name__ == "__main__":
    validation()
    revet()
    pilot()
