#!/usr/bin/env python3
"""
build.py — regenerate index.html (a single self-contained web page) from timeline_v9.md.

Usage:
    python3 build.py

- timeline_v9.md stays the canonical source. This script parses its era sections
  and tables and embeds the data inline in index.html, so the page works by
  double-click (file://) AND on GitHub Pages with no server and no separate JSON.
- Re-run after updating timeline_v9.md.
"""
import json, re, sys, pathlib, datetime

HERE = pathlib.Path(__file__).parent
SRC = HERE / "timeline_v9.md"
OUT = HERE / "index.html"

# --- confidence -> group/color (priority order; REFUTED dominates) -----------
def confidence_group(conf: str):
    c = conf.upper()
    if "REFUTED" in c or "🔴" in conf:
        return ("Refuted / unresolved", "refuted")
    if "✅" in conf:
        return ("Documented (primary)", "documented")
    if "📚" in conf:
        return ("Secondary / compiled", "secondary")
    if "🔵" in conf:
        return ("Probable inference", "inference")
    if "🟡" in conf:
        return ("Possible / lead", "possible")
    if "🗣️" in conf or "🗣" in conf:
        return ("Oral history", "oral")
    if "⬜" in conf:
        return ("Unverified", "unverified")
    return ("Other / unrated", "other")

# --- family tagging (keyword-based; a lead, not authoritative) ----------------
FAMILY_PATTERNS = {
    "Hutcheson": r"hutche?son|hutchi?son|hutchinson|hutcherson|\bsion\b|\bdaniel\b|\bgreen\b|\bgus\b|\bkitsy\b|\bkitsey\b|fleming|pollard",
    "Chancey":   r"chancey|chancy|chaney|chauncey|\bkitsy\b|\bkitsey\b|irvin|irwin|alexander chanc|rhoda|rhody",
    "Mixon":     r"mixon|moxon|\bsamuel gooden\b|sarah mixon|ichabod|nathan mixon|jehu",
}
def families_for(event: str):
    e = event.lower()
    return [fam for fam, pat in FAMILY_PATTERNS.items() if re.search(pat, e)]

# --- parse the markdown ------------------------------------------------------
def parse(md: str):
    lines = md.splitlines()
    title = "Family Timeline"
    last_updated = ""
    sections, cur = [], None
    for ln in lines:
        s = ln.strip()
        if s.startswith("# ") and title == "Family Timeline":
            title = s[2:].strip()
        m = re.match(r"\*\*Last Updated:\*\*\s*(.+)", s)
        if m and not last_updated:
            last_updated = re.sub(r"\s*\(.*", "", m.group(1)).strip()  # trim the long parenthetical
        if s.startswith("## "):
            cur = {"title": s[3:].strip(), "events": []}
            sections.append(cur)
            continue
        if cur is None or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        date, event, conf, ref = cells
        if date.lower() in ("year", "date") or set(date) <= set("-: "):
            continue  # header row / separator
        grp, cls = confidence_group(conf)
        cur["events"].append({
            "date": date,
            "event": event,
            "confidence": conf,
            "reference": ref,
            "era": cur["title"],
            "is_context": "HISTORICAL CONTEXT" in event,
            "families": families_for(event),
            "group": grp,
            "cls": cls,
        })
    sections = [s for s in sections if s["events"]]
    return title, last_updated, sections

