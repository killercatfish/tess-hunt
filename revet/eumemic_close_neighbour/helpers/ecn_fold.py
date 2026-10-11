"""Export a folded, 10-min-binned CSV for TRICERATOPS. Pipeline venv + PYTHONPATH=~/dev/tess-hunt.
usage: ecn_fold.py TIC P T0_btjd DUR_h OUT.csv [maskP,maskT0,maskDur_h ...]"""
import sys, numpy as np, warnings
warnings.simplefilter("ignore")
from tesshunt import config, lightcurves, stellar
tic, P, T0, DURh, out = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
masks = [dict(zip(("period", "t0", "duration_h"), map(float, m.split(",")))) for m in sys.argv[6:]]
DUR = DURh / 24
cfg = config.load("/tmp/ecn/config.yaml")
star = stellar.tic_row(tic)
lc = lightcurves.prepare(cfg, lightcurves.fetch(cfg, tic), lightcurves.detrend_window(cfg, star))
me = dict(period=P, t0=T0, duration_h=DURh)
lc = lightcurves.redetrend_masked(cfg, lc, [me] + masks)
t, f = lc["time"], lc["flux"]
bad = np.zeros(len(t), bool)
for m in masks:
    bad |= np.abs((t - m["t0"] + 0.5 * m["period"]) % m["period"] - 0.5 * m["period"]) < m["duration_h"] / 24
dt = (t - T0 + 0.5 * P) % P - 0.5 * P
keep = ~bad & (np.abs(dt) < 3 * DUR) & np.isfinite(f)
x, y = dt[keep], f[keep]
edges = np.arange(-3 * DUR, 3 * DUR + 1e-9, 10 / 1440)
idx = np.digitize(x, edges)
rows = np.array([(x[idx == k].mean(), y[idx == k].mean(), np.std(y[idx == k]) / np.sqrt((idx == k).sum()))
                 for k in range(1, len(edges)) if (idx == k).sum() >= 5])
oot = np.abs(rows[:, 0]) > 0.75 * DUR
rows[:, 1] /= np.median(rows[oot, 1])
np.savetxt(out, rows, delimiter=",", header="time_from_mid_d,flux,flux_err", comments="")
print(tic, "sectors", sorted(set(lc["sector"].tolist())), "bins", len(rows),
      "depth ppm", round(1e6 * (1 - rows[np.abs(rows[:, 0]) < 0.3 * DUR, 1].mean())), "err ppm", round(1e6 * np.median(rows[:, 2])))
