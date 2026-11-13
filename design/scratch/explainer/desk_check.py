"""Check of the desktop sizes SYSTEM.md section 2.4 marks "spec": display 88 / 0.94 (fluid),
body 19 / 1.5 at a 34em measure, note 16 / 1.42, label 11, tag 10.5, plus the desktop spacing
of section 6 (1200 max, 56 side padding, 96 between sections, figures out to 960).

A scratch page, not a deliverable. It is fluid: the phone scale under 1024, the desktop scale above.

  python3 desk_check.py     writes Explainer-Desk-Check.dc.html next to this file
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
sys.path.insert(0, str(HERE.parent / "director"))
from lib import *  # noqa: E402,F403
import lock_proof as LP  # noqa: E402

PW = 960                       # the plate fills a 960 column on desktop
c, g, mu, live = INK, STOCK, MUTED, LIVE

CSS = f"""body{{margin:0;background:{g}}}
a{{color:{c}}}a:hover{{color:{mu}}}
.pg{{max-width:1200px;margin:0 auto;padding:0 20px;box-sizing:border-box}}
.sec{{margin-top:40px}}
.col{{max-width:34em;font-size:17px}}
.t-display{{font-size:clamp(44px,7.2vw,88px);line-height:.94}}
.t-headline{{font-size:44px;line-height:.98}}
.t-head2{{font-size:30px;line-height:1.02}}
.t-key{{font-size:30px;line-height:1.06}}
.t-xl{{font-size:72px;line-height:.86}}
.t-readout{{font-size:30px;line-height:1}}
.t-body{{font-size:17px;line-height:1.47}}
.t-note{{font-size:15px;line-height:1.4}}
.t-label{{font-size:10.5px;line-height:1.3}}
.t-tag{{font-size:10px;line-height:1.3}}
.wm{{font-size:33px}}
.plate-ph{{display:block}}.plate-dk{{display:none}}
@media (min-width:1024px){{
.pg{{padding:0 56px}}
.sec{{margin-top:96px}}
.col{{font-size:19px}}
.t-headline{{font-size:66px;line-height:.95}}
.t-head2{{font-size:44px;line-height:.98}}
.t-key{{font-size:40px;line-height:1.04}}
.t-xl{{font-size:88px;line-height:.84}}
.t-readout{{font-size:48px;line-height:1}}
.t-body{{font-size:19px;line-height:1.5}}
.t-note{{font-size:16px;line-height:1.42}}
.t-label{{font-size:11px}}
.t-tag{{font-size:10.5px}}
.wm{{font-size:38px}}
.plate-ph{{display:none}}.plate-dk{{display:block}}
}}
""" + KEYFRAMES + """
@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}
@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}
""" + ink_keyframes("inkproof", 390, LP.BAND)

D1 = f"font-family: {DISP}; font-weight: 800; font-stretch: 62.5%; letter-spacing: -0.005em"
D4 = f"font-family: {DISP}; font-weight: 300; font-stretch: 100%; letter-spacing: -0.012em; font-style: italic"
T1 = f"font-family: {TEXT}; font-weight: 400"
T3 = f"font-family: {TEXT}; font-weight: 400; font-style: italic"
M1 = f"font-family: {MONO}; font-stretch: 75%; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase"
M2 = f"font-family: {MONO}; font-stretch: 75%; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase"
double = f'<div style="height: 3px; background-color: {c}"></div><div style="height: 0.75px; background-color: {c}; margin-top: 2px"></div>'
hair = f'<div style="height: 0.75px; background-color: {c}"></div>'


def range_bar(pid, width):
    s = (width - 62) / 600
    X = lambda v: v * s
    ax = 44
    lab = f"font-family: {MONO}; font-stretch: 75%; font-weight: 500; letter-spacing: 0.06em"
    ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ax}" x2="{X(v):.1f}" y2="{ax + (7 if v % 200 == 0 else 4)}"></line>' for v in range(0, 601, 50))
    tl = "".join(f'<text x="{X(v):.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 200, 400, 600))
    return (
        f'<svg viewBox="0 0 {width} 70" width="{width}" height="70" role="img" aria-label="Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570" style="display: block; max-width: 100%">'
        f'<defs>{patterns(pid, c, tones={"a2": (A1, 0.46)})}</defs>'
        f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="url(#{pid}a2)"></rect>'
        f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
        f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{g}" stroke-width="7"></line>'
        f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{live}" stroke-width="2"></line>'
        f'<circle cx="{X(410):.1f}" cy="9" r="3.6" fill="{live}"></circle>'
        f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{X(600):.1f}" y2="{ax}"></line>{ticks}</g>'
        f'<g fill="{c}" class="t-label" style="{lab}">{tl}<text x="{width}" y="{ax + 20}" text-anchor="end">Mpc</text>'
        f'<text x="{X(230):.1f}" y="11" text-anchor="middle">230</text><text x="{X(570):.1f}" y="11" text-anchor="middle">570</text></g>'
        f'</svg>'
    )


def plate_at(pid, width):
    LP.W = width
    html = LP.plate(pid, "day")
    LP.W = 390
    return html


def row(label, value, n):
    return (f'<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {c}">'
            f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
            f'<div class="t-label" style="{M1}; color: {mu}; flex: none">{label}</div>'
            f'<div class="t-readout" style="{D1}; font-variant-numeric: lining-nums; text-align: right">{value}</div></div>'
            f'<div class="t-note" style="{T3}; text-wrap: pretty">{n}</div></div>')


unit = lambda t: f'<span class="t-note" style="{T3}; margin-left: 6px">{t}</span>'
tag_o = lambda t: f'<span class="t-tag" style="{M2}; color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'
tag_s = lambda t: f'<span class="t-tag" style="{M2}; color: {g}; background-color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'

body = f"""<div style="background-color: {g}; color: {c}; font-family: {TEXT}; padding-bottom: 96px">
<div class="pg">
<header style="padding-top: 12px; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; justify-content: space-between">
<div class="wm" style="{D1}; line-height: 1; padding-bottom: 5px">Paper<span style="{D4}; letter-spacing: -0.02em">boy</span><span style="display: inline-block; width: 0.17em; height: 0.17em; border-radius: 50%; background-color: {live}; margin-left: 3px"></span></div>
<div class="t-label" style="{M1}; color: {mu}">Science and math, newly released</div>
</div>
{double}
</header>

