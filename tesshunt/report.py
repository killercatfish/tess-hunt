"""Static, sortable report.html of survivors (plus run counts). No external assets."""
import html
import json
import os
import time

from . import db, provenance

CSS = """
:root{--bg:#fff;--fg:#1d1d1f;--mut:#666;--line:#ddd;--pass:#1a7f37;--fail:#c62828;--flag:#9a6700;--row:#f6f6f6}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#e8e8e8;--mut:#999;--line:#333;--pass:#4ac26b;--fail:#ff6b6b;--flag:#e3b341;--row:#1d1d1d}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1500px}
h1{font-size:20px;margin:0 0 4px} .mut{color:var(--mut)} table{border-collapse:collapse;width:100%;margin-top:12px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{cursor:pointer;position:sticky;top:0;background:var(--bg)} tr:nth-child(even) td{background:var(--row)}
.p{color:var(--pass)} .f{color:var(--fail)} .w{color:var(--flag)} .wrap{overflow-x:auto}
.audit{max-width:420px;font-size:12px;white-space:pre-wrap} img{max-width:100%}
"""
JS = """
document.querySelectorAll('th').forEach((th,i)=>th.onclick=()=>{const tb=th.closest('table').tBodies[0];
const rows=[...tb.rows];const asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
rows.sort((a,b)=>{const x=a.cells[i].dataset.v??a.cells[i].innerText,y=b.cells[i].dataset.v??b.cells[i].innerText;
const nx=parseFloat(x),ny=parseFloat(y);const c=(isNaN(nx)||isNaN(ny))?x.localeCompare(y):nx-ny;return asc?c:-c});
rows.forEach(r=>tb.appendChild(r))});
"""


def _fmt(v, f="{:.2f}"):
    return "" if v is None else f.format(v)


def build(cfg, title="tess-hunt candidates", labels=None):
    con = db.connect(cfg["paths"]["db"])
    q = "SELECT label, status, COUNT(*) FROM targets"
    counts = con.execute(q + " GROUP BY label, status").fetchall()
    where = "WHERE s.verdict='survivor'"
    args = []
    if labels:
        where += f" AND t.label IN ({','.join('?' * len(labels))})"
        args = list(labels)
    rows = con.execute(f"""SELECT s.tic, s.iteration, s.period, s.depth_ppm, s.duration_h, s.rp_rearth, s.sde, s.snr,
        s.n_transits, s.score, s.tests, s.audit, t.teff, t.tmag, t.n_sectors, t.baseline_d, t.provenance
        FROM signals s JOIN targets t USING(tic) {where} ORDER BY s.score DESC""", args).fetchall()
    nrej = con.execute("SELECT COUNT(*) FROM signals WHERE verdict='rejected'").fetchone()[0]
    out_dir = os.path.dirname(cfg["paths"]["report"])
    trs = []
    for i, r in enumerate(rows, 1):
        (tic, it, P, dep, dur, rp, sde, snr, ntr, score, tj, audit, teff, tmag, nsec, base, pj) = r
        tests = json.loads(tj)
        flags = []
        for name, res in tests.items():
            p = res.get("pass")
            if p is False:
                flags.append(f'<span class="w">{name}</span>')
            elif p is None:
                flags.append(f'<span class="mut">{name}:n/a</span>')
        ho = tests.get("holdout", {})
        hos = f"{ho['hits']}/{ho['attempts']}" if ho.get("attempts") else "n/a"
        rel = os.path.relpath(os.path.join(cfg["paths"]["candidates_dir"], str(tic)), out_dir)
        known = tests.get("known", {})
        kn = ", ".join(m["name"] for v in known.get("matches", {}).values() for m in v)[:60]
        trs.append(f"""<tr><td>{i}</td><td data-v="{tic}"><a href="{rel}/sig{it}.png">TIC {tic}</a><br>
<span class="mut">sig#{it} · <a href="{rel}/sig{it}.json">json</a><br>{html.escape(provenance.label(json.loads(pj) if pj else None))}</span></td>
<td>{_fmt(score, '{:.1f}')}</td><td>{_fmt(P, '{:.5f}')}</td><td>{_fmt(dep, '{:.0f}')}</td><td>{_fmt(dur)}</td>
<td>{_fmt(rp)}</td><td>{_fmt(sde, '{:.1f}')}</td><td>{_fmt(snr, '{:.1f}')}</td><td>{ntr}</td><td>{hos}</td>
<td>{_fmt(teff, '{:.0f}')}</td><td>{_fmt(tmag)}</td><td>{nsec}</td><td>{_fmt(base, '{:.0f}')}</td>
<td>{' '.join(flags)}{('<br><span class="w">known: ' + html.escape(kn) + '</span>') if kn else ''}</td>
<td class="audit">{html.escape(audit or '')}</td></tr>""")
    made = html.escape(provenance.label(cfg.get("_provenance") or provenance.stamp(cfg)))
    runs = "<br>".join(f"{n} star(s): {html.escape(provenance.label(st))}" for st, n in db.provenance_counts(con))
    cnt = " · ".join(f"{l or '-'} {s}: {n}" for l, s, n in counts)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<h1>{html.escape(title)}</h1>
<div class="mut">Generated {time.strftime('%Y-%m-%d %H:%M')} · {len(rows)} survivor signal(s) · {nrej} rejected by kill tests<br>{cnt}<br>
Report built by {made}.<br>Stars processed by:<br>{runs}</div>
<p class="mut">These are <b>candidates</b>, not discoveries. A survivor only means no automatic test killed it.
Score = SNR × (1 + holdout hit fraction) ÷ (1 + soft flags); it ranks, it is not a probability. Click headers to sort.</p>
<div class="wrap"><table><thead><tr><th>#</th><th>target</th><th>score</th><th>P (d)</th><th>depth ppm</th><th>dur h</th><th>Rp R⊕</th>
<th>SDE</th><th>SNR</th><th>N tr</th><th>holdout</th><th>Teff</th><th>Tmag</th><th>sectors</th><th>baseline d</th><th>flags</th><th>audit: reasons it might not be a planet</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div><script>{JS}</script></body></html>"""
    with open(cfg["paths"]["report"], "w") as fh:
        fh.write(doc)
    return cfg["paths"]["report"], len(rows)
