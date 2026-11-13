"""Motion-Storyboard.dc.html: every named animation as stills. Start, middle, rest, and the
reduced-motion frame, with duration, delay, and easing beside them, and a score of the first 2.6 s.

Each still is the real animation, paused at an exact time (Clock(hold=ms)), not a redrawing.

  python3 storyboard.py
"""
from scenes import *

W = 1200
M = 48
FW = 258                 # frame width: four frames and three 24 px gutters fill the measure
GUT = 24
CW = W - 2 * M


def cap(kind, when):
    return (f'<div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px; {lab(MUTED)}">'
            f'<span style="color: {INK}; font-weight: 600">{kind}</span><span>{when}</span></div>')


def frame(inner, kind, when, h=None, w=FW):
    hs = f"height: {h}px; " if h else ""
    return (f'<div style="width: {w}px; flex: none; display: flex; flex-direction: column">'
            f'<div style="{hs}width: {w}px; position: relative; overflow: hidden">{inner}</div>{cap(kind, when)}</div>')


def row(n, name, voice, spec, curve, frames, note=""):
    nt = f'<p style="margin: 10px 0 0; {text(15, lh=1.4, italic=True)}; text-wrap: pretty; max-width: 760px">{note}</p>' if note else ""
    return (
        f'<section style="display: flex; flex-direction: column; padding-top: 14px; border-top: 0.75px solid {INK}; margin-top: 30px">'
        f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px">'
        f'<div style="display: flex; align-items: baseline; gap: 14px"><span style="{lab(MUTED, 600)}">{n}</span>'
        f'<h3 style="margin: 0; {disp(30, lh=1)}">{name} <span style="{disp(30, weight=300, stretch=100, lh=1.06, ls=-0.012, italic=True)}">{voice}</span></h3></div>'
        f'<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 2px">{ease_glyph(curve, size=18) if curve else ""}<div style="{lab(INK)}; text-align: right">{spec}</div></div>'
        f'</div>'
        f'<div style="display: flex; gap: {GUT}px; margin-top: 14px; align-items: flex-end">{"".join(frames)}</div>{nt}'
        f'</section>'
    )


H = lambda ms: Clock(hold=ms)
STILL = Clock(still=True)
_p = [0]


def pid():
    _p[0] += 1
    return f"s{_p[0]}"


# ------------------------------------------------------------------ rows
def r_press():
    f = lambda ck: f'<div style="padding: 6px 0 4px">{headline(ck, "day", size=30)}</div>'
    return row("01", "Press.", "Print lands.", "190 ms · delay 0, 50, 100 · cubic-bezier(0.2, 0, 0, 1)", PRESS, [
        frame(f(H(40)), "Start", "40 ms"), frame(f(H(110)), "Middle", "110 ms"),
        frame(f(H(290)), "Rest", "290 ms"), frame(f(STILL), "Reduced motion", "no animation")],
        "Opacity 0 to 1 and a 6 px rise, one line after another. At 200 ms the third line is at 89 percent, so the headline is readable inside the 200 ms rule.")


def r_wipe():
    f = lambda ck: plate(ck, pid(), "day", W=FW, M=12, MR=12)
    return row("02", "Ink wipe.", "The plate inks in.", "520 ms · delay 60 · cubic-bezier(0.2, 0, 0, 1)", PRESS, [
        frame(f(H(120)), "Start", "120 ms"), frame(f(H(180)), "Middle", "180 ms"),
        frame(f(H(580)), "Rest", "580 ms"), frame(f(STILL), "Reduced motion", "no animation")],
        "The edge of the wipe runs along the 72 degree screen angle. The pen point waits at the start of its path until 320 ms.")


def r_register():
    # zoom on the subject, with no wipe over it, so the two layers can be seen apart
    Z = 1.55
    cx, cy = 20 + 350 * 0.76, 62

    def f(ck):
        inner = plate(ck, pid(), "day", wipe=False, reg=True, live=False, target=(cx - 92, cy + 34))
        return (f'<div style="position: absolute; left: {FW / 2 - (cx - 34) * Z:.1f}px; top: {84 - cy * Z:.1f}px"><div style="zoom: {Z}">{inner}</div></div>')

    return row("03", "Register.", "Two layers lock.", "480 ms · delay 60 · cubic-bezier(0.16, 1, 0.3, 1)", REGISTER, [
        frame(f(H(60)), "Start", "60 ms", h=176), frame(f(H(100)), "Middle", "100 ms", h=176),
        frame(f(H(540)), "Rest", "540 ms", h=176), frame(f(STILL), "Reduced motion", "no animation", h=176)],
        "Shown at 1.55 times, with the wipe taken off and a target added for this proof: the cross is on the blue layer, the circle on the black. At 60 ms the blue layer is 5 px right and 3 px up, the black layer 5 px left and 3 px down. At 100 ms each is 2.9 px from home. At 540 ms they are locked. In the product the wipe hides most of this: it uncovers the subject between about 170 and 290 ms, when each layer is already within 1 px of home.")


