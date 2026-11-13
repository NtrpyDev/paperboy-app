"""Plate 1 and the live line, as revised after CRITIQUE.md. Self-contained on top of
scratch/engraved/lib.py, so any board can call it:

    from plate import plate1, chirp2, live_paths, pen_point

What changed against scratch/feed/plates.py (plate1, soft=2), which this is built from:

  - the wells are open. The two solid discs are gone. Each well is closed by contour lines
    that tighten toward its center, and the center is left as paper (CRITIQUE, Feed Day 1,
    Explainer Night 3);
  - the chirp ends cleanly: three decaying cycles after the peak, then a flat run into the
    pen point (CRITIQUE, Feed Day 2);
  - night: ground trap 4 px, halo 11 px at 0.16 drawn over the plate, core 1.9 px, and the
    heaviest ring pass is drawn in a dimmer blue (CRITIQUE, system fixes 1 and 2).

No path data is hand-edited.
"""
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import (INK, STOCK, MUTED, LIVE, NG, NT, NM, NS, AMBER, MONO, PRESS, REGISTER,  # noqa: E402
                 SWEEP_DASH, at, wavefield, _closed_path)

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
NBLUE_DIM = "#3B4C9E"            # the heaviest ring pass at night
W, M, BAND = 390, 20, 196
PH = BAND + 34
LAB = 10.5
LABEL = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"

# the live line, night (CRITIQUE system fix 1). PB_HALO=a,b,c,d overrides for comparisons.
N_TRAP, N_HALO, N_HALO_O, N_CORE = 4.0, 11.0, 0.16, 1.9
N_PEN_TRAP, N_PEN_HALO, N_PEN_HALO_O = 5.0, 10.0, 0.18
D_TRAP, D_CORE = 7.0, 1.9
NIGHT_HEAVY = os.environ.get("PB_NHEAVY", "dim")     # dim | drop | full


def tokens(theme):
    day = theme == "day"
    return dict(day=day, ground=STOCK if day else NG, text=INK if day else NT, muted=MUTED if day else NM,
                plate=BLUE if day else NBLUE, key=INK if day else NM, live=LIVE if day else AMBER,
                grid=MUTED if day else NS, chrome=INK if day else NM)


# ------------------------------------------------------------------ the chirp
def chirp2(x0, y0, w, amp, tm=0.78, tr=0.11):
    """The live line: a smooth chirp as cubic curves. Illustration only.
    Up to the merger at tm it is lib.chirp. After it the line rings down in three decaying
    cycles, reaches zero at tm + tr with zero slope, and runs flat to the end.
    Returns a dict: d (path), xm (x of the merger), y(t), phase(t), env(t) with t in 0..1."""
    c1, c4 = 2.0, 7.0
    rate_m = 2 * math.pi * (c1 + 4 * c4) / tm
    ph_m = 2 * math.pi * (c1 + c4)
    te = tm + tr

    def env(t):
        if t <= tm:
            u = t / tm
            return 0.06 + 0.94 * u ** 3
        if t >= te:
            return 0.0
        v = (t - tm) / tr
        return (1 - v) ** 1.5 * math.exp(-1.0 * v)

    def phase(t):
        if t <= tm:
            u = t / tm
            return 2 * math.pi * (c1 * u + c4 * u ** 4)
        return ph_m + rate_m * (t - tm)

    def rate(t):
        if t <= tm:
            u = t / tm
            return 2 * math.pi * (c1 + 4 * c4 * u ** 3) / tm
        return rate_m

    def y(t):
        return -amp * env(t) * math.sin(phase(t))

    def dy(t):
        if abs(t - tm) < 1e-9:
            return -amp * math.cos(ph_m) * rate_m
        if t >= te - 1e-9:
            return 0.0
        h = 1e-6
        a, b = max(0.0, t - h), min(1.0, t + h)
        if a < tm < b:
            a, b = (a, t) if t < tm else (t, b)
        return (y(b) - y(a)) / (b - a)

    ts = [0.0]
    while ts[-1] < 1.0 - 1e-9:
        t = ts[-1]
        if t >= te - 1e-9:
            ts.append(1.0)
            break
        nt = t + min(0.02, (math.pi / 6) / rate(t))
        if t < tm - 1e-9 and nt > tm:
            nt = tm
        if t < te - 1e-9 and nt > te:
            nt = te
        ts.append(min(1.0, nt))
    pts = [(x0 + w * t, y0 + y(t), dy(t) / w) for t in ts]
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for (xa, ya, sa), (xb, yb, sb) in zip(pts, pts[1:]):
        if abs(ya - y0) < 1e-6 and abs(yb - y0) < 1e-6 and sa == 0 and sb == 0:
            d += f"H{xb:.2f}"
            continue
        k = (xb - xa) / 3
        d += f"C{xa + k:.2f} {ya + sa * k:.2f} {xb - k:.2f} {yb - sb * k:.2f} {xb:.2f} {yb:.2f}"
    return dict(d=d, xm=x0 + w * tm, xe=x0 + w * te, y=lambda t: y0 + y(t), phase=phase, env=env, tm=tm, te=te)


