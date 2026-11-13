"""Load the site artboard at a width and run a JS expression. usage: probe.py WIDTH HEIGHT WAIT_MS 'js' [file]"""
import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
w, h, wait, js = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
src = pathlib.Path(sys.argv[5]).resolve() if len(sys.argv) > 5 else HERE.parents[1] / "canvas" / "project" / "Site.dc.html"
tmp = src.with_name("." + src.name + ".probe.html")
tmp.write_text(dc_shot.to_plain_html(src.read_text()))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_context(viewport={"width": w, "height": h}).new_page()
        pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(wait)
        print(json.dumps(pg.evaluate(js), indent=1))
        b.close()
finally:
    tmp.unlink(missing_ok=True)
