"""See the 5.45 d dip on TOI-913 with your own eyes, in about 40 lines you can read top to bottom.

This is deliberately NOT the pipeline. It uses only lightkurve's standard tools, so if the dip shows up
here, it is not something our own code invented. Read every line before you run it.

  cd ~/dev/TESS
  python3 -m venv .venv-learn && .venv-learn/bin/pip install lightkurve matplotlib
  .venv-learn/bin/python learn/fold_by_hand.py

It writes learn/fold_by_hand.png. The first run downloads about 8 sectors of TESS data from MAST.
"""
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

# 1. Download every 2-minute TESS light curve the SPOC pipeline made for this star, and join them.
#    stitch() divides each sector by its own median, so they line up at 1.0.
found = lk.search_lightcurve("TIC 407126408", author="SPOC", exptime=120)
print(found)                                    # look: which sectors, which years
lc = found.download_all(quality_bitmask="default").stitch().remove_nans()

# 2. The known planet TOI-913 b (11.10 d) and the two TOI-913.02 events would swamp a 200 ppm dip.
#    Mark them so the detrending ignores them and so we can cut them out. Times are BTJD (BJD - 2457000).
mask_known = lc.create_transit_mask(period=[11.099372, 1469.851],
                                    transit_time=[1636.3086, 1648.0720],
                                    duration=[2.990 / 24 * 2, 5.95 / 24 * 2])   # twice the duration, to be safe

# 3. Remove slow wiggles (star spots, spacecraft drifts) with a smoothing window of ~0.6 day.
#    720 two-minute points per day, so ~433 points; the window must be odd.
#    We do it twice, to show you the most important trap in this whole business:
#      "blind":  the filter only knows about TOI-913 b. It partly flattens the 2.4 h dip too, so the dip shrinks.
#      "masked": the filter is also told where the 5.45 d transits are, so it leaves them alone.
#    The pipeline does the second one, but only AFTER the search has found the signal. Masking stops the
#    filter eating a dip that is there; it cannot create a dip that isn't. Compare the two depths.
P, T0, DUR_H = 5.450138, 1628.647932, 2.37     # period, mid-transit time (from the transit fit), duration
mask_cand = lc.create_transit_mask(period=P, transit_time=T0, duration=DUR_H / 24 * 2)


def fold(mask_for_filter):
    flat = lc.flatten(window_length=433, mask=mask_for_filter)
    flat = flat[~mask_known]                    # now throw the known planet's transits away
    flat = flat.remove_outliers(sigma_upper=4, sigma_lower=20)   # clip upward spikes only
    # 4. Fold: stack every 5.45-day stretch on top of the others, centred on the predicted transit.
    folded = flat.fold(period=P, epoch_time=T0)
    binned = folded.bin(time_bin_size=20 / 1440)               # average into 20-minute bins
    # 5. Measure: mean flux in the middle of the transit against the flux around it.
    t, f = binned.time.value * 24, binned.flux.value           # hours from predicted mid-transit
    inside = np.abs(t) < 0.7                                   # the central ~1.4 h of a ~2.4 h transit
    outside = (np.abs(t) > 3) & (np.abs(t) < 12)
    depth = 1e6 * (np.nanmedian(f[outside]) - np.nanmean(f[inside]))
    noise = 1e6 * np.nanstd(f[outside]) / np.sqrt(inside.sum())
    return folded, t, f, depth, noise


runs = {"blind": fold(mask_known), "masked": fold(mask_known | mask_cand)}
for name, (_, _, _, depth, noise) in runs.items():
    print(f"{name:7s} depth {depth:.0f} ppm, about {depth / noise:.1f} times the noise in those bins")

# 6. Plot: grey = every single 2-minute point (you will not see the dip in these), dots = 20-minute bins.
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for ax, (name, (folded, t, f, depth, _)) in zip(axes, runs.items()):
    ax.plot(folded.time.value * 24, 1e6 * (folded.flux.value - 1), ",", color="0.8")
    ax.plot(t, 1e6 * (f - 1), "o", color="k", ms=4)
    ax.axvspan(-DUR_H / 2, DUR_H / 2, color="tab:orange", alpha=0.15, label="expected 2.4 h transit")
    ax.set(xlim=(-12, 12), ylim=(-500, 300), xlabel="hours from predicted mid-transit",
           title=f"{name} filter: depth {depth:.0f} ppm")
axes[0].set_ylabel("ppm")
axes[0].legend(loc="lower left")
fig.suptitle(f"TOI-913 folded at {P} d (TESS 2-minute data, plain lightkurve)")
fig.tight_layout()
fig.savefig("learn/fold_by_hand.png", dpi=130)
print("wrote learn/fold_by_hand.png")
