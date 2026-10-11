import sqlite3, json, csv
c = sqlite3.connect("/tmp/ecn/results.db")
theirs = {}
for r in csv.DictReader(open("/tmp/ecn/signals.csv")):
    theirs.setdefault(int(r["TIC"]), []).append(float(r["P_d"]))
for tic, ps in theirs.items():
    st = c.execute("select status, n_sectors, error from targets where tic=?", (tic,)).fetchone()
    print(f"== {tic} status={st[0]} sectors={st[1]} their P={ps} {st[2] or ''}")
    for it, P, dep, dur, sde, snr, ntr, verdict, tests in c.execute(
            "select iteration, period, depth_ppm, duration_h, sde, snr, n_transits, verdict, tests from signals where tic=? order by iteration", (tic,)):
        t = json.loads(tests) if tests else {}
        fails = [k for k, v in t.items() if isinstance(v, dict) and v.get("pass") is False]
        match = ""
        for p in ps:
            for h in (1, 2, 0.5, 3, 1/3):
                if abs(P / (p * h) - 1) < 0.01:
                    match = f"MATCH {p}" + ("" if h == 1 else f" x{h:.2g}")
        print(f"  it{it} P={P:.5f} dep={dep:.0f} dur={dur:.2f}h SDE={sde:.1f} SNR={snr:.1f} ntr={ntr} {verdict:15s} fails={fails} {match}")
