"""Feed plates for the app feed boards.

Plate 1 calls the shared generator gw_print() in scratch/engraved/lib.py (the wave field
with tapered swells and no mask, the wells as open contours). Plate 2 is AlphaFold: a
carbon atom and two beams on open ground, on one angstrom ruler, drawn to scale.

All geometry comes from scratch/engraved/lib.py or is computed here. No path data is hand-edited.
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
sys.path.insert(0, str(HERE.parent / "director"))
from lib import *  # noqa: E402,F403
from lock_proof import T, BLUE, NBLUE, LAB  # noqa: E402

W, M, BAND = 390, 20, 196
PH = BAND + 34
P2BAND = 122            # Plate 2 has no field to fill, so its band is only as tall as its marks
P2H = P2BAND + 34
LABEL = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"


def chrome(t):
    """Non-text structure: rules, outlines, axes. Ink by day. At night it steps down to
    light-muted so the order on screen is text, amber, structure (CRITIQUE system fix 4)."""
    return t["text"] if t["day"] else NM


def _frame(blue_svg, key_svg, live_svg, ink_name, animate=True, band=BAND, top=12):
    """The locked layer stack: ink wipe around two registering layers, live layer on top."""
    reg_a = f"; animation: registerA 480ms {REGISTER} {at(60)} both" if animate else ""
    reg_b = f"; animation: registerB 480ms {REGISTER} {at(60)} both" if animate else ""
    ink = f"; animation: {ink_name} 520ms {PRESS} {at(60)} both" if animate else ""
    return (
        f'<div style="position: relative; width: {W}px; height: {band + 34}px; margin-top: {top}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {band}px{ink}">'
        f'<div style="position: absolute; left: 0; top: 0{reg_a}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0{reg_b}">{key_svg}</div>'
        f'</div>'
        f'{live_svg}'
        f'</div>'
    )


def _svg(inner, defs="", h=BAND):
    d = f"<defs>{defs}</defs>" if defs else ""
    return f'<svg viewBox="0 0 {W} {h}" width="{W}" height="{h}" aria-hidden="true" style="display: block">{d}{inner}</svg>'


# ------------------------------------------------------------------ Plate 1
def plate1(pid, theme, animate=True, sweep_ms=1900, top=12):
    """Plate 1, gravitational waves: the shared print layers and the chirp crossing them."""
    t = T(theme)
    cx, cy = M + (W - 2 * M) * 0.76, 62
    y0, amp = 157, 29
    d, xm, crest = chirp(M, y0, W - 2 * M, amp)
    ruler = BAND
    (bdefs, blue), (kdefs, key) = gw_print(pid, cx, cy, W, BAND, theme)

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
    return _frame(_svg(blue, bdefs), _svg(key, kdefs), live_svg, "inkproof", animate, top=top)


def _live(pid, t, d, sweep_ms, animate, aria, ticks, labels, mid="", over="", start=320, band=BAND):
    """The live layer of a hero plate, in the locked order: trap, (halo), core, ruler,
    carriage, tick labels, pen trap, (pen halo), pen point. `mid` is drawn under the core,
    `over` after the tick labels."""
    day = t["day"]
    ruler = band
    ch = chrome(t)
    sweep = f"; animation: sweep {sweep_ms}ms linear {at(start)} both" if animate else ""
    ride = f"; animation: travel {sweep_ms}ms linear {at(start)} both" if animate else ""
    pulse = f"; animation: travel {sweep_ms}ms linear {at(start)} both, pulse 2400ms ease-in-out {at(max(2400, start + sweep_ms + 200))} infinite" if animate else ""
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    return (
        f'<svg viewBox="0 0 {W} {band + 34}" width="{W}" height="{band + 34}" role="img" aria-label="{aria}" style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ruler - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'{live_under_strokes(d, day, t["ground"], t["live"], SWEEP_DASH + sweep)}{mid}'
        f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="1.9" style="{SWEEP_DASH}{sweep}"></path>'
        f'<g stroke="{ch}" stroke-width="0.9" fill="none"><line x1="{M}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{ticks}</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{t["text"]}" stroke-width="9"></line></g></g>'
        f'<g fill="{t["text"] if day else t["muted"]}" style="{LABEL}">{labels}</g>'
        f'{over}'
        f'{pen_under_marks(day, t["ground"], t["live"], pen + ride)}'
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


def plate2(pid, theme, animate=True, sweep_ms=1400, s=60.0, band=P2BAND, top=12, y_live=12.0, y_ink=27.0,
           lo=0.08, hi=0.50, cross=True):
    """Plate 2, AlphaFold, on open ground. One ruler in angstroms along the bottom. The live
    beam rules off 0.96 and an ink beam marks the next best method at 2.8, both from zero.
    Under them a carbon atom about 1.4 wide stands over the same zero, engraved as a ball.
    Each mark carries its own label. There is no field behind them."""
    t = T(theme)
    day = t["day"]
    X = lambda v: M + v * s
    r = 0.7 * s
    ax, cy = X(0.7), band - 3.0 - 0.7 * s
    ruler = band
    plate, ground = t["plate"], t["ground"]
    ink = t["text"] if day else NM          # the black layer goes dim at night, as the contours of Plate 1 do
    drop = t["muted"] if day else NS        # drop lines: ink-muted by day, structure by night (SYSTEM 4.2.3)
    cap = 5

    # the atom: a screen that swells away from the light, so it reads as a ball,
    # and a second screen across it where the shade is deepest
    lx, ly, lz = -0.52, -0.60, 0.61
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    def shade(px, py):
        dx, dy = (px - ax) / r, (py - cy) / r
        z = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        lit = max(0.0, dx * lx + dy * ly + z * lz)
        # Day is ink: the lines swell where the ball is in shade. Night is light: the lines
        # swell where the ball is lit. Same lamp, upper left, in both.
        return (1 - lit) ** 1.25 if day else lit ** 1.6

    ball = _swell(ax, cy, r, A2, PITCH, lambda px, py: lo + (hi - lo) * shade(px, py))
    if cross:
        ball += _swell(ax, cy, r, A1, PITCH, lambda px, py: max(0.0, shade(px, py) - (0.42 if day else 0.5)) ** 1.35 * (1.15 if day else 1.0), step=3.0)
    blue_svg = _svg(
        f'<g clip-path="url(#{pid}atom)"><path d="{ball}" fill="{plate}"></path></g>',
        f'<clipPath id="{pid}atom"><circle cx="{ax:.2f}" cy="{cy:.2f}" r="{r:.2f}"></circle></clipPath>',
        h=band,
    )

    # black layer: the outline of the atom, the line that drops its far side to the ruler,
    # and the 2.8 beam with its end caps
    key_svg = _svg(
        f'<g fill="none">'
        f'<line x1="{X(1.4):.2f}" y1="{cy:.2f}" x2="{X(1.4):.2f}" y2="{ruler}" stroke="{drop}" stroke-width="0.6"></line>'
        f'<circle cx="{ax:.2f}" cy="{cy:.2f}" r="{r:.2f}" stroke="{ink}" stroke-width="0.9"></circle>'
        f'<g stroke="{ink}" stroke-width="1.4"><line x1="{X(0):.2f}" y1="{y_ink}" x2="{X(2.8):.2f}" y2="{y_ink}"></line>'
        f'<line x1="{X(0) + 0.7:.2f}" y1="{y_ink - cap}" x2="{X(0) + 0.7:.2f}" y2="{y_ink + cap}"></line>'
        f'<line x1="{X(2.8):.2f}" y1="{y_ink - cap}" x2="{X(2.8):.2f}" y2="{y_ink + cap}"></line></g>'
        f'</g>'
        # the labels of the two printed marks are print too: they ink in with their marks
        f'<g fill="{t["muted"]}" style="{LABEL}"><text x="{X(2.8) + 9:.1f}" y="{y_ink + 3.8:.1f}">NEXT BEST, 2.8 Å</text>'
        f'<text x="{X(1.4) + 9:.1f}" y="{cy + 3.8:.1f}">CARBON ATOM, ABOUT 1.4 Å</text></g>',
        h=band,
    )

    d = f"M{X(0):.2f} {y_live}H{X(0.96):.2f}"
    ticks = "".join(
        f'<line x1="{X(i / 5):.2f}" y1="{ruler}" x2="{X(i / 5):.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>'
        for i in range(0, 60) if X(i / 5) <= W
    )
    last = int((W - M - 30) // s)
    labels = "".join(
        f'<text x="{X(v):.1f}" y="{ruler + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in range(0, last + 1)
    ) + f'<text x="{X(last) + 9:.1f}" y="{ruler + 20}">Å</text>'
    # the start cap of the live beam, on the zero both beams share
    start_cap = f'<line x1="{X(0) + 0.8:.2f}" y1="{y_live - cap}" x2="{X(0) + 0.8:.2f}" y2="{y_live + cap}" stroke="{t["live"]}" stroke-width="1.9"></line>'
    # Direct labels, each at its mark. The live beam's label is in the text color and lands
    # (Press) as the pen point reaches 0.96. The other two are second rank (muted) and sit in
    # the black layer above. No label is on screen before its mark.
    land = f' style="animation: press 190ms {PRESS} {at(320 + sweep_ms - 120)} both"' if animate else ""
    marks = (
        f'<g style="{LABEL}">'
        f'<text x="{X(0.96) + 15:.1f}" y="{y_live + 3.8:.1f}" fill="{t["text"]}"{land}>ALPHAFOLD, 0.96 Å</text>'
        f'</g>'
    )
    live_svg = _live(
        pid, t, d, sweep_ms, animate,
        aria="Illustration drawn to scale on a ruler in angstroms: AlphaFold's median error of 0.96, the next best method at 2.8, and a carbon atom about 1.4 wide",
        ticks=ticks, labels=labels, mid=start_cap, over=marks, band=band,
    )
    return _frame(blue_svg, key_svg, live_svg, "inkp2", animate, band=band, top=top)
