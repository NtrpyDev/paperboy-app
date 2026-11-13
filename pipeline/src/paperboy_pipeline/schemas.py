"""Loads the shared JSON schemas from the repo's schema/ folder and validates records."""
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


def errors(name: str, record: object) -> list[str]:
    return [f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in validator(name).iter_errors(record)]
