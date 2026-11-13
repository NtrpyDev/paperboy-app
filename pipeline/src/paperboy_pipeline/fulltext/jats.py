"""JATS XML (bioRxiv and medRxiv source XML, Europe PMC fullTextXML) to a Paper.

Equations come from <tex-math> when present, else from the MathML (its TeX annotation, or a
conversion). Where the source has only an image of an equation or a table, the Markdown says
so in place instead of inventing content.
"""
import re

from lxml import etree

from . import licenses, mathml
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

XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
EQUATION_IMAGE = "[Equation shown only as an image in the source; not transcribed.]"
INLINE_EQUATION_IMAGE = "[formula image]"
TABLE_IMAGE = "[The table body is an image in the source and is not transcribed.]"

_PASS_THROUGH = {
    "sc", "monospace", "underline", "roman", "sans-serif", "styled-content", "named-content", "span",
    "abbrev", "overline", "strike", "x", "chem-struct", "chem-struct-wrap", "glyph-data", "caption",
    "alternatives", "disp-formula-group", "app", "term", "def", "related-article", "inline-supplementary-material",
}
_SKIP = {
    "object-id", "permissions", "graphic", "media", "attrib", "ref-list", "counts", "self-uri",
    "custom-meta-group", "funding-group", "history", "pub-date", "contrib-group", "aff",
}


def _local(tag) -> str:
    return etree.QName(tag).localname if isinstance(tag, str) else ""


def _child(el, name: str):
    return next((c for c in el if _local(c.tag) == name), None)


def _children(el, name: str) -> list:
    return [c for c in el if _local(c.tag) == name]


def _descendant(el, name: str):
    return next((c for c in el.iter() if _local(c.tag) == name), None)


def _strip_ns(root) -> None:
    """Drop namespaces from JATS element names (MathML keeps its local names, which is all we use)."""
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.startswith("{") and "MathML" not in el.tag:
            el.tag = etree.QName(el.tag).localname


def clean_tex(tex: str) -> str:
    """The formula inside a <tex-math>, without the LaTeX document wrapper some publishers add."""
    match = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, flags=re.S)
    if match:
        tex = match.group(1)
    tex = tex.strip()
    for open_, close in (("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$")):
        if tex.startswith(open_) and tex.endswith(close) and len(tex) > len(open_) + len(close):
            tex = tex[len(open_) : -len(close)].strip()
            break
    match = re.fullmatch(r"\\begin\{(equation\*?|displaymath|math)\}(.*)\\end\{\1\}", tex, flags=re.S)
    if match:
        tex = match.group(2).strip()
    tex = re.sub(r"\\(begin|end)\{(align|eqnarray|gather|multline)\*?\}", lambda m: f"\\{m.group(1)}{{aligned}}", tex)
    return tex


