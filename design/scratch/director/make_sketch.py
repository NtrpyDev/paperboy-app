import math, sys
def chirp(w=350, amp=34, n=700):
    pts=[]
    for i in range(n+1):
        x=w*i/n; t=i/n
        if t<0.78:
            u=t/0.78
            a=amp*(0.10+0.90*u**3.2)
            ph=2*math.pi*(2.2*u+9.5*u**4)
        else:
            u=(t-0.78)/0.22
            a=amp*math.exp(-7*u)
            ph=2*math.pi*(2.2+9.5)+2*math.pi*5.5*u
        pts.append((x, -a*math.sin(ph)))
    return "M"+" L".join(f"{x:.1f} {y:.1f}" for x,y in pts)
C=chirp()
FONTS='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Display:ital,wdth,wght@0,62.5..100,100..900;1,62.5..100,100..900&family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&family=Big+Shoulders:opsz,wght@10..72,100..900&family=Martian+Mono:wdth,wght@75..112.5,100..800&display=swap">'
def tile(bg, fg, font, fstyle, svg, slug, slugcol):
    return f'''<div style="display: flex; flex-direction: column; background-color: {bg}; color: {fg}">
<div style="position: relative; height: 290px; overflow: hidden">{svg}
<div style="position: absolute; left: 20px; top: 14px; font-family: 'Martian Mono', monospace; font-size: 10px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; color: {slugcol}">{slug}</div>
</div>
<div style="padding: 18px 20px 26px; font-family: {font}; {fstyle}; text-wrap: balance">Two black holes merged. Earth felt space stretch.</div>
</div>'''
def engraved(day):
    ink = "#16130F" if day else "#5E6573"
    live = "#E0330A" if day else "#FFA63D"
    halo = "" if day else f'<path d="{C}" fill="none" stroke="{live}" stroke-width="6" stroke-opacity="0.18" stroke-linejoin="round" stroke-linecap="round"></path>'
    rings="".join(f'<circle cx="150" cy="118" r="{r}" fill="none" stroke="{ink}" stroke-width="{0.6 if r>70 else 0.9}"></circle>' for r in range(20,260,9))
    pid = "ed" if day else "en"
    return f'''<svg viewBox="0 0 390 290" role="img" aria-label="Illustration of two black holes and the chirp signal" style="position: absolute; inset: 0; width: 100%; height: 100%">
<defs>
<pattern id="{pid}a" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.2" height="2.2" fill="{ink}"></rect></pattern>
<pattern id="{pid}b" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="3.2" height="1.1" fill="{ink}"></rect></pattern>
<clipPath id="{pid}c"><rect x="0" y="0" width="390" height="210"></rect></clipPath>
</defs>
<g clip-path="url(#{pid}c)">{rings}</g>
<circle cx="128" cy="112" r="44" fill="{"#E9E6DE" if day else "#0E1116"}"></circle>
<circle cx="128" cy="112" r="44" fill="url(#{pid}b)"></circle>
<circle cx="128" cy="112" r="24" fill="url(#{pid}a)"></circle>
<circle cx="192" cy="126" r="36" fill="{"#E9E6DE" if day else "#0E1116"}"></circle>
<circle cx="192" cy="126" r="36" fill="url(#{pid}b)"></circle>
<circle cx="192" cy="126" r="19" fill="url(#{pid}a)"></circle>
<line x1="20" y1="240" x2="370" y2="240" stroke="{ink}" stroke-width="0.75"></line>
<g transform="translate(20 240)">{halo}<path d="{C}" fill="none" stroke="{live}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="stroke-dasharray: 1; animation: draw 1.8s linear 0.3s both"></path></g>
</svg>'''
def overprint(day):
    if day:
        blue, pink, line, bg, blend = "#1F3FD0", "#F0308C", "#F2F1EC", "#F2F1EC", "multiply"
    else:
        blue, pink, line, bg, blend = "#7A97FF", "#FF74B8", "#FFF7FB", "#0C0A26", "screen"
    pid = "od" if day else "on"
    field = (f'<rect x="0" y="0" width="390" height="290" fill="{blue}"></rect>' if day else f'<rect x="0" y="0" width="390" height="290" fill="url(#{pid}f)"></rect>')
    halo = "" if day else f'<path d="{C}" fill="none" stroke="#FF74B8" stroke-width="7" stroke-opacity="0.22" stroke-linejoin="round" stroke-linecap="round"></path>'
    return f'''<svg viewBox="0 0 390 290" role="img" aria-label="Illustration of two black holes and the chirp signal" style="position: absolute; inset: 0; width: 100%; height: 100%">
<defs>
<pattern id="{pid}f" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(15)"><rect width="4" height="1" fill="#272458"></rect></pattern>
<pattern id="{pid}p" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(75)"><rect width="4" height="2.6" fill="{pink}"></rect></pattern>
<pattern id="{pid}b" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(15)"><rect width="4" height="2.6" fill="{blue}"></rect></pattern>
</defs>
{field}
<circle cx="150" cy="120" r="92" fill="{("url(#"+pid+"p)")}" style="mix-blend-mode: {blend}"></circle>
<circle cx="222" cy="138" r="70" fill="{pink if day else "url(#"+pid+"b)"}" style="mix-blend-mode: {blend}"></circle>
<circle cx="150" cy="120" r="30" fill="{"#1D0C72" if day else "#0C0A26"}"></circle>
<circle cx="222" cy="138" r="23" fill="{"#1D0C72" if day else "#0C0A26"}"></circle>
<g transform="translate(20 236)">{halo}<path d="{C}" fill="none" stroke="{line}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="stroke-dasharray: 1; animation: draw 1.8s linear 0.3s both"></path></g>
</svg>'''
def recorder(day):
    if day: grid, ink, live, bg = "#C3CFC6", "#0F1F1A", "#00794C", "#EDF0EA"
    else: grid, ink, live, bg = "#173027", "#8DA397", "#62F5A4", "#07130F"
    g="".join(f'<line x1="{x}" y1="40" x2="{x}" y2="250" stroke="{grid}" stroke-width="{1 if (x-20)%70==0 else 0.5}"></line>' for x in range(20,371,14))
    g+="".join(f'<line x1="20" y1="{y}" x2="370" y2="{y}" stroke="{grid}" stroke-width="{1 if (y-40)%70==0 else 0.5}"></line>' for y in range(40,251,14))
    ticks="".join(f'<line x1="{x}" y1="250" x2="{x}" y2="{258 if (x-20)%70==0 else 254}" stroke="{ink}" stroke-width="0.75"></line>' for x in range(20,371,14))
    halo = "" if day else f'<path d="{C}" fill="none" stroke="{live}" stroke-width="6" stroke-opacity="0.2" stroke-linejoin="round" stroke-linecap="round"></path>'
    return f'''<svg viewBox="0 0 390 290" role="img" aria-label="Illustration of the chirp signal on chart paper" style="position: absolute; inset: 0; width: 100%; height: 100%">
{g}{ticks}
<line x1="20" y1="250" x2="370" y2="250" stroke="{ink}" stroke-width="0.75"></line>
<g transform="translate(20 145) scale(1 2.2)">{halo}<path d="{C}" fill="none" stroke="{live}" stroke-width="{0.8 if day else 0.65}" stroke-linejoin="round" stroke-linecap="round" pathLength="1" style="stroke-dasharray: 1; animation: draw 1.8s linear 0.3s both"></path></g>
<circle cx="370" cy="145" r="3.5" fill="{live}"></circle>
</svg>'''
tiles=[
 tile("#E9E6DE","#16130F","'Noto Serif Display', Georgia, serif","font-size: 40px; line-height: 1.0; font-weight: 800; font-stretch: 62.5%; letter-spacing: -0.005em", engraved(True), "Plate 1 / Illustration, not to scale", "#16130F"),
 tile("#F2F1EC","#1D0C72","'Bricolage Grotesque', 'Arial Black', sans-serif","font-size: 35px; line-height: 1.0; font-weight: 800; letter-spacing: -0.03em", overprint(True), "Plate 1 / Illustration", "#F2F1EC"),
 tile("#EDF0EA","#0F1F1A","'Big Shoulders', 'Arial Narrow', sans-serif","font-size: 42px; line-height: 1.0; font-weight: 600; letter-spacing: 0", recorder(True), "Trace 1 / Illustration of the signal", "#4C5C55"),
 tile("#0E1116","#E9E4D7","'Noto Serif Display', Georgia, serif","font-size: 40px; line-height: 1.0; font-weight: 800; font-stretch: 62.5%; letter-spacing: -0.005em", engraved(False), "Plate 1 / Illustration, not to scale", "#9C988D"),
 tile("#0C0A26","#F2EFF8","'Bricolage Grotesque', 'Arial Black', sans-serif","font-size: 35px; line-height: 1.0; font-weight: 800; letter-spacing: -0.03em", overprint(False), "Plate 1 / Illustration", "#A9A4C8"),
 tile("#07130F","#DDE7DF","'Big Shoulders', 'Arial Narrow', sans-serif","font-size: 42px; line-height: 1.0; font-weight: 600; letter-spacing: 0", recorder(False), "Trace 1 / Illustration of the signal", "#8DA397"),
]
html=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Director mechanics sketch</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
body{{margin:0}}
@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}
</style>
</helmet>
<div style="width: 1170px; box-sizing: border-box; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr))">
{chr(10).join(tiles)}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1170,"height":900}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''
open(sys.argv[1],"w").write(html)
