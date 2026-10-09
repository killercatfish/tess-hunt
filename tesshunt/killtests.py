"""Automatic kill tests. Each returns {"pass": True|False|None, ...details}. None = not applicable.

Depths are measured on full-cadence detrended flux using the central 60% of the transit, with
errors from the scatter of out-of-transit window means (per sector), so red noise is included.
"""
import numpy as np
from scipy import optimize, stats

from . import stellar
from .lightcurves import bin_lc, detrend_raw, seasons
from .search import tls, passes, summarize, transit_mask

CORE = 0.3   # half-width of the in-transit core, in units of the duration


class Ctx:
    def __init__(self, lc, sig, prior, cfg):
        self.cfg = cfg
        self.P, self.t0, self.dur = sig["period"], sig["t0"], sig["duration_h"] / 24
        mult = cfg["search"]["mask_width_mult"]
        prior_mask = np.zeros(len(lc["time"]), bool)
        for p in prior:
            prior_mask |= transit_mask(lc["time"], p["period"], p["duration_h"] / 24, p["t0"], mult)
        keep = ~prior_mask
        self.t, self.f, self.sector = lc["time"][keep], lc["flux"][keep], lc["sector"][keep]
        self.prior_mask = prior_mask
        self.oot = ~transit_mask(self.t, self.P, self.dur, self.t0, mult)
        self.noise = self._noise()

    def _noise(self):
        w = 2 * CORE * self.dur
        out = {}
        for s in np.unique(self.sector):
            m = (self.sector == s) & self.oot
            t, f = self.t[m], self.f[m]
            if len(t) < 20:
                continue
            idx = np.floor((t - t.min()) / w).astype(int)
            cnt = np.bincount(idx)
            means = np.bincount(idx, f) / np.maximum(cnt, 1)
            good = cnt >= max(2, 0.5 * np.median(cnt[cnt > 0]))
            if good.sum() < 5:
                continue
            mm = means[good]
            out[s] = 1.4826 * np.median(np.abs(mm - np.median(mm)))
        return out

    def centers(self, phase=0.0):
        n0 = np.floor((self.t.min() - self.t0) / self.P) - 1
        n1 = np.ceil((self.t.max() - self.t0) / self.P) + 1
        n = np.arange(n0, n1 + 1)
        return n, self.t0 + (n + phase) * self.P

    def per_transit(self, phase=0.0, t=None, f=None, sector=None):
        t = self.t if t is None else t
        f = self.f if f is None else f
        sector = self.sector if sector is None else sector
        n, cs = self.centers(phase)
        rows = []
        half = CORE * self.dur
        lo = np.searchsorted(t, cs - half)
        hi = np.searchsorted(t, cs + half)
        for k, c, a, b in zip(n, cs, lo, hi):
            if b - a < 2:
                continue
            s = int(np.bincount(sector[a:b]).argmax())
            if s not in self.noise:
                continue
            rows.append((int(k), c, 1 - np.mean(f[a:b]), self.noise[s], s))
        if not rows:
            return None
        k, c, d, e, s = map(np.array, zip(*rows))
        return dict(epoch=k, center=c, depth=d, err=e, sector=s)


def combine(d, e):
    w = 1 / e ** 2
    return float(np.sum(w * d) / np.sum(w)), float(1 / np.sqrt(np.sum(w)))


def combine_robust(d, e, clip=5.0):
    """As combine(), but first drop single epochs > clip sigma from the median. A real eclipse
    repeats every orbit; a few stray deep events (flares' rebound, momentum dumps, another
    signal's dips) must not masquerade as one."""
    if len(d) >= 5:
        keep = np.abs(d - np.median(d)) / e <= clip
        if keep.sum() >= 3:
            d, e = d[keep], e[keep]
    return combine(d, e)


# ---------------------------------------------------------------- individual tests

def odd_even(ctx):
    pt = ctx.per_transit()
    if pt is None:
        return {"pass": None, "why": "no transits with data"}
    odd = pt["epoch"] % 2 == 1
    if odd.sum() < 1 or (~odd).sum() < 1:
        return {"pass": None, "why": "need both odd and even transits"}
    do, eo = combine(pt["depth"][odd], pt["err"][odd])
    de, ee = combine(pt["depth"][~odd], pt["err"][~odd])
    sig = abs(do - de) / np.hypot(eo, ee)
    return {"pass": bool(sig <= ctx.cfg["kill_tests"]["odd_even_sigma"]), "sigma": sig,
            "depth_odd_ppm": do * 1e6, "depth_even_ppm": de * 1e6, "err_odd_ppm": eo * 1e6, "err_even_ppm": ee * 1e6}


