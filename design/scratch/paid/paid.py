"""The paid app's screens, and the owner's private numbers page.

  python3 paid.py            writes five boards into design/canvas/project/
  PB_BOARDS=/some/dir python3 paid.py   writes them somewhere else

Boards:
  Paid-Subscribe-Day / -Night   after picking fields: the free trial, waiting on Google Play,
                                Google Play not reached, no subscription found, no free trial
                                offered, waiting before the price has loaded
  Paid-States-Day / -Night      subscription ended, payment failed (feed still works), payment
                                failed (reading paused), paused by the person, the update
                                cover, the subscription rows in About
  Owner-Numbers                 a web page only the owner sees. Fluid, day only.

Every word on a screen was written by the coordinator for the owner and is used verbatim.
Facts that are not decided are visible placeholders: [PRICE], [TRIAL DAYS], [DATE], [N], [$],
[MONTH]. No price, number of days, date or figure is invented here.

Built from the locked parts: tokens, type helpers and icons from scratch/engraved/lib.py, the
Kit from scratch/feed/app_feed.py, and the head row, the strip, the cover, the notice, the
48 px button, the text link, the top bar and About from scratch/states/states.py. The Fields
row and the board frame come from scratch/onboarding/onboarding.py. None of those files is changed.

Headlines are head-2 (30 / 1.02), one line per voice. At the 44 px headline size only
"Payment problem." fits the 350 px measure (measure_copy.py prints the widths).

New parts drawn here, all from existing tokens:
  gets()        the list of what you get: ledger rows, a check, one sentence each
  under_link()  a text link under a slab button
  small_print() a footnote rule and one note, held to the foot of the screen
  about_row()   a 48 px row in About: a name, a status in the label style, an arrow when it opens something
  table()       a dense table for the owner's page: label heads, hairline rows, figures set right
"""
import os
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "onboarding"))
from onboarding import *  # noqa: E402,F403  (states, Kit, lib, FIELDS, SOME_OUT, note_frame, PAD, GAP)

DESIGN = _HERE.parents[1]
BOARDS = pathlib.Path(os.environ.get("PB_BOARDS") or DESIGN / "canvas" / "project")
OUT14 = OUTARROW.replace("11", "14", 2)      # a link that leaves the app, at the notice's icon size
OUT15 = OUTARROW.replace("11", "15", 2)      # the same, at the outline button's icon size

# ------------------------------------------------------------------ copy, verbatim
SUB_BODY = ("After the trial it costs [PRICE] a month. Google Play charges you when the trial ends unless you cancel first. "
            "Cancel any time in Google Play.")
SUB_GETS = ["New science and math papers in the fields you picked.",
            "Every paper explained with pictures and plain words.",
            "Change your fields any time."]
SMALL = "The explanations are written by AI from the paper. Check the paper before relying on a fact."
WAITING = "Waiting for Google Play..."
NOTICE = "Your payment did not go through. Fix it in Google Play to keep reading."
ABOUT_LINE = "No ads."
ABOUT_MADE = ("Every paper gets a visual explainer. The best few are built from the full paper by three agents in turn. "
              "The rest are built from the paper's summary by one agent.")


# ------------------------------------------------------------------ parts
def head2(k, first, second):
    """A two-voice headline at head-2, one line per voice."""
    return (k.headline([[(first, False)], [(second, True)]], size=30, lh=1.02)
            .replace("<h2 ", f'<h2{m("headline")} ', 1).replace('<span style="display: block', '<span style="display: block; white-space: nowrap'))


def gets(k, lines):
    """The list of what you get: ledger rows split by full-measure hairlines (SYSTEM 9.16),
    each one sentence in body-feed after the check of SYSTEM section 8."""
    rows = "".join(
        f'<li style="list-style: none; display: flex; align-items: flex-start; gap: 9px; padding: 11px 0 12px; border-top: 0.75px solid {k.ch}">'
        f'<span style="flex: none; display: inline-flex; align-items: center; height: 22.72px">{CHECK}</span>'
        f'<span style="{text(16, lh=1.42)}; text-wrap: pretty">{s}</span></li>' for s in lines)
    return (f'<ul{m("gets")} style="margin: 14px {M}px 0; padding: 0; flex: none; display: flex; flex-direction: column; '
            f'border-bottom: 0.75px solid {k.ch}">{rows}</ul>')


