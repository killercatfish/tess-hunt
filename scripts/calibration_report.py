"""Score the kill-test calibration run (calibration/README.md; Josh decided 10/27 to calibrate before any new search).

Reads every machine's database, recomputes the run-level systematics test over all of them together, and
writes calibration/out/CALIBRATION.md plus one CSV row per planet, false positive and binary:
  - planets: found at their period? which hard tests kill them? -> each test's false-rejection rate
  - false positives and binaries: found? rejected? by which test? -> each test's catch rate, per type
  - which processing of the data every star used
Run from the repo root with the pipeline's Python, after copying each machine's results.db into
calibration/out/<machine>/:
  .venv/bin/python scripts/calibration_report.py [DB ...]     (default: calibration/out/*/results.db)
"""
import glob
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tesshunt import config as cfgmod, db, provenance, systematics  # noqa: E402

CAL = os.path.join(cfgmod.ROOT, "calibration")
OUT = os.path.join(CAL, "out")
TOL = 0.01                      # a signal within 1% of the catalogue period counts as found


def wilson(k, n, z=1.96):
    """95% interval for a rate k/n (Wilson score), as (low, high) fractions."""
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate(k, n):
    if not n:
        return "–"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% ({100 * lo:.0f}–{100 * hi:.0f}%)"


def match(p, ref, aliases=(1,)):
    return any(abs(p / (ref * a) - 1) < TOL for a in aliases)


def fp_type(r):
    """Rough type from the TFOP comment (the same keyword match as calibration/README.md)."""
    c = str(r.get("Comments") or "").lower()
    if re.search(r"neb|nearby|contamina|centroid|offset|off-target|blend", c):
        return "nearby star"
    if re.search(r"\beb\b|sb1|sb2|secondary|odd.?even|v-shape|v shape|binary|stellar companion", c):
        return "binary on target"
    if re.search(r"systematic|scatter|momentum|instrument|false alarm|noise", c) or r.get("TFOPWG Disposition") == "FA":
        return "systematic or false alarm"
    return "not stated"


def load(dbs):
    sig, tg = [], []
    for d in dbs:
        con = db.connect(d)
        s = pd.read_sql("SELECT * FROM signals", con)
        t = pd.read_sql("SELECT * FROM targets", con)
        s["machine"] = t["machine"] = os.path.basename(os.path.dirname(d))
        sig.append(s); tg.append(t)
    sig, tg = pd.concat(sig, ignore_index=True), pd.concat(tg, ignore_index=True)
    dup = tg[tg.status != "queued"].tic.duplicated()
    if dup.any():
        raise SystemExit(f"stars processed twice across databases: {sorted(tg[tg.status != 'queued'].tic[dup])[:10]}")
    sig["tests"] = sig.tests.map(lambda x: json.loads(x) if x else {})
    return sig, tg.set_index("tic")


def merged_systematics(sig, tg, cfg):
    """The run-level test (pipeline.postprocess, tesshunt/systematics.py) over every machine's signals at once."""
    k = cfg["kill_tests"]
    thr = sig[sig.passes_threshold == 1]
    sectors = {t: set(str(s or "").split(",")) - {""} for t, s in tg.sectors.items()}
    n_per, n_times = systematics.systematics_counts(thr.period, thr.t0, thr.duration_h, thr.tic, sectors, cfg)
    sig["n_same_period"] = pd.Series(n_per, index=thr.index)
    sig["n_same_times"] = pd.Series(n_times, index=thr.index)
    sig["sys_pass_merged"] = sig.n_same_times.map(lambda n: None if pd.isna(n) else n <= k["systematics_max_targets"])
    return sig


def fails(row, hard):
    """Hard tests this signal fails, with systematics taken from the merged recomputation."""
    f = [n for n in hard if n != "systematics" and row.tests.get(n, {}).get("pass") is False]
    m = row.sys_pass_merged
    if m is not None and not pd.isna(m) and not bool(m):
        f.append("systematics")
    return f


def best(sig_star, ref, aliases):
    """The threshold-passing signal on this star nearest the catalogue period (exact first, then aliases)."""
    s = sig_star[sig_star.passes_threshold == 1]
    for al in ((1,), aliases):
        hit = s[s.period.map(lambda p: match(p, ref, al))]
        if len(hit):
            return hit.iloc[0], al != (1,)
    return None, False


def score_planets(sig, tg, hard, soft):
    pl = pd.read_csv(os.path.join(CAL, "planets.csv"))
    rows = []
    for r in pl.itertuples():
        st = tg.status.get(r.tic)
        hit, alias = best(sig[sig.tic == r.tic], r.pl_orbper, (2, 0.5))
        f = fails(hit, hard) if hit is not None and not alias else []
        rows.append(dict(kind="planet", tic=r.tic, name=r.pl_name, period=r.pl_orbper, rp=r.pl_rade, tmag=r.sy_tmag,
                         status=st, found=hit is not None and not alias, alias_only=alias,
                         iteration=None if hit is None else int(hit.iteration), sde=None if hit is None else hit.sde,
                         snr=None if hit is None else hit.snr, killed=bool(f), killed_by=",".join(f),
                         soft=",".join(n for n in soft if hit is not None and hit.tests.get(n, {}).get("pass") is False)))
    return pd.DataFrame(rows)


