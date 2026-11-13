"""The paper as the converters see it, and how it is written out as Markdown.

Every converter fills a Paper; render() turns it into the fulltext.md layout: title,
authors, abstract, the sections with their headings in order, then a Figures list, the
footnotes, and the reference count.
"""
import re
from dataclasses import dataclass, field


@dataclass
class Section:
    level: int  # 2 for a top-level section, 3 for a subsection, and so on up to 6
    heading: str
    blocks: list[str] = field(default_factory=list)
    synthetic: bool = False  # a heading the converter added, not one from the paper


@dataclass
class Paper:
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: list[str] = field(default_factory=list)
    front: list[str] = field(default_factory=list)  # keywords and the like, shown after the abstract
    extra_abstracts: list[Section] = field(default_factory=list)  # author summary, significance
    preamble: list[str] = field(default_factory=list)  # body text that comes before any heading
    sections: list[Section] = field(default_factory=list)
    figures: list[tuple[str, str]] = field(default_factory=list)  # (label, caption)
    footnotes: list[tuple[str, str]] = field(default_factory=list)  # (label, text)
    reference_count: int = 0

    def section_count(self) -> int:
        return sum(1 for s in self.sections if not s.synthetic)


def squash(text: str) -> str:
    """Collapse runs of whitespace to one space and trim."""
    return re.sub(r"\s+", " ", text).strip()


def strip_tex_comments(tex: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", tex)


def inline_math(tex: str) -> str:
    tex = squash(strip_tex_comments(tex))
    return f"${tex}$" if tex else ""


def display_math(tex: str, tag: str | None = None) -> str:
    tex = strip_tex_comments(tex).strip()
    tex = "\n".join(line.rstrip() for line in tex.splitlines() if line.strip())
    if tag:
        tex += f" \\tag{{{tag}}}"
    return f"$$\n{tex}\n$$"


def escape_text(text: str) -> str:
    """Prose escaping: only the dollar sign, so math delimiters stay unambiguous."""
    return text.replace("$", "\\$")


def emphasis(text: str, marker: str) -> str:
    """Wrap text in * or ** while keeping surrounding spaces outside the markers."""
    core = text.strip()
    if not core:
        return text
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    return f"{lead}{marker}{core}{marker}{trail}"


def script(name: str, text: str) -> str:
    """<sup> or <sub>, without emphasis markers that would only add noise inside them."""
    text = re.sub(r"^(\*+)(.+?)\1$", r"\2", text.strip())
    return f"<{name}>{text}</{name}>"


def clean_label(label: str) -> str:
    return squash(label).rstrip(".: ")


class Flow:
    """Collects inline text into paragraphs, with block elements (display math, tables,
    lists) breaking the paragraph where they occur."""

    def __init__(self):
        self.blocks: list[str] = []
        self._buffer: list[str] = []

    def text(self, text: str) -> None:
        self._buffer.append(text)

    def block(self, block: str) -> None:
        self.flush()
        if block.strip():
            self.blocks.append(block.strip("\n"))

    def flush(self) -> None:
        paragraph = squash("".join(self._buffer))
        self._buffer = []
        if paragraph:
            self.blocks.append(paragraph)

    def done(self) -> list[str]:
        self.flush()
        return self.blocks


# Tables


@dataclass
class Cell:
    text: str
    colspan: int = 1
    rowspan: int = 1


@dataclass
class Table:
    rows: list[list[Cell]]
    head_rows: int = 0  # leading rows that form the header


_MATH_SPAN = re.compile(r"(?<!\\)\$(?:\\.|[^$\\])*?\$")


def _cell_text(text: str) -> str:
    """Cell text safe inside a Markdown table row. A bar in prose is escaped as \\|; a bar
    inside math becomes \\vert (and \\| becomes \\Vert), because \\| is a norm in LaTeX."""
    text = squash(text)
    out, pos = [], 0
    for match in _MATH_SPAN.finditer(text):
        out.append(text[pos:match.start()].replace("|", "\\|"))
        out.append(match.group(0).replace("\\|", "\\Vert ").replace("|", "\\vert "))
        pos = match.end()
    out.append(text[pos:].replace("|", "\\|"))
    return "".join(out)


def table_markdown(table: Table) -> str:
    """A Markdown table. Spanned cells are expanded into the grid: header text repeats across
    its span so each column's header reads fully; a body value appears once, in the first
    cell of its span, so no number is duplicated. Several header rows merge into one with " / "."""
    grid: list[dict[int, tuple[str, bool]]] = []
    carried: dict[tuple[int, int], tuple[str, bool]] = {}
    n_rows = len(table.rows)
    for r, row in enumerate(table.rows):
        placed: dict[int, tuple[str, bool]] = {}
        col = 0
        for cell in row:
            while (r, col) in carried:
                placed[col] = carried.pop((r, col))
                col += 1
            colspan = max(1, cell.colspan)
            rowspan = max(1, min(cell.rowspan, n_rows - r))
            text = _cell_text(cell.text)
            for dc in range(colspan):
                placed[col + dc] = (text, dc > 0)
                for dr in range(1, rowspan):
                    carried[(r + dr, col + dc)] = (text, True)
            col += colspan
        for key in sorted(k for k in carried if k[0] == r):
            placed[key[1]] = carried.pop(key)
        grid.append(placed)
    width = max((max(row) + 1 for row in grid if row), default=0)
    if width == 0:
        return ""

    head = []
    for c in range(width):
        parts: list[str] = []
        for row in grid[: table.head_rows]:
            text = row.get(c, ("", False))[0]
            if text and (not parts or parts[-1] != text):
                parts.append(text)
        head.append(" / ".join(parts))
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * width]
    for row in grid[table.head_rows:]:
        values = ["" if row.get(c, ("", False))[1] else row.get(c, ("", False))[0] for c in range(width)]
        if any(values):
            lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


# The document


def render(paper: Paper) -> str:
    out: list[str] = [f"# {squash(paper.title)}"]
    if paper.authors:
        out.append("Authors: " + ", ".join(squash(a) for a in paper.authors if squash(a)))
    if paper.abstract:
        out.append("## Abstract")
        out.extend(paper.abstract)
    out.extend(paper.front)
    for section in paper.extra_abstracts:
        out.append(f"## {squash(section.heading)}")
        out.extend(section.blocks)
    if paper.preamble:
        out.append("## Main text")
        out.extend(paper.preamble)
    for section in paper.sections:
        out.append(f"{'#' * min(max(section.level, 2), 6)} {squash(section.heading)}")
        out.extend(section.blocks)
    if paper.figures:
        out.append("## Figures")
        out.append("\n".join(f"- **{clean_label(label)}:** {caption}" for label, caption in paper.figures))
    footnotes = list(dict.fromkeys(paper.footnotes))  # a table can repeat one note per mark
    if footnotes:
        out.append("## Footnotes")
        out.append("\n".join(f"[^{clean_label(label)}]: {text}" if label else f"- {text}" for label, text in footnotes))
    if paper.reference_count:
        out.append("## References")
        out.append(f"The reference list ({paper.reference_count} entries) is left out.")
    text = "\n\n".join(block.strip("\n") for block in out if block.strip())
    return re.sub(r"\n{3,}", "\n\n", text) + "\n"
