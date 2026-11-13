"""Director's proof of the locked First Light components that no candidate drew at phone width:
key idea, caveat, stat with a range, analogy, the "how sure" ledger, source footer, the short
card, the preprint card, and the stamped rating. 390 wide, day or night. Facts from CONTENT.md only.

  python3 lock_parts.py     writes LockParts-Day.dc.html and LockParts-Night.dc.html
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import *  # noqa: E402,F403

BLUE, NBLUE = "#1F3FD0", "#4D63C9"
LAB = 10.5
W, M = 390, 20
CW = W - 2 * M


def build(theme):
    day = theme == "day"
    g = STOCK if day else NG
    c = INK if day else NT
    mu = MUTED if day else NM
    plate = BLUE if day else NBLUE
    live = LIVE if day else AMBER
    grid = MUTED if day else NS
    hw = 800 if day else 900
    iw = 300 if day else 400
    L = lambda t, col=None, w=500: f'<div style="{mono(LAB, color=col or mu, weight=w, ls=0.06)}">{t}</div>'
    slug = lambda t: f'<div style="{mono(LAB, color=c, weight=600, ls=0.06)}">{t}</div>'
    lab = f"font-family: {MONO}; font-stretch: 75%; font-size: {LAB}px; font-weight: 500; letter-spacing: 0.06em"
    hair = f'<div style="height: 0.75px; background-color: {c}"></div>'
    double = f'<div style="height: 3px; background-color: {c}"></div><div style="height: 0.75px; background-color: {c}; margin-top: 2px"></div>'
    it = lambda size: disp(size, weight=iw, stretch=100, lh=1.06, ls=-0.012, italic=True)

    def tag_outline(t):
        return f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'

    def tag_solid(t):
        return f'<span style="{mono(10, color=g, weight=600, ls=0.06)}; background-color: {c}; border: 1px solid {c}; padding: 4px 6px 3px">{t}</span>'

    def tag_screen(t):
        hatch = f"repeating-linear-gradient(135deg, {c} 0 1.1px, transparent 1.1px 3.2px)"
        return (f'<span style="display: inline-flex; padding: 3.5px; background-image: {hatch}">'
                f'<span style="{mono(10, color=c, weight=600, ls=0.06)}; background-color: {g}; padding: 1.5px 4px 0.5px">{t}</span></span>')

    def source(label):
        return (f'<a href="#paper" style="min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
                f'{text(15, lh=1.15, italic=True)}; color: {c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</a>')

    def rate(icon, label, on=False):
        bg, fg = (c, g) if on else ("transparent", c)
        pressed = ' aria-pressed="true"' if on else ' aria-pressed="false"'
        return (f'<button type="button"{pressed} style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; '
                f'border: 1px solid {c}; border-radius: 0; color: {fg}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">'
                f'{icon}<span style="{text(16, lh=1, weight=500)}">{label}</span></button>')

    def btn_outline(label):
        return (f'<a href="#paper" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
                f'padding: 0 14px 0 16px; border: 1px solid {c}; color: {c}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{OUTARROW.replace("11", "15", 2)}</a>')

    # ---- stat range bar: 410 Mpc, range 230 to 570, on a ruler from 0 to 600
    def range_bar(pid):
        s = (CW - 62) / 600
        X = lambda v: v * s
        ax = 44
        ticks = "".join(f'<line x1="{X(v):.1f}" y1="{ax}" x2="{X(v):.1f}" y2="{ax + (7 if v % 200 == 0 else 4)}"></line>' for v in range(0, 601, 50))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in (0, 200, 400, 600))
        return (
            f'<svg viewBox="0 0 {CW} 70" width="{CW}" height="70" role="img" aria-label="Data from the paper: distance about 410 megaparsecs, with a range of roughly 230 to 570, on a scale from 0 to 600" style="display: block">'
            f'<defs>{patterns(pid, c if day else NM, tones={"a2": (A1, 0.46)})}</defs>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="url(#{pid}a2)"></rect>'
            f'<rect x="{X(230):.1f}" y="16" width="{X(340):.1f}" height="16" fill="none" stroke="{c}" stroke-width="0.9"></rect>'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{g}" stroke-width="7"></line>'
            f'<line x1="{X(410):.1f}" y1="9" x2="{X(410):.1f}" y2="{ax}" stroke="{live}" stroke-width="{2 if day else 1.75}"></line>'
            f'<circle cx="{X(410):.1f}" cy="9" r="3.6" fill="{live}"></circle>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="0" y1="{ax}" x2="{X(600):.1f}" y2="{ax}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab}">{tl}<text x="{CW}" y="{ax + 20}" text-anchor="end">Mpc</text>'
            f'<text x="{X(230):.1f}" y="11" text-anchor="middle">230</text><text x="{X(570):.1f}" y="11" text-anchor="middle">570</text></g>'
            f'</svg>'
        )

    # ---- analogy: one ruler in angstroms, drawn to scale
    def analogy(pid):
        x0, s, ry = 1, 100, 196
        X = lambda v: x0 + v * s
        r = 0.7 * s
        ccx, ccy = X(0.7), ry - r - 8
        ticks = "".join(f'<line x1="{X(i / 5):.1f}" y1="{ry}" x2="{X(i / 5):.1f}" y2="{ry + (7 if i % 5 == 0 else 4)}"></line>' for i in range(0, 16))
        tl = "".join(f'<text x="{X(v):.1f}" y="{ry + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in range(0, 4))

        def beam(v, y, col, w):
            return (f'<line x1="{x0}" y1="{y}" x2="{X(v):.1f}" y2="{y}" stroke="{col}" stroke-width="{w}"></line>'
                    f'<line x1="{x0}" y1="{y - 5}" x2="{x0}" y2="{y + 5}" stroke="{col}" stroke-width="{w}"></line>'
                    f'<line x1="{X(v):.1f}" y1="{y - 5}" x2="{X(v):.1f}" y2="{y + 5}" stroke="{col}" stroke-width="{w}"></line>')

        return (
            f'<svg viewBox="0 0 {CW} 220" width="{CW}" height="220" role="img" aria-label="Drawing to scale on a ruler in angstroms: a carbon atom about 1.4 wide, AlphaFold median error 0.96, next best method 2.8" style="display: block">'
            f'<defs>{patterns(pid, plate, tones={"a1": (A1, 0.3)})}</defs>'
            f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r:.1f}" fill="url(#{pid}a1)"></circle>'
            f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r:.1f}" fill="none" stroke="{c}" stroke-width="0.9"></circle>'
            f'<g stroke="{grid}" stroke-width="0.6" fill="none">'
            f'<line x1="{X(0.96):.1f}" y1="14" x2="{X(0.96):.1f}" y2="{ry}"></line><line x1="{X(2.8):.1f}" y1="34" x2="{X(2.8):.1f}" y2="{ry}"></line></g>'
            f'{beam(2.8, 34, c, 1.4)}'
            f'<line x1="{x0}" y1="14" x2="{X(0.96):.1f}" y2="14" stroke="{g}" stroke-width="7"></line>{beam(0.96, 14, live, 2 if day else 1.75)}'
            f'<circle cx="{X(0.96):.1f}" cy="14" r="3.6" fill="{live}"></circle>'
            f'<g stroke="{c}" stroke-width="0.9" fill="none"><line x1="{x0}" y1="{ry}" x2="{X(3):.1f}" y2="{ry}"></line>{ticks}</g>'
            f'<g fill="{c}" style="{lab}">{tl}<text x="{X(3) + 9:.1f}" y="{ry + 20}">Å</text>'
            f'<text x="{X(0.96) + 10:.1f}" y="18">ALPHAFOLD, 0.96 Å</text>'
            f'<text x="{X(2.8):.1f}" y="54" text-anchor="end">NEXT BEST, 2.8 Å</text>'
            f'<text x="{X(1.4) + 10:.1f}" y="{ccy:.1f}">CARBON ATOM,</text><text x="{X(1.4) + 10:.1f}" y="{ccy + 14:.1f}">ABOUT 1.4 Å WIDE</text>'
            f'</g></svg>'
        )

    def row(label, value, note=""):
        n = f'<div style="{text(15, lh=1.4, italic=True)}; text-wrap: pretty">{note}</div>' if note else ""
        return (f'<div style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {c}">'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
                f'<div style="{mono(LAB, color=mu, ls=0.06)}; flex: none">{label}</div>'
                f'<div style="{disp(30, weight=hw, lh=1)}; font-variant-numeric: lining-nums; text-align: right">{value}</div></div>{n}</div>')

    unit = lambda t: f'<span style="{text(15, lh=1, italic=True)}; margin-left: 6px">{t}</span>'
    body = f"""<div style="width: {W}px; box-sizing: border-box; background-color: {g}; color: {c}; font-family: {TEXT}; display: flex; flex-direction: column; padding: 0 {M}px 40px">

