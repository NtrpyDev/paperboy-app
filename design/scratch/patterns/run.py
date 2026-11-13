"""Build the patterns boards, render them with the screenshot tool, fix the declared heights, slice the renders.
usage: python3 run.py TAG [day|night ...]      renders land in design/shots/patterns/TAG/"""
import json, pathlib, subprocess, sys
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
tag = sys.argv[1]
themes = sys.argv[2:] or ["day", "night"]
out = ROOT / "design" / "shots" / "patterns" / tag
out.mkdir(parents=True, exist_ok=True)
hfile = HERE / "heights.json"
heights = json.loads(hfile.read_text()) if hfile.exists() else {}

def shot(theme, extra):
    f = ROOT / "design" / "canvas" / "project" / f"Explainer-Patterns-{theme.capitalize()}.dc.html"
    r = subprocess.run(["uv", "run", "--quiet", "--with", "playwright", "design/tools/dc_shot.py", str(f), "--out", str(out)] + extra,
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr); sys.exit(1)
    return json.loads(r.stdout.strip().splitlines()[-1])

for th in themes:
    subprocess.run([sys.executable, str(HERE / "patterns.py"), th], check=True)
    j = shot(th, ["--full", "--frames", "7"])
    h = j["size"]["scrollHeight"]
    if heights.get(th) != h:
        heights[th] = h
        hfile.write_text(json.dumps(heights))
        subprocess.run([sys.executable, str(HERE / "patterns.py"), th], check=True)
    print(th, "height", h, "overflow_x", j["overflow_x"], "console", j["console"], "fonts", sorted(set(f.split(" ")[0].strip('"') + (" " + " ".join(f.split(" ")[1:]) if 0 else "") for f in j["fonts"])), len(j["fonts"]))
    im = Image.open(j["shots"][0])
    y, i, ph, ov = 0, 1, 1700, 60
    while y < im.height:
        im.crop((0, y, im.width, min(im.height, y + ph))).save(out / f"{th}-{i:02d}.png")
        y += ph - ov; i += 1
    print("  slices", i - 1, "of", im.size)
