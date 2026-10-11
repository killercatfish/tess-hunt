import json, sqlite3, csv, os, glob
c = sqlite3.connect("/tmp/ecn/results.db")
geo = {(g["tic"], round(g["period"], 4)): g for g in json.load(open("/tmp/ecn/geometry.json"))}
fixed = json.load(open("/tmp/ecn/fixed.json"))
matched = json.load(open("/tmp/ecn/matched.json"))
tri = {}
for f in glob.glob("/tmp/ecn/tri/*/triceratops.json"):
    d = json.load(open(f)); tri[str(d["tic"])] = dict(FPP=round(d["FPP_mean"], 4), FPP_std=round(d["FPP_std"], 4),
        NFPP=d["NFPP_mean"], NFPP_std=d["NFPP_std"], depth_used_ppm=round(d["depth_ppm"]))
out = []
for r in csv.DictReader(open("/tmp/ecn/signals.csv")):
    tic, P = int(r["TIC"]), float(r["P_d"])
    sigs = c.execute("select period, verdict, tests, snr, depth_ppm from signals where tic=?", (tic,)).fetchall()
    hit = [s for s in sigs if abs(s[0] / P - 1) < 0.01]
    rec = dict(tic=tic, their_P=P, their_depth_ppm=float(r["depth_ppm"]), their_T14_h=float(r["T14_h"]), their_MES=float(r["MES"]))
    if hit:
        t = json.loads(hit[0][2]); rec.update(recovered_blind=True, our_P=hit[0][0], our_verdict=hit[0][1], our_snr=round(hit[0][3], 1),
            our_depth_ppm=round(hit[0][4]), failed=[k for k, v in t.items() if isinstance(v, dict) and v.get("pass") is False])
        m = matched.get(str(tic))
        if m: rec["known_matches"] = m["known"].get("matches") if m["known"] else None
    else:
        rec.update(recovered_blind=False, fixed_ephemeris=fixed.get(str(tic)))
    g = geo.get((tic, round(P, 4)))
    if g:
        rec["neighbours_within_16"] = [dict(tic=n["tic"], sep=n["sep_arcsec"], tmag=n["tmag"], need=n["required_depth"], rad=n["rad"],
            lum=n["lumclass"], plx=n["plx_mas"], verdict=n["verdict"]) for n in g["neighbours"] if n["sep_arcsec"] <= 16]
        rec["n_capable_60"] = g["n_capable"]; rec["n_not_excluded_60"] = g["n_possible"]
    if hit and str(tic) in tri: rec["triceratops"] = tri[str(tic)]
    out.append(rec)
json.dump(out, open("/tmp/ecn/ecn_summary.json", "w"), indent=1, default=str)
print(json.dumps(tri, indent=0))
