"""Brand.dc.html: the Paperboy wordmark and app icon. 1200 by 900.

  python3 brand.py

Sources for the launcher sizes (read 2026-11-13):
  developer.android.com/develop/ui/views/launch/icon_design_adaptive
    "Size all layers to 108x108 dp."
    "Use a logo that's at least 48x48 dp. It must not exceed 66x66 dp, because the inner 66x66 dp
     of the icon appears within the masked viewport."
    "The outer 18 dp on each of the four sides of the layers is reserved for masking and to create
     visual effects such as parallax or pulsing."
    The <monochrome> layer of <adaptive-icon> is the one a launcher tints for themed icons.
  developer.android.com/training/multiscreen/screendensities
    A 48 px mdpi bitmap is 72 px at hdpi, 96 at xhdpi, 144 at xxhdpi, 192 at xxxhdpi.
"""
from bm import *

W, H = 1200, 900
M = 48
S = 116                      # type size of the construction drawing


def construction():
    marks, m = wm_outline(S)
    x = m["xh"]                       # the clear space unit
    asc, desc = m["asc"], m["desc"]
    iw, ih = m["width"], asc + desc   # the mark's own box
    fw, fh = iw + 2 * x, ih + 2 * x   # the clear space
    base = x + asc
    B = 14                            # band of print outside the clear space
    LW = 100                          # label column on the right
    BH = 28                           # labels under the figure
    pid = "cs"
    band = f"M{-B} {-B}H{fw + B:.1f}V{fh + B:.1f}H{-B}ZM0 0V{fh:.1f}H{fw:.1f}V0Z"
    guides = ""
    for name, y in (("CAP LINE", base - m["cap"]), ("X-HEIGHT", base - m["xh"]), ("BASELINE", base)):
        guides += f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{fw + B + 6:.1f}" y2="{y:.1f}" stroke="{MUTED}" stroke-width="0.6"></line>'
        guides += f'<text x="{fw + B + 12:.1f}" y="{y + 3.6:.1f}" fill="{INK}" style="{SVGLAB}">{name}</text>'

    def bar_v(xx, y0, y1):
        return (f'<line x1="{xx:.1f}" y1="{y0:.1f}" x2="{xx:.1f}" y2="{y1:.1f}"></line><line x1="{xx - 5:.1f}" y1="{y0:.1f}" x2="{xx + 5:.1f}" y2="{y0:.1f}"></line>'
                f'<line x1="{xx - 5:.1f}" y1="{y1:.1f}" x2="{xx + 5:.1f}" y2="{y1:.1f}"></line>')

    def bar_h(yy, x0, x1):
        return (f'<line x1="{x0:.1f}" y1="{yy:.1f}" x2="{x1:.1f}" y2="{yy:.1f}"></line><line x1="{x0:.1f}" y1="{yy - 5:.1f}" x2="{x0:.1f}" y2="{yy + 5:.1f}"></line>'
                f'<line x1="{x1:.1f}" y1="{yy - 5:.1f}" x2="{x1:.1f}" y2="{yy + 5:.1f}"></line>')

    xl = f"font-family: {TEXT}; font-size: 15px; font-style: italic"
    mid = base - m["cap"] / 2
    vx = x + m["paper_w"] * 0.62
    bars = bar_h(mid, 0, x) + bar_h(base - m["dot"] / 2, x + iw, fw) + bar_v(vx, 0, x) + bar_v(vx, x + ih, fh)
    xs = (f'<text x="{x / 2:.1f}" y="{mid - 8:.1f}" text-anchor="middle">x</text>'
          f'<text x="{x + iw + x / 2:.1f}" y="{base - m["dot"] / 2 - 8:.1f}" text-anchor="middle">x</text>'
          f'<text x="{vx + 10:.1f}" y="{x / 2 + 4:.1f}">x</text>'
          f'<text x="{vx + 10:.1f}" y="{x + ih + x / 2 + 4:.1f}">x</text>')
    # leaders from each part down to its label under the figure
    px, bx, dx = x + m["paper_w"] * 0.3, x + m["boy_x"] + (m["dot_x"] - m["boy_x"]) * 0.11, x + m["dot_x"] + m["dot"] / 2
    ly = fh + B + 12
    leaders = "".join(f'<line x1="{xx:.1f}" y1="{y0:.1f}" x2="{xx:.1f}" y2="{ly:.1f}"></line>' for xx, y0 in ((px, base + 7), (bx, base + 7), (dx, base + 5)))
    d, g = dot_rule(S)
    return (
        f'<svg viewBox="{-B} {-B} {fw + 2 * B + LW:.0f} {fh + 2 * B + BH:.0f}" width="{fw + 2 * B + LW:.0f}" height="{fh + 2 * B + BH:.0f}" role="img" '
        f'aria-label="Construction of the Paperboy wordmark: Paper in the heavy condensed roman, boy in the light italic, then the vermilion dot on the baseline. Clear space is one x-height on every side." style="display: block">'
        f'<defs>{patterns(pid, BLUE, tones={"a1": (A1, 0.24), "a2": (A1, 0.46)})}</defs>'
        f'<path d="{band}" fill="url(#{pid}a2)" fill-rule="evenodd"></path>'
        f'<rect x="0" y="0" width="{fw:.1f}" height="{fh:.1f}" fill="none" stroke="{INK}" stroke-width="0.9"></rect>'
        f'<rect x="{x:.1f}" y="{x:.1f}" width="{iw:.1f}" height="{ih:.1f}" fill="none" stroke="{MUTED}" stroke-width="0.6"></rect>'
        f'{guides}'
        f'<g transform="translate({x:.2f} {base:.2f})">{marks}</g>'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none">{bars}</g>'
        f'<g fill="{INK}" style="{xl}">{xs}</g>'
        f'<g stroke="{INK}" stroke-width="0.75" fill="none">{leaders}</g>'
        f'<g fill="{INK}" style="{SVGLAB}">'
        f'<text x="{px + 7:.1f}" y="{ly + 1:.1f}">ROMAN 800, WIDTH 62.5</text>'
        f'<text x="{bx + 7:.1f}" y="{ly + 1:.1f}">ITALIC 300, WIDTH 100</text>'
        f'<text x="{dx + 7:.1f}" y="{ly + 1:.1f}">PEN POINT, {d:g} PX</text>'
        f'</g></svg>'
    ), fw + 2 * B + LW, fh + 2 * B + BH