def under_link(k, label, href="#", top=0):
    """A text link under a slab button: the journal link's form (note italic, hairline
    underline, a 44 px target) with the small in-app arrow, at the left margin."""
    return f'<div{m("underlink")} style="display: flex; flex: none; padding: {top}px {M}px 0">{textlink(k, label, href, ARROW_S)}</div>'


def small_print(k, s):
    """Small print: the caveat's footnote rule and a note (SYSTEM 9.10), in the muted color,
    held to the foot of the screen."""
    return (f'<div{m("small")} style="margin-top: auto; flex: none; padding: 16px {M}px 20px">'
            f'<div style="width: 64px; height: 0.75px; background-color: {k.ch}"></div>'
            f'<p style="margin: 10px 0 0; {text(15, lh=1.4, italic=True)}; color: {k.mu}; text-wrap: pretty">{s}</p></div>')


def waiting(k, pid):
    """The system's loading treatment (SYSTEM 9.19, ADDENDUM-APP 1.2) in the button's place:
    a slug, and the flat live line that sweeps and then waits."""
    return (f'<div{m("waiting")} style="display: flex; flex-direction: column; flex: none">'
            + slug_row(k, WAITING, "", top=14, name="waitrow") + strip(k, "loading", pid) + '</div>')


def about_row(k, name, status="", icon="", href=None, last=False, top=0):
    """One 48 px row in About between hairlines: a name in the button cut, then its status in
    the label style. A row that opens something is a link and ends in an arrow."""
    box = (f"margin-top: {top}px; min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; gap: 12px; "
           f"border-top: 0.75px solid {k.ch}; {'border-bottom: 0.75px solid ' + k.ch + '; ' if last else ''}color: {k.c}; text-decoration: none")
    st = f'<span style="{k.label()}; white-space: nowrap">{status}</span>' if status else ""
    inner = (f'<span style="display: inline-flex; align-items: baseline; gap: 10px">'
             f'<span style="{disp(23, weight=700, stretch=75, lh=1, ls=0.005)}; white-space: nowrap">{name}</span>{st}</span>{icon}')
    if href:
        return f'<a href="{href}"{m("row")} style="{box}">{inner}</a>'
    return f'<div{m("row")} style="{box}">{inner}</div>'


# ------------------------------------------------------------------ board: subscribe
def sub_top(k):
    return k.masthead(top=TOP) + slug_row(k, "Subscription", "", top=15, name="head")


def s_trial(k, wait=False):
    act = (waiting(k, "w" + k.theme[0]) if wait
           else f'<div{m("act")} style="flex: none; padding: 14px {M}px 0">{button(k, "Start free trial", name="go")}</div>')
    return root(k, sub_top(k)
                + head2(k, "Start your free trial.", "[TRIAL DAYS] days free.")
                + k.summary(SUB_BODY).replace("<p ", f'<p{m("sentence")} ', 1)
                + gets(k, SUB_GETS) + act + under_link(k, "I already subscribed", "#restore", top=2)
                + small_print(k, SMALL))


def s_no_trial(k):
    """Google Play offers this person no free trial: the same screen, selling the subscription."""
    return root(k, sub_top(k)
                + head2(k, "Subscribe to Paperboy.", "[PRICE] a month.")
                + k.summary("Cancel any time in Google Play.").replace("<p ", f'<p{m("sentence")} ', 1)
                + gets(k, SUB_GETS)
                + f'<div{m("act")} style="flex: none; padding: 14px {M}px 0">{button(k, "Subscribe", name="go")}</div>'
                + under_link(k, "I already subscribed", "#restore", top=2)
                + small_print(k, SMALL))


def s_waiting_price(k):
    """Before the price has loaded: the label and the waiting line, and nothing else."""
    return root(k, sub_top(k) + waiting(k, "wp" + k.theme[0]))