<section style="display: flex; flex-direction: column; padding: 40px 0">
{slug("Key idea")}
<p style="margin: 12px 0 0; {it(30)}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p>
</section>

<section style="display: flex; flex-direction: column">
<p style="margin: 0; {text(17, lh=1.47)}; text-wrap: pretty">The merger happened about 410 megaparsecs away, roughly 1.3 billion light years.† The signal reached Livingston about 7 milliseconds before Hanford.</p>
<div style="width: 64px; height: 0.75px; background-color: {c}; margin-top: 16px"></div>
<p style="margin: 10px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">† The distance carries a wide error range, roughly 230 to 570 megaparsecs. The sky position was known only to within about 600 square degrees.</p>
</section>

<section style="display: flex; flex-direction: column; margin-top: 40px">
{hair}
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">{slug("Fig. 2")}{L("Data, from the paper")}</div>
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 10px">
<div style="{disp(72, weight=hw, lh=0.86)}; font-variant-numeric: lining-nums">410</div>
<div style="display: flex; flex-direction: column; gap: 3px; padding-bottom: 3px">{L("Megaparsecs away", c, 600)}<div style="{text(15, lh=1.3, italic=True)}">roughly 1.3 billion light years</div></div>
</div>
<div style="margin-top: 14px">{range_bar("r" + theme[0])}</div>
<div style="display: flex; gap: 16px; align-items: center; margin-top: 8px; {mono(LAB, color=mu, ls=0.06)}">
<span style="display: inline-flex; align-items: center; gap: 6px"><span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background-color: {live}"></span>Reported value</span>
<span style="display: inline-flex; align-items: center; gap: 6px"><svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><defs>{patterns("k" + theme[0], c if day else NM, tones={"a2": (A1, 0.46)})}</defs><rect width="22" height="10" fill="url(#k{theme[0]}a2)"></rect><rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{c}" stroke-width="0.9"></rect></svg>Range</span>
</div>
</section>

