"""Print the laid-out height of each direct child of an artboard root, to tune a fixed-size board.
  uv run --quiet --with playwright design/scratch/recorder/measure.py FILE.dc.html WIDTH [css selector]"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright

src = pathlib.Path(sys.argv[1]).resolve()
width = int(sys.argv[2])
sel = sys.argv[3] if len(sys.argv) > 3 else "body > div > *"
plain = src.with_name("." + src.name + ".measure.html")
plain.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": width, "height": 900})
        pg.goto(plain.as_uri())
        pg.evaluate("() => document.fonts.ready.then(() => true)")
        rows = pg.evaluate(
            "(s) => [...document.querySelectorAll(s)].map(e => { const r = e.getBoundingClientRect(); return [e.tagName, Math.round(r.top), Math.round(r.height), Math.round(r.left), Math.round(r.width), (e.textContent || '').trim().slice(0, 40)]; })",
            sel)
        for r in rows:
            print(r)
        b.close()
finally:
    plain.unlink(missing_ok=True)
