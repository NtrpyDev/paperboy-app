"""Builds design/canvas/project/Cand-z-Feed.dc.html (390 x 844, day theme)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib import DAY, VOICE, SERIF, MONO, Chirp, f, grid, ruler, perforation, page

D = DAY
W, H = 390, 844
M = 20            # side margin, also the plot origin
CELL = 14         # 0.01 s on the time ruler
SWEEP = 2.2       # seconds, linear
START = 0.3
BAND = 72

# ---------- plate 1: the chirp, written by the pen ----------
AX = 24                    # y of the ruler axis inside the plate svg
ROWS = 14
PH = ROWS * CELL           # plot height 196
YC = AX + PH / 2           # zero line
AMP = 6 * CELL             # 84 px, the crest touches the 6th grid line
PEN_X = M + CELL * 24      # parked pen
ch = Chirp(M, YC, 1400, AMP, PEN_X, env=0.33)
PLATE_H = AX + PH

win_read = (M, AX, M + CELL * 12, AX + CELL * 4)                 # top left legend window
win_note = (M, AX + PH - CELL * 3, M + CELL * 15, AX + PH)        # bottom left note window

g1 = grid(M, W, AX, AX + PH, CELL, D["grid"], holes=[win_read, win_note], origin_x=M, origin_y=YC,
          w_minor=0.5, w_major=0.9)
r1 = ruler(M, W, AX, CELL, D["ink"], major_every=5, up=True, minor=4, major=8, w=1)

peak = ch.peak
ex = ch.extrema()
pin = max((e for e in ex if e[2] == "trough" and 232 <= e[0] <= 262), key=lambda e: e[1])
t_peak = START + SWEEP * ch.frac_at(peak)
t_pin = START + SWEEP * ch.frac_at(pin)
note_y = win_note[1] + 14


def axis_labels(items):
    return "".join(
        f'<text x="{x}" y="11" text-anchor="{a}" font-family="{VOICE}" font-size="13" font-weight="600" fill="{D["ink"]}" letter-spacing="0.2">{t}</text>'
        for x, t, a in items)


plate1 = f'''<div style="position: relative; height: {PLATE_H}px">
<svg width="{W}" height="{PLATE_H}" viewBox="0 0 {W} {PLATE_H}" role="img" aria-label="Illustration of the signal: a wave that rises in pitch and strength over 0.2 seconds, then stops. A pen writes it from left to right." style="position: absolute; left: 0; top: 0; display: block">
<defs>
<clipPath id="f1plot"><path clip-rule="evenodd" d="M0 {AX} H{W} V{AX + PH} H0 Z M{win_read[0] - 1} {win_read[1]} H{win_read[2]} V{win_read[3]} H{win_read[0] - 1} Z M{win_note[0] - 1} {win_note[1]} H{win_note[2]} V{win_note[3]} H{win_note[0] - 1} Z"></path></clipPath>
<clipPath id="f1rail"><rect x="0" y="{AX - 9}" width="{W}" height="9"></rect></clipPath>
</defs>
{g1}
<line x1="{M}" y1="{YC}" x2="{W}" y2="{YC}" stroke="{D["muted"]}" stroke-width="0.75"></line>
{r1}
{axis_labels([(M, "0", "start"), (M + 140, "0.1", "middle"), (M + 280, "0.2 s", "middle")])}
<path class="pb-trace" d="{ch.d}" pathLength="1" fill="none" stroke="{D["live"]}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"></path>
<g class="pb-pin" style="animation-delay: {t_peak:.2f}s">
<line x1="{M + 82}" y1="{f(peak[1])}" x2="{f(peak[0] - 5.5)}" y2="{f(peak[1])}" stroke="{D["ink"]}" stroke-width="0.75"></line>
<circle cx="{f(peak[0])}" cy="{f(peak[1])}" r="3.25" fill="none" stroke="{D["ink"]}" stroke-width="1"></circle>
</g>
<g class="pb-pin" style="animation-delay: {t_pin:.2f}s">
<path d="M{M + 196} {note_y} H{f(pin[0])} V{f(pin[1] + 5.5)}" fill="none" stroke="{D["ink"]}" stroke-width="0.75"></path>
<circle cx="{f(pin[0])}" cy="{f(pin[1])}" r="3.25" fill="none" stroke="{D["ink"]}" stroke-width="1"></circle>
</g>
<g clip-path="url(#f1plot)"><g class="pb-pen"><line x1="0" y1="-400" x2="0" y2="400" stroke="{D["ink"]}" stroke-width="1"></line></g></g>
<g clip-path="url(#f1rail)"><g class="pb-pen"><line x1="0" y1="-400" x2="0" y2="400" stroke="{D["ink"]}" stroke-width="9"></line></g></g>
<g class="pb-pen"><circle r="6" fill="{D["stock"]}"></circle><circle class="pb-nib" r="4" fill="{D["live"]}"></circle></g>
</svg>
<div style="position: absolute; left: {M}px; top: {AX + 6}px; display: flex; flex-direction: column; gap: 4px">
<div style="font-family: {MONO}; font-size: 10px; line-height: 16px; letter-spacing: 0.06em; text-transform: uppercase; color: {D["muted"]}">Peak strain</div>
<div style="font-family: {VOICE}; font-size: 36px; font-weight: 700; line-height: 28px; letter-spacing: 0.005em; font-variant-numeric: tabular-nums; color: {D["ink"]}; white-space: nowrap">1.0 <span style="font-weight: 500">&times;</span> 10<sup style="font-size: 18px; line-height: 0; vertical-align: 14px; margin-left: 1px; letter-spacing: 0.02em">&minus;21</sup></div>
</div>
<div style="position: absolute; left: {M}px; top: {win_note[1] + 4}px; width: 200px; font-family: {SERIF}; font-style: italic; font-size: 14px; line-height: 18px; color: {D["ink"]}; white-space: nowrap">Pitch climbs from 35 to 250&nbsp;Hz<br>in about a fifth of a second.</div>
</div>'''

# ---------- plate 2 (peek): AlphaFold error on an angstrom ruler ----------
A = 105                    # px per angstrom, 0.2 A = 21 px
AX2 = 24
PH2 = 63
x_af = M + 0.96 * A
y_af = AX2 + 18
win_af = (M + 126, AX2, W, AX2 + 42)
g2 = grid(M, W, AX2, AX2 + PH2, 21, D["grid"], holes=[win_af], origin_x=M, origin_y=AX2, w_minor=0.5, w_major=0.9)
r2 = ruler(M, W, AX2, 21, D["ink"], major_every=5, up=True, minor=4, major=8, w=1)
plate2 = f'''<div style="position: relative; height: {AX2 + PH2}px">
<svg width="{W}" height="{AX2 + PH2}" viewBox="0 0 {W} {AX2 + PH2}" role="img" aria-label="Data from the paper: AlphaFold's median backbone error, 0.96 angstroms, drawn on an angstrom ruler." style="position: absolute; left: 0; top: 0; display: block; overflow: visible">
{g2}{r2}{axis_labels([(M, "0", "start"), (M + A, "1", "middle"), (M + 2 * A, "2", "middle"), (M + 3 * A, "3 Å", "middle")])}
<path d="M{M} {y_af} H{f(x_af)} M{M} {y_af - 6} V{y_af + 6} M{f(x_af)} {y_af - 6} V{y_af + 6}" fill="none" stroke="{D["ink"]}" stroke-width="2"></path>
</svg>
<div style="position: absolute; left: {M + 130}px; top: {AX2 + 6}px; display: flex; align-items: baseline; gap: 7px; white-space: nowrap">
<div style="font-family: {VOICE}; font-size: 26px; font-weight: 700; line-height: 26px; font-variant-numeric: tabular-nums; color: {D["ink"]}">0.96 <span style="font-size: 17px; font-weight: 600">&Aring;</span></div>
<div style="font-family: {MONO}; font-size: 10px; letter-spacing: 0.03em; text-transform: uppercase; color: {D["muted"]}">AlphaFold, median error</div>
</div>
</div>'''


def tags(field, journal, href):
    return f'''<div style="height: 34px; padding: 0 {M}px; display: flex; align-items: center; gap: 6px; font-family: {MONO}; font-size: 10px; line-height: 1; letter-spacing: 0.06em; text-transform: uppercase">
<span style="box-sizing: border-box; height: 20px; display: flex; align-items: center; padding: 0 6px; border: 1px solid {D["ink"]}; color: {D["ink"]}; font-weight: 700">{field}</span>
<span style="box-sizing: border-box; height: 20px; display: flex; align-items: center; padding: 0 7px; background-color: {D["ink"]}; color: {D["stock"]}; font-weight: 700">Peer-reviewed</span>
<a href="{href}" style="margin-left: auto; height: 44px; display: flex; align-items: center; gap: 5px; color: {D["ink"]}; text-decoration: none; text-transform: none; letter-spacing: 0; font-family: {SERIF}; font-style: italic; font-size: 13.5px"><span style="border-bottom: 1px solid {D["ink"]}; padding-bottom: 1px">{journal}</span><svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 8 L8 2 M3.5 2 H8 V6.5"></path></svg></a>
</div>'''


# wordmark tail: the word hands off to a line that ends in the pen
tail = Chirp(0, 15, 150, 7, 46, T=0.2, f0=13, f1=58, tau_d=0.012, lead=0.05)
wordmark = f'''<div style="display: flex; align-items: flex-end; gap: 5px">
<div style="font-family: {VOICE}; font-size: 34px; font-weight: 800; line-height: 30px; letter-spacing: 0.005em; color: {D["stock"]}">Paperboy</div>
<svg width="54" height="30" viewBox="0 0 54 30" aria-hidden="true" style="display: block; margin-bottom: -5px"><path d="{tail.d}" fill="none" stroke="{D["stock"]}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"></path><circle cx="46" cy="15" r="3.5" fill="#62F5A4"></circle></svg>
</div>'''

pulse_up = '<svg width="26" height="16" viewBox="0 0 26 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="miter" aria-hidden="true"><path d="M1 13 H8 L13 2 L18 13 H25"></path></svg>'
pulse_dn = '<svg width="26" height="16" viewBox="0 0 26 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="miter" aria-hidden="true"><path d="M1 3 H8 L13 14 L18 3 H25"></path></svg>'
rate_style = (f"flex: 1 1 0; min-width: 0; height: 44px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; gap: 9px; "
              f"padding: 0; background-color: transparent; border: 1px solid {D['ink']}; border-radius: 0; color: {D['ink']}; "
              f"font-family: {VOICE}; font-size: 17px; font-weight: 600; letter-spacing: 0.015em; cursor: pointer")

body = f'''<div style="position: relative; width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; background-color: {D["stock"]}; color: {D["ink"]}; font-family: {SERIF}">

<header style="position: absolute; left: 0; top: 0; width: {W}px; height: {BAND}px; box-sizing: border-box; padding: 24px 8px 0 {M}px; background-color: {D["ink"]}; display: flex; align-items: center; justify-content: space-between; z-index: 2">
{wordmark}
<button type="button" aria-label="Switch to night theme" style="width: 44px; height: 44px; padding: 0; background-color: transparent; border: 0; color: {D["stock"]}; display: flex; align-items: center; justify-content: center; cursor: pointer"><svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="7.25"></circle><path d="M11 3.75 A7.25 7.25 0 0 1 11 18.25 Z" fill="currentColor"></path></svg></button>
</header>

<main class="pb-roll" style="position: absolute; left: 0; top: {BAND}px; width: {W}px; display: flex; flex-direction: column">

<article style="display: flex; flex-direction: column">
{tags("Physics", "Phys. Rev. Lett. 116", "#paper-1")}
{plate1}
<div style="padding: 5px {M}px 0; font-family: {MONO}; font-size: 10px; line-height: 14px; letter-spacing: 0.06em; text-transform: uppercase; color: {D["muted"]}">Illustration of the signal, not data</div>
<h2 style="margin: 10px {M}px 0; font-family: {VOICE}; font-size: 52px; font-weight: 700; line-height: 49px; letter-spacing: -0.005em; color: {D["ink"]}"><span style="display: block; white-space: nowrap">Two black holes</span><span style="display: block; white-space: nowrap">merged. <span style="font-family: {SERIF}; font-style: italic; font-weight: 440; font-size: 40px; line-height: 0; letter-spacing: -0.02em">Earth felt</span></span><span style="display: block; white-space: nowrap; margin-top: -5px; font-family: {SERIF}; font-style: italic; font-weight: 440; font-size: 40px; line-height: 46px; letter-spacing: -0.02em">space stretch.</span></h2>
<p style="margin: 11px {M}px 0; font-family: {SERIF}; font-size: 16px; line-height: 24px; color: {D["ink"]}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>
<div style="margin: 12px {M}px 0; display: flex; flex-direction: column; gap: 8px">
<a href="#explainer" style="height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; background-color: {D["ink"]}; color: {D["stock"]}; text-decoration: none; font-family: {VOICE}; font-size: 20px; font-weight: 700; letter-spacing: 0.015em"><span>Open the explainer</span><svg width="26" height="14" viewBox="0 0 26 14" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M0 7 H24 M18 1 L24 7 L18 13"></path></svg></a>
<div style="display: flex; gap: 8px">
<button type="button" style="{rate_style}">{pulse_up}<span>More like this</span></button>
<button type="button" style="{rate_style}">{pulse_dn}<span>Less like this</span></button>
</div>
</div>
</article>

<div style="margin-top: 12px">{perforation(W, D["ink"])}</div>

<article style="display: flex; flex-direction: column">
{tags("Biology", "Nature 596", "#paper-2")}
{plate2}
</article>

</main>
</div>'''

css = f'''body{{margin:0}}
a{{color:{D["ink"]}}}a:hover{{color:{D["live"]}}}
@keyframes pb-sweep{{from{{stroke-dashoffset:1}}}}
@keyframes pb-ride{{from{{offset-distance:0%}}}}
@keyframes pb-step{{from{{transform:translateY(28px)}}}}
@keyframes pb-press{{from{{opacity:0}}}}
@keyframes pb-pulse{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
.pb-roll{{animation:pb-step .2s steps(4,end) both}}
.pb-trace{{stroke-dasharray:1 2;stroke-dashoffset:0;animation:pb-sweep {SWEEP}s linear {START}s both}}
.pb-pen{{offset-path:path("{ch.d}");offset-rotate:0deg;offset-distance:100%;animation:pb-ride {SWEEP}s linear {START}s both}}
.pb-pin{{animation:pb-press .2s cubic-bezier(.2,0,0,1) both}}
.pb-nib{{animation:pb-pulse 2.4s ease-in-out {START + SWEEP + 0.1:.1f}s infinite}}
@media (prefers-reduced-motion:reduce){{.pb-roll,.pb-trace,.pb-pen,.pb-pin,.pb-nib{{animation:none}}}}'''

out = pathlib.Path(__file__).resolve().parents[2] / "canvas/project/Cand-z-Feed.dc.html"
out.write_text(page("Feed, Strip Chart direction, day", W, H, css, body))
print("wrote", out, "trace length px", round(ch.length), "speed px/s", round(ch.length / SWEEP), "peak", peak, "pin", pin)
