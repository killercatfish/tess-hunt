"""Download (cached), clean, detrend and stitch every available TESS sector for one star."""
import os
import re
import warnings

import numpy as np

from . import stellar


class NoData(Exception):
    pass


def star_cache(cfg, tic):
    d = os.path.join(cfg["paths"]["cache_dir"], str(tic))
    os.makedirs(d, exist_ok=True)
    return d


def choose_products(sr, cfg):
    """One product per sector, by author preference; SPOC only at the configured 2-min cadence."""
    prefs = cfg["download"]["authors"]
    best = {}
    for i, row in enumerate(sr.table):
        m = re.search(r"Sector\s+(\d+)", str(row["mission"]))
        if not m:
            continue
        sector, author = int(m.group(1)), str(row["author"])
        if author not in prefs:
            continue
        exptime = float(getattr(row["exptime"], "value", row["exptime"]))
        if author == "SPOC" and abs(exptime - cfg["download"]["spoc_exptime"]) > 1:
            continue
        rank = prefs.index(author)
        if sector not in best or rank < best[sector][0]:
            best[sector] = (rank, i, author)
    return {s: (i, a) for s, (_, i, a) in sorted(best.items())}


def _retry(fn, tries=4, wait=20):
    """MAST throws transient RemoteServiceErrors; back off rather than lose the star."""
    import time
    for k in range(tries):
        try:
            return fn()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(wait * (k + 1))


def fetch(cfg, tic):
    import lightkurve as lk
    sr = _retry(lambda: lk.search_lightcurve(f"TIC {tic}", mission="TESS"))
    chosen = choose_products(sr, cfg)
    if cfg["targets"].get("require_2min") and not any(a == "SPOC" for _, a in chosen.values()):
        raise NoData("no 2-min SPOC data")
    if not chosen:
        raise NoData("no usable light curves")
    out = []
    for sector, (i, author) in chosen.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lc = _retry(lambda: sr[i].download(download_dir=star_cache(cfg, tic), quality_bitmask="default"))
        if lc is None:
            continue
        out.append((sector, author, lc))
    if not out:
        raise NoData("downloads empty")
    return out


def detrend_window(cfg, star):
    """window = mult x the longest duration we search (central transit at period_max)."""
    p = cfg["prep"]
    tmax = stellar.expected_duration_d(cfg["search"]["period_max_d"], star.get("rad") or 0.5,
                                       star.get("mass") or 0.5)
    return float(np.clip(p["window_mult"] * tmax, p["window_min_d"], p["window_max_d"]))


def prepare(cfg, sectors, window_d):
    """Return a dict of stitched arrays. `raw` is normalized but not detrended (used for injection)."""
    from wotan import flatten
    p = cfg["prep"]
    cols = {k: [] for k in ("time", "raw", "flux", "err", "sector")}
    authors = {}
    for sector, author, lc in sectors:
        lc = lc.remove_nans()
        if len(lc) < 100:
            continue
        lc = lc.normalize()
        lc = lc.remove_outliers(sigma_upper=p["sigma_upper"], sigma_lower=np.inf)  # never clip dips
        t = np.asarray(lc.time.value, float)
        f = np.asarray(lc.flux.value, float)
        e = np.asarray(lc.flux_err.value, float)
        flat, trend = flatten(t, f, method="biweight", window_length=window_d,
                              edge_cutoff=p["edge_cutoff_d"], break_tolerance=p["break_tolerance_d"],
                              return_trend=True)
        ok = np.isfinite(flat) & np.isfinite(e) & (e > 0)
        cols["time"].append(t[ok]); cols["raw"].append(f[ok]); cols["flux"].append(flat[ok])
        cols["err"].append(e[ok] / trend[ok]); cols["sector"].append(np.full(ok.sum(), sector))
        authors[sector] = author
    if not cols["time"]:
        raise NoData("all sectors empty after cleaning")
    d = {k: np.concatenate(v) for k, v in cols.items()}
    o = np.argsort(d["time"])
    d = {k: v[o] for k, v in d.items()}
    d["authors"] = authors
    d["window_d"] = window_d
    return d


def detrend_raw(cfg, t, raw, sector, window_d):
    """Re-detrend (used after injecting a synthetic transit into the raw flux)."""
    from wotan import flatten
    p = cfg["prep"]
    out = np.empty_like(raw)
    for s in np.unique(sector):
        m = sector == s
        out[m] = flatten(t[m], raw[m], method="biweight", window_length=window_d,
                         edge_cutoff=p["edge_cutoff_d"], break_tolerance=p["break_tolerance_d"])
    return out


def bin_lc(t, f, e, minutes):
    w = minutes / 1440.0
    idx = np.floor((t - t.min()) / w).astype(np.int64)
    _, inv, cnt = np.unique(idx, return_inverse=True, return_counts=True)
    good = np.isfinite(f)
    wts = np.where(good, 1.0 / e ** 2, 0.0)
    sw = np.bincount(inv, wts)
    keep = sw > 0
    tb = (np.bincount(inv, t * (wts > 0)) / np.maximum(np.bincount(inv, (wts > 0).astype(float)), 1))[keep]
    fb = (np.bincount(inv, np.where(good, f, 0) * wts) / np.where(sw > 0, sw, 1))[keep]
    eb = (1 / np.sqrt(sw))[keep]
    return tb, fb, eb


def seasons(t, gap_d):
    """Split times into observing seasons separated by gaps > gap_d. Returns season index per point."""
    o = np.argsort(t)
    breaks = np.where(np.diff(t[o]) > gap_d)[0]
    lab = np.zeros(len(t), int)
    s = np.zeros(len(t), int)
    for b in breaks:
        s[b + 1:] += 1
    lab[o] = s
    return lab
