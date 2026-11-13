"""Cut a tall screenshot into readable pieces.
usage: slices.py IN OUTPREFIX [piece_height_px=1800] [overlap_px=60]"""
import sys
from PIL import Image
src, pre = sys.argv[1], sys.argv[2]
ph = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
ov = int(sys.argv[4]) if len(sys.argv) > 4 else 60
im = Image.open(src)
y, i = 0, 1
while y < im.height:
    piece = im.crop((0, y, im.width, min(im.height, y + ph)))
    piece.save(f"{pre}-{i}.png")
    print(f"{pre}-{i}.png", piece.size, "from y", y)
    y += ph - ov
    i += 1
