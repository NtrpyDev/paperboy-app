"""The app state boards: App-States-Day and App-States-Night.

Each board is one row of 390 by 844 phone screens, 40 px apart, with a mono slug above each
screen. The screens are the app states the design round left undrawn (HANDOFF.md 3.1, 6.7,
section 8 item 11) and the About screen.

  python3 states.py            writes the two boards into design/canvas/project/
  PB_BOARDS=/some/dir python3 states.py   writes them somewhere else

Everything is built from the locked parts: tokens, type helpers, icons and the live line from
scratch/engraved/lib.py, and the Kit (masthead, tags, headline, buttons, rating row, cards)
from scratch/feed/app_feed.py. Nothing in those files is changed.

New parts drawn here, all from existing tokens:
  strip()     the flat live line of HANDOFF 6.9 placed on the phone, in three states
  notice()    the message that replaces the Material snackbar
  topbar()    the explainer top bar (SYSTEM 9.2), used for the explainer cover and for About
  made()      "Paper in, explainer out", the website figure, redrawn at phone width in both themes
  RETURN      one new icon, for Undo

Facts: design/CONTENT.md, the app code, NOTICE.md, and app/build.gradle.kts (versionName).
Test knobs: PB_BOARDS, PB_DELAY, PB_NOTICE=ink (the notice as a full ink slab, never rendered),
PB_STRIP_H, PB_REFRESH_TOP, PB_LEAD_END, PB_LEAD_LESS, PB_LEAVE, PB_ABOUT, PB_ABOUT_FOOT.
"""
import math
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "feed"))
from app_feed import *  # noqa: E402,F403  (Kit, cards, root, css, plates, lib)

HERE = _HERE
DESIGN = HERE.parents[1]
BOARDS = pathlib.Path(os.environ.get("PB_BOARDS") or DESIGN / "canvas" / "project")
GITHUB = "https://github.com/NtrpyDev/paperboy-app"
VERSION = "0.1.0"            # app/build.gradle.kts, versionName. The app reads BuildConfig.VERSION_NAME.
STRIP_H = int(os.environ.get("PB_STRIP_H", 36))   # the band the flat line sits in, line at its middle
TOP = 24                     # open stock for the phone's own status bar, as on App-Feed-Day
NOTICE_INK = os.environ.get("PB_NOTICE") == "ink"

RETURN = ('<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" '
          'stroke-linecap="square" aria-hidden="true"><path d="M11.5 2.5v5.5H3M6 4.5L2.5 8 6 11.5"></path></svg>')
ARROW15 = OUTARROW.replace("11", "15", 2)
BACK = ('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="square" aria-hidden="true"><path d="M17 10H4M9 5l-5 5 5 5"></path></svg>')


def m(name):
    """A measuring tag. check.py reads the box of every element that carries one."""
    return f' data-m="{name}"'


# ------------------------------------------------------------------ small parts
def slug_row(k, left, right="", top=13, name="slugrow"):
    """A head row: what this is on the left (slug), its state on the right (label, muted)."""
    r = f'<div style="{k.label()}; text-align: right">{right}</div>' if right else ""
    return (f'<div{m(name)} style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: {top}px {M}px 0">'
            f'<div style="{k.label(color=k.c, weight=600)}">{left}</div>{r}</div>')


def strip(k, mode, pid, h=STRIP_H, y=None, start=320, dur=1900):
    """The flat live line of HANDOFF 6.9, on the phone. One path from the left margin to the
    right margin.
      loading  the line sweeps across, then its pen point pulses (the locked loading state)
      rest     the whole line, pen point parked at its end, nothing moving
      idle     nothing drawn: the pen point waits at the start of an empty track
    The idle frame is the loading frame at 0 ms plus the track, so "Try again" starts the
    sweep from exactly what the reader is looking at."""
    y = h / 2 if y is None else y
    d = f"M{M} {y:g}H{W - M}"
    day, g, live = k.day, k.g, k.live
    line = 'fill="none" stroke-linejoin="round" stroke-linecap="round" pathLength="1"'
    pen = f"offset-path: path('{d}'); offset-rotate: 0deg"
    r = 3.6 if day else 3.4
    if mode == "loading":
        sw = f"{SWEEP_DASH}; animation: sweep {dur}ms linear {at(start)} both"
        ride = f"{pen}; offset-distance: 100%; animation: travel {dur}ms linear {at(start)} both"
        beat = f"{ride}, pulse 2400ms ease-in-out {at(max(2400, start + dur + 200))} infinite"
        marks = (live_under_strokes(d, day, g, live, sw)
                 + f'<path d="{d}" {line} stroke="{live}" stroke-width="1.9" style="{sw}"></path>'
                 + pen_under_marks(day, g, live, ride)
                 + f'<circle r="{r}" fill="{live}" style="{beat}"></circle>')
        say = "Loading: a flat line is drawn across the sheet, then its pen point waits"
    elif mode == "rest":
        at_end = f"{pen}; offset-distance: 100%"
        marks = (live_under_strokes(d, day, g, live, "")
                 + f'<path d="{d}" {line} stroke="{live}" stroke-width="1.9"></path>'
                 + pen_under_marks(day, g, live, at_end)
                 + f'<circle r="{r}" fill="{live}" style="{at_end}"></circle>')
        say = "A flat line, fully drawn, with its pen point at rest at the end: nothing more to report"
    else:
        at_start = f"{pen}; offset-distance: 0%"
        marks = (f'<g stroke="{k.mu}" stroke-width="0.9" fill="none"><line x1="{M}" y1="{y}" x2="{W - M}" y2="{y}"></line>'
                 f'<line x1="{W - M - 0.45}" y1="{y - 5}" x2="{W - M - 0.45}" y2="{y + 5}"></line></g>'
                 + pen_under_marks(day, g, live, at_start)
                 + f'<circle r="{r}" fill="{live}" style="{at_start}"></circle>')
        say = "No signal: an empty track, with the pen point waiting at its start"
    return (f'<svg{m("strip")} viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{say}" '
            f'style="display: block; flex: none">{marks}</svg>')


