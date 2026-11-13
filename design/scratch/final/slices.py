#!/usr/bin/env python3
"""slices.py SRC PREFIX SLICE_H_PX [scale]  cut a tall screenshot into slices (image pixels)"""
import sys
from PIL import Image
src, prefix, sh = sys.argv[1], sys.argv[2], int(sys.argv[3])
s = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
im = Image.open(src)
n = 0
for y in range(0, im.height, sh):
    part = im.crop((0, y, im.width, min(im.height, y + sh)))
    if s != 1.0:
        part = part.resize((int(part.width * s), int(part.height * s)), Image.LANCZOS)
    n += 1
    part.save(f"{prefix}-{n:02d}.png")
print(prefix, im.size, n, "slices")
