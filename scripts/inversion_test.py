"""Inverted-light-curve test for the 5.45 d signal on TIC 407126408 (suggested by eumemic, 2026-10-12).
Not part of the pipeline. Run on Cortex from the repo root with PYTHONPATH set:

  nice -n 19 ionice -c3 .venv/bin/python scripts/inversion_test.py --out /tmp/invert --iters 4

Reflecting the flux about its median keeps the timing and timescale of every systematic but turns dips
into bumps. TLS on the inverted light curve, with the same data, detrending and masks as the shuffled
FAP test (scripts/periodogram_fap.py), shows how strong a peak this light curve's own systematics can
make. The flux is inverted right after normalising, before the upper-outlier clip and the detrend, so
the inverted copy goes through the same prep the real one did.

Each search is iterated: after a search, its top peak is masked and TLS is rerun, as the pipeline does.
The real light curve runs through the same code as a check (it should give 5.45 d at SDE about 21.8).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse, json, sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robustness_check as rc  # noqa: E402
from periodogram_fap import SYST, P_C  # noqa: E402

CFG = rc.CFG


def invert_sectors(sectors):
    out = []
    for sector, author, lc in sectors:
        lc = lc.remove_nans().normalize()
        med = np.nanmedian(lc.flux.value)
        lc.flux = (2 * med - lc.flux.value) * lc.flux.unit
        out.append((sector, author, lc))
    return out


def arrays(sectors):
    srch, _ = rc.prep(sectors, "biweight", 0.607)
    t, f, e = rc.search_arrays(srch)                          # TOI-913 b and TOI-913.02 masked
    from tesshunt.search import transit_mask
    m = transit_mask(t, SYST["period"], SYST["duration_h"] / 24, SYST["t0"], CFG["search"]["mask_width_mult"])
    t, f = t[~m], f[~m]                                       # the 27.3 d systematic, as in the FAP test
    f = f - np.median(f) + 1.0
    return t, f, np.full(len(t), np.std(f))


def iterate(job):
    label, t, f, e, iters = job
    from tesshunt import stellar
    from tesshunt.search import tls, transit_mask
    cfg = dict(CFG)
    cfg["resources"] = dict(CFG["resources"], threads_per_worker=1)
    star, ab = dict(rad=0.732535, mass=0.82), stellar.limb_darkening(rc.TIC)
    keep = np.ones(len(t), bool)
    peaks = []
    for k in range(iters):
        r = tls(t[keep], f[keep], e[keep], star, ab, cfg)
        per, sde = np.asarray(r.periods), np.asarray(r.power)
        near = np.abs(per / P_C - 1) < 0.003
        peaks.append(dict(iteration=k + 1, period=float(r.period), sde=float(r.SDE), t0=float(r.T0),
                          duration_h=float(r.duration * 24), depth_ppm=float((1 - r.depth) * 1e6),
                          n_transits_with_data=int(np.sum(np.asarray(r.per_transit_count) > 0)),
                          sde_near_5p45=float(sde[near].max()) if near.any() else None))
        print(label, peaks[-1], flush=True)
        keep &= ~transit_mask(t, r.period, r.duration, r.T0, CFG["search"]["mask_width_mult"])
    return label, peaks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/invert")
    ap.add_argument("--iters", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    real = arrays(rc.load_spoc())
    inv = arrays(invert_sectors(rc.load_spoc()))
    jobs = [("real", *real, a.iters), ("inverted", *inv, a.iters)]
    with Pool(2) as pool:
        out = dict(pool.map(iterate, jobs))
    res = dict(method="flux reflected about its median after normalising, then the same prep, masks "
                      "(TOI-913 b, TOI-913.02, 27.3 d systematic) and TLS as scripts/periodogram_fap.py",
               n_points=int(len(real[0])), real=out["real"], inverted=out["inverted"],
               inverted_max_sde=max(p["sde"] for p in out["inverted"]),
               real_sde_5p45=next((p["sde"] for p in out["real"] if abs(p["period"] / P_C - 1) < 0.003), None))
    print(json.dumps({k: v for k, v in res.items() if k not in ("real", "inverted")}, indent=1))
    json.dump(res, open(os.path.join(a.out, "inversion_test.json"), "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