def secondary(ctx):
    k = ctx.cfg["kill_tests"]
    pt = ctx.per_transit(0.5)
    if pt is None:
        return {"pass": None, "why": "no data at phase 0.5"}
    d, e = combine_robust(pt["depth"], pt["err"])
    sig_half = d / e
    step = max(ctx.dur / ctx.P / 2, 0.002)
    best = (0.0, 0.5, 0.0)
    for ph in np.arange(0.3, 0.7 + 1e-9, step)[:400]:
        p = ctx.per_transit(ph)
        if p is None:
            continue
        dd, ee = combine_robust(p["depth"], p["err"])
        if dd / ee > best[0]:
            best = (dd / ee, ph, dd)
    ok = sig_half <= k["secondary_sigma_half"] and best[0] <= k["secondary_sigma_scan"]
    return {"pass": bool(ok), "sigma_half": sig_half, "depth_half_ppm": d * 1e6,
            "scan_max_sigma": best[0], "scan_phase": best[1], "scan_depth_ppm": best[2] * 1e6}


def duration(sig, star, cfg):
    exp = stellar.expected_duration_d(sig["period"], star.get("rad"), star.get("mass"))
    if not exp:
        return {"pass": None, "why": "no stellar radius/mass"}
    ratio = sig["duration_h"] / 24 / exp
    k = cfg["kill_tests"]
    return {"pass": bool(k["duration_ratio_min"] <= ratio <= k["duration_ratio_max"]),
            "ratio": ratio, "expected_h": exp * 24}


def size(sig, cfg):
    if sig.get("rp_rearth") is None:
        return {"pass": None, "why": "no stellar radius"}
    return {"pass": bool(sig["rp_rearth"] <= cfg["kill_tests"]["max_radius_rearth"]), "rp_rearth": sig["rp_rearth"]}


def harmonic(sig, prior, cfg):
    tol = cfg["kill_tests"]["period_match_tol"]
    for p in prior:
        for ratio in (1, 2, 0.5, 3, 1 / 3):
            if abs(sig["period"] / (p["period"] * ratio) - 1) < tol:
                return {"pass": False, "matches_iteration": p["iteration"], "ratio": ratio}
    return {"pass": True}


def _trap(x, depth, t14, flat):
    t23 = flat * t14
    ax = np.abs(x)
    m = np.zeros_like(x)
    m[ax <= t23 / 2] = depth
    ramp = (ax > t23 / 2) & (ax < t14 / 2)
    if t14 > t23:
        m[ramp] = depth * (t14 / 2 - ax[ramp]) / ((t14 - t23) / 2)
    return 1 - m


def shape(ctx, sig):
    k = ctx.cfg["kill_tests"]
    ph = ((ctx.t - ctx.t0 + 0.5 * ctx.P) % ctx.P) - 0.5 * ctx.P
    w = np.abs(ph) < 1.5 * ctx.dur
    if w.sum() < 30:
        return {"pass": None, "why": "too few in-window points"}
    nb = 60
    edges = np.linspace(-1.5 * ctx.dur, 1.5 * ctx.dur, nb + 1)
    idx = np.digitize(ph[w], edges) - 1
    cnt = np.bincount(idx, minlength=nb)[:nb]
    good = cnt >= 3
    x = 0.5 * (edges[1:] + edges[:-1])[good]
    y = (np.bincount(idx, ctx.f[w], minlength=nb)[:nb] / np.maximum(cnt, 1))[good]
    scat = np.std(y[np.abs(x) > 0.75 * ctx.dur]) if np.sum(np.abs(x) > 0.75 * ctx.dur) > 5 else np.std(y)
    e = np.full_like(y, max(scat, 1e-7))
    d0 = max(sig["depth_ppm"] / 1e6, 1e-6)

    def fit(flat_bounds):
        def res(p):
            return (y - _trap(x, p[0], p[1], p[2])) / e
        lo, hi = [0, 0.3 * ctx.dur, flat_bounds[0]], [10 * d0 + 0.01, 2.5 * ctx.dur, flat_bounds[1]]
        x0 = [d0, ctx.dur, np.clip(0.7, *flat_bounds) if flat_bounds[1] > 0 else 0]
        r = optimize.least_squares(res, x0, bounds=(lo, [max(h, l + 1e-9) for l, h in zip(lo, hi)]))
        return float(np.sum(r.fun ** 2)), r.x
    chi_u, pu = fit((0.3, 1.0))
    chi_v, pv = fit((0.0, 1e-9))
    dchi = chi_u - chi_v
    if sig["snr"] < k["shape_min_snr"]:
        return {"pass": None, "why": f"SNR {sig['snr']:.1f} < {k['shape_min_snr']}: inconclusive", "dchi2_U_minus_V": dchi}
    return {"pass": bool(dchi <= k["shape_dchi2"]), "dchi2_U_minus_V": dchi, "flat_frac_U": pu[2]}


