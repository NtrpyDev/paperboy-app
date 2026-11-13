"""Motion scenes for the Paperboy motion boards.

Every scene is drawn once, at rest, with inline styles (that is the reduced-motion frame).
A Clock then adds the named animations on top. The same scene can run three ways:

  Clock(T)            loop it every T ms (the specimen board)
  Clock(T, hold=ms)   freeze it at an exact time, with the animation paused (the storyboard)
  Clock(T, still=True) no animation at all (the reduced-motion frame)

Times given to a scene are the product times from SYSTEM.md section 12. The clock adds its
own lead-in, so a loop opens on the start state for a beat before anything moves.
"""
from bm import *

CSS = []          # keyframes collected for the helmet
_n = [0]

SPEC = dict(
    press=(190, PRESS), inkwipe=(520, PRESS), register=(480, REGISTER), sweep=(1900, "linear"),
    pulse=(2400, "ease-in-out"), stamp=(120, PRESS), feedup=(360, PRESS),
)


class Clock:
    def __init__(self, T=5400, lead=600, hold=None, still=False):
        self.T, self.lead, self.hold, self.still = T, lead, hold, still

    def _kf(self, steps):
        name = f"k{_n[0]}"
        _n[0] += 1
        frames = []
        for t, props, ease in steps:
            e = f";animation-timing-function:{ease}" if ease else ""
            frames.append(f"{min(100.0, max(0.0, (t + self.lead) / self.T * 100)):.3f}%{{{props}{e}}}")
        CSS.append(f"@keyframes {name}{{{''.join(frames)}}}")
        return name

    def _decl(self, name):
        if self.hold is None:
            return f"{name} {self.T}ms linear infinite"
        return f"{name} {self.T}ms linear {-(self.hold + self.lead)}ms 1 paused both"

    def go(self, *tracks):
        """tracks: lists of (time ms, css, easing to the next step). Returns '; animation: ...' or ''."""
        if self.still:
            return ""
        return "; animation: " + ", ".join(self._decl(self._kf(tr)) for tr in tracks)

    # one-shot: hold `frm` until delay, move to `to` over dur, then rest
    def shot(self, delay, dur, frm, to, ease):
        return [(-self.lead, frm, None), (delay, frm, ease), (delay + dur, to, None), (self.T - self.lead, to, None)]

    def press(self, delay):
        return self.go(self.shot(delay, 190, "opacity:0;transform:translateY(6px)", "opacity:1;transform:none", PRESS))

    def pulse(self, start=2400):
        end = self.T - self.lead
        tr, t = [(-self.lead, "opacity:1", None)], start
        while t + 2400 <= end + 1:
            tr += [(t, "opacity:1", "ease-in-out"), (t + 1200, "opacity:.55", "ease-in-out")]
            t += 2400
        tr.append((end, "opacity:1", None))
        return tr

    def sweep(self, delay=320, dur=1900):
        return self.shot(delay, dur, "stroke-dashoffset:1.003", "stroke-dashoffset:0", "linear")

    def travel(self, delay=320, dur=1900):
        return self.shot(delay, dur, "offset-distance:0%", "offset-distance:100%", "linear")

    def wipe(self, w, h, delay=60):
        k = abs(h / math.tan(math.radians(A1))) / w * 100
        return self.go(self.shot(delay, 520, f"clip-path:polygon(0% 0%,0% 0%,{-k:.1f}% 100%,0% 100%)",
                                 f"clip-path:polygon(0% 0%,{100 + k:.1f}% 0%,100% 100%,0% 100%)", PRESS))

    def register(self, which, delay=60):
        frm = "transform:translate(5px,-3px)" if which == "a" else "transform:translate(-5px,3px)"
        return self.go(self.shot(delay, 480, frm, "transform:none", REGISTER))


