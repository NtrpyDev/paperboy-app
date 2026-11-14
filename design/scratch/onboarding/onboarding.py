"""The first screen of a new install: pick your fields. And where fields are changed later.

  python3 onboarding.py            writes three boards into design/canvas/project/
  python3 onboarding.py takes      also writes the two takes that were not picked into scratch/onboarding/hold/
  PB_BOARDS=/some/dir python3 onboarding.py   writes the boards somewhere else

Boards:
  Onboarding-B-Day / -Night    the chosen screen: a grid of eleven drawings, one per field
  Onboarding-Reentry-Day       where fields are changed later: a row in About

Each board of the chosen screen is one row of four 390 by 844 phones, 40 px apart: the first
time the app opens (every field selected), a few fields deselected, only one left (it cannot
be deselected), and the same screen opened later from About (a top bar with a back control, the
saved fields, a Save button).

History: three takes were drawn on 2026-11-13 (A the index, B the grid of drawings, C the
headline). The owner picked B and rewrote its words. The code for A and C stays here
(a_screen, c_screen, take_board) and is no longer written to the canvas.

Built from the locked parts and nothing else: tokens, type helpers and icons from
scratch/engraved/lib.py, the Kit from scratch/feed/app_feed.py, and the head row, the 48 px
button, the rating stamp, the top bar and the double rule from scratch/states/states.py.
None of those files is changed. The eleven drawings are in emblems.py.

Facts: the eleven field labels and wire values, the rules of the screen, and every word on
it come from the owner's brief. The one number on a screen is the count of selected fields
in the About row, which matches the "a few deselected" selection drawn on the boards.
"""
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "states"))
from states import *  # noqa: E402,F403  (Kit, root, css, page, slug_row, button, rate, topbar, double, lib)
from emblems import EH, EW, Style, emblem  # noqa: E402

DESIGN = _HERE.parents[1]
BOARDS = pathlib.Path(os.environ.get("PB_BOARDS") or DESIGN / "canvas" / "project")

# The fields, in the order the app shows them: (wire value, label).
FIELDS = [
    ("physics", "Physics"), ("space", "Space"), ("math", "Math"), ("cs", "Computer science"),
    ("biology", "Biology"), ("neuroscience", "Neuroscience"), ("medicine", "Medicine"),
    ("chemistry", "Chemistry"), ("earth", "Earth"), ("engineering", "Engineering"),
    ("social", "Social science"),
]
SOME_OUT = {"biology", "medicine", "chemistry", "social"}
ONE_LEFT = {w for w, _ in FIELDS} - {"math"}

# (key, slug, what the slug's second line says, the fields left out, the head row's state)
STATES = [
    ("all", "First seen", "A new install opens here. Every field starts in.", set(), "Every field in"),
    ("some", "Several fields left out", "Biology, Medicine, Chemistry, Social science are out.", SOME_OUT, "Some left out"),
    ("one", "One field left", "The last field cannot be taken out.", ONE_LEFT, "One field left"),
]

HOW = {
    "A": "Tap a field to strike it. A struck field never shows in your feed. You can change this later.",
    "B": "Tap a plate to blank it. A blank field never shows in your feed. You can change this later.",
    "C": "Take a field out and it never shows in your feed. You can change this later.",
}
LAST = "One field has to stay in. Put another back to take this one out."
GO = "Open the feed"



# ------------------------------------------------------------------ shared parts
def top(k, state):
    """The feed masthead, then the head row: what this is, and its state."""
    return k.masthead(top=TOP) + slug_row(k, "Your fields", state, top=15, name="head")


def head(k, lines, size=44):
    return k.headline(lines, size=size, lh=0.98 if size == 44 else 1.02).replace("padding: 10px", "padding: 8px", 1).replace("<h2 ", f'<h2{m("headline")} ', 1)


def say(k, s):
    return k.summary(s).replace("<p ", f'<p{m("sentence")} ', 1)


