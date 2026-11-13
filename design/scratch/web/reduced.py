"""Full-page capture with prefers-reduced-motion: reduce, taken at once. usage: reduced.py WIDTH OUT.png"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
w, out = int(sys.argv[1]), sys.argv[2]
src = HERE.parents[1] / "canvas" / "project" / "Site.dc.html"
tmp = src.with_name("." + src.name + ".reduced.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1, reduced_motion="reduce").new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(100)
        print("running animations:", pg.evaluate("() => document.getAnimations().length"))
        pg.screenshot(path=out, full_page=True)
        b.close()
finally:
    tmp.unlink(missing_ok=True)
