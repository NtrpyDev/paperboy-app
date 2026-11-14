"""Eleven small engraved plates, one per field, for the interest picker (take B).

Each emblem is drawn in the plate language of SYSTEM.md section 5: a blue print layer made of
engraved lines and line screens, and a key layer of contours in the text color. No flat floods,
no gradients, no opacity tones. A lighter tone is a thinner line.

  emblem(name, pid, style)             the printed plate: (defs, marks)
  emblem(name, pid, style, ghost=True) the same plate left blank: its key contour only, as a
                                       hairline in the muted color

All geometry is computed here. Do not hand-edit path data in the boards.
Every drawing is an illustration of the field, not data.
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import patterns  # noqa: E402

EW, EH = 110, 76     # one plate, px


class Style:
    """Colors and line weights of one theme."""

    def __init__(self, plate, key, ground, ghost, hair=0.5, kw=0.9, gw=0.6):
        self.P, self.K, self.G, self.GC = plate, key, ground, ghost
        self.hair, self.kw, self.gw = hair, kw, gw


def n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def spline(pts):
    """Open Catmull-Rom spline through pts, as cubic curves."""
    d = f"M{n(pts[0][0])} {n(pts[0][1])}"
    m = len(pts)
    for i in range(m - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}"
    return d


def ring(cx, cy, r):
    return f"M{n(cx - r)} {n(cy)}a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0"


def stroke(d, color, w, extra=""):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{n(w)}"{extra}></path>'


# ------------------------------------------------------------------ physics: two sources, one field
def physics(pid, s, ghost=False):
    """Rings from two sources crossing: interference."""
    a, b = (36.0, 43.0), (76.0, 31.0)
    if ghost:
        d = "".join(ring(c[0], c[1], r) for c in (a, b) for r in (10, 22, 34))
        return "", stroke(d, s.GC, s.gw) + "".join(f'<circle cx="{c[0]}" cy="{c[1]}" r="2.2" fill="{s.G}" stroke="{s.GC}" stroke-width="{s.gw}"></circle>' for c in (a, b))
    fine, crest = "", ""
    for c in (a, b):
        r, i = 6.0, 0
        while r < 112:
            if i % 3 == 2:
                crest += ring(c[0], c[1], r)
            else:
                fine += ring(c[0], c[1], r)
            r += 4.0
            i += 1
    marks = stroke(fine, s.P, s.hair) + stroke(crest, s.P, s.hair + 0.45)
    marks += "".join(f'<circle cx="{c[0]}" cy="{c[1]}" r="2.4" fill="{s.G}" stroke="{s.K}" stroke-width="{s.kw}"></circle>' for c in (a, b))
    return "", marks


# ------------------------------------------------------------------ space: a ringed planet
def space(pid, s, ghost=False):
    cx, cy, r, rot, tilt = 55.0, 38.0, 15.5, -18, 0.3
    rxs = [23.0, 25.4, 27.8, 30.2, 35.0, 37.4, 39.8, 42.2]
    turn = f'transform="rotate({rot} {cx} {cy})"'
    full = lambda rx: f"M{n(cx - rx)} {n(cy)}a{n(rx)} {n(rx * tilt)} 0 1 0 {n(2 * rx)} 0a{n(rx)} {n(rx * tilt)} 0 1 0 {n(-2 * rx)} 0"
    front = lambda rx: f"M{n(cx - rx)} {n(cy)}A{n(rx)} {n(rx * tilt)} 0 0 0 {n(cx + rx)} {n(cy)}"
    if ghost:
        return "", (f'<g {turn}>{stroke(full(rxs[-1]) + full(rxs[0]), s.GC, s.gw)}</g>'
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{s.G}" stroke="{s.GC}" stroke-width="{s.gw}"></circle>'
                    f'<g {turn}>{stroke(front(rxs[-1]) + front(rxs[0]), s.GC, s.gw)}</g>')
    defs = patterns(pid, s.P) + f'<clipPath id="{pid}lit"><circle cx="{cx + 7}" cy="{cy + 6}" r="{r + 1.5}"></circle></clipPath>'
    band = (f"M{n(cx - rxs[-1] - 0.6)} {n(cy)}A{n(rxs[-1] + 0.6)} {n((rxs[-1] + 0.6) * tilt)} 0 0 0 {n(cx + rxs[-1] + 0.6)} {n(cy)}"
            f"L{n(cx + rxs[0] - 0.6)} {n(cy)}A{n(rxs[0] - 0.6)} {n((rxs[0] - 0.6) * tilt)} 0 0 1 {n(cx - rxs[0] + 0.6)} {n(cy)}Z")
    marks = (
        f'<g {turn}>{stroke("".join(full(rx) for rx in rxs), s.P, s.hair)}</g>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{s.G}"></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{pid}b1)"></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{pid}b3)" clip-path="url(#{pid}lit)"></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{s.K}" stroke-width="{s.kw}"></circle>'
        f'<g {turn}><path d="{band}" fill="{s.G}"></path>{stroke("".join(front(rx) for rx in rxs), s.P, s.hair)}</g>'
    )
    return defs, marks


# ------------------------------------------------------------------ math: straight lines, one curve
def maths(pid, s, ghost=False):
    """Straight lines whose envelope is a curve (an astroid)."""
    cx, cy, R, k = 55.0, 38.0, 33.0, 12
    axes = f"M{n(cx - R - 5)} {cy}H{n(cx + R + 5)}M{cx} {n(cy - R - 2.5)}V{n(cy + R + 2.5)}"
    if ghost:
        curve = (f"M{n(cx + R)} {cy}Q{cx} {cy} {cx} {n(cy + R)}Q{cx} {cy} {n(cx - R)} {cy}"
                 f"Q{cx} {cy} {cx} {n(cy - R)}Q{cx} {cy} {n(cx + R)} {cy}")
        return "", stroke(axes + curve, s.GC, s.gw)
    d = ""
    for i in range(1, k):
        t = R * i / k
        for sx in (1, -1):
            for sy in (1, -1):
                d += f"M{n(cx + sx * t)} {cy}L{cx} {n(cy + sy * (R - t))}"
    return "", stroke(d, s.P, s.hair) + stroke(axes, s.K, s.kw)


# ------------------------------------------------------------------ computer science: a rule, run
def computing(pid, s, ghost=False):
    """Rule 110, a one-line program, run row by row. Each row is one engraved line that swells
    where a cell is on."""
    cols, rows, cw, rh, skip = 20, 10, 5.0, 6.6, 9
    x0, y0 = (EW - cols * cw) / 2, (EH - (rows - 1) * rh) / 2
    rule = {(1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0, (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0}
    row = [0] * cols
    row[-1] = 1
    grid = []
    for _ in range(skip + rows):
        grid.append(row)
        row = [rule[(row[(i - 1) % cols], row[i], row[(i + 1) % cols])] for i in range(cols)]
    lines = "".join(f"M{n(x0)} {n(y0 + j * rh)}H{n(x0 + cols * cw)}" for j in range(rows))
    if ghost:
        return "", stroke(lines, s.GC, s.gw)
    runs = ""
    for j, cells in enumerate(grid[skip:]):
        i = 0
        while i < cols:
            if cells[i]:
                e = i
                while e < cols and cells[e]:
                    e += 1
                runs += f'<rect x="{n(x0 + i * cw + 0.5)}" y="{n(y0 + j * rh - 1.7)}" width="{n((e - i) * cw - 1.0)}" height="3.4"></rect>'
                i = e
            else:
                i += 1
    return "", stroke(lines, s.P, s.hair) + f'<g fill="{s.P}">{runs}</g>'


# ------------------------------------------------------------------ biology: a double helix
def biology(pid, s, ghost=False):
    x0, x1, cy, amp, wave = 5.0, 105.0, 38.0, 15.0, 50.0
    ya = lambda x: cy + amp * math.sin(2 * math.pi * (x - x0) / wave)
    yb = lambda x: cy - amp * math.sin(2 * math.pi * (x - x0) / wave)
    xs = [x0 + i * 2.5 for i in range(int((x1 - x0) / 2.5) + 1)]
    A, B = spline([(x, ya(x)) for x in xs]), spline([(x, yb(x)) for x in xs])
    if ghost:
        return "", stroke(A + B, s.GC, s.gw)
    thin, thick = "", ""
    x, i = x0 + 2.2, 0
    while x < x1 - 1:
        if abs(ya(x) - yb(x)) > 5:
            seg = f"M{n(x)} {n(ya(x))}V{n(yb(x))}"
            if i % 2:
                thick += seg
            else:
                thin += seg
        x += 3.1
        i += 1
    marks = stroke(thin, s.P, s.hair) + stroke(thick, s.P, s.hair + 0.7)
    marks += stroke(A, s.K, s.kw + 0.2) + stroke(B, s.K, s.kw + 0.2)
    # at each crossing the strand that is coming forward is redrawn over a ground trap
    k = 0
    xc = x0
    while xc <= x1 + 0.1:
        fn = ya if k % 2 == 0 else yb
        seg = spline([(x, fn(x)) for x in [max(x0, min(x1, xc + t)) for t in (-5, -2.5, 0, 2.5, 5)]])
        if x0 < xc < x1:
            marks += stroke(seg, s.G, 4.2) + stroke(seg, s.K, s.kw + 0.2)
        xc += wave / 2
        k += 1
    return "", marks


# ------------------------------------------------------------------ neuroscience: one neuron
def neuro(pid, s, ghost=False):
    sx, sy, sr = 37.0, 39.0, 7.0
    levels = {0: "", 1: "", 2: "", 3: ""}

    def branch(x, y, ang, ln, depth, bend):
        x2, y2 = x + ln * math.cos(ang), y + ln * math.sin(ang)
        mx, my = (x + x2) / 2 - bend * math.sin(ang), (y + y2) / 2 + bend * math.cos(ang)
        levels[depth] += f"M{n(x)} {n(y)}Q{n(mx)} {n(my)} {n(x2)} {n(y2)}"
        if depth < 3:
            branch(x2, y2, ang - 0.46, ln * 0.74, depth + 1, -bend * 0.8)
            branch(x2, y2, ang + 0.52, ln * 0.70, depth + 1, bend * 0.8)

    for deg, ln, bend in ((118, 11.5, 1.6), (163, 12.5, -1.4), (207, 12.0, 1.5), (250, 11.0, -1.6)):
        a = math.radians(deg)
        branch(sx + sr * math.cos(a), sy + sr * math.sin(a), a, ln, 0, bend)
    axon = f"M{n(sx + sr)} {n(sy)}C56 {n(sy)} 62 31 74 32S89 38 95 33"
    fork = "M95 33Q99 29.5 103.5 28.5M95 33Q99 35.5 103 40.5"
    if ghost:
        return "", (stroke(levels[0] + levels[1] + axon + fork, s.GC, s.gw)
                    + f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="{s.G}" stroke="{s.GC}" stroke-width="{s.gw}"></circle>')
    defs = patterns(pid, s.P)
    sheath = f"M50 {n(sy - 0.6)}C57 {n(sy - 1.5)} 62 31 74 32S86 36.5 90 35.6"
    marks = (
        stroke(sheath, f"url(#{pid}a3)", 4.6, ' stroke-dasharray="8.5 3"')
        + stroke(levels[0], s.K, s.kw + 0.2) + stroke(levels[1], s.K, s.kw) + stroke(levels[2], s.K, s.kw - 0.2) + stroke(levels[3], s.K, s.kw - 0.35)
        + stroke(axon + fork, s.K, s.kw)
        + f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="{s.G}"></circle>'
        f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="url(#{pid}a2)"></circle>'
        f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="url(#{pid}b2)"></circle>'
        f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="none" stroke="{s.K}" stroke-width="{s.kw}"></circle>'
        + "".join(f'<circle cx="{x}" cy="{y}" r="1.5" fill="{s.K}"></circle>' for x, y in ((103.5, 28.5), (103, 40.5)))
    )
    return defs, marks


# ------------------------------------------------------------------ medicine: a pulse on ruled paper
def medicine(pid, s, ghost=False):
    base, period = 45.0, 54.0

    def beat(o):
        return (f"L{n(o + 7)} {base}Q{n(o + 10.5)} {n(base - 6)} {n(o + 14)} {base}L{n(o + 19)} {base}"
                f"L{n(o + 21)} {n(base + 3.5)}L{n(o + 24)} {n(base - 30)}L{n(o + 27.5)} {n(base + 10)}L{n(o + 30)} {base}"
                f"L{n(o + 35)} {base}Q{n(o + 40.5)} {n(base - 10)} {n(o + 46)} {base}")

    trace = f"M-4 {base}" + beat(-10) + beat(-10 + period) + beat(-10 + 2 * period) + f"L{EW + 4} {base}"
    join = ' stroke-linejoin="round" stroke-linecap="round"'
    if ghost:
        return "", stroke(trace, s.GC, s.gw, join)
    pitch = 5.5
    fine, heavy = "", ""
    i, x = 0, 0.0
    while x <= EW + 0.01:
        seg = f"M{n(x)} 0V{EH}"
        if i % 5 == 0:
            heavy += seg
        else:
            fine += seg
        x += pitch
        i += 1
    j, y = 0, base - 7 * pitch
    while y <= EH:
        if y >= 0:
            seg = f"M0 {n(y)}H{EW}"
            if (j - 7) % 5 == 0:
                heavy += seg
            else:
                fine += seg
        y += pitch
        j += 1
    marks = stroke(fine, s.P, s.hair - 0.1) + stroke(heavy, s.P, s.hair + 0.4)
    marks += stroke(trace, s.G, 4.2, join) + stroke(trace, s.K, s.kw + 0.35, join)
    return "", marks


# ------------------------------------------------------------------ chemistry: a ring of six
def chemistry(pid, s, ghost=False):
    cx, cy, R = 51.0, 39.0, 21.0
    v = [(cx + R * math.cos(math.radians(-90 + 60 * i)), cy + R * math.sin(math.radians(-90 + 60 * i))) for i in range(6)]
    hexd = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in v) + "Z"
    out = lambda i, ln: (v[i][0] + ln * math.cos(math.radians(-90 + 60 * i)), v[i][1] + ln * math.sin(math.radians(-90 + 60 * i)))
    subs = [out(1, 17.0), out(4, 15.0)]
    far = (subs[0][0] + 14.5, subs[0][1] + 8.4)
    bonds = (f"M{n(v[1][0])} {n(v[1][1])}L{n(subs[0][0])} {n(subs[0][1])}L{n(far[0])} {n(far[1])}"
             f"M{n(v[4][0])} {n(v[4][1])}L{n(subs[1][0])} {n(subs[1][1])}")
    if ghost:
        return "", stroke(hexd + bonds, s.GC, s.gw)
    defs = patterns(pid, s.P)
    inner = ""
    for i in (0, 2, 4):
        (xa, ya), (xb, yb) = v[i], v[(i + 1) % 6]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        ux, uy = cx - mx, cy - my
        ul = math.hypot(ux, uy)
        ox, oy = ux / ul * 3.6, uy / ul * 3.6
        inner += f"M{n(xa + (xb - xa) * 0.25 + ox)} {n(ya + (yb - ya) * 0.25 + oy)}L{n(xa + (xb - xa) * 0.75 + ox)} {n(ya + (yb - ya) * 0.75 + oy)}"
    atoms = ""
    for (x, y), r, tone in [(p, 3.6, "a1") for p in v] + [(subs[0], 5.2, "a3"), (subs[1], 5.2, "a3"), (far, 4.2, "a2")]:
        cross = f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="url(#{pid}b2)"></circle>' if tone == "a3" else ""
        atoms += (f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{s.G}"></circle>'
                  f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="url(#{pid}{tone})"></circle>{cross}'
                  f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="none" stroke="{s.K}" stroke-width="{s.kw}"></circle>')
    marks = (f'<path d="{hexd}" fill="url(#{pid}b1)"></path>'
             + stroke(hexd + bonds, s.K, s.kw + 0.1) + stroke(inner, s.K, s.kw) + atoms)
    return defs, marks


# ------------------------------------------------------------------ earth: strata and a fault
def earth(pid, s, ghost=False):
    base = [17.0, 29.0, 39.5, 50.0, 61.0, 71.0]
    amp = [3.2, 3.6, 3.0, 3.4, 2.6, 2.2]
    lam = [150.0, 120.0, 135.0, 110.0, 140.0, 125.0]
    ph = [0.4, 1.3, 0.2, 1.9, 0.9, 2.6]
    tones = ["a1", "b2", "a3", "b1", "a2", "b3"]
    xt, xb, drop = 70.0, 57.0, 8.0
    yk = lambda k, x: base[k] + amp[k] * math.sin(2 * math.pi * x / lam[k] + ph[k]) + 0.045 * (x - 55)
    xs = [-10 + 10 * i for i in range(14)]
    line = lambda k: spline([(x, yk(k, x)) for x in xs])
    left = f"M-2 -30H{n(xt + 12 * 30 / EH + 0.0)}L{n(xb - 13 * 30 / EH)} {EH + 30}H-2Z"
    fx = lambda y: xt + (xb - xt) * y / EH
    right = f"M{EW + 2} -30H{n(fx(-30))}L{n(fx(EH + 30))} {EH + 30}H{EW + 2}Z"
    left = f"M-2 -30H{n(fx(-30))}L{n(fx(EH + 30))} {EH + 30}H-2Z"
    defs = f'<clipPath id="{pid}L"><path d="{left}"></path></clipPath><clipPath id="{pid}R"><path d="{right}"></path></clipPath>'
    ytop = yk(0, fx(base[0]))
    fault = f"M{n(fx(ytop))} {n(ytop)}L{n(fx(EH))} {EH}"
    if ghost:
        body = stroke(line(0) + line(2) + line(4), s.GC, s.gw)
        return defs, (f'<g clip-path="url(#{pid}L)">{body}</g><g clip-path="url(#{pid}R)"><g transform="translate(0 {drop})">{body}</g></g>'
                      + stroke(fault, s.GC, s.gw))
    defs += patterns(pid, s.P)
    bands = ""
    for k in range(6):
        top = [(x, yk(k, x)) for x in xs]
        bot = [(x, yk(k + 1, x)) for x in reversed(xs)] if k < 5 else [(xs[-1], EH + 20), (xs[0], EH + 20)]
        d = spline(top) + "L" + "L".join(f"{n(x)} {n(y)}" for x, y in bot) + "Z"
        bands += f'<path d="{d}" fill="url(#{pid}{tones[k]})"></path>'
    seams = stroke("".join(line(k) for k in range(1, 6)), s.P, s.hair + 0.2)
    top = stroke(line(0), s.K, s.kw + 0.1)
    body = bands + seams + top
    marks = (f'<g clip-path="url(#{pid}L)">{body}</g><g clip-path="url(#{pid}R)"><g transform="translate(0 {drop})">{body}</g></g>'
             + stroke(fault, s.G, 3.4) + stroke(fault, s.K, s.kw))
    return defs, marks


# ------------------------------------------------------------------ engineering: a truss
def engineering(pid, s, ghost=False):
    yb, yt, step = 47.0, 22.0, 14.0
    b = [(13.0 + step * i, yb) for i in range(7)]
    t = [(20.0 + step * i, yt) for i in range(6)]
    P = lambda p: f"{n(p[0])} {n(p[1])}"
    chords = f"M{P(b[0])}L{P(b[6])}M{P(t[0])}L{P(t[5])}"
    web = "".join(f"M{P(b[i])}L{P(t[i])}L{P(b[i + 1])}" for i in range(6))
    feet = "".join(f"M{n(x)} {yb}l-5.5 9.5h11Z" for x in (b[0][0], b[6][0]))
    ground = f"M3 {n(yb + 9.5)}H25M85 {n(yb + 9.5)}H107"
    if ghost:
        return "", stroke(chords + web + feet + ground, s.GC, s.gw, ' stroke-linejoin="round"')
    defs = patterns(pid, s.P)
    tri = "".join(f'<path d="M{P(b[i])}L{P(t[i])}L{P(b[i + 1])}Z" fill="url(#{pid}a1)"></path>' for i in range(6))
    tri += "".join(f'<path d="M{P(t[i])}L{P(b[i + 1])}L{P(t[i + 1])}Z" fill="url(#{pid}b2)"></path>' for i in range(5))
    hatch = f'<rect x="3" y="{n(yb + 9.5)}" width="22" height="5" fill="url(#{pid}a3)"></rect><rect x="85" y="{n(yb + 9.5)}" width="22" height="5" fill="url(#{pid}a3)"></rect>'
    joints = "".join(f'<circle cx="{n(x)}" cy="{n(y)}" r="1.9" fill="{s.G}" stroke="{s.K}" stroke-width="{n(s.kw - 0.1)}"></circle>' for x, y in b + t)
    marks = (tri + hatch + stroke(web, s.K, s.kw, ' stroke-linejoin="round"') + stroke(chords, s.K, s.kw + 0.5)
             + f'<path d="{feet}" fill="{s.G}" stroke="{s.K}" stroke-width="{s.kw}" stroke-linejoin="round"></path>'
             + stroke(ground, s.K, s.kw) + joints)
    return defs, marks


# ------------------------------------------------------------------ social science: a distribution
def social(pid, s, ghost=False):
    cx, axis, hgt, sig = 55.0, 61.0, 46.0, 15.0
    y = lambda x: axis - hgt * math.exp(-((x - cx) / sig) ** 2 / 2)
    xs = [9 + 2.0 * i for i in range(47)]
    curve = spline([(x, y(x)) for x in xs])
    ax = f"M5 {axis}H105"
    ticks = "".join(f"M{n(cx + k * sig)} {axis}v4" for k in (-3, -2, -1, 0, 1, 2, 3))
    if ghost:
        return "", stroke(curve + ax + ticks, s.GC, s.gw)
    defs = patterns(pid, s.P) + f'<clipPath id="{pid}mid"><rect x="{n(cx - sig)}" y="0" width="{n(2 * sig)}" height="{EH}"></rect></clipPath>'
    area = curve + f"L{n(xs[-1])} {axis}L{n(xs[0])} {axis}Z"
    drops = f"M{n(cx - sig)} {n(y(cx - sig))}V{axis}M{n(cx + sig)} {n(y(cx + sig))}V{axis}"
    marks = (f'<path d="{area}" fill="url(#{pid}a1)"></path>'
             f'<path d="{area}" fill="url(#{pid}a3)" clip-path="url(#{pid}mid)"></path>'
             + stroke(drops, s.K, 0.6) + stroke(curve, s.K, s.kw + 0.2) + stroke(ax + ticks, s.K, s.kw))
    return defs, marks


EMBLEMS = {
    "physics": physics, "space": space, "math": maths, "cs": computing, "biology": biology,
    "neuroscience": neuro, "medicine": medicine, "chemistry": chemistry, "earth": earth,
    "engineering": engineering, "social": social,
}


def emblem(wire, pid, style, ghost=False, w=EW, h=EH):
    """One plate as an <svg>. The picture is decorative: the button that holds it carries the
    field's name."""
    defs, marks = EMBLEMS[wire](pid, style, ghost=ghost)
    d = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg viewBox="0 0 {EW} {EH}" width="{w}" height="{h}" aria-hidden="true" '
            f'style="display: block; overflow: hidden">{d}{marks}</svg>')