def r_sweep():
    f = lambda ck: plate(ck, pid(), "day", W=FW, M=12, MR=12, layers=False)
    return row("04", "Sweep.", "A waveform, with Travel and the carriage.", "1900 ms · delay 320 · linear", "linear", [
        frame(f(H(320)), "Start", "320 ms"), frame(f(H(1500)), "Middle", "1500 ms"),
        frame(f(H(2220)), "Rest", "2220 ms"), frame(f(STILL), "Reduced motion", "no animation")],
        "Trap and core share one clock. The pen point leads, and the carriage sits under it on the ruler the whole way, because both ride the same path.")


def r_ring():
    f = lambda ck: plate_m87(ck, pid(), "day")
    return row("05", "Sweep.", "A ring, with Orbit.", "1800 ms · delay 380 · linear", "linear", [
        frame(f(H(380)), "Start", "380 ms"), frame(f(H(1280)), "Middle", "1280 ms"),
        frame(f(H(2180)), "Rest", "2180 ms"), frame(f(STILL), "Reduced motion", "no animation")],
        "Plate 3, the ring in galaxy M87, 42 microarcseconds across. No ruler and no carriage, because the ring is not plotted against an axis. The pen point leads alone, from 12 o'clock.")


def r_ruled():
    f = lambda ck: ruled(ck, pid(), "day", CW=FW, s=62.0, ry=132.0, short=True)
    return row("06", "Sweep.", "A ruled distance.", "1400 ms · delay 320 · linear", "linear", [
        frame(f(H(320)), "Start", "320 ms"), frame(f(H(1020)), "Middle", "1020 ms"),
        frame(f(H(1720)), "Rest", "1720 ms"), frame(f(STILL), "Reduced motion", "no animation")],
        "AlphaFold's 0.96 angstroms is ruled off against the ruler, so the carriage rides under the pen. The atom inks in with the wipe and the print Presses, both before the line starts.")


def r_pulse():
    Z = 2.0
    d, xm, crest = chirp(12, 157, FW - 24, 29)
    ex, ey = FW - 12, 157

    def f(ck, theme):
        t = T(theme)
        inner = plate(ck, pid(), theme, W=FW, M=12, MR=12, layers=False)
        return (f'<div style="position: absolute; left: 0; top: 0; width: {FW}px; height: 110px; background-color: {t["ground"]}"></div>'
                f'<div style="position: absolute; left: {FW - FW * Z:.1f}px; top: {58 - ey * Z:.1f}px"><div style="zoom: {Z}">{inner}</div></div>')

    return row("07", "Pulse.", "The one loop.", "2400 ms, loops · delay 2400 · ease-in-out", "ease-in-out", [
        frame(f(H(2400), "day"), "Start", "2400 ms, full", h=110), frame(f(H(3600), "day"), "Middle", "3600 ms, at 0.55", h=110),
        frame(f(H(3600), "night"), "Night", "3600 ms, halo holds", h=110), frame(f(STILL, "day"), "Reduced motion", "steady", h=110)],
        "Shown at 2 times. Only the pen point breathes. Its trap, and at night its halo, stay still, so the plate never shows through.")


def r_stamp():
    tap = 0

    def f(ck, on=True):
        return (f'<div style="padding: 10px 0 10px 20px; display: flex; width: 176px">'
                f'{picture(rate(PLUS, "More like this", "day", stamp=stamp_anim(ck, tap) if on else None))}</div>')

    return row("08", "Stamp.", "A rating tap.", "120 ms · on the tap · cubic-bezier(0.2, 0, 0, 1)", PRESS, [
        frame(f(H(0)), "Start", "0 ms, outline at 1.1"), frame(f(H(STAMP_HALF)), "Middle", f"{STAMP_HALF} ms, half strength"),
        frame(f(H(120)), "Rest", "120 ms, solid at 1"), frame(f(STILL), "Reduced motion", "the fill, at once")],
        "The whole button jumps to 1.1 on the tap and settles to 1 while its fill floods in across the whole surface at once. There is no wipe and no moving edge. The label and the icon change over at 60 ms, when the fill is four fifths in, so the words can be read in every frame. The stamped fill is one step under the primary slab and the plus becomes a check, as the feed boards draw it.")