def button(k, label, kind="primary", icon=ARROW, name="button"):
    """The 48 px button of SYSTEM 9.6 as a real <button>: the ink slab, or the ruled outline."""
    if kind == "primary":
        look = f"background-color: {k.c}; color: {k.g}; border: 0"
    else:
        look = f"background-color: transparent; color: {k.c}; border: 1px solid {k.ch}"
    return (f'<button type="button"{m(name)} style="width: 100%; min-height: 48px; box-sizing: border-box; display: flex; align-items: center; '
            f'justify-content: space-between; padding: 0 14px 0 16px; border-radius: 0; cursor: pointer; text-align: left; {look}; '
            f'{disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{label}</span>{icon}</button>')


def stack(inner, top=14):
    return f'<div style="display: flex; flex-direction: column; gap: 8px; padding: {top}px {M}px 0">{inner}</div>'


STAMP_T = 2100           # ms after load at which the board's one stamp lands


def rate(k, icon, label, on=False, stamp=False):
    """A rating button (SYSTEM 9.7). on: stamped at rest, the stamped fill and a check.
    stamp: the same rest, reached by Stamp as HANDOFF 6.7 says to build it: the whole button
    jumps to 1.1 and settles while the fill floods the whole surface at once, and the label
    color and the icon change in one step at 60 ms. Nothing wipes."""
    bg, fg, bd = (k.mu, k.g, k.mu) if on else ("transparent", k.c, k.ch)
    anim = ""
    if on and stamp:
        anim = f"; animation: stampbody 120ms {PRESS} {at(STAMP_T)} both, stampink 120ms linear {at(STAMP_T)} both"
        icon = (f'<span style="position: relative; display: inline-flex; width: 14px; height: 14px">'
                f'<span style="position: absolute; left: 0; top: 0; display: inline-flex; opacity: 0; animation: stampold 120ms linear {at(STAMP_T)} both">{icon}</span>'
                f'<span style="display: inline-flex; animation: stampnew 120ms linear {at(STAMP_T)} both">{CHECK}</span></span>')
    elif on:
        icon = CHECK
    return (f'<button type="button" aria-pressed="{"true" if on else "false"}" style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; '
            f'border: 1px solid {bd}; border-radius: 0; color: {fg}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer{anim}">'
            f'{icon}<span style="{text(16, lh=1, weight=500)}">{label}</span></button>')


def rating_row(k, more=False, less=False, stamp=False):
    return (f'<div{m("rating")} style="display: flex; gap: 8px">{rate(k, PLUS, "More like this", on=more, stamp=stamp and more)}'
            f'{rate(k, MINUS, "Less like this", on=less, stamp=stamp and less)}</div>')


def textlink(k, label, href, icon=OUTARROW, name="link"):
    """The journal link of SYSTEM 9.5: note italic, hairline underline, a 44 px target."""
    return (f'<a href="{href}"{m(name)} style="min-height: 44px; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; '
            f'{text(15, lh=1, italic=True)}; color: {k.c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{icon}</a>')


def double(k, heavy_first=True):
    a = f'<div style="height: 3px; flex: none; background-color: {k.ch}"></div>'
    b = f'<div style="height: 0.75px; flex: none; background-color: {k.ch}"></div>'
    gap = '<div style="height: 2px; flex: none"></div>'
    return a + gap + b if heavy_first else b + gap + a


def hair(k):
    return f'<div style="height: 0.75px; background-color: {k.ch}"></div>'


