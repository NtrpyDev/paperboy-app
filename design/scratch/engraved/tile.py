"""Cand-x-System: the Engraved Broadsheet style tile, 1200 by 1700."""
import os
import pathlib
from lib import *

OUT = pathlib.Path(os.environ.get("PB_OUT") or pathlib.Path(__file__).resolve().parents[2] / "canvas" / "project" / "Cand-x-System.dc.html")
W, H = 1200, 1700
M = 56
RULE = f"0.75px solid {INK}"


def col(n):
    return n * (1088 - 11 * 24) / 12 + (n - 1) * 24


def slug(n, t, color=INK, sub=MUTED, note=""):
    extra = f'<span style="color: {sub}; margin-left: 14px">{note}</span>' if note else ""
    return f'<div style="{mono(9, color=color, weight=600)}"><span style="color: {sub}; margin-right: 10px">{n}</span>{t}{extra}</div>'


def spec(t, color=MUTED):
    return f'<div style="{mono(8.5, color=color)}">{t}</div>'


# ---------------------------------------------------------------- swatches
def chip(fill, name, hexv, role, w, text_c=INK, sub_c=MUTED, border=None, h=46):
    b = f"border: 0.75px solid {border}; " if border else ""
    return (
        f'<div style="display: flex; flex-direction: column; gap: 7px; width: {w}px">'
        f'<div style="height: {h}px; box-sizing: border-box; {b}background-color: {fill}"></div>'
        f'<div style="display: flex; flex-direction: column; gap: 2px">'
        f'<div style="{text(14, lh=1.15, weight=600, color=text_c)}">{name}</div>'
        f'<div style="{mono(8.5, color=text_c)}">{hexv}</div>'
        f'<div style="{mono(8.5, color=sub_c, ls=0.05)}; line-height: 1.4; white-space: nowrap">{role}</div>'
        f'</div></div>'
    )


def screen_chip(pid, layers, name, role, w, ink=INK, text_c=INK, sub_c=MUTED, h=46):
    rects = "".join(f'<rect width="{w}" height="{h}" fill="url(#{pid}{l})"></rect>' for l in layers)
    return (
        f'<div style="display: flex; flex-direction: column; gap: 7px; width: {w}px">'
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true" style="display: block"><defs>{patterns(pid, ink)}</defs>{rects}</svg>'
        f'<div style="display: flex; flex-direction: column; gap: 2px">'
        f'<div style="{text(14, lh=1.15, weight=600, color=text_c)}">{name}</div>'
        f'<div style="{mono(8.5, color=sub_c, ls=0.05)}; line-height: 1.4; white-space: nowrap">{role}</div>'
        f'</div></div>'
    )


