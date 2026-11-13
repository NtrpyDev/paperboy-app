"""The render check at the command seam: an explainer folder in, exit code and check.json out.

These tests drive a real headless browser. They are skipped when none is found
(set PAPERBOY_CHROME or put google-chrome, chromium, chromium-browser, or brave on PATH).
"""
import json
import shutil
from pathlib import Path

import pytest

from paperboy_pipeline.cli import main
from paperboy_pipeline.render.browser import find_browser

FIXTURES = Path(__file__).parent / "fixtures" / "check"
REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

pytestmark = pytest.mark.skipif(
    find_browser() is None,
    reason="no Chromium-family browser found: set PAPERBOY_CHROME or install google-chrome, chromium, or brave",
)


def run_check(tmp_path: Path, page: Path):
    explainer = tmp_path / "explainer"
    explainer.mkdir()
    shutil.copy(page, explainer / "index.html")
    code = main(["check", "--explainer", str(explainer), "--kit", str(KIT)])
    report = json.loads((tmp_path / "check.json").read_text())
    return code, report


def test_kit_gallery_passes(tmp_path):
    code, report = run_check(tmp_path, KIT / "v1" / "gallery.html")
    assert report["problems"] == []
    assert code == 0
    assert report["page"]["data_figures"] == 2
    assert (tmp_path / "explainer" / "hero.webp").is_file()


def test_missing_index_is_a_tool_error(tmp_path):
    (tmp_path / "explainer").mkdir()
    assert main(["check", "--explainer", str(tmp_path / "explainer"), "--kit", str(KIT)]) == 2
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
    for theme in ("light", "dark", "still"):
        assert (tmp_path / "shots" / f"{theme}-01.png").is_file()
    assert set(report["shots"]) == {str(p.relative_to(tmp_path)) for p in (tmp_path / "shots").iterdir()}
    hero = tmp_path / "explainer" / "hero.webp"
    assert hero.is_file()
    assert report["hero"]["path"] == "explainer/hero.webp"
    assert 300 <= report["hero"]["width"] <= 1200
    assert report["page"]["figures"] == 3
    assert report["page"]["data_figures"] == 1
    assert report["page"]["height_px"] > 844
