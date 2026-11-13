"""Site: the Paperboy website as one fluid PAGE, day theme. Revision 2, after CRITIQUE.md.

Built from the locked First Light system (design/SYSTEM.md). Reuses the drawing code in
scratch/engraved/lib.py. Facts come from design/CONTENT.md only.

  python3 site.py                 writes design/canvas/project/Site.dc.html
  PB_DELAY=1500 python3 site.py   same, every animation pushed back 1.5 s (for early frames)
  PB_OUT=/path/x.dc.html          write somewhere else

Motion on the artboard: the hero sweeps on arrival. The draw-ins lower on the page (the ring
in the feed picture, the live marks of Fig. 1 and Fig. 2, the line of "How an explainer is made")
start a little after it so one render shows them part way. Fig. 3 is still. In production each of those runs
once, when its figure scrolls into view. How that trigger is built was not checked here.
"""
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
import lib as _lib  # noqa: E402
from lib import *  # noqa: E402,F403

BLUE = "#1F3FD0"
OUT = pathlib.Path(os.environ.get("PB_OUT") or HERE.parents[1] / "canvas" / "project" / "Site.dc.html")
PREVIEW_H = int(os.environ.get("PB_H", "4868"))

GITHUB = "https://github.com/NtrpyDev/paperboy-app"
RELEASES = "https://github.com/NtrpyDev/paperboy-app/releases"

# when each draw-in starts, ms after load
T_HERO, T_RING, T_F1, T_F2, T_MADE = 320, 520, 700, 1300, 900


# ------------------------------------------------------------------ type
def px(v):
    return f"{v}px" if isinstance(v, (int, float)) else v


def d1(size, lh=0.98, ls=-0.005):
    return (f"font-family: {DISP}; font-size: {px(size)}; font-weight: 800; font-stretch: 62.5%; "
            f"line-height: {lh}; letter-spacing: {ls}em")


def d3(size=23):
    return (f"font-family: {DISP}; font-size: {px(size)}; font-weight: 700; font-stretch: 75%; "
            f"line-height: 1; letter-spacing: 0.005em")


def d4(size, lh=0.98, ls=-0.012, weight=300, stretch="100%"):
    return (f"font-family: {DISP}; font-size: {px(size)}; font-weight: {weight}; font-stretch: {stretch}; "
            f"line-height: {lh}; letter-spacing: {ls}em; font-style: italic")


def t1(size="var(--fs-body)", lh="var(--lh-body)", weight=400, italic=False):
    s = f"font-family: {TEXT}; font-size: {px(size)}; line-height: {lh}; font-weight: {weight}"
    return s + ("; font-style: italic" if italic else "")


def lab(color=MUTED, weight=500, size="var(--fs-label)", lh=1.3):
    return (f"font-family: {MONO}; font-stretch: 75%; font-size: {px(size)}; font-weight: {weight}; "
            f"letter-spacing: 0.06em; line-height: {lh}; text-transform: uppercase; color: {color}")


SVGLAB = f"font-family: {MONO}; font-stretch: 75%; font-size: 10.5px; font-weight: 500; letter-spacing: 0.06em"
SVGLAB6 = SVGLAB.replace("font-weight: 500", "font-weight: 600")
NOTE = t1("var(--fs-note)", 1.42, italic=True)
DOUBLE = (f'<div style="height: 3px; background-color: {INK}"></div>'
          f'<div style="height: 0.75px; background-color: {INK}; margin-top: 2px"></div>')
HAIR = f'<div style="height: 0.75px; background-color: {INK}"></div>'

# The multiplication and greater-than signs are the drawn ones every board uses (lib.sign_times,
# lib.sign_gt, CRITIQUE.md system fix 3). The character is kept for screen readers.
SR = lambda t: f'<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%)">{t}</span>'
TIMES = sign_times() + SR("×")
GT = f'<span style="position: relative">{sign_gt()}{SR("greater than ")}</span>'

# New icon, in the weight and ends of the set in SYSTEM.md section 8.
DOWN = ('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="square" aria-hidden="true"><path d="M10 3v10.5M5.5 9.5l4.5 4.5 4.5-4.5M4 17.25h12"></path></svg>')
DOWN_S = ('<svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" stroke-width="1.3" '
          'stroke-linecap="square" aria-hidden="true"><path d="M5.5 1v6.5M2.75 5l2.75 2.75L8.25 5M1.5 10h8"></path></svg>')
OUT15 = OUTARROW.replace("11", "15", 2)


# ------------------------------------------------------------------ small parts
def tag_outline(t, size="var(--fs-tag)"):
    return f'<span style="{lab(INK, 600, size)}; border: 1px solid {INK}; padding: 4px 6px 3px">{t}</span>'


def tag_solid(t, size="var(--fs-tag)"):
    return (f'<span style="{lab(STOCK, 600, size)}; background-color: {INK}; border: 1px solid {INK}; '
            f'padding: 4px 6px 3px">{t}</span>')


def tag_screen(t, size="var(--fs-tag)"):
    hatch = f"repeating-linear-gradient(135deg, {INK} 0 1.1px, transparent 1.1px 3.2px)"
    return (f'<span style="display: inline-flex; padding: 3.5px; background-image: {hatch}">'
            f'<span style="{lab(INK, 600, size)}; background-color: {STOCK}; padding: 1.5px 4px 0.5px">{t}</span></span>')


def slab(label, href, icon=DOWN):
    return (f'<a class="slab" href="{href}" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; '
            f'justify-content: space-between; gap: 12px; padding: 0 14px 0 16px; background-color: {INK}; color: {STOCK}; '
            f'text-decoration: none; white-space: nowrap; {d3()}"><span>{label}</span>{icon}</a>')


def outline(label, href, icon=OUT15):
    return (f'<a href="{href}" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; '
            f'justify-content: space-between; gap: 12px; padding: 0 14px 0 16px; border: 1px solid currentColor; '
            f'text-decoration: none; white-space: nowrap; {d3()}"><span>{label}</span>{icon}</a>')


def textlink(label, href, icon=OUTARROW, size="var(--fs-note)", extra=""):
    return (f'<a href="{href}" style="min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
            f'{t1(size, 1, italic=True)}; text-decoration: underline; text-decoration-thickness: 0.75px; '
            f'text-underline-offset: 3px; white-space: nowrap{extra}"><span>{label}</span>{icon}</a>')


def wordmark(size, dot, gap, ls=(-0.005, -0.02)):
    return (f'<span style="{d1(size, 1, ls[0])}">Paper</span><span style="{d4(size, 1, ls[1])}">boy</span>'
            f'<span style="display: inline-block; width: {dot}; height: {dot}; border-radius: 50%; '
            f'background-color: {LIVE}; margin-left: {gap}"></span>')


# ------------------------------------------------------------------ Plate 1, from the shared generator
def crest_gap(r):
    """Pitch of the spiral crests. As in lib.py out to 380 px (every phone plate), then it
    levels off, so a plate 1900 px wide keeps fine crests far from the center and does not
    turn into broad stripes."""
    return 9.0 + 0.085 * min(r, 380.0) + 0.012 * max(0.0, r - 380.0)


def far_taper(r):
    """Far from the source the swells thin toward the hairline, so the wide plate goes lighter
    to the left and the tone falls by line weight. 1 inside 360 px: no phone plate changes."""
    return 1.0 if r <= 360.0 else max(0.4, 1.0 - 0.6 * (r - 360.0) / 600.0)


def print_layers(pid, cx, cy, w, h, k=1.0, taper=True, **kw):
    """The print layers of Plate 1 from gw_print() in scratch/engraved/lib.py, the one generator
    every board calls. Returns ((blue_defs, blue_marks), (key_defs, key_marks)).
    taper: scale the swell thickness by far_taper(radius) while the generator runs. It wraps
    lib._lune for the length of the call and puts it back."""
    orig = getattr(_lib, "_lune", None)
    if taper and orig:
        _lib._lune = lambda cx_, cy_, r, t0, t1, peak: orig(cx_, cy_, r, t0, t1, peak * far_taper(r))
    try:
        return _lib.gw_print(pid, cx, cy, w, h, "day", k=k, **kw)
    finally:
        if orig:
            _lib._lune = orig