# ---------------------------------------------------------------- M87 plate
def plate_m87(pid="xm", PW=496, SH=300, R=88):
    cx, cy = 276, SH / 2
    tones = {"h1": (A2, 0.2), "h2": (A2, 0.42), "h3": (A2, 0.66), "c2": (A1, 0.38), "c3": (A1, 0.6)}
    defs = patterns(pid, INK, pitch=3.2, tones=tones)

    def disc(r, fill):
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"></circle>'

    sky = (
        f'<rect width="{PW}" height="{SH}" fill="url(#{pid}h3)"></rect>'
        f'{disc(R + 132, STOCK)}{disc(R + 132, f"url(#{pid}h2)")}'
        f'{disc(R + 66, STOCK)}{disc(R + 66, f"url(#{pid}h1)")}'
        f'{disc(R + 24, STOCK)}'
        f'{disc(R - 20, f"url(#{pid}h1)")}'
        f'{disc(R - 34, f"url(#{pid}h2)")}{disc(R - 34, f"url(#{pid}c2)")}'
        f'{disc(R - 50, STOCK)}{disc(R - 50, f"url(#{pid}h3)")}{disc(R - 50, f"url(#{pid}c3)")}'
    )
    print_svg = f'<svg viewBox="0 0 {PW} {SH}" width="{PW}" height="{SH}" aria-hidden="true" style="display: block"><defs>{defs}</defs>{sky}</svg>'
    by = SH + 20
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: 9px; font-weight: 500; letter-spacing: 0.06em"
    live_svg = (
        f'<svg viewBox="0 0 {PW} {SH + 44}" width="{PW}" height="{SH + 44}" role="img" '
        f'aria-label="Illustration of the bright ring around the black hole in galaxy M87, with a scale bar showing the ring is 42 microarcseconds across" '
        f'style="position: absolute; left: 0; top: 0">'
        f'<g stroke="{INK}" stroke-width="0.75" fill="none">'
        f'<line x1="{cx - R}" y1="{by}" x2="{cx + R}" y2="{by}"></line>'
        f'<line x1="{cx - R}" y1="{SH + 6}" x2="{cx - R}" y2="{by + 5}"></line>'
        f'<line x1="{cx + R}" y1="{SH + 6}" x2="{cx + R}" y2="{by + 5}"></line>'
        f'</g>'
        f'<text x="{cx}" y="{by + 17}" text-anchor="middle" fill="{INK}" style="{lab}">42 microarcseconds</text>'
        f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{LIVE}" stroke-width="1.9" pathLength="1" transform="rotate(-90 {cx} {cy})" '
        f'style="{SWEEP_DASH}; animation: sweep 1800ms linear {at(380)} both"></circle>'
        f'<g style="transform-origin: {cx}px {cy}px; animation: orbit 1800ms linear {at(380)} both">'
        f'<circle cx="{cx}" cy="{cy - R}" r="3.8" fill="{LIVE}" style="animation: pulse 2400ms ease-in-out {at(2400)} infinite"></circle></g>'
        f'</svg>'
    )
    return (
        f'<div style="position: relative; width: {PW}px; height: {SH + 44}px">'
        f'<div style="position: absolute; left: 0; top: 0; width: {PW}px; height: {SH}px; animation: register 500ms {REGISTER} {at(120)} both">'
        f'<div style="width: {PW}px; height: {SH}px; animation: inkm87 560ms {PRESS} {at(120)} both">{print_svg}</div></div>'
        f'{live_svg}'
        f'<div style="position: absolute; left: 0; top: {SH + 12}px; {mono(9)}; line-height: 1.45">Plate 3<br>Illustration, not to scale</div>'
        f'</div>'
    )