# ------------------------------------------------------------------ the live line, any path
def live_line(ck, d, theme, delay=320, dur=1900, carriage=None, pulse=True, extra_pen="", car_color=None):
    """Trap, halo (night), core, then the pen point. The strokes under the core and the marks under
    the pen point come from the shared helpers in lib.py, so every board draws one halo.
    carriage = id of a clipPath: puts the block on the ruler under the pen.
    Returns (line marks, carriage marks, pen marks)."""
    t = T(theme)
    day = t["day"]
    dash = SWEEP_DASH
    sw = ck.go(ck.sweep(delay, dur))
    ride = ck.go(ck.travel(delay, dur))
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"
    common = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    line = live_under_strokes(d, day, t["ground"], t["live"], f"{dash}{sw}")
    line += f'<path d="{d}" {common} stroke="{t["live"]}" stroke-width="1.9" style="{dash}{sw}"></path>'
    car = ""
    if carriage:
        car = (f'<g clip-path="url(#{carriage})"><g style="{pen}{ride}"><line x1="0" y1="-600" x2="0" y2="600" stroke="{car_color or t["text"]}" stroke-width="9"></line></g></g>')
    under = pen_under_marks(day, t["ground"], t["live"], f"{pen}{ride}")
    tracks = [ck.travel(delay, dur)] + ([ck.pulse()] if pulse else [])
    point = f'<circle r="{3.6 if day else 3.4}" fill="{t["live"]}" style="{pen}{ck.go(*tracks)}"></circle>'
    return line, car, under + extra_pen + point


