"""Touch targets, text sizes, overflow, at several widths. usage: audit.py [widths...]"""
import sys, pathlib, json, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
src = HERE.parents[1] / "canvas" / "project" / "Site.dc.html"
raw = src.read_text()
print("em dashes:", raw.count("\u2014"), "| en dashes:", raw.count("\u2013"), "| gradient fns:", len(re.findall(r"gradient\(", raw)), "| border-radius values:", sorted(set(re.findall(r"border-radius: ([^;\"]+)", raw))), "| filter/blur/shadow:", len(re.findall(r"filter:|blur\(|drop-shadow|box-shadow|text-shadow", raw)), "| infinite:", raw.count("infinite"))
widths = [int(a) for a in sys.argv[1:]] or [1440, 390]
JS = """() => {
  const els = [];
  for (const el of document.querySelectorAll('a[href],button,input')) {
    const r = el.getBoundingClientRect();
    els.push({text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 34), w: Math.round(r.width), h: Math.round(r.height * 10) / 10, y: Math.round(r.top + scrollY)});
  }
  const sizes = {};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const pe = n.parentElement; if (pe.closest('svg') || pe.offsetParent === null) continue;
    const cs = getComputedStyle(pe); const k = parseFloat(cs.fontSize) + ' ' + cs.fontFamily.split(',')[0].replace(/['"]/g, '');
    sizes[k] = (sizes[k] || 0) + 1;
  }
  const svgText = [...document.querySelectorAll('svg text')].filter(t => t.getBoundingClientRect().width > 0).map(t => parseFloat(getComputedStyle(t).fontSize) * (t.getCTM() ? t.getCTM().a : 1));
  const over = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > document.documentElement.clientWidth + 0.5 && !e.closest('[style*="overflow: hidden"]') }).map(e => e.tagName + ' ' + (e.innerText || '').slice(0, 30) + ' right=' + Math.round(e.getBoundingClientRect().right)).slice(0, 8);
  return {els, sizes, svgMin: svgText.length ? Math.min(...svgText) : null, over, sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight};
}"""
tmp = src.with_name("." + src.name + ".audit.html")
tmp.write_text(dc_shot.to_plain_html(raw))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        for w in widths:
            pg = b.new_context(viewport={"width": w, "height": 900}).new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(500)
            r = pg.evaluate(JS)
            small = [e for e in r["els"] if e["h"] < 44 or e["w"] < 44]
            print(f"== {w}: scrollWidth {r['sw']} height {r['sh']} | targets {len(r['els'])}, under 44: {small} | svg text min {r['svgMin'] and round(r['svgMin'], 2)} | past right edge: {r['over']}")
            if w in (1440, 390):
                for e in r["els"]: print("   ", e)
                print("    sizes", dict(sorted(r["sizes"].items(), key=lambda kv: float(kv[0].split(' ')[0]))))
            pg.close()
        b.close()
finally:
    tmp.unlink(missing_ok=True)
