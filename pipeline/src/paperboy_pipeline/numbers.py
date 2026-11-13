"""The numbers check for a quick explainer: every number the page prints is printed in the
paper's title or abstract.

A quick explainer is built from the title and abstract alone (pipeline/QUICK.md), so a number on
the page that is not in them was made up, worked out, or remembered. The render check collects
the page's text as (zone, text) runs (render/probe.js) and calls check() when the page has
data-depth="abstract" and the paper's record is at hand.

What counts as a number on the page: a run of digits, with thousands separators (1,234 or a thin
space), a decimal point, and a leading sign, in prose, labels drawn in figures, tables, stats, and
the readout. Signs, percent marks, ranges (2-20), and plus or minus (0.63 +/- 0.19) split into
their numbers, each checked on its own. Numbers are compared by magnitude: 0.630 matches 0.63,
and -12 matches a "12 percent drop". A power of ten (1.0 x 10^-21, 10<sup>6</sup>, or Unicode
superscripts) checks its mantissa and its exponent; the base 10 is not a claim.

Exempt, because they are not claims about the paper's results:
- ruler and value line labels drawn by the kit (zone "scale": .pb-tick-label, .pb-value-label),
  which are a scale, and the plate slug ("Plate 1", zone "slug");
- figure, plate, table, step, panel, section, and equation numbers ("Fig. 2", "Step 3");
- the citation: the paper's DOI, arXiv id, and venue name, its publication date written as a
  date ("November 12, 2026", "12 November 2026", "2026-11-12") and its year alone;
- names with digits: digits glued to a letter (Cas9, Gaia DR3, O2, v2) or joined to one by a
  hyphen (COVID-19, IL-6), 2D and 3D, and subscripts (H<sub>2</sub>O);
- unit exponents: a power written after a letter (m<sup>2</sup>, year<sup>-1</sup>).

What the title and abstract print is read generously: every digit run in them, LaTeX as written
($63{,}254$, $10^{-21}$, $4\\pi$), superscripts flattened by tag stripping (10<sup>6</sup> read as
"106" after a times sign), and number words (two, twenty-five, twofold, first).
"""
import re
from decimal import Decimal, InvalidOperation

SUPER = dict(zip("\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b", "0123456789+-"))
SUB = dict(zip("\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u208a\u208b", "0123456789+-"))
DASHES = re.compile("[\u2212\u2010\u2011\u2012\u2013\u2014\ufe63\uff0d]")
LETTER = "A-Za-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f\u0370-\u03ff"  # Latin and Greek letters, not the signs \u00d7 and \u00f7
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]

WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
BIG = {"hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9, "trillion": 10**12, "dozen": 12,
       "twice": 2, "double": 2, "doubled": 2, "triple": 3, "tripled": 3, "quadruple": 4}
