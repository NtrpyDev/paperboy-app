"""The render check at the command seam: an explainer folder in, exit code and check.json out.

These tests drive a real headless browser. They are skipped when none is found
(set PAPERBOY_CHROME or put google-chrome, chromium, chromium-browser, or brave on PATH).
"""
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from paperboy_pipeline.cli import main
from paperboy_pipeline.render.browser import find_browser

FIXTURES = Path(__file__).parent / "fixtures" / "check"
REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

pytestmark = pytest.mark.skipif(
    find_browser() is None,
    reason="no Chromium-family browser found: set PAPERBOY_CHROME or install google-chrome, chromium, or brave",
)


def run_check(tmp_path: Path, page: Path | str, kit: Path = KIT):
    """page is a file to copy or the page's HTML."""
    explainer = tmp_path / "explainer"
    explainer.mkdir()
    if isinstance(page, Path):
        shutil.copy(page, explainer / "index.html")
    else:
        (explainer / "index.html").write_text(page)
    code = main(["check", "--explainer", str(explainer), "--kit", str(kit)])
    report = json.loads((tmp_path / "check.json").read_text())
    return code, report


PASS_PAGE = (FIXTURES / "pass" / "index.html").read_text()
HERO_STAGE = '<div class="pb-stage" id="hero" data-kind="data"></div>'


def pass_page_with(stage: str = HERO_STAGE, head: str = "") -> str:
    """The passing fixture with its hero stage replaced and extra markup at the end of <head>."""
    assert PASS_PAGE.count(HERO_STAGE) == 1 and PASS_PAGE.count("</head>") == 1
    return PASS_PAGE.replace(HERO_STAGE, stage).replace("</head>", head + "</head>")


def test_kit_v1_gallery_passes_once_its_hero_stage_has_a_kind(tmp_path):
    # The v1 gallery predates the hero-without-kind rule and kit v1 is never edited.
    gallery = (KIT / "v1" / "gallery.html").read_text()
    stage = '<div class="pb-stage" id="hero">'
    assert gallery.count(stage) == 1
    code, report = run_check(tmp_path, gallery.replace(stage, '<div class="pb-stage" id="hero" data-kind="illustration">'))
    assert report["problems"] == []
    assert code == 0
    assert report["page"]["data_figures"] == 2
    assert (tmp_path / "explainer" / "hero.webp").is_file()
    assert (tmp_path / "explainer" / "hero-night.webp").is_file()


def test_missing_index_is_a_tool_error(tmp_path):
    (tmp_path / "explainer").mkdir()
    assert main(["check", "--explainer", str(tmp_path / "explainer"), "--kit", str(KIT)]) == 2
    assert not (tmp_path / "check.json").exists()


def test_unusable_browser_from_environment_is_a_tool_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERBOY_CHROME", str(tmp_path / "no-such-browser"))
    explainer = tmp_path / "explainer"
    explainer.mkdir()
    shutil.copy(FIXTURES / "pass" / "index.html", explainer / "index.html")
    assert main(["check", "--explainer", str(explainer), "--kit", str(KIT)]) == 2
    assert not (tmp_path / "check.json").exists()


RULE_FIXTURES = sorted(d.name for d in FIXTURES.iterdir() if d.is_dir() and d.name != "pass")


@pytest.mark.parametrize("rule", RULE_FIXTURES)
def test_page_breaking_one_rule_fails_with_that_rule_named(tmp_path, rule):
    code, report = run_check(tmp_path, FIXTURES / rule / "index.html")
    assert {p["rule"] for p in report["problems"]} == {rule}, report["problems"]
    assert report["pass"] is False
    assert code == 1


def test_passing_page_passes_and_writes_shots_and_hero(tmp_path):
    code, report = run_check(tmp_path, FIXTURES / "pass" / "index.html")
    assert report["problems"] == []
    assert report["pass"] is True
    assert code == 0
    for theme in ("light", "dark", "still", "still-dark"):
        assert (tmp_path / "shots" / f"{theme}-01.png").is_file()
    assert set(report["shots"]) == {str(p.relative_to(tmp_path)) for p in (tmp_path / "shots").iterdir()}
    for name in ("hero.webp", "hero-night.webp"):
        assert (tmp_path / "explainer" / name).is_file()
    hero = report["hero"]
    assert hero["path"] == "explainer/hero.webp"
    assert hero["night"]["path"] == "explainer/hero-night.webp"
    assert 300 <= hero["width"] <= 1200
    assert (hero["night"]["width"], hero["night"]["height"]) == (hero["width"], hero["height"])
    assert hero["kind"] == "data"
    assert "to_scale" not in hero
    assert report["page"]["figures"] == 3
    assert report["page"]["data_figures"] == 1
    assert report["page"]["height_px"] > 844
    assert report["page"]["kit"] == 1


