"""Shared drawing helpers for the Strip Chart angle. Generates SVG path data only;
every number shown as a label in the artboards comes from design/CONTENT.md."""
import math

DAY = dict(stock="#EDF0EA", ink="#0F1F1A", muted="#4C5C55", grid="#C3CFC6", live="#00794C")
NIGHT = dict(ground="#07130F", text="#DDE7DF", muted="#8DA397", grid="#173027", structure="#4A6E5E", live="#62F5A4")

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=B612+Mono:wght@400;700'
         '&family=Big+Shoulders:opsz,wght@10..72,100..900'
         '&family=Literata:ital,opsz,wght@0,7..72,200..900;1,7..72,200..900'
         '&display=swap">')

VOICE = "'Big Shoulders', 'Arial Narrow', 'Helvetica Neue', sans-serif"
SERIF = "'Literata', Georgia, 'Times New Roman', serif"
MONO = "'B612 Mono', 'DejaVu Sans Mono', 'Courier New', monospace"


def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


class Chirp:
    """An illustration of a compact-binary chirp: frequency rising from f0 to f1 over T
    seconds (35 Hz to 250 Hz in 0.2 s, from CONTENT.md), then a fast ring-down.
    The shape is a drawing, not the measured strain. It is always slugged as such."""

    def __init__(self, x0, yc, pps, amp, x_end, T=0.2, f0=35.0, f1=250.0, tau_d=0.0042, lead=0.0, env=0.25, fade=0.0, pre=0.0):
        self.env, self.fade, self.pre = env, fade, pre
        self.x0, self.yc, self.pps, self.amp, self.x_end, self.T = x0, yc, pps, amp, x_end, T
        r = (f0 / f1) ** (8 / 3)
        self.tau0 = T / (1 - r)
        self.tau1 = self.tau0 * r
        self.K = 2 * math.pi * f0 * self.tau0 ** 0.375 * 1.6
        self.f1, self.tau_d, self.lead = f1, tau_d, lead
        self.phT = self._ph(T)
        self.off = (-self.phT) % math.pi
        # normalise so the tallest crest is exactly `amp` and points up
        best, sign = 0, 1
        n = 40000
        t_hi = T + 0.05
        for i in range(n + 1):
            t = -lead + (t_hi + lead) * i / n
            v = self._raw(t)
            if abs(v) > best:
                best, sign, self.t_peak = abs(v), (1 if v > 0 else -1), t
        self.scale = amp / best * sign
        self._build()

    def _ph(self, t):
        tau = self.tau0 - t
        return self.K * (self.tau0 ** 0.625 - tau ** 0.625)

    def _raw(self, t):
        if t <= self.T:
            tau = self.tau0 - t
            v = (tau / self.tau1) ** -self.env * math.sin(self._ph(t) + self.off)
            if self.fade > 0:
                q = min(1.0, max(0.0, (t + self.lead) / self.fade))
                v *= q * q * (3 - 2 * q)
            return v
        u = t - self.T
        return math.exp(-u / self.tau_d) * math.sin(self.phT + self.off + 2 * math.pi * self.f1 * u)

    def pt(self, t):
        return (self.x0 + self.pps * (t + self.lead), self.yc - self.scale * self._raw(t))

    def _build(self):
        step = math.pi / 8
        knots = [-self.lead]
        ph = self._ph(-self.lead)
        k = math.floor(ph / step) + 1
        while k * step < self.phT - 1e-9:
            tau = (self.tau0 ** 0.625 - k * step / self.K) ** 1.6
            knots.append(self.tau0 - tau)
            k += 1
        knots.append(self.T)
        dt = step / (2 * math.pi * self.f1)
        u = dt
        while self.amp * math.exp(-u / self.tau_d) > 0.12:
            knots.append(self.T + u)
            u += dt
        self.t_tail = knots[-1]
        h = 1e-7
        P = [self.pt(t) for t in knots]
        D = [((self.pt(t + h)[0] - self.pt(t - h)[0]) / (2 * h), (self.pt(t + h)[1] - self.pt(t - h)[1]) / (2 * h)) for t in knots]
        segs = []
        d = [f"M{f(P[0][0])} {f(P[0][1])}"]
        if self.pre > 0:
            a = (P[0][0] - self.pre, P[0][1])
            d = [f"M{f(a[0])} {f(a[1])}", f"L{f(P[0][0])} {f(P[0][1])}"]
            segs.append((a, a, P[0], P[0]))
        for i in range(len(knots) - 1):
            w = (knots[i + 1] - knots[i]) / 3
            c1 = (P[i][0] + D[i][0] * w, P[i][1] + D[i][1] * w)
            c2 = (P[i + 1][0] - D[i + 1][0] * w, P[i + 1][1] - D[i + 1][1] * w)
            d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(P[i+1][0])} {f(P[i+1][1])}")
            segs.append((P[i], c1, c2, P[i + 1]))
        # quiet tail out to the parked pen
        last = P[-1]
        end = (self.x_end, self.yc)
        gap = (end[0] - last[0]) / 3
        c1 = (last[0] + gap, last[1])
        c2 = (end[0] - gap, end[1])
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(end[0])} {f(end[1])}")
        segs.append((last, c1, c2, end))
        self.d = " ".join(d)
        # dense polyline of the actual drawn curve, with running arc length
        poly = []
        for (p0, p1, p2, p3) in segs:
            for j in range(24):
                s = j / 24
                a = (1 - s) ** 3
                b = 3 * (1 - s) ** 2 * s
                c = 3 * (1 - s) * s * s
                e = s ** 3
                poly.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
        poly.append(end)
        acc = [0.0]
        for i in range(1, len(poly)):
            acc.append(acc[-1] + math.hypot(poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1]))
        self.poly, self.acc, self.length = poly, acc, acc[-1]
        self.peak = min(poly, key=lambda p: p[1])
        self.trough = max(poly, key=lambda p: p[1])

    def frac_at(self, pt):
        """Fraction of arc length at the polyline vertex nearest to pt."""
        i = min(range(len(self.poly)), key=lambda j: (self.poly[j][0] - pt[0]) ** 2 + (self.poly[j][1] - pt[1]) ** 2)
        return self.acc[i] / self.length

    def extrema(self):
        """Local crests (up) and troughs (down) of the drawn curve as (x, y, kind)."""
        out = []
        p = self.poly
        for i in range(1, len(p) - 1):
            if p[i][1] < p[i - 1][1] and p[i][1] <= p[i + 1][1]:
                out.append((p[i][0], p[i][1], "crest"))
            if p[i][1] > p[i - 1][1] and p[i][1] >= p[i + 1][1]:
                out.append((p[i][0], p[i][1], "trough"))
        return out