# ------------------------------------------------------------------ chrome
def masthead(k, pressed=False):
    """The feed masthead of SYSTEM 9.1, unchanged to the eye. The one addition: the wordmark is
    a link to About, with a 44 px target. pressed=True shows it under the finger (ink-muted)."""
    wc = k.mu if pressed else k.c
    return (
        f'<header{m("masthead")} style="padding: {TOP}px {M}px 0; display: flex; flex-direction: column">'
        f'<div style="display: flex; align-items: center; gap: 10px">'
        f'<a href="#about" aria-label="About Paperboy"{m("wordmark")} style="min-height: 44px; display: flex; align-items: center; color: {wc}; text-decoration: none">'
        f'<span style="{disp(33, weight=k.hw, lh=1)}; padding-bottom: 4px">Paper<span style="{disp(33, weight=k.iw, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span>'
        f'<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: {k.live}; margin-left: 3px"></span></span></a>'
        f'<div style="margin-left: auto; text-align: right; {k.label(lh=1.35)}">Science and math,<br>newly released</div>'
        f'<button type="button" aria-label="Switch to {"night" if k.day else "day"} theme" style="width: 44px; height: 44px; margin-right: -11px; background-color: transparent; border: 0; color: {k.c}; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0">{THEME}</button>'
        f'</div>{k.masthead_rule()}</header>'
    )


def topbar(k):
    """The explainer top bar of SYSTEM 9.2: back to the feed on the left, the small wordmark on
    the right, then the double rule."""
    return (
        f'<header{m("topbar")} style="padding: {TOP}px {M}px 0; display: flex; flex-direction: column; flex: none">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; height: 48px">'
        f'<a href="#feed"{m("back")} style="margin-left: -12px; padding: 0 12px; min-width: 44px; height: 44px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 8px; '
        f'color: {k.ch}; text-decoration: none; {mono(LAB, color=k.ch, weight=600, ls=0.06)}">{BACK}<span>Feed</span></a>'
        f'<div style="{disp(22, weight=k.hw, lh=1)}; padding-bottom: 3px">Paper<span style="{disp(22, weight=400, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span>'
        f'<span style="display: inline-block; width: 4px; height: 4px; border-radius: 50%; background-color: {k.live}; margin-left: 2px"></span></div>'
        f'</div>{k.masthead_rule()}</header>'
    )


def notice(k, message, action=None, icon=RETURN, where=None, land=None):
    """The message that takes the snackbar's job. A band across the foot of the screen, edge to
    edge, square, in the stamped fill (one step under the primary slab), so a card's own action
    stays the heaviest thing in view. One sentence on the left. On the right an outline button
    when there is something to do, or a label that says where to look.
    land: ms after load at which it lands (Press). None draws it at rest."""
    fill = k.c if NOTICE_INK else k.mu
    on = k.g
    go = f"; animation: press 190ms {PRESS} {at(land)} both" if land is not None else ""
    right = ""
    if action:
        right = (f'<button type="button"{m("notice-action")} style="flex: none; min-height: 44px; box-sizing: border-box; background-color: transparent; border: 1px solid {on}; '
                 f'border-radius: 0; color: {on}; padding: 0 14px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">'
                 f'<span style="{text(16, lh=1, weight=500)}">{action}</span>{icon}</button>')
    elif where:
        right = f'<div style="flex: none; {k.label(color=on)}; text-align: right">{where}</div>'
    return (
        f'<div role="status"{m("notice")} style="position: absolute; left: 0; right: 0; bottom: 0; box-sizing: border-box; min-height: 64px; padding: 10px {M}px; '
        f'background-color: {fill}; color: {on}; display: flex; align-items: center; justify-content: space-between; gap: 16px{go}">'
        f'<div style="{text(16, lh=1.3)}; text-wrap: balance">{message}</div>{right}</div>'
    )


# ------------------------------------------------------------------ the failure cover and its relatives
REASON = {
    "offline": ("No connection", "You are offline, or the feed cannot be reached."),
    "server": ("Server error", "The feed server had a problem."),
    "baddata": ("Unreadable data", "The feed arrived in a form this app cannot read."),
}
PAGE_REASON = {
    "offline": ("No connection", "You are offline, or the server cannot be reached."),
    "server": ("Server error", "The server had a problem."),
}


def cover(k, pid, slug, state, mode, lines, body, btn=None, size=44, top=15, extra="", wrap="pretty"):
    """Head row, the strip, a two-voice headline, one sentence, one action."""
    lh = 0.98 if size == 44 else 1.02
    return (
        f'<section style="display: flex; flex-direction: column">'
        + slug_row(k, slug, state, top=top)
        + strip(k, mode, pid)
        + k.headline(lines, size=size, lh=lh).replace("padding: 10px", "padding: 2px", 1).replace("<h2 ", f'<h2{m("headline")} ', 1)
        + (k.summary(body).replace("<p ", f'<p{m("sentence")} ', 1).replace("text-wrap: pretty", f"text-wrap: {wrap}") if body else "")
        + (stack(btn) if btn else "")
        + extra
        + '</section>'
    )


# ------------------------------------------------------------------ cards
def tail2(k):
    """The end of the Paper 2 card: summary and actions."""
    return f'<article style="display: flex; flex-direction: column">{k.summary(SUMMARY2)}{stack(k.primary() + rating_row(k))}</article>'


def tail2r(k):
    """The end of the Paper 2 card from its readout row down."""
    return (f'<article style="display: flex; flex-direction: column">'
            + k.readout_row("0.96" + k.unit("angstroms"), "Median error, CASP14 blind test", "Plate 2<br>Illustration,<br>drawn to scale")
            + k.summary(SUMMARY2) + stack(k.primary() + rating_row(k)) + '</article>')