def sector_consistency(ctx):
    pt = ctx.per_transit()
    if pt is None:
        return {"pass": None, "why": "no transits with data"}
    per = {}
    for s in np.unique(pt["sector"]):
        m = pt["sector"] == s
        per[int(s)] = combine(pt["depth"][m], pt["err"][m])
    if len(per) < 2:
        return {"pass": None, "why": "transits in fewer than 2 sectors", "per_sector": per}
    d = np.array([v[0] for v in per.values()])
    e = np.array([v[1] for v in per.values()])
    mu, _ = combine(d, e)
    chi2 = float(np.sum(((d - mu) / e) ** 2))
    p = float(stats.chi2.sf(chi2, len(d) - 1))
    n_det = int(np.sum(d / e >= 1))
    return {"pass": bool(p >= ctx.cfg["kill_tests"]["sector_consistency_p"]), "chi2": chi2, "dof": len(d) - 1,
            "p": p, "sectors_with_depth_1sigma": n_det, "n_sectors": len(d),
            "per_sector_ppm": {s: (v[0] * 1e6, v[1] * 1e6) for s, v in per.items()}}


def holdout(ctx, lc, sig, star, ab):
    """Hide one season, refit period/epoch on the rest, check only at the predicted hidden times."""
    k = ctx.cfg["kill_tests"]
    lab = seasons(ctx.t, k["season_gap_d"])
    ns = lab.max() + 1
    if ns < k["holdout_min_seasons"]:
        return {"pass": None, "why": f"{ns} season(s) < {k['holdout_min_seasons']}", "n_seasons": int(ns)}
    err = lc["err"][~ctx.prior_mask]
    trials = []
    for h in range(ns):
        rest = lab != h
        tb, fb, eb = bin_lc(ctx.t[rest], ctx.f[rest], err[rest], ctx.cfg["search"]["bin_minutes"])
        r = tls(tb, fb, eb, star, ab, ctx.cfg, period_min=ctx.P * 0.98, period_max=ctx.P * 1.02)
        if r is None:
            trials.append({"season": h, "attempted": False, "why": "refit failed"})
            continue
        sub = Ctx.__new__(Ctx)
        sub.__dict__.update(ctx.__dict__)
        sub.P, sub.t0 = float(r.period), float(r.T0)
        hid = lab == h
        pt = sub.per_transit(t=ctx.t[hid], f=ctx.f[hid], sector=ctx.sector[hid])
        if pt is None:
            trials.append({"season": h, "attempted": False, "why": "no data at predicted times"})
            continue
        d, e = combine(pt["depth"], pt["err"])
        trials.append({"season": h, "attempted": True, "hit": bool(d / e >= k["holdout_hit_sigma"]),
                       "depth_ppm": d * 1e6, "sigma": d / e, "n_predicted": int(len(pt["depth"])),
                       "fit_period": float(r.period), "years": [float(ctx.t[hid].min()), float(ctx.t[hid].max())]})
    att = [x for x in trials if x["attempted"]]
    hits = sum(x["hit"] for x in att)
    if not att:
        return {"pass": None, "why": "no attempts possible", "trials": trials}
    return {"pass": bool(hits / len(att) >= k["holdout_min_hit_frac"]), "hits": hits, "attempts": len(att), "trials": trials}