def mean_brightness(path: Path) -> float:
    with Image.open(path) as image:
        return ImageStat.Stat(image.convert("L")).mean[0]


def test_plates_are_the_hero_at_rest_in_the_light_and_dark_color_schemes(tmp_path):
    # The stage is white at rest in light, black at rest in dark, and red whenever motion is allowed,
    # so the stills show which emulated color scheme and motion setting each was captured under.
    style = """<style>
#hero { background: #ff0000 !important; }
@media (prefers-reduced-motion: reduce) and (prefers-color-scheme: light) { #hero { background: #ffffff !important; } }
@media (prefers-reduced-motion: reduce) and (prefers-color-scheme: dark) { #hero { background: #000000 !important; } }
</style>"""
    code, report = run_check(tmp_path, pass_page_with(head=style))
    assert report["problems"] == []
    assert code == 0
    with Image.open(tmp_path / "explainer" / "hero.webp") as day, Image.open(tmp_path / "explainer" / "hero-night.webp") as night:
        day_corner = day.convert("RGB").getpixel((8, 8))
        night_corner = night.convert("RGB").getpixel((8, 8))
    assert min(day_corner) > 230, day_corner
    assert max(night_corner) < 25, night_corner
    assert mean_brightness(tmp_path / "explainer" / "hero.webp") > mean_brightness(tmp_path / "explainer" / "hero-night.webp")


@pytest.mark.parametrize(
    "attributes, kind, to_scale",
    [
        ('data-kind="illustration" data-scale="true"', "illustration", True),
        ('data-kind="illustration"', "illustration", False),
        ('data-kind="data" data-scale="true"', "data", None),
    ],
    ids=["illustration to scale", "illustration not to scale", "data ignores data-scale"],
)
def test_hero_kind_and_scale_are_read_from_the_stage(tmp_path, attributes, kind, to_scale):
    code, report = run_check(tmp_path, pass_page_with(stage=f'<div class="pb-stage" id="hero" {attributes}></div>'))
    assert code == 0, report["problems"]
    assert report["hero"]["kind"] == kind
    assert report["hero"].get("to_scale") == to_scale


def test_hero_stage_marked_as_a_paper_figure_has_no_valid_kind(tmp_path):
    code, report = run_check(tmp_path, pass_page_with(stage='<div class="pb-stage" id="hero" data-kind="paper"></div>'))
    assert {p["rule"] for p in report["problems"]} == {"hero-without-kind"}
    assert 'data-kind="paper"' in report["problems"][0]["detail"]
    assert "kind" not in report["hero"]
    assert code == 1


def test_any_single_kit_version_passes(tmp_path):
    kit = tmp_path / "kit"
    shutil.copytree(KIT / "v1", kit / "v7")
    page = PASS_PAGE.replace("/kit/v1/", "/kit/v7/")
    assert "/kit/v1/" not in page
    code, report = run_check(tmp_path, page, kit=kit)
    assert report["problems"] == []
    assert code == 0
    assert report["page"]["kit"] == 7


def test_kit_files_from_two_versions_fail(tmp_path):
    code, report = run_check(tmp_path, pass_page_with(head='<link rel="stylesheet" href="/kit/v2/paperboy.css">\n'))
    assert {p["rule"] for p in report["problems"]} == {"kit-not-absolute"}
    assert "one version" in report["problems"][0]["detail"]
    assert report["page"]["kit"] is None
    assert code == 1


def test_kit_folder_without_a_version_folder_is_a_tool_error(tmp_path):
    (tmp_path / "kit" / "fonts").mkdir(parents=True)
    explainer = tmp_path / "explainer"
    explainer.mkdir()
    shutil.copy(FIXTURES / "pass" / "index.html", explainer / "index.html")
    assert main(["check", "--explainer", str(explainer), "--kit", str(tmp_path / "kit")]) == 2
    assert not (tmp_path / "check.json").exists()
