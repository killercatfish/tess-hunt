"""Per-sector centroid test: which star is the dip on? Error bars calibrated by injection.

One-off vetting tool, not part of the pipeline. Builds on pixel_vet.py (same difference-image
stacks and the same template: the target's out-of-transit image). For each SPOC 2-min sector:

  1. Fit the stacked difference image with the template shifted over a grid of positions. The
     best-fitting shift is that sector's centroid of the dip.
  2. For each star tested, inject a dip of the given depth at that star's position into the
     null stacks (the same stack built at off-transit phases, so real noise and systematics),
     and refit. The recovered positions give, per sector, where a dip on that star lands and
     how much it scatters (mean and 2x2 covariance), including any bias of the fit.
  3. Score the observed centroid against each star: d2 = (obs - mean)^T C^-1 (obs - mean).

Summed over sectors, d2 is compared with chi2 on 2 x n_sectors degrees of freedom (p_chi2). At low
SNR the fit sometimes runs off to the edge of the grid, so the recovered positions are heavy-tailed
and p_chi2 is unreliable. p_emp is the calibrated one: it draws one injected recovery per sector,
sums their d2, and asks how often that sum is at least the observed sum. A small p means the
observed centroids are unlikely if the dip is on that star. `edge` marks sectors whose centroid
ran to the grid edge (no localisation); the summary also gives p_emp without them. Run the same thing on a
known planet (TOI-913 b) as the control: its p for the target should not be small.

  python scripts/centroid_per_sector.py --tic 407126408 --sig 5.450138,1628.64793,2.369 \
      --depth-ppm 196 --mask 11.099366,1636.30922,3.273 \
      --stars 407126405,407126406,407126397 --out vet/407126408_centroids
"""
import argparse, json, os, sys
import numpy as np
from scipy import ndimage, stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_vet import parse_sig, phase_dt, stack, neighbours, propagate  # noqa: E402

N_NULL = 60
TPL_RADIUS = 4.0       # pixels of the out-of-transit image kept in the template
FIT_RADIUS = 4.0       # pixels around the target used in the fit (the 58" star is 2.8 px away)
GRID = np.round(np.arange(-3.5, 3.5001, 0.1), 3)   # trial shifts, pixels
PIX_ARCSEC = 21.0


