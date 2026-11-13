"""Render the patterns stylesheet in both themes and measure what the addendum claims.
usage: uv run --quiet --with playwright python design/scratch/patterns/kit-test/shot.py"""
import pathlib, sys, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import dc_shot
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
    for scheme in ("light", "dark"):
        pg = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=scheme, has_touch=True).new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((HERE / "test.html").as_uri()); pg.evaluate("() => document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(700)
        info = pg.evaluate("""() => {
          const R = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left*10)/10, Math.round(r.top*10)/10, Math.round(r.width*10)/10, Math.round(r.height*10)/10] };
          const q = s => document.querySelector(s);
          const cv = document.createElement('canvas').getContext('2d');
          const xh = f => { cv.font = f; return cv.measureText('x').actualBoundingBoxAscent };
          const kx = getComputedStyle(q('#xk .katex .mord') || q('#xk .katex'));
          return {sw: document.documentElement.scrollWidth, wordmark: R(q('.pb-wordmark')), topbar: R(q('.pb-topbar')), term: R(q('#term')),
            summaryClosed: R(q('#closed > summary')), summaryOpen: R(q('#open > summary')), toggleBtn: R(q('#toggle button')), tip: R(q('#tip')),
            katexInline: getComputedStyle(q('p .katex')).fontSize, katexFont: kx.fontFamily, katexLoaded: [...document.fonts].filter(f => f.family.includes('KaTeX') && f.status === 'loaded').map(f => f.family + ' ' + f.style),
            xBodyPerEm: xh("1000px 'Source Serif 4'") / 1000, xKatexMainPerEm: xh("1000px KaTeX_Main") / 1000, xKatexMathPerEm: xh("italic 1000px KaTeX_Math") / 1000, xOldStandardNote: 'mock font not loaded here',
            mathRect: R(q('.katex-display .katex-html')), afterMath: R(q('#after-math')), para2: R(q('#para + p')), body: [getComputedStyle(q('#para')).fontSize, getComputedStyle(q('#para')).lineHeight],
            display: R(q('.katex-display')), tag: q('.katex .katex-tag') ? [R(q('.katex .katex-tag')), getComputedStyle(q('.katex .katex-tag .mord .mord') || q('.katex .katex-tag')).fontFamily.slice(0, 20), getComputedStyle(q('.katex .katex-tag .mord .mord') || q('.katex .katex-tag')).fontSize, q('.katex .katex-tag').textContent] : null,
            small: [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && e.textContent.trim() && !e.closest('.katex') && parseFloat(getComputedStyle(e).fontSize) < 10).length}
        }""")
        print(scheme, json.dumps(info), errs[:5])
        pg.screenshot(path=str(HERE / f"t-{scheme}-full.png"), full_page=True)
        # the term, opened
        pg.tap("#term"); pg.wait_for_timeout(400)
        t = pg.evaluate("""() => { const p = document.querySelector('.pb-term-pop').getBoundingClientRect(), para = document.querySelector('#para').getBoundingClientRect(), lh = parseFloat(getComputedStyle(document.querySelector('#para')).lineHeight);
          return {popTopInLines: (p.top - para.top) / lh, popHeightInLines: p.height / lh, popLeft: p.left, popWidth: p.width, expanded: document.querySelector('#term').getAttribute('aria-expanded')} }""")
        print("  term open", json.dumps(t))
        pg.screenshot(path=str(HERE / f"t-{scheme}-term.png"), clip={"x": 0, "y": 0, "width": 390, "height": 560})
        pg.tap("h2"); pg.wait_for_timeout(100)
        # scroll steps: pin, then walk the steps
        top = pg.evaluate("() => document.querySelector('#steps').getBoundingClientRect().top + scrollY")
        for k, dy in enumerate((0, 60, 140, 230, 330, 430, 560)):
            pg.evaluate(f"() => window.scrollTo(0, {top + dy})"); pg.wait_for_timeout(250)
            st = pg.evaluate("""() => ({active: [...document.querySelectorAll('.pb-step')].findIndex(s => s.classList.contains('is-active')) + 1, on: document.querySelectorAll('.pb-steps-gauge .is-on').length,
              visualTop: Math.round(document.querySelector('.pb-steps-visual').getBoundingClientRect().top), visualBottom: Math.round(document.querySelector('.pb-steps-visual').getBoundingClientRect().bottom),
              stepTops: [...document.querySelectorAll('.pb-step')].map(s => Math.round(s.getBoundingClientRect().top))})""")
            print("  steps scroll", dy, json.dumps(st))
            if (scheme == "light" and k in (0, 3, 5)) or k == 3:
                pg.screenshot(path=str(HERE / f"t-{scheme}-steps-{k}.png"))
        # toggle: tap the first segment, focus the last of the second toggle
        pg.evaluate("() => document.querySelector('#toggle').scrollIntoView({block: 'center'})"); pg.tap("#toggle button"); pg.keyboard.press("Tab"); pg.keyboard.press("Tab")
        pg.wait_for_timeout(200)
        print("  toggle", pg.evaluate("() => [...document.querySelectorAll('#toggle button')].map(b => b.getAttribute('aria-pressed') + ' ' + getComputedStyle(b).backgroundColor)"))
        pg.screenshot(path=str(HERE / f"t-{scheme}-figure.png"))
    b.close()
