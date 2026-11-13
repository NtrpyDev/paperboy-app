"""Screenshot a board with every animation paused at a given time (ms), to see states the
frame tool cannot catch. usage: start_state.py NAME W H MS OUT.png [clip x y w h]"""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
name, w, h, ms, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
clip = [float(v) for v in sys.argv[6:10]] if len(sys.argv) >= 10 else None
src = (HERE.parents[1] / "canvas" / "project" / f"{name}.dc.html").resolve()
tmp = src.with_name("." + src.name + ".start.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2).new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)")
        n = pg.evaluate("(ms) => { const a = document.getAnimations(); a.forEach(x => { x.pause(); x.currentTime = ms }); return a.length }", ms)
        pg.wait_for_timeout(150)
        kw = {"clip": {"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3]}} if clip else {}
        pg.screenshot(path=out, **kw)
        print(name, "paused", n, "animations at", ms, "ms ->", out)
        b.close()
finally:
    tmp.unlink(missing_ok=True)
