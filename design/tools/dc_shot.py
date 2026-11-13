#!/usr/bin/env python3
"""Render a Claude Design artboard file (.dc.html) to PNG screenshots, locally.

The canvas runtime is not available offline, so this builds a plain HTML page from
the artboard: the <helmet> contents go in <head>, the rest of <x-dc> becomes <body>.
That is faithful for artboards written as literal markup (no {{holes}}, sc-for, sc-if).

  uv run --with playwright design/tools/dc_shot.py FILE.dc.html --out DIR \
      [--width 390] [--height 844] [--full] [--frames 0.2,1.2,3] [--scheme light|dark]

Prints one JSON line: screenshot paths, page size, horizontal overflow, console errors.
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import sys

from playwright.sync_api import sync_playwright


def browser_path() -> str:
    for candidate in (os.environ.get("PAPERBOY_CHROME"), "google-chrome", "chromium", "brave"):
        if candidate and (os.path.isabs(candidate) and os.path.exists(candidate) or shutil.which(candidate)):
            return candidate if os.path.isabs(candidate) else shutil.which(candidate)
    sys.exit("no Chromium-family browser found; set PAPERBOY_CHROME")


def to_plain_html(source: str) -> str:
    m = re.search(r"<x-dc>(.*)</x-dc>", source, re.S)
    if not m:
        sys.exit("no <x-dc> block in file")
    inner = m.group(1)
    helmet = ""
    hm = re.search(r"<helmet>(.*?)</helmet>", inner, re.S)
    if hm:
        helmet = hm.group(1)
        inner = inner.replace(hm.group(0), "")
    title = re.search(r"<title>(.*?)</title>", source, re.S)
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title.group(1) if title else 'artboard'}</title>{helmet}</head><body>{inner}</body></html>"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=390)
    ap.add_argument("--height", type=int, default=844)
    ap.add_argument("--full", action="store_true", help="capture the full scroll height")
    ap.add_argument("--frames", default="1.0", help="comma separated seconds after load to capture")
    ap.add_argument("--scheme", default="light", choices=["light", "dark"])
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    src = pathlib.Path(args.file).resolve()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plain = src.with_name("." + src.name + ".preview.html")
    plain.write_text(to_plain_html(src.read_text()))
    stem = src.name.replace(".dc.html", "")
    frames = [float(x) for x in args.frames.split(",") if x.strip()]
    result = {"file": str(src), "shots": [], "console": []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=browser_path(), headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(
                viewport={"width": args.width, "height": args.height},
                device_scale_factor=args.scale,
                color_scheme=args.scheme,
            )
            page = ctx.new_page()
            page.on("console", lambda m: result["console"].append(f"{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: result["console"].append(f"pageerror: {e}"))
            page.goto(plain.as_uri())
            page.evaluate("() => document.fonts.ready.then(() => true)")
            elapsed = 0.0
            for t in sorted(frames):
                page.wait_for_timeout(max(0, int((t - elapsed) * 1000)))
                elapsed = t
                name = f"{stem}-{args.width}w-{args.scheme}-t{t:g}.png"
                page.screenshot(path=str(out / name), full_page=args.full)
                result["shots"].append(str(out / name))
            result["size"] = page.evaluate(
                "() => ({scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth, scrollHeight: document.documentElement.scrollHeight})"
            )
            result["overflow_x"] = result["size"]["scrollWidth"] > result["size"]["clientWidth"]
            result["fonts"] = page.evaluate("() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight)")
            browser.close()
    finally:
        plain.unlink(missing_ok=True)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
