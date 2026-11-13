"""Split a tall screenshot into readable parts. usage: crop.py PNG CHUNK_PX [SCALE]"""
import sys, pathlib
from PIL import Image
src = pathlib.Path(sys.argv[1]); chunk = int(sys.argv[2]); scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
im = Image.open(src); w, h = im.size
n = 0
for y in range(0, h, chunk):
    part = im.crop((0, y, w, min(h, y + chunk)))
    if scale != 1.0:
        part = part.resize((int(part.width * scale), int(part.height * scale)), Image.LANCZOS)
    n += 1
    out = src.with_name(f"{src.stem}-p{n}.png"); part.save(out); print(out, part.size)