# ---------------------------------------------------------------- chart
def chart_mass(pid="xc", CW=532):
    x0, s = 62, 4.2
    X = lambda v: x0 + v * s
    axis = 148
    b1, b2, bh = 28, 86, 20
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: 9px; font-weight: 500; letter-spacing: 0.06em"
    num = f"font-family: {DISP}; font-stretch: 62.5%; font-weight: 800; font-size: 25px; font-variant-numeric: lining-nums"
    ticks = "".join(
        f'<line x1="{X(v):.1f}" y1="{axis}" x2="{X(v):.1f}" y2="{axis + (6 if v % 10 == 0 else 3.5)}"></line>' for v in range(0, 71, 5)
    )
    tlabels = "".join(f'<text x="{X(v):.1f}" y="{axis + 18}" text-anchor="middle">{v}</text>' for v in range(0, 71, 10))
    drops = "".join(
        f'<line x1="{X(v):.1f}" y1="{y}" x2="{X(v):.1f}" y2="{axis}"></line>' for v, y in ((62, b2 + bh), (65, b2 + bh))
    )

    def bar(v0, v1, y, fills):
        r = "".join(f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="{f}"></rect>' for f in fills)
        return r + f'<rect x="{X(v0):.1f}" y="{y}" width="{(v1 - v0) * s:.1f}" height="{bh}" fill="none" stroke="{INK}" stroke-width="0.9"></rect>'

    return (
        f'<svg viewBox="0 0 {CW} 176" width="{CW}" height="176" role="img" '
        f'aria-label="Chart of mass in solar masses. Before: two black holes of about 36 and 29. After: one black hole of about 62, and about 3 that left as gravitational waves." style="display: block">'
        f'<defs>{patterns(pid, INK)}</defs>'
        f'<g stroke="{MUTED}" stroke-width="0.6" fill="none">{drops}</g>'
        f'{bar(0, 36, b1, [f"url(#{pid}a2)"])}{bar(36, 65, b1, [f"url(#{pid}b2)"])}'
        f'{bar(0, 62, b2, [f"url(#{pid}a2)", f"url(#{pid}b2)"])}'
        f'<rect x="{X(62):.1f}" y="{b2}" width="{3 * s:.1f}" height="{bh}" fill="{LIVE}"></rect>'
        f'<g stroke="{INK}" stroke-width="0.75" fill="none"><line x1="{x0}" y1="{axis}" x2="{X(70):.1f}" y2="{axis}"></line>{ticks}'
        f'<path d="M{X(65) + 3:.1f} {b2 + bh / 2}H{X(65) + 22:.1f}"></path></g>'
        f'<g fill="{INK}" style="{lab}">{tlabels}'
        f'<text x="0" y="{b1 + 14}">BEFORE</text><text x="0" y="{b2 + 14}">AFTER</text>'
        f'<text x="{X(70) + 14:.1f}" y="{axis + 18}">SOLAR MASSES</text>'
        f'<text x="{X(65) + 50:.1f}" y="{b2 + 8}">LEFT AS</text><text x="{X(65) + 50:.1f}" y="{b2 + 20}">GRAVITATIONAL WAVES</text>'
        f'<text x="{X(65) + 14:.1f}" y="{b1 + 14}">TWO BLACK HOLES</text>'
        f'</g>'
        f'<g fill="{INK}" style="{num}">'
        f'<text x="{X(18):.1f}" y="{b1 - 7}" text-anchor="middle">36</text><text x="{X(50.5):.1f}" y="{b1 - 7}" text-anchor="middle">29</text>'
        f'<text x="{X(31):.1f}" y="{b2 - 7}" text-anchor="middle">62</text>'
        f'<text x="{X(65) + 28:.1f}" y="{b2 + 19}">3</text>'
        f'</g>'
        f'</svg>'
    )


# ---------------------------------------------------------------- analogy
def analogy(pid="xa", AW=254):
    x0, s, ry = 6, 78, 146
    X = lambda v: x0 + v * s
    r = 0.7 * s
    ccx, ccy = X(0.7), ry - r - 5
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: 8.5px; font-weight: 500; letter-spacing: 0.06em"
    ticks = "".join(
        f'<line x1="{X(i / 5):.1f}" y1="{ry}" x2="{X(i / 5):.1f}" y2="{ry + (6 if i % 5 == 0 else 3.5)}"></line>' for i in range(0, 16)
    )
    tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 18}" text-anchor="middle">{v if v == 0 else str(v) + " Å"}</text>' for v in range(0, 4))
    y1, y2 = 18, 4

    def beam(v, y):
        return (
            f'<line x1="{x0}" y1="{y}" x2="{X(v):.1f}" y2="{y}"></line>'
            f'<line x1="{x0}" y1="{y - 4}" x2="{x0}" y2="{y + 4}"></line>'
            f'<line x1="{X(v):.1f}" y1="{y - 4}" x2="{X(v):.1f}" y2="{y + 4}"></line>'
        )

    return (
        f'<svg viewBox="0 0 {AW} 168" width="{AW}" height="168" role="img" '
        f'aria-label="Drawing to scale on a ruler in angstroms: a carbon atom about 1.4 wide, AlphaFold median error 0.96, next best method 2.8" style="display: block">'
        f'<defs>{patterns(pid, INK)}</defs>'
        f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r:.1f}" fill="url(#{pid}a1)"></circle>'
        f'<g stroke="{MUTED}" stroke-width="0.6" fill="none">'
        f'<line x1="{X(0.96):.1f}" y1="{y2 + 6}" x2="{X(0.96):.1f}" y2="{ry}"></line>'
        f'<line x1="{X(2.8):.1f}" y1="{y1 + 6}" x2="{X(2.8):.1f}" y2="{ry}"></line>'
        f'</g>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none">'
        f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r:.1f}"></circle>'
        f'<line x1="{x0}" y1="{ry}" x2="{X(3):.1f}" y2="{ry}"></line>{ticks}'
        f'</g>'
        f'<g stroke="{INK}" stroke-width="1.4" fill="none">{beam(2.8, y1 + 12)}{beam(0.96, y2 + 2)}</g>'
        f'<g fill="{INK}" style="{lab}">{tl}'
        f'<text x="{X(0.96) + 8:.1f}" y="{y2 + 5}">ALPHAFOLD, 0.96 Å</text>'
        f'<text x="{X(1.4) + 10:.1f}" y="{y1 + 27}">NEXT BEST, 2.8 Å</text>'
        f'<text x="{X(1.4) + 10:.1f}" y="{ccy + 6:.1f}">CARBON ATOM,</text><text x="{X(1.4) + 10:.1f}" y="{ccy + 18:.1f}">ABOUT 1.4 Å WIDE</text>'
        f'</g>'
        f'</svg>'
    )


