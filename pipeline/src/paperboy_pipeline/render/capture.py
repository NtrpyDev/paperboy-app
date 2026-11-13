"""Loading an explainer in a headless browser in each theme, measuring it, and saving
the screenshots and the two plate stills (the hero stage at rest in the light and in the
dark color scheme). The four themes load in parallel, one browser context each."""
import asyncio
import io
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

VIEWPORT = {"width": 390, "height": 844}
SCALE = 2
PIECE_CSS_PX = 1200  # 2400 device pixels at SCALE 2
READY_TIMEOUT_MS = 20_000
SETTLE_MS = 1_500
HERO_MAX_WIDTH = 1200
HERO_QUALITY = 85
HERO_MIN_CSS_WIDTH = 300

# name, color scheme, reduced motion
THEMES = (
    ("light", "light", "no-preference"),
    ("dark", "dark", "no-preference"),
    ("still", "light", "reduce"),
    ("still-dark", "dark", "reduce"),
)
STRUCTURE_THEME = "light"  # rules about the document itself are reported once, from this theme
# The plate stills are the hero stage at rest (reduced motion), one per color scheme. The
# browser's emulated color scheme drives which form the page draws, whatever the kit version.
PLATE_THEMES = {"still": "day", "still-dark": "night"}
KIND_PLATE = "day"  # the hero's data-kind and data-scale are read in this plate's capture
HERO_KINDS = ("data", "illustration")

PROBE = resources.files(__package__).joinpath("probe.js").read_text()

SCROLL_THROUGH = """async () => {
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const pause = ms => new Promise(r => setTimeout(r, ms));
  const step = Math.max(200, Math.floor(innerHeight * 0.8));
  for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
    scrollTo(0, y);
    await frame();
    await pause(60);
  }
  scrollTo(0, document.documentElement.scrollHeight);
  await frame();
  await pause(60);
  scrollTo(0, 0);
  await frame();
}"""


@dataclass
class Problem:
    rule: str
    detail: str
    theme: str

    def as_dict(self):
        return {"rule": self.rule, "detail": self.detail, "theme": self.theme}


@dataclass
class Result:
    problems: list[Problem] = field(default_factory=list)
    shots: list[Path] = field(default_factory=list)
    plates: dict = field(default_factory=dict)  # "day" and "night": {"path", "width", "height"}
    hero_kind: str | None = None  # data-kind of the hero stage when it is data or illustration
    hero_to_scale: bool | None = None  # for an illustration: data-scale="true" on the hero stage
    page: dict = field(default_factory=dict)


async def _save_pieces(page, height: int, shots_dir: Path, theme: str) -> list[Path]:
    saved = []
    y, n = 0, 1
    while y < height:
        h = min(PIECE_CSS_PX, height - y)
        png = await page.screenshot(full_page=True, clip={"x": 0, "y": y, "width": VIEWPORT["width"], "height": h})
        path = shots_dir / f"{theme}-{n:02d}.png"
        path.write_bytes(png)
        saved.append(path)
        y += h
        n += 1
    return saved


def _is_flat(png: bytes) -> bool:
    image = Image.open(io.BytesIO(png)).convert("RGB")
    return all(lo == hi for lo, hi in image.getextrema())


async def _save_plate(page, plate_path: Path, theme: str, plate: str, result: Result):
    def fail(detail):
        result.problems.append(Problem("hero-not-capturable", detail, theme))

    stage = page.locator(".pb-hero .pb-stage").first
    if await stage.count() == 0:
        return fail("no .pb-stage inside .pb-hero")
    box = await stage.bounding_box()
    if not box or box["width"] < HERO_MIN_CSS_WIDTH or box["height"] < 1:
        width = round(box["width"]) if box else 0
        return fail(f"hero stage is {width} px wide, needs at least {HERO_MIN_CSS_WIDTH}")
    if await stage.evaluate("el => el.childElementCount === 0 && !el.textContent.trim()"):
        return fail("hero stage is empty")
    if plate == KIND_PLATE:
        kind = await stage.get_attribute("data-kind")
        if kind in HERO_KINDS:
            result.hero_kind = kind
            if kind == "illustration":
                result.hero_to_scale = await stage.get_attribute("data-scale") == "true"
    await stage.scroll_into_view_if_needed()
    png = await stage.screenshot()
    if _is_flat(png):
        return fail("hero stage screenshot is a single flat color")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    if image.width > HERO_MAX_WIDTH:
        image = image.resize((HERO_MAX_WIDTH, round(image.height * HERO_MAX_WIDTH / image.width)), Image.LANCZOS)
    image.save(plate_path, "WEBP", quality=HERO_QUALITY)
    result.plates[plate] = {"path": plate_path, "width": image.width, "height": image.height}