def tile(svg, cap, c=MUTED, gap=7):
    return f'<div style="display: flex; flex-direction: column; gap: {gap}px; align-items: flex-start">{svg}<div style="{lab(c)}; white-space: nowrap">{cap}</div></div>'


def rule_row(name, value):
    return (f'<div style="display: flex; gap: 10px; padding: 6px 0 6px; border-top: 0.75px solid {INK}">'
            f'<div style="{lab(INK, 600)}; width: 88px; flex: none">{name}</div>'
            f'<div style="{lab(MUTED)}; flex: 1 1 0; white-space: nowrap">{value}</div></div>')


def build():
    fig, fw, fh = construction()
    d, g = dot_rule(S)
    row = lambda inner, note: (
        f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; height: 64px; box-sizing: border-box; padding: 0 0 12px; border-top: 0.75px solid {INK}">'
        f'{inner}<div style="{lab(MUTED)}; text-align: right; white-space: nowrap">{note}</div></div>')
    ladder = (
        row(wm(38), "38 px, web masthead<br>dot 6.5, gap 3")
        + row(wm(33), "33 px, app masthead<br>dot 6, gap 3")
        + row(wm(22), "22 px, the smallest<br>dot 4, gap 2")
    )
    one = (
        f'<div style="display: flex; gap: 8px; margin-top: 8px">'
        f'<div style="flex: 1 1 0; height: 58px; box-sizing: border-box; border: 1px solid {INK}; display: flex; align-items: center; justify-content: center">{wm(28, color=INK, dot=INK)}</div>'
        f'<div style="flex: 1 1 0; height: 58px; background-color: {INK}; display: flex; align-items: center; justify-content: center">{wm(28, "night", color=STOCK, dot=STOCK)}</div>'
        f'</div>'
    )
    E = MUTED
    sizes = "".join(tile(app_icon(f"s{s}", s, "day", "small", edge=E, label=f"Small master at {s} px"), f"{s} px") for s in (96, 72, 48))
    rules = (
        rule_row("Large master", "Above 96 px. Rings at pitch 8<br>that swell, pen point 43")
        + rule_row("Small master", "96 px and under, and launchers.<br>Five rings at pitch 24, point 56")
        + rule_row("Clear space", "One pen point diameter")
        + rule_row("Smallest", "48 px. Under that, one color")
    )
    layers = (
        tile(app_icon("lb", 108, "day", "small", layer="bg", extend=BLEED, guides=True, label="Background layer: the ground and the rings"), "Background")
        + tile(app_icon("lf", 108, "day", "small", layer="fg", extend=BLEED, guides=True, label="Foreground layer: the P on its trap and the pen point"), "Foreground")
        + tile(app_icon("lm", 108, "mono", "small", layer="mono", extend=BLEED, guides=True, label="Monochrome layer: the P and the pen point in one color"), "Monochrome")
    )
    masks = "".join(app_icon(f"k{i}", 72, "day", "small", shape=sh, edge=E, label=f"The icon under a {nm} mask") for i, (sh, nm) in enumerate((("circle", "circle"), ("squircle", "squircle"), ("round", "rounded square"))))
    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 16px {M}px 0; display: flex; flex-direction: column">
{double()}
</header>

