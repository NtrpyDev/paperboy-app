"""Loading an explainer in a headless browser in each theme, measuring it, and saving
the screenshots and the hero still."""
import io
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 390, "height": 844}
SCALE = 2
PIECE_CSS_PX = 1200  # 2400 device pixels at SCALE 2
READY_TIMEOUT_MS = 20_000
SETTLE_MS = 1_500
HERO_MAX_WIDTH = 1200
HERO_QUALITY = 85
HERO_MIN_CSS_WIDTH = 300

# name, color scheme, reduced motion
THEMES = (("light", "light", "no-preference"), ("dark", "dark", "no-preference"), ("still", "light", "reduce"))

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
    hero: dict | None = None
    page: dict = field(default_factory=dict)


def _save_pieces(page, height: int, shots_dir: Path, theme: str) -> list[Path]:
    saved = []
    y, n = 0, 1
    while y < height:
        h = min(PIECE_CSS_PX, height - y)
        png = page.screenshot(full_page=True, clip={"x": 0, "y": y, "width": VIEWPORT["width"], "height": h})
        path = shots_dir / f"{theme}-{n:02d}.png"
        path.write_bytes(png)
        saved.append(path)
        y += h
        n += 1
    return saved


def _is_flat(png: bytes) -> bool:
    image = Image.open(io.BytesIO(png)).convert("RGB")
    return all(lo == hi for lo, hi in image.getextrema())


def _save_hero(page, hero_path: Path, theme: str, result: Result):
    stage = page.locator("article.pb .pb-hero .pb-stage").first
    if stage.count() == 0:
        result.problems.append(Problem("hero-not-capturable", "no .pb-stage inside .pb-hero", theme))
        return
    box = stage.bounding_box()
    if not box or box["width"] < HERO_MIN_CSS_WIDTH or box["height"] < 1:
        width = round(box["width"]) if box else 0
        result.problems.append(Problem("hero-not-capturable", f"hero stage is {width} px wide, needs at least {HERO_MIN_CSS_WIDTH}", theme))
        return
    if stage.evaluate("el => el.childElementCount === 0 && !el.textContent.trim()"):
        result.problems.append(Problem("hero-not-capturable", "hero stage is empty", theme))
        return
    stage.scroll_into_view_if_needed()
    png = stage.screenshot()
    if _is_flat(png):
        result.problems.append(Problem("hero-not-capturable", "hero stage screenshot is a single flat color", theme))
        return
    image = Image.open(io.BytesIO(png)).convert("RGB")
    if image.width > HERO_MAX_WIDTH:
        image = image.resize((HERO_MAX_WIDTH, round(image.height * HERO_MAX_WIDTH / image.width)), Image.LANCZOS)
    image.save(hero_path, "WEBP", quality=HERO_QUALITY)
    result.hero = {"path": hero_path, "width": image.width, "height": image.height}


def render(url: str, browser_path: str, shots_dir: Path, hero_path: Path) -> Result:
    """Load `url` in each theme. Raises PlaywrightError if the browser cannot start."""
    origin = urlsplit(url).netloc
    result = Result()
    shots_dir.mkdir(parents=True, exist_ok=True)
    for old in shots_dir.glob("*.png"):
        old.unlink()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=browser_path, headless=True, args=["--no-sandbox"])
        try:
            for theme, scheme, motion in THEMES:
                context = browser.new_context(
                    viewport=VIEWPORT, device_scale_factor=SCALE, color_scheme=scheme, reduced_motion=motion
                )
                try:
                    page = context.new_page()
                    page.goto(url, wait_until="load")
                    try:
                        page.wait_for_selector('html[data-pb-ready="1"]', state="attached", timeout=READY_TIMEOUT_MS)
                    except PlaywrightTimeout:
                        result.problems.append(Problem("not-ready", f'html[data-pb-ready="1"] did not appear within {READY_TIMEOUT_MS // 1000} s', theme))
                    page.evaluate(SCROLL_THROUGH)
                    page.wait_for_timeout(SETTLE_MS)
                    probe = page.evaluate(PROBE)
                    if theme == "light":
                        result.page = {"height_px": probe["height"], "figures": probe["figures"], "data_figures": probe["dataFigures"]}
                    result.shots += _save_pieces(page, probe["height"], shots_dir, theme)
                    if theme == "dark":
                        _save_hero(page, hero_path, theme, result)
                finally:
                    context.close()
        finally:
            browser.close()
    return result
