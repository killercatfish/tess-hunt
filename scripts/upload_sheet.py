"""Make a copy-paste sheet (HTML) for a Zenodo upload, one copy button per field.

  python3 scripts/upload_sheet.py paper/prereg_s114/zenodo_fields.json
  -> writes zenodo_fields.html next to the JSON and prints its path

JSON: {"title": "...", "files": ["..."], "fields": [{"label": "...", "value": "...", "note": "..."}]}
A field may set "rows" (a list of lists) instead of "value" for tables such as Related works.
"""
import html, json, os, sys

CSS = """
:root{--bg:#0d1220;--panel:#151c2e;--rule:#2a3550;--ink:#e8ebf3;--muted:#9aa5bf;--accent:#ffad5c;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,system-ui,sans-serif;padding:32px 16px 64px}
.wrap{max-width:860px;margin:0 auto;display:grid;gap:14px}h1{font-size:1.5rem;margin:0}.muted{color:var(--muted)}
.f{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:14px 16px;display:grid;gap:8px}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:12px}.lab{font-weight:700}
.val{font-family:ui-monospace,Menlo,monospace;font-size:.88rem;white-space:pre-wrap;word-break:break-word;background:#0a0f1c;border-radius:6px;padding:10px 12px}
button{font:600 .8rem/1 -apple-system,system-ui,sans-serif;color:#1a1206;background:var(--accent);border:0;border-radius:999px;padding:7px 14px;cursor:pointer}
button.done{background:#7fd6a6}table{border-collapse:collapse;width:100%;font-size:.88rem}td,th{border-bottom:1px solid var(--rule);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600}td button{padding:5px 10px}ul{margin:0;padding-left:1.2em}
"""
JS = """
function cp(b,t){const done=()=>{b.textContent='Copied';b.classList.add('done');setTimeout(()=>{b.textContent='Copy';b.classList.remove('done')},1500)};
 if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,()=>fb(t,done))}else fb(t,done)}
function fb(t,done){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();done()}
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>cp(b,b.dataset.copy)));
"""


def btn(text):
    return f'<button data-copy="{html.escape(text, quote=True)}">Copy</button>'


def main(path):
    spec = json.load(open(path))
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
           f"<title>{html.escape(spec['title'])}</title><style>{CSS}</style></head><body><div class='wrap'>",
           f"<h1>{html.escape(spec['title'])}</h1>"]
    if spec.get("intro"):
        out.append(f"<p class='muted'>{html.escape(spec['intro'])}</p>")
    if spec.get("files"):
        out.append("<div class='f'><span class='lab'>Files to upload</span><ul>" +
                   "".join(f"<li><code>{html.escape(f)}</code></li>" for f in spec["files"]) + "</ul></div>")
    for f in spec["fields"]:
        out.append("<div class='f'>")
        if "rows" in f:
            out.append(f"<span class='lab'>{html.escape(f['label'])}</span><table><tr>" +
                       "".join(f"<th>{html.escape(h)}</th>" for h in f["header"]) + "</tr>")
            for r in f["rows"]:
                out.append("<tr>" + "".join(f"<td>{html.escape(c)} {btn(c) if i in f.get('copy_cols', []) else ''}</td>"
                                            for i, c in enumerate(r)) + "</tr>")
            out.append("</table>")
        else:
            out.append(f"<div class='top'><span class='lab'>{html.escape(f['label'])}</span>{btn(f['value'])}</div>"
                       f"<div class='val'>{html.escape(f['value'])}</div>")
        if f.get("note"):
            out.append(f"<span class='muted'>{html.escape(f['note'])}</span>")
        out.append("</div>")
    out.append(f"</div><script>{JS}</script></body></html>")
    dest = os.path.splitext(path)[0] + ".html"
    open(dest, "w").write("\n".join(out))
    print(dest)


if __name__ == "__main__":
    main(sys.argv[1])
