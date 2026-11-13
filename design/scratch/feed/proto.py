"""Plate trials: writes scratch/feed/Proto-*.dc.html, a column of plate variants at 390 wide."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plates import *  # noqa: E402,F403

CSS_EXTRA = (
    "@keyframes registerA{from{transform:translate(5px,-3px)}to{transform:none}}\n"
    "@keyframes registerB{from{transform:translate(-5px,3px)}to{transform:none}}\n"
    + ink_keyframes("inkproof", W, BAND) + "\n" + ink_keyframes("inkp2", W, P2BAND)
)


def sheet(name, theme, items):
    t = T(theme)
    rows = "".join(
        f'<div style="padding: 14px 20px 0; {mono(10.5, color=t["muted"], ls=0.06)}">{label}</div>{markup}' for label, markup in items
    )
    body = (f'<div style="width: {W}px; box-sizing: border-box; background-color: {t["ground"]}; color: {t["text"]}; '
            f'font-family: {TEXT}; display: flex; flex-direction: column; padding-bottom: 30px">{rows}</div>')
    css = f"body{{margin:0;background:{t['ground']}}}\na{{color:{t['text']}}}\n" + KEYFRAMES + "\n" + CSS_EXTRA
    out = HERE / f"Proto-{name}.dc.html"
    out.write_text(page(f"Proto {name}", css, body, W, 1200))
    print("wrote", out, out.stat().st_size)


P2 = [dict(), dict(s=64.0, band=128), dict(cross=False)]

if __name__ == "__main__":
    for th in ("day", "night"):
        sheet(f"P1-{th}", th, [("shared generator, gw_print()", plate1(f"a{th[0]}", th, animate=False))])
        sheet(f"P2-{th}", th, [(str(kw), plate2(f"b{i}{th[0]}", th, animate=False, **kw)) for i, kw in enumerate(P2)])