# ------------------------------------------------------------------ hero plate (Plate 1)
def plate_gw(pid, W, band, x0, cw, k, cy, amp, zero_up, tick_s, label_every, ink_name, lab_px=10.5, sweep_ms=1900):
    """The locked hero plate at any size. Blue engraved field, black contour figure, the live
    line crossing the lower third on its trap, the ruler as the bottom edge, the carriage.
    The drawing is W wide at fixed scale. Its window is fluid and clips it at the right."""
    # tm = 0.8 puts the merger at 0.2 s and the end of the line at exactly 0.25 s, so the pen
    # point parks on the last tick of the ruler (the other boards use 0.78: 0.256 s)
    cx = x0 + cw * 0.775
    y0 = band - zero_up
    d, xm, _ = chirp(x0, y0, cw, amp, tm=0.8)
    PH = band + 34
    (bdefs, blue), (kdefs, key) = print_layers(pid, cx, cy, W, band, k=k, gap=crest_gap)
    svg = lambda defs, marks: (f'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block">'
                               + (f"<defs>{defs}</defs>" if defs else "") + f"{marks}</svg>")
    blue_svg, key_svg = svg(bdefs, blue), svg(kdefs, key)

    # ruler: 0.2 s falls at the merger. Ticks stop where the line stops.
    per_s = (xm - x0) / 0.2
    ticks, labels, i = [], [], 0
    n_label = round(label_every / tick_s)
    while x0 + i * tick_s * per_s <= x0 + cw + 0.5:
        x = x0 + i * tick_s * per_s
        major = i % n_label == 0
        ticks.append(f'<line x1="{x:.2f}" y1="{band}" x2="{x:.2f}" y2="{band + (7 if major else 4)}"></line>')
        if major:
            txt = "0" if i == 0 else f"{i * tick_s:.2f}".rstrip("0")
            labels.append((x, txt, "start" if i == 0 else "middle"))
        i += 1
    x_last, txt_last, a_last = labels[-1]
    labels[-1] = (x_last, txt_last + " s", a_last)
    tl = "".join(f'<text x="{x:.1f}" y="{band + 20}" text-anchor="{a}">{t}</text>' for x, t, a in labels)

    lab_style = SVGLAB.replace("10.5px", f"{lab_px}px")
    sweep = f"; animation: sweep {sweep_ms}ms linear {at(T_HERO)} both"
    ride = f"; animation: travel {sweep_ms}ms linear {at(T_HERO)} both"
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"
    live_svg = (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" '
        f'aria-label="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{band - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'<path d="{d}" fill="none" stroke="{STOCK}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="{SWEEP_DASH}{sweep}"></path>'
        f'<path d="{d}" fill="none" stroke="{LIVE}" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="{SWEEP_DASH}{sweep}"></path>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{x0}" y1="{band}" x2="{W}" y2="{band}"></line>{"".join(ticks)}</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{INK}" stroke-width="9"></line></g></g>'
        f'<g fill="{INK}" style="{lab_style}">{tl}</g>'
        f'<circle r="6.5" fill="{STOCK}" style="{pen}{ride}"></circle>'
        f'<circle r="3.6" fill="{LIVE}" style="{pen}; animation: travel {sweep_ms}ms linear {at(T_HERO)} both, pulse 2400ms ease-in-out {at(T_HERO + sweep_ms + 180)} infinite"></circle>'
        f'</svg>'
    )
    reg_a = f"animation: registerA 480ms {REGISTER} {at(60)} both"
    reg_b = f"animation: registerB 480ms {REGISTER} {at(60)} both"
    ink = f"animation: {ink_name} 520ms {PRESS} {at(60)} both"
    return (
        f'<div style="position: relative; height: {PH}px; overflow: hidden">'
        f'<div style="position: absolute; left: 0; top: 0; width: 100%; height: {band}px; {ink}">'
        f'<div style="position: absolute; left: 0; top: 0; {reg_a}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0; {reg_b}">{key_svg}</div>'
        f'</div>{live_svg}</div>'
    )


def wipe_px(name, band):
    k = abs(band / math.tan(math.radians(A1)))
    return (f"@keyframes {name}{{from{{clip-path:polygon(0 0,0 0,{-k:.1f}px 100%,0 100%)}}"
            f"to{{clip-path:polygon(0 0,calc(100% + {k:.1f}px) 0,100% 100%,0 100%)}}}}")


# ------------------------------------------------------------------ Plate 3 (M87) for the feed sheet
def plate_m87(pid="sm", PW=390, SH=196, R=57.0, cx=228.0):
    cy = SH / 2
    tones_b = {"h1": (A2, 0.2), "h2": (A2, 0.42), "h3": (A2, 0.66)}
    tones_k = {"c2": (A1, 0.38), "c3": (A1, 0.6)}
    defs = patterns(pid, BLUE, pitch=3.2, tones=tones_b) + patterns(pid, INK, pitch=3.2, tones=tones_k)

    def disc(r, fill):
        return f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{fill}"></circle>'

    f = R / 88.0
    sky = (
        f'<rect width="{PW}" height="{SH}" fill="url(#{pid}h3)"></rect>'
        f'{disc(R + 132 * f, STOCK)}{disc(R + 132 * f, f"url(#{pid}h2)")}'
        f'{disc(R + 66 * f, STOCK)}{disc(R + 66 * f, f"url(#{pid}h1)")}'
        f'{disc(R + 24 * f, STOCK)}'
        f'{disc(R - 20 * f, f"url(#{pid}h1)")}'
        f'{disc(R - 34 * f, f"url(#{pid}h2)")}{disc(R - 34 * f, f"url(#{pid}c2)")}'
        f'{disc(R - 50 * f, STOCK)}{disc(R - 50 * f, f"url(#{pid}h3)")}{disc(R - 50 * f, f"url(#{pid}c3)")}'
    )
    by = SH + 13
    ring = f'cx="{cx}" cy="{cy}" r="{R}" fill="none" pathLength="1" transform="rotate(-90 {cx} {cy})"'
    sweep = f"{SWEEP_DASH}; animation: sweep 1800ms linear {at(T_RING)} both"
    return (
        f'<div style="position: relative; width: {PW}px; height: {SH + 34}px; margin-top: 12px">'
        f'<svg viewBox="0 0 {PW} {SH}" width="{PW}" height="{SH}" aria-hidden="true" style="display: block"><defs>{defs}</defs>{sky}</svg>'
        f'<svg viewBox="0 0 {PW} {SH + 34}" width="{PW}" height="{SH + 34}" aria-hidden="true" style="position: absolute; left: 0; top: 0">'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none">'
        f'<line x1="{cx - R}" y1="{by}" x2="{cx + R}" y2="{by}"></line>'
        f'<line x1="{cx - R}" y1="{by - 5}" x2="{cx - R}" y2="{by + 5}"></line>'
        f'<line x1="{cx + R}" y1="{by - 5}" x2="{cx + R}" y2="{by + 5}"></line></g>'
        f'<text x="{cx}" y="{by + 17}" text-anchor="middle" fill="{INK}" style="{SVGLAB}">RING DIAMETER</text>'
        f'<circle {ring} stroke="{STOCK}" stroke-width="7" style="{sweep}"></circle>'
        f'<circle {ring} stroke="{LIVE}" stroke-width="1.9" style="{sweep}"></circle>'
        f'<g style="transform-origin: {cx}px {cy}px; animation: orbit 1800ms linear {at(T_RING)} both">'
        f'<circle cx="{cx}" cy="{cy - R}" r="6.5" fill="{STOCK}"></circle>'
        f'<circle cx="{cx}" cy="{cy - R}" r="3.6" fill="{LIVE}"></circle></g>'
        f'</svg></div>'
    )


# ------------------------------------------------------------------ figures of the excerpt
CW = 346      # four columns of twelve
CW8 = 716     # eight columns of twelve
FIGSVG = "display: block; width: 100%; max-width: 350px; height: auto"


def figbox(svg, w=346, mt=14):
    """A column figure. On a phone narrower than the drawing it reaches into the page margins
    (20 px at most) so its labels stay at their drawn size."""
    m = f"max(-20px, min(0px, calc((100% - {w}px) / 2)))"
    return f'<div style="margin: {mt}px {m} 0">{svg}</div>'


