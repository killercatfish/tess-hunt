"""Can a neighbouring star physically produce this transit signal? (one-off vetting tool)

Generalizes the TOI-913 argument: a 2.4 h transit can't come from an eclipse on a 10 R_sun giant,
because anything orbiting a star that size at a few days takes about a day to cross it.

For each star within --radius arcsec that is bright enough (required eclipse depth on it <= 100%),
scan eclipsing configurations on that star:
  companion radius ratio k = 0.05..1.5, impact parameter b = 0..1+k,
  total system mass M_n x {1, 2} and M_n + 2 M_sun, period P and 2P (an EB found at half its period),
and ask whether any of them gives a mid-eclipse depth >= the required depth (uniform-disk overlap
area) AND a total duration within [0.7, 1.4] x the observed T14 (circular orbit, a/R from Kepler).
If none can, the neighbour is "excluded by geometry".

Conservative choices (all make exclusion harder):
- required depth uses only the target + that neighbour's flux (ignores other stars in the aperture);
- uniform disks (limb darkening would lower grazing depths further);
- the companion's own light isn't counted as extra dilution;
- a neighbour with no TIC radius is never excluded ("radius unknown").

  python scripts/neighbour_geometry.py --tic 407126408 --period 5.450138 --t14 2.37 --depth 196
  python scripts/neighbour_geometry.py --csv signals.csv --out geometry.json   # columns TIC,P_d,T14_h,depth_ppm
"""
import argparse, csv, json, time
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tesshunt.stellar import is_real_star  # noqa: E402

G = 6.674e-11; MSUN = 1.989e30; RSUN = 6.957e8; DAY = 86400.0


def overlap_frac(k, b):
    """Fraction of a unit disk covered by a disk of radius k at centre separation b (uniform disks)."""
    k = np.asarray(k, float); b = np.asarray(b, float)
    out = np.zeros(np.broadcast(k, b).shape)
    full = b <= np.abs(1 - k)
    out = np.where(full, np.minimum(k, 1.0) ** 2, out)
    part = (b < 1 + k) & ~full
    bb = np.where(part, b, 1.0); kk = np.where(part, k, 1.0)
    c1 = np.clip((bb**2 + 1 - kk**2) / (2 * bb), -1, 1)
    c2 = np.clip((bb**2 + kk**2 - 1) / (2 * bb * kk), -1, 1)
    area = np.arccos(c1) + kk**2 * np.arccos(c2) - 0.5 * np.sqrt(np.clip((-bb + kk + 1) * (bb + kk - 1) * (bb - kk + 1) * (bb + kk + 1), 0, None))
    return np.where(part, area / np.pi, out)


def feasible(R_n, M_n, P_d, t14_h, dreq, lo=0.7, hi=1.4):
    """Return (ok, best) where ok is True if some configuration matches depth and duration."""
    ks = np.linspace(0.05, 1.5, 59)
    best = None
    for P in (P_d, 2 * P_d):
        for Mtot in (M_n, 2 * M_n, M_n + 2.0):
            a = (G * Mtot * MSUN * (P * DAY) ** 2 / (4 * np.pi**2)) ** (1 / 3) / (R_n * RSUN)  # a / R_n
            for k in ks:
                bs = np.linspace(0, 1 + k, 120)
                depth = overlap_frac(k, bs)
                chord = np.sqrt(np.clip((1 + k) ** 2 - bs**2, 0, None))
                if a <= 1 + k:  # stars (nearly) in contact: eclipses last a large fraction of the orbit
                    t14 = np.full_like(bs, P * 24 / 2)
                else:
                    sini = np.sqrt(1 - (bs / a) ** 2)
                    t14 = P * 24 / np.pi * np.arcsin(np.clip(chord / (a * sini), 0, 1))
                ok = (depth >= dreq) & (t14 >= lo * t14_h) & (t14 <= hi * t14_h)
                if ok.any():
                    i = int(np.argmax(ok))
                    return True, dict(P=P, Mtot=Mtot, a_over_R=float(a), k=float(k), b=float(bs[i]),
                                      depth=float(depth[i]), t14_h=float(t14[i]))
                # track the shortest duration reaching the depth, for the explanation
                m = depth >= dreq
                if m.any():
                    tmin = float(t14[m].min())
                    if best is None or tmin < best["min_t14_h_at_depth"]:
                        best = dict(P=P, Mtot=Mtot, a_over_R=float(a), k=float(k), min_t14_h_at_depth=tmin)
    return False, best


