import sys, pathlib, re
sys.path.insert(0, "design/tools")
import dc_shot
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve()
plain = src.with_name("." + src.name + ".probe.html")
plain.write_text(dc_shot.to_plain_html(src.read_text()))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    pg = b.new_context(viewport={"width": int(sys.argv[2]), "height": 900}).new_page()
    pg.goto(plain.as_uri()); pg.wait_for_timeout(3500)
    print(pg.evaluate(sys.argv[3]))
    b.close()
plain.unlink()
