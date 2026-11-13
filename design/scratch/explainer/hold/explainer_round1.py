"""The explainer page for Paper 1 (GW150914), phone width, First Light system.

  python3 explainer.py     writes canvas/project/Explainer-Day.dc.html (390 wide, full page)
                           and canvas/project/Explainer-Night.dc.html (the first 390 by 1800, night)

It reuses the locked drawing code: tokens, type helpers, line screens and the chirp from
scratch/engraved/lib.py, and the locked hero plate from scratch/director/lock_proof.py.
Facts come from design/CONTENT.md only. Tick numbering is ordinary axis numbering.
"""
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
sys.path.insert(0, str(HERE.parent / "director"))
from lib import *  # noqa: E402,F403
import lock_proof as LP  # noqa: E402

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
LAB = 10.5
W, M = 390, 20
CW = W - 2 * M
OUT = pathlib.Path(os.environ.get("PB_OUT") or HERE.parents[1] / "canvas" / "project")
NIGHT_H = 1800

BACK = ('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="square" aria-hidden="true"><path d="M17 10H4M9 5l-5 5 5 5"></path></svg>')


def chirp_y(t, amp, tm=0.78):
    """Height of the lib.py chirp at t, for parking a pen point part way along it."""
    c1, c4 = 2.0, 7.0
    if t <= tm:
        u = t / tm
        return -amp * (0.06 + 0.94 * u ** 3) * math.sin(2 * math.pi * (c1 * u + c4 * u ** 4))
    fr = (c1 + 4 * c4) / tm * (1 - tm)
    u = (t - tm) / (1 - tm)
    return -amp * math.exp(-6.5 * u) * math.sin(2 * math.pi * (c1 + c4) + 2 * math.pi * fr * u)


def tangents(c1, c2):
    """The two outer tangent segments between circles (x, y, r)."""
    (x1, y1, r1), (x2, y2, r2) = c1, c2
    d = math.hypot(x2 - x1, y2 - y1)
    base = math.atan2(y2 - y1, x2 - x1)
    al = math.acos((r1 - r2) / d)
    out = []
    for s in (1, -1):
        a = base + s * al
        out.append((x1 + r1 * math.cos(a), y1 + r1 * math.sin(a), x2 + r2 * math.cos(a), y2 + r2 * math.sin(a)))
    return out


