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


# ================================================================== app icon, second pass
# Two masters on one 512 grid. The P sits in the same place in both. The 512 square is the 72 dp
# left of a 108 dp adaptive layer after 18 dp is taken off each side, so 1 dp is 512 / 72 units.
DP = 512 / 72.0
SAFE_R = 33 * DP           # the 66 dp safe zone, as a circle
BLEED = 18 * DP            # 128 units of layer outside the 512 square
ICON_TRAP = 8.0            # rings are held back this far from the P
ICON_CLEAR = 1.47          # ground dot around the pen point, in pen point radii (5 / 3.4)
ICON_HALO = 2.94           # night halo radius, in pen point radii (10 / 3.4)
MASTER = dict(
    large=dict(dot=43.0, pitch=8.0, weights=(1.25, 3.0, 4.75)),
    small=dict(dot=56.0, pitch=24.0, stroke=10.0, rings=5),
)


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def spiral_bands(cx, cy, rot, r0, rmax, gap, duty, taper=0.6, step=6.0):
    """The crest mask as two filled arms of one spiral. The pitch opens with radius, the width is
    continuous, and each arm opens from nothing over `taper` radians, so a ring that crosses an arm
    swells and thins over 15 to 30 degrees of arc and never ends in a cut."""
    st = math.radians(step)
    out = []
    for arm in (0.0, math.pi):
        th, r = 0.0, r0
        inner, outer = [], []
        while r < rmax:
            hw = 0.5 * duty * gap(r) * _smooth(th / taper)
            a = math.radians(rot) + arm + th
            ca, sa = math.cos(a), math.sin(a)
            inner.append((cx + (r - hw) * ca, cy + (r - hw) * sa))
            outer.append((cx + (r + hw) * ca, cy + (r + hw) * sa))
            r += gap(r) / math.pi * st
            th += st
        pts = outer + inner[::-1]
        out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def ring_d(cx, cy, radii):
    return "".join(f"M{cx - r:.2f} {cy:.2f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0" for r in radii)


def icon_geo(master="large", theme="day"):
    """P and pen point on the 512 grid. The P is placed from the large master and does not move."""
    box = G["P_d1"]["boxes"][0]
    pw = (box[2] - box[0]) * ICON_S
    cap = -box[1] * ICON_S
    left = (512 - (pw + ICON_GAP + 2 * MASTER["large"]["dot"])) / 2
    base = (512 + cap) / 2
    nb = G["P_d2" if theme == "night" else "P_d1"]["boxes"][0]
    R = MASTER[master]["dot"]
    right = left + (nb[2] - nb[0]) * ICON_S
    return dict(left=left, base=base, cap=cap, R=R, dot=(right + ICON_GAP + R, base - R), tx=left - nb[0] * ICON_S,
                glyph=G["P_d2" if theme == "night" else "P_d1"]["glyphs"][0])


def _mix(a, b, k):
    pa, pb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02X}" for x, y in zip(pa, pb))


HALO_MODE = ["rings"]      # test switch: none, disc, rings, lit
SMALL_FADE = [0.0]       # 0 keeps every ring of the small master at one weight