# --- HTML template (placeholders filled by replace) --------------------------
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex, nofollow" />
<title>__TITLE__</title>
<style>
  :root{
    --bg:#f5f1e8; --panel:#fffdf8; --ink:#2b2622; --muted:#7a7068; --line:#e3dccd;
    --documented:#2e7d32; --secondary:#1565c0; --inference:#00838f; --possible:#c98a00;
    --unverified:#8a8a8a; --oral:#6a1b9a; --refuted:#c62828; --other:#8a8a8a;
  }
  *{box-sizing:border-box}
  body{margin:0;font:16px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
  a{color:var(--secondary)}
  header.hero{background:#3a322a;color:#f5f1e8;padding:28px 22px}
  header.hero h1{margin:.1em 0;font-size:1.5rem}
  header.hero p{margin:.2em 0;color:#d9cfbf;max-width:60ch}
  .eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;color:#c0b29a}
  .wrap{display:grid;grid-template-columns:240px 1fr;gap:22px;max-width:1100px;margin:22px auto;padding:0 18px}
  .sidebar{position:sticky;top:14px;align-self:start;display:grid;gap:14px}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
  .panel h2{margin:0 0 .5em;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
  nav#eraNav a{display:block;padding:4px 6px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:.86rem}
  nav#eraNav a:hover{background:#efe9da}
  .legend p{display:flex;align-items:center;gap:8px;margin:.35em 0;font-size:.82rem}
  .swatch{width:12px;height:12px;border-radius:3px;flex:0 0 auto}
  .controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
  .controls input,.controls select,.controls button{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink)}
  .controls input[type=search]{flex:1;min-width:200px}
  .controls button{cursor:pointer}
  .stats{display:flex;gap:18px;flex-wrap:wrap;margin:0 0 14px;color:var(--muted);font-size:.85rem}
  .stats b{color:var(--ink);font-size:1.1rem}
  .era{margin:0 0 26px}
  .era h2{font-size:1.05rem;border-bottom:2px solid var(--line);padding-bottom:6px;margin:0 0 12px;scroll-margin-top:14px}
  .card{position:relative;background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--other);
        border-radius:10px;padding:12px 14px;margin:0 0 10px;display:grid;grid-template-columns:96px 1fr;gap:14px}
  .card.documented{border-left-color:var(--documented)} .card.secondary{border-left-color:var(--secondary)}
  .card.inference{border-left-color:var(--inference)} .card.possible{border-left-color:var(--possible)}
  .card.unverified{border-left-color:var(--unverified)} .card.oral{border-left-color:var(--oral)}
  .card.refuted{border-left-color:var(--refuted);background:#fdf3f2}
  .card.context{background:#f3f0ff}
  .date{font-weight:700;color:var(--muted);font-size:.9rem}
  .event{font-size:.97rem}
  .event strong{font-weight:700}
  .muted{color:var(--muted);text-decoration:line-through}
  .meta{margin-top:7px;display:flex;flex-wrap:wrap;gap:6px}
  .pill{font-size:.72rem;padding:2px 8px;border-radius:999px;border:1px solid var(--line);background:#faf7f0;color:var(--muted)}
  .pill.conf{color:#fff;border:0}
  .conf.documented{background:var(--documented)} .conf.secondary{background:var(--secondary)}
  .conf.inference{background:var(--inference)} .conf.possible{background:var(--possible)}
  .conf.unverified{background:var(--unverified)} .conf.oral{background:var(--oral)}
  .conf.refuted{background:var(--refuted)} .conf.other{background:var(--other)}
  .src{margin-top:6px;font-size:.76rem;color:var(--muted)}
  code{background:#efe9da;padding:0 4px;border-radius:4px;font-size:.85em}
  footer{max-width:1100px;margin:10px auto 40px;padding:0 18px;color:var(--muted);font-size:.8rem}
  @media(max-width:760px){.wrap{grid-template-columns:1fr}.sidebar{position:static}.card{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="hero">
  <p class="eyebrow">Family History Project</p>
  <h1>__TITLE__</h1>
  <p>A navigable chronology of the Hutcheson, Chancey, and Mixon families — every entry tagged with how solid the evidence is. <span style="color:#c0b29a">Last updated: __LASTUPDATED__</span></p>
</header>
<div class="wrap">
  <aside class="sidebar">
    <div class="panel"><h2>Jump to era</h2><nav id="eraNav"></nav></div>
    <div class="panel legend"><h2>Confidence key</h2>
      <p><span class="swatch" style="background:var(--documented)"></span>✅ Documented (primary)</p>
      <p><span class="swatch" style="background:var(--secondary)"></span>📚 Secondary / compiled</p>
      <p><span class="swatch" style="background:var(--inference)"></span>🔵 Probable inference</p>
      <p><span class="swatch" style="background:var(--possible)"></span>🟡 Possible / lead</p>
      <p><span class="swatch" style="background:var(--oral)"></span>🗣️ Oral history</p>
      <p><span class="swatch" style="background:var(--unverified)"></span>⬜ Unverified</p>
      <p><span class="swatch" style="background:var(--refuted)"></span>🔴 Refuted / unresolved</p>
      <p style="color:var(--muted)"><span class="swatch" style="background:#f3f0ff;border:1px solid var(--line)"></span>Historical context</p>
    </div>
  </aside>
  <main>
    <div class="stats" id="stats"></div>
    <div class="controls">
      <input id="q" type="search" placeholder="Search people, places, events, sources…" />
      <select id="era"><option value="">All eras</option></select>
      <select id="family"><option value="">All families</option></select>
      <select id="conf"><option value="">All confidence</option></select>
      <label style="display:flex;align-items:center;gap:6px;font-size:.85rem"><input type="checkbox" id="ctx" /> Hide context notes</label>
      <button id="reset">Reset</button>
    </div>
    <div id="timeline"></div>
  </main>
</div>
<footer>Generated from <code>timeline_v9.md</code> (the canonical source). To update, edit the Markdown and run <code>python3 build.py</code>. Confidence ratings reflect the research project's evidence discipline.</footer>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const f = {q:"",era:"",family:"",conf:"",hideCtx:false};
const md = s => (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;")
  .replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>")
  .replace(/~~(.+?)~~/g,'<span class="muted">$1</span>')
  .replace(/`([^`]+)`/g,"<code>$1</code>");
const all = () => DATA.sections.flatMap(s=>s.events);
const uniq = a => [...new Set(a)].sort();

function fill(sel, vals){vals.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;sel.appendChild(o)})}
function init(){
  fill($("#era"), DATA.sections.map(s=>s.title));
  fill($("#family"), uniq(all().flatMap(e=>e.families)));
  fill($("#conf"), uniq(all().map(e=>e.group)));
  $("#eraNav").innerHTML = DATA.sections.map(s=>`<a href="#${slug(s.title)}">${s.title}</a>`).join("");
  ["q","era","family","conf"].forEach(id=>$("#"+id).addEventListener("input",e=>{f[id===''?'':id]=e.target.value; f[id]=e.target.value; render()}));
  $("#ctx").addEventListener("change",e=>{f.hideCtx=e.target.checked; render()});
  $("#reset").addEventListener("click",()=>{Object.assign(f,{q:"",era:"",family:"",conf:"",hideCtx:false});["q","era","family","conf"].forEach(id=>$("#"+id).value="");$("#ctx").checked=false;render()});
  render();
}
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/(^-|-$)/g,"");
function match(e){
  if(f.era && e.era!==f.era) return false;
  if(f.family && !e.families.includes(f.family)) return false;
  if(f.conf && e.group!==f.conf) return false;
  if(f.hideCtx && e.is_context) return false;
  if(f.q){const h=[e.date,e.event,e.confidence,e.reference,e.era].join(" ").toLowerCase(); if(!h.includes(f.q.toLowerCase())) return false;}
  return true;
}
function card(e){
  const fam = e.families.map(x=>`<span class="pill">${x}</span>`).join("");
  const ctx = e.is_context?'<span class="pill">Historical context</span>':"";
  const src = e.reference && e.reference!=="—" ? `<div class="src">Source: ${md(e.reference)}</div>`:"";
  return `<article class="card ${e.cls}${e.is_context?' context':''}">
    <div class="date">${e.date}</div>
    <div><div class="event">${md(e.event)}</div>
    <div class="meta"><span class="pill conf ${e.cls}">${e.confidence}</span>${ctx}${fam}</div>${src}</div></article>`;
}
function render(){
  const t=$("#timeline"); t.innerHTML="";
  let shown=0;
  DATA.sections.forEach(sec=>{
    const evs=sec.events.filter(match); if(!evs.length) return; shown+=evs.length;
    const el=document.createElement("section"); el.className="era"; el.id=slug(sec.title);
    el.innerHTML=`<h2>${sec.title}</h2>`+evs.map(card).join(""); t.appendChild(el);
  });
  if(!shown) t.innerHTML="<p>No entries match those filters.</p>";
  const total=all().length, ctx=all().filter(e=>e.is_context).length;
  $("#stats").innerHTML=`<span><b>${shown}</b> of ${total} entries shown</span><span><b>${DATA.sections.length}</b> eras</span><span><b>${ctx}</b> historical-context notes</span>`;
}
init();
</script>
</body>
</html>
"""

def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    title, last_updated, sections = parse(SRC.read_text(encoding="utf-8"))
    data = {"title": title, "sections": sections}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")  # safe inside <script>
    html = (TEMPLATE
            .replace("__TITLE__", title)
            .replace("__LASTUPDATED__", last_updated or "")
            .replace("__DATA__", payload))
    OUT.write_text(html, encoding="utf-8")
    n = sum(len(s["events"]) for s in sections)
    print(f"Wrote {OUT}  ({n} entries across {len(sections)} eras)")

if __name__ == "__main__":
    main()