def foot(k, pinned=True):
    """The one action. It leads to the feed. Pinned to the foot of the screen."""
    push = "margin-top: auto; " if pinned else ""
    return f'<div{m("foot")} style="{push}flex: none; padding: 14px {M}px 20px">{button(k, GO, name="go")}</div>'


def pressed(on, locked=False):
    return f'aria-pressed="{"true" if on else "false"}"' + (' aria-disabled="true"' if locked else "")


def stays(k):
    return f'<span style="{k.label(color=k.c, weight=600)}; white-space: nowrap">Stays in</span>'


# ------------------------------------------------------------------ take A: the index
def a_row(k, name, out, locked):
    """One line of the index. In: the first voice, and a check. Struck: the line turns to the
    second voice in the muted color, a 1.4 px rule runs through it, and the label says so."""
    box = (f"width: 100%; min-height: 44px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; "
           f"gap: 12px; padding: 0 0 2px; margin: 0; background-color: transparent; border: 0; border-top: 0.75px solid {k.ch}; "
           f"border-radius: 0; color: {k.c}; cursor: pointer; text-align: left")
    if out:
        left = (f'<span style="position: relative; {k.voice2(30, 1)}; color: {k.mu}">{name}'
                f'<span aria-hidden="true" style="position: absolute; left: -4px; right: -5px; top: 58%; height: 1.4px; background-color: {k.c}"></span></span>')
        right = f'<span style="{k.label()}; white-space: nowrap">Left out</span>'
    else:
        left = f'<span style="{disp(30, weight=k.hw, lh=1)}">{name}</span>'
        right = f'<span style="display: inline-flex; align-items: center; gap: 8px">{stays(k) if locked else ""}{CHECK}</span>'
    return f'<button type="button"{m("row")} {pressed(not out, locked)} style="{box}">{left}{right}</button>'


def a_screen(k, key, out, state):
    one = key == "one"
    rows = "".join(a_row(k, name, wire in out, one and wire not in out) for wire, name in FIELDS)
    index = (f'<div{m("index")} style="display: flex; flex-direction: column; flex: none; margin: 12px {M}px 0; border-bottom: 0.75px solid {k.ch}">{rows}</div>')
    return root(k, top(k, state)
                + head(k, [[("Every field is in.", False)], [("Strike any out.", True)]])
                + say(k, LAST if one else HOW["A"]) + index + foot(k))


# ------------------------------------------------------------------ the chosen screen (was take B)
# The owner picked this one on 2026-11-13 and rewrote its words, twice. Every string a reader
# sees is his, verbatim. The screen's vocabulary is "select" and "deselect" and nothing else:
# no "print", "plate", "blank", "on", "off", "in" or "out". The drawings in emblems.py are unchanged.
PICK_HEAD = [[("Pick your fields.", False)], [("Deselect the rest.", True)]]
PICK_HOW = "Tap an icon to deselect it. Deselected fields never show in your feed. You can change this later."
PICK_LAST = "One field has to stay selected."
PICK_STAYS = "Stays selected"
BODY_LINES = int(os.environ.get("PB_BODY_LINES", 3))   # lines the body holds in every state, so the grid does not move
PICK_GO, PICK_SAVE = "Open the feed", "Save"
# (key, the note above the phone, fields that are off, the status at the top right, how it was opened)
PICK_STATES = [
    ("all", "1. First time the app opens: every field is selected", set(), "All selected", "first"),
    ("some", "2. A few fields deselected", SOME_OUT, "Some deselected", "first"),
    ("one", "3. Only one left: it cannot be deselected", ONE_LEFT, "One left", "first"),
    ("later", "4. Opened later from About, to change fields", SOME_OUT, "Some deselected", "later"),
]
CAP = 10     # the `tag` size (SYSTEM 2.3). At 10.5 "Computer science" was 104 px in a 110 px column.


