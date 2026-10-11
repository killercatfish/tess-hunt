"""Measure eumemic's unrecovered signals in our data at their ephemeris (+ a narrow TLS search)."""
import sys, os, json, sqlite3, numpy as np, warnings
warnings.filterwarnings("ignore")
from tesshunt import config, lightcurves, stellar, search
from transitleastsquares import transitleastsquares
cfg = config.load("/tmp/ecn/config.yaml")
c = sqlite3.connect("/tmp/ecn/results.db")
jobs = [(24621747,5.20863,2458521.38358,1.6),(304655480,6.747383,2459286.75364,1.97),(422677298,12.364255,2458422.47101,3.48),
        (147163875,5.579849,2458330.74654,1.72),(48439430,0.551576,2458601.38146,1.08),(422217860,4.992141,2458931.05083,1.37),
        (247166992,10.166239,2459507.5765,2.37),(231725883,18.965313,2458420.84302,3.67),(163029327,0.946925,2458571.85816,1.73)]
out = {}
for tic, P, T0, Dh in jobs:
    T0 -= 2457000.0; D = Dh / 24
    star = stellar.tic_row(tic)
    lc = lightcurves.prepare(cfg, lightcurves.fetch(cfg, tic), lightcurves.detrend_window(cfg, star))
    others = [dict(period=r[0], t0=r[1], duration_h=r[2]) for r in c.execute(
        "select period,t0,duration_h from signals where tic=? and (snr>=7 or depth_ppm>3000)", (tic,)) if abs(r[0]/P-1) > 0.01]
    me = dict(period=P, t0=T0, duration_h=Dh)
    lc = lightcurves.redetrend_masked(cfg, lc, [me] + others)
    t, f, e = lc["time"], lc["flux"], lc["err"]
    bad = np.zeros(len(t), bool)
    for o in others:
        bad |= np.abs((t - o["t0"] + 0.5*o["period"]) % o["period"] - 0.5*o["period"]) < o["duration_h"]/24
    def depth_at(off):
        dt = (t - T0 - off*P + 0.5*P) % P - 0.5*P
        it = ~bad & (np.abs(dt) < 0.3*D); oot = ~bad & (np.abs(dt) > D) & (np.abs(dt) < 3*D)
        if it.sum() < 5 or oot.sum() < 20: return np.nan
        return 1e6*(np.median(f[oot]) - np.mean(f[it]))
    d0 = depth_at(0.0)
    nulls = np.array([depth_at(o) for o in np.linspace(0.1, 0.9, 120)]); nulls = nulls[np.isfinite(nulls)]
    sig = 1.4826*np.median(np.abs(nulls - np.median(nulls)))
    sel = ~bad
    tb, fb, eb = lightcurves.bin_lc(t[sel], f[sel], e[sel], 10)
    r = transitleastsquares(tb, fb, eb).power(period_min=P*0.99, period_max=P*1.01, oversampling_factor=5,
        R_star=star.get("rad") or 0.7, M_star=star.get("mass") or 0.7, R_star_min=0.1, R_star_max=3, M_star_min=0.1, M_star_max=3,
        use_threads=1, show_progress_bar=False)
    out[tic] = dict(P=P, depth_at_ephem_ppm=round(float(d0)), null_sigma_ppm=round(float(sig)), sigma=round(float(d0/sig), 1),
                    tls_P=round(float(r.period), 5), tls_snr=round(float(r.snr), 1), tls_depth_ppm=round(float(1e6*(1-r.depth))), tls_ntr=int(r.distinct_transit_count),
                    masked_signals=[round(o["period"], 4) for o in others])
    print(tic, json.dumps(out[tic]), flush=True)
json.dump(out, open("/tmp/ecn/fixed.json", "w"), indent=1)
