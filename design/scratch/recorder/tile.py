"""Builds design/canvas/project/Cand-z-System.dc.html (1200 x 1700 style tile)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib import DAY, NIGHT, VOICE, SERIF, MONO, Chirp, f, grid, ruler, perforation, page

D, N = DAY, NIGHT
W, H = 1200, 1700
PAD = 48
LW, RW, GAP = 712, 344, 48
CELL = 14
SWEEP, START = 2.2, 0.3


def slug(text, color=None, extra=""):
    return (f'<div style="font-family: {MONO}; font-size: 9.5px; line-height: 14px; letter-spacing: 0.06em; text-transform: uppercase; '
            f'color: {color or D["muted"]}; {extra}">{text}</div>')


def sec(title, note=""):
    n = f'<span style="color: {D["muted"]}; font-weight: 400">{note}</span>' if note else ""
    return (f'<div style="display: flex; gap: 12px; font-family: {MONO}; font-size: 10px; line-height: 14px; letter-spacing: 0.08em; text-transform: uppercase; '
            f'font-weight: 700; color: {D["ink"]}"><span>{title}</span>{n}</div>')


def axis_labels(items, color, y=11, size=13):
    return "".join(
        f'<text x="{f(x)}" y="{y}" text-anchor="{a}" font-family="{VOICE}" font-size="{size}" font-weight="600" fill="{color}" letter-spacing="0.2">{t}</text>'
        for x, t, a in items)


# =====================================================================================
# 0. Night band: wordmark + hero graphic (the animated one)
# =====================================================================================
BAND = 318
HX0 = 552                      # plot origin, time zero
HYC = 190                      # zero line = baseline of the wordmark
HTOP, HBOT = HYC - 7 * CELL, HYC + 7 * CELL
hero = Chirp(HX0, HYC, 2800, 6 * CELL, HX0 + CELL * 44, env=0.33, fade=0.055, pre=26)
hgrid = grid(HX0, W, HTOP, HBOT, CELL, N["grid"], origin_x=HX0, origin_y=HYC, w_minor=0.6, w_major=1.1)
hruler = ruler(HX0, W, HTOP, CELL, N["structure"], major_every=5, up=True, minor=4, major=8, w=1)
band = f'''<div style="position: relative; height: {BAND}px; background-color: {N["ground"]}; color: {N["text"]}; overflow: hidden; flex-shrink: 0">
<svg width="{W}" height="{BAND}" viewBox="0 0 {W} {BAND}" role="img" aria-label="Paperboy wordmark. Its baseline runs on as a glowing line that a pen writes across chart paper: an illustration of the chirp signal." style="position: absolute; left: 0; top: 0; display: block">
<defs>
<clipPath id="hplot"><rect x="{HX0}" y="{HTOP}" width="{W - HX0}" height="{HBOT - HTOP}"></rect></clipPath>
<clipPath id="hrail"><rect x="0" y="{HTOP - 9}" width="{W}" height="9"></rect></clipPath>
</defs>
{hgrid}
<line x1="{HX0}" y1="{HYC}" x2="{W}" y2="{HYC}" stroke="{N["structure"]}" stroke-width="0.75"></line>
{hruler}
{axis_labels([(HX0, "0", "start"), (HX0 + 280, "0.1", "middle"), (HX0 + 560, "0.2 s", "middle")], N["muted"], y=HTOP - 13)}
<text x="{PAD - 5}" y="{HYC}" font-family="{VOICE}" font-size="132" font-weight="800" fill="{N["text"]}" letter-spacing="0.5">Paperboy</text>
<path class="pb-trace" d="{hero.d}" pathLength="1" fill="none" stroke="{N["live"]}" stroke-opacity="0.07" stroke-width="15" stroke-linejoin="round" stroke-linecap="round"></path>
<path class="pb-trace" d="{hero.d}" pathLength="1" fill="none" stroke="{N["live"]}" stroke-opacity="0.2" stroke-width="6.5" stroke-linejoin="round" stroke-linecap="round"></path>
<path class="pb-trace" d="{hero.d}" pathLength="1" fill="none" stroke="{N["live"]}" stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round"></path>
<g clip-path="url(#hplot)"><g class="pb-pen"><line x1="0" y1="-500" x2="0" y2="500" stroke="{N["structure"]}" stroke-width="1"></line></g></g>
<g clip-path="url(#hrail)"><g class="pb-pen"><line x1="0" y1="-500" x2="0" y2="500" stroke="{N["text"]}" stroke-width="9"></line></g></g>
<g class="pb-pen"><circle r="12" fill="{N["live"]}" fill-opacity="0.12"></circle><circle r="7.5" fill="{N["live"]}" fill-opacity="0.22"></circle><circle class="pb-nib" r="4.25" fill="{N["live"]}"></circle></g>
</svg>
<div style="position: absolute; left: {PAD}px; top: 26px; font-family: {MONO}; font-size: 10px; line-height: 14px; letter-spacing: 0.08em; text-transform: uppercase; color: {N["muted"]}"><span style="color: {N["text"]}; font-weight: 700">Strip Chart</span>&nbsp;&nbsp;System tile</div>
<div style="position: absolute; left: {PAD}px; top: {HYC + 42}px; width: 430px; font-family: {SERIF}; font-style: italic; font-weight: 500; font-size: 21px; line-height: 30px; color: {N["text"]}; text-wrap: balance">A feed of newly released science and math papers, each one explained visually.</div>
<div style="position: absolute; left: {HX0}px; right: {PAD}px; top: {HBOT + 10}px; display: flex; justify-content: space-between; font-family: {MONO}; font-size: 9.5px; line-height: 14px; letter-spacing: 0.06em; text-transform: uppercase; color: {N["muted"]}"><span>Illustration of the signal, not data</span><span>Sweep: 2.2 s, linear. Then the pen point pulses</span></div>
</div>'''

# =====================================================================================
# 1. Type
# =====================================================================================
row_css = f"display: grid; grid-template-columns: 116px minmax(0, 1fr); column-gap: 20px; padding: 7px 0 8px; border-top: 0.5px solid {D['ink']}"


def spec(role, face, size):
    return (f'<div style="font-family: {MONO}; font-size: 9.5px; line-height: 15px; letter-spacing: 0.06em; text-transform: uppercase; color: {D["muted"]}">'
            f'<div style="color: {D["ink"]}; font-weight: 700">{role}</div><div>{face}</div><div>{size}</div></div>')


def readout(val, unit, cap, sup=""):
    u = f' <span style="font-size: 26px; font-weight: 600; letter-spacing: 0.01em">{unit}</span>' if unit else ""
    return (f'<div style="display: flex; flex-direction: column; gap: 5px">'
            f'<div style="height: 46px; font-family: {VOICE}; font-size: 56px; font-weight: 700; line-height: 46px; font-variant-numeric: tabular-nums; color: {D["ink"]}; white-space: nowrap">{val}{sup}{u}</div>'
            f'{slug(cap)}</div>')


sup21 = '<sup style="font-size: 27px; line-height: 0; vertical-align: 22px; margin-left: 2px; letter-spacing: 0.02em">&minus;21</sup>'
type_block = f'''<div style="width: {LW}px; display: flex; flex-direction: column">
<div style="padding-bottom: 10px">{sec("Type", "Three families: Big Shoulders, Literata, B612 Mono")}</div>
<div style="padding: 8px 0 10px; border-top: 0.5px solid {D["ink"]}; display: flex; flex-direction: column; gap: 4px">
{slug(f'<span style="color: {D["ink"]}; font-weight: 700">Display</span>&nbsp;&nbsp;Big Shoulders 700, 76 / 70&nbsp;&nbsp;Second voice: Literata Italic 400, 56 / 60')}
<div style="font-family: {VOICE}; font-size: 76px; font-weight: 700; line-height: 70px; letter-spacing: -0.005em; color: {D["ink"]}; white-space: nowrap">Two black holes merged.</div>
<div style="font-family: {SERIF}; font-style: italic; font-weight: 400; font-size: 56px; line-height: 60px; letter-spacing: -0.02em; color: {D["ink"]}; white-space: nowrap">Earth felt space stretch.</div>
</div>
<div style="{row_css}">{spec("Headline", "Big Shoulders 700", "52 / 49")}
<div style="font-family: {VOICE}; font-size: 52px; font-weight: 700; line-height: 49px; letter-spacing: -0.005em; color: {D["ink"]}">A neural network learned to fold proteins.</div></div>
<div style="{row_css}">{spec("Body", "Literata 400", "17 / 26")}
<div style="font-family: {SERIF}; font-size: 17px; line-height: 26px; color: {D["ink"]}; text-wrap: pretty">Given only a protein's amino acid sequence, AlphaFold predicted its 3D shape to within about the width of an atom in a blind test.</div></div>
<div style="{row_css}">{spec("Label", "B612 Mono", "10 / 16, caps")}
<div style="font-family: {MONO}; font-size: 10px; line-height: 16px; letter-spacing: 0.06em; text-transform: uppercase; color: {D["ink"]}"><div style="font-weight: 700">Illustration of the signal, not data</div><div style="color: {D["muted"]}">Physical Review Letters 116, 061102. February 11, 2016</div></div></div>
<div style="{row_css}; padding-bottom: 0">{spec("Numeral", "Big Shoulders 700", "56, tabular")}
<div style="display: flex; gap: 38px; align-items: flex-start; padding-top: 3px">
{readout('1.0 <span style="font-weight: 500">&times;</span> 10', "", "Peak strain", sup21)}
{readout("410", "Mpc", "Distance")}
{readout("&gt;5.1", "sigma", "Significance")}
</div></div>
</div>'''

# =====================================================================================
# 2. Palette
# =====================================================================================


def swatch(name, hexv, note, w, text, muted, outline=None, fs=14.5):
    b = f"box-shadow: inset 0 0 0 1px {outline};" if outline else ""
    return (f'<div style="width: {w}px; display: flex; flex-direction: column; gap: 6px">'
            f'<div style="height: 60px; background-color: {hexv}; {b}"></div>'
            f'<div style="display: flex; flex-direction: column; gap: 1px">'
            f'<div style="font-family: {VOICE}; font-size: {fs}px; font-weight: 600; line-height: 17px; letter-spacing: 0; color: {text}; white-space: nowrap">{name}</div>'
            f'<div style="font-family: {MONO}; font-size: 8.5px; line-height: 13px; letter-spacing: 0.02em; color: {text}">{hexv}</div>'
            f'<div style="font-family: {VOICE if ":" in note else MONO}; font-size: {"12.5px" if ":" in note else "8.5px"}; font-weight: {600 if ":" in note else 400}; line-height: 13px; letter-spacing: 0.02em; font-variant-numeric: tabular-nums; color: {muted}">{note}</div>'
            f'</div></div>')


def live_strip(w, h, ground, grid_c, zero_c, live, night, ident):
    c = Chirp(0, h / 2, 1150, h / 2 - 9, w - 28, env=0.33, lead=0.0)
    halo = ""
    if night:
        halo = (f'<path d="{c.d}" fill="none" stroke="{live}" stroke-opacity="0.07" stroke-width="13" stroke-linejoin="round" stroke-linecap="round"></path>'
                f'<path d="{c.d}" fill="none" stroke="{live}" stroke-opacity="0.2" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"></path>')
        nib = (f'<circle cx="{w - 28}" cy="{h/2}" r="7" fill="{live}" fill-opacity="0.22"></circle><circle cx="{w - 28}" cy="{h/2}" r="3.75" fill="{live}"></circle>')
    else:
        nib = f'<circle cx="{w - 28}" cy="{h/2}" r="5.5" fill="{ground}"></circle><circle cx="{w - 28}" cy="{h/2}" r="3.75" fill="{live}"></circle>'
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Sample of the live line" style="display: block">'
            f'{grid(0, w, 0, h, CELL, grid_c, origin_x=0, origin_y=h/2, w_minor=0.5, w_major=0.9)}'
            f'<line x1="0" y1="{h/2}" x2="{w}" y2="{h/2}" stroke="{zero_c}" stroke-width="0.75"></line>'
            f'{halo}<path d="{c.d}" fill="none" stroke="{live}" stroke-width="{1.6 if night else 1.75}" stroke-linejoin="round" stroke-linecap="round"></path>{nib}</svg>')


day_sw = "".join([
    swatch("Stock", D["stock"], "ground", 60, D["ink"], D["muted"], outline=D["ink"]),
    swatch("Ink", D["ink"], "14.8:1", 60, D["ink"], D["muted"]),
    swatch("Muted", D["muted"], "6.2:1", 60, D["ink"], D["muted"]),
    swatch("Plot grid", D["grid"], "plots only", 60, D["ink"], D["muted"]),
    swatch("Viridian", D["live"], "4.8:1", 60, D["ink"], D["muted"]),
])
night_sw = "".join([
    swatch("Ground", N["ground"], "ground", 48, N["text"], N["muted"], outline=N["structure"], fs=13.5),
    swatch("Text", N["text"], "14.9:1", 48, N["text"], N["muted"], fs=13.5),
    swatch("Muted", N["muted"], "7.1:1", 48, N["text"], N["muted"], fs=13.5),
    swatch("Grid", N["grid"], "plots", 48, N["text"], N["muted"], fs=13.5),
    swatch("Structure", N["structure"], "3.3:1", 48, N["text"], N["muted"], fs=13.5),
    swatch("Phosphor", N["live"], "13.6:1", 48, N["text"], N["muted"], fs=13.5),
])
palette_block = f'''<div style="width: {RW + PAD}px; display: flex; flex-direction: column; gap: 20px">
<div style="width: {RW}px; display: flex; flex-direction: column; gap: 10px">
{sec("Day", "Ink on chart stock")}
<div style="display: flex; gap: 11px">{day_sw}</div>
<div style="display: flex; flex-direction: column; gap: 6px; padding-top: 4px">
{live_strip(RW, 70, D["stock"], D["grid"], D["muted"], D["live"], False, "d")}
{slug("The live line by day: solid ink, 1.75 px, pen point")}
</div>
</div>
<div style="margin-left: -24px; padding: 18px {PAD}px 18px 24px; background-color: {N["ground"]}; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; gap: 12px; font-family: {MONO}; font-size: 10px; line-height: 14px; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; color: {N["text"]}"><span>Night</span><span style="color: {N["muted"]}; font-weight: 400">Light on a green-black ground</span></div>
<div style="display: flex; gap: 11.2px">{night_sw}</div>
<div style="display: flex; flex-direction: column; gap: 6px; padding-top: 4px">
{live_strip(RW, 70, N["ground"], N["grid"], N["structure"], N["live"], True, "n")}
{slug("By night: a 1.6 px core, two halos of one hue", N["muted"])}
</div>
</div>
</div>'''

# =====================================================================================
# 3. Tags, badges, controls
# =====================================================================================
tag_base = f"box-sizing: border-box; height: 22px; display: flex; align-items: center; padding: 0 7px; font-family: {MONO}; font-size: 10px; line-height: 1; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 700"


def field_tag(t):
    return f'<span style="{tag_base}; border: 1px solid {D["ink"]}; color: {D["ink"]}">{t}</span>'


peer = f'<span style="{tag_base}; background-color: {D["ink"]}; color: {D["stock"]}">Peer-reviewed</span>'
preprint = (f'<span style="{tag_base}; position: relative; padding: 0 4px; border: 1px solid {D["ink"]}; color: {D["ink"]}">'
            f'<svg width="100%" height="100%" aria-hidden="true" style="position: absolute; left: 0; top: 0"><defs><pattern id="scr-pp" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3" height="1" fill="{D["ink"]}"></rect></pattern></defs><rect width="100%" height="100%" fill="url(#scr-pp)"></rect></svg>'
            f'<span style="position: relative; height: 14px; display: flex; align-items: center; padding: 0 4px; background-color: {D["stock"]}">Preprint</span></span>')

pulse_up = '<svg width="26" height="16" viewBox="0 0 26 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="miter" aria-hidden="true"><path d="M1 13 H8 L13 2 L18 13 H25"></path></svg>'
pulse_dn = '<svg width="26" height="16" viewBox="0 0 26 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="miter" aria-hidden="true"><path d="M1 3 H8 L13 14 L18 3 H25"></path></svg>'


def rate(label, icon, on=False):
    bg, fg = (D["ink"], D["stock"]) if on else ("transparent", D["ink"])
    pressed = ' aria-pressed="true"' if on else ""
    return (f'<button type="button"{pressed} style="flex: 1 1 0; min-width: 0; height: 44px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; gap: 9px; padding: 0; '
            f'background-color: {bg}; border: 1px solid {D["ink"]}; border-radius: 0; color: {fg}; font-family: {VOICE}; font-size: 17px; font-weight: 600; letter-spacing: 0.015em; cursor: pointer">{icon}<span>{label}</span></button>')


tags_block = f'''<div style="width: {LW}px; display: flex; gap: 40px">
<div style="width: 336px; display: flex; flex-direction: column; gap: 12px">
{sec("Tags and badges", "Told apart by form, not hue")}
<div style="display: flex; flex-direction: column; gap: 7px">
<div style="display: flex; gap: 6px">{field_tag("Physics")}{field_tag("Biology")}{field_tag("Space")}</div>
{slug("Field tag: a ruled outline")}
</div>
<div style="display: flex; flex-direction: column; gap: 7px">
<div style="display: flex; gap: 6px">{peer}{preprint}</div>
{slug("Solid means reviewed. Screened means not yet")}
</div>
<div style="display: flex; flex-direction: column; gap: 5px; padding-top: 2px">
<div style="display: flex; gap: 6px; align-items: center">{field_tag("Physics")}{peer}<a href="#paper-1" style="margin-left: 8px; display: flex; align-items: center; gap: 5px; height: 22px; color: {D["ink"]}; text-decoration: none; font-family: {SERIF}; font-style: italic; font-size: 13.5px; line-height: 1"><span style="border-bottom: 1px solid {D["ink"]}; padding-bottom: 1px">Phys. Rev. Lett. 116</span><svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 8 L8 2 M3.5 2 H8 V6.5"></path></svg></a></div>
{slug("In use: the card header, with a link to the paper")}
</div>
</div>
<div style="width: 336px; display: flex; flex-direction: column; gap: 9px">
{slug("A preprint card, with placeholder content")}
<div style="display: flex; gap: 6px; align-items: center">{preprint}</div>
<div style="font-family: {VOICE}; font-size: 38px; font-weight: 700; line-height: 36px; letter-spacing: -0.005em; color: {D["ink"]}">[PREPRINT TITLE]</div>
<div style="font-family: {SERIF}; font-size: 16px; line-height: 24px; color: {D["ink"]}">[ONE LINE SUMMARY]</div>
</div>
</div>'''

controls_block = f'''<div style="width: {RW}px; display: flex; flex-direction: column; gap: 8px">
<div style="padding-bottom: 2px">{sec("Controls", "Square, 44 px and up")}</div>
<a href="#explainer" style="height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; background-color: {D["ink"]}; color: {D["stock"]}; text-decoration: none; font-family: {VOICE}; font-size: 20px; font-weight: 700; letter-spacing: 0.015em"><span>Open the explainer</span><svg width="26" height="14" viewBox="0 0 26 14" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M0 7 H24 M18 1 L24 7 L18 13"></path></svg></a>
<div style="display: flex; gap: 8px">{rate("More like this", pulse_up)}{rate("Less like this", pulse_dn)}</div>
<div style="display: flex; gap: 8px; align-items: center">
<div style="width: 168px; display: flex">{rate("More like this", pulse_up, on=True)}</div>
{slug("Tapped: the fill floods in, a 120 ms stamp", extra="flex: 1 1 0; min-width: 0")}
</div>
</div>'''

# =====================================================================================
# 4. Key idea (pinned to the trace) and caveat (a note)
# =====================================================================================
KAX, KROWS = 22, 6
KPH = KROWS * CELL
KYC = KAX + KPH / 2
kc = Chirp(0, KYC, 2800, 2 * CELL + 7, 630, env=0.33)
ktrough = kc.trough
KH = KAX + KPH + 26
kgrid = grid(0, LW, KAX, KAX + KPH, CELL, D["grid"], origin_x=0, origin_y=KYC, w_minor=0.5, w_major=0.9)
kruler = ruler(0, LW, KAX, CELL, D["ink"], major_every=5, up=True, minor=4, major=8, w=1)
key_block = f'''<div style="width: {LW}px; display: flex; flex-direction: column">
<div style="padding-bottom: 8px">{sec("Key idea", "Pinned to the trace with a leader, then set at scale. No box")}</div>
<div style="position: relative; height: {KH}px">
<svg width="{LW}" height="{KH}" viewBox="0 0 {LW} {KH}" role="img" aria-label="Illustration of the signal. A leader line runs from its deepest swing to the key idea below." style="position: absolute; left: 0; top: 0; display: block; overflow: visible">
{kgrid}
<line x1="0" y1="{KYC}" x2="{LW}" y2="{KYC}" stroke="{D["muted"]}" stroke-width="0.75"></line>
{kruler}
{axis_labels([(0, "0", "start"), (280, "0.1", "middle"), (560, "0.2 s", "middle")], D["ink"])}
<path d="{kc.d}" fill="none" stroke="{D["live"]}" stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round"></path>
<circle cx="630" cy="{KYC}" r="6" fill="{D["stock"]}"></circle><circle cx="630" cy="{KYC}" r="4" fill="{D["live"]}"></circle>
<path d="M76 {KH - 7} H{f(ktrough[0])} V{f(ktrough[1] + 5.5)}" fill="none" stroke="{D["ink"]}" stroke-width="0.75"></path>
<circle cx="{f(ktrough[0])}" cy="{f(ktrough[1])}" r="3.25" fill="none" stroke="{D["ink"]}" stroke-width="1"></circle>
</svg>
<div style="position: absolute; left: 0; top: {KH - 14}px">{slug("Key idea", D["ink"], "font-weight: 700")}</div>
</div>
<div style="padding-top: 12px; font-family: {SERIF}; font-style: italic; font-weight: 400; font-size: 32px; line-height: 39px; letter-spacing: -0.015em; color: {D["ink"]}; text-wrap: balance">The ripple changed the length of a 4&nbsp;km arm by far less than the width of a proton.</div>
</div>'''

# range strip: 410 Mpc, roughly 230 to 570
RS = 0.5      # px per megaparsec
RAX = 22
rng_ruler = ruler(0, 300, RAX, 25, D["ink"], major_every=2, up=True, minor=4, major=8, w=1)
range_svg = f'''<svg width="{RW}" height="68" viewBox="0 0 {RW} 68" role="img" aria-label="Data from the paper: distance 410 megaparsecs, range roughly 230 to 570, drawn on a ruler from 0 to 600." style="display: block; overflow: visible">
<defs><pattern id="scr-rng" width="3.5" height="3.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.5" height="1.2" fill="{D["ink"]}"></rect></pattern></defs>
{rng_ruler}
{axis_labels([(0, "0", "start"), (100, "200", "middle"), (200, "400", "middle"), (300, "600 Mpc", "middle")], D["ink"])}
<rect x="{230 * RS}" y="{RAX + 9}" width="{(570 - 230) * RS}" height="14" fill="url(#scr-rng)"></rect>
<rect x="{230 * RS}" y="{RAX + 9}" width="{(570 - 230) * RS}" height="14" fill="none" stroke="{D["ink"]}" stroke-width="0.75"></rect>
<line x1="{410 * RS}" y1="{RAX + 5}" x2="{410 * RS}" y2="{RAX + 27}" stroke="{D["ink"]}" stroke-width="3"></line>
<text x="{230 * RS}" y="{RAX + 40}" text-anchor="middle" font-family="{VOICE}" font-size="13" font-weight="600" fill="{D["ink"]}">230</text>
<text x="{410 * RS}" y="{RAX + 44}" text-anchor="middle" font-family="{VOICE}" font-size="17" font-weight="700" fill="{D["ink"]}">410</text>
<text x="{570 * RS}" y="{RAX + 40}" text-anchor="middle" font-family="{VOICE}" font-size="13" font-weight="600" fill="{D["ink"]}">570</text>
</svg>'''
caveat_block = f'''<div style="width: {RW}px; display: flex; flex-direction: column">
<div style="padding-bottom: 10px">{sec("Caveat", "A dagger and a note")}</div>
<div style="font-family: {SERIF}; font-size: 16px; line-height: 25px; color: {D["ink"]}; text-wrap: pretty">The two black holes merged about 410 megaparsecs away,<span style="font-size: 17px">&dagger;</span> roughly 1.3 billion light years.</div>
<div style="margin-top: 12px; width: 56px; height: 0; border-top: 0.5px solid {D["ink"]}"></div>
<div style="padding-top: 8px; font-family: {SERIF}; font-style: italic; font-size: 14px; line-height: 21px; color: {D["ink"]}; text-wrap: pretty">&dagger; The distance carries a wide error range: 410 megaparsecs, within roughly 230 to 570.</div>
<div style="padding-top: 16px; display: flex; flex-direction: column; gap: 4px">
{range_svg}
{slug("Data, from the paper. Solid: value. Screened: range")}
</div>
</div>'''

# =====================================================================================
# 5. Chart (masses) and analogy (carbon atom)
# =====================================================================================
S = 9                 # px per solar mass
CAX = 24
CPH = 146
y1, y2 = CAX + 52, CAX + 120
BAR = 12
wave = Chirp(62 * S, y2 + BAR / 2, 135, 8, 65 * S, T=0.2, f0=18, f1=70, tau_d=0.008, env=0.3)
holes = [(-1, CAX, 232, y1 - 3), (36 * S + 1, CAX, 36 * S + 136, y1 - 3), (-1, y1 + BAR, 190, y2 - 3)]
cgrid = grid(0, 65 * S + 1, CAX, CAX + CPH, 5 * S, D["grid"], holes=holes, origin_x=0, origin_y=CAX, major_every=2, w_minor=0.5, w_major=0.9, horizontal=False)
# only vertical lines: drop the horizontals by clipping to nothing below (grid draws both, keep it simple with a tall cell)
cruler = ruler(0, 70 * S, CAX, S, D["ink"], major_every=10, up=True, minor=4, major=8, w=1)


def mass_lbl(x, y, num, cap):
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; display: flex; align-items: baseline; gap: 7px; white-space: nowrap">'
            f'<div style="font-family: {VOICE}; font-size: 36px; font-weight: 700; line-height: 34px; font-variant-numeric: tabular-nums; color: {D["ink"]}">{num}</div>'
            f'{slug(cap)}</div>')


chart_block = f'''<div style="width: {LW}px; display: flex; flex-direction: column">
<div style="padding-bottom: 10px">{sec("Chart", "A ruler axis, direct labels, the live line carries the finding")}</div>
<div style="position: relative; height: {CAX + CPH}px">
<svg width="{LW}" height="{CAX + CPH}" viewBox="0 0 {LW} {CAX + CPH}" role="img" aria-label="Data from the paper. Before: black holes of about 36 and 29 solar masses. After: one black hole of about 62 solar masses, with about 3 solar masses left as gravitational waves." style="position: absolute; left: 0; top: 0; display: block; overflow: visible">
{cgrid}
{cruler}
{axis_labels([(0, "0", "start")] + [(k * 10 * S, str(k * 10), "middle") for k in range(1, 7)] + [(70 * S - 6, "70 solar masses", "start")], D["ink"])}
<rect x="0" y="{y1}" width="{36 * S - 1.5}" height="{BAR}" fill="{D["ink"]}"></rect>
<rect x="{36 * S + 1.5}" y="{y1}" width="{29 * S - 1.5}" height="{BAR}" fill="{D["ink"]}"></rect>
<rect x="0" y="{y2}" width="{62 * S - 1.5}" height="{BAR}" fill="{D["ink"]}"></rect>
<line x1="{65 * S}" y1="{y1 + BAR}" x2="{65 * S}" y2="{y2 + BAR / 2 - 7}" stroke="{D["ink"]}" stroke-width="0.75"></line>
<line x1="{62 * S + 1.5}" y1="{y2 + BAR / 2}" x2="{65 * S}" y2="{y2 + BAR / 2}" stroke="{D["live"]}" stroke-width="1.75"></line>
<circle cx="{65 * S}" cy="{y2 + BAR / 2}" r="5.5" fill="{D["stock"]}"></circle><circle cx="{65 * S}" cy="{y2 + BAR / 2}" r="3.75" fill="{D["live"]}"></circle>
</svg>
{mass_lbl(0, y1 - 39, "36", "Before: the larger black hole")}
{mass_lbl(36 * S + 6, y1 - 39, "29", "The smaller")}
{mass_lbl(0, y2 - 39, "62", "After: one black hole")}
{mass_lbl(65 * S + 13, y2 + BAR / 2 - 20, "3", "Left as waves")}
</div>
<div style="padding-top: 8px">{slug("Data, from the paper. All four masses are approximate")}</div>
</div>'''

AS = 58               # px per angstrom
AAX = 24
atom_r = 0.7 * AS
acy = AAX + 14 + atom_r
ay2 = acy + atom_r + 18
aruler = ruler(0, 3 * AS + 14, AAX, AS / 5, D["ink"], major_every=5, up=True, minor=4, major=8, w=1)
AH = ay2 + 14
analogy_svg = f'''<svg width="{RW}" height="{f(AH)}" viewBox="0 0 {RW} {f(AH)}" role="img" aria-label="Drawn to scale on an angstrom ruler: a carbon atom about 1.4 angstroms wide, AlphaFold's median error of 0.96 angstroms inside it, and the next best method's 2.8 angstroms." style="display: block; overflow: visible">
{aruler}
{axis_labels([(0, "0", "start"), (AS, "1", "middle"), (2 * AS, "2", "middle"), (3 * AS, "3 Å", "middle")], D["ink"])}
<circle cx="{f(atom_r)}" cy="{f(acy)}" r="{f(atom_r)}" fill="none" stroke="{D["ink"]}" stroke-width="1"></circle>
<path d="M0 {f(acy)} H{f(0.96 * AS)}" fill="none" stroke="{D["live"]}" stroke-width="1.75" stroke-linecap="round"></path>
<circle cx="{f(0.96 * AS)}" cy="{f(acy)}" r="5.5" fill="{D["stock"]}"></circle><circle cx="{f(0.96 * AS)}" cy="{f(acy)}" r="3.75" fill="{D["live"]}"></circle>
<path d="M0 {f(ay2)} H{f(2.8 * AS)} M0 {f(ay2 - 5)} V{f(ay2 + 5)} M{f(2.8 * AS)} {f(ay2 - 5)} V{f(ay2 + 5)}" fill="none" stroke="{D["ink"]}" stroke-width="1"></path>
<path d="M{f(atom_r + 0.707 * atom_r + 3)} {f(acy - 0.707 * atom_r)} H{f(2 * atom_r + 24)} M{f(0.96 * AS + 8)} {f(acy)} H{f(2 * atom_r + 24)}" fill="none" stroke="{D["ink"]}" stroke-width="0.75"></path>
</svg>'''
def a_lbl(x, yc, num, cap):
    return (f'<div style="position: absolute; left: {f(x)}px; top: {f(yc - 13)}px; display: flex; align-items: baseline; gap: 6px; white-space: nowrap">'
            f'<div style="font-family: {VOICE}; font-size: 22px; font-weight: 700; line-height: 24px; color: {D["ink"]}">{num} <span style="font-size: 15px; font-weight: 600">&Aring;</span></div>{slug(cap)}</div>')


analogy_block = f'''<div style="width: {RW}px; display: flex; flex-direction: column">
<div style="padding-bottom: 10px">{sec("Analogy", "A drawing on one ruler")}</div>
<div style="position: relative">
{analogy_svg}
{a_lbl(2 * atom_r + 30, acy - 0.707 * atom_r, "1.4", "One carbon atom")}
{a_lbl(2 * atom_r + 30, acy, "0.96", "AlphaFold, median error")}
{a_lbl(2.8 * AS + 10, ay2, "2.8", "Next best")}
</div>
<div style="padding-top: 4px">{slug("Illustration, drawn to scale")}</div>
<div style="padding-top: 8px; font-family: {SERIF}; font-style: italic; font-size: 16px; line-height: 23px; color: {D["ink"]}; text-wrap: pretty">AlphaFold's median error is narrower than a single carbon atom.</div>
</div>'''


def row(left, right, top=20, bottom=20, extra=""):
    return f'<section style="display: flex; flex-shrink: 0; gap: {GAP}px; padding: {top}px {PAD}px {bottom}px; {extra}">{left}{right}</section>'


perf = perforation(W, D["ink"])
body = f'''<div style="position: relative; width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; background-color: {D["stock"]}; color: {D["ink"]}; font-family: {SERIF}; display: flex; flex-direction: column">
{band}
{row(type_block, palette_block, 20, 18, "padding-right: 0")}
{perf}
{row(tags_block, controls_block, 14, 16)}
{perf}
{row(key_block, caveat_block, 14, 16)}
{perf}
{row(chart_block, analogy_block, 14, 0)}
</div>'''

css = f'''body{{margin:0}}
a{{color:{D["ink"]}}}a:hover{{color:{D["live"]}}}
@keyframes pb-sweep{{from{{stroke-dashoffset:1}}}}
@keyframes pb-ride{{from{{offset-distance:0%}}}}
@keyframes pb-pulse{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
.pb-trace{{stroke-dasharray:1 2;stroke-dashoffset:0;animation:pb-sweep {SWEEP}s linear {START}s both}}
.pb-pen{{offset-path:path("{hero.d}");offset-rotate:0deg;offset-distance:100%;animation:pb-ride {SWEEP}s linear {START}s both}}
.pb-nib{{animation:pb-pulse 2.4s ease-in-out {START + SWEEP + 0.1:.1f}s infinite}}
.pb-knock{{-webkit-text-stroke:4px {D["stock"]};paint-order:stroke fill}}
@media (prefers-reduced-motion:reduce){{.pb-trace,.pb-pen,.pb-nib{{animation:none}}}}'''

out = pathlib.Path(__file__).resolve().parents[2] / "canvas/project/Cand-z-System.dc.html"
out.write_text(page("System tile, Strip Chart direction", W, H, css, body))
print("wrote", out, "hero length px", round(hero.length), "speed px/s", round(hero.length / SWEEP))
