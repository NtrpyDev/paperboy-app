"""Print every response that is not 200 while a page loads.

  uv run --with playwright design/scratch/web/status_log.py URL
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from dc_shot import browser_path  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=browser_path())
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.on("response", lambda r: r.status != 200 and print(r.status, r.url))
    page.goto(sys.argv[1], wait_until="networkidle")
    browser.close()
