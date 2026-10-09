"""Run on the Mac: one fresh, read-only `claude -p` session per survivor in a mirrored candidates dir.
Writes sig<N>.audit.txt next to each sig<N>.png/json. Usage: python3 scripts/claude_audit.py <dir> [--redo]"""
import glob
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tesshunt import audit  # noqa: E402

root = sys.argv[1]
redo = "--redo" in sys.argv
cfg = {"audit": {"timeout_s": 600}}
jobs = [j[:-5] for j in sorted(glob.glob(f"{root}/*/sig*.json"))
        if redo or not os.path.exists(j[:-5] + ".audit.txt")]


def one(stem):
    t = time.time()
    try:
        note = audit.claude_cli(cfg, stem + ".png", audit._summary_text(stem + ".json"))
    except Exception as e:
        note = f"[audit failed: {e!r}]"
    with open(stem + ".audit.txt", "w") as fh:
        fh.write(note + "\n")
    return os.path.relpath(stem, root), round(time.time() - t)


with ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, jobs):
        print(*r, flush=True)
print(f"{len(jobs)} audited")
