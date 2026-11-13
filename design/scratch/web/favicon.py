"""The website's favicon, from the Brand board's small icon master.

  uv run --with playwright --with pillow design/scratch/web/favicon.py

writes site/favicon.svg and site/favicon.ico (16, 32, and 48 px). Browsers ask for
/favicon.ico on every page, explainers included, so the worker serves it from the site root.
"""
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "design" / "scratch" / "brandmotion"))
sys.path.insert(0, str(ROOT / "design" / "tools"))
import bm  # noqa: E402
from dc_shot import browser_path  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

SITE = ROOT / "site"
svg = bm.app_icon("fav", 512, theme="day", master="small")
svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1).replace(' style="display: block; flex: none"', "")
(SITE / "favicon.svg").write_text(svg + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=browser_path())
    page = browser.new_page(viewport={"width": 512, "height": 512})
    page.set_content(f'<body style="margin:0">{svg}</body>')
    png = page.screenshot(clip={"x": 0, "y": 0, "width": 512, "height": 512})
    browser.close()

Image.open(io.BytesIO(png)).convert("RGBA").save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("wrote", SITE / "favicon.svg", SITE / "favicon.ico")