<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding-top: 16px">
{tag_o("Physics")}{tag_s("Peer-reviewed")}
<a href="#paper" class="t-note" style="margin-left: auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; {T3}; color: {c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">Physical Review Letters{OUTARROW}</a>
</div>
<div class="t-label" style="{M1}; color: {mu}; margin-top: 8px">display, 88 / 0.94, clamp(44px, 7.2vw, 88px)</div>
<h1 class="t-display" style="margin: 6px 0 0; {D1}; max-width: 11em">Two black holes merged. <span style="{D4}">Earth felt space stretch.</span></h1>
<div class="t-label" style="{M1}; color: {mu}; margin-top: 28px">headline, 66 / 0.95</div>
<div class="t-headline" style="margin: 6px 0 0; {D1}">Two black holes merged. <span style="{D4}">Earth felt space stretch.</span></div>

<div style="margin-top: 20px"><div class="plate-dk">{plate_at("dk", PW)}</div><div class="plate-ph" style="margin: 0 -20px">{plate_at("ph", 390)}</div></div>

<div class="col" style="margin-top: 16px">
<p class="t-body" style="margin: 0; {T1}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>
</div>

<section class="sec">
<div class="t-label" style="{M2}">Key idea</div>
<p class="t-key" style="margin: 12px 0 0; {D4}; text-wrap: balance; max-width: 22em">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</section>

<section class="sec">
{double}
<div class="t-label" style="{M2}; margin-top: 12px">What they found</div>
<h2 class="t-head2" style="margin: 8px 0 0; {D1}">One chirp, <span style="{D4}">a fifth of a second long.</span></h2>
<div class="col">
<p class="t-body" style="margin: 14px 0 0; {T1}; text-wrap: pretty">The signal swept up in frequency from 35 Hz to 250 Hz in about 0.2 seconds. A rising sweep like that is called a chirp.</p>
<p class="t-body" style="margin: 12px 0 0; {T1}; text-wrap: pretty">Its shape matches two black holes spiraling into one, about 410 megaparsecs away, roughly 1.3 billion light years.† The two black holes had about 36 and 29 solar masses. The one they formed has about 62. About 3 solar masses of energy left as gravitational waves.</p>
<div style="width: 64px; height: 0.75px; background-color: {c}; margin-top: 16px"></div>
<p class="t-note" style="margin: 10px 0 0; {T3}; text-wrap: pretty">† The mass and distance values carry wide error ranges. The distance, for example, is 410 megaparsecs with a range of roughly 230 to 570.</p>
</div>
<figure class="col" style="margin: 28px 0 0; display: flex; flex-direction: column">
{hair}
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px"><div class="t-label" style="{M2}">Fig. 2</div><div class="t-label" style="{M1}; color: {mu}">Data, from the paper</div></div>
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div class="t-xl" style="{D1}; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px"><div class="t-label" style="{M2}">Megaparsecs away</div><div class="t-note" style="{T3}">roughly 1.3 billion light years</div></div>
</div>
<div style="margin-top: 14px">{range_bar("rk", 350)}</div>
</figure>
</section>

<section class="sec col">
{double}
<h2 class="t-head2" style="margin: 12px 0 12px; {D1}">How sure <span style="{D4}">is this?</span></h2>
{row("Review", tag_s("Peer-reviewed"), "Physical Review Letters, February 11, 2016.")}
{row("Significance", "&gt; 5.1" + unit("sigma"), "A false alarm this strong is expected less than once in 203,000 years.")}
{row("Sky position", "600" + unit("square degrees"), "Where it came from was known only to within about this much sky.")}
<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 0 0; border-top: 0.75px solid {c}">
<div class="t-label" style="{M1}; color: {mu}">This explainer</div>
<p class="t-body" style="margin: 0; {T1}; text-wrap: pretty">Machine written, and it can be wrong. Check it against the paper.</p>
</div>
</section>
</div>
</div>"""

out = HERE / "Explainer-Desk-Check.dc.html"
out.write_text(page("Desktop size check, explainer", CSS, body, 1440, 2600))
print("wrote", out, out.stat().st_size)
