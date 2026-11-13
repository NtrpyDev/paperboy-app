"""Shared parts for the brand and motion boards. Built on the locked system code in
scratch/engraved/lib.py. Everything returns literal markup.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import *  # noqa: E402,F403

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
LABSZ = 10.5
G = json.loads((HERE / "glyphs.json").read_text())
PROJECT = HERE.parents[1] / "canvas" / "project"


def T(theme):
    day = theme == "day"
    return dict(
        day=day,
        ground=STOCK if day else NG,
        text=INK if day else NT,
        muted=MUTED if day else NM,
        plate=BLUE if day else NBLUE,
        key=INK if day else NM,
        grid=MUTED if day else NS,
        live=LIVE if day else AMBER,
        hw=800 if day else 900,
        iw=300 if day else 400,
    )


def lab(color=MUTED, weight=500, size=LABSZ, lh=1.3):
    return (f"font-family: {MONO}; font-stretch: 75%; font-size: {size}px; font-weight: {weight}; "
            f"letter-spacing: 0.06em; line-height: {lh}; text-transform: uppercase; color: {color}")


def L(t, color=MUTED, weight=500, extra=""):
    return f'<div style="{lab(color, weight)}{extra}">{t}</div>'


SVGLAB = f"font-family: {MONO}; font-stretch: 75%; font-size: {LABSZ}px; font-weight: 500; letter-spacing: 0.06em"
SVGSLUG = f"font-family: {MONO}; font-stretch: 75%; font-size: {LABSZ}px; font-weight: 600; letter-spacing: 0.06em"


def head(n, name, kind, c=INK, mu=MUTED, note=""):
    """Figure head row: section slug on the left, kind slug on the right."""
    extra = f'<span style="color: {mu}; font-weight: 500; margin-left: 14px">{note}</span>' if note else ""
    return (f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
            f'<div style="{lab(c, 600)}"><span style="color: {mu}; margin-right: 10px">{n}</span>{name}{extra}</div>'
            f'<div style="{lab(mu)}; text-align: right">{kind}</div></div>')


def double(c=INK):
    return f'<div style="height: 3px; background-color: {c}"></div><div style="height: 0.75px; background-color: {c}; margin-top: 2px"></div>'


# ------------------------------------------------------------------ wordmark
def dot_rule(size):
    """Dot diameter and the gap after the y, in px. The four sizes named in SYSTEM.md 9.1 are
    exact. Other sizes are read off the same curve."""
    exact = {22: (4, 2), 33: (6, 3), 38: (6.5, 3), 150: (22, 10)}
    if size in exact:
        return exact[size]
    pts = [(22, 4 / 22, 2 / 22), (33, 6 / 33, 3 / 33), (38, 6.5 / 38, 3 / 38), (150, 22 / 150, 10 / 150)]
    if size <= pts[0][0]:
        d, g = pts[0][1], pts[0][2]
    elif size >= pts[-1][0]:
        d, g = pts[-1][1], pts[-1][2]
    else:
        for (s0, d0, g0), (s1, d1, g1) in zip(pts, pts[1:]):
            if s0 <= size <= s1:
                u = (size - s0) / (s1 - s0)
                d, g = d0 + (d1 - d0) * u, g0 + (g1 - g0) * u
    return round(size * d * 2) / 2, round(size * g * 2) / 2


def wm(size, theme="day", color=None, dot=None, extra="", parts=None):
    """The wordmark as live type, exactly as SYSTEM.md 9.1 sets it. parts lets the motion
    board put a style on each of the three pieces."""
    t = T(theme)
    c = color or t["text"]
    dcol = dot or t["live"]
    hero = size >= 100
    iw = t["iw"] if size > 22 else 400
    d, g = dot_rule(size)
    pa, pb, pd = parts or ("", "", "")
    return (
        f'<div style="{disp(size, weight=t["hw"], lh=1, ls=-0.012 if hero else -0.005)}; color: {c}; white-space: nowrap{extra}">'
        f'<span style="display: inline-block{pa}">Paper</span>'
        f'<span style="display: inline-block; {disp(size, weight=iw, stretch=100, lh=1, ls=-0.025 if hero else -0.02, italic=True)}{pb}">boy</span>'
        f'<span style="display: inline-block; width: {d}px; height: {d}px; border-radius: 50%; background-color: {dcol}; margin-left: {g}px{pd}"></span></div>'
    )


def wm_outline(size, theme="day", color=None, dot=None):
    """The wordmark as outlines taken from the font files (outline.py). Returns the marks, drawn
    with the baseline at y = 0 and the P's stem at x = 0, and the measures in px."""
    t = T(theme)
    c = color or t["text"]
    dcol = dot or t["live"]
    hero = size >= 100
    k = size / 1000
    ls1, ls2 = (-12, -25) if hero else (-5, -20)
    pk = G["paper_d1" if t["day"] else "paper_d2"]
    bk = G["boy_d4" if (t["day"] and size > 22) else "boy_d5"]
    lsb = pk["boxes"][0][0]
    out, x = [], -lsb
    for i, (d, gx) in enumerate(zip(pk["glyphs"], pk["x"])):
        out.append(f'<path d="{d}" transform="translate({(x + gx + i * ls1) * k:.2f} 0) scale({k})"></path>')
    x += pk["advance"] + 5 * ls1
    boy_x = x * k
    for i, (d, gx) in enumerate(zip(bk["glyphs"], bk["x"])):
        out.append(f'<path d="{d}" transform="translate({(x + gx + i * ls2) * k:.2f} 0) scale({k})"></path>')
    x += bk["advance"] + 3 * ls2
    dd, g = dot_rule(size)
    dot_x = x * k + g
    marks = (f'<g fill="{c}">{"".join(out)}</g>'
             f'<circle cx="{dot_x + dd / 2:.2f}" cy="{-dd / 2:.2f}" r="{dd / 2}" fill="{dcol}"></circle>')
    return marks, dict(width=dot_x + dd, boy_x=boy_x, dot_x=dot_x, dot=dd, gap=g, cap=714 * k, xh=548 * k,
                       asc=760 * k, desc=240 * k, paper_w=(pk["advance"] + 5 * ls1 - lsb) * k)