class _Converter:
    def __init__(self, paper: Paper):
        self.paper = paper

    def walk(self, el, flow: Flow) -> None:
        if el.text:
            flow.text(escape_text(el.text))
        for child in el:
            if isinstance(child.tag, str):
                self.element(child, flow)
            if child.tail:
                flow.text(escape_text(child.tail))

    def inline(self, el) -> str:
        flow = Flow()
        self.walk(el, flow)
        return " ".join(flow.done())

    def blocks(self, el) -> list[str]:
        flow = Flow()
        self.walk(el, flow)
        return flow.done()

    def element(self, el, flow: Flow) -> None:
        name = _local(el.tag)
        if name in _SKIP:
            return
        if name == "p":
            flow.flush()
            self.walk(el, flow)
            flow.flush()
        elif name == "italic":
            flow.text(emphasis(self.inline(el), "*"))
        elif name == "bold":
            flow.text(emphasis(self.inline(el), "**"))
        elif name in ("sup", "sub"):
            flow.text(script(name, self.inline(el)))
        elif name in ("ext-link", "uri"):
            text = self.inline(el)
            href = el.get(XLINK_HREF) or ""
            flow.text(f"{text} ({href})" if href and href not in text else text)
        elif name == "inline-formula":
            flow.text(self.formula(el, display=False))
        elif name == "disp-formula":
            flow.block(self.formula(el, display=True))
        elif name in ("math", "tex-math"):
            flow.text(self.formula(el, display=False))
        elif name in ("fig", "fig-group"):
            self.figure(el)
        elif name in ("table-wrap", "table-wrap-group"):
            flow.block(self.table_wrap(el))
        elif name == "list":
            flow.block(self.list(el))
        elif name == "def-list":
            items = []
            for item in _children(el, "def-item"):
                term, definition = _child(item, "term"), _child(item, "def")
                items.append(f"- {self.inline(term) if term is not None else ''}: {self.inline(definition) if definition is not None else ''}")
            flow.block("\n".join(items))
        elif name == "disp-quote":
            flow.block("\n".join("> " + block for block in self.blocks(el)))
        elif name in ("boxed-text", "statement", "sec"):
            flow.flush()
            for block in self.blocks(el):
                flow.block(block)
        elif name in ("title", "label"):
            flow.text(emphasis(self.inline(el), "**") + " ")
        elif name == "supplementary-material":
            label = _child(el, "label")
            caption = _child(el, "caption")
            text = " ".join(part for part in [self.inline(label) if label is not None else "", self.inline(caption) if caption is not None else ""] if part)
            if text:
                flow.block(f"Supplementary material: {text}")
        elif name == "fn":
            flow.text(self.footnote(el))
        elif name == "fn-group":
            for fn in _children(el, "fn"):
                self.footnote(fn)
        elif name == "inline-graphic":
            flow.text(INLINE_EQUATION_IMAGE)
        elif name == "break":
            flow.text(" ")
        elif name == "preformat" or name == "code":
            flow.block("```\n" + "".join(el.itertext()).strip("\n") + "\n```")
        elif name == "hr":
            return
        else:
            self.walk(el, flow)

    # Pieces

    def formula(self, el, *, display: bool) -> str:
        tex = None
        tex_math = el if _local(el.tag) == "tex-math" else _descendant(el, "tex-math")
        if tex_math is not None:
            tex = clean_tex("".join(tex_math.itertext()))
        else:
            math = el if _local(el.tag) == "math" else _descendant(el, "math")
            if math is not None:
                tex = mathml.to_latex(math)
        label = _child(el, "label")
        tag = squash("".join(label.itertext())).strip("()") if label is not None else None
        if not tex:
            if display:
                return EQUATION_IMAGE + (f" ({tag})" if tag else "")
            return INLINE_EQUATION_IMAGE
        return display_math(tex, tag or None) if display else inline_math(tex)

    def footnote(self, fn) -> str:
        label_el = _child(fn, "label")
        label = squash("".join(label_el.itertext())) if label_el is not None else ""
        flow = Flow()
        for child in fn:
            if _local(child.tag) != "label":
                self.element(child, flow)
        text = " ".join(flow.done())
        if not text:
            return ""
        if not label:
            label = str(len(self.paper.footnotes) + 1)
        self.paper.footnotes.append((label, text))
        return f"[^{squash(label).rstrip('.: ')}]"

    def _caption(self, el) -> tuple[str, str]:
        label = _child(el, "label")
        caption = _child(el, "caption")
        label_text = squash("".join(label.itertext())) if label is not None else ""
        caption_text = " ".join(self.blocks(caption)) if caption is not None else ""
        return label_text, caption_text

    def figure(self, el) -> None:
        if _local(el.tag) == "fig-group":
            label, caption = self._caption(el)
            if label or caption:
                self.paper.figures.append((label or f"Figure {len(self.paper.figures) + 1}", caption))
            for fig in _children(el, "fig"):
                self.figure(fig)
            return
        label, caption = self._caption(el)
        self.paper.figures.append((label or f"Figure {len(self.paper.figures) + 1}", caption))

    def table_wrap(self, el) -> str:
        if _local(el.tag) == "table-wrap-group":
            return "\n\n".join(self.table_wrap(tw) for tw in _children(el, "table-wrap"))
        label, caption = self._caption(el)
        parts = []
        if label or caption:
            parts.append(f"**{label.rstrip(':. ')}:** {caption}" if label else caption)
        table = _descendant(el, "table")
        if table is not None:
            parts.append(table_markdown(self.table(table)))
        else:
            parts.append(TABLE_IMAGE)
        foot = _child(el, "table-wrap-foot")
        if foot is not None:
            for child in foot:
                if _local(child.tag) == "fn":
                    label_el = _child(child, "label")
                    mark = squash("".join(label_el.itertext())) if label_el is not None else ""
                    flow = Flow()
                    for part in child:
                        if _local(part.tag) != "label":
                            self.element(part, flow)
                    text = " ".join(flow.done())
                    parts.append(f"{mark} {text}".strip())
                elif isinstance(child.tag, str):
                    flow = Flow()
                    self.element(child, flow)
                    parts.extend(flow.done())
        return "\n\n".join(p for p in parts if p)

    def table(self, table) -> Table:
        rows, head_rows = [], 0
        for part in table:
            kind = _local(part.tag)
            trs = [part] if kind == "tr" else _children(part, "tr") if kind in ("thead", "tbody", "tfoot") else []
            for tr in trs:
                cells = [c for c in tr if _local(c.tag) in ("td", "th")]
                rows.append([Cell(self.inline(c), int(c.get("colspan") or 1), int(c.get("rowspan") or 1)) for c in cells])
                if kind == "thead":
                    head_rows += 1
        if head_rows == 0:
            for part in table.iter():
                if _local(part.tag) != "tr":
                    continue
                cells = [c for c in part if _local(c.tag) in ("td", "th")]
                if cells and all(_local(c.tag) == "th" for c in cells):
                    head_rows += 1
                else:
                    break
        return Table(rows, head_rows)

    def list(self, el) -> str:
        ordered = el.get("list-type") in ("order", "arabic", "alpha-lower", "alpha-upper", "roman-lower", "roman-upper")
        lines = []
        for n, item in enumerate(_children(el, "list-item"), start=1):
            label = _child(item, "label")
            marker = squash("".join(label.itertext())) if label is not None else (f"{n}." if ordered else "")
            flow = Flow()
            for child in item:
                if _local(child.tag) != "label":
                    self.element(child, flow)
                if child.tail:
                    flow.text(escape_text(child.tail))
            text = " ".join(flow.done())
            lines.append(f"- {marker} {text}".replace("-  ", "- ") if marker else f"- {text}")
        return "\n".join(lines)

    # Sections

    def section(self, sec, level: int) -> None:
        refs = _children(sec, "ref-list")
        if refs:
            self.count_references(sec)
            return
        title = _child(sec, "title")
        label = _child(sec, "label")
        heading = squash(" ".join(part for part in [
            "".join(label.itertext()) if label is not None else "",
            self.inline(title) if title is not None else "",
        ] if part))
        if heading:
            self.paper.sections.append(Section(level, heading))
        for child in sec:
            if not isinstance(child.tag, str) or child is title or child is label:
                continue
            if _local(child.tag) in ("sec", "app"):
                self.section(child, min(level + 1, 6))
                continue
            flow = Flow()
            self.element(child, flow)
            target = self.paper.sections[-1].blocks if self.paper.sections else self.paper.preamble
            target.extend(flow.done())

    def count_references(self, el) -> None:
        for ref_list in el.iter():
            if _local(ref_list.tag) == "ref-list":
                self.paper.reference_count += len(_children(ref_list, "ref"))


