"""Target selection from the TIC (cached CSV). Criteria live in config.yaml -> targets."""
import os

import numpy as np
import pandas as pd


def pool(cfg, refresh=False):
    path = os.path.join(cfg["paths"]["catalog_dir"], "target_pool.csv")
    if os.path.exists(path) and not refresh:
        return pd.read_csv(path)
    from astroquery.mast import Catalogs
    t = cfg["targets"]
    kw = dict(catalog="Tic", Teff=[t["teff_min"], t["teff_max"]], d=[0, t["dist_max_pc"]],
              Tmag=[-5, t["tmag_max"]], objType="STAR")
    if t.get("dwarfs_only"):
        kw["lumclass"] = "DWARF"
    tab = Catalogs.query_criteria(**kw)
    df = tab.to_pandas()[["ID", "Teff", "rad", "mass", "Tmag", "d", "ra", "dec", "logg"]]
    df = df.rename(columns={"ID": "tic", "Teff": "teff", "Tmag": "tmag", "d": "dist"})
    df["tic"] = df["tic"].astype(int)
    df.to_csv(path, index=False)
    return df


def sample(cfg, n=None, exclude=()):
    df = pool(cfg)
    df = df[~df["tic"].isin(set(exclude))]
    n = n or cfg["targets"]["pilot_size"]
    rng = np.random.default_rng(cfg["targets"]["seed"])
    idx = rng.choice(len(df), size=min(n, len(df)), replace=False)
    return df.iloc[np.sort(idx)].to_dict("records")