# ------------------------------------------------------------------ the wells
WELL_RADII = [6.5]
while WELL_RADII[-1] < 42:
    WELL_RADII.append(WELL_RADII[-1] + 2.3 + 0.2 * (len(WELL_RADII) - 1))


def wells2(cx, cy, ink, ang=-25, sep=84, radii=None, samples=72, w_in=0.85, w_out=0.55):
    """The two bodies as a contour map with open centers. The lines are levels of the combined
    pull of masses 36 and 29, read off a ray leaving the heavier body at the radii given, so
    they tighten toward each center and merge into one shared figure farther out.
    Returns dict: marks (the contour strokes), figure(reach) (path data of the closed figure
    at that distance, for knockouts and masks), knock (path data of the outermost figure)."""
    radii = radii or WELL_RADII
    m1, m2 = 36.0, 29.0
    da, db = sep * m2 / (m1 + m2), sep * m1 / (m1 + m2)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    A = (cx - da * ca, cy - da * sa)
    B = (cx + db * ca, cy + db * sa)

    def phi(x, y):
        return m1 / max(1e-6, math.hypot(x - A[0], y - A[1])) + m2 / max(1e-6, math.hypot(x - B[0], y - B[1]))

    ts = [i / 2000 for i in range(1, 2000)]
    tsad = min(ts, key=lambda t: phi(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t))
    S = (A[0] + (B[0] - A[0]) * tsad, A[1] + (B[1] - A[1]) * tsad)
    phi_s = phi(*S)
    level = lambda r: phi(A[0] - ca * r, A[1] - sa * r)

    def lobe(c, lv):
        pts = []
        for i in range(samples):
            th = 2 * math.pi * i / samples
            ux, uy = math.cos(th), math.sin(th)
            r = 0.4
            while phi(c[0] + ux * r, c[1] + uy * r) > lv and r < 400:
                r += 0.4
            lo, hi = max(0.0, r - 0.4), r
            for _ in range(30):
                mid = (lo + hi) / 2
                if phi(c[0] + ux * mid, c[1] + uy * mid) > lv:
                    lo = mid
                else:
                    hi = mid
            pts.append((c[0] + ux * lo, c[1] + uy * lo))
        return pts

    def envelope(lv):
        pts = []
        for i in range(samples):
            th = 2 * math.pi * i / samples
            ux, uy = math.cos(th), math.sin(th)
            r = 300.0
            while phi(S[0] + ux * r, S[1] + uy * r) < lv and r > 0.5:
                r -= 0.5
            lo, hi = r, r + 0.5
            for _ in range(30):
                mid = (lo + hi) / 2
                if phi(S[0] + ux * mid, S[1] + uy * mid) > lv:
                    lo = mid
                else:
                    hi = mid
            pts.append((S[0] + ux * lo, S[1] + uy * lo))
        return pts

    def figure(reach):
        lv = level(reach)
        return _closed_path(envelope(lv) if lv < phi_s else lobe(A, lv))

    out = []
    n = len(radii) - 1          # the last radius is the knockout edge and is not stroked
    for k, r in enumerate(radii[:-1]):
        lv = level(r)
        wd = w_in + (w_out - w_in) * k / max(1, n - 1)
        if lv < phi_s * 0.995:
            ds = [_closed_path(envelope(lv))]
        elif lv > phi_s * 1.005:
            ds = [_closed_path(lobe(A, lv)), _closed_path(lobe(B, lv))]
        else:
            continue
        for d in ds:
            out.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{wd:.2f}"></path>')
    return dict(marks="".join(out), figure=figure, knock=figure(radii[-1]), A=A, B=B)


# ------------------------------------------------------------------ the live line
def live_paths(d, t, anim="", halo=True):
    """(under, core) for a live line that sweeps. under is the trap, and at night the halo."""
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    st = f'style="{SWEEP_DASH}{anim}"'
    if t["day"]:
        under = f'<path d="{d}" {line} stroke="{t["ground"]}" stroke-width="{D_TRAP}" {st}></path>'
        core = f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{D_CORE}" {st}></path>'
    else:
        under = f'<path d="{d}" {line} stroke="{t["ground"]}" stroke-width="{N_TRAP}" {st}></path>'
        if halo:
            under += f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{N_HALO}" stroke-opacity="{N_HALO_O}" {st}></path>'
        core = f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{N_CORE}" {st}></path>'
    return under, core


