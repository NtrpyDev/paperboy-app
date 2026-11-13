import sys, urllib.parse
# name, css2 axis spec (or ""), list of (style css) variants to show
DISPLAY = [
 ("Bodoni Moda","ital,opsz,wght@0,6..96,400..900;1,6..96,400..900",["font-weight:500","font-weight:800","font-weight:500;font-style:italic"]),
 ("Gloock","",["font-weight:400"]),
 ("Fraunces","ital,opsz,wght@0,9..144,100..900;1,9..144,100..900",["font-weight:400","font-weight:800","font-weight:400;font-style:italic"]),
 ("Libre Caslon Display","",["font-weight:400"]),
 ("Instrument Serif","ital@0;1",["font-weight:400","font-weight:400;font-style:italic"]),
 ("Young Serif","",["font-weight:400"]),
 ("Libertinus Serif Display","",["font-weight:400"]),
 ("Noto Serif Display","ital,wdth,wght@0,62.5..100,100..900;1,62.5..100,100..900",["font-weight:500","font-weight:800;font-stretch:62.5%","font-weight:500;font-style:italic;font-stretch:75%"]),
 ("Roboto Serif","opsz,wdth,wght@8..144,50..150,100..900",["font-weight:700;font-stretch:60%","font-weight:500"]),
 ("Old Standard TT","ital,wght@0,400;0,700;1,400",["font-weight:700","font-weight:400;font-style:italic"]),
 ("Besley","ital,wght@0,400..900;1,400..900",["font-weight:800"]),
 ("Gupter","wght@400;500;700",["font-weight:700"]),
 ("Archivo","wdth,wght@62..125,100..900",["font-weight:800;font-stretch:125%","font-weight:800;font-stretch:62%","font-weight:600"]),
 ("Anybody","wdth,wght@50..150,100..900",["font-weight:800;font-stretch:150%","font-weight:800;font-stretch:50%","font-weight:600"]),
 ("Bricolage Grotesque","opsz,wdth,wght@12..96,75..100,200..800",["font-weight:800","font-weight:700;font-stretch:75%"]),
 ("Big Shoulders","opsz,wght@10..72,100..900",["font-weight:800","font-weight:500"]),
 ("Familjen Grotesk","wght@400..700",["font-weight:700"]),
 ("Schibsted Grotesk","wght@400..900",["font-weight:800","font-weight:500"]),
 ("Chivo","wght@100..900",["font-weight:900","font-weight:500"]),
 ("Libre Franklin","wght@100..900",["font-weight:900","font-weight:500"]),
 ("Special Gothic Expanded One","",["font-weight:400"]),
 ("Special Gothic Condensed One","",["font-weight:400"]),
 ("Special Gothic","wdth,wght@75..125,400..700",["font-weight:700;font-stretch:125%","font-weight:600;font-stretch:75%"]),
 ("Zalando Sans Expanded","wght@200..900",["font-weight:800"]),
 ("Mozilla Headline","wdth,wght@75..100,200..700",["font-weight:700","font-weight:600;font-stretch:75%"]),
 ("Science Gothic","wdth,wght@50..200,100..900",["font-weight:800;font-stretch:50%","font-weight:700;font-stretch:150%","font-weight:500"]),
 ("Boldonse","",["font-weight:400"]),
 ("Mona Sans","wdth,wght@75..125,200..900",["font-weight:800;font-stretch:125%","font-weight:700;font-stretch:75%"]),
 ("Sofia Sans Extra Condensed","wght@1..1000",["font-weight:700","font-weight:500"]),
 ("League Gothic","wdth@75..100",["font-weight:400"]),
 ("Stack Sans Headline","wght@200..700",["font-weight:600"]),
 ("Host Grotesk","wght@300..800",["font-weight:700"]),
 ("Funnel Display","wght@300..800",["font-weight:700"]),
 ("Saira","wdth,wght@50..125,100..900",["font-weight:600;font-stretch:50%","font-weight:700;font-stretch:125%"]),
 ("Encode Sans Condensed","wght@400;500;600;700",["font-weight:600"]),
 ("IBM Plex Sans Condensed","wght@400;500;600;700",["font-weight:600"]),
 ("Instrument Sans","wdth,wght@75..100,400..700",["font-weight:600;font-stretch:75%"]),
 ("B612","wght@400;700",["font-weight:700"]),
]
TEXT = [
 ("Source Serif 4","ital,opsz,wght@0,8..60,200..900;1,8..60,200..900",["font-weight:400","font-weight:400;font-style:italic"]),
 ("Literata","ital,opsz,wght@0,7..72,200..900;1,7..72,200..900",["font-weight:400","font-weight:400;font-style:italic"]),
 ("STIX Two Text","ital,wght@0,400..700;1,400..700",["font-weight:400","font-weight:400;font-style:italic"]),
 ("Spectral","ital,wght@0,400;0,600;1,400",["font-weight:400","font-weight:400;font-style:italic"]),
 ("Libre Caslon Text","ital,wght@0,400;0,700;1,400",["font-weight:400","font-weight:400;font-style:italic"]),
 ("Gelasio","ital,wght@0,400..700;1,400..700",["font-weight:400"]),
 ("Atkinson Hyperlegible Next","wght@200..800",["font-weight:400"]),
 ("Public Sans","wght@100..900",["font-weight:400"]),
 ("Hanken Grotesk","wght@100..900",["font-weight:400"]),
 ("Geist","wght@100..900",["font-weight:400"]),
 ("Schibsted Grotesk","wght@400..900",["font-weight:400"]),
 ("Instrument Sans","wdth,wght@75..100,400..700",["font-weight:400"]),
 ("Libre Franklin","wght@100..900",["font-weight:400"]),
 ("Mozilla Text","wght@200..700",["font-weight:400"]),
 ("Stack Sans Text","wght@200..700",["font-weight:400"]),
]
MONO = [
 ("Martian Mono","wdth,wght@75..112.5,100..800",["font-weight:500","font-weight:500;font-stretch:75%"]),
 ("DM Mono","wght@300;400;500",["font-weight:500"]),
 ("Geist Mono","wght@100..900",["font-weight:500"]),
 ("Spline Sans Mono","wght@300..700",["font-weight:500"]),
 ("Azeret Mono","wght@100..900",["font-weight:500"]),
 ("Sometype Mono","wght@400..700",["font-weight:500"]),
 ("B612 Mono","wght@400;700",["font-weight:400"]),
 ("Red Hat Mono","wght@300..700",["font-weight:500"]),
 ("Chivo Mono","wght@100..900",["font-weight:500"]),
 ("Google Sans Code","wght@300..800",["font-weight:500"]),
 ("Fragment Mono","",["font-weight:400"]),
 ("Doto","wght@100..900",["font-weight:800"]),
 ("Reddit Mono","wght@200..900",["font-weight:500"]),
 ("SUSE Mono","wght@100..800",["font-weight:500"]),
 ("Xanh Mono","ital@0;1",["font-weight:400"]),
 ("Kode Mono","wght@400..700",["font-weight:500"]),
]
def link(name, spec):
    fam = name.replace(" ", "+")
    return f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fam}{":"+spec if spec else ""}&display=swap">'
