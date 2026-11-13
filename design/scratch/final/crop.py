#!/usr/bin/env python3
"""crop.py SRC OUT x y w h [scale]  (coordinates in image pixels)"""
import sys
from PIL import Image
src, out, x, y, w, h = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
s = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
im = Image.open(src).crop((x, y, x + w, y + h))
if s != 1.0:
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
im.save(out)
print(out, im.size)