def short3(k, less=False, stamp=False):
    """Paper 3, the short card, with its rating row in any state."""
    return (
        f'<article{m("card3")} style="display: flex; flex-direction: column">'
        + k.tag_row([k.tag_outline("Space"), k.tag_solid("Peer-reviewed")], "The Astrophysical Journal Letters")
        + k.headline([[("The first picture of", False)], [("a black hole's shadow.", True)]], size=30, lh=1.02, press=False)
        + f'<div style="display: flex; align-items: flex-end; gap: 10px; padding: 12px {M}px 0">'
        f'<div style="{disp(44, weight=k.hw, lh=0.86, ls=k.num_ls)}; font-variant-numeric: lining-nums">42</div>'
        f'<div style="{k.label()}; padding-bottom: 1px">Microarcseconds across,<br>the bright ring in galaxy M87</div></div>'
        + stack(k.outline() + rating_row(k, less=less, stamp=stamp))
        + '</article>'
    )


def preprint4(k):
    """The preprint card as a whole short card. Every fact is a visible placeholder."""
    return (
        '<article style="display: flex; flex-direction: column">'
        + k.tag_row([k.tag_outline("[FIELD]"), k.tag_screen("Preprint")])
        + f'<h2 style="margin: 0; padding: 10px {M}px 0; {disp(30, weight=k.hw, lh=1.02)}">[PREPRINT TITLE]</h2>'
        + f'<p style="margin: 0; padding: 8px {M}px 0; {text(16, lh=1.42)}">[ONE LINE SUMMARY]</p>'
        + stack(k.outline() + rating_row(k))
        + '</article>'
    )


def hero1(k, tag_top=13, plate_top=12):
    return card1(k, animate=False, plate_top=plate_top, tag_top=tag_top)


def column(inner, lead=0):
    return f'<main style="display: flex; flex-direction: column; flex: none; margin-top: {lead}px">{inner}</main>'


# ------------------------------------------------------------------ screens: first load
def s_loading(k):
    return root(k, masthead(k) + slug_row(k, "Loading new papers", "No signal yet", top=15) + strip(k, "loading", "ld"))


def s_first_failed(k, why):
    state, body = REASON[why]
    return root(k, masthead(k) + cover(
        k, "ff", "Feed not loaded", state, "idle",
        [[("The feed", False)], [("did not load.", True)]], body,
        button(k, "Try again")))


def s_empty(k):
    about = (f'<div style="padding: 20px {M}px 0; display: flex; flex-direction: column; align-items: flex-start">'
             f'<div style="width: 64px; height: 0.75px; background-color: {k.ch}"></div>'
             f'{textlink(k, "About Paperboy", "#about", ARROW_S)}</div>')
    return root(k, masthead(k) + cover(
        k, "em", "Feed loaded", "Nothing to show", "rest",
        [[("No papers yet.", False)], [("The feed is empty.", True)]],
        "Pull down to check for new papers.", extra=about))


# ------------------------------------------------------------------ screens: the end of the list
def _above_footer(k):
    return tail2(k) + k.divider() + short3(k) + k.divider()


def s_older_loading(k):
    foot = f'<section{m("footer")} style="display: flex; flex-direction: column">' + slug_row(k, "Loading older papers", "No signal yet") + strip(k, "loading", "ol") + '</section>'
    return root(k, column(_above_footer(k) + foot, LEAD_END))


def s_older_failed(k, why="server"):
    state, body = REASON[why]
    foot = f'<div{m("footer")} style="display: flex; flex-direction: column">' + cover(
        k, "of", "Older papers not loaded", state, "idle",
        [[("Older papers ", False), ("did not load.", True)]],
        body + " The papers above are still here.",
        button(k, "Try again", kind="outline"), size=30, top=13, wrap="balance") + '</div>'
    return root(k, column(_above_footer(k) + foot, LEAD_END))


def s_end(k):
    about = (f'<div style="padding: 16px {M}px 0; display: flex; flex-direction: column; align-items: flex-start">'
             f'<div style="width: 64px; height: 0.75px; background-color: {k.ch}"></div>'
             f'{textlink(k, "About Paperboy", "#about", ARROW_S)}</div>')
    foot = f'<div{m("footer")} style="display: flex; flex-direction: column">' + cover(
        k, "en", "End of the feed", "Nothing older", "rest",
        [[("You have reached", False)], [("the end of the feed.", True)]],
        "There are no older papers. New ones arrive at the top of the feed.",
        size=30, top=13, extra=about) + '</div>'
    return root(k, column(_above_footer(k) + foot, LEAD_END))


# ------------------------------------------------------------------ screens: pull to refresh
def _feed_top(k, pressed=False):
    return masthead(k, pressed=pressed) + column(hero1(k, tag_top=15, plate_top=16) + k.divider() + card2(k, part="head"))


