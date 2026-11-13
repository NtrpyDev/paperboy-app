"""Crop a region of a 2x render (coordinates in 1x px) and scale it. crop.py SRC OUT x0 y0 x1 y1 [scale]"""
import sys
from PIL import Image
src, out, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0
im = Image.open(src)
c = im.crop((int(x0 * 2), int(y0 * 2), int(min(x1 * 2, im.width)), int(min(y1 * 2, im.height))))
c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
c.save(out)
print(out, c.size)