def grid(x0, x1, y0, y1, cell, color, holes=(), major_every=5, w_minor=0.5, w_major=0.9, major_color=None, origin_x=None, origin_y=None, horizontal=True):
    """Solid hairline grid inside [x0,x1]x[y0,y1]. `holes` are rects (x0,y0,x1,y1) left blank
    so no grid runs behind text. Lines are split around holes."""
    major_color = major_color or color
    ox = x0 if origin_x is None else origin_x
    oy = y0 if origin_y is None else origin_y
    out = []

    def spans(lo, hi, cuts):
        segs = [(lo, hi)]
        for (a, b) in cuts:
            nxt = []
            for (s, e) in segs:
                if b <= s or a >= e:
                    nxt.append((s, e))
                else:
                    if a > s:
                        nxt.append((s, a))
                    if b < e:
                        nxt.append((b, e))
            segs = nxt
        return segs

    k = math.ceil((x0 - ox) / cell - 1e-9)
    while ox + k * cell <= x1 + 1e-9:
        x = ox + k * cell
        cuts = [(h[1], h[3]) for h in holes if h[0] < x < h[2]]
        maj = (k % major_every == 0)
        for (s, e) in spans(y0, y1, cuts):
            out.append(f'<line x1="{f(x)}" y1="{f(s)}" x2="{f(x)}" y2="{f(e)}" stroke="{major_color if maj else color}" stroke-width="{w_major if maj else w_minor}"></line>')
        k += 1
    k = math.ceil((y0 - oy) / cell - 1e-9)
    while horizontal and oy + k * cell <= y1 + 1e-9:
        y = oy + k * cell
        cuts = [(h[0], h[2]) for h in holes if h[1] < y < h[3]]
        maj = (k % major_every == 0)
        for (s, e) in spans(x0, x1, cuts):
            out.append(f'<line x1="{f(s)}" y1="{f(y)}" x2="{f(e)}" y2="{f(y)}" stroke="{major_color if maj else color}" stroke-width="{w_major if maj else w_minor}"></line>')
        k += 1
    return "".join(out)


def ruler(x0, x1, y, step, color, major_every=5, up=True, minor=4, major=8, w=1, origin=None):
    """A ruler axis: the ticks sit on the axis line, outside the plot."""
    o = x0 if origin is None else origin
    s = -1 if up else 1
    out = [f'<line x1="{f(x0)}" y1="{f(y)}" x2="{f(x1)}" y2="{f(y)}" stroke="{color}" stroke-width="{w}"></line>']
    k = math.ceil((x0 - o) / step - 1e-9)
    while o + k * step <= x1 + 1e-9:
        x = o + k * step
        ln = major if k % major_every == 0 else minor
        out.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(y + s * ln)}" stroke="{color}" stroke-width="{w}"></line>')
        k += 1
    return "".join(out)


def perforation(width, color, pitch=7, r=1.15, y=4, height=8):
    """A tear line between cards: one row of punched holes, full width."""
    n = int(width / pitch) + 1
    dots = "".join(f'<circle cx="{f(pitch/2 + i*pitch)}" cy="{y}" r="{r}"></circle>' for i in range(n))
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-hidden="true" '
            f'style="display: block; flex-shrink: 0" fill="{color}">{dots}</svg>')


def page(title, w, h, helmet_css, body):
    return f'''<!doctype html>
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
'''
