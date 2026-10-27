"""Per-survivor noise checks, run after a search (board item n1, Josh approved 2026-10-26).

Both were first done by hand for TOI-913 (scripts/periodogram_fap.py, scripts/inversion_test.py) and are on
the pre-share checklist. Each survivor is tested on the light curve the search saw when it found the signal:
the same prep, with every earlier signal on the star masked.

- fap: the empirical false-alarm probability. Flux is shuffled in 1-day blocks within each sector, which keeps
  the noise below a day (red noise, systematics) and destroys any period; TLS runs on each copy. The FAP is the
  fraction of copies whose strongest peak anywhere reaches the signal's SDE.
- inversion: the flux is reflected about its median before prep, so every systematic keeps its timing but dips
  become bumps. TLS is iterated on it as the search is; the strongest inverted peak should stay below the SDE.

Both are soft flags (ranked lower, never killed); the numbers go in the signal's tests.
"""
import json
import logging
import multiprocessing as mp
import os

import numpy as np

from . import db

log = logging.getLogger("tesshunt")
_W = {}


def block_shuffle(t, f, sector, rng, block_d):
    """Permute ~block_d blocks of flux within each sector, keeping the timestamps."""
    out = f.copy()
    for s in np.unique(sector):
        m = np.flatnonzero(sector == s)
        blk = np.floor((t[m] - t[m].min()) / block_d).astype(int)
        chunks = [m[blk == b] for b in np.unique(blk)]
        vals = np.concatenate([f[chunks[k]] for k in rng.permutation(len(chunks))])
        out[m] = vals[:len(m)]
    return out


def invert(sectors):
    """Reflect each sector's normalised flux about its median, before the clip and the detrend."""
    out = []
    for sector, author, lc in sectors:
        lc = lc.remove_nans().normalize()
        med = np.nanmedian(lc.flux.value)
        lc.flux = (2 * med - lc.flux.value) * lc.flux.unit
        out.append((sector, author, lc))
    return out


def masked(cfg, lc, prior):
    """The unbinned points the search saw after masking every earlier signal on the star."""
    from .search import transit_mask
    t = lc["time"]
    keep = np.ones(len(t), bool)
    for p in prior:
        keep &= ~transit_mask(t, p["period"], p["duration_h"] / 24, p["t0"], cfg["search"]["mask_width_mult"])
    return t[keep], lc["flux"][keep], lc["err"][keep], lc["sector"][keep]


def _tls_max(t, f, e):
    from .lightcurves import bin_lc
    from .search import tls
    tb, fb, eb = bin_lc(t, f, e, _W["cfg"]["search"]["bin_minutes"])
    r = tls(tb, fb, eb, _W["star"], _W["ab"], _W["cfg"])
    return r


def _trial(seed):
    rng = np.random.default_rng(seed)
    t, f, e, s = _W["arr"]
    r = _tls_max(t, block_shuffle(t, f, s, rng, _W["cfg"]["survivor_checks"]["fap_block_d"]), e)
    return None if r is None else (float(r.period), float(r.SDE))


def _inverted(_):
    from .search import transit_mask
    t, f, e, _s = _W["inv"]
    keep = np.ones(len(t), bool)
    peaks = []
    for k in range(_W["cfg"]["survivor_checks"]["inversion_iters"]):
        r = _tls_max(t[keep], f[keep], e[keep])
        if r is None:
            break
        peaks.append(dict(iteration=k, period=float(r.period), sde=float(r.SDE)))
        keep &= ~transit_mask(t, r.period, r.duration, r.T0, _W["cfg"]["search"]["mask_width_mult"])
    return peaks


