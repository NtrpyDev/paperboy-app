"""Motion.dc.html: the named animations of First Light, each looping in its own cell. 1200 by 1000.

  python3 motion.py            the looping specimen
  PB_HOLD=900 python3 motion.py    the same board frozen at 900 ms, written to scratch for checking
"""
import os

from scenes import *

W, H = 1200, 1000
M = 48
CWD = 357                   # cell width
RX = 810                    # the card column starts here and bleeds off the right edge
HOLD = os.environ.get("PB_HOLD")
STILL = os.environ.get("PB_STILL")
ck = Clock(hold=float(HOLD) if HOLD else None, still=bool(STILL))


def cell_head(n, name, kind, theme="day"):
    t = T(theme)
    return head(n, name, kind, t["text"], t["muted"])


def cell_wordmark():
    parts = (ck.press(0), ck.press(50), ck.go(ck.shot(100, 190, "opacity:0;transform:translateY(6px)", "opacity:1;transform:none", PRESS), ck.pulse()))
    tl = timeline(ck, "day", CWD, [("Paper", 0, 190, "solid"), ("boy", 50, 190, "solid"), ("Pen point", 100, 190, "solid"), ("Pulse 2400, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("01", "The wordmark lands", "Press, 190 ms, 50 ms apart")}'
            f'<div style="height: 112px; display: flex; align-items: center">{wm(76, parts=parts)}</div>'
            f'{tl}</div>')


def cell_loading():
    y = 58
    d = f"M0 {y}L{CWD} {y}"
    line, car, pen = live_line(ck, d, "day")
    tl = timeline(ck, "day", CWD, [("Sweep 1900, linear", 320, 1900, "solid"), ("Pulse 2400, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("02", "The feed is loading", "Sweep, then Pulse")}'
            f'<div style="height: 112px; position: relative">'
            f'<div style="position: absolute; left: 0; top: 16px; {lab(INK, 600)}">Loading new papers</div>'
            f'<div style="position: absolute; right: 0; top: 16px; {lab(MUTED)}">No signal yet</div>'
            f'<svg viewBox="0 0 {CWD} 112" width="{CWD}" height="112" role="img" aria-label="Loading: a flat line is drawn across the sheet, then its pen point waits" style="position: absolute; left: 0; top: 0; overflow: visible">{line}{pen}</svg>'
            f'</div>{tl}</div>')


def cell_card():
    c, g = INK, STOCK
    tl = timeline(ck, "day", 350, [("Press × 3", 0, 290, "solid"), ("Ink wipe 520", 60, 520, "solid"), ("Register 480", 60, 480, "solid"),
                                   ("Sweep and Travel 1900", 320, 1900, "solid"), ("Pulse, loops", 2400, 2400, "loop")])
    return (f'<div style="width: 390px; display: flex; flex-direction: column">'
            f'<div style="padding: 0 20px">{cell_head("03", "A card enters the feed", "Arrival, 0 to 2.6 s")}</div>'
            f'<div style="margin: 12px 20px 0; height: 0.75px; background-color: {c}"></div><div style="margin: 2px 20px 0; height: 3px; background-color: {c}"></div>'
            f'<div style="display: flex; align-items: center; gap: 6px; padding: 13px 20px 0">{tag_outline("Physics", c)}{tag_solid("Peer-reviewed", c, g)}{journal("Physical Review Letters", c)}</div>'
            f'<div style="padding: 10px 20px 0">{headline(ck, "day")}</div>'
            f'<div style="margin-top: 12px">{plate(ck, "cd", "day")}</div>'
            f'<div style="padding: 10px 20px 0">{tl}</div>'
            f'</div>')


def cell_hero():
    BW = RX - 24
    t = T("night")
    tl = timeline(ck, "night", CWD, [("Sweep 1900, linear", 320, 1900, "solid"), ("Travel, same clock", 320, 1900, "solid"), ("Pulse 2400, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {BW}px; background-color: {NG}; color: {NT}; display: flex; flex-direction: column; padding: 14px 0 12px">'
            f'<div style="padding: 0 24px 0 {M}px">{cell_head("04", "The trace draws in", "Sweep, Travel, the carriage, then Pulse", "night")}</div>'
            f'<div style="margin-top: 12px">{plate(ck, "hn", "night", W=BW, M=M, MR=24, layers=False)}</div>'
            f'<div style="display: flex; gap: 24px; align-items: flex-end; padding: 10px 24px 0 {M}px">'
            f'<div style="width: {CWD}px; flex: none">{tl}</div>'
            f'<p style="margin: 0 0 4px; flex: 1 1 0; {text(15, lh=1.4, italic=True)}; color: {NT}; text-wrap: pretty">Trap, halo, and core share one clock, so no ghost of the line runs ahead of the pen. The pen point and the carriage ride the same path.</p>'
            f'</div></div>')


def cell_chart():
    tl = timeline(ck, "day", CWD, [("Press 190", 0, 190, "solid"), ("Ink wipe 520", 60, 520, "solid"), ("Sweep 1400, linear", 320, 1400, "solid"), ("Pulse, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("05", "A chart draws in", "Illustration, drawn to scale")}'
            f'<div style="margin-top: 12px">{ruled(ck, "ru", "day", CWD, s=78.0)}</div>'
            f'<div style="margin-top: 8px">{tl}</div></div>')


def cell_stamp():
    tap = 600
    tl = timeline(ck, "day", CWD, [("Stamp 120", tap, 120, "solid")], marks=(("tap", tap),))
    frozen = "".join(
        f'<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 6px"><div style="display: flex">{rate(PLUS, "More like this", "day", stamp=stamp_anim(Clock(hold=tap + ms), tap))}</div>'
        f'<div style="{lab(MUTED)}">{note}</div></div>' for ms, note in ((12, "12 ms after the tap"), (36, "36 ms"))
    )
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("06", "More like this", "Stamp, 120 ms, on the tap")}'
            f'<div style="margin-top: 12px; display: flex; flex-direction: column; gap: 8px">{primary("See it explained", "day")}'
            f'<div style="display: flex; gap: 8px">{rate(PLUS, "More like this", "day", stamp=stamp_anim(ck, tap))}{rate(MINUS, "Less like this", "day", stamp=None)}</div></div>'
            f'<div style="margin-top: 22px; display: flex; gap: 8px">{frozen}</div>'
            f'<div style="margin-top: 8px; {lab(MUTED)}">Slab inks in at 1.1, settles to size</div>'
            f'<div style="margin-top: auto">{tl}</div></div>')


def ledger():
    rows = [
        ("Press", "190 ms", "0, 50, 100", PRESS),
        ("Ink wipe", "520 ms", "60", PRESS),
        ("Register", "480 ms", "60", REGISTER),
        ("Sweep, Travel", "1900 ms", "320", "linear"),
        ("Pulse", "2400 ms", "2400, loops", "ease-in-out"),
        ("Stamp", "120 ms", "on the tap", PRESS),
        ("Feed up", "360 ms", "on open", PRESS),
    ]
    out = ""
    for name, dur, delay, curve in rows:
        out += (f'<div style="display: flex; align-items: center; gap: 10px; padding: 5px 0 5px; border-top: 0.75px solid {INK}">'
                f'{ease_glyph(curve)}'
                f'<div style="{lab(INK, 600)}; flex: 1 1 0">{name}</div>'
                f'<div style="{lab(INK)}; width: 62px; text-align: right">{dur}</div>'
                f'<div style="{lab(MUTED)}; width: 104px; text-align: right">{delay}</div></div>')
    return (f'<div style="width: 350px; display: flex; flex-direction: column">'
            f'{head("07", "The whole set", "Duration, delay in ms")}'
            f'<div style="margin-top: 10px; display: flex; flex-direction: column">{out}</div>'
            f'<div style="border-top: 0.75px solid {INK}; padding-top: 7px; {lab(MUTED)}; line-height: 1.45">Curves plot progress against time.<br>None rises past its end: nothing overshoots.</div>'
            f'</div>')


def build():
    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}">

<header style="position: absolute; left: {M}px; right: {M}px; top: 16px; display: flex; flex-direction: column">
{double()}
<div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 9px">
<div style="{lab(INK, 600)}">Paperboy motion<span style="color: {MUTED}; font-weight: 500; margin-left: 14px">Three verbs and one loop. Print is still. One line moves.</span></div>
<div style="{lab(MUTED)}">Each cell replays every 5.4 s here. In the product each runs once.</div>
</div>
</header>

<div style="position: absolute; left: {M}px; top: 62px; display: flex; gap: 24px">{cell_wordmark()}{cell_loading()}</div>
<div style="position: absolute; left: {RX}px; top: 62px">{cell_card()}</div>
<div style="position: absolute; left: 0; top: 296px">{cell_hero()}</div>
<div style="position: absolute; left: {M}px; top: 694px; display: flex; gap: 24px; height: 290px">{cell_chart()}{cell_stamp()}</div>
<div style="position: absolute; left: {RX + 20}px; top: 664px">{ledger()}</div>
</div>"""
    css = "body{margin:0}\na{color:#16130F}\n" + "\n".join(CSS) + "\n" + KEY_REDUCED
    if HOLD or STILL:
        out = HERE / "hold" / (f"Motion-t{HOLD}.dc.html" if HOLD else "Motion-still.dc.html")
        out.parent.mkdir(exist_ok=True)
    else:
        out = PROJECT / "Motion.dc.html"
    out.write_text(page("Paperboy motion: the named animations", css, body, W, H))
    print("wrote", out, out.stat().st_size)


if __name__ == "__main__":
    build()
