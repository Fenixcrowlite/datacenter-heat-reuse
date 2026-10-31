from pathlib import Path
import json
from html import escape
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image
R=Path(__file__).resolve().parents[2];O=R/'results'/'pool_failure_v06'
J=json.loads((O/'vysledky_v06_SK.json').read_text(encoding='utf-8'))
QA=json.loads((O/'QA_NEZAVISLA_V06_SK.json').read_text(encoding='utf-8'))
assert QA['status']=='PASS' and len(J['scenarios'])==7
pdfmetrics.registerFont(TTFont('A',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('AB',r'C:\Windows\Fonts\arialbd.ttf'))
S={
'tit':ParagraphStyle('Ti',fontName='AB',fontSize=17,leading=23,spaceAfter=13),
'h':ParagraphStyle('H',fontName='AB',fontSize=11.8,leading=17,spaceBefore=12,spaceAfter=6),
'p':ParagraphStyle('P',fontName='A',fontSize=9.2,leading=14,spaceAfter=8),
'm':ParagraphStyle('Math',fontName='A',fontSize=8.8,leading=13,leftIndent=11,spaceAfter=5),
's':ParagraphStyle('Small',fontName='A',fontSize=7.8,leading=11)}
L={
'SK':{
'title':'V06: fyzické poruchy pri ohreve bazéna 500 m³',
'sub':'Skutočne spustený Simulink R2026a | 7 scenárov po 168 h | syntetické vstupy',
'a':'1. Modelový rozdiel medzi softvérom a fyzikou',
'desc':'Nový samostatný model vychádza z v05, ale dva simulované snímače majú 15/30-minútové oneskorenie. Pri zaklinenom ventile môže voda fyzicky dostávať teplo aj pri príkaze vypnúť ohrev. Nezávislý chladič REJECT môže zlyhať a teplo zostane nezvládnuté. Pôvodné v85, v04 a v05 sa neprepísali. Stále nejde o skutočné merania.',
'b':'2. Energetické rovnice a prvý zákon',
'method':'Únik tepla sa odoberá z existujúcej vetvy REJECT, nie z vymysleného zdroja. Náhradný buffer IT slúži len na zobrazenie tepelného rizika; jeho teplota nie je fyzická teplota serverov.',
'c':'3. Logika a bezpečnostné hranice',
'safety':'Senzory vidia iba oneskorenú modelovú teplotu plus umelú chybu. Nesúhlas nad 0,35 K alebo prehriatie nad 27,70 °C vyvolá západku. Reset len pri zdravých signáloch a teplote do 27,65 °C. Rovnaký bias oboch snímačov sa v skúške NEROZPOZNAL. Tento výsledok ukazuje hranicu softvérovej diagnostiky.',
'd':'4. Výsledky skutočne vykonaných prípadov',
'col':['Scenár','Únik MWh','Neodv. MWh','T_IT max °C','Latch'],
'names':['Zdravý','Chyba snímača','Spoločný bias','Zaklinený ventil','REJECT off','Bez prietoku','Kombinovaná porucha'],
'e':'5. Závery, dôkazy a nesplnené podmienky',
'limits':'84 801 nezávislých testov nad CSV prešlo, vrátane energie DC a bazéna, oneskorenia senzorov a rizikového buffera. Fyzická bezpečnosť však nie je dokázaná. Chýbajú reálne nezávislé snímače, redundancia ventilu, výkon reálneho REJECT, skutočné COP mapy, hydraulika a rok meraní.',
'fig':'6. Grafické výsledky Simulinku'
},
'EN':{
'title':'V06: physical failure simulation for a 500 m³ pool',
'sub':'Executed Simulink R2026a | 7 cases, 168 h each | synthetic inputs',
'a':'1. Software shutdown versus physical leakage',
'desc':'The new standalone model is derived from v05. Its two simulated temperature channels have separate 15/30-minute delays. A valve stuck open can physically deliver heat despite zero pool heating command. Insufficient independent data-centre heat rejection leaves unhandled cooling heat. Original v85, v04 and v05 are unchanged. No facility measurements were used.',
'b':'2. Energy equations and conservation',
'method':'Uncontrolled heat transfers out of existing commanded reject heat, so no energy is invented. The lumped IT heat buffer is merely a scenario risk indicator, NOT a measured server or coolant temperature.',
'c':'3. Safety-state logic and limitations',
'safety':'The simulated sensors have no access to the true current water temperature. A disagreement above 0.35 K or measured temperature above 27.70°C trips a latched shutdown. Manual reset requires cleared faults and readings at or below 27.65°C. Identical bias on both sensors was NOT detected, illustrating a common-mode risk.',
'd':'4. Actual completed scenario outputs',
'col':['Scenario','Leak MWh','Unrej. MWh','IT max °C','Latch'],
'names':['Healthy','One sensor bias','Common bias','Valve stuck','REJECT down','No pool flow','Combined failure'],
'e':'5. Independent verification and gaps',
'limits':'84,801 independent checks passed on exported Simulink CSV, including pool and DC energy balances, sensor delays and the latch. A passing model is not a physical safety certificate. Real sensor independence, redundant isolation valves, documented reject capacity, hydraulic design, measured COP maps and measured annual loads remain essential.',
'fig':'6. Actual simulated time series'
},
'RU':{
'title':'V06: моделирование физических отказов бассейна 500 м³',
'sub':'Выполнено в Simulink R2026a | 7 сценариев по 168 часов | синтетические входы',
'a':'1. Отличие программной защиты от физической',
'desc':'Новая отдельная модель основана на v05, но двум виртуальным датчикам заданы разные задержки 15 и 30 минут. Заклинивший клапан может передавать тепло даже при команде выключения. Отказ отвода тепла ЦОД приводит к накоплению неотведённой энергии. Исходные v85, v04 и v05 не изменены. Измеренных данных установки в модели пока нет.',
'b':'2. Уравнения энергии и сохранения тепла',
'method':'Неконтролируемая передача тепла вычитается из исходной линии REJECT, чтобы не создавать энергию. Температура упрощённого теплового буфера ИТ служит лишь индикатором риска, а не измерением температуры процессоров или теплоносителя.',
'c':'3. Защита, задержки и их ограничения',
'safety':'Виртуальные датчики не получают истинную текущую температуру воды. Расхождение более 0,35 К или показания от 27,70°C включают защитную защёлку. Сброс возможен только после устранения аварии и при показаниях до 27,65°C. Одинаковая ошибка обоих датчиков осталась НЕОБНАРУЖЕННОЙ.',
'd':'4. Результаты семи выполненных сценариев',
'col':['Сценарий','Утечка МВт·ч','Неотвод МВт·ч','Макс ИТ °C','Блок.'],
'names':['Без аварии','Ошибка датчика','Общая ошибка','Заклинил клапан','Отказ REJECT','Нет протока','Комплексная авария'],
'e':'5. Независимая проверка и недостающие этапы',
'limits':'По сохранённым CSV успешно выполнена 84 801 независимая проверка: баланс энергии ЦОД, бассейна и насоса, запаздывание датчиков и работа аварийной защёлки. Математическая корректность не означает физическую безопасность. Ещё нужны реальные датчики, резервные клапаны, паспортные характеристики охладителя, гидравлика, COP и измеренный годовой профиль.',
'fig':'6. Графики результатов моделирования'
}}
FORM=[
'C_pool = 997 * 500 * 4182 = 2 084 727 000 J/K',
'T_pool(k+1) = T_pool(k) + 900 (Q_pool_physical - Q_loss)/C_pool',
'T_sensor1(k) = T_true(k-1) + bias1; T_sensor2(k) = T_true(k-2) + bias2',
'Q_leak = min(25 kW, Q_reject_command, 4.5 kW/K * max(0, T_DC - T_pool - 3 K))',
'Q_pool_physical = Q_pool_command + Q_leak',
'Q_reject_physical = min(Q_reject_command - Q_leak, 180 kW * availability)',
'Q_unhandled = Q_reject_command - Q_leak - Q_reject_physical',
'Q_DC = Q_HX_physical + Q_HP_source + Q_reject_physical + Q_unhandled',
'C_IT = 8e6 J/K; T_IT(k+1) = max(30, T_IT(k) + 900*(Q_unhandled - Q_passive)/C_IT)',
'Q_passive = max(0, 2000 W/K * (T_IT - 30 C)); IT risk alarm at 42 C (scenario).'
]
def p(s,sty='p'):return Paragraph(escape(s),S[sty])
def footer(c,d,lang):
 c.saveState();c.setFont('A',7.5);c.setFillColor(colors.grey)
 c.drawString(39,22,'DATA CENTER / POOL v06 | SYNTHETIC | 2026-10-23')
 c.drawRightString(554,22,str(d.page));c.restoreState()
for lang,t in L.items():
 story=[p(t['title'],'tit'),p(t['sub']),p(t['a'],'h'),p(t['desc']),p(t['b'],'h'),p(t['method'])]
 story.extend(p(x,'m') for x in FORM)
 story+=[p(t['c'],'h'),p(t['safety']),PageBreak(),p(t['d'],'h')]
 head=[p(x,'s') for x in t['col']];tab=[head]
 for s,n in zip(J['scenarios'],t['names']):
  vals=[n,f"{s['leak_stuck_MWh']:.3f}",f"{s['unhandled_cooling_MWh']:.3f}",
        f"{s['T_IT_risk_max_C']:.2f}",str(s['fault_latched_samples'])]
  tab.append([p(v,'s') for v in vals])
 table=Table(tab,colWidths=[174,84,91,87,69],repeatRows=1)
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1e9f2')),
 ('GRID',(0,0),(-1,-1),.25,colors.HexColor('#bdc7d2')),
 ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
 ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.extend([table,Spacer(1,14),p(t['e'],'h'),p(t['limits']),
 p(f"QA: {QA['test_assertions']} PASS; 7 * 672 time steps (dt=900 s).",'m'),
 p('Provenance D: synthetic. Model buffer IT temperature is NOT an actual server temperature.','m'),
 p('EU 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj','s')])
 story.extend([PageBreak(),p(t['fig'],'h')])
 for im in ('povel_vs_prietok_v06_SK.png','teplota_IT_riziko_v06_SK.png'):
  from PIL import Image as PIL
  ip=O/im;w,h=PIL.open(ip).size
  story.append(Image(str(ip),width=505,height=505*h/w))
  story.append(Spacer(1,8))
 doc=SimpleDocTemplate(str(O/f'DC_Bazen_Fyzikalne_Poruchy_v06_{lang}.pdf'),
  pagesize=A4,leftMargin=38,rightMargin=38,topMargin=38,bottomMargin=38,title=t['title'])
 doc.build(story,onFirstPage=lambda c,d:footer(c,d,lang),
           onLaterPages=lambda c,d:footer(c,d,lang))
 pdf=pymupdf.open(str(O/f'DC_Bazen_Fyzikalne_Poruchy_v06_{lang}.pdf'))
 txt='\n'.join(page.get_text() for page in pdf)
 assert 3<=len(pdf)<=5,(lang,len(pdf))
 assert '84801' in txt.replace(' ','') and '0.490' in txt,(lang,'key data missing')
 assert sum(len(pg.get_images(full=True)) for pg in pdf)>=2,(lang,'charts not embedded')
 for idx,page in enumerate(pdf):
  for b in page.get_text('blocks'):
   if b[2]>page.rect.width+1 or b[3]>page.rect.height+1:raise AssertionError((lang,idx,'overflow'))
 pdf[-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(O/f'QA_PREVIEW_V06_{lang}.png'))
 print('PDF_V06_VERIFIED',lang,len(pdf), (O/f'DC_Bazen_Fyzikalne_Poruchy_v06_{lang}.pdf').stat().st_size)
