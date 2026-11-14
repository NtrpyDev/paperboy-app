"""A proof sheet of the eleven field plates at 3x, printed and blank, day and night.
Writes scratch/onboarding/EmblemProof-*.dc.html (not a board)."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "engraved"))
from lib import *  # noqa
from emblems import EMBLEMS, emblem, Style, EW, EH

def sheet(theme):
    day = theme == "day"
    g = STOCK if day else NG
    s = Style(PLATE_D if day else PLATE_N, INK if day else NM, g, MUTED if day else NS, hair=0.5 if day else 0.6)
    k = 3
    cells = ""
    for i, name in enumerate(EMBLEMS):
        cells += (f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="{mono(10.5, color=INK if day else NT)}">{name}</div>'
                  f'{emblem(name, f"e{i}", s, w=EW * k, h=EH * k)}{emblem(name, f"g{i}", s, ghost=True, w=EW * k, h=EH * k)}</div>')
    body = (f'<div style="width: 1400px; height: 1560px; box-sizing: border-box; padding: 20px; background-color: {g}; display: grid; '
            f'grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px">{cells}</div>')
    return page("Emblem proof " + theme, "body{margin:0}", body, 1400, 1560)

for th in ("day", "night"):
    (HERE / f"EmblemProof-{th}.dc.html").write_text(sheet(th))
