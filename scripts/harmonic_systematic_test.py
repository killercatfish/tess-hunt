"""Is the 5.45 d signal on TIC 407126408 a 1/5 harmonic of the 27.3 d systematic? (Question from P. Mistry, 2026-10-12.)
Not part of the pipeline. Run on Cortex from the repo root with PYTHONPATH set:

  nice -n 19 ionice -c3 .venv/bin/python scripts/harmonic_systematic_test.py --out /tmp/harm

A periodic systematic at period Ps puts box-search peaks at Ps/n, because folding at Ps/n stacks every systematic
event at one phase. That only works while n * P stays phase-locked to Ps across the baseline, and only with the
systematic's events in the data. This script measures both, on the same light curve, detrending and masks as the
shuffled FAP and inversion tests (scripts/periodogram_fap.py, scripts/inversion_test.py):

1. arithmetic: 5P against Ps, in units of their errors, and how far the two drift apart over the baseline;
2. for every 5.45 d transit with data, its offset from the nearest 27.3 d event;
3. the depth of the 5.45 d signal from transits far from any 27.3 d event against those near one.
If the signal were a harmonic, all of its depth would sit in the transits that coincide with 27.3 d events.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse, json, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robustness_check as rc  # noqa: E402

SYST = dict(period=27.285213, t0=1644.5582, duration_h=2.844)   # as in periodogram_fap.py (pipeline iteration 1)
SIG = dict(period=5.450138, period_err=0.000016, t0=1628.647932, duration_h=2.37)   # transit fit (joint)


def box_depth(t, f, period, t0, dur_d):
    """Mean depth in the central 60% of the transit against the local baseline (1-3 durations either side), per event."""
    out = []
    n0, n1 = int(np.floor((t.min() - t0) / period)), int(np.ceil((t.max() - t0) / period))
    for n in range(n0, n1 + 1):
        tc = t0 + n * period
        dt = np.abs(t - tc)
        inn, base = dt < 0.3 * dur_d, (dt > dur_d) & (dt < 3 * dur_d)
        if inn.sum() >= 3 and base.sum() >= 10:
            out.append(dict(epoch=n, tc=float(tc), n_in=int(inn.sum()),
                            depth=float(np.median(f[base]) - np.mean(f[inn])),
                            err=float(np.std(f[base]) / np.sqrt(inn.sum()))))
    return out


def combine(ev):
    if not ev:
        return dict(n=0)
    d, e = np.array([x["depth"] for x in ev]), np.array([x["err"] for x in ev])
    w = 1 / e**2
    m, s = float(np.sum(w * d) / np.sum(w)), float(1 / np.sqrt(np.sum(w)))
    return dict(n=len(ev), depth_ppm=1e6 * m, err_ppm=1e6 * s, snr=m / s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--near_d", type=float, default=0.5, help="'near' = within this many days of a 27.3 d event")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    P, Ps = SIG["period"], SYST["period"]
    srch, _ = rc.prep(rc.load_spoc(), "biweight", 0.607)
    t, f, _e = rc.search_arrays(srch)                      # TOI-913 b and TOI-913.02 masked, systematic NOT masked
    span = float(t.max() - t.min())
    slip = abs(5 * P - Ps) * span / Ps                      # drift of the 5:1 alignment across the baseline [d]

    ev = box_depth(t, f, P, SIG["t0"], SIG["duration_h"] / 24)
    for x in ev:
        k = np.round((x["tc"] - SYST["t0"]) / Ps)
        x["offset_from_syst_d"] = float(x["tc"] - (SYST["t0"] + k * Ps))
    near = [x for x in ev if abs(x["offset_from_syst_d"]) < a.near_d]
    far = [x for x in ev if abs(x["offset_from_syst_d"]) >= a.near_d]
    syst_ev = box_depth(t, f, Ps, SYST["t0"], SYST["duration_h"] / 24)

    res = dict(period=P, five_P=5 * P, five_P_err=5 * SIG["period_err"], syst_period=Ps,
               five_P_minus_syst_d=5 * P - Ps, baseline_d=span, alignment_slip_d=slip,
               alignment_slip_in_5p45_periods=slip / P,
               all=combine(ev), far=combine(far), near=combine(near), near_d=a.near_d,
               syst_events=combine(syst_ev), events=ev)
    json.dump(res, open(os.path.join(a.out, "harmonic_systematic_test.json"), "w"), indent=1)
    print(f"5P = {5*P:.5f} +/- {5*SIG['period_err']:.5f} d; systematic {Ps:.5f} d; difference {5*P-Ps:+.4f} d")
    print(f"baseline {span:.0f} d -> the 5:1 alignment slips {slip:.2f} d = {slip/P:.2f} of a 5.45 d period")
    for k in ("all", "far", "near"):
        print(f"{k:5s} transits: {res[k]}")
    print(f"27.3 d events themselves: {res['syst_events']}")
    print("offsets of observed 5.45 d transits from the nearest 27.3 d event [d]:",
          np.round(sorted(x["offset_from_syst_d"] for x in ev), 2).tolist())


if __name__ == "__main__":
    main()
