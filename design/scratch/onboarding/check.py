"""Checks and crops for the onboarding boards.

  uv run --quiet --with playwright --with pillow python design/scratch/onboarding/check.py [options] [BOARD ...]

  BOARD            board names without .dc.html (default: the three Onboarding boards)
  --audit          run the two existing audits on each board: the AUDIT script of
                   scratch/states/check.py (targets under 44 px, contrast, text sizes, shadows,
                   radii) and the JS of scratch/final/audit.py (root size, overflow, targets,
                   text sizes, contrast). Neither file is changed: their scripts are read and run.
  --measure        print the box of every [data-m] element, relative to its screen
  --reduced        render with prefers-reduced-motion and count running animations
  --crops          crop each screen at 2x into design/shots/onboarding/<board>/NN.png and a tile
  --t 2            seconds after load at which crops are taken

Nothing here writes outside design/shots/onboarding.
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
DESIGN = HERE.parents[1]
sys.path.insert(0, str(DESIGN / "tools"))
sys.path.insert(0, str(HERE.parent / "states"))
import dc_shot  # noqa: E402
from check import AUDIT, MEASURE  # noqa: E402  (scratch/states/check.py)
from playwright.sync_api import sync_playwright  # noqa: E402

FINAL_JS = re.search(r'JS = r"""(.*?)"""', (HERE.parent / "final" / "audit.py").read_text(), re.S).group(1)
ALL = ["Onboarding-B-Day", "Onboarding-B-Night", "Onboarding-Reentry-Day"]


def run(name, a):
    src = (DESIGN / "canvas" / "project" / f"{name}.dc.html").resolve()
    raw = src.read_text()
    pv = re.search(r'"\$preview":\{"width":(\d+),"height":(\d+)\}', raw)
    w, h = int(pv.group(1)), int(pv.group(2))
    out = DESIGN / "shots" / "onboarding" / name
    tmp = src.with_name("." + src.name + ".obcheck.html")
    tmp.write_text(dc_shot.to_plain_html(raw))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=dc_shot.browser_path(), headless=True, args=["--no-sandbox"])
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2,
                                color_scheme="dark" if name.endswith("Night") else "light",
                                reduced_motion="reduce" if a.reduced else "no-preference")
            pg = ctx.new_page()
            errors = []
            pg.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(tmp.as_uri())
            pg.evaluate("() => document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(int(a.t * 1000))
            print(f"== {name} ({w} by {h})")
            if a.reduced:
                print("   running animations with reduced motion:", pg.evaluate("() => document.getAnimations().filter(x => x.playState === 'running').length"))
            if a.measure:
                for s in pg.evaluate(MEASURE):
                    print("   screen", s["screen"])
                    for mk in s["marks"]:
                        print(f'      {mk["m"]:<12} top {mk["top"]:>8}  bottom {mk["bottom"]:>8}  left {mk["left"]:>7}  w {mk["w"]:>7}  h {mk["h"]:>7}')
            if a.audit:
                r = pg.evaluate(AUDIT)
                print("   [states/check.py AUDIT] root", r["root"], "scroll", r["sw"], r["sh"], "screens", sorted(set(r["screens"])), "targets", r["targets"])
                print("      small targets:", r["small"] or "none")
                print("      low contrast:", r["low"] or "none")
                print("      mono min px:", r["monoMin"], " other text min px:", r["sentenceMin"], " svg text min:", r["svgTextMin"])
                print("      sizes:", dict(sorted(r["sizes"].items())))
                print("      elements with a shadow:", r["shadow"], " with a corner radius that is not a circle:", r["radius"])
                f = pg.evaluate(FINAL_JS)
                small = [e for e in f["els"] if e["h"] < 44 or e["w"] < 44]
                print(f"   [final/audit.py JS] root {f['root']} scroll {f['sw']}x{f['sh']} overflow_x {f['sw'] > f['cw']} past-right {f['over']}")
                print(f"      targets {len(f['els'])}, under 44: {small}")
                print("      low contrast", f["low"])
                print("      console:", errors or "none")
            if a.crops:
                from PIL import Image
                out.mkdir(parents=True, exist_ok=True)
                sfx = "-reduced" if a.reduced else ""
                shots = []
                for n in pg.evaluate("() => [...document.querySelectorAll('[data-screen]')].map(s => s.dataset.screen)"):
                    path = out / f"{n}{sfx}.png"
                    box = pg.locator(f'[data-screen="{n}"]').bounding_box()
                    pg.screenshot(path=str(path), full_page=True, clip={"x": box["x"] - 1, "y": box["y"] - 36, "width": box["width"] + 2, "height": box["height"] + 37})
                    shots.append(path)
                ims = [Image.open(s) for s in shots]
                gap = 24
                tile = Image.new("RGB", (sum(im.width for im in ims) + gap * (len(ims) - 1), max(im.height for im in ims)), (128, 128, 128))
                x = 0
                for im in ims:
                    tile.paste(im, (x, 0))
                    x += im.width + gap
                tile.save(out / f"tile{sfx}.png")
                print("   crops", [str(s) for s in shots], str(out / f"tile{sfx}.png"), tile.size)
            b.close()
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("boards", nargs="*")
    ap.add_argument("--t", type=float, default=2.0)
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--crops", action="store_true")
    a = ap.parse_args()
    for name in (a.boards or ALL):
        run(name, a)
