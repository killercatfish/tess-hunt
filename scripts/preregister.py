"""Pre-registered transit predictions for a candidate (one-off).

Writes predicted mid-transit times (BJD_TDB and geocentric UTC, with ingress/egress) for a time
window, using a conservative uncertainty sigma_n = sqrt(sigma_T0^2 + (n sigma_P)^2) that ignores
the (negative) T0-P covariance.

  python scripts/preregister.py --period 5.450138 --sig-p 0.000016 --t0 2458628.6479 --sig-t0 0.0073 \
      --dur-h 2.37 --ra 234.573404 --dec -80.803786 --start 2027-02-13 --end 2027-03-14 --out s114.csv
"""
import argparse, csv
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u


def bjd_to_utc(bjd, coord):
    geocentre = EarthLocation.from_geocentric(0, 0, 0, unit=u.m)
    t = Time(bjd, format="jd", scale="tdb", location=geocentre)
    geo = t
    for _ in range(3):  # light travel time depends weakly on the epoch itself
        geo = Time(t - geo.light_travel_time(coord, "barycentric"), location=geocentre)
    return geo.utc


def main():
    ap = argparse.ArgumentParser()
    for k in ("period", "sig_p", "t0", "sig_t0", "dur_h", "ra", "dec"):
        ap.add_argument("--" + k.replace("_", "-"), type=float, required=True)
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    coord = SkyCoord(a.ra * u.deg, a.dec * u.deg)
    t0s, t1s = Time(a.start).jd, Time(a.end).jd
    n0 = int(np.ceil((t0s - a.t0) / a.period)); n1 = int(np.floor((t1s - a.t0) / a.period))
    half = a.dur_h / 48
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["epoch", "mid_BJD_TDB", "sigma_min", "mid_UTC", "ingress_UTC", "egress_UTC"])
        for n in range(n0, n1 + 1):
            mid = a.t0 + n * a.period
            sig = np.hypot(a.sig_t0, n * a.sig_p) * 1440
            m, i, e = (bjd_to_utc(x, coord) for x in (mid, mid - half, mid + half))
            w.writerow([n, f"{mid:.5f}", f"{sig:.1f}", m.isot[:16], i.isot[:16], e.isot[:16]])
    print(open(a.out).read())


if __name__ == "__main__":
    main()
