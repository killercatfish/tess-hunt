"""Period search: full-grid TLS (primary), BLS cross-check, iterative masking."""
import contextlib
import io
import warnings

import numpy as np

from .lightcurves import bin_lc
from . import stellar


def _patch_tls_fill_factor():
    """TLS scales its duration estimate by a 'fill factor' (data span / baseline). For multi-year
    stitched light curves that is ~0.05, so durations come out ~20x too short and TLS's SNR (which
    integrates over that in-transit window) ~4x too low. Phase coverage doesn't depend on the gaps
    between years, so the correction is wrong for our data: neutralize it. See CHANGELOG 2026-10-09."""
    import transitleastsquares.stats as st
    st.calculate_fill_factor = lambda t: 1.0


_patch_tls_fill_factor()


def _star_kwargs(star, ab):
    r = star.get("rad") or 0.5
    m = star.get("mass") or 0.5
    return dict(R_star=r, R_star_min=max(0.1, 0.7 * r), R_star_max=1.3 * r,
                M_star=m, M_star_min=max(0.08, 0.7 * m), M_star_max=1.3 * m, u=list(ab))


def tls(t, f, e, star, ab, cfg, period_min=None, period_max=None):
    from transitleastsquares import transitleastsquares
    s = cfg["search"]
    baseline = t.max() - t.min()
    pmax = min(period_max or s["period_max_d"], baseline / 2)
    pmin = period_min or s["period_min_d"]
    if pmax <= pmin:
        return None
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        model = transitleastsquares(t, f, e)
        r = model.power(period_min=pmin, period_max=pmax, use_threads=cfg["resources"]["threads_per_worker"],
                        show_progress_bar=False, oversampling_factor=s["oversampling"],
                        duration_grid_step=s["duration_grid_step"], **_star_kwargs(star, ab))
    if not np.isfinite(r.period):
        return None
    return r


def bls_check(t, f, e, cfg):
    from astropy.timeseries import BoxLeastSquares
    s = cfg["search"]
    baseline = t.max() - t.min()
    pmax = min(s["period_max_d"], baseline / 2)
    periods = np.exp(np.linspace(np.log(s["period_min_d"]), np.log(pmax), s["bls_max_periods"]))
    r = BoxLeastSquares(t, f, e).power(periods, [0.03, 0.06, 0.1, 0.16, 0.25], objective="snr")
    return float(periods[np.argmax(r.power)])


def summarize(r, star):
    depth = (1 - r.depth) * 1e6 if np.isfinite(r.depth) else np.nan
    rp = None
    if star.get("rad") and depth > 0:
        rp = float(np.sqrt(depth / 1e6) * star["rad"] * stellar.REARTH_PER_RSUN)
    return dict(period=float(r.period), t0=float(r.T0), depth_ppm=float(depth),
                duration_h=float(r.duration * 24), sde=float(r.SDE), snr=float(r.snr),
                n_transits=int(r.distinct_transit_count), sde_source="tls", rp_rearth=rp)


def passes(sig, cfg):
    th = cfg["thresholds"]
    return bool(sig["sde"] >= th["sde_min"] and sig["snr"] >= th["snr_min"] and sig["n_transits"] >= th["min_transits"])


def transit_mask(t, period, duration_d, t0, mult):
    from transitleastsquares import transit_mask as tm
    return tm(t, period, mult * duration_d, t0)


def iterative(lc, star, ab, cfg):
    """Search, mask, re-search. Stops at the first signal below threshold (which is still recorded)."""
    s = cfg["search"]
    t, f, e = lc["time"], lc["flux"].copy(), lc["err"]
    keep = np.ones(len(t), bool)
    out = []
    for it in range(s["max_iterations"]):
        tb, fb, eb = bin_lc(t[keep], f[keep], e[keep], s["bin_minutes"])
        r = tls(tb, fb, eb, star, ab, cfg)
        if r is None:
            break
        sig = summarize(r, star)
        sig["iteration"] = it
        sig["passes_threshold"] = passes(sig, cfg)
        if it == 0:
            try:
                sig["bls_period"] = bls_check(tb, fb, eb, cfg)
            except Exception:
                sig["bls_period"] = None
        out.append(sig)
        if not sig["passes_threshold"]:
            break
        keep &= ~transit_mask(t, sig["period"], sig["duration_h"] / 24, sig["t0"], s["mask_width_mult"])
    return out
