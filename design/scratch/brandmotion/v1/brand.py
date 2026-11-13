"""Brand.dc.html: the Paperboy wordmark and app icon. 1200 by 900.

  python3 brand.py
"""
from bm import *

W, H = 1200, 900
M = 48
S = 124                      # type size of the construction drawing


def construction():
    marks, m = wm_outline(S)
    x = m["xh"]                       # the clear space unit
    asc, desc = m["asc"], m["desc"]
    iw, ih = m["width"], asc + desc   # the mark's own box
    fw, fh = iw + 2 * x, ih + 2 * x   # the clear space
    base = x + asc
    B = 14                            # band of print outside the clear space
    LW = 100                          # label column on the right
    BH = 30                           # labels under the figure
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


def tile(svg, cap, c=MUTED):
    return f'<div style="display: flex; flex-direction: column; gap: 7px; align-items: flex-start">{svg}<div style="{lab(c)}; white-space: nowrap">{cap}</div></div>'


def build():
    fig, fw, fh = construction()
    row = lambda inner, note: (
        f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; padding: 10px 0 9px; border-top: 0.75px solid {INK}">'
        f'{inner}<div style="{lab(MUTED)}; text-align: right; white-space: nowrap">{note}</div></div>')
    ladder = (
        row(L("Web hero, 150 px", INK), "dot 22, gap 10")
        + row(wm(38), "38 px<br>dot 6.5, gap 3")
        + row(wm(33), "33 px<br>dot 6, gap 3")
        + row(wm(22), "22 px, the smallest<br>dot 4, gap 2<br>under that, the icon")
    )
    one = (
        f'<div style="display: flex; gap: 8px; margin-top: 8px">'
        f'<div style="flex: 1 1 0; height: 54px; box-sizing: border-box; border: 1px solid {INK}; display: flex; align-items: center; justify-content: center">{wm(28, color=INK, dot=INK)}</div>'
        f'<div style="flex: 1 1 0; height: 54px; background-color: {INK}; display: flex; align-items: center; justify-content: center">{wm(28, "night", color=STOCK, dot=STOCK)}</div>'
        f'</div>'
    )
    sizes = "".join(tile(icon(f"i{s}", s), f"{s} px<br>{d}") for s, d in ((144, "xxhdpi"), (96, "xhdpi"), (72, "hdpi"), (48, "mdpi")))
    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 16px {M}px 0; display: flex; flex-direction: column">
{double()}
</header>

<section style="padding: 10px {M}px 0; display: flex; gap: 28px; height: 338px; box-sizing: border-box">
<div style="width: {fw:.0f}px; flex: none; display: flex; flex-direction: column">
{head("01", "Wordmark", "Construction, drawn to scale", note="Clear space: one x-height (x) on every side")}
<div style="margin: 10px 0 0 0">{fig}</div>
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column">
{head("02", "Sizes", "Type size, dot, gap after the y")}
<div style="margin-top: 10px; display: flex; flex-direction: column">{ladder}</div>
<div style="margin-top: auto; border-top: 0.75px solid {INK}; padding-top: 8px">{L("One color", INK, 600)}{one}</div>
</div>
</section>

<section style="display: flex; gap: 28px; padding: 18px 0 0 {M}px; flex: 1 1 0">
<div style="flex: none">{icon("i512", 512)}</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; height: 512px">
<div style="padding-right: {M}px">{head("03", "App icon", "Drawn at 512 by 512, shown at launcher sizes")}</div>
<p style="margin: 10px {M}px 0 0; {text(15, lh=1.38, italic=True)}; text-wrap: pretty">Three parts of the system: the P of the wordmark, the pen point, and the engraved field, its rings centered on the pen point. The square is the launcher's 72 dp window. The P and the pen point sit inside the middle 48 dp, so no launcher mask cuts them.</p>
<div style="display: flex; align-items: flex-start; gap: 12px; margin-top: 14px; padding-right: {M}px">
<div style="display: flex; align-items: flex-end; gap: 12px">{sizes}</div>
<div style="margin-left: auto; display: flex; gap: 12px; align-self: flex-end">
{tile(icon("ic", 72, mask="circle"), "Launcher<br>mask")}
{tile('<div style="outline: 1px solid ' + INK + '; outline-offset: -1px">' + icon("im", 72, "mono") + '</div>', "One<br>color")}
</div>
</div>
<div style="margin-top: 16px; flex: 1 1 0; background-color: {NG}; color: {NT}; display: flex; flex-direction: column; padding: 14px {M}px 0 24px">
{head("04", "Night", "Roman 900, italic 400, amber dot", NT, NM)}
<div style="display: flex; align-items: flex-end; gap: 16px; flex: 1 1 0; padding-bottom: 16px">
<div style="flex: 1 1 0; padding-bottom: 14px">{wm(76, "night")}</div>
{tile(icon("in", 128, "night"), "128 px", NM)}{tile(icon("in2", 48, "night"), "48 px", NM)}
</div>
</div>
</div>
</section>
</div>"""
    css = "body{margin:0}\na{color:#16130F}"
    out = PROJECT / "Brand.dc.html"
    out.write_text(page("Paperboy brand: wordmark and app icon", css, body, W, H))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build()
