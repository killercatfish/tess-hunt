"""Compare our per-sector centroids (centroid_per_sector.py) with eumemic's, on the sky.

One-off vetting tool, not part of the pipeline. Reads our centroids.json and eumemic's
validation/centroid_sectors_per_sector.csv.gz, puts both in arcsec east/north of the target, and
runs eumemic's two tests on each set:

  F test:     scatter of the n sector centroids about their mean is the common per-sector error;
              F = (n |mean - s|^2 / 2) / (RSS / (2(n - 1))) against F(2, 2(n - 1)).
  sign flip:  |mean(c_i - s)| against all 2^n sign flips of the vectors c_i - s.

Each test is run twice per star: against the star's catalogue position s, and against where our
injections say a dip on that star is actually measured (recovered mean, per sector). The second
version allows for the fit pulling a faint neighbour's dip toward the target. Pixel offsets are
turned into arcsec with a per-sector linear map fitted to the catalogue stars' pixel offsets.

  python scripts/compare_centroids.py --ours paper/data/centroids_s196.json \
      --theirs centroid_sectors_per_sector.csv.gz --key extra_407126408_5.45017 \
      --out paper/data/centroids_compare_s196
"""
import argparse, itertools, json, os
import numpy as np
import pandas as pd
from scipy import stats

EPOCH_JD = 2460400.0    # ~2024, middle of the sectors; proper motions here are tiny anyway


def sky_offsets(tic, tics):
    """Arcsec east/north of the target for each TIC, propagated to EPOCH_JD."""
    from astroquery.mast import Catalogs
    r = Catalogs.query_object(f"TIC {tic}", radius=90 / 3600, catalog="TIC").to_pandas()
    r["ID"] = r.ID.astype(int)
    yrs = (EPOCH_JD - 2451545.0) / 365.25
    out = {}
    for t in tics:
        s = r[r.ID == t].iloc[0]
        pmra = 0.0 if not np.isfinite(s.pmRA) else s.pmRA
        pmde = 0.0 if not np.isfinite(s.pmDEC) else s.pmDEC
        out[t] = (s.ra + pmra * yrs / 3.6e6 / np.cos(np.radians(s.dec)), s.dec + pmde * yrs / 3.6e6)
    ra0, de0 = out[tic]
    return {t: np.array([(ra - ra0) * np.cos(np.radians(de0)) * 3600, (de - de0) * 3600])
            for t, (ra, de) in out.items()}


def f_test(res):
    """res: (n, 2) residuals c_i - s. Returns (F, p)."""
    n = len(res)
    m = res.mean(0)
    rss = np.sum((res - m) ** 2)
    F = (n * m @ m / 2) / (rss / (2 * (n - 1)))
    return F, stats.f.sf(F, 2, 2 * (n - 1))


def sign_flip(res):
    """Exact sign-flip p for |mean(res)|: the fraction of the 2^n flips at least as large."""
    n = len(res)
    obs = np.linalg.norm(res.mean(0))
    flips = np.array(list(itertools.product([1, -1], repeat=n)))
    sims = np.linalg.norm(flips @ res / n, axis=1)
    return float(np.mean(sims >= obs - 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", required=True)
    ap.add_argument("--theirs", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    ours = json.load(open(a.ours))
    tic = ours["tic"]
    tics = [s["tic"] for s in ours["sectors"][0]["stars"]]
    sky = sky_offsets(tic, tics)

    th = pd.read_csv(a.theirs)
    th = th[th.key == a.key].set_index("sector")

    rows, recov = [], {t: [] for t in tics}
    for r in ours["sectors"]:
        others = [s for s in r["stars"] if s["tic"] != tic]
        P = np.array([s["offset_px"] for s in others])           # (k, 2) column, row
        S = np.array([sky[s["tic"]] for s in others])            # (k, 2) east, north
        A, *_ = np.linalg.lstsq(P, S, rcond=None)                # sky = px @ A
        fit_rms = float(np.sqrt(np.mean((P @ A - S) ** 2)))
        ours_en = np.array(r["obs_shift_px"]) @ A
        for s in r["stars"]:
            recov[s["tic"]].append(np.array(s["recovered_mean_px"]) @ A)
        sd = r["stars"][0]["recovered_sd_arcsec"]                # dip-on-target recovery scatter
        row = dict(sector=r["sector"], edge=r["edge"], ours_east=ours_en[0], ours_north=ours_en[1],
                   ours_inj_sd_arcsec=sd, map_rms_arcsec=fit_rms)
        if r["sector"] in th.index:
            t = th.loc[r["sector"]]
            row.update(theirs_east=t.east, theirs_north=t.north, theirs_quality=t.quality,
                       diff_arcsec=float(np.hypot(ours_en[0] - t.east, ours_en[1] - t.north)))
        rows.append(row)
    tab = pd.DataFrame(rows)
    tab.round(2).to_csv(os.path.join(a.out, "per_sector.csv"), index=False)

    sets = {"ours, all 8": (tab, slice(None)),
            "ours, 5 non-edge": (tab, ~tab.edge.values),
            "theirs, all 8": (tab, slice(None)),
            "theirs, same 5": (tab, ~tab.edge.values)}
    results = []
    for t in tics:
        rec = np.array(recov[t])
        for name, (df, keep) in sets.items():
            c = df[["ours_east", "ours_north"]].values if name.startswith("ours") \
                else df[["theirs_east", "theirs_north"]].values
            c, rk = c[keep], rec[keep]
            for ref, target in (("catalogue position", np.broadcast_to(sky[t], c.shape)),
                                ("where our injections land", rk)):
                res = c - target
                F, pF = f_test(res)
                results.append(dict(star=t, sep_arcsec=float(np.hypot(*sky[t])), centroids=name,
                                    compared_with=ref, F=float(F), p_F=float(pF),
                                    p_signflip=sign_flip(res), n=len(res)))
    res = pd.DataFrame(results)
    res.to_csv(os.path.join(a.out, "tests.csv"), index=False)
    json.dump({str(t): v.tolist() for t, v in sky.items()}, open(os.path.join(a.out, "sky_offsets.json"), "w"))

    pd.set_option("display.width", 200)
    print(tab.round(1).to_string(index=False))
    print()
    print(res.assign(F=res.F.round(2), sep_arcsec=res.sep_arcsec.round(1)).to_string(index=False))
    for t in tics:
        r = np.array(recov[t])
        print(f"TIC {t}: catalogue {np.round(sky[t], 1)}\"  injected dip measured at "
              f"{np.round(r.mean(0), 1)}\" on average (per sector: "
              + ", ".join(f"{np.hypot(*x):.0f}" for x in r) + " arcsec from target)")


if __name__ == "__main__":
    main()