# ---------------------------------------------------------------- tags and controls
def tag_outline(t, c=INK):
    return f'<span style="{mono(9, color=c, weight=600)}; border: 1px solid {c}; padding: 5px 7px 4px">{t}</span>'


def tag_solid(t, bg=INK, fg=STOCK):
    return f'<span style="{mono(9, color=fg, weight=600)}; background-color: {bg}; border: 1px solid {bg}; padding: 5px 7px 4px">{t}</span>'


def tag_screen(t, c=INK, ground=STOCK):
    hatch = f"repeating-linear-gradient(135deg, {c} 0 1.1px, transparent 1.1px 3.2px)"
    return (
        f'<span style="display: inline-flex; padding: 3.5px; background-image: {hatch}">'
        f'<span style="{mono(9, color=c, weight=600)}; background-color: {ground}; padding: 2.5px 5px 1.5px">{t}</span></span>'
    )


def btn_primary(label, bg=INK, fg=STOCK, w=None):
    ws = f"width: {w}px; " if w else ""
    return (
        f'<a href="#explainer" style="{ws}min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
        f'padding: 0 14px 0 16px; background-color: {bg}; color: {fg}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{ARROW}</a>'
    )


def btn_rate(icon, label, c=INK, on=False, ground=STOCK):
    bg, fg = (c, ground) if on else ("transparent", c)
    pressed = ' aria-pressed="true"' if on else ""
    return (
        f'<button type="button"{pressed} style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; '
        f'border: 1px solid {c}; border-radius: 0; color: {fg}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">'
        f'{icon}<span style="{text(15, lh=1, weight=500)}">{label}</span></button>'
    )


def build():
    it = lambda size, w=300, st=100: disp(size, weight=w, stretch=st, lh=0.98, ls=-0.012, italic=True)
    press = lambda i: f"display: block; animation: press 200ms {PRESS} {at(i * 55)} both"
    cw = 136

    day_bar = "".join([
        chip(STOCK, "Stock", "#E9E6DE", "Ground, gray not cream", cw, border=INK, h=34),
        chip(INK, "Ink", "#16130F", "Text and print, 14.9 : 1", cw, h=34),
        chip(MUTED, "Muted ink", "#5A554B", "Second rank, 5.9 : 1", cw, h=34),
        chip(LIVE, "Vermilion", "#E0330A", "Live line only, 3.6 : 1", cw, h=34),
        screen_chip("xs1", ["a1"], "Screen, light", "A quarter of the pitch", cw, h=34),
        screen_chip("xs2", ["a2"], "Screen, mid", "Half of the pitch", cw, h=34),
        screen_chip("xs3", ["a3"], "Screen, heavy", "Two thirds of the pitch", cw, h=34),
        screen_chip("xs4", ["a2", "b2"], "Weave", "Two screens, 60° apart", cw, h=34),
    ])

    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 24px {M}px 0; display: flex; flex-direction: column">
