"""Screenshots of a page at a phone viewport, scrolled like a reader would scroll it.

  uv run --with playwright design/scratch/web/scroll_shots.py URL OUT_DIR [--scheme dark] [--max 12]

Saves OUT_DIR/scroll-NN.png, one per viewport height from the top, and prints the page height.
A full-page capture stretches the viewport, which distorts anything sized by viewport height
(scroll steps), so this scrolls a real 390 by 844 window.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from dc_shot import browser_path  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

url, out = sys.argv[1], pathlib.Path(sys.argv[2])
scheme = "dark" if "--scheme" in sys.argv and sys.argv[sys.argv.index("--scheme") + 1] == "dark" else "light"
limit = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 12
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=browser_path())
    page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=scheme)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(3000)
    height = page.evaluate("document.documentElement.scrollHeight")
    print("page height at 390x844:", height, "errors:", errors)
    y, n = 0, 0
    while y < height and n < limit:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(900)
        page.screenshot(path=str(out / f"scroll-{n:02d}.png"))
        y += 800
        n += 1
    browser.close()
