"""Loads the shared JSON schemas from the repo's schema/ folder and validates records.

errors() also applies the rules a JSON schema cannot state (see hook_turn_errors), so every
caller that validates a record against its schema gets them too.
"""
import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schema"


@cache
def _registry() -> Registry:
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        resources.append((path.name, Resource.from_contents(json.loads(path.read_text()))))
    return Registry().with_resources(resources)


@cache
def validator(name: str) -> Draft202012Validator:
    """name is the file stem before .schema.json: candidate, judged, feed-item, chunk, head, paper-meta."""
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text())
    return Draft202012Validator(schema, registry=_registry())


def hook_turn_problem(hook: str, turn: str) -> str | None:
    """Why `turn` is not a valid hook_turn for `hook`, or None when it is.

    The turn is the hook's closing clause: an exact suffix of the hook, shorter than the
    whole hook, starting at the start of a word (the character before it is a space).
    """
    if not hook.endswith(turn):
        return "hook_turn is not an exact suffix of hook"
    if turn == hook:
        return "hook_turn is the whole hook"
    if turn[:1].isspace() or not hook[len(hook) - len(turn) - 1].isspace():
        return "hook_turn must start at the start of a word in hook"
    return None


def hook_turn_errors(record: object, path: tuple = ()) -> list[str]:
    """The hook_turn rule, for every object in `record` that holds both hook and hook_turn
    as strings (a Judged record, a feed item, a paper record, or the items of a chunk)."""
    found = []
    if isinstance(record, dict):
        hook, turn = record.get("hook"), record.get("hook_turn")
        if isinstance(hook, str) and isinstance(turn, str):
            problem = hook_turn_problem(hook, turn)
            if problem:
                found.append(f"{'/'.join(str(p) for p in (*path, 'hook_turn'))}: {problem}: {turn!r}")
        for key, value in record.items():
            found += hook_turn_errors(value, (*path, key))
    elif isinstance(record, list):
        for index, value in enumerate(record):
            found += hook_turn_errors(value, (*path, index))
    return found


def errors(name: str, record: object) -> list[str]:
    schema_errors = [f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in validator(name).iter_errors(record)]
    return schema_errors + hook_turn_errors(record)
