"""Run-level systematics test, shared by pipeline.postprocess and scripts/calibration_report.py (numpy only, so
the report can run without the search stack)."""
import numpy as np


def systematics_counts(period, t0, dur_h, tic, sectors, cfg):
    """For each threshold-passing signal (arrays, one entry per signal; `sectors` maps tic -> set of sectors), count
    the stars with a signal at the same period (within systematics_period_tol), and of those, the stars whose dips
    also land at the same times in a sector both were observed in. An instrumental signal (or one eclipsing binary
    leaking into several apertures) dips at the same moments in every star it touches; unrelated stars only share
    a period by chance, and how often they do grows with the size of the run and with how crowded that stretch of
    period is (signals pile up near the 40 d ceiling). Calibration, 10/28: by period alone the test killed 25 of
    234 confirmed planets over the 698-star set; with matching transit times, none.
    Returns (n_same_period, n_same_times), each counting the signal's own star."""
    k = cfg["kill_tests"]
    period, t0, dur = (np.asarray(x, float) for x in (period, t0, dur_h))
    dur = dur / 24
    tic = np.asarray(tic)
    n_per, n_times = [], []
    for p, t, d, s in zip(period, t0, dur, tic):
        same_p, same_t = {s}, {s}
        for j in np.where(np.abs(period / p - 1) < k["systematics_period_tol"])[0]:
            if tic[j] == s:
                continue
            same_p.add(tic[j])
            if not (sectors.get(s, set()) & sectors.get(tic[j], set())):
                continue
            n = round((t0[j] - t) / p)   # cycles between the two reference transits; allow the period mismatch to drift
            if abs(t0[j] - (t + n * p)) <= 0.5 * (d + dur[j]) + abs(n) * abs(period[j] - p):
                same_t.add(tic[j])
        n_per.append(len(same_p))
        n_times.append(len(same_t))
    return n_per, n_times
