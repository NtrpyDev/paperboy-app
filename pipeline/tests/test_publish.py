"""The publish command, tested at the command line: a work folder in, a content repo tree out."""
import copy
import json
import re
import subprocess
from pathlib import Path

import pytest

from paperboy_pipeline import ids, schemas
from paperboy_pipeline.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "publish"
BASE = json.loads((FIXTURES / "judged-base.json").read_text())
NOW = "2026-11-12T08:00:00Z"


def judged(n: int, **overrides) -> dict:
    """A valid Judged record numbered n, so each one is a distinct paper."""
    record = copy.deepcopy(BASE)
    arxiv = f"2611.{n:05d}"
    record.update(
        id=f"arxiv-{arxiv}",
        arxiv_id=arxiv,
        title=f"Observation number {n} of a thing in a place",
        url=f"https://arxiv.org/abs/{arxiv}",
    )
    record.update(overrides)
    return record


def write_work(work: Path, records: list[dict], explained: dict[str, dict] | None = None) -> Path:
    """explained maps paper id to {"check": bool, "review": bool, "files": bool, "night": bool, "hero": dict,
    "kit": int | None, "card": dict}. The booleans default to True; "hero" (the hero check.json reports)
    defaults to none; "kit" (check.json's page.kit) defaults to 1, and None leaves page out; "card" is
    written as card.json when given."""
    work.mkdir(parents=True, exist_ok=True)
    (work / "judged.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    for paper_id, opts in (explained or {}).items():
        folder = work / "papers" / paper_id
        (folder / "explainer").mkdir(parents=True, exist_ok=True)
        if opts.get("files", True):
            (folder / "explainer" / "index.html").write_bytes((FIXTURES / "explainer.html").read_bytes())
            (folder / "explainer" / "hero.webp").write_bytes((FIXTURES / "hero.webp").read_bytes())
            if opts.get("night", True):
                (folder / "explainer" / "hero-night.webp").write_bytes((FIXTURES / "hero-night.webp").read_bytes())
        check = {"pass": opts.get("check", True), "problems": []}
        if "hero" in opts:
            check["hero"] = opts["hero"]
        if opts.get("kit", 1) is not None:
            check["page"] = {"height_px": 2000, "figures": 3, "data_figures": 1, "kit": opts.get("kit", 1)}
        (folder / "check.json").write_text(json.dumps(check))
        if "card" in opts:
            (folder / "card.json").write_text(json.dumps(opts["card"]))
        (folder / "review.json").write_text(json.dumps({"pass": opts.get("review", True), "problems": []}))
    return work


def publish(work: Path, content: Path, *extra: str, now: str = NOW) -> int:
    content.mkdir(parents=True, exist_ok=True)
    return main(["publish", "--work", str(work), "--content", str(content), "--now", now, *extra])


def read_json(path: Path):
    return json.loads(path.read_text())


def test_first_publish_into_empty_repo_writes_a_short_card(tmp_path):
    work = write_work(tmp_path / "work", [judged(1)])
    content = tmp_path / "content"

    assert publish(work, content) == 0

    chunk = read_json(content / "feed/v1/chunks/000001.json")
    assert chunk["v"] == 1
    assert chunk["number"] == 1
    assert chunk["items"] == [
        {
            "id": "arxiv-2611.00001",
            "title": "Observation number 1 of a thing in a place",
            "hook": "A thing turned up exactly where nobody looked",
            "summary": BASE["summary"],
            "field": "space",
            "tags": ["galaxies", "surveys"],
            "status": "preprint",
            "venue": "arXiv",
            "published": "2026-11-10",
            "authors_short": "Lovelace et al.",
            "url": "https://arxiv.org/abs/2611.00001",
            "has_explainer": False,
            "significance": 7.5,
            "added_at": NOW,
        }
    ]
    assert read_json(content / "feed/v1/head.json") == {
        "v": 1,
        "updated_at": NOW,
        "chunk_count": 1,
        "total_items": 1,
        "chunk_size": 40,
        "kit": 1,
        "min_app": 1,
    }
    paper = content / "papers/arxiv-2611.00001"
    assert sorted(p.name for p in paper.iterdir()) == ["meta.json"]
    meta = read_json(paper / "meta.json")
    assert meta["has_explainer"] is False
    assert meta["authors"] == ["Ada Lovelace", "Charles Babbage", "Mary Somerville"]
    assert meta["license"] == "cc-by"
    assert "abstract" not in meta


def test_paper_with_a_passing_explainer_is_published_as_an_explained_card(tmp_path):
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": {}})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["has_explainer"] is True
    assert item["explainer"] == "papers/arxiv-2611.00001/"
    assert item["hero"] == {
        "path": "papers/arxiv-2611.00001/hero.webp",
        "width": 120,
        "height": 63,
        "night": {"path": "papers/arxiv-2611.00001/hero-night.webp", "width": 120, "height": 63},
    }
    paper = content / "papers/arxiv-2611.00001"
    assert sorted(p.name for p in paper.iterdir()) == ["hero-night.webp", "hero.webp", "index.html", "meta.json"]
    assert (paper / "index.html").read_bytes() == (FIXTURES / "explainer.html").read_bytes()
    assert (paper / "hero.webp").read_bytes() == (FIXTURES / "hero.webp").read_bytes()
    assert (paper / "hero-night.webp").read_bytes() == (FIXTURES / "hero-night.webp").read_bytes()
    meta = read_json(paper / "meta.json")
    assert meta["has_explainer"] is True
    assert meta["explained_at"] == NOW
    assert meta["kit"] == 1
    assert meta["check"]["render"]["pass"] is True
    assert meta["check"]["review"]["pass"] is True


MADE_BY = {"expert": "claude-opus-5-5", "visualizer": "claude-opus-5-5", "checker": "claude-sonnet-5-5"}


def test_explained_paper_records_which_models_made_it(tmp_path):
    work = write_work(tmp_path / "work", [judged(1), judged(2)], explained={"arxiv-2611.00001": {}, "arxiv-2611.00002": {}})
    (work / "papers/arxiv-2611.00001/made_by.json").write_text(json.dumps(MADE_BY))
    content = tmp_path / "content"

    assert publish(work, content) == 0

    assert read_json(content / "papers/arxiv-2611.00001/meta.json")["made_by"] == MADE_BY
    assert "made_by" not in read_json(content / "papers/arxiv-2611.00002/meta.json")


def test_made_by_without_every_role_aborts_with_nothing_written(tmp_path, capsys):
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": {}})
    (work / "papers/arxiv-2611.00001/made_by.json").write_text(json.dumps({"expert": "claude-opus-5-5"}))
    content = tmp_path / "content"

    assert publish(work, content) == 1

    assert not (content / "papers").exists()
    assert "made_by" in capsys.readouterr().err


@pytest.mark.parametrize(
    "rendered, expected",
    [
        ({"kind": "illustration", "to_scale": True}, {"kind": "illustration", "to_scale": True}),
        ({"kind": "data"}, {"kind": "data"}),
        (None, {}),
    ],
    ids=["illustration to scale", "data", "check.json without a hero"],
)
def test_plate_kind_comes_from_the_hero_the_render_check_reported(tmp_path, rendered, expected):
    opts = {} if rendered is None else {"hero": {"path": "explainer/hero.webp", "width": 600, "height": 450, **rendered}}
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": opts})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["hero"] == {**HERO, **expected}


TURN = "Earth felt space stretch."
CARD_TEXT = {
    "hook": "Two black holes merged. " + TURN,
    "hook_turn": TURN,
    "readout": {"value": "1.0", "exponent": -21, "label": "Peak strain. Pitch 35 to 250 Hz"},
}


@pytest.mark.parametrize("explained", [False, True], ids=["short card", "explained card"])
def test_second_voice_and_readout_reach_the_feed_item_and_the_paper_record(tmp_path, explained):
    paywalled = {"fulltext": {"available": False, "kind": None, "url": None}} if not explained else {}
    record = judged(1, **CARD_TEXT, **paywalled)
    work = write_work(tmp_path / "work", [record, judged(2)], explained={"arxiv-2611.00001": {}} if explained else None)
    content = tmp_path / "content"

    assert publish(work, content) == 0

    first, second = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert first["has_explainer"] is explained
    meta = read_json(content / "papers/arxiv-2611.00001/meta.json")
    for published in (first, meta):
        assert {k: published[k] for k in CARD_TEXT} == CARD_TEXT
    other_meta = read_json(content / "papers/arxiv-2611.00002/meta.json")
    for published in (second, other_meta):
        assert "hook_turn" not in published and "readout" not in published


@pytest.mark.parametrize(
    "turn",
    ["Earth felt space stretch", "Two black holes merged. Earth felt space stretch.", "arth felt space stretch.", " Earth felt space stretch."],
    ids=["not a suffix", "the whole hook", "starts inside a word", "starts with a space"],
)
def test_hook_turn_that_is_not_the_closing_clause_aborts_with_nothing_changed(tmp_path, capsys, turn):
    content = published_repo(tmp_path)
    before = tree(content)
    work = write_work(tmp_path / "work", [judged(60), judged(61, **{**CARD_TEXT, "hook_turn": turn})])

    assert publish(work, content) == 1

    assert tree(content) == before
    err = capsys.readouterr().err
    assert "line 2" in err and "hook_turn" in err


@pytest.mark.parametrize(
    "readout",
    [
        {"value": "about 5", "label": "Peak strain"},
        {"value": "5", "label": "x"},
        {"value": "5"},
        {"value": "5", "label": "Peak strain", "note": "extra"},
        {"value": "5", "exponent": 2.5, "label": "Peak strain"},
    ],
    ids=["value with words", "label too short", "no label", "unknown field", "fractional exponent"],
)
def test_schemas_reject_a_malformed_readout(readout):
    record = judged(1, readout=readout)
    assert schemas.errors("judged", record)
    item = {k: v for k, v in record.items() if k in ("id", "title", "hook", "summary", "field", "tags", "status", "venue", "published", "url", "significance")}
    item.update(authors_short="Lovelace et al.", has_explainer=False, added_at=NOW, readout=readout)
    assert schemas.errors("feed-item", item)


def test_hook_turn_rule_applies_to_every_item_in_a_chunk():
    record = judged(1)
    item = {k: record[k] for k in ("id", "title", "hook", "summary", "field", "tags", "status", "venue", "published", "url", "significance")}
    item.update(authors_short="Lovelace et al.", has_explainer=False, added_at=NOW)
    good = {**item, "hook_turn": "where nobody looked"}
    bad = {**item, "hook_turn": "where nobody looks"}
    assert schemas.errors("chunk", {"v": 1, "number": 1, "items": [item, good]}) == []
    assert schemas.errors("chunk", {"v": 1, "number": 1, "items": [good, bad]}) == [
        "items/1/hook_turn: hook_turn is not an exact suffix of hook: 'where nobody looks'"
    ]


EXPERT_READOUT = {"value": "1.3", "exponent": -21, "unit": "strain", "label": "Peak strain, from Table 2"}
SCOUT_READOUT = CARD_TEXT["readout"]


@pytest.mark.parametrize(
    "card, expected",
    [({"readout": EXPERT_READOUT}, EXPERT_READOUT), ({"readout": None}, None), (None, SCOUT_READOUT)],
    ids=["expert readout replaces the scout's", "null removes it", "no card.json leaves it"],
)
def test_explained_card_takes_the_readout_the_expert_settled(tmp_path, card, expected):
    opts = {} if card is None else {"card": card}
    work = write_work(tmp_path / "work", [judged(1, **CARD_TEXT)], explained={"arxiv-2611.00001": opts})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    meta = read_json(content / "papers/arxiv-2611.00001/meta.json")
    for published in (item, meta):
        assert published.get("readout") == expected
        assert published["hook_turn"] == CARD_TEXT["hook_turn"]
    assert not (content / "papers/arxiv-2611.00001/card.json").exists()


def test_card_json_of_an_explainer_that_did_not_pass_is_ignored(tmp_path):
    work = write_work(tmp_path / "work", [judged(1, **CARD_TEXT)], explained={"arxiv-2611.00001": {"review": False, "card": {"readout": None}}})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["has_explainer"] is False
    assert item["readout"] == SCOUT_READOUT


@pytest.mark.parametrize("card", [{"readout": None}, {"readout": EXPERT_READOUT}], ids=["null", "object"])
def test_open_chunk_upgrade_replaces_or_removes_the_readout_in_place(tmp_path, card):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1, **CARD_TEXT), judged(2)]), content)

    work = write_work(tmp_path / "w2", [judged(1, **CARD_TEXT)], explained={"arxiv-2611.00001": {"card": card}})
    assert publish(work, content, now=LATER) == 0

    first, _ = read_json(content / "feed/v1/chunks/000001.json")["items"]
    meta = read_json(content / "papers/arxiv-2611.00001/meta.json")
    for published in (first, meta):
        assert published.get("readout") == card["readout"]
    assert first["has_explainer"] is True
    assert not (content / "feed/v1/upgrades.json").exists()


