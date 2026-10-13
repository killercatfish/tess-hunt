"""Pixel-level check: does the flux drop come from the target or from a neighbour?

One-off vetting tool, not part of the pipeline. For each SPOC 2-min sector it stacks
difference images (local out-of-transit mean minus in-transit mean, per transit), then fits
the stack with the out-of-transit image (an empirical PSF of the target, which dominates the
light) placed either at the target or shifted to a neighbour's position. Per-pixel noise and
the null spread come from the same stack built at random off-transit phases.

  python scripts/pixel_vet.py --tic 407126408 --sig 5.450098,1628.6592,2.361 \
      --mask 11.099372,1636.3086,2.990 --out vet/407126408_sig2
"""
import argparse, json, os
import numpy as np
from scipy import ndimage
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tesshunt.stellar import is_real_star  # noqa: E402

IN_FRAC = 0.3          # in-transit = central 60% of the transit (as in the kill tests)
OOT_IN, OOT_OUT = 1.0, 3.0   # local out-of-transit window, in transit durations from mid-transit
N_NULL = 60
FIT_RADIUS = 2.5       # pixels around the target used in the fit


def parse_sig(s):
    p, t0, d = (float(x) for x in s.split(","))
    return p, t0, d / 24.0


def phase_dt(t, p, t0):
    return (t - t0 + 0.5 * p) % p - 0.5 * p


def stack(t, cube, p, t0, dur, bad, offset=0.0):
    """Mean over transits of (local OOT mean - in-transit mean). Returns image, n_events, OOT image."""
    tc = t0 + offset * p
    n = np.round((t - tc) / p)
    dt = t - (tc + n * p)
    it = (np.abs(dt) < IN_FRAC * dur) & ~bad
    oot = (np.abs(dt) > OOT_IN * dur) & (np.abs(dt) < OOT_OUT * dur) & ~bad
    diffs, oots = [], []
    shp = cube.shape[1:]
    for k in np.unique(n[it]):
        a, b = it & (n == k), oot & (n == k)
        if a.sum() < 10 or b.sum() < 30 or (dt[b] < 0).sum() < 10 or (dt[b] > 0).sum() < 10:
            continue
        # per-pixel straight-line baseline fitted on both sides, evaluated at the in-transit times
        X = np.vstack([np.ones(b.sum()), dt[b]]).T
        Y = np.nan_to_num(cube[b].reshape(b.sum(), -1))
        coef = np.linalg.lstsq(X, Y, rcond=None)[0]
        base = (np.vstack([np.ones(a.sum()), dt[a]]).T @ coef).mean(0).reshape(shp)
        diffs.append(base - np.nanmean(cube[a], 0)); oots.append(coef[0].reshape(shp))
    if not diffs:
        return None, 0, None
    return np.mean(diffs, 0), len(diffs), np.mean(oots, 0)


def fit(D, sig, M, use):
    """Least-squares amplitude of template M for image D; returns a, a_err, chi2."""
    w = use & np.isfinite(D) & np.isfinite(M) & (sig > 0)
    x, y, s = M[w], D[w], sig[w]
    a = np.sum(x * y / s**2) / np.sum(x**2 / s**2)
    return a, 1 / np.sqrt(np.sum(x**2 / s**2)), float(np.sum(((y - a * x) / s) ** 2))


def neighbours(tic, radius=60):
    from astroquery.mast import Catalogs
    r = Catalogs.query_object(f"TIC {tic}", radius=radius / 3600, catalog="TIC").to_pandas()
    return r[r.apply(is_real_star, axis=1)].reset_index(drop=True)   # drop artifacts, duplicates, galaxies


