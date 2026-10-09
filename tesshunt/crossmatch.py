"""Known-object cross-match: ExoFOP TOIs, NASA Exoplanet Archive confirmed planets, TESS EB catalog.
Known means FLAGGED (soft), never deleted. Catalogs are cached as CSV and refreshed after max_age_days."""
import os
import time

import numpy as np
import pandas as pd

TOI_URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
PS_URL = ("https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query="
          "select+pl_name,tic_id,pl_orbper+from+pscomppars+where+tic_id+is+not+null")
EB_VIZIER = "J/ApJS/258/16"   # Prsa et al. 2022, TESS EBs from 2-min data (sectors 1-26)


def _cached(path, max_age_days, fetch):
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_days * 86400:
        return pd.read_csv(path)
    df = fetch()
    df.to_csv(path, index=False)
    return df


def load(cfg, max_age_days=7):
    d = cfg["paths"]["catalog_dir"]
    toi = _cached(os.path.join(d, "toi.csv"), max_age_days, lambda: pd.read_csv(TOI_URL, comment="#"))
    toi = pd.DataFrame({"tic": toi["TIC ID"].astype(int), "name": "TOI-" + toi["TOI"].astype(str),
                        "period": pd.to_numeric(toi["Period (days)"], errors="coerce"),
                        "disposition": toi.get("TFOPWG Disposition", pd.Series([""] * len(toi))).fillna("")})
    ps = _cached(os.path.join(d, "confirmed.csv"), max_age_days, lambda: pd.read_csv(PS_URL))
    ps = pd.DataFrame({"tic": ps["tic_id"].astype(str).str.replace("TIC ", "", regex=False).astype(int),
                       "name": ps["pl_name"], "period": ps["pl_orbper"]})

    def fetch_eb():
        from astroquery.vizier import Vizier
        v = Vizier(row_limit=-1, columns=["TIC", "Per", "Morph"])
        t = v.get_catalogs(EB_VIZIER)[0].to_pandas()
        return t
    eb = _cached(os.path.join(d, "tess_ebs.csv"), 365, fetch_eb)
    eb = pd.DataFrame({"tic": eb["TIC"].astype(int), "name": "EB", "period": eb["Per"],
                       "morph": eb.get("Morph")})
    return {"toi": toi, "confirmed": ps, "eb": eb}


def _match(df, tic, period, tol):
    rows = df[df["tic"] == int(tic)]
    out = []
    for _, r in rows.iterrows():
        pm = None
        if np.isfinite(r["period"]) and r["period"] > 0:
            pm = any(abs(period / (r["period"] * k) - 1) < tol for k in (1, 2, 0.5, 3, 1 / 3))
        out.append({"name": str(r["name"]), "period": float(r["period"]) if np.isfinite(r["period"]) else None,
                    "period_match": pm, **({"disposition": r["disposition"]} if "disposition" in r else {})})
    return out


def check(tic, period, catalogs, cfg):
    tol = cfg["kill_tests"]["period_match_tol"]
    hits = {k: _match(v, tic, period, tol) for k, v in catalogs.items()}
    hits = {k: v for k, v in hits.items() if v}
    same = any(h["period_match"] for v in hits.values() for h in v)
    return {"pass": not hits, "on_known_star": bool(hits), "same_period_as_known": same, "matches": hits}
