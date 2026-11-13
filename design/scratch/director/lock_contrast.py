"""WCAG contrast for the locked First Light tokens. Run: python lock_contrast.py"""
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
if __name__ == "__main__":
    import sys
    pairs = [a.split(":") for a in sys.argv[1:]]
    for a,b in pairs:
        print(f"{a} on {b}: {cr(a,b):.2f}  L*a={lum(a):.3f} L*b={lum(b):.3f}")