def _authors(meta) -> list[str]:
    names = []
    for group in meta.iter():
        if _local(group.tag) != "contrib-group":
            continue
        for contrib in _children(group, "contrib"):
            kind = (contrib.get("contrib-type") or group.get("content-type") or "author").lower()
            if not kind.startswith("author"):
                continue
            name = _descendant(contrib, "name")
            if name is not None:
                parts = [_child(name, "given-names"), _child(name, "surname"), _child(name, "suffix")]
                text = " ".join(squash("".join(p.itertext())) for p in parts if p is not None)
            else:
                other = _descendant(contrib, "string-name") or _descendant(contrib, "collab")
                text = squash("".join(other.itertext())) if other is not None else ""
            if text:
                names.append(text)
    return names


def _license(meta) -> str | None:
    permissions = _child(meta, "permissions")
    license_el = _child(permissions, "license") if permissions is not None else None
    if license_el is None:
        return None
    urls = [license_el.get(XLINK_HREF)]
    for el in license_el.iter():
        if _local(el.tag) == "license_ref":
            urls.append("".join(el.itertext()))
        urls.append(el.get(XLINK_HREF))
    for url in urls:
        found = licenses.from_url(url)
        if found:
            return found
    found = licenses.from_text(license_el.get("license-type")) or licenses.from_text(" ".join(license_el.itertext()))
    return found or "other"


