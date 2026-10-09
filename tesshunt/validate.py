"""Step 0.5: known planets + known EBs through the full pipeline, and an injection-recovery grid."""
import json
import os
import time

import numpy as np
import pandas as pd

from . import config as cfgmod, db, pipeline

VDIR = os.path.join(cfgmod.ROOT, "validation")
PL_CSV = os.path.join(VDIR, "known_planets.csv")
EB_CSV = os.path.join(VDIR, "known_ebs.csv")
PS_QUERY = ("https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query="
            "select+pl_name,hostname,tic_id,pl_orbper,pl_rade,st_teff,st_rad,st_mass,sy_tmag,sy_dist,disc_facility"
            "+from+pscomppars+where+tran_flag=1+and+pl_rade<4+and+st_teff<5200+and+sy_dist<100"
            "+and+pl_orbper>0.5+and+pl_orbper<40+and+sy_tmag<13+and+tic_id+is+not+null+and+disc_facility+like+'%25TESS%25'")


def vcfg(cfg):
    out = os.path.join(VDIR, "out")
    os.makedirs(out, exist_ok=True)
    c = cfgmod.with_overrides(cfg, db=os.path.join(out, "validation.db"),
                              candidates_dir=os.path.join(out, "candidates"), report=os.path.join(out, "report.html"))
    c["search"]["plot_rejected"] = True
    return c


def build_sets(n_hosts=20, n_eb_shallow=5, n_eb_deep=5, seed=7):
    """Draw the validation sets once from live catalogs and freeze them as CSV (committed)."""
    rng = np.random.default_rng(seed)
    p = pd.read_csv(PS_QUERY)
    p["tic"] = p["tic_id"].str.replace("TIC ", "", regex=False).astype(int)
    hosts = sorted(p["tic"].unique())
    pick = rng.choice(hosts, size=n_hosts, replace=False)
    p[p["tic"].isin(pick)].sort_values(["tic", "pl_orbper"]).to_csv(PL_CSV, index=False)

    from astroquery.vizier import Vizier
    eb = Vizier(row_limit=-1).get_catalogs("J/ApJS/258/16")[0].to_pandas()
    eb = eb[(eb["Morph"] < 0.5) & (eb["Per"] > 0.5) & (eb["Per"] < 40) & (eb["Tmag"] < 13)]
    eb = eb[eb["TIC"].astype(int).isin(set(pick)) == False]  # noqa: E712
    shallow = eb[(eb["Dp-pf"] > 0.005) & (eb["Dp-pf"] < 0.05)]
    deep = eb[(eb["Dp-pf"] >= 0.05) & (eb["Dp-pf"] < 0.6)]
    sel = pd.concat([shallow.sample(n_eb_shallow, random_state=seed), deep.sample(n_eb_deep, random_state=seed)])
    sel = sel.assign(tic=sel["TIC"].astype(int))[["tic", "Per", "Morph", "Dp-pf", "Ds-pf", "Tmag", "RAJ2000", "DEJ2000"]]
    sel.to_csv(EB_CSV, index=False)
    return len(pick), len(sel)


def queue(cfg):
    c = vcfg(cfg)
    con = db.connect(c["paths"]["db"])
    pl = pd.read_csv(PL_CSV).drop_duplicates("tic")
    db.add_targets(con, [{"tic": int(r.tic), "teff": r.st_teff, "rad": r.st_rad, "mass": r.st_mass,
                          "tmag": r.sy_tmag, "dist": r.sy_dist} for r in pl.itertuples()], "val_planet")
    eb = pd.read_csv(EB_CSV)
    db.add_targets(con, [{"tic": int(r.tic), "tmag": r.Tmag} for r in eb.itertuples()], "val_eb")
    return c


def _pmatch(p, ref, tol=0.01, aliases=(1,)):
    return any(abs(p / (ref * k) - 1) < tol for k in aliases)


