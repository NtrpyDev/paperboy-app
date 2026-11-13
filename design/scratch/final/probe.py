"""probe.py NAME WIDTH HEIGHT 'js expression returning JSON-able'  evaluate in the rendered board"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
name, w, h, js = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
src = (HERE.parents[1] / "canvas" / "project" / f"{name}.dc.html").resolve()
tmp = src.with_name("." + src.name + ".probe.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": w, "height": h}).new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(800)
        print(json.dumps(pg.evaluate(js), indent=1))
        b.close()
finally:
    tmp.unlink(missing_ok=True)
