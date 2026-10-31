from pathlib import Path
import csv
import pymupdf as z
O=Path(__file__).resolve().parents[2]/'results'/'pool_failure_v06'
names=['zdravy','oneskorene_snimace_bias','spolocny_bias_nedetekovany',
       'zaseknuty_ventil','vypadok_REJECT','bez_prietoku','kombinovana_porucha']
D={}
for name in names:
 with (O/f'scenar_{name}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  D[name]=[{k:float(v) for k,v in rec.items()} for rec in csv.DictReader(f)]
def picture(page,name):
 page.get_pixmap(matrix=z.Matrix(1.4,1.4),alpha=False).save(str(O/name))
# Absolute risk temperature in modelled IT thermal buffer.
p=z.open();page=p.new_page(width=980,height=500)
page.insert_text((58,35),'Modelova teplota tepelneho buffera IT pri poruche REJECT',fontsize=17)
left,right,top,bottom=93,925,65,433
for v in (30,35,40,42,45,50):
 y=bottom-(v-28)/24*(bottom-top)
 page.draw_line((left,y),(right,y),color=(.84,.88,.93),width=.9)
 page.insert_text((48,y+4),str(v),fontsize=12)
for hour in (0,24,48,72,96,120,144,168):
 x=left+hour/168*(right-left)
 page.draw_line((x,top),(x,bottom),color=(.91,.92,.94),width=.5)
 page.insert_text((x-8,bottom+25),str(hour),fontsize=12)
for name,color in [('zdravy',(0.15,0.5,0.85)),('vypadok_REJECT',(0.83,0.25,0.22)),('kombinovana_porucha',(0.77,0.47,0.13))]:
 rows=D[name]
 pts=[(left+r['cas_h']/168*(right-left),bottom-(r['T_IT_risk_C']-28)/24*(bottom-top)) for r in rows]
 page.draw_polyline(pts,color=color,width=2.6)
page.draw_line((left,bottom-(42-28)/24*(bottom-top)),(right,bottom-(42-28)/24*(bottom-top)),color=(.9,.1,.1),width=1,dashes='[4 4] 0')
page.insert_text((70,486),'Cas [h] | Modelovy signal rizika - NIE namerane teploty serverov',fontsize=11)
picture(page,'teplota_IT_riziko_v06_SK.png');p.close()
# Red overlay = actual physical leakage while software heat request is zero.
p=z.open();page=p.new_page(width=980,height=510)
page.insert_text((50,35),'Povel STOP vs. zaseknuty ventil: skutocny unik tepla',fontsize=18)
page.insert_text((50,57),'Cervena = fyzikalny prenos tepla napriek nulovemu povelu, modra = SW blokovanie',fontsize=11)
rows=D['zaseknuty_ventil']
left,right=94,925;top=125
for n,key,color in ((0,'safety_latched',(0.23,0.45,0.82)),(1,'leak_without_command',(0.85,0.25,0.19))):
 y=top+n*104
 page.insert_text((48,y-18),('Safety latch','Netesny ventil')[n],fontsize=14)
 page.draw_rect(z.Rect(left,y,right,y+35),color=(.84,.85,.88),fill=(.96,.97,.98))
 for r in rows:
  if r[key]>.5:
   x=left+r['cas_h']/168*(right-left)
   page.draw_rect(z.Rect(x,y,x+.25/168*(right-left)+.1,y+35),color=None,fill=color)
for h in range(0,169,24):
 x=left+h/168*(right-left)
 page.draw_line((x,top+230),(x,top+241),color=(.3,.3,.3))
 page.insert_text((x-9,top+264),str(h),fontsize=12)
page.insert_text((380,467),'Cas simulacie [h], 15 minutovy krok',fontsize=12)
picture(page,'povel_vs_prietok_v06_SK.png');p.close()
print('V06_GRAPHICS_OK',2)
