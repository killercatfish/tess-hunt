"""Where a result came from: the code commit and the exact settings, stamped on every output.

The stamp is taken once when a run starts, so it names the code the workers actually loaded even
if someone pulls mid-run. Settings are the loaded config minus `paths` (machine-specific); their
hash names them, and db.save_config keeps the full text so any hash can be read back later.
"""
import hashlib
import json
import subprocess
import time

from . import config as cfgmod


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=cfgmod.ROOT, capture_output=True, text=True,
                              timeout=10, check=True).stdout.rstrip()
    except Exception:
        return None


def settings(cfg):
    """Everything that can change a result: the config without paths or private (_) keys."""
    return {k: v for k, v in cfg.items() if k != "paths" and not k.startswith("_")}


def settings_text(cfg):
    return json.dumps(settings(cfg), sort_keys=True, separators=(",", ":"))


def stamp(cfg):
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "dirty": None if dirty is None else bool(dirty),   # uncommitted edits to tracked files
        "dirty_files": sorted(l[3:] for l in dirty.splitlines()) if dirty else [],
        "config_sha": hashlib.sha256(settings_text(cfg).encode()).hexdigest()[:12],
        "stamped": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def label(st):
    """Short human form, e.g. 'code 8daf300 · config 3f2a9c01b7de' (+ 'with uncommitted edits')."""
    if not st:
        return "unstamped (processed before 2026-10-23)"
    code = (st.get("commit") or "unknown")[:7]
    s = f"code {code} · config {st.get('config_sha')}"
    return s + " with uncommitted edits" if st.get("dirty") else s