def injection(ctx, lc, sig, star, ab, prior):
    """Inject a fake of the same period/depth into this star (real transits removed); must be recovered."""
    import batman
    cfg = ctx.cfg
    mult = cfg["search"]["mask_width_mult"]
    keep = ~(ctx.prior_mask | transit_mask(lc["time"], ctx.P, ctx.dur, ctx.t0, mult))
    t, raw, err, sec = lc["time"][keep], lc["raw"][keep], lc["err"][keep], lc["sector"][keep]
    pr = batman.TransitParams()
    pr.t0 = ctx.t0 + 0.37 * ctx.P
    pr.per = ctx.P
    pr.rp = float(np.sqrt(max(sig["depth_ppm"], 1) / 1e6))
    a_m = (stellar.G * (star.get("mass") or 0.5) * stellar.MSUN * (ctx.P * 86400) ** 2 / (4 * np.pi ** 2)) ** (1 / 3)
    pr.a = a_m / ((star.get("rad") or 0.5) * stellar.RSUN)
    pr.inc, pr.ecc, pr.w = 90.0, 0.0, 90.0
    pr.u, pr.limb_dark = list(ab), "quadratic"
    model = batman.TransitModel(pr, t, supersample_factor=3, exp_time=float(np.median(np.diff(t))))
    inj = raw * model.light_curve(pr)
    flat = detrend_raw(cfg, t, inj, sec, lc["window_d"])
    tb, fb, eb = bin_lc(t, flat, err, cfg["search"]["bin_minutes"])
    r = tls(tb, fb, eb, star, ab, cfg)
    if r is None:
        return {"pass": False, "why": "search failed on injected data"}
    rec = summarize(r, star)
    ok_p = abs(rec["period"] / ctx.P - 1) < cfg["kill_tests"]["injection_period_tol"]
    return {"pass": bool(ok_p and passes(rec, cfg)), "recovered_period": rec["period"], "recovered_sde": rec["sde"],
            "recovered_snr": rec["snr"], "injected_rp_rs": pr.rp}


def contamination(sig, star, cfg):
    k = cfg["kill_tests"]
    if star.get("ra") is None or star.get("tmag") is None:
        return {"pass": None, "why": "no position/Tmag"}
    depth = max(sig["depth_ppm"], 1) / 1e6
    dm = 2.5 * np.log10(k["contamination_max_eclipse"] / depth)
    nb = stellar.neighbours(star["ra"], star["dec"], k["contamination_radius_arcsec"], star["tic"])
    bright = [n for n in nb if n["tmag"] <= star["tmag"] + dm]
    return {"pass": not bright, "dmag_limit": dm, "capable_neighbours": bright[:20], "n_neighbours": len(nb)}


# ---------------------------------------------------------------- orchestration

def run_all(lc, sig, prior, star, ab, catalogs, cfg):
    from . import crossmatch
    ctx = Ctx(lc, sig, prior, cfg)
    tests = {}

    def safe(name, fn, *a):
        try:
            tests[name] = fn(*a)
        except Exception as ex:  # a broken test is recorded, never silently passed
            tests[name] = {"pass": None, "error": f"{type(ex).__name__}: {ex}"}
    safe("known", crossmatch.check, star["tic"], sig["period"], catalogs, cfg)
    safe("harmonic", harmonic, sig, prior, cfg)
    safe("odd_even", odd_even, ctx)
    safe("secondary", secondary, ctx)
    safe("duration", duration, sig, star, cfg)
    safe("size", size, sig, cfg)
    safe("shape", shape, ctx, sig)
    tests["systematics"] = {"pass": None, "why": "run-level; filled in postprocess"}
    safe("contamination", contamination, sig, star, cfg)
    safe("sector_consistency", sector_consistency, ctx)
    safe("holdout", holdout, ctx, lc, sig, star, ab)
    safe("injection", injection, ctx, lc, sig, star, ab, prior)
    return tests


def verdict(sig, cfg):
    if not sig["passes_threshold"]:
        return "below_threshold"
    hard = cfg["kill_tests"]["hard_fail"]
    if any(sig["tests"].get(n, {}).get("pass") is False for n in hard):
        return "rejected"
    return "survivor"


def failed(sig, cfg, which="hard_fail"):
    return [n for n in cfg["kill_tests"][which] if sig["tests"].get(n, {}).get("pass") is False]


def score(sig, cfg):
    """Ranking only (not a probability): SNR, boosted by holdout hits, damped by soft flags."""
    h = sig["tests"].get("holdout", {})
    boost = 1 + (h["hits"] / h["attempts"] if h.get("attempts") else 0)
    return float(sig["snr"] * boost / (1 + len(failed(sig, cfg, "soft_flag"))))
