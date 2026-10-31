from pathlib import Path
import csv
import pymupdf as p
O=Path(__file__).resolve().parents[2]/'results'/'pool_redundancy_v07'
names=['primarny_ventil_zaseknuty','oba_ventily_zaseknute',
       'oba_REJECT_off_bez_shedding','oba_REJECT_off_so_shedding',
       'hlavny_REJECT_off_zalozny_ok']
D={}
for name in names:
 with (O/('scenar_'+name+'_SK.csv')).open(encoding='utf-8-sig',newline='') as f:
  D[name]=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
# Chart I: physical failure despite logical isolation.
doc=p.open();pg=doc.new_page(width=1010,height=470)
pg.insert_text((50,37),'Redundancia uzatvaracich ventilov - fyzicke teplo do bazena',fontsize=19)
pg.insert_text((50,59),'Modra: iba prvy zaseknuty; cervena: oba zaseknute (Q_pool software vypnuty)',fontsize=11)
left,right,top,bottom=87,953,94,390
for yk in (0,5,10,15,20,25):
 y=bottom-(yk/25)*(bottom-top)
 pg.draw_line((left,y),(right,y),color=(.88,.9,.93))
 pg.insert_text((48,y+4),str(yk),fontsize=11)
for t in range(0,169,24):
 x=left+t/168*(right-left)
 pg.draw_line((x,top),(x,bottom),color=(.91,.92,.94))
 pg.insert_text((x-12,416),str(t),fontsize=11)
for name,col in [('primarny_ventil_zaseknuty',(0.2,0.4,0.8)),
 ('oba_ventily_zaseknute',(0.86,.25,.19))]:
 rows=D[name]
 pts=[(left+r['cas_h']/168*(right-left),
        bottom-r['Q_leak_W']/1000/25*(bottom-top)) for r in rows]
 pg.draw_polyline(pts,color=col,width=2.2)
pg.insert_text((445,450),'Cas [h], os Y = kW fyzickeho uniku',fontsize=12)
pg.get_pixmap(matrix=p.Matrix(1.3,1.3),alpha=False).save(str(O/'ventily_a_redundancia_v07_SK.png'))
doc.close()
# Chart II: risk buffer with and without modeled IT load reduction.
doc=p.open();pg=doc.new_page(width=1010,height=500)
pg.insert_text((50,37),'Obe vetvy REJECT mimo prevadzky - efekt znizenia IT zataze',fontsize=19)
pg.insert_text((50,58),'Modra: automaticke odlahcenie, cervena: bez odlahcenia',fontsize=12)
left,right,top,bottom=87,953,91,416
for yk in (30,35,38,40,42,45,50):
 y=bottom-(yk-28)/24*(bottom-top)
 pg.draw_line((left,y),(right,y),color=(.86,.89,.92))
 pg.insert_text((48,y+3),str(yk),fontsize=11)
for t in range(0,169,24):
 x=left+t/168*(right-left)
 pg.draw_line((x,top),(x,bottom),color=(.92,.93,.95))
 pg.insert_text((x-11,440),str(t),fontsize=11)
for name,color in [('oba_REJECT_off_so_shedding',(0.13,.34,.78)),
 ('oba_REJECT_off_bez_shedding',(0.86,.23,.19))]:
 pts=[(left+r['cas_h']/168*(right-left),
       bottom-(r['T_IT_model_C']-28)/24*(bottom-top)) for r in D[name]]
 pg.draw_polyline(pts,color=color,width=2.5)
pg.insert_text((50,481),'Os Y: teplota modeloveho IT buffera [C], NIE teplota CPU / serverov.',fontsize=11)
pg.get_pixmap(matrix=p.Matrix(1.3,1.3),alpha=False).save(str(O/'IT_riziko_v07_SK.png'))
doc.close()
print('V07_CHARTS_OK',2)
