"""Do the single 5.45 d transits on TIC 407126408 scatter more than noise allows, and does TOI-913 b play a part?
Raised by Josh's hand check 6 (2026-10-16). Not part of the pipeline. Light enough to run on the Mac:

  .venv-learn/bin/python scripts/single_transit_scatter.py --lc_dir ~/.cache/lightkurve/mastDownload/TESS --out /tmp/scat
  On Cortex: PYTHONPATH=. nice -n 19 ionice -c3 .venv/bin/python scripts/single_transit_scatter.py --lc_dir data/cache/407126408 --out /tmp/scat

Same detrending, masks and per-transit measure as the kill tests (scripts/robustness_check.py: biweight 0.607 d,
candidate and priors masked, central 60% of the transit, per-sector errors from out-of-transit window means).

1. scatter: chi2/dof of the single-transit depths about their weighted mean, against the same statistic at
   off-transit phases (the null). Pipeline errors already include red noise, so the null should sit near 1.
2. where the scatter lives: per-sector and per-season depths, and whether the transits nearest a TOI-913 b
   transit are the odd ones (b's mask cuts data; b's ingress/egress residuals or its detrending shoulders
   could bias a nearby 5.45 d transit).
3. b's mask width: rerun at 1.5x, 2x (pipeline), 3x and 4x b's duration.
4. timing: the expected TTV from b near 2:1 (Lithwick et al. 2012), and a per-season mid-time offset fitted
   on a grid, to see whether shifted transits could explain the scatter.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse, copy, glob, json, sys, warnings

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robustness_check as rc  # noqa: E402
from tesshunt.killtests import Ctx  # noqa: E402

SIG = dict(period=5.450138, t0=1628.647932, duration_h=2.37)   # transit fit (joint), as harmonic_systematic_test.py
B = rc.PRIOR[0]                                                   # TOI-913 b
SEASONS = {1: (12, 13), 2: (65, 66), 3: (93,), 4: (100, 101, 102)}


def load(lc_dir):
    import lightkurve as lk
    out = []
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(lc_dir), "**", "*407126408*s_lc.fits"), recursive=True)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lc = lk.read(f, flux_column="pdcsap_flux", quality_bitmask="default")
        out.append((int(lc.sector), "SPOC", lc))
    return out


def chi2(d, e):
    w = 1 / e**2
    m = np.sum(w * d) / np.sum(w)
    z = (d - m) / e
    return float(np.sum(z**2)), len(d) - 1, float(m), z


def per_transit(meas, sig, cfg, phase=0.0):
    pt = Ctx(meas, sig, rc.PRIOR, cfg).per_transit(phase=phase)
    return pt


def scatter_vs_null(meas, sig, cfg):
    pt = per_transit(meas, sig, cfg)
    c, dof, m, z = chi2(pt["depth"], pt["err"])
    k = int(np.argmax(z**2))
    c_drop = (c - z[k]**2) / (dof - 1)
    null = []
    for ph in np.arange(0.06, 0.945, 0.005):          # keep >= 2 durations (0.036 in phase) clear of the transit
        q = per_transit(meas, sig, cfg, phase=ph)
        if q is None or len(q["depth"]) < 20:
            continue
        cn, dn, mn, zn = chi2(q["depth"], q["err"])
        kn = int(np.argmax(zn**2))
        null.append((float(ph), cn / dn, (cn - zn[kn]**2) / (dn - 1), 1e6 * mn, len(q["depth"])))
    null = np.array(null)
    return pt, dict(n=len(pt["depth"]), mean_ppm=1e6 * m, chi2=c, dof=dof, chi2_dof=c / dof,
                    p_chi2=float(stats.chi2.sf(c, dof)), chi2_dof_drop_worst=c_drop,
                    worst_epoch=int(pt["epoch"][k]), worst_z=float(z[k]),
                    null_n=len(null), null_median=float(np.median(null[:, 1])),
                    null_frac_ge=float(np.mean(null[:, 1] >= c / dof)),
                    null_median_drop_worst=float(np.median(null[:, 2])),
                    null_frac_ge_drop_worst=float(np.mean(null[:, 2] >= c_drop)),
                    null_mean_depth_ppm_range=[float(null[:, 3].min()), float(null[:, 3].max())]), null


def groups(pt):
    out = {}
    for name, keyset in [("sector", {s: (s,) for s in np.unique(pt["sector"])}), ("season", SEASONS)]:
        rows = []
        for k, secs in keyset.items():
            m = np.isin(pt["sector"], secs)
            if m.sum() == 0:
                continue
            w = 1 / pt["err"][m]**2
            d = np.sum(w * pt["depth"][m]) / np.sum(w)
            rows.append((int(k), int(m.sum()), 1e6 * d, 1e6 / np.sqrt(np.sum(w)),
                         float(np.sum(((pt["depth"][m] - d) / pt["err"][m])**2) / max(m.sum() - 1, 1))))
        d, e = np.array([r[2] for r in rows]), np.array([r[3] for r in rows])
        c, dof, _, _ = chi2(d, e)
        out[name] = dict(rows=[dict(id=r[0], n=r[1], depth_ppm=r[2], err_ppm=r[3], within_chi2_dof=r[4]) for r in rows],
                         chi2=c, dof=dof, p=float(stats.chi2.sf(c, dof)))
    return out


def b_proximity(pt, meas):
    """Hours from each 5.45 d transit to the nearest b mid-transit, and the share of the transit core lost to b's mask."""
    tb = B["t0"] + np.round((pt["center"] - B["t0"]) / B["period"]) * B["period"]
    dt_h = 24 * (pt["center"] - tb)
    near = np.abs(dt_h) < 24
    d = pt["depth"]
    rho, p = stats.spearmanr(np.abs(dt_h), d)
    w = 1 / pt["err"]**2
    mean = lambda m: (1e6 * np.sum(w[m] * d[m]) / np.sum(w[m]), 1e6 / np.sqrt(np.sum(w[m]))) if m.any() else (None, None)
    # transits that would have data but fall inside b's mask (lost entirely)
    t = meas["time"]
    n = np.arange(np.floor((t.min() - SIG["t0"]) / SIG["period"]), np.ceil((t.max() - SIG["t0"]) / SIG["period"]) + 1)
    tc = SIG["t0"] + n * SIG["period"]
    has = np.array([np.any(np.abs(t - c) < 0.3 * SIG["duration_h"] / 24) for c in tc])
    lost = [int(k) for k, c, h in zip(n, tc, has) if h and int(k) not in set(pt["epoch"].tolist())]
    return dict(dt_to_b_h=dict(zip([int(x) for x in pt["epoch"]], np.round(dt_h, 2).tolist())),
                n_within_24h_of_b=int(near.sum()), depth_within_24h=mean(near), depth_beyond_24h=mean(~near),
                spearman_abs_dt_vs_depth=dict(rho=float(rho), p=float(p)),
                epochs_with_data_lost_to_b_mask=lost)


