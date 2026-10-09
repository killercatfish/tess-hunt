import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load(path=None):
    path = Path(path or os.environ.get("TESSHUNT_CONFIG", ROOT / "config.yaml"))
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    p = cfg["paths"]
    for key in ("data_dir", "db", "candidates_dir", "report"):
        if not os.path.isabs(p[key]):
            p[key] = str(ROOT / p[key])
    p["cache_dir"] = str(Path(p["data_dir"]) / "cache")
    p["catalog_dir"] = str(Path(p["data_dir"]) / "catalogs")
    os.makedirs(p["cache_dir"], exist_ok=True)
    os.makedirs(p["catalog_dir"], exist_ok=True)
    return cfg


def with_overrides(cfg, **paths):
    """Return a copy of cfg with path overrides (used by validation to keep its own db/outputs)."""
    import copy
    c = copy.deepcopy(cfg)
    c["paths"].update({k: str(v) for k, v in paths.items()})
    return c


def limit_threads(n):
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
        os.environ[var] = str(n)
