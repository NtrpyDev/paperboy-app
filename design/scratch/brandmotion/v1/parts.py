"""Brand-Parts.dc.html: the color tokens with their checked contrast, the eleven type cuts, the icon set.
1200 by 900. Contrast figures are WCAG 2 ratios from scratch/director/lock_contrast.py, rerun 2026-11-13.

  python3 parts.py
"""
from bm import *

W, H = 1200, 900
M = 48
LC = 500          # left column width
SW, SH = 76, 34   # swatch


def sw_solid(fill, border=None):
    b = f"; border: 0.9px solid {border}" if border else ""
    return f'<div style="width: {SW}px; height: {SH}px; box-sizing: border-box; background-color: {fill}{b}; flex: none"></div>'


def sw_screen(pid, ink, ground, outline, night=False):
    """Plate ink is never a flat flood, so its swatch is the three screen tones."""
    w3 = SW / 3
    rects = "".join(f'<rect x="{i * w3:.2f}" y="0" width="{w3:.2f}" height="{SH}" fill="url(#{pid}{n})"></rect>' for i, n in enumerate(("a1", "a2", "a3")))
    return (f'<svg width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" aria-hidden="true" style="display: block; flex: none"><defs>{patterns(pid, ink)}</defs>'
            f'<rect width="{SW}" height="{SH}" fill="{ground}"></rect>{rects}<rect x="0.45" y="0.45" width="{SW - 0.9}" height="{SH - 0.9}" fill="none" stroke="{outline}" stroke-width="0.9"></rect></svg>')


def sw_live(theme):
    """The live color only ever appears as the line and its pen point, so that is its swatch."""
    t = T(theme)
    y = SH / 2
    d = f"M0 {y}C14 {y} 14 {y - 9} 24 {y - 9}S34 {y + 9} 44 {y + 9}S52 {y} {SW - 12} {y}"
    halo = "" if t["day"] else (f'<path d="{d}" fill="none" stroke="{t["live"]}" stroke-width="7" stroke-opacity="0.22" stroke-linecap="round"></path>'
                                f'<circle cx="{SW - 12}" cy="{y}" r="8.5" fill="{t["live"]}" fill-opacity="0.24"></circle>')
    return (f'<svg width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" aria-hidden="true" style="display: block; flex: none">{halo}'
            f'<path d="{d}" fill="none" stroke="{t["live"]}" stroke-width="{1.9 if t["day"] else 1.6}" stroke-linecap="round"></path>'
            f'<circle cx="{SW - 12}" cy="{y}" r="{3.6 if t["day"] else 3.4}" fill="{t["live"]}"></circle></svg>')


def color_row(swatch, name, hexv, use, ratio, theme):
    t = T(theme)
    pad = 11 if t["day"] else 7
    r = (f'<div style="{disp(25, weight=t["hw"], lh=1)}; font-variant-numeric: lining-nums; white-space: nowrap">{ratio}<span style="{text(15, lh=1, italic=True)}; margin-left: 4px">: 1</span></div>'
         if ratio else f'<div style="{lab(t["muted"])}">the ground</div>')
    return (f'<div style="display: flex; align-items: center; gap: 14px; padding: {pad}px 0; border-top: 0.75px solid {t["text"]}">'
            f'{swatch}<div style="display: flex; flex-direction: column; gap: 2px; flex: 1 1 0; min-width: 0">'
            f'<div style="{lab(t["text"], 600)}">{name}<span style="font-weight: 500; margin-left: 10px">{hexv}</span></div>'
            f'<div style="{lab(t["muted"])}">{use}</div></div>{r}</div>')


def cut_row(code, specimen, spec, role, theme):
    t = T(theme)
    pad = 11 if t["day"] else 7
    return (f'<div style="display: flex; align-items: center; gap: 14px; padding: {pad}px 0 {pad + 1}px; border-top: 0.75px solid {t["text"]}">'
            f'<div style="{lab(t["text"], 600)}; width: 22px; flex: none">{code}</div>'
            f'<div style="flex: 1 1 0; min-width: 0; white-space: nowrap; color: {t["text"]}">{specimen}</div>'
            f'<div style="{lab(t["muted"])}; text-align: right; flex: none"><span style="color: {t["text"]}">{spec}</span><br>{role}</div></div>')


def icon_cell(svg, name, note):
    return (f'<div style="display: flex; flex-direction: column; gap: 8px; align-items: flex-start"><div style="height: 28px; display: flex; align-items: center; color: {INK}">{svg}</div>'
            f'<div style="{lab(INK, 600)}">{name}</div><div style="{lab(MUTED)}; margin-top: -6px">{note}</div></div>')


