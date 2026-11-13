"""Final audit of the seven boards: root size, overflow, touch targets, text sizes, text contrast.
usage: uv run --quiet --with playwright python design/scratch/final/audit.py
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

P = HERE.parents[1] / "canvas" / "project"
JOBS = [
    ("App-Feed-Day", 390, 844), ("App-Feed-Night", 390, 844),
    ("Explainer-Day", 390, 844), ("Explainer-Night", 390, 844),
    ("Site", 1440, 900), ("Site", 1160, 900), ("Site", 1024, 900), ("Site", 900, 900),
    ("Site", 768, 900), ("Site", 700, 900), ("Site", 390, 844), ("Site", 360, 800),
    ("Brand", 1200, 900), ("Motion", 1200, 1000),
]
JS = r"""() => {
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]) };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > 0.99) return c } return parse(getComputedStyle(document.body).backgroundColor) || [255, 255, 255, 1] };
  const els = [];
  for (const el of document.querySelectorAll('a[href],button,input')) {
    const r = el.getBoundingClientRect(); if (r.width === 0) continue;
    els.push({tag: el.tagName, text: (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 34), w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, y: Math.round(r.top + scrollY)});
  }
  const sizes = {}; const low = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const pe = n.parentElement; if (pe.closest('svg') || pe.closest('script') || pe.closest('style')) continue;
    const r = pe.getBoundingClientRect(); if (r.width === 0) continue;
    const cs = getComputedStyle(pe); const fs = parseFloat(cs.fontSize);
    const k = fs + ' ' + cs.fontFamily.split(',')[0].replace(/['"]/g, ''); sizes[k] = (sizes[k] || 0) + 1;
    const fg = parse(cs.color), bg = bgOf(pe); if (!fg) continue;
    const a = lum(fg), b = lum(bg); const cr = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const need = fs >= 24 ? 3 : 4.5;
    if (cr < need) { const kk = cs.color + ' on ' + bg.slice(0, 3).join(',') + ' @' + fs + 'px = ' + cr.toFixed(2); low[kk] = (low[kk] || '') || n.textContent.trim().slice(0, 30) }
  }
  const svgText = [...document.querySelectorAll('svg text')].filter(t => t.getBoundingClientRect().width > 0).map(t => ({px: parseFloat(getComputedStyle(t).fontSize) * (t.getCTM() ? t.getCTM().a : 1), fill: getComputedStyle(t).fill, s: t.textContent.slice(0, 24)}));
  const svgMin = svgText.length ? svgText.reduce((m, t) => t.px < m.px ? t : m) : null;
  const svgFills = {}; for (const t of svgText) svgFills[t.fill] = (svgFills[t.fill] || 0) + 1;
  const cw = document.documentElement.clientWidth;
  const over = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); if (r.width === 0 || r.right <= cw + 0.5) return false; for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'hidden' || o === 'clip') return false } return !e.closest('svg') }).map(e => e.tagName + ' ' + (e.innerText || '').slice(0, 24) + ' right=' + Math.round(e.getBoundingClientRect().right)).slice(0, 6);
  const root = document.body.firstElementChild.getBoundingClientRect();
  return {els, sizes, low, svgMin, svgFills, over, root: [root.width, root.height], sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight, cw};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for name, w, h in JOBS:
        src = (P / f"{name}.dc.html").resolve()
        raw = src.read_text()
        tmp = src.with_name("." + src.name + ".finalaudit.html")
        tmp.write_text(dc_shot.to_plain_html(raw))
        try:
            pg = b.new_context(viewport={"width": w, "height": h}).new_page()
            pg.goto(tmp.as_uri())
            pg.evaluate("() => document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(6500)
            r = pg.evaluate(JS)
        finally:
            tmp.unlink(missing_ok=True)
        small = [e for e in r["els"] if e["h"] < 44 or e["w"] < 44]
        print(f"== {name} @{w}: root {r['root']} scroll {r['sw']}x{r['sh']} overflow_x {r['sw'] > r['cw']} past-right {r['over']}")
        print(f"   targets {len(r['els'])}, under 44: {small}")
        print("   sizes", dict(sorted(r["sizes"].items(), key=lambda kv: float(kv[0].split(' ')[0]))))
        print("   svg text min", r["svgMin"], "fills", r["svgFills"])
        print("   low contrast", r["low"])
        if w in (1440, 390, 1200) and name == "Site":
            pass
    b.close()
