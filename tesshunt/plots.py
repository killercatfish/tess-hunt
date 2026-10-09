"""One-page diagnostic PNG per signal."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .lightcurves import seasons  # noqa: E402
from .search import transit_mask  # noqa: E402

MARK = {True: "PASS", False: "FAIL", None: "n/a"}


def _fold(t, P, t0):
    return ((t - t0 + 0.5 * P) % P) - 0.5 * P


def _binned(x, y, lo, hi, nb):
    e = np.linspace(lo, hi, nb + 1)
    i = np.digitize(x, e) - 1
    ok = (i >= 0) & (i < nb)
    c = np.bincount(i[ok], minlength=nb)
    m = np.bincount(i[ok], y[ok], minlength=nb) / np.maximum(c, 1)
    s = np.sqrt(np.maximum(np.bincount(i[ok], y[ok] ** 2, minlength=nb) / np.maximum(c, 1) - m ** 2, 0)) / np.sqrt(np.maximum(c, 1))
    g = c >= 3
    return 0.5 * (e[1:] + e[:-1])[g], m[g], s[g]


def _foldpanel(ax, t, f, P, t0, dur, title, color="k", phase=0.0):
    x = _fold(t - phase * P, P, t0) * 24
    w = np.abs(x) < 3 * dur * 24
    ax.plot(x[w], (f[w] - 1) * 1e6, ".", ms=1, color="0.75", rasterized=True)
    bx, by, be = _binned(x[w], (f[w] - 1) * 1e6, -3 * dur * 24, 3 * dur * 24, 45)
    ax.errorbar(bx, by, be, fmt="o", ms=3, color=color, lw=0.8)
    ax.axvspan(-dur * 12, dur * 12, color="C1", alpha=0.08)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("hours from mid-transit", fontsize=8)
    ax.tick_params(labelsize=7)


def diagnostic(path, tic, sig, lc, prior, star, cfg):
    P, t0, dur = sig["period"], sig["t0"], sig["duration_h"] / 24
    keep = np.ones(len(lc["time"]), bool)
    for p in prior:
        keep &= ~transit_mask(lc["time"], p["period"], p["duration_h"] / 24, p["t0"], cfg["search"]["mask_width_mult"])
    t, f, sec = lc["time"][keep], lc["flux"][keep], lc["sector"][keep]
    tests = sig["tests"]
    depth = sig["depth_ppm"]
    ylim = (-max(3 * depth, 1500), max(1.5 * depth, 1000))

    fig = plt.figure(figsize=(17, 13))
    gs = fig.add_gridspec(4, 4, hspace=0.55, wspace=0.28)

    ax = fig.add_subplot(gs[0, :])
    lab = seasons(t, cfg["kill_tests"]["season_gap_d"])
    # compress the gaps between seasons so a multi-year light curve stays readable
    xs, off, ticks = np.empty_like(t), 0.0, []
    for s in range(lab.max() + 1):
        m = lab == s
        xs[m] = t[m] - t[m].min() + off
        ticks.append((off, f"{t[m].min():.0f}"))
        off = xs[m].max() + 15
    bx, by, _ = _binned(xs, (f - 1) * 1e6, xs.min(), xs.max(), int((xs.max() - xs.min()) * 24 * 2))
    ax.plot(bx, by, ".", ms=1.5, color="k", rasterized=True)
    intr = transit_mask(t, P, dur, t0, 1.0)
    ax.plot(xs[intr], np.full(intr.sum(), ylim[0] * 0.9), "|", color="C3", ms=4)
    for x0, lbl in ticks:
        ax.axvline(x0 - 7, color="0.6", lw=0.5)
        ax.text(x0, ylim[1] * 0.85, f"BTJD {lbl}", fontsize=7, color="0.4")
    ax.set_ylim(ylim)
    ax.set_title(f"TIC {tic}  sig#{sig['iteration']}: detrended, 30-min bins, seasons compressed (red ticks = predicted transits)", fontsize=10)
    ax.set_ylabel("ppm", fontsize=8)

    ax = fig.add_subplot(gs[1, :2])
    _foldpanel(ax, t, f, P, t0, dur, f"phase-folded  P={P:.5f} d  depth={depth:.0f} ppm  dur={sig['duration_h']:.2f} h")
    ax.set_ylim(ylim)

    epoch = np.round((t - t0) / P).astype(int)
    oe = tests.get("odd_even", {})
    for j, (name, m) in enumerate((("odd", epoch % 2 == 1), ("even", epoch % 2 == 0))):
        ax = fig.add_subplot(gs[1, 2 + j])
        d = oe.get(f"depth_{name}_ppm")
        _foldpanel(ax, t[m], f[m], P, t0, dur, f"{name}: {d:.0f} ppm" if d is not None else name, color="C0" if j else "C2")
        ax.axhline(-depth, color="C3", lw=0.6, ls="--")
        ax.set_ylim(ylim)

    ax = fig.add_subplot(gs[2, 0])
    sc = tests.get("secondary", {})
    _foldpanel(ax, t, f, P, t0, dur, f"phase 0.5: {sc.get('sigma_half', float('nan')):.1f}σ; scan max {sc.get('scan_max_sigma', float('nan')):.1f}σ", phase=0.5)
    ax.set_ylim(ylim)

    ax = fig.add_subplot(gs[2, 1])
    ps = tests.get("sector_consistency", {}).get("per_sector_ppm", {})
    if ps:
        ks = sorted(ps, key=int)
        ax.errorbar(range(len(ks)), [ps[k][0] for k in ks], [ps[k][1] for k in ks], fmt="o", ms=3)
        ax.set_xticks(range(len(ks)))
        ax.set_xticklabels(ks, fontsize=6, rotation=90)
        ax.axhline(depth, color="C3", lw=0.6, ls="--")
        ax.axhline(0, color="0.5", lw=0.5)
    ax.set_title(f"depth per sector (p={tests.get('sector_consistency', {}).get('p', float('nan')):.3g})", fontsize=9)
    ax.tick_params(labelsize=7)

    ax = fig.add_subplot(gs[2, 2])
    ho = tests.get("holdout", {})
    tr = [x for x in ho.get("trials", []) if x.get("attempted")]
    if tr:
        ax.bar(range(len(tr)), [x["sigma"] for x in tr], color=["C2" if x["hit"] else "C3" for x in tr])
        ax.axhline(cfg["kill_tests"]["holdout_hit_sigma"], color="k", lw=0.6, ls="--")
        ax.set_xticks(range(len(tr)))
        ax.set_xticklabels([f"BTJD {x['years'][0]:.0f}" for x in tr], fontsize=6, rotation=30)
        ax.set_title(f"holdout: {ho['hits']}/{ho['attempts']} hidden seasons hit (σ at predicted times)", fontsize=9)
    else:
        ax.set_title(f"holdout: {ho.get('why', 'n/a')}", fontsize=9)
    ax.tick_params(labelsize=7)

    ax = fig.add_subplot(gs[2, 3])
    ax.axis("off")
    lines = [f"TIC {tic}  Teff={star.get('teff')}  R*={star.get('rad')}  M*={star.get('mass')}  Tmag={star.get('tmag')}",
             f"SDE={sig['sde']:.1f}  SNR={sig['snr']:.1f}  N_tr={sig['n_transits']}  Rp={sig.get('rp_rearth') or float('nan'):.2f} R⊕",
             f"BLS cross-check P={sig.get('bls_period')}", f"VERDICT: {sig.get('verdict')}", ""]
    for name, r in tests.items():
        if name == "systematics" and r.get("pass") is None:
            lines.append("run  systematics: run-level, see report/json")
            continue
        extra = r.get("why") or r.get("error") or ""
        lines.append(f"{MARK.get(r.get('pass'))}  {name} {extra[:38]}")
    ax.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=7.5)

    lab_all = seasons(t, cfg["kill_tests"]["season_gap_d"])
    for j, s in enumerate(range(min(lab_all.max() + 1, 4))):
        ax = fig.add_subplot(gs[3, j])
        m = lab_all == s
        secs = sorted(set(sec[m].tolist()))
        _foldpanel(ax, t[m], f[m], P, t0, dur, f"season {s + 1}: sectors {secs[0]}–{secs[-1]}")
        ax.axhline(-depth, color="C3", lw=0.6, ls="--")
        ax.set_ylim(ylim)

    fig.savefig(path, dpi=80)
    plt.close(fig)