<div style="display: flex; justify-content: space-between; align-items: baseline">
<span style="{mono(9, weight=600)}">Paperboy design language</span>
<span style="{mono(9, color=MUTED)}">Angle x · Engraved Broadsheet · style tile</span>
</div>
<div style="display: flex; align-items: flex-end; justify-content: space-between; margin-top: 6px">
<div style="{disp(150, weight=800, lh=1, ls=-0.012)}; padding-bottom: 22px">Paper<span style="{disp(150, weight=300, stretch=100, lh=1, ls=-0.025, italic=True)}">boy</span><span style="display: inline-block; width: 22px; height: 22px; border-radius: 50%; background-color: {LIVE}; margin-left: 10px"></span></div>
<div style="width: {col(4):.0f}px; display: flex; flex-direction: column; gap: 9px; padding-bottom: 26px">
{slug("01", "Wordmark")}
<div style="{text(15, lh=1.42)}; text-wrap: pretty">Two voices of one family: a heavy condensed roman and a light italic. The dot is the pen point of the live line, and the only color in the mark.</div>
<div style="display: flex; align-items: baseline; gap: 26px; margin-top: 2px">
<div style="{disp(38, weight=800, lh=1)}">Paper<span style="{disp(38, weight=300, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 6.5px; height: 6.5px; border-radius: 50%; background-color: {LIVE}; margin-left: 3px"></span></div>
<div style="{disp(22, weight=800, lh=1)}">Paper<span style="{disp(22, weight=400, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: {LIVE}; margin-left: 2px"></span></div>
</div>
</div>
</div>
<div style="height: 4px; background-color: {INK}"></div>
<div style="height: 0.75px; background-color: {INK}; margin-top: 3px"></div>
</header>

<section style="padding: 12px {M}px 0; display: flex; flex-direction: column; gap: 10px">
{slug("02", "Day palette", note="One hot ink. Tone comes from line screens, never from gray.")}
<div style="display: flex; justify-content: space-between">{day_bar}</div>
</section>

<div style="margin: 12px {M}px 0; border-top: {RULE}"></div>
<section style="margin: 0 0 0 {M}px; padding-top: 12px; display: flex; gap: 24px">
<div style="width: {col(7):.0f}px; flex: none; display: flex; flex-direction: column">
{slug("03", "Type", note="Noto Serif Display, Source Serif 4, Martian Mono")}
<div style="margin-top: 10px; {disp(66, lh=0.95)}">
<span style="{press(0)}">Two black holes</span>
<span style="{press(1)}">merged. <span style="{it(66)}">Earth felt</span></span>
<span style="{press(2)}; {it(66)}">space stretch.</span>
</div>
<div style="margin-top: 8px">{spec("Display · 66 / 63 · Noto Serif Display 800 at width 62.5, then 300 italic at width 100")}</div>
<div style="margin-top: 14px; {disp(44, lh=0.98)}">The first picture of<br><span style="{it(44)}">a black hole's shadow.</span></div>
<div style="margin-top: 8px">{spec("Headline · 44 / 43 · sentence case, never all caps · the last clause turns italic")}</div>
<div style="display: flex; gap: 24px; margin-top: 14px">
<div style="width: {col(4):.0f}px; flex: none; display: flex; flex-direction: column; gap: 8px">
<p style="margin: 0; {text(17, lh=1.45)}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. <em>Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</em></p>
{spec("Body · 17 / 25 · Source Serif 4, roman and italic")}
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 6px">
<div style="{disp(48, lh=1)}; font-variant-numeric: lining-nums; white-space: nowrap">1.0 × 10<sup style="{SUP}">−21</sup></div>
<div style="{disp(48, lh=1.04)}; font-variant-numeric: lining-nums; white-space: nowrap">36 + 29<span style="margin-left: 18px">5.1</span><span style="{it(34, 400)}; margin-left: 3px">σ</span></div>
<div style="margin-top: 2px">{spec("Numerals · 48 · lining, real × and −")}</div>
<div style="{mono(8.5, weight=600)}">Label · 8.5 to 9.5 · Martian Mono, width 75</div>
</div>
</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{slug("04", "Hero plate", note="Print is still. One line moves.")}
<div style="margin-top: 12px">{plate_m87()}</div>
<div style="display: flex; align-items: flex-end; gap: 16px; margin-top: 6px; padding-right: {M}px">
<div style="{disp(88, lh=0.84)}; font-variant-numeric: lining-nums">42</div>
<div style="display: flex; flex-direction: column; gap: 5px; padding-bottom: 2px">
<div style="{mono(9, weight=600)}">Microarcseconds across</div>
<div style="{text(15, lh=1.3, italic=True)}; text-wrap: pretty">The bright ring around the black hole in galaxy M87, about 55 million light years away.</div>
</div>
</div>
</div>
</section>