def b_mask_widths(srch_meas_by_mult, sig):
    out = []
    for mult, (meas, cfg) in srch_meas_by_mult.items():
        pt = per_transit(meas, sig, cfg)
        c, dof, m, _ = chi2(pt["depth"], pt["err"])
        out.append(dict(b_mask_mult=mult, n=len(pt["depth"]), mean_ppm=1e6 * m, chi2_dof=c / dof))
    return out


def expected_ttv(mb_earth=(4, 8, 15)):
    """Lithwick, Xie & Wu (2012) amplitude for the inner planet of a near 2:1 pair, circular orbits (free
    eccentricity can raise it; this is the forced part)."""
    Pc, Pb, j = SIG["period"], B["period"], 2
    delta = Pb / Pc * (j - 1) / j - 1
    f = -1.190 + 2.20 * delta
    msun_earth = 332946.0
    super_d = 1 / abs(j / Pb - (j - 1) / Pc)
    amp = {m: float(abs(Pc / (np.pi * j**(2 / 3) * (j - 1)**(1 / 3) * delta) * (m / msun_earth / rc.STAR["mass"]) * f) * 1440)
           for m in mb_earth}
    return dict(delta=delta, super_period_d=super_d, amplitude_min_by_b_mass_earth=amp)


def season_timing(meas, cfg, sig):
    """Best mid-time offset per season: grid over -60..+60 min, maximise the combined depth; error from a
    bootstrap over that season's transits."""
    rng = np.random.default_rng(1)
    grid = np.arange(-60, 61, 3)
    curves = {}
    for off in grid:
        s = dict(sig, t0=sig["t0"] + off / 1440)
        pt = per_transit(meas, s, cfg)
        curves[off] = pt
    out = {}
    for k, secs in SEASONS.items():
        tab = []
        for off in grid:
            pt = curves[off]
            m = np.isin(pt["sector"], secs)
            tab.append((pt["epoch"][m], pt["depth"][m], pt["err"][m]))
        ep = tab[0][0]
        best = []
        for _ in range(300):
            pick = rng.choice(len(ep), len(ep))
            sc = []
            for e_, d_, s_ in tab:
                idx = np.array([np.where(e_ == ep[i])[0][0] for i in pick if np.any(e_ == ep[i])])
                w = 1 / s_[idx]**2
                sc.append(np.sum(w * d_[idx]) / np.sum(w))
            best.append(grid[int(np.argmax(sc))])
        full = [np.sum(d_ / s_**2) / np.sum(1 / s_**2) for _, d_, s_ in tab]
        out[k] = dict(n=len(ep), best_offset_min=int(grid[int(np.argmax(full))]),
                      bootstrap_16_84_min=[float(np.percentile(best, 16)), float(np.percentile(best, 84))])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lc_dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="paper/data/robustness.json", help="pipeline per-transit table to reproduce")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sectors = load(a.lc_dir)
    print("sectors:", [s for s, _, _ in sectors])

    # reproduce the pipeline's per-transit table (robustness.json) before trusting anything new
    _, meas_rc = rc.prep(sectors, "biweight", 0.607)
    pt_rc = Ctx(meas_rc, rc.SIG, rc.PRIOR, rc.CFG).per_transit()
    res = {}
    if os.path.exists(a.ref):                             # paper/data is gitignored, so absent on Cortex
        ref = json.load(open(a.ref))["diagnostics"]["per_transit"]
        diff = np.max(np.abs(1e6 * pt_rc["depth"] - np.array([r[2] for r in ref])))
        print(f"reproduction: {len(pt_rc['depth'])} transits vs {len(ref)}; max depth difference {diff:.1f} ppm")
        res["reproduction_max_diff_ppm"] = float(diff)
    else:
        print(f"no {a.ref}: skipping the reproduction check")
    pt, res["scatter"], null = scatter_vs_null(meas_rc, SIG, rc.CFG)
    res["groups"] = groups(pt)
    res["b_proximity"] = b_proximity(pt, meas_rc)

    by_mult = {}
    for mult in (1.5, 2.0, 3.0, 4.0):
        cfg = copy.deepcopy(rc.CFG)
        cfg["search"]["mask_width_mult"] = mult
        rc.CFG = cfg                                     # prep() reads the mask width from rc.CFG
        _, m_ = rc.prep(sectors, "biweight", 0.607)
        by_mult[mult] = (m_, cfg)
    rc.CFG = by_mult[2.0][1]
    res["b_mask_widths"] = b_mask_widths(by_mult, SIG)
    res["ttv_expected"] = expected_ttv()
    res["season_timing"] = season_timing(meas_rc, rc.CFG, SIG)
    res["per_transit"] = [dict(epoch=int(e), center=float(c), depth_ppm=1e6 * float(d), err_ppm=1e6 * float(s), sector=int(q))
                          for e, c, d, s, q in zip(pt["epoch"], pt["center"], pt["depth"], pt["err"], pt["sector"])]
    np.save(os.path.join(a.out, "single_transit_null.npy"), null)
    json.dump(res, open(os.path.join(a.out, "single_transit_scatter.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "per_transit"}, indent=1))


if __name__ == "__main__":
    main()
