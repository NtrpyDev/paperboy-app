"""Motion.dc.html: the named animations of First Light, each looping in its own cell. 1200 by 1000.

  python3 motion.py            the looping specimen
  PB_HOLD=900 python3 motion.py    the same board frozen at 900 ms, written to scratch for checking
  PB_STILL=1 python3 motion.py     no animation at all: the reduced-motion frame
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
REST = Clock(still=True)


def cell_head(n, name, kind, theme="day"):
    """Cell title in the display face at 22 px, its number and its spec in mono."""
    t = T(theme)
    return (f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 14px">'
            f'<div style="display: flex; align-items: baseline; gap: 9px; white-space: nowrap"><span style="{lab(t["muted"], 600)}">{n}</span>'
            f'<h3 style="margin: 0; {disp(22, weight=t["hw"], lh=1.05)}; color: {t["text"]}">{name}</h3></div>'
            f'<div style="{lab(t["muted"])}; text-align: right">{kind}</div></div>')


def cell_wordmark():
    parts = (ck.press(0), ck.press(50), ck.press(100))
    tl = timeline(ck, "day", CWD, [("Paper", 0, 190, "solid"), ("boy", 50, 190, "solid"), ("Pen point", 100, 190, "solid")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("01", "The wordmark lands", "At app launch only")}'
            f'<div style="height: 100px; display: flex; align-items: flex-end; padding-bottom: 6px; box-sizing: border-box">{wm(76, parts=parts)}</div>'
            f'<div style="position: relative; margin-top: auto">{tl}<div style="position: absolute; right: 0; top: 1px; text-align: right; white-space: nowrap; {lab(MUTED)}">Press, 190 ms, 50 ms apart.<br>The dot lands last and rests.<br>It never pulses.</div></div></div>')


def cell_loading():
    y = 62
    d = f"M0 {y}L{CWD} {y}"
    line, car, pen = live_line(ck, d, "day")
    tl = timeline(ck, "day", CWD, [("Sweep 1900, linear", 320, 1900, "solid"), ("Pulse 2400, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("02", "The feed is loading", "Sweep, then Pulse")}'
            f'<div style="height: 124px; position: relative">'
            f'<div style="position: absolute; left: 0; top: 20px; {lab(INK, 600)}">Loading new papers</div>'
            f'<div style="position: absolute; right: 0; top: 20px; {lab(MUTED)}">No signal yet</div>'
            f'<svg viewBox="0 0 {CWD} 124" width="{CWD}" height="124" role="img" aria-label="Loading: a flat line is drawn across the sheet, then its pen point waits" style="position: absolute; left: 0; top: 0; overflow: visible">{line}{pen}</svg>'
            f'<div style="position: absolute; left: 0; top: 84px; white-space: nowrap; {lab(MUTED)}">A flat line: nothing to report yet.<br>The first card replaces it. No spinner.</div>'
            f'</div><div style="margin-top: auto">{tl}</div></div>')


def cell_card():
    c, g = INK, STOCK
    tl = timeline(ck, "day", 350, [("Press × 3", 0, 290, "solid"), ("Ink wipe 520", 60, 520, "solid"), ("Register 480", 60, 480, "solid"),
                                   ("Sweep and Travel 1900", 320, 1900, "solid"), ("Pulse, loops", 2400, 2400, "loop")])
    return (f'<div style="width: 390px; display: flex; flex-direction: column">'
            f'<div style="padding: 0 20px">{cell_head("03", "A card enters the feed", "0 to 2.6 s")}</div>'
            f'<div style="display: flex; align-items: center; gap: 6px; padding: 14px 20px 0">{tag_outline("Physics", c)}{tag_solid("Peer-reviewed", c, g)}{journal("Physical Review Letters", c)}</div>'
            f'<div style="padding: 10px 20px 0">{headline(ck, "day")}</div>'
            f'<div style="margin-top: 12px">{plate(ck, "cd", "day", BAND=150)}</div>'
            f'<div style="padding: 8px 20px 0">{tl}</div>'
            f'</div>')


def cell_hero():
    BW = RX - 24
    t = T("night")
    tl = timeline(ck, "night", CWD, [("Sweep 1900, linear", 320, 1900, "solid"), ("Travel, same clock", 320, 1900, "solid"), ("Pulse 2400, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {BW}px; background-color: {NG}; color: {NT}; display: flex; flex-direction: column; padding: 13px 0 12px">'
            f'<div style="padding: 0 24px 0 {M}px">{cell_head("04", "The trace draws in", "Sweep, Travel, the carriage, then Pulse", "night")}</div>'
            f'<div style="margin-top: 11px">{plate(ck, "hn", "night", W=BW, M=M, MR=24, layers=False)}</div>'
            f'<div style="display: flex; gap: 24px; align-items: flex-end; padding: 8px 24px 0 {M}px">'
            f'<div style="width: {CWD}px; flex: none">{tl}</div>'
            f'<p style="margin: 0 0 4px; flex: 1 1 0; {text(15, lh=1.4, italic=True)}; color: {NT}; text-wrap: pretty">Trap, halo, and core share one clock, so no ghost of the line runs ahead of the pen. The pen point and the carriage ride the same path.</p>'
            f'</div></div>')


def cell_chart():
    tl = timeline(ck, "day", CWD, [("Press 190, per mark", (0, 390, 1530), 190, "solid"), ("Ink wipe 520", 60, 520, "solid"), ("Sweep 1400, linear", 320, 1400, "solid"), ("Pulse, loops", 2400, 2400, "loop")])
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("05", "A chart draws in", "Press, Ink wipe, Sweep")}'
            f'<div style="margin-top: 12px; position: relative">{ruled(ck, "ru", "day", CWD, s=70.0, ry=160.0)}<div style="position: absolute; right: 0; bottom: 34px; text-align: right; {lab(MUTED)}">Illustration,<br>drawn to scale</div></div>'
            f'<div style="margin-top: auto">{tl}</div></div>')


def cell_stamp():
    tap = 600
    tl = timeline(ck, "day", CWD, [("Stamp 120", tap, 120, "solid")], marks=(("tap", tap),))
    frames = ""
    for ms, a, b in ((0, "0 ms, the tap", "Outline at 1.1"), (STAMP_HALF, f"{STAMP_HALF} ms", "Half strength at 1.05"), (120, "120 ms", "Solid at 1, a check")):
        frames += (f'<div style="display: flex; gap: 8px; align-items: center; padding-left: 9px"><div role="img" aria-label="More like this, held at {ms} milliseconds after the tap: {b.lower()}" style="flex: none; width: 158px; display: flex">{picture(rate(PLUS, "More like this", "day", stamp=stamp_anim(Clock(hold=tap + ms), tap)))}</div>'
                   f'<div style="flex: 1 1 0; padding-left: 14px; box-sizing: border-box; {lab(MUTED)}"><span style="color: {INK}; font-weight: 600">{a}</span><br>{b}</div></div>')
    return (f'<div style="width: {CWD}px; display: flex; flex-direction: column">'
            f'{cell_head("06", "More like this", "Stamp, 120 ms, on the tap")}'
            f'<div style="margin-top: 12px; display: flex; gap: 8px">{rate(PLUS, "More like this", "day", stamp=stamp_anim(ck, tap))}{rate(MINUS, "Less like this", "day", stamp=None)}</div>'
            f'<div style="margin-top: 9px; {lab(MUTED)}">The whole surface floods at once. Held frames:</div>'
            f'<div style="margin-top: 10px; display: flex; flex-direction: column; gap: 9px">{frames}</div>'
            f'<div style="margin-top: auto">{tl}</div></div>')


def greek(widths, pitch, h, color, top=0):
    """Text shown as rules: one bar per line, at the line pitch of the type it stands for."""
    return "".join(f'<div style="position: absolute; left: 20px; top: {top + i * pitch:.1f}px; width: {w}px; height: {h}px; background-color: {color}"></div>' for i, w in enumerate(widths))


def feedup_frame(hold, n, FW=108, FH=146):
    """One frame of Feed up, cut from the 390 px screen and shown small: the plate, its readout and the
    summary hold, and the sheet under them feeds up. The plate and the numerals are the real ones and
    the move is the real transition, paused. Running text is drawn as rules, since at this size it
    could not be read."""
    c, g = INK, STOCK
    k = FW / 390
    TOPH = 230 + 60 + 101
    D = round(FH / k) - TOPH
    fk = Clock(hold=hold)
    U = 1 / k                                  # units of the 390 px screen per px of the board
    top = (f'{plate(REST, f"fu{n}", "day", labels=False)}'
           f'<div style="position: relative; height: 60px; flex: none"><div style="position: absolute; left: 20px; top: 2px; {disp(44, lh=1)}; font-variant-numeric: lining-nums; white-space: nowrap">1.0{sign_times()}10<sup style="{SUP}">−21</sup></div>'
           f'{greek((168,), 0, 1.1 * U, MUTED, 50)}'
           f'<div style="position: absolute; right: 20px; top: 28px; width: 78px; height: {1.1 * U:.1f}px; background-color: {MUTED}"></div>'
           f'<div style="position: absolute; right: 20px; top: 50px; width: 62px; height: {1.1 * U:.1f}px; background-color: {MUTED}"></div></div>'
           f'<div style="position: relative; height: 101px; flex: none">{greek((350, 338, 346, 182), 22.7, 1.1 * U, MUTED, 20)}</div>')
    feed = (f'<div style="height: {D}px; overflow: hidden; flex: none; box-sizing: border-box; padding: 14px 20px 0; display: flex; flex-direction: column; gap: 8px">'
            f'<div style="height: 48px; background-color: {c}; flex: none"></div>'
            f'<div style="display: flex; gap: 8px; flex: none"><div style="flex: 1 1 0; height: 44px; box-sizing: border-box; border: {U:.1f}px solid {c}"></div><div style="flex: 1 1 0; height: 44px; box-sizing: border-box; border: {U:.1f}px solid {c}"></div></div>'
            f'</div>')
    expl = (f'<div style="position: relative; height: {D}px; overflow: hidden; flex: none">'
            f'{greek((64,), 0, 1.1 * U, c, 40)}{greek((322, 300, 338, 250), 31.8, 2 * U, c, 66)}</div>')
    move = fk.go(fk.shot(0, 360, "transform:translateY(0px)", f"transform:translateY(-{D}px)", PRESS))
    return (f'<div aria-hidden="true" style="width: {FW}px; height: {FH}px; position: relative; overflow: hidden; flex: none">'
            f'<div style="width: 390px; height: {TOPH + D}px; transform: scale({k:.4f}); transform-origin: 0 0; background-color: {g}; display: flex; flex-direction: column; overflow: hidden">'
            f'{top}<div style="height: {D}px; overflow: hidden; flex: none"><div style="display: flex; flex-direction: column; transform: translateY(-{D}px){move}">{feed}{expl}</div></div>'
            f'</div></div>')


def cell_feedup():
    FW, GAP = 108, 13
    up = round(bezier(0.2, 0, 0, 1, 0.5) * 100)
    frames = ""
    for n, (hold, a, b) in enumerate(((0, "0 ms", "The tap"), (180, "180 ms", f"{up} percent up"), (360, "360 ms", "At rest"))):
        frames += (f'<div style="display: flex; flex-direction: column; gap: 6px">{feedup_frame(hold, n, FW)}'
                   f'<div style="{lab(MUTED)}"><span style="color: {INK}; font-weight: 600">{a}</span><br>{b}</div></div>')
    return (f'<div style="width: 350px; display: flex; flex-direction: column" role="img" aria-label="Feed up, from feed to explainer, in three frames at 0, 180 and 360 milliseconds: the plate, its readout and the summary stay where they are while the sheet under them feeds up and the key idea replaces the buttons. Running text is drawn as rules.">'
            f'{cell_head("07", "Feed up", "The plate holds, 360 ms")}'
            f'<div style="margin-top: 10px; display: flex; gap: {GAP}px">{frames}</div></div>')


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
        out += (f'<div style="display: flex; align-items: center; gap: 10px; height: 20px; box-sizing: border-box; border-top: 0.75px solid {INK}">'
                f'<div style="{lab(INK, 600)}; flex: 1 1 0">{name}</div>'
                f'<div style="{lab(INK)}; width: 62px; text-align: right">{dur}</div>'
                f'<div style="{lab(MUTED)}; width: 96px; text-align: right">{delay}</div>'
                f'<div style="width: 30px; display: flex; justify-content: flex-end">{ease_glyph(curve, size=22, h=11)}</div></div>')
    return (f'<div style="width: 350px; display: flex; flex-direction: column">'
            f'{cell_head("08", "The whole set", "Duration, delay, curve")}'
            f'<div style="margin-top: 8px; display: flex; flex-direction: column; border-bottom: 0.75px solid {INK}">{out}</div>'
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

<div style="position: absolute; left: {M}px; top: 60px; display: flex; gap: 24px; height: 216px">{cell_wordmark()}{cell_loading()}</div>
<div style="position: absolute; left: {RX}px; top: 60px">{cell_card()}</div>
<div style="position: absolute; left: 0; top: 282px">{cell_hero()}</div>
<div style="position: absolute; left: {M}px; top: 672px; display: flex; gap: 24px; height: 312px">{cell_chart()}{cell_stamp()}</div>
<div style="position: absolute; left: {RX + 20}px; top: 582px">{cell_feedup()}</div>
<div style="position: absolute; left: {RX + 20}px; top: 808px">{ledger()}</div>
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