def mass_bar(X, s, bh, pid):
    def bar(v0, v1, y, fills):
        r = "".join(f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="{f}"></rect>' for f in fills)
        return r + f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="none" stroke="{INK}" stroke-width="0.9"></rect>'
    return bar


MASS_ARIA = ("Data from the paper, in solar masses. Before: two black holes of about 36 and 29. "
             "After: one black hole of about 62, and about 3 that left as gravitational waves.")
NUM25 = f"font-family: {DISP}; font-stretch: 62.5%; font-weight: 800; font-size: 25px; font-variant-numeric: lining-nums"
# both screens of the "62" weave are the light tone, so the weave does not outweigh the live segment
MASS_TONES = {"a2": (A1, 0.46), "b2": (A2, 0.44), "a1": (A1, 0.24), "b1": (A2, 0.24)}


def live_seg(X, s, y, bh):
    # Still on purpose. Three ways of animating this segment (opacity, a dash sweep, a transform)
    # all left it unpainted in the wide chart in full-page captures, though it painted when
    # scrolled into view. The cause was not found, so the segment does not animate.
    return (f'<rect x="{X(62):.1f}" y="{y}" width="{3 * s:.1f}" height="{bh}" fill="{LIVE}"></rect>'
            f'<rect x="{X(62):.1f}" y="{y}" width="{3 * s:.1f}" height="{bh}" fill="none" stroke="{INK}" stroke-width="0.9"></rect>')


def chart_mass(pid="fm"):
    """Fig. 3 at column width: the explainer's chart (scratch/explainer/explainer.py)."""
    s = 4.0
    X = lambda v: 0.5 + v * s
    bh = 20
    l1, b1 = 11, 48
    l2, b2 = 96, 133
    axis = b2 + bh + 26
    H = axis + 26
    bar = mass_bar(X, s, bh, pid)
    ticks = "".join(f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (7 if v % 10 == 0 else 4)}"></line>' for v in range(0, 71, 5))
    tl = "".join(f'<text x="{X(v):.1f}" y="{axis + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 20, 40, 60))
    drops = "".join(f'<line x1="{X(v):.1f}" y1="{b2 + bh}" x2="{X(v):.1f}" y2="{axis}"></line>' for v in (62, 65))
    return (
        f'<svg viewBox="0 0 350 {H}" width="350" height="{H}" role="img" aria-label="{MASS_ARIA}" style="{FIGSVG}">'
        f'<defs>{patterns(pid, INK, tones=MASS_TONES)}</defs>'
        f'<g stroke="{MUTED}" stroke-width="0.6" fill="none">{drops}</g>'
        f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
        f'{bar(0, 62, b2, [f"url(#{pid}a1)", f"url(#{pid}b1)"])}{live_seg(X, s, b2, bh)}'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}</g>'
        f'<g fill="{INK}" style="{SVGLAB6}"><text x="0" y="{l1}">BEFORE</text><text x="0" y="{l2}">AFTER</text></g>'
        f'<g fill="{MUTED}" style="{SVGLAB}"><text x="50" y="{l1}">TWO BLACK HOLES</text><text x="43" y="{l2}">ONE BLACK HOLE, AND WAVES</text></g>'
        f'<g fill="{INK}" style="{SVGLAB}">{tl}<text x="350" y="{axis + 20}" text-anchor="end">SOLAR MASSES</text>'
        f'<text x="{X(65) + 9:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 9:.1f}" y="{b2 + 20}">WAVES</text></g>'
        f'<g fill="{INK}" style="{NUM25}">'
        f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
        f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text><text x="{X(63.5):.1f}" y="{b2 - 7}" text-anchor="middle">3</text>'
        f'</g></svg>'
    )


def chart_mass_wide(pid="fw"):
    """Fig. 3 across eight columns. Same marks, the row labels moved to the left of the bars."""
    x0, s = 76.0, 8.4
    X = lambda v: x0 + v * s
    bh = 20
    b1 = 34
    b2 = b1 + bh + 44
    axis = b2 + bh + 20
    H = axis + 26
    bar = mass_bar(X, s, bh, pid)
    ticks = "".join(f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (7 if v % 10 == 0 else 4)}"></line>' for v in range(0, 71, 5))
    tl = "".join(f'<text x="{X(v):.1f}" y="{axis + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 10, 20, 30, 40, 50, 60))
    drops = "".join(f'<line x1="{X(v):.1f}" y1="{b2 + bh}" x2="{X(v):.1f}" y2="{axis}"></line>' for v in (62, 65))
    return (
        f'<svg viewBox="0 0 {CW8} {H}" width="{CW8}" height="{H}" role="img" aria-label="{MASS_ARIA}" style="display: block; width: 100%; height: auto">'
        f'<defs>{patterns(pid, INK, tones=MASS_TONES)}</defs>'
        f'<g stroke="{MUTED}" stroke-width="0.6" fill="none">{drops}</g>'
        f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
        f'{bar(0, 62, b2, [f"url(#{pid}a1)", f"url(#{pid}b1)"])}{live_seg(X, s, b2, bh)}'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}</g>'
        f'<g fill="{INK}" style="{SVGLAB6}"><text x="0" y="{b1 + 14}">BEFORE</text><text x="0" y="{b2 + 14}">AFTER</text></g>'
        f'<g fill="{INK}" style="{SVGLAB}">{tl}<text x="{CW8}" y="{axis + 20}" text-anchor="end">SOLAR MASSES</text>'
        f'<text x="{X(65) + 10:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 10:.1f}" y="{b2 + 20}">WAVES</text></g>'
        f'<g fill="{INK}" style="{NUM25}">'
        f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
        f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text><text x="{X(63.5):.1f}" y="{b2 - 7}" text-anchor="middle">3</text>'
        f'</g></svg>'
    )


def range_bar(pid="fr"):
    s = (CW - 62) / 600
    X = lambda v: v * s
    ax = 44
    ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ax}" x2="{X(v):.1f}" y2="{ax + (7 if v % 200 == 0 else 4)}"></line>' for v in range(0, 601, 50))
    tl = "".join(f'<text x="{X(v):.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 200, 400, 600))
    drop = f"animation: drop 260ms {PRESS} {at(T_F2)} both"
    return (
        f'<svg viewBox="0 0 {CW} 70" width="{CW}" height="70" role="img" aria-label="Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570, on a scale from 0 to 600" style="{FIGSVG}">'
        f'<defs>{patterns(pid, INK, tones={"a2": (A1, 0.46)})}</defs>'
        f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="url(#{pid}a2)"></rect>'
        f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="none" stroke="{INK}" stroke-width="0.9"></rect>'
        f'<g style="{drop}"><line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{STOCK}" stroke-width="7"></line>'
        f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{LIVE}" stroke-width="2"></line>'
        f'<circle cx="{X(410):.1f}" cy="9" r="3.6" fill="{LIVE}"></circle></g>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{X(600):.1f}" y2="{ax}"></line>{ticks}</g>'
        f'<g fill="{INK}" style="{SVGLAB}">{tl}<text x="{CW}" y="{ax + 20}" text-anchor="end">Mpc</text>'
        f'<text x="{X(230):.1f}" y="11" text-anchor="middle">230</text><text x="{X(570):.1f}" y="11" text-anchor="middle">570</text></g>'
        f'</svg>'
    )


def fig_detectors(pid="fd"):
    """Fig. 1 of the excerpt: the explainer's own drawing of when the wave reached each detector
    (ifo_when() in scratch/explainer/explainer.py) at column width. The wave as an engraved
    field, the two detectors as tube drawings with their end stations over it, and under the
    band, on open ground, the gap between arrivals as the live beam on a ruler of milliseconds."""
    s, x0 = 29.0, 14.0
    X = lambda v: x0 + v * s
    N = 22                       # room for the two names above the band
    a, band, tube = 112, 160, 5
    cy = N + 140
    by, ry = N + band + 32, N + band + 62
    H = ry + 26

    def det(cx):
        return (
            f'<rect x="{cx - tube / 2:.1f}" y="{cy - 6 - a}" width="{tube}" height="{a}"></rect>'
            f'<rect x="{cx - 4:.1f}" y="{cy - 6 - a - 8}" width="8" height="8"></rect>'
            f'<rect x="{cx + 6:.1f}" y="{cy - tube / 2}" width="{a}" height="{tube}"></rect>'
            f'<rect x="{cx + 6 + a:.1f}" y="{cy - 4}" width="8" height="8"></rect>'
            f'<rect x="{cx - 6:.1f}" y="{cy - 6}" width="12" height="12"></rect>'
        )

    (wdefs, wmarks), _ = print_layers(pid, -162.0, 250.0, CW, band, taper=False, rot=18, rmin=150.0)
    ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ry}" x2="{X(v):.1f}" y2="{ry + (7 if v % 5 == 0 else 4)}"></line>' for v in range(0, 11))
    tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="middle">{v}</text>' for v in (0, 5, 10))
    bd = f"M{X(0):.1f} {by}H{X(7):.1f}"
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    sweep = f"{SWEEP_DASH}; animation: sweep 600ms linear {at(T_F1)} both"
    pen = f"offset-path: path('{bd}'); offset-distance: 100%; offset-rotate: 0deg; animation: travel 600ms linear {at(T_F1)} both"
    return (
        f'<svg viewBox="0 0 {CW} {H}" width="{CW}" height="{H}" role="img" aria-label="Illustration, not to scale: a wave crossing the two detectors. '
        f'It reaches Livingston, Louisiana first and Hanford, Washington about 7 milliseconds later." style="{FIGSVG}">'
        f'<defs>{wdefs}<clipPath id="{pid}band"><rect x="0" y="0" width="{CW}" height="{band}"></rect></clipPath>'
        f'<clipPath id="{pid}rail"><rect x="0" y="{ry - 0.5}" width="{CW}" height="8"></rect></clipPath></defs>'
        f'<g fill="{INK}" style="{SVGLAB6}"><text x="0" y="10">LIVINGSTON, LOUISIANA</text><text x="{X(7) - x0:.1f}" y="10">HANFORD, WASHINGTON</text></g>'
        f'<g transform="translate(0 {N})" clip-path="url(#{pid}band)">{wmarks}</g>'
        f'<g fill="{STOCK}" stroke="{STOCK}" stroke-width="6" stroke-linejoin="round">{det(X(0))}{det(X(7))}</g>'
        f'<g fill="{STOCK}" stroke="{INK}" stroke-width="1.1">{det(X(0))}{det(X(7))}</g>'
        f'<g fill="none" stroke="{MUTED}" stroke-width="0.6">'
        f'<line x1="{X(0):.1f}" y1="{N + band}" x2="{X(0):.1f}" y2="{ry}"></line><line x1="{X(7):.1f}" y1="{N + band}" x2="{X(7):.1f}" y2="{ry}"></line></g>'
        f'<g fill="none" stroke="{STOCK}" stroke-width="5"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{N + band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{N + band}"></line></g>'
        f'<g fill="none" stroke="{INK}" stroke-width="0.6"><line x1="{X(0):.1f}" y1="{cy + 6}" x2="{X(0):.1f}" y2="{N + band}"></line><line x1="{X(7):.1f}" y1="{cy + 6}" x2="{X(7):.1f}" y2="{N + band}"></line></g>'
        f'<path d="{bd}" {line} stroke="{STOCK}" stroke-width="7" style="{sweep}"></path>'
        f'<line x1="{X(0):.1f}" y1="{by - 5}" x2="{X(0):.1f}" y2="{by + 5}" stroke="{LIVE}" stroke-width="2"></line>'
        f'<path d="{bd}" {line} stroke="{LIVE}" stroke-width="1.9" style="{sweep}"></path>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="{ry}" x2="{CW}" y2="{ry}"></line>{ticks}</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{INK}" stroke-width="9"></line></g></g>'
        f'<g fill="{INK}" style="{SVGLAB}">{tl}<text x="{X(10) + 16:.1f}" y="{ry + 20}">MS</text>'
        f'<text x="{X(0) + 9:.1f}" y="{by - 10}">ABOUT 7 MILLISECONDS LATER</text></g>'
        f'<g style="{pen}"><line x1="0" y1="-5" x2="0" y2="5" stroke="{LIVE}" stroke-width="2"></line></g>'
        f'<circle r="3.6" fill="{LIVE}" style="{pen}"></circle>'
        f'</svg>'
    )