async def _one_theme(browser, url: str, theme: str, scheme: str, motion: str, shots_dir: Path, plate_paths: dict, result: Result):
    origin = urlsplit(url).netloc
    problems = []

    def add(rule, detail):
        problems.append(Problem(rule, detail, theme))

    external = []

    async def only_this_host(route):
        parts = urlsplit(route.request.url)
        if parts.scheme in ("http", "https") and parts.netloc == origin:
            await route.continue_()
        else:
            if route.request.url not in external:
                external.append(route.request.url)
            await route.abort("blockedbyclient")

    context = await browser.new_context(viewport=VIEWPORT, device_scale_factor=SCALE, color_scheme=scheme, reduced_motion=motion)
    await context.route("**/*", only_this_host)
    try:
        page = await context.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(error.message or str(error)))
        page.on("websocket", lambda ws: external.append(ws.url))
        await page.goto(url, wait_until="load")
        try:
            await page.wait_for_selector('html[data-pb-ready="1"]', state="attached", timeout=READY_TIMEOUT_MS)
        except PlaywrightTimeout:
            add("not-ready", f'html[data-pb-ready="1"] did not appear within {READY_TIMEOUT_MS // 1000} s')
        await page.evaluate(SCROLL_THROUGH)
        await page.wait_for_timeout(SETTLE_MS)
        probe = await page.evaluate(PROBE)

        kit_errors = probe["errors"] or []
        errors = kit_errors + [m for m in page_errors if not any(m in k for k in kit_errors)]
        for message in errors:
            add("script-error", message.strip().splitlines()[0][:300] if message.strip() else "(empty error)")
        for request_url in external:
            add("external-request", f"request to another host was blocked: {request_url[:300]}")
        for rule, detail in probe["layout"]:
            add(rule, detail)
        if theme == STRUCTURE_THEME:
            for rule, detail in probe["structure"]:
                add(rule, detail)
            result.page = {
                "height_px": probe["height"],
                "figures": probe["figures"],
                "data_figures": probe["dataFigures"],
                "kit": probe["kit"],  # the one kit version the page loads, or None
                "depth": probe["depth"],  # "full" or "abstract" (article.pb data-depth), or None when unknown
            }
        result.shots += await _save_pieces(page, probe["height"], shots_dir, theme)
        if theme in PLATE_THEMES:
            plate = PLATE_THEMES[theme]
            await _save_plate(page, plate_paths[plate], theme, plate, result)
    finally:
        await context.close()
    result.problems += problems


async def _render(url: str, browser_path: str, shots_dir: Path, plate_paths: dict) -> Result:
    result = Result()
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=browser_path, headless=True, args=["--no-sandbox"])
        try:
            await asyncio.gather(*(
                _one_theme(browser, url, theme, scheme, motion, shots_dir, plate_paths, result)
                for theme, scheme, motion in THEMES
            ))
        finally:
            await browser.close()
    order = {name: i for i, (name, _, _) in enumerate(THEMES)}
    result.shots.sort(key=lambda s: (order[s.stem.rsplit("-", 1)[0]], s.name))
    result.problems.sort(key=lambda p: order[p.theme])
    return result


def render(url: str, browser_path: str, shots_dir: Path, plate_paths: dict) -> Result:
    """Load `url` in each theme and save the plate stills to plate_paths ({"day": path, "night": path}).
    Raises playwright's Error if the browser cannot start."""
    shots_dir.mkdir(parents=True, exist_ok=True)
    for old in shots_dir.glob("*.png"):
        old.unlink()
    return asyncio.run(_render(url, browser_path, shots_dir, plate_paths))
