"""Feed plates for the app feed boards.

Plate 1 is the locked plate from scratch/director/lock_proof.py, redrawn here only so the
boundary of the well figure can be softened (JURY-1 must-fix 7). Plate 2 is new: AlphaFold,
a carbon atom on an angstrom ruler, drawn to scale.

All geometry comes from scratch/engraved/lib.py or is computed here. No path data is hand-edited.
"""
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
sys.path.insert(0, str(HERE.parent / "director"))
from lib import *  # noqa: E402,F403
from lock_proof import T, BLUE, NBLUE, LAB  # noqa: E402

W, M, BAND = 390, 20, 196
PH = BAND + 34
LABEL = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"


def _first_d(markup):
    return re.search(r'<path d="([^"]+)"', markup).group(1)


def _frame(pid, blue_svg, key_svg, live_svg, ink_name, animate=True):
    """The locked layer stack: ink wipe around two registering layers, live layer on top."""
    reg_a = f"; animation: registerA 480ms {REGISTER} {at(60)} both" if animate else ""
    reg_b = f"; animation: registerB 480ms {REGISTER} {at(60)} both" if animate else ""
    ink = f"; animation: {ink_name} 520ms {PRESS} {at(60)} both" if animate else ""
    return (
        f'<div style="position: relative; width: {W}px; height: {PH}px; margin-top: 12px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {BAND}px{ink}">'
        f'<div style="position: absolute; left: 0; top: 0{reg_a}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0{reg_b}">{key_svg}</div>'
        f'</div>'
        f'{live_svg}'
        f'</div>'
    )


def _svg(inner, defs="", h=BAND):
    return (f'<svg viewBox="0 0 {W} {h}" width="{W}" height="{h}" aria-hidden="true" style="display: block">'
            f'<defs>{defs}</defs>{inner}</svg>')


