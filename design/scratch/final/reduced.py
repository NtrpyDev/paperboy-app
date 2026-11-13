"""Render every board with prefers-reduced-motion: reduce, to check the still frame."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
P = HERE.parents[1] / "canvas" / "project"
OUT = HERE.parents[1] / "shots" / "final" / "reduced"
OUT.mkdir(parents=True, exist_ok=True)
JOBS = [("App-Feed-Day", 390, 844, False), ("App-Feed-Night", 390, 844, False), ("Explainer-Day", 390, 844, True),
        ("Explainer-Night", 390, 844, True), ("Site", 1440, 900, True), ("Site", 390, 844, True),
        ("Brand", 1200, 900, False), ("Motion", 1200, 1000, False)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for name, w, h, full in JOBS:
        src = (P / f"{name}.dc.html").resolve()
        tmp = src.with_name("." + src.name + ".reduced.html")
        tmp.write_text(dc_shot.to_plain_html(src.read_text()))
        try:
            pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, reduced_motion="reduce").new_page()
            pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(300)
            running = pg.evaluate("() => document.getAnimations().filter(a => a.playState === 'running').length")
            out = OUT / f"{name}-{w}w-reduced.png"
            pg.screenshot(path=str(out), full_page=full)
            print(name, w, "running animations:", running, out)
        finally:
            tmp.unlink(missing_ok=True)
    b.close()