<section style="margin: 12px {M}px 0; padding-top: 12px; border-top: {RULE}; display: flex; flex-direction: column">
{slug("05", "Key idea, caveat, analogy", note="Three forms. None is a box, and nothing sits on a side edge.")}
<div style="display: flex; gap: 24px; margin-top: 16px">
<div style="width: {col(5):.0f}px; flex: none; display: flex; flex-direction: column">
<div style="{mono(9, weight=600)}">Key idea</div>
<div style="margin-top: 12px; {disp(40, weight=300, stretch=100, lh=1.04, ls=-0.012, italic=True)}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</div>
</div>
<div style="width: {col(4):.0f}px; flex: none; display: flex; flex-direction: column">
<p style="margin: 0; {text(17, lh=1.45)}; text-wrap: pretty">The merger happened about 410 megaparsecs away, roughly 1.3 billion light years.† The signal reached Livingston about 7 milliseconds before Hanford.</p>
<div style="width: 64px; height: 0.75px; background-color: {INK}; margin-top: 14px"></div>
<p style="margin: 9px 0 0; {text(15, lh=1.42, italic=True)}; text-wrap: pretty">† The distance carries a wide error range, roughly 230 to 570 megaparsecs. The sky position was known only to within about 600 square degrees.</p>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{analogy()}
<div style="margin-top: 6px; {mono(8.5, color=MUTED)}">Illustration, drawn to scale</div>
<p style="margin: 6px 0 0; {text(15, lh=1.36, italic=True)}; text-wrap: pretty">AlphaFold's typical error is smaller than a single carbon atom.</p>
</div>
</div>
</section>

