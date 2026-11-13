"""After the animations rest, is every animated vermilion mark painted in a full-page capture?
(One was not: see live_seg() in site.py.) usage: paintcheck.py [widths...]"""
import sys, pathlib, io
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
from PIL import Image
src = HERE.parents[1] / "canvas" / "project" / "Site.dc.html"
tmp = src.with_name("." + src.name + ".paint.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
JS = """() => [...document.querySelectorAll('[style*="animation"]')].map(e => {
  const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
  const live = [cs.fill, cs.stroke, cs.backgroundColor].some(c => c === 'rgb(224, 51, 10)') || !!e.querySelector('[fill="#E0330A"],[stroke="#E0330A"]');
  let vis = r.width + r.height > 0; for (let p = e; p; p = p.parentElement) { const s = getComputedStyle(p); if (s.display === 'none' || s.visibility === 'hidden') vis = false; }
  return {tag: e.tagName, live, vis, x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height, an: cs.animationName};
})"""
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        for w in [int(a) for a in sys.argv[1:]] or [1440, 390]:
            pg = b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1).new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(4000)
            els = [e for e in pg.evaluate(JS) if e["live"] and e["vis"]]
            im = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")
            bad = []
            for e in els:
                x0, y0 = max(0, int(e["x"]) - 4), max(0, int(e["y"]) - 4)
                x1, y1 = min(im.width, int(e["x"] + e["w"]) + 5), min(im.height, int(e["y"] + e["h"]) + 5)
                if x1 <= x0 or y1 <= y0: continue
                px = im.crop((x0, y0, x1, y1)).getdata()
                n = sum(1 for r, g, bl in px if r > 180 and g < 110 and bl < 80)
                if n == 0: bad.append((e["tag"], e["an"], round(e["x"]), round(e["y"])))
            print(w, "animated vermilion marks:", len(els), "unpainted:", bad)
            pg.close()
        b.close()
finally:
    tmp.unlink(missing_ok=True)