@pytest.mark.parametrize(
    "card", [{"readout": None}, {"readout": EXPERT_READOUT}, None], ids=["null", "object", "no card.json"]
)
def test_closed_chunk_upgrade_carries_the_readout_in_upgrades_json(tmp_path, card):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1, **CARD_TEXT)] + [judged(n) for n in range(2, 42)]), content)
    closed = (content / "feed/v1/chunks/000001.json").read_bytes()

    opts = {} if card is None else {"card": card}
    work = write_work(tmp_path / "w2", [judged(1, **CARD_TEXT)], explained={"arxiv-2611.00001": opts})
    assert publish(work, content, now=LATER) == 0

    assert (content / "feed/v1/chunks/000001.json").read_bytes() == closed
    entry = read_json(content / "feed/v1/upgrades.json")["upgrades"]["arxiv-2611.00001"]
    expected = {"explainer": "papers/arxiv-2611.00001/", "hero": HERO, "explained_at": LATER}
    if card is not None:
        expected["readout"] = card["readout"]
    assert entry == expected
    meta = read_json(content / "papers/arxiv-2611.00001/meta.json")
    assert meta.get("readout") == (SCOUT_READOUT if card is None else card["readout"])
    assert schemas.errors("upgrades", read_json(content / "feed/v1/upgrades.json")) == []


