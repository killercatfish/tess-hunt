"""One-off periodogram checks for the 5.45 d signal on TIC 407126408 (asked for by P. Mistry, 2026-10-12).
Not part of the pipeline. Run on Cortex from the repo root with PYTHONPATH set:

  nice -n 19 ionice -c3 .venv/bin/python scripts/periodogram_fap.py --out /tmp/pgram --procs 10 --trials 200

Same data and detrending as the robustness baseline (SPOC PDCSAP, biweight 0.61 d, TOI-913 b and
TOI-913.02 masked, 10-minute bins). Produces:
  1. GLS (generalised Lomb-Scargle) with Baluev and bootstrap false-alarm levels
  2. the spectral window of the sampling (where would aliases come from?)
  3. a periodogram of the momentum-dump times, and the dump phases folded at 5.45 d
  4. TLS (the pipeline's detector) with an empirical false-alarm probability from block-shuffled
     light curves (GLS fits sinusoids, so it is the wrong detector for a 2.4 h box at 1.8% duty
     cycle; TLS is the matched one, and we report both)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse, json, sys, warnings
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robustness_check import CFG, PRIOR, SIG, TIC, load_spoc, prep, search_arrays  # noqa: E402

PMIN, PMAX = 0.5, 40.0
P_C, P_B = SIG["period"], PRIOR[0]["period"]


def near(periods, power, target, tol=0.003):
    """Highest power within tol (fractional) of target, and its rank among local peaks."""
    m = np.abs(periods / target - 1) < tol
    i = np.flatnonzero(m)[np.argmax(power[m])]
    pk = np.flatnonzero((power[1:-1] > power[:-2]) & (power[1:-1] >= power[2:])) + 1
    rank = int(np.sum(power[pk] > power[i])) + 1
    return i, rank


def top_peaks(periods, power, n=8, sep=0.01):
    out = []
    for i in np.argsort(power)[::-1]:
        if all(abs(periods[i] / periods[j] - 1) > sep for j in out):
            out.append(i)
        if len(out) == n:
            break
    return [[float(periods[i]), float(power[i])] for i in out]


def block_shuffle(t, f, sector, rng, block_d=1.0):
    """Permute ~1-day blocks of flux within each sector, keeping the timestamps. Preserves noise on
    scales below a day (red noise, residual systematics) and destroys any coherent period."""
    out = f.copy()
    for s in np.unique(sector):
        m = np.flatnonzero(sector == s)
        blk = np.floor((t[m] - t[m].min()) / block_d).astype(int)
        ids = np.unique(blk)
        chunks = [m[blk == b] for b in ids]
        order = rng.permutation(len(chunks))
        vals = np.concatenate([f[chunks[k]] for k in order])
        out[m] = vals[:len(m)] if len(vals) >= len(m) else np.resize(vals, len(m))
    return out


_W = {}
SYST = dict(period=27.285213, t0=1644.5582, duration_h=2.844)   # pipeline iteration 1, rejected systematic


def _init(t, f, e, sec, star, ab):
    _W.update(t=t, f=f, e=e, sec=sec, star=star, ab=ab)


def run_tls(f):
    from tesshunt.search import tls
    cfg = dict(CFG)
    cfg["resources"] = dict(CFG["resources"], threads_per_worker=1)
    r = tls(_W["t"], f, _W["e"], _W["star"], _W["ab"], cfg)
    per, sde = np.asarray(r.periods), np.asarray(r.power)
    m = np.abs(per / P_C - 1) < 0.003
    return dict(period=float(r.period), sde=float(r.SDE), sde_near_5p45=float(sde[m].max()) if m.any() else None)


def _trial(seed):
    if seed < 0:                       # the real light curve, same masks
        return run_tls(_W["f"])
    rng = np.random.default_rng(seed)
    return run_tls(block_shuffle(_W["t"], _W["f"], _W["sec"], rng))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/pgram")
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--gls-only", action="store_true", help="steps 1 and 1b only")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    from astropy.timeseries import LombScargle

    sectors = load_spoc()
    srch, _ = prep(sectors, "biweight", 0.607)
    t, f, e = search_arrays(srch)
    sec = np.interp(t, srch["time"], srch["sector"]).round().astype(int)
    f = f - np.median(f)
    res = dict(n_points=int(len(t)), sectors=sorted({int(s) for s in sec}), baseline_d=float(t.max() - t.min()))
    print(res)

    # 1. GLS
    freq = np.linspace(1 / PMAX, 1 / PMIN, 400000)
    per = 1 / freq
    ls = LombScargle(t, f, e)
    pw = ls.power(freq)
    i, rank = near(per, pw, P_C)
    lvl = [0.1, 0.01, 0.001]
    baluev = ls.false_alarm_level(lvl, minimum_frequency=freq[0], maximum_frequency=freq[-1], method="baluev")
    boot = ls.false_alarm_level(lvl, minimum_frequency=freq[0], maximum_frequency=freq[-1], method="bootstrap",
                                method_kwds=dict(n_bootstraps=1000, random_seed=1))
    ib, rank_b = near(per, pw, P_B)
    res["gls"] = dict(power_at_5p45=float(pw[i]), period_at_peak=float(per[i]), rank_at_5p45=rank,
                      fap_baluev_at_5p45=float(ls.false_alarm_probability(pw[i], minimum_frequency=freq[0],
                                                                          maximum_frequency=freq[-1], method="baluev")),
                      levels=lvl, level_power_baluev=[float(x) for x in baluev], level_power_bootstrap=[float(x) for x in boot],
                      toi913b_power=float(pw[ib]), toi913b_rank=rank_b, top=top_peaks(per, pw))
    print("GLS:", {k: v for k, v in res["gls"].items() if k != "top"})

    # 1b. the same GLS with TOI-913 b left in (only the two TOI-913.02 events masked): does GLS see a
    # confirmed 920 ppm transiting planet at all? This is the fair yardstick for the 5.45 d result.
    from tesshunt.lightcurves import bin_lc
    from tesshunt.search import transit_mask as tmask
    p2 = PRIOR[1]
    m2 = tmask(srch["time"], p2["period"], p2["duration_h"] / 24, p2["t0"], CFG["search"]["mask_width_mult"])
    tb_, fb_, eb_ = bin_lc(srch["time"][~m2], srch["flux"][~m2], np.full((~m2).sum(), np.nanstd(srch["flux"][~m2])),
                           CFG["search"]["bin_minutes"])
    lsb = LombScargle(tb_, fb_ - np.median(fb_), eb_)
    pwb = lsb.power(freq)
    lvb = lsb.false_alarm_level(lvl, minimum_frequency=freq[0], maximum_frequency=freq[-1], method="baluev")
    j, rj = near(per, pwb, P_B)
    j2, rj2 = near(per, pwb, P_B / 2)
    k5, rk5 = near(per, pwb, P_C)
    fapb = lambda x: float(lsb.false_alarm_probability(x, minimum_frequency=freq[0], maximum_frequency=freq[-1], method="baluev"))
    res["gls_with_b"] = dict(level_power_baluev=[float(x) for x in lvb],
                             toi913b=dict(power=float(pwb[j]), rank=rj, fap_baluev=fapb(pwb[j])),
                             toi913b_half=dict(power=float(pwb[j2]), rank=rj2, fap_baluev=fapb(pwb[j2])),
                             cand_5p45=dict(power=float(pwb[k5]), rank=rk5, fap_baluev=fapb(pwb[k5])),
                             top=top_peaks(per, pwb))
    print("GLS with b:", res["gls_with_b"])
    if a.gls_only:
        np.savez_compressed(os.path.join(a.out, "gls_with_b.npz"), freq=freq, gls_with_b=pwb)
        json.dump(res, open(os.path.join(a.out, "gls_with_b.json"), "w"), indent=1)
        return

    # 2. spectral window of the sampling (unit flux, no mean fit)
    wls = LombScargle(t, np.ones_like(t), fit_mean=False, center_data=False)
    ww = wls.power(freq)
    iw, _ = near(per, ww, P_C)
    res["window"] = dict(power_at_5p45=float(ww[iw]), median_power=float(np.median(ww)),
                         percentile_of_5p45=float(np.mean(ww < ww[iw]) * 100), top=top_peaks(per, ww))
    # is 5.45 d an alias of b or of a strong window peak? f_c = f_b +/- f_w  ->  |f_c - f_b| = f_w ?
    fw_needed = abs(1 / P_C - 1 / P_B)
    res["window"]["alias_check"] = dict(freq_diff_c_minus_b=float(fw_needed), period_of_diff=float(1 / fw_needed),
                                        window_power_there=float(np.interp(fw_needed, freq, ww)) if fw_needed > freq[0] else None)
    print("window:", res["window"])

    # 3. momentum dumps (quality bit 32): periodogram of the dump comb and the dump phases at 5.45 d
    # the default bitmask drops the flagged cadences, so re-read the files with no mask
    import glob
    import lightkurve as lk
    dumps = []
    for fn in sorted(glob.glob(os.path.join(CFG["paths"]["cache_dir"], str(TIC), "**", "*s_lc.fits"), recursive=True)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lc = lk.read(fn, quality_bitmask="none")
        q = np.asarray(lc.quality.value if hasattr(lc.quality, "value") else lc.quality).astype(int)
        dumps.append(np.asarray(lc.time.value)[(q & 32) > 0])
    dumps = np.unique(np.round(np.concatenate(dumps), 3))
    # collapse consecutive flagged cadences into one event
    ev = dumps[np.r_[True, np.diff(dumps) > 0.05]]
    dls = LombScargle(ev, np.ones_like(ev), fit_mean=False, center_data=False)
    dp = dls.power(freq)
    idp, _ = near(per, dp, P_C)
    ph = ((ev - SIG["t0"]) / P_C + 0.5) % 1 - 0.5           # 0 = mid-transit
    half = SIG["duration_h"] / 24 / 2 / P_C
    gaps = np.diff(ev)
    res["dumps"] = dict(n_events=int(len(ev)), median_interval_d=float(np.median(gaps[gaps < 10])),
                        interval_quartiles_d=[float(x) for x in np.percentile(gaps[gaps < 10], [25, 75])],
                        dump_power_at_5p45=float(dp[idp]), dump_power_percentile=float(np.mean(dp < dp[idp]) * 100),
                        dump_top=top_peaks(per, dp),
                        n_in_transit=int(np.sum(np.abs(ph) < half)),
                        expected_in_transit=float(len(ev) * 2 * half),
                        rayleigh_z=float(len(ev) * np.abs(np.mean(np.exp(2j * np.pi * ph))) ** 2))
    print("dumps:", res["dumps"])

    # 4. TLS (the pipeline's detector) with an empirical FAP. The real detection came at pipeline
    # iteration 2, after TOI-913 b and a rejected 27.3 d systematic were masked. Reproduce that state
    # (plus TOI-913.02), then ask how often block-shuffled copies reach the same SDE anywhere in 0.5-40 d.
    from tesshunt import stellar
    from tesshunt.search import transit_mask
    m = transit_mask(t, SYST["period"], SYST["duration_h"] / 24, SYST["t0"], CFG["search"]["mask_width_mult"])
    t4, f4, e4, s4 = t[~m], f[~m] + 1.0, np.full((~m).sum(), np.std(f[~m])), sec[~m]
    star = dict(rad=0.732535, mass=0.82)
    ab = stellar.limb_darkening(TIC)
    seeds = [-1] + list(range(a.trials))
    with Pool(a.procs, initializer=_init, initargs=(t4, f4, e4, s4, star, ab)) as pool:
        out = pool.map(_trial, seeds)
    real, null = out[0], out[1:]
    nmax = np.array([o["sde"] for o in null])
    obs = real["sde_near_5p45"] if abs(real["period"] / P_C - 1) > 0.003 else real["sde"]
    k = int(np.sum(nmax >= obs))
    res["tls"] = dict(masked=["TOI-913 b", "TOI-913.02", "27.3 d systematic"], real=real, observed_sde=obs,
                      null=dict(method="1-day blocks shuffled within each sector", trials=len(null),
                                max_sde_quantiles={str(q): float(np.quantile(nmax, q)) for q in (0.5, 0.9, 0.99)},
                                max_sde_max=float(nmax.max()), n_exceeding=k, fap=k / len(null),
                                fap_upper_95=float(3.0 / len(null)) if k == 0 else None,
                                sde_near_5p45_quantiles={str(q): float(np.quantile([o["sde_near_5p45"] or 0 for o in null], q)) for q in (0.5, 0.99)}))
    print("TLS:", res["tls"])
    np.save(os.path.join(a.out, "tls_null_max_sde.npy"), nmax)
    np.savez_compressed(os.path.join(a.out, "spectra.npz"), freq=freq, gls=pw, window=ww, dumps=dp,
                        gls_levels_baluev=baluev)
    json.dump(res, open(os.path.join(a.out, "periodogram_fap.json"), "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
