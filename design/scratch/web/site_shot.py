"""Screenshot the built website from a URL and check it.

  uv run --with playwright design/scratch/web/site_shot.py URL --out DIR \
      [--widths 1440,1024,700,390,360] [--frames 4] [--full] [--reduced] [--height 900]

Prints one JSON line per width: shots, page size, horizontal overflow, console errors,
requests to any host other than the page's, and links or buttons under 44 px tall.
"""
import argparse
import json
import pathlib
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from dc_shot import browser_path  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

TARGETS = """() => [...document.querySelectorAll('a[href],button,input')].map(el => {
  const r = el.getBoundingClientRect();
  return {text: (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 40),
          w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, href: el.getAttribute('href')};
})"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", required=True)
    ap.add_argument("--widths", default="1440,1024,700,390,360")
    ap.add_argument("--height", type=int, default=0, help="viewport height, default 900 (844 under 700 wide)")
    ap.add_argument("--frames", default="4")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--scroll", action="store_true", help="scroll through the page first, so every figure draws in")
    args = ap.parse_args()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    host = urlparse(args.url).netloc
    frames = [float(x) for x in args.frames.split(",") if x.strip()]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=browser_path(), headless=True, args=["--no-sandbox"])
        for w in [int(x) for x in args.widths.split(",")]:
            h = args.height or (844 if w < 700 else 900)
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=args.scale,
                                      reduced_motion="reduce" if args.reduced else "no-preference")
            page = ctx.new_page()
            res = {"width": w, "shots": [], "console": [], "requests": [], "foreign": []}
            page.on("console", lambda m: res["console"].append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda e: res["console"].append(f"pageerror: {e}"))
            page.on("requestfailed", lambda r: res["console"].append(f"failed: {r.url}"))

            def on_request(r):
                res["requests"].append(r.url.replace(args.url.rstrip("/"), ""))
                net = urlparse(r.url).netloc
                if r.url.startswith("http") and net != host:
                    res["foreign"].append(r.url)
            page.on("request", on_request)
            page.goto(args.url)
            if args.full:
                # Playwright's full-page capture resizes the viewport for a moment, which restarts
                # the hero plate's animations (its window for each width is display: none until its
                # breakpoint). So a full capture makes the viewport as tall as the page instead,
                # before anything animates, and every figure is in view from the start.
                page.evaluate("() => document.fonts.ready.then(() => true)")
                page.set_viewport_size({"width": w, "height": page.evaluate("() => document.documentElement.scrollHeight")})
            if args.scroll:
                page.evaluate("""async () => { for (let y = 0; y < document.documentElement.scrollHeight; y += 300) { scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); } scrollTo(0, 0); }""")
            elapsed = 0.0
            for t in sorted(frames):
                page.wait_for_timeout(max(0, int((t - elapsed) * 1000)))
                elapsed = t
                name = f"site{args.tag}-{w}w{'-reduced' if args.reduced else ''}-t{t:g}.png"
                page.screenshot(path=str(out / name))
                res["shots"].append(name)
            res["size"] = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, sh: document.documentElement.scrollHeight})")
            res["overflow_x"] = res["size"]["sw"] > res["size"]["cw"]
            res["fonts"] = sorted(set(page.evaluate("() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.style)")))
            res["running_animations"] = page.evaluate("() => document.getAnimations().filter(a => a.playState === 'running').length")
            res["under44"] = [t for t in page.evaluate(TARGETS) if t["h"] < 44 or t["w"] < 44]
            res["requests"] = sorted(set(res["requests"]))
            print(json.dumps(res))
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