@pytest.mark.parametrize(
    "card_text",
    ['{"readout": {"value": "about 5", "label": "Peak strain"}}', "{}", '{"readout": null, "hook": "x"}', "{not json"],
    ids=["bad readout", "no readout key", "unknown field", "not JSON"],
)
def test_invalid_card_json_aborts_with_nothing_changed(tmp_path, capsys, card_text):
    content = published_repo(tmp_path)
    before = tree(content)
    work = write_work(tmp_path / "work", [judged(60), judged(61)], explained={"arxiv-2611.00061": {}})
    (work / "papers/arxiv-2611.00061/card.json").write_text(card_text)

    assert publish(work, content) == 1

    assert tree(content) == before
    assert "card.json" in capsys.readouterr().err


def test_paper_record_names_the_kit_version_its_page_loads(tmp_path):
    work = write_work(tmp_path / "work", [judged(1), judged(2)], explained={"arxiv-2611.00001": {"kit": 2}, "arxiv-2611.00002": {}})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    assert read_json(content / "papers/arxiv-2611.00001/meta.json")["kit"] == 2
    assert read_json(content / "papers/arxiv-2611.00002/meta.json")["kit"] == 1
    assert read_json(content / "feed/v1/head.json")["kit"] == 1


def test_passing_check_without_the_page_kit_version_aborts_with_nothing_changed(tmp_path, capsys):
    content = published_repo(tmp_path)
    before = tree(content)
    work = write_work(tmp_path / "work", [judged(61)], explained={"arxiv-2611.00061": {"kit": None}})

    assert publish(work, content) == 1

    assert tree(content) == before
    assert "page.kit" in capsys.readouterr().err


