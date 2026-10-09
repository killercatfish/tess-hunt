"""Per-star processing, the resumable worker pool, and run-level postprocessing."""
import json
import logging
import multiprocessing as mp
import os
import shutil
import time
import traceback

import numpy as np

from . import db, config as cfgmod

log = logging.getLogger("tesshunt")
PAUSE_FILE = os.path.join(cfgmod.ROOT, "PAUSE")


def setup_logging():
    os.makedirs(os.path.join(cfgmod.ROOT, "logs"), exist_ok=True)
    logging.basicConfig(filename=os.path.join(cfgmod.ROOT, "logs", "run.log"), level=logging.INFO,
                        format="%(asctime)s %(processName)s %(levelname)s %(message)s")


def star_params(con, tic):
    from . import stellar
    keys = ("teff", "rad", "mass", "tmag", "dist", "ra", "dec")
    row = con.execute(f"SELECT {','.join(keys)} FROM targets WHERE tic=?", (tic,)).fetchone()
    star = dict(zip(keys, row or (None,) * len(keys)), tic=tic)
    if star["rad"] is None or star["ra"] is None:
        fresh = stellar.tic_row(tic)
        star.update({k: v for k, v in fresh.items() if star.get(k) is None})
    return star


def process_star(cfg, con, tic, catalogs):
    from . import lightcurves, search, killtests, plots, stellar
    t_start = time.time()
    star = star_params(con, tic)
    sectors = lightcurves.fetch(cfg, tic)
    window = lightcurves.detrend_window(cfg, star)
    lc = lightcurves.prepare(cfg, sectors, window)
    del sectors
    ab = stellar.limb_darkening(tic)
    sigs = search.iterative(lc, star, ab, cfg)
    prior = []
    for s in sigs:
        if s["passes_threshold"]:
            s["tests"] = killtests.run_all(lc, s, prior, star, ab, catalogs, cfg)
        else:
            s["tests"] = {}
        s["verdict"] = killtests.verdict(s, cfg)
        s["score"] = killtests.score(s, cfg) if s["passes_threshold"] else None
        s["tic"] = tic
        prior.append(s)
        if s["passes_threshold"] and (s["verdict"] == "survivor" or cfg["search"].get("plot_rejected")):
            write_candidate(cfg, tic, s, lc, prior[:-1], star)
    db.save_signals(con, tic, sigs)
    secs = sorted(set(int(x) for x in np.unique(lc["sector"])))
    db.finish(con, tic, "done", teff=star.get("teff"), rad=star.get("rad"), mass=star.get("mass"),
              tmag=star.get("tmag"), ra=star.get("ra"), dec=star.get("dec"), dist=star.get("dist"),
              n_sectors=len(secs), sectors=",".join(map(str, secs)),
              baseline_d=float(lc["time"].max() - lc["time"].min()), n_points=int(len(lc["time"])),
              authors=json.dumps(sorted(set(lc["authors"].values()))),
              files_bytes=dir_bytes(lightcurves.star_cache(cfg, tic)))
    log.info("TIC %s done in %.0fs: %s", tic, time.time() - t_start,
             [(round(s["period"], 4), s["verdict"]) for s in sigs])


def write_candidate(cfg, tic, sig, lc, prior, star):
    from . import plots
    d = os.path.join(cfg["paths"]["candidates_dir"], str(tic))
    os.makedirs(d, exist_ok=True)
    png = os.path.join(d, f"sig{sig['iteration']}.png")
    plots.diagnostic(png, tic, sig, lc, prior, star, cfg)
    with open(os.path.join(d, f"sig{sig['iteration']}.json"), "w") as fh:
        json.dump({"star": star, "signal": sig}, fh, indent=1, default=db._json_default)


def dir_bytes(d):
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(d) for f in fs)


