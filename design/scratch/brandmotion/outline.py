"""Outline the wordmark from the real font files, so the brand sheet and the app icon
carry true vector geometry and exact metrics.

  uv run --quiet --with uharfbuzz python outline.py

Writes glyphs.json next to this file. Units are thousandths of an em, y down, baseline at 0.
"""
import json
import pathlib

import uharfbuzz as hb

HERE = pathlib.Path(__file__).resolve().parent
ROMAN = HERE / "fontdata" / "nsd.ttf"
ITALIC = HERE / "fontdata" / "nsd-italic.ttf"


class Pen:
    def __init__(self, dx, k):
        self.d, self.dx, self.k = [], dx, k
        self.xs, self.ys = [], []

    def p(self, x, y):
        X, Y = (x + self.dx) * self.k, -y * self.k
        self.xs.append(X)
        self.ys.append(Y)
        return f"{X:.1f} {Y:.1f}"

    def move_to(self, x, y, _):
        self.d.append("M" + self.p(x, y))

    def line_to(self, x, y, _):
        self.d.append("L" + self.p(x, y))

    def quadratic_to(self, cx, cy, x, y, _):
        self.d.append("Q" + self.p(cx, cy) + " " + self.p(x, y))

    def cubic_to(self, c1x, c1y, c2x, c2y, x, y, _):
        self.d.append("C" + self.p(c1x, c1y) + " " + self.p(c2x, c2y) + " " + self.p(x, y))

    def close_path(self, _):
        self.d.append("Z")


def shape(path, text, wght, wdth):
    face = hb.Face(hb.Blob.from_file_path(str(path)))
    font = hb.Font(face)
    font.set_variations({"wght": wght, "wdth": wdth})
    upem = face.upem
    k = 1000 / upem
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "lnum": True})
    funcs = hb.DrawFuncs()
    x = 0
    parts, boxes, xs = [], [], []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = Pen(0, k)
        funcs.set_move_to_func(Pen.move_to and (lambda px, py, ud: ud.move_to(px, py, None)), None)
        funcs.set_line_to_func(lambda px, py, ud: ud.line_to(px, py, None), None)
        funcs.set_quadratic_to_func(lambda a, b, c, d, ud: ud.quadratic_to(a, b, c, d, None), None)
        funcs.set_cubic_to_func(lambda a, b, c, d, e, f, ud: ud.cubic_to(a, b, c, d, e, f, None), None)
        funcs.set_close_path_func(lambda ud: ud.close_path(None), None)
        font.draw_glyph(info.codepoint, funcs, pen)
        parts.append("".join(pen.d))
        xs.append((x + pos.x_offset) * k)
        if pen.xs:
            boxes.append([min(pen.xs), min(pen.ys), max(pen.xs), max(pen.ys)])
        else:
            boxes.append(None)
        x += pos.x_advance
    return {"glyphs": parts, "x": xs, "advance": x * k, "boxes": boxes}


def main():
    out = {}
    for name, w in (("d1", 800), ("d2", 900)):
        out[f"paper_{name}"] = shape(ROMAN, "Paper", w, 62.5)
        out[f"P_{name}"] = shape(ROMAN, "P", w, 62.5)
        out[f"Hx_{name}"] = shape(ROMAN, "Hxdp.", w, 62.5)
    for name, w in (("d4", 300), ("d5", 400)):
        out[f"boy_{name}"] = shape(ITALIC, "boy", w, 100)
    (HERE / "glyphs.json").write_text(json.dumps(out))
    for k, v in out.items():
        print(k, round(v["advance"], 1), [None if b is None else [round(t) for t in b] for b in v["boxes"]])


if __name__ == "__main__":
    main()