def test_schemas_accept_only_a_readout_object_or_null_in_upgrades_and_card():
    def upgrades(readout):
        entry = {"explainer": "papers/arxiv-1/", "hero": HERO, "explained_at": NOW, "readout": readout}
        return {"v": 1, "upgrades": {"arxiv-1": entry}}

    assert schemas.errors("upgrades", upgrades(None)) == []
    assert schemas.errors("upgrades", upgrades(EXPERT_READOUT)) == []
    assert schemas.errors("upgrades", upgrades({"value": "5"}))
    assert schemas.errors("upgrades", upgrades("5 strain"))
    assert schemas.errors("card", {"readout": None}) == []
    assert schemas.errors("card", {"readout": EXPERT_READOUT}) == []
    assert schemas.errors("card", {"readout": False})


def test_content_published_before_plates_and_readouts_still_validates_and_publishes(tmp_path):
    # A repo written before hero.night, hero.kind, hook_turn, and readout existed: one-image heroes,
    # in a closed chunk, in the open chunk, and in upgrades.json.
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(n) for n in range(1, 42)], explained={"arxiv-2611.00002": {}, "arxiv-2611.00041": {}}), content)
    publish(write_work(tmp_path / "w2", [judged(1)], explained={"arxiv-2611.00001": {}}), content, now=LATER)
    for path in content.glob("feed/v1/chunks/*.json"):
        chunk = read_json(path)
        for item in chunk["items"]:
            if "hero" in item:
                item["hero"].pop("night")
        path.write_text(json.dumps(chunk, indent=2, sort_keys=True) + "\n")
    upgrades = read_json(content / "feed/v1/upgrades.json")
    for entry in upgrades["upgrades"].values():
        entry["hero"].pop("night")
    (content / "feed/v1/upgrades.json").write_text(json.dumps(upgrades, indent=2, sort_keys=True) + "\n")
    for path in content.glob("papers/*/hero-night.webp"):
        path.unlink()

    assert publish(write_work(tmp_path / "w3", [judged(42), judged(43)], explained={"arxiv-2611.00043": {}}), content, now="2026-11-15T00:00:00Z") == 0

    for pattern, schema in SCHEMA_FOR:
        for path in content.glob(pattern):
            lines = path.read_text().splitlines() if path.suffix == ".jsonl" else [path.read_text()]
            for line in lines:
                assert schemas.errors(schema, json.loads(line)) == [], path
    assert "night" not in read_json(content / "feed/v1/chunks/000001.json")["items"][1]["hero"]
    assert read_json(content / "feed/v1/chunks/000002.json")["items"][-1]["hero"]["night"]["path"] == "papers/arxiv-2611.00043/hero-night.webp"


