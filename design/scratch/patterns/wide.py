"""The explainer at desktop width: the first screen and one section with a figure. Day, 1200 wide.

  python3 wide.py        writes canvas/project/Explainer-Wide.dc.html
  python3 run_wide.py TAG   builds, renders, sets the height, slices

It answers one question: at 1200 px, how wide is the text, how wide is the plate, and what
does "bleed" mean. The answer follows the website board (scratch/web/site.py), whose helpers
and hero plate this file imports so the two stay identical:

  page        1200 px at most, 56 px side margins, 12 columns, 24 px gutter (column 68.67 px)
  text        columns 1 to 7, 625 px
  rail        columns 9 to 12, 346 px: a phone-width figure sits here unchanged
  plate       starts at the left edge of the text and runs off the right edge of the screen
"""
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
import importlib.util  # noqa: E402

# the website generator is loaded by path, because its file name is the same as a standard module

_spec = importlib.util.spec_from_file_location("pb_site", HERE.parent / "web" / "site.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)
from lib import INK, STOCK, MUTED, LIVE, TEXT, MONO, FONTS, KEYFRAMES, PRESS, at  # noqa: E402

W, M, GUT = 1200, 56, 24
COL = (W - 2 * M - 11 * GUT) / 12
span = lambda n: n * COL + (n - 1) * GUT
TEXT_W, RAIL_W = span(7), span(4)
OUT = pathlib.Path(os.environ.get("PB_OUT") or HERE.parents[1] / "canvas" / "project")
HEIGHTS = HERE / "heights.json"

VARS = (":root{--fs-body:19px;--lh-body:1.5;--fs-note:16px;--fs-label:11px;--fs-tag:10.5px;--fs-readout:48px;"
        "--fs-xl:88px;--lh-xl:.84;--fs-key:40px;--lh-key:1.04;--fs-wm:38px;--wm-dot:6.5px;--it-st:100%}")


def measures():
    """A note to the reader of the board: the page's measures at 1200, drawn as dimension lines."""
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: 11px; font-weight: 500; letter-spacing: 0.06em"
    x_text0, x_text1 = M, M + TEXT_W
    x_rail0, x_rail1 = M + span(8) + GUT, W - M
    cols = "".join(f'<rect x="{M + i * (COL + GUT):.1f}" y="0" width="{COL:.1f}" height="10" fill="none" stroke="{MUTED}" stroke-width="0.6"></rect>' for i in range(12))

    def dim(xa, xb, y, label, anchor="middle", open_end=False):
        cap = lambda x: f'<line x1="{x:.1f}" y1="{y - 5}" x2="{x:.1f}" y2="{y + 5}"></line>'
        end = f'<path d="M{xb - 7:.1f} {y - 4}L{xb:.1f} {y}L{xb - 7:.1f} {y + 4}"></path>' if open_end else cap(xb)
        tx = (xa + xb) / 2 if anchor == "middle" else xa
        return (f'<g fill="none" stroke="{INK}" stroke-width="0.75"><line x1="{xa:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}"></line>{cap(xa)}{end}</g>'
                f'<text x="{tx:.1f}" y="{y + 19}" text-anchor="{anchor}" fill="{INK}" style="{lab}">{label}</text>')

    return (f'<svg viewBox="0 0 {W} 118" width="{W}" height="118" role="img" aria-label="The measures of the page at 1200 pixels wide: side margins of 56, '
            f'twelve columns with a 24 pixel gutter, text on columns 1 to 7 at 625 pixels, a rail on columns 9 to 12 at 346 pixels, and a plate that starts at the left edge of the text and runs off the right edge of the screen." style="display: block">'
            f'{cols}'
            f'{dim(x_text0, x_text1, 34, "TEXT, COLUMNS 1 TO 7, 625 PX")}'
            f'{dim(x_rail0, x_rail1, 34, "RAIL, COLUMNS 9 TO 12, 346 PX")}'
            f'{dim(0, M, 34, "56", "middle")}{dim(W - M, W, 34, "56", "middle")}'
            f'{dim(M, W, 80, "PLATE AND BLEED FIGURES: FROM THE LEFT EDGE OF THE TEXT OFF THE RIGHT EDGE OF THE SCREEN", "start", True)}'
            f'</svg>')


def build():
    lab, t1, d1, d4 = S.lab, S.t1, S.d1, S.d4
    BODY = t1()
    NOTE = t1("var(--fs-note)", 1.42, italic=True)
    hero = S.plate_gw("hw", 1900, 320, 0, 1088, 1.6, 104, 46, 62, 0.005, 0.05, "wipeL", lab_px=11, sweep_ms=2100)
    pad = f"padding-left: {M}px; padding-right: {M}px"
    grid12 = "display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); column-gap: 24px"
    P = lambda s, mt=14: f'<p style="margin: {mt}px 0 0; max-width: {TEXT_W:.0f}px; {BODY}; text-wrap: pretty">{s}</p>'

    body = f"""<div style="width: {W}px; box-sizing: border-box; position: relative; overflow: hidden; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="{pad}; padding-top: 20px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center">
<a href="#site" aria-label="Paperboy, to the website" style="display: inline-block; text-decoration: none; color: {INK}; padding: 1px 0 5px; line-height: 1; white-space: nowrap">{S.wordmark("38px", "6.5px", "3px")}</a>
</div>
{S.DOUBLE}
</header>

<main style="display: flex; flex-direction: column">
<article style="display: flex; flex-direction: column">

<div style="{pad}; padding-top: 13px">
<div style="display: flex; align-items: center; gap: 6px">
{S.tag_outline("Physics")}{S.tag_solid("Peer-reviewed")}
<span style="margin-left: auto">{S.textlink("Physical Review Letters", "#paper", extra="; margin: -14px 0")}</span>
</div>
</div>
<h1 style="margin: 0; {pad}; padding-top: 10px; {d1("66px", 0.95)}">
<span style="display: block; animation: press 190ms {PRESS} {at(0)} both">Two black holes merged.</span>
<span style="display: block; animation: press 190ms {PRESS} {at(50)} both; {d4("66px", 0.95)}">Earth felt space stretch.</span>
</h1>
<div style="margin: 34px 0 0 {M}px">{hero}</div>
<div style="{pad}; padding-top: 6px; {grid12}; align-items: start">
<div style="grid-column: 1 / span 4; display: flex; flex-direction: column; gap: 3px">
<div style="{d1("48px", 1)}; font-variant-numeric: lining-nums; white-space: nowrap">1.0{S.TIMES}10<sup style="{S.SUP}">−21</sup></div>
<div style="{lab()}">Peak strain. Pitch 35 to 250 Hz</div>
</div>
<p style="grid-column: 5 / span 5; margin: 0; padding-top: 6px; {BODY}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>
<div style="grid-column: 10 / span 3; text-align: right; padding-top: 6px; {lab(MUTED, 500, "var(--fs-label)", 1.4)}">Plate 1<br>Illustration,<br>not to scale</div>
</div>

<section style="{pad}; padding-top: 56px; display: flex; flex-direction: column">
<div style="{lab(INK, 600)}">Key idea</div>
<p style="margin: 12px 0 0; max-width: {span(10):.0f}px; {d4("40px", 1.04)}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</section>

<section style="{pad}; margin-top: 56px; display: block">
{S.DOUBLE}
<div style="margin-top: 12px; {lab(INK, 600)}">What they found</div>
<h2 style="margin: 8px 0 0; {d1("44px", 0.98)}">One chirp, <span style="{d4("44px", 0.98)}">a fifth of a second long.</span></h2>

<figure style="float: right; width: {RAIL_W:.0f}px; margin: 22px 0 0; display: flex; flex-direction: column">
{S.fig_head("Fig. 2", "Data, from the paper")}
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div style="{d1("88px", 0.84)}; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px"><div style="{lab(INK, 600)}">Megaparsecs away</div><div style="{t1(15, 1.3, italic=True)}">roughly 1.3 billion light years</div></div>
</div>
{S.figbox(S.range_bar("wr"))}
<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; {lab()}">
<span style="display: inline-flex; align-items: center; gap: 6px">{S.LEGEND_DOT}Reported value</span>
<span style="display: inline-flex; align-items: center; gap: 6px">{S.swatch("wk")}Range</span>
</div>
</figure>

{P("The signal swept up in frequency from 35 Hz to 250 Hz in about 0.2 seconds. A rising sweep like that is called a chirp.", 20)}
{P("Its shape matches two black holes spiraling into one, about 410 megaparsecs away, roughly 1.3 billion light years.†")}
<div style="width: 64px; height: 0.75px; background-color: {INK}; margin-top: 16px"></div>
<p style="margin: 10px 0 0; max-width: {TEXT_W:.0f}px; {NOTE}; text-wrap: pretty">† The mass and distance values carry wide error ranges. The distance, for example, is 410 megaparsecs with a range of roughly 230 to 570.</p>
{P("The two black holes had about 36 and 29 solar masses. The one they formed has about 62. About 3 solar masses of energy left as gravitational waves.", 20)}
<div style="clear: both"></div>
</section>

</article>
</main>

<aside aria-label="Measures of this board" style="margin-top: 72px; padding-bottom: 40px; display: flex; flex-direction: column">
<div style="{pad}">{S.HAIR}<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px"><div style="{lab(INK, 600)}">Measures at 1200</div><div style="{lab()}">A note on this board, not part of the page</div></div></div>
<div style="margin-top: 16px">{measures()}</div>
</aside>

</div>"""

    css = (
        f"body{{margin:0;background:{STOCK}}}\na{{color:{INK}}}\na:hover{{color:{MUTED}}}\n"
        f"a:focus-visible{{outline:2px solid {INK};outline-offset:2px}}\n"
        f"{KEYFRAMES}\n"
        "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
        "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
        "@keyframes drop{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:none}}\n"
        f"{S.wipe_px('wipeL', 320)}\n{VARS}"
    )
    heights = json.loads(HEIGHTS.read_text()) if HEIGHTS.exists() else {}
    h = int(heights.get("wide", 1500))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Explainer, Paper 1, desktop width</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
{css}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{W},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""
    out = OUT / "Explainer-Wide.dc.html"
    out.write_text(page)
    print("wrote", out, out.stat().st_size, "height", h)


if __name__ == "__main__":
    build()
