"""The active fields: the fields at least one paying subscriber has picked.

The worker publishes them at GET /v1/active-fields as {"v": 1, "fields": [...], "updated_at":
"<RFC 3339>"} (Contract 2 of the paid app spec). queue take reads that list from the URL or from a
file of the same shape and takes papers only for those fields. A list that cannot be read, is not
that shape, or names a field the feed does not know is refused: no list, no spend. An empty list is
valid and takes nothing.
"""
import json
from datetime import datetime
from pathlib import Path

import httpx

from . import schemas
from .sources.http import make_client


class FieldsError(Exception):
    """The active field list could not be read or is not valid."""


def known_fields() -> list[str]:
    """The 11 wire values, in the feed's order. The source of truth is the feed item schema."""
    return list(schemas.validator("feed-item").schema["properties"]["field"]["enum"])


def _client() -> httpx.Client:
    return make_client()


def fetch(url: str) -> str:
    """The body at url. One request: a run that cannot read the list stops, it does not wait."""
    try:
        with _client() as client:
            response = client.get(url)
    except httpx.HTTPError as error:
        raise FieldsError(f"could not fetch {url}: {error.__class__.__name__}: {error}")
    if response.status_code != 200:
        raise FieldsError(f"{url} answered HTTP {response.status_code}")
    return response.text


def parse(text: str, where: str) -> list[str]:
    """The fields in a body of the /v1/active-fields shape, in the order given."""
    try:
        body = json.loads(text)
    except json.JSONDecodeError as error:
        raise FieldsError(f"{where} is not valid JSON: {error}")
    if not isinstance(body, dict):
        raise FieldsError(f"{where} is not a JSON object")
    if body.get("v") != 1:
        raise FieldsError(f"{where} has \"v\" {body.get('v')!r}, expected 1")
    fields = body.get("fields")
    if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
        raise FieldsError(f"{where} has no \"fields\" list of strings")
    updated = body.get("updated_at")
    try:
        if not isinstance(updated, str):
            raise ValueError
        datetime.fromisoformat(updated.replace("Z", "+00:00"))
    except ValueError:
        raise FieldsError(f"{where} has no RFC 3339 \"updated_at\"")
    known = known_fields()
    unknown = [f for f in fields if f not in known]
    if unknown:
        raise FieldsError(f"{where} names fields the feed does not know: {', '.join(unknown)}")
    if len(set(fields)) != len(fields):
        raise FieldsError(f"{where} names a field more than once")
    return fields


def load(*, url: str | None = None, file: Path | None = None) -> list[str]:
    if url is not None:
        return parse(fetch(url), url)
    try:
        text = Path(file).read_text()
    except OSError as error:
        raise FieldsError(f"could not read {file}: {error.strerror or error}")
    return parse(text, str(file))