<section style="padding: 10px {M}px 0; display: flex; gap: 28px; height: 326px; box-sizing: border-box">
<div style="width: {fw:.0f}px; flex: none; display: flex; flex-direction: column">
{head("01", "Wordmark", f"Construction at {S} px, drawn to scale", note="Clear space: one x-height (x) on every side")}
<div style="margin: 10px 0 0 0">{fig}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{head("02", "Sizes", "Type size, dot, gap after the y")}
<div style="margin-top: 10px; display: flex; flex-direction: column">{ladder}</div>
<div style="margin-top: auto; border-top: 0.75px solid {INK}; padding-top: 8px">{L("One color", INK, 600)}{one}</div>
</div>
</section>

<section style="display: flex; gap: 28px; padding: 14px 0 0 {M}px; flex: 1 1 0">
<div style="flex: none; width: 480px; display: flex; flex-direction: column">
{head("03", "App icon", "512 master, shown at 480. Arcs only, no mask")}
<div style="margin-top: 8px">{app_icon("big", 480, "day", "large", label="Paperboy app icon, large master: the P of the wordmark and the vermilion pen point on a field of engraved blue rings centered on the pen point")}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; height: 502px">

<div style="padding-right: {M}px">{head("04", "Small master", "The same 512 grid, redrawn for small sizes")}</div>
<div style="display: flex; align-items: flex-start; gap: 24px; margin-top: 8px; padding-right: {M}px">
<div style="display: flex; align-items: flex-end; gap: 12px">{sizes}</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; border-bottom: 0.75px solid {INK}">{rules}</div>
</div>

<div style="padding-right: {M}px; margin-top: 12px">{head("05", "Launcher layers", "Android adaptive icon, 108 dp, shown at 1 px per dp")}</div>
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 8px; padding-right: {M}px">
{layers}
<div style="margin-left: auto; display: flex; flex-direction: column; gap: 7px"><div style="display: flex; gap: 10px">{masks}</div><div style="{lab(MUTED)}; white-space: nowrap">Circle, squircle, rounded square</div></div>
</div>
<div style="margin-top: 6px; padding-right: {M}px; {lab(MUTED)}">Square: the 72 dp a mask can show. Circle: the 66 dp safe zone. Hatch: transparent.</div>

<div style="margin-top: 12px; flex: 1 1 0; background-color: {NG}; color: {NT}; display: flex; flex-direction: column; padding: 11px {M}px 0 20px">
{head("06", "Night", "The halo is engraved: amber rings that thin as they leave the pen point", NT, NM)}
<div style="display: flex; align-items: flex-end; gap: 12px; flex: 1 1 0; padding-bottom: 12px">
<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 9px; padding-bottom: 2px"><div style="{lab(NM)}">Roman 900, italic 400, amber dot</div>{wm(64, "night")}</div>
{app_icon("nl", 104, "night", "large", label="Night app icon, large master, at 104 px")}
<div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px"><div style="{lab(NM)}; text-align: right; white-space: nowrap">104 px, large<br>48 px, small</div>{app_icon("ns", 48, "night", "small", edge=NS, label="Night app icon, small master, at 48 px")}</div>
</div>
</div>

</div>
</section>
</div>"""
    css = "body{margin:0}\na{color:#16130F}"
    out = PROJECT / "Brand.dc.html"
    out.write_text(page("Paperboy brand: wordmark and app icon", css, body, W, H))
    print("wrote", out, out.stat().st_size, "fig", round(fw), round(fh))


if __name__ == "__main__":
    build()
