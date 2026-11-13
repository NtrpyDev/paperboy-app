"""Compare a screenshot of the built site with the board's render of the same width.

  uv run --with pillow python design/scratch/web/site_diff.py BUILT.png BOARD.png OUT_PREFIX [band_px]

Prints the share of differing pixels in each horizontal band and writes OUT_PREFIX-diff.png
(differences in red over a faded copy of the built page).
"""
import sys
from PIL import Image, ImageChops

a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB")
out = sys.argv[3]
band = int(sys.argv[4]) if len(sys.argv) > 4 else 400
print("sizes", a.size, b.size)
h = min(a.height, b.height)
a, b = a.crop((0, 0, a.width, h)), b.crop((0, 0, b.width, h))
d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 40 else 0)
for y in range(0, h, band):
    part = d.crop((0, y, d.width, min(h, y + band)))
    n = sum(1 for v in part.get_flattened_data() if v)
    share = n / (part.width * part.height)
    if share > 0.0005:
        print(f"y {y // 2:5d}-{min(h, y + band) // 2:5d} css px: {share * 100:.2f}% differ")
faded = Image.blend(a, Image.new("RGB", a.size, "white"), 0.7)
red = Image.new("RGB", a.size, (230, 0, 0))
faded.paste(red, mask=d)
faded.save(out + "-diff.png")
