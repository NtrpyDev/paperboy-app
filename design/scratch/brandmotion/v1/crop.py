"""Crop a region out of a screenshot. crop.py SRC OUT x y w h [scale]  (coordinates in CSS px of the board)"""
import sys
from PIL import Image
src, out, x, y, w, h = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
k = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0
im = Image.open(src)
im.crop((int(x * k), int(y * k), int((x + w) * k), int((y + h) * k))).save(out)
print(out, im.size)