def s_refreshing(k):
    """The strip opens between the masthead and the first card, where the first load draws it,
    and the cards move down by its height."""
    opened = (f'<section{m("refresh")} style="display: flex; flex-direction: column">'
              + slug_row(k, "Loading new papers", "No signal yet", top=REFRESH_TOP) + strip(k, "loading", "rf") + '</section>')
    return root(k, masthead(k) + opened + column(k.divider().replace("margin: 18px", "margin: 0px", 1) + hero1(k, tag_top=13, plate_top=12)))


def s_refreshed(k, n=2):
    msg = "No new papers" if n == 0 else "1 new paper" if n == 1 else f"{n} new papers"
    return root(k, _feed_top(k) + notice(k, msg, where="At the top of the feed" if n else None, land=900))


def s_refresh_failed(k, why="offline"):
    return root(k, _feed_top(k) + notice(k, "Could not refresh. " + REASON[why][0] + ".", action="Try again", icon=ARROW_S14, land=900))


# ------------------------------------------------------------------ screens: less like this
def _less_column(k, visible=None, stamped=True, gone=False):
    """Mid feed: the end of card 2, the short card that is rated less, the preprint card, the
    top of the next card. One feed item is a card and the divider under it. Feed up closes the
    item from the top: the card and everything under it rise together, and the card goes under
    the rule above it. visible is how many px of the card are still out."""
    card = short3(k, less=stamped, stamp=stamped and visible is None)
    if gone:
        mid = ""
    elif visible is not None:
        mid = (f'<div{m("leaving")} style="height: {visible}px; overflow: hidden; flex: none; display: flex; flex-direction: column; justify-content: flex-end">'
               f'<div style="flex: none; display: flex; flex-direction: column">{card}</div></div>' + k.divider())
    else:
        mid = f'<div{m("leaving")} style="display: flex; flex-direction: column; flex: none">{card}</div>' + k.divider()
    return column(tail2r(k) + k.divider() + mid + preprint4(k) + k.divider() + hero1(k), LEAD_LESS)


def s_less_stamped(k):
    return root(k, _less_column(k))


def s_less_leaving(k):
    return root(k, _less_column(k, visible=LEAVE_VISIBLE))


def s_less_gone(k):
    return root(k, _less_column(k, gone=True) + notice(k, "Paper hidden", action="Undo", land=900))


# ------------------------------------------------------------------ screens: explainer cover
def s_explainer_failed(k, why="offline"):
    state, body = PAGE_REASON[why]
    return root(k, topbar(k) + cover(
        k, "xf", "Explainer not loaded", state, "idle",
        [[("This explainer", False)], [("did not load.", True)]], body,
        button(k, "Try again")))


# ------------------------------------------------------------------ screens: About
def s_feed_about_entry(k):
    return root(k, _feed_top(k, pressed=True))


MK_W, MK_H, MK_BAND = 400, 132, 84


def made(k):
    """"Paper in, explainer out" (the website figure, SYSTEM 9.20 item 5) at phone width: one
    live line through three plates. The paper as lines of text, the ring field in its fine
    pass only, the ring field at full strength."""
    day = k.day
    pid = "mk" + k.theme[0]
    (_, blue), _ = gw_print(pid, MK_W, MK_H / 2, MK_W, MK_H, k.theme, k=0.42)
    parts = [x + "</path>" for x in blue.split("</path>") if x]

    def rings(full):
        marks = "".join(parts if full else parts[:2])
        return (f'<svg viewBox="0 0 {MK_W} {MK_H}" width="{MK_W}" height="{MK_H}" aria-hidden="true" '
                f'style="position: absolute; top: 50%; margin-top: -{MK_H / 2}px; right: 0">{marks}</svg>')

    out = ['<line x1="0" y1="9" x2="82%" y2="9" stroke-width="2.6"></line>',
           '<line x1="0" y1="16.5" x2="54%" y2="16.5" stroke-width="2.6"></line>',
           '<line x1="0" y1="27" x2="38%" y2="27" stroke-width="0.9"></line>']
    ends = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 46, 100, 100, 100, 100, 100, 100]
    y, first = 38.0, True
    for e in ends:
        out.append(f'<line x1="{"5%" if first else "0"}" y1="{y:.1f}" x2="{e}%" y2="{y:.1f}"></line>')
        first = e < 100
        y += 4.5
    paper = (f'<svg width="100%" height="{MK_BAND}" aria-hidden="true" style="position: absolute; left: 0; top: 0">'
             f'<g stroke="{k.ch}" stroke-width="0.8" fill="none">{"".join(out)}</g></svg>')

    col = "calc((100% - 48px) / 3)"
    plate = "position: absolute; top: 0; bottom: 0; overflow: hidden"
    grow = f"transform-origin: 0 50%; animation: growx 1600ms linear {at(900)} both"
    ride = f"animation: ridex 1600ms linear {at(900)} both"
    band = lambda hgt, color, op=1: (f'<div style="position: absolute; left: 0; right: 0; top: {-hgt / 2}px; height: {hgt}px; '
                                     f'background-color: {color}{"; opacity: " + str(op) if op < 1 else ""}; {grow}"></div>')
    disc = lambda rad, color, op=1: (f'<div style="position: absolute; left: 100%; top: 0; width: {2 * rad}px; height: {2 * rad}px; margin: {-rad}px 0 0 {-rad}px; '
                                     f'border-radius: 50%; background-color: {color}{"; opacity: " + str(op) if op < 1 else ""}"></div>')
    if day:
        line = band(7, k.g) + band(1.9, k.live)
        pen = disc(6.5, k.g) + disc(3.6, k.live)
    else:
        line = band(4, k.g) + "".join(band(wd, k.live, op) for wd, op in HALO) + band(1.9, k.live)
        pen = disc(5, k.g) + "".join(disc(rd, k.live, op) for rd, op in PEN_HALO) + disc(3.4, k.live)
    return (
        f'<div role="img"{m("made")} aria-label="Illustration: one line runs left to right through three plates. In the first, lines of text: the paper. In the second, a field of fine rings: the visuals, being built. In the third, the same rings at full strength: the finished explainer. A pen point rests at the end of the line." '
        f'style="position: relative; height: {MK_BAND}px; margin-top: 14px">'
        f'<div style="{plate}; left: 0; width: {col}">{paper}</div>'
        f'<div style="{plate}; left: calc((100% + 24px) / 3); width: {col}">{rings(False)}</div>'
        f'<div style="{plate}; right: 0; width: {col}">{rings(True)}</div>'
        f'<div aria-hidden="true" style="position: absolute; left: 0; right: 0; top: 50%; height: 0">{line}'
        f'<div style="position: absolute; left: 0; right: 0; top: 0; height: 0; {ride}">{pen}</div></div></div>'
    )