def propagate(row, jd):
    """TIC ra/dec are epoch 2000; move by proper motion to the given BJD."""
    yrs = (jd - 2451545.0) / 365.25
    pmra = 0.0 if not np.isfinite(row.pmRA) else row.pmRA
    pmde = 0.0 if not np.isfinite(row.pmDEC) else row.pmDEC
    dec = row.dec + pmde * yrs / 3.6e6
    ra = row.ra + pmra * yrs / 3.6e6 / np.cos(np.radians(row.dec))
    return ra, dec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tic", type=int, required=True)
    ap.add_argument("--sig", required=True, help="period_d,t0_btjd,duration_h")
    ap.add_argument("--mask", action="append", default=[], help="other signals to mask, same format")
    ap.add_argument("--neighbour", type=int, help="TIC of the suspect neighbour (default: brightest within 42\")")
    ap.add_argument("--out", required=True)
    ap.add_argument("--download-dir", default=os.path.expanduser("~/.lightkurve/tpf"))
    a = ap.parse_args()
    import lightkurve as lk
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    os.makedirs(a.out, exist_ok=True)
    P, T0, DUR = parse_sig(a.sig)
    masks = [parse_sig(m) for m in a.mask]

    tab = neighbours(a.tic)
    tgt = tab[tab.ID.astype(int) == a.tic].iloc[0]
    others = tab[tab.ID.astype(int) != a.tic].copy()
    others["sep"] = others.dstArcSec
    if a.neighbour:
        nb = others[others.ID.astype(int) == a.neighbour].iloc[0]
    else:
        nb = others[others.sep < 42].sort_values("Tmag").iloc[0]
    print(f"target TIC {a.tic} Tmag {tgt.Tmag:.2f}; neighbour TIC {nb.ID} Tmag {nb.Tmag:.2f} at {nb.sep:.1f}\"")

    sr = lk.search_targetpixelfile(f"TIC {a.tic}", author="SPOC", exptime=120)
    print(f"{len(sr)} TPFs")
    rows, figs = [], []
    for i in range(len(sr)):
        tpf = sr[i].download(quality_bitmask="default", download_dir=a.download_dir)
        sec = int(tpf.sector)
        t = tpf.time.value
        cube = np.asarray(tpf.flux.value, float)
        good = np.isfinite(t) & np.all(np.isfinite(cube.reshape(len(t), -1)).sum(1, keepdims=True) > 0, 1)
        t, cube = t[good], cube[good]
        bad = np.zeros(len(t), bool)
        for (p, t0, d) in masks:
            bad |= np.abs(phase_dt(t, p, t0)) < 1.0 * d  # ± one full duration around the other planet

        D, nev, O = stack(t, cube, P, T0, DUR, bad)
        if D is None:
            print(f"S{sec}: no usable transits"); continue
        nulls = []
        for off in np.linspace(0.15, 0.85, N_NULL):
            Dn, k, _ = stack(t, cube, P, T0, DUR, bad, offset=off)
            if Dn is not None and k >= max(2, nev // 2):
                nulls.append(Dn * np.sqrt(k / nev))   # rescale to this stack's event count
        nulls = np.array(nulls)
        sig = np.nanstd(nulls, 0)

        # target and neighbour pixel positions (relative offset from WCS, proper motion applied)
        jd = np.median(t) + 2457000.0
        (rt, dt_), (rn, dn) = propagate(tgt, jd), propagate(nb, jd)
        ct, rwt = tpf.wcs.all_world2pix([[rt, dt_]], 0)[0]
        cn, rwn = tpf.wcs.all_world2pix([[rn, dn]], 0)[0]
        dcol, drow = cn - ct, rwn - rwt

        # template = out-of-transit image around the target only (other stars in the cutout blanked),
        # centred on the brightest pixel within 1.5 px of the target's WCS position
        O = np.nan_to_num(O)
        yy, xx = np.indices(D.shape)
        near = np.hypot(yy - rwt, xx - ct) <= 1.5
        py, px = np.unravel_index(np.argmax(np.where(near, O, -np.inf)), O.shape)
        box = (np.abs(yy - py) <= 1) & (np.abs(xx - px) <= 1)
        cy = np.sum(yy[box] * O[box]) / np.sum(O[box]); cx = np.sum(xx[box] * O[box]) / np.sum(O[box])
        bkg = np.median(O[np.hypot(yy - cy, xx - cx) > 3.5]) if (np.hypot(yy - cy, xx - cx) > 3.5).any() else 0.0
        M0 = np.where(np.hypot(yy - cy, xx - cx) <= 3.5, np.clip(O - bkg, 0, None), 0.0)
        Mn = ndimage.shift(M0, (drow, dcol), order=3, mode="constant")
        use = np.hypot(yy - cy, xx - cx) <= FIT_RADIUS
        aT, eT, chiT = fit(D, sig, M0, use)
        aN, eN, chiN = fit(D, sig, Mn, use)
        # same comparison on each null stack: spread of dchi2 under no signal
        null_d = np.array([fit(Dn, sig, Mn, use)[2] - fit(Dn, sig, M0, use)[2] for Dn in nulls])
        # best-fit location on a fine grid
        best = (np.inf, 0, 0)
        for sy in np.linspace(-1.5, 1.5, 31):
            for sx in np.linspace(-1.5, 1.5, 31):
                c = fit(D, sig, ndimage.shift(M0, (sy, sx), order=3, mode="constant"), use)[2]
                if c < best[0]:
                    best = (c, sy, sx)
        npix = int((use & np.isfinite(D)).sum())
        row = dict(sector=sec, n_events=nev, n_null=len(nulls), npix=npix,
                   depth_target_ppm=1e6 * aT, depth_target_err_ppm=1e6 * eT, chi2_target=chiT,
                   chi2_neighbour=chiN, dchi2_N_minus_T=chiN - chiT,
                   null_dchi2_mean=float(np.mean(null_d)), null_dchi2_std=float(np.std(null_d)),
                   neighbour_offset_px=[float(dcol), float(drow)],
                   best_shift_px=[float(best[2]), float(best[1])],
                   best_shift_arcsec=float(21.0 * np.hypot(best[1], best[2])))
        rows.append(row)
        print(f"S{sec:3d} npix {npix} events {nev:2d}  depth(T) {1e6*aT:6.0f}±{1e6*eT:4.0f} ppm  "
              f"chi2 T {chiT:6.1f}  N {chiN:6.1f}  dchi2(N-T) {chiN-chiT:+6.1f}  "
              f"null {np.mean(null_d):+.1f}±{np.std(null_d):.1f}  best shift {row['best_shift_arcsec']:.1f}\"")
        figs.append((sec, D / np.where(sig > 0, sig, np.nan), M0, (cx, cy), (cx + dcol, cy + drow),
                     (cx + best[2], cy + best[1]), row))

    tot = sum(r["dchi2_N_minus_T"] for r in rows)
    null_mean = sum(r["null_dchi2_mean"] for r in rows)
    null_std = float(np.sqrt(sum(r["null_dchi2_std"] ** 2 for r in rows)))
    wd = np.array([r["depth_target_ppm"] for r in rows]); we = np.array([r["depth_target_err_ppm"] for r in rows])
    comb = float(np.sum(wd / we**2) / np.sum(1 / we**2)); comb_e = float(1 / np.sqrt(np.sum(1 / we**2)))
    summary = dict(tic=a.tic, signal=dict(period=P, t0=T0, duration_h=DUR * 24),
                   neighbour=dict(tic=int(nb.ID), tmag=float(nb.Tmag), sep_arcsec=float(nb.sep)),
                   sectors=rows, dchi2_N_minus_T_total=tot,
                   null_dchi2_total_mean=null_mean, null_dchi2_total_std=null_std,
                   pixel_depth_ppm=comb, pixel_depth_err_ppm=comb_e)
    json.dump(summary, open(os.path.join(a.out, "pixel_vet.json"), "w"), indent=1)
    print(f"\nTOTAL dchi2(neighbour - target) = {tot:+.1f}  (null: {null_mean:+.1f} ± {null_std:.1f}); "
          f"positive favours the target")
    print(f"pixel-stack depth on target: {comb:.0f} ± {comb_e:.0f} ppm")

    n = len(figs)
    fig, axs = plt.subplots(2, n, figsize=(2.6 * n, 5.6), squeeze=False)
    for j, (sec, snr, M0, pt, pn, pb, r) in enumerate(figs):
        ax = axs[0, j]
        ax.imshow(snr, origin="lower", cmap="RdBu_r", vmin=-4, vmax=4)
        ax.plot(*pt, "kx", ms=9, mew=2); ax.plot(*pn, "o", mfc="none", mec="m", ms=10, mew=2)
        ax.plot(*pb, "*", color="gold", mec="k", ms=12)
        ax.set_title(f"S{sec}  Δχ² {r['dchi2_N_minus_T']:+.1f}", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
        ax = axs[1, j]
        ax.imshow(np.log10(np.clip(M0, 1, None)), origin="lower", cmap="Greys")
        ax.plot(*pt, "kx", ms=9, mew=2); ax.plot(*pn, "o", mfc="none", mec="m", ms=10, mew=2)
        ax.set_xticks([]); ax.set_yticks([])
    axs[0, 0].set_ylabel("difference / noise")
    axs[1, 0].set_ylabel("out-of-transit")
    fig.suptitle(f"TIC {a.tic}  P={P:.5f} d   × target   ○ TIC {int(nb.ID)} ({nb.sep:.1f}\")   ★ best fit   "
                 f"total Δχ²(N−T) {tot:+.1f}", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "pixel_vet.png"), dpi=110)


if __name__ == "__main__":
    main()