def phone(ck, PH=760):
    """Feed to explainer. Fixed: the masthead, the card head, the plate, the readout. Moving: the sheet under them."""
    c, g = INK, STOCK
    k = FW / 390
    top = (
        f'<header style="padding: 8px 20px 0; display: flex; flex-direction: column"><div style="display: flex; align-items: center; gap: 10px">'
        f'<div style="padding-bottom: 4px">{wm(33)}</div>'
        f'<div style="margin-left: auto; text-align: right; {mono(LABSZ, color=MUTED, ls=0.06)}; line-height: 1.35">Science and math,<br>newly released</div>'
        f'<div style="width: 33px; height: 44px; display: flex; align-items: center; justify-content: flex-end">{THEME}</div></div>{double()}</header>'
        f'<div style="display: flex; align-items: center; gap: 6px; padding: 13px 20px 0">{tag_outline("Physics", c)}{tag_solid("Peer-reviewed", c, g)}{journal("Physical Review Letters", c)}</div>'
        f'<div style="padding: 10px 20px 0">{headline(STILL, "day")}</div>'
        f'<div style="margin-top: 12px">{plate(STILL, pid(), "day")}</div>{readout("day")}'
        f'<p style="margin: 0; padding: 10px 20px 0; height: 91px; overflow: hidden; flex: none; {text(16, lh=1.42)}; text-wrap: pretty">LIGO\'s two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>'
    )
    TOPH = 56 + 35 + 139 + 242 + 68 + 101
    D = PH - TOPH
    feed = (
        f'<div style="height: {D}px; overflow: hidden; flex: none">'
        f'<div style="display: flex; flex-direction: column; gap: 8px; padding: 14px 20px 0">{primary("See it explained", "day")}'
        f'<div style="display: flex; gap: 8px">{rate(PLUS, "More like this", "day", stamp=None)}{rate(MINUS, "Less like this", "day", stamp=None)}</div></div></div>'
    )
    expl = (
        f'<div style="height: {D}px; overflow: hidden; flex: none; padding: 0 20px">'
        f'<div style="margin-top: 40px; {lab(INK, 600)}">Key idea</div>'
        f'<p style="margin: 12px 0 0; {disp(30, weight=300, stretch=100, lh=1.06, ls=-0.012, italic=True)}; text-wrap: balance">The first direct detection of gravitational waves, and the first sight of two black holes merging.</p></div>'
    )
    move = ck.go(ck.shot(0, 360, "transform:translateY(0px)", f"transform:translateY(-{D}px)", PRESS))
    return (
        f'<div style="width: {FW}px; height: {PH * k:.0f}px; position: relative; overflow: hidden; outline: 0.75px solid {MUTED}; outline-offset: -0.75px">'
        f'<div style="width: 390px; height: {PH}px; transform: scale({k:.4f}); transform-origin: 0 0; background-color: {g}; display: flex; flex-direction: column; overflow: hidden">'
        f'{top}<div style="height: {D}px; overflow: hidden; flex: none"><div style="display: flex; flex-direction: column; transform: translateY(-{D}px){move}">{feed}{expl}</div></div>'
        f'</div></div>'
    ), PH * k


def r_feedup():
    frames = []
    for ck, kind, when in ((H(0), "Start", "0 ms, the tap"), (H(45), "Middle", "45 ms"), (H(360), "Rest", "360 ms"), (STILL, "Reduced motion", "a cut")):
        inner, h = phone(ck)
        frames.append(frame(inner, kind, when))
    return row("09", "Feed up.", "Feed to explainer.", "360 ms · on open · cubic-bezier(0.2, 0, 0, 1)", PRESS, frames,
               "The plate stays and the sheet feeds up under it. Drawn here with the card at the top of the screen. The spec holds only if the plate is read as the whole card head: tags, headline, plate, readout, summary. Those are the same on both screens. Otherwise the same headline leaves and comes back. It does not yet say what happens when the card is lower on the screen at the tap: see the notes with this board.")


