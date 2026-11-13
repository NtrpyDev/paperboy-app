"""The explainer page for Paper 1 (GW150914), phone width, First Light system. Round 2,
after design/CRITIQUE.md.

  python3 explainer.py [day|night]   writes canvas/project/Explainer-Day.dc.html and
                                     canvas/project/Explainer-Night.dc.html, both 390 wide and the whole page
  python3 run.py TAG                 builds, renders with the screenshot tool, sets the declared heights, slices
  python3 frames.py ...              exact animation frames (every animation paused at one clock time)
  python3 audit.py                   touch targets, type sizes, forbidden marks, numbers against CONTENT.md

Plate 1 is the feed's plate1() (scratch/feed/plates.py), which calls the shared generator
gw_print() in scratch/engraved/lib.py. The chirp, the traps, the night halo, and the drawn
multiplication and greater-than signs also come from lib.py, so every board draws them one way.
Facts come from design/CONTENT.md only. Tick numbering is ordinary axis numbering. No path data
is hand-edited.

  PB_DELAY=ms   pushes every animation back
  PB_OUT=dir    writes somewhere else
  PB_NCORE=px   night core weight of the live line, for comparisons
"""
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
sys.path.insert(0, str(HERE.parent / "feed"))
from lib import (INK, STOCK, MUTED, LIVE, NG, NT, NM, NS, AMBER, DISP, TEXT, MONO, A1, A2, PRESS,  # noqa: E402
                 mono, disp, text, patterns, page, ink_keyframes, at, OUTARROW, SWEEP_DASH,
                 chirp, gw_print, live_under_strokes, pen_under_marks, sign_times, sign_gt)
import plates as FP  # noqa: E402  the feed's Plate 1: one generator for every board

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
LAB = 10.5
W, M = 390, 20
CW = W - 2 * M
BAND = FP.BAND
OUT = pathlib.Path(os.environ.get("PB_OUT") or HERE.parents[1] / "canvas" / "project")
HEIGHTS = HERE / "heights.json"
N_CORE = float(os.environ.get("PB_NCORE", "1.9"))     # night core of the live line. lib and plates draw 1.6; CRITIQUE, Explainer Night fix 2, asks for 1.9

# The inspiral part of lib.chirp(), needed here to place a pen point part way along the line
# and to swell the field of the control where its crests are. Same constants as lib.chirp().
TM, C1, C4 = 0.78, 2.0, 7.0


def chirp_env(t):
    u = min(1.0, t / TM)
    return 0.06 + 0.94 * u ** 3


def chirp_phase(t):
    u = min(1.0, t / TM)
    return 2 * math.pi * (C1 * u + C4 * u ** 4)


# when each figure's live mark draws in on the artboard (ms). In the app each runs once,
# when its figure scrolls into view.
T_FIG1, T_FIG2, T_FIG3, T_SCALE, T_TRY = 2700, 3850, 4250, 4650, 4950