# ------------------------------------------------------------------ app icon
ICON_S = 0.44          # px per font unit at 512: the P is 314 px tall
ICON_DOT = 43.0        # pen point radius at 512
ICON_GAP = 28.0


def icon_geometry():
    box = G["P_d1"]["boxes"][0]
    pw = (box[2] - box[0]) * ICON_S
    cap = -box[1] * ICON_S
    mark_w = pw + ICON_GAP + 2 * ICON_DOT
    left = (512 - mark_w) / 2
    base = (512 + cap) / 2
    return dict(left=left, base=base, pw=pw, cap=cap, mark_w=mark_w,
                dot=(left + pw + ICON_GAP + ICON_DOT, base - ICON_DOT), tx=left - box[0] * ICON_S)


def icon(pid, px, theme="day", mask=None, field=True, extend=0, label="Paperboy app icon", pitch=8.0, trap=5.0, rot=-118, halo=1.38):
    """The app icon, drawn on a 512 grid from three parts of the system: the P of the wordmark,
    the pen point, and the engraved field, whose rings are centered on the pen point.
    theme: day, night, mono (one color, ink on stock), mono-rev (stock on ink).
    extend adds field outside the 512 square, for the adaptive layer."""
    g = icon_geometry()
    if theme == "day":
        ground, ink, plate, live = STOCK, INK, BLUE, LIVE
    elif theme == "night":
        ground, ink, plate, live = NG, NT, NBLUE, AMBER
    elif theme == "mono":
        ground, ink, plate, live = STOCK, INK, INK, INK
    else:
        ground, ink, plate, live = INK, STOCK, STOCK, STOCK
    night = theme == "night"
    cx, cy = g["dot"]
    lo, size = -extend, 512 + 2 * extend
    defs, marks = "", ""
    if field and theme in ("day", "night"):
        wdefs, wmarks = wavefield(pid, cx, cy, size, size, plate, rot=rot, rmin=ICON_DOT * 1.8 + pitch * 0.5, rmax=640.0 + extend,
                                  pitch=pitch, weights=(pitch * 0.156, pitch * 0.36, pitch * 0.58), gap=lambda r: pitch * 2.8 + 0.085 * r)
        wdefs = wdefs.replace('x="0" y="0"', f'x="{lo}" y="{lo}"')
        if night:
            wmarks = wmarks.replace(f'stroke="{plate}" stroke-width="{pitch * 0.156}"', f'stroke="{plate}" stroke-width="{pitch * 0.19:.2f}" stroke-opacity="0.55"', 1)
        defs += wdefs
        marks += wmarks
    pd = G["P_d1" if theme != "night" else "P_d2"]["glyphs"][0]
    tr = f'transform="translate({g["tx"]:.2f} {g["base"]:.2f}) scale({ICON_S})"'
    trap = 2 * trap / ICON_S
    p_marks = ""
    if field and theme in ("day", "night"):
        p_marks += f'<path d="{pd}" {tr} fill="{ground}" stroke="{ground}" stroke-width="{trap:.1f}" stroke-linejoin="round"></path>'
        p_marks += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{ICON_DOT * 1.8:.1f}" fill="{ground}"></circle>'
    p_marks += f'<path d="{pd}" {tr} fill="{ink}"></path>'
    if night:
        p_marks += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{ICON_DOT * halo:.1f}" fill="{live}" fill-opacity="0.24"></circle>'
    p_marks += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{ICON_DOT}" fill="{live}"></circle>'
    clip, cattr = "", ""
    if mask == "circle":
        clip = f'<clipPath id="{pid}c"><circle cx="256" cy="256" r="256"></circle></clipPath>'
        cattr = f' clip-path="url(#{pid}c)"'
    return (
        f'<svg viewBox="{lo} {lo} {size} {size}" width="{px}" height="{px}" role="img" aria-label="{label}" style="display: block; flex: none">'
        f'<defs>{defs}{clip}</defs><g{cattr}><rect x="{lo}" y="{lo}" width="{size}" height="{size}" fill="{ground}"></rect>{marks}{p_marks}</g></svg>'
    )