# ------------------------------------------------------------------ Plate 1, any width
def plate(ck, pid, theme, W=390, M=20, MR=20, BAND=196, layers=True, live=True, wipe=None, reg=None, target=None, labels=True):
    """The hero plate at any width and band height. The print layers are gw_print() in lib.py, the
    generator every board calls. layers=False leaves out the wipe and Register, live=False leaves
    out the line. A band under 196 px scales the wells and the swing of the line with it."""
    t = T(theme)
    day = t["day"]
    if BAND >= 196:
        k, cy, amp = 1.0, 62.0, 29.0
    else:                                      # sized so the wells clear both the top edge and the crest
        k, cy, amp = 0.74 * BAND / 150, 43.0 * BAND / 150, 21.5 * BAND / 150
    cx = M + (W - M - MR) * 0.76
    y0 = BAND - 39
    d, xm, crest = chirp(M, y0, W - M - MR, amp)
    ruler, PH = BAND, BAND + 34
    (bdefs, blue), (kdefs, key) = gw_print(pid, cx, cy, W, BAND, theme, k=k)
    if k < 1:
        # a smaller figure keeps the line spacing of the full-size one, so it does not go dark
        from lib import _Pair
        key = wells_open(_Pair(cx, cy, ang=-25, sep=84.0 * k, ra=17.0 * k), t["ground"], INK if day else NM, k=k, step=(1.55 / k, 0.058 / k))
    chrome = t["text"] if day else NM          # night: structure steps down, as the feed boards do
    ta = tb = ""
    if target:
        tx, ty = target
        ta = (f'<circle cx="{tx}" cy="{ty}" r="13" fill="{t["ground"]}"></circle>'
              f'<path d="M{tx - 9} {ty}H{tx + 9}M{tx} {ty - 9}V{ty + 9}" stroke="{t["plate"]}" stroke-width="1.2" fill="none"></path>')
        tb = f'<circle cx="{tx}" cy="{ty}" r="5.5" fill="none" stroke="{t["text"]}" stroke-width="1"></circle>'
    blue_svg = f'<svg viewBox="0 0 {W} {BAND}" width="{W}" height="{BAND}" aria-hidden="true" style="display: block"><defs>{bdefs}</defs>{blue}{ta}</svg>'
    key_svg = f'<svg viewBox="0 0 {W} {BAND}" width="{W}" height="{BAND}" aria-hidden="true" style="display: block; overflow: visible"><defs>{kdefs}</defs>{key}{tb}</svg>'
    step = (xm - M) / 10
    ticks, x, i = [], float(M), 0
    while x <= W:
        ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
        x += step
        i += 1
    line = car = pen = ""
    if live:
        line, car, pen = live_line(ck, d, theme, carriage=f"{pid}rail", car_color=t["text"])
    live_svg = (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" '
        f'aria-label="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ruler - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'{line}'
        f'<g stroke="{chrome}" stroke-width="0.9" fill="none"><line x1="{M}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{"".join(ticks)}</g>'
        f'{car}'
        + (f'<g fill="{t["text"] if day else t["muted"]}" style="{SVGLAB}">'
           f'<text x="{M}" y="{ruler + 20}">0</text>'
           f'<text x="{(M + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
           f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text></g>' if labels else "") +
        f'{pen}</svg>'
    )
    wipe = layers if wipe is None else wipe
    reg = layers if reg is None else reg
    wipe = ck.wipe(W, BAND) if wipe else ""
    ra = ck.register("a") if reg else ""
    rb = ck.register("b") if reg else ""
    return (
        f'<div style="position: relative; width: {W}px; height: {PH}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {BAND}px{wipe}">'
        f'<div style="position: absolute; left: 0; top: 0{ra}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0{rb}">{key_svg}</div>'
        f'</div>{live_svg}</div>'
    )


# ------------------------------------------------------------------ card parts
def tag_outline(tx, c):
    return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {c}; padding: 4px 6px 3px">{tx}</span>'


def tag_solid(tx, bg, fg):
    return f'<span style="{mono(10, color=fg, weight=600, ls=0.06)}; background-color: {bg}; border: 1px solid {bg}; padding: 4px 6px 3px">{tx}</span>'


def journal(label, c):
    return (f'<a href="#paper" style="margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
            f'{text(15, lh=1, italic=True)}; color: {c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</a>')


def headline(ck, theme, size=44, press=True):
    t = T(theme)
    it = disp(size, weight=t["iw"], stretch=100 if t["day"] else 87.5, lh=0.98, ls=-0.012, italic=True)
    p = (lambda i: ck.press(i * 50)) if press else (lambda i: "")
    return (f'<h2 style="margin: 0; {disp(size, weight=t["hw"], lh=0.98)}">'
            f'<span style="display: block{p(0)}">Two black holes</span>'
            f'<span style="display: block{p(1)}">merged. <span style="{it}">Earth felt</span></span>'
            f'<span style="display: block; {it}{p(2)}">space stretch.</span></h2>')


def readout(theme):
    t = T(theme)
    return (f'<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px 20px 0">'
            f'<div style="display: flex; flex-direction: column; gap: 3px">'
            f'<div style="{disp(44, weight=t["hw"], lh=1, color=t["text"])}; font-variant-numeric: lining-nums">1.0{sign_times()}10<sup style="{SUP}">−21</sup></div>'
            f'<div style="{mono(LABSZ, color=t["muted"], ls=0.06)}">Peak strain. Pitch 35 to 250 Hz</div></div>'
            f'<div style="text-align: right; {mono(LABSZ, color=t["muted"], ls=0.06)}; line-height: 1.4">Plate 1<br>Illustration,<br>not to scale</div></div>')


def primary(label, theme):
    t = T(theme)
    return (f'<a href="#explainer" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; '
            f'background-color: {t["text"]}; color: {t["ground"]}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{ARROW}</a>')


STAMP_HALF = 24      # ms: where cubic-bezier(0.2, 0, 0, 1) over 120 ms passes half way
STAMP_FLIP = 60      # ms: the fill is four fifths in, and the label and icon change over


def stamp_fill(theme):
    """The stamped fill, one step under the primary slab: ink-muted by day, light-muted at night
    (CRITIQUE system fix 5, as the feed boards draw it). SYSTEM.md 9.6 still says full ink: if the
    director keeps that, return T(theme)["text"] here and every board of this role follows."""
    return T(theme)["muted"]


def rate(icon, label, theme, stamp=""):
    """Rating button. stamp=None is the outline. stamp='' is the stamped state at rest: filled, and
    its plus turned to a check, so the state is not carried by the fill alone. Otherwise stamp is
    what stamp_anim() returns, and the inline style is still the rest."""
    t = T(theme)
    c, g = t["text"], t["ground"]
    on = stamp is not None
    a_btn, a_old, a_new = stamp if isinstance(stamp, tuple) else ("", "", "")
    fill = stamp_fill(theme)
    if on:
        icon = (f'<span style="position: relative; display: inline-flex"><span style="position: absolute; left: 0; top: 0; display: inline-flex; opacity: 0{a_old}">{icon}</span>'
                f'<span style="display: inline-flex{a_new}">{CHECK}</span></span>')
    return (f'<button type="button" aria-pressed="{"true" if on else "false"}" style="position: relative; flex: 1 1 0; min-height: 44px; box-sizing: border-box; '
            f'background-color: {fill if on else "transparent"}; border: 1px solid {fill if on else c}; border-radius: 0; color: {g if on else c}; padding: 0 12px; '
            f'display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer{a_btn}">'
            f'{icon}<span style="{text(16, lh=1, weight=500)}">{label}</span></button>')


def stamp_anim(ck, tap, theme="day", **_):
    """Stamp, as SYSTEM.md section 12 and the feed boards build it: the whole button jumps to 1.1 on
    the tap and settles to 1 over 120 ms while its fill floods in across the whole surface at once.
    No wipe and no moving edge. The label and the icon change over once the fill is four fifths in,
    so the words are readable in every frame. Returns the three declarations rate() takes."""
    t = T(theme)
    c, g = t["text"], t["ground"]
    fill = stamp_fill(theme)
    r_, g_, b_ = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
    clear = f"rgba({r_},{g_},{b_},0)"
    off = f"transform:none;background-color:{clear};border-color:{c}"
    up = f"transform:scale(1.1);background-color:{clear};border-color:{c}"
    on = f"transform:none;background-color:{fill};border-color:{fill}"
    end = ck.T - ck.lead
    flip = tap + STAMP_FLIP
    body = [(-ck.lead, off, None), (tap - 1, off, None), (tap, up, PRESS), (tap + 120, on, None), (end, on, None)]
    step = lambda a, b: [(-ck.lead, a, None), (flip, a, "step-end"), (flip + 1, b, None), (end, b, None)]
    return (ck.go(body, step(f"color:{c}", f"color:{g}")), ck.go(step("opacity:1", "opacity:0")), ck.go(step("opacity:0", "opacity:1")))


# ------------------------------------------------------------------ the ruled distance (AlphaFold, for scale)
def ruled(ck, pid, theme, CW=357, s=86.0, dur=1400, ry=150.0, short=False):
    """The analogy figure of LockParts with its live beam ruled off: one ruler in angstroms,
    the carbon atom as a screened shape, the next best method as an ink beam, and AlphaFold's 0.96
    as the live line. The carriage rides the ruler because the line is plotted against it.
    Each label lands with its own mark. The atom's label sits under the disc, between the two
    drop lines that carry its width to the ruler. short=True keeps the label beside the disc."""
    t = T(theme)
    day = t["day"]
    c, g, live = t["text"], t["ground"], t["live"]
    x0 = 6.0
    X = lambda v: x0 + v * s
    r = 0.7 * s
    under = not short
    ccx, ccy = X(0.7), ry - r - (34 if under else 8)
    ticks = "".join(f'<line x1="{X(i / 5):.1f}" y1="{ry}" x2="{X(i / 5):.1f}" y2="{ry + (7 if i % 5 == 0 else 4)}"></line>' for i in range(0, 16))
    tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in range(0, 4))
    yb, yl = 23.0, 8.0
    d = f"M{x0} {yl}L{X(0.96):.2f} {yl}"
    cap = lambda xx, y, col, w: f'<line x1="{xx:.1f}" y1="{y - 5}" x2="{xx:.1f}" y2="{y + 5}" stroke="{col}" stroke-width="{w}"></line>'
    lw = 2 if day else 1.75
    jaw = f'<line x1="0" y1="-5" x2="0" y2="5" stroke="{live}" stroke-width="{lw}" style="offset-path: path(\'{d}\'); offset-distance: 100%; offset-rotate: 0deg{ck.go(ck.travel(320, dur))}"></line>'
    line, car, pen = live_line(ck, d, theme, dur=dur, carriage=f"{pid}rail", extra_pen=jaw)
    box = 2 * r
    wipe = ck.wipe(box, box)
    grid = f'stroke="{t["grid"]}" stroke-width="0.6" fill="none"'
    # the 0.96 drop line stops where it meets the atom: the carriage carries it on to the ruler
    top96 = ccy - math.sqrt(max(0.0, r * r - (X(0.96) - ccx) ** 2)) - 3
    lands = lambda ms: f"transform-box: fill-box{ck.press(ms)}"
    if under:
        atom = (f'<g style="{lands(390)}"><g {grid}><line x1="{X(0):.1f}" y1="{ccy:.1f}" x2="{X(0):.1f}" y2="{ry}"></line><line x1="{X(1.4):.1f}" y1="{ccy:.1f}" x2="{X(1.4):.1f}" y2="{ry}"></line></g>'
                f'<g fill="{c}" style="{SVGLAB}" text-anchor="middle"><text x="{ccx:.1f}" y="{ccy + r + 14:.1f}">CARBON ATOM,</text><text x="{ccx:.1f}" y="{ccy + r + 27:.1f}">ABOUT 1.4 Å</text></g></g>')
    else:
        atom = (f'<g fill="{c}" style="{SVGLAB}; {lands(390)}"><text x="{X(1.4) + 8:.1f}" y="{ccy - 7:.1f}">CARBON</text><text x="{X(1.4) + 8:.1f}" y="{ccy + 7:.1f}">ATOM,</text>'
                f'<text x="{X(1.4) + 8:.1f}" y="{ccy + 21:.1f}">ABOUT 1.4 Å</text></g>')
    return (
        f'<div style="position: relative; width: {CW}px; height: {ry + 26:.0f}px">'
        f'<div style="position: absolute; left: {ccx - r:.1f}px; top: {ccy - r:.1f}px; width: {box:.1f}px; height: {box:.1f}px{wipe}">'
        f'<svg viewBox="0 0 {box:.1f} {box:.1f}" width="{box:.1f}" height="{box:.1f}" aria-hidden="true" style="display: block"><defs>{patterns(pid, t["plate"], tones={"a1": (A1, 0.3)})}</defs>'
        f'<circle cx="{r:.1f}" cy="{r:.1f}" r="{r - 0.45:.1f}" fill="url(#{pid}a1)" stroke="{c}" stroke-width="0.9"></circle></svg></div>'
        f'<svg viewBox="0 0 {CW} {ry + 26:.0f}" width="{CW}" height="{ry + 26:.0f}" role="img" aria-label="Drawing to scale on a ruler in angstroms: a carbon atom about 1.4 wide, AlphaFold median error 0.96, next best method 2.8" style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="-6" y="{ry - 0.5}" width="{CW + 6}" height="8"></rect></clipPath></defs>'
        f'<g style="{lands(0)}">'
        f'<line x1="{X(2.8):.1f}" y1="{yb}" x2="{X(2.8):.1f}" y2="{ry}" {grid}></line>'
        f'<line x1="{x0}" y1="{yb}" x2="{X(2.8):.1f}" y2="{yb}" stroke="{c}" stroke-width="1.4"></line>{cap(x0, yb, c, 1.4)}{cap(X(2.8), yb, c, 1.4)}'
        f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{x0}" y1="{ry}" x2="{X(3):.1f}" y2="{ry}"></line>{ticks}</g>'
        f'<g fill="{c}" style="{SVGLAB}">{tl}<text x="{X(3) + 9:.1f}" y="{ry + 20}">Å</text>'
        + (f'<text x="{X(2.8) + 10:.1f}" y="{yb + 4}">NEXT BEST,</text><text x="{X(2.8) + 10:.1f}" y="{yb + 18}">2.8 Å</text>' if short else
           f'<text x="{X(2.8) + 10:.1f}" y="{yb + 4}">NEXT BEST, 2.8 Å</text>') + f'</g></g>'
        f'{atom}'
        f'<g style="{lands(320 + dur - 190)}"><line x1="{X(0.96):.1f}" y1="{yl + 6}" x2="{X(0.96):.1f}" y2="{top96:.1f}" {grid}></line>'
        f'<text x="{X(0.96) + 10:.1f}" y="{yl + 4}" fill="{c}" style="{SVGLAB}">ALPHAFOLD, 0.96 Å</text></g>'
        f'{line}{cap(x0, yl, live, lw)}{car}{pen}'
        f'</svg></div>'
    )