def score_fakes(sig, tg, hard, kind):
    if kind == "fp":
        src = pd.read_csv(os.path.join(CAL, "false_positives.csv"))
        items = [(r["tic"], r["TOI"], r["Period (days)"], fp_type(r), r["TFOPWG Disposition"]) for _, r in src.iterrows()]
    else:
        src = pd.read_csv(os.path.join(CAL, "ebs.csv"))
        items = [(r["tic"], None, r["Per"], "shallow binary" if r["Dp-pf"] < 0.05 else "deep binary", "EB")
                 for _, r in src.iterrows()]
    rows = []
    for tic, toi, P, typ, disp in items:
        s = sig[sig.tic == tic]
        hit, alias = best(s, P, (2, 0.5, 3, 1 / 3))
        rel = s[(s.passes_threshold == 1) & s.period.map(lambda p: match(p, P, (1, 2, 0.5, 3, 1 / 3)))]
        # credit the tests that rejected the first signal at this period; `harmonic` then only shows up when the
        # first one was an alias of something else, not for the echoes at 2x or 1/2x that it rejects by design
        f = fails(rel.sort_values("iteration").iloc[0], hard) if len(rel) else []
        surv = [x for _, x in rel.iterrows() if not fails(x, hard)]
        rows.append(dict(kind=kind, tic=tic, toi=toi, period=P, type=typ, disposition=disp, status=tg.status.get(tic),
                         found=len(rel) > 0, at_alias=alias, n_signals=len(rel), leaked=bool(surv),
                         leaked_period=surv[0].period if surv else None, caught_by=",".join(f)))
    return pd.DataFrame(rows)


def per_test(df, col, hard, base):
    """For each hard test: how many of `base` rows it hits (alone and in total)."""
    out = []
    for n in hard:
        hit = df[base & df[col].str.split(",").map(lambda xs: n in xs)]
        alone = hit[hit[col] == n]
        out.append((n, len(hit), len(alone)))
    return out


