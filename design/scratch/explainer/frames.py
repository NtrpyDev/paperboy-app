"""Exact animation frames. Every CSS animation on the page is paused and set to the same clock
time, so a frame at 150 ms really is 150 ms (the screenshot tool cannot land that early).

usage: frames.py FILE.dc.html OUTDIR PREFIX "name@ms,ms,..:selector-or-y0-y1" ...
  a target is either a CSS selector with an index (figure#2) or a y range in css px (0-520)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright

src = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
prefix = sys.argv[3]
plain = src.with_name("." + src.name + ".frames.html")
plain.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2).new_page()
        pg.goto(plain.as_uri())
        pg.evaluate("() => document.fonts.ready.then(() => true)")
        H = pg.evaluate("() => document.documentElement.scrollHeight")
        for spec in sys.argv[4:]:
            head, target = spec.split(":")
            name, times = head.split("@")
            if "#" in target:
                sel, idx = target.split("#")
                r = pg.evaluate("([s, i]) => { const e = document.querySelectorAll(s)[i].getBoundingClientRect(); return [e.top + scrollY, e.bottom + scrollY]; }", [sel, int(idx)])
                y0, y1 = max(0, r[0] - 12), min(H, r[1] + 12)
            else:
                y0, y1 = [float(v) for v in target.split("-")]
            for t in times.split(","):
                pg.evaluate("(t) => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", float(t))
                f = out / f"{prefix}-{name}-t{int(float(t)):04d}.png"
                pg.screenshot(path=str(f), full_page=True, clip={"x": 0, "y": y0, "width": 390, "height": y1 - y0})
                print(f)
        b.close()
finally:
    plain.unlink(missing_ok=True)