ORDINALS = {w: i + 1 for i, w in enumerate(
    "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split())}


def _scripts(text: str) -> str:
    """Unicode superscript runs become ^{...} and subscript runs _{...}."""
    text = re.sub("[" + "".join(SUPER) + "]+", lambda m: "^{" + "".join(SUPER[c] for c in m.group()) + "}", text)
    return re.sub("[" + "".join(SUB) + "]+", lambda m: "_{" + "".join(SUB[c] for c in m.group()) + "}", text)


def normalize(text: str) -> str:
    """One spelling for what pages, abstracts, and LaTeX write in many ways."""
    text = _scripts(text)
    text = DASHES.sub("-", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\\[()\[\]]|\$", " ", text)  # math delimiters
    text = text.replace("{,}", ",").replace("\\%", "%")
    text = re.sub(r"\\(?:times|cdot)\b", "\u00d7", text)
    text = re.sub(r"\\pm\b", "\u00b1", text)
    text = re.sub(r"(\d)(?:\\[,;:!]|[\u2009\u202f])(?=\d{3}(?!\d))", r"\1,", text)  # thin space thousands
    text = re.sub(r"\\[,;:!]|~", " ", text)
    text = re.sub(r"\^\s*([+-]?\s*\d+)", r"^{\1}", text)
    text = re.sub(r"_\s*(\d+)", r"_{\1}", text)
    return text


def _magnitude(token: str) -> Decimal | None:
    try:
        return abs(Decimal(token.replace(",", ""))).normalize()
    except InvalidOperation:
        return None


def _digit_runs(text: str) -> list[str]:
    """The numbers in text, as written: thousands kept together, lists and versions split."""
    out = []
    for run in re.findall(r"[\d.,]*\d[\d.,]*", text):
        run = run.strip(".,")
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", run):
            out.append(run)
            continue
        for part in run.split(","):
            part = part.strip(".")
            if re.fullmatch(r"\d+(?:\.\d+)?", part):
                out.append(part)
            else:
                out += [p for p in part.split(".") if p]
    return out


def _word_numbers(text: str) -> set[Decimal]:
    found = set()
    lower = text.lower()
    for tens, value in TENS.items():
        for unit, extra in WORDS.items():
            if 0 < extra < 10 and re.search(rf"\b{tens}[- ]{unit}\b", lower):
                found.add(Decimal(value + extra))
    for table in (WORDS, TENS, BIG, ORDINALS):
        for word, value in table.items():
            if re.search(rf"\b{word}(?:-?fold)?\b", lower):
                found.add(Decimal(value))
    return found


def allowed_numbers(record: dict) -> set[Decimal]:
    """Every number the title and abstract print, read generously."""
    text = normalize(record.get("title", "") + "\n" + record.get("abstract", ""))
    found = _word_numbers(text)
    flat = re.sub(r"[\^_]\{([^}]*)\}", r" \1 ", text)
    for token in _digit_runs(flat):
        value = _magnitude(token)
        if value is not None:
            found.add(value)
    # A superscript flattened by tag stripping: "3 x 106" is 3 x 10^6.
    for exponent in re.findall(r"[\u00d7x]\s*10-?(\d{1,2})(?!\d)", flat):
        found.add(Decimal(exponent))
    return {v.normalize() for v in found}


def _date_patterns(published: str) -> list[str]:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", published or "")
    if not match:
        return []
    year, month, day = match.group(1), int(match.group(2)), int(match.group(3))
    name = MONTHS[month - 1]
    months = f"(?:{name}|{name[:3]}\\.?)"
    return [
        re.escape(published),
        rf"{months}\s+0?{day}(?:st|nd|rd|th)?,?\s+{year}",
        rf"0?{day}\s+{months},?\s+{year}",
        rf"{months},?\s+{year}",
        rf"{months}\s+0?{day}(?:st|nd|rd|th)?\b",
        rf"\b{year}\b",
    ]


def _strip_exempt(text: str, record: dict) -> str:
    """Remove what is not a claim (see the module docstring)."""
    for literal in (record.get("url"), record.get("doi"), record.get("arxiv_id"), record.get("venue")):
        if literal:
            text = re.sub(re.escape(literal) + (r"(?:v\d+)?" if literal == record.get("arxiv_id") else ""), " ", text, flags=re.I)
    for pattern in _date_patterns(record.get("published", "")):
        text = re.sub(pattern, " ", text, flags=re.I)
    text = re.sub(r"\b(?:fig(?:ure)?s?\.?|plates?|tables?|steps?|panels?|sections?|eqs?\.?|equations?)\s*\(?\d+[a-z]?\)?"
                  r"(?:\s*(?:,|and|to|-)\s*\d+[a-z]?\b)*", " ", text, flags=re.I)
    text = re.sub(r"_\{[^}]*\}", " ", text)  # subscripts: H2O, CO2
    text = re.sub(rf"(?<=[{LETTER}])\s*\^\{{[^}}]*\}}", " ", text)  # unit exponents: m^2, year^-1
    text = re.sub(rf"(?<=[{LETTER}])-?\d+(?:\.\d+)*", " ", text)  # names: Cas9, DR3, COVID-19, v2
    text = re.sub(r"\b[1-4]-?D\b", " ", text)  # 2D, 3D
    return text


def page_numbers(text: str, record: dict) -> list[tuple[str, Decimal]]:
    """The numbers one run of page text claims, as (as printed, magnitude)."""
    text = _strip_exempt(normalize(text), record)
    out = []

    def power(m: re.Match) -> str:
        if m.group(1):
            out.append((m.group(1), m.group(1)))
        out.append((m.group(0).strip(), m.group(3)))
        return " "

    text = re.sub(r"(?:(\d+(?:\.\d+)?)\s*[\u00d7x\u00b7*]\s*)?\b10\s*\^\{\s*([+-]?)\s*(\d+)\s*\}", power, text)
    text = re.sub(r"\^\{([^}]*)\}", r" \1 ", text)
    out += [(token, token) for token in _digit_runs(text)]
    numbers = []
    for printed, token in out:
        value = _magnitude(token)
        if value is not None:
            numbers.append((printed, value.normalize()))
    return numbers


def check(runs, record: dict) -> tuple[int, list[str]]:
    """(numbers checked, problems): one problem per number the page prints that the title and
    abstract do not. runs are (zone, text) pairs from the render check's probe."""
    allowed = allowed_numbers(record)
    checked, problems = 0, []
    for zone, text in runs:
        if zone in ("scale", "slug"):
            continue
        for printed, value in page_numbers(text, record):
            checked += 1
            if value not in allowed:
                snippet = text if len(text) <= 80 else text[:77] + "..."
                problem = f'"{printed}" in "{snippet}"'
                if problem not in problems:
                    problems.append(problem)
    return checked, problems
