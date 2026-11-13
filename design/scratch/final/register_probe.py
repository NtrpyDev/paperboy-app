"""Read the transforms of the two plate layers with every animation paused at a few times,
to confirm Register (the frame tool's first frame lands after it has finished)."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
src = (HERE.parents[1] / "canvas" / "project" / "App-Feed-Day.dc.html").resolve()
tmp = src.with_name("." + src.name + ".reg.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
JS = """(ms) => { document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms });
  const out = {}; for (const a of document.getAnimations()) { const n = a.animationName; if (n === 'registerA' || n === 'registerB' || n === 'inkproof') { const cs = getComputedStyle(a.effect.target); out[n] = n === 'inkproof' ? cs.clipPath : cs.transform } } return out }"""
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)")
        for ms in (0, 60, 120, 300, 540, 600):
            print(ms, json.dumps(pg.evaluate(JS, ms)))
        b.close()
finally:
    tmp.unlink(missing_ok=True)
