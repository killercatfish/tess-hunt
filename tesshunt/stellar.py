"""Stellar parameters (TIC), expected durations, neighbour lookups."""
import numpy as np

G = 6.674e-11
RSUN = 6.957e8
MSUN = 1.989e30
REARTH_PER_RSUN = 109.1


def tic_row(tic):
    from astroquery.mast import Catalogs
    t = Catalogs.query_criteria(catalog="Tic", ID=int(tic))
    if len(t) == 0:
        return {}
    r = t[0]

    def g(k):
        try:
            v = float(r[k])
            return None if not np.isfinite(v) else v
        except Exception:
            return None
    return dict(tic=int(tic), teff=g("Teff"), rad=g("rad"), mass=g("mass"), tmag=g("Tmag"),
                dist=g("d"), ra=g("ra"), dec=g("dec"), logg=g("logg"))


def limb_darkening(tic):
    """Quadratic LD (a, b) from TLS's Claret-table lookup; generic fallback if MAST is unhappy."""
    try:
        from transitleastsquares import catalog_info
        ab = catalog_info(TIC_ID=int(tic))[0]
        if ab is not None and len(ab) == 2 and all(np.isfinite(ab)):
            return tuple(float(x) for x in ab)
    except Exception:
        pass
    return (0.4804, 0.1867)


def expected_duration_d(period_d, rad_rsun, mass_msun, b=0.0):
    """Total duration of a central, circular transit (small-planet limit)."""
    if not rad_rsun or not mass_msun:
        return None
    p = period_d * 86400
    a = (G * mass_msun * MSUN * p ** 2 / (4 * np.pi ** 2)) ** (1 / 3)
    x = rad_rsun * RSUN / a * np.sqrt(max(1 - b ** 2, 0))
    return period_d / np.pi * np.arcsin(min(x, 1.0))


NOT_STARS = {"ARTIFACT", "DUPLICATE"}


def is_real_star(row):
    """False for TIC entries that are not stars: disposition ARTIFACT or DUPLICATE (Paegert et al. 2021 say
    to ignore them) or objType EXTENDED (2MASS extended sources, mostly galaxies). Works on astropy rows and
    pandas rows; masked or missing fields count as a real star."""
    def field(k):
        try:
            v = row[k]
        except (KeyError, IndexError, ValueError):
            return ""
        return "" if v is None or np.ma.is_masked(v) else str(v).strip().upper()
    return field("disposition") not in NOT_STARS and field("objType") != "EXTENDED"


def neighbours(ra, dec, radius_arcsec, tic):
    from astroquery.mast import Catalogs
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    c = SkyCoord(ra * u.deg, dec * u.deg)
    t = Catalogs.query_region(c, radius=radius_arcsec * u.arcsec, catalog="Tic")
    out = []
    for r in t:
        if int(r["ID"]) == int(tic) or not is_real_star(r):
            continue
        try:
            tm = float(r["Tmag"])
        except Exception:
            continue
        if not np.isfinite(tm):
            continue
        out.append(dict(tic=int(r["ID"]), tmag=tm, sep_arcsec=float(r["dstArcSec"])))
    return sorted(out, key=lambda n: n["tmag"])