def evaluate(cfg):
    c = vcfg(cfg)
    con = db.connect(c["paths"]["db"])
    sig = pd.read_sql("SELECT * FROM signals", con)
    tg = pd.read_sql("SELECT * FROM targets", con).set_index("tic")
    pl = pd.read_csv(PL_CSV)
    eb = pd.read_csv(EB_CSV)
    lines = []

    # ---- planets: per planet, was it found at the right period, and what did the kill tests say?
    prow = []
    for r in pl.itertuples():
        s = sig[(sig.tic == r.tic) & (sig.passes_threshold == 1)]
        exact = s[[_pmatch(x, r.pl_orbper) for x in s.period]]
        alias = s[[_pmatch(x, r.pl_orbper, aliases=(2, 0.5, 3, 1 / 3)) for x in s.period]]
        hit = exact.iloc[0] if len(exact) else None
        fails = []
        if hit is not None:
            t = json.loads(hit.tests)
            fails = [k for k in c["kill_tests"]["hard_fail"] if t.get(k, {}).get("pass") is False]
        prow.append(dict(planet=r.pl_name, tic=r.tic, P=r.pl_orbper, Rp=r.pl_rade, status=tg.loc[r.tic, "status"],
                         n_sectors=tg.loc[r.tic, "n_sectors"], found=hit is not None, alias=len(alias) > 0,
                         sde=None if hit is None else round(hit.sde, 1), snr=None if hit is None else round(hit.snr, 1),
                         verdict=None if hit is None else hit.verdict, killed_by=",".join(fails)))
    pr = pd.DataFrame(prow)
    hosts = pr.groupby("tic").agg(any_found=("found", "any"))
    lines += ["## Known planets", "",
              f"- Hosts recovered (≥1 planet at the right period): **{int(hosts.any_found.sum())}/{len(hosts)}**",
              f"- Individual planets recovered at the right period: **{int(pr.found.sum())}/{len(pr)}** "
              f"(+{int((~pr.found & pr.alias).sum())} found only at an alias)",
              f"- Of recovered planets, surviving all hard kill tests: **{int((pr.verdict == 'survivor').sum())}/{int(pr.found.sum())}**",
              "", pr.to_markdown(index=False), ""]

    # ---- EBs: was it detected, and did the kill tests reject every EB-period signal?
    erow = []
    for r in eb.itertuples():
        s = sig[(sig.tic == r.tic) & (sig.passes_threshold == 1)]
        rel = s[[_pmatch(x, r.Per, 0.01, (1, 2, 0.5)) for x in s.period]]
        surv = s[s.verdict == "survivor"]
        why = set()
        for t in rel.tests:
            t = json.loads(t)
            why |= {k for k in c["kill_tests"]["hard_fail"] if t.get(k, {}).get("pass") is False}
        erow.append(dict(tic=r.tic, P=r.Per, depth=r._4, status=tg.loc[r.tic, "status"], detected=len(rel) > 0,
                         eb_signals=len(rel), eb_signals_surviving=int((rel.verdict == "survivor").sum()),
                         any_survivor=len(surv) > 0, killed_by=",".join(sorted(why))))
    er = pd.DataFrame(erow)
    det = er[er.detected]
    lines += ["## Known eclipsing binaries", "",
              f"- Detected at the EB period (or ×2, ×½): **{len(det)}/{len(er)}**",
              f"- Correctly rejected (no EB-period signal survives): **{int((det.eb_signals_surviving == 0).sum())}/{len(det)}**",
              f"- EB stars with ANY survivor (incl. unrelated periods): {int(er.any_survivor.sum())}",
              "", er.to_markdown(index=False), ""]

    # ---- kill-test pass rates over all threshold-passing signals
    rates = {}
    for t in sig[sig.passes_threshold == 1].tests:
        for k, v in json.loads(t).items():
            rates.setdefault(k, {"pass": 0, "fail": 0, "n/a": 0})[{True: "pass", False: "fail", None: "n/a"}[v.get("pass")]] += 1
    lines += ["## Kill-test outcomes over all threshold-passing validation signals", "",
              pd.DataFrame(rates).T.to_markdown(), ""]
    rt = tg.runtime_s.dropna()
    lines += [f"Runtime per star: median {rt.median():.0f}s, max {rt.max():.0f}s, total {rt.sum() / 3600:.1f} CPU-h.", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ injection-recovery grid

def _inj_task(args):
    cfg, tic, rp_re, P, phase = args
    cfgmod.limit_threads(1)
    import batman
    from . import lightcurves, search, stellar
    con = db.connect(vcfg(cfg)["paths"]["db"])
    star = pipeline.star_params(con, tic)
    lc = lightcurves.prepare(cfg, lightcurves.fetch(cfg, tic), lightcurves.detrend_window(cfg, star))
    ab = stellar.limb_darkening(tic)
    pr = batman.TransitParams()
    t = lc["time"]
    pr.t0, pr.per = t.min() + phase * P, P
    pr.rp = rp_re / stellar.REARTH_PER_RSUN / (star["rad"] or 0.5)
    a = (stellar.G * (star["mass"] or 0.5) * stellar.MSUN * (P * 86400) ** 2 / (4 * np.pi ** 2)) ** (1 / 3)
    pr.a = a / ((star["rad"] or 0.5) * stellar.RSUN)
    pr.inc, pr.ecc, pr.w, pr.u, pr.limb_dark = 89.9, 0.0, 90.0, list(ab), "quadratic"
    m = batman.TransitModel(pr, t, supersample_factor=3, exp_time=float(np.median(np.diff(t))))
    flat = lightcurves.detrend_raw(cfg, t, lc["raw"] * m.light_curve(pr), lc["sector"], lc["window_d"])
    tb, fb, eb = lightcurves.bin_lc(t, flat, lc["err"], cfg["search"]["bin_minutes"])
    r = search.tls(tb, fb, eb, star, ab, cfg)
    rec = search.summarize(r, star) if r is not None else None
    ok = rec is not None and abs(rec["period"] / P - 1) < 0.01 and search.passes(rec, cfg)
    return dict(tic=tic, rp=rp_re, P=P, recovered=bool(ok), rec_P=rec and rec["period"],
                sde=rec and rec["sde"], snr=rec and rec["snr"])


def injection_grid(cfg, tics, radii=(0.75, 1.0, 1.5, 2.0, 3.0), periods=(1.0, 3.0, 7.0, 15.0, 30.0)):
    import multiprocessing as mp
    rng = np.random.default_rng(11)
    tasks = [(cfg, t, r, p, float(rng.uniform(0, 1))) for t in tics for r in radii for p in periods]
    with mp.get_context("fork").Pool(cfg["resources"]["workers"]) as pool:
        res = pool.map(_inj_task, tasks, chunksize=1)
    df = pd.DataFrame(res)
    df.to_csv(os.path.join(VDIR, "out", "injection_grid.csv"), index=False)
    tab = df.pivot_table(index="rp", columns="P", values="recovered", aggfunc="mean")
    return df, tab
