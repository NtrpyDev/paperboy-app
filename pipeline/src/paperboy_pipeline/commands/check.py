"""check: the render check. Loads one explainer in a headless browser at phone size in
light, dark, and reduced motion in light and in dark, writes check.json and screenshots,
and saves the two plate stills, the hero stage at rest: explainer/hero.webp (day, light
color scheme) and explainer/hero-night.webp (night, dark color scheme). Exit 0 on pass,
1 on fail, 2 on a tool error."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import Error as PlaywrightError

from ..render import browser, capture, server

PASS, FAIL, TOOL_ERROR = 0, 1, 2
PLATE_FILES = {"day": "hero.webp", "night": "hero-night.webp"}
KIT_VERSION = re.compile(r"v[1-9][0-9]*")


def register(subparsers):
    parser = subparsers.add_parser("check", help="render check one explainer", description=__doc__)
    parser.add_argument("--explainer", required=True, type=Path, help="folder holding index.html")
    parser.add_argument("--kit", required=True, type=Path, help="the repo's kit folder (holds v1/, v2/, ...)")
    parser.add_argument("--out", type=Path, help="where check.json and shots/ go (default: the explainer's parent)")
    parser.set_defaults(run=run)


def _tool_error(message: str) -> int:
    print(f"check: {message}", file=sys.stderr)
    return TOOL_ERROR


def run(args) -> int:
    explainer = args.explainer.resolve()
    kit = args.kit.resolve()
    out = (args.out or explainer.parent).resolve()
    if not (explainer / "index.html").is_file():
        return _tool_error(f"no index.html in {explainer}")
    if not any(p.is_dir() and KIT_VERSION.fullmatch(p.name) for p in kit.glob("v*")):
        return _tool_error(f"no version folder (v1, v2, ...) in kit {kit}")
    executable = browser.find_browser()
    if executable is None:
        return _tool_error(f"no browser found: set {browser.ENV} or put one of {', '.join(browser.NAMES)} on PATH")
    out.mkdir(parents=True, exist_ok=True)
    plate_paths = {plate: explainer / name for plate, name in PLATE_FILES.items()}
    for path in plate_paths.values():
        if path.exists():
            path.unlink()

    try:
        with server.serve(explainer, kit) as url:
            result = capture.render(url, executable, out / "shots", plate_paths)
    except PlaywrightError as e:
        return _tool_error(f"browser failed ({executable}): {e}")

    def rel(path: Path) -> str:
        return Path(os.path.relpath(path, out)).as_posix()

    def plate(name: str) -> dict:
        p = result.plates[name]
        return {"path": rel(p["path"]), "width": p["width"], "height": p["height"]}

    hero = None
    if "day" in result.plates and "night" in result.plates:
        hero = {**plate("day"), "night": plate("night")}
        if result.hero_kind is not None:
            hero["kind"] = result.hero_kind
        if result.hero_to_scale is not None:
            hero["to_scale"] = result.hero_to_scale
    report = {
        "pass": not result.problems,
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "problems": [p.as_dict() for p in result.problems],
        "shots": [rel(s) for s in result.shots],
        "hero": hero,
        "page": result.page,
    }
    (out / "check.json").write_text(json.dumps(report, indent=2) + "\n")
    for p in result.problems:
        print(f"{p.rule} ({p.theme}): {p.detail}", file=sys.stderr)
    return PASS if report["pass"] else FAIL
