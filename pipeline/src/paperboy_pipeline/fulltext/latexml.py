"""arXiv's HTML rendering (LaTeXML output) to a Paper.

Only the <article class="ltx_document"> is read, so the site's navigation, banners and
footers never reach the text. Math is taken from each <math> element's alttext, which is the
author's own LaTeX.
"""
import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from .document import (
    Cell,
    Flow,
    Paper,
    Section,
    Table,
    display_math,
    emphasis,
    script,
    escape_text,
    inline_math,
    squash,
    table_markdown,
)

_SKIP_TAGS = {"script", "style", "button", "svg", "nav", "header", "footer", "noscript", "img", "input", "form"}
_SKIP_CLASSES = {
    "ltx_pubnotes",
    "ltx_classification",
    "ltx_dates",
    "ltx_TOC",
    "ltx_page_navbar",
    "ltx_bibliography",
    "ltx_authors",
}
_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def _classes(el: Tag) -> set[str]:
    return set(el.get("class") or [])


def _tex(math: Tag) -> str:
    alttext = math.get("alttext")
    if alttext is not None:
        return alttext
    annotation = math.find("annotation", attrs={"encoding": "application/x-tex"})
    return annotation.get_text() if annotation else math.get_text()


class _Converter:
    def __init__(self, paper: Paper):
        self.paper = paper

    # Walking

    def walk(self, node: Tag, flow: Flow) -> None:
        for child in node.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                flow.text(escape_text(str(child)))
            elif isinstance(child, Tag):
                self.element(child, flow)

    def inline(self, node: Tag) -> str:
        flow = Flow()
        self.walk(node, flow)
        return " ".join(flow.done())

    def blocks(self, node: Tag) -> list[str]:
        flow = Flow()
        self.walk(node, flow)
        return flow.done()

    def element(self, el: Tag, flow: Flow) -> None:
        name, cls = el.name, _classes(el)
        if name in _SKIP_TAGS or cls & _SKIP_CLASSES:
            return
        if name == "math":
            if el.get("display") == "block":
                flow.block(display_math(_tex(el)))
            else:
                flow.text(inline_math(_tex(el)))
        elif "ltx_note" in cls:
            if "ltx_role_footnote" in cls:
                flow.text(self.footnote(el))
        elif name == "table" and cls & {"ltx_equation", "ltx_equationgroup"}:
            for block in self.equation(el):
                flow.block(block)
        elif name == "figure":
            if "ltx_table" in cls or (el.find("table", class_="ltx_tabular") and not el.find("img")):
                flow.block(self.table_figure(el))
            else:
                self.figure(el)
        elif name == "table" and "ltx_tabular" in cls:
            flow.block(table_markdown(self.table(el)))
        elif name in ("ul", "ol"):
            flow.block(self.list(el))
        elif name == "blockquote":
            flow.block("\n".join("> " + block for block in self.blocks(el)))
        elif "ltx_listing" in cls:
            lines = [squash(line.get_text()) for line in el.find_all(class_="ltx_listingline")]
            flow.block("```\n" + "\n".join(lines) + "\n```")
        elif name in _HEADINGS:
            flow.text(emphasis(self.inline(el), "**") + " ")
        elif name in ("em", "i") or "ltx_font_italic" in cls:
            flow.text(emphasis(self.inline(el), "*"))
        elif name in ("b", "strong") or "ltx_font_bold" in cls:
            flow.text(emphasis(self.inline(el), "**"))
        elif name in ("sup", "sub"):
            flow.text(script(name, self.inline(el)))
        elif name == "br":
            flow.text(" ")
        elif name in ("p", "div", "section", "li", "dl", "dd", "dt") or "ltx_para" in cls:
            flow.flush()
            self.walk(el, flow)
            flow.flush()
        else:
            self.walk(el, flow)

    # Pieces

    def footnote(self, note: Tag) -> str:
        mark = note.find("sup", class_="ltx_note_mark")
        label = squash(mark.get_text()) if mark else str(len(self.paper.footnotes) + 1)
        content = note.find(class_="ltx_note_content") or note
        for junk in content.find_all(["sup"], class_="ltx_note_mark") + content.find_all(class_="ltx_tag_note"):
            junk.extract()
        self.paper.footnotes.append((label, self.inline(content)))
        return f"[^{label}]"

    def equation(self, table: Tag) -> list[str]:
        out = []
        for row in table.find_all("tr", class_="ltx_eqn_row"):
            maths = [m for m in row.find_all("math")]
            if not maths:
                continue
            tex = " ".join(_tex(m) for m in maths)
            number = row.find(class_="ltx_eqn_eqno")
            tag = squash(number.get_text()).strip("()") if number else None
            out.append(display_math(tex, tag or None))
        return out

    def _caption(self, figure: Tag) -> tuple[str, str]:
        caption = figure.find("figcaption", recursive=False)
        if caption is None:
            return "", ""
        tag = caption.find(class_="ltx_tag")
        label = squash(tag.get_text()) if tag else ""
        if tag:
            tag.extract()
        return label, self.inline(caption)

    def figure(self, figure: Tag) -> None:
        if figure.find_parent("figure", class_="ltx_figure"):
            return  # a panel inside a figure; its caption is folded into the parent's
        label, caption = self._caption(figure)
        panels = []
        for panel in figure.find_all("figure"):
            panel_label, panel_caption = self._caption(panel)
            if panel_caption:
                panels.append(f"{panel_label} {panel_caption}".strip())
        caption = " ".join(part for part in [caption, *panels] if part)
        if not label:
            label = f"Figure {len(self.paper.figures) + 1}"
        self.paper.figures.append((label, caption))

    def table_figure(self, figure: Tag) -> str:
        label, caption = self._caption(figure)
        parts = []
        if label or caption:
            parts.append(f"**{label.rstrip(':. ')}:** {caption}" if label else caption)
        flow = Flow()
        has_body = False
        for child in figure.children:
            if isinstance(child, Tag) and child.name == "figcaption":
                continue
            if isinstance(child, Tag) and child.find("table", class_="ltx_tabular") or (
                isinstance(child, Tag) and child.name == "table"
            ):
                has_body = True
            if isinstance(child, Tag) and child.name == "img" or (isinstance(child, Tag) and child.find("img")):
                if not child.find("table", class_="ltx_tabular"):
                    flow.block("[The table body is an image in the source and is not transcribed.]")
                    has_body = True
                    continue
            if isinstance(child, NavigableString):
                flow.text(escape_text(str(child)))
            elif isinstance(child, Tag):
                self.element(child, flow)
        if not has_body:
            flow.block("[No table body found in the source.]")
        parts.extend(flow.done())
        return "\n\n".join(parts)

    def table(self, table: Tag) -> Table:
        rows: list[list[Cell]] = []
        head_rows = 0
        all_rows = [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]
        for tr in all_rows:
            cells = [c for c in tr.find_all(["td", "th"], recursive=False)]
            rows.append(
                [Cell(self.inline(c), int(c.get("colspan") or 1), int(c.get("rowspan") or 1)) for c in cells]
            )
        head_rows = sum(1 for tr in all_rows if tr.parent.name == "thead")
        if head_rows == 0:
            for tr in all_rows:
                cells = tr.find_all(["td", "th"], recursive=False)
                if cells and all(c.name == "th" and "ltx_th_row" not in _classes(c) for c in cells):
                    head_rows += 1
                else:
                    break
        return Table(rows, head_rows)

    def list(self, el: Tag) -> str:
        ordered = el.name == "ol"
        lines = []
        for li in el.find_all("li", recursive=False):
            tag = li.find(class_="ltx_tag_item")
            marker = squash(tag.get_text()) if tag else ""
            if tag:
                tag.extract()
            text = " ".join(self.blocks(li))
            if ordered or (marker and marker not in ("•", "–", "-", "∙", "◦")):
                lines.append(f"- {marker} {text}".rstrip())
            else:
                lines.append(f"- {text}")
        return "\n".join(lines)

    # Sections

    def section(self, el: Tag) -> None:
        heading = next((c for c in el.children if isinstance(c, Tag) and c.name in _HEADINGS), None)
        if heading is not None:
            level = int(heading.name[1])
            self.paper.sections.append(Section(level, self.inline(heading)))
        for child in el.children:
            if child is heading or isinstance(child, Comment):
                continue
            if isinstance(child, Tag) and child.name == "section":
                if "ltx_bibliography" in _classes(child):
                    self.paper.reference_count += len(child.find_all("li", class_="ltx_bibitem"))
                else:
                    self.section(child)
                continue
            flow = Flow()
            if isinstance(child, NavigableString):
                flow.text(escape_text(str(child)))
            else:
                self.element(child, flow)
            target = self.paper.sections[-1].blocks if self.paper.sections else self.paper.preamble
            target.extend(flow.done())


