# -*- coding: utf-8 -*-
"""Three technical PDF reports for actual 7-day Stateflow closed-loop run v04."""
import json
from pathlib import Path
from html import escape
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
BASE=Path(__file__).resolve().parents[2]
O=BASE/'results'/'pool_feedback_v04'
d=json.loads((O/'vysledky_dispecer_v04_SK.json').read_text(encoding='utf-8'))
q=json.loads((O/'QA_NEZAVISLA_V04_SK.json').read_text(encoding='utf-8'))
assert q['status']=='PASS' and len(d['scenarios'])==8
pdfmetrics.registerFont(TTFont('Ar',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArB',r'C:\Windows\Fonts\arialbd.ttf'))
ST={
 'title':ParagraphStyle('ti',fontName='ArB',fontSize=16.5,leading=22,spaceAfter=14),
 'h':ParagraphStyle('h',fontName='ArB',fontSize=11.5,leading=16,spaceBefore=10,spaceAfter=6),
 'p':ParagraphStyle('p',fontName='Ar',fontSize=9.3,leading=14,spaceAfter=8),
 'formula':ParagraphStyle('fm',fontName='Ar',fontSize=9,leading=13,spaceAfter=6,leftIndent=11),
 'tiny':ParagraphStyle('tiny',fontName='Ar',fontSize=7.7,leading=10.5),
}
TR={
'SK':{
'title':'Uzavretá regulácia DC - bazén 500 m³ a tepelná sieť (v04)',
'sub':'Stateflow a Simulink R2026a, 168 hodín, osem syntetických scenárov. Nepreukazuje skutočnú prevádzku.',
'arch':'1. Architektúra a fyzikálna hranica',
'desc':'Nový dispečer je uzavretá regulačná slučka: teplota vody, požiadavka bazéna a stav TES sa vracajú do Stateflow. Dispečer prepína PRIAMY HX, TČ, TES, odstavenie IT a bez zdroja. Pôvodná nezmenená v85 slúži ako nezávislý historický etalón, nie ako vykonávací blok nového v04. Tepelný výkon DC je syntetický vstup.',
'physics':'2. Rovnice prenosu tepla a akumulácie',
'physdesc':'Energetický model bazéna je jedna dokonale premiešaná hmota vody, UA a odpar sú zvolené modelové parametre. Tepelný zásobník je vysokoteplotný scenár bez rozloženia teploty a bez hydrauliky. COP(T) je Carnotov odhad, nie overená mapa výrobcu.',
'control':'3. Regulácia výkonov a bezpečné podmienky',
'controltext':'Termostat: zapnutie 27,35 °C, vypnutie 27,65 °C, modelový horný strop 27,75 °C. Pre IT_ok=0 sa dostupné zdrojové teplo odvádza do nezávislej vetvy; TES ešte môže pomáhať tepelnej sieti. BAZEN_ok=0 znamená nulový prívod tepla do bazéna. Výkon HP výstup max. 200 kW, kompresor 55 kW; výkon do bazéna max. 150 kW.',
'results':'4. Reálne spustené porovnávacie scenáre',
'cols':['Scenár','Bazén MWh','Sieť MWh','TČ el. MWh','Nevyhovená sieť MWh'],
'names':['Základ','Bazén vypnutý','IT STOP 24h','DC bez zdroja','Teplejší zdroj','Bez plachty','TES vypnuté','Vysoký dopyt DH'],
'qa':'5. Overenia, neistota a ďalšie práce',
'qatext':'Nezávislé CSV QA prešlo {n} kontrolami v ôsmich prípadoch. V každom 15-minútovom kroku sa kontrolujú prvý zákon, priradenie DC zdroja, výstup TČ, stav TES, teplota vody, režim Stateflow a výpadky. Žiadny výpočet neposkytuje certifikáciu: na reálny návrh chýbajú merané profily, výrobné mapy TČ, prietoky, tlakové straty, vysušenie haly, poruchové snímače a platné právne znenie.',
'fig':'6. Teplota bazéna za sedem dní',
'footer':'DCHR v04 | SYNTHETICKÉ ÚDAJE | 2026-10-23',
},
'EN':{
'title':'Closed-loop DC heat dispatch for a 500 m³ pool (v04)',
'sub':'Executed Stateflow and Simulink R2026a: 168 hours, eight synthetic scenarios. Not field-measured.',
'arch':'1. Architecture and physical scope',
'desc':'A new closed-loop dispatcher receives water temperature, pool heat demand and TES inventory as feedback. Stateflow selects direct exchanger, heat pump, TES-only, IT shutdown or no-source operation. The unchanged original v85 is a preserved reference, not the controller of this new v04. DC heat input is generated synthetically.',
'physics':'2. Thermodynamic conservation and storage',
'physdesc':'The pool is modelled as one well-mixed thermal capacity, with assumed evaporation and heat-loss coefficients. TES is a lumped high-grade store without stratification or hydraulic sizing. COP(T) uses a bounded Carnot-style hypothesis, not verified manufacturer performance.',
'control':'3. Allocation and protective constraints',
'controltext':'Thermostat: ON below 27.35 °C, OFF above 27.65 °C, predicted water ceiling 27.75 °C. IT_ok=0 routes recoverable heat to independent rejection, while TES may still serve district heat. BAZEN_ok=0 stops pool heating only. Heat-pump output is capped at 200 kW, compressor at 55 kW, pool input at 150 kW.',
'results':'4. Executed comparison scenarios',
'cols':['Scenario','Pool MWh','DH MWh','HP el. MWh','Unmet DH MWh'],
'names':['Base','Pool disabled','IT shutdown 24h','No DC source','Warmer source','No pool cover','TES disabled','High DH demand'],
'qa':'5. Independent QA, uncertainty and next work',
'qatext':'Independent CSV analysis passed {n} checks for eight cases. For every 15-minute time step it verifies source and heat-pump first-law balances, TES energy, pool temperature, Stateflow mode and emergency isolation. No physical commissioning or certified compliance is claimed. Measurements, manufacturer COP maps, hydraulic sizing, natatorium HVAC, fault-tolerant sensing and consolidated regulatory review remain necessary.',
'fig':'6. Pool temperature during the seven-day scenarios',
'footer':'DCHR v04 | SYNTHETIC DATA | 2026-10-23',
},
'RU':{
'title':'Замкнутый диспетчер тепла ЦОД и бассейна 500 м³ (v04)',
'sub':'Реальные запуски Stateflow и Simulink R2026a: 168 часов, 8 синтетических сценариев.',
'arch':'1. Архитектура и физическая граница модели',
'desc':'В новом замкнутом диспетчере температура воды, запрос мощности бассейна и энергия аккумулятора поступают обратно в Stateflow. Контроллер переключает прямой теплообменник, тепловой насос, режим накопителя, остановку ИТ и отсутствие источника. Оригинальная v85 остаётся неизменённым эталоном, но не является управляющим блоком новой v04. Источник тепла ЦОД задан синтетически.',
'physics':'2. Сохранение энергии и тепловое накопление',
'physdesc':'Бассейн представлен одной идеально перемешанной массой воды. Коэффициенты испарения и потерь сценарные. Накопитель рассматривается как единый высокотемпературный резервуар без слоёв и гидравлики. COP(T) определён упрощённой ограниченной моделью Карно, не паспортными измерениями производителя.',
'control':'3. Регулирование мощности и ограничения',
'controltext':'Термостат: включение при 27,35°C, выключение при 27,65°C, расчётный потолок 27,75°C. Когда IT_ok=0, извлекаемое тепло направляется на независимый сброс; накопитель при этом может обслуживать теплосеть. При BAZEN_ok=0 нагрев бассейна прекращается. Ограничения: тепловой насос 200 кВт, компрессор 55 кВт, бассейн 150 кВт.',
'results':'4. Результаты выполненных сценариев',
'cols':['Сценарий','Бассейн МВт·ч','Сеть МВт·ч','Эл. ТН МВт·ч','Дефицит сети МВт·ч'],
'names':['Базовый','Бассейн отключён','Остановка ИТ 24 ч','Нет источника ЦОД','Тёплый источник','Без покрытия','Накопитель отключён','Высокий спрос сети'],
'qa':'5. Независимая проверка, неопределённость и дальнейшие работы',
'qatext':'Независимый контроль CSV успешно выполнил {n} проверок в восьми сценариях. Для каждого 15-минутного интервала проверены балансы источника, насоса и TES, температура воды, состояния Stateflow и сигналы защиты. Модель не прошла физические испытания и не подтверждает сертификацию. Требуются измеренные профили, карты COP, расчёт гидравлики, вентиляция и осушение помещения, защита от отказов и проверка актуальных нормативов.',
'fig':'6. Температура бассейна за семь суток',
'footer':'DCHR v04 | СИНТЕТИЧЕСКИЕ ДАННЫЕ | 2026-10-23',
}
}
FORMULAS=[
'C_pool = rho V cp = 997 · 500 · 4182 = 2 084 727 000 J/K',
'E_water(16 -> 28°C) = C_pool · 12 / 3.6e9 = 6.94909 MWh (without losses)',
'T(k+1) = T(k) + 900 (Q_pool - Q_loss) / C_pool',
'Q_loss = Q_evap + Q_conv + Q_rad + Q_construction + Q_makeup + 2 kW',
'Q_DC_available = Q_direct + Q_HP_source + Q_reject',
'Q_HP_out = Q_HP_pool + Q_HP_DH + Q_HP_TES = Q_HP_source + P_HP_compressor',
'Q_pool = Q_direct + Q_HP_pool ; Q_DH = Q_HP_DH + Q_TES_discharge',
'E_TES(k+1) = E_TES(k) + 900 (0.93 Q_charge - Q_discharge/0.91 - Q_standing_loss)',
'Q_pool <= min(150 kW, Q_pool_requested, Q_safe) ; Q_safe = max(0, C(27.75-T)/900 + Q_loss)',
'COP_scenario = clip(0.43 · (52+273.15)/(52-(T_DC-5)), 2.5, 6)',
]
def para(txt,style='p'):return Paragraph(escape(txt),ST[style])
def footer(canvas,doc,lang):
 canvas.saveState();canvas.setFont('Ar',7.5);canvas.setFillColor(colors.grey)
 canvas.drawString(40,24,TR[lang]['footer']);canvas.drawRightString(558,24,str(doc.page));canvas.restoreState()
for lang,x in TR.items():
 pdfpath=O/f'Dispecer_Bazen_v04_{lang}.pdf'
 story=[para(x['title'],'title'),para(x['sub']),para(x['arch'],'h'),para(x['desc'])]
 story+=[para(x['physics'],'h'),para(x['physdesc'])]
 story.extend(para(eq,'formula') for eq in FORMULAS[:4])
 story.append(PageBreak())
 story+=[para(x['control'],'h'),para(x['controltext'])]
 story.extend(para(eq,'formula') for eq in FORMULAS[4:])
 story.append(para(x['results'],'h'))
 rows=[[para(z,'tiny') for z in x['cols']]]
 for i,z in enumerate(d['scenarios']):
  rows.append([para(x['names'][i],'tiny')]+
   [para(f"{z[col]:.2f}",'tiny') for col in
    ('Bazen_delivered_MWh','DH_delivered_MWh','HP_compressor_MWh','DH_unmet_MWh')])
 tab=Table(rows,colWidths=[155,84,78,88,99],repeatRows=1)
 tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7f4')),
   ('GRID',(0,0),(-1,-1),0.26,colors.HexColor('#c6d1e0')),
   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
   ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(tab)
 story.append(PageBreak())
 story+=[para(x['qa'],'h'),para(x['qatext'].format(n=q['checks'])),
         para('Maximum modelled T = 27.58°C; 8 × 672 steps of 900 s.','formula'),
         para('Original v85 SHA256: '+q['old_v85_sha256'],'tiny'),
         para(x['fig'],'h')]
 fig=O/'priebeh_teploty_v04_SK.png'
 if fig.is_file():
  from PIL import Image as PIL
  image=PIL.open(fig);w,h=image.size
  story.append(Image(str(fig),width=490,height=490*h/w))
 story.append(Spacer(1,12))
 story.append(para('Method: MATLAB model, CSV exports, independent Python QA; operating inputs class D = assumed synthetic.','tiny'))
 story.append(para('EU 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj','tiny'))
 story.append(para('EN 15288-1+A1:2024, swimming pool safety; applicability and actual law must be independently checked.','tiny'))
 doc=SimpleDocTemplate(str(pdfpath),pagesize=A4,
   leftMargin=40,rightMargin=40,topMargin=39,bottomMargin=37,title=x['title'])
 doc.build(story,onFirstPage=lambda c,d:footer(c,d,lang),onLaterPages=lambda c,d:footer(c,d,lang))
 pdf=pymupdf.open(str(pdfpath));txt='\n'.join(page.get_text() for page in pdf)
 assert len(pdf)>=3 and '27.58' in txt and '10.39' in txt,(lang,len(pdf))
 for ix,page in enumerate(pdf):
  for b in page.get_text('blocks'):
   if b[2]>page.rect.width+1 or b[3]>page.rect.height+1:
    raise RuntimeError((lang,ix,'clipped'))
 print('PDF_V04_OK',lang,len(pdf),pdfpath.stat().st_size)