@pytest.mark.parametrize(
    "opts",
    [{"check": False}, {"review": False}, {"files": False}, {"night": False}],
    ids=["render check failed", "review failed", "explainer files missing", "night plate missing"],
)
def test_explainer_that_is_missing_or_failed_gives_a_short_card(tmp_path, opts):
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": opts})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["has_explainer"] is False
    assert "hero" not in item and "explainer" not in item
    assert sorted(p.name for p in (content / "papers/arxiv-2611.00001").iterdir()) == ["meta.json"]


def tree(root: Path) -> dict[str, bytes]:
    """Every file under root (outside .git) and its bytes."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def chunk_ids(content: Path, number: int) -> list[str]:
    return [i["id"] for i in read_json(content / f"feed/v1/chunks/{number:06d}.json")["items"]]


def test_chunk_rolls_over_after_40_items(tmp_path):
    work = write_work(tmp_path / "work", [judged(n) for n in range(1, 42)])
    content = tmp_path / "content"

    assert publish(work, content) == 0

    assert chunk_ids(content, 1) == [f"arxiv-2611.{n:05d}" for n in range(1, 41)]
    assert chunk_ids(content, 2) == ["arxiv-2611.00041"]
    head = read_json(content / "feed/v1/head.json")
    assert (head["chunk_count"], head["total_items"]) == (2, 41)


def test_items_append_to_the_open_chunk_across_runs_in_the_order_added(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(3), judged(1)]), content)
    publish(write_work(tmp_path / "w2", [judged(2)]), content, now="2026-11-12T09:00:00Z")

    assert chunk_ids(content, 1) == ["arxiv-2611.00003", "arxiv-2611.00001", "arxiv-2611.00002"]
    assert read_json(content / "feed/v1/head.json")["updated_at"] == "2026-11-12T09:00:00Z"


def test_second_run_with_the_same_work_folder_changes_nothing(tmp_path):
    records = [judged(n) for n in range(1, 45)]
    work = write_work(tmp_path / "work", records, explained={"arxiv-2611.00002": {}, "arxiv-2611.00043": {}})
    content = tmp_path / "content"
    publish(work, content)
    before = tree(content)

    assert publish(work, content, now="2026-11-13T00:00:00Z") == 0

    assert tree(content) == before


def test_a_paper_already_in_the_feed_is_never_added_twice(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1)]), content)
    same_doi = judged(7, doi="10.1000/ABC")
    publish(write_work(tmp_path / "w2", [same_doi]), content)
    later = [
        judged(1),
        judged(1),
        judged(8, title=judged(1)["title"].upper() + "!"),
        judged(9, id="doi-10.1000-abc", arxiv_id=None, doi="https://doi.org/10.1000/abc"),
        judged(10),
    ]

    publish(write_work(tmp_path / "w3", later), content)

    assert chunk_ids(content, 1) == ["arxiv-2611.00001", "arxiv-2611.00007", "arxiv-2611.00010"]
    assert read_json(content / "feed/v1/head.json")["total_items"] == 3


def test_closed_chunks_are_never_modified(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(n) for n in range(1, 81)]), content)
    closed = {k: v for k, v in tree(content).items() if k in ("feed/v1/chunks/000001.json", "feed/v1/chunks/000002.json")}
    assert len(closed) == 2

    later = [judged(n) for n in range(1, 101)]
    publish(write_work(tmp_path / "w2", later, explained={"arxiv-2611.00005": {}, "arxiv-2611.00045": {}}), content)

    after = tree(content)
    assert {k: after[k] for k in closed} == closed
    assert chunk_ids(content, 3) == [f"arxiv-2611.{n:05d}" for n in range(81, 101)]


LATER = "2026-11-14T10:30:00Z"
HERO = {
    "path": "papers/arxiv-2611.00001/hero.webp",
    "width": 120,
    "height": 63,
    "night": {"path": "papers/arxiv-2611.00001/hero-night.webp", "width": 120, "height": 63},
}


def test_short_card_in_the_open_chunk_gains_its_explainer_in_place(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1), judged(2)]), content)

    work = write_work(tmp_path / "w2", [judged(1)], explained={"arxiv-2611.00001": {}})
    assert publish(work, content, now=LATER) == 0

    first, second = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert first["has_explainer"] is True
    assert first["explainer"] == "papers/arxiv-2611.00001/"
    assert first["hero"] == HERO
    assert first["added_at"] == NOW
    assert second["has_explainer"] is False
    assert not (content / "feed/v1/upgrades.json").exists()
    meta = read_json(content / "papers/arxiv-2611.00001/meta.json")
    assert (meta["has_explainer"], meta["added_at"], meta["explained_at"]) == (True, NOW, LATER)
    assert (content / "papers/arxiv-2611.00001/index.html").exists()
    assert read_json(content / "feed/v1/head.json")["updated_at"] == LATER
    assert read_json(content / "feed/v1/head.json")["total_items"] == 2


def test_short_card_in_a_closed_chunk_gains_its_explainer_through_upgrades(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(n) for n in range(1, 42)]), content)
    closed = (content / "feed/v1/chunks/000001.json").read_bytes()

    work = write_work(tmp_path / "w2", [judged(1)], explained={"arxiv-2611.00001": {}})
    assert publish(work, content, now=LATER) == 0

    assert (content / "feed/v1/chunks/000001.json").read_bytes() == closed
    assert read_json(content / "feed/v1/upgrades.json") == {
        "v": 1,
        "upgrades": {"arxiv-2611.00001": {"explainer": "papers/arxiv-2611.00001/", "hero": HERO, "explained_at": LATER}},
    }
    assert read_json(content / "papers/arxiv-2611.00001/meta.json")["has_explainer"] is True
    assert (content / "papers/arxiv-2611.00001/hero.webp").exists()
    assert (content / "papers/arxiv-2611.00001/hero-night.webp").exists()

    before = tree(content)
    assert publish(work, content, now="2026-11-15T00:00:00Z") == 0
    assert tree(content) == before


def test_seen_state_records_each_paper_by_month_added(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1, doi="10.1000/x")]), content)
    publish(write_work(tmp_path / "w2", [judged(2)]), content, now="2026-12-01T00:00:00Z")

    assert (content / "state/seen/2026-11.jsonl").read_text().splitlines() == [
        json.dumps(
            {
                "added_at": NOW,
                "arxiv_id": "2611.00001",
                "chunk": 1,
                "doi": "10.1000/x",
                "id": "arxiv-2611.00001",
                "title_key": ids.title_key("Observation number 1 of a thing in a place"),
            }
        )
    ]
    [december] = (content / "state/seen/2026-12.jsonl").read_text().splitlines()
    assert json.loads(december)["id"] == "arxiv-2611.00002"


def test_publish_never_touches_the_cursors(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1, published="2026-11-11")]), content)
    assert not (content / "state/cursors.json").exists()

    (content / "state/cursors.json").write_text('{"v": 1, "cursors": {"arxiv": "2026-11-01"}}\n')
    publish(write_work(tmp_path / "w2", [judged(2, published="2026-11-11")]), content)
    assert (content / "state/cursors.json").read_text() == '{"v": 1, "cursors": {"arxiv": "2026-11-01"}}\n'


SCHEMA_FOR = [
    ("feed/v1/head.json", "head"),
    ("feed/v1/chunks/*.json", "chunk"),
    ("feed/v1/upgrades.json", "upgrades"),
    ("papers/*/meta.json", "paper-meta"),
    ("state/cursors.json", "cursors"),
    ("state/seen/*.jsonl", "seen"),
]


def test_every_output_file_matches_its_schema(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(n) for n in range(1, 42)], explained={"arxiv-2611.00002": {}}), content)
    publish(write_work(tmp_path / "w2", [judged(1), judged(41)], explained={"arxiv-2611.00001": {}, "arxiv-2611.00041": {}}), content)

    checked = set()
    for pattern, schema in SCHEMA_FOR:
        for path in content.glob(pattern):
            lines = path.read_text().splitlines() if path.suffix == ".jsonl" else [path.read_text()]
            for line in lines:
                assert schemas.errors(schema, json.loads(line)) == [], path
            checked.add(path.relative_to(content).as_posix())
    json_files = {k for k in tree(content) if k.endswith((".json", ".jsonl"))}
    assert json_files == checked
    assert "feed/v1/upgrades.json" in checked
    assert schemas.errors("feed-item", read_json(content / "feed/v1/chunks/000002.json")["items"][0]) == []
    assert read_json(content / "feed/v1/chunks/000002.json")["items"][0]["has_explainer"] is True


def test_schemas_reject_what_publish_must_never_write():
    assert schemas.errors("chunk", {"v": 1, "number": 1, "items": [{"id": "arxiv-1"}]})
    assert schemas.errors("upgrades", {"v": 1, "upgrades": {"arxiv-1": {"explainer": "papers/arxiv-1/", "hero": {"path": "x"}, "explained_at": NOW}}})
    assert schemas.errors("cursors", {"v": 1, "cursors": {"nature": "2026-11-01"}})
    assert schemas.errors("seen", {"id": "arxiv-1", "doi": None, "arxiv_id": "1", "title_key": "x", "chunk": 1, "added_at": NOW})


def published_repo(tmp_path: Path) -> Path:
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w0", [judged(n) for n in range(1, 42)]), content)
    return content


def test_invalid_judged_record_aborts_with_nothing_changed(tmp_path, capsys):
    content = published_repo(tmp_path)
    before = tree(content)
    bad = judged(50)
    del bad["hook"]
    work = write_work(tmp_path / "work", [judged(60), bad])

    assert publish(work, content) == 1

    assert tree(content) == before
    assert "line 2" in capsys.readouterr().err


def test_unparseable_judged_line_aborts_with_nothing_changed(tmp_path):
    content = published_repo(tmp_path)
    before = tree(content)
    work = write_work(tmp_path / "work", [judged(60)])
    with (work / "judged.jsonl").open("a") as f:
        f.write("{not json\n")

    assert publish(work, content) == 1
    assert tree(content) == before


def test_unreadable_explainer_files_abort_with_nothing_changed(tmp_path):
    content = published_repo(tmp_path)
    before = tree(content)
    work = write_work(tmp_path / "work", [judged(60), judged(61)], explained={"arxiv-2611.00061": {}})
    (work / "papers/arxiv-2611.00061/explainer/hero.webp").write_bytes(b"not an image")

    assert publish(work, content) == 1
    assert tree(content) == before

    (work / "papers/arxiv-2611.00061/explainer/hero.webp").write_bytes((FIXTURES / "hero.webp").read_bytes())
    (work / "papers/arxiv-2611.00061/explainer/hero-night.webp").write_bytes(b"not an image")
    assert publish(work, content) == 1
    assert tree(content) == before

    (work / "papers/arxiv-2611.00061/explainer/hero-night.webp").write_bytes((FIXTURES / "hero-night.webp").read_bytes())
    (work / "papers/arxiv-2611.00061/review.json").write_text("{")
    assert publish(work, content) == 1
    assert tree(content) == before


def test_output_that_fails_its_schema_aborts_with_nothing_changed(tmp_path, capsys):
    content = published_repo(tmp_path)
    with (content / "state/seen/2026-11.jsonl").open("a") as f:
        f.write('{"id": "arxiv-2611.99999", "title_key": "not a key"}\n')
    before = tree(content)

    assert publish(write_work(tmp_path / "work", [judged(60)]), content) == 1

    assert tree(content) == before
    assert "state/seen/2026-11.jsonl" in capsys.readouterr().err


def test_bad_now_aborts(tmp_path):
    content = published_repo(tmp_path)
    before = tree(content)
    assert publish(write_work(tmp_path / "work", [judged(60)]), content, now="yesterday") == 1
    assert publish(write_work(tmp_path / "work", [judged(60)]), content, now="2026-11-12T08:00:00") == 1
    assert tree(content) == before


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def git_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@example.invalid")
    (path / "README.md").write_text("content repo\n")
    git(path, "add", "README.md")
    git(path, "commit", "-q", "-m", "Start")
    return path


SUBJECTS = {
    "feed": "Feed head and chunks the app reads",
    "papers": "Published papers: explainer page, card image, and record for each",
    "state": "Pipeline bookkeeping: papers in the feed, source cursors, and the explain queue",
}


def test_commit_makes_one_commit_per_changed_folder_with_its_subject(tmp_path):
    content = git_repo(tmp_path / "content")
    (content / "README.md").write_text("an unrelated edit the caller has not committed\n")
    (content / "notes.txt").write_text("untracked\n")

    assert publish(write_work(tmp_path / "work", [judged(1)]), content, "--commit") == 0

    subjects = git(content, "log", "--format=%s").splitlines()
    assert sorted(subjects[:3]) == sorted(SUBJECTS.values())
    assert subjects[3] == "Start"
    for folder, subject in SUBJECTS.items():
        assert git(content, "log", "-1", "--format=%s", "--", folder).strip() == subject
        changed = git(content, "show", "--name-only", "--format=", git(content, "log", "-1", "--format=%H", "--", folder).strip())
        assert {line.split("/")[0] for line in changed.split()} == {folder}
    assert git(content, "status", "--porcelain").splitlines() == [" M README.md", "?? notes.txt"]


def test_commit_skips_folders_that_did_not_change(tmp_path):
    content = git_repo(tmp_path / "content")
    work = write_work(tmp_path / "work", [judged(1)])
    publish(work, content, "--commit")
    count = len(git(content, "log", "--format=%s").splitlines())

    assert publish(work, content, "--commit") == 0
    assert len(git(content, "log", "--format=%s").splitlines()) == count

    publish(write_work(tmp_path / "w2", [judged(1)], explained={"arxiv-2611.00001": {}}), content, "--commit", now=LATER)
    subjects = git(content, "log", "--format=%s").splitlines()
    assert sorted(subjects[:2]) == sorted([SUBJECTS["feed"], SUBJECTS["papers"]])
    assert len(subjects) == count + 2


def test_state_commit_carries_the_explain_queue_and_its_removals(tmp_path):
    content = git_repo(tmp_path / "content")
    work = write_work(tmp_path / "work", [judged(1)])
    (content / "state/queue").mkdir(parents=True)
    (content / "state/queue/arxiv-2611.00002.json").write_text("{}\n")
    (content / "state/queue/arxiv-2611.00003.json").write_text("{}\n")
    (content / "state/queue-failed.jsonl").write_text('{"id": "arxiv-2611.00004", "reason": "x", "at": "%s"}\n' % NOW)

    assert publish(work, content, "--commit") == 0
    committed = git(content, "show", "--name-only", "--format=", git(content, "log", "-1", "--format=%H", "--", "state").strip()).split()
    assert {"state/queue/arxiv-2611.00002.json", "state/queue/arxiv-2611.00003.json", "state/queue-failed.jsonl"} <= set(committed)

    (content / "state/queue/arxiv-2611.00002.json").unlink()
    assert publish(work, content, "--commit") == 0
    assert git(content, "status", "--porcelain").strip() == ""
    assert git(content, "log", "-1", "--format=%s").strip() == SUBJECTS["state"]
    assert "state/queue/arxiv-2611.00002.json" not in git(content, "ls-files", "state")


def test_without_commit_nothing_is_committed(tmp_path):
    content = git_repo(tmp_path / "content")
    assert publish(write_work(tmp_path / "work", [judged(1)]), content) == 0
    assert git(content, "log", "--format=%s").splitlines() == ["Start"]


def test_push_sends_main_to_origin(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    content = git_repo(tmp_path / "content")
    git(content, "remote", "add", "origin", str(remote))
    git(content, "push", "-q", "origin", "main")

    assert publish(write_work(tmp_path / "work", [judged(1)]), content, "--commit", "--push") == 0

    assert git(remote, "rev-parse", "main") == git(content, "rev-parse", "main")


def test_git_failure_is_reported_as_an_error(tmp_path, capsys):
    content = tmp_path / "content"
    assert publish(write_work(tmp_path / "work", [judged(1)]), content, "--commit") == 1
    assert "publish: git" in capsys.readouterr().err


def test_without_now_the_current_utc_time_is_used(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    work = write_work(tmp_path / "work", [judged(1)])

    assert main(["publish", "--work", str(work), "--content", str(content)]) == 0

    added_at = read_json(content / "feed/v1/chunks/000001.json")["items"][0]["added_at"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", added_at)
    assert read_json(content / "feed/v1/head.json")["updated_at"] == added_at


def test_now_with_an_offset_is_converted_to_utc(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "work", [judged(1)]), content, now="2026-11-12T03:00:00-05:00")
    assert read_json(content / "feed/v1/head.json")["updated_at"] == NOW
