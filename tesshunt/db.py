"""SQLite status tracking. One row per target; one row per signal. Resumable by design."""
import json
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
    tic INTEGER PRIMARY KEY,
    label TEXT,                -- e.g. pilot / val_planet / val_eb / inj
    status TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|error|nodata
    teff REAL, rad REAL, mass REAL, tmag REAL, dist REAL, ra REAL, dec REAL,
    n_sectors INTEGER, sectors TEXT, baseline_d REAL, n_points INTEGER,
    authors TEXT,
    error TEXT,
    started REAL, finished REAL, runtime_s REAL,
    files_bytes INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS signals (
    tic INTEGER NOT NULL,
    iteration INTEGER NOT NULL,
    period REAL, t0 REAL, depth_ppm REAL, duration_h REAL,
    sde REAL, snr REAL, n_transits INTEGER, sde_source TEXT,
    bls_period REAL, rp_rearth REAL,
    passes_threshold INTEGER,
    tests TEXT,                -- JSON: {name: {"pass": bool|None, ...details}}
    verdict TEXT,              -- survivor | rejected | below_threshold | pending_runlevel
    score REAL,
    audit TEXT,
    PRIMARY KEY (tic, iteration)
);
"""


def connect(path):
    con = sqlite3.connect(path, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def add_targets(con, rows, label):
    """rows: iterable of dicts with tic + stellar fields. Existing targets are left alone."""
    cols = ("tic", "teff", "rad", "mass", "tmag", "dist", "ra", "dec")
    for r in rows:
        con.execute(
            f"INSERT OR IGNORE INTO targets ({','.join(cols)}, label) VALUES ({','.join('?' * len(cols))}, ?)",
            [r.get(c) for c in cols] + [label],
        )
    con.commit()


def reset_stale(con):
    """Anything left 'running' by a crash or Ctrl-C goes back to the queue."""
    n = con.execute("UPDATE targets SET status='queued' WHERE status='running'").rowcount
    con.commit()
    return n


def claim_next(con, labels=None):
    q = "SELECT tic FROM targets WHERE status='queued'"
    args = []
    if labels:
        q += f" AND label IN ({','.join('?' * len(labels))})"
        args = list(labels)
    q += " ORDER BY rowid LIMIT 1"
    with con:
        row = con.execute(q, args).fetchone()
        if not row:
            return None
        n = con.execute("UPDATE targets SET status='running', started=? WHERE tic=? AND status='queued'",
                        (time.time(), row[0])).rowcount
    return row[0] if n else claim_next(con, labels)


def finish(con, tic, status, error=None, **fields):
    now = time.time()
    started = con.execute("SELECT started FROM targets WHERE tic=?", (tic,)).fetchone()[0]
    fields.update(status=status, error=error, finished=now, runtime_s=now - started if started else None)
    sets = ",".join(f"{k}=?" for k in fields)
    with con:
        con.execute(f"UPDATE targets SET {sets} WHERE tic=?", list(fields.values()) + [tic])


def save_signals(con, tic, signals):
    with con:
        con.execute("DELETE FROM signals WHERE tic=?", (tic,))
        for s in signals:
            s = dict(s)
            s["tests"] = json.dumps(s.get("tests", {}), default=_json_default)
            cols = list(s)
            con.execute(f"INSERT INTO signals ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                        [s[c] for c in cols])


def _json_default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)