def range_mini(pid="fq"):
    """The same range at ledger size, as in the explainer's ledger: 120 px for 0 to 600 megaparsecs."""
    s = 120 / 600
    X = lambda v: 1 + v * s
    return (
        f'<svg viewBox="0 0 124 30" width="124" height="30" role="img" aria-label="The distance drawn: a band from 230 to 570 megaparsecs with a mark at 410, on a line from 0 to 600" style="display: block; flex: none">'
        f'<defs>{patterns(pid, INK, tones={"a2": (A1, 0.46)})}</defs>'
        f'<rect x="{X(230):.1f}" y="10" width="{340 * s:.1f}" height="11" fill="url(#{pid}a2)"></rect>'
        f'<rect x="{X(230):.1f}" y="10" width="{340 * s:.1f}" height="11" fill="none" stroke="{INK}" stroke-width="0.9"></rect>'
        f'<line x1="{X(410):.1f}" y1="5" x2="{X(410):.1f}" y2="26" stroke="{STOCK}" stroke-width="6"></line>'
        f'<line x1="{X(410):.1f}" y1="5" x2="{X(410):.1f}" y2="26" stroke="{LIVE}" stroke-width="2"></line>'
        f'<circle cx="{X(410):.1f}" cy="5" r="3.2" fill="{LIVE}"></circle>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{X(0):.1f}" y1="26" x2="{X(600):.1f}" y2="26"></line>'
        f'<line x1="{X(0):.1f}" y1="22" x2="{X(0):.1f}" y2="26"></line><line x1="{X(600):.1f}" y1="22" x2="{X(600):.1f}" y2="26"></line></g>'
        f'</svg>'
    )


def swatch(pid, tone="a2"):
    return (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><defs>{patterns(pid, INK)}</defs>'
            f'<rect width="22" height="10" fill="url(#{pid}{tone})"></rect>'
            f'<rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{INK}" stroke-width="0.9"></rect></svg>')


LEGEND_DOT = f'<span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: {LIVE}"></span>'


def fig_head(left, right):
    return (f'{HAIR}<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-top: 10px">'
            f'<div style="{lab(INK, 600)}">{left}</div><div style="{lab()}; text-align: right">{right}</div></div>')


def ledger_row(label, value, note="", value_style=None, extra=""):
    n = f'<div style="{t1("var(--fs-note)", 1.4, italic=True)}; text-wrap: {"balance" if extra else "pretty"}">{note}</div>' if note else ""
    if extra:
        n = f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 16px">{n}{extra}</div>'
    vs = value_style or f"{d1(30, 1)}; font-variant-numeric: lining-nums; text-align: right"
    return (f'<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {INK}">'
            f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
            f'<div style="{lab()}; flex: none">{label}</div><div style="{vs}">{value}</div></div>{n}</div>')


UNIT = lambda t: f'<span style="{t1(15, 1, italic=True)}; margin-left: 6px">{t}</span>'


# ------------------------------------------------------------------ the feed, as a flat sheet (a picture, not controls)
def rate_pic(icon, label, on=False, size=16, extra="", pad="0 12px", gap="9px"):
    """A rating button as a picture. Stamped (on) follows the feed boards: the fill is one step
    down from the primary slab (ink-muted) and the plus becomes a check."""
    bg, fg, bd = (MUTED, STOCK, MUTED) if on else ("transparent", INK, INK)
    icon = CHECK if on else icon
    return (f'<span style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; border: 1px solid {bd}; '
            f'color: {fg}; padding: {pad}; display: flex; align-items: center; justify-content: center; gap: {gap}; white-space: nowrap{extra}">'
            f'{icon}<span style="{t1(size, 1, weight=500)}">{label}</span></span>')


def journal_pic(label, tall=True):
    mh = "min-height: 44px; " if tall else ""
    return (f'<span style="{mh}display: inline-flex; align-items: center; gap: 5px; {t1(15, 1.15, italic=True)}; '
            f'text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</span>')


SHEET_H = int(os.environ.get("PB_SHEET_H", "844"))
SHEET_FS = float(os.environ.get("PB_SHEET_FS", "38"))