def still_paths(d, t, halo=True):
    """The same strokes with no sweep, for a line shown part drawn behind a clip."""
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round"'
    if t["day"]:
        return (f'<path d="{d}" {line} stroke="{t["ground"]}" stroke-width="{D_TRAP}"></path>'
                f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{D_CORE}"></path>')
    h = f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{N_HALO}" stroke-opacity="{N_HALO_O}"></path>' if halo else ""
    return (f'<path d="{d}" {line} stroke="{t["ground"]}" stroke-width="{N_TRAP}"></path>{h}'
            f'<path d="{d}" {line} stroke="{t["live"]}" stroke-width="{N_CORE}"></path>')


def pen_point(t, pos, ride="", last="", halo=True):
    """The pen point: trap, (halo at night), dot. pos is the style or attributes that place it."""
    def circ(r, fill, extra="", anim=ride):
        if pos.startswith("cx="):
            st = f' style="{anim.lstrip("; ")}"' if anim else ""
            return f'<circle {pos} r="{r}" fill="{fill}"{extra}{st}></circle>'
        return f'<circle r="{r}" fill="{fill}"{extra} style="{pos}{anim}"></circle>'
    if t["day"]:
        return circ(6.5, t["ground"]) + circ(3.6, t["live"], anim=last or ride)
    h = circ(N_PEN_HALO, t["live"], f' fill-opacity="{N_PEN_HALO_O}"') if halo else ""
    return circ(N_PEN_TRAP, t["ground"]) + h + circ(3.4, t["live"], anim=last or ride)


def ring_marks(pid, cx, cy, w, h, t, rot, rmin, rmax, holes=()):
    """The engraved wave field. holes: (mask index, path data) pairs cut out of the two heavier
    ring passes. Night: the finest pass at 0.55 opacity, the heaviest in a dimmer blue."""
    wdefs, wmarks = wavefield(pid, cx, cy, w, h, t["plate"], rot=rot, rmin=rmin, rmax=rmax)
    parts = wdefs.split("</mask>")
    for i, d in holes:
        parts[i] += f'<path d="{d}" fill="#000"></path>'
    wdefs = "</mask>".join(parts)
    if not t["day"]:
        p = t["plate"]
        wmarks = wmarks.replace(f'stroke="{p}" stroke-width="0.5"', f'stroke="{p}" stroke-width="0.6" stroke-opacity="0.55"', 1)
        if NIGHT_HEAVY == "dim":
            wmarks = wmarks.replace(f'stroke="{p}" stroke-width="1.85"', f'stroke="{NBLUE_DIM}" stroke-width="1.85"', 1)
        elif NIGHT_HEAVY == "drop":
            head, _, tail = wmarks.rpartition('<path d="')
            wmarks = head
    return wdefs, wmarks


# ------------------------------------------------------------------ Plate 1
def plate1(pid, theme, animate=True, start=320, sweep_ms=1900, wipe=60, ink_name="inkproof", margin_top=12):
    t = tokens(theme)
    day = t["day"]
    cx, cy = M + (W - 2 * M) * 0.76, 62
    y0, amp = 157, 29
    ch = chirp2(M, y0, W - 2 * M, amp)
    d, xm = ch["d"], ch["xm"]
    ruler = BAND

    wl = wells2(cx, cy, t["key"])
    # the heavy ring pass stops well short of the figure, the middle pass a little closer,
    # and only the hairline pass runs on to it. Tone falls by line weight, not by opacity.
    wdefs, wmarks = ring_marks(pid, cx, cy, W, BAND, t, rot=-25, rmin=14.0, rmax=420.0,
                               holes=((0, wl["figure"](58.0)), (1, wl["figure"](74.0))))
    svg = lambda inner, defs="": (f'<svg viewBox="0 0 {W} {BAND}" width="{W}" height="{BAND}" aria-hidden="true" style="display: block">'
                                  f'<defs>{defs}</defs>{inner}</svg>')
    blue_svg = svg(wmarks, wdefs)
    key_svg = svg(f'<path d="{wl["knock"]}" fill="{t["ground"]}"></path>{wl["marks"]}')

    step = (xm - M) / 10
    ticks, x, i = [], float(M), 0
    while x <= W:
        ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
        x += step
        i += 1
    sweep = f"; animation: sweep {sweep_ms}ms linear {at(start)} both" if animate else ""
    ride = f"; animation: travel {sweep_ms}ms linear {at(start)} both" if animate else ""
    pulse = (f"; animation: travel {sweep_ms}ms linear {at(start)} both, pulse 2400ms ease-in-out {at(max(2400, start + sweep_ms + 200))} infinite"
             if animate else "")
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"
    under, core = live_paths(d, t, sweep)
    live_svg = (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" '
        f'aria-label="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ruler - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'{under}{core}'
        f'<g stroke="{t["text"]}" stroke-width="0.9" fill="none"><line x1="{M}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{"".join(ticks)}</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{t["text"]}" stroke-width="9"></line></g></g>'
        f'<g fill="{t["text"]}" style="{LABEL}">'
        f'<text x="{M}" y="{ruler + 20}">0</text>'
        f'<text x="{(M + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
        f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text></g>'
        f'{pen_point(t, pen, ride, pulse)}'
        f'</svg>'
    )
    reg_a = f"; animation: registerA 480ms {REGISTER} {at(wipe)} both" if animate else ""
    reg_b = f"; animation: registerB 480ms {REGISTER} {at(wipe)} both" if animate else ""
    ink = f"; animation: {ink_name} 520ms {PRESS} {at(wipe)} both" if animate else ""
    return (
        f'<div style="position: relative; width: {W}px; height: {PH}px; margin-top: {margin_top}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {BAND}px{ink}">'
        f'<div style="position: absolute; left: 0; top: 0{reg_a}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0{reg_b}">{key_svg}</div>'
        f'</div>'
        f'{live_svg}'
        f'</div>'
    )