def s_unreachable(k):
    return root(k, k.masthead(top=TOP) + cover(
        k, "ur" + k.theme[0], "Subscription", "", "idle",
        [[("Can't reach Google Play.", False)], [("Nothing was charged.", True)]],
        "Check your connection and try again.", button(k, "Try again"), size=30))


def s_none_found(k):
    return root(k, k.masthead(top=TOP) + cover(
        k, "nf" + k.theme[0], "Subscription", "", "rest",
        [[("No subscription found.", False)], [("On this Google account.", True)]],
        "Subscriptions belong to the Google account that bought them. Switch accounts in Google Play, or start a free trial.",
        button(k, "Start free trial"), size=30, extra=under_link(k, "Try again", "#restore", top=2)))


# ------------------------------------------------------------------ board: subscription states
def s_ended(k):
    return root(k, masthead(k) + cover(
        k, "en" + k.theme[0], "Subscription", "", "rest",
        [[("Your subscription ended.", False)], [("Subscribe to keep reading.", True)]],
        "[PRICE] a month. Cancel any time in Google Play.",
        button(k, "Subscribe"), size=30, extra=under_link(k, "I already subscribed", "#restore", top=2)))


def s_retrying(k):
    """The feed still works. The notice of ADDENDUM-APP 1.4 carries the message and its action."""
    return root(k, _feed(k) + notice(k, NOTICE, action="Fix payment", icon=OUT14, land=900))


def _feed(k):
    return masthead(k) + column(hero1(k, tag_top=15, plate_top=16) + k.divider() + card2(k, part="head"))


def s_paused(k):
    return root(k, masthead(k) + cover(
        k, "pa" + k.theme[0], "Subscription", "", "idle",
        [[("Payment problem.", False)], [("Reading is paused.", True)]],
        "Google Play could not charge your payment method. Fix it there and your feed comes back.",
        button(k, "Fix payment in Google Play", icon=OUT15), size=30))


def s_user_paused(k):
    """The person paused the subscription themselves. Same layout as "Payment problem."."""
    return root(k, masthead(k) + cover(
        k, "up" + k.theme[0], "Subscription", "", "idle",
        [[("Your subscription is paused.", False)], [("Reading is paused.", True)]],
        "Resume it in Google Play and your feed comes back.",
        button(k, "Resume in Google Play", icon=OUT15), size=30))


def s_update(k):
    """The update cover, as the app builds it (FeedScreen.kt UpdateCover, ui/design/Cover.kt):
    under the masthead, a cover with no strip (head row, the head-2 headline, one sentence, the
    outline button), then 18 px and a double rule with the hairline on top, then the feed,
    which stays. Copy from the code, verbatim.
    One difference from the app: Cover.kt puts the headline 2 dp under the head row. That 2 dp
    was set for a headline under the strip's 36 dp band. With no strip, the system's own space
    between a head row and a head-2 is 8 (ADDENDUM-APP 7.2), so the board draws 8."""
    head = (k.headline([[("An update ", False), ("is needed.", True)]], size=30, lh=1.02)
            .replace("padding: 10px", "padding: 8px", 1).replace("<h2 ", f'<h2{m("headline")} ', 1))
    block = (f'<section{m("update")} style="display: flex; flex-direction: column; flex: none">'
             + slug_row(k, "Update needed", "Version " + VERSION, top=15)
             + head
             + k.summary("This version of Paperboy is too old for the newest papers.").replace("<p ", f'<p{m("sentence")} ', 1)
             + stack(button(k, "Get the update", kind="outline", icon=OUT15))
             + k.divider() + '</section>')
    return root(k, masthead(k) + block + column(hero1(k)))


def sub_rows(k, status):
    on = len(FIELDS) - len(SOME_OUT)
    return (about_row(k, "Fields", f"{on} of {len(FIELDS)} selected", ARROW, "#fields", top=28)
            + about_row(k, "Subscription", status)
            + about_row(k, "Manage in Google Play", "", OUT15, "#play", last=True))


