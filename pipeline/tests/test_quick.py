"""The quick explainer's starter and manual: the starter passes the render check as a page built
from the abstract, and every ```js example in QUICK.md runs as written. Both drive a real headless
browser and are skipped when none is found."""
import json
import re
from pathlib import Path

import pytest

from paperboy_pipeline.cli import main
from paperboy_pipeline.render.browser import find_browser

PIPELINE = Path(__file__).resolve().parents[1]
KIT = PIPELINE.parent / "kit"
STARTER = (PIPELINE / "quick-starter.html").read_text()
MANUAL = (PIPELINE / "QUICK.md").read_text()

pytestmark = pytest.mark.skipif(find_browser() is None, reason="no Chromium-family browser found")


def check(tmp_path: Path, html: str):
    explainer = tmp_path / "explainer"
    explainer.mkdir()
    (explainer / "index.html").write_text(html)
    code = main(["check", "--explainer", str(explainer), "--kit", str(KIT)])
    return code, json.loads((tmp_path / "check.json").read_text())


def test_the_starter_passes_as_a_page_built_from_the_abstract(tmp_path):
    code, report = check(tmp_path, STARTER)
    assert report["problems"] == []
    assert code == 0
    assert report["page"]["depth"] == "abstract"
    assert report["page"]["kit"] == 2


def test_the_starter_fails_without_its_note_to_the_reader(tmp_path):
    note = "Built from the paper's abstract, not its full text. "
    assert STARTER.count(note) == 1
    code, report = check(tmp_path, STARTER.replace(note, ""))
    assert {p["rule"] for p in report["problems"]} == {"missing-depth-note"}
    assert code == 1


def examples_page() -> tuple[str, int]:
    """A page that runs each ```js block of QUICK.md as written, inside its own PB.ready with the
    starter's helpers. Each block's element ids are renamed so blocks do not collide; the first
    block keeps #hero as the hero stage, later plates draw into a .pb-bleed."""
    blocks = re.findall(r"```js\n(.*?)```", MANUAL, re.S)
    helpers = re.search(r"(  /\* A mark label.*?\n  }\n\n  /\* Engrave a field.*?\n  }\n)", STARTER, re.S).group(1)
    figures, scripts = [], []
    for i, block in enumerate(blocks):
        code, holders = block, []
        for name in sorted(set(re.findall(r'"#([a-z0-9-]+)"', block))):
            new = name if (name == "hero" and i == 0) else f"b{i}-{name}"
            code = code.replace(f'"#{name}"', f'"#{new}"')
            if new != "hero":
                holders.append(f'<div class="pb-bleed" id="{new}"></div>' if name == "hero" else f'<div id="{new}"></div>')
        figures.append(f'<figure class="pb-fig" data-kind="illustration" data-slug="Example {i + 1}">{"".join(holders)}</figure>')
        scripts.append(f"<script>\nPB.ready(function () {{\n{helpers}\n{code}}});\n</script>")
    head = STARTER.split("<body>")[0]
    body = f"""<body>
<article class="pb">
<header class="pb-hero"><h1 class="pb-title">QUICK.md examples</h1><div class="pb-stage" id="hero" data-kind="illustration"></div><p class="pb-dek">Each example as written.</p></header>
{"".join(figures)}
<section class="pb-section" data-section="question"><h2>Question</h2></section>
<section class="pb-section" data-section="method"><h2>Method</h2></section>
<section class="pb-section" data-section="findings"><h2>Findings</h2></section>
<section class="pb-section" data-section="confidence"><h2>Confidence</h2></section>
<section class="pb-section" data-section="matters"><h2>Matters</h2></section>
<footer class="pb-source"><a class="pb-btn" href="https://example.org/">Read the paper</a><p>Written by a machine.</p></footer>
</article>
{"".join(scripts)}
</body>
</html>
"""
    return head + body, len(blocks)


def test_every_example_in_the_manual_runs(tmp_path):
    html, count = examples_page()
    assert count >= 8
    code, report = check(tmp_path, html)
    assert report["problems"] == []
    assert code == 0
