def rgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def hx(c): return '#%02X%02X%02X'%tuple(int(round(x)) for x in c)
def lum(h):
    def f(v):
        v/=255
        return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    r,g,b=rgb(h); return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def cr(a,b):
    la,lb=lum(a),lum(b)
    if la<lb: la,lb=lb,la
    return (la+0.05)/(lb+0.05)
def mul(a,b): return hx(tuple(x*y/255 for x,y in zip(rgb(a),rgb(b))))
def scr(a,b): return hx(tuple(255-(255-x)*(255-y)/255 for x,y in zip(rgb(a),rgb(b))))
P = {
 "engraved day": {"stock":"#E9E6DE","ink":"#16130F","muted":"#5A554B","live":"#E0330A","screenline":"#16130F"},
 "engraved night": {"ground":"#0E1116","text":"#E9E4D7","muted":"#9C988D","structure":"#5E6573","texture":"#2B303B","live":"#FFA63D"},
 "overprint day": {"stock":"#F2F1EC","blue":"#1F3FD0","pink":"#FF4FA3","pinkdeep":"#F0308C"},
 "overprint night": {"ground":"#0C0A26","text":"#F2EFF8","muted":"#A9A4C8","bluelight":"#7A97FF","pinklight":"#FF74B8","structure":"#5A56A8","texture":"#272458","live":"#FFF7FB"},
 "recorder day": {"stock":"#EDF0EA","ink":"#0F1F1A","muted":"#4C5C55","grid":"#C3CFC6","live":"#00794C"},
 "recorder night": {"ground":"#07130F","text":"#DDE7DF","muted":"#8DA397","structure":"#4A6E5E","texture":"#173027","live":"#62F5A4"},
}
for name,p in P.items():
    base = p.get("stock") or p.get("ground")
    print(name, "base", base)
    for k,v in p.items():
        if v==base: continue
        print(f"   {k:11s} {v}  vs base {cr(v,base):5.2f}")
d=P["overprint day"]
ov=mul(d["blue"],d["pink"]); print("overprint blue x pink", ov, "vs stock", round(cr(ov,d["stock"]),2), "stock on blue", round(cr(d["stock"],d["blue"]),2), "stock on overprint", round(cr(d["stock"],ov),2))
ov2=mul(d["blue"],d["pinkdeep"]); print("overprint blue x pinkdeep", ov2, round(cr(ov2,d["stock"]),2))
n=P["overprint night"]
print("screen bluelight+pinklight", scr(n["bluelight"],n["pinklight"]))
print("ink on pink", round(cr(ov,d["pink"]),2), "ink on pinkdeep", round(cr(ov2,d["pinkdeep"]),2))
print("night ground on bluelight", round(cr(n["ground"],n["bluelight"]),2), "ground on pinklight", round(cr(n["ground"],n["pinklight"]),2))
e=P["engraved day"]; print("stock on ink (reversed band)", round(cr(e["stock"],e["ink"]),2), "stock on live", round(cr(e["stock"],e["live"]),2), "ink on live", round(cr(e["ink"],e["live"]),2))
en=P["engraved night"]; print("ground on live night", round(cr(en["ground"],en["live"]),2))
r=P["recorder day"]; print("stock on live rec", round(cr(r["stock"],r["live"]),2)); rn=P["recorder night"]; print("ground on live night rec", round(cr(rn["ground"],rn["live"]),2))
