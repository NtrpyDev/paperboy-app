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


def chirp(x0, y0, w, amp, tm=0.78, ring=(3, 0.55, 1.7)):
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


# ---------------------------------------------------------------------------------------
# Plate 1, the shared drawing (revision after CRITIQUE.md, 2026-11-13).
#
# gw_print() is the one generator for the print layers of Plate 1: the engraved wave
# field and the two wells. Every board that shows Plate 1 should call it, at any size.
# What changed against wavefield() + wells():
#   - no SVG mask. A ring swells where a crest crosses it as a filled lune (two arcs
#     through the same end points), so each swell tapers to the hairline at both ends.
#     In Compose that is Path.arcTo twice per swell. SYSTEM.md section 13, ring swelling.
#   - the field fades toward the wells by line weight and line count, never by opacity:
#     the heavy swells stop first, then the light swells, then every other hairline.
#   - the wells have no solid discs. Each closes with contours that tighten to an open
#     center. Radii stay in the ratio 36 to 29 because every contour is a level of the
#     combined pull of the two masses.
PLATE_D = "#1F3FD0"
PLATE_N = "#4D63C9"


def _num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _spiral_radii(rmin, rmax, gap):
    a = [rmin]
    while a[-1] < rmax:
        a.append(a[-1] + gap(a[-1]))
    return a


def _crest_spans(r, a, gap, duty):
    """Angles (radians, in the spiral's own frame) where a ring of radius r lies inside the
    crest band of the two-armed spiral that spiral() draws. Returns merged (start, end)."""
    spans = []
    for arm in (1, -1):
        for k in range(len(a) - 1):
            g = a[k + 1] - a[k]
            R = (a[k] + a[k + 1]) / 2
            hw = duty * gap(R) / 2
            if r < a[k] - hw - g or r > a[k + 1] + hw + g:
                continue
            s = arm * (1 if k % 2 == 0 else -1)
            lo = ((R - hw) ** 2 - r * r - g * g / 4) / (r * g)
            hi = ((R + hw) ** 2 - r * r - g * g / 4) / (r * g)
            lo, hi = max(-1.0, min(1.0, lo)), max(-1.0, min(1.0, hi))
            if hi - lo < 1e-9:
                continue
            if s > 0:      # lower half plane on screen, angle in (0, pi), distance grows with cos
                spans.append((math.acos(hi), math.acos(lo)))
            else:          # upper half plane, angle in (pi, 2 pi), distance falls with cos
                spans.append((2 * math.pi - math.acos(-hi), 2 * math.pi - math.acos(-lo)))
                spans[-1] = (min(spans[-1]), max(spans[-1]))
    spans.sort()
    merged = []
    for s0, s1 in spans:
        if merged and s0 <= merged[-1][1] + 2e-3:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s1))
        else:
            merged.append((s0, s1))
    if len(merged) > 1 and merged[0][0] < 2e-3 and merged[-1][1] > 2 * math.pi - 2e-3:
        first = merged.pop(0)
        merged[-1] = (merged[-1][0], first[1] + 2 * math.pi)
    return merged


def _lune(cx, cy, r, th0, th1, peak):
    """A swelling line: the ring from angle th0 to th1, `peak` px thick at its middle and
    coming to a point at both ends. Two arcs."""
    al = (th1 - th0) / 2
    sag = r * (1 - math.cos(al))
    e = min(peak / 2, sag * 0.45)
    if e < 0.12:
        return ""
    co = (2 * r * e + e * e) / (2 * (r + e - r * math.cos(al)))
    ci = (-2 * r * e + e * e) / (2 * (r - e - r * math.cos(al)))
    ro, ri = r + e - co, r - e - ci
    x0, y0 = cx + r * math.cos(th0), cy + r * math.sin(th0)
    x1, y1 = cx + r * math.cos(th1), cy + r * math.sin(th1)
    return (f"M{_num(x0)} {_num(y0)}A{_num(ro)} {_num(ro)} 0 0 1 {_num(x1)} {_num(y1)}"
            f"A{_num(ri)} {_num(ri)} 0 0 0 {_num(x0)} {_num(y0)}Z")


def _arc_in_view(cx, cy, r, th0, th1, w, h, pad=3.0):
    n = max(2, int((th1 - th0) / math.radians(3)) + 1)
    for i in range(n + 1):
        th = th0 + (th1 - th0) * i / n
        x, y = cx + r * math.cos(th), cy + r * math.sin(th)
        if -pad <= x <= w + pad and -pad <= y <= h + pad:
            return True
    return False


