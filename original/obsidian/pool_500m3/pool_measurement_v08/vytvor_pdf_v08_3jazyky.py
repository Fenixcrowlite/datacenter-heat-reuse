# -*- coding: utf-8 -*-
"""Tri technicke spravy z vykonanych v08 replay: SK/EN/RU."""
from pathlib import Path
import json
from html import escape
import pymupdf
from PIL import Image as PIL
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image
R=Path(__file__).resolve().parents[2]/'results'/'pool_measurement_v08'
j=json.loads((R/'vysledky_v08_SK.json').read_text(encoding='utf-8'))
q=json.loads((R/'QA_NEZAVISLA_V08_SK.json').read_text(encoding='utf-8'))
u=json.loads((R/'NEISTOTY_MERANIA_V08_SK.json').read_text(encoding='utf-8'))
assert q['status']=='PASS' and len(j['cases'])==8
pdfmetrics.registerFont(TTFont('Ar',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArB',r'C:\Windows\Fonts\arialbd.ttf'))
styles={
 't':ParagraphStyle('title',fontName='ArB',fontSize=17,leading=22,spaceAfter=12),
 'h':ParagraphStyle('heading',fontName='ArB',fontSize=11.5,leading=16,spaceBefore=10,spaceAfter=6),
 'p':ParagraphStyle('text',fontName='Ar',fontSize=9.2,leading=13.4,spaceAfter=7),
 'm':ParagraphStyle('math',fontName='Ar',fontSize=9,leading=13,spaceAfter=5,leftIndent=10),
 's':ParagraphStyle('tiny',fontName='Ar',fontSize=7.6,leading=10.6)
}
L={
'SK':{
'title':'V08: externé merania bazéna a reprodukovateľný Simulink replay',
'sub':'8 scenárov × 168 h | 672 vzoriek na scenár | 900 s | dôkaz triedy D',
'h1':'1. Skutočne implementované dátové pripojenie',
'desc':'Model v08 je samostatným potomkom v07. Virtuálne teplotné oneskorenia vstupujúce do bezpečnostného gate boli nahradené dvoma EXTERNÝMI meracími kanálmi z overeného CSV. Pred spracovaním sa testuje presný časový krok, jednotky, zdroj dát a proveniencia. Na vyskúšanie sa použili uložené syntetické časové rady zo skutočných behov Simulink v07, preto nejde o meranie reálneho zariadenia.',
'h2':'2. Rovnice fyziky a signálové podmienky',
'method':'V08 nepozná pravú T vody v safety gate; dostáva dva časovo vzorkované signály T1 a T2. Nepripočítava k nim bias druhýkrát: pôvodný pokus tak urobil, nezávislý QA chybu odhalil a opravil. Termodynamika v04-v07 a redundantné vetvy REJECT sa neprepísali. Spoločná chyba senzorov ostáva bez nezávislej referencie neodhaliteľná.',
'h3':'3. Osemdielny regresný test',
'cols':['Scenár','Max. ΔT [°C]','Max. ΔQ [W]','Δ latch'],
'names':['Zdravý','Prvý ventil','Oba ventily','REJECT záložný','Oba REJECT OFF','IT odľahčenie','Spoločný bias','Kombinácia'],
'h4':'4. Predbežná neistota merania (D predpoklady)',
'inc':'Ilustrácia pre 30 m³/h, ΔT=3 K, dva teplomery s u(T)=0,2 K a relatívne u(prietoku)=5 %. Ide o ŠTANDARDNÉ neistoty pri nezávislých chybách, NIE o údaje skutočnej kalibrácie. Meranie priamo z teploty 500 m³ vody po 15 minútach by bolo extrémne hlučné; potrebný je kalorimeter s dvojicou teplomerov a meraným prietokom.',
'h5':'5. Stav overenia a nesplnená podmienka',
'limit':'Nezávislý Python prešiel {n} kontrolami surových výstupov Simulink a externých signálov. Všetky zdroje sú triedy D. Merania kategórie A s identifikáciou a kalibráciou prístrojov ešte neboli dodané. V08 je preukázaná integrácia signálov a regresná kompatibilita, nie meraná optimalizácia ani prevádzková bezpečnosť.',
'h6':'6. Grafické výsledky vykonaných behov',
'foot':'V08 | SIMULINK REAL RUN, SYNTHETIC D INPUT | 23.10.2026'
},
'EN':{
'title':'V08: external pool measurement channels integrated into Simulink',
'sub':'8 scenarios × 168 h | 672 samples each | 900 s cadence | Class D evidence',
'h1':'1. Implemented time-series input',
'desc':'A new independent v08 model replaces the virtual sensor-delay blocks leading into the safety gate with two external temperature channels from independently validated CSV records. Metadata, UTC timestamps, sampling cadence and source provenance are checked first. The eight actual Simulink replays use previously generated SYNTHETIC v07 traces, not real facility measurements.',
'h2':'2. Thermodynamics and sensor logic',
'method':'The gate now receives two externally supplied T1 and T2 signals; it does not directly access simulated true pool temperature. The first QA run detected an accidental second application of a sensor bias. It was repaired and all scenarios rerun. Thermodynamic and redundant cooling modules otherwise match v07. Shared-mode sensor errors remain intrinsically undetectable without an independent reference.',
'h3':'3. Eight executed replay comparisons',
'cols':['Scenario','Max ΔT [°C]','Max ΔQ [W]','Latch Δ'],
'names':['Healthy','First valve','Both valves','Backup reject','Both rejects off','IT load shedding','Common sensor bias','Combined'],
'h4':'4. Demonstration measurement uncertainty (assumptions only)',
'inc':'The calculation uses 30 m³/h, heat-exchanger delta-T of 3 K, independent temperature standard uncertainties of 0.2 K each and 5% flow uncertainty. These are assumed numbers, NOT calibrated instrument performance. Estimating 15-minute power directly from the 500 m³ pool water temperature is much noisier than flow calorimetry.',
'h5':'5. Independent validation and next dependency',
'limit':'Independent Python checks passed {n} conditions using native Simulink CSV exports and external sensor records. Provenance remains Class D. Physical Class A measurement streams with instrument IDs and calibration records are missing, so physical calibration, safety certification and plant performance estimates are NOT established.',
'h6':'6. Graphs from executed simulations',
'foot':'V08 | SYNTHETIC D INPUT | 2026-10-23'
},
'RU':{
'title':'V08: внешние датчики бассейна подключены к Simulink',
'sub':'8 сценариев по 168 часов | 672 шага на сценарий | 900 с | класс источника D',
'h1':'1. Реальная интеграция временных рядов',
'desc':'Новая модель v08 отдельно сохранена от v07. Два блока виртуальных температурных задержек перед защитным контуром заменены внешними сигналами T1 и T2 из проверенного CSV. До запуска контролируются временные метки UTC, шаг, единицы и происхождение данных. В восьми запусках использованы ранее сохранённые СИНТЕТИЧЕСКИЕ ряды v07, а не реальные показания объекта.',
'h2':'2. Физика и логика измерений',
'method':'Защитный контур получает две внешние температуры и не использует истинную температуру модели напрямую. Независимый QA обнаружил ошибку повторного добавления смещения датчика, после исправления проведён повторный запуск всех сценариев. Энергетическая модель и резервирование охлаждения сохранены. Общая ошибка обоих датчиков без независимой опоры не обнаруживается.',
'h3':'3. Сравнение восьми выполненных сценариев',
'cols':['Сценарий','Макс ΔT [°C]','Макс ΔQ [Вт]','Δ защиты'],
'names':['Нормальный','Первый клапан','Два клапана','Резерв REJECT','Оба REJECT off','Разгрузка ИТ','Общая ошибка','Комплексный отказ'],
'h4':'4. Пример неопределённости измерений (предположения D)',
'inc':'Приняты поток 30 м³/ч, перепад 3 К, стандартная неопределённость двух термометров по 0,2 К и расходомера 5%. Это не паспорт и не калибровка настоящих приборов. Вычисление тепловой мощности по изменению температуры всех 500 м³ за 15 минут даёт намного большую погрешность, чем расчёт через расход и перепад температур.',
'h5':'5. Проверки и недостающие реальные данные',
'limit':'Независимая проверка оригинальных CSV Simulink и входных показаний выполнила {n} условий PASS. Все данные относятся к классу D. Измерений класса A с номерами приборов и документами калибровки нет, поэтому подтверждения реального теплового КПД, промышленной безопасности и фактической экономии здесь нет.',
'h6':'6. Графики фактических расчётов Simulink',
'foot':'V08 | СИНТЕТИЧЕСКИЕ ВХОДЫ D | 23.10.2026'
}}
EQ=[
'C_pool = rho V cp = 997 · 500 · 4182 = 2 084 727 000 J/K',
'T(k+1) = T(k) + 900 [Q_pool_physical - Q_loss]/C_pool',
'T1[k], T2[k] = imported calibrated-format CSV samples; no internal Ttrue input to gate',
'Q_DC = Q_HX_physical + Q_HP_source + Q_REJECT_main + Q_REJECT_backup + Q_unhandled',
'Q_HP_out = Q_HP_source + P_HP_compressor',
'Q_flow = rho (Vdot/3600) cp (T_supply - T_return)',
'u_rel(Q_flow) = sqrt[ u_rel(Vdot)^2 + (sqrt(uT1^2+uT2^2)/deltaT)^2 ]',
'u(Q_from_pool_dT) = C_pool * sqrt(2) * u(T) / 900'
]
def p(t,st='p'):return Paragraph(escape(str(t)),styles[st])
def footer(c,doc,lang):
 c.saveState();c.setFont('Ar',7);c.setFillColor(colors.grey)
 c.drawString(38,22,L[lang]['foot']);c.drawRightString(550,22,str(doc.page));c.restoreState()
for lang,t in L.items():
 filename=R/f'DC_Bazen_Externe_Merania_v08_{lang}.pdf'
 story=[p(t['title'],'t'),p(t['sub']),p(t['h1'],'h'),p(t['desc']),p(t['h2'],'h'),
        p(t['method'])]
 story.extend(p(formula,'m') for formula in EQ)
 story.extend([PageBreak(),p(t['h3'],'h')])
 cells=[[p(v,'s') for v in t['cols']]]
 for i,r in enumerate(j['cases']):
  vals=[t['names'][i],f"{r['maximum_temperature_error_vs_v07_C']:.2e}",
   f"{r['maximum_heat_error_vs_v07_W']:.4f}",f"{r['maximum_latch_error']:.0f}"]
  cells.append([p(v,'s') for v in vals])
 table=Table(cells,colWidths=[200,105,110,89],repeatRows=1)
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf6')),
 ('GRID',(0,0),(-1,-1),.25,colors.HexColor('#c5cfdc')),
 ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
 ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.extend([table,Spacer(1,13),p(t['h4'],'h'),p(t['inc']),
  p(f"Q_flow = {u['nominal_flow_based_heat_W']/1000:.3f} kW; u(Q_flow) = {u['standard_uncertainty_flow_heat_W']/1000:.3f} kW.",'m'),
  p(f"u(Q from 15-min whole-pool dT) = {u['standard_uncertainty_15min_pool_dT_power_W']/1000:.1f} kW.",'m'),
  p(t['h5'],'h'),p(t['limit'].format(n=q['checks'])),
  p('Class A = measured; B = published study; C = manufacturer; D = synthetic / assumption.','s'),
  PageBreak(),p(t['h6'],'h')])
 for fname in ('externe_snimace_v08_SK.png','regresia_tepla_v08_SK.png'):
  im=PIL.open(R/fname)
  width,height=im.size
  story.append(Image(str(R/fname),width=495,height=495*height/width))
  story.append(Spacer(1,8))
 doc=SimpleDocTemplate(str(filename),pagesize=A4,leftMargin=41,rightMargin=41,
  topMargin=39,bottomMargin=37,title=t['title'])
 doc.build(story,onFirstPage=lambda c,d:footer(c,d,lang),onLaterPages=lambda c,d:footer(c,d,lang))
 pdf=pymupdf.open(str(filename));body='\n'.join(pg.get_text() for pg in pdf)
 assert 3<=len(pdf)<=5,(lang,len(pdf))
 assert str(q['checks']) in body.replace(' ','') and '104.236' in body,(lang,'numeric evidence')
 assert sum(len(pg.get_images(full=True)) for pg in pdf)>=2,(lang,'embedded charts')
 if lang=='RU':assert sum(1 for ch in body if '\u0400'<=ch<='\u04ff')>250,(lang,'Cyrillic font')
 for i,page in enumerate(pdf):
  for b in page.get_text('blocks'):
   if b[2]>page.rect.width+1 or b[3]>page.rect.height+1:raise ValueError((lang,i,'overflow'))
 pdf[-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(R/f'PREVIEW_PDF_V08_{lang}.png'))
 print('V08_PDF_VERIFIED',lang,len(pdf),filename.stat().st_size)
