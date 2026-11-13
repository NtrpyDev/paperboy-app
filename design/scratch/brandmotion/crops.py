"""Crop several regions out of one screenshot. crops.py SRC OUTDIR name:x:y:w:h ...  (CSS px of the board, shots at 2x)"""
import sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src)
k = im.width / float(sys.argv[3]) if sys.argv[3].replace(".", "").isdigit() else 2.0
for spec in sys.argv[4:]:
    name, x, y, w, h = spec.split(":")
    x, y, w, h = (float(v) * k for v in (x, y, w, h))
    im.crop((int(x), int(y), int(x + w), int(y + h))).save(f"{out}/{name}.png")
