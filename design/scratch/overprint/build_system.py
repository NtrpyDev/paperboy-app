"""Builds design/canvas/project/Cand-y-System.dc.html (1200 by 1700 style tile)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib import *  # noqa

OUT = pathlib.Path(__file__).resolve().parents[2] / "canvas/project/Cand-y-System.dc.html"
W, H = 1200, 1700
M = 56                      # outer margin
RX = 660                    # right block starts here
SPLIT = 930                 # day / night boundary
REG = "480ms cubic-bezier(0.16, 1, 0.3, 1) both"

NR = 10
WTS = tone_weights(NR, 0.9, 3.1, 1.0)

mono = f"font-family: {MONO}; font-stretch: 87.5%; font-weight: 500; font-size: 9.5px; line-height: 13px; letter-spacing: 0.07em; text-transform: uppercase"


def cap(text, color=MUTED, extra=""):
    return f'<div style="{mono}; color: {color}; {extra}">{text}</div>'


def box(x, y, w, inner, extra=""):
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; {extra}">{inner}</div>'


# ------------------------------------------------------------------ shared defs
defs = ('<svg width="0" height="0" aria-hidden="true" style="position: absolute"><defs>'
        + tone_patterns("b", BLUE, BLUE_ANGLE, WTS) + tone_patterns("p", PINK, PINK_ANGLE, WTS)
        + tone_patterns("nb", N_BLUE, BLUE_ANGLE, WTS) + tone_patterns("np", N_PINK, PINK_ANGLE, WTS)
        + pattern("ntex", N_TEX, BLUE_ANGLE, 1.0)
        + pattern("tagb", BLUE, BLUE_ANGLE, 0.9, 3.5)
        + pattern("stockb", STOCK, BLUE_ANGLE, 1.3)
        + '</defs></svg>')

# ------------------------------------------------------------------ header
def wordmark(size, anim=True):
    a = f"animation: regB {REG}" if anim else ""
    b = f"animation: regP {REG}" if anim else ""
    return (f'<div style="position: relative; isolation: isolate; font-family: {VOICE}; font-weight: 800; font-size: {size}px; line-height: 0.82; letter-spacing: -0.055em; white-space: nowrap">'
            f'<span style="display: block; color: {BLUE}; {a}">Paperboy</span>'
            f'<span aria-hidden="true" style="position: absolute; left: 0; top: 0; color: {PINK}; mix-blend-mode: multiply; {b}">Paperboy</span></div>')


def plate_word(color, label, hexv, both=False):
    word = (f'<div style="position: relative; isolation: isolate; font-family: {VOICE}; font-weight: 800; font-size: 27px; line-height: 0.9; letter-spacing: -0.05em">'
            + (f'<span style="display: block; color: {BLUE}">Paperboy</span><span aria-hidden="true" style="position: absolute; left: 0; top: 0; color: {PINK}; mix-blend-mode: multiply">Paperboy</span>' if both
               else f'<span style="display: block; color: {color}">Paperboy</span>') + '</div>')
    return f'<div style="display: flex; flex-direction: column; gap: 7px">{word}{cap(label + "<br>" + hexv, INDIGO if both else MUTED)}</div>'


RULE_Y = 212
header = (
    box(M, 30, W - 2 * M, f'<div style="display: flex; justify-content: space-between">{cap("Paperboy / Two-Ink Overprint / style tile", INDIGO)}{cap("Two inks and no black by day. Two lights by night.")}</div>')
    + box(M - 6, 54, 660, wordmark(150))
    + box(RX + 20, 116, 470, '<div style="display: flex; gap: 20px; align-items: flex-end">'
          + plate_word(BLUE, "Blue plate", BLUE) + f'<div style="{mono}; font-size: 15px; padding-bottom: 36px">+</div>'
          + plate_word(PINK, "Pink plate", PINK) + f'<div style="{mono}; font-size: 15px; padding-bottom: 36px">=</div>'
          + plate_word(INDIGO, "In register", INDIGO, both=True) + '</div>')
    + f'<div aria-hidden="true" style="position: absolute; isolation: isolate; left: 0; top: {RULE_Y}px; width: {W}px; height: 6px"><div style="position: absolute; left: 0; top: 0; height: 6px; width: 62%; background-color: {BLUE}"></div><div style="position: absolute; right: 0; top: 0; height: 6px; width: 60%; background-color: {PINK}; mix-blend-mode: multiply"></div></div>'
)
HERO_Y = RULE_Y + 6

# ------------------------------------------------------------------ type specimen
TW = RX - 40 - M   # 564
num = f"font-family: {VOICE}; font-variant-numeric: tabular-nums"
spec = f'''<div style="display: flex; flex-direction: column; gap: 26px">
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Display and second voice / Bricolage Grotesque 800 and 300 / 62 on 58")}
<div style="font-family: {VOICE}; font-weight: 800; font-size: 62px; line-height: 0.94; letter-spacing: -0.04em; text-wrap: balance">Two black holes merged. <span style="font-weight: 300; color: {BLUE}; letter-spacing: -0.035em">Earth felt space stretch.</span></div>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Headline / Bricolage Grotesque 800 / 37 on 35")}
<div style="font-family: {VOICE}; font-weight: 800; font-size: 37px; line-height: 0.95; letter-spacing: -0.035em; text-wrap: balance">A neural network learned to fold proteins.</div>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Body / Schibsted Grotesk 400 / 16 on 23")}
<div style="font-family: {TEXT}; font-size: 16px; line-height: 23px; text-wrap: pretty; max-width: 520px">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</div>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Note / Schibsted Grotesk italic / 14 on 21")}
<div style="font-family: {TEXT}; font-style: italic; font-size: 14px; line-height: 21px; text-wrap: pretty">Explainers are machine written and can be wrong. Every card links to the original paper.</div>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Numerals / Bricolage Grotesque 300 and 800 / 58, unit 20")}
<div style="display: flex; gap: 48px; align-items: flex-start">
<div style="display: flex; flex-direction: column; gap: 10px">
<div style="{num}; font-weight: 300; font-size: 58px; line-height: 0.9; letter-spacing: -0.05em; white-space: nowrap">1.0<span style="font-size: 34px; letter-spacing: -0.02em; margin: 0 6px">&times;</span>10<sup style="font-size: 20px; font-weight: 600; letter-spacing: 0; vertical-align: 27px; line-height: 0; margin-left: 3px">&minus;21</sup></div>
{cap("Peak strain")}
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
<div style="{num}; font-weight: 800; font-size: 58px; line-height: 0.9; letter-spacing: -0.045em; white-space: nowrap">410<span style="font-size: 20px; font-weight: 600; letter-spacing: 0; margin-left: 6px">Mpc</span></div>
{cap("Distance, megaparsecs")}
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
<div style="{num}; font-weight: 300; font-size: 58px; line-height: 0.9; letter-spacing: -0.05em; white-space: nowrap">0.2<span style="font-size: 20px; font-weight: 600; letter-spacing: 0; margin-left: 5px">s</span></div>
{cap("Length of the signal", MUTED, "white-space: nowrap")}
</div>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
{cap("Label and slug / Martian Mono 500, width 87.5 / caps")}
<div style="{mono}; font-size: 11px; line-height: 16px; color: {INDIGO}">Illustration, not to scale &nbsp;/&nbsp; Data, from the paper</div>
</div>
</div>'''
type_block = box(M, HERO_Y + 30, TW, spec)

# ------------------------------------------------------------------ hero plate, day and night in one
HW, HH = W - RX, 476
SX = SPLIT - RX               # 270
Bx, By, BR = 242, 154, 106
Px, Py, PR = 314, 254, 95
CORE = 0.87
DIST = math.dist((Bx, By), (Px, Py))
LX0, LY0, LW, LAMP = 30, 390, 480, 30
hp = chirp_points(LW, LAMP)
HCH = path_d(hp)


def rings_about(cx, cy, r_far, r_near, prefix, clip):
    out = []
    for i in range(NR):
        r = r_far - (r_far - r_near) * (i / NR)
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="url(#{prefix}{i})"></circle>')
    return f'<g clip-path="url(#{clip})">' + "".join(out) + "</g>"


def plates(bp, pp, blue, pink):
    b = rings_about(Px, Py, DIST + BR, PR * CORE, bp, "hcB") + f'<circle cx="{Bx}" cy="{By}" r="{f(BR * CORE)}" fill="{blue}" clip-path="url(#hkP)"></circle>'
    p = rings_about(Bx, By, DIST + PR, BR * CORE, pp, "hcP") + f'<circle cx="{Px}" cy="{Py}" r="{f(PR * CORE)}" fill="{pink}" clip-path="url(#hkB)"></circle>'
    return b, p


db, dp = plates("b", "p", BLUE, PINK)
nb, npk = plates("nb", "np", N_BLUE, N_PINK)
sweep = 'style="stroke-dasharray: 1; stroke-dashoffset: 0; animation: sweep 2000ms linear 300ms backwards"'
ride = f"offset-path: path('{HCH}'); offset-rotate: 0deg; offset-distance: 100%; animation: ride 2000ms linear 300ms backwards"
hero_svg = f'''<svg viewBox="0 0 {HW} {HH}" width="{HW}" height="{HH}" role="img" aria-label="Illustration: the same two overlapping line screens and the same chirp line, printed as ink on paper on the left and shown as light on a dark ground on the right. The overlap is darkest by day and brightest by night." style="display: block">
<defs>
<path id="hchirp" d="{HCH}" pathLength="1"></path>
<clipPath id="hday"><rect x="0" y="0" width="{SX}" height="{HH}"></rect></clipPath>
<clipPath id="hnight"><rect x="{SX}" y="0" width="{HW - SX}" height="{HH}"></rect></clipPath>
<clipPath id="hcB"><circle cx="{Bx}" cy="{By}" r="{BR}"></circle></clipPath>
<clipPath id="hcP"><circle cx="{Px}" cy="{Py}" r="{PR}"></circle></clipPath>
<clipPath id="hkB"><circle cx="{Bx}" cy="{By}" r="{f(BR * CORE)}"></circle></clipPath>
<clipPath id="hkP"><circle cx="{Px}" cy="{Py}" r="{f(PR * CORE)}"></circle></clipPath>
</defs>
<g clip-path="url(#hday)">
<g style="animation: regB {REG}">{db}</g>
<g style="mix-blend-mode: multiply; animation: regP {REG}">{dp}</g>
</g>
<g clip-path="url(#hnight)">
<rect x="{SX}" y="0" width="{HW - SX}" height="{HH}" fill="{N_GROUND}"></rect>
<g style="isolation: isolate"><g style="animation: regB {REG}">{nb}</g>
<g style="mix-blend-mode: screen; animation: regP {REG}">{npk}</g></g>
</g>
<g clip-path="url(#hday)"><g transform="translate({LX0} {LY0})">
<use href="#hchirp" fill="none" stroke="{PINK}" stroke-width="2.25" stroke-linejoin="round" stroke-linecap="round" {sweep}></use>
<g style="{ride}"><circle r="4.75" fill="{PINK}"></circle></g>
</g></g>
<g clip-path="url(#hnight)"><g transform="translate({LX0} {LY0})">
<use href="#hchirp" fill="none" stroke="{N_PINK}" stroke-opacity="0.24" stroke-width="8" stroke-linejoin="round" stroke-linecap="round" {sweep}></use>
<use href="#hchirp" fill="none" stroke="{N_LIVE}" stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round" {sweep}></use>
<g style="{ride}"><circle r="9.5" fill="{N_PINK}" fill-opacity="0.26"></circle><circle r="4" fill="{N_LIVE}" style="animation: pulse 2400ms ease-in-out 2600ms infinite alternate"></circle></g>
</g></g>
</svg>'''

NIGHT_BOTTOM = 1016
hero = (
    f'<div style="position: absolute; left: {SPLIT}px; top: {HERO_Y}px; width: {W - SPLIT}px; height: {NIGHT_BOTTOM - HERO_Y}px; background-color: {N_GROUND}"></div>'
    + box(RX, HERO_Y, HW, hero_svg)
    + box(RX + 20, HERO_Y + 18, 240, cap("Hero plate / illustration", INDIGO) + cap("Register 480 ms, Sweep 2 s"))
    + box(SPLIT + 20, HERO_Y + 18, 230, cap("The same plate at night", N_MUTED))
    + box(RX + 20, HERO_Y + 440, 230, f'<div style="font-family: {VOICE}; font-weight: 800; font-size: 20px; letter-spacing: -0.02em; line-height: 1">Day: inks multiply</div>' + cap("The overlap is the darkest value", MUTED, "margin-top: 6px"))
    + box(SPLIT + 20, HERO_Y + 440, 240, f'<div style="font-family: {VOICE}; font-weight: 700; font-size: 20px; letter-spacing: -0.02em; line-height: 1; color: {N_TEXT}">Night: lights screen</div>' + cap("The overlap is the brightest value", N_MUTED, "margin-top: 6px"))
)

# ------------------------------------------------------------------ palettes
def chip_label(name, hexv, note, color, mutedc):
    notes = "".join(f'<div style="{mono}; color: {mutedc}; white-space: nowrap">{n}</div>' for n in note.split("|") if n)
    return (f'<div style="{mono}; color: {color}; margin-top: 7px; white-space: nowrap">{name}</div>'
            f'<div style="{mono}; color: {mutedc}; white-space: nowrap">{hexv}</div>{notes}')


CW = 76   # chip width
CG = 9    # gap
day_x = RX + 20
day_pal = f'''<div style="display: flex; flex-direction: column; gap: 14px">
{cap("Day palette / inks on stock")}
<div style="position: relative; isolation: isolate; height: 48px">
<div style="position: absolute; left: 0; top: 0; width: {CW * 2}px; height: 48px; background-color: {BLUE}"></div>
<div style="position: absolute; left: {CW}px; top: 0; width: {CW * 2}px; height: 48px; background-color: {PINK}; mix-blend-mode: multiply"></div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: -14px">
<div>{chip_label("Blue ink", BLUE, "6.9:1|links", INDIGO, MUTED)}</div>
<div>{chip_label("Overprint", INDIGO, "13.8:1|all text", INDIGO, MUTED)}</div>
<div>{chip_label("Pink ink", PINK, "3.4:1|live line", INDIGO, MUTED)}</div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr))">
<div><div style="height: 36px; box-sizing: border-box; margin-right: {CG}px; border: 1px solid {MUTED}; background-color: {STOCK}"></div>{chip_label("Stock", STOCK, "the paper", INDIGO, MUTED)}</div>
<div><div style="height: 36px; margin-right: {CG}px; background-color: {MUTED}"></div>{chip_label("Muted text", MUTED, "7.7:1", INDIGO, MUTED)}</div>
<div><svg width="{CW - CG}" height="36" viewBox="0 0 {CW - CG} 36" aria-hidden="true" style="display: block"><rect width="{CW - CG}" height="12" fill="url(#b1)"></rect><rect y="12" width="{CW - CG}" height="12" fill="url(#b5)"></rect><rect y="24" width="{CW - CG}" height="12" fill="url(#b8)"></rect></svg>{chip_label("Tone", "line weight", "never gray", INDIGO, MUTED)}</div>
</div>
</div>'''


def nchip(color, name, hexv, note, outline=False):
    sw = f'<div style="height: 28px; margin-right: {CG}px; box-sizing: border-box; background-color: {color}; {"border: 1px solid " + N_STRUCT if outline else ""}"></div>'
    return f'<div>{sw}{chip_label(name, hexv, note, N_TEXT, N_MUTED)}</div>'


night_pal = f'''<div style="display: flex; flex-direction: column; gap: 14px">
{cap("Night palette / lights on ground", N_MUTED)}
<div style="position: relative; isolation: isolate; height: 48px">
<div style="position: absolute; left: 0; top: 0; width: {CW * 2}px; height: 48px; background-color: {N_BLUE}"></div>
<div style="position: absolute; left: {CW}px; top: 0; width: {CW * 2}px; height: 48px; background-color: {N_PINK}; mix-blend-mode: screen"></div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: -14px">
<div>{chip_label("Blue light", N_BLUE, "7.1:1", N_TEXT, N_MUTED)}</div>
<div>{chip_label("Screened", N_OVER, "brightest", N_TEXT, N_MUTED)}</div>
<div>{chip_label("Pink light", N_PINK, "7.8:1", N_TEXT, N_MUTED)}</div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); row-gap: 12px">
{nchip(N_TEXT, "Text", N_TEXT, "17.0:1")}{nchip(N_MUTED, "Muted text", N_MUTED, "8.1:1")}{nchip(N_LIVE, "Live line", N_LIVE, "18.4:1")}
{nchip(N_STRUCT, "Structure", N_STRUCT, "3.1:1")}{nchip(N_TEX, "Texture", N_TEX, "decorative")}{nchip(N_GROUND, "Ground", N_GROUND, "", True)}
</div>
</div>'''

PAL_Y = HERO_Y + HH + 22
palettes = box(day_x, PAL_Y, CW * 3, day_pal) + box(SPLIT + 20, PAL_Y, CW * 3, night_pal, "isolation: isolate")

# ------------------------------------------------------------------ components
COMP_Y = NIGHT_BOTTOM + 26
tagbase = f"display: inline-flex; align-items: center; height: 22px; box-sizing: border-box; padding: 0 7px; {mono}; font-weight: 600"
def tag_field(t): return f'<span style="{tagbase}; border: 1.25px solid {INDIGO}; color: {INDIGO}">{t}</span>'
tag_solid = f'<span style="{tagbase}; background-color: {INDIGO}; color: {STOCK}">Peer-reviewed</span>'
tag_pre = (f'<span style="{tagbase}; position: relative; border: 1.25px solid {INDIGO}; color: {INDIGO}">'
           f'<svg aria-hidden="true" width="100%" height="100%" style="position: absolute; left: 0; top: 0"><rect width="100%" height="100%" fill="url(#tagb)"></rect></svg>'
           f'<span style="position: relative; -webkit-text-stroke: 3.5px {STOCK}; paint-order: stroke fill">Preprint</span></span>')

btn_txt = f"font-family: {TEXT}; font-weight: 500; font-size: 16px"
plus = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 2v12M2 8h12"></path></svg>'
minus = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 8h12"></path></svg>'
def rate(label, icon, on=False, last=False):
    fill = f"background-color: {INDIGO}; color: {STOCK}" if on else f"background: none; color: {INDIGO}"
    return (f'<button type="button" aria-pressed="{"true" if on else "false"}" style="flex: 1 1 0; height: 44px; box-sizing: border-box; border: 1.25px solid {INDIGO}; {"" if last else "border-right-width: 0;"} {fill}; display: flex; align-items: center; justify-content: center; gap: 8px; {btn_txt}; cursor: pointer">{icon}{label}</button>')

components = (
    box(M, COMP_Y, 470, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("Tags and badges / outline, solid, screened")}
<div style="display: flex; gap: 6px; flex-wrap: wrap">{tag_field("Physics")}{tag_field("Biology")}{tag_field("Space")}{tag_solid}{tag_pre}</div>
<div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px">
<div style="display: flex; gap: 6px; align-items: center">{tag_pre}<span style="{mono}; color: {MUTED}; margin-left: 4px">A card that is still a preprint</span></div>
<div style="font-family: {VOICE}; font-weight: 800; font-size: 20px; line-height: 1; letter-spacing: -0.02em; margin-top: 8px">[PREPRINT TITLE]</div>
<div style="font-family: {TEXT}; font-size: 16px; line-height: 23px">[ONE LINE SUMMARY]</div>
</div></div>''')
    + box(560, COMP_Y, 250, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("Primary button and paper link")}
<div style="display: flex; gap: 6px">
<a href="#explainer" style="flex-grow: 1; height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {BLUE}; color: {STOCK}; text-decoration: none; font-family: {VOICE}; font-weight: 700; font-size: 16px; letter-spacing: -0.01em"><span>See it explained</span><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"></path></svg></a>
<a href="#paper" aria-label="Open the original paper" style="width: 48px; height: 48px; box-sizing: border-box; border: 1.25px solid {INDIGO}; color: {INDIGO}; display: flex; align-items: center; justify-content: center"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 7h9v9M17 7L6.5 17.5"></path></svg></a>
</div>
<a href="#explainer" style="height: 48px; box-sizing: border-box; margin-top: -4px; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {INDIGO}; color: {STOCK}; text-decoration: none; font-family: {VOICE}; font-weight: 700; font-size: 16px; letter-spacing: -0.01em"><span>See it explained</span><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"></path></svg></a>
{cap("Pressed: overprint indigo")}
</div>''')
    + box(850, COMP_Y, 294, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("More like this, less like this")}
<div style="display: flex">{rate("More like this", plus)}{rate("Less like this", minus, last=True)}</div>
<div style="display: flex; margin-top: -4px">{rate("More like this", plus, on=True)}{rate("Less like this", minus, last=True)}</div>
{cap("Stamped: the fill floods in 120 ms")}
</div>''')
)

# ------------------------------------------------------------------ key idea band
KY = COMP_Y + 170
BH = 168
suns = ""
band = f'''<div style="position: absolute; left: 0; top: {KY}px; width: {W}px; height: {BH}px">
<svg aria-hidden="true" width="{W}" height="{BH}" viewBox="0 0 {W} {BH}" style="position: absolute; left: 0; top: 0">
<rect y="0" width="{W}" height="7" fill="url(#b2)"></rect><rect y="7" width="{W}" height="7" fill="url(#b7)"></rect>
<rect y="14" width="{W}" height="{BH - 28}" fill="{BLUE}"></rect>
<rect y="{BH - 14}" width="{W}" height="7" fill="url(#b7)"></rect><rect y="{BH - 7}" width="{W}" height="7" fill="url(#b2)"></rect>
{suns}
</svg>
<div style="position: absolute; left: {M}px; top: 34px; width: {W - 2 * M}px; display: flex; flex-direction: column; gap: 12px; color: {STOCK}">
<div style="{mono}; color: {STOCK}">Key idea</div>
<div style="font-family: {VOICE}; font-weight: 800; font-size: 45px; line-height: 0.96; letter-spacing: -0.04em; text-wrap: balance">Two black holes became one, and about three Suns of mass left as gravitational waves.</div>
</div>
</div>'''

# ------------------------------------------------------------------ caveat
BY = KY + BH + 26
caveat = box(M, BY, 300, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("Caveat / a dagger, then a note")}
<p style="margin: 0; font-family: {TEXT}; font-size: 16px; line-height: 24px; text-wrap: pretty">The signal came from about 410 megaparsecs away, roughly 1.3 billion light years.<span style="font-weight: 600; margin-left: 1px">&dagger;</span></p>
<div style="width: 56px; height: 0; border-top: 1px solid {INDIGO}; margin-top: 2px"></div>
<p style="margin: 0; font-family: {TEXT}; font-style: italic; font-size: 14px; line-height: 21px; text-wrap: pretty"><span style="font-style: normal; font-weight: 600">&dagger;</span> The distance carries a wide range, roughly 230 to 570 megaparsecs, and the sky position was known only to within about 600 square degrees.</p>
</div>''')

# ------------------------------------------------------------------ analogy drawing
AX0, AS = 4, 70.0     # px per angstrom
aw, ah = 350, 172
ruler_y = 150
def ax(v): return AX0 + v * AS
ticks = "".join(f'<path d="M{f(ax(v / 10))} {ruler_y}v{7 if v % 10 == 0 else (5 if v % 5 == 0 else 3)}"></path>' for v in range(0, 31))
tlabels = "".join(f'<text x="{f(ax(v))}" y="{ruler_y + 20}" text-anchor="middle">{v}</text>' for v in range(0, 4))
svgmono = f"font-family: {MONO}; font-stretch: 87.5%; font-weight: 500; font-size: 9.5px; letter-spacing: 0.07em"
svgnum = f"font-family: {VOICE}; font-weight: 800; font-size: 17px; letter-spacing: -0.02em"
atom_r = 1.4 * AS / 2
acy = 56
lab_x = ax(1.4) + 22
analogy_svg = f'''<svg viewBox="0 0 {aw} {ah}" width="{aw}" height="{ah}" role="img" aria-label="Drawing on one ruler in angstroms: a carbon atom 1.4 wide, AlphaFold's median error of 0.96 fits inside it, the next best method's 2.8 does not." style="display: block; overflow: visible">
<circle cx="{f(ax(0.7))}" cy="{acy}" r="{f(atom_r)}" fill="url(#b1)"></circle>
<circle cx="{f(ax(0.7))}" cy="{acy}" r="{f(atom_r)}" fill="none" stroke="{INDIGO}" stroke-width="1"></circle>
<g fill="none" stroke="{INDIGO}" stroke-width="0.75">
<path d="M{AX0} {acy + atom_r:.1f}V{ruler_y}M{f(ax(1.4))} {acy}V{ruler_y}" stroke-dasharray="none"></path>
<path d="M{f(ax(0.96) + 9)} {acy}H{f(lab_x - 6)}"></path>
<path d="M{f(ax(0.7) + atom_r * 0.74)} {f(acy - atom_r * 0.672)}L{f(lab_x - 6)} 16"></path>
</g>
<g fill="none" stroke="{INDIGO}" stroke-width="1">
<path d="M{AX0} {ruler_y}H{f(ax(3))}"></path>{ticks}
<path d="M{AX0} 126H{f(ax(2.8))}M{AX0} 121v10M{f(ax(2.8))} 121v10" stroke-width="1.5"></path>
</g>
<path d="M{AX0} {acy}H{f(ax(0.96))}" fill="none" stroke="{STOCK}" stroke-width="7"></path>
<path d="M{AX0} {acy}H{f(ax(0.96))}" fill="none" stroke="{PINK}" stroke-width="2.25" stroke-linecap="round"></path>
<circle cx="{f(ax(0.96))}" cy="{acy}" r="6.5" fill="{STOCK}"></circle>
<circle cx="{f(ax(0.96))}" cy="{acy}" r="4.5" fill="{PINK}"></circle>
<g fill="{INDIGO}" style="{svgmono}">{tlabels}<text x="{f(ax(3) + 12)}" y="{ruler_y + 20}">&#197;NGSTROMS</text>
<text x="{f(lab_x)}" y="20"><tspan style="{svgnum}">1.4</tspan><tspan dx="5">ONE CARBON ATOM</tspan></text>
<text x="{f(lab_x)}" y="{acy + 5}"><tspan style="{svgnum}">0.96</tspan><tspan dx="5">ALPHAFOLD, MEDIAN</tspan></text>
<text x="{f(ax(2.8) + 10)}" y="131"><tspan style="{svgnum}">2.8</tspan><tspan dx="5">NEXT BEST</tspan></text>
</g>
</svg>'''
analogy = box(404, BY, 350, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("Analogy / a drawing on one ruler")}
{analogy_svg}
<p style="margin: 0; font-family: {TEXT}; font-style: italic; font-size: 14px; line-height: 21px; text-wrap: pretty">AlphaFold's median error fits inside a single carbon atom. The next best method's does not.</p>
{cap("Illustration. Lengths drawn to one scale.")}
</div>''')

# ------------------------------------------------------------------ chart
cw_, ch_ = 348, 184
CX0, CS = 2, 4.9
def cx_(v): return CX0 + v * CS
axis_y = 138
r1, r2, bh = 30, 88, 14
grid = "".join(f'<path d="M{f(cx_(v))} {r1 - 4}V{axis_y}"></path>' for v in (20, 40, 60))
cticks = "".join(f'<path d="M{f(cx_(v))} {axis_y}v{6 if v % 10 == 0 else 3}"></path>' for v in range(0, 71, 5))
clabels = "".join(f'<text x="{f(cx_(v))}" y="{axis_y + 19}" text-anchor="middle">{v}</text>' for v in (0, 20, 40, 60))
halo = f"paint-order: stroke fill; stroke: {STOCK}; stroke-width: 4px; stroke-linejoin: round"
chart_svg = f'''<svg viewBox="0 0 {cw_} {ch_}" width="{cw_}" height="{ch_}" role="img" aria-label="Bar chart in solar masses. Before the merger: black holes of about 36 and 29. After: one black hole of about 62, and about 3 left as gravitational waves." style="display: block; overflow: visible; isolation: isolate">
<g fill="none" stroke="{MUTED}" stroke-width="0.6">{grid}</g>
<rect x="{f(cx_(0))}" y="{r1}" width="{f(36 * CS)}" height="{bh}" fill="{STOCK}"></rect><rect x="{f(cx_(0))}" y="{r1}" width="{f(36 * CS)}" height="{bh}" fill="url(#b5)"></rect>
<rect x="{f(cx_(36) + 1.5)}" y="{r1}" width="{f(29 * CS - 1.5)}" height="{bh}" fill="{STOCK}"></rect><rect x="{f(cx_(36) + 1.5)}" y="{r1}" width="{f(29 * CS - 1.5)}" height="{bh}" fill="url(#p5)"></rect>
<rect x="{f(cx_(0))}" y="{r2}" width="{f(62 * CS)}" height="{bh}" fill="{STOCK}"></rect>
<rect x="{f(cx_(0))}" y="{r2}" width="{f(62 * CS)}" height="{bh}" fill="url(#b5)"></rect>
<rect x="{f(cx_(0))}" y="{r2}" width="{f(62 * CS)}" height="{bh}" fill="url(#p5)" style="mix-blend-mode: multiply"></rect>
<rect x="{f(cx_(62) + 1.5)}" y="{r2}" width="{f(3 * CS - 1.5)}" height="{bh}" fill="{PINK}"></rect>
<g fill="none" stroke="{INDIGO}" stroke-width="1"><path d="M{f(cx_(0))} {axis_y}H{f(cx_(70))}"></path>{cticks}
<path d="M{f(cx_(63.5))} {r2 + bh + 3}v9" stroke-width="0.75"></path></g>
<g fill="{INDIGO}" style="{svgmono}">{clabels}<text x="{f(cx_(0))}" y="{axis_y + 36}">SOLAR MASSES</text>
<text x="{f(cx_(0))}" y="{r1 - 8}" style="{halo}"><tspan style="{svgnum}">36</tspan></text>
<text x="{f(cx_(36) + 1.5)}" y="{r1 - 8}" style="{halo}"><tspan style="{svgnum}">29</tspan></text>
<text x="{f(cx_(70))}" y="{r1 - 9}" text-anchor="end" style="{halo}">BEFORE</text>
<text x="{f(cx_(0))}" y="{r2 - 8}" style="{halo}"><tspan style="{svgnum}">62</tspan></text>
<text x="{f(cx_(70))}" y="{r2 - 9}" text-anchor="end" style="{halo}">AFTER</text>
<text x="{f(cx_(63.5) + 9)}" y="{r2 + bh + 27}" text-anchor="end" style="{halo}"><tspan style="{svgnum}">3</tspan><tspan dx="5">LEFT AS GRAVITATIONAL WAVES</tspan></text>
</g>
</svg>'''
chart = box(796, BY, 348, f'''<div style="display: flex; flex-direction: column; gap: 12px">
{cap("Chart / the merged hole overprints both inks")}
{chart_svg}
{cap("Data, from the paper. Values are approximate.")}
</div>''')

# ------------------------------------------------------------------ assemble
body = f'''<div style="width: {W}px; height: {H}px; box-sizing: border-box; position: relative; overflow: hidden; background-color: {STOCK}; color: {INDIGO}; font-family: {TEXT}">
{defs}
{header}
{type_block}
{hero}
{palettes}
{components}
{band}
{caveat}
{analogy}
{chart}
</div>'''

css = '''@keyframes regB{from{opacity:0;transform:translate(-5px,3px)}35%{opacity:1}}
@keyframes regP{from{opacity:0;transform:translate(5px,-3px)}35%{opacity:1}}
@keyframes sweep{from{stroke-dashoffset:1}}
@keyframes ride{from{offset-distance:0%}}
@keyframes pulse{to{opacity:.55}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}'''

if "--hold" in sys.argv:
    OUT = pathlib.Path(__file__).parent / "Hold-System.dc.html"
    ms = sys.argv[sys.argv.index("--hold") + 1]
    css += f"\n*{{animation-play-state:paused!important;animation-delay:-{ms}ms!important}}"
OUT.write_text(wrap("Paperboy style tile, Two-Ink Overprint", W, H, css, body))
print("wrote", OUT, OUT.stat().st_size)