def cone(tic, radius):
    from astroquery.mast import Catalogs
    for i in range(5):
        try:
            tab = Catalogs.query_object(f"TIC {tic}", radius=radius / 3600, catalog="TIC").to_pandas()
            return tab[tab.apply(is_real_star, axis=1)].reset_index(drop=True)   # drop artifacts, duplicates, galaxies
        except Exception as e:
            print("  MAST retry", e); time.sleep(15)
    raise RuntimeError("MAST cone search failed")


def mass_guess(row):
    m = row.get("mass")
    if m is not None and np.isfinite(m):
        return float(m), "TIC"
    r = row.get("rad")
    if str(row.get("lumclass")) == "GIANT":
        return 1.2, "assumed 1.2 (giant)"
    if r is not None and np.isfinite(r):
        return float(np.clip(r, 0.1, 2.5)), "~R (dwarf)"
    return 1.0, "assumed 1.0"


def check(tic, P, t14, depth_ppm, radius=60.0):
    tab = cone(tic, radius)
    t = tab[tab.ID.astype(int) == int(tic)].iloc[0]
    res = []
    for _, n in tab[tab.ID.astype(int) != int(tic)].iterrows():
        if not np.isfinite(n.Tmag):
            continue
        ratio = 10 ** (-0.4 * (n.Tmag - t.Tmag))
        dreq = depth_ppm * 1e-6 * (1 + ratio) / ratio
        if dreq > 1.0:
            continue
        row = dict(tic=int(n.ID), sep_arcsec=round(float(n.dstArcSec), 2), tmag=round(float(n.Tmag), 2),
                   required_depth=round(float(dreq), 4),
                   rad=None if not np.isfinite(n.rad) else round(float(n.rad), 3),
                   teff=None if not np.isfinite(n.Teff) else float(n.Teff),
                   plx_mas=None if not np.isfinite(n.plx) else round(float(n.plx), 3),
                   plx_err=None if not np.isfinite(n.e_plx) else round(float(n.e_plx), 3),
                   dist_pc=None if not np.isfinite(n.d) else round(float(n.d), 1),
                   lumclass=None if not isinstance(n.lumclass, str) else n.lumclass)
        M, msrc = mass_guess(dict(mass=n.mass, rad=n.rad, lumclass=n.lumclass))
        row["mass"], row["mass_source"] = round(M, 3), msrc
        if row["rad"] is None:
            row["verdict"] = "radius unknown (not excluded)"
        else:
            ok, info = feasible(row["rad"], M, P, t14, dreq)
            if not ok and row["lumclass"] == "GIANT":   # giants: also try a heavy giant
                ok, info2 = feasible(row["rad"], 3.0, P, t14, dreq)
                info = info2 if ok else info
            row["verdict"] = "possible" if ok else "excluded by geometry"
            row["detail"] = info
        res.append(row)
    res.sort(key=lambda r: r["sep_arcsec"])
    return dict(tic=int(tic), period=P, t14_h=t14, depth_ppm=depth_ppm, target_tmag=float(t.Tmag),
                n_capable=len(res), n_possible=sum(r["verdict"] != "excluded by geometry" for r in res),
                neighbours=res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tic", type=int); ap.add_argument("--period", type=float)
    ap.add_argument("--t14", type=float, help="hours"); ap.add_argument("--depth", type=float, help="ppm")
    ap.add_argument("--csv"); ap.add_argument("--radius", type=float, default=60.0); ap.add_argument("--out")
    a = ap.parse_args()
    jobs = []
    if a.csv:
        for r in csv.DictReader(open(a.csv)):
            jobs.append((int(r["TIC"]), float(r["P_d"]), float(r["T14_h"]), float(r["depth_ppm"])))
    else:
        jobs.append((a.tic, a.period, a.t14, a.depth))
    out = []
    for (tic, P, t14, d) in jobs:
        r = check(tic, P, t14, d, a.radius)
        out.append(r)
        print(f"TIC {tic} P={P} T14={t14} h depth={d} ppm: {r['n_capable']} capable, {r['n_possible']} not excluded")
        for n in r["neighbours"]:
            print(f"   {n['tic']:>12} {n['sep_arcsec']:6.1f}\" T={n['tmag']:5.2f} need {100*n['required_depth']:6.2f}%  "
                  f"R={n['rad']} M={n['mass']} plx={n['plx_mas']} {n['lumclass']}  -> {n['verdict']}")
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1, default=float)