class _Pair:
    """The two masses, 36 and 29, and the contours of their combined pull."""

    def __init__(self, cx, cy, ang=-25, sep=84.0, ra=17.0, samples=72):
        self.m1, self.m2 = 36.0, 29.0
        self.ra, self.samples = ra, samples
        da, db = sep * self.m2 / (self.m1 + self.m2), sep * self.m1 / (self.m1 + self.m2)
        self.ca, self.sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        self.A = (cx - da * self.ca, cy - da * self.sa)
        self.B = (cx + db * self.ca, cy + db * self.sa)
        ts = [i / 2000 for i in range(1, 2000)]
        tsad = min(ts, key=lambda t: self.phi(self.A[0] + (self.B[0] - self.A[0]) * t, self.A[1] + (self.B[1] - self.A[1]) * t))
        self.S = (self.A[0] + (self.B[0] - self.A[0]) * tsad, self.A[1] + (self.B[1] - self.A[1]) * tsad)
        self.phi_s = self.phi(*self.S)

    def phi(self, x, y):
        return (self.m1 / max(1e-6, math.hypot(x - self.A[0], y - self.A[1]))
                + self.m2 / max(1e-6, math.hypot(x - self.B[0], y - self.B[1])))

    def level_at(self, r):
        """The level whose contour passes r px from body A, on the side away from B."""
        return self.phi(self.A[0] - self.ca * r, self.A[1] - self.sa * r)

    def _trace(self, c, level, inward):
        pts = []
        for i in range(self.samples):
            th = 2 * math.pi * i / self.samples
            ux, uy = math.cos(th), math.sin(th)
            if inward:
                lo, hi = 0.0, 400.0     # phi > level at lo is false far out: search the last crossing
                r = 400.0
                while self.phi(c[0] + ux * r, c[1] + uy * r) < level and r > 0.5:
                    r -= 0.5
                lo, hi = r, r + 0.5
            else:
                r = 0.25
                while self.phi(c[0] + ux * r, c[1] + uy * r) > level and r < 400:
                    r += 0.25
                lo, hi = max(0.0, r - 0.25), r
            for _ in range(30):
                mid = (lo + hi) / 2
                if self.phi(c[0] + ux * mid, c[1] + uy * mid) > level:
                    lo = mid
                else:
                    hi = mid
            pts.append((c[0] + ux * lo, c[1] + uy * lo))
        return pts

    def paths(self, level):
        """Closed curves of one level: one shared figure below the saddle, two rings above."""
        if level < self.phi_s * 0.995:
            return [_closed_path(self._trace(self.S, level, True))]
        if level > self.phi_s * 1.005:
            return [_closed_path(self._trace(self.A, level, False)), _closed_path(self._trace(self.B, level, False))]
        return []

    def figure(self, reach):
        """The outline that passes `reach` px from body A: used to clear or thin the field."""
        return "".join(self.paths(self.level_at(reach)))


def wells_open(pair, ground, ink, k=1.0, reach=44.0, r_core=3.4, step=(2.0, 0.05), weights=(0.55, 0.8), knock=True):
    """The two wells as contours only, with no solid discs. The contours are levels of the
    combined pull, read off a ray leaving body A. Their spacing closes slowly toward each
    center, so the tone deepens the way a well does and the center stays open."""
    radii, r = [], reach * k
    while r > r_core * k:
        radii.append(r)
        r -= (step[0] * k + step[1] * r)
    out = []
    if knock:
        out.append(f'<path d="{pair.figure(reach * k)}" fill="{ground}"></path>')
    n = len(radii)
    by_weight = {}
    for i, rr in enumerate(radii[1:] if knock else radii, start=1 if knock else 0):
        wgt = weights[0] + (weights[1] - weights[0]) * (i / max(1, n - 1)) ** 0.8
        by_weight.setdefault(f"{wgt * (0.75 + 0.25 * k):.2f}", []).extend(pair.paths(pair.level_at(rr)))
    for wgt, ds in by_weight.items():
        out.append(f'<path d="{"".join(ds)}" fill="none" stroke="{ink}" stroke-width="{wgt}"></path>')
    return "".join(out)