def sheet():
    fs = SHEET_FS
    it = d4(fs, 0.98, stretch="87.5%")
    it44 = d4(44, 0.98)
    M = 20
    return f"""<div role="img" aria-label="The Paperboy feed on a phone. First card: Space, peer-reviewed, The Astrophysical Journal Letters. Headline: The first picture of a black hole's shadow. A plate shows the bright ring, 42 microarcseconds across. Buttons: See it explained, More like this, Less like this. The next card is Biology, peer-reviewed, Nature: A neural network learned to fold proteins." style="zoom: var(--sz); width: 390px; padding-bottom: 16px; flex: none; border: 1px solid {INK}; overflow: hidden; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">
<div aria-hidden="true" style="display: flex; flex-direction: column">
<div style="padding: 8px {M}px 0; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 10px">
<div style="padding-bottom: 4px; line-height: 1">{wordmark(33, "6px", "3px")}</div>
<div style="margin-left: auto; text-align: right; {lab(MUTED, 500, 10.5, 1.35)}">Science and math,<br>newly released</div>
<span style="width: 44px; height: 44px; margin-right: -11px; display: flex; align-items: center; justify-content: center">{THEME}</span>
</div>
{DOUBLE}
</div>
<div style="display: flex; flex-wrap: wrap; align-items: center; column-gap: 6px; row-gap: 6px; padding: 13px {M}px 0">
{tag_outline("Space", 10)}{tag_solid("Peer-reviewed", 10)}
<span style="flex: 1 1 auto; display: flex; justify-content: flex-end; margin: -13px 0">{journal_pic("The Astrophysical Journal Letters")}</span>
</div>
<div style="padding: 6px {M}px 0; {d1(fs, 0.98)}">
<span style="display: block; white-space: nowrap">The first picture of</span>
<span style="display: block; white-space: nowrap; {it}">a black hole's shadow.</span>
</div>
{plate_m87()}
<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px {M}px 0">
<div style="display: flex; align-items: flex-end; gap: 10px">
<div style="{d1(44, 0.86)}; font-variant-numeric: lining-nums">42</div>
<div style="{lab(MUTED, 500, 10.5, 1.4)}; padding-bottom: 1px">Microarcseconds<br>across</div>
</div>
<div style="text-align: right; {lab(MUTED, 500, 10.5, 1.4)}">Plate 3<br>Illustration,<br>not to scale</div>
</div>
<div style="padding: 10px {M}px 0; {t1(16, 1.42)}; text-wrap: pretty">Eight radio telescopes observing together imaged a bright ring around the black hole in galaxy M87, about 55 million light years away.</div>
<div style="display: flex; flex-direction: column; gap: 8px; padding: 14px {M}px 0">
<span style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {INK}; color: {STOCK}; {d3()}"><span>See it explained</span>{ARROW}</span>
<div style="display: flex; gap: 8px">{rate_pic(PLUS, "More like this")}{rate_pic(MINUS, "Less like this")}</div>
</div>
<div style="margin: 18px {M}px 0; height: 0.75px; background-color: {INK}"></div>
<div style="margin: 2px {M}px 0; height: 3px; background-color: {INK}"></div>
<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Biology", 10)}{tag_solid("Peer-reviewed", 10)}
<span style="margin: -13px 0 -13px auto">{journal_pic("Nature")}</span>
</div>
<div style="padding: 10px {M}px 0; {d1(44, 0.98)}">
<span style="display: block">A neural network</span>
<span style="display: block">learned <span style="{it44}">to fold</span></span>
<span style="display: block; {it44}">proteins.</span>
</div>
</div>
</div>"""


# ------------------------------------------------------------------ "How an explainer is made": one line through three plates
MK_W, MK_H = 400, 132


def made_rings(passes):
    """The ring field of the made figure, from the shared generator, drawn at fixed scale and
    anchored to the right edge of its plate. Plates 2 and 3 show the same drawing at two
    stages: plate 2 its hairline passes only (the visuals, being built), plate 3 with the
    swells too (finished), the pen point parked at its center."""
    (_, blue), _ = print_layers("mk", MK_W, MK_H / 2, MK_W, MK_H, k=0.42, taper=False)
    parts = [x + "</path>" for x in blue.split("</path>") if x]
    marks = "".join(parts[:2] if passes == 1 else parts)
    return (f'<svg viewBox="0 0 {MK_W} {MK_H}" width="{MK_W}" height="{MK_H}" aria-hidden="true" '
            f'style="position: absolute; top: 50%; margin-top: -{MK_H / 2}px; right: 0">{marks}</svg>')


def made_text():
    """Plate 1: the paper, as lines of text. A title, an author line, then paragraphs."""
    out = [f'<line x1="0" y1="9" x2="82%" y2="9" stroke-width="2.6"></line>',
           f'<line x1="0" y1="16.5" x2="54%" y2="16.5" stroke-width="2.6"></line>',
           f'<line x1="0" y1="27" x2="38%" y2="27" stroke-width="0.9"></line>']
    ends = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 46, 100, 100, 100, 100, 100, 100, 100, 100, 72, 100, 100, 100, 100, 100, 100, 100]
    y, first = 38.0, True
    for e in ends:
        x1 = "5%" if first else "0"
        out.append(f'<line x1="{x1}" y1="{y:.1f}" x2="{e}%" y2="{y:.1f}"></line>')
        first = e < 100
        y += 4.5
    return (f'<svg width="100%" height="{MK_H + 40}" aria-hidden="true" style="position: absolute; left: 0; top: 0">'
            f'<g stroke="{INK}" stroke-width="0.8" fill="none">{"".join(out)}</g></svg>')


def made_figure():
    col = "calc((100% - 48px) / 3)"
    sweep_ms = 1600
    grow = f"transform-origin: 0 50%; animation: growx {sweep_ms}ms linear {at(T_MADE)} both"
    ride = f"animation: ridex {sweep_ms}ms linear {at(T_MADE)} both"
    plate = "position: absolute; top: 0; bottom: 0; overflow: hidden"
    return (
        f'<div role="img" aria-label="Illustration: one line runs left to right through three plates. In the first, lines of text: the paper. In the second, a field of fine rings: the visuals, being built. In the third, the same rings at full strength: the finished explainer. A pen point rests at the end of the line." '
        f'style="position: relative; height: var(--mk-h); margin-top: 14px">'
        f'<div style="{plate}; left: 0; width: {col}">{made_text()}</div>'
        f'<div style="{plate}; left: calc((100% + 24px) / 3); width: {col}">{made_rings(1)}</div>'
        f'<div style="{plate}; right: 0; width: {col}">{made_rings(3)}</div>'
        f'<div aria-hidden="true" style="position: absolute; left: 0; right: 0; top: 50%; height: 0">'
        f'<div style="position: absolute; left: 0; right: 0; top: -3.5px; height: 7px; background-color: {STOCK}; {grow}"></div>'
        f'<div style="position: absolute; left: 0; right: 0; top: -0.95px; height: 1.9px; background-color: {LIVE}; {grow}"></div>'
        f'<div style="position: absolute; left: 0; right: 0; top: 0; height: 0; {ride}">'
        f'<div style="position: absolute; left: 100%; top: 0; width: 13px; height: 13px; margin: -6.5px 0 0 -6.5px; border-radius: 50%; background-color: {STOCK}"></div>'
        f'<div style="position: absolute; left: 100%; top: 0; width: 7px; height: 7px; margin: -3.5px 0 0 -3.5px; border-radius: 50%; background-color: {LIVE}"></div></div>'
        f'</div></div>'
    )


def made_step(n, statement):
    return (f'<div style="display: flex; flex-direction: column; gap: 8px; padding: var(--step-pad); border-top: var(--step-rule)">'
            f'<div style="{lab(INK, 600)}">Agent {n} <span style="color: {MUTED}; font-weight: 500">of 3</span></div>'
            f'<div style="{d1(30, 1.02)}">{statement}</div></div>')


# ------------------------------------------------------------------ page
def feat_row(label, specimen, note, last=False, spec_style="flex: none"):
    spec = f'<div style="margin-left: auto; {spec_style}">{specimen}</div>' if specimen else ""
    return (f'<div style="display: flex; flex-direction: column; gap: 9px; padding: 14px 0 {0 if last else 16}px; border-top: 0.75px solid {INK}">'
            f'<div style="display: flex; flex-wrap: wrap; align-items: center; column-gap: 16px; row-gap: 10px">'
            f'<div style="{lab()}; flex: none">{label}</div>{spec}</div>'
            f'<div style="{NOTE}; text-wrap: pretty">{note}</div></div>')