def icon_layers(pid, theme="day", master="large", extend=0.0, rot=-118):
    """Returns (defs, background marks, foreground marks) on the 512 grid.
    Background: the ground and the rings, centered on the pen point. Foreground: the P on its
    ground-colored trap, the ground dot, and the pen point. Kept apart so a launcher can move one
    against the other and the rings still never touch the P."""
    if theme == "day":
        ground, ink, plate, live = STOCK, INK, BLUE, LIVE
    elif theme == "night":
        ground, ink, plate, live = NG, NT, NBLUE, AMBER
    elif theme == "mono":
        ground, ink, plate, live = STOCK, INK, None, INK
    else:
        ground, ink, plate, live = INK, STOCK, None, STOCK
    g = icon_geo(master, theme)
    m = MASTER[master]
    cx, cy = g["dot"]
    R = g["R"]
    lo, size = -extend, 512 + 2 * extend
    far = max(math.hypot(cx - lo, cy - lo), math.hypot(lo + size - cx, cy - lo), math.hypot(cx - lo, lo + size - cy), math.hypot(lo + size - cx, lo + size - cy))
    defs, bg = "", f'<rect x="{lo}" y="{lo}" width="{size}" height="{size}" fill="{ground}"></rect>'
    night = theme == "night"
    mode = HALO_MODE[0] if night else "none"
    halo = ""
    if plate and master == "large":
        p = m["pitch"]
        r0 = R * ICON_CLEAR + m["weights"][0] / 2 + 1.0
        n = int((far - r0) / p) + 1
        radii = [r0 + i * p for i in range(n)]
        k_halo = 0
        if mode in ("rings", "lit"):
            k_halo = sum(1 for r in radii if r < R * ICON_HALO)
        d = ring_d(cx, cy, radii[k_halo:] if mode == "rings" else radii)
        gap = lambda r: p * 2.8 + 0.085 * r
        w0, w1, w2 = m["weights"]
        # The swells are drawn the way gw_print() in lib.py draws them on every plate: each one a
        # lune of two arcs that comes to a point at both ends. No mask, and no ring ends in a cut.
        from lib import _spiral_radii, _crest_spans, _lune, _arc_in_view
        arms = _spiral_radii(r0 + p, far + 40, gap)
        rr = math.radians(rot)
        crest = (w1, 0.0) if night else (w1, w2)       # night leaves out the heaviest pass, as the plates do
        broad, narrow = [], []
        for r in radii[k_halo:] if mode == "rings" else radii:
            for dty, peak, bucket in ((0.52, crest[0], broad), (0.2, crest[1], narrow)):
                if peak <= 0:
                    continue
                for s0, s1 in _crest_spans(r, arms, gap, dty):
                    if extend or _arc_in_view(cx, cy, r, s0 + rr, s1 + rr, 512, 512):
                        bucket.append(_lune(cx, cy, r, s0 + rr, s1 + rr, peak))
        fine = f'stroke-width="{w0 * 1.2:.2f}" stroke-opacity="0.55"' if night else f'stroke-width="{w0}"'
        bg += f'<path d="{d}" fill="none" stroke="{plate}" {fine}></path><path d="{"".join(broad)}{"".join(narrow)}" fill="{plate}"></path>'
        if mode == "rings":
            # the halo, engraved: the rings nearest the pen point are drawn in the live light, and
            # thin as they leave it. Tone falls by line weight, the ground stays clean.
            for i, r in enumerate(radii[:k_halo]):
                w = 3.4 - 2.6 * i / max(1, k_halo - 1)
                halo += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{live}" stroke-width="{w:.2f}"></circle>'
        elif mode == "lit":
            for i, r in enumerate(radii[:k_halo]):
                kk = 0.75 - 0.6 * i / max(1, k_halo - 1)
                halo += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{_mix(plate, live, kk)}" stroke-width="{w1:.2f}"></circle>'
    elif plate:
        st = m["stroke"]
        r0 = R * ICON_CLEAR + st / 2
        radii = [r0 + i * m["pitch"] for i in range(m["rings"])]
        ws = [st * (1 - SMALL_FADE[0] * i) for i in range(len(radii))]
        k_halo = 0
        if mode == "rings":
            k_halo = 2
            ws = [st * 0.6, st * 0.3] + ws[2:]
        elif mode == "lit":
            k_halo = 2
        for i, (r, w) in enumerate(zip(radii, ws)):
            col = plate
            if i < k_halo:
                col = live if mode == "rings" else _mix(plate, live, 0.7 - 0.35 * i)
            bg += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{col}" stroke-width="{w:.2f}"></circle>'
    tr = f'transform="translate({g["tx"]:.2f} {g["base"]:.2f}) scale({ICON_S})"'
    fg = ""
    if plate:
        if mode == "disc":
            fg += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{R * ICON_HALO:.1f}" fill="{live}" fill-opacity="0.18"></circle>'
        fg += (f'{halo}<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{R * ICON_CLEAR:.1f}" fill="{ground}"></circle>'
               f'<path d="{g["glyph"]}" {tr} fill="{ground}" stroke="{ground}" stroke-width="{2 * ICON_TRAP / ICON_S:.1f}" stroke-linejoin="round"></path>')
    fg += f'<path d="{g["glyph"]}" {tr} fill="{ink}"></path><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{R}" fill="{live}"></circle>'
    return defs, bg, fg