def s_about_rows(k):
    """About as built (states.about_body), with three changes: the three rows sit right under
    the title, where the Fields row was drawn; the first paragraph, which held the old lines
    about cost and accounts, is replaced by one line; and the sentence under "Three AI agents,
    one job each." says what is true now (every paper gets an explainer)."""
    body = about_body(k)
    body, n1 = re.subn(r'(<p data-m="p1"[^>]*>).*?(</p>)', lambda mo: mo.group(1) + ABOUT_LINE + mo.group(2), body, count=1, flags=re.S)
    body, n3 = re.subn(r'(<p data-m="p3"[^>]*>).*?(</p>)', lambda mo: mo.group(1) + ABOUT_MADE + mo.group(2), body, count=1, flags=re.S)
    at = body.index('<p data-m="p1"')
    assert n1 == 1 and n3 == 1
    body = body[:at] + sub_rows(k, "Free trial, ends [DATE]") + body[at:]
    return root(k, topbar(k) + f'<div style="flex: 1 1 0; min-height: 0; overflow: hidden; position: relative">'
                   f'<main{m("about")} style="display: flex; flex-direction: column; padding: 0 {M}px 40px">{body}</main></div>')


def alternates(k):
    """Beside the About phone, for the owner: the Subscription row in its two other states."""
    rows = "".join(f'<div style="margin-top: 14px">{about_row(k, "Subscription", s, last=True)}</div>'
                   for s in ("Active, renews [DATE]", "Canceled, ends [DATE]"))
    return (f'<div style="width: 350px; flex: none; display: flex; flex-direction: column">'
            f'<div style="height: {NH}px; display: flex; align-items: flex-end; {k.label(color=k.c, weight=600)}">The Subscription row can also read</div>'
            f'<div style="margin-top: -2px">{rows}</div></div>')


SUBSCRIBE = [
    ("1. After picking fields: start the free trial", lambda k: s_trial(k)),
    ("2. Waiting on Google Play", lambda k: s_trial(k, wait=True)),
    ("3. Google Play could not be reached", s_unreachable),
    ("4. Tapped I already subscribed, nothing found", s_none_found),
    ("5. Google Play offers this person no free trial (they used it before)", s_no_trial),
    ("6. Waiting on Google Play before the price has loaded", s_waiting_price),
]
STATES_ = [
    ("1. Subscription ended", s_ended),
    ("2. Payment failed, Google is retrying (the feed still works)", s_retrying),
    ("3. Payment failed and access is paused", s_paused),
    ("4. The person paused the subscription themselves", s_user_paused),
    ("5. This version of the app is too old (already in the app, never drawn)", s_update),
    ("6. Subscription rows in About", s_about_rows),
]


NH = 30      # room for a two-line note above a phone


def frame(k, i, note, markup):
    """A phone with the owner's note above it. The note is not app copy."""
    return (f'<div style="width: {W}px; flex: none; display: flex; flex-direction: column">'
            f'<div style="height: {NH}px; display: flex; align-items: flex-end; {k.label(color=k.c, weight=600)}">{note}</div>'
            f'<div data-screen="{i:02d}" style="margin-top: 12px; outline: 1px solid {k.ch}">{markup}</div></div>')


def phone_board(theme, title, phones, extra=None):
    k = Kit(theme)
    cols = [frame(k, i, note, fn(k)) for i, (note, fn) in enumerate(phones, start=1)]
    bw = 2 * PAD + len(cols) * W + (len(cols) - 1) * GAP
    if extra:
        cols.append(extra(k))
        bw += GAP + 350
    bh = PAD + 32 + 28 + NH + 12 + H + PAD
    headrow = f'{double(k)}<div style="{k.label(color=k.c, weight=600)}; margin-top: 12px">{title} ({theme})</div>'
    body = (f'<div style="width: {bw}px; height: {bh}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {k.g}; color: {k.c}; '
            f'font-family: {TEXT}; padding: {PAD}px; display: flex; flex-direction: column">'
            f'<div style="height: 32px; flex: none; display: flex; flex-direction: column">{headrow}</div>'
            f'<div style="display: flex; gap: {GAP}px; margin-top: 28px">{"".join(cols)}</div></div>')
    return body, bw, bh


