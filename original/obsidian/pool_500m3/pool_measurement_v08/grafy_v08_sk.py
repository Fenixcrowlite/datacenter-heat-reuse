from pathlib import Path
import csv,pymupdf as p
R=Path(__file__).resolve().parents[2]/'results'/'pool_measurement_v08'
def read(n):
 with (R/f'sim_v08_{n}_SK.csv').open(encoding='utf-8-sig',newline='') as f:
  return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
case=read('spolocny_bias_senzorov')
d=p.open();pg=d.new_page(width=1020,height=500)
pg.insert_text((48,36),'Odchylka externych snimacov v08 voci modelovanej vode',fontsize=18)
pg.insert_text((48,60),'Modra = 0 K referencia, oranzova = T1-Tmodel, cervena = T2-Tmodel; spolocny bias -0.4 K',fontsize=11)
left,right,top,bottom=102,964,93,430
for T in (-.7,-.5,-.3,-.1,.1):
 y=bottom-(T+.75)/.9*(bottom-top)
 pg.draw_line((left,y),(right,y),color=(.88,.91,.94))
 pg.insert_text((54,y+4),f'{T:.1f} K',fontsize=11)
for hour in (24,28,32,36,40,44,48):
 x=left+(hour-24)/24*(right-left)
 pg.draw_line((x,top),(x,bottom),color=(.93,.94,.96))
 pg.insert_text((x-11,455),str(hour),fontsize=11)
for field,color in [('T_pool_C',(.14,.4,.8)),('external_T1_C',(.95,.55,.15)),
                    ('external_T2_C',(.8,.2,.19))]:
 pts=[(left+(r['cas_h']-24)/24*(right-left),
   bottom-((r[field]-r['T_pool_C'])+.75)/.9*(bottom-top)) for r in case if 24<=r['cas_h']<=48]
 pg.draw_polyline(pts,color=color,width=2.4)
pg.insert_text((365,486),'Cas [h], os Y = chyba T [K]; iba D-synteticky replay',fontsize=11)
pg.get_pixmap(matrix=p.Matrix(1.45,1.45),alpha=False).save(str(R/'externe_snimace_v08_SK.png'))
d.close()
# regression error across cases
import json
j=json.loads((R/'vysledky_v08_SK.json').read_text(encoding='utf-8'))
d=p.open();pg=d.new_page(width=1020,height=485)
pg.insert_text((50,36),'Regresná zhoda v08 s v07 - maximálna absolútna odchýlka',fontsize=18)
pg.insert_text((50,60),'Odchýlky Q_pool v watt-och pre rovnaké D-vstupy. 8 skutocnych Simulink replay behov.',fontsize=11)
left,right,top,bottom=325,948,89,416
for xval in (0,.01,.02,.03,.04,.05):
 x=left+xval/.05*(right-left)
 pg.draw_line((x,top),(x,bottom),color=(.85,.88,.91))
 pg.insert_text((x-10,441),f'{xval:.2f}',fontsize=10)
for i,row in enumerate(j['cases']):
 y=top+15+i*40
 value=row['maximum_heat_error_vs_v07_W']
 pg.insert_text((48,y+13),row['scenario'].replace('_',' ')[:37],fontsize=11)
 pg.draw_rect(p.Rect(left,y,left+value/.05*(right-left),y+18),
    color=None,fill=(.18,.43,.75))
 pg.insert_text((left+value/.05*(right-left)+7,y+13),f'{value:.4f} W',fontsize=10)
pg.insert_text((470,473),'Os X = maximalny rozdiel vypoctu tepla [W]',fontsize=11)
pg.get_pixmap(matrix=p.Matrix(1.45,1.45),alpha=False).save(str(R/'regresia_tepla_v08_SK.png'))
d.close()
print('V08_CHARTS_OK 2')