def about_body(k):
    c, mu, ch = k.c, k.mu, k.ch
    P = lambda s, mt=12, name="p": f'<p{m(name)} style="margin: {mt}px 0 0; {text(17, lh=1.47)}; text-wrap: pretty">{s}</p>'
    slug = lambda s: f'<div style="{k.label(color=c, weight=600)}">{s}</div>'
    lab = lambda s: f'<div style="{k.label()}; text-align: right">{s}</div>'
    v30 = k.voice2(30, 1.02)

    def section(name, left, right, head):
        return (f'<div{m(name)} style="margin-top: 40px">{double(k)}</div>'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-top: 12px">{slug(left)}{lab(right) if right else ""}</div>'
                f'<h2 style="margin: 8px 0 0; {disp(30, weight=k.hw, lh=1.02)}">{head}</h2>')

    def step(n, statement):
        return (f'<div{m("agent" + str(n))} style="display: flex; flex-direction: column; gap: 8px; padding: 12px 0 14px; border-top: 0.75px solid {ch}">'
                f'<div style="{k.label(color=c, weight=600)}">Agent {n} <span style="color: {mu}; font-weight: 500">of 3</span></div>'
                f'<div style="{disp(30, weight=k.hw, lh=1.02)}">{statement}</div></div>')

    def row(name, label, value, note):
        return (f'<div{m(name)} style="display: flex; flex-direction: column; gap: 4px; padding: 11px 0 12px; border-top: 0.75px solid {ch}">'
                f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px">'
                f'<div style="{k.label()}; flex: none">{label}</div>'
                f'<div style="{disp(30, weight=k.hw, lh=1, ls=k.num_ls)}; font-variant-numeric: lining-nums; text-align: right">{value}</div></div>'
                f'<div style="{text(15, lh=1.4, italic=True)}; text-wrap: pretty">{note}</div></div>')

    head = (
        f'<div{m("about-head")} style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding-top: 15px">{slug("About")}{lab("Version " + VERSION)}</div>'
        f'<h1{m("about-h1")} style="margin: 10px 0 0; {disp(44, weight=k.hw, lh=0.98)}">'
        f'<span style="display: block; animation: press 190ms {PRESS} {at(0)} both">New science</span>'
        f'<span style="display: block; animation: press 190ms {PRESS} {at(50)} both">and math papers,</span>'
        f'<span style="display: block; white-space: nowrap; animation: press 190ms {PRESS} {at(100)} both; {k.voice2(44, 0.98)}">explained visually.</span></h1>'
        + P("Paperboy is a free, open source Android app: an endless feed of newly released science and math papers, peer-reviewed and preprints, each labeled as one or the other. No account. No ads.", 14, "p1")
        + P("Every card links to the original paper. &ldquo;More like this&rdquo; and &ldquo;Less like this&rdquo; tune the feed, and your ratings stay on this phone.", 12, "p2")
    )
    how = (
        section("sec-made", "How an explainer is made", "Machine written", f'<span style="display: block">Three AI agents,</span><span style="display: block; {v30}">one job each.</span>')
        + P("Papers with a free legal full text get a visual explainer, made by three agents in turn.", 12, "p3")
        + f'<figure style="margin: 40px 0 0; display: flex; flex-direction: column">'
        f'{hair(k)}<div{m("fighead")} style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-top: 10px">{slug("Paper in, explainer out")}{lab("Illustration")}</div>'
        f'{made(k)}'
        f'<div style="display: flex; flex-direction: column; margin-top: 14px">'
        + step(1, f'<span style="display: block">Reads the paper</span><span style="display: block; {v30}">as a domain expert.</span>')
        + step(2, f'Builds <span style="{v30}">the visuals.</span>')
        + step(3, f'<span style="display: block">Checks every number</span><span style="display: block">against the paper,</span><span style="display: block; {v30}">and checks the</span><span style="display: block; {v30}">visuals are clear.</span>')
        + '</div></figure>'
        f'<div{m("every")} style="display: flex; flex-direction: column; margin-top: 24px; padding-top: 12px; border-top: 0.75px solid {ch}">'
        f'<div style="{k.label()}">Every explainer</div>'
        f'<p style="margin: 10px 0 0; {disp(30, weight=k.iw, stretch=100, lh=1.06, ls=-0.012, italic=True)}; text-wrap: balance">Machine written, and it can be wrong.</p>'
        + P("The page says so, and links the source so you can check it against the paper.", 12, "p4")
        + '</div>'
    )
    source = (
        section("sec-source", "Source", "", f'Free and <span style="{v30}">open source.</span>')
        + P("Paperboy&rsquo;s source code is public.", 12, "p5")
        + f'<div style="margin-top: 14px">{button(k, "Source on GitHub", kind="outline", icon=ARROW15, name="github")}</div>'
        f'<div{m("address")} style="margin-top: 14px; {text(15, lh=1.4, italic=True)}">github.com/NtrpyDev/paperboy-app</div>'
    )
    licenses = (
        section("sec-lic", "Licenses", "", f'<span style="display: block">The app, the typefaces,</span><span style="display: block; {v30}">and the libraries.</span>')
        + '<div style="display: flex; flex-direction: column; margin-top: 12px">'
        + row("lic-app", "The app", "GPL 3.0", "The GNU General Public License, version 3 or later.")
        + row("lic-type", "Typefaces", "OFL 1.1", "Noto Serif Display, Source Serif 4, and Martian Mono, each under the SIL Open Font License 1.1.")
        + row("lic-libs", "Libraries", "NOTICE.md", "The open source libraries in the app, each with its license.")
        + f'<div style="border-top: 0.75px solid {ch}"></div></div>'
        + f'<div style="display: flex">{textlink(k, "Read it on GitHub", GITHUB + "/blob/main/NOTICE.md", OUTARROW, name="notice-link")}</div>'
    )
    return head + how + source + licenses