def page(kind, rows, sample, size, lh, title):
    links = "\n".join(dict.fromkeys(link(n, s) for n, s, _ in rows))
    cells = []
    for n, s, vs in rows:
        for v in vs:
            cells.append(f'<div style="display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; border-top: 1px solid #16130f"><div style="font-family: monospace; font-size: 11px; color: #444">{n} / {v}</div><div style="font-family: \'{n}\', \'Comic Sans MS\', cursive; {v}; font-size: {size}px; line-height: {lh}; color: #16130f; text-wrap: balance">{sample}</div></div>')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{links}
<style>
body{{margin:0}}
</style>
</helmet>
<div style="box-sizing: border-box; background-color: #ebe8e0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr))">
{chr(10).join(cells)}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1560,"height":2000}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''
out = sys.argv[1]
open(out + "/SpecDisplay.dc.html", "w").write(page("d", DISPLAY, "Two black holes merged. Earth felt space stretch. 36 + 29", 34, 1.04, "Display specimen"))
open(out + "/SpecText.dc.html", "w").write(page("t", TEXT, "LIGO's two detectors caught a ripple in spacetime lasting a fifth of a second. Its shape matches black holes of about 36 and 29 solar masses spiraling into one.", 17, 1.45, "Text specimen"))
open(out + "/SpecMono.dc.html", "w").write(page("m", MONO, "PEER-REVIEWED &nbsp; PHYS. REV. LETT. 116<br>1.0 x 10^-21 &nbsp; 35 to 250 Hz &nbsp; 0.2 s<br><span style=\"font-size: 30px\">410 Mpc</span>", 12, 1.5, "Mono specimen"))
