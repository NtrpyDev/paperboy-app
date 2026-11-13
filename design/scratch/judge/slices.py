import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
src, prefix, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
overlap = 60
im = Image.open(src)
y = 0; i = 1
while y < im.height:
    c = im.crop((0, y, im.width, min(im.height, y+step)))
    c.save(f"{prefix}-{i:02d}.png")
    print(i, y, c.size)
    y += step - overlap; i += 1