def convert(html: str | bytes) -> Paper:
    soup = BeautifulSoup(html, "lxml")
    article = soup.find("article", class_="ltx_document")
    if article is None:
        raise ValueError("no LaTeXML article in the page")
    paper = Paper()
    conv = _Converter(paper)

    title = article.find(class_="ltx_title_document")
    if title is not None:
        for note in title.find_all(class_="ltx_note"):
            note.extract()
        paper.title = conv.inline(title)

    for creator in article.select(".ltx_authors .ltx_creator.ltx_role_author"):
        name = creator.find(class_="ltx_personname")
        if name is None:
            continue
        for junk in name.find_all(class_=["ltx_note", "ltx_contact", "ltx_author_notes"]):
            junk.extract()
        first_line = re.split(r"<br[^>]*>", str(name), maxsplit=1)[0]
        text = squash(BeautifulSoup(first_line, "lxml").get_text(" "))
        if text:
            paper.authors.append(text)

    for child in article.children:
        if not isinstance(child, Tag) or child is title:
            continue
        cls = _classes(child)
        if "ltx_abstract" in cls:
            heading = child.find(class_="ltx_title_abstract")
            if heading:
                heading.extract()
            paper.abstract.extend(conv.blocks(child))
        elif "ltx_keywords" in cls:
            paper.front.append(conv.inline(child))
        elif "ltx_bibliography" in cls:
            paper.reference_count += len(child.find_all("li", class_="ltx_bibitem"))
        elif child.name == "section" or "ltx_acknowledgements" in cls and child.find(_HEADINGS):
            conv.section(child)
        elif cls & _SKIP_CLASSES or child.name in _SKIP_TAGS:
            continue
        else:
            flow = Flow()
            conv.element(child, flow)
            target = paper.sections[-1].blocks if paper.sections else paper.preamble
            target.extend(flow.done())

    # A \thanks line LaTeXML could not place sometimes lands as a lone e-mail paragraph.
    paper.preamble = [b for b in paper.preamble if not re.fullmatch(r"\S*@\S+", b)]
    return paper


def license_label(html: str | bytes) -> str | None:
    """The license line arXiv prints at the top of the HTML page, such as "CC BY 4.0"."""
    soup = BeautifulSoup(html, "lxml")
    node = soup.find(id="license-tr")
    return squash(node.get_text()).removeprefix("License:").strip() if node else None