def style(k):
    """Colors for emblems.py. A deselected field is a hairline in the muted color by day and
    in the structure color at night."""
    return Style(PLATE_D if k.day else PLATE_N, k.ch, k.g, k.mu if k.day else NS, hair=0.5 if k.day else 0.6)


def cap(k, on=True):
    """The small caps of the grid: a field's name and the key."""
    return f"{mono(CAP, color=k.c if on else k.mu, weight=600 if on else 500, ls=0.06)}; line-height: 1.3; white-space: nowrap"


def b_cell(k, s, pid, wire, name, out, locked):
    """One field. Selected: its drawing, under a heavy rule, its name in the text color.
    Deselected: only the drawing's outline as a hairline, the rule over it thins to a hairline,
    and the name steps down to the muted color. The heavy rule and the hairline are the two
    halves of the double rule (SYSTEM section 6). The whole cell is the button.
    locked: the last selected field. "Stays selected" does not fit beside a name in a 110 px
    column, so it takes its own line under the name, at the label size (10.5). The drawings of
    a row sit on one line at the foot of their cells, so that row grows by 14 px and stays level."""
    rule, gap = (0.75, 10.25) if out else (3, 8)
    box = (f"display: flex; flex-direction: column; align-items: stretch; min-width: 0; padding: 0; margin: 0; "
           f"background-color: transparent; border: 0; border-radius: 0; color: {k.c}; cursor: pointer; text-align: left")
    line = "height: 14px; flex: none; display: flex; align-items: center"
    stays = f'<span{m("stays")} style="{line}; {k.label(color=k.c, weight=600)}; white-space: nowrap">{PICK_STAYS}</span>' if locked else ""
    return (f'<button type="button"{m("plate")} {pressed(not out, locked)} style="{box}">'
            f'<span aria-hidden="true" style="display: block; flex: none; height: {rule}px; background-color: {k.ch}"></span>'
            f'<span style="display: flex; flex-direction: column; flex: none; margin: {gap}px 0 6px">'
            f'<span style="{line}"><span{m("cap")} style="{cap(k, not out)}">{name}</span></span>{stays}</span>'
            f'<span style="display: block; flex: none; margin-top: auto">{emblem(wire, pid, s, ghost=out)}</span></button>')


def b_key(k, s, pid):
    """The twelfth cell: the key (SYSTEM 4.2 rule 7: a 22 by 10 swatch and a label)."""
    inked = (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true" style="flex: none"><defs>{patterns(pid, s.P)}</defs>'
             f'<rect x="0.45" y="0.45" width="21.1" height="9.1" fill="url(#{pid}a3)" stroke="{k.ch}" stroke-width="0.9"></rect></svg>')
    blank = (f'<svg width="22" height="10" viewBox="0 0 22 10" aria-hidden="true" style="flex: none">'
             f'<rect x="0.45" y="0.45" width="21.1" height="9.1" fill="none" stroke="{s.GC}" stroke-width="0.9"></rect></svg>')
    line = lambda sw, t: f'<span style="display: flex; align-items: center; gap: 6px; {cap(k, False)}">{sw}<span>{t}</span></span>'
    return (f'<div{m("key")} style="display: flex; flex-direction: column; gap: 8px">'
            f'<span aria-hidden="true" style="display: block; flex: none; height: 0.75px; background-color: {k.ch}; margin-bottom: 1.25px"></span>'
            f'<span style="{cap(k)}; height: 14px; display: flex; align-items: center">Key</span>'
            f'{line(inked, "Selected")}{line(blank, "Deselected")}</div>')


def about_bar(k):
    """The top bar of SYSTEM 9.2 as About uses it (states.topbar), with the back control
    leading to About, where this screen was opened from."""
    return topbar(k).replace('href="#feed"', 'href="#about"', 1).replace("<span>Feed</span>", "<span>About</span>", 1)


