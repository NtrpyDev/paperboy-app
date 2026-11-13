"""Checks and crops for the two state boards.

  uv run --quiet --with playwright --with pillow python design/scratch/states/check.py [day|night|both] [options]

  --t 4            seconds after load at which the crops are taken
  --only 02,03     screens to crop (default: all)
  --tiles 4        screens per tile image (default 3). Tiles go to shots/states/<theme>/tile-*.png
  --measure        print the box of every [data-m] element, relative to its screen
  --audit          targets under 44 px, text sizes, contrast under 4.5:1 (3:1 at 24 px and up), overflow
  --reduced        render with prefers-reduced-motion and count running animations
  --boards DIR     read the boards from DIR instead of design/canvas/project
  --pause 2130     hold every animation at that many ms after load (for frames inside a short move)
  --tag NAME       suffix for the crop file names

Screens are cropped at 2x. Nothing here writes outside design/shots/states.
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DESIGN = HERE.parents[1]
sys.path.insert(0, str(DESIGN / "tools"))
import dc_shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

MEASURE = r"""() => [...document.querySelectorAll('[data-screen]')].map(s => {
  const o = s.getBoundingClientRect();
  return {screen: s.dataset.screen, marks: [...s.querySelectorAll('[data-m], button[aria-pressed], article > a, article > div > a[href="#explainer"], article > div > a[href="#paper"]')].map(e => { const r = e.getBoundingClientRect();
    return {m: e.dataset.m || (e.tagName === 'A' ? 'card-button' : 'rate-button'), top: +(r.top - o.top).toFixed(2), bottom: +(r.bottom - o.top).toFixed(2), left: +(r.left - o.left).toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2)} })};
})"""

AUDIT = r"""() => {
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]) };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > 0.99) return c } return [255, 255, 255, 1] };
  const out = {small: [], sizes: {}, low: {}, monoMin: 99, sentenceMin: 99, radius: 0, shadow: 0, targets: 0};
  for (const s of document.querySelectorAll('[data-screen]')) {
    const o = s.getBoundingClientRect();
    for (const el of s.querySelectorAll('a[href],button,input')) {
      const r = el.getBoundingClientRect(); if (r.width === 0) continue; out.targets++;
      if (r.width < 43.99 || r.height < 43.99) out.small.push(s.dataset.screen + ' ' + el.tagName + ' "' + (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 28) + '" ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
  }
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.boxShadow !== 'none') out.shadow++;
    if (parseFloat(cs.borderTopLeftRadius) > 0 && cs.borderTopLeftRadius !== '50%') out.radius++;
  }
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const pe = n.parentElement; if (pe.closest('svg') || pe.closest('script') || pe.closest('style')) continue;
    const r = pe.getBoundingClientRect(); if (r.width === 0) continue;
    const cs = getComputedStyle(pe); const fs = parseFloat(cs.fontSize); const fam = cs.fontFamily.split(',')[0].replace(/['"]/g, '');
    const k = fs + ' ' + fam; out.sizes[k] = (out.sizes[k] || 0) + 1;
    if (fam.includes('Mono')) out.monoMin = Math.min(out.monoMin, fs); else out.sentenceMin = Math.min(out.sentenceMin, fs);
    const fg = parse(cs.color), bg = bgOf(pe); if (!fg) continue;
    const a = lum(fg), b = lum(bg); const cr = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    if (cr < (fs >= 24 ? 3 : 4.5)) { const kk = cs.color + ' on ' + bg.slice(0, 3).join(',') + ' @' + fs + 'px = ' + cr.toFixed(2); out.low[kk] = n.textContent.trim().slice(0, 30) }
  }
  const svgText = [...document.querySelectorAll('svg text')].map(t => parseFloat(getComputedStyle(t).fontSize));
  out.svgTextMin = svgText.length ? Math.min(...svgText) : null;
  const root = document.body.firstElementChild.getBoundingClientRect();
  out.root = [root.width, root.height]; out.sw = document.documentElement.scrollWidth; out.sh = document.documentElement.scrollHeight;
  out.screens = [...document.querySelectorAll('[data-screen]')].map(s => { const r = s.firstElementChild.getBoundingClientRect(); return r.width + 'x' + r.height });
  return out;
}"""


def run(theme, a):
    from PIL import Image
    boards = pathlib.Path(a.boards) if a.boards else DESIGN / "canvas" / "project"
    src = (boards / f"App-States-{theme.capitalize()}.dc.html").resolve()
    out = DESIGN / "shots" / "states" / theme
    out.mkdir(parents=True, exist_ok=True)
    tmp = src.with_name("." + src.name + ".check.html")
    tmp.write_text(dc_shot.to_plain_html(src.read_text()))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
            ctx = b.new_context(viewport={"width": 1400, "height": 1100}, device_scale_factor=2,
                                reduced_motion="reduce" if a.reduced else "no-preference")
            pg = ctx.new_page()
            errors = []
            pg.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(tmp.as_uri())
            pg.evaluate("() => document.fonts.ready.then(() => true)")
            if a.pause is not None:
                pg.evaluate("ms => document.getAnimations().forEach(x => { x.pause(); x.currentTime = ms })", a.pause)
                pg.wait_for_timeout(120)
            else:
                pg.wait_for_timeout(int(a.t * 1000))
            if a.reduced:
                print(theme, "running animations with reduced motion:", pg.evaluate("() => document.getAnimations().filter(x => x.playState === 'running').length"))
            if a.measure:
                for s in pg.evaluate(MEASURE):
                    if a.only and s["screen"] not in a.only:
                        continue
                    print(theme, "screen", s["screen"])
                    for mk in s["marks"]:
                        print(f'   {mk["m"]:<14} top {mk["top"]:>8}  bottom {mk["bottom"]:>8}  left {mk["left"]:>7}  w {mk["w"]:>7}  h {mk["h"]:>7}')
            if a.audit:
                r = pg.evaluate(AUDIT)
                print(theme, "root", r["root"], "scroll", r["sw"], r["sh"], "screens", sorted(set(r["screens"])), "targets", r["targets"])
                print("   small targets:", r["small"] or "none")
                print("   low contrast:", r["low"] or "none")
                print("   mono min px:", r["monoMin"], " other text min px:", r["sentenceMin"], " svg text min:", r["svgTextMin"])
                print("   sizes:", dict(sorted(r["sizes"].items())))
                print("   elements with a shadow:", r["shadow"], " with a corner radius that is not a circle:", r["radius"])
                print("   console:", errors or "none")
            names = pg.evaluate("() => [...document.querySelectorAll('[data-screen]')].map(s => s.dataset.screen)")
            want = [n for n in names if not a.only or n in a.only]
            sfx = "-reduced" if a.reduced else ("" if a.tag == "" else "-" + a.tag)
            shots = []
            for n in want:
                path = out / f"{n}{sfx}.png"
                el = pg.locator(f'[data-screen="{n}"]')
                box = el.bounding_box()
                pg.screenshot(path=str(path), full_page=True, clip={"x": box["x"] - 1, "y": box["y"] - 59, "width": box["width"] + 2, "height": box["height"] + 60})
                shots.append(path)
            b.close()
        if a.tiles:
            for i in range(0, len(shots), a.tiles):
                ims = [Image.open(s) for s in shots[i:i + a.tiles]]
                gap = 24
                wd = sum(im.width for im in ims) + gap * (len(ims) - 1)
                tile = Image.new("RGB", (wd, max(im.height for im in ims)), (128, 128, 128))
                x = 0
                for im in ims:
                    tile.paste(im, (x, 0))
                    x += im.width + gap
                name = out / f"tile-{want[i]}-{want[min(i + a.tiles, len(want)) - 1]}{sfx}.png"
                tile.save(name)
                print("tile", name, tile.size)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("theme", nargs="?", default="both")
    ap.add_argument("--t", type=float, default=4.0)
    ap.add_argument("--only", default="")
    ap.add_argument("--tiles", type=int, default=3)
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--pause", type=float, default=None, help="hold every animation at this many ms after load, then crop")
    ap.add_argument("--boards", default="")
    a = ap.parse_args()
    a.only = [x.strip() for x in a.only.split(",") if x.strip()]
    for th in (["day", "night"] if a.theme == "both" else [a.theme]):
        run(th, a)
