"""Which judged papers are worth an explainer. select and queue add both decide with this.

A paper is worth an explainer when it has full text, its full text kind is in the allowlist
`explain_fulltext_kinds` in pipeline/config.json, and its significance is at least the explain
floor.
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"

EXPLAIN_FLOOR = 6.5


def explain_kinds() -> list[str]:
    return list(json.loads(CONFIG_PATH.read_text())["explain_fulltext_kinds"])


def worth_explaining(record: dict, floor: float, kinds) -> bool:
    fulltext = record["fulltext"]
    return bool(fulltext["available"]) and fulltext.get("kind") in kinds and record["significance"] >= floor