def b_screen(k, key, out, state, opened="first"):
    """opened: "first" is the first screen of a new install, under the feed masthead, and its
    button opens the feed. "later" is the same screen reached from About: the top bar with a
    back control, the saved fields, and the button saves."""
    one = key == "one"
    s = style(k)
    cells = "".join(b_cell(k, s, f"b{k.theme[0]}{key[0]}{i}", wire, name, wire in out, one and wire not in out)
                    for i, (wire, name) in enumerate(FIELDS))
    sheet = (f'<div{m("sheet")} style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: 10px; row-gap: 10px; '
             f'flex: none; margin: 12px {M}px 0">{cells}{b_key(k, s, f"b{k.theme[0]}{key[0]}k")}</div>')
    bar = k.masthead(top=TOP) if opened == "first" else about_bar(k)
    # the body holds the same number of lines in every state, so the grid never moves when the words change
    body = say(k, PICK_LAST if one else PICK_HOW).replace("margin: 0;", f"margin: 0; box-sizing: border-box; min-height: {10 + BODY_LINES * 22.72:.2f}px; flex: none;", 1)
    go = f'<div{m("foot")} style="margin-top: auto; flex: none; padding: 14px {M}px 20px">{button(k, PICK_GO if opened == "first" else PICK_SAVE, name="go")}</div>'
    return root(k, bar + slug_row(k, "Your fields", state, top=15, name="head") + head(k, PICK_HEAD) + body + sheet + go)


# ------------------------------------------------------------------ take C: the headline
C_HEAD = {
    "all": [[("Every field.", False)], [("Nothing left out.", True)]],
    "some": [[("Everything but", False)], [("biology, medicine,", True)], [("chemistry, and", True)], [("social science.", True)]],
    "one": [[("Only ", False), ("math.", True)]],
}


def c_screen(k, key, out, state):
    """The headline reads the picks back as one sentence. Under it, held to the foot of the
    screen so they never move when the headline grows, eleven stamps (the rating stamp of
    SYSTEM 9.7, here with any number stamped at once)."""
    one = key == "one"
    stamps = ""
    for wire, name in FIELDS:
        b = (rate(k, PLUS, name, on=wire not in out)
             .replace("flex: 1 1 0; ", "min-width: 0; white-space: nowrap; ", 1)
             .replace("padding: 0 12px", "padding: 0 6px", 1)
             .replace('<svg width="14" height="14"', '<svg width="14" height="14" style="flex: none"', 1)
             .replace("<button ", f'<button{m("stamp")} ', 1))
        if one and wire not in out:
            b = b.replace('aria-pressed="true"', 'aria-pressed="true" aria-disabled="true"', 1)
        stamps += b
    grid = (f'<div{m("stamps")} style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; flex: none; '
            f'margin: 14px {M}px 0">{stamps}</div>')
    tool = (f'<div{m("tool")} style="margin-top: auto; flex: none; display: flex; flex-direction: column">'
            f'{k.divider().replace("margin: 18px", "margin: 0px", 1)}{say(k, LAST if one else HOW["C"])}{grid}{foot(k, pinned=False)}</div>')
    return root(k, top(k, state) + head(k, C_HEAD[key]) + tool)


TAKES = {
    "A": ("the index", a_screen,
          "Eleven lines of type. In is the first voice with a check, out is the second voice, struck.",
          "Nothing scrolls at 844. On a shorter phone the index scrolls and the button stays."),
    "C": ("the headline", c_screen,
          "The headline reads the picks back. The stamps are the rating stamp, any number at once.",
          "The sentence and the stamps are held to the foot, so they do not move when the headline grows."),
}


# ------------------------------------------------------------------ where fields are changed later
REENTRY_H = int(os.environ.get("PB_REENTRY_H", 352))


