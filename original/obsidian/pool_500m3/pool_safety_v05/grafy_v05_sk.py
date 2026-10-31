from pathlib import Path
import csv
import pymupdf as fitz
base=Path(__file__).resolve().parents[2]/"results"/"pool_safety_v05"
names=["normalny","rozdiel_senzorov","pomaly_drift_senzora","bez_prietoku",
       "havarijne_tlacidlo","reset_pocas_poruchy","oba_senzory_bias"]
labels=["Bez poruchy","Nesuhlas teplotnych snimacov","Pomaly drift senzora",
        "Bez prietoku","Havarijne tlacidlo","Reset pocas poruchy","Spolocny bias senzorov"]
records=[]
for name in names:
 with (base/f"scenar_{name}_SK.csv").open(encoding="utf-8-sig",newline="") as f:
  records.append([{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)])
p=fitz.open()
page=p.new_page(width=1060,height=530)
page.insert_text((47,37),"Zablokovanie ohrevu bazena - 7 simulovanych scenarov",fontsize=20,color=(.12,.2,.3))
page.insert_text((47,61),"Skutocne vykonane simulacie; 15-minutove kroky; synteticke senzoricke poruchy",fontsize=11,color=(.4,.44,.52))
for i in range(0,169,24):
 x=245+i/168*770
 page.draw_line((x,96),(x,437),color=(.84,.86,.89),width=.8)
 page.insert_text((x-11,463),str(i),fontsize=11,color=(.2,.3,.4))
for n,(name,lab,rr) in enumerate(zip(names,labels,records)):
 y=116+n*47
 page.insert_text((24,y+14),lab,fontsize=12,color=(.12,.2,.3))
 page.draw_rect(fitz.Rect(245,y,1015,y+23),color=(.85,.86,.89),fill=(.95,.96,.98))
 for r in rr:
  if r["blokovanie"]>.5:
   x1=245+r["cas_h"]/168*770
   x2=x1+0.25/168*770+.05
   page.draw_rect(fitz.Rect(x1,y,x2,y+23),color=None,fill=(.89,.25,.20))
page.insert_text((570,491),"Cas [h]  | Cervena = blokovany ohrev",fontsize=13,color=(.15,.2,.3))
pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
pix.save(str(base/"interlock_timeline_v05_SK.png"))
p.close()
# Tepelny priebeh dvoch porovnatelnych profilov.
p=fitz.open();page=p.new_page(width=1060,height=525)
page.insert_text((47,36),"Teplota vody pri poruche a bez poruchy",fontsize=20,color=(.12,.2,.3))
page.insert_text((47,58),"Porovnanie zaklad vs. rozdiel teplotnych snimacov; SYNTHETIC",fontsize=11,color=(.4,.44,.52))
left,top,right,bottom=90,87,1010,440
for T in (16,18,20,22,24,26,28):
 y=bottom-(T-15.5)/13*350
 page.draw_line((left,y),(right,y),color=(.86,.89,.92),width=.8)
 page.insert_text((45,y+4),str(T),fontsize=11)
for t in (0,24,48,72,96,120,144,168):
 x=left+t/168*(right-left)
 page.draw_line((x,top),(x,bottom),color=(.9,.91,.93),width=.8)
 page.insert_text((x-8,460),str(t),fontsize=11)
for j,color in ((0,(.10,.32,.82)),(1,(.9,.32,.16))):
 rr=records[j];pts=[]
 for r in rr:
  x=left+r["cas_h"]/168*(right-left)
  y=bottom-(r["T_bazen_C"]-15.5)/13*350
  pts.append((x,y))
 page.draw_polyline(pts,color=color,width=2)
page.insert_text((88,494),"Vodorovna os = cas [h]; zvisla os = teplota [C]",fontsize=12)
page.insert_text((590,494),"Modra = normal; cervena = porucha senzora",fontsize=12)
page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(base/"teplota_poruchy_v05_SK.png"))
p.close()
print("V05_CHARTS_RENDERED",2)
