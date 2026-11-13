"""Screenshot the element matched by a selector (with padding). usage: clip.py WIDTH HEIGHT WAIT_MS SELECTOR OUT.png [pad] [index]"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
w, h, wait, sel, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
pad = int(sys.argv[6]) if len(sys.argv) > 6 else 16
idx = int(sys.argv[7]) if len(sys.argv) > 7 else 0
src = pathlib.Path(sys.argv[8]).resolve() if len(sys.argv) > 8 else HERE.parents[1] / "canvas" / "project" / "Site.dc.html"
tmp = src.with_name("." + src.name + ".clip.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2).new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(wait)
        r = pg.evaluate("([s, i]) => { const e = document.querySelectorAll(s)[i]; const r = e.getBoundingClientRect(); return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height} }", [sel, idx])
        pg.screenshot(path=out, full_page=True, clip={"x": max(0, r["x"] - pad), "y": max(0, r["y"] - pad), "width": r["w"] + 2 * pad, "height": r["h"] + 2 * pad})
        print(out, r)
        b.close()
finally:
    tmp.unlink(missing_ok=True)