def reentry_screen(k):
    """The top of About with one new row, Fields, right under the title. The row's status
    counts the selected fields in the "a few deselected" selection drawn on the boards. Only the
    top of About is drawn: the rest of About follows the row unchanged."""
    slug = lambda s: f'<div style="{k.label(color=k.c, weight=600)}">{s}</div>'
    lab = lambda s: f'<div style="{k.label()}; text-align: right">{s}</div>'
    on = len(FIELDS) - len(SOME_OUT)
    row = (f'<a href="#fields"{m("row")} style="margin-top: 28px; min-height: 48px; box-sizing: border-box; display: flex; align-items: center; '
           f'justify-content: space-between; gap: 12px; border-top: 0.75px solid {k.ch}; border-bottom: 0.75px solid {k.ch}; color: {k.c}; text-decoration: none">'
           f'<span style="display: inline-flex; align-items: baseline; gap: 10px">'
           f'<span style="{disp(23, weight=700, stretch=75, lh=1, ls=0.005)}">Fields</span>'
           f'<span style="{k.label()}; white-space: nowrap">{on} of {len(FIELDS)} selected</span></span>{ARROW}</a>')
    body = (
        f'<div{m("about-head")} style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding-top: 15px">{slug("About")}{lab("Version " + VERSION)}</div>'
        f'<h1 style="margin: 10px 0 0; {disp(44, weight=k.hw, lh=0.98)}">'
        f'<span style="display: block">New science</span><span style="display: block">and math papers,</span>'
        f'<span style="display: block; white-space: nowrap; {k.voice2(44, 0.98)}">explained visually.</span></h1>'
        + row
    )
    return (f'<div style="width: {W}px; height: {REENTRY_H}px; box-sizing: border-box; overflow: hidden; position: relative; '
            f'background-color: {k.g}; color: {k.c}; display: flex; flex-direction: column">'
            f'{topbar(k)}<main style="display: flex; flex-direction: column; padding: 0 {M}px">{body}</main></div>')


# ------------------------------------------------------------------ boards
PAD, GAP, SLUG_H, HEAD_H = 40, 40, 44, 46


def frame(k, i, name, when, markup):
    return (f'<div style="width: {W}px; flex: none; display: flex; flex-direction: column">'
            f'<div style="height: {SLUG_H}px; display: flex; flex-direction: column; justify-content: flex-end; gap: 3px">'
            f'<div style="{k.label(color=k.c, weight=600)}"><span style="color: {k.mu}">{i:02d}</span>&nbsp; {name}</div>'
            f'<div style="{k.label()}">{when}</div></div>'
            f'<div data-screen="{i:02d}" style="margin-top: 12px; outline: 1px solid {k.ch}">{markup}</div></div>')


def take_board(theme, take):
    k = Kit(theme)
    name, screen, blurb, note = TAKES[take]
    cols = [frame(k, i, slug, when, screen(k, key, out, state)) for i, (key, slug, when, out, state) in enumerate(STATES, start=1)]
    n = len(cols)
    bw = 2 * PAD + n * W + (n - 1) * GAP
    bh = PAD + HEAD_H + 28 + SLUG_H + 12 + H + PAD
    headrow = (
        f'{double(k)}'
        f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 24px; margin-top: 12px">'
        f'<div style="display: flex; align-items: baseline; gap: 14px"><div style="{k.label(color=k.c, weight=600)}; white-space: nowrap">First run, take {take}: {name}, {theme}</div>'
        f'<div style="{k.label()}">{blurb}</div></div>'
        f'<div style="{k.label()}; text-align: right">{note}</div></div>'
    )
    body = (f'<div style="width: {bw}px; height: {bh}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {k.g}; color: {k.c}; '
            f'font-family: {TEXT}; padding: {PAD}px; display: flex; flex-direction: column">'
            f'<div style="height: {HEAD_H}px; flex: none; display: flex; flex-direction: column">{headrow}</div>'
            f'<div style="display: flex; gap: {GAP}px; margin-top: 28px">{"".join(cols)}</div></div>')
    return body, bw, bh