# ------------------------------------------------------------------ a time ruler with its carriage
def timeline(ck, theme, w, bars, span=4800, marks=()):
    """The cell's own instrument: a ruler in seconds, one bar per named animation, and a carriage
    that rides the ruler in real time. bars: (label, start ms, length ms, 'solid' or 'loop')."""
    t = T(theme)
    c, mu = t["text"], t["muted"]
    px = w / span
    rows = len(bars)
    ax = rows * 13 + 5
    pid = f"tl{_n[0]}"
    _n[0] += 1
    out = ""
    for i, (label, start, length, kind) in enumerate(bars):
        y = i * 13 + 2
        if isinstance(start, (list, tuple)):       # one verb used several times: a bar for each, one label
            for st in start[:-1]:
                out += f'<rect x="{st * px:.1f}" y="{y}" width="{max(1.5, length * px):.1f}" height="6" fill="{c}"></rect>'
            start = start[-1]
        x0, x1 = start * px, (start + length) * px
        if kind == "loop":
            out += (f'<rect x="{x0:.1f}" y="{y}" width="{x1 - x0:.1f}" height="6" fill="url(#{pid}s)"></rect>'
                    f'<rect x="{x0 + 0.45:.1f}" y="{y + 0.45}" width="{x1 - x0 - 0.9:.1f}" height="5.1" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
                    f'<text x="{x0 - 7:.1f}" y="{y + 7.6}" text-anchor="end" fill="{c}">{label.upper()}</text>')
        else:
            out += (f'<rect x="{x0:.1f}" y="{y}" width="{max(1.5, x1 - x0):.1f}" height="6" fill="{c}"></rect>'
                    f'<text x="{x1 + 7:.1f}" y="{y + 7.6}" fill="{c}">{label.upper()}</text>')
    ticks = "".join(f'<line x1="{v * px:.1f}" y1="{ax}" x2="{v * px:.1f}" y2="{ax + (7 if v % 1000 == 0 else 4)}"></line>' for v in range(0, span + 1, 200))
    tl = "".join(f'<text x="{v * px:.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v // 1000}{" s" if v == 4000 else ""}</text>' for v in range(0, span + 1, 1000))
    for label, at_ms in marks:
        tl += f'<text x="{at_ms * px:.1f}" y="{ax + 20}" text-anchor="middle">{label.upper()}</text>'
    T_ = ck.T - ck.lead
    car = ck.go([(-ck.lead, "transform:translateX(0px)", None), (0, "transform:translateX(0px)", "linear"),
                 (span, f"transform:translateX({w:.1f}px)", None), (T_, f"transform:translateX({w:.1f}px)", None)])
    rest = f"transform: translateX({w:.1f}px)"
    return (
        f'<svg viewBox="-5 0 {w + 10} {ax + 26}" width="{w + 10}" height="{ax + 26}" aria-hidden="true" style="display: block; margin: 0 -5px; overflow: visible">'
        f'<defs>{patterns(pid, c if t["day"] else NM, tones={"s": (A1, 0.46)})}</defs>'
        f'<g style="{SVGLAB}">{out}</g>'
        f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{w}" y2="{ax}"></line>{ticks}</g>'
        f'<g fill="{mu}" style="{SVGLAB}">{tl}</g>'
        f'<rect x="-4.5" y="{ax - 0.5}" width="9" height="8" fill="{c}" style="{rest}{car}"></rect>'
        f'</svg>'
    )


