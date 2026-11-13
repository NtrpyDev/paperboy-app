"""Crop a region of a full render. usage: crop.py TAG THEME Y0 Y1 [name]   (css px)"""
import sys, pathlib, glob
from PIL import Image
root = pathlib.Path(__file__).resolve().parents[2] / "shots" / "patterns" / sys.argv[1]
th = sys.argv[2]; y0, y1 = int(sys.argv[3]), int(sys.argv[4])
src = sorted(glob.glob(str(root / f"Explainer-Patterns-{th.capitalize()}-390w-*.png")))[-1]
im = Image.open(src)
out = root / (sys.argv[5] if len(sys.argv) > 5 else f"crop-{th}-{y0}.png")
im.crop((0, y0 * 2, im.width, min(im.height, y1 * 2))).save(out)
print(out, im.size)