BACK = ('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="square" aria-hidden="true"><path d="M17 10H4M9 5l-5 5 5 5"></path></svg>')


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
    g, c, mu = (STOCK, INK, MUTED) if day else (NG, NT, NM)
    ch = c if day else NM             # rules, outlines, axes: one step under text at night
    tk = c if day else NM             # tick labels, as in the feed's plates
    plate, live, grid = (BLUE, LIVE, MUTED) if day else (NBLUE, AMBER, NS)
    core_w = 1.9 if day else N_CORE
    scr = c if day else NM            # the screen that marks an estimate or a range
    hw = 800 if day else 900
    iw = 300 if day else 400
    lw = 2 if day else 1.9            # live beam weight in figures
    t0 = theme[0]

    L = lambda s, col=None, w=500: f'<div style="{mono(LAB, color=col or mu, weight=w, ls=0.06)}">{s}</div>'
    slug = lambda s: f'<div style="{mono(LAB, color=c, weight=600, ls=0.06)}">{s}</div>'
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"
    lab6 = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 600; letter-spacing: 0.06em"
    num = f"font-family: {DISP}; font-stretch: 62.5%; font-weight: {hw}; font-size: 25px; font-variant-numeric: lining-nums"
    hair = f'<div style="height: 0.75px; background-color: {ch}"></div>'
    double = f'<div style="height: 3px; background-color: {ch}"></div><div style="height: 0.75px; background-color: {ch}; margin-top: 2px"></div>'
    it = lambda size, lh=1.06, st=100: disp(size, weight=iw, stretch=st, lh=lh, ls=-0.012, italic=True)
    P = lambda s, mt=12: f'<p style="margin: {mt}px 0 0; {text(17, lh=1.47)}; text-wrap: pretty">{s}</p>'
    note = lambda s, mt=10: f'<p style="margin: {mt}px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">{s}</p>'
    unit = lambda s: f'<span style="{text(15, lh=1, italic=True)}; font-stretch: 100%; letter-spacing: 0; margin-left: 6px">{s}</span>'
    fighead = lambda a, b: (f'{hair}<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">'
                            f'{slug(a)}{L(b)}</div>')
    # exponents: 0.56em beside display numerals (SYSTEM 2.2), 0.64em in running text
    sup_d = "font-size: 0.56em; line-height: 0; vertical-align: 0.72em; letter-spacing: 0.01em"
    sup_t = "font-size: 0.64em; line-height: 0; vertical-align: 0.5em; letter-spacing: 0.01em"

    # the multiplication sign and the greater-than sign are drawn (lib.sign_times, lib.sign_gt),
    # with the character kept for screen readers
    sr = lambda ch_: f'<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%)">{ch_}</span>'
    times = sign_times() + sr("×")
    gt = sign_gt() + sr("greater than ")
    line_attr = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'

    def live_core(d, style=""):
        return f'<path d="{d}" {line_attr} stroke="{live}" stroke-width="{core_w}" style="{style}"></path>'

    def pen_at(x, y):
        st = f"transform: translate({x:.2f}px, {y:.2f}px)"
        return pen_under_marks(day, g, live, st) + f'<circle r="{3.6 if day else 3.4}" fill="{live}" style="{st}"></circle>'

    def tag_outline(s):
        return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {ch}; padding: 4px 6px 3px">{s}</span>'

    def tag_solid(s):
        return f'<span style="{mono(10, color=g, weight=600, ls=0.06)}; background-color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{s}</span>'

    def source(label):
        return (f'<a href="#paper" style="margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
                f'{text(15, lh=1, italic=True)}; color: {c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</a>')

    def btn_outline(label):
        return (f'<a href="#paper" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
                f'padding: 0 14px 0 16px; border: 1px solid {ch}; color: {c}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{OUTARROW.replace("11", "15", 2)}</a>')

    def section(slug_t, head):
        return (f'<div style="margin-top: 40px">{double}</div><div style="margin-top: 12px">{slug(slug_t)}</div>'
                f'<h2 style="margin: 8px 0 0; {disp(30, weight=hw, lh=1.02)}">{head}</h2>')

    def swatch(pid):
        return (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><defs>{patterns(pid, scr, tones={"a2": (A1, 0.46)})}</defs>'
                f'<rect width="22" height="10" fill="url(#{pid}a2)"></rect><rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{c}" stroke-width="0.9"></rect></svg>')

    def legend(items):
        return (f'<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; {mono(LAB, color=mu, ls=0.06)}">'
                + "".join(f'<span style="display: inline-flex; align-items: center; gap: 6px">{k}{s}</span>' for k, s in items) + '</div>')

    dot = f'<span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: {live}"></span>'

    def beam(xa, xb, y, col, w, cap=5):
        return (f'<line x1="{xa:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}" stroke="{col}" stroke-width="{w}"></line>'
                f'<line x1="{xa:.1f}" y1="{y - cap}" x2="{xa:.1f}" y2="{y + cap}" stroke="{col}" stroke-width="{w}"></line>'
                f'<line x1="{xb:.1f}" y1="{y - cap}" x2="{xb:.1f}" y2="{y + cap}" stroke="{col}" stroke-width="{w}"></line>')

    # ------------------------------------------------------------------ Fig. 1, part one: how one detector works
    def ifo_how():
        """One detector in plan, as a plotter drawing on open ground: the laser, two arms, and the
        path the light takes, down each arm and back."""
        cx0, cy0, a = 130.0, 179.0, 150.0
        tw, st, eb = 15.0, 11.0, 16.0
        top, right = cy0 - st - a, cx0 + st + a
        H = 236
        rect = lambda x, y, w_, h_: f'<rect x="{x:.1f}" y="{y:.1f}" width="{w_}" height="{h_}"></rect>'
        lx = cx0 - st - 8 - 22                 # laser housing
        parts = (rect(cx0 - tw / 2, top, tw, a) + rect(cx0 + st, cy0 - tw / 2, a, tw)
                 + rect(cx0 - eb / 2, top - eb, eb, eb) + rect(right, cy0 - eb / 2, eb, eb)
                 + rect(cx0 - st, cy0 - st, 2 * st, 2 * st) + rect(lx, cy0 - 6, 22, 12))
        o = 3.0
        # one continuous line: out of the laser, up the arm and back, along the other arm and back
        path = f"M{lx + 22:.1f} {cy0}H{cx0 - o}V{top}H{cx0 + o}V{cy0 - o}H{right}V{cy0 + o}H{cx0 - o}"

        def chev(x, y, dx, dy, k=2.5):
            # an open arrowhead with its point at (x, y), heading (dx, dy)
            bx, by_ = x - dx * k * 1.5, y - dy * k * 1.5
            return f"M{bx - dy * k:.1f} {by_ + dx * k:.1f}L{x:.1f} {y:.1f}L{bx + dy * k:.1f} {by_ - dx * k:.1f}"
        ym, xmid = cy0 - st - a * 0.5, cx0 + st + a * 0.5
        arrows = (chev(cx0 - o, ym - 22, 0, -1) + chev(cx0 + o, ym + 22, 0, 1)
                  + chev(xmid + 22, cy0 - o, 1, 0) + chev(xmid - 22, cy0 + o, -1, 0))
        xd, yd = cx0 + tw / 2 + 17, cy0 + st + 19
        dims = (f'<line x1="{xd}" y1="{top}" x2="{xd}" y2="{cy0 - st}"></line>'
                f'<line x1="{xd - 4}" y1="{top}" x2="{xd + 4}" y2="{top}"></line><line x1="{xd - 4}" y1="{cy0 - st}" x2="{xd + 4}" y2="{cy0 - st}"></line>'
                f'<line x1="{cx0 + st}" y1="{yd}" x2="{right}" y2="{yd}"></line>'
                f'<line x1="{cx0 + st}" y1="{yd - 4}" x2="{cx0 + st}" y2="{yd + 4}"></line><line x1="{right}" y1="{yd - 4}" x2="{right}" y2="{yd + 4}"></line>')
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Illustration, not to scale: one detector seen from above. '
            f'A laser at the corner of an L sends light down two arms, each 4 kilometers long, and back." style="display: block">'
            f'<g fill="{g}" stroke="{c}" stroke-width="0.9">{parts}</g>'
            f'<path d="{path}" fill="none" stroke="{c}" stroke-width="1.2" stroke-linejoin="miter"></path>'
            f'<path d="{arrows}" fill="none" stroke="{c}" stroke-width="1.2" stroke-linejoin="miter"></path>'
            f'<g fill="none" stroke="{c}" stroke-width="0.75">{dims}</g>'
            f'<g fill="{c}" style="{lab}"><text x="{lx - 8:.1f}" y="{cy0 + 3.8}" text-anchor="end">LASER</text>'
            f'<text x="{xd + 11}" y="{ym + 3.8:.1f}">ARM, 4 KM</text>'
            f'<text x="{xmid:.1f}" y="{yd + 18}" text-anchor="middle">ARM, 4 KM</text></g>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ Fig. 1, part two: when the wave reached each
    def ifo_when(pid):
        """A full-bleed band: the wave as an engraved field in plate ink, the two detectors over
        it, and under the band, on open ground, the gap between arrivals. The gap is the live beam."""
        s, x0 = 30.0, 26.0
        X = lambda v: x0 + v * s
        a = 112
        band = 160
        cy = 140
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

        (wdefs, wmarks), _ = gw_print(pid, -150.0, 250.0, W, band, theme, rot=18, rmin=150.0)
        field = (f'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block; position: absolute; left: 0; top: 0; '
                 f'animation: inkband 520ms {PRESS} {at(T_FIG1 - 420)} both"><defs>{wdefs}</defs>{wmarks}</svg>')
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ry}" x2="{X(v):.1f}" y2="{ry + (7 if v % 5 == 0 else 4)}"></line>' for v in range(0, 11))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="middle">{v}</text>' for v in (0, 5, 10))
        bd = f"M{X(0):.1f} {by}H{X(7):.1f}"
        dur = 900
        sweep = f"; animation: sweep {dur}ms linear {at(T_FIG1)} both"
        ride = f"; animation: travel {dur}ms linear {at(T_FIG1)} both"
        pen = f"offset-path: path('{bd}'); offset-distance: 100%; offset-rotate: 0deg"
        under = f'<path d="{bd}" {line_attr} stroke="{g}" stroke-width="7" style="{SWEEP_DASH}{sweep}"></path>'
        core = live_core(bd, SWEEP_DASH + sweep)
        draw = (
            f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Illustration, not to scale: a wave crossing the two detectors. '
            f'It reaches Livingston, Louisiana first and Hanford, Washington about 7 milliseconds later." style="display: block; position: absolute; left: 0; top: 0">'
            f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ry - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
            f'<g fill="{g}" stroke="{g}" stroke-width="6" stroke-linejoin="round">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="{g}" stroke="{c if day else NT}" stroke-width="1.1">{det(X(0))}{det(X(7))}</g>'
            f'<g fill="none" stroke="{grid}" stroke-width="0.6">'
            f'<line x1="{X(0):.1f}" y1="{band}" x2="{X(0):.1f}" y2="{ry}"></line><line x1="{X(7):.1f}" y1="{band}" x2="{X(7):.1f}" y2="{ry}"></line></g>'
            f'<g fill="none" stroke="{g}" stroke-width="5"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'<g fill="none" stroke="{c}" stroke-width="0.6"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{band}"></line></g>'
            f'{under}'
            f'<line x1="{X(0):.1f}" y1="{by - 5}" x2="{X(0):.1f}" y2="{by + 5}" stroke="{live}" stroke-width="{lw}"></line>'
            f'{core}'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{ry}" x2="{W}" y2="{ry}"></line>{ticks}</g>'
            f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{c}" stroke-width="9"></line></g></g>'
            f'<g fill="{tk}" style="{lab}">{tl}<text x="{X(10) + 16:.1f}" y="{ry + 20}">MS</text></g>'
            f'<g fill="{c}" style="{lab}"><text x="{X(0) + 9:.1f}" y="{by - 10}">ABOUT 7 MILLISECONDS LATER</text></g>'
            f'<g style="{pen}{ride}"><line x1="0" y1="-5" x2="0" y2="5" stroke="{live}" stroke-width="{lw}"></line></g>'
            f'<circle r="{3.6 if day else 3.4}" fill="{live}" style="{pen}{ride}"></circle>'
            f'</svg>'
        )
        names = (
            f'<div style="display: flex; margin-bottom: 8px">'
            f'<div style="width: 210px; flex: none">{L("Livingston, Louisiana", c, 600)}</div>'
            f'<div>{L("Hanford, Washington", c, 600)}</div></div>'
        )
        return f'{names}<div style="position: relative; width: {W}px; height: {H}px; margin: 0 -{M}px">{field}{draw}</div>'

    # ------------------------------------------------------------------ Fig. 2, the distance and its range
    def range_bar(pid):
        s = (CW - 62) / 600
        X = lambda v: v * s
        ax = 44
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ax}" x2="{X(v):.1f}" y2="{ax + (7 if v % 200 == 0 else 4)}"></line>' for v in range(0, 601, 50))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 200, 400, 600))
        return (
            f'<svg viewBox="0 0 {CW} 70" width="{CW}" height="70" role="img" aria-label="Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570, on a scale from 0 to 600" style="display: block; overflow: visible">'
            f'<defs>{patterns(pid, scr, tones={"a2": (A1, 0.46)})}</defs>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="url(#{pid}a2)"></rect>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<g style="animation: drop 260ms {PRESS} {at(T_FIG2)} both">'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{g}" stroke-width="7"></line>'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{live}" stroke-width="{lw}"></line>'
            f'<circle cx="{X(410):.1f}" cy="9" r="3.6" fill="{live}"></circle></g>'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{X(600):.1f}" y2="{ax}"></line>{ticks}</g>'
            f'<g fill="{tk}" style="{lab}">{tl}<text x="{CW}" y="{ax + 20}" text-anchor="end">Mpc</text></g>'
            f'<g fill="{c}" style="{lab}"><text x="{X(230):.1f}" y="11" text-anchor="middle">230</text><text x="{X(570):.1f}" y="11" text-anchor="middle">570</text></g>'
            f'</svg>'
        )

    def range_mini(pid):
        """The same range at ledger size: 120 px for 0 to 600 megaparsecs."""
        s = 120 / 600
        X = lambda v: 1 + v * s
        return (
            f'<svg viewBox="0 0 124 30" width="124" height="30" role="img" aria-label="The distance drawn: a band from 230 to 570 megaparsecs with a mark at 410, on a line from 0 to 600" style="display: block; flex: none">'
            f'<defs>{patterns(pid, scr, tones={"a2": (A1, 0.46)})}</defs>'
            f'<rect x="{X(230):.1f}" y="10" width="{340 * s:.1f}" height="11" fill="url(#{pid}a2)"></rect>'
            f'<rect x="{X(230):.1f}" y="10" width="{340 * s:.1f}" height="11" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<line x1="{X(410):.1f}" y1="5" x2="{X(410):.1f}" y2="26" stroke="{g}" stroke-width="6"></line>'
            f'<line x1="{X(410):.1f}" y1="5" x2="{X(410):.1f}" y2="26" stroke="{live}" stroke-width="{lw}"></line>'
            f'<circle cx="{X(410):.1f}" cy="5" r="3.2" fill="{live}"></circle>'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="26" x2="{X(600):.1f}" y2="26"></line>'
            f'<line x1="{X(0):.1f}" y1="22" x2="{X(0):.1f}" y2="26"></line><line x1="{X(600):.1f}" y1="22" x2="{X(600):.1f}" y2="26"></line></g>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ Fig. 3, where the mass went
    def chart_mass(pid):
        s = 4.0
        X = lambda v: 0.5 + v * s
        bh = 20
        l1, b1 = 11, 48
        l2, b2 = 96, 133
        axis = b2 + bh + 26
        H = axis + 26
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (7 if v % 10 == 0 else 4)}"></line>' for v in range(0, 71, 5))
        tl = "".join(f'<text x="{X(v):.1f}" y="{axis + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 20, 40, 60))
        drops = "".join(f'<line x1="{X(v):.1f}" y1="{b2 + bh}" x2="{X(v):.1f}" y2="{axis}"></line>' for v in (62, 65))

        def bar(v0, v1, y, fills):
            r = "".join(f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="{f}"></rect>' for f in fills)
            return r + f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'

        # the two bodies each get one screen angle at the mid tone. The body they form is the
        # weave of both angles at the light tone, so it does not outweigh the live segment.
        defs = patterns(pid, scr, tones={"a2": (A1, 0.46), "b2": (A2, 0.44), "a1": (A1, 0.24), "b1": (A2, 0.24)})
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" '
            f'aria-label="Data from the paper, in solar masses. Before: two black holes of about 36 and 29. After: one black hole of about 62, and about 3 that left as gravitational waves." style="display: block">'
            f'<defs>{defs}</defs>'
            f'<g stroke="{grid}" stroke-width="0.6" fill="none">{drops}</g>'
            f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
            f'{bar(0, 62, b2, [f"url(#{pid}a1)", f"url(#{pid}b1)"])}'
            f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="{live}" style="animation: flood 260ms {PRESS} {at(T_FIG3)} both"></rect>'
            f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab6}"><text x="0" y="{l1}">BEFORE</text><text x="0" y="{l2}">AFTER</text></g>'
            f'<g fill="{mu}" style="{lab}"><text x="50" y="{l1}">TWO BLACK HOLES</text><text x="43" y="{l2}">ONE BLACK HOLE, AND WAVES</text></g>'
            f'<g fill="{tk}" style="{lab}">{tl}<text x="{CW}" y="{axis + 20}" text-anchor="end">SOLAR MASSES</text></g>'
            f'<g fill="{c}" style="{lab}"><text x="{X(65) + 9:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 9:.1f}" y="{b2 + 20}">WAVES</text></g>'
            f'<g fill="{c}" style="{num}">'
            f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
            f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text><text x="{X(63.5):.1f}" y="{b2 - 7}" text-anchor="middle">3</text>'
            f'</g></svg>'
        )

    # ------------------------------------------------------------------ For scale: the change in arm length against a proton
    def analogy(pid):
        """An arm, a detail of its end, and inside the detail a proton. Under the proton, from one
        zero line: the proton's width as an ink beam, and the change in arm length as the live
        beam, which is too short to have a length. It is an end cap and the pen point."""
        ay = 12
        big = (175.0, 174.0, 126.0)
        small = (343.0, float(ay), 6.0)
        px, py, pr = 175.0, 146.0, 56.0
        zx = px - pr                           # the zero line both widths start from
        yb, yl = 222, 248                      # proton width, change in arm length
        H = 304
        tan = "".join(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{d:.1f}" y2="{e:.1f}"></line>' for a, b, d, e in tangents(small, big))
        return (
            f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Illustration, not to scale: one 4 kilometer arm, and a detail of its end. '
            f'Inside the detail, the width of a proton is ruled off, and beside it the change in arm length, which is far smaller." style="display: block">'
            f'<defs>{patterns(pid, plate, tones={"a1": (A1, 0.3)})}</defs>'
            f'<g fill="none" stroke="{grid}" stroke-width="0.6">{tan}'
            f'<circle cx="{small[0]}" cy="{small[1]}" r="{small[2]}"></circle><circle cx="{big[0]}" cy="{big[1]}" r="{big[2]}"></circle>'
            f'<line x1="{zx:.1f}" y1="{py}" x2="{zx:.1f}" y2="{yl + 8}"></line><line x1="{px + pr:.1f}" y1="{py}" x2="{px + pr:.1f}" y2="{yb}"></line></g>'
            f'{beam(1, 349, ay, c, 1.4)}'
            f'<circle cx="{px}" cy="{py}" r="{pr}" fill="url(#{pid}a1)"></circle>'
            f'<circle cx="{px}" cy="{py}" r="{pr}" fill="none" stroke="{c}" stroke-width="0.9"></circle>'
            f'{beam(zx, px + pr, yb, c, 1.4)}'
            f'<g style="animation: flood 260ms {PRESS} {at(T_SCALE)} both">'
            f'<line x1="{zx:.1f}" y1="{yl - 10}" x2="{zx:.1f}" y2="{yl + 10}" stroke="{g}" stroke-width="7"></line>'
            f'<line x1="{zx:.1f}" y1="{yl - 8}" x2="{zx:.1f}" y2="{yl + 8}" stroke="{live}" stroke-width="{lw}"></line>'
            f'<circle cx="{zx:.1f}" cy="{yl}" r="3.6" fill="{live}"></circle></g>'
            f'<g fill="{c}" style="{lab}"><text x="1" y="{ay + 21}">ONE ARM, 4 KM</text>'
            f'<text x="{px}" y="{py - pr - 10}" text-anchor="middle">A PROTON</text>'
            f'<text x="{zx + 13:.1f}" y="{yl + 3.8}">CHANGE IN ARM LENGTH</text></g>'
            f'</svg>'
        )

    # ------------------------------------------------------------------ Try it: the chirp as a control
    def chirp_plate(pid, t_pos, vx, vw, band, amp, labels, real=False, aria=""):
        """The control, drawn at one position. The field is a vertical line screen that swells
        where a crest of the signal passes, and only as far as the carriage has been dragged.
        vx, vw: the window of the 390 wide drawing that is shown, so a detail is a crop at full size."""
        x0, w = float(M), float(W - 2 * M)
        y0 = band / 2 + 2
        d, xm, _ = chirp(x0, y0, w, amp)
        xh, yh = x0 + w * t_pos, y0 - amp * chirp_env(t_pos) * math.sin(chirp_phase(t_pos))
        ruler = band
        H = band + 34
        # field: wave fronts arriving from the left. Fine arcs 3.2 px apart, each one swelling
        # where a crest of the signal sits, and only as far as the carriage has been dragged.
        # Where the crests come closer than the arcs can show, the tone holds steady instead.
        rcx = -260.0
        hairs, swells = [], []
        r = 3.2 * math.ceil((vx - rcx - 4) / 3.2)
        while rcx + r < vx + vw + 4:
            x = rcx + r
            tt = (x - x0) / w
            wd = 0.0
            if 0 <= tt <= TM + 1e-6 and x < xh - 0.5:
                crest = max(0.0, math.sin(chirp_phase(tt))) ** 0.85
                u = tt / TM
                period = w * TM / (C1 + 4 * C4 * u ** 3)
                k = min(1.0, max(0.0, (17.0 - period) / 7.0))
                wd = 1.7 * (crest * (1 - k) + 0.5 * k) * (0.3 + 0.7 * chirp_env(tt) ** 0.6)
            (swells if wd > 0.1 else hairs).append((r, 0.5 + (wd if day else wd * 0.75)))
            r += 3.2
        hair_attr = f'stroke="{plate}" stroke-width="0.5"' if day else f'stroke="{plate}" stroke-width="0.6" stroke-opacity="0.55"'
        ring = lambda r_, extra="": f'<circle cx="{rcx}" cy="{y0}" r="{r_:.1f}"{extra}></circle>'
        heavy = lambda wd_: ""
        field = (f'<g fill="none" {hair_attr}>{"".join(ring(r_) for r_, _ in hairs)}</g>'
                 f'<g fill="none" stroke="{plate}">{"".join(ring(r_, f" stroke-width={chr(34)}{wd_:.2f}{chr(34)}{heavy(wd_)}") for r_, wd_ in swells)}</g>')
        step = (xm - x0) / 10
        ticks, x, i = [], x0, 0
        while x <= W:
            ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
            x += step
            i += 1
        tl = ""
        if "0" in labels:
            tl += f'<text x="{x0}" y="{ruler + 20}">0</text>'
        if "0.1" in labels:
            tl += f'<text x="{(x0 + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
        if "0.2" in labels:
            tl += f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text>'
        # the control's field is its own layer, so it can ink in like the hero plate
        under = (f'<svg viewBox="{vx} 0 {vw} {band}" width="{vw}" height="{band}" aria-hidden="true" style="display: block; position: absolute; left: 0; top: 0; '
                 f'animation: inkproof 520ms {PRESS} {at(T_TRY)} both">{field}</svg>') if real else ""
        acc = 'aria-hidden="true"' if real else f'role="img" aria-label="{aria}"'
        carriage = "" if real else f'<rect x="{xh - 6:.2f}" y="{ruler - 13}" width="12" height="22" fill="{c}"></rect>'
        rest = (f'<path d="{d}" fill="none" stroke="{g}" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<path d="{d}" fill="none" stroke="{mu if day else NM}" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round"></path>')
        svg = (
            f'{under}<svg viewBox="{vx} 0 {vw} {H}" width="{vw}" height="{H}" {acc} style="display: block; position: relative">'
            f'<defs><clipPath id="{pid}c"><rect x="0" y="0" width="{xh:.2f}" height="{band}"></rect></clipPath>'
            f'<clipPath id="{pid}r"><rect x="{xh:.2f}" y="0" width="{W - xh:.2f}" height="{band}"></rect></clipPath>'
            f'<clipPath id="{pid}b"><rect x="{vx}" y="0" width="{vw}" height="{band}"></rect></clipPath></defs>'
            f'<g clip-path="url(#{pid}b)">{"" if real else field}'
            f'<g clip-path="url(#{pid}r)">{rest}</g>'
            f'<g clip-path="url(#{pid}c)">{live_under_strokes(d, day, g, live)}{live_core(d)}</g></g>'
            f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{max(x0, vx)}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{"".join(ticks)}</g>'
            f'<g fill="{tk}" style="{lab}">{tl}</g>'
            f'{carriage}{pen_at(xh, yh)}'
            f'</svg>'
        )
        return svg, xh, ruler, H

    def tryit_main(pid, t_pos):
        svg, xh, ruler, H = chirp_plate(pid, t_pos, 0, W, 196, 46, ("0", "0.1", "0.2"), real=True)
        inp = (f'<input type="range" class="pb-carriage" min="0" max="1000" value="{round(t_pos * 1000)}" aria-label="Time in the signal" '
               f'aria-valuetext="between 0.1 and 0.2 seconds, pitch rising" '
               f'style="position: absolute; left: {M - 6}px; top: {ruler - 24}px; width: {W - 2 * M + 12}px; height: 44px; margin: 0; padding: 0; color: {c}">')
        return f'<div style="position: relative; width: {W}px; height: {H}px; margin: 0 -{M}px">{svg}{inp}</div>'

    def tryit_detail(pid, t_pos, vx, labels, state, value, aria):
        svg, _, _, _ = chirp_plate(pid, t_pos, vx, 165, 112, 46, labels, aria=aria)
        return (f'<div style="display: flex; flex-direction: column; width: 165px">{svg}'
                f'<div style="display: flex; flex-direction: column; gap: 3px; margin-top: 8px">{L(state)}'
                f'<div style="{disp(30, weight=hw, lh=1)}; font-variant-numeric: lining-nums">{value}</div></div></div>')

    def row(label, value, n="", extra=""):
        nn = f'<div style="{text(15, lh=1.4, italic=True)}; text-wrap: {"balance" if extra else "pretty"}">{n}</div>' if n else ""
        if extra:
            nn = f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 16px">{nn}{extra}</div>'
        return (f'<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {ch}">'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
                f'<div style="{mono(LAB, color=mu, ls=0.06)}; flex: none">{label}</div>'
                f'<div style="{disp(30, weight=hw, lh=1)}; font-variant-numeric: lining-nums; text-align: right">{value}</div></div>{nn}</div>')

    group = lambda s: f'<div style="padding: 9px 0 8px; border-top: 0.75px solid {ch}">{slug(s)}</div>'

    # second voice inside a 30 px head: D4 by day, D5 at width 87.5 by night (SYSTEM 2.1)
    hit = it(30, 1.02, 100 if day else 87.5)
    press = lambda i: f"display: block; animation: press 190ms {PRESS} {at(i * 50)} both"
    h_it = disp(44, weight=iw, stretch=100 if day else 87.5, lh=0.98, ls=-0.012, italic=True)
    feed = "App-Feed-Day.dc.html" if day else "App-Feed-Night.dc.html"
    wrap = f"display: flex; flex-direction: column; padding: 0 {M}px"

    hero = FP.plate1("ex" + t0, theme)
    if not day and N_CORE != 1.6:
        hero = hero.replace(f'stroke="{live}" stroke-width="1.6"', f'stroke="{live}" stroke-width="{N_CORE}"')

    body = f"""<div style="width: {W}px; box-sizing: border-box; position: relative; background-color: {g}; color: {c}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 0 {M}px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; justify-content: space-between; height: 48px">
<a href="{feed}" style="margin-left: -12px; padding: 0 12px; min-width: 44px; height: 44px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 8px; color: {ch}; text-decoration: none; {mono(LAB, color=ch, weight=600, ls=0.06)}">{BACK}<span>Feed</span></a>
<div style="{disp(22, weight=hw, lh=1)}; padding-bottom: 3px">Paper<span style="{disp(22, weight=400, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: {live}; margin-left: 2px"></span></div>
</div>
{double}
</header>

<main style="display: flex; flex-direction: column">
<article style="display: flex; flex-direction: column">

<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Physics")}{tag_solid("Peer-reviewed")}
{source("Physical Review Letters")}
</div>
<h1 style="margin: 0; padding: 10px {M}px 0; {disp(44, weight=hw, lh=0.98)}">
<span style="{press(0)}">Two black holes</span>
<span style="{press(1)}">merged. <span style="{h_it}">Earth felt</span></span>
<span style="{press(2)}; {h_it}">space stretch.</span>
</h1>
{hero}
<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px {M}px 0">
<div style="display: flex; flex-direction: column; gap: 3px">
<div style="{disp(44, weight=hw, lh=1)}; font-variant-numeric: lining-nums; position: relative">1.0{times}10<sup style="{sup_d}">−21</sup></div>
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
{P("LIGO has two detectors, one in Hanford, Washington and one in Livingston, Louisiana. Each is an L-shaped laser interferometer.", 14)}
<figure style="margin: 24px 0 0; display: flex; flex-direction: column">
{fighead("Fig. 1", "Illustration, not to scale")}
<div style="margin-top: 16px">{ifo_how()}</div>
<div style="margin-top: 26px">{ifo_when("i" + t0)}</div>
</figure>
{P("On September 14, 2015, at 09:50:45 UTC, both recorded the same signal. It reached Livingston about 7 milliseconds before Hanford. The event is named GW150914.", 20)}
</section>

<section style="{wrap}">
{section("What they found", f'<span style="display: block">One chirp,</span><span style="display: block; white-space: nowrap; {hit}">a fifth of a second long.</span>')}
{P("The signal swept up in frequency from 35 Hz to 250 Hz in about 0.2 seconds. A rising sweep like that is called a chirp.", 14)}
{P("Its shape matches two black holes spiraling into one, about 410 megaparsecs away, roughly 1.3 billion light years.†")}
<div style="width: 64px; height: 0.75px; background-color: {ch}; margin-top: 16px"></div>
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
{legend([(swatch("j" + t0), "An estimate")])}
</figure>

{P(f'By the time the wave reached Earth, its peak strain was 1.0 × 10<sup style="{sup_t}">−21</sup>.', 28)}

<figure style="margin: 28px 0 0; display: flex; flex-direction: column">
{fighead("For scale", "Illustration, not to scale")}
<div style="margin-top: 14px">{analogy("a" + t0)}</div>
{note("That strain is a change in arm length far smaller than a proton.", 8)}
</figure>

<figure style="margin: 40px 0 0; display: flex; flex-direction: column">
{fighead("Try it", "Illustration, not to scale")}
<div style="margin-top: 10px; {disp(30, weight=hw, lh=1)}">Play the chirp by hand</div>
<div style="margin-top: 12px">{tryit_main("s2" + t0, 0.665)}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 4px">{L("Dragging")}<div style="{text(15, lh=1.2, italic=True)}">pitch rising</div></div>
<div style="display: flex; justify-content: space-between; margin-top: 22px">
{tryit_detail("s1" + t0, 0.0, 12, ("0",), "At rest", "35" + unit("Hz"), "Detail of the control at rest: the carriage at 0 seconds, where the pitch is 35 hertz")}
{tryit_detail("s3" + t0, 0.78, 225, ("0.2",), "At 0.2 seconds", "250" + unit("Hz"), "Detail of the control with the carriage at 0.2 seconds, where the pitch is 250 hertz")}
</div>
{note("Drag the carriage along the ruler to move through the signal.", 14)}
</figure>
</section>

<section style="{wrap}; margin-top: 40px">
{double}
<h2 style="margin: 12px 0 12px; {disp(30, weight=hw, lh=1)}">How sure <span style="{hit}">is this?</span></h2>
{group("Strengths")}
{row("Review", tag_solid("Peer-reviewed"), "Physical Review Letters, February 11, 2016.")}
{row("Significance", f'<span style="position: relative">{gt}5.1</span>' + unit("sigma"), "A false alarm this strong is expected less than once in 203,000 years.")}
{row("Detectors", "2" + unit("sites"), "Hanford and Livingston both recorded it, about 7 milliseconds apart.")}
{group("Limits")}
{row("Distance", "410" + unit("megaparsecs"), "With a range of roughly 230 to 570.", range_mini("q" + t0))}
{row("Masses", "36, 29, 62" + unit("solar masses"), "All three are estimates with wide error ranges.")}
{row("Sky position", "600" + unit("square degrees"), "Where it came from was known only to within about this much sky.")}
<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 0 0; border-top: 0.75px solid {ch}">
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
        f"body{{margin:0;background:{g}}}\na{{color:{c}}}\n"
        "@keyframes press{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}\n"
        "@keyframes sweep{from{stroke-dashoffset:1.003}to{stroke-dashoffset:0}}\n"
        "@keyframes travel{from{offset-distance:0%}to{offset-distance:100%}}\n"
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}\n"
        "@keyframes drop{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:none}}\n"
        "@keyframes flood{from{opacity:0}to{opacity:1}}\n"
        "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
        "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
        + ink_keyframes("inkproof", W, BAND) + "\n" + ink_keyframes("inkband", W, 160) + "\n"
        "@media (prefers-reduced-motion: reduce){*{animation:none!important}}\n"
        ".pb-carriage{-webkit-appearance:none;appearance:none;background:transparent;border-radius:0;cursor:ew-resize}\n"
        ".pb-carriage::-webkit-slider-runnable-track{-webkit-appearance:none;background:transparent;height:44px}\n"
        ".pb-carriage::-webkit-slider-thumb{-webkit-appearance:none;width:12px;height:22px;margin-top:11px;background:currentColor;border:0;border-radius:0}\n"
        ".pb-carriage::-moz-range-track{background:transparent;height:44px}\n"
        ".pb-carriage::-moz-range-thumb{width:12px;height:22px;background:currentColor;border:0;border-radius:0}\n"
        ".pb-carriage:focus-visible{outline:2px solid currentColor;outline-offset:2px}"
    )
    heights = json.loads(HEIGHTS.read_text()) if HEIGHTS.exists() else {}
    h = int(heights.get(theme, 5600))
    out = OUT / f"Explainer-{theme.capitalize()}.dc.html"
    out.write_text(page(f"Explainer, Paper 1, {theme}", css, body, W, h))
    print("wrote", out, out.stat().st_size, "height", h)


if __name__ == "__main__":
    for th in (sys.argv[1:] or ["day", "night"]):
        build(th)
