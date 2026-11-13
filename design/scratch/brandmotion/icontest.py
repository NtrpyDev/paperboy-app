from bm import *
cells=[]
for i,(kw,name) in enumerate([
 (dict(pitch=8.0,trap=7.0),"p8 t7"),
 (dict(pitch=8.0,trap=0.01),"p8 t0"),
 (dict(pitch=10.67,trap=6.0),"p10.7 t6"),
 (dict(pitch=6.4,trap=6.0),"p6.4 t6"),
]):
    row="".join(icon(f"t{i}{j}",s,th,**kw) for j,(s,th) in enumerate(((300,"day"),(96,"day"),(48,"day"),(300,"night"),(96,"night"),(48,"night"))))
    cells.append(f'<div style="display:flex;gap:16px;align-items:flex-end">{row}<div style="{lab()}">{name}</div></div>')
body=f'<div style="width:1200px;height:1320px;background:{STOCK};padding:16px;box-sizing:border-box;display:flex;flex-direction:column;gap:16px">{"".join(cells)}</div>'
(HERE/"IconTest.dc.html").write_text(page("icon test","body{margin:0}",body,1200,1320))