# ------------------------------------------------------------------ the owner's numbers (a web page)
PAGE_CSS = """body{margin:0;background-color:#E9E6DE}
:root{--on-pad:40px 56px 96px;--on-h1:66px;--on-h1-lh:0.95;--on-num:48px;--on-body:19px;--on-note:16px;--on-lab:11px;--on-figs:repeat(4,minmax(0,1fr));--on-gap:56px}
@media (max-width:1159px){:root{--on-pad:24px 20px 56px;--on-h1:44px;--on-h1-lh:0.98;--on-num:44px;--on-body:17px;--on-note:15px;--on-lab:10.5px;--on-gap:40px}}
@media (max-width:759px){:root{--on-figs:repeat(2,minmax(0,1fr))}}
@media (max-width:419px){:root{--on-figs:repeat(1,minmax(0,1fr))}}"""

PLAB = f"font-family: {MONO}; font-stretch: 75%; font-size: var(--on-lab); letter-spacing: 0.06em; line-height: 1.3; text-transform: uppercase"
CELL = f"font-family: {TEXT}; font-size: var(--on-body); line-height: 1.3; font-weight: 400; font-variant-numeric: lining-nums tabular-nums"
NOTE = f"font-family: {TEXT}; font-size: var(--on-note); line-height: 1.4; font-style: italic"


def rule2():
    return f'<div style="height: 3px; background-color: {INK}"></div><div style="height: 0.75px; background-color: {INK}; margin-top: 2px"></div>'


def headrow(left, right=""):
    r = f'<div style="{PLAB}; font-weight: 500; color: {MUTED}; text-align: right">{right}</div>' if right else ""
    return (f'<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-top: 12px">'
            f'<div style="{PLAB}; font-weight: 600; color: {INK}">{left}</div>{r}</div>')


def figure(label, value, under=""):
    """One figure: a hairline, a label, a large number (the readout), and words under it."""
    return (f'<div style="display: flex; flex-direction: column; border-top: 0.75px solid {INK}; padding-top: 10px; min-width: 0">'
            f'<div style="{PLAB}; font-weight: 500; color: {MUTED}">{label}</div>'
            f'<div style="margin-top: 8px; font-family: {DISP}; font-size: var(--on-num); font-weight: 800; font-stretch: 62.5%; line-height: 1; '
            f'letter-spacing: -0.005em; font-variant-numeric: lining-nums">{value}</div>{under}</div>')


def table(heads, rows, min_width=760):
    """A dense table: heads in the label style, rows split by hairlines, figures set right.
    heads: (text, "l" or "r"). rows: lists of (text, muted)."""
    th = "".join(
        f'<th scope="col" style="{PLAB}; font-weight: 500; color: {MUTED}; text-align: {"right" if a == "r" else "left"}; vertical-align: bottom; '
        f'padding: 0 {0 if i == len(heads) - 1 else 20}px 8px 0; border-bottom: 0.75px solid {INK}">{t}</th>' for i, (t, a) in enumerate(heads))
    trs = ""
    for row in rows:
        tds = ""
        for i, ((t, muted), (_, a)) in enumerate(zip(row, heads)):
            style = CELL if i < len(heads) - 1 or a == "r" else f"{PLAB}; font-weight: {500 if muted else 600}"
            tag = "th" if i == 0 else "td"
            scope = ' scope="row"' if i == 0 else ""
            tds += (f'<{tag}{scope} style="{style}; color: {MUTED if muted else INK}; text-align: {"right" if a == "r" else "left"}; vertical-align: baseline; '
                    f'padding: 9px {0 if i == len(heads) - 1 else 20}px 10px 0; border-bottom: 0.75px solid {INK}; white-space: nowrap">{t}</{tag}>')
        trs += f"<tr>{tds}</tr>"
    return (f'<div style="overflow-x: auto; margin-top: 14px"><table style="width: 100%; min-width: {min_width}px; border-collapse: collapse">'
            f'<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')