<section style="display: flex; flex-direction: column; margin-top: 40px">
{hair}
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px">{slug("For scale")}{L("Illustration, drawn to scale")}</div>
<div style="margin-top: 14px">{analogy("a" + theme[0])}</div>
<p style="margin: 8px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty">AlphaFold's median error is smaller than a single carbon atom.</p>
</section>

<section style="display: flex; flex-direction: column; margin-top: 40px">
{double}
<h3 style="margin: 12px 0 12px; {disp(30, weight=hw, lh=1)}">How sure <span style="{it(30)}">is this?</span></h3>
{row("Review", tag_solid("Peer-reviewed"))}
{row("Significance", "&gt; 5.1" + unit("sigma"), "A false alarm this strong is expected less than once in 203,000 years.")}
{row("Sky position", "600" + unit("square degrees"), "Known only to within about this much sky.")}
{row("Distance", "410" + unit("megaparsecs"), "With a range of roughly 230 to 570.")}
<div style="display: flex; flex-direction: column; gap: 6px; padding: 11px 0 0; border-top: 0.75px solid {c}">
{L("This explainer")}
<p style="margin: 0; {text(17, lh=1.47)}; text-wrap: pretty">Machine written, and it can be wrong. Check it against the paper.</p>
</div>
</section>

<footer style="display: flex; flex-direction: column; margin-top: 40px">
{double}
<div style="margin-top: 12px">{slug("Source")}</div>
<p style="margin: 8px 0 0; {text(17, lh=1.4, italic=True)}; text-wrap: pretty">Observation of Gravitational Waves from a Binary Black Hole Merger</p>
<p style="margin: 6px 0 0; {text(15, lh=1.4)}; color: {mu}; text-wrap: pretty">B. P. Abbott et al. (LIGO Scientific Collaboration and Virgo Collaboration)</p>
<div style="margin-top: 8px; display: flex; flex-direction: column; gap: 3px">{L("Physical Review Letters 116, 061102")}{L("February 11, 2016. CC BY 3.0")}</div>
<div style="margin-top: 14px">{btn_outline("Read the paper")}</div>
</footer>

<div style="margin-top: 56px">{hair}</div>
<div style="margin-top: 10px">{L("Short card, no explainer", c, 600)}</div>

<article style="display: flex; flex-direction: column; margin-top: 12px">
{double}
<div style="display: flex; flex-wrap: wrap; align-items: center; column-gap: 6px; row-gap: 0; padding-top: 13px">
{tag_outline("Space")}{tag_solid("Peer-reviewed")}
<span style="flex: 1 1 auto; display: flex; justify-content: flex-end; margin: -13px 0">{source("The Astrophysical Journal Letters")}</span>
</div>
<h2 style="margin: 0; padding-top: 10px; {disp(30, weight=hw, lh=1.02)}">The first picture of <span style="{disp(30, weight=iw, stretch=100, lh=1.02, ls=-0.012, italic=True)}">a black hole's shadow.</span></h2>
<div style="display: flex; align-items: flex-end; gap: 10px; margin-top: 12px">
<div style="{disp(44, weight=hw, lh=0.86)}; font-variant-numeric: lining-nums">42</div>
<div style="{mono(LAB, color=mu, ls=0.06)}; padding-bottom: 1px">Microarcseconds across,<br>the bright ring in galaxy M87</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px; margin-top: 14px">
{btn_outline("Read the paper")}
<div style="display: flex; gap: 8px">{rate(PLUS, "More like this", on=True)}{rate(MINUS, "Less like this")}</div>
</div>
</article>

<article style="display: flex; flex-direction: column; margin-top: 20px">
<div style="height: 0.75px; background-color: {c}"></div><div style="height: 3px; background-color: {c}; margin-top: 2px"></div>
<div style="display: flex; align-items: center; gap: 6px; padding-top: 13px">{tag_outline("Physics")}{tag_screen("Preprint")}</div>
<h2 style="margin: 0; padding-top: 10px; {disp(30, weight=hw, lh=1.02)}">[PREPRINT TITLE]</h2>
<p style="margin: 8px 0 0; {text(16, lh=1.42)}">[ONE LINE SUMMARY]</p>
</article>
</div>"""
    css = f"body{{margin:0;background:{g}}}\na{{color:{c}}}\n" + KEYFRAMES
    out = HERE / f"LockParts-{theme.capitalize()}.dc.html"
    out.write_text(page(f"Lock proof parts, First Light, {theme}", css, body, W, 1900))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build("day")
    build("night")
