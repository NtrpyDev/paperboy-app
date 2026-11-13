"""Scratch: plate variants side by side. Not a deliverable."""
import pathlib, sys, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib import *  # noqa

OUT = pathlib.Path(__file__).parent / "ExpPlates.dc.html"
W, PH = 390, 250
NR = 10
WTS = tone_weights(NR, 0.9, 3.1, 1.0)
pts = chirp_points(350, 27)
CH = path_d(pts)

def defs(day=True):
    b, p = (BLUE, PINK) if day else (N_BLUE, N_PINK)
    s = "d" if day else "n"
    return tone_patterns(s + "b", b, BLUE_ANGLE, WTS) + tone_patterns(s + "p", p, PINK_ANGLE, WTS) + pattern("ntex", N_TEX, BLUE_ANGLE, 1.0)

def rings_about(cx, cy, r_far, r_near, prefix, n, clip):
    out = []
    for i in range(n):
        r = r_far - (r_far - r_near) * (i / n)
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="url(#{prefix}{i})"></circle>')
    return f'<g clip-path="url(#{clip})">' + "".join(out) + "</g>"

def plate(variant, day=True, uid="a"):
    s = "d" if day else "n"
    b, p = (BLUE, PINK) if day else (N_BLUE, N_PINK)
    blend = "multiply" if day else "screen"
    Bx, By, BR = 208, 102, 100
    Px, Py, PR = 336, 114, 90
    k = 0.80
    d = math.dist((Bx, By), (Px, Py))
    cl = (f'<clipPath id="{uid}cB"><circle cx="{Bx}" cy="{By}" r="{BR}"></circle></clipPath>'
          f'<clipPath id="{uid}cP"><circle cx="{Px}" cy="{Py}" r="{PR}"></circle></clipPath>'
          f'<clipPath id="{uid}kB"><circle cx="{Bx}" cy="{By}" r="{BR * k}"></circle></clipPath>'
          f'<clipPath id="{uid}kP"><circle cx="{Px}" cy="{Py}" r="{PR * k}"></circle></clipPath>')
    if variant == "conc":
        blue = "".join(f'<circle cx="{Bx}" cy="{By}" r="{f(BR - (BR - 6) * i / NR)}" fill="url(#{s}b{i})"></circle>' for i in range(NR))
        pink = "".join(f'<circle cx="{Px}" cy="{Py}" r="{f(PR - (PR - 6) * i / NR)}" fill="url(#{s}p{i})"></circle>' for i in range(NR))
    else:
        blue = rings_about(Px, Py, d + BR, PR * k, s + "b", NR, uid + "cB")
        pink = rings_about(Bx, By, d + PR, BR * k, s + "p", NR, uid + "cP")
    lensB = f'<circle cx="{Bx}" cy="{By}" r="{BR * k}" fill="{b}" clip-path="url(#{uid}kP)"></circle>'
    lensP = f'<circle cx="{Px}" cy="{Py}" r="{PR * k}" fill="{p}" clip-path="url(#{uid}kB)"></circle>'
    ground = "" if day else f'<rect width="{W}" height="{PH}" fill="{N_GROUND}"></rect>'
    if day:
        line = (f'<path d="{CH}" fill="none" stroke="{STOCK}" stroke-width="6.5" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<path d="{CH}" fill="none" stroke="{PINK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<circle cx="{f(pts[-1][0])}" cy="0" r="4.25" fill="{PINK}"></circle>')
    else:
        line = (f'<path d="{CH}" fill="none" stroke="{N_PINK}" stroke-width="7" stroke-opacity="0.22" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<path d="{CH}" fill="none" stroke="{N_LIVE}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<circle cx="{f(pts[-1][0])}" cy="0" r="8" fill="{N_PINK}" fill-opacity="0.25"></circle><circle cx="{f(pts[-1][0])}" cy="0" r="3.5" fill="{N_LIVE}"></circle>')
    return f'''<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" style="display: block"><defs>{cl}</defs>
{ground}
<g>{blue}{lensB}</g>
<g style="mix-blend-mode: {blend}">{pink}{lensP}</g>
<g transform="translate(20 212)">{line}</g>
</svg>'''

cells = []
for v in ("conc", "dir"):
    for day in (True, False):
        cells.append(f'<div style="background-color: {STOCK if day else N_GROUND}">{plate(v, day, v + ("d" if day else "n"))}</div>')
body = f'''<div style="width: 780px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); background-color: {STOCK}">
<svg width="0" height="0" style="position: absolute"><defs>{defs(True)}{defs(False)}</defs></svg>
{"".join(cells)}</div>'''
OUT.write_text(wrap("exp", 780, 500, "", body))