def owner_page():
    left_over = (f'<div style="{NOTE}; color: {INK}; margin-top: 8px">The app paid for itself this month.</div>'
                 f'<div style="{PLAB}; font-weight: 500; color: {MUTED}; margin-top: 6px">or</div>'
                 f'<div style="{NOTE}; color: {MUTED}; margin-top: 4px">The app cost you [$] this month.</div>')
    figs = (figure("Subscribers", "[N]") + figure("Income after Google's cut", "[$]")
            + figure("API cost", "[$]") + figure("Left over", "[$]", left_over))
    making, none = ("Making pages", False), ("No subscribers, no pages", True)
    by_field = [[(name, False), ("[N]", False), ("[N]", False), ("[$]", False), making] for _, name in FIELDS[:-1]]
    by_field.append([(FIELDS[-1][1], True), ("0", True), ("0", True), ("$0", True), none])
    by_month = [[("[MONTH]", False), ("[N]", False), ("[$]", False), ("[$]", False), ("[$]", False)] for _ in range(4)]
    section = lambda inner: f'<section style="margin-top: var(--on-gap); display: flex; flex-direction: column">{inner}</section>'
    body = (
        f'<div style="background-color: {STOCK}; color: {INK}; font-family: {TEXT}">'
        f'<div style="max-width: 1200px; margin: 0 auto; box-sizing: border-box; padding: var(--on-pad); display: flex; flex-direction: column">'
        f'{rule2()}'
        f'<h1 style="margin: 14px 0 0; font-family: {DISP}; font-size: var(--on-h1); line-height: var(--on-h1-lh); font-weight: 800; font-stretch: 62.5%; letter-spacing: -0.005em">Paperboy numbers</h1>'
        + section(rule2() + headrow("This month", "[MONTH]")
                  + f'<div style="display: grid; grid-template-columns: var(--on-figs); column-gap: 24px; row-gap: 28px; margin-top: 14px">{figs}</div>'
                  + f'<p style="margin: 24px 0 0; padding-top: 11px; border-top: 0.75px solid {INK}; font-family: {TEXT}; font-size: var(--on-body); line-height: 1.5">Trials not yet paying: [N]</p>')
        + section(rule2() + headrow("By field", "[MONTH]")
                  + table([("Field", "l"), ("Subscribers who picked it", "r"), ("Pages made this month", "r"), ("API cost this month", "r"), ("Status", "l")], by_field))
        + section(rule2() + headrow("By month", "Newest first")
                  + table([("Month", "l"), ("Subscribers at month end", "r"), ("Income after Google's cut", "r"), ("API cost", "r"), ("Left over", "r")], by_month, min_width=700))
        + f'<div style="margin-top: var(--on-gap); width: 64px; height: 0.75px; background-color: {INK}"></div>'
        f'<p style="margin: 10px 0 0; max-width: 760px; {NOTE}; text-wrap: pretty">Income is counted from active subscriptions at the listed price minus Google\'s fee. '
        f'API cost comes from each run\'s own record.</p>'
        f'</div></div>'
    )
    return body


def main():
    for name, title, phones, extra in (("Subscribe", "Subscribe", SUBSCRIBE, None),
                                       ("States", "Subscription states", STATES_, alternates)):
        for theme in ("day", "night"):
            body, bw, bh = phone_board(theme, title, phones, extra)
            path = BOARDS / f"Paid-{name}-{theme.capitalize()}.dc.html"
            path.write_text(page(f"{title}, {theme}", board_css(theme), body, bw, bh))
            print("wrote", path, path.stat().st_size, bw, bh)
    ph = int(os.environ.get("PB_OWNER_H", 1576))   # the page's height at 1280 wide, measured
    path = BOARDS / "Owner-Numbers.dc.html"
    path.write_text(page("Paperboy numbers", PAGE_CSS, owner_page(), 1280, ph))
    print("wrote", path, path.stat().st_size, 1280, ph)


if __name__ == "__main__":
    main()