def gw_print(pid, cx, cy, w, h, theme="day", k=1.0, rot=-25, ang=-25, plate=None, key=None, ground=None,
             pitch=3.2, rmin=14.0, hair=None, crest=None, duty=(0.52, 0.2), gap=lambda r: 9.0 + 0.085 * r,
             soft=(60.0, 76.0), near=(50.0, 66.0, 0.62), ramp=(46.0, 118.0)):
    """Plate 1, the print layers. Returns ((blue_defs, blue_marks), (key_defs, key_marks)).

    cx, cy   center of the ring field and of the pair of wells
    k        scale of the wells (1.0 is the 390 px phone plate)
    hair     (width, opacity) of the fine ring pass. Day (0.5, 1), night (0.6, 0.55).
    crest    peak thickness of the broad and the narrow swell. Day (1.5, 2.3). Night
             (1.4, 0): the heaviest pass is left out at night so the plate stays dim and
             the amber line leads (CRITIQUE system fix 2; the director confirms).
    soft     distances from body A, in px at k = 1, where the light swells and the heavy
             swells end. A swell that meets one of these contours is redrawn shorter, so it
             still comes to a point and never ends in a cut.
    ramp     ring radii, in px at k = 1, between which the swells grow from nothing to full
             height, so the field starts quietly at the wells and no short swell sits alone.
    near     (r0, r1, width) in px at k = 1. No ring is drawn inside r0. From r0 to r1 only
             every other ring is drawn, at `width`. Fine rings crowded into the notches
             beside the wells broke into dashes on a 2x screen (CRITIQUE, Feed Day fix 5).
    """
    day = theme == "day"
    plate = plate or (PLATE_D if day else PLATE_N)
    key = key or (INK if day else NM)
    ground = ground or (STOCK if day else NG)
    hair = hair or ((0.5, 1.0) if day else (0.6, 0.55))
    crest = crest or ((1.5, 2.3) if day else (1.4, 0.0))
    pair = _Pair(cx, cy, ang=ang, sep=84.0 * k, ra=17.0 * k)

    rmax = max(math.hypot(x - cx, y - cy) for x in (0, w) for y in (0, h)) + pitch
    a = _spiral_radii(rmin, rmax + 40, gap)
    rr = math.radians(rot)

    def outside_runs(r, th0, th1, level, inner=None):
        """The parts of an arc that lie outside the contour of `level` (and, when `inner`
        is given, inside the contour of `inner`)."""
        def out(th):
            v = pair.phi(cx + r * math.cos(th), cy + r * math.sin(th))
            return v < level and (inner is None or v > inner)
        n = max(8, int(r * (th1 - th0) / 1.5))
        ths = [th0 + (th1 - th0) * i / n for i in range(n + 1)]
        flags = [out(t) for t in ths]
        if all(flags):
            return [(th0, th1)]

        def edge(t_in, t_out):
            for _ in range(24):
                m = (t_in + t_out) / 2
                if out(m):
                    t_out = m
                else:
                    t_in = m
            return t_out

        runs, start = [], ths[0] if flags[0] else None
        for i in range(1, n + 1):
            if flags[i] and not flags[i - 1]:
                start = edge(ths[i - 1], ths[i])
            elif not flags[i] and flags[i - 1]:
                runs.append((start, edge(ths[i], ths[i - 1])))
                start = None
        if start is not None:
            runs.append((start, ths[-1]))
        return runs

    allr, even, broad, narrow = [], [], [], []
    r, i = rmin, 0
    while r < rmax:
        full = f"M{_num(cx - r)} {_num(cy)}a{_num(r)} {_num(r)} 0 1 0 {_num(2 * r)} 0a{_num(r)} {_num(r)} 0 1 0 {_num(-2 * r)} 0"
        if r >= near[1] * k:
            allr.append(full)
        elif r >= near[0] * k and i % 2 == 0:
            even.append(full)
        for dty, peak, reach, bucket in ((duty[0], crest[0], soft[0], broad), (duty[1], crest[1], soft[1], narrow)):
            if peak <= 0:
                continue
            level = pair.level_at(reach * k)
            for s0, s1 in _crest_spans(r, a, gap, dty):
                t0, t1 = s0 + rr, s1 + rr
                if not _arc_in_view(cx, cy, r, t0, t1, w, h):
                    continue
                mid, al = (t0 + t1) / 2, (t1 - t0) / 2
                for u0, u1 in outside_runs(r, t0, t1, level):
                    off = 0.0 if u0 <= mid <= u1 else min(abs(u0 - mid), abs(u1 - mid))
                    pk = peak * (1 - (off / al) ** 2)
                    part = (u1 - u0) / (t1 - t0)
                    if part < 0.4:
                        continue          # no stubs: a swell cut to a short piece is left out
                    if part < 1 - 1e-6:
                        pk = min(pk, peak * part)
                    pk *= max(0.0, min(1.0, (r - ramp[0] * k) / ((ramp[1] - ramp[0]) * k)))
                    if _arc_in_view(cx, cy, r, u0, u1, w, h):
                        bucket.append(_lune(cx, cy, r, u0, u1, pk))
        r += pitch
        i += 1

    ho = f' stroke-opacity="{hair[1]}"' if hair[1] < 1 else ""
    blue_defs = ""
    blue = (
        f'<path d="{"".join(allr)}" fill="none" stroke="{plate}" stroke-width="{hair[0]}"{ho}></path>'
        f'<path d="{"".join(even)}" fill="none" stroke="{plate}" stroke-width="{near[2]}"{ho}></path>'
        f'<path d="{"".join(broad)}" fill="{plate}"></path>'
    )
    if narrow:
        blue += f'<path d="{"".join(narrow)}" fill="{plate}"></path>'
    return (blue_defs, blue), ("", wells_open(pair, ground, key, k=k))


