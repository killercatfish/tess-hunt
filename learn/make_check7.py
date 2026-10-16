"""Hand check 7, side by side: every number the preprint states, next to the file it should come from.

  python3 learn/make_check7.py        -> writes learn/check7.html

Reads paper/toi913_candidate.tex and paper/data/*.json (paper/data is gitignored; it's the supplement zip's data).
For each claim it shows the sentence from the preprint, the raw value from the source file, the arithmetic that
turns one into the other, and a status computed here: MATCH, MISMATCH, or BY HAND (no file holds it). It doesn't
judge whether the science is right; that's your part. It only says whether the paper repeats its own files.
"""
import html, json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = open(os.path.join(ROOT, "paper/toi913_candidate.tex")).read()


def J(name):
    return json.load(open(os.path.join(ROOT, "paper/data", name)))


def tex_plain(s):
    s = re.sub(r"\\(textbf|emph|texttt|textsc|mathrm)\{([^}]*)\}", r"\2", s)
    s = re.sub(r"\^\{\+?([^}]*)\}_\{-?([^}]*)\}", r" (+\1 / −\2)", s)
    for a, b in [("\\,", " "), ("\\pm", "±"), ("$", ""), ("''", "″"), ("\\%", "%"), ("\\star", "★"), ("\\odot", "☉"),
                 ("\\oplus", "⊕"), ("\\rho", "ρ"), ("\\chi", "χ"), ("\\sigma", "σ"), ("\\approx", "≈"), ("\\geq", "≥"),
                 ("\\&", "&"), ("--", "–"), ("~", " "), ("\\ ", " "), ("``", "“"), ("\\le", "≤")]:
        s = s.replace(a, b)
    s = re.sub(r"\\(cite|ref|label)\{[^}]*\}", "", s)
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def quote(*needles):
    """The preprint sentence (or table row) containing each needle, in plain text."""
    out = []
    flat = re.sub(r"\s+", " ", TEX)
    for n in needles:
        i = flat.find(n)
        if i < 0:
            out.append(f"[not found in the .tex: {n}]")
            continue
        t0, t1 = flat.rfind("\\begin{tabular}", 0, i), flat.rfind("\\end{tabular}", 0, i)
        if t0 > t1:                                         # inside a table: return that row
            a = flat.rfind("\\\\", 0, i) + 2
            b = flat.find("\\\\", i)
            out.append("Table row: " + tex_plain(flat[a:b]).replace(" & ", " | "))
            continue
        a = max(flat.rfind(". ", 0, i) + 2, flat.rfind("\\noindent ", 0, i) + 10, flat.rfind("} ", 0, i) + 2 if flat.rfind("\\textbf", 0, i) < flat.rfind(". ", 0, i) else 0)
        b = flat.find(". ", i)
        out.append(tex_plain(flat[a:b + 1 if b > 0 else len(flat)]))
    return out


def pm(q):   # [16th, 50th, 84th] percentiles -> median, +err, -err
    return q[1], q[2] - q[1], q[1] - q[0]


def same(paper, value, places):
    return round(value, places) == paper


rows = []


def row(n, claim, needles, source, raw, work, checks, say, worry, concept):
    status = "BY HAND" if checks is None else ("MATCH" if all(checks) else "MISMATCH")
    rows.append(dict(n=n, claim=claim, quotes=quote(*needles), source=source, raw=raw, work=work,
                     status=status, say=say, worry=worry, concept=concept))


