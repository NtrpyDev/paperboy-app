"""Measures the given copy in the system's cuts, to see which lines fit 350 px. Prints widths."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools")); sys.path.insert(0, str(HERE.parent / "engraved"))
import dc_shot
from lib import FONTS, DISP
from playwright.sync_api import sync_playwright
FIRST = ["Start your free trial.", "Can't reach Google Play.", "No subscription found.", "Your subscription ended.", "Payment problem.", "Paperboy numbers"]
SECOND = ["[TRIAL DAYS] days free.", "days free.", "Nothing was charged.", "On this Google account.", "Subscribe to keep reading.", "Reading is paused."]
BTN = ["Start free trial", "Fix payment in Google Play", "Manage in Google Play", "Subscription", "Subscribe", "Try again"]
def span(t, st): return f'<div><span class="m" data-k="{st[0]}" style="white-space: nowrap; font-family: {DISP}; {st[1]}">{t}</span></div>'
cuts = []
for size in (44, 30):
    cuts.append((f"D1 {size} day", f"font-size: {size}px; font-weight: 800; font-stretch: 62.5%; letter-spacing: -0.005em", FIRST))
    cuts.append((f"D2 {size} night", f"font-size: {size}px; font-weight: 900; font-stretch: 62.5%; letter-spacing: -0.005em", FIRST))
    cuts.append((f"D4 {size} day", f"font-size: {size}px; font-weight: 300; font-stretch: 100%; font-style: italic; letter-spacing: -0.012em", SECOND))
    cuts.append((f"D5 {size} night", f"font-size: {size}px; font-weight: 400; font-stretch: 87.5%; font-style: italic; letter-spacing: -0.012em", SECOND))
cuts.append(("D3 23", "font-size: 23px; font-weight: 700; font-stretch: 75%; letter-spacing: 0.005em", BTN))
html = "<!doctype html><html><head>" + FONTS + "</head><body>" + "".join(span(t, c) for c in cuts for t in c[2]) + "</body></html>"
tmp = HERE / ".measure.html"; tmp.write_text(html)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
        pg = b.new_page(); pg.goto(tmp.as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)"); pg.wait_for_timeout(800)
        for k, t, w in pg.evaluate("() => [...document.querySelectorAll('.m')].map(e => [e.dataset.k, e.textContent, e.getBoundingClientRect().width])"):
            print(f"{k:<14} {w:7.1f} {'FITS' if w <= 350 else 'over'}  {t}")
        b.close()
finally:
    tmp.unlink(missing_ok=True)
