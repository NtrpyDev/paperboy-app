"""Shared geometry and tokens for the Two-Ink Overprint artboards (Cand-y)."""
import math

# ---- palette (from BRIEF.md section 10, angle overprint) ----
STOCK = "#F2F1EC"
INDIGO = "#1D0C72"   # blue multiplied with pink; the day text color
MUTED = "#4A3F8F"
BLUE = "#1F3FD0"
PINK = "#F0308C"

N_GROUND = "#0C0A26"
N_TEXT = "#F2EFF8"
N_MUTED = "#A9A4C8"
N_BLUE = "#7A97FF"
N_PINK = "#FF74B8"
N_OVER = "#FFC6FF"
N_STRUCT = "#5A56A8"
N_TEX = "#272458"
N_LIVE = "#FFF7FB"

VOICE = "'Bricolage Grotesque', 'Arial Black', 'Helvetica Neue', sans-serif"
TEXT = "'Schibsted Grotesk', 'Helvetica Neue', Arial, sans-serif"
MONO = "'Martian Mono', 'DejaVu Sans Mono', 'Courier New', monospace"

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800'
         '&family=Martian+Mono:wdth,wght@75..112.5,100..800'
         '&family=Schibsted+Grotesk:ital,wght@0,400..900;1,400..900&display=swap">')

BLUE_ANGLE = 15
PINK_ANGLE = 75
PITCH = 4.0


def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pattern(pid, ink, angle, w, pitch=PITCH):
    y = (pitch - w) / 2
    return (f'<pattern id="{pid}" width="600" height="{f(pitch)}" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate({angle})"><rect x="0" y="{y:.2f}" width="600" height="{w:.2f}" fill="{ink}"></rect></pattern>')


def tone_weights(n, wmin, wmax, gamma=1.0):
    return [wmin + (wmax - wmin) * (i / (n - 1)) ** gamma for i in range(n)]


def tone_patterns(prefix, ink, angle, weights, pitch=PITCH):
    return "".join(pattern(f"{prefix}{i}", ink, angle, w, pitch) for i, w in enumerate(weights))


def circle_d(cx, cy, r):
    return f"M{f(cx - r)} {f(cy)}a{f(r)} {f(r)} 0 1 0 {f(2 * r)} 0a{f(r)} {f(r)} 0 1 0 {f(-2 * r)} 0Z"


def well(cx, cy, R, rh, prefix, n, curve=1.0):
    """A disc whose line screen thickens toward a knocked-out center (the horizon).
    Rings are drawn large to small; every ring uses the same screen so the lines run through."""
    out = []
    for i in range(n):
        t = (i / n) ** curve
        r = R - (R - rh) * t
        out.append(f'<path fill-rule="evenodd" d="{circle_d(cx, cy, r)}{circle_d(cx, cy, rh)}" fill="url(#{prefix}{i})"></path>')
    return "".join(out)


def chirp_points(width, amp, seg=1.2, merge=0.76, ratio=5.5, cycles=9.5, decay=5.0, lead=0.05):
    """Illustrative inspiral chirp. Frequency follows (1 - k u)^(-3/8), amplitude follows f^(2/3),
    then a damped ringdown. Returned samples are at most `seg` px apart along the curve,
    so round joins leave no visible corner. y is negative upward."""
    k = 1 - ratio ** (-8 / 3)
    C = 2 * math.pi * cycles * (k * 5 / 8) / (1 - (1 - k) ** (5 / 8))
    f_end = C * ratio / (2 * math.pi)  # cycles per unit u at merger

    def y_at(t):
        if t < merge:
            u = t / merge
            fr = (1 - k * u) ** (-3 / 8)
            ph = C * (1 - (1 - k * u) ** (5 / 8)) / (k * 5 / 8)
            a = amp * (fr / ratio) ** (2 / 3)
            if t < lead:
                s = t / lead
                a *= s * s * (3 - 2 * s)
        else:
            v = (t - merge) / (1 - merge)
            u_span = (1 - merge) / merge
            ph = 2 * math.pi * cycles + 2 * math.pi * f_end * u_span * v * (1 - 0.18 * v)
            a = amp * math.exp(-decay * v)
        return -a * math.sin(ph)

    n = int(width / 0.02)
    fine = [(width * i / n, y_at(i / n)) for i in range(n + 1)]
    pts = [fine[0]]
    acc = 0.0
    for i in range(1, len(fine)):
        acc += math.dist(fine[i - 1], fine[i])
        if acc >= seg:
            pts.append(fine[i])
            acc = 0.0
    if pts[-1] != fine[-1]:
        pts.append(fine[-1])
    return pts


def path_d(pts):
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts)


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def wrap(title, w, h, helmet_css, body):
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
body{{margin:0}}
a{{color:{BLUE}}}a:hover{{color:{INDIGO}}}
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