# 1 -------------------------------------------------------------------------------------------------
tf, ps = J("transit_fit.json"), J("pipeline_signal.json")
c = tf["joint"]["P5.4501"]
P, Pp, Pm = pm(c["period"]); D, Dp, Dm = pm(c["depth_ppm"]); K = c["k"]
R_EARTH_PER_SUN = 109.076
rp = K[1] * ps["star"]["rad"] * R_EARTH_PER_SUN
row(1, "Period, depth and radius", ["P = 5.450138 \\pm 0.000016", "radius of $1.12"],
    "paper/data/transit_fit.json → joint → P5.4501 (16th, 50th, 84th percentiles)",
    f"period {c['period']}\ndepth_ppm {[round(x, 1) for x in c['depth_ppm']]}\nk (Rp/R★) {[round(x, 5) for x in K]}\n"
    f"R★ {ps['star']['rad']} R☉ (pipeline_signal.json → star.rad)",
    f"P = {P:.6f} ± {(Pp + Pm) / 2:.6f} d\ndepth = {D:.0f} +{Dp:.0f} / −{Dm:.0f} ppm\n"
    f"Rp = k × R★ × 109.08 = {K[1]:.5f} × {ps['star']['rad']:.4f} × 109.08 = {rp:.2f} R⊕\n"
    f"The ±0.09 also carries R★'s own uncertainty, which isn't in this file (paper/code/transit_fit.py).",
    [same(5.450138, P, 6), same(196, D, 0), same(24, Dp, 0), same(21, Dm, 0), same(1.12, rp, 2)],
    "Depth is (Rp/R★)². 196 ppm on a 0.73 R☉ star is a planet about Earth's size. You did this in hand check 1.",
    "A radius that doesn't follow from k and R★.", "§1, §4")

# 2 -------------------------------------------------------------------------------------------------
s = ps["signal"]
row(2, "Search detection: SDE, SNR, transits", ["SDE 23.6"],
    "paper/data/pipeline_signal.json → signal",
    f"sde {s['sde']}\nsnr {s['snr']}\nn_transits {s['n_transits']}\niteration {s['iteration']}",
    f"SDE {s['sde']:.1f}, SNR {s['snr']:.1f}, {s['n_transits']} transits. Iteration 2 means TOI-913 b was found and masked first.",
    [same(23.6, s["sde"], 1), same(8.9, s["snr"], 1), s["n_transits"] == 34],
    "SDE is how far the best peak stands above the rest of the periodogram (threshold 9). SNR is depth over its noise.",
    "Numbers that only clear the thresholds narrowly. These clear them comfortably, but see rows 3 and 4 for why SDE alone isn't the story.",
    "§4")
if "SDE 23.6" not in TEX:
    rows[-1]["quotes"] = quote("SDE", "34 transits")[:1]

# 3 -------------------------------------------------------------------------------------------------
oe = s["tests"]["odd_even"]
sig = abs(oe["depth_odd_ppm"] - oe["depth_even_ppm"]) / math.hypot(oe["err_odd_ppm"], oe["err_even_ppm"])
row(3, "Odd/even depths", ["odd/even depth ($211$"],
    "paper/data/pipeline_signal.json → signal.tests.odd_even",
    "\n".join(f"{k} {v}" for k, v in oe.items()),
    f"|{oe['depth_odd_ppm']:.0f} − {oe['depth_even_ppm']:.0f}| / √({oe['err_odd_ppm']:.1f}² + {oe['err_even_ppm']:.1f}²) = {sig:.2f}σ\n"
    f"(the formula in tesshunt/killtests.py odd_even). The preprint said 0.4σ until 10/16.",
    [same(211, oe["depth_odd_ppm"], 0), same(245, oe["depth_even_ppm"], 0), same(0.7, sig, 1)],
    "An eclipsing binary at twice the period shows alternating depths. Odd and even agree here either way (pass limit 3σ).",
    "A difference over 3σ. Here the issue is only that the paper misquotes its own file.", "§8")

# 4 -------------------------------------------------------------------------------------------------
rob = {v["name"]: v for v in J("robustness.json")["variants"]}
q = rob["QLP (FFI) biweight auto"]
b0 = rob["baseline PDCSAP biweight auto"]
row(4, "Robustness table: QLP row", ["QLP FFI photometry (8 sectors)", "independently recovered as the strongest periodic signal"],
    "paper/data/robustness.json → variants → \"QLP (FFI) biweight auto\" (the file in the supplement zip)",
    "\n".join(f"{k} {v}" for k, v in q.items() if k != "sectors"),
    f"File: {q['depth_ppm']:.0f} ± {q['err_ppm']:.0f} ppm, SNR {q['snr']:.1f}; robust {q['depth_robust_ppm']:.0f} ppm; no full-search result.\n"
    f"Paper: 250 ± 23 ppm, SNR 10.6, top peak SDE 15.2. No file in the supplement holds those numbers. The file looks like a run "
    f"from before the QLP quality fix in scripts/robustness_check.py (load_ffi), which drops QLP's junk cadences in Sectors 100–102.",
    [same(250, q["depth_ppm"], 0)],
    "QLP is a different pipeline working from different images (30-min full frames). Seeing the signal there too means it isn't an artefact of SPOC's processing. That's why the abstract leans on it.",
    "A claim in the abstract with no file behind it. That's what this is until the QLP run is redone and saved.", "§4, §6")

