from pathlib import Path
import json
from html import escape
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
O=Path(__file__).resolve().parents[2]/'results'/'pool_redundancy_v07'
R=json.loads((O/'vysledky_v07_SK.json').read_text(encoding='utf-8'))
Q=json.loads((O/'QA_NEZAVISLA_V07_SK.json').read_text(encoding='utf-8'))
assert len(R['cases'])==8 and Q['status']=='PASS'
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialB',r'C:\Windows\Fonts\arialbd.ttf'))
ST={'ti':ParagraphStyle('ti',fontName='ArialB',fontSize=17,leading=22,spaceAfter=12),
'h':ParagraphStyle('h',fontName='ArialB',fontSize=11.5,leading=16,spaceBefore=9,spaceAfter=6),
'p':ParagraphStyle('p',fontName='Arial',fontSize=9.2,leading=13.6,spaceAfter=6),
'm':ParagraphStyle('m',fontName='Arial',fontSize=8.8,leading=13,leftIndent=10,spaceAfter=4),
's':ParagraphStyle('s',fontName='Arial',fontSize=7.4,leading=11)}
L={
'SK':{
't':'V07: dva ventily, rezervné chladenie DC a IT odľahčenie',
's':'MATLAB/Simulink R2026a | 8 scenárov, 168 h | iba syntetické vstupy',
'h1':'1. Hranice a architektúra',
'd':'Nový kontrolér dedí päť stavov Stateflow z nezmenených verzií v04-v06. Má dve sériové uzatváracie vetvy HX, hlavný a rezervný chladič REJECT a scenárovú núdzovú redukciu tepelného vstupu DC. Originálna v85 nebola zmenená ani priamo integrovaná. Žiadne fyzické meranie, COP výrobcu ani schválenie bezpečnosti sa netvrdí.',
'h2':'2. Matematické uzavretie energie',
'x':'Vždy sa zachová tepelná bilancia zdroja a vody. Pri poškodení obidvoch ventilov sa fyzický únik odoberá z existujúceho toku REJECT. Pri výpadku chladičov sa nezvládnutý tok nestratí z účtovania.',
'h3':'3. Zálohovanie, snímače a riziko IT',
'y':'Dva virtuálne snímače majú oneskorenia 15/30 min. Spoločnú chybu -0,4 K ich rozdiel nedetekoval. Záložný REJECT má scenárovú kapacitu 150 kW pri hlavnom 180 kW. Pri obojstrannom výpadku a T_IT_model >= 38°C automatika modelovo zníži disponibilné odpadové teplo o 70%. T_IT_model NIE JE meraná teplota serverov.',
'h4':'4. Výsledky 8 vykonaných skúšok',
'cols':['Režim','Únik MWh','Neodv. MWh','Backup MWh','IT max °C'],
'names':['Zdravý','Primárny ventil zlyhá','Oba ventily zlyhajú','Hlavný REJECT off','Oba off, bez odľ.','Oba off, s odľ.','Spoločný bias','Kombinovaná porucha'],
'h5':'5. Nezávislé overenie a nedostatky',
'z':'Pôvodné CSV prešlo {n} nezávislými kontrolami: prvý zákon vody a TČ, štyri odvodné vetvy, ventilové úniky, meracie oneskorenia, ochranná západka a bilančný účinok odľahčenia. Reálna spoľahlivosť hardvéru, hydraulika, schéma elektro napájania, reakčná doba IT a aktuálna legislatíva ostávajú neoverené.',
'h6':'6. Grafy vypočítaných priebehov'
},
'EN':{
't':'V07: dual isolation valves, redundant DC cooling and IT derating',
's':'Executed MATLAB/Simulink R2026a | 8 cases × 168 h | synthetic input data',
'h1':'1. Scope and system topology',
'd':'This is an independent new model preserving the five-state Stateflow dispatcher originating in v04. Two series isolation valves and two independent reject-cooling channels are represented, plus assumed emergency IT thermal-load reduction. The original v85 is unchanged and is NOT the active closed-loop controller. No physical measurements or certified safety are claimed.',
'h2':'2. Thermodynamic conservation',
'x':'The original DC source heat balance closes at every step. Leakage through BOTH damaged isolation valves is subtracted from commanded reject heat rather than invented. Heat not removed by the coolers is explicitly included in the source balance.',
'h3':'3. Cooling failover and measurement limits',
'y':'Two virtual temperature sensors use 15/30-minute delays; a shared -0.4 K bias remained undetected. Main and backup coolers have hypothesized 180 and 150 kW ratings. During their joint failure, automatic derating removes 70% of available modeled DC waste heat when the synthetic IT buffer exceeds 38°C. This buffer temperature is NOT actual server temperature.',
'h4':'4. Eight actually executed test results',
'cols':['Scenario','Leak MWh','Unrej. MWh','Backup MWh','IT max °C'],
'names':['Healthy','Primary valve stuck','Both valves stuck','Main REJECT down','Both down, no shedding','Both down, shedding','Common sensor bias','Combined failure'],
'h5':'5. Independent QA and outstanding work',
'z':'{n} assertions passed independently over saved CSV: conservation of water, HP and DC heat, two valves, two cooling channels, sensor delay, latch state and derating accounting. Real hardware separation, hydraulic data, common-power faults, IT reaction latency, manufacturer COP and the applicable regulatory edition remain unverified.',
'h6':'6. Plots of executed simulations'
},
'RU':{
't':'V07: двойная изоляция, резерв охлаждения и разгрузка ИТ',
's':'Реальные расчёты MATLAB/Simulink R2026a | 8 сценариев по 168 ч | синтетика',
'h1':'1. Архитектура и границы расчёта',
'd':'Новая отдельная модель сохраняет пять состояний диспетчера Stateflow, созданного в v04. Введены два последовательных запорных клапана, основной и резервный контуры REJECT, а также модель аварийного снижения тепловыделения ИТ. Оригинальная v85 не изменена и НЕ является исполняемым контроллером v07. Реальных измерений и сертификации безопасности пока нет.',
'h2':'2. Математика сохранения энергии',
'x':'В каждом интервале проверяется баланс тепла воды и ЦОД. Утечка через два неисправных клапана вычитается из исходного отвода REJECT. Тепло, которое оба охладителя не смогли отвести, учитывается отдельно, а не исчезает из энергетического баланса.',
'h3':'3. Резервирование, измерения и тепловой риск',
'y':'Два виртуальных датчика имеют задержки 15/30 минут. Общий сдвиг -0,4 К не был обнаружен. Основной и резервный охладители условно имеют мощности 180 и 150 кВт. При одновременном отказе и нагреве модельного ИТ-буфера до 38°C система уменьшает доступное тепло ЦОД на 70%. Температура буфера НЕ является реальной температурой процессоров или серверов.',
'h4':'4. Результаты восьми выполненных сценариев',
'cols':['Сценарий','Утечка МВт·ч','Неотв. МВт·ч','Резерв МВт·ч','ИТ макс °C'],
'names':['Без аварии','Первый клапан заклинил','Оба клапана','Основной REJECT off','Оба off, без разгрузки','Оба off, разгрузка','Общая ошибка датчиков','Комбинированный отказ'],
'h5':'5. Независимая проверка и ограничения',
'z':'Проверено {n} условий по оригинальным CSV: первый закон для воды, насоса и ЦОД, обе линии охлаждения, клапаны, задержки датчиков, защёлка блокировки и баланс аварийного снижения нагрузки. Пока отсутствуют фактические характеристики оборудования, реальная надёжность независимых систем, гидравлика, карта COP и подтверждение действующих норм.',
'h6':'6. Графики выполненных расчётов'
}}
FORM=[
'C_water = 997 × 500 × 4182 = 2 084 727 000 J/K',
'T_water(k+1) = T_water(k) + 900 (Q_pool_physical - Q_loss)/C_water',
'Q_leak = (valve1_stuck AND valve2_stuck AND heat_command=0) * Q_leak_limit',
'Q_leak_limit = min(25 kW, Q_reject_cmd, 4.5 kW/K * max(0,T_DC-T_pool-3 K))',
'Q_reject_A = min(Q_reject_remaining, 180 kW * availability_A)',
'Q_reject_B = min(Q_reject_remaining-Q_A, 150 kW * availability_B)',
'Q_DC = Q_HX_physical + Q_HP_source + Q_A + Q_B + Q_unhandled',
'Q_HP_out = Q_HP_source + P_compressor',
'Q_DC_effective = Q_DC_raw - Q_IT_avoided',
'Q_IT_avoided = 70% Q_DC_raw when both coolers fail and T_IT_model >= 38 C',
'T_IT_model(k+1) = max(30, T_IT + 900 (Q_unhandled-Q_passive)/8e6)'
]
def txt(s,sty='p'):return Paragraph(escape(s),ST[sty])
def foot(c,doc):
 c.saveState();c.setFont('Arial',7);c.setFillColor(colors.grey)
 c.drawString(40,24,'POOL/DC | V07 | SYNTHETIC ENGINEERING MODEL | 2026-10-23')
 c.drawRightString(557,24,str(doc.page));c.restoreState()
