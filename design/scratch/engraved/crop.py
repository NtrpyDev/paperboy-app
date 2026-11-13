"""Crop and enlarge a region of a screenshot so details can be judged.
usage: crop.py IN OUT x y w h [scale]   (coordinates in screenshot pixels)"""
import sys
from PIL import Image
src, dst, x, y, w, h = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0
im = Image.open(src).crop((x, y, x + w, y + h))
im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
im.save(dst)
print(dst, im.size)