# ------------------------------------------------------------------ Plate 1
def plate1(pid, theme, soft=2, animate=True, sweep_ms=1900):
    """Plate 1, gravitational waves. soft=0 is the locked plate. soft=1 thins the rings
    in two steps as they near the well figure. soft=2 also drops the outline that closed
    the figure, so the rings fade out and the contours begin, with no edge between them."""
    t = T(theme)
    day = t["day"]
    cx, cy = M + (W - 2 * M) * 0.76, 62
    y0, amp = 157, 29
    d, xm, crest = chirp(M, y0, W - 2 * M, amp)
    ruler = BAND

    wdefs, wmarks = wavefield(pid, cx, cy, W, BAND, t["plate"], rot=-25, rmax=420.0)
    if not day:
        wmarks = wmarks.replace(f'stroke="{t["plate"]}" stroke-width="0.5"', f'stroke="{t["plate"]}" stroke-width="0.6" stroke-opacity="0.55"', 1)
    key = t["key"] if day else NM
    bod = wells(pid, cx, cy, t["ground"], key, night=not day)

    if soft:
        # Two larger figures of the same family (equal pull, farther out). The heavy ring
        # pass stops at the outer one, the middle pass at the inner one, and only the
        # hairline pass runs on to the figure. Tone falls by line weight, not by opacity.
        far = _first_d(wells(pid, cx, cy, "#000", "#000", reach=74.0, n=3, samples=72))
        near = _first_d(wells(pid, cx, cy, "#000", "#000", reach=58.0, n=3, samples=72))
        wdefs = wdefs.replace("</mask>", f'<path d="{near}" fill="#000"></path></mask>', 1)
        head, tail = wdefs.rsplit("</mask>", 1)
        wdefs = head + f'<path d="{far}" fill="#000"></path></mask>' + tail
    if soft >= 2:
        # drop the last contour, which sat exactly on the edge of the knockout
        strokes = list(re.finditer(r'<path d="[^"]+" fill="none" stroke="[^"]+" stroke-width="[^"]+"></path>', bod))
        last = strokes[-1]
        bod = bod[:last.start()] + bod[last.end():]

    if day:
        key_defs = patterns(pid, t["plate"], tones={"a3": (A1, 0.68)}) + patterns(pid, t["key"], tones={"b3": (A2, 0.66)})
    else:
        key_defs = patterns(pid, NBLUE, tones={"n1": (A2, 0.34)})

    blue_svg = _svg(wmarks, wdefs)
    key_svg = _svg(bod, key_defs)

    step = (xm - M) / 10
    ticks, x, i = [], float(M), 0
    while x <= W:
        ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
        x += step
        i += 1
    live_svg = _live(
        pid, t, d, sweep_ms, animate,
        aria="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away",
        ticks="".join(ticks),
        labels=(f'<text x="{M}" y="{ruler + 20}">0</text>'
                f'<text x="{(M + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
                f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text>'),
    )
    return _frame(pid, blue_svg, key_svg, live_svg, "inkproof", animate)


def _live(pid, t, d, sweep_ms, animate, aria, ticks, labels, mid="", start=320):
    """The live layer of a hero plate, in the locked order: trap, (halo), core, ruler,
    carriage, tick labels, pen trap, (pen halo), pen point."""
    day = t["day"]
    ruler = BAND
    sweep = f"; animation: sweep {sweep_ms}ms linear {at(start)} both" if animate else ""
    ride = f"; animation: travel {sweep_ms}ms linear {at(start)} both" if animate else ""
    pulse = f"; animation: travel {sweep_ms}ms linear {at(start)} both, pulse 2400ms ease-in-out {at(max(2400, start + sweep_ms + 200))} infinite" if animate else ""
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    under = f'<path d="{d}" {line} stroke="{t["ground"]}" stroke-width="7" style="{SWEEP_DASH}{sweep}"></path>'
    if day:
        pen_under = f'<circle r="6.5" fill="{t["ground"]}" style="{pen}{ride}"></circle>'
    else:
        under += f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="7" stroke-opacity="0.22" style="{SWEEP_DASH}{sweep}"></path>'
        pen_under = (f'<circle r="8.5" fill="{t["ground"]}" style="{pen}{ride}"></circle>'
                     f'<circle r="8.5" fill="{t["live"]}" fill-opacity="0.24" style="{pen}{ride}"></circle>')
    return (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" aria-label="{aria}" style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ruler - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'{under}{mid}'
        f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{1.9 if day else 1.6}" style="{SWEEP_DASH}{sweep}"></path>'
        f'<g stroke="{t["text"]}" stroke-width="0.9" fill="none"><line x1="{M}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{ticks}</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{t["text"]}" stroke-width="9"></line></g></g>'
        f'<g fill="{t["text"]}" style="{LABEL}">{labels}</g>'
        f'{pen_under}'
        f'<circle r="{3.6 if day else 3.4}" fill="{t["live"]}" style="{pen}{pulse}"></circle>'
        f'</svg>'
    )


# ------------------------------------------------------------------ Plate 2
def _swell(cx, cy, r, ang, pitch, tone, step=3.0):
    """A line screen whose lines swell: one closed outline per line, its width set by
    tone(x, y) as a fraction of the pitch. Returns path data."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    # line centers sit at pitch / 2 + k * pitch on the normal, measured from the origin,
    # the same phase as patterns() in lib.py
    c0 = cx * nx + cy * ny
    k0 = math.floor((c0 - r - pitch / 2) / pitch)
    out = []
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    k = k0
    while True:
        c = pitch / 2 + k * pitch
        k += 1
        dc = c - c0
        if dc > r:
            break
        if dc < -r:
            continue
        half = math.sqrt(max(0.0, r * r - dc * dc))
        if half < 1.0:
            continue
        tm = cx * ux + cy * uy
        n = max(2, int(math.ceil(2 * half / step)))
        top, bot = [], []
        for i in range(n + 1):
            tt = tm - half + 2 * half * i / n
            px, py = tt * ux + c * nx, tt * uy + c * ny
            hw = 0.5 * pitch * tone(px, py)
            top.append((px + hw * nx, py + hw * ny))
            bot.append((px - hw * nx, py - hw * ny))
        pts = top + bot[::-1]
        out.append("M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z")
    return "".join(out)


def plate2(pid, theme, field="rise", animate=True, sweep_ms=1400, s=100.0, cy=82.0, cross=True, ink_trap=0.0):
    """Plate 2, AlphaFold. One ruler in angstroms along the bottom edge. A carbon atom about
    1.4 wide stands over it, engraved as a ball in the plate ink. Under the atom, like the
    dimension lines of a drawing, the live beam rules off 0.96 and an ink beam marks the next
    best method at 2.8. All three start on one zero line. The field behind them is the same
    ruler read as tone: it steps once at every whole angstrom."""
    t = T(theme)
    day = t["day"]
    X = lambda v: M + v * s
    r = 0.7 * s
    ax = X(0.7)
    y_live, y_ink = BAND - 33, BAND - 16
    ruler = BAND
    plate, ground = t["plate"], t["ground"]
    ink = t["text"] if day else NM      # night: the black layer goes dim, as the contours of Plate 1 do

    tones = {"rise": [0.15, 0.25, 0.35, 0.45], "steps": [0.41, 0.33, 0.25, 0.17], "flat": [0.24] * 4, "none": []}[field]
    fdefs = patterns(pid, plate, tones={f"f{i}": (A1, v) for i, v in enumerate(tones)})
    edges = [0, X(1), X(2), X(3), W]
    frects = "".join(
        f'<rect x="{edges[i]:.2f}" y="0" width="{edges[i + 1] - edges[i]:.2f}" height="{BAND}" fill="url(#{pid}f{i})"></rect>'
        for i in range(len(tones))
    )

    # the atom: a screen that swells away from the light, so it reads as a ball,
    # and a second screen across it where the shade is deepest
    lx, ly, lz = -0.52, -0.60, 0.61
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    def shade(px, py):
        dx, dy = (px - ax) / r, (py - cy) / r
        z = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        lit = max(0.0, dx * lx + dy * ly + z * lz)
        return (1 - lit) ** 1.25      # same geometry by day and by night: dense is dark ink by day, bright light by night

    ball = _swell(ax, cy, r, A2, PITCH, lambda px, py: 0.10 + 0.56 * shade(px, py))
    if cross:
        ball += _swell(ax, cy, r, A1, PITCH, lambda px, py: max(0.0, shade(px, py) - 0.38) ** 1.35 * 1.25, step=3.0)
    blue_svg = _svg(
        f'{frects}<circle cx="{ax:.2f}" cy="{cy}" r="{r:.2f}" fill="{ground}"></circle>'
        f'<g clip-path="url(#{pid}atom)"><path d="{ball}" fill="{plate}"></path></g>',
        f'{fdefs}<clipPath id="{pid}atom"><circle cx="{ax:.2f}" cy="{cy}" r="{r:.2f}"></circle></clipPath>',
    )

    # black layer: the outline of the atom, the extension line of its far side, the 2.8 beam
    cap = 5
    trap = (f'<line x1="{X(0):.2f}" y1="{y_ink}" x2="{X(2.8) + ink_trap / 2:.2f}" y2="{y_ink}" stroke="{ground}" stroke-width="{ink_trap}"></line>'
            f'<line x1="{X(2.8):.2f}" y1="{y_ink - cap - 1.5}" x2="{X(2.8):.2f}" y2="{ruler}" stroke="{ground}" stroke-width="{ink_trap}"></line>') if ink_trap else ""
    key_svg = _svg(
        f'<g fill="none" stroke="{ink}">'
        f'<circle cx="{ax:.2f}" cy="{cy}" r="{r:.2f}" stroke-width="0.9"></circle>'
        f'{trap}'
        f'<g stroke-width="0.75"><line x1="{X(1.4):.2f}" y1="{cy}" x2="{X(1.4):.2f}" y2="{ruler}"></line>'
        f'<line x1="{X(2.8):.2f}" y1="{y_ink}" x2="{X(2.8):.2f}" y2="{ruler}"></line></g>'
        f'<g stroke-width="1.4"><line x1="{X(0):.2f}" y1="{y_ink}" x2="{X(2.8):.2f}" y2="{y_ink}"></line>'
        f'<line x1="{X(2.8):.2f}" y1="{y_ink - cap}" x2="{X(2.8):.2f}" y2="{y_ink + cap}"></line></g>'
        f'</g>'
    )

    d = f"M{X(0):.2f} {y_live}H{X(0.96):.2f}"
    ticks = "".join(
        f'<line x1="{X(i / 5):.2f}" y1="{ruler}" x2="{X(i / 5):.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>'
        for i in range(0, 40) if X(i / 5) <= W
    )
    labels = "".join(
        f'<text x="{X(v):.1f}" y="{ruler + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in range(0, 4)
    ) + f'<text x="{X(3) + 9:.1f}" y="{ruler + 20}">Å</text>'
    # the zero line: the ruler turned up the left side of the drawing. It sits over the
    # trap of the live beam and under its core.
    zero = f'<line x1="{X(0):.2f}" y1="{cy}" x2="{X(0):.2f}" y2="{ruler}" stroke="{ink}" stroke-width="0.9"></line>'
    live_svg = _live(
        pid, t, d, sweep_ms, animate,
        aria="Illustration drawn to scale on a ruler in angstroms: a carbon atom about 1.4 wide, AlphaFold's median error of 0.96, and the next best method at 2.8",
        ticks=ticks, labels=labels, mid=zero,
    )
    return _frame(pid, blue_svg, key_svg, live_svg, "inkproof", animate)
