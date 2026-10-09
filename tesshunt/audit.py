"""Per-survivor skeptic audit: a fresh, stateless, read-only model session looks at the diagnostic
page + summary and writes 'reasons this might not be a planet'. It never changes a verdict."""
import base64
import json
import os
import subprocess
import urllib.request

from . import db

PROMPT = """You are a skeptical TESS vetting reviewer. Below is an automated pipeline's diagnostic page
(image) and JSON summary for ONE transit-like signal that survived its automatic false-positive tests.
Your only job: list the concrete reasons this might NOT be a planet (eclipsing binary, blend from a
neighbour, systematics, stellar variability, detrending artefact, period alias, too few or too noisy
transits, inconsistent depths, anything you see in the plots). Cite the panel or number behind each reason.
Do not praise it and do not call it a discovery. If you find nothing, say what follow-up would still
be needed. At most 8 bullets, under 160 words. Plain text."""


def _summary_text(path):
    with open(path) as fh:
        d = json.load(fh)
    s = d["signal"]
    keep = {k: s.get(k) for k in ("period", "t0", "depth_ppm", "duration_h", "rp_rearth", "sde", "snr", "n_transits", "bls_period")}
    keep["tests"] = s.get("tests")
    keep["star"] = d["star"]
    return json.dumps(keep, default=str)[:12000]


def cortex_vlm(cfg, png, summary):
    a = cfg["audit"]
    with open(png, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    body = {"model": a["model"], "temperature": 0.2, "max_tokens": 600,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT + "\n\nSUMMARY JSON:\n" + summary},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}]}
    trace = os.environ.get("CLAUDE_CODE_SESSION_ID")
    req = urllib.request.Request(a["endpoint"], data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "X-HKOS-Requester": a["requester"],
        "X-HKOS-Trace": f"claude:{trace}" if trace else "tess-hunt:pipeline"})
    with urllib.request.urlopen(req, timeout=a["timeout_s"]) as r:
        out = json.load(r)
    return out["choices"][0]["message"]["content"].strip()


def claude_cli(cfg, png, summary):
    """Fresh headless Claude Code session restricted to the Read tool, run in the candidate dir."""
    d = os.path.dirname(png)
    p = PROMPT + f"\n\nRead the image {os.path.basename(png)} and use this summary JSON:\n" + summary
    r = subprocess.run(["claude", "-p", p, "--allowedTools", "Read", "--disallowedTools", "Bash,Edit,Write"],
                       cwd=d, capture_output=True, text=True, timeout=cfg["audit"]["timeout_s"])
    return r.stdout.strip()


def run(cfg, redo=False):
    con = db.connect(cfg["paths"]["db"])
    q = "SELECT tic, iteration FROM signals WHERE verdict='survivor'" + ("" if redo else " AND audit IS NULL")
    fn = {"cortex_vlm": cortex_vlm, "claude_cli": claude_cli}[cfg["audit"]["backend"]]
    n = 0
    for tic, it in con.execute(q).fetchall():
        d = os.path.join(cfg["paths"]["candidates_dir"], str(tic))
        png, js = os.path.join(d, f"sig{it}.png"), os.path.join(d, f"sig{it}.json")
        if not (os.path.exists(png) and os.path.exists(js)):
            continue
        try:
            note = fn(cfg, png, _summary_text(js))
        except Exception as ex:
            note = f"[audit failed: {type(ex).__name__}: {ex}]"
        with open(os.path.join(d, f"sig{it}.audit.txt"), "w") as fh:
            fh.write(note + "\n")
        with con:
            con.execute("UPDATE signals SET audit=? WHERE tic=? AND iteration=?", (note, tic, it))
        n += 1
    return n
