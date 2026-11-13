"""Cand-x-Feed: the app feed, day theme, 390 by 844."""
import os
import pathlib
from lib import *

OUT = pathlib.Path(os.environ.get("PB_OUT") or pathlib.Path(__file__).resolve().parents[2] / "canvas" / "project" / "Cand-x-Feed.dc.html")

W, H = 390, 844
PW, BAND = 390, 140


def tag_outline(t):
    return f'<span style="{mono(9, weight=600)}; border: 1px solid {INK}; padding: 4px 6px 3px">{t}</span>'


def tag_solid(t):
    return f'<span style="{mono(9, color=STOCK, weight=600)}; background-color: {INK}; border: 1px solid {INK}; padding: 4px 6px 3px">{t}</span>'


def rate_btn(icon, label):
    return (
        f'<button type="button" style="flex: 1 1 0; min-height: 44px; box-sizing: border-box; background-color: transparent; '
        f'border: 1px solid {INK}; border-radius: 0; color: {INK}; padding: 0 12px; display: flex; align-items: center; justify-content: center; gap: 9px; cursor: pointer">'
        f'{icon}<span style="{text(15, lh=1, weight=500)}">{label}</span></button>'
    )


def source(label):
    return (
        f'<a href="#paper" style="margin: -13px 0 -13px auto; min-height: 44px; display: inline-flex; align-items: center; gap: 5px; '
        f'{text(13.5, lh=1, italic=True)}; color: {INK}; text-decoration: underline; text-decoration-thickness: 0.75px; text-underline-offset: 3px">{label}{OUTARROW}</a>'
    )


def build():
    press = lambda i: f"display: block; animation: press 190ms {PRESS} {at(i * 50)} both"
    it = disp(44, weight=300, stretch=100, lh=0.98, ls=-0.012, italic=True)
    body = f"""<div style="width: {W}px; height: {H}px; box-sizing: border-box; overflow: hidden; position: relative; background-color: {STOCK}; color: {INK}; font-family: {TEXT}; display: flex; flex-direction: column">

<header style="padding: 8px 20px 0; display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 10px">
<div style="{disp(33, weight=800, lh=1)}; padding-bottom: 4px">Paper<span style="{disp(33, weight=300, stretch=100, lh=1, ls=-0.02, italic=True)}">boy</span><span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: {LIVE}; margin-left: 3px"></span></div>
<div style="margin-left: auto; text-align: right; {mono(9, color=MUTED)}; line-height: 1.4">Science and math,<br>newly released</div>
<button type="button" aria-label="Switch to night theme" style="width: 44px; height: 44px; margin-right: -11px; background-color: transparent; border: 0; color: {INK}; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0">{THEME}</button>
</div>
<div style="height: 3px; background-color: {INK}"></div>
<div style="height: 0.75px; background-color: {INK}; margin-top: 2px"></div>
</header>

<main style="display: flex; flex-direction: column; flex-grow: 1">
<article style="display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 6px; padding: 13px 20px 0">
{tag_outline("Physics")}{tag_solid("Peer-reviewed")}
{source("Physical Review Letters")}
</div>
<h2 style="margin: 0; padding: 10px 20px 0; {disp(44, lh=0.98)}">
<span style="{press(0)}">Two black holes</span>
<span style="{press(1)}">merged. <span style="{it}">Earth felt</span></span>
<span style="{press(2)}; {it}">space stretch.</span>
</h2>
{plate_gw("xg")}
<p style="margin: 0; padding: 10px 20px 0; {text(16, lh=1.42)}; text-wrap: pretty">LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.</p>
<div style="display: flex; flex-direction: column; gap: 8px; padding: 14px 20px 0">
<a href="#explainer" style="min-height: 48px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 14px 0 16px; background-color: {INK}; color: {STOCK}; text-decoration: none; {disp(23, weight=700, stretch=75, lh=1, ls=0.005)}"><span>See it explained</span>{ARROW}</a>
<div style="display: flex; gap: 8px">
{rate_btn(PLUS, "More like this")}
{rate_btn(MINUS, "Less like this")}
</div>
</div>
</article>

<div style="margin: 20px 20px 0; height: 0.75px; background-color: {INK}"></div>
<div style="margin: 2px 20px 0; height: 3px; background-color: {INK}"></div>

<article style="display: flex; flex-direction: column">
<div style="display: flex; align-items: center; gap: 6px; padding: 13px 20px 0">
{tag_outline("Biology")}{tag_solid("Peer-reviewed")}
{source("Nature")}
</div>
<h2 style="margin: 0; padding: 10px 20px 0; {disp(44, lh=0.98)}">
<span style="display: block">A neural network</span>
<span style="display: block">learned <span style="{it}">to fold</span></span>
<span style="display: block; {it}">proteins.</span>
</h2>
</article>
</main>
</div>"""
    css = "body{margin:0}\na{color:#16130F}a:hover{color:#5A554B}\n" + KEYFRAMES + "\n" + ink_keyframes("inkfeed", PW, BAND)
    OUT.write_text(page("Feed, Engraved Broadsheet, day", css, body, W, H))
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
