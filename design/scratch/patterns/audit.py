"""Audit the patterns boards: root size, overflow, touch targets, text sizes, text contrast, svg text, running animations
with reduced motion. usage: uv run --quiet --with playwright python design/scratch/patterns/audit.py [Name:width ...]"""
import pathlib, sys, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
P = HERE.parents[1] / "canvas" / "project"
JOBS = [a.split(":") for a in sys.argv[1:]] or [["Explainer-Patterns-Day", "390"], ["Explainer-Patterns-Night", "390"]]
JS = r"""() => {
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]) };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > 0.99) return c } return parse(getComputedStyle(document.body).backgroundColor) || [255, 255, 255, 1] };
  const cr = (fg, bg) => { const a = lum(fg), b = lum(bg); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) };
  const els = [];
  for (const el of document.querySelectorAll('a[href],button,input,summary')) {
    const r = el.getBoundingClientRect(); if (r.width === 0) continue;
    els.push({tag: el.tagName, text: (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 30), w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, y: Math.round(r.top + scrollY)});
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
    const v = cr(fg, bg); const need = fs >= 24 ? 3 : 4.5;
    if (v < need) { const kk = cs.color + ' on ' + bg.slice(0, 3).join(',') + ' @' + fs + 'px = ' + v.toFixed(2); low[kk] = low[kk] || n.textContent.trim().slice(0, 30) }
  }
  const page = parse(getComputedStyle(document.body).backgroundColor);
  const svgText = [...document.querySelectorAll('svg text')].filter(t => t.getBoundingClientRect().width > 0).map(t => ({px: parseFloat(getComputedStyle(t).fontSize) * (t.getCTM() ? t.getCTM().a : 1), fill: getComputedStyle(t).fill, s: t.textContent.slice(0, 24)}));
  const svgMin = svgText.length ? svgText.reduce((m, t) => t.px < m.px ? t : m) : null;
  const svgFills = {}; for (const t of svgText) { const f = parse(t.fill); const k = t.fill + ' = ' + (f ? cr(f, page).toFixed(2) : '?'); svgFills[k] = (svgFills[k] || 0) + 1 }
  const cw = document.documentElement.clientWidth;
  const over = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); if (r.width === 0 || r.right <= cw + 0.5) return false; for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'hidden' || o === 'clip') return false } return !e.closest('svg') }).map(e => e.tagName + ' ' + (e.innerText || '').slice(0, 24) + ' right=' + Math.round(e.getBoundingClientRect().right)).slice(0, 6);
  const root = document.body.firstElementChild.getBoundingClientRect();
  const bad = [...document.querySelectorAll('body *')].filter(e => { const cs = getComputedStyle(e); return cs.boxShadow !== 'none' || parseFloat(cs.borderLeftWidth) > 1.01 || (cs.filter && cs.filter !== 'none') || cs.backgroundImage.includes('gradient') }).map(e => e.tagName + ':' + (e.className || '') ).slice(0, 8);
  const radius = [...document.querySelectorAll('body *')].filter(e => { const r = parseFloat(getComputedStyle(e).borderTopLeftRadius); const b = e.getBoundingClientRect(); return r > 0 && b.width > 8 }).map(e => e.tagName + ' ' + Math.round(e.getBoundingClientRect().width)).slice(0, 8);
  const running = document.getAnimations().filter(a => a.playState === 'running').length;
  const fonts = [...new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/"/g, '')))];
  return {els, sizes, low, svgMin, svgFills, over, bad, radius, running, fonts, root: [root.width, root.height], sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight, cw};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for name, w in JOBS:
        w = int(w)
        src = (P / f"{name}.dc.html").resolve()
        tmp = src.with_name("." + src.name + ".paudit.html")
        tmp.write_text(dc_shot.to_plain_html(src.read_text()))
        try:
            for reduced in (False, True):
                ctx = b.new_context(viewport={"width": w, "height": 844}, reduced_motion="reduce" if reduced else "no-preference")
                pg = ctx.new_page()
                errs = []
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(tmp.as_uri())
                pg.evaluate("() => document.fonts.ready.then(() => true)")
                pg.wait_for_timeout(600 if reduced else 6500)
                r = pg.evaluate(JS)
                if reduced:
                    print(f"   reduced motion: running animations {r['running']}, errors {errs}")
                    continue
                small = [e for e in r["els"] if e["h"] < 44 or e["w"] < 44]
                print(f"== {name} @{w}: root {r['root']} scroll {r['sw']}x{r['sh']} overflow_x {r['sw'] > r['cw']} past-right {r['over']} errors {errs}")
                print(f"   fonts {r['fonts']}")
                print(f"   targets {len(r['els'])}: {[(e['tag'], e['text'], e['w'], e['h']) for e in r['els']]}")
                print(f"   under 44: {small}")
                print("   sizes", dict(sorted(r["sizes"].items(), key=lambda kv: float(kv[0].split(' ')[0]))))
                print("   svg text min", r["svgMin"], "fills", r["svgFills"])
                print("   low contrast", r["low"])
                print("   shadow, left border over 1px, filter, gradient:", r["bad"], " radius on boxes over 8px:", r["radius"])
        finally:
            tmp.unlink(missing_ok=True)
    b.close()
