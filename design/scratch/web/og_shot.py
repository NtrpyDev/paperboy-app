"""Render the Open Graph card (design/scratch/web/og.html, written by site_page.py) to site/og.png.

  uv run --with playwright design/scratch/web/og_shot.py

Serves the repo root on a local port so the card loads the kit fonts at /kit/v2/fonts/.
"""
import functools
import http.server
import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "design" / "tools"))
from dc_shot import browser_path  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(REPO)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/design/scratch/web/og.html"
out = REPO / "site" / "og.png"
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=browser_path(), headless=True, args=["--no-sandbox"])
        page = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1, reduced_motion="reduce")
        page.goto(url)
        page.evaluate("() => document.fonts.ready.then(() => true)")
        fonts = sorted(set(page.evaluate("() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.style)")))
        page.wait_for_timeout(300)
        page.screenshot(path=str(out))
        b.close()
finally:
    server.shutdown()
print("wrote", out, "fonts:", fonts)
