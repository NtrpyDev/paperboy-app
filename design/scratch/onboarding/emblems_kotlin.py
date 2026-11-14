"""Writes the eleven field drawings of emblems.py as Kotlin data for the app.

  python3 design/scratch/onboarding/emblems_kotlin.py

writes app/src/main/java/io/github/ntrpydev/paperboy/ui/fields/EmblemArt.kt. Run it again
whenever emblems.py or the line screens in scratch/engraved/lib.py change; never edit the
Kotlin file by hand.

How: each drawing is drawn by emblems.py itself, once per form (printed and deselected) and
once per theme's hairline (day 0.5, night 0.6), with stand-in colors. The SVG it returns is
read back into a small tree of shapes and groups: circles and rectangles become path data,
colors become theme tokens (plate, key, ground, ghost) or one of the six line screens, and a
stroke width that differs between the two runs is written as a day and a night width. The
app draws the tree with Compose paths (EmblemCanvas.kt), in the theme's colors.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emblems  # noqa: E402
from emblems import EH, EMBLEMS, EW, Style, n  # noqa: E402
from lib import A1, A2, PITCH  # noqa: E402  (emblems.py put scratch/engraved on the path)

REPO = HERE.parents[2]
OUT = REPO / "app/src/main/java/io/github/ntrpydev/paperboy/ui/fields/EmblemArt.kt"
PID = "E"
TOKENS = {"@P": "Ink.Plate", "@K": "Ink.Key", "@G": "Ink.Ground", "@GC": "Ink.Ghost"}
# The six line screens of lib.patterns: (name, angle, fraction of the pitch inked).
SCREENS = [("a1", A1, 0.24), ("a2", A1, 0.46), ("a3", A1, 0.68), ("b1", A2, 0.24), ("b2", A2, 0.44), ("b3", A2, 0.66)]


def draw(wire, ghost, hair):
    defs, marks = EMBLEMS[wire](PID, Style("@P", "@K", "@G", "@GC", hair=hair), ghost=ghost)
    return ET.fromstring(f"<svg><defs>{defs}</defs>{marks}</svg>")


def check_screens(svg):
    """The patterns emblems.py used must be the six line screens the app knows."""
    for p in svg.iter("pattern"):
        name = p.get("id")[len(PID):]
        _, ang, frac = next(s for s in SCREENS if s[0] == name)
        rect = p.find("rect")
        assert p.get("patternTransform") == f"rotate({ang})", p.attrib
        assert abs(float(p.get("height")) - PITCH) < 1e-9, p.attrib
        assert abs(float(rect.get("height")) - PITCH * frac) < 1e-3, rect.attrib
        assert rect.get("fill") == "@P", rect.attrib


def shape_d(el):
    tag = el.tag
    if tag == "path":
        return el.get("d")
    if tag == "circle":
        cx, cy, r = (float(el.get(a)) for a in ("cx", "cy", "r"))
        return emblems.ring(cx, cy, r) + "Z"
    if tag == "rect":
        x, y, w, h = (float(el.get(a)) for a in ("x", "y", "width", "height"))
        return f"M{n(x)} {n(y)}h{n(w)}v{n(h)}h{n(-w)}Z"
    raise ValueError(f"unknown shape {tag}")


def clips(svg):
    out = {}
    for cp in svg.iter("clipPath"):
        out[cp.get("id")] = "".join(shape_d(c) for c in cp)
    return out


def paint(v):
    if v is None or v == "none":
        return None
    if v in TOKENS:
        return TOKENS[v]
    m = re.fullmatch(rf"url\(#{PID}([ab][123])\)", v)
    if m:
        return f"Ink.{m.group(1).upper()}"
    raise ValueError(f"unknown paint {v}")


def kstr(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"'


def f(v):
    return n(float(v)) + "f"


def node(day, night, cp, fill=None):
    """One element of the day run and the same element of the night run, as Kotlin."""
    assert day.tag == night.tag
    fill = day.get("fill", fill)
    transform, clip = day.get("transform"), day.get("clip-path")
    if day.tag == "g":
        inner = [node(a, b, cp, fill) for a, b in zip(day, night, strict=True)]
    else:
        assert fill is not None, day.attrib
        args = [kstr(shape_d(day))]
        fp, sp = paint(fill), paint(day.get("stroke"))
        if fp:
            args.append(f"fill = {fp}")
        if sp:
            wd, wn = float(day.get("stroke-width")), float(night.get("stroke-width"))
            args += [f"stroke = {sp}", f"width = {f(wd)}"]
            if abs(wd - wn) > 1e-9:
                args.append(f"widthNight = {f(wn)}")
            if day.get("stroke-linejoin") == "round":
                args.append("roundJoin = true")
            if day.get("stroke-linecap") == "round":
                args.append("roundCap = true")
            if day.get("stroke-dasharray"):
                args.append("dash = floatArrayOf(" + ", ".join(f(x) for x in day.get("stroke-dasharray").split()) + ")")
        inner = None
        leaf = f"Shape({', '.join(args)})"
    if transform is None and clip is None:
        return leaf if inner is None else f"Group(listOf({', '.join(inner)}))"
    args = [f"listOf({', '.join(inner)})" if inner is not None else f"listOf({leaf})"]
    if clip:
        cid = re.fullmatch(r"url\(#(.+)\)", clip).group(1)
        args.append(f"clip = {kstr(cp[cid])}")
    if transform:
        m = re.fullmatch(r"rotate\(([-\d.]+) ([-\d.]+) ([-\d.]+)\)", transform)
        if m:
            args += [f"rotate = {f(m.group(1))}", f"pivotX = {f(m.group(2))}", f"pivotY = {f(m.group(3))}"]
        else:
            m = re.fullmatch(r"translate\(([-\d.]+) ([-\d.]+)\)", transform)
            assert m, transform
            args += [f"dx = {f(m.group(1))}", f"dy = {f(m.group(2))}"]
    return f"Group({', '.join(args)})"


def form(wire, ghost):
    day, night = draw(wire, ghost, 0.5), draw(wire, ghost, 0.6)
    check_screens(day)
    cp = clips(day)
    marks = [e for e in day if e.tag != "defs"], [e for e in night if e.tag != "defs"]
    return ",\n        ".join(node(a, b, cp) for a, b in zip(*marks, strict=True))


def main():
    funcs, entries = [], []
    for wire in EMBLEMS:
        name = re.sub(r"\W", "", wire)
        funcs.append(
            f"private fun {name}() = EmblemDrawing(\n"
            f"    printed = listOf(\n        {form(wire, False)},\n    ),\n"
            f"    deselected = listOf(\n        {form(wire, True)},\n    ),\n)\n"
        )
        entries.append(f'    "{wire}" -> {name}()')
    screens = ",\n    ".join(f"Ink.{s.upper()} to Screen({f(a)}, {f(fr)})" for s, a, fr in SCREENS)
    text = (
        "// Generated by design/scratch/onboarding/emblems_kotlin.py from emblems.py. Do not edit.\n"
        "// To regenerate: python3 design/scratch/onboarding/emblems_kotlin.py\n"
        "package io.github.ntrpydev.paperboy.ui.fields\n\n"
        f"/** The drawings' own size, in the units of their path data. */\n"
        f"internal const val EMBLEM_W = {f(EW)}\ninternal const val EMBLEM_H = {f(EH)}\n\n"
        f"/** The line screens' pitch (scratch/engraved/lib.py PITCH). */\n"
        f"internal const val SCREEN_PITCH = {f(PITCH)}\n\n"
        f"/** The six line screens of scratch/engraved/lib.py `patterns`: angle and inked fraction of the pitch. */\n"
        f"internal val Screens: Map<Ink, Screen> = mapOf(\n    {screens},\n)\n\n"
        "/** The drawing for a field's wire value, or null for a field the drawings do not know. */\n"
        "internal fun emblemDrawing(wire: String): EmblemDrawing? = when (wire) {\n"
        + "\n".join(entries) + "\n    else -> null\n}\n\n" + "\n".join(funcs)
    )
    OUT.write_text(text)
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