def build():
    press = lambda i: f"animation: press 190ms {PRESS} {at(i * 50)} both"
    WRAP = "max-width: var(--wrap); margin-left: auto; margin-right: auto; padding-left: var(--m); padding-right: var(--m); box-sizing: border-box"
    SH = d1("var(--fs-sec)", "var(--lh-sec)")
    SHI = d4("var(--fs-sec)", "var(--lh-sec)")
    BODY = t1()
    G12 = "display: grid; grid-template-columns: var(--g12); column-gap: 24px"
    I30 = d4(30, 1.02)

    def sec_head(slug, right=""):
        r = f'<div style="{lab()}; text-align: right">{right}</div>' if right else ""
        return (f'{DOUBLE}<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-top: 12px">'
                f'<div style="{lab(INK, 600)}">{slug}</div>{r}</div>')

    cta_a = (f'<div style="{lab()}; margin-bottom: 8px">Android APK, from GitHub Releases</div>'
             f'{slab("Download the APK", RELEASES)}')
    cta_b = (f'{outline("Source on GitHub", GITHUB)}'
             f'<p style="margin: 10px 0 0; {t1("var(--fs-note)", 1.4, italic=True)}">Not on Google Play yet.</p>')

    hero_L = plate_gw("hl", 1900, 320, 0, 1088, 1.6, 104, 46, 62, 0.005, 0.05, "wipeL", lab_px=11, sweep_ms=2100)
    hero_N = plate_gw("hn", 1160, 284, 20, 870, 1.42, 92, 41, 56, 0.005, 0.05, "wipeN", sweep_ms=2000)
    hero_M = plate_gw("hm", 930, 250, 20, 640, 1.25, 80, 36, 50, 0.01, 0.05, "wipeM")
    hero_S = plate_gw("hs", 700, 196, 20, 330, 1.0, 62, 29, 39, 0.025, 0.1, "wipeS")
    turn = "display: var(--d-turn)"
    AREA = "auto / 1 / auto / -1"
    win = lambda v, area: f"grid-area: {area}; height: var(--h-{v}); visibility: var(--v-{v}); overflow: hidden; margin-top: var(--plate-mt)"

    body = f"""<div id="top" style="background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="{WRAP}; width: 100%; padding-top: var(--mast-pt); display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 10px">
<a href="#top" aria-label="Paperboy" style="display: inline-block; text-decoration: none; padding: var(--wm-pad); line-height: 1; white-space: nowrap">{wordmark("var(--fs-wm)", "var(--wm-dot)", "3px")}</a>
<nav aria-label="Site" style="margin-left: auto; display: flex; align-items: center; gap: var(--nav-gap)">
<span style="display: var(--d-src)">{textlink('Source<span style="display: var(--d-wi)"> on GitHub</span>', GITHUB)}</span>
{textlink('Download<span style="display: var(--d-wi)"> the APK</span>', RELEASES, DOWN_S)}
</nav>
</div>
{DOUBLE}
</header>

<main style="display: flex; flex-direction: column">

<section aria-label="Paperboy" style="display: grid; grid-template-columns: var(--hero-cols); grid-template-rows: var(--hero-rows); padding-top: var(--hero-pt)">
<h1 style="grid-area: var(--ga-h1); margin: 0; {d1("var(--fs-display)", "var(--lh-display)")}">
<span style="display: block; {press(0)}">New science<span style="display: var(--d-ph)"> and</span></span>
<span style="display: block; {press(1)}"><span style="display: var(--d-wi)">and </span>math papers,</span>
<span style="display: block; white-space: nowrap; {press(2)}; {d4("var(--fs-display)", "var(--lh-display)", stretch="var(--it-st)")}">explained in pictures.</span>
</h1>
<div style="grid-area: var(--ga-ca); align-self: end; display: flex; flex-direction: column; max-width: var(--cta-max); padding-top: var(--ca-pt)">
{cta_a}
</div>
<div style="grid-area: var(--ga-cb); display: flex; flex-direction: column; max-width: var(--cta-max); padding-top: var(--cb-pt); padding-bottom: var(--cb-pb)">
{cta_b}
</div>
<div style="{win("s", "3 / 1 / 4 / 6")}">{hero_S}</div>
<div style="{win("m", "3 / 1 / 4 / 6")}">{hero_M}</div>
<div style="{win("n", "3 / 1 / 4 / 6")}">{hero_N}</div>
<div style="{win("l", "3 / 2 / 4 / 6")}">{hero_L}</div>
<div style="grid-area: var(--ga-under); display: grid; grid-template-columns: var(--under-cols); grid-template-rows: var(--under-rows); column-gap: 24px; row-gap: 10px; padding-top: 6px; align-items: start">
<div style="grid-area: var(--ga-u1); display: flex; flex-direction: column; gap: 3px">
<div style="{d1("var(--fs-readout)", 1)}; font-variant-numeric: lining-nums; white-space: nowrap">1.0{TIMES}10<sup style="{SUP}">−21</sup></div>
<div style="{lab()}"><span style="display: inline-block">Peak strain.&nbsp;</span><span style="display: inline-block">Pitch 35 to 250 Hz</span></div>
</div>
<div style="grid-area: var(--ga-u3); text-align: right; align-self: var(--as-u3); padding-top: var(--u3-pt); {lab(MUTED, 500, "var(--fs-label)", 1.4)}">Plate 1<br>Illustration,<br>not to scale</div>
<div style="grid-area: var(--ga-u4); display: flex; flex-direction: column; align-items: flex-start">
<p style="margin: 0; {t1("var(--fs-note)", 1.4, italic=True)}; text-wrap: pretty">From the explainer for Observation of Gravitational Waves from a Binary Black Hole Merger.</p>
{textlink("Physical Review Letters", "#paper", extra="; margin: -6px 0 -10px")}
</div>
<p style="grid-area: var(--ga-u2); margin: 0; padding-top: var(--deck-pt); max-width: 34em; {BODY}; text-wrap: pretty">Paperboy is a feed of newly released science and math papers for Android. Papers with a free legal full text get a visual explainer. Every card links to the original paper.</p>
</div>
</section>

<section aria-labelledby="h-feed" style="{WRAP}; width: 100%; margin-top: var(--sec)">
{sec_head("The feed", "Free. No account. No ads.")}
<div style="{G12}; grid-template-rows: var(--feed-rows); margin-top: var(--head-mt)">
<div style="grid-area: var(--ga-fa); display: flex; flex-direction: column">
<h2 id="h-feed" style="margin: 0; {SH}"><span style="display: block">Science and math,</span><span style="display: block">newly released.</span><span style="display: block; {SHI}">Peer-reviewed</span><span style="display: block; {SHI}">and preprints.</span></h2>
<p style="margin: var(--p-mt) 0 0; max-width: 30em; {BODY}; text-wrap: pretty">Each card says what kind of paper it is, links to the paper itself, and takes one tap to rate.</p>
</div>
<div style="grid-area: var(--ga-fs); justify-self: var(--js-sheet); margin-top: var(--stack)">{sheet()}</div>
<div style="grid-area: var(--ga-fl); align-self: end; display: flex; flex-direction: column; margin-top: var(--stack)">
{feat_row("Labeled", f'<span style="display: flex; align-items: center; gap: 6px">{tag_solid("Peer-reviewed")}{tag_screen("Preprint")}</span>', "Every paper carries one of these two tags. Solid means reviewed. Screened means not yet.")}
{feat_row("Linked", journal_pic("Physical Review Letters", tall=False), "Every card links to the original paper.")}
{feat_row("Tuned", f'<span role="img" aria-label="The two rating buttons: More like this, shown chosen, and Less like this" style="display: flex; gap: 8px">{rate_pic(PLUS, "More like this", on=True, pad="var(--rate-pad)", gap="var(--rate-gap)")}{rate_pic(MINUS, "Less like this", pad="var(--rate-pad)", gap="var(--rate-gap)")}</span>', 'More like this and Less like this tune the feed. It <span style="white-space: nowrap">re-ranks</span> on the phone.', spec_style="flex: 1 1 300px; max-width: var(--spec-max)")}
{feat_row("Your ratings", "", "Ratings stay on the phone.")}
{feat_row("Paywalled", f'<span role="img" aria-label="The outline button on a short card: Read the paper" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; gap: 28px; padding: 0 14px 0 16px; border: 1px solid {INK}; white-space: nowrap; {d3()}"><span>Read the paper</span>{OUT15}</span>', "Paywalled papers get a short card: no explainer, and a link out to the paper.", last=True)}
</div>
</div>
</section>

<section aria-labelledby="h-exp" style="{WRAP}; width: 100%; margin-top: var(--sec)">
{sec_head("The explainer")}
<h2 id="h-exp" style="margin: var(--head-mt) 0 0; {SH}"><span style="display: block; text-wrap: balance">Papers with a free full text</span><span style="display: block; {SHI}">get a visual explainer.</span></h2>
<p style="margin: var(--p-mt) 0 0; max-width: 30em; {BODY}; text-wrap: pretty">A page of diagrams, charts drawn from the paper's reported numbers, and plain text. Here is part of one.</p>

<div style="margin-top: var(--exc-mt)">{HAIR}</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; column-gap: 24px; row-gap: 2px; margin-top: 10px">
<div style="{lab(INK, 600)}">Excerpt</div>
<div style="{t1("var(--fs-note)", 1.4, italic=True)}">Observation of Gravitational Waves from a Binary Black Hole Merger</div>
</div>

<div style="{G12}; row-gap: 40px; margin-top: 40px; align-items: start">

<div style="grid-area: var(--ga-xk); display: flex; flex-direction: column">
<div style="{lab(INK, 600)}">Key idea</div>
<p style="margin: 12px 0 0; {d4("var(--fs-key)", "var(--lh-key)")}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</div>

<div style="grid-area: var(--ga-xa); display: flex; flex-direction: column">
<p style="margin: 0; {BODY}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. The signal reached Livingston about 7 milliseconds before Hanford.</p>
<div style="margin-top: 28px; display: flex; flex-direction: column">
{fig_head("Fig. 1", "Illustration, not to scale")}
{figbox(fig_detectors())}
<p style="margin: 8px 0 0; {t1("var(--fs-note)", 1.4, italic=True)}; text-wrap: pretty">Each detector is an L with two 4 km arms.</p>
</div>
</div>

<div style="grid-area: var(--ga-xb); display: flex; flex-direction: column">
<p style="margin: 0; {BODY}; text-wrap: pretty">The signal's shape matches black holes of about 36 and 29 solar masses spiraling into one, about 410 megaparsecs away.†</p>
<div style="width: 64px; height: 0.75px; background-color: {INK}; margin-top: 16px"></div>
<p style="margin: 10px 0 0; {t1("var(--fs-note)", 1.4, italic=True)}; text-wrap: pretty">† The distance carries a wide error range, roughly 230 to 570 megaparsecs.</p>
<div style="margin-top: 28px; display: flex; flex-direction: column">
{fig_head("Fig. 2", "Data, from the paper")}
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div style="{d1("var(--fs-xl)", "var(--lh-xl)")}; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px"><div style="{lab(INK, 600)}">Megaparsecs away</div><div style="{t1(15, 1.3, italic=True)}">roughly 1.3 billion light years</div></div>
</div>
{figbox(range_bar())}
<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; {lab()}">
<span style="display: inline-flex; align-items: center; gap: 6px">{LEGEND_DOT}Reported value</span>
<span style="display: inline-flex; align-items: center; gap: 6px">{swatch("k2")}Range</span>
</div>
</div>
</div>

<div style="grid-area: var(--ga-xc); display: flex; flex-direction: column">
{fig_head("Fig. 3", "Data, from the paper")}
<h3 style="margin: 10px 0 0; {d1(30, 1)}">Where the mass went</h3>
<div style="display: var(--d-f3n)">{figbox(chart_mass(), 350)}</div>
<div style="margin-top: 14px; display: var(--d-f3w)">{chart_mass_wide()}</div>
<div style="display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; column-gap: 24px; row-gap: 8px; margin-top: 10px">
<p style="margin: 0; {t1("var(--fs-note)", 1.4, italic=True)}; text-wrap: pretty">About 3 solar masses of energy left as gravitational waves.</p>
<div style="display: inline-flex; align-items: center; gap: 6px; {lab()}">{swatch("k1")}An estimate</div>
</div>
</div>

<div style="grid-area: var(--ga-xl); display: flex; flex-direction: column">
{DOUBLE}
<h3 style="margin: 12px 0 12px; {d1(30, 1)}">How sure <span style="{d4(30, 1.06)}">is this?</span></h3>
{ledger_row("Review", tag_solid("Peer-reviewed"), value_style="display: flex")}
{ledger_row("Significance", GT + "5.1" + UNIT("sigma"), "A false alarm this strong is expected less than once in 203,000 years.")}
{ledger_row("Sky position", "600" + UNIT("square degrees"), "Known only to within about this much sky.")}
{ledger_row("Distance", "410" + UNIT("megaparsecs"), "With a range of roughly 230 to 570.", extra=range_mini())}
<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 0 0; border-top: 0.75px solid {INK}">
<div style="{lab()}">This explainer</div>
<p style="margin: 0; {BODY}; text-wrap: pretty">Machine written, and it can be wrong. Check it against the paper.</p>
</div>
</div>

<div style="grid-area: var(--ga-xs); align-self: stretch; display: flex; flex-direction: column">
{DOUBLE}
<div id="paper" style="margin-top: 12px; {lab(INK, 600)}">Source</div>
<p style="margin: 8px 0 0; {t1(17, 1.4, italic=True)}; text-wrap: pretty">Observation of Gravitational Waves from a Binary Black Hole Merger</p>
<p style="margin: 6px 0 0; {t1(15, 1.4)}; color: {MUTED}; text-wrap: pretty">B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)</p>
<div style="margin-top: 8px; display: flex; flex-direction: column; gap: 3px"><div style="{lab()}">Physical Review Letters 116, 061102</div><div style="{lab()}">February 11, 2016. Peer-reviewed. CC BY 3.0</div></div>
<div style="margin-top: auto; padding-top: 14px">{outline("Read the paper", "#paper")}</div>
</div>

</div>
</section>

<section aria-labelledby="h-made" style="{WRAP}; width: 100%; margin-top: var(--sec)">
{sec_head("How an explainer is made", "Machine written")}
<h2 id="h-made" style="margin: var(--head-mt) 0 0; {SH}"><span style="display: block">Three AI agents,</span><span style="display: block; {SHI}">one job each.</span></h2>
<figure style="margin: var(--exc-mt) 0 0; display: flex; flex-direction: column">
{fig_head("Paper in, explainer out", "Illustration")}
{made_figure()}
<div style="display: grid; grid-template-columns: var(--g3); column-gap: 24px; margin-top: var(--step-mt)">
{made_step(1, f'<span style="display: block">Reads the paper</span><span style="display: block; text-wrap: balance; {I30}">as a domain expert.</span>')}
{made_step(2, f'Builds <span style="{I30}">the visuals.</span>')}
{made_step(3, f'<span style="display: block; text-wrap: balance">Checks every number against the paper,</span><span style="display: block; text-wrap: balance; {I30}">and checks the visuals are clear.</span>')}
</div>
</figure>
<div style="{G12}; row-gap: 10px; margin-top: 40px; padding: var(--row-pt) 0 0; border-top: 0.75px solid {INK}; align-items: baseline">
<div style="grid-column: var(--k-1-4); {lab()}">Every explainer</div>
<div style="grid-column: var(--k-5-8); display: flex; flex-direction: column">
<p style="margin: 0; {d4("var(--fs-key)", "var(--lh-key)")}; text-wrap: balance">Machine written, and it can be wrong.</p>
<p style="margin: 14px 0 0; max-width: 34em; {BODY}; text-wrap: pretty">The page says so, and links the source so you can check it against the paper.</p>
</div>
</div>
</section>

<section aria-labelledby="h-get" style="{WRAP}; width: 100%; margin-top: var(--sec)">
{sec_head("Download")}
<div style="{G12}; margin-top: var(--head-mt); align-items: end">
<h2 id="h-get" style="grid-column: var(--k-1-8); margin: 0; {d1("var(--fs-headline)", "var(--lh-headline)")}"><span style="display: block"><span style="{turn}">No account. </span><span style="{turn}">No ads.</span></span><span style="display: block; {d4("var(--fs-headline)", "var(--lh-headline)")}; text-wrap: balance">Free and open source.</span></h2>
<div style="grid-column: var(--k-9-4); justify-self: var(--js-sheet); width: 100%; display: flex; flex-direction: column; max-width: var(--cta-max); margin-top: var(--stack)">
{cta_a}<div style="height: 8px"></div>{cta_b}
</div>
</div>
</section>

</main>

<footer style="{WRAP}; width: 100%; margin-top: var(--sec); padding-bottom: 40px; display: flex; flex-direction: column">
{HAIR}
<div style="{G12}; align-items: end; padding-top: var(--foot-pt)">
<div aria-hidden="true" style="grid-column: var(--k-1-8); font-size: var(--fs-wm-xl); line-height: 1; white-space: nowrap; padding-bottom: 0.12em">{wordmark("1em", "0.147em", "0.067em", ls=(-0.012, -0.025))}</div>
<div style="grid-column: var(--k-9-4); display: flex; flex-direction: column; margin-top: var(--stack); padding-bottom: var(--foot-pb)">
<div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; column-gap: 16px; border-top: 0.75px solid {INK}">
<div style="{lab()}; flex: none">Source</div>
{textlink("github.com/NtrpyDev/paperboy-app", GITHUB)}
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 44px; border-top: 0.75px solid {INK}">
<div style="{lab()}; flex: none">Site</div>
<div style="{t1("var(--fs-note)", 1, italic=True)}">[YOUR DOMAIN]</div>
</div>
</div>
</div>
</footer>
</div>"""

    css = f"""body{{margin:0;background:{STOCK}}}
a{{color:{INK}}}a:hover{{color:{MUTED}}}
a.slab:hover{{background-color:{MUTED}!important}}
a:focus-visible{{outline:2px solid {INK};outline-offset:2px}}
{KEYFRAMES}
@keyframes registerA{{from{{transform:translate(5px,-3px)}}to{{transform:none}}}}
@keyframes registerB{{from{{transform:translate(-5px,3px)}}to{{transform:none}}}}
@keyframes growx{{from{{transform:scaleX(0)}}to{{transform:none}}}}
@keyframes ridex{{from{{transform:translateX(-100%)}}to{{transform:none}}}}
@keyframes drop{{from{{opacity:0;transform:translateY(-12px)}}to{{opacity:1;transform:none}}}}
{wipe_px("wipeS", 196)}
{wipe_px("wipeM", 250)}
{wipe_px("wipeN", 284)}
{wipe_px("wipeL", 320)}
:root{{--m:20px;--wrap:100%;--sec:56px;--stack:32px;--head-mt:16px;--p-mt:14px;--mast-pt:8px;--nav-gap:16px;--hero-pt:20px;
--g12:minmax(0,1fr);--g3:minmax(0,1fr);
--fs-display:clamp(34px,10.7vw,64px);--lh-display:.98;--it-st:87.5%;--fs-headline:44px;--lh-headline:.98;
--fs-sec:30px;--lh-sec:1.02;--fs-key:30px;--lh-key:1.06;--fs-body:17px;--lh-body:1.47;--fs-note:15px;--fs-label:10.5px;--fs-tag:10px;
--fs-wm:33px;--wm-dot:6px;--wm-pad:3.5px 0 7.5px;--fs-wm-xl:clamp(60px,19.5vw,120px);--fs-readout:44px;--fs-xl:72px;--lh-xl:.86;
--h-s:230px;--v-s:visible;--h-m:0px;--v-m:hidden;--h-n:0px;--v-n:hidden;--h-l:0px;--v-l:hidden;--plate-mt:18px;
--d-wi:none;--d-ph:inline;--d-src:none;--rate-pad:0 6px;--rate-gap:6px;--d-turn:block;--sz:.71;
--hero-cols:20px minmax(0,1fr) 0px 0px 20px;--hero-rows:none;
--ga-h1:1 / 2 / 2 / 3;--ga-ca:2 / 2 / 3 / 3;--ca-pt:18px;--ga-under:4 / 2 / 5 / 3;--ga-cb:5 / 2 / 6 / 3;--cb-pt:20px;--cb-pb:0px;
--under-cols:minmax(0,1fr) auto;--under-rows:none;--ga-u1:1 / 1 / 2 / 2;--ga-u3:1 / 2 / 2 / 3;--ga-u4:2 / 1 / 3 / 3;--ga-u2:3 / 1 / 4 / 3;
--as-u3:end;--u3-pt:0px;--deck-pt:2px;
--feed-rows:none;--ga-fa:{AREA};--ga-fs:{AREA};--ga-fl:{AREA};--js-sheet:start;
--ga-xk:{AREA};--ga-xa:{AREA};--ga-xb:{AREA};--ga-xc:{AREA};--ga-xl:{AREA};--ga-xs:{AREA};--d-f3n:block;--d-f3w:none;--cta-max:400px;
--mk-h:84px;--step-mt:14px;--spec-max:100%;--step-pad:12px 0 14px;--step-rule:0.75px solid {INK};
--k-1-4:1 / -1;--k-5-8:1 / -1;--k-1-8:1 / -1;--k-9-4:1 / -1;
--exc-mt:32px;--row-pt:14px;--foot-pt:24px;--foot-pb:0px}}
@media (min-width:360px){{:root{{--sz:.81;--d-src:inline-flex;--rate-pad:0 12px;--rate-gap:9px}}}}
@media (min-width:375px){{:root{{--sz:.85}}}}
@media (min-width:390px){{:root{{--sz:.89}}}}
@media (min-width:412px){{:root{{--sz:.94}}}}
@media (min-width:432px){{:root{{--sz:1}}}}
@media (min-width:700px){{:root{{--h-s:0px;--v-s:hidden;--h-m:284px;--v-m:visible;--plate-mt:22px;--mast-pt:14px;--hero-pt:32px;
--d-wi:inline;--d-ph:none;--it-st:100%;--fs-sec:44px;--lh-sec:.98;--mk-h:108px;--spec-max:348px}}}}
@media (min-width:760px){{:root{{--sz:.89;--g12:repeat(12,minmax(0,1fr));--g3:repeat(3,minmax(0,1fr));--step-mt:12px;--step-pad:0;--step-rule:0;
--ga-fs:2 / 1 / 3 / span 6;--ga-fl:2 / 7 / 3 / span 6;
--ga-xk:1 / 1 / 2 / -1;--ga-xa:2 / 1 / 3 / span 6;--ga-xb:2 / 7 / 3 / span 6;--ga-xc:3 / 1 / 4 / span 6;--ga-xs:3 / 7 / 4 / span 6;--ga-xl:4 / 1 / 5 / -1}}}}
@media (min-width:860px){{:root{{--sz:1}}}}
@media (min-width:930px){{:root{{--h-m:0px;--v-m:hidden;--h-n:318px;--v-n:visible}}}}
@media (min-width:1160px){{:root{{--m:56px;--wrap:1200px;--sec:96px;--stack:0px;--head-mt:22px;--p-mt:20px;--mast-pt:20px;--nav-gap:28px;--hero-pt:44px;
--g12:repeat(12,minmax(0,1fr));--g3:repeat(3,minmax(0,1fr));
--fs-display:clamp(44px,7.2vw,88px);--lh-display:.94;--fs-headline:66px;--lh-headline:.95;
--fs-sec:66px;--lh-sec:.95;--fs-key:40px;--lh-key:1.04;--fs-body:19px;--lh-body:1.5;--fs-note:16px;--fs-label:11px;--fs-tag:10.5px;
--fs-wm:38px;--wm-dot:6.5px;--wm-pad:1px 0 5px;--fs-wm-xl:150px;--fs-readout:48px;--fs-xl:88px;--lh-xl:.84;
--h-n:0px;--v-n:hidden;--h-l:354px;--v-l:visible;--plate-mt:34px;--d-turn:inline;
--hero-cols:minmax(56px,1fr) minmax(0,810px) 24px minmax(0,254px) minmax(56px,1fr);--hero-rows:1fr auto;
--ga-h1:1 / 2 / 3 / 3;--ga-ca:1 / 4 / 2 / 5;--ca-pt:0px;--ga-cb:2 / 4 / 3 / 5;--cb-pt:8px;--cb-pb:8px;--ga-under:4 / 2 / 5 / 5;
--under-cols:repeat(12,minmax(0,1fr));--under-rows:auto 1fr;--ga-u1:1 / 1 / 2 / span 4;--ga-u4:2 / 1 / 3 / span 4;--ga-u2:1 / 5 / 3 / span 5;--ga-u3:1 / 10 / 2 / span 3;
--as-u3:start;--u3-pt:6px;--deck-pt:6px;
--feed-rows:auto 1fr;--ga-fa:1 / 1 / 2 / span 6;--ga-fs:1 / 8 / 3 / span 5;--ga-fl:2 / 1 / 3 / span 6;--js-sheet:end;
--ga-xk:1 / 1 / 2 / span 10;--ga-xa:2 / 1 / 3 / span 4;--ga-xb:2 / 5 / 3 / span 4;--ga-xl:2 / 9 / 3 / span 4;--ga-xc:3 / 1 / 4 / span 8;--ga-xs:3 / 9 / 4 / span 4;
--d-f3n:none;--d-f3w:block;--cta-max:254px;
--mk-h:132px;--step-mt:12px;--step-pad:0;--step-rule:0;
--k-1-4:1 / span 4;--k-5-8:5 / span 8;--k-1-8:1 / span 8;--k-9-4:9 / span 4;
--exc-mt:56px;--row-pt:20px;--foot-pt:40px;--foot-pb:22px}}}}"""
    OUT.write_text(page("Paperboy website, day", css, body, 1440, PREVIEW_H))
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