def check(cfg, star, ab, lc, inv_lc, sig, prior, workers):
    k = cfg["survivor_checks"]
    _W.update(cfg=cfg, star=star, ab=ab, arr=masked(cfg, lc, prior), inv=masked(cfg, inv_lc, prior))
    n = k["fap_trials"]
    with mp.get_context("fork").Pool(workers) as pool:
        inv_job = pool.map_async(_inverted, [0])
        trials = [x for x in pool.map(_trial, range(n)) if x is not None]
        peaks = inv_job.get()[0]
    sdes = np.array([x[1] for x in trials])
    hits = int(np.sum(sdes >= sig["sde"]))
    fap = hits / len(sdes) if len(sdes) else None
    out = {"fap": {"pass": None if fap is None else bool(fap <= k["fap_max"]), "fap": fap, "trials": len(sdes),
                   "n_reaching_sde": hits, "signal_sde": sig["sde"], "block_d": k["fap_block_d"],
                   "null_max_sde_quantiles": {q: float(np.quantile(sdes, float(q))) for q in ("0.5", "0.9", "0.99")}
                   if len(sdes) else {}}}
    top = max((p["sde"] for p in peaks), default=None)
    out["inversion"] = {"pass": None if top is None else bool(top < sig["sde"]), "max_inverted_sde": top,
                        "signal_sde": sig["sde"], "peaks": peaks}
    return out


def run(cfg, workers=None, redo=False, tics=None):
    """Add fap and inversion to every survivor in the run's database that lacks them (or only those on `tics`),
    and re-rank them. Verdicts don't change: both are soft flags."""
    from . import killtests, lightcurves, pipeline, stellar
    con = db.connect(cfg["paths"]["db"])
    workers = workers or cfg["resources"]["workers"]
    tics = tics or [r[0] for r in con.execute("SELECT DISTINCT tic FROM signals WHERE verdict='survivor' ORDER BY tic")]
    done = 0
    for tic in tics:
        rows = con.execute("SELECT iteration, period, t0, duration_h, sde, snr, verdict, tests FROM signals "
                           "WHERE tic=? ORDER BY iteration", (tic,)).fetchall()
        sigs = [dict(iteration=r[0], period=r[1], t0=r[2], duration_h=r[3], sde=r[4], snr=r[5], verdict=r[6],
                     tests=json.loads(r[7] or "{}")) for r in rows]
        todo = [s for s in sigs if s["verdict"] == "survivor" and (redo or "fap" not in s["tests"])]
        if not todo:
            continue
        try:
            star = pipeline.star_params(con, tic)
            sectors = lightcurves.fetch(cfg, tic)
            window = lightcurves.detrend_window(cfg, star)
            lc = lightcurves.prepare(cfg, sectors, window)
            inv_lc = lightcurves.prepare(cfg, invert(sectors), window)
            ab = stellar.limb_darkening(tic)
        except Exception as ex:  # one star's missing data must not stop the rest
            log.warning("TIC %s: survivor checks skipped: %s: %s", tic, type(ex).__name__, ex)
            continue
        for s in todo:
            prior = [p for p in sigs if p["iteration"] < s["iteration"]]
            s["tests"].update(check(cfg, star, ab, lc, inv_lc, s, prior, workers))
            score = killtests.score({"snr": s["snr"], "tests": s["tests"]}, cfg)
            with con:
                con.execute("UPDATE signals SET tests=?, score=? WHERE tic=? AND iteration=?",
                            (json.dumps(s["tests"], default=db._json_default), score, tic, s["iteration"]))
            js = os.path.join(cfg["paths"]["candidates_dir"], str(tic), f"sig{s['iteration']}.json")
            if os.path.exists(js):  # keep the per-candidate summary in step with the DB
                with open(js) as fh:
                    d = json.load(fh)
                d["signal"]["tests"] = s["tests"]
                with open(js, "w") as fh:
                    json.dump(d, fh, indent=1, default=db._json_default)
            f, i = s["tests"]["fap"], s["tests"]["inversion"]
            log.info("TIC %s sig#%s P %.4f SDE %.1f: FAP %s (%s/%s), max inverted SDE %s", tic, s["iteration"],
                     s["period"], s["sde"], f["fap"], f["n_reaching_sde"], f["trials"], i["max_inverted_sde"])
            done += 1
    return done
