"""Render an artboard with prefers-reduced-motion: reduce. reduced_shot.py FILE OUT.png W H"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from dc_shot import to_plain_html, browser_path
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve()
plain = src.with_name("." + src.name + ".rm.html")
plain.write_text(to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=browser_path(), headless=True, args=["--no-sandbox"])
        ctx = b.new_context(viewport={"width": int(sys.argv[3]), "height": int(sys.argv[4])}, device_scale_factor=1, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.goto(plain.as_uri())
        pg.evaluate("() => document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(700)
        pg.screenshot(path=sys.argv[2])
        print("running animations:", pg.evaluate("() => document.getAnimations().filter(a => a.playState === 'running').length"),
              "paused:", pg.evaluate("() => document.getAnimations().filter(a => a.playState === 'paused').length"))
        b.close()
finally:
    plain.unlink(missing_ok=True)