<section style="margin: 12px {M}px 0; padding-top: 12px; border-top: {RULE}; display: flex; gap: 24px">
<div style="width: {col(6):.0f}px; flex: none; display: flex; flex-direction: column">
{slug("06", "Chart", note="Fig. 1 · Data, from the paper")}
<div style="margin-top: 10px; display: flex; align-items: baseline; justify-content: space-between">
<div style="{disp(30, lh=1)}">Where the mass went</div>
<div style="display: flex; align-items: center; gap: 7px; {mono(8.5, color=MUTED)}">
<svg width="22" height="9" viewBox="0 0 22 9" aria-hidden="true"><defs>{patterns("xk", INK)}</defs><rect width="22" height="9" fill="url(#xka2)"></rect><rect x="0.4" y="0.4" width="21.2" height="8.2" fill="none" stroke="{INK}" stroke-width="0.8"></rect></svg>
<span>An estimate</span>
<span style="display: inline-block; width: 22px; height: 9px; background-color: {LIVE}; margin-left: 10px"></span>
<span>Left as waves</span>
</div>
</div>
<div style="margin-top: 10px">{chart_mass()}</div>
</div>
<div style="width: {col(3):.0f}px; flex: none; display: flex; flex-direction: column">
{slug("07", "Tags and badges")}
<div style="margin-top: 14px; display: flex; flex-wrap: wrap; gap: 6px">{tag_outline("Physics")}{tag_outline("Biology")}{tag_outline("Space")}</div>
<div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center">{tag_solid("Peer-reviewed")}{tag_screen("Preprint")}</div>
<div style="margin-top: 9px">{spec("Solid means reviewed.<br>Screened means not yet.")}</div>
<div style="margin-top: 18px; display: flex; gap: 6px; align-items: center">{tag_outline("Physics")}{tag_screen("Preprint")}</div>
<div style="margin-top: 9px; {disp(31, lh=1)}; white-space: nowrap">[PREPRINT TITLE]</div>
<div style="margin-top: 6px; {text(15.5, lh=1.4)}">[ONE LINE SUMMARY]</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{slug("08", "Controls")}
<div style="margin-top: 14px">{btn_primary("See it explained")}</div>
<div style="margin-top: 8px; display: flex; flex-direction: column; gap: 8px">
{btn_rate(PLUS, "More like this")}
{btn_rate(MINUS, "Less like this")}
{btn_rate(PLUS, "More like this", on=True)}
</div>
<div style="margin-top: 8px">{spec("Rest, rest, and stamped. Square corners.")}</div>
</div>
</section>

<section style="margin-top: auto; flex: none; height: 268px; background-color: {NG}; color: {NT}; display: flex; overflow: hidden">
<div style="width: 440px; flex: none">{plate_gw("xn", theme="night", W=440, band=134, animate=False, margin_top=0)}</div>
<div style="flex: 1 1 0; padding: 26px {M}px 0 40px; display: flex; flex-direction: column">
{slug("09", "Night, the light table", color=NT, sub=NM, note="Designed, not inverted. The line carries the picture.")}
<div style="display: flex; gap: 28px; margin-top: 20px">
<div style="width: 340px; flex: none; display: flex; flex-direction: column">
<div style="{disp(33, weight=900, lh=1)}; white-space: nowrap">Two black holes merged.<br><span style="{it(33, 400, 87.5)}">Earth felt space stretch.</span></div>
<div style="margin-top: 16px; display: flex; gap: 6px; align-items: center">{tag_outline("Physics", NT)}{tag_solid("Peer-reviewed", NT, NG)}{tag_screen("Preprint", NT, NG)}</div>
<div style="margin-top: 16px; display: flex; gap: 8px">{btn_rate(PLUS, "More like this", NT, ground=NG)}{btn_rate(MINUS, "Less like this", NT, on=True, ground=NG)}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between">{chip(NG, "Ground", "#0E1116", "Blue-black", 86, NT, NM, border=NS, h=30)}{chip(NT, "Text", "#E9E4D7", "14.9 : 1", 86, NT, NM, h=30)}{chip(NM, "Muted", "#9C988D", "6.6 : 1", 86, NT, NM, h=30)}</div>
<div style="display: flex; justify-content: space-between">{chip(NS, "Structure", "#5E6573", "Print, 3.2 : 1", 86, NT, NM, h=30)}{chip(NX, "Texture", "#2B303B", "Decoration", 86, NT, NM, h=30)}{chip(AMBER, "Amber", "#FFA63D", "Live, 9.7 : 1", 86, NT, NM, h=30)}</div>
</div>
</div>
</div>
</section>
</div>"""
    css = (
        "body{margin:0}\na{color:#16130F}a:hover{color:#5A554B}\n" + KEYFRAMES + "\n"
        + ink_keyframes("inkm87", 496, 300)
    )
    OUT.write_text(page("Style tile, Engraved Broadsheet", css, body, W, H))
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
