"""The explainer patterns the first round left undrawn, in the First Light system, phone width.

  python3 patterns.py [day|night]   writes canvas/project/Explainer-Patterns-Day.dc.html and
                                    canvas/project/Explainer-Patterns-Night.dc.html
  python3 run.py TAG                builds, renders with the screenshot tool, sets the heights, slices

Tokens, type helpers, line screens, the wave field, the traps and the night halo all come
from scratch/engraved/lib.py, so they match the seven final boards. The small helpers
(labels, figure head, legend, swatch) follow scratch/explainer/explainer.py line for line.

Facts come from design/CONTENT.md only. Where a chart form needs numbers that file does not
have (several series, a scatter, a dumbbell, error bars), the chart is a specimen: its
labels are placeholders in brackets, its kind slug says so, and its shapes mean nothing.

  PB_DELAY=ms   pushes every animation back
  PB_OUT=dir    writes somewhere else
"""
import json
import math
import os
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import (INK, STOCK, MUTED, LIVE, NG, NT, NM, NS, AMBER, DISP, TEXT, MONO, A1, A2, PRESS,  # noqa: E402
                 FONTS, mono, disp, text, patterns, ink_keyframes, at, SWEEP_DASH, PLUS, MINUS, CHECK,
                 gw_print, live_under_strokes, pen_under_marks, sign_times)

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
LAB = 10.5
W, M = 390, 20
CW = W - 2 * M
OUT = pathlib.Path(os.environ.get("PB_OUT") or HERE.parents[1] / "canvas" / "project")
HEIGHTS = HERE / "heights.json"

# The stand-in for KaTeX's fonts, which the canvas cannot load. KaTeX_Main and KaTeX_Math are
# Computer Modern, a "Modern" face. Old Standard TT is the Modern face on Google Fonts.
MATH = "'Old Standard TT', 'Times New Roman', serif"
MATH_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap">'

# when each specimen's live mark draws in on the artboard (ms)
T_STEPS, T_LINE, T_SCATTER, T_DUMB, T_UNC, T_TOGGLE, T_TABLE = 900, 1500, 2300, 2700, 3000, 1300, 700


def crom(pts):
    """An open Catmull-Rom spline through pts, as cubic curves."""
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d