def convert(xml: bytes) -> tuple[Paper, str | None]:
    """The paper and the license id its <permissions> state (None when it states none)."""
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=True, recover=True)
    root = etree.fromstring(xml, parser)
    if root is None or _local(root.tag) != "article":
        raise ValueError("not a JATS <article>")
    _strip_ns(root)
    paper = Paper()
    conv = _Converter(paper)

    meta = root.find("front/article-meta")
    if meta is None:
        raise ValueError("JATS article has no <article-meta>")
    title = meta.find("title-group/article-title")
    paper.title = conv.inline(title) if title is not None else ""
    paper.authors = _authors(meta)

    abstracts = _children(meta, "abstract")
    main = next((a for a in abstracts if a.get("abstract-type") in (None, "standard", "abstract")), None)
    for abstract in abstracts:
        heading = _child(abstract, "title")
        flow = Flow()
        for child in abstract:
            if child is not heading and isinstance(child.tag, str):
                conv.element(child, flow)
        blocks = flow.done()
        if abstract is main:
            paper.abstract = blocks
        elif blocks:
            name = squash("".join(heading.itertext())) if heading is not None else (abstract.get("abstract-type") or "Summary").replace("-", " ").capitalize()
            paper.extra_abstracts.append(Section(2, name, blocks))
    for group in _children(meta, "kwd-group"):
        words = [squash("".join(k.itertext())) for k in _children(group, "kwd")]
        if words:
            paper.front.append("Keywords: " + "; ".join(words))
    for group in _children(meta, "fn-group"):
        conv.element(group, Flow())

    body = _child(root, "body")
    if body is not None:
        for child in body:
            if not isinstance(child.tag, str):
                continue
            if _local(child.tag) == "sec":
                conv.section(child, 2)
            else:
                flow = Flow()
                conv.element(child, flow)
                target = paper.sections[-1].blocks if paper.sections else paper.preamble
                target.extend(flow.done())

    back = _child(root, "back")
    if back is not None:
        for child in back:
            kind = _local(child.tag)
            if kind == "ref-list":
                conv.count_references(child)
            elif kind in ("sec", "app", "notes", "glossary", "ack"):
                if _child(child, "title") is None and kind == "ack":
                    paper.sections.append(Section(2, "Acknowledgments"))
                    paper.sections[-1].blocks.extend(conv.blocks(child))
                else:
                    conv.section(child, 2)
            elif kind == "app-group":
                for app in child:
                    if _local(app.tag) in ("app", "sec"):
                        conv.section(app, 2)
            elif kind == "fn-group":
                conv.element(child, Flow())

    floats = _child(root, "floats-group")
    if floats is not None:
        tables = []
        for child in floats:
            kind = _local(child.tag)
            if kind in ("fig", "fig-group"):
                conv.figure(child)
            elif kind in ("table-wrap", "table-wrap-group"):
                tables.append(conv.table_wrap(child))
        if tables:
            paper.sections.append(Section(2, "Tables", tables, synthetic=True))

    return paper, _license(meta)
