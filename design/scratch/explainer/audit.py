"""Audit both boards: touch targets, text sizes, forbidden marks, numbers against CONTENT.md.
usage (from design/): uv run --with playwright python scratch/explainer/audit.py"""
import pathlib, re, sys
sys.path.insert(0, "tools")
import dc_shot
from playwright.sync_api import sync_playwright
P = pathlib.Path("canvas/project")
JS = """() => {
  const els = [...document.querySelectorAll('a[href],button,input')].map(el => { const r = el.getBoundingClientRect();
    return {tag: el.tagName, text: (el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,40), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.top + scrollY)}; });
  const seen = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const p = n.parentElement; if (p.closest('svg') && p.tagName !== 'text') continue;
    const cs = getComputedStyle(p); const k = parseFloat(cs.fontSize).toFixed(2) + '|' + cs.fontFamily.split(',')[0] + '|' + cs.fontWeight + '|' + cs.fontStyle + '|' + cs.fontStretch; seen[k] = (seen[k]||0)+1; }
  const radius = [...document.querySelectorAll('*')].filter(e => { const r = getComputedStyle(e).borderRadius; return r && r !== '0px' && r !== '50%'; }).map(e => e.tagName + ':' + getComputedStyle(e).borderRadius);
  const text = document.body.innerText;
  return {els, seen, radius, text, w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight};
}"""
content = pathlib.Path("CONTENT.md").read_text()
allowed = set(re.findall(r"\d[\d,.:]*\d|\d", content))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for name in ("Explainer-Day", "Explainer-Night"):
        src = (P / f"{name}.dc.html").resolve()
        raw = src.read_text()
        tmp = src.with_name("." + src.name + ".audit.html"); tmp.write_text(dc_shot.to_plain_html(raw))
        try:
            pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(300)
            r = pg.evaluate(JS)
        finally:
            tmp.unlink(missing_ok=True)
        print("==", name, r["w"], "x", r["h"])
        for e in r["els"]:
            print(f"  {e['tag']:6} {e['w']:4}x{e['h']:<4} y={e['y']:<5} {e['text']!r}" + ("   <-- UNDER 44" if e["h"] < 44 or e["w"] < 44 else ""))
        for k, v in sorted(r["seen"].items(), key=lambda kv: float(kv[0].split("|")[0])):
            print("  type", k, "x", v)
        print("  radius other than 0 or 50%:", r["radius"])
        print("  em dash:", raw.count(chr(0x2014)), " en dash:", raw.count(chr(0x2013)), " gradient:", len(re.findall(r"gradient", raw)), " filter:", len(re.findall(r"filter|drop-shadow|blur", raw)),
              " holes:", len(re.findall(r"\{\{|sc-for|sc-if", raw)), " border-left:", len(re.findall(r"border-left|border-inline", raw)), " mask:", raw.count("<mask"))
        nums = set(re.findall(r"\d[\d,.:]*\d|\d", r["text"]))
        extra = sorted(n.rstrip(".,") for n in nums if n.rstrip(".,") not in allowed and n not in allowed)
        print("  numbers on the page not literally in CONTENT.md:", extra)
    b.close()
