"""Freeze the kill-test calibration set (Josh, 2026-10-27: calibrate the kill tests before any new search).

Why: TOI-2018 b, a real planet, flipped from survivor to rejected when MAST reprocessed two sectors, and the
26 validation planets can't measure how often the hard tests reject real planets. This draws a larger set of
stars whose answer is known, so each test gets a measured rate:
  planets.csv          confirmed transiting planets around stars like ours (how often a test kills a planet)
  false_positives.csv  TOIs that follow-up showed are not planets, FP or FA (how often a test catches a fake)
  ebs.csv              detached eclipsing binaries from the TESS EB catalog, on cool dwarfs
  long_period.csv      confirmed planets at 40-100 d: frozen now for the long-period mode, not run yet
Plain Python (no packages), so it runs anywhere. Inputs are the raw downloads, passed as paths:
  python3 -I scripts/calibration_build.py PLANETS_CSV TOI_CSV EBS_CSV
    PLANETS_CSV  NASA Exoplanet Archive pscomppars (query in calibration/README.md)
    TOI_CSV      ExoFOP TOI list (https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv)
    EBS_CSV      VizieR J/ApJS/258/16 detached EBs (query in calibration/README.md)
"""
import csv
import json
import os
import random
import sys
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calibration")
SEED = 20261027
N_HOSTS = 350          # planet hosts in total; every host with a planet at 15-40 d is kept, the rest drawn at random
N_EBS = 120
TEFF_MAX, TMAG_MAX, P_MIN, P_MAX = 5200, 14, 0.5, 40


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def tic_of(s):
    return int(str(s).replace("TIC", "").strip())


def write(name, rows, cols):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def tic_params(tics):
    """Teff, logg and radius from the TIC through MAST's web API, 500 stars per request."""
    out = {}
    tics = sorted(tics)
    for i in range(0, len(tics), 500):
        req = {"service": "Mast.Catalogs.Filtered.Tic", "format": "json", "pagesize": 1000,
               "params": {"columns": "ID,Teff,logg,rad",
                          "filters": [{"paramName": "ID", "values": [str(t) for t in tics[i:i + 500]]}]}}
        body = urllib.parse.urlencode({"request": json.dumps(req)}).encode()
        with urllib.request.urlopen("https://mast.stsci.edu/api/v0/invoke", body, timeout=120) as r:
            for d in json.load(r)["data"]:
                out[int(d["ID"])] = d
    return out


def main(planets_csv, toi_csv, ebs_csv):
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(SEED)

    # planets: confirmed, transiting, not flagged controversial, our kind of star
    pl = [r for r in csv.DictReader(open(planets_csv)) if r["pl_controv_flag"] != "1"]
    for r in pl:
        r["tic"] = tic_of(r["tic_id"])
    ok = [r for r in pl if (num(r["st_teff"]) or 9e9) < TEFF_MAX and (num(r["sy_tmag"]) or 99) < TMAG_MAX]
    short = [r for r in ok if P_MIN < num(r["pl_orbper"]) < P_MAX and (num(r["pl_rade"]) or 99) < 6]
    longp = [r for r in pl if 40 <= num(r["pl_orbper"]) < 100 and (num(r["st_teff"]) or 9e9) < TEFF_MAX]
    hosts = sorted({r["tic"] for r in short})
    keep = {r["tic"] for r in short if num(r["pl_orbper"]) >= 15}
    rest = sorted(set(hosts) - keep)
    keep |= set(rng.sample(rest, max(0, min(len(rest), N_HOSTS - len(keep)))))
    # every planet on a kept host, so a multi-planet star is judged on each of its planets
    chosen = sorted((r for r in ok if r["tic"] in keep and P_MIN < num(r["pl_orbper"]) < P_MAX),
                    key=lambda r: (r["tic"], num(r["pl_orbper"])))
    pcols = ["tic", "pl_name", "hostname", "pl_orbper", "pl_tranmid", "pl_trandur", "pl_rade", "st_teff", "st_rad",
             "st_mass", "st_logg", "sy_tmag", "sy_dist", "disc_facility", "disc_year"]
    write("planets.csv", chosen, pcols)
    write("long_period.csv", sorted(longp, key=lambda r: (r["tic"], num(r["pl_orbper"]))), pcols)

    # false positives: TOIs that TFOP dispositioned FP (astrophysical, not a planet) or FA (false alarm)
    toi = [r for r in csv.DictReader(open(toi_csv))]
    fp = [r for r in toi if r["TFOPWG Disposition"] in ("FP", "FA")
          and (num(r["Stellar Eff Temp (K)"]) or 9e9) < TEFF_MAX and (num(r["TESS Mag"]) or 99) < TMAG_MAX
          and P_MIN < (num(r["Period (days)"]) or 0) < P_MAX
          and int(r["TIC ID"]) not in keep]  # a star that also hosts a confirmed planet would blur both tallies
    fcols = ["tic", "TOI", "TFOPWG Disposition", "Period (days)", "Epoch (BJD)", "Duration (hours)", "Depth (ppm)",
             "Planet Radius (R_Earth)", "Stellar Eff Temp (K)", "Stellar Radius (R_Sun)", "TESS Mag",
             "Stellar Distance (pc)", "Comments"]
    for r in fp:
        r["tic"] = int(r["TIC ID"])
    write("false_positives.csv", sorted(fp, key=lambda r: (r["tic"], num(r["TOI"]))), fcols)

    # eclipsing binaries: detached, on cool dwarfs (TIC Teff < 5200 K, logg > 4), shallow ones first
    eb = [r for r in csv.DictReader(open(ebs_csv)) if num(r["Tmag"]) < TMAG_MAX]
    for r in eb:
        r["tic"] = int(r["TIC"])
    eb = [r for r in eb if r["tic"] not in keep and r["tic"] not in {f["tic"] for f in fp}]
    par = tic_params({r["tic"] for r in eb})
    for r in eb:
        p = par.get(r["tic"], {})
        r.update(teff=p.get("Teff"), logg=p.get("logg"), rad=p.get("rad"))
    eb = [r for r in eb if (num(r["teff"]) or 9e9) < TEFF_MAX and (num(r["logg"]) or 0) > 4.0]
    shallow = [r for r in eb if (num(r["Dp-pf"]) or 1) < 0.05]
    deep = [r for r in eb if r not in shallow]
    pick = rng.sample(shallow, min(len(shallow), N_EBS * 2 // 3))
    pick += rng.sample(deep, min(len(deep), N_EBS - len(pick)))
    ecols = ["tic", "Per", "BJD0", "Morph", "Dp-pf", "Ds-pf", "Tmag", "teff", "logg", "rad", "RAJ2000", "DEJ2000"]
    write("ebs.csv", sorted(pick, key=lambda r: r["tic"]), ecols)

    print(json.dumps({
        "planet_pool_hosts": len(hosts), "planet_hosts": len(keep), "planets": len(chosen),
        "planets_15_40d": sum(num(r["pl_orbper"]) >= 15 for r in chosen),
        "long_period_planets_40_100d": len(longp), "long_period_hosts": len({r["tic"] for r in longp}),
        "false_positives": len(fp), "fp_by_disposition": {d: sum(r["TFOPWG Disposition"] == d for r in fp) for d in ("FP", "FA")},
        "eb_cool_dwarfs": len(eb), "eb_shallow_pool": len(shallow), "ebs": len(pick),
        "stars_to_run": len(keep | {r["tic"] for r in fp} | {r["tic"] for r in pick}),
    }, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