def _squircle(c=256.0, r=256.0, n=4.6, steps=96):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        ct, s_ = math.cos(t), math.sin(t)
        pts.append((c + r * math.copysign(abs(ct) ** (2 / n), ct), c + r * math.copysign(abs(s_) ** (2 / n), s_)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def app_icon(pid, px, theme="day", master="large", shape=None, layer="both", extend=0.0, guides=False, edge=None, label="Paperboy app icon"):
    """The app icon at px. shape: None (the square), circle, squircle, round. layer: both, bg, fg, mono.
    extend shows layer outside the 512 square. guides draws the 72 dp square and the 66 dp safe zone.
    edge draws the outline of the shape in that color, for an icon whose ground is the board's ground."""
    defs, bg, fg = icon_layers(pid, theme, master, extend)
    lo, size = -extend, 512 + 2 * extend
    u = size / px                      # units per px, so guide lines keep their weight
    clip, cattr = "", ""
    inner = {None: f'<rect x="{lo}" y="{lo}" width="{size}" height="{size}"></rect>', "circle": '<circle cx="256" cy="256" r="256"></circle>',
             "squircle": f'<path d="{_squircle()}"></path>', "round": '<rect x="0" y="0" width="512" height="512" rx="112"></rect>'}[shape]
    if shape:
        clip = f'<clipPath id="{pid}c">{inner}</clipPath>'
        cattr = f' clip-path="url(#{pid}c)"'
    body = ""
    if layer in ("both", "bg"):
        body += bg
    if layer in ("fg", "mono"):
        # an empty layer shows as a light line screen: that part is transparent
        defs += (f'<pattern id="{pid}t" width="{40 * u:.1f}" height="{3 * u:.2f}" patternUnits="userSpaceOnUse" patternTransform="rotate({A2})">'
                 f'<rect x="0" y="0" width="{40 * u:.1f}" height="{0.45 * u:.2f}" fill="{MUTED}"></rect></pattern>')
        body += f'<rect x="{lo}" y="{lo}" width="{size}" height="{size}" fill="url(#{pid}t)"></rect>'
    if layer in ("both", "fg", "mono"):
        body += fg
    marks = ""
    if edge:
        # drawn inside the clip at twice the weight, so half of it shows and the shape keeps its size
        marks += f'<g fill="none" stroke="{edge}" stroke-width="{1.5 * u:.2f}"{cattr}>{inner}</g>'
    if guides:
        marks += (f'<g fill="none" stroke="{INK}" stroke-width="{0.9 * u:.2f}"><rect x="{lo + 0.45 * u:.2f}" y="{lo + 0.45 * u:.2f}" width="{size - 0.9 * u:.2f}" height="{size - 0.9 * u:.2f}"></rect>'
                  f'<rect x="0" y="0" width="512" height="512"></rect><circle cx="256" cy="256" r="{SAFE_R:.1f}"></circle></g>')
    return (f'<svg viewBox="{lo} {lo} {size} {size}" width="{px}" height="{px}" role="img" aria-label="{label}" style="display: block; flex: none">'
            f'<defs>{defs}{clip}</defs><g{cattr}>{body}</g>{marks}</svg>')