def enforce_cache(cfg, con):
    """LRU-evict raw FITS of fully processed stars while the cache is over its cap."""
    cap = cfg["resources"]["cache_max_gb"] * 1e9
    root = cfg["paths"]["cache_dir"]
    dirs = [(os.path.getmtime(os.path.join(root, d)), d) for d in os.listdir(root)]
    sizes = {d: dir_bytes(os.path.join(root, d)) for _, d in dirs}
    total = sum(sizes.values())
    if total <= cap:
        return 0
    done = {str(r[0]) for r in con.execute("SELECT tic FROM targets WHERE status='done'")}
    freed = 0
    for _, d in sorted(dirs):
        if total - freed <= cap:
            break
        if d in done:
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
            freed += sizes[d]
    log.info("cache eviction freed %.1f GB", freed / 1e9)
    return freed


def _wait_for_resources(cfg):
    import psutil
    need = cfg["resources"]["min_free_ram_gb"] * 1e9
    while os.path.exists(PAUSE_FILE) or psutil.virtual_memory().available < need:
        time.sleep(15)


def worker(cfg, labels):
    cfgmod.limit_threads(cfg["resources"]["threads_per_worker"])
    setup_logging()
    from . import crossmatch, lightcurves
    con = db.connect(cfg["paths"]["db"])
    catalogs = crossmatch.load(cfg)
    while True:
        _wait_for_resources(cfg)
        tic = db.claim_next(con, labels)
        if tic is None:
            return
        try:
            process_star(cfg, con, tic, catalogs)
        except lightcurves.NoData as ex:
            db.finish(con, tic, "nodata", error=str(ex))
        except Exception as ex:
            log.error("TIC %s failed: %s", tic, traceback.format_exc())
            db.finish(con, tic, "error", error=f"{type(ex).__name__}: {ex}"[:500])
        try:
            enforce_cache(cfg, con)
        except Exception:
            log.exception("cache eviction failed")


def run(cfg, labels=None, workers=None):
    cfgmod.limit_threads(cfg["resources"]["threads_per_worker"])
    setup_logging()
    from . import crossmatch
    con = db.connect(cfg["paths"]["db"])
    n = db.reset_stale(con)
    if n:
        log.info("requeued %d interrupted star(s)", n)
    crossmatch.load(cfg)  # fetch catalogs once, before workers race for them
    nw = workers or cfg["resources"]["workers"]
    ctx = mp.get_context("fork")
    procs = [ctx.Process(target=worker, args=(cfg, labels), name=f"w{i}") for i in range(nw)]
    for p in procs:
        p.start()
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
        db.reset_stale(con)
        raise
    postprocess(cfg)


def postprocess(cfg):
    """Run-level systematics test: a period shared by too many unrelated stars is instrumental."""
    from . import killtests
    con = db.connect(cfg["paths"]["db"])
    k = cfg["kill_tests"]
    rows = con.execute("SELECT tic, iteration, period, tests FROM signals WHERE passes_threshold=1").fetchall()
    periods = np.array([r[2] for r in rows])
    tics = np.array([r[0] for r in rows])
    with con:
        for tic, it, P, tj in rows:
            near = np.abs(periods / P - 1) < k["systematics_period_tol"]
            n_stars = len(set(tics[near].tolist()))
            inst = [x for x in k["instrumental_periods_d"] for m in (1, 2, 3, 0.5, 1 / 3)
                    if abs(P / (x * m) - 1) < k["systematics_period_tol"]]
            tests = json.loads(tj)
            tests["systematics"] = {"pass": n_stars <= k["systematics_max_targets"], "n_targets_same_period": n_stars,
                                    "near_instrumental_period": inst}
            sig = {"passes_threshold": True, "tests": tests, "snr": con.execute(
                "SELECT snr FROM signals WHERE tic=? AND iteration=?", (tic, it)).fetchone()[0]}
            v = killtests.verdict(sig, cfg)
            con.execute("UPDATE signals SET tests=?, verdict=?, score=? WHERE tic=? AND iteration=?",
                        (json.dumps(tests, default=db._json_default), v, killtests.score(sig, cfg), tic, it))
            js = os.path.join(cfg["paths"]["candidates_dir"], str(tic), f"sig{it}.json")
            if os.path.exists(js):  # keep the per-candidate summary in step with the DB
                with open(js) as fh:
                    d = json.load(fh)
                d["signal"].update(tests=tests, verdict=v)
                with open(js, "w") as fh:
                    json.dump(d, fh, indent=1, default=db._json_default)
