"""TRICERATOPS false-positive probability for one candidate (one-off vetting tool).

Runs in its own venv (triceratops pins old numpy/scipy). Input is a folded, binned CSV
(time_from_mid_d, flux, flux_err) exported with the pipeline's prep, plus optional speckle
contrast curves (CSV: separation_arcsec, delta_mag).

  python triceratops_fpp.py --tic 407126408 --sectors 12,13,65,66,93,100,101,102 \
      --period 5.450098 --fold fold.csv --cc zorro832.csv --filt Vis --runs 6 --N 1000000 --out out/
"""
import argparse, json, os, time, warnings
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tic", type=int, required=True)
    ap.add_argument("--sectors", required=True)
    ap.add_argument("--period", type=float, required=True)
    ap.add_argument("--fold", required=True)
    ap.add_argument("--cc", default=None)
    ap.add_argument("--filt", default="Vis")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--N", type=int, default=1000000)
    ap.add_argument("--exptime", type=float, default=10 / 1440, help="bin width of the folded data [d]")
    ap.add_argument("--bg", default=None, help="saved field-star population CSV (skips the slow Gaia query)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    warnings.simplefilter("ignore")
    import triceratops.triceratops as tr

    os.makedirs(a.out, exist_ok=True)
    d = np.loadtxt(a.fold, delimiter=",", skiprows=1)
    t, f, e = d[:, 0], d[:, 1], d[:, 2]
    sigma = float(np.median(e))
    intr = np.abs(t) < 0.3 * 2.361 / 24
    depth = float(1 - np.mean(f[intr]))
    print(f"{len(t)} bins, sigma {1e6*sigma:.0f} ppm, central depth {1e6*depth:.0f} ppm")

    sectors = np.array([int(s) for s in a.sectors.split(",")])
    tgt = tr.target(ID=a.tic, sectors=sectors, search_radius=10, trilegal_fname=a.bg)
    aps = tgt.get_spoc_apertures()
    ok = [i for i, x in enumerate(aps) if x is not None]
    if len(ok) < len(aps):
        print("dropping sectors without SPOC aperture:", [int(sectors[i]) for i in range(len(aps)) if i not in ok])
        tgt = tr.target(ID=a.tic, sectors=sectors[ok], search_radius=10, trilegal_fname=a.bg)
        aps = [aps[i] for i in ok]
    tgt.calc_depths(tdepth=depth, all_ap_pixels=aps)
    stars = tgt.stars[["ID", "Tmag", "ra", "dec", "sep (arcsec)", "fluxratio", "tdepth"]].copy()
    near = stars[stars.tdepth > 0]
    print(f"{len(stars)} stars in field; {len(near)} could produce the depth (tdepth <= 1):")
    print(near.to_string(index=False))

    res = []
    for k in range(a.runs):
        t0 = time.time()
        tgt.calc_probs(time=t, flux_0=f, flux_err_0=sigma, P_orb=a.period, contrast_curve_file=a.cc,
                       filt=a.filt, N=a.N, parallel=True, exptime=a.exptime, verbose=0)
        res.append(dict(FPP=float(tgt.FPP), NFPP=float(tgt.NFPP),
                        probs=tgt.probs[["ID", "scenario", "prob"]].to_dict("records")))
        print(f"run {k+1}: FPP {tgt.FPP:.4g}  NFPP {tgt.NFPP:.3g}  ({time.time()-t0:.0f} s)", flush=True)
    fpp = np.array([r["FPP"] for r in res]); nfpp = np.array([r["NFPP"] for r in res])
    # mean scenario probabilities across runs
    import pandas as pd
    allp = pd.concat([pd.DataFrame(r["probs"]) for r in res])
    allp["ID"] = allp["ID"].astype(str)
    mean_p = allp.groupby(["ID", "scenario"])["prob"].agg(["mean", "std"]).sort_values("mean", ascending=False)
    print(f"\nFPP  {fpp.mean():.4g} ± {fpp.std():.2g}   NFPP {nfpp.mean():.3g} ± {nfpp.std():.2g}   ({a.runs} runs, N={a.N})")
    print(mean_p.head(10).to_string())
    json.dump(dict(tic=a.tic, period=a.period, depth_ppm=1e6 * depth, sigma_ppm=1e6 * sigma, cc=a.cc,
                   filt=a.filt, N=a.N, runs=res, FPP_mean=float(fpp.mean()), FPP_std=float(fpp.std()),
                   NFPP_mean=float(nfpp.mean()), NFPP_std=float(nfpp.std()),
                   stars=near.astype({"ID": str}).to_dict("records")),
              open(os.path.join(a.out, "triceratops.json"), "w"), indent=1)
    mean_p.reset_index().to_csv(os.path.join(a.out, "scenario_probs.csv"), index=False)


if __name__ == "__main__":
    main()