def main(dbs):
    cfg = cfgmod.load()
    hard, soft = cfg["kill_tests"]["hard_fail"], cfg["kill_tests"]["soft_flag"]
    dbs = dbs or sorted(glob.glob(os.path.join(OUT, "*", "results.db")))
    sig, tg = load(dbs)
    sig = merged_systematics(sig, tg, cfg)
    pl, fp, eb = score_planets(sig, tg, hard, soft), score_fakes(sig, tg, hard, "fp"), score_fakes(sig, tg, hard, "eb")
    rows = pd.concat([d.dropna(axis=1, how="all") for d in (pl, fp, eb)], ignore_index=True)
    rows["tic"] = rows.tic.astype(int)
    rows.to_csv(os.path.join(OUT, "calibration_rows.csv"), index=False)

    done = tg[tg.status == "done"]
    L = ["# Kill-test calibration results", "",
         f"Databases: {', '.join(os.path.relpath(d, cfgmod.ROOT) for d in dbs)}. Stars: {len(tg)}, of which "
         f"{len(done)} done, {int((tg.status == 'nodata').sum())} with no usable TESS data, "
         f"{int((tg.status == 'error').sum())} errors, {int((tg.status == 'queued').sum())} not yet run.", "",
         "Rates are given with 95% intervals (Wilson). A test can hit a signal that another test also kills, so "
         "'alone' counts the signals that test is the only reason for.", ""]
    for d in dbs:
        for st, n in db.provenance_counts(db.connect(d)):
            L.append(f"- {os.path.basename(os.path.dirname(d))}: {n} star(s) processed by {provenance.label(st)}")
    L.append("")

    # ---- planets
    ran = pl[pl.status == "done"]
    found = ran[ran.found]
    L += ["## Real planets: how often each test rejects one", "",
          f"- Planets on stars that ran: {len(ran)} of {len(pl)}",
          f"- Found at their period: **{rate(len(found), len(ran))}** (another {int(ran.alias_only.sum())} only at "
          "twice or half the period)",
          f"- Of those found, rejected by at least one hard test: **{rate(int(found.killed.sum()), len(found))}**", "",
          "| Hard test | Kills (of found planets) | Only reason for the rejection |", "|---|---|---|"]
    for n, k, alone in per_test(found, "killed_by", hard, found.killed):
        L.append(f"| {n} | {rate(k, len(found))} | {alone} |")
    L += ["", "Confirmed planets are biased toward clean, strong signals (that's how they got confirmed), while a new "
          "planet would sit near our threshold. So the rows by search SNR matter most: the rate below SNR 10 is the "
          "one that applies to a new find.", "", "Broken down (found planets rejected / found):", ""]
    groups = {
        "period below 15 d": found.period < 15, "period 15–40 d": found.period >= 15,
        "radius below 1.5 R⊕": found.rp < 1.5, "radius 1.5–2.5 R⊕": (found.rp >= 1.5) & (found.rp < 2.5),
        "radius 2.5–4 R⊕": (found.rp >= 2.5) & (found.rp < 4), "radius 4 R⊕ and up": found.rp >= 4,
        "TESS mag below 10": found.tmag < 10, "TESS mag 10–12": (found.tmag >= 10) & (found.tmag < 12),
        "TESS mag 12–14": found.tmag >= 12,
        "search SNR below 10": found.snr < 10, "search SNR 10–20": (found.snr >= 10) & (found.snr < 20),
        "search SNR 20 and up": found.snr >= 20}
    for g, m in groups.items():
        sub = found[m]
        top = Counter(x for xs in sub.killed_by for x in xs.split(",") if x).most_common(3)
        L.append(f"- {g}: {rate(int(sub.killed.sum()), len(sub))}" + (f"; most often {', '.join(f'{a} ({b})' for a, b in top)}" if top else ""))
    L += ["", "Soft flags on found planets: " + ", ".join(
        f"{n} {int(found.soft.str.split(',').map(lambda xs: n in xs).sum())}" for n in soft), ""]

    # ---- false positives and binaries
    for kind, df, title in (("fp", fp, "TFOP false positives and false alarms"), ("eb", eb, "Eclipsing binaries on cool dwarfs")):
        ran = df[df.status == "done"]
        fnd = ran[ran.found]
        L += [f"## {title}: how often the tests catch them", "",
              f"- On stars that ran: {len(ran)} of {len(df)}. Found at the catalogue period (or 2×, ½×, 3×, ⅓×): "
              f"{rate(len(fnd), len(ran))}",
              f"- Of those found, **leaked through as a survivor: {rate(int(fnd.leaked.sum()), len(fnd))}**", "",
              "| Type | Ran | Found | Leaked (survivor at that period) | Most common catching tests |", "|---|---|---|---|---|"]
        for typ in sorted(df.type.unique()):
            r_ = ran[ran.type == typ]; f_ = r_[r_.found]
            top = Counter(x for xs in f_.caught_by for x in xs.split(",") if x).most_common(3)
            L.append(f"| {typ} | {len(r_)} | {len(f_)} | {rate(int(f_.leaked.sum()), len(f_))} | "
                     f"{', '.join(f'{a} ({b})' for a, b in top) or '–'} |")
        L += ["", "| Hard test | Catches (of found) |", "|---|---|"]
        for n in hard:
            k = int(fnd.caught_by.str.split(",").map(lambda xs: n in xs).sum())
            L.append(f"| {n} | {rate(k, len(fnd))} |")
        L.append("")

    # ---- the run-level test
    thr = sig[sig.passes_threshold == 1]
    stored = thr.tests.map(lambda t: t.get("systematics", {}).get("pass"))
    n = cfg["kill_tests"]["systematics_max_targets"]
    L += [f"## The systematics test (more than {n} stars dipping at the same period and the same times)", "",
          f"- Threshold-passing signals: {len(thr)}. Failing it over all runs together: "
          f"{int((thr.sys_pass_merged == False).sum())}. By period alone (the rule before 10/28), it would be "  # noqa: E712
          f"{int((thr.n_same_period > n).sum())}; as stored by each machine's own run, {int((stored == False).sum())}.",  # noqa: E712
          f"- Found real planets it rejects over both runs together: "
          f"{int(found.killed_by.str.split(',').map(lambda xs: 'systematics' in xs).sum())} of {len(found)}.", ""]

    # ---- data versions
    ver = Counter()
    for v in done.get("data_versions", pd.Series(dtype=object)).dropna():
        for sec, d in json.loads(v).items():
            pv = str(d.get("procver") or "none")
            ver[(d.get("author"), pv.split("-")[1].split(".")[0] if pv.startswith("spoc-") else pv)] += 1
    L += ["## Which processing of the data was used", "",
          "| Product | Processing version (major) | Sector files |", "|---|---|---|",
          *[f"| {a} | {b} | {n} |" for (a, b), n in sorted(ver.items(), key=lambda x: -x[1])], ""]
    rt = done.runtime_s.dropna()
    L += [f"Runtime per star: median {rt.median():.0f} s, max {rt.max():.0f} s, total {rt.sum() / 3600:.1f} CPU-h "
          f"({', '.join(f'{m} {g.runtime_s.sum() / 3600:.1f}' for m, g in done.groupby('machine'))}).", ""]

    path = os.path.join(OUT, "CALIBRATION.md")
    with open(path, "w") as fh:
        fh.write("\n".join(L))
    print(path)


if __name__ == "__main__":
    main(sys.argv[1:])
