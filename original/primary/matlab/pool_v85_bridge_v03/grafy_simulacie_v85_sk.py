# -*- coding: utf-8 -*-
"""Vektorove grafy bez zavislosti na matplotlib; PDF/Pixmap cez pymupdf."""
from pathlib import Path
import csv,math
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_v85_bridge_v03'
name='service_E3.0_a1.0_H2_dt0.25'
data={}
for mode in ('studena_voda','tepla_voda','stop_bazen'):
 with (OUT/f'sim_{name}__{mode}.csv').open(encoding='utf-8-sig',newline='') as f:
  data[mode]=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
def txt(x,y,string,size=17,color='#17212f',weight='normal'):
 return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial" font-size="{size}" font-weight="{weight}">{string}</text>'
def base(title,xlab,ylab):
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="555" viewBox="0 0 1000 555">','<rect width="1000" height="555" fill="white"/>']
 parts+=[txt(55,40,title,24,weight='bold'),txt(485,530,xlab,18)]
 parts+=['<path d="M95 70 V475 H940" fill="none" stroke="#334155" stroke-width="2"/>']
 parts+=[f'<text x="19" y="317" transform="rotate(-90 19 317)" fill="#17212f" font-family="Arial" font-size="16">{ylab}</text>']
 return parts
def save(parts,name):
 svg=''.join(parts)+ '</svg>'
 (OUT/(name+'.svg')).write_text(svg,encoding='utf-8')
 p=pymupdf.open(stream=svg.encode('utf-8'),filetype='svg')
 p[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(str(OUT/(name+'.png')))
 print('PLOT_OK',name)
# Teplotny priebeh odlisnych pociatocnych T: realne casove body.
parts=base('Prepojenie Stateflow v85 - teplota bazena','Cas scenara [h]','T [C]')
for yval in (16,18,20,22,24,26,28):
 y=475-(yval-15.5)/13*405
 parts+= [f'<path d="M95 {y:.1f} H940" stroke="#e2e8f0"/>',txt(58,y+6,str(yval),15)]
for i in range(5):
 x=95+(i/4)*845
 parts+=[f'<path d="M{x:.1f} 475 v8" stroke="#475569"/>',txt(x-10,505,f'{i/4:.2f}',15)]
colors={'studena_voda':'#2563eb','tepla_voda':'#d97706','stop_bazen':'#64748b'}
for mode,color in colors.items():
 pts=' '.join(f'{95+((r["interval"]+1)/4)*845:.1f},{475-(r["T_bazen_C"]-15.5)/13*405:.1f}' for r in data[mode])
 parts+=[f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4"/>']
 for r in data[mode]:
  x=95+((r["interval"]+1)/4)*845;y=475-(r['T_bazen_C']-15.5)/13*405
  parts+=[f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>']
for i,(m,c) in enumerate(colors.items()):
 parts+=[f'<rect x="{220+i*235}" y="72" width="18" height="18" fill="{c}"/>',txt(244+i*235,87,m.replace('_',' '),15)]
save(parts,'priebeh_bazen_v85_SK')
# Presmerovany vykon - skladane segmenty a povodna sluzba.
parts=base('Presmerovana sluzba v85 bez dvojiteho zapocitania','Cas scenara [h]','kW')
for val in range(0,501,100):
 y=475-val/500*405
 parts+=[f'<path d="M95 {y:.1f} H940" stroke="#e2e8f0"/>',txt(45,y+5,str(val),15)]
for r in data['studena_voda']:
 x=165+r['interval']*205
 qp=r['Q_bazen_W']/1000;qh=r['Q_DH_povodne_W']/1000; qorig=r['Q_v85_povodna_sluzba_W']/1000
 h1=qp/500*405;h2=qh/500*405
 parts+=[f'<rect x="{x:.1f}" y="{475-h1:.1f}" width="92" height="{h1:.1f}" fill="#2563eb"/>',
        f'<rect x="{x:.1f}" y="{475-h1-h2:.1f}" width="92" height="{h2:.1f}" fill="#059669"/>',
        txt(x+20,505,f'{(r["interval"]+1)*0.25:.2f}',15)]
 yorig=475-qorig/500*405
 parts+=[f'<path d="M{x-10} {yorig:.1f} h110" stroke="#111827" stroke-dasharray="5 4" stroke-width="2"/>']
parts+=[f'<rect x="110" y="85" width="18" height="18" fill="#2563eb"/>',txt(136,100,'Do bazena',15),
         f'<rect x="320" y="85" width="18" height="18" fill="#059669"/>',txt(346,100,'Zvysok pre DH',15),
         txt(610,100,'Cierna = povodny vykon v85',15)]
save(parts,'rozdelena_sluzba_v85_SK')
