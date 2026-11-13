"""The app feed boards: App-Feed-Day and App-Feed-Night, fixed 390 by 844 phone screens.

  python3 app_feed.py            writes the two boards into design/canvas/project/
  python3 app_feed.py proofs     also writes other scroll positions into scratch/feed/ (not boards)

Markup patterns are the locked ones from scratch/director/lock_proof.py and lock_parts.py.
Plates come from plates.py. Facts come from design/CONTENT.md only.
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plates import *  # noqa: E402,F403

BOARDS = pathlib.Path(os.environ.get("PB_BOARDS") or HERE.parents[1] / "canvas" / "project")   # PB_BOARDS: write test copies elsewhere
H = 844
# PB_P2: trial geometry for Plate 2, for example PB_P2="s=110,cy=103"
P2KW = {k: float(v) for k, v in (kv.split("=") for kv in os.environ.get("PB_P2", "").split(",") if kv)}
STAMP_AT = 2100          # ms after load: the tap on "More like this" lands once the plate is at rest


class Kit:
    """The locked component patterns, for one theme."""

    def __init__(self, theme):
        self.theme = theme
        t = T(theme)
        self.t = t
        self.day = t["day"]
        self.c, self.g, self.mu, self.live = t["text"], t["ground"], t["muted"], t["live"]
        self.hw = 800 if self.day else 900
        self.iw = 300 if self.day else 400

    # --- type
    def label(self, color=None, weight=500, lh=1.3):
        return f"{mono(LAB, color=color or self.mu, weight=weight, ls=0.06)}; line-height: {lh}"

    def voice2(self, size, lh):
        """The second voice: D4 by day; D5 at night, at width 87.5 inside a headline of 30 px or more."""
        return disp(size, weight=self.iw, stretch=100 if self.day else 87.5, lh=lh, ls=-0.012, italic=True)

    # --- tags
    def tag_outline(self, s):
        return f'<span style="{mono(10, color=self.c, weight=600, ls=0.06)}; border: 1px solid {self.c}; padding: 4px 6px 3px">{s}</span>'

    def tag_solid(self, s):
        return f'<span style="{mono(10, color=self.g, weight=600, ls=0.06)}; background-color: {self.c}; border: 1px solid {self.c}; padding: 4px 6px 3px">{s}</span>'

    def tag_screen(self, s):
        hatch = f"repeating-linear-gradient(135deg, {self.c} 0 1.1px, transparent 1.1px 3.2px)"
        return (f'<span style="display: inline-flex; padding: 3.5px; background-image: {hatch}">'
                f'<span style="{mono(10, color=self.c, weight=600, ls=0.06)}; background-color: {self.g}; padding: 1.5px 4px 0.5px">{s}</span></span>')

    def tag_row(self, tags, journal=None):
        """Tags, then the journal link. The link stays on the row when it fits and takes its own
        row, right aligned, when it does not. The name is never shortened."""
        link = ""
        if journal:
            link = (f'<span style="flex: 1 1 auto; display: flex; justify-content: flex-end; margin: -13px 0">'
                    f'<a href="#paper" style="min-height: 44px; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; '
                    f'{text(15, lh=1, italic=True)}; color: {self.c}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{journal}{OUTARROW}</a></span>')
        return (f'<div style="display: flex; flex-wrap: wrap; align-items: center; column-gap: 6px; row-gap: 0; padding: 13px {M}px 0">'
                f'{"".join(tags)}{link}</div>')

    # --- controls
    def primary(self, s="See it explained"):
        return (f'<a href="#explainer" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
                f'padding: 0 14px 0 16px; background-color: {self.c}; color: {self.g}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{s}</span>{ARROW}</a>')

    def outline(self, s="Read the paper"):
        return (f'<a href="#paper" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; '
                f'padding: 0 14px 0 16px; border: 1px solid {self.c}; color: {self.c}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>{s}</span>{OUTARROW.replace("11", "15", 2)}</a>')

    def rate(self, icon, s, on=False, stamp=False):
        bg, fg = (self.c, self.g) if on else ("transparent", self.c)
        anim = f"; animation: stamp 120ms {PRESS} {at(STAMP_AT)} both" if (on and stamp) else ""
        return (f'<button type="button" aria-pressed="{"true" if on else "false"}" style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: {bg}; '
                f'border: 1px solid {self.c}; border-radius: 0; color: {fg}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer{anim}">'
                f'{icon}<span style="{text(16, lh=1, weight=500)}">{s}</span></button>')

    def actions(self, main, more=False, stamp=False):
        return (f'<div style="display: flex; flex-direction: column; gap: 8px; padding: 14px {M}px 0">{main}'
                f'<div style="display: flex; gap: 8px">{self.rate(PLUS, "More like this", on=more, stamp=stamp)}{self.rate(MINUS, "Less like this")}</div></div>')

    # --- rules
    def masthead_rule(self):
        return f'<div style="height: 3px; background-color: {self.c}"></div><div style="height: 0.75px; background-color: {self.c}; margin-top: 2px"></div>'

    def divider(self):
        return (f'<div style="margin: 18px {M}px 0; height: 0.75px; background-color: {self.c}"></div>'
                f'<div style="margin: 2px {M}px 0; height: 3px; background-color: {self.c}"></div>')

    # --- blocks
    def masthead(self):
        c = self.c
        return (
            f'<header style="padding: 8px {M}px 0; display: flex; flex-direction: column">'
            f'<div style="display: flex; align-items: center; gap: 10px">'
            f'<div style="{disp(33, weight=self.hw, lh=1)}; padding-bottom: 4px">Paper<span style="{disp(33, weight=self.iw, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span>'
            f'<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: {self.live}; margin-left: 3px"></span></div>'
            f'<div style="margin-left: auto; text-align: right; {self.label(lh=1.35)}">Science and math,<br>newly released</div>'
            f'<button type="button" aria-label="Switch to {"night" if self.day else "day"} theme" style="width: 44px; height: 44px; margin-right: -11px; background-color: transparent; border: 0; color: {c}; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0">{THEME}</button>'
            f'</div>{self.masthead_rule()}</header>'
        )

    def headline(self, lines, size=44, lh=0.98, press=True):
        """lines: a list of lines, each a list of (text, is_second_voice)."""
        out = []
        for i, parts in enumerate(lines):
            anim = f"; animation: press 190ms {PRESS} {at(i * 50)} both" if press else ""
            if all(v for _, v in parts):
                out.append(f'<span style="display: block{anim}; {self.voice2(size, lh)}">{"".join(s for s, _ in parts)}</span>')
            else:
                inner = "".join(f'<span style="{self.voice2(size, lh)}">{s}</span>' if v else s for s, v in parts)
                out.append(f'<span style="display: block{anim}">{inner}</span>')
        return f'<h2 style="margin: 0; padding: 10px {M}px 0; {disp(size, weight=self.hw, lh=lh)}">{"".join(out)}</h2>'

    def readout_row(self, readout, what, slug):
        return (
            f'<div style="display: flex; align-items: flex-end; justify-content: space-between; padding: 6px {M}px 0">'
            f'<div style="display: flex; flex-direction: column; gap: 3px">'
            f'<div style="{disp(44, weight=self.hw, lh=1, color=self.c)}; font-variant-numeric: lining-nums">{readout}</div>'
            f'<div style="{self.label()}">{what}</div></div>'
            f'<div style="text-align: right; {self.label(lh=1.4)}">{slug}</div></div>'
        )

    def summary(self, s):
        return f'<p style="margin: 0; padding: 10px {M}px 0; {text(16, lh=1.42)}; text-wrap: pretty">{s}</p>'

    def unit(self, s):
        return f'<span style="{text(15, lh=1, italic=True)}; letter-spacing: 0; margin-left: 7px">{s}</span>'


# ------------------------------------------------------------------ cards
def card1(k, animate=True):
    """Paper 1, the locked hero card."""
    return (
        '<article style="display: flex; flex-direction: column">'
        + k.tag_row([k.tag_outline("Physics"), k.tag_solid("Peer-reviewed")], "Physical Review Letters")
        + k.headline([[("Two black holes", False)], [("merged. ", False), ("Earth felt", True)], [("space stretch.", True)]], press=animate)
        + plate1("p1" + k.theme[0], k.theme, soft=2, animate=animate)
        + k.readout_row(f'1.0 × 10<sup style="{SUP}">−21</sup>', "Peak strain. Pitch 35 to 250 Hz", "Plate 1<br>Illustration,<br>not to scale")
        + k.summary("LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.")
        + k.actions(k.primary())
        + '</article>'
    )


def card2(k, animate=True, part="all", more=False, stamp=False):
    """Paper 2, a hero card. part: "all", "head" (tag row and headline), or "tail" (plate onward)."""
    head = (
        k.tag_row([k.tag_outline("Biology"), k.tag_solid("Peer-reviewed")], "Nature")
        + k.headline([[("A neural network", False)], [("learned ", False), ("to fold", True)], [("proteins.", True)]], press=False)
    )
    tail = (
        plate2("p2" + k.theme[0], k.theme, animate=animate, **P2KW)
        + k.readout_row("0.96" + k.unit("angstroms"), "Median error. Next best 2.8 Å", "Plate 2<br>Illustration,<br>drawn to scale")
        + k.summary("Given only a protein's amino acid sequence, AlphaFold predicted its 3D shape to within about the width of an atom in a blind test.")
        + k.actions(k.primary(), more=more, stamp=stamp)
    )
    body = {"all": head + tail, "head": head, "tail": tail}[part]
    return f'<article style="display: flex; flex-direction: column">{body}</article>'


def card3(k, more=False, stamp=False):
    """Paper 3, the short card: no plate, no explainer, a link out."""
    return (
        '<article style="display: flex; flex-direction: column">'
        + k.tag_row([k.tag_outline("Space"), k.tag_solid("Peer-reviewed")], "The Astrophysical Journal Letters")
        + k.headline([[("The first picture of", False)], [("a black hole's shadow.", True)]], size=30, lh=1.02, press=False)
        + f'<div style="display: flex; align-items: flex-end; gap: 10px; padding: 12px {M}px 0">'
        f'<div style="{disp(44, weight=k.hw, lh=0.86)}; font-variant-numeric: lining-nums">42</div>'
        f'<div style="{k.label()}; padding-bottom: 1px">Microarcseconds across,<br>the bright ring in galaxy M87</div></div>'
        + k.actions(k.outline(), more=more, stamp=stamp)
        + '</article>'
    )


def card4(k):
    """The preprint card. No real preprint facts exist, so every fact is a visible placeholder."""
    return (
        '<article style="display: flex; flex-direction: column">'
        + k.tag_row([k.tag_outline("[FIELD]"), k.tag_screen("Preprint")])
        + f'<h2 style="margin: 0; padding: 10px {M}px 0; {disp(30, weight=k.hw, lh=1.02)}">[PREPRINT TITLE]</h2>'
        + f'<p style="margin: 0; padding: 8px {M}px 0; {text(16, lh=1.42)}">[ONE LINE SUMMARY]</p>'
        + '</article>'
    )


# ------------------------------------------------------------------ screens
def root(k, inner):
    return (f'<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; '
            f'background-color: {k.g}; color: {k.c}; font-family: {TEXT}; display: flex; flex-direction: column">{inner}</div>')


def screen_top(theme):
    """Scroll position 0: masthead, all of card 1, card 2 starting."""
    k = Kit(theme)
    return root(k, k.masthead() + f'<main style="display: flex; flex-direction: column; flex: none">{card1(k)}{k.divider()}{card2(k, part="head")}</main>')


def screen_hero2(theme):
    """Card 2 as the hero: the end of card 1 above it."""
    k = Kit(theme)
    tail1 = (f'<article style="display: flex; flex-direction: column">'
             + k.summary("LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.")
             + k.actions(k.primary()) + '</article>')
    return root(k, f'<main style="display: flex; flex-direction: column; flex: none; margin-top: -84px">{tail1}{k.divider()}{card2(k)}{k.divider()}{card3(k)}</main>')


def screen_lower(theme, show=132):
    """Scrolled further: the last `show` px of Plate 2, the end of card 2, the short card with
    "More like this" just stamped, and the preprint card."""
    k = Kit(theme)
    up = 12 + PH - show
    return root(k, f'<main style="display: flex; flex-direction: column; flex: none; margin-top: -{up}px">'
                   f'{card2(k, part="tail")}{k.divider()}{card3(k, more=True, stamp=True)}{k.divider()}{card4(k)}</main>')


def css(theme):
    t = T(theme)
    c, g = t["text"], t["ground"]
    return (
        f"body{{margin:0}}\na{{color:{c}}}\n" + KEYFRAMES + "\n"
        "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
        "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
        f"@keyframes stamp{{0%{{transform:none;background-color:transparent;color:{c}}}1%{{transform:scale(1.1);background-color:transparent;color:{c}}}100%{{transform:none;background-color:{c};color:{g}}}}}\n"
        + ink_keyframes("inkproof", W, BAND)
    )


def write(path, title, theme, body):
    path.write_text(page(title, css(theme), body, W, H))
    print("wrote", path, path.stat().st_size)


if __name__ == "__main__":
    write(BOARDS / "App-Feed-Day.dc.html", "Paperboy feed, day", "day", screen_top("day"))
    write(BOARDS / "App-Feed-Night.dc.html", "Paperboy feed, night", "night", screen_lower("night"))
    if "proofs" in sys.argv:
        write(HERE / "Proof-Top-Night.dc.html", "Proof: feed top, night", "night", screen_top("night"))
        write(HERE / "Proof-Lower-Day.dc.html", "Proof: feed lower, day", "day", screen_lower("day"))
        write(HERE / "Proof-Hero2-Day.dc.html", "Proof: card 2 hero, day", "day", screen_hero2("day"))
        write(HERE / "Proof-Hero2-Night.dc.html", "Proof: card 2 hero, night", "night", screen_hero2("night"))
