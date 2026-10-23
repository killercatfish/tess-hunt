"""Publish the negatives: every signal that did not survive, and why (honesty upgrade n2).

Writes negatives.csv (one row per rejected or below-threshold signal) and negatives.md (counts by
reason, then the rejected signals) next to report.html. Survivors are in the report; together the two
account for every signal the search found.
"""
import csv
import json
import os
import sqlite3

from . import db, provenance


def _f(v, fmt="{:.1f}"):
    return "?" if v is None else fmt.format(v)


def _why_failed(name, t, k):
    """One plain phrase per failed hard test, with the number that failed it."""
    if name == "odd_even":
        return f"odd/even depths differ by {_f(t.get('sigma'))} sigma (limit {k['odd_even_sigma']})"
    if name == "secondary":
        return (f"secondary eclipse: {_f(t.get('sigma_half'))} sigma at phase 0.5 (limit {k['secondary_sigma_half']}), "
                f"{_f(t.get('scan_max_sigma'))} sigma best elsewhere (limit {k['secondary_sigma_scan']})")
    if name == "duration":
        return (f"duration {_f(t.get('ratio'), '{:.2f}')}x what the star allows "
                f"(allowed {k['duration_ratio_min']}-{k['duration_ratio_max']})")
    if name == "size":
        return f"implied radius {_f(t.get('rp_rearth'))} R_earth (limit {k['max_radius_rearth']})"
    if name == "harmonic":
        return f"period is a harmonic of signal #{t.get('matches_iteration')} on the same star"
    if name == "shape":
        return f"V-shaped, like a grazing binary (U minus V chi2 {_f(t.get('dchi2_U_minus_V'))}, limit {k['shape_dchi2']})"
    if name == "sector_consistency":
        return f"depth differs between sectors (p {_f(t.get('p'), '{:.2g}')}, limit {k['sector_consistency_p']})"
    if name == "holdout":
        return f"not re-found in held-out seasons ({t.get('hits')}/{t.get('attempts')})"
    if name == "injection":
        return t.get("why") or f"a copy injected at this period was not recovered (found {_f(t.get('recovered_period'), '{:.4f}')} d)"
    if name == "systematics":
        return f"same period on {t.get('n_targets_same_period')} stars: instrumental"
    return name


def _why_below(r, th):
    out = []
    if r["sde"] is not None and r["sde"] < th["sde_min"]:
        out.append(f"SDE {r['sde']:.1f} < {th['sde_min']}")
    if r["snr"] is not None and r["snr"] < th["snr_min"]:
        out.append(f"SNR {r['snr']:.1f} < {th['snr_min']}")
    if r["n_transits"] is not None and r["n_transits"] < th["min_transits"]:
        out.append(f"{r['n_transits']} transits < {th['min_transits']}")
    return "; ".join(out) or "below threshold"


def rows(cfg, con):
    con.row_factory = sqlite3.Row
    k, th = cfg["kill_tests"], cfg["thresholds"]
    out = []
    for r in con.execute("""SELECT s.tic, s.iteration, s.period, s.depth_ppm, s.duration_h, s.rp_rearth, s.sde, s.snr,
            s.n_transits, s.verdict, s.tests, t.label, t.provenance FROM signals s JOIN targets t USING(tic)
            WHERE s.verdict != 'survivor' ORDER BY s.verdict, s.tic, s.iteration"""):
        tests = json.loads(r["tests"] or "{}")
        failed = [n for n in k["hard_fail"] if tests.get(n, {}).get("pass") is False]
        if r["verdict"] == "rejected":
            why = "; ".join(_why_failed(n, tests[n], k) for n in failed)
        else:
            why = _why_below(r, th)
        st = json.loads(r["provenance"]) if r["provenance"] else None
        out.append(dict(tic=r["tic"], signal=r["iteration"], label=r["label"], verdict=r["verdict"],
                        failed_tests=",".join(failed), why=why, period_d=r["period"], depth_ppm=r["depth_ppm"],
                        duration_h=r["duration_h"], rp_rearth=r["rp_rearth"], sde=r["sde"], snr=r["snr"],
                        n_transits=r["n_transits"], provenance=provenance.label(st)))
    return out


def write(cfg, title="tess-hunt negatives"):
    con = db.connect(cfg["paths"]["db"])
    rs = rows(cfg, con)
    con.row_factory = None
    base = os.path.dirname(cfg["paths"]["report"])
    csv_path, md_path = os.path.join(base, "negatives.csv"), os.path.join(base, "negatives.md")
    cols = list(rs[0]) if rs else ["tic", "signal", "verdict", "why"]
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(rs)

    n_surv = con.execute("SELECT COUNT(*) FROM signals WHERE verdict='survivor'").fetchone()[0]
    rej = [r for r in rs if r["verdict"] == "rejected"]
    below = [r for r in rs if r["verdict"] == "below_threshold"]
    by_test = {}
    for r in rej:
        for n in r["failed_tests"].split(","):
            by_test[n] = by_test.get(n, 0) + 1
    only = {}
    for r in rej:
        if "," not in r["failed_tests"]:
            only[r["failed_tests"]] = only.get(r["failed_tests"], 0) + 1
    made = provenance.label(cfg.get("_provenance") or provenance.stamp(cfg))
    lines = [f"# {title}", "",
             f"Every signal the search found that did not survive, and why. Built by {made}.", "",
             *[f"- {n} star(s) processed by {provenance.label(st)}" for st, n in db.provenance_counts(con)], "",
             f"**{len(rs) + n_surv} signals: {n_surv} survivors (in the report), {len(rej)} rejected by a kill test, "
             f"{len(below)} below the search threshold.** A signal can fail several tests.", "",
             "| Kill test | Signals it failed | ...and the only test it failed |", "|---|---|---|",
             *[f"| {n} | {c} | {only.get(n, 0)} |" for n, c in sorted(by_test.items(), key=lambda x: -x[1])], "",
             f"The {len(below)} below-threshold signals are in `negatives.csv` with the number that kept each out.", "",
             "## Rejected signals", "",
             "| TIC | sig | P (d) | depth ppm | Rp R⊕ | SNR | why |", "|---|---|---|---|---|---|---|",
             *[f"| {r['tic']} | {r['signal']} | {_f(r['period_d'], '{:.5f}')} | {_f(r['depth_ppm'], '{:.0f}')} | "
               f"{_f(r['rp_rearth'])} | {_f(r['snr'])} | {r['why']} |" for r in rej], ""]
    with open(md_path, "w") as fh:
        fh.write("\n".join(lines))
    return csv_path, md_path, len(rej), len(below)
