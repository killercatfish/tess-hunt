import sqlite3, json
c = sqlite3.connect("/tmp/ecn/results.db")
want = {88407114: 1.49751, 420529106: 21.958436, 306990399: 4.705146, 408310006: 27.017032, 146282666: 9.995027, 76228620: 24.524859, 165337974: 8.95644, 163029327: 0.946925}
out = {}
for tic, p in want.items():
    rows = c.execute("select iteration, period, t0, duration_h, depth_ppm, passes_threshold, tests from signals where tic=?", (tic,)).fetchall()
    me = [r for r in rows if abs(r[1] / p - 1) < 0.01][0]
    t = json.loads(me[6])
    masks = [f"{r[1]:.6f},{r[2]:.5f},{r[3]:.3f}" for r in rows if r is not me and r[5]]
    out[tic] = dict(P=me[1], t0=me[2], dur=me[3], depth=me[4], known=t.get("known"), odd_even=t.get("odd_even", {}).get("sigma"),
                    secondary=t.get("secondary", {}).get("scan_max_sigma"), holdout=(t.get("holdout", {}).get("hits"), t.get("holdout", {}).get("attempts")),
                    sector=t.get("sector_consistency", {}).get("p"), shape=t.get("shape", {}).get("why") or t.get("shape", {}).get("pass"), masks=masks)
    print(tic, json.dumps(out[tic], default=str)[:600])
json.dump(out, open("/tmp/ecn/matched.json", "w"), default=str, indent=1)