# 5 -------------------------------------------------------------------------------------------------
row(5, "Robustness table: the other rows", ["Every season and sector jackknife gives"],
    "paper/data/robustness.json → variants, diagnostics.jackknife",
    "\n".join(f"{n}: {v['depth_ppm']:.1f} ± {v['err_ppm']:.1f} ppm, SNR {v['snr']:.2f}, full search {v.get('full_tls_period')}"
              for n, v in rob.items() if not n.startswith("QLP")),
    "Baseline 225 ± 24 (9.5); cosine 297 ± 23 (13.1); SAP 159 ± 24 (6.6); TESS-SPOC 185 ± 31 (6.0); windows 230 / 232 / 231 / 235.\n"
    "Jackknife range: " + ", ".join(f"{x[1]:.0f}" for x in J("robustness.json")["diagnostics"]["jackknife"]),
    [same(225, b0["depth_ppm"], 0), same(297, rob["cosine (robust) auto"]["depth_ppm"], 0),
     same(159, rob["SAP biweight auto"]["depth_ppm"], 0), same(185, rob["TESS-SPOC (FFI) biweight auto"]["depth_ppm"], 0),
     min(x[1] for x in J("robustness.json")["diagnostics"]["jackknife"]) >= 195.5,
     max(x[1] for x in J("robustness.json")["diagnostics"]["jackknife"]) < 244.5],
    "Detrending choices move the depth by tens of ppm, not hundreds, and dropping any season or sector keeps it. "
    "Depths here (225) sit above the fit's 196 because this measure uses the transit's deeper middle.",
    "A variant where the signal vanishes. Only uncorrected SAP flux weakens it, and the paper says so.", "§3, §6")

# 6 -------------------------------------------------------------------------------------------------
fap = J("periodogram_fap.json")["tls"]
row(6, "Shuffled false-alarm test", ["block-shuffled copies"],
    "paper/data/periodogram_fap.json → tls",
    f"observed_sde {fap['observed_sde']}\nnull.trials {fap['null']['trials']}\nnull.max_sde_max {fap['null']['max_sde_max']}\n"
    f"null.n_exceeding {fap['null']['n_exceeding']}\nnull.fap_upper_95 {fap['null']['fap_upper_95']}\nmasked {fap['masked']}",
    f"0 of {fap['null']['trials']} shuffled light curves reached SDE {fap['observed_sde']:.1f} (their best was {fap['null']['max_sde_max']:.1f}). "
    f"Zero in 200 gives a 95% upper limit of 3/200 = 1.5%.",
    [fap["null"]["n_exceeding"] == 0, fap["null"]["trials"] == 200, same(0.015, fap["null"]["fap_upper_95"], 3)],
    "Shuffling one-day blocks keeps the noise but breaks any real period, so this asks how often noise alone gives an SDE this high.",
    "Shuffling can't keep systematics that repeat over many days. That's what row 7 is for.", "§5")

# 7 -------------------------------------------------------------------------------------------------
inv = J("inversion_test.json")
unrel = [x for x in inv["inverted"] if abs(x["period"] - 11.0994) > 0.01]
row(7, "Inverted light curve", ["inverted light curve"],
    "paper/data/inversion_test.json",
    "real:\n" + "\n".join(f"  {x['period']:.4f} d SDE {x['sde']:.2f}" for x in inv["real"]) +
    "\ninverted:\n" + "\n".join(f"  {x['period']:.4f} d SDE {x['sde']:.2f}" for x in inv["inverted"]),
    f"Signal SDE {inv['real_sde_5p45']:.1f}. Strongest inverted peak not at b's period (11.099 d): {unrel[0]['period']:.2f} d, SDE {max(x['sde'] for x in unrel):.1f}.\n"
    f"The two inverted peaks at 11.099 d are b's detrending shoulders turned upside down.",
    [same(21.7, inv["real_sde_5p45"], 1), same(14.5, max(x["sde"] for x in unrel), 1)],
    "Flipping the light curve turns bumps into dips. Systematics come out about as strong either way; a real transit doesn't.",
    "An inverted peak as strong as the signal.", "§5")