# ------------------------------------------------------------------ the score
def score():
    span, x0 = 2600, 150.0
    w = CW - x0 - 60
    px = w / span
    rows = [("Press, line 1", 0, 190, "s"), ("Press, line 2", 50, 190, "s"), ("Press, line 3", 100, 190, "s"), ("Ink wipe", 60, 520, "s"),
            ("Register", 60, 480, "s"), ("Sweep", 320, 1900, "s"), ("Travel, carriage", 320, 1900, "s"), ("Pulse", 2400, 260, "l")]
    ax = len(rows) * 17 + 8
    out = ""
    for i, (label, start, length, kind) in enumerate(rows):
        y = i * 17 + 4
        a, b = x0 + start * px, x0 + (start + length) * px
        out += f'<text x="0" y="{y + 8.6}" fill="{INK}" style="{SVGLAB}">{label.upper()}</text>'
        if kind == "l":
            out += (f'<rect x="{a:.1f}" y="{y}" width="{b - a:.1f}" height="8" fill="url(#scs)"></rect>'
                    f'<path d="M{b:.1f} {y + 0.45}H{a + 0.45:.1f}V{y + 7.55}H{b:.1f}" fill="none" stroke="{INK}" stroke-width="0.9"></path>'
                    f'<text x="{a - 8:.1f}" y="{y + 8.6}" text-anchor="end" fill="{MUTED}" style="{SVGLAB}">2400 MS, LOOPS, RUNS ON</text>')
        else:
            out += (f'<rect x="{a:.1f}" y="{y}" width="{b - a:.1f}" height="8" fill="{INK}"></rect>'
                    f'<text x="{b + 8:.1f}" y="{y + 8.6}" fill="{MUTED}" style="{SVGLAB}">{start} TO {start + length} MS</text>')
    ticks = "".join(f'<line x1="{x0 + v * px:.1f}" y1="{ax}" x2="{x0 + v * px:.1f}" y2="{ax + (7 if v % 500 == 0 else 4)}"></line>' for v in range(0, span + 1, 100))
    tl = "".join(f'<text x="{x0 + v * px:.1f}" y="{ax + 20}" text-anchor="{"start" if v == 0 else "middle"}">{v}</text>' for v in range(0, 2501, 500))
    tl += f'<text x="{x0 + span * px + 10:.1f}" y="{ax + 20}">2600 MS</text>'
    drops = "".join(f'<line x1="{x0 + v * px:.1f}" y1="0" x2="{x0 + v * px:.1f}" y2="{ax}"></line>' for v in (200, 2220, 2600))
    notes = (f'<text x="{x0 + 200 * px + 6:.1f}" y="{ax - 6 - 17 * 4:.1f}" fill="{INK}" style="{SVGLAB}"></text>')
    return (
        f'<svg viewBox="0 0 {CW} {ax + 28}" width="{CW}" height="{ax + 28}" role="img" aria-label="Timeline of the first 2.6 seconds of a card arriving: three Press steps from 0 to 290 milliseconds, the ink wipe from 60 to 580, Register from 60 to 540, Sweep and Travel from 320 to 2220, and the pulse loop from 2400" style="display: block">'
        f'<defs>{patterns("sc", INK, tones={"s": (A1, 0.46)})}</defs>'
        f'<g stroke="{MUTED}" stroke-width="0.6" fill="none">{drops}</g>{out}{notes}'
        f'<g stroke="{INK}" stroke-width="0.9" fill="none"><line x1="{x0}" y1="{ax}" x2="{x0 + span * px:.1f}" y2="{ax}"></line>{ticks}</g>'
        f'<g fill="{INK}" style="{SVGLAB}">{tl}</g></svg>'
    )


def build():
    rows = [r_press(), r_wipe(), r_register(), r_sweep(), r_ring(), r_ruled(), r_pulse(), r_stamp(), r_feedup()]
    body = f"""<div style="width: {W}px; box-sizing: border-box; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column; padding: 16px {M}px 40px">
{double()}
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 9px">
<div style="{lab(INK, 600)}">Paperboy motion storyboard<span style="color: {MUTED}; font-weight: 500; margin-left: 14px">Three verbs and one loop, as stills</span></div>
<div style="{lab(MUTED)}">Every still is the real animation, paused at the time shown</div>
</div>
<h2 style="margin: 26px 0 0; {disp(66, lh=0.95)}">The first 2.6 seconds, <span style="{disp(66, weight=300, stretch=100, lh=0.95, ls=-0.012, italic=True)}">then one pulse.</span></h2>
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 22px">{L("Fig. 1", INK, 600)}{L("The score of a card arriving. Drop lines: readable by 200 ms, the line drawn at 2220, all at rest by 2600")}</div>
<div style="margin-top: 12px">{score()}</div>
{"".join(rows)}
</div>"""
    css = "body{margin:0;background:#E9E6DE}\na{color:#16130F}\n" + "\n".join(CSS) + "\n" + KEY_REDUCED
    out = PROJECT / "Motion-Storyboard.dc.html"
    import os
    out.write_text(page("Paperboy motion storyboard: start, middle, rest", css, body, W, int(os.environ.get("PB_SBH", "3760"))))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build()
