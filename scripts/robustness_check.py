"""One-off robustness checks for one candidate (default: the 5.45 d signal on TIC 407126408).
Not part of the pipeline. Run on Cortex from the repo root with PYTHONPATH set:

  nice -n 19 ionice -c3 .venv/bin/python scripts/robustness_check.py --out /tmp/rob --procs 6

Variants: detrending window/method, SAP vs PDCSAP, FFI products (QLP, TESS-SPOC), jackknife by
season and sector, per-transit depths, gap-edge / momentum-dump coincidence, and full TLS
re-searches with TOI-913 b and the TOI-913.02 events removed. Depths use the pipeline's kill-test
measure (central 60% of the transit, red-noise-aware per-sector errors).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse, glob, json, warnings
from multiprocessing import Pool

import numpy as np

from tesshunt import config, stellar
from tesshunt.killtests import Ctx, combine, combine_robust
from tesshunt.lightcurves import bin_lc, detrend_window, seasons
from tesshunt.search import tls, transit_mask

TIC = 407126408
SIG = dict(period=5.450098, t0=1628.6592, duration_h=2.361)
PRIOR = [dict(period=11.099372, t0=1636.3086, duration_h=2.990),     # TOI-913 b
         dict(period=1469.851, t0=1648.0720, duration_h=5.95)]       # TOI-913.02 (both events)
STAR = dict(rad=0.732535, mass=0.82, teff=4969.0)
CFG = config.load()
OUT = "/tmp/rob"


def load_spoc(flux_column="pdcsap_flux"):
    import lightkurve as lk
    files = sorted(glob.glob(os.path.join(CFG["paths"]["cache_dir"], str(TIC), "**", "*s_lc.fits"), recursive=True))
    out = []
    for f in files:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lc = lk.read(f, flux_column=flux_column, quality_bitmask="default")
        out.append((int(lc.sector), "SPOC", lc))
    return out


def load_ffi(author):
    import lightkurve as lk
    sr = lk.search_lightcurve(f"TIC {TIC}", mission="TESS", author=author)
    out = []
    for i in range(len(sr)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                lc = sr[i].download(download_dir=os.path.join(OUT, "dl"), quality_bitmask="default")
            except Exception as e:
                print(f"{author} {i}: {e}")
                continue
        if lc is not None:
            if author == "QLP":
                # QLP's own quality flags are not covered by lightkurve's default bitmask; keep only
                # cadences QLP marks good (sectors 100-102 otherwise carry 0.1x-7x junk values)
                lc = lc[np.asarray(lc.quality) == 0]
            out.append((int(lc.sector), author, lc))
    # one product per sector
    seen, uniq = set(), []
    for s, a, lc in out:
        if s not in seen:
            seen.add(s); uniq.append((s, a, lc))
    return uniq


def flatten(t, f, method, window, mask=None):
    from wotan import flatten as wf
    kw = dict(window_length=window, edge_cutoff=0.0, break_tolerance=CFG["prep"]["break_tolerance_d"], return_trend=True)
    if method == "cosine":
        kw["robust"] = True
    if mask is None:
        return wf(t, f, method=method, **kw)
    _, trend = wf(t[~mask], f[~mask], method=method, **kw)
    ok = np.isfinite(trend)
    tr = np.interp(t, t[~mask][ok], trend[ok])
    return f / tr, tr


def prep(sectors, method, window):
    """Pipeline-style prep with a chosen detrender. Returns (search_lc, measure_lc): the first is plain
    detrended (as the search sees it), the second re-detrended with candidate + priors masked
    (as the kill tests see it)."""
    cols = {k: [] for k in ("time", "raw", "flux", "flux_m", "sector")}
    mult = CFG["search"]["mask_width_mult"]
    for sector, author, lc in sectors:
        lc = lc.remove_nans()
        if len(lc) < 100:
            continue
        lc = lc.normalize().remove_outliers(sigma_upper=CFG["prep"]["sigma_upper"], sigma_lower=np.inf)
        t = np.asarray(lc.time.value, float); f = np.asarray(lc.flux.value, float)
        flat, _ = flatten(t, f, method, window)
        m = transit_mask(t, SIG["period"], SIG["duration_h"] / 24, SIG["t0"], mult)
        for p in PRIOR:
            m |= transit_mask(t, p["period"], p["duration_h"] / 24, p["t0"], mult)
        try:
            flat_m, _ = flatten(t, f, method, window, mask=m)
        except Exception:
            flat_m = flat
        ok = np.isfinite(flat) & np.isfinite(flat_m)
        for k, v in (("time", t), ("raw", f), ("flux", flat), ("flux_m", flat_m)):
            cols[k].append(v[ok])
        cols["sector"].append(np.full(ok.sum(), sector))
    d = {k: np.concatenate(v) for k, v in cols.items()}
    o = np.argsort(d["time"])
    d = {k: v[o] for k, v in d.items()}
    meas = dict(time=d["time"], flux=d["flux_m"], sector=d["sector"])
    srch = dict(time=d["time"], flux=d["flux"], sector=d["sector"])
    return srch, meas


def measure(meas):
    ctx = Ctx(meas, SIG, PRIOR, CFG)
    pt = ctx.per_transit()
    d, e = combine(pt["depth"], pt["err"])
    dr, er = combine_robust(pt["depth"], pt["err"])
    return ctx, pt, dict(depth_ppm=1e6 * d, err_ppm=1e6 * e, snr=d / e, depth_robust_ppm=1e6 * dr,
                         err_robust_ppm=1e6 * er, n_transits=int(len(pt["depth"])))


def search_arrays(srch):
    t, f, s = srch["time"], srch["flux"], srch["sector"]
    m = np.zeros(len(t), bool)
    for p in PRIOR:
        m |= transit_mask(t, p["period"], p["duration_h"] / 24, p["t0"], CFG["search"]["mask_width_mult"])
    t, f = t[~m], f[~m]
    e = np.full(len(t), np.nanstd(f))
    return bin_lc(t, f, e, CFG["search"]["bin_minutes"])


def peak_rank(r, target=SIG["period"], tol=0.002):
    from scipy.signal import find_peaks
    pw, per = np.asarray(r.power), np.asarray(r.periods)
    idx, _ = find_peaks(pw, distance=50)
    idx = idx[np.argsort(pw[idx])[::-1]]
    top = [(float(per[i]), float(pw[i])) for i in idx[:5]]
    rank = None
    for k, i in enumerate(idx):
        if abs(per[i] - target) / target < tol:
            rank = k + 1; break
    return top, rank


def run_variant(spec):
    name, source, method, window, full = spec
    try:
        ab = stellar.limb_darkening(TIC)
        if source == "PDCSAP":
            secs = load_spoc("pdcsap_flux")
        elif source == "SAP":
            secs = load_spoc("sap_flux")
        else:
            secs = load_ffi(source)
        if not secs:
            return dict(name=name, error="no data")
        win = window or detrend_window(CFG, STAR)
        srch, meas = prep(secs, method, win)
        _, _, m = measure(meas)
        res = dict(name=name, source=source, method=method, window_d=round(win, 3),
                   sectors=sorted({s for s, _, _ in secs}), **m)
        tb, fb, eb = search_arrays(srch)
        rn = tls(tb, fb, eb, STAR, ab, CFG, period_min=5.40, period_max=5.50)
        if rn is not None:
            res.update(narrow_tls_period=float(rn.period), narrow_tls_snr=float(rn.snr),
                       narrow_tls_depth_ppm=float((1 - rn.depth) * 1e6), narrow_tls_dur_h=float(rn.duration * 24))
        if full:
            rf = tls(tb, fb, eb, STAR, ab, CFG)
            if rf is not None:
                top, rank = peak_rank(rf)
                res.update(full_tls_period=float(rf.period), full_tls_sde=float(rf.SDE), full_tls_snr=float(rf.snr),
                           full_top5=top, full_rank_545=rank)
        print("done", name, flush=True)
        return res
    except Exception as e:
        import traceback; traceback.print_exc()
        return dict(name=name, error=repr(e))


def base_diagnostics():
    """Jackknife, per-transit outliers, gap-edge and momentum-dump coincidence on the baseline."""
    import lightkurve as lk
    secs = load_spoc("pdcsap_flux")
    srch, meas = prep(secs, "biweight", detrend_window(CFG, STAR))
    ctx, pt, m = measure(meas)
    d, e, s, c, k = pt["depth"], pt["err"], pt["sector"], pt["center"], pt["epoch"]
    out = dict(base=m)
    seas = seasons(c, CFG["kill_tests"]["season_gap_d"])
    jk = []
    for lab, keep in [(f"drop season {i+1} (S{','.join(map(str, sorted(set(s[seas == i]))))})", seas != i)
                      for i in np.unique(seas)] + [(f"drop S{x}", s != x) for x in np.unique(s)]:
        dd, ee = combine(d[keep], e[keep])
        jk.append((lab, 1e6 * dd, 1e6 * ee, dd / ee, int(keep.sum())))
    out["jackknife"] = jk
    mu, _ = combine(d, e)
    z = (d - mu) / e
    out["per_transit"] = [(int(a), float(b), 1e6 * float(x), 1e6 * float(y), int(q), float(zz))
                          for a, b, x, y, q, zz in zip(k, c, d, e, s, z)]
    out["outliers_3sig"] = [r for r in out["per_transit"] if abs(r[5]) > 3]
    deepest = np.argsort(d)[::-1][:3]
    keep = np.ones(len(d), bool); keep[deepest] = False
    dd, ee = combine(d[keep], e[keep])
    out["drop_3_deepest"] = (1e6 * dd, 1e6 * ee, dd / ee)
    # gap edges: segment boundaries in the cleaned time series
    t = meas["time"]
    gaps = np.where(np.diff(t) > 0.25)[0]
    edges = np.concatenate([[t[0]], t[gaps], t[gaps + 1], [t[-1]]])
    dist = np.array([np.min(np.abs(edges - x)) for x in c])
    tt = t[::10]
    exp_frac = float(np.mean([np.min(np.abs(edges - x)) < 0.5 for x in tt]))
    out["gap_edge"] = dict(frac_transits_within_0p5d=float(np.mean(dist < 0.5)), n=int(len(c)),
                           expected_frac=exp_frac, n_within=int(np.sum(dist < 0.5)))
    # momentum dumps (quality bit 32 = reaction wheel desaturation)
    files = sorted(glob.glob(os.path.join(CFG["paths"]["cache_dir"], str(TIC), "**", "*s_lc.fits"), recursive=True))
    dumps = []
    for f in files:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lc = lk.read(f, quality_bitmask="none")
        q = np.asarray(lc.quality.value if hasattr(lc.quality, "value") else lc.quality)
        dumps.append(np.asarray(lc.time.value)[(q & 32) > 0])
    dumps = np.concatenate(dumps) if dumps else np.array([])
    if len(dumps):
        dd_ = np.array([np.min(np.abs(dumps - x)) for x in c])
        exp_d = float(np.mean([np.min(np.abs(dumps - x)) < 0.1 for x in tt]))
        out["dumps"] = dict(n_dumps=int(len(dumps)), frac_transits_within_0p1d=float(np.mean(dd_ < 0.1)),
                            n_within=int(np.sum(dd_ < 0.1)), expected_frac=exp_d)
    return out


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--procs", type=int, default=6)
    a = ap.parse_args()
    OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    specs = [
        ("baseline PDCSAP biweight auto", "PDCSAP", "biweight", None, True),
        ("biweight 0.5 d", "PDCSAP", "biweight", 0.5, True),
        ("biweight 0.75 d", "PDCSAP", "biweight", 0.75, False),
        ("biweight 1.0 d", "PDCSAP", "biweight", 1.0, False),
        ("biweight 1.5 d", "PDCSAP", "biweight", 1.5, True),
        ("cosine (robust) auto", "PDCSAP", "cosine", None, True),
        ("SAP biweight auto", "SAP", "biweight", None, True),
        ("QLP (FFI) biweight auto", "QLP", "biweight", None, False),
        ("TESS-SPOC (FFI) biweight auto", "TESS-SPOC", "biweight", None, False),
    ]
    with Pool(a.procs) as pool:
        diag = pool.apply_async(base_diagnostics)
        res = pool.map(run_variant, specs, chunksize=1)
        diag = diag.get()
    json.dump(dict(variants=res, diagnostics=diag), open(os.path.join(OUT, "robustness.json"), "w"), indent=1, default=str)
    print("\nVARIANTS")
    for r in res:
        if "error" in r:
            print(f"  {r['name']:32s} ERROR {r['error']}"); continue
        line = (f"  {r['name']:32s} n={r['n_transits']:3d} depth {r['depth_ppm']:6.0f}±{r['err_ppm']:4.0f} "
                f"SNR {r['snr']:4.1f} | narrowTLS P {r.get('narrow_tls_period', np.nan):.4f} "
                f"SNR {r.get('narrow_tls_snr', np.nan):4.1f} dep {r.get('narrow_tls_depth_ppm', np.nan):4.0f}")
        if "full_tls_period" in r:
            line += (f" | fullTLS top P {r['full_tls_period']:.4f} SDE {r['full_tls_sde']:.1f} "
                     f"SNR {r['full_tls_snr']:.1f} rank(5.45)={r['full_rank_545']}")
        print(line)
        if "full_top5" in r:
            print("      top peaks: " + ", ".join(f"{p:.4f}({s:.1f})" for p, s in r["full_top5"]))
    print("\nJACKKNIFE")
    for lab, dd, ee, sn, n in diag["jackknife"]:
        print(f"  {lab:28s} n={n:3d} depth {dd:6.0f}±{ee:4.0f} SNR {sn:4.1f}")
    print("\nPER-TRANSIT >3 sigma:", diag["outliers_3sig"])
    print("drop 3 deepest:", diag["drop_3_deepest"])
    print("gap edge:", diag["gap_edge"])
    print("dumps:", diag.get("dumps"))


if __name__ == "__main__":
    main()