# 8 -------------------------------------------------------------------------------------------------
h = J("harmonic_systematic_test.json")
row(8, "Not a harmonic of the 27.3 d systematic", ["drift apart by 0.59"],
    "paper/data/harmonic_systematic_test.json",
    f"five_P {h['five_P']}\nfive_P_err {h['five_P_err']}\nsyst_period {h['syst_period']}\nalignment_slip_d {h['alignment_slip_d']}\n"
    f"alignment_slip_in_5p45_periods {h['alignment_slip_in_5p45_periods']}\nfar {h['far']}\nall {h['all']}",
    f"5P = {h['five_P']:.4f} vs {h['syst_period']:.4f} d; slip {h['alignment_slip_d']:.1f} d = {h['alignment_slip_in_5p45_periods']:.2f} periods.\n"
    f"Far transits: {h['far']['depth_ppm']:.0f} ± {h['far']['err_ppm']:.0f} ppm (n={h['far']['n']}); all: {h['all']['depth_ppm']:.0f} ± {h['all']['err_ppm']:.0f}.",
    [same(0.59, h["alignment_slip_in_5p45_periods"], 2), same(222, h["far"]["depth_ppm"], 0), h["far"]["n"] == 32],
    "If the dip were the systematic folded at a fifth of its period, the depth would sit in the transits that line up with it. It doesn't.",
    "Depth concentrated in the 2 transits near a 27.3 d event.", "§6")

# 9 -------------------------------------------------------------------------------------------------
fr = tf["free"]["P5.4501"]["rho"]
r, rp_, rm_ = pm(fr)
row(9, "Stellar density from the transit", ["free stellar density"],
    "paper/data/transit_fit.json → free → P5.4501 → rho, and catalogue_rho",
    f"rho {fr}\ncatalogue_rho {tf['catalogue_rho']}",
    f"ρ★ = {r:.2f} +{rp_:.2f} / −{rm_:.2f} ρ☉ against the catalogue's {tf['catalogue_rho'][0]:.2f} ± {tf['catalogue_rho'][1]:.2f}.",
    [same(2.43, r, 2), same(0.97, rp_, 2), same(1.01, rm_, 2), same(2.09, tf["catalogue_rho"][0], 2)],
    "Transit shape and period imply how dense the star is. A dip on a different star (a giant, say) would imply the wrong density.",
    "A density far from the catalogue's. These overlap well, though the error is wide.", "§7")

# 10 ------------------------------------------------------------------------------------------------
M_SUN, G, R_SUN = 1.989e30, 6.674e-11, 6.957e8
ar = {m: (G * m * M_SUN * (5.450138 * 86400) ** 2 / (4 * math.pi ** 2)) ** (1 / 3) / (10 * R_SUN) for m in (1, 3)}
dur = {m: 5.450138 * 24 / math.pi * math.asin(min(1, 1 / ar[m])) for m in ar}
row(10, "The 9.5″ giant is excluded by duration", ["a/R_\\star \\approx 1.3"],
    "Computed here from Kepler's third law (no file); R = 10 R☉ from the TIC",
    "R = 10 R☉, M = 1–3 M☉, P = 5.450138 d",
    f"a/R★ = {ar[1]:.2f} (1 M☉) to {ar[3]:.2f} (3 M☉)\ncentral transit ≈ P/π × asin(R★/a) = {dur[1]:.0f} h to {dur[3]:.0f} h, against 2.4 h observed.",
    [same(1.3, ar[1], 1), same(1.9, ar[3], 1), same(36, dur[1], 0), same(23, dur[3], 0)],
    "Something orbiting a 10 R☉ giant every 5.45 days would take a day or more to cross it. A 2.4 h dip can't come from there. You did this in hand check 1.",
    "If the giant's radius in the TIC were wrong by a factor of several. The paper says the exclusion rests on this alone.", "§8")
