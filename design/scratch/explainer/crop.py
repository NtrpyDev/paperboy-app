"""crop.py IN OUT x y w h [scale]   (css px at 2x renders; scale enlarges the crop)"""
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
x, y, w, h = [int(float(v) * 2) for v in sys.argv[3:7]]
k = float(sys.argv[7]) if len(sys.argv) > 7 else 1
im = Image.open(src).crop((x, y, x + w, y + h))
if k != 1:
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
im.save(dst)
print(dst, im.size)
