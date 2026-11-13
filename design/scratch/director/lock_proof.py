"""Director's proof of the locked First Light system: one feed screen, day and night.

It reuses the Engraved Broadsheet drawing code (scratch/engraved/lib.py) and adds the
grafts named in JURY-1.md, so every value written into SYSTEM.md has been looked at:

  - a second print ink (plate blue) so the plate carries color mass
  - the live line crossing the plate, with a paper trap by day and a halo by night
  - the pen carriage riding the ruler axis (from Strip Chart)
  - true two-plate Register (from Two-Ink Overprint)
  - mono labels at 10.5 px

  python3 lock_proof.py            writes LockProof-Day.dc.html and LockProof-Night.dc.html
  PB_PLATE=ink python3 lock_proof.py   same, with the plate in black ink (the A/B comparison)
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import *  # noqa: E402,F403

BLUE = "#1F3FD0"      # plate ink, day
NBLUE = "#4D63C9"     # plate light, night (structure)
PLATE_INK = INK if os.environ.get("PB_PLATE") == "ink" else BLUE
SUFFIX = "-ink" if os.environ.get("PB_PLATE") == "ink" else ""
LAB = 10.5

W, H = 390, 844
M = 20
BAND = 196


def T(theme):
    day = theme == "day"
    return dict(
        day=day,
        ground=STOCK if day else NG,
        text=INK if day else NT,
        muted=MUTED if day else NM,
        plate=PLATE_INK if day else NBLUE,
        key=INK if day else NS,          # the black plate: wells, contours
        fine=INK if day else NX,
        live=LIVE if day else AMBER,
    )


def tag_outline(t, c):
    return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'


def tag_solid(t, bg, fg):
    return f'<span style="{mono(10, color=fg, weight=600, ls=0.06)}; background-color: {bg}; border: 1px solid {bg}; padding: 4px 6px 3px">{t}</span>'


def source(label, c):
    return (
        f'<a href="#paper" style="margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
        f'{text(15, lh=1, italic=True)}; color: {c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</a>'
    )


def rate_btn(icon, label, c):
    return (
        f'<button type="button" style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: transparent; '
        f'border: 1px solid {c}; border-radius: 0; color: {c}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">'
        f'{icon}<span style="{text(16, lh=1, weight=500)}">{label}</span></button>'
    )


def plate(pid, theme):
    t = T(theme)
    day = t["day"]
    cx, cy = M + (W - 2 * M) * 0.76, 62
    y0, amp = 157, 29
    d, xm, crest = chirp(M, y0, W - 2 * M, amp)
    ruler = BAND                      # the ruler axis is the bottom edge of the plate
    PH = BAND + 34

    wdefs, wmarks = wavefield(pid, cx, cy, W, BAND, t["plate"], rot=-25, rmax=420.0)
    if not day:
        wmarks = wmarks.replace(f'stroke="{t["plate"]}" stroke-width="0.5"', f'stroke="{t["plate"]}" stroke-width="0.6" stroke-opacity="0.55"', 1)
    bod = wells(pid, cx, cy, t["ground"], t["key"] if day else NM, night=not day)
    # the well discs are the one place the two inks overprint: a blue screen under a black cross screen
    if day:
        key_defs = patterns(pid, t["plate"], tones={"a3": (A1, 0.68)}) + patterns(pid, t["key"], tones={"b3": (A2, 0.66)})
    else:
        key_defs = patterns(pid, NBLUE, tones={"n1": (A2, 0.34)})

    blue_svg = (
        f'<svg viewBox="0 0 {W} {BAND}" width="{W}" height="{BAND}" aria-hidden="true" style="display: block">'
        f'<defs>{wdefs}</defs>{wmarks}</svg>'
    )
    key_svg = (
        f'<svg viewBox="0 0 {W} {BAND}" width="{W}" height="{BAND}" aria-hidden="true" style="display: block">'
        f'<defs>{key_defs}</defs>{bod}</svg>'
    )

    step = (xm - M) / 10
    ticks, x, i = [], float(M), 0
    while x <= W:
        ticks.append(f'<line x1="{x:.2f}" y1="{ruler}" x2="{x:.2f}" y2="{ruler + (7 if i % 5 == 0 else 4)}"></line>')
        x += step
        i += 1
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"
    sweep = f"; animation: sweep 1900ms linear {at(320)} both"
    ride = f"; animation: travel 1900ms linear {at(320)} both"
    pen = f"offset-path: path('{d}'); offset-distance: 100%; offset-rotate: 0deg"

    if day:
        under = (f'<path d="{d}" fill="none" stroke="{t["ground"]}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
                 f'style="{SWEEP_DASH}{sweep}"></path>')
        pen_under = f'<circle r="6.5" fill="{t["ground"]}" style="{pen}{ride}"></circle>'
    else:
        under = (f'<path d="{d}" fill="none" stroke="{t["ground"]}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
                 f'style="{SWEEP_DASH}{sweep}"></path>'
                 f'<path d="{d}" fill="none" stroke="{t["live"]}" stroke-width="7" stroke-opacity="0.22" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
                 f'style="{SWEEP_DASH}{sweep}"></path>')
        pen_under = (f'<circle r="8.5" fill="{t["ground"]}" style="{pen}{ride}"></circle>'
                     f'<circle r="8.5" fill="{t["live"]}" fill-opacity="0.24" style="{pen}{ride}"></circle>')

    live_svg = (
        f'<svg viewBox="0 0 {W} {PH}" width="{W}" height="{PH}" role="img" '
        f'aria-label="Illustration of the signal: a wave that rises in pitch from 35 hertz to 250 hertz over about 0.2 seconds, then dies away" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<defs><clipPath id="{pid}rail"><rect x="0" y="{ruler - 0.5}" width="{W}" height="8"></rect></clipPath></defs>'
        f'{under}'
        f'<path d="{d}" fill="none" stroke="{t["live"]}" stroke-width="{1.9 if day else 1.6}" stroke-linejoin="round" stroke-linecap="round" pathLength="1" '
        f'style="{SWEEP_DASH}{sweep}"></path>'
        f'<g stroke="{t["text"]}" stroke-width="0.9" fill="none">'
        f'<line x1="{M}" y1="{ruler}" x2="{W}" y2="{ruler}"></line>{"".join(ticks)}'
        f'</g>'
        f'<g clip-path="url(#{pid}rail)"><g style="{pen}{ride}"><line x1="0" y1="-400" x2="0" y2="400" stroke="{t["text"]}" stroke-width="9"></line></g></g>'
        f'<g fill="{t["text"]}" style="{lab}">'
        f'<text x="{M}" y="{ruler + 20}">0</text>'
        f'<text x="{(M + xm) / 2:.1f}" y="{ruler + 20}" text-anchor="middle">0.1</text>'
        f'<text x="{xm:.1f}" y="{ruler + 20}" text-anchor="middle">0.2 s</text>'
        f'</g>'
        f'{pen_under}'
        f'<circle r="{3.6 if day else 3.4}" fill="{t["live"]}" style="{pen}; animation: travel 1900ms linear {at(320)} both, pulse 2400ms ease-in-out {at(2400)} infinite"></circle>'
        f'</svg>'
    )
    reg_a = f"animation: registerA 480ms {REGISTER} {at(60)} both"
    reg_b = f"animation: registerB 480ms {REGISTER} {at(60)} both"
    ink = f"animation: inkproof 520ms {PRESS} {at(60)} both"
    return (
        f'<div style="position: relative; width: {W}px; height: {PH}px; margin-top: 12px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {BAND}px; {ink}">'
        f'<div style="position: absolute; left: 0; top: 0; {reg_a}">{blue_svg}</div>'
        f'<div style="position: absolute; left: 0; top: 0; {reg_b}">{key_svg}</div>'
        f'</div>'
        f'{live_svg}'
        f'</div>'
    )


def screen(theme):
    t = T(theme)
    day = t["day"]
    c, g = t["text"], t["ground"]
    hw = 800 if day else 900
    iw = 300 if day else 400
    press = lambda i: f"display: block; animation: press 190ms {PRESS} {at(i * 50)} both"
    it = disp(44, weight=iw, stretch=100 if day else 87.5, lh=0.98, ls=-0.012, italic=True)
    rule_a = f'<div style="height: 3px; background-color: {c}"></div><div style="height: 0.75px; background-color: {c}; margin-top: 2px"></div>'
    return f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {g}; color: {c}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 8px {M}px 0; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 10px">
<div style="{disp(33, weight=hw, lh=1)}; padding-bottom: 4px">Paper<span style="{disp(33, weight=iw, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: {t["live"]}; margin-left: 3px"></span></div>
<div style="margin-left: auto; text-align: right; {mono(LAB, color=t["muted"], ls=0.06)}; line-height: 1.35">Science and math,<br>newly released</div>
<button type="button" aria-label="Switch to {'night' if day else 'day'} theme" style="width: 44px; height: 44px; margin-right: -11px; background-color: transparent; border: 0; color: {c}; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0">{THEME}</button>
</div>
{rule_a}
</header>

<main style="display: flex; flex-direction: column; flex-grow: 1">
<article style="display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Physics", c)}{tag_solid("Peer-reviewed", c, g)}
{source("Physical Review Letters", c)}
</div>
<h2 style="margin: 0; padding: 10px {M}px 0; {disp(44, weight=hw, lh=0.98)}">
<span style="{press(0)}">Two black holes</span>
<span style="{press(1)}">merged. <span style="{it}">Earth felt</span></span>
<span style="{press(2)}; {it}">space stretch.</span>
</h2>
{plate("lp" + theme[0], theme)}
<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px {M}px 0">
<div style="display: flex; flex-direction: column; gap: 3px">
<div style="{disp(44, weight=hw, lh=1, color=c)}; font-variant-numeric: lining-nums">1.0 × 10<sup style="{SUP}">−21</sup></div>
<div style="{mono(LAB, color=t["muted"], ls=0.06)}">Peak strain. Pitch 35 to 250 Hz</div>
</div>
<div style="text-align: right; {mono(LAB, color=t["muted"], ls=0.06)}; line-height: 1.4">Plate 1<br>Illustration,<br>not to scale</div>
</div>
<p style="margin: 0; padding: 10px {M}px 0; {text(16, lh=1.42)}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>
<div style="display: flex; flex-direction: column; gap: 8px; padding: 14px {M}px 0">
<a href="#explainer" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {c}; color: {g}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>See it explained</span>{ARROW}</a>
<div style="display: flex; gap: 8px">
{rate_btn(PLUS, "More like this", c)}
{rate_btn(MINUS, "Less like this", c)}
</div>
</div>
</article>

<div style="margin: 18px {M}px 0; height: 0.75px; background-color: {c}"></div>
<div style="margin: 2px {M}px 0; height: 3px; background-color: {c}"></div>

<article style="display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 6px; padding: 13px {M}px 0">
{tag_outline("Biology", c)}{tag_solid("Peer-reviewed", c, g)}
{source("Nature", c)}
</div>
</article>
</main>
</div>"""


def build(theme):
    c = INK if theme == "day" else NT
    css = (
        f"body{{margin:0}}\na{{color:{c}}}\n" + KEYFRAMES + "\n"
        "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
        "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
        + ink_keyframes("inkproof", W, BAND)
    )
    out = HERE / f"LockProof-{theme.capitalize()}{SUFFIX}.dc.html"
    out.write_text(page(f"Lock proof, First Light, {theme}", css, screen(theme), W, H))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build("day")
    build("night")
