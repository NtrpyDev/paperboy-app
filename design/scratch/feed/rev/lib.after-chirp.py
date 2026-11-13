"""Shared drawing code for the Engraved Broadsheet artboards.

Everything here returns literal markup. The artboards are written out as plain
.dc.html files with no template holes.
"""
import math
import os

# Test aid: PB_DELAY (ms) pushes every animation back so early frames can be captured.
D0 = int(os.environ.get("PB_DELAY", "0"))


def at(ms):
    return f"{ms + D0}ms"

INK = "#16130F"
STOCK = "#E9E6DE"
MUTED = "#5A554B"
LIVE = "#E0330A"
NG = "#0E1116"
NT = "#E9E4D7"
NM = "#9C988D"
NS = "#5E6573"
NX = "#2B303B"
AMBER = "#FFA63D"

DISP = "'Noto Serif Display', Didot, 'Bodoni MT', Georgia, serif"
TEXT = "'Source Serif 4', Georgia, 'Times New Roman', serif"
MONO = "'Martian Mono', 'DejaVu Sans Mono', Menlo, monospace"

FONTS = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Martian+Mono:wdth,wght@75..112.5,100..800"
    "&family=Noto+Serif+Display:ital,wdth,wght@0,62.5..100,100..900;1,62.5..100,100..900"
    "&family=Source+Serif+4:ital,opsz,wght@0,8..60,200..900;1,8..60,200..900"
    '&display=swap">'
)

# Screen angles. The plate wipe runs along A1.
A1 = -72
A2 = -12
PITCH = 3.0

PRESS = "cubic-bezier(0.2, 0, 0, 1)"
REGISTER = "cubic-bezier(0.16, 1, 0.3, 1)"


def mono(size=9.5, color=INK, weight=500, ls=0.08, stretch=75, upper=True):
    s = (
        f"font-family: {MONO}; font-stretch: {stretch}%; font-size: {size}px; "
        f"font-weight: {weight}; letter-spacing: {ls}em; color: {color}; line-height: 1.3"
    )
    if upper:
        s += "; text-transform: uppercase"
    return s


def disp(size, weight=800, stretch=62.5, lh=0.96, ls=-0.005, italic=False, color=None):
    s = (
        f"font-family: {DISP}; font-size: {size}px; font-weight: {weight}; "
        f"font-stretch: {stretch}%; line-height: {lh}; letter-spacing: {ls}em"
    )
    if italic:
        s += "; font-style: italic"
    if color:
        s += f"; color: {color}"
    return s


def text(size=17, lh=1.45, weight=400, italic=False, color=None):
    s = f"font-family: {TEXT}; font-size: {size}px; line-height: {lh}; font-weight: {weight}"
    if italic:
        s += "; font-style: italic"
    if color:
        s += f"; color: {color}"
    return s


def patterns(pid, ink, pitch=PITCH, a1=A1, a2=A2, tones=None):
    """Line screens. Same pitch and phase in every tone, so a line swells
    from light to heavy without breaking where two tones meet."""
    tones = tones or {"a1": (a1, 0.24), "a2": (a1, 0.46), "a3": (a1, 0.68), "b1": (a2, 0.24), "b2": (a2, 0.44), "b3": (a2, 0.66)}
    out = []
    for name, (ang, frac) in tones.items():
        h = pitch * frac
        y = (pitch - h) / 2
        out.append(
            f'<pattern id="{pid}{name}" width="40" height="{pitch}" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate({ang})"><rect x="0" y="{y:.3f}" width="40" height="{h:.3f}" fill="{ink}"></rect></pattern>'
        )
    return "".join(out)