def ease_glyph(curve, c=INK, size=22, h=None):
    """A small plot of an easing curve: time across, progress up. It stands on a baseline only.
    There is no upright axis, so a column of these never reads as a row of marks on an edge."""
    s = size
    h = h or size
    if curve == "linear":
        d = f"M0 {h}L{s} 0"
    elif curve == "ease-in-out":
        d = f"M0 {h}C{0.42 * s:.1f} {h} {0.58 * s:.1f} 0 {s} 0"
    else:
        a = [float(v) for v in curve[curve.index("(") + 1:-1].split(",")]
        d = f"M0 {h}C{a[0] * s:.1f} {h - a[1] * h:.1f} {a[2] * s:.1f} {h - a[3] * h:.1f} {s} 0"
    return (f'<svg width="{s + 2}" height="{h + 2}" viewBox="-1 -1 {s + 2} {h + 2}" aria-hidden="true" style="display: block; flex: none">'
            f'<path d="M0 {h}H{s}" fill="none" stroke="{c}" stroke-width="0.6"></path>'
            f'<path d="{d}" fill="none" stroke="{c}" stroke-width="1.4" stroke-linecap="round"></path></svg>')


# ------------------------------------------------------------------ Plate 3: the ring as the live line
def plate_m87(ck, pid, theme, PW=258, SH=170, R=52, delay=380, dur=1800):
    """Plate 3 of Cand-x-System in the locked inks: a ruled sky in plate blue, the shadow as the one
    overprint, and the bright ring as the live line, drawn from 12 o'clock. No ruler and no carriage,
    because the ring is not plotted against an axis. A scale bar gives the 42 microarcseconds."""
    t = T(theme)
    day = t["day"]
    c, g = t["text"], t["ground"]
    cx, cy = PW * 0.56, SH / 2
    k = R / 88.0
    tones = {"h1": (A2, 0.2), "h2": (A2, 0.42), "h3": (A2, 0.66), "c3": (A1, 0.68)}
    defs = patterns(pid, t["plate"], tones=tones) + patterns(pid, t["key"], tones={"k3": (A2, 0.66)})
    disc = lambda r, fill: f'<circle cx="{cx:.1f}" cy="{cy}" r="{r:.1f}" fill="{fill}"></circle>'
    sky = (f'<rect width="{PW}" height="{SH}" fill="url(#{pid}h3)"></rect>'
           f'{disc(R + 132 * k, g)}{disc(R + 132 * k, f"url(#{pid}h2)")}'
           f'{disc(R + 66 * k, g)}{disc(R + 66 * k, f"url(#{pid}h1)")}'
           f'{disc(R + 24 * k, g)}'
           f'{disc(R - 20 * k, f"url(#{pid}h1)")}{disc(R - 34 * k, f"url(#{pid}h2)")}')
    shadow = (f'{disc(R - 50 * k, g)}{disc(R - 50 * k, f"url(#{pid}c3)")}{disc(R - 50 * k, f"url(#{pid}k3)")}'
              f'<circle cx="{cx:.1f}" cy="{cy}" r="{R - 50 * k:.1f}" fill="none" stroke="{t["key"]}" stroke-width="1"></circle>')
    d = f"M{cx:.2f} {cy - R:.2f}A{R} {R} 0 1 1 {cx - 0.01:.2f} {cy - R:.2f}"
    line, car, pen = live_line(ck, d, theme, delay=delay, dur=dur)
    by = SH + 16
    return (
        f'<div style="position: relative; width: {PW}px; height: {SH + 36}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {PW}px; height: {SH}px">'
        f'<svg viewBox="0 0 {PW} {SH}" width="{PW}" height="{SH}" aria-hidden="true" style="display: block"><defs>{defs}</defs>{sky}{shadow}</svg></div>'
        f'<svg viewBox="0 0 {PW} {SH + 36}" width="{PW}" height="{SH + 36}" role="img" aria-label="Illustration of the bright ring around the black hole in galaxy M87, with a scale bar showing the ring is 42 microarcseconds across" style="position: absolute; left: 0; top: 0">'
        f'{line}'
        f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{cx - R:.1f}" y1="{by}" x2="{cx + R:.1f}" y2="{by}"></line>'
        f'<line x1="{cx - R:.1f}" y1="{by - 5}" x2="{cx - R:.1f}" y2="{by + 5}"></line><line x1="{cx + R:.1f}" y1="{by - 5}" x2="{cx + R:.1f}" y2="{by + 5}"></line></g>'
        f'<text x="{cx + R + 9:.1f}" y="{by + 3.6}" fill="{c}" style="{SVGLAB}">42 µAS</text>'
        f'{pen}</svg></div>'
    )


def bezier(x1, y1, x2, y2, x):
    """Progress of a CSS cubic-bezier easing at time fraction x."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        u = (lo + hi) / 2
        bx = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3
        if bx < x:
            lo = u
        else:
            hi = u
    u = (lo + hi) / 2
    return 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3


# Only running animations are removed for reduced motion. A paused still (a storyboard frame) has
# no motion in it, and removing it would throw the frame to its rest state.
KEY_REDUCED = '@media (prefers-reduced-motion: reduce){[style*="infinite"]{animation:none!important}}'


def picture(markup):
    """A held frame is a picture of a control, not a control: its buttons and links become plain
    boxes, so nothing in it takes focus or counts as a touch target."""
    for a, b in (('<button type="button"', '<span'), ("</button>", "</span>"), ('<a href="#explainer"', '<span'), ('<a href="#paper"', '<span'), ("</a>", "</span>"),
                 (' aria-pressed="true"', ""), (' aria-pressed="false"', ""), ("cursor: pointer", "cursor: default")):
        markup = markup.replace(a, b)
    return markup