def build():
    D = lambda size, w, st, it=False, ls=-0.005: disp(size, weight=w, stretch=st, lh=1.05, ls=ls, italic=it)
    day_colors = (
        color_row(sw_solid(STOCK, INK), "Stock", "#E9E6DE", "The ground. Gray, not cream", "", "day")
        + color_row(sw_solid(INK), "Ink", "#16130F", "Text, rules, solid buttons and tags", "14.85", "day")
        + color_row(sw_solid(MUTED), "Ink-muted", "#5A554B", "Second-rank labels, grid lines", "5.94", "day")
        + color_row(sw_screen("pd", BLUE, STOCK, INK), "Plate", "#1F3FD0", "Print only: screens and engraved lines", "6.28", "day")
        + color_row(sw_live("day"), "Live", "#E0330A", "The live mark only. Never text", "3.62", "day")
    )
    night_colors = (
        color_row(sw_solid(NG, NS), "Ground", "#0E1116", "Blue-black, never neutral", "", "night")
        + color_row(sw_solid(NT), "Light", "#E9E4D7", "Text, rules, solid buttons and tags", "14.90", "night")
        + color_row(sw_solid(NM), "Light-muted", "#9C988D", "Second-rank labels, range screens", "6.56", "night")
        + color_row(sw_solid(NS), "Structure", "#5E6573", "Grid and drop lines in figures", "3.23", "night")
        + color_row(sw_solid(NX), "Texture", "#2B303B", "Decoration only. Carries no meaning", "1.43", "night")
        + color_row(sw_screen("pn", NBLUE, NG, NT), "Plate-night", "#4D63C9", "The plate light: rings and fills", "3.55", "night")
        + color_row(sw_live("night"), "Live-night", "#FFA63D", "The live mark only, core and halo", "9.70", "night")
    )
    day_cuts = (
        cut_row("D1", f'<span style="{D(30, 800, 62.5)}">Two black holes</span>', "Noto Serif Display 800, width 62.5", "Headlines, wordmark, numerals", "day")
        + cut_row("D3", f'<span style="{D(23, 700, 75, ls=0.005)}">See it explained</span>', "Noto Serif Display 700, width 75", "Button labels", "day")
        + cut_row("D4", f'<span style="{D(30, 300, 100, True, -0.012)}">space stretch.</span>', "Noto Serif Display 300 italic, width 100", "The second voice, the key idea", "day")
        + cut_row("T1", f'<span style="{text(17, lh=1.2)}">A ripple in spacetime.</span>', "Source Serif 4, 400", "Body text, summaries", "day")
        + cut_row("T2", f'<span style="{text(16, lh=1.2, weight=500)}">More like this</span>', "Source Serif 4, 500", "Rating labels", "day")
        + cut_row("T3", f'<span style="{text(15, lh=1.2, italic=True)}">† A wide error range.</span>', "Source Serif 4, 400 italic", "Notes, captions, units, links", "day")
        + cut_row("M1", f'<span style="{lab(INK)}">Peak strain. 35 to 250 Hz</span>', "Martian Mono 500, width 75", "Labels, axis labels, slugs of a picture", "day")
        + cut_row("M2", f'<span style="{lab(INK, 600)}">Key idea · Fig. 2 · Source</span>', "Martian Mono 600, width 75", "Tags, badges, section slugs", "day")
    )
    night_cuts = (
        cut_row("D2", f'<span style="{D(30, 900, 62.5)}">Two black holes</span>', "Noto Serif Display 900, width 62.5", "D1 on the night ground", "night")
        + cut_row("D5", f'<span style="{D(30, 400, 87.5, True, -0.012)}">space stretch.</span>', "400 italic, width 87.5", "D4 in a night headline, 30 px and up", "night")
        + cut_row("D5", f'<span style="{D(22, 400, 100, True, -0.012)}">two black holes merging.</span>', "400 italic, width 100", "D4 at night, and under 24 px by day", "night")
    )
    icons = "".join([
        icon_cell(ARROW, "Arrow", "20 px"), icon_cell(OUTARROW.replace('width="11" height="11"', 'width="15" height="15"'), "Out arrow", "11, 15 px"),
        icon_cell(PLUS, "Plus", "14 px"), icon_cell(MINUS, "Minus", "14 px"), icon_cell(THEME, "Theme", "22 px"),
    ])
    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 16px {M}px 0; display: flex; flex-direction: column">{double()}</header>

<section style="padding: 10px {M}px 0; display: flex; gap: 40px">
<div style="width: {LC}px; flex: none; display: flex; flex-direction: column">
{head("05", "Color, day", "Contrast on stock, WCAG 2", note="Inks on stock")}
<div style="margin-top: 10px; display: flex; flex-direction: column">{day_colors}</div>
<div style="border-top: 0.75px solid {INK}; padding-top: 14px; margin-top: 0">{head("07", "Icons", "Inline SVG, current color", note="1.5 px stroke, square ends")}</div>
<div style="margin-top: 14px; display: flex; justify-content: space-between; padding-right: 40px">{icons}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{head("06", "Type", "Three families, no other weight or width", note="Eleven cuts")}
<div style="margin-top: 10px; display: flex; flex-direction: column">{day_cuts}</div>
</div>
</section>

<section style="margin-top: auto; background-color: {NG}; color: {NT}; padding: 14px {M}px 16px; display: flex; gap: 40px">
<div style="width: {LC}px; flex: none; display: flex; flex-direction: column">
{head("05", "Color, night", "Contrast on ground, WCAG 2", NT, NM, note="Lights on ground")}
<div style="margin-top: 10px; display: flex; flex-direction: column">{night_colors}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{head("06", "Type, night", "One weight step up, so the hairlines hold", NT, NM)}
<div style="margin-top: 10px; display: flex; flex-direction: column">{night_cuts}</div>
<div style="border-top: 0.75px solid {NT}; padding-top: 14px; {D(44, 900, 62.5)}; line-height: 0.98">Two black holes merged. <span style="{D(44, 400, 87.5, True, -0.012)}; line-height: 0.98">Earth felt space stretch.</span></div>
<div style="margin-top: auto; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">Live against plate is 1.73 : 1 by day and 2.73 : 1 by night, so the line never touches plate ink. It always rides on a trap of the ground color.</div>
</div>
</section>
</div>"""
    css = "body{margin:0}\na{color:#16130F}"
    out = PROJECT / "Brand-Parts.dc.html"
    out.write_text(page("Paperboy brand: color, type, icons", css, body, W, H))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build()
