"""Check the shared Plate 1 generator at other sizes: writes rev/GwScale.dc.html."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "engraved"))
from lib import *  # noqa

def plate(pid, w, h, cx, cy, theme, k):
    (bd, blue), (kd, key) = gw_print(pid, cx, cy, w, h, theme, k=k)
    g = STOCK if theme == "day" else NG
    return (f'<div style="position: relative; width: {w}px; height: {h}px; background-color: {g}; margin-bottom: 16px">'
            f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true" style="display: block; position: absolute">{blue}</svg>'
            f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true" style="display: block; position: absolute">{key}</svg></div>')

body = ('<div style="width: 1200px; background-color: #777; padding: 16px; box-sizing: border-box">'
        + plate("ga", 1160, 380, 780, 150, "day", 1.6) + plate("gb", 1160, 300, 800, 130, "night", 1.3)
        + plate("gc", 350, 150, 250, 70, "day", 0.8) + '</div>')
(HERE / "GwScale.dc.html").write_text(page("gw_print scale test", "body{margin:0}", body, 1200, 920))