def s_about(k, scroll=0):
    return root(k, topbar(k) + f'<div style="flex: 1 1 0; min-height: 0; overflow: hidden; position: relative">'
                   f'<main{m("about")} style="display: flex; flex-direction: column; padding: 0 {M}px {ABOUT_FOOT}px; margin-top: {-scroll}px">{about_body(k)}</main></div>')


# ------------------------------------------------------------------ tuning, measured in the renderer (check.py)
ARROW_S = '<svg width="13" height="11" viewBox="0 0 13 11" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="square" aria-hidden="true"><path d="M1.5 5.5h9.5M7.5 2l3.5 3.5L7.5 9"></path></svg>'
ARROW_S14 = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" aria-hidden="true"><path d="M1.5 7h10.5M8 3l4 4-4 4"></path></svg>'
LEAD_END = int(os.environ.get("PB_LEAD_END", 0))        # scroll offset of the end-of-list screens
LEAD_LESS = int(os.environ.get("PB_LEAD_LESS", 6))      # scroll offset of the less-like-this screens
REFRESH_TOP = int(os.environ.get("PB_REFRESH_TOP", 13)) # px above the head row of the strip while refreshing
LEAVE_VISIBLE = float(os.environ.get("PB_LEAVE", 160))  # px of the leaving card still uncovered in the held frame
ABOUT_SCROLL = [int(v) for v in os.environ.get("PB_ABOUT", "0,774,1336").split(",")]
ABOUT_FOOT = int(os.environ.get("PB_ABOUT_FOOT", 63))   # open ground under the last line of About
ITEM_H = 317.77          # the short card and the divider under it, measured in the renderer


def bezier_time(p, x1=0.2, y1=0.0, x2=0.0, y2=1.0):
    """The fraction of the duration at which cubic-bezier(x1, y1, x2, y2) has covered p."""
    best = (9, 0)
    for i in range(20001):
        s = i / 20000
        x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
        y = 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
        if abs(y - p) < best[0]:
            best = (abs(y - p), x)
    return best[1]


