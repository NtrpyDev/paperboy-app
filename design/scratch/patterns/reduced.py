"""Render each board with prefers-reduced-motion: reduce and compare the still with the resting frame of the normal render.
usage: uv run --quiet --with playwright --with pillow python design/scratch/patterns/reduced.py"""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
P = HERE.parents[1] / "canvas" / "project"
OUT = HERE.parents[1] / "shots" / "patterns" / "reduced"
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for name, w in (("Explainer-Patterns-Day", 390), ("Explainer-Patterns-Night", 390), ("Explainer-Wide", 1200)):
        src = (P / f"{name}.dc.html").resolve()
        tmp = src.with_name("." + src.name + ".reduced.html")
        tmp.write_text(dc_shot.to_plain_html(src.read_text()))
        try:
            shots = {}
            for mode, wait in (("reduce", 500), ("no-preference", 7000)):
                pg = b.new_context(viewport={"width": w, "height": 844}, device_scale_factor=2, reduced_motion=mode).new_page()
                pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(wait)
                if mode == "no-preference":
                    pg.evaluate("() => document.getAnimations().forEach(a => { try { a.finish() } catch (e) {} })")   # the pen point's pulse is the one loop: park it at full opacity
                    pg.evaluate("() => document.getAnimations().forEach(a => a.cancel())")
                f = OUT / f"{name}-{mode}.png"
                pg.screenshot(path=str(f), full_page=True); shots[mode] = f
            a, c = Image.open(shots["reduce"]).convert("RGB"), Image.open(shots["no-preference"]).convert("RGB")
            diff = ImageChops.difference(a, c).getbbox() if a.size == c.size else "sizes differ"
            print(name, a.size, "difference between the reduced-motion still and the resting frame:", diff)
        finally:
            tmp.unlink(missing_ok=True)
    b.close()
