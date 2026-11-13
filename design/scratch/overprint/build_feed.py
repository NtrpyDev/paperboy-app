"""Builds design/canvas/project/Cand-y-Feed.dc.html (390 by 844, day theme)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib import *  # noqa

OUT = pathlib.Path(__file__).resolve().parents[2] / "canvas/project/Cand-y-Feed.dc.html"

W, H = 390, 844
PLATE_H = 260

# ---- plate geometry ----
import math
Bx, By, BR = 208, 112, 100   # blue body (36 solar masses)
Px, Py, PR = 336, 124, 90    # pink body (29 solar masses); radii follow the square root of the mass ratio
CORE = 0.87                  # the solid overprint lens is the overlap of the two cores
DIST = math.dist((Bx, By), (Px, Py))
NRING = 10
WEIGHTS = tone_weights(NRING, 0.9, 3.1, 1.0)
LINE_X0, LINE_Y0, LINE_W, LINE_AMP = 20, 221, 350, 28

def rings_about(cx, cy, r_far, r_near, prefix, clip):
    out = []
    for i in range(NRING):
        r = r_far - (r_far - r_near) * (i / NRING)
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="url(#{prefix}{i})"></circle>')
    return f'<g clip-path="url(#{clip})">' + "".join(out) + "</g>"

CLIPS = (f'<clipPath id="cB"><circle cx="{Bx}" cy="{By}" r="{BR}"></circle></clipPath>'
         f'<clipPath id="cP"><circle cx="{Px}" cy="{Py}" r="{PR}"></circle></clipPath>'
         f'<clipPath id="kB"><circle cx="{Bx}" cy="{By}" r="{f(BR * CORE)}"></circle></clipPath>'
         f'<clipPath id="kP"><circle cx="{Px}" cy="{Py}" r="{f(PR * CORE)}"></circle></clipPath>')
BLUE_PLATE = rings_about(Px, Py, DIST + BR, PR * CORE, "b", "cB") + f'<circle cx="{Bx}" cy="{By}" r="{f(BR * CORE)}" fill="{BLUE}" clip-path="url(#kP)"></circle>'
PINK_PLATE = rings_about(Bx, By, DIST + PR, BR * CORE, "p", "cP") + f'<circle cx="{Px}" cy="{Py}" r="{f(PR * CORE)}" fill="{PINK}" clip-path="url(#kB)"></circle>' 
pts = chirp_points(LINE_W, LINE_AMP)
CHIRP = path_d(pts)
END = pts[-1]

mono = f"font-family: {MONO}; font-stretch: 87.5%; font-weight: 500; font-size: 9.5px; line-height: 12px; letter-spacing: 0.07em; text-transform: uppercase"

defs = (f'<svg width="0" height="0" aria-hidden="true" style="position: absolute"><defs>'
        + tone_patterns("b", BLUE, BLUE_ANGLE, WEIGHTS)
        + tone_patterns("p", PINK, PINK_ANGLE, WEIGHTS)
        + pattern("sepb", BLUE, BLUE_ANGLE, 1.0)
        + '</defs></svg>')

plate = f'''<svg viewBox="0 0 {W} {PLATE_H}" width="{W}" height="{PLATE_H}" role="img" aria-label="Illustration: two black holes drawn as overlapping blue and pink line screens, with the chirp signal they produced running underneath" style="display: block; position: absolute; left: 0; top: 0; isolation: isolate">
<defs>{CLIPS}<path id="chirp" d="{CHIRP}" pathLength="1"></path></defs>
<g style="animation: regB 480ms cubic-bezier(0.16, 1, 0.3, 1) both">{BLUE_PLATE}</g>
<g style="mix-blend-mode: multiply; animation: regP 480ms cubic-bezier(0.16, 1, 0.3, 1) both">{PINK_PLATE}</g>
<g transform="translate({LINE_X0} {LINE_Y0})">
<use href="#chirp" fill="none" stroke="{STOCK}" stroke-width="6.5" stroke-linejoin="round" stroke-linecap="round" style="stroke-dasharray: 1; stroke-dashoffset: 0; animation: sweep 1900ms linear 300ms backwards"></use>
<use href="#chirp" fill="none" stroke="{PINK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" style="stroke-dasharray: 1; stroke-dashoffset: 0; animation: sweep 1900ms linear 300ms backwards"></use>
<g style="offset-path: path('{CHIRP}'); offset-rotate: 0deg; offset-distance: 100%; animation: ride 1900ms linear 300ms backwards">
<circle cx="0" cy="0" r="7" fill="{STOCK}"></circle>
<circle cx="0" cy="0" r="4.25" fill="{PINK}" style="animation: pulse 2400ms ease-in-out 2600ms infinite alternate"></circle>
</g>
</g>
<g fill="none" stroke="{INDIGO}" stroke-width="0.75">
<path d="M62 133H{Bx - BR + 4}"></path>
<path d="M{W - 28} 24V{Py - PR + 4}"></path>
</g>
</svg>'''

def tag(text, kind):
    base = f"display: inline-flex; align-items: center; height: 20px; box-sizing: border-box; padding: 0 6px; {mono}; font-weight: 600"
    if kind == "field":
        return f'<span style="{base}; border: 1.25px solid {INDIGO}; color: {INDIGO}">{text}</span>'
    if kind == "solid":
        return f'<span style="{base}; background-color: {INDIGO}; color: {STOCK}">{text}</span>'
    return ""

def kicker(field, journal):
    return f'''<div style="display: flex; align-items: center; gap: 6px; padding: 10px 20px 0">
{tag(field, "field")}{tag("Peer-reviewed", "solid")}
<span style="{mono}; color: {MUTED}; margin-left: 4px">{journal}</span>
</div>'''

h2 = f"margin: 0; font-family: {VOICE}; font-weight: 800; font-size: 37px; line-height: 0.95; letter-spacing: -0.035em; color: {INDIGO}; text-wrap: balance"
press = "animation: press 160ms cubic-bezier(0.2, 0, 0, 1) {d}ms both"

body = f'''<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INDIGO}; font-family: {TEXT}">
{defs}
<header style="display: flex; align-items: center; justify-content: space-between; padding: 4px 8px 0 20px; height: 44px">
<h1 style="margin: 0; position: relative; isolation: isolate; font-family: {VOICE}; font-weight: 800; font-size: 31px; line-height: 1; letter-spacing: -0.045em">
<span style="color: {BLUE}; display: block; animation: regB 480ms cubic-bezier(0.16, 1, 0.3, 1) both">Paperboy</span>
<span aria-hidden="true" style="color: {PINK}; position: absolute; left: 0; top: 0; mix-blend-mode: multiply; animation: regP 480ms cubic-bezier(0.16, 1, 0.3, 1) both">Paperboy</span>
</h1>
<div style="{mono}; color: {MUTED}; margin: 9px auto 0 14px">Newly released<br>science and math</div>
<button type="button" aria-label="Switch to the night theme" style="width: 44px; height: 44px; padding: 0; border: 0; background: none; color: {INDIGO}; display: flex; align-items: center; justify-content: center; cursor: pointer">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="8.25"></circle><path d="M12 3.75a8.25 8.25 0 0 1 0 16.5z" fill="currentColor"></path></svg>
</button>
</header>
<div aria-hidden="true" style="position: relative; isolation: isolate; height: 4px; margin-top: 4px">
<div style="position: absolute; left: 0; top: 0; height: 4px; width: 62%; background-color: {BLUE}"></div>
<div style="position: absolute; right: 0; top: 0; height: 4px; width: 60%; background-color: {PINK}; mix-blend-mode: multiply"></div>
</div>

<article>
<div style="{press.format(d=0)}">{kicker("Physics", "Phys. Rev. Lett. 116")}</div>
<h2 style="{h2}; padding: 9px 20px 0; {press.format(d=40)}">Two black holes merged. <span style="font-weight: 300; color: {BLUE}; letter-spacing: -0.03em">Earth felt space stretch.</span></h2>

<div style="position: relative; height: {PLATE_H}px; margin-top: 9px">
{plate}
<div style="position: absolute; left: 20px; top: 16px; display: flex; flex-direction: column; gap: 5px">
<div style="font-family: {VOICE}; font-weight: 300; font-size: 58px; line-height: 0.82; letter-spacing: -0.05em">0.2<span style="font-size: 20px; font-weight: 600; letter-spacing: 0; margin-left: 5px">s</span></div>
<div style="{mono}; color: {MUTED}">Length of<br>the signal</div>
</div>
<div style="position: absolute; left: 20px; top: 117px; {mono}"><div style="font-family: {VOICE}; font-stretch: 100%; font-weight: 800; font-size: 20px; line-height: 20px; letter-spacing: -0.02em">36</div>solar<br>masses</div>
<div style="position: absolute; right: 20px; top: 2px; {mono}; text-align: right"><span style="font-family: {VOICE}; font-stretch: 100%; font-weight: 800; font-size: 20px; line-height: 20px; letter-spacing: -0.02em; vertical-align: -2px; margin-right: 5px">29</span>solar masses</div>
<div style="position: absolute; left: 20px; top: 245px; {mono}; color: {MUTED}">Illustration, not to scale</div>
</div>

<p style="margin: 0; padding: 8px 20px 0; font-size: 16px; line-height: 23px; text-wrap: pretty; {press.format(d=80)}">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>

<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 20px 0; {press.format(d=120)}">
<div style="display: flex; gap: 6px">
<a href="#explainer" style="flex-grow: 1; height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {BLUE}; color: {STOCK}; text-decoration: none; font-family: {VOICE}; font-weight: 700; font-size: 16px; letter-spacing: -0.01em"><span>See it explained</span><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"></path></svg></a>
<a href="#paper" aria-label="Open the original paper" style="width: 48px; height: 48px; box-sizing: border-box; border: 1.25px solid {INDIGO}; color: {INDIGO}; display: flex; align-items: center; justify-content: center"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 7h9v9M17 7L6.5 17.5"></path></svg></a>
</div>
<div style="display: flex">
<button type="button" style="flex: 1 1 0; height: 44px; box-sizing: border-box; border: 1.25px solid {INDIGO}; border-right-width: 0; background: none; color: {INDIGO}; display: flex; align-items: center; justify-content: center; gap: 8px; font-family: {TEXT}; font-weight: 500; font-size: 16px; cursor: pointer"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 2v12M2 8h12"></path></svg>More like this</button>
<button type="button" style="flex: 1 1 0; height: 44px; box-sizing: border-box; border: 1.25px solid {INDIGO}; background: none; color: {INDIGO}; display: flex; align-items: center; justify-content: center; gap: 8px; font-family: {TEXT}; font-weight: 500; font-size: 16px; cursor: pointer"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 8h12"></path></svg>Less like this</button>
</div>
</div>
</article>

<svg aria-hidden="true" width="{W}" height="8" viewBox="0 0 {W} 8" style="display: block; margin-top: 11px"><rect width="{W}" height="8" fill="url(#sepb)"></rect></svg>

<article>
{kicker("Biology", "Nature 596")}
<h2 style="{h2}; text-wrap: wrap; padding: 9px 20px 0">A neural network learned to fold proteins.</h2>
</article>
</div>'''

css = '''@keyframes press{from{opacity:0;transform:translateY(6px)}}
@keyframes regB{from{opacity:0;transform:translate(-5px,3px)}35%{opacity:1}}
@keyframes regP{from{opacity:0;transform:translate(5px,-3px)}35%{opacity:1}}
@keyframes sweep{from{stroke-dashoffset:1}}
@keyframes ride{from{offset-distance:0%}}
@keyframes pulse{to{opacity:.55}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}'''

if "--hold" in sys.argv:
    OUT = pathlib.Path(__file__).parent / "Hold-Feed.dc.html"
    ms = sys.argv[sys.argv.index("--hold") + 1]
    css += f"\n*{{animation-play-state:paused!important;animation-delay:-{ms}ms!important}}"
OUT.write_text(wrap("Paperboy feed, Two-Ink Overprint, day", W, H, css, body))
print("wrote", OUT, OUT.stat().st_size)
