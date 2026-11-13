"""Presentation MathML to LaTeX, for sources that carry MathML without a TeX version.

When the MathML has a TeX annotation that is used as is. Otherwise the elements are mapped
one by one; the result is LaTeX a reader or KaTeX understands, not a byte copy of whatever
the authors typed.
"""
import re

from lxml import etree

GREEK = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\epsilon", "ϵ": r"\epsilon",
    "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta", "ϑ": r"\vartheta", "ι": r"\iota", "κ": r"\kappa",
    "λ": r"\lambda", "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ϖ": r"\varpi", "ρ": r"\rho",
    "ϱ": r"\varrho", "σ": r"\sigma", "ς": r"\varsigma", "τ": r"\tau", "υ": r"\upsilon", "φ": r"\phi",
    "ϕ": r"\phi", "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega", "Γ": r"\Gamma", "Δ": r"\Delta",
    "Θ": r"\Theta", "Λ": r"\Lambda", "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Ψ": r"\Psi", "Ω": r"\Omega",
}
SYMBOLS = {
    "−": "-", "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp", "≤": r"\leq", "≥": r"\geq",
    "⩽": r"\leq", "⩾": r"\geq", "≠": r"\neq", "≈": r"\approx", "∼": r"\sim", "≃": r"\simeq",
    "≅": r"\cong", "≡": r"\equiv", "∝": r"\propto", "∞": r"\infty", "∂": r"\partial", "∇": r"\nabla",
    "∑": r"\sum", "∏": r"\prod", "∫": r"\int", "∬": r"\iint", "∮": r"\oint", "⋅": r"\cdot", "·": r"\cdot",
    "∘": r"\circ", "°": r"^{\circ}", "→": r"\to", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow", "↦": r"\mapsto", "∈": r"\in",
    "∉": r"\notin", "∋": r"\ni", "⊂": r"\subset", "⊆": r"\subseteq", "⊃": r"\supset", "⊇": r"\supseteq",
    "∪": r"\cup", "∩": r"\cap", "∀": r"\forall", "∃": r"\exists", "∅": r"\emptyset", "¬": r"\neg",
    "∧": r"\wedge", "∨": r"\vee", "ℏ": r"\hbar", "ℓ": r"\ell", "⟨": r"\langle", "⟩": r"\rangle",
    "〈": r"\langle", "〉": r"\rangle", "‖": r"\|", "∥": r"\parallel", "⊥": r"\perp", "…": r"\ldots",
    "⋯": r"\cdots", "⋮": r"\vdots", "⋱": r"\ddots", "′": "'", "″": "''", "∗": "*", "⊗": r"\otimes",
    "⊕": r"\oplus", "†": r"\dagger", "≪": r"\ll", "≫": r"\gg", "∣": r"\mid", "⌊": r"\lfloor",
    "⌋": r"\rfloor", "⌈": r"\lceil", "⌉": r"\rceil", "%": r"\%", "#": r"\#", "&": r"\&",
    "{": r"\{", "}": r"\}", "⁡": "", "⁢": "", "⁣": "", "⁤": "", "​": "",
}
FUNCTIONS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh", "coth", "arcsin", "arccos",
    "arctan", "log", "ln", "lg", "exp", "lim", "max", "min", "sup", "inf", "det", "arg", "deg", "dim",
    "ker", "gcd", "hom", "Pr",
}
OPERATORS = {r"\sum", r"\prod", r"\int", r"\iint", r"\oint", r"\lim", r"\max", r"\min", r"\sup", r"\inf"}
ACCENTS = {
    "¯": r"\bar", "‾": r"\overline", "^": r"\hat", "ˆ": r"\hat", "˜": r"\tilde", "~": r"\tilde",
    "→": r"\vec", "⃗": r"\vec", "˙": r"\dot", "¨": r"\ddot", "⏞": r"\overbrace", "⏟": r"\underbrace",
    "_": r"\underline", "̲": r"\underline",
}
VARIANTS = {
    "normal": r"\mathrm", "bold": r"\mathbf", "bold-italic": r"\boldsymbol", "double-struck": r"\mathbb",
    "script": r"\mathcal", "bold-script": r"\mathcal", "fraktur": r"\mathfrak", "sans-serif": r"\mathsf",
    "bold-sans-serif": r"\mathsf", "monospace": r"\mathtt",
}


def _local(tag) -> str:
    return etree.QName(tag).localname if isinstance(tag, str) else ""


def _children(el) -> list:
    return [c for c in el if isinstance(c.tag, str)]


def _text(el) -> str:
    return "".join(el.itertext()).strip()


def _symbols(text: str) -> str:
    return "".join(GREEK.get(ch) or SYMBOLS.get(ch, ch) for ch in text)


def _join(parts: list[str]) -> str:
    out = ""
    for part in parts:
        if not part:
            continue
        if re.search(r"\\[A-Za-z]+$", out) and re.match(r"[A-Za-z0-9]", part):
            out += " "
        out += part
    return out


def _group(tex: str) -> str:
    return "{" + tex + "}"


