"""Figure for scripts/periodogram_fap.py output: GLS with false-alarm levels, the spectral window, the
momentum-dump periodogram, and the TLS null distribution.

  .venv/bin/python scripts/periodogram_fig.py /tmp/pgram200 /tmp/pglsb paper/figures/fig4_periodograms.png
(the second directory is a --gls-only run: GLS with TOI-913 b left in)
"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INK, MUTED, GRID, MARK, B = "#1f2937", "#6b7280", "#e5e7eb", "#c2410c", "#2563eb"
P_C, P_B = 5.450098, 11.099372


def mark(ax, y=0.97):
    for p, lab, c in ((P_C, "5.45 d", MARK), (P_B, "b 11.10 d", B)):
        ax.axvline(p, color=c, lw=1, ls=(0, (2, 2)), zorder=0)
        ax.text(p, y, " " + lab, color=c, fontsize=8, va="top", transform=ax.get_xaxis_transform())


def style(ax, title, ylab):
    ax.set_xscale("log"); ax.set_xlim(0.5, 40)
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    ax.set_ylabel(ylab, fontsize=9, color=MUTED); ax.tick_params(labelsize=8, colors=MUTED)
    ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)


def main(src, src_b, out):
    d = np.load(os.path.join(src, "spectra.npz"))
    r = json.load(open(os.path.join(src, "periodogram_fap.json")))
    per = 1 / d["freq"]
    fig, axs = plt.subplots(4, 1, figsize=(8, 10.5), constrained_layout=True)

    gb = np.load(os.path.join(src_b, "gls_with_b.npz"))
    rb = json.load(open(os.path.join(src_b, "gls_with_b.json")))["gls_with_b"]
    ax = axs[0]
    ax.plot(per, gb["gls_with_b"], color=INK, lw=0.5)
    for lv, pw in zip(r["gls"]["levels"], rb["level_power_baluev"]):
        ax.axhline(pw, color=MUTED, lw=0.8, ls="--")
        ax.text(40, pw, f" FAP {lv:g}", fontsize=7.5, color=MUTED, va="center")
    mark(ax)
    style(ax, "GLS with planet b left in: neither b (920 ppm) nor 5.45 d clears any FAP line (Baluev)", "GLS power")

    ax = axs[1]
    ax.plot(per, d["window"], color=INK, lw=0.5)
    mark(ax)
    style(ax, "Spectral window of the sampling (no strong window peak at or aliasing onto 5.45 d)", "window power")

    ax = axs[2]
    ax.plot(per, d["dumps"], color=INK, lw=0.5)
    mark(ax)
    dm = r["dumps"]
    style(ax, f"Periodogram of the {dm['n_events']} momentum-dump times "
              f"(0 dumps in transit; {dm['expected_in_transit']:.1f} expected)", "dump power")
    ax.set_xlabel("period (days)", fontsize=9, color=MUTED)

    ax = axs[3]
    t = r["tls"]
    null = np.load(os.path.join(src, "tls_null_max_sde.npy"))
    ax.hist(null, bins=np.arange(np.floor(null.min()), max(null.max(), t["observed_sde"]) + 1, 0.5),
            color=MUTED, edgecolor="white", lw=0.5)
    ax.axvline(t["observed_sde"], color=MARK, lw=1.5)
    ax.text(t["observed_sde"], 0.95, f" observed 5.45 d\n SDE {t['observed_sde']:.1f}", color=MARK, fontsize=8,
            va="top", transform=ax.get_xaxis_transform())
    n = t["null"]
    ax.set_title(f"TLS: highest SDE anywhere in 0.5-40 d, {n['trials']} block-shuffled light curves "
                 f"({n['n_exceeding']} reach the observed SDE)", loc="left", fontsize=10, color=INK)
    ax.set_xlabel("max TLS SDE per shuffled light curve", fontsize=9, color=MUTED)
    ax.set_ylabel("trials", fontsize=9, color=MUTED); ax.tick_params(labelsize=8, colors=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.suptitle("TIC 407126408 (TOI-913): periodogram checks for the 5.45 d candidate", fontsize=11, color=INK)
    fig.savefig(out, dpi=150)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