def chirp(x0, y0, w, amp, tm=0.78, ring=(3, 0.62, 2.0)):
    """The live line: a smooth chirp as cubic curves. Illustration only.
    Returns (path d, x of the merger, (x, y) of the highest crest).

    ring=(cycles, slow, power) is the ringdown after the merger: that many whole cycles,
    the pitch easing down to `slow` times the merger pitch so the last swings stay wide
    enough to read, the height falling as (1 - u) ** power to exactly zero. After that the
    line is flat into the pen point. ring=None is the first version (a long exponential
    tail at the merger pitch), which showed as jitter at 390 px (CRITIQUE, Feed Day fix 2)."""
    c1, c4 = 2.0, 7.0
    fr = (c1 + 4 * c4) / tm * (1 - tm)
    ph_m = 2 * math.pi * (c1 + c4)
    r_m = 2 * math.pi * (c1 + 4 * c4) / tm           # phase rate at the merger
    if ring:
        n_ring, slow, power = ring
        te = min(1.0, tm + 4 * math.pi * n_ring / (r_m * (1 + slow)))
    else:
        te = 1.0

    def amp_at(t):
        if t <= tm:
            u = t / tm
            return amp * (0.06 + 0.94 * u ** 3)
        if ring:
            if t >= te:
                return 0.0
            return amp * (1 - (t - tm) / (te - tm)) ** power
        u = (t - tm) / (1 - tm)
        return amp * math.exp(-6.5 * u)

    def phase(t):
        if t <= tm:
            u = t / tm
            return 2 * math.pi * (c1 * u + c4 * u ** 4)
        if ring:
            u = min(1.0, (t - tm) / (te - tm))
            return ph_m + r_m * (te - tm) * (u - (1 - slow) * u * u / 2)
        u = (t - tm) / (1 - tm)
        return ph_m + 2 * math.pi * fr * u

    def rate(t):
        if t <= tm:
            u = t / tm
            return 2 * math.pi * (c1 + 4 * c4 * u ** 3) / tm
        if ring:
            u = min(1.0, (t - tm) / (te - tm))
            return r_m * (1 - (1 - slow) * u)
        return 2 * math.pi * fr / (1 - tm)

    def y(t):
        return -amp_at(t) * math.sin(phase(t))

    def dy(t):
        if abs(t - tm) < 1e-9:
            return -amp * math.cos(ph_m) * rate(tm)
        if ring and t >= te - 1e-9:
            return 0.0
        h = 1e-6
        a, b = max(0.0, t - h), min(1.0, t + h)
        if a < tm < b:
            a, b = (a, t) if t < tm else (t, b)
        return (y(b) - y(a)) / (b - a)

    ts = [0.0]
    while ts[-1] < 1.0 - 1e-9:
        t = ts[-1]
        if ring and t >= te - 1e-9:
            ts.append(1.0)               # the flat run is one straight segment
            break
        nt = t + min(0.02, (math.pi / 6) / rate(t))
        if t < tm - 1e-9 and nt > tm:
            nt = tm
        if ring and t < te - 1e-9 and nt > te:
            nt = te
        ts.append(min(1.0, nt))
    pts = [(x0 + w * t, y0 + y(t), dy(t) / w) for t in ts]
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for (xa, ya, sa), (xb, yb, sb) in zip(pts, pts[1:]):
        k = (xb - xa) / 3
        d += f"C{xa + k:.2f} {ya + sa * k:.2f} {xb - k:.2f} {yb - sb * k:.2f} {xb:.2f} {yb:.2f}"
    crest = min(((x0 + w * i / 4000, y0 + y(i / 4000)) for i in range(4001)), key=lambda p: p[1])
    return d, x0 + w * tm, crest


def spiral(cx, cy, rot, a0, rmax, color, gap=lambda r: 2.7 + 0.019 * r, width=lambda r: 1.0 - 0.5 * min(1.0, r / 250.0)):
    """Two-armed spiral built from half circles, so it stays exact and small.
    The pitch opens with radius: a chirp drawn in space."""
    a = [a0]
    while a[-1] < rmax:
        a.append(a[-1] + gap(a[-1]))
    out = []
    for arm in (1, -1):
        for k in range(len(a) - 1):
            s = arm * (1 if k % 2 == 0 else -1)
            r = (a[k] + a[k + 1]) / 2
            out.append(
                f'<path d="M{s * a[k]:.2f} 0A{r:.2f} {r:.2f} 0 0 1 {-s * a[k + 1]:.2f} 0" stroke-width="{width(r):.2f}"></path>'
            )
    return f'<g transform="translate({cx} {cy}) rotate({rot})" fill="none" stroke="{color}">{"".join(out)}</g>'