def best_shift(D, s2, T, use):
    """Best shift for difference image D: T is (n_grid, n_pix) templates on the `use` pixels."""
    w = use & np.isfinite(D)
    y = D[use]; y = np.where(w[use], y, 0.0)
    iv = np.where(w[use], 1.0 / s2[use], 0.0)
    b = T @ (y * iv)
    c = (T ** 2) @ iv
    a = np.where(c > 0, b / np.where(c > 0, c, 1), 0.0)
    chi2 = np.sum(y ** 2 * iv) - a * b
    k = int(np.argmin(chi2))
    return k, a[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tic", type=int, required=True)
    ap.add_argument("--sig", required=True, help="period_d,t0_btjd,duration_h")
    ap.add_argument("--depth-ppm", type=float, required=True, help="dip depth injected at each star")
    ap.add_argument("--mask", action="append", default=[], help="other signals to mask, same format")
    ap.add_argument("--stars", default="", help="comma-separated TICs to test besides the target")
    ap.add_argument("--out", required=True)
    ap.add_argument("--download-dir", default=os.path.expanduser("~/.lightkurve/tpf"))
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    import lightkurve as lk
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    P, T0, DUR = parse_sig(a.sig)
    masks = [parse_sig(m) for m in a.mask]
    depth = a.depth_ppm * 1e-6

    tab = neighbours(a.tic, radius=90)
    tab["ID"] = tab.ID.astype(int)
    tgt = tab[tab.ID == a.tic].iloc[0]
    want = [a.tic] + [int(x) for x in a.stars.split(",") if x]
    stars = []
    for t in want:
        r = tab[tab.ID == t]
        if r.empty:
            sys.exit(f"TIC {t} not within 90\" or filtered out as not a real star")
        stars.append(r.iloc[0])
    for s in stars:
        print(f"TIC {s.ID}  Tmag {s.Tmag:.2f}  sep {s.dstArcSec:.1f}\"")

    sr = lk.search_targetpixelfile(f"TIC {a.tic}", author="SPOC", exptime=120)
    print(f"{len(sr)} TPFs")
    gy, gx = np.meshgrid(GRID, GRID, indexing="ij")
    gy, gx = gy.ravel(), gx.ravel()
    rows, figs = [], []
    for i in range(len(sr)):
        tpf = sr[i].download(quality_bitmask="default", download_dir=a.download_dir)
        sec = int(tpf.sector)
        t = tpf.time.value
        cube = np.asarray(tpf.flux.value, float)
        good = np.isfinite(t) & (np.isfinite(cube.reshape(len(t), -1)).sum(1) > 0)
        t, cube = t[good], cube[good]
        bad = np.zeros(len(t), bool)
        for (p, t0, d) in masks:
            bad |= np.abs(phase_dt(t, p, t0)) < 1.0 * d

        D, nev, O = stack(t, cube, P, T0, DUR, bad)
        if D is None:
            print(f"S{sec}: no usable transits"); continue
        nulls = []
        for off in np.linspace(0.15, 0.85, N_NULL):
            Dn, k, _ = stack(t, cube, P, T0, DUR, bad, offset=off)
            if Dn is not None and k >= max(2, nev // 2):
                nulls.append(Dn * np.sqrt(k / nev))
        nulls = np.array(nulls)
        s2 = np.nanvar(nulls, 0)

        jd = np.median(t) + 2457000.0
        rt, dt_ = propagate(tgt, jd)
        ct, rwt = tpf.wcs.all_world2pix([[rt, dt_]], 0)[0]
        offs = []
        for s in stars:
            rs, ds = propagate(s, jd)
            cs, rws = tpf.wcs.all_world2pix([[rs, ds]], 0)[0]
            offs.append((cs - ct, rws - rwt))

        # template: the target's out-of-transit image, as in pixel_vet.py, kept out to TPL_RADIUS
        O = np.nan_to_num(O)
        yy, xx = np.indices(D.shape)
        near = np.hypot(yy - rwt, xx - ct) <= 1.5
        py, px = np.unravel_index(np.argmax(np.where(near, O, -np.inf)), O.shape)
        box = (np.abs(yy - py) <= 1) & (np.abs(xx - px) <= 1)
        cy = np.sum(yy[box] * O[box]) / np.sum(O[box]); cx = np.sum(xx[box] * O[box]) / np.sum(O[box])
        far = np.hypot(yy - cy, xx - cx) > TPL_RADIUS
        bkg = np.median(O[far]) if far.any() else 0.0
        M0 = np.where(~far, np.clip(O - bkg, 0, None), 0.0)
        M0 /= M0.sum()                      # template sums to 1: amplitude = fraction of target flux
        flux = np.clip(O - bkg, 0, None)[~far].sum()
        use = (np.hypot(yy - cy, xx - cx) <= FIT_RADIUS) & (s2 > 0) & np.isfinite(s2)
        T = np.array([ndimage.shift(M0, (sy, sx), order=3, mode="constant")[use] for sy, sx in zip(gy, gx)])
        shifted = {j: ndimage.shift(M0, (dr, dc), order=3, mode="constant") for j, (dc, dr) in enumerate(offs)}

        k, amp = best_shift(D, s2, T, use)
        obs = np.array([gx[k], gy[k]])
        inj_flux = depth * flux             # same flux loss wherever the dip sits
        per_star = []
        for j, s in enumerate(stars):
            rec = []
            for Dn in nulls:
                kk, _ = best_shift(Dn + inj_flux * shifted[j], s2, T, use)
                rec.append((gx[kk], gy[kk]))
            rec = np.array(rec)
            mu, C = rec.mean(0), np.cov(rec.T) + np.eye(2) * 1e-4
            d = obs - mu
            d2 = float(d @ np.linalg.solve(C, d))
            per_star.append(dict(tic=int(s.ID), offset_px=[float(offs[j][0]), float(offs[j][1])],
                                 recovered_mean_px=mu.tolist(), recovered_cov_px2=C.tolist(),
                                 recovered_sd_arcsec=float(PIX_ARCSEC * np.sqrt(np.trace(C) / 2)),
                                 d2=d2, d2_injected=[float(x @ np.linalg.solve(C, x)) for x in rec - mu]))

        # observed centroid on the sky: offset and position angle (east of north) from the target
        ra_b, de_b = tpf.wcs.all_pix2world([[ct + obs[0], rwt + obs[1]]], 0)[0]
        dra = (ra_b - rt) * np.cos(np.radians(dt_)) * 3600; dde = (de_b - dt_) * 3600
        edge = bool(np.max(np.abs(obs)) >= GRID[-1] - 0.05)
        row = dict(sector=sec, edge=edge, n_events=nev, n_null=len(nulls), npix=int(use.sum()),
                   obs_shift_px=obs.tolist(), obs_offset_arcsec=float(np.hypot(dra, dde)),
                   obs_pa_deg=float(np.degrees(np.arctan2(dra, dde)) % 360),
                   amp_fraction_ppm=float(1e6 * amp), stars=per_star)
        rows.append(row)
        print(f"S{sec:3d}{'*' if edge else ' '}events {nev:2d}  centroid {row['obs_offset_arcsec']:5.1f}\" PA {row['obs_pa_deg']:5.0f}  "
              + "  ".join(f"{p['tic']}: d2 {p['d2']:6.1f} (sd {p['recovered_sd_arcsec']:4.1f}\")" for p in per_star))
        figs.append((sec, D / np.sqrt(np.where(s2 > 0, s2, np.nan)), (cx, cy), offs, obs, row))

    nsec = len(rows)
    N_SIM = 200_000

    def p_emp(j, keep):
        obs_tot = sum(r["stars"][j]["d2"] for r, k in zip(rows, keep) if k)
        sim = np.zeros(N_SIM)
        for r, k in zip(rows, keep):
            if k:
                inj = np.array(r["stars"][j]["d2_injected"])
                sim += inj[rng.integers(0, len(inj), N_SIM)]
        n_ge = int(np.sum(sim >= obs_tot))
        return obs_tot, max(n_ge, 1) / N_SIM, n_ge == 0

    summary = []
    all_ = [True] * nsec
    no_edge = [not r["edge"] for r in rows]
    for j, s in enumerate(stars):
        tot, pe, lim = p_emp(j, all_)
        tot_ne, pe_ne, lim_ne = p_emp(j, no_edge)
        pc = float(stats.chi2.sf(tot, 2 * nsec))
        summary.append(dict(tic=int(s.ID), tmag=float(s.Tmag), sep_arcsec=float(s.dstArcSec),
                            d2_total=tot, dof=2 * nsec, p_chi2=pc, p_emp=pe, p_emp_is_upper_limit=lim,
                            n_sectors_no_edge=sum(no_edge), d2_total_no_edge=tot_ne,
                            p_emp_no_edge=pe_ne, p_emp_no_edge_is_upper_limit=lim_ne))
        f = lambda p, l: ("<" if l else "") + f"{p:.2g}"
        print(f"TIC {s.ID:>10}  sep {s.dstArcSec:5.1f}\"  d2 {tot:7.1f} on {2*nsec} dof  p_chi2 {pc:.2g}  "
              f"p_emp {f(pe, lim)}   without edge sectors ({sum(no_edge)}): p_emp {f(pe_ne, lim_ne)}")
    out = dict(tic=a.tic, signal=dict(period=P, t0=T0, duration_h=DUR * 24), depth_ppm=a.depth_ppm,
               masks=[dict(period=p, t0=t0, duration_h=d * 24) for p, t0, d in masks],
               n_null=N_NULL, fit_radius_px=FIT_RADIUS, grid_step_px=float(GRID[1] - GRID[0]),
               seed=a.seed, n_sim=N_SIM, sectors=rows, summary=summary)
    json.dump(out, open(os.path.join(a.out, "centroids.json"), "w"), indent=1)

    n = len(figs)
    fig, axs = plt.subplots(1, n, figsize=(2.6 * n, 3.0), squeeze=False)
    cols = ["k", "m", "c", "orange", "g"]
    for j, (sec, snr, (cx, cy), offs, obs, row) in enumerate(figs):
        ax = axs[0, j]
        ax.imshow(snr, origin="lower", cmap="RdBu_r", vmin=-4, vmax=4)
        for q, (dc, dr) in enumerate(offs):
            ax.plot(cx + dc, cy + dr, "x" if q == 0 else "o", mfc="none", mec=cols[q % 5], color=cols[q % 5], ms=9, mew=2)
        ax.plot(cx + obs[0], cy + obs[1], "*", color="gold", mec="k", ms=12)
        ax.set_title(f"S{sec}", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(f"TIC {a.tic}  P={P:.5f} d   × target   ○ " +
                 ", ".join(f"{s['tic']} ({s['sep_arcsec']:.0f}\")" for s in summary[1:]) + "   ★ centroid",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "centroids.png"), dpi=110)


if __name__ == "__main__":
    main()