def screens(theme):
    """(slug, when it appears, markup) for every screen, in board order."""
    k = Kit(theme)
    return [
        ("First load, loading", "FeedState.loading, no items. HANDOFF 6.9, placed", s_loading(k)),
        ("First load failed, no connection", "FeedState.error = Offline, no items", s_first_failed(k, "offline")),
        ("First load failed, server error", "FeedState.error = Server, no items", s_first_failed(k, "server")),
        ("Empty feed", "No items, not loading, no error", s_empty(k)),
        ("End of list, loading older", "FeedState.loading, with items", s_older_loading(k)),
        ("End of list, older papers failed", "FeedState.error, with items", s_older_failed(k)),
        ("End of the feed", "FeedState.reachedEnd", s_end(k)),
        ("Pull to refresh, refreshing", "FeedState.refreshing", s_refreshing(k)),
        ("Refreshed, new papers", "RefreshResult.Arrived(2)", s_refreshed(k)),
        ("Refresh failed", "RefreshResult.Failed(Offline)", s_refresh_failed(k)),
        ("Less like this, stamped", "0 to 700 ms after the tap", s_less_stamped(k)),
        ("Less like this, feed up", "LEAVE_SLUG", s_less_leaving(k)),
        ("Less like this, hidden", "FeedModel.collapsed, from 1060 ms", s_less_gone(k)),
        ("Explainer did not load", "PageFailure.Offline", s_explainer_failed(k)),
        ("Feed, the way to About", "The wordmark is the link, shown pressed", s_feed_about_entry(k)),
        ("About, top", "Opened from the wordmark", s_about(k, ABOUT_SCROLL[0])),
        ("About, scrolled", "The bar stays, the page scrolls", s_about(k, ABOUT_SCROLL[1])),
        ("About, end", "Source and licenses", s_about(k, ABOUT_SCROLL[2])),
    ]


PAD, GAP, SLUG_H = 40, 40, 44


def board(theme):
    k = Kit(theme)
    scr = screens(theme)
    n = len(scr)
    bw = 2 * PAD + n * W + (n - 1) * GAP
    cols = []
    for i, (name, when, markup) in enumerate(scr, start=1):
        when = when.replace("LEAVE_SLUG", LEAVE_SLUG)
        cols.append(
            f'<div style="width: {W}px; flex: none; display: flex; flex-direction: column">'
            f'<div style="height: {SLUG_H}px; display: flex; flex-direction: column; justify-content: flex-end; gap: 3px">'
            f'<div style="{k.label(color=k.c, weight=600)}"><span style="color: {k.mu}">{i:02d}</span>&nbsp; {name}</div>'
            f'<div style="{k.label()}">{when}</div></div>'
            f'<div data-screen="{i:02d}" style="margin-top: 12px; outline: 1px solid {k.ch}">{markup}</div></div>'
        )
    head = (
        f'{double(k)}'
        f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 24px; margin-top: 12px">'
        f'<div style="display: flex; align-items: baseline; gap: 14px"><div style="{k.label(color=k.c, weight=600)}">Paperboy app states, {theme}</div>'
        f'<div style="{k.label()}">The states the feed boards do not show, and About. Each screen is 390 by 844.</div></div>'
        f'<div style="{k.label()}; text-align: right">No status bar is drawn. The top 24 px of a screen are left for the phone\'s own.</div></div>'
    )
    bh = PAD + 32 + 28 + SLUG_H + 12 + H + PAD
    body = (f'<div style="width: {bw}px; height: {bh}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {k.g}; color: {k.c}; '
            f'font-family: {TEXT}; padding: {PAD}px; display: flex; flex-direction: column">'
            f'<div style="height: 32px; flex: none; display: flex; flex-direction: column">{head}</div>'
            f'<div style="display: flex; gap: {GAP}px; margin-top: 28px">{"".join(cols)}</div></div>')
    return body, bw, bh


def board_css(theme):
    k = Kit(theme)
    return (css(theme) + "\n"
            f"@keyframes stampbody{{0%{{transform:none;background-color:transparent;border-color:{k.ch}}}1%{{transform:scale(1.1);background-color:transparent;border-color:{k.ch}}}100%{{transform:none;background-color:{k.mu};border-color:{k.mu}}}}}\n"
            f"@keyframes stampink{{0%,50%{{color:{k.c}}}50.01%,100%{{color:{k.g}}}}}\n"
            "@keyframes stampold{0%,50%{opacity:1}50.01%,100%{opacity:0}}\n"
            "@keyframes stampnew{0%,50%{opacity:0}50.01%,100%{opacity:1}}\n"
            "@keyframes growx{from{transform:scaleX(0)}to{transform:none}}\n"
            "@keyframes ridex{from{transform:translateX(-100%)}to{transform:none}}")


LEAVE_SLUG = ""


def main():
    global LEAVE_SLUG
    p = 1 - (LEAVE_VISIBLE + 23.75) / ITEM_H
    LEAVE_SLUG = f"About {700 + round(360 * bezier_time(p))} ms: Feed up, {round(p * 100)} percent up"
    for theme in ("day", "night"):
        body, bw, bh = board(theme)
        path = BOARDS / f"App-States-{theme.capitalize()}.dc.html"
        path.write_text(page(f"Paperboy app states, {theme}", board_css(theme), body, bw, bh))
        print("wrote", path, path.stat().st_size, bw, bh)


if __name__ == "__main__":
    main()