if "a/R_\\star \\approx 1.3" not in TEX:
    rows[-1]["quotes"] = quote("a/R")

# 11 ------------------------------------------------------------------------------------------------
tr = J("triceratops_speckle_nogalaxy.json")
val = tr["FPP_mean"] < 0.015 and tr["NFPP_mean"] < 0.001
lik = tr["FPP_mean"] < 0.5 and tr["NFPP_mean"] < 0.001
row(11, "TRICERATOPS FPP and NFPP, and 'planet candidate'", ["FPP $=0.036\\pm0.001$", "it is a planet candidate, not a likely or validated planet"],
    "paper/data/triceratops_speckle_nogalaxy.json",
    f"FPP_mean {tr['FPP_mean']}\nFPP_std {tr['FPP_std']}\nNFPP_mean {tr['NFPP_mean']}\nNFPP_std {tr['NFPP_std']}\ndropped {tr['dropped']}\nruns {len(tr['runs'])} × N={tr['N']}",
    f"FPP {tr['FPP_mean']:.3f} ± {tr['FPP_std']:.3f}, NFPP {tr['NFPP_mean']:.3f} ± {tr['NFPP_std']:.3f}.\n"
    f"Validated needs FPP < 0.015 and NFPP < 0.001: {val}. Likely planet needs FPP < 0.5 and NFPP < 0.001: {lik}.\n"
    f"Dropped from the scenarios: the 56.9″ galaxy and its duplicate (your hand check 3).",
    [same(0.036, tr["FPP_mean"], 3), same(0.023, tr["NFPP_mean"], 3), not val, not lik],
    "FPP is the chance it's any false positive; NFPP is the chance it's an eclipse on a neighbouring star. NFPP is what keeps this a candidate.",
    "Calling it 'likely' or 'validated' with NFPP at 0.023.", "§9, §10, §11")

# 12 ------------------------------------------------------------------------------------------------
sc = J("single_transit_scatter.json")
x, g = sc["scatter"], sc["groups"]
row(12, "Single-transit scatter and TOI-913 b", ["Single-transit scatter", "Neither b's mask nor its gravity"],
    "paper/data/single_transit_scatter.json (the Cortex run)",
    f"scatter.chi2_dof {x['chi2_dof']}\nscatter.null_median {x['null_median']}\nscatter.null_frac_ge {x['null_frac_ge']}\n"
    f"groups.sector chi2 {g['sector']['chi2']} p {g['sector']['p']}\ngroups.season p {g['season']['p']}\n"
    f"b_proximity spearman {sc['b_proximity']['spearman_abs_dt_vs_depth']['rho']}\nb_mask_widths {[round(m['mean_ppm']) for m in sc['b_mask_widths']]}",
    f"χ²/dof {x['chi2_dof']:.2f} vs null median {x['null_median']:.2f}; {100 * x['null_frac_ge']:.0f}% of null phases as large.\n"
    f"Sector χ² {g['sector']['chi2']:.1f} (p {g['sector']['p']:.3f}); season p {g['season']['p']:.2f}.",
    [same(1.51, x["chi2_dof"], 2), same(1.16, x["null_median"], 2), same(21, 100 * x["null_frac_ge"], 0),
     same(16.6, g["sector"]["chi2"], 1), same(0.020, g["sector"]["p"], 3), same(0.30, g["season"]["p"], 2)],
    "Your hand check 6. A planet blocks the same light every time; extra scatter would point to a blend or a systematic. It's somewhat high here, not significant.",
    "Scatter well beyond what blank stretches of the same light curve show.", "§4, §6")