def build(theme):
    day = theme == "day"
    g = STOCK if day else NG
    c = INK if day else NT
    mu = MUTED if day else NM
    plate = BLUE if day else NBLUE
    live = LIVE if day else AMBER
    grid = MUTED if day else NS
    scr = c if day else NM            # the screen that marks an estimate or a range
    hw = 800 if day else 900
    iw = 300 if day else 400
    lw = 2 if day else 1.75           # live beam weight in figures
    t0 = theme[0]

    L = lambda t, col=None, w=500: f'<div style="{mono(LAB, color=col or mu, weight=w, ls=0.06)}">{t}</div>'
    slug = lambda t: f'<div style="{mono(LAB, color=c, weight=600, ls=0.06)}">{t}</div>'
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"
    lab6 = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 600; letter-spacing: 0.06em"
    num = f"font-family: {DISP}; font-stretch: 62.5%; font-weight: {hw}; font-size: 25px; font-variant-numeric: lining-nums"
    hair = f'<div style="height: 0.75px; background-color: {c}"></div>'
    double = f'<div style="height: 3px; background-color: {c}"></div><div style="height: 0.75px; background-color: {c}; margin-top: 2px"></div>'
    it = lambda size, lh=1.06, st=100: disp(size, weight=iw, stretch=st, lh=lh, ls=-0.012, italic=True)
    P = lambda t, mt=12: f'<p style="margin: {mt}px 0 0; {text(17, lh=1.47)}; text-wrap: pretty">{t}</p>'
    note = lambda t, mt=10: f'<p style="margin: {mt}px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">{t}</p>'
    unit = lambda t: f'<span style="{text(15, lh=1, italic=True)}; margin-left: 6px">{t}</span>'
    fighead = lambda a, b: (f'{hair}<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">'
                            f'{slug(a)}{L(b)}</div>')

    def tag_outline(t):
        return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'

    def tag_solid(t):
        return f'<span style="{mono(10, color=g, weight=600, ls=0.06)}; background-color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'

    def btn_outline(label):
        return (f'<a href="#paper" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
                f'padding: 0 14px 0 16px; border: 1px solid {c}; color: {c}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{OUTARROW.replace("11", "15", 2)}</a>')

    def section(slug_t, head):
        return (f'<div style="margin-top: 40px">{double}</div><div style="margin-top: 12px">{slug(slug_t)}</div>'
                f'<h2 style="margin: 8px 0 0; {disp(30, weight=hw, lh=1.02)}">{head}</h2>')

    def swatch(pid):
        return (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><defs>{patterns(pid, scr, tones={"a2": (A1, 0.46)})}</defs>'
                f'<rect width="22" height="10" fill="url(#{pid}a2)"></rect><rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{c}" stroke-width="0.9"></rect></svg>')

    def legend(items):
        return (f'<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; {mono(LAB, color=mu, ls=0.06)}">'
                + "".join(f'<span style="display: inline-flex; align-items: center; gap: 6px">{k}{t}</span>' for k, t in items) + '</div>')

    dot = f'<span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: {live}"></span>'

    def beam(xa, xb, y, col, w, cap=5):
        return (f'<line x1="{xa:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}" stroke="{col}" stroke-width="{w}"></line>'
                f'<line x1="{xa:.1f}" y1="{y - cap}" x2="{xa:.1f}" y2="{y + cap}" stroke="{col}" stroke-width="{w}"></line>'
                f'<line x1="{xb:.1f}" y1="{y - cap}" x2="{xb:.1f}" y2="{y + cap}" stroke="{col}" stroke-width="{w}"></line>')

    # ------------------------------------------------------------------ Fig. 1, the two detectors
    def ifo(pid):
        """A full-bleed band: the wave as an engraved field in plate ink, the two detectors as a
        plotter drawing over it, and under the band, on open ground, the gap between arrivals."""
        s, x0 = 30.0, 26.0
        X = lambda v: x0 + v * s
        a = 112                      # arm length on paper
        band = 160
        cy = 140                     # corner stations
        by, ry = band + 32, band + 62
        H = ry + 26
        tube = 5

        def det(cx):
            return (
                f'<rect x="{cx - tube / 2:.1f}" y="{cy - 6 - a}" width="{tube}" height="{a}"></rect>'
                f'<rect x="{cx - 4:.1f}" y="{cy - 6 - a - 8}" width="8" height="8"></rect>'
                f'<rect x="{cx + 6:.1f}" y="{cy - tube / 2}" width="{a}" height="{tube}"></rect>'
                f'<rect x="{cx + 6 + a:.1f}" y="{cy - 4}" width="8" height="8"></rect>'
                f'<rect x="{cx - 6:.1f}" y="{cy - 6}" width="12" height="12"></rect>'
            )

        wdefs, wmarks = wavefield(pid, -150.0, 250.0, W, band, plate, rot=18, rmin=150.0, rmax=640.0)
        if not day:
            wmarks = wmarks.replace(f'stroke="{plate}" stroke-width="0.5"', f'stroke="{plate}" stroke-width="0.6" stroke-opacity="0.55"', 1)
        field = (f'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block; position: absolute; left: 0; top: 0">'
                 f'<defs>{wdefs}</defs>{wmarks}</svg>')
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ry}" x2="{X(v):.1f}" y2="{ry + (7 if v % 5 == 0 else 4)}"></line>' for v in range(0, 11))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="middle">{v}</text>' for v in (0, 5, 10))
        draw = (
            f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Illustration, not to scale: a wave crossing two L-shaped detectors, each with two 4 kilometer arms. '
            f'It reaches Livingston, Louisiana first and Hanford, Washington about 7 milliseconds later." style="display: block; position: absolute; left: 0; top: 0">'
            f'<g fill="{g}" stroke="{g}" stroke-width="6" stroke-linejoin="round">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="{g}" stroke="{c}" stroke-width="1.2">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="none" stroke="{grid}" stroke-width="0.6">'
            f'<line x1="{X(0):.1f}" y1="{band}" x2="{X(0):.1f}" y2="{ry}"></line><line x1="{X(7):.1f}" y1="{band}" x2="{X(7):.1f}" y2="{ry}"></line></g>'
            f'<g fill="none" stroke="{g}" stroke-width="5"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'<g fill="none" stroke="{c}" stroke-width="0.6"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'<line x1="{X(0):.1f}" y1="{by}" x2="{X(7):.1f}" y2="{by}" stroke="{g}" stroke-width="7"></line>{beam(X(0), X(7), by, live, lw)}'
            f'<circle cx="{X(7):.1f}" cy="{by}" r="3.6" fill="{live}"></circle>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{ry}" x2="{W}" y2="{ry}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab}">{tl}<text x="{X(10) + 16:.1f}" y="{ry + 20}">MS</text>'
            f'<text x="{X(0) + 9:.1f}" y="{by - 9}">ABOUT 7 MILLISECONDS LATER</text></g>'
            f'</svg>'
        )
        names = (
            f'<div style="display: flex; margin-bottom: 8px">'
            f'<div style="width: 210px; flex: none; display: flex; flex-direction: column; gap: 2px">{L("Livingston, Louisiana", c, 600)}{L("Two arms, 4 km each")}</div>'
            f'<div style="display: flex; flex-direction: column; gap: 2px">{L("Hanford, Washington", c, 600)}{L("Two arms, 4 km each")}</div></div>'
        )
        return (f'{names}<div style="position: relative; width: {W}px; height: {H}px; margin: 0 -{M}px">{field}{draw}</div>')

    # ------------------------------------------------------------------ Fig. 2, the distance and its range
    def range_bar(pid):
        s = (CW - 62) / 600
        X = lambda v: v * s
        ax = 44
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ax}" x2="{X(v):.1f}" y2="{ax + (7 if v % 200 == 0 else 4)}"></line>' for v in range(0, 601, 50))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 200, 400, 600))
        return (
            f'<svg viewBox="0 0 {CW} 70" width="{CW}" height="70" role="img" aria-label="Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570, on a scale from 0 to 600" style="display: block">'
            f'<defs>{patterns(pid, scr, tones={"a2": (A1, 0.46)})}</defs>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="url(#{pid}a2)"></rect>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{g}" stroke-width="7"></line>'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{live}" stroke-width="{lw}"></line>'
            f'<circle cx="{X(410):.1f}" cy="9" r="3.6" fill="{live}"></circle>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{X(600):.1f}" y2="{ax}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab}">{tl}<text x="{CW}" y="{ax + 20}" text-anchor="end">Mpc</text>'
            f'<text x="{X(230):.1f}" y="11" text-anchor="middle">230</text><text x="{X(570):.1f}" y="11" text-anchor="middle">570</text></g>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ Fig. 3, where the mass went
    def chart_mass(pid):
        s = 4.0
        X = lambda v: 0.5 + v * s
        bh = 20
        l1, b1 = 11, 48           # row label baseline, bar top
        l2, b2 = 96, 133
        axis = b2 + bh + 26
        H = axis + 26
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (7 if v % 10 == 0 else 4)}"></line>' for v in range(0, 71, 5))
        tl = "".join(f'<text x="{X(v):.1f}" y="{axis + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 20, 40, 60))
        drops = "".join(f'<line x1="{X(v):.1f}" y1="{b2 + bh}" x2="{X(v):.1f}" y2="{axis}"></line>' for v in (62, 65))

        def bar(v0, v1, y, fills):
            r = "".join(f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="{f}"></rect>' for f in fills)
            return r + f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'

        defs = patterns(pid, scr, tones={"a2": (A1, 0.46), "b2": (A2, 0.44)})
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" '
            f'aria-label="Data from the paper, in solar masses. Before: two black holes of about 36 and 29. After: one black hole of about 62, and about 3 that left as gravitational waves." style="display: block">'
            f'<defs>{defs}</defs>'
            f'<g stroke="{grid}" stroke-width="0.6" fill="none">{drops}</g>'
            f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
            f'{bar(0, 62, b2, [f"url(#{pid}a2)", f"url(#{pid}b2)"])}'
            f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="{live}"></rect>'
            f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab6}"><text x="0" y="{l1}">BEFORE</text><text x="0" y="{l2}">AFTER</text></g>'
            f'<g fill="{mu}" style="{lab}"><text x="50" y="{l1}">TWO BLACK HOLES</text><text x="43" y="{l2}">ONE BLACK HOLE, AND WAVES</text></g>'
            f'<g fill="{c}" style="{lab}">{tl}<text x="{CW}" y="{axis + 20}" text-anchor="end">SOLAR MASSES</text>'
            f'<text x="{X(65) + 9:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 9:.1f}" y="{b2 + 20}">WAVES</text></g>'
            f'<g fill="{c}" style="{num}">'
            f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
            f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text><text x="{X(63.5):.1f}" y="{b2 - 7}" text-anchor="middle">3</text>'
            f'</g></svg>'
        )

    # ------------------------------------------------------------------ For scale: the change in arm length against a proton
    def analogy(pid):
        """An arm, a detail of its end, and inside the detail a proton with its width ruled off.
        The change in arm length is the live mark: a width too small to rule, so it is one line."""
        ay = 12
        big = (175.0, 172.0, 108.0)
        small = (343.0, float(ay), 6.0)
        px, py, pr = 199.0, 158.0, 52.0       # the proton
        yb = 238                               # both widths sit on this line
        mx = 110.0                             # the change in arm length
        H = 286
        tan = "".join(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{d:.1f}" y2="{e:.1f}"></line>' for a, b, d, e in tangents(small, big))
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Illustration, not to scale: one 4 kilometer arm, and a detail of its end. '
            f'Inside the detail, the change in arm length is drawn far smaller than a proton." style="display: block">'
            f'<defs>{patterns(pid, plate, tones={"a1": (A1, 0.3)})}</defs>'
            f'<g fill="none" stroke="{grid}" stroke-width="0.6">{tan}'
            f'<circle cx="{small[0]}" cy="{small[1]}" r="{small[2]}"></circle><circle cx="{big[0]}" cy="{big[1]}" r="{big[2]}"></circle>'
            f'<line x1="{px - pr:.1f}" y1="{py}" x2="{px - pr:.1f}" y2="{yb}"></line><line x1="{px + pr:.1f}" y1="{py}" x2="{px + pr:.1f}" y2="{yb}"></line></g>'
            f'{beam(1, 349, ay, c, 1.4)}'
            f'<circle cx="{px}" cy="{py}" r="{pr}" fill="url(#{pid}a1)"></circle>'
            f'<circle cx="{px}" cy="{py}" r="{pr}" fill="none" stroke="{c}" stroke-width="0.9"></circle>'
            f'{beam(px - pr, px + pr, yb, c, 1.4)}'
            f'<line x1="{mx}" y1="{yb - 20}" x2="{mx}" y2="{yb + 5}" stroke="{g}" stroke-width="7"></line>'
            f'<line x1="{mx}" y1="{yb - 20}" x2="{mx}" y2="{yb + 5}" stroke="{live}" stroke-width="{lw}"></line>'
            f'<circle cx="{mx}" cy="{yb - 20}" r="3.6" fill="{live}"></circle>'
            f'<line x1="74" y1="{yb - 8}" x2="{mx - 8}" y2="{yb - 8}" fill="none" stroke="{c}" stroke-width="0.75"></line>'
            f'<g fill="{c}" style="{lab}"><text x="1" y="{ay + 21}">ONE ARM, 4 KM</text>'
            f'<text x="{px}" y="{py - pr - 10}" text-anchor="middle">A PROTON</text>'
            f'<text x="1" y="{yb - 11}">CHANGE IN</text><text x="1" y="{yb + 2}">ARM LENGTH</text></g>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ Try it: one slider, three states
    def slider_state(pid, t, state, readout, value_text, real=False):
        x0, w, amp = 0.0, 334.0, 22
        y0, ruler = 30, 68
        d, xm, crest = chirp(x0, y0, w, amp)
        xh, yh = x0 + w * t, y0 + chirp_y(t, amp)
        H = ruler + 26
        step = (xm - x0) / 10
        ticks, x, i = [], x0, 0
        while x <= W - M:
            ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
            x += step
            i += 1
        acc = 'aria-hidden="true"' if real else f'role="img" aria-label="The same slider with the carriage at {value_text}"'
        carriage = "" if real else f'<rect x="{xh - 6:.2f}" y="{ruler - 13}" width="12" height="22" fill="{c}"></rect>'
        halo = "" if day else f'<path d="{d}" fill="none" stroke="{live}" stroke-width="7" stroke-opacity="0.22" stroke-linejoin="round" stroke-linecap="round"></path>'
        pen = (f'<circle cx="{xh:.2f}" cy="{yh:.2f}" r="6.5" fill="{g}"></circle>' if day else
               f'<circle cx="{xh:.2f}" cy="{yh:.2f}" r="8.5" fill="{g}"></circle><circle cx="{xh:.2f}" cy="{yh:.2f}" r="8.5" fill="{live}" fill-opacity="0.24"></circle>')
        svg = (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" {acc} style="display: block; overflow: visible">'
            f'<defs><clipPath id="{pid}c"><rect x="0" y="0" width="{xh:.2f}" height="{ruler - 6}"></rect></clipPath></defs>'
            f'<path d="{d}" fill="none" stroke="{grid}" stroke-width="0.75" stroke-linejoin="round" stroke-linecap="round"></path>'
            f'<g clip-path="url(#{pid}c)"><path d="{d}" fill="none" stroke="{g}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"></path>{halo}'
            f'<path d="{d}" fill="none" stroke="{live}" stroke-width="{1.9 if day else 1.6}" stroke-linejoin="round" stroke-linecap="round"></path></g>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{x0}" y1="{ruler}" x2="{W - M}" y2="{ruler}"></line>{"".join(ticks)}</g>'
            f'<g fill="{c}" style="{lab}"><text x="{x0}" y="{ruler + 20}">0</text><text x="{(x0 + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
            f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text></g>'
            f'{carriage}{pen}<circle cx="{xh:.2f}" cy="{yh:.2f}" r="{3.6 if day else 3.4}" fill="{live}"></circle>'
            f'</svg>'
        )
        inp = "" if not real else (f'<input type="range" class="pb-carriage" min="0" max="1000" value="{round(t * 1000)}" aria-label="Time in the signal" aria-valuetext="{value_text}" '
               f'style="position: absolute; left: {x0 - 6}px; top: {ruler - 24}px; width: {w + 12}px; height: 44px; margin: 0; padding: 0; color: {c}">')
        return (
            f'<div style="display: flex; flex-direction: column; gap: 2px">'
            f'<div style="display: flex; align-items: baseline; justify-content: space-between">{L(state)}<div style="{disp(30, weight=hw, lh=1)}; font-variant-numeric: lining-nums">{readout}</div></div>'
            f'<div style="position: relative; width: {CW}px; height: {H}px">{svg}{inp}</div>'
            f'</div>'
        )

    def row(label, value, n=""):
        nn = f'<div style="{text(15, lh=1.4, italic=True)}; text-wrap: pretty">{n}</div>' if n else ""
        return (f'<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {c}">'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
                f'<div style="{mono(LAB, color=mu, ls=0.06)}; flex: none">{label}</div>'
                f'<div style="{disp(30, weight=hw, lh=1)}; font-variant-numeric: lining-nums; text-align: right">{value}</div></div>{nn}</div>')

    group = lambda t: f'<div style="padding: 9px 0 8px; border-top: 0.75px solid {c}">{slug(t)}</div>'

    # second voice inside a 30 px head: D4 by day, D5 at width 87.5 by night (SYSTEM 2.1)
    hit = it(30, 1.02, 100 if day else 87.5)
    press = lambda i: f"display: block; animation: press 190ms {PRESS} {at(i * 50)} both"
    h_it = disp(44, weight=iw, stretch=100 if day else 87.5, lh=0.98, ls=-0.012, italic=True)
    feed = "App-Feed-Day.dc.html" if day else "App-Feed-Night.dc.html"
    wrap = f"display: flex; flex-direction: column; padding: 0 {M}px"
    full_night = bool(os.environ.get("PB_NIGHT_FULL"))
    root_extra = "" if day or full_night else f" height: {NIGHT_H}px; overflow: hidden;"

    body = f"""<div style="width: {W}px;{root_extra} box-sizing: border-box; position: relative; background-color: {g}; color: {c}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 0 {M}px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; justify-content: space-between; height: 48px">
<a href="{feed}" style="margin-left: -12px; padding: 0 12px; min-width: 44px; height: 44px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 8px; color: {c}; text-decoration: none; {mono(LAB, color=c, weight=600, ls=0.06)}">{BACK}<span>Feed</span></a>
<div style="{disp(22, weight=hw, lh=1)}; padding-bottom: 3px">Paper<span style="{disp(22, weight=400, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: {live}; margin-left: 2px"></span></div>
</div>
{double}
</header>

<main style="display: flex; flex-direction: column">
<article style="display: flex; flex-direction: column">

<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Physics")}{tag_solid("Peer-reviewed")}
{LP.source("Physical Review Letters", c)}
</div>
<h1 style="margin: 0; padding: 10px {M}px 0; {disp(44, weight=hw, lh=0.98)}">
<span style="{press(0)}">Two black holes</span>
<span style="{press(1)}">merged. <span style="{h_it}">Earth felt</span></span>
<span style="{press(2)}; {h_it}">space stretch.</span>
</h1>
{LP.plate("ex" + t0, theme)}
<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px {M}px 0">
<div style="display: flex; flex-direction: column; gap: 3px">
<div style="{disp(44, weight=hw, lh=1)}; font-variant-numeric: lining-nums">1.0 × 10<sup style="{SUP}">−21</sup></div>
{L("Peak strain. Pitch 35 to 250 Hz")}
</div>
<div style="text-align: right; {mono(LAB, color=mu, ls=0.06)}; line-height: 1.4">Plate 1<br>Illustration,<br>not to scale</div>
</div>
<p style="margin: 0; padding: 14px {M}px 0; {text(17, lh=1.47)}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>

<section style="{wrap}; padding-top: 40px; padding-bottom: 40px">
{slug("Key idea")}
<p style="margin: 12px 0 0; {it(30)}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</section>

<section style="{wrap}">
<div>{double}</div><div style="margin-top: 12px">{slug("The question")}</div>
<h2 style="margin: 8px 0 0; {disp(30, weight=hw, lh=1.02)}"><span style="display: block">Can a machine on Earth</span><span style="display: block; {hit}">feel space stretch?</span></h2>
{P("A gravitational wave is a ripple in spacetime. Before this paper, no one had detected one directly.", 14)}
{P("When a wave passes, lengths change. Here a 4 km arm changed by far less than the width of a proton. Could any instrument register something that small?")}
</section>

<section style="{wrap}">
{section("What they did", f'<span style="display: block">Two detectors,</span><span style="display: block; white-space: nowrap; {hit}">each an L with 4 km arms.</span>')}
<figure style="margin: 20px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 1", "Illustration, not to scale")}
<div style="margin-top: 14px">{ifo("i" + t0)}</div>
</figure>
{P("LIGO has two detectors, one in Hanford, Washington and one in Livingston, Louisiana. Each is an L-shaped laser interferometer.", 20)}
{P("On September 14, 2015, at 09:50:45 UTC, both recorded the same signal. It reached Livingston about 7 milliseconds before Hanford. The event is named GW150914.")}
</section>

<section style="{wrap}">
{section("What they found", f'<span style="display: block">One chirp,</span><span style="display: block; white-space: nowrap; {hit}">a fifth of a second long.</span>')}
{P("The signal swept up in frequency from 35 Hz to 250 Hz in about 0.2 seconds. A rising sweep like that is called a chirp.", 14)}
{P("Its shape matches two black holes spiraling into one, about 410 megaparsecs away, roughly 1.3 billion light years.†")}
<div style="width: 64px; height: 0.75px; background-color: {c}; margin-top: 16px"></div>
{note("† The mass and distance values carry wide error ranges. The distance, for example, is 410 megaparsecs with a range of roughly 230 to 570.")}

<figure style="margin: 28px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 2", "Data, from the paper")}
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div style="{disp(72, weight=hw, lh=0.86)}; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px">{L("Megaparsecs away", c, 600)}<div style="{text(15, lh=1.3, italic=True)}">roughly 1.3 billion light years</div></div>
</div>
<div style="margin-top: 14px">{range_bar("r" + t0)}</div>
{legend([(dot, "Reported value"), (swatch("k" + t0), "Range")])}
</figure>

{P("The two black holes had about 36 and 29 solar masses. The one they formed has about 62. About 3 solar masses of energy left as gravitational waves.", 28)}

<figure style="margin: 28px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 3", "Data, from the paper")}
<div style="margin-top: 10px; {disp(30, weight=hw, lh=1)}">Where the mass went</div>
<div style="margin-top: 14px">{chart_mass("m" + t0)}</div>
{legend([(swatch("j" + t0), "An estimate"), (dot, "Left as waves")])}
</figure>

{P(f'By the time the wave reached Earth, its peak strain was 1.0 × 10<sup style="{SUP}">−21</sup>.', 28)}

<figure style="margin: 28px 0 0; display: flex; flex-direction: column">
{fighead("For scale", "Illustration, not to scale")}
<div style="margin-top: 14px">{analogy("a" + t0)}</div>
{note("That strain is a change in arm length far smaller than a proton.", 8)}
</figure>

<figure style="margin: 40px 0 0; display: flex; flex-direction: column">
{fighead("Try it", "Illustration, not to scale")}
<div style="margin-top: 10px; {disp(30, weight=hw, lh=1)}">Play the chirp by hand</div>
<div style="display: flex; flex-direction: column; gap: 14px; margin-top: 14px">
{slider_state("s1" + t0, 0.0, "At rest", "35" + unit("Hz"), "0 seconds, 35 hertz", real=True)}
{slider_state("s2" + t0, 0.624, "Dragging", f'<span style="{text(15, lh=1, italic=True)}">pitch rising</span>', "between 0.1 and 0.2 seconds, pitch rising")}
{slider_state("s3" + t0, 0.78, "At 0.2 seconds", "250" + unit("Hz"), "0.2 seconds, 250 hertz")}
</div>
{note("Drag the carriage along the ruler to move through the signal. Shown here in three positions.", 10)}
</figure>
</section>

<section style="{wrap}; margin-top: 40px">
{double}
<h2 style="margin: 12px 0 12px; {disp(30, weight=hw, lh=1)}">How sure <span style="{hit}">is this?</span></h2>
{group("Strengths")}
{row("Review", tag_solid("Peer-reviewed"), "Physical Review Letters, February 11, 2016.")}
{row("Significance", "&gt; 5.1" + unit("sigma"), "A false alarm this strong is expected less than once in 203,000 years.")}
{row("Detectors", "2" + unit("sites"), "Hanford and Livingston both recorded it, about 7 milliseconds apart.")}
{group("Limits")}
{row("Distance", "410" + unit("megaparsecs"), "With a range of roughly 230 to 570. Drawn in Fig. 2.")}
{row("Masses", "36, 29, 62" + unit("solar masses"), "All three are estimates with wide error ranges.")}
{group("Open question")}
{row("Sky position", "600" + unit("square degrees"), "Where it came from was known only to within about this much sky.")}
<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 0 0; border-top: 0.75px solid {c}">
{L("This explainer")}
<p style="margin: 0; {text(17, lh=1.47)}; text-wrap: pretty">Machine written, and it can be wrong. Check it against the paper.</p>
</div>
</section>

<section style="{wrap}">
{section("Why it matters", f'Two firsts <span style="{hit}">in one signal.</span>')}
{P("Before this paper, gravitational waves had never been detected directly, and no one had observed two black holes merging. One signal, a fifth of a second long, did both.", 14)}
</section>

<footer style="{wrap}; margin-top: 40px; padding-bottom: 40px">
{double}
<div style="margin-top: 12px">{slug("Source")}</div>
<p style="margin: 8px 0 0; {text(17, lh=1.4, italic=True)}; text-wrap: pretty">Observation of Gravitational Waves from a Binary Black Hole Merger</p>
<p style="margin: 6px 0 0; {text(15, lh=1.4)}; color: {mu}; text-wrap: pretty">B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)</p>
<div style="margin-top: 8px; display: flex; flex-direction: column; gap: 3px">{L("Physical Review Letters 116, 061102")}{L("February 11, 2016. Peer-reviewed. CC BY 3.0")}</div>
<div style="margin-top: 14px">{btn_outline("Read the paper")}</div>
{note("This page was written by a machine and can be wrong. The paper is the source.", 14)}
</footer>

</article>
</main>
</div>"""

    css = (
        f"body{{margin:0;background:{g}}}\na{{color:{c}}}\n" + KEYFRAMES + "\n"
        "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
        "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
        + ink_keyframes("inkproof", W, LP.BAND) + "\n"
        ".pb-carriage{-webkit-appearance:none;appearance:none;background:transparent;border-radius:0;cursor:ew-resize}\n"
        ".pb-carriage::-webkit-slider-runnable-track{-webkit-appearance:none;background:transparent;height:44px}\n"
        ".pb-carriage::-webkit-slider-thumb{-webkit-appearance:none;width:12px;height:22px;margin-top:11px;background:currentColor;border:0;border-radius:0}\n"
        ".pb-carriage::-moz-range-track{background:transparent;height:44px}\n"
        ".pb-carriage::-moz-range-thumb{width:12px;height:22px;background:currentColor;border:0;border-radius:0}\n"
        ".pb-carriage:focus-visible{outline:2px solid currentColor;outline-offset:2px}"
    )
    out = (HERE / "Explainer-Night-Full.dc.html") if (not day and full_night) else OUT / f"Explainer-{theme.capitalize()}.dc.html"
    h = int(os.environ.get("PB_H", "5464")) if day else NIGHT_H
    out.write_text(page(f"Explainer, Paper 1, {theme}", css, body, W, h))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build("day")
    build("night")