# The boards of the chosen screen. The small caps above each phone are notes for the owner,
# in plain English. They are not app copy.
NOTE_H = 16


def note_frame(k, i, note, markup):
    cap_ = f'<div style="height: {NOTE_H}px; display: flex; align-items: flex-end; {k.label(color=k.c, weight=600)}">{note}</div>' if note else ""
    return (f'<div style="width: {W}px; flex: none; display: flex; flex-direction: column">{cap_}'
            f'<div data-screen="{i:02d}" style="margin-top: {12 if note else 0}px; outline: 1px solid {k.ch}">{markup}</div></div>')


def pick_board(theme):
    k = Kit(theme)
    cols = [note_frame(k, i, note, b_screen(k, key, out, state, opened))
            for i, (key, note, out, state, opened) in enumerate(PICK_STATES, start=1)]
    n = len(cols)
    bw = 2 * PAD + n * W + (n - 1) * GAP
    bh = PAD + 32 + 28 + NOTE_H + 12 + H + PAD
    headrow = (
        f'{double(k)}'
        f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 24px; margin-top: 12px">'
        f'<div style="{k.label(color=k.c, weight=600)}">First screen: pick your fields ({theme})</div>'
        f'<div style="{k.label()}; text-align: right">On a short phone the list scrolls and the button stays put.</div></div>'
    )
    body = (f'<div style="width: {bw}px; height: {bh}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {k.g}; color: {k.c}; '
            f'font-family: {TEXT}; padding: {PAD}px; display: flex; flex-direction: column">'
            f'<div style="height: 32px; flex: none; display: flex; flex-direction: column">{headrow}</div>'
            f'<div style="display: flex; gap: {GAP}px; margin-top: 28px">{"".join(cols)}</div></div>')
    return body, bw, bh


RE_HEAD_H = 32


def reentry_board(theme="day"):
    k = Kit(theme)
    bw = 2 * PAD + W
    bh = PAD + RE_HEAD_H + 28 + REENTRY_H + PAD
    headrow = (
        f'{double(k)}'
        f'<div style="{k.label(color=k.c, weight=600)}; margin-top: 12px">Where you change fields later: a row in About</div>'
    )
    body = (f'<div style="width: {bw}px; height: {bh}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {k.g}; color: {k.c}; '
            f'padding: {PAD}px; display: flex; flex-direction: column">'
            f'<div style="height: {RE_HEAD_H}px; flex: none; display: flex; flex-direction: column">{headrow}</div>'
            f'<div style="display: flex; margin-top: 28px">{note_frame(k, 1, "", reentry_screen(k))}</div></div>')
    return body, bw, bh


def main():
    """Writes the two boards of the chosen screen and the About row board. `takes` as an
    argument also writes the two takes that were not picked (A and C) into scratch/onboarding/hold,
    never onto the canvas."""
    for theme in ("day", "night"):
        body, bw, bh = pick_board(theme)
        path = BOARDS / f"Onboarding-B-{theme.capitalize()}.dc.html"
        path.write_text(page(f"Pick your fields, {theme}", css(theme), body, bw, bh))
        print("wrote", path, path.stat().st_size, bw, bh)
    body, bw, bh = reentry_board("day")
    path = BOARDS / "Onboarding-Reentry-Day.dc.html"
    path.write_text(page("Where you change fields later", css("day"), body, bw, bh))
    print("wrote", path, path.stat().st_size, bw, bh)
    if "takes" in sys.argv:
        hold = _HERE / "hold"
        hold.mkdir(exist_ok=True)
        for take in TAKES:
            for theme in ("day", "night"):
                body, bw, bh = take_board(theme, take)
                path = hold / f"Onboarding-{take}-{theme.capitalize()}.dc.html"
                path.write_text(page(f"Paperboy first run, take {take}, {theme}", css(theme), body, bw, bh))
                print("wrote", path, path.stat().st_size, bw, bh)


if __name__ == "__main__":
    main()
