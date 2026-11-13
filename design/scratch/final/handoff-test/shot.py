import pathlib, sys, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for scheme in ("light", "dark"):
        pg = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=scheme).new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
        pg.goto((HERE / "test.html").as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(900); pg.screenshot(path=str(HERE / f"test-{scheme}-t1.png"))
        names = pg.evaluate("() => [...new Set(document.getAnimations().map(a => a.animationName))]")
        pg.wait_for_timeout(2600)
        pg.evaluate("() => { const b = document.getElementById('more'); b.setAttribute('aria-pressed', 'true'); b.classList.add('is-stamping') }")
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(HERE / f"test-{scheme}-full.png"), full_page=True)
        info = pg.evaluate("() => ({sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight, penR: getComputedStyle(document.querySelector('.pb-pen')).r, trapW: getComputedStyle(document.querySelector('.pb-live-trap')).strokeWidth, stamp: getComputedStyle(document.getElementById('more')).backgroundColor, small: [...document.querySelectorAll('.pb *')].filter(e => e.children.length === 0 && e.textContent.trim() && parseFloat(getComputedStyle(e).fontSize) < 10).length})")
        print(scheme, names, json.dumps(info), errs[:5])
    b.close()