# The night halo and the traps under a live line (CRITIQUE system fix 1). The ground trap is
# narrow and the halo is wider than the trap, so the halo lies over the plate and warms it.
# CRITIQUE asks for a 4 px ground trap, an 11 px halo at about 0.16 and a pen halo of 10 px
# radius at about 0.18. Drawn as one flat step on open ground that still read as a brown
# pill. So the halo is three strokes that add up to those values (0.16 across the 11 px
# band, 0.18 across the 10 px disc), a little stronger close to the line and with a faint
# feather outside, so it falls off the way light does. PB_HALO=flat draws the one-step form.
HALO = [(17.0, 0.05), (11.0, 0.12), (6.0, 0.08)]      # (stroke width, opacity), widest first
PEN_HALO = [(13.0, 0.05), (10.0, 0.14), (6.5, 0.09)]  # (radius, opacity)
if os.environ.get("PB_HALO") == "flat":
    HALO = [(11.0, 0.16)]
    PEN_HALO = [(10.0, 0.18)]


def live_under_strokes(d, day, ground, live, style=""):
    """The strokes under the core of a live line, in drawing order."""
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    if day:
        return f'<path d="{d}" {line} stroke="{ground}" stroke-width="7" style="{style}"></path>'
    return (f'<path d="{d}" {line} stroke="{ground}" stroke-width="4" style="{style}"></path>'
            + "".join(f'<path d="{d}" {line} stroke="{live}" stroke-width="{wd:g}" stroke-opacity="{op:g}" style="{style}"></path>' for wd, op in HALO))


def pen_under_marks(day, ground, live, style=""):
    """The marks under the pen point, in drawing order."""
    if day:
        return f'<circle r="6.5" fill="{ground}" style="{style}"></circle>'
    return (f'<circle r="5" fill="{ground}" style="{style}"></circle>'
            + "".join(f'<circle r="{rd:g}" fill="{live}" fill-opacity="{op:g}" style="{style}"></circle>' for rd, op in PEN_HALO))


# Signs drawn as strokes, so they hold beside weight 800 numerals (CRITIQUE system fix 3).
# Each sits in a 0.5em box on the numeral's optical center and scales with the font size.
def sign_times(stroke=1.05):
    return (f'<svg viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="{stroke}" aria-hidden="true" '
            f'style="display: inline-block; width: 0.5em; height: 0.5em; margin: 0 0.13em 0 0.15em; vertical-align: 0.1em">'
            f'<path d="M1.6 1.6l6.8 6.8M8.4 1.6l-6.8 6.8"></path></svg>')


def sign_gt(stroke=1.05):
    return (f'<svg viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="{stroke}" stroke-linejoin="miter" aria-hidden="true" '
            f'style="display: inline-block; width: 0.5em; height: 0.5em; margin: 0 0.12em 0 0; vertical-align: 0.1em">'
            f'<path d="M1.8 1.4l6.6 3.6-6.6 3.6"></path></svg>')


CHECK = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" aria-hidden="true"><path d="M2 7.6l3.4 3.4 6.6-8"></path></svg>'


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
@keyframes sweep{from{stroke-dashoffset:1.003}to{stroke-dashoffset:0}}
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
