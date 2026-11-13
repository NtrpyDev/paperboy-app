import pytest

from paperboy_pipeline import ids, schemas
from paperboy_pipeline.cli import build_parser


def test_parser_builds_without_commands():
    assert build_parser().prog == "paperboy-pipeline"


def test_paper_id_prefers_arxiv_and_drops_version():
    assert ids.paper_id(arxiv_id="2611.01234v3", doi="10.1/x") == "arxiv-2611.01234"


def test_paper_id_sanitizes_doi():
    assert ids.paper_id(doi="https://doi.org/10.1103/PhysRevLett.116.061102") == "doi-10.1103-physrevlett.116.061102"


def test_paper_id_needs_an_identifier():
    with pytest.raises(ValueError):
        ids.paper_id()


def test_title_key_ignores_case_and_punctuation():
    assert ids.title_key("Observation of Gravitational Waves!") == ids.title_key("observation of  gravitational-waves")


def test_candidate_schema_rejects_missing_fields():
    assert schemas.errors("candidate", {"id": "arxiv-1"})
