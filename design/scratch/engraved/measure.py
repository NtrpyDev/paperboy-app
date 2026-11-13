"""Print bounding boxes for elements matching a selector in an artboard.
usage: measure.py FILE.dc.html WIDTH HEIGHT 'css selector' [more selectors]"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve()
w, h = int(sys.argv[2]), int(sys.argv[3])
plain = src.with_name("." + src.name + ".measure.html")
plain.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        page = b.new_context(viewport={"width": w, "height": h}).new_page()
        page.goto(plain.as_uri())
        page.evaluate("() => document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)
        for sel in sys.argv[4:]:
            rects = page.evaluate("""(sel) => [...document.querySelectorAll(sel)].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.x*10)/10, Math.round(r.y*10)/10, Math.round(r.width*10)/10, Math.round(r.height*10)/10, (e.textContent||'').trim().slice(0,28)] })""", sel)
            print(sel)
            for r in rects: print("   ", r)
        b.close()
finally:
    plain.unlink(missing_ok=True)