def page(title, helmet_css, body, w, h):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
{MATH_LINK}
<style>
{helmet_css}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def build(theme):
    day = theme == "day"
    g, c, mu = (STOCK, INK, MUTED) if day else (NG, NT, NM)
    ch = c if day else NM             # rules, outlines, axes: one step under text at night
    tk = c if day else NM             # tick labels
    plate, live, grid = (BLUE, LIVE, MUTED) if day else (NBLUE, AMBER, NS)
    scr = c if day else NM            # the screen that marks an estimate or a range
    stamp, on_stamp = (MUTED, STOCK) if day else (NM, NG)
    hw = 800 if day else 900
    iw = 300 if day else 400
    lw = 2 if day else 1.9
    pen_r = 3.6 if day else 3.4
    t0 = theme[0]

    L = lambda s, col=None, w=500: f'<div style="{mono(LAB, color=col or mu, weight=w, ls=0.06)}">{s}</div>'
    slug = lambda s: f'<div style="{mono(LAB, color=c, weight=600, ls=0.06)}">{s}</div>'
    code = lambda s: f'<div style="{mono(LAB, color=mu, weight=500, ls=0.02, upper=False)}; text-align: right">{s}</div>'
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"
    lab6 = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 600; letter-spacing: 0.06em"
    num = f"font-family: {DISP}; font-stretch: 62.5%; font-weight: {hw}; font-size: 25px; font-variant-numeric: lining-nums"
    hair = f'<div style="height: 0.75px; background-color: {ch}"></div>'
    double = f'<div style="height: 3px; background-color: {ch}"></div><div style="height: 0.75px; background-color: {ch}; margin-top: 2px"></div>'
    it = lambda size, lh=1.06, st=100: disp(size, weight=iw, stretch=st, lh=lh, ls=-0.012, italic=True)
    hit = it(30, 1.02, 100 if day else 87.5)
    BODY = f"{text(17, lh=1.47)}; text-wrap: pretty"
    P = lambda s, mt=12, col=None: f'<p style="margin: {mt}px 0 0; {BODY}{"; color: " + col if col else ""}">{s}</p>'
    note = lambda s, mt=10: f'<p style="margin: {mt}px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">{s}</p>'
    unit = lambda s: f'<span style="{text(15, lh=1, italic=True)}; font-stretch: 100%; letter-spacing: 0; margin-left: 6px">{s}</span>'
    fighead = lambda a, b: (f'{hair}<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">'
                            f'{slug(a)}{L(b)}</div>')
    figtitle = lambda s: f'<div style="margin-top: 10px; {disp(30, weight=hw, lh=1)}">{s}</div>'
    sup_t = "font-size: 0.64em; line-height: 0; vertical-align: 0.5em; letter-spacing: 0.01em"
    line_attr = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    SPEC = "Specimen, placeholder data"
    wrap = f"display: flex; flex-direction: column; padding: 0 {M}px"

    def tag_outline(s):
        return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {ch}; padding: 4px 6px 3px">{s}</span>'

    def tag_solid(s):
        return f'<span style="{mono(10, color=g, weight=600, ls=0.06)}; background-color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{s}</span>'

    def swatch(pid, tone=("a2", A1, 0.46), col=None):
        name, ang, frac = tone
        return (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><defs>{patterns(pid, col or scr, tones={name: (ang, frac)})}</defs>'
                f'<rect width="22" height="10" fill="url(#{pid}{name})"></rect><rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{c}" stroke-width="0.9"></rect></svg>')

    def legend(items, mt=8):
        return (f'<div style="display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; margin-top: {mt}px; {mono(LAB, color=mu, ls=0.06)}">'
                + "".join(f'<span style="display: inline-flex; align-items: center; gap: 6px">{k}{s}</span>' for k, s in items) + '</div>')

    dot = f'<span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: {live}"></span>'
    key = lambda inner, w_=22, h_=10: f'<svg width="{w_}" height="{h_}" viewBox="0 0 {w_} {h_}" aria-hidden="true">{inner}</svg>'

    def live_core(d, style=""):
        return f'<path d="{d}" {line_attr} stroke="{live}" stroke-width="1.9" style="{style}"></path>'

    def pen_at(x, y, style=""):
        st = f"transform: translate({x:.2f}px, {y:.2f}px){style}"
        return pen_under_marks(day, g, live, st) + f'<circle r="{pen_r}" fill="{live}" style="{st}"></circle>'

    def section(n, name, cls, head, intro=""):
        return (f'<div style="margin-top: 56px">{double}</div>'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-top: 12px">{slug(f"{n:02d} {name}")}{code(cls)}</div>'
                f'<h2 style="margin: 8px 0 0; {disp(30, weight=hw, lh=1.02)}">{head}</h2>'
                + (P(intro, 14) if intro else ""))

    def state(s, mt=32):
        """A note to the reader of the board: which state the specimen under it shows."""
        return f'<div style="margin-top: {mt}px; display: flex; align-items: center; gap: 10px">{L(s)}<div style="flex: 1 1 auto; height: 0.6px; background-color: {grid}"></div></div>'

    def strip(cells, mt=14):
        """A row of states of one small element, each named under it."""
        return (f'<div style="display: flex; gap: 12px; margin-top: {mt}px">'
                + "".join(f'<div style="flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: 6px; align-items: flex-start">'
                          f'<div style="height: 52px; display: flex; align-items: center">{h}</div>{L(lbl)}</div>' for h, lbl in cells)
                + '</div>')

    def ruler(x0, x1, y, n, major_every, labels, unit_s="", unit_x=None):
        """The axis as a ruler: a 0.9 px line, ticks below it, labels 20 px under it."""
        step = (x1 - x0) / n
        ticks = "".join(f'<line x1="{x0 + i * step:.1f}" y1="{y}" x2="{x0 + i * step:.1f}" y2="{y + (7 if i % major_every == 0 else 4)}"></line>' for i in range(n + 1))
        tl = "".join(f'<text x="{x0 + i * step:.1f}" y="{y + 20}" text-anchor="{"start" if i == 0 else "middle"}">{s}</text>' for i, s in labels)
        if unit_s:
            tl += f'<text x="{CW if unit_x is None else unit_x}" y="{y + 20}" text-anchor="end">{unit_s}</text>'
        return (f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{x0:.1f}" y1="{y}" x2="{x1:.1f}" y2="{y}"></line>{ticks}</g>'
                f'<g fill="{tk}" style="{lab}">{tl}</g>')

    def gridlines(x0, x1, ys, labels):
        """Value lines: 0.6 px, inside the plot, each named at its left end above the line."""
        return (f'<g stroke="{grid}" stroke-width="0.6" fill="none">' + "".join(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"></line>' for y in ys) + '</g>'
                f'<g fill="{tk if not day else mu}" style="{lab}">' + "".join(f'<text x="{x0}" y="{y - 5:.1f}">{s}</text>' for y, s in zip(ys, labels)) + '</g>')

    # ------------------------------------------------------------------ the wordmark, small
    def wordmark(col=None, boy=None):
        col = col or c
        return (f'<span style="{disp(22, weight=hw, lh=1)}; color: {col}; padding-bottom: 3px; white-space: nowrap">Paper'
                f'<span style="{disp(22, weight=400, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span>'
                f'<span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: {live}; margin-left: 2px"></span></span>')

    # ------------------------------------------------------------------ Fig. 3, where the mass went (from explainer.py)
    def chart_mass(pid, rows=("before", "after"), t_live=None):
        s = 4.0
        X = lambda v: 0.5 + v * s
        bh = 20
        ys = {}
        y = 0
        for r in rows:
            ys[r] = (y + 11, y + 48)
            y += 85
        last_b = ys[rows[-1]][1]
        axis = last_b + bh + 26
        H = axis + 26
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (7 if v % 10 == 0 else 4)}"></line>' for v in range(0, 71, 5))
        tl = "".join(f'<text x="{X(v):.1f}" y="{axis + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 20, 40, 60))

        def bar(v0, v1, yy, fills):
            r = "".join(f'<rect x="{X(v0):.1f}" y="{yy}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="{f}"></rect>' for f in fills)
            return r + f'<rect x="{X(v0):.1f}" y="{yy}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'

        defs = patterns(pid, scr, tones={"a2": (A1, 0.46), "b2": (A2, 0.44), "a1": (A1, 0.24), "b1": (A2, 0.24)})
        out, heads, nums, extra = "", "", "", ""
        if "before" in rows:
            l1, b1 = ys["before"]
            out += f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
            heads += f'<text x="0" y="{l1}" fill="{c}" style="{lab6}">BEFORE</text><text x="50" y="{l1}" fill="{mu}" style="{lab}">TWO BLACK HOLES</text>'
            nums += f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
        if "after" in rows:
            l2, b2 = ys["after"]
            fl = f' style="animation: flood 260ms {PRESS} {at(t_live)} both"' if t_live is not None else ""
            extra += f'<g stroke="{grid}" stroke-width="0.6" fill="none">' + "".join(f'<line x1="{X(v):.1f}" y1="{b2 + bh}" x2="{X(v):.1f}" y2="{axis}"></line>' for v in (62, 65)) + '</g>'
            out += (f'{bar(0, 62, b2, [f"url(#{pid}a1)", f"url(#{pid}b1)"])}'
                    f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="{live}"{fl}></rect>'
                    f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
                    f'<g fill="{c}" style="{lab}"><text x="{X(65) + 9:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 9:.1f}" y="{b2 + 20}">WAVES</text></g>')
            heads += f'<text x="0" y="{l2}" fill="{c}" style="{lab6}">AFTER</text><text x="43" y="{l2}" fill="{mu}" style="{lab}">ONE BLACK HOLE, AND WAVES</text>'
            nums += f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text><text x="{X(63.5):.1f}" y="{b2 - 7}" text-anchor="middle">3</text>'
        aria = {("before", "after"): "Before: two black holes of about 36 and 29. After: one black hole of about 62, and about 3 that left as gravitational waves.",
                ("after",): "After: one black hole of about 62, and about 3 that left as gravitational waves.",
                ("before",): "Before: two black holes of about 36 and 29."}[tuple(rows)]
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Data from the paper, in solar masses. {aria}" style="display: block">'
            f'<defs>{defs}</defs>{extra}{out}'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}</g>'
            f'{heads}'
            f'<g fill="{tk}" style="{lab}">{tl}<text x="{CW}" y="{axis + 20}" text-anchor="end">SOLAR MASSES</text></g>'
            f'<g fill="{c}" style="{num}">{nums}</g></svg>'
        )

    # ------------------------------------------------------------------ 02 the data table
    def disclosure(is_open, table=""):
        icon = (MINUS if is_open else PLUS)
        summ = (f'<summary style="list-style: none; cursor: pointer; min-height: 44px; display: flex; align-items: center; justify-content: space-between; color: {c}">'
                f'{slug("The numbers")}{icon}</summary>')
        close = "" if is_open else f"; border-bottom: 0.75px solid {ch}"
        return (f'<details class="pb-data"{' open=""' if is_open else ""} style="margin-top: 14px; border-top: 0.75px solid {ch}{close}">{summ}{table}</details>')

    def table_mass():
        th = lambda s, right=False: (f'<th scope="col" style="{mono(LAB, color=mu, ls=0.06)}; text-align: {"right" if right else "left"}; '
                                     f'padding: 0 {0 if right else 12}px 7px 0; border-bottom: 0.75px solid {ch}; white-space: nowrap">{s}</th>')
        rows = [("Before", "The heavier black hole", "36"), ("Before", "The lighter black hole", "29"),
                ("After", "The black hole they formed", "62"), ("After", "Left as gravitational waves", "3")]
        body = ""
        for i, (a, b, v) in enumerate(rows):
            bb = f"0.75px solid {ch}" if i == len(rows) - 1 else f"0.6px solid {grid}"
            td = f"{text(15, lh=1.4)}; padding: 8px 12px 9px 0; border-bottom: {bb}; vertical-align: baseline"
            body += (f'<tr><td style="{td}; white-space: nowrap">{a}</td><td style="{td}">{b}</td>'
                     f'<td style="{td}; padding-right: 0; text-align: right; font-variant-numeric: tabular-nums lining-nums">{v}</td></tr>')
        return (f'<div style="padding-bottom: 2px; animation: press 190ms {PRESS} {at(T_TABLE)} both">'
                f'<table class="pb-table" style="border-collapse: collapse; width: 100%; margin: 0">'
                f'<caption style="caption-side: top; text-align: left; {text(15, lh=1.4, italic=True)}; padding: 0 0 12px">All four values are estimates.</caption>'
                f'<thead><tr>{th("When")}{th("What")}{th("Solar masses", True)}</tr></thead><tbody>{body}</tbody></table></div>')

    # ------------------------------------------------------------------ 03 scroll steps: the pinned visual at step 3 of 4
    def steps_plate(pid):
        """Fig. 1 of the explainer, built in steps. This is the third state: both detectors are
        drawn, the wave front has just reached Hanford, and the gap between arrivals is ruled off."""
        s, x0 = 30.0, 26.0
        X = lambda v: x0 + v * s
        a, band, cy = 112, 160, 140
        by, ry = band + 32, band + 62
        H = ry + 26
        tube = 5
        fcx, fcy = -150.0, 250.0
        front = math.hypot(X(7) - fcx, cy - fcy)

        def det(cx):
            return (f'<rect x="{cx - tube / 2:.1f}" y="{cy - 6 - a}" width="{tube}" height="{a}"></rect>'
                    f'<rect x="{cx - 4:.1f}" y="{cy - 6 - a - 8}" width="8" height="8"></rect>'
                    f'<rect x="{cx + 6:.1f}" y="{cy - tube / 2}" width="{a}" height="{tube}"></rect>'
                    f'<rect x="{cx + 6 + a:.1f}" y="{cy - 4}" width="8" height="8"></rect>'
                    f'<rect x="{cx - 6:.1f}" y="{cy - 6}" width="12" height="12"></rect>')

        (wdefs, wmarks), _ = gw_print(pid, fcx, fcy, W, band, theme, rot=18, rmin=150.0)
        field = (f'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block; position: absolute; left: 0; top: 0; '
                 f'animation: inkband 520ms {PRESS} {at(T_STEPS - 420)} both"><defs>{wdefs}'
                 f'<clipPath id="{pid}front"><circle cx="{fcx}" cy="{fcy}" r="{front + 0.4:.2f}"></circle></clipPath></defs>'
                 f'<g clip-path="url(#{pid}front)">{wmarks}</g></svg>')
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ry}" x2="{X(v):.1f}" y2="{ry + (7 if v % 5 == 0 else 4)}"></line>' for v in range(0, 11))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="middle">{v}</text>' for v in (0, 5, 10))
        bd = f"M{X(0):.1f} {by}H{X(7):.1f}"
        dur = 900
        sweep = f"; animation: sweep {dur}ms linear {at(T_STEPS)} both"
        ride = f"; animation: travel {dur}ms linear {at(T_STEPS)} both"
        pen = f"offset-path: path('{bd}'); offset-distance: 100%; offset-rotate: 0deg"
        under = f'<path d="{bd}" {line_attr} stroke="{g}" stroke-width="7" style="{SWEEP_DASH}{sweep}"></path>'
        draw = (
            f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Illustration, not to scale, step 3 of 4: a wave has crossed both detectors. '
            f'It reached Livingston, Louisiana first and Hanford, Washington about 7 milliseconds later." style="display: block; position: absolute; left: 0; top: 0">'
            f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ry - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
            f'<g fill="{g}" stroke="{g}" stroke-width="6" stroke-linejoin="round">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="{g}" stroke="{c}" stroke-width="1.1">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="none" stroke="{grid}" stroke-width="0.6">'
            f'<line x1="{X(0):.1f}" y1="{band}" x2="{X(0):.1f}" y2="{ry}"></line><line x1="{X(7):.1f}" y1="{band}" x2="{X(7):.1f}" y2="{ry}"></line></g>'
            f'<g fill="none" stroke="{g}" stroke-width="5"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'<g fill="none" stroke="{c}" stroke-width="0.6"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'{under}'
            f'<line x1="{X(0):.1f}" y1="{by - 5}" x2="{X(0):.1f}" y2="{by + 5}" stroke="{live}" stroke-width="{lw}"></line>'
            f'{live_core(bd, SWEEP_DASH + sweep)}'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{ry}" x2="{W}" y2="{ry}"></line>{ticks}</g>'
            f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{c}" stroke-width="9"></line></g></g>'
            f'<g fill="{tk}" style="{lab}">{tl}<text x="{X(10) + 16:.1f}" y="{ry + 20}">MS</text></g>'
            f'<g fill="{c}" style="{lab}"><text x="{X(0) + 9:.1f}" y="{by - 10}">ABOUT 7 MILLISECONDS LATER</text></g>'
            f'<g style="{pen}{ride}"><line x1="0" y1="-5" x2="0" y2="5" stroke="{live}" stroke-width="{lw}"></line></g>'
            f'<circle r="{pen_r}" fill="{live}" style="{pen}{ride}"></circle>'
            f'</svg>'
        )
        names = (f'<div style="display: flex; margin: 12px 0 8px">'
                 f'<div style="width: 210px; flex: none">{L("Livingston, Louisiana", c, 600)}</div>'
                 f'<div>{L("Hanford, Washington", c, 600)}</div></div>')
        return f'{names}<div style="position: relative; width: {W}px; height: {H}px; margin: 0 -{M}px">{field}{draw}</div>'

    def gauge(n, cur):
        """The foot of the pinned block: a double rule whose heavy half is cut into one part
        per step. A part is printed once its step has been reached."""
        segs = "".join(f'<div style="flex: 1 1 0; background-color: {ch if i < cur else "transparent"}"></div>' for i in range(n))
        return (f'<div role="img" aria-label="Step {cur} of {n}" style="display: flex; flex-direction: column; margin-top: 16px">'
                f'<div style="display: flex; gap: 4px; height: 3px">{segs}</div><div style="height: 0.75px; background-color: {ch}; margin-top: 2px"></div></div>')

    def step(i, n, s, current):
        col = c if current else mu
        return (f'<div class="pb-step"{' data-current="true"' if current else ""} style="display: flex; flex-direction: column; gap: 6px">'
                f'<div style="{mono(LAB, color=col, weight=600 if current else 500, ls=0.06)}">Step {i} of {n}</div>'
                f'<p style="margin: 0; {BODY}; color: {col}">{s}</p></div>')

    # ------------------------------------------------------------------ 04 the glossary term
    TERM_BTN = ("font: inherit; letter-spacing: inherit; color: inherit; background: none; border: 0; border-radius: 0; cursor: pointer; "
                "display: inline-block; padding: 10px 4px; margin: -10px -4px; -webkit-appearance: none; appearance: none")
    term_rest = lambda s: (f'<button type="button" aria-expanded="false" style="{TERM_BTN}"><span style="text-decoration: underline dotted {c}; '
                           f'text-decoration-thickness: 1.5px; text-underline-offset: 4px">{s}</span></button>')
    term_open = lambda s: (f'<button type="button" aria-expanded="true" style="{TERM_BTN}"><span style="background-color: {c}; color: {g}; '
                           f'padding: 0 3px; margin: 0 -3px">{s}</span></button>')
    term_pic = lambda inner, extra="": f'<span role="img" aria-label="The word chirp as a glossary term" style="{text(17, lh=1.47)}{extra}">{inner}</span>'

    def term_pop(top):
        return (f'<div role="tooltip" class="pb-term-pop" style="position: absolute; left: 0; right: 0; top: {top}px; height: 100px; box-sizing: border-box; padding-top: 6px; background-color: {g}; '
                f'display: flex; flex-direction: column; animation: press 190ms {PRESS} {at(600)} both">'
                f'{double}'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">{slug("Chirp")}{L("Glossary")}</div>'
                f'<p style="margin: 6px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">A signal that sweeps up in frequency. This one rose from 35 Hz to 250 Hz in about 0.2 seconds.</p>'
                f'<div style="margin-top: auto; height: 0.75px; background-color: {ch}"></div></div>')

    # ------------------------------------------------------------------ 05 the segmented toggle
    def toggle(options, chosen, label, pressed=None, focus=None, pic=False):
        segs = ""
        for i, o in enumerate(options):
            on = i == chosen
            bg, bd, fg = (stamp, stamp, on_stamp) if on else ("transparent", ch, c)
            if i == pressed:
                fg, bd = mu, (mu if day else NM)
            ol = f"; outline: 2px solid {c}; outline-offset: 2px; position: relative; z-index: 1" if i == focus else ""
            inner = (CHECK if on else "") + f'<span style="{text(16, lh=1, weight=500)}">{o}</span>'
            st = (f'flex: 1 1 0; min-width: 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; border: 1px solid {bd}; border-radius: 0; color: {fg}; '
                  f'padding: 0 10px; display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer{"; margin-left: -1px" if i else ""}{ol}')
            segs += (f'<span style="{st}">{inner}</span>' if pic else f'<button type="button" aria-pressed="{"true" if on else "false"}" style="{st}">{inner}</button>')
        acc = f'role="img" aria-label="{label}"' if pic else f'role="group" aria-label="{label}"'
        return f'<div class="pb-toggle" {acc} style="display: flex">{segs}</div>'

    # ------------------------------------------------------------------ 06 a line chart with four series
    def chart_lines(pid):
        PW, top, bot = 246.0, 24.0, 174.0
        X = lambda t: t * PW
        Y = lambda v: bot - v * (bot - top)
        fa = lambda t: 0.10 + 0.82 * t ** 2.2
        fb = lambda t: 0.30 + 0.30 * t + 0.04 * math.sin(3 * t)
        fc = lambda t: 0.66 - 0.28 * t + 0.03 * math.sin(5 * t)
        fd = lambda t: 0.07 + 0.11 * t
        path = lambda f: crom([(X(i / 12), Y(f(i / 12))) for i in range(13)])
        da, db, dc, dd = path(fa), path(fb), path(fc), path(fd)
        H = bot + 26
        sweep = f"; animation: sweep 1500ms linear {at(T_LINE)} both"
        ride = f"; animation: travel 1500ms linear {at(T_LINE)} both"
        pen = f"offset-path: path('{da}'); offset-distance: 100%; offset-rotate: 0deg"
        end = lambda f: Y(f(1.0)) + 3.8
        ya = Y(fa(1.0))
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Specimen with placeholder data: a line chart with four series, each named at its right end. '
            f'One is the live line with a pen point and a carriage under it on the ruler, two are solid lines, one is a thin line that marks an estimate." style="display: block">'
            f'<defs><clipPath id="{pid}rail"><rect x="0" y="{bot - 0.5}" width="{CW}" height="8"></rect></clipPath></defs>'
            f'{gridlines(0, PW, [Y(1 / 3), Y(2 / 3), Y(1.0)], ["[Y1]", "[Y2]", "[Y3] [UNIT]"])}'
            f'<path d="{dd}" fill="none" stroke="{mu}" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round"></path>'
            f'<path d="{dc}" fill="none" stroke="{plate}" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"></path>'
            f'<path d="{db}" fill="none" stroke="{c}" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"></path>'
            f'{live_under_strokes(da, day, g, live, SWEEP_DASH + sweep)}{live_core(da, SWEEP_DASH + sweep)}'
            f'{ruler(0, PW, bot, 12, 6, [(0, "[X1]"), (6, "[X2]"), (12, "[X3]")], "[UNIT]")}'
            f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{c}" stroke-width="9"></line></g></g>'
            f'<g fill="{c}" style="{num}"><text x="{PW + 12}" y="{ya + 1:.1f}">[N]</text></g>'
            f'<g fill="{c}" style="{lab6}"><text x="{PW + 12}" y="{ya + 21:.1f}">[SERIES A]</text></g>'
            f'<g fill="{c}" style="{lab}"><text x="{PW + 12}" y="{end(fb):.1f}">[SERIES B]</text><text x="{PW + 12}" y="{end(fc):.1f}">[SERIES C]</text></g>'
            f'<g fill="{mu}" style="{lab}"><text x="{PW + 12}" y="{end(fd):.1f}">[SERIES D]</text></g>'
            f'{pen_under_marks(day, g, live, pen + ride)}<circle r="{pen_r}" fill="{live}" style="{pen}{ride}"></circle>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ 07 and 08 a scatter, at rest and touched
    SPW = 286.0

    def scatter_points():
        rnd = random.Random(11)
        pts = []
        while len(pts) < 46:
            t = rnd.random()
            x = 0.07 + 0.86 * t
            y = 0.12 + 0.52 * t + rnd.gauss(0, 0.085)
            if 0.05 < y < 0.86 and all(math.hypot((x - px) * SPW, (y - py) * 160) > 9 for px, py in pts):
                pts.append((x, y))
        return pts

    def chart_scatter(pid, touch=False):
        top, bot = 24.0, 184.0
        X = lambda v: v * SPW
        Y = lambda v: bot - v * (bot - top)
        ax = bot + 8
        H = ax + 26
        pts = scatter_points()
        named = {"b": (0.94, 0.23, "[POINT B]"), "c": (0.46, 0.09, "[POINT C]")}
        find = (0.90, 0.94)
        clear = [(x, y) for x, y in pts if all(math.hypot((x - nx) * SPW, (y - ny) * 160) > 14 for nx, ny, _ in named.values())
                 and math.hypot((x - find[0]) * SPW, (y - find[1]) * 160) > 18]
        tp = min(clear, key=lambda p: math.hypot((p[0] - 0.40) * SPW, (p[1] - 0.33) * 160))
        dots = "".join(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="2.1"></circle>' for x, y in clear if not (touch and (x, y) == tp))
        nm = "".join(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="3.2"></circle>' for x, y, _ in named.values())
        bx, by_, bl = named["b"]
        cx_, cy_, cl = named["c"]
        fx, fy = X(find[0]), Y(find[1])
        labels = (f'<g fill="{c}" style="{lab}"><text x="{X(bx) - 9:.1f}" y="{Y(by_) + 3.8:.1f}" text-anchor="end">{bl}</text>'
                  f'<text x="{X(cx_) + 9:.1f}" y="{Y(cy_) + 3.8:.1f}">{cl}</text></g>'
                  f'<g fill="{c}" style="{lab6}"><text x="{fx - 11:.1f}" y="{fy + 3.8:.1f}" text-anchor="end">[THE FINDING]</text></g>')
        fl = f' style="animation: flood 260ms {PRESS} {at(T_SCATTER)} both"' if not touch else ""
        finding = (f'<g{fl}><circle cx="{fx:.1f}" cy="{fy:.1f}" r="{6.5 if day else 5}" fill="{g}"></circle>'
                   + ("" if day else "".join(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{rd:g}" fill="{live}" fill-opacity="{op:g}"></circle>' for rd, op in ((13.0, 0.05), (10.0, 0.14), (6.5, 0.09))))
                   + f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{pen_r}" fill="{live}"></circle></g>')
        touched, tip = "", ""
        if touch:
            tx, ty = X(tp[0]), Y(tp[1])
            touched = (f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx:.1f}" y2="{ax}" stroke="{grid}" stroke-width="0.6"></line>'
                       f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="8" fill="{g}"></circle>'
                       f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="6.5" fill="none" stroke="{c}" stroke-width="0.9"></circle>'
                       f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="2.6" fill="{c}"></circle>'
                       f'<line x1="{tx:.1f}" y1="{ty - 6.5:.1f}" x2="{tx:.1f}" y2="{ty - 14:.1f}" stroke="{c}" stroke-width="0.75"></line>'
                       f'<line x1="{tx:.1f}" y1="{ax}" x2="{tx:.1f}" y2="{ax + 7}" stroke="{c}" stroke-width="2"></line>')
            cell = f"{text(15, lh=1.2)}; color: {g}; text-align: right; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap"
            k = f"{mono(LAB, color=g, ls=0.06)}; white-space: nowrap"
            tip = (f'<div role="status" class="pb-tip" style="position: absolute; left: {tx:.1f}px; top: {ty - 14:.1f}px; transform: translate(-50%, -100%); background-color: {c}; color: {g}; '
                   f'padding: 8px 10px 8px; display: flex; flex-direction: column; gap: 5px; pointer-events: none; animation: tipin 190ms {PRESS} {at(500)} both">'
                   f'<div style="{mono(LAB, color=g, weight=600, ls=0.06)}; white-space: nowrap">[Point name]</div>'
                   f'<div style="display: grid; grid-template-columns: auto auto; column-gap: 14px; row-gap: 1px; align-items: baseline">'
                   f'<span style="{k}">[X]</span><span style="{cell}">[value] <span style="font-style: italic">[unit]</span></span>'
                   f'<span style="{k}">[Y]</span><span style="{cell}">[value] <span style="font-style: italic">[unit]</span></span></div></div>')
        aria = ("Specimen with placeholder data: the scatter with one unnamed point touched. A ring marks the point, a line drops from it to the ruler, and a readout above it gives its name and its two values."
                if touch else "Specimen with placeholder data: a scatter of 46 points. Three are named. One of the three is the live mark.")
        svg = (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="{aria}" style="display: block">'
            f'{gridlines(0, SPW, [Y(1 / 3), Y(2 / 3), Y(1.0)], ["[Y1]", "[Y2]", "[Y3] [UNIT]"])}'
            f'<g fill="{mu}">{dots}</g><g fill="{c}">{nm}</g>{touched}{finding}{labels}'
            f'{ruler(0, SPW, ax, 12, 6, [(0, "[X1]"), (6, "[X2]"), (12, "[X3]")], "[UNIT]")}'
            f'</svg>'
        )
        return f'<div style="position: relative">{svg}{tip}</div>'

    # ------------------------------------------------------------------ 09 a dumbbell
    def chart_dumbbell(pid):
        x0, x1 = 86.0, 290.0
        X = lambda v: x0 + v * (x1 - x0)
        rows = [("[ITEM A]", 0.18, 0.86), ("[ITEM B]", 0.30, 0.66), ("[ITEM C]", 0.12, 0.44), ("[ITEM D]", 0.38, 0.27)]
        y0, dy = 34.0, 30.0
        ax = y0 + dy * (len(rows) - 1) + 24
        H = ax + 26
        out = ""
        for i, (name, a, b) in enumerate(rows):
            y = y0 + i * dy
            first = i == 0
            xa, xb = X(a), X(b)
            lo, hi = min(xa, xb), max(xa, xb)
            out += (f'<text x="0" y="{y + 3.8:.1f}" fill="{c}" style="{lab6 if first else lab}">{name}</text>'
                    f'<line x1="{lo:.1f}" y1="{y}" x2="{hi:.1f}" y2="{y}" stroke="{g}" stroke-width="5"></line>'
                    f'<line x1="{lo:.1f}" y1="{y}" x2="{hi:.1f}" y2="{y}" stroke="{c}" stroke-width="1.4"></line>'
                    f'<circle cx="{xa:.1f}" cy="{y}" r="4" fill="{g}" stroke="{c}" stroke-width="0.9"></circle>')
            if first:
                out += (f'<g style="animation: flood 260ms {PRESS} {at(T_DUMB)} both"><circle cx="{xb:.1f}" cy="{y}" r="{6.5 if day else 5}" fill="{g}"></circle>'
                        f'<line x1="{xb - 6.5:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}" stroke="{c}" stroke-width="1.4"></line>'
                        + ("" if day else "".join(f'<circle cx="{xb:.1f}" cy="{y}" r="{rd:g}" fill="{live}" fill-opacity="{op:g}"></circle>' for rd, op in ((13.0, 0.05), (10.0, 0.14), (6.5, 0.09))))
                        + f'<circle cx="{xb:.1f}" cy="{y}" r="{pen_r + 0.4}" fill="{live}"></circle></g>'
                        f'<g fill="{c}" style="{lab}"><text x="{xa:.1f}" y="{y - 12}" text-anchor="middle">[BEFORE]</text><text x="{xb:.1f}" y="{y - 12}" text-anchor="middle">[AFTER]</text></g>')
            else:
                out += f'<circle cx="{xb:.1f}" cy="{y}" r="4" fill="{c}"></circle>'
        vl = "".join(f'<line x1="{X(v):.1f}" y1="{y0 - 6}" x2="{X(v):.1f}" y2="{ax}"></line>' for v in (0.5, 1.0))
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Specimen with placeholder data: a dumbbell chart of four items. '
            f'Each row joins an open ring, the value before, to a solid dot, the value after. The first row is the finding and its solid dot is the live mark." style="display: block">'
            f'<g stroke="{grid}" stroke-width="0.6" fill="none">{vl}</g>{out}'
            f'{ruler(x0, x1, ax, 10, 5, [(0, "[X1]"), (5, "[X2]"), (10, "[X3]")], "[UNIT]")}'
            f'</svg>'
        )

    # ------------------------------------------------------------------ 10 uncertainty: error bars and a band
    def chart_uncertainty(pid):
        top, bot = 24.0, 174.0
        PW = 286.0
        X = lambda t: 12 + t * (PW - 62)
        Y = lambda v: bot - v * (bot - top)
        mid = lambda t: 0.20 + 0.52 * t ** 1.4
        half = lambda t: 0.05 + 0.13 * t
        ts = [i / 12 for i in range(13)]
        up = [(X(t), Y(mid(t) + half(t))) for t in ts]
        lo = [(X(t), Y(mid(t) - half(t))) for t in ts]
        d_up, d_lo, d_mid = crom(up), crom(list(reversed(lo))), crom([(X(t), Y(mid(t))) for t in ts])
        band = d_up + "L" + d_lo[1:] + "Z"
        obs = [(0.13, 0.31, 0.07), (0.27, 0.22, 0.08), (0.42, 0.45, 0.06), (0.59, 0.40, 0.10), (0.76, 0.62, 0.07), (0.93, 0.84, 0.09)]
        marks = ""
        for i, (t, v, e) in enumerate(obs):
            x, ya, yb, y = X(t), Y(v + e), Y(v - e), Y(v)
            last = i == len(obs) - 1
            wh = (f'<line x1="{x:.1f}" y1="{ya:.1f}" x2="{x:.1f}" y2="{yb:.1f}"></line><line x1="{x - 4:.1f}" y1="{ya:.1f}" x2="{x + 4:.1f}" y2="{ya:.1f}"></line>'
                  f'<line x1="{x - 4:.1f}" y1="{yb:.1f}" x2="{x + 4:.1f}" y2="{yb:.1f}"></line>')
            marks += f'<g stroke="{g}" stroke-width="4.5" fill="none">{wh}</g><g stroke="{c}" stroke-width="0.9" fill="none">{wh}</g>'
            if last:
                marks += (f'<g style="animation: drop 260ms {PRESS} {at(T_UNC)} both"><circle cx="{x:.1f}" cy="{y:.1f}" r="{6.5 if day else 5}" fill="{g}"></circle>'
                          f'<line x1="{x:.1f}" y1="{y - 6.5:.1f}" x2="{x:.1f}" y2="{y + 6.5:.1f}" stroke="{c}" stroke-width="0.9"></line>'
                          + ("" if day else "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rd:g}" fill="{live}" fill-opacity="{op:g}"></circle>' for rd, op in ((13.0, 0.05), (10.0, 0.14), (6.5, 0.09))))
                          + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pen_r}" fill="{live}"></circle></g>'
                          f'<text x="{x - 11:.1f}" y="{ya + 3.8:.1f}" text-anchor="end" fill="{c}" style="{lab6}">[THE FINDING]</text>')
            else:
                marks += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{c}"></circle>'
        H = bot + 8 + 26
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Specimen with placeholder data: six measured points, each with an error bar, over a line with a screened band around it. '
            f'The last point is the live mark." style="display: block">'
            f'<defs>{patterns(pid, scr, tones={"a1": (A1, 0.30)})}</defs>'
            f'{gridlines(0, PW, [Y(1 / 3), Y(2 / 3), Y(1.0)], ["[Y1]", "[Y2]", "[Y3] [UNIT]"])}'
            f'<path d="{band}" fill="{g}"></path><path d="{band}" fill="url(#{pid}a1)"></path>'
            f'<path d="{band}" fill="none" stroke="{c}" stroke-width="0.6" stroke-linejoin="round"></path>'
            f'<path d="{d_mid}" fill="none" stroke="{g}" stroke-width="4.5"></path>'
            f'<path d="{d_mid}" fill="none" stroke="{c}" stroke-width="1.4"></path>'
            f'{marks}'
            f'<rect x="{X(1.0) + 5:.1f}" y="{Y(mid(1.0)) - 8:.1f}" width="58" height="16" fill="{g}"></rect>'
            f'<g fill="{c}" style="{lab}"><text x="{X(1.0) + 9:.1f}" y="{Y(mid(1.0)) + 3.8:.1f}">[MODEL]</text></g>'
            f'{ruler(0, PW, bot + 8, 12, 6, [(0, "[X1]"), (6, "[X2]"), (12, "[X3]")], "[UNIT]")}'
            f'</svg>'
        )

    # ------------------------------------------------------------------ 11 math, mocked in Old Standard TT
    MF = f"font-family: {MATH}; font-style: normal; font-weight: 400; font-variant-numeric: lining-nums"
    mi = lambda s: f'<span style="font-style: italic">{s}</span>'
    op = lambda s, sp="0.2222em": f'<span style="margin: 0 {sp}">{s}</span>'
    rel = lambda s: f'<span style="margin: 0 0.2778em">{s}</span>'
    sun = ('<svg viewBox="0 0 10 10" aria-hidden="true" style="display: inline-block; width: 0.62em; height: 0.62em; vertical-align: -0.24em; margin-left: 0.03em" fill="none" '
           'stroke="currentColor" stroke-width="0.75"><circle cx="5" cy="5" r="3.9"></circle><circle cx="5" cy="5" r="0.85" fill="currentColor" stroke="none"></circle></svg>')
    msun = f'{mi("M")}{sun}'
    qty = lambda n: f'{n}<span style="margin-left: 0.1667em">{msun}</span>'
    inline_math = lambda s, label: f'<span role="math" aria-label="{label}" style="{MF}; font-size: 1.1em; line-height: 0; white-space: nowrap">{s}</span>'
    sup_m = "font-size: 0.7em; line-height: 0; vertical-align: 0.5em"

    # ================================================================== the page
    body = f"""<div style="width: {W}px; box-sizing: border-box; position: relative; background-color: {g}; color: {c}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 0 {M}px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; height: 48px">
<a href="#site" aria-label="Paperboy, to the website" style="margin-left: -10px; padding: 0 10px; min-width: 44px; height: 44px; box-sizing: border-box; display: inline-flex; align-items: center; color: {c}; text-decoration: none">{wordmark()}</a>
</div>
{double}
</header>

<main style="display: flex; flex-direction: column; padding-bottom: 48px">

<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Explainer kit")}{tag_solid("Specimen sheet")}
<div style="margin-left: auto">{L("Night" if not day else "Day")}</div>
</div>
<h1 style="margin: 0; padding: 10px {M}px 0; {disp(44, weight=hw, lh=0.98)}">
<span style="display: block">Eleven patterns,</span>
<span style="display: block; {disp(44, weight=iw, stretch=100 if day else 87.5, lh=0.98, ls=-0.012, italic=True)}">drawn for the kit.</span>
</h1>
<p style="margin: 0; padding: 14px {M}px 0; {BODY}">The parts of an explainer that the first round left undrawn. Facts are from Paper 1. Where a chart needs numbers that paper does not have, its labels are placeholders in brackets and its shapes mean nothing.</p>

<section style="{wrap}">
{section(1, "Top bar on the web", ".pb-topbar", f'<span style="display: block">On the web,</span><span style="display: block; {hit}">the wordmark leads home.</span>',
         "The bar at the top of this sheet is the web form. The wordmark links to the site. There is no back control, because a browser has its own.")}
{strip([(f'<span role="img" aria-label="The wordmark at rest">{wordmark()}</span>', "At rest"),
        (f'<span role="img" aria-label="The wordmark while pressed">{wordmark(mu)}</span>', "Pressed"),
        (f'<span role="img" aria-label="The wordmark with keyboard focus" style="display: inline-flex; align-items: center; box-sizing: border-box; height: 44px; padding: 0 10px; margin-left: 4px; outline: 2px solid {c}; outline-offset: 2px">{wordmark()}</span>', "Focus")], 18)}
</section>

<section style="{wrap}">
{section(2, "Data table", ".pb-data .pb-table", f'<span style="display: block">Every data figure</span><span style="display: block; {hit}">carries its numbers.</span>',
         "A figure drawn from the paper's numbers closes with one row. Opened, it lists every number the chart draws.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 3", "Data, from the paper")}
{figtitle("Where the mass went")}
<div style="margin-top: 14px">{chart_mass("m" + t0)}</div>
{legend([(swatch("j" + t0), "An estimate")])}
{disclosure(False)}
</figure>
{state("The same row, opened")}
{disclosure(True, table_mass())}
</section>

<section style="{wrap}">
{section(3, "Scroll steps", ".pb-steps .pb-step", f'<span style="display: block">One picture stays.</span><span style="display: block; {hit}">The steps scroll past it.</span>',
         "The picture is pinned under the top of the screen. Three to six short steps pass beneath it, and each one changes the picture in one way.")}
{state("Pinned")}
<figure style="margin: 14px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 1", "Illustration, not to scale")}
{steps_plate("s" + t0)}
{gauge(4, 3)}
</figure>
{state("Scrolling under it", 22)}
<div class="pb-steps" style="display: flex; flex-direction: column; gap: 40px; margin-top: 16px">
{step(2, 4, "LIGO has two, one in Livingston, Louisiana and one in Hanford, Washington.", False)}
{step(3, 4, "On September 14, 2015, a wave crossed both. It reached Livingston first, and Hanford about 7 milliseconds later.", True)}
{step(4, 4, "Both recorded the same signal. The event is named GW150914.", False)}
</div>
</section>

<section style="{wrap}">
{section(4, "Glossary term", ".pb-term .pb-term-pop", f'<span style="display: block">A term you can tap,</span><span style="display: block; {hit}">defined in place.</span>')}
{state("At rest", 22)}
<p style="margin: 14px 0 0; {BODY}">Both detectors recorded the same {term_rest("chirp")} on September 14, 2015. It reached Livingston about 7 milliseconds before Hanford.</p>
{state("Open")}
<div style="position: relative; margin-top: 14px">
<p style="margin: 0; {BODY}">Both detectors recorded the same {term_open("chirp")} on September 14, 2015. It reached Livingston about 7 milliseconds before Hanford. Its shape matches two black holes of about 36 and 29 solar masses spiraling into one of about 62 solar masses.</p>
{term_pop(25)}
</div>
{state("The term alone")}
{strip([(term_pic(f'<span style="text-decoration: underline dotted {c}; text-decoration-thickness: 1.5px; text-underline-offset: 4px">chirp</span>'), "At rest"),
        (term_pic(f'<span style="background-color: {c}; color: {g}; padding: 0 3px">chirp</span>'), "Open"),
        (term_pic(f'<span style="text-decoration: underline dotted {c}; text-decoration-thickness: 1.5px; text-underline-offset: 4px; outline: 2px solid {c}; outline-offset: 3px">chirp</span>', "; padding-left: 5px"), "Focus")], 10)}
</section>

<section style="{wrap}">
{section(5, "Segmented toggle", ".pb-toggle", f'<span style="display: block">One switch,</span><span style="display: block; {hit}">two or three positions.</span>',
         "It changes what one figure shows. The chosen position is stamped, the way a rating is.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 3", "Data, from the paper")}
{figtitle("Where the mass went")}
<div style="margin-top: 14px; display: flex; flex-direction: column; gap: 7px">{L("Show the mass")}{toggle(["Before", "After"], 1, "Show the mass")}</div>
<div style="margin-top: 18px">{chart_mass("t" + t0, rows=("after",), t_live=T_TOGGLE)}</div>
{legend([(swatch("u" + t0), "An estimate")])}
</figure>
{state("With three positions")}
<div style="display: flex; flex-direction: column; gap: 7px; margin-top: 14px">
{L("At rest")}{toggle(["Physics", "Biology", "Space"], 0, "Three positions, the first one chosen", pic=True)}
<div style="margin-top: 9px">{L("The middle one pressed")}</div>{toggle(["Physics", "Biology", "Space"], 0, "Three positions, the second one pressed", pressed=1, pic=True)}
<div style="margin-top: 9px">{L("The last one in focus")}</div>{toggle(["Physics", "Biology", "Space"], 0, "Three positions, the third one in keyboard focus", focus=2, pic=True)}
</div>
</section>

<section style="{wrap}">
{section(6, "Line chart", "PB.plot, lines", f'<span style="display: block">Up to four lines,</span><span style="display: block; {hit}">each named at its end.</span>',
         "Lines differ by weight and lightness, never by hue alone. One of them is the finding, and it is the only one that is drawn as you watch.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. [N]", SPEC)}
{figtitle("Four lines, one ruler")}
<div style="margin-top: 16px">{chart_lines("l" + t0)}</div>
{legend([(dot, "The finding"), (key(f'<line x1="0" y1="5" x2="22" y2="5" stroke="{c}" stroke-width="1.4"></line>'), "Measured"),
         (key(f'<line x1="0" y1="5" x2="22" y2="5" stroke="{mu}" stroke-width="0.9"></line>'), "An estimate")], 10)}
</figure>
</section>

<section style="{wrap}">
{section(7, "Scatter", "PB.plot, dots", f'<span style="display: block">Many points,</span><span style="display: block; {hit}">a few of them named.</span>',
         "Most points are small and muted. The ones that matter are larger, in the text color, and named beside the mark. One is the finding.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. [N]", SPEC)}
{figtitle("Many points, three named")}
<div style="margin-top: 14px">{chart_scatter("c" + t0)}</div>
{legend([(dot, "The finding"), (key('<circle cx="5" cy="5" r="3.2" fill="' + c + '"></circle>', 10), "Named"), (key('<circle cx="5" cy="5" r="2.1" fill="' + mu + '"></circle>', 10), "Every other point")], 10)}
</figure>
</section>

<section style="{wrap}">
{section(8, "Touch readout", ".pb-tip", f'<span style="display: block">Touch a mark</span><span style="display: block; {hit}">and it reads out.</span>',
         "A ring closes on the mark, a line drops to the ruler, and a slab above the mark gives its name and its values. Lift the finger and all three go.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. [N]", SPEC)}
<div style="margin-top: 14px">{chart_scatter("d" + t0, touch=True)}</div>
</figure>
</section>

<section style="{wrap}">
{section(9, "Dumbbell", "PB.plot, pairs", f'<span style="display: block">Before and after,</span><span style="display: block; {hit}">one row for each item.</span>',
         "An open ring is the value before. A solid dot is the value after. The row that carries the finding ends in the live mark.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. [N]", SPEC)}
{figtitle("Four pairs of values")}
<div style="margin-top: 14px">{chart_dumbbell("b" + t0)}</div>
{legend([(key(f'<circle cx="5" cy="5" r="4" fill="{g}" stroke="{c}" stroke-width="0.9"></circle>', 10), "Before"), (key(f'<circle cx="5" cy="5" r="4" fill="{c}"></circle>', 10), "After"), (dot, "The finding")], 10)}
</figure>
</section>

<section style="{wrap}">
{section(10, "Uncertainty", "PB.plot, ranges", f'<span style="display: block">What is not known</span><span style="display: block; {hit}">is drawn too.</span>',
         "A measured point carries its error bar. A line that is an estimate carries a screened band. Solid means measured, and screened means a range.")}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. [N]", SPEC)}
{figtitle("Each value, its range")}
<div style="margin-top: 14px">{chart_uncertainty("e" + t0)}</div>
{legend([(dot, "The finding"), (key(f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="3" y1="5" x2="19" y2="5"></line><line x1="3" y1="1.5" x2="3" y2="8.5"></line><line x1="19" y1="1.5" x2="19" y2="8.5"></line></g><circle cx="11" cy="5" r="2.6" fill="{c}"></circle>'), "Measured, with its range"),
         (swatch("v" + t0, ("a1", A1, 0.30)), "Estimated range")], 10)}
</figure>
</section>

<section style="{wrap}">
{section(11, "Math", "KaTeX", f'<span style="display: block">Math sits in the column</span><span style="display: block; {hit}">like a sentence.</span>')}
{P(f'By the time the wave reached Earth, its peak strain was {inline_math("1.0" + op("×") + "10" + f"<span style={chr(34)}{sup_m}{chr(34)}>−21</span>", "1.0 times 10 to the power of negative 21")}. Before and after, the masses add up, each within its error range:', 14)}
<div role="math" aria-label="36 solar masses plus 29 solar masses is about 62 solar masses plus 3 solar masses. Equation 1." style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 20px 0 20px; padding-left: {M}px">
<div style="{MF}; font-size: 18.7px; line-height: 1.2; white-space: nowrap; color: {c}">{qty("36")}{op("+")}{qty("29")}{rel("≈")}{qty("62")}{op("+")}{qty("3")}</div>
<div style="flex: none; white-space: nowrap">{L("Eq. 1")}</div>
</div>
<p style="margin: 0; {BODY}">Here {inline_math(msun, "M sub sun")} is one solar mass. About {inline_math(qty("3"), "3 solar masses")} left as gravitational waves.</p>
{note("Mock. Old Standard TT stands in for KaTeX's own fonts, which this canvas cannot load.", 18)}
</section>

</main>
</div>"""

    css = (
        f"body{{margin:0;background:{g}}}\na{{color:{c}}}\n"
        "@keyframes press{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}\n"
        "@keyframes tipin{from{opacity:0;transform:translate(-50%,-100%) translateY(6px)}to{opacity:1;transform:translate(-50%,-100%)}}\n"
        "@keyframes sweep{from{stroke-dashoffset:1.003}to{stroke-dashoffset:0}}\n"
        "@keyframes travel{from{offset-distance:0%}to{offset-distance:100%}}\n"
        "@keyframes drop{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:none}}\n"
        "@keyframes flood{from{opacity:0}to{opacity:1}}\n"
        + ink_keyframes("inkband", W, 160) + "\n"
        "@media (prefers-reduced-motion: reduce){*{animation:none!important}}\n"
        "summary::-webkit-details-marker{display:none}\n"
        "summary:focus-visible,button:focus-visible,a:focus-visible{outline:2px solid currentColor;outline-offset:2px}"
    )
    heights = json.loads(HEIGHTS.read_text()) if HEIGHTS.exists() else {}
    h = int(heights.get(theme, 7000))
    out = OUT / f"Explainer-Patterns-{theme.capitalize()}.dc.html"
    out.write_text(page(f"Explainer patterns, {theme}", css, body, W, h))
    print("wrote", out, out.stat().st_size, "height", h)


if __name__ == "__main__":
    for th in (sys.argv[1:] or ["day", "night"]):
        build(th)