def wavefield(pid, cx, cy, w, h, ink, rot=-34, rmin=14.0, rmax=340.0, pitch=3.2, weights=(0.5, 1.15, 1.85),
              gap=lambda r: 9.0 + 0.085 * r, duty=(0.52, 0.2)):
    """Engraved wave field. Fine concentric rings carry the tone: each ring
    swells where a wave crest crosses it, in two steps. The crests are a
    two-armed spiral whose pitch opens with radius. Returns (defs, marks)."""
    rings = []
    r = rmin
    while r < rmax:
        rings.append(f"M{cx - r:.2f} {cy}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0")
        r += pitch
    d = "".join(rings)
    defs = ""
    for i, k in enumerate(duty):
        arms = spiral(cx, cy, rot, rmin, rmax, "#fff", gap=gap, width=lambda r, k=k: k * gap(r))
        defs += f'<mask id="{pid}m{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">{arms}</mask>'
    marks = (
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{weights[0]}"></path>'
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{weights[1]}" mask="url(#{pid}m0)"></path>'
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{weights[2]}" mask="url(#{pid}m1)"></path>'
    )
    return defs, marks


def bodies(pid, cx, cy, ground, ink, ang=-34, sep=66, ra=23.0, k_halo=1.95, k_ring=1.5, outline=0.9):
    """Two bodies with radii in the ratio 36 to 29, placed about their
    shared center of mass. Tone is built from swelling lines, then a cross
    screen. The outer tones lean toward the partner, so the pair reads as
    one well and not as two targets."""
    rb = ra * 29 / 36
    da, db = sep * 29 / 65, sep * 36 / 65
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    A = (cx - da * ca, cy - da * sa, ra)
    B = (cx + db * ca, cy + db * sa, rb)
    out = []

    def ring(k, fill, lean=0.0):
        s = ""
        for x, y, r in (A, B):
            x2, y2 = x + (cx - x) * lean, y + (cy - y) * lean
            s += f'<circle cx="{x2:.2f}" cy="{y2:.2f}" r="{r * k:.2f}" fill="{fill}"></circle>'
        return s

    out.append(ring(k_halo, ground, 0.55))
    out.append(ring(k_halo, f"url(#{pid}a1)", 0.55))
    out.append(ring(k_ring, f"url(#{pid}a2)", 0.28))
    out.append(ring(k_ring, f"url(#{pid}b1)", 0.28))
    out.append(ring(1.0, ground))
    out.append(ring(1.0, f"url(#{pid}a3)"))
    out.append(ring(1.0, f"url(#{pid}b3)"))
    out.append("".join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="none" stroke="{ink}" stroke-width="{outline}"></circle>' for x, y, r in (A, B)))
    return "".join(out), A, B


def _closed_path(pts):
    """Closed Catmull-Rom spline through pts, written as cubic curves."""
    n = len(pts)
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + "Z"


def wells(pid, cx, cy, ground, ink, ang=-25, sep=84, ra=17.0, n=10, reach=44.0, night=False, samples=60):
    """The two bodies as a contour map. The lines are equal steps of the
    combined pull of masses 36 and 29: separate rings close in, one shared
    figure farther out. Lines crowd toward each body, so tone deepens the
    way a well does. Radii are in the ratio 36 to 29."""
    m1, m2 = 36.0, 29.0
    rb = ra * m2 / m1
    da, db = sep * m2 / (m1 + m2), sep * m1 / (m1 + m2)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    A = (cx - da * ca, cy - da * sa)
    B = (cx + db * ca, cy + db * sa)

    def phi(x, y):
        return m1 / max(1e-6, math.hypot(x - A[0], y - A[1])) + m2 / max(1e-6, math.hypot(x - B[0], y - B[1]))

    # saddle between the bodies
    ts = [i / 2000 for i in range(1, 2000)]
    tsad = min(ts, key=lambda t: phi(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t))
    S = (A[0] + (B[0] - A[0]) * tsad, A[1] + (B[1] - A[1]) * tsad)
    phi_s = phi(*S)
    # levels read off a ray leaving A on the far side from B
    r_in = ra * 1.16
    q = (reach / r_in) ** (1 / (n - 1))
    levels = [phi(A[0] - ca * r_in * q ** k, A[1] - sa * r_in * q ** k) for k in range(n)]

    def lobe(c, level):
        pts = []
        for i in range(samples):
            th = 2 * math.pi * i / samples
            ux, uy = math.cos(th), math.sin(th)
            r = 2.0
            while phi(c[0] + ux * r, c[1] + uy * r) > level and r < 400:
                r += 0.5
            lo, hi = r - 0.5, r
            for _ in range(30):
                mid = (lo + hi) / 2
                if phi(c[0] + ux * mid, c[1] + uy * mid) > level:
                    lo = mid
                else:
                    hi = mid
            pts.append((c[0] + ux * lo, c[1] + uy * lo))
        return pts

    def envelope(level):
        pts = []
        for i in range(samples):
            th = 2 * math.pi * i / samples
            ux, uy = math.cos(th), math.sin(th)
            r = 300.0
            while phi(S[0] + ux * r, S[1] + uy * r) < level and r > 0.5:
                r -= 0.5
            lo, hi = r, r + 0.5
            for _ in range(30):
                mid = (lo + hi) / 2
                if phi(S[0] + ux * mid, S[1] + uy * mid) > level:
                    lo = mid
                else:
                    hi = mid
            pts.append((S[0] + ux * lo, S[1] + uy * lo))
        return pts

    out = []
    # outermost figure clears the field
    outer = _closed_path(envelope(levels[-1]) if levels[-1] < phi_s else lobe(A, levels[-1]))
    out.append(f'<path d="{outer}" fill="{ground}"></path>')
    for k, lv in enumerate(levels):
        w = 1.0 - 0.45 * k / (n - 1)
        if lv < phi_s * 0.995:
            ds = [_closed_path(envelope(lv))]
        elif lv > phi_s * 1.005:
            ds = [_closed_path(lobe(A, lv)), _closed_path(lobe(B, lv))]
        else:
            continue
        for d in ds:
            out.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{w:.2f}"></path>')
    for (x, y), r in ((A, ra), (B, rb)):
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{ground}"></circle>')
        if night:
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="url(#{pid}n1)"></circle>')
        else:
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="url(#{pid}a3)"></circle>')
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="url(#{pid}b3)"></circle>')
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="none" stroke="{ink}" stroke-width="1.1"></circle>')
    return "".join(out)


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


KEYFRAMES = """@keyframes press{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes sweep{from{stroke-dashoffset:1.01}to{stroke-dashoffset:0}}
@keyframes travel{from{offset-distance:0%}to{offset-distance:100%}}
@keyframes orbit{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}
@keyframes register{from{transform:translate(5px,-3px)}to{transform:none}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}"""


def ink_keyframes(name, w, h, ang=A1):
    """Wipe along the screen angle."""
    k = abs(h / math.tan(math.radians(ang))) / w * 100
    return (
        f"@keyframes {name}{{from{{clip-path:polygon(0% 0%,0% 0%,{-k:.1f}% 100%,0% 100%)}}"
        f"to{{clip-path:polygon(0% 0%,{100 + k:.1f}% 0%,100% 100%,0% 100%)}}}}"
    )


SWEEP_DASH = "stroke-dasharray: 1 1.5"

ARROW = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" aria-hidden="true"><path d="M3 10h13M11 5l5 5-5 5"></path></svg>'
PLUS = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" aria-hidden="true"><path d="M7 1.5v11M1.5 7h11"></path></svg>'
MINUS = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" aria-hidden="true"><path d="M1.5 7h11"></path></svg>'
OUTARROW = '<svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="square" aria-hidden="true"><path d="M2 9l7-7M3.5 2H9v5.5"></path></svg>'
THEME = '<svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="7.25"></circle><path d="M11 3.75a7.25 7.25 0 0 1 0 14.5z" fill="currentColor" stroke="none"></path></svg>'

SUP = 'font-size: 0.56em; line-height: 0; vertical-align: 0.72em; letter-spacing: 0.01em'


def plate_gw(pid, theme="day", W=390, band=140, animate=True, ink_name="inkfeed", margin_top=12):
    """Plate 1: the engraved wave field with the two bodies, and under it,
    on open ground, the live line with its ruler and one readout."""
    day = theme == "day"
    ground = STOCK if day else NG
    ink = INK if day else NS
    fine = INK if day else NX
    txt = INK if day else NT
    sub = INK if day else NM
    live = LIVE if day else AMBER
    PH = band + 132
    cx, cy = 20 + (W - 40) * 0.78, band / 2
    y0, amp, ruler = band + 84, 27, band + 113
    d, xm, crest = chirp(20, y0, W - 40, amp)
    wdefs, wmarks = wavefield(pid, cx, cy, W, band, ink, rot=-25)
    if not day:
        wmarks = wmarks.replace(f'stroke="{ink}" stroke-width="0.5"', f'stroke="{fine}" stroke-width="0.9"', 1)
    bod = wells(pid, cx, cy, ground, ink, night=not day)
    extra = "" if day else patterns(pid, NX, tones={"n1": (A2, 0.3)})
    print_svg = (
        f'<svg viewBox="0 0 {W} {band}" width="{W}" height="{band}" aria-hidden="true" style="display: block">'
        f'<defs>{patterns(pid, ink)}{extra}{wdefs}</defs>{wmarks}{bod}'
        f'</svg>'
    )
    step = (xm - 20) / 10
    ticks, x, i = [], 20.0, 0
    while x <= W:
        ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (6 if i % 5 == 0 else 3.5)}"></line>')
        x += step
        i += 1
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: 9.5px; font-weight: 500; letter-spacing: 0.06em"
    a_sweep = f"; animation: sweep 1900ms linear {at(320)} both" if animate else ""
    a_pen = f"; animation: travel 1900ms linear {at(320)} both, pulse 2400ms ease-in-out {at(2400)} infinite" if animate else ""
    halo = ""
    pen_halo = ""
    if not day:
        halo = (f'<path d="{d}" fill="none" stroke="{live}" stroke-width="6.5" stroke-opacity="0.2" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
                f'style="{SWEEP_DASH}{a_sweep}"></path>')
        pen_halo = f'<circle r="8" fill="{live}" fill-opacity="0.22" style="offset-path: path(\'{d}\'); offset-distance: 100%; offset-rotate: 0deg{a_pen}"></circle>'
    live_svg = (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" '
        f'aria-label="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<g stroke="{ink}" stroke-width="0.75" fill="none">'
        f'<line x1="20" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{"".join(ticks)}'
        f'<line x1="20.4" y1="{y0 + 5}" x2="20.4" y2="{y0 + 11}"></line>'
        f'<line x1="{xm + 9:.1f}" y1="{y0 + 17.5}" x2="{xm + 15:.1f}" y2="{y0 + 17.5}"></line>'
        f'</g>'
        f'<g fill="{sub}" style="{lab}">'
        f'<text x="20" y="{ruler + 17}">0</text>'
        f'<text x="{xm:.1f}" y="{ruler + 17}" text-anchor="middle">0.2 s</text>'
        f'<text x="20" y="{y0 + 21}">35 Hz</text>'
        f'<text x="{xm + 19:.1f}" y="{y0 + 21}">250 Hz</text>'
        f'</g>'
        f'{halo}'
        f'<path d="{d}" fill="none" stroke="{live}" stroke-width="{1.7 if day else 1.5}" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
        f'style="{SWEEP_DASH}{a_sweep}"></path>'
        f'{pen_halo}'
        f'<circle r="3.4" fill="{live}" style="offset-path: path(\'{d}\'); offset-distance: 100%; offset-rotate: 0deg{a_pen}"></circle>'
        f'</svg>'
    )
    a_reg = f"; animation: register 500ms {REGISTER} {at(60)} both" if animate else ""
    a_ink = f"; animation: {ink_name} 520ms {PRESS} {at(60)} both" if animate else ""
    return (
        f'<div style="position: relative; width: {W}px; height: {PH}px; margin-top: {margin_top}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {band}px{a_reg}"><div style="width: {W}px; height: {band}px{a_ink}">{print_svg}</div></div>'
        f'{live_svg}'
        f'<div style="position: absolute; right: 20px; top: {band + 12}px; text-align: right; {mono(9, color=sub)}; line-height: 1.45">Plate 1<br>Illustration, not to scale</div>'
        f'<div style="position: absolute; left: 20px; top: {band + 9}px; display: flex; flex-direction: column; gap: 3px">'
        f'<div style="{disp(42, weight=800 if day else 900, lh=1, color=txt)}; font-variant-numeric: lining-nums">1.0 × 10<sup style="{SUP}">−21</sup></div>'
        f'<div style="{mono(9, color=sub)}">Peak strain, the size of the stretch</div>'
        f'</div>'
        f'</div>'
    )
