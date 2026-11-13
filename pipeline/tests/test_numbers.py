"""The numbers check's rules: what counts as a number on a quick explainer, what is exempt, and how
the title and abstract are read. The render check runs it on a real page (test_quick.py)."""
from decimal import Decimal

import pytest

from paperboy_pipeline import numbers

RECORD = {
    "title": "Atmospheric O 2 reveals a strengthening ocean carbon sink since 1990",
    "abstract": (
        "Leveraging 30+ years of observations, the sink increased by 0.63 ± 0.19 Pg C year −1 decade −1, "
        "35% of emissions between 1990 and 2019, in $63{,}254$ stars with masses $m<4\\pi$, a strain of "
        "$1.0\\times10^{-21}$, at 3 × 106 cells per liter, over twenty-five sites and twofold faster."
    ),
    "published": "2026-11-12",
    "doi": "10.1126/science.aed9544",
    "arxiv_id": None,
    "venue": "Science",
    "url": "https://doi.org/10.1126/science.aed9544",
}


def claims(text, zone="text", record=RECORD):
    return [printed for printed, _ in numbers.page_numbers(text, record)] if zone == "text" else []


def bad(text, zone="text", record=RECORD):
    return numbers.check([(zone, text)], record)[1]


@pytest.mark.parametrize("text", [
    "The sink rose by 0.63 ± 0.19 Pg C a year each decade.",
    "0.630 and 0.19",                     # trailing zero, same value
    "−0.63 and -0.19",                    # signs: compared by magnitude
    "35 percent, 35%, and 35 %",
    "From 1990 to 2019, 1990–2019",       # ranges split
    "63,254 stars; 63\u2009254 stars",     # thousands, comma or thin space
    "masses below 4π",
    "1.0×10⁻²¹ strain",                   # Unicode superscripts
    "1.0 × 10 ^{−21} strain",             # <sup> as the probe reads it
    "3 × 10 ^{6} cells",                  # the abstract's 10<sup>6</sup> flattened to 106
    "More than 30 years, 30+ years",
    "25 sites; 2 times faster",           # the abstract's number words
])
def test_numbers_printed_in_the_title_or_abstract_pass(text):
    assert bad(text) == []


@pytest.mark.parametrize("text, invented", [
    ("averaging 3.1 ± 0.4", ["3.1", "0.4"]),
    ("a 12% drop", ["12"]),
    ("63,255 stars", ["63,255"]),
    ("1.0×10⁻²² strain", ["1.0×10^{-22}"]),
    ("from 2018 to 2019", ["2018"]),
    ("0.6 per decade", ["0.6"]),            # rounding is a new number
    ("0.82, the ratio of 0.63 to 0.77", ["0.82", "0.77"]),
])
def test_numbers_not_in_the_title_or_abstract_fail(text, invented):
    problems = bad(text)
    assert [p.split('"')[1] for p in problems] == invented


@pytest.mark.parametrize("text, zone", [
    ("0 1 2 3 4 Pg C A YEAR", "scale"),       # ruler tick labels drawn by the kit
    ("Plate 1 Data, from the abstract", "slug"),
    ("See Fig. 2 and Figure 3, Table 4, step 5, Panel 6, Eq. 7", "text"),
    ("Science, doi:10.1126/science.aed9544", "source"),
    ("November 12, 2026. Peer-reviewed. 12 Nov. 2026, 2026-11-12, Nov 12", "text"),
    ("Cas9, Gaia DR3, COVID-19, IL-6, kit v2, a 3D model", "text"),
    ("CO _{2} and H₂O and O2", "text"),       # subscripts and glued names
    ("km ^{2} and year ^{-1} and m²", "text"),  # unit exponents
])
def test_exempt_numbers_are_not_claims(text, zone):
    assert numbers.check([(zone, text)], RECORD) == (len(claims(text, zone)), [])
    assert bad(text, zone) == []


def test_an_invented_number_in_the_source_footer_still_fails():
    assert bad("Science, doi:10.1126/science.aed9544, volume 390", "source") == ['"390" in "Science, doi:10.1126/science.aed9544, volume 390"']


def test_the_arxiv_id_and_its_version_are_exempt():
    record = {**RECORD, "arxiv_id": "2611.09160", "doi": None}
    assert bad("arXiv:2611.09160v2", record=record) == []


def test_allowed_numbers_read_latex_and_words():
    allowed = numbers.allowed_numbers(RECORD)
    assert {Decimal("63254"), Decimal("21"), Decimal("4"), Decimal("6"), Decimal("25"), Decimal("2"), Decimal("1.0")} <= allowed


def test_the_check_counts_every_number_and_reports_each_invented_one_once():
    runs = [("text", "0.63 and 9.9"), ("text", "9.9 again"), ("scale", "100"), ("text", "0.63 and 9.9")]
    checked, problems = numbers.check(runs, RECORD)
    assert checked == 5
    assert problems == ['"9.9" in "0.63 and 9.9"', '"9.9" in "9.9 again"']