for lang,t in L.items():
 report=O/f'DC_Bazen_Dvojita_Ochrana_v07_{lang}.pdf'
 story=[txt(t['t'],'ti'),txt(t['s']),txt(t['h1'],'h'),txt(t['d']),
        txt(t['h2'],'h'),txt(t['x'])]
 story.extend(txt(eq,'m') for eq in FORM)
 story.extend([txt(t['h3'],'h'),txt(t['y']),PageBreak(),txt(t['h4'],'h')])
 cells=[[txt(x,'s') for x in t['cols']]]
 for i,r in enumerate(R['cases']):
  vals=[t['names'][i],f"{r['leak_MWh']:.3f}",f"{r['unhandled_MWh']:.3f}",
        f"{r['backup_rejected_MWh']:.3f}",f"{r['T_IT_model_max_C']:.2f}"]
  cells.append([txt(z,'s') for z in vals])
 table=Table(cells,colWidths=[177,84,91,87,65],repeatRows=1)
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf7')),
     ('GRID',(0,0),(-1,-1),.25,colors.HexColor('#c1cbd6')),
     ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
     ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 story.extend([table,Spacer(1,10),txt(t['h5'],'h'),txt(t['z'].format(n=Q['checks'])),
  txt('Comparison: unhandled heat 0.07966 MWh -> 0.04989 MWh (approximately 37% reduction).','m'),
  txt('Source class D = synthetic; main REJECT 180 kW, backup 150 kW are assumptions.','s'),
  txt('EU Delegated Regulation 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj','s'),
  PageBreak(),txt(t['h6'],'h')])
 from PIL import Image as PIL
 for name in ('ventily_a_redundancia_v07_SK.png','IT_riziko_v07_SK.png'):
  im=PIL.open(O/name);w,h=im.size
  story.append(Image(str(O/name),width=506,height=506*h/w))
  story.append(Spacer(1,7))
 doc=SimpleDocTemplate(str(report),pagesize=A4,leftMargin=39,rightMargin=39,
  topMargin=37,bottomMargin=39,title=t['t'])
 doc.build(story,onFirstPage=foot,onLaterPages=foot)
 pdf=pymupdf.open(str(report))
 body='\n'.join(pg.get_text() for pg in pdf)
 assert 3<=len(pdf)<=5,(lang,len(pdf))
 assert str(Q['checks']) in body.replace(' ','') and '0.490' in body,(lang,'numbers')
 assert sum(len(pg.get_images(full=True)) for pg in pdf)>=2,(lang,'images')
 for i,page in enumerate(pdf):
  for b in page.get_text('blocks'):
   if b[2]>page.rect.width+1 or b[3]>page.rect.height+1:raise AssertionError((lang,i,'overflow'))
 pdf[-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(O/f'QA_PREVIEW_V07_{lang}.png'))
 print('PDF_VERIFIED_V07',lang,len(pdf),report.stat().st_size)
