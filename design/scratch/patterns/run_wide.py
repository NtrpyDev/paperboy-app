"""Build the wide explainer board, render it, fix the declared height. usage: python3 run_wide.py TAG"""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
out = ROOT / "design" / "shots" / "patterns" / sys.argv[1]
out.mkdir(parents=True, exist_ok=True)
hfile = HERE / "heights.json"
heights = json.loads(hfile.read_text()) if hfile.exists() else {}
f = ROOT / "design" / "canvas" / "project" / "Explainer-Wide.dc.html"
def shot(extra):
    r = subprocess.run(["uv", "run", "--quiet", "--with", "playwright", "design/tools/dc_shot.py", str(f), "--out", str(out), "--width", "1200", "--height", "900"] + extra, cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr); sys.exit(1)
    return json.loads(r.stdout.strip().splitlines()[-1])
subprocess.run([sys.executable, str(HERE / "wide.py")], check=True)
j = shot(["--full", "--frames", "6"])
h = j["size"]["scrollHeight"]
if heights.get("wide") != h:
    heights["wide"] = h
    hfile.write_text(json.dumps(heights))
    subprocess.run([sys.executable, str(HERE / "wide.py")], check=True)
print("wide height", h, "overflow_x", j["overflow_x"], "console", j["console"], "fonts", sorted(set(x.split(" ")[0].strip('"') for x in j["fonts"])), j["shots"])
