"""Screenshot an artboard with prefers-reduced-motion set, to check the resting frame.
usage: reduced.py FILE.dc.html WIDTH HEIGHT OUT.png"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve()
w, h = int(sys.argv[2]), int(sys.argv[3])
plain = src.with_name("." + src.name + ".reduced.html")
plain.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, reduced_motion="reduce")
        page = ctx.new_page()
        page.goto(plain.as_uri())
        page.evaluate("() => document.fonts.ready.then(() => true)")
        page.wait_for_timeout(200)
        page.screenshot(path=sys.argv[4])
        print("running animations:", page.evaluate("() => document.getAnimations().length"))
        b.close()
finally:
    plain.unlink(missing_ok=True)