def _mi(el) -> str:
    text = _text(el)
    if not text:
        return ""
    if text in FUNCTIONS:
        return "\\" + text
    variant = el.get("mathvariant")
    mapped = _symbols(text)
    if variant == "normal" and text in GREEK:
        return mapped
    if variant in VARIANTS:
        return VARIANTS[variant] + _group(mapped)
    if len(text) > 1 and mapped == text:
        return r"\mathrm" + _group(text)
    return mapped


def _script_base(tex: str) -> str:
    return tex if tex else "{}"


def convert(el) -> str:
    name = _local(el.tag)
    kids = _children(el)
    if name == "semantics":
        for annotation in kids[1:]:
            if _local(annotation.tag) == "annotation" and annotation.get("encoding") in ("application/x-tex", "TeX", "LaTeX"):
                return _text(annotation)
        return convert(kids[0]) if kids else ""
    if name in ("annotation", "annotation-xml", "none", "mprescripts", "maligngroup", "malignmark"):
        return ""
    if name == "mi":
        return _mi(el)
    if name == "mn":
        return _symbols(_text(el))
    if name == "mo":
        return _symbols(_text(el))
    if name == "mtext":
        text = "".join(el.itertext())
        if not text.strip():
            return r"\ "
        return r"\text" + _group(re.sub(r"([{}%#&$_])", r"\\\1", text))
    if name == "ms":
        return r"\text" + _group('"' + _text(el) + '"')
    if name == "mspace":
        return r"\,"
    if name == "msub" and len(kids) == 2:
        return f"{_script_base(convert(kids[0]))}_{_group(convert(kids[1]))}"
    if name == "msup" and len(kids) == 2:
        return f"{_script_base(convert(kids[0]))}^{_group(convert(kids[1]))}"
    if name == "msubsup" and len(kids) == 3:
        return f"{_script_base(convert(kids[0]))}_{_group(convert(kids[1]))}^{_group(convert(kids[2]))}"
    if name == "mfrac" and len(kids) == 2:
        top, bottom = convert(kids[0]), convert(kids[1])
        if el.get("linethickness") in ("0", "0pt", "0px", "0em"):
            return r"\genfrac{}{}{0pt}{}" + _group(top) + _group(bottom)
        if el.get("bevelled") == "true":
            return f"{_group(top)}/{_group(bottom)}"
        return r"\frac" + _group(top) + _group(bottom)
    if name == "msqrt":
        return r"\sqrt" + _group(_join([convert(k) for k in kids]))
    if name == "mroot" and len(kids) == 2:
        return r"\sqrt[" + convert(kids[1]) + "]" + _group(convert(kids[0]))
    if name in ("mover", "munder") and len(kids) == 2:
        base, script = convert(kids[0]), convert(kids[1])
        mark = _text(kids[1]) if _local(kids[1].tag) == "mo" else ""
        if mark in ACCENTS:
            return ACCENTS[mark] + _group(base)
        if base in OPERATORS:
            return f"{base}{'^' if name == 'mover' else '_'}{_group(script)}"
        command = r"\overset" if name == "mover" else r"\underset"
        return command + _group(script) + _group(base)
    if name == "munderover" and len(kids) == 3:
        base, under, over = (convert(k) for k in kids)
        if base in OPERATORS:
            return f"{base}_{_group(under)}^{_group(over)}"
        return r"\overset" + _group(over) + _group(r"\underset" + _group(under) + _group(base))
    if name == "mfenced":
        open_, close = el.get("open", "("), el.get("close", ")")
        separators = (el.get("separators", ",") or "").strip()
        parts = [convert(k) for k in kids]
        sep = separators[0] if separators else ""
        body = sep.join(parts)
        return rf"\left{_symbols(open_) or '.'}{body}\right{_symbols(close) or '.'}"
    if name == "mtable":
        rows = []
        for row in kids:
            cells = [c for c in _children(row) if _local(c.tag) == "mtd"]
            if _local(row.tag) == "mlabeledtr":
                cells = cells[1:]
            rows.append(" & ".join(_join([convert(k) for k in _children(cell)]) for cell in cells))
        return r"\begin{matrix}" + r" \\ ".join(rows) + r"\end{matrix}"
    if name == "mmultiscripts" and kids:
        base = convert(kids[0])
        post, pre, into_pre = [], [], False
        for k in kids[1:]:
            if _local(k.tag) == "mprescripts":
                into_pre = True
                continue
            (pre if into_pre else post).append(convert(k))
        out = ""
        for i in range(0, len(pre) - 1, 2):
            out += "{}_" + _group(pre[i]) + "^" + _group(pre[i + 1])
        out += _script_base(base)
        for i in range(0, len(post) - 1, 2):
            out += "_" + _group(post[i]) + "^" + _group(post[i + 1])
        return out
    # math, mrow, mstyle, mpadded, mphantom, menclose, merror and anything unknown
    return _join([convert(k) for k in kids])


def to_latex(math) -> str:
    """LaTeX for a <math> element (any namespace prefix)."""
    return convert(math).strip()