# ---------------------------------------------------------------------------------------------------- page
CSS = """
:root{--bg:#0d1220;--panel:#151c2e;--rule:#2a3550;--ink:#e8ebf3;--muted:#9aa5bf;--accent:#ffad5c;--good:#7fd6a6;--wait:#f2c46b;--bad:#ff8a80;
  --body:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;--mono:ui-monospace,Menlo,monospace;color-scheme:dark}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f7f6f2;--panel:#fff;--rule:#dcd8cc;--ink:#1d2233;--muted:#535c72;
  --accent:#b85c00;--good:#1f7a4d;--wait:#8a6400;--bad:#b3261e;color-scheme:light}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--body);padding:36px 16px 80px}
.wrap{max-width:1180px;margin:0 auto;display:grid;gap:22px}h1{font-size:1.8rem;margin:0}p{margin:0}.muted{color:var(--muted)}
.sum{display:flex;gap:10px;flex-wrap:wrap}.pill{font:600 .8rem/1 var(--mono);padding:7px 12px;border-radius:999px;border:1px solid var(--rule)}
article{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:18px 20px;display:grid;gap:14px}
article.MISMATCH{border-color:var(--bad)}
.head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}.head h2{font-size:1.1rem;margin:0}
.st{font:700 .72rem/1 var(--mono);letter-spacing:.08em;padding:6px 10px;border-radius:6px;color:var(--bg)}
.MATCH .st{background:var(--good)}.MISMATCH .st{background:var(--bad)}.BYHAND .st{background:var(--wait)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media (max-width:820px){.cols{grid-template-columns:1fr}}
.k{font:600 .68rem/1.2 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.box{background:var(--bg);border:1px solid var(--rule);border-radius:8px;padding:10px 12px;min-width:0}
pre{margin:0;font:12.5px/1.5 var(--mono);white-space:pre-wrap;word-break:break-word}
blockquote{margin:0 0 8px;font-size:.95rem}code{font-family:var(--mono);font-size:.85em}
.say{border-left:3px solid var(--good);padding-left:12px}.worry{border-left:3px solid var(--bad);padding-left:12px}
label{display:flex;gap:8px;align-items:center;font-size:.9rem;color:var(--muted)}
"""
n_m = sum(r["status"] == "MATCH" for r in rows)
n_x = sum(r["status"] == "MISMATCH" for r in rows)
e = html.escape
arts = []
for r in rows:
    arts.append(f"""<article class="{r['status'].replace(' ', '')}" id="r{r['n']}">
<div class="head"><h2>{r['n']}. {e(r['claim'])}</h2><span class="st">{r['status']}</span></div>
<div class="cols">
<div class="box"><div class="k">The preprint says</div>{''.join(f'<blockquote>{e(q)}</blockquote>' for q in r['quotes'])}</div>
<div class="box"><div class="k">The source holds</div><p class="muted" style="font-size:.85rem;margin-bottom:6px"><code>{e(r['source'])}</code></p><pre>{e(r['raw'])}</pre></div>
</div>
<div class="box"><div class="k">From one to the other</div><pre>{e(r['work'])}</pre></div>
<div class="cols"><p class="say"><b>You should be able to say:</b> {e(r['say'])} <span class="muted">(guide {e(r['concept'])})</span></p>
<p class="worry"><b>Would worry you:</b> {e(r['worry'])}</p></div>
<label><input type="checkbox"> I traced this and can explain it</label>
</article>""")
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Check 7 Side by Side</title><style>{CSS}</style></head><body><div class="wrap">
<p class="muted"><a href="guide.html" style="color:inherit">← Learning guide</a> · <a href="../index.html" style="color:inherit">TESS home</a></p>
<h1>Hand check 7, side by side</h1>
<p class="muted">Each claim in the preprint next to the file it comes from. Green means the paper repeats its own file; red means it doesn't.
Green doesn't mean the science is right. That's what the "you should be able to say" line is for. Built by <code>learn/make_check7.py</code> from
<code>paper/toi913_candidate.tex</code> and <code>paper/data/</code>; rerun it after any edit. Ticks aren't saved.</p>
<div class="sum"><span class="pill" style="color:var(--good)">{n_m} match</span><span class="pill" style="color:var(--bad)">{n_x} mismatch</span>
<span class="pill">{len(rows)} claims</span></div>
{''.join(arts)}
</div></body></html>"""
open(os.path.join(ROOT, "learn/check7.html"), "w").write(page)
print(f"learn/check7.html: {n_m} match, {n_x} mismatch, {len(rows)} claims")
for r in rows:
    if r["status"] != "MATCH":
        print(f"  {r['n']}. {r['claim']}: {r['status']}")
