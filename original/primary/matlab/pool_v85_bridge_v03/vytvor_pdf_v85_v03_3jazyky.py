# -*- coding: utf-8 -*-
"""3 jazyky PDF: realny kratky Stateflow v85 -> Simulink bazen v03."""
from pathlib import Path
import json
from html import escape
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_v85_bridge_v03'
report=json.loads((OUT/'most_v85_bazen_v03_SK.json').read_text(encoding='utf-8'))
qa=json.loads((OUT/'QA_NEZAVISLA_V85_BRIDGE_SK.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('A',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('AB',r'C:\Windows\Fonts\arialbd.ttf'))
styles={
 'h1':ParagraphStyle('h1',fontName='AB',fontSize=18,leading=23,spaceAfter=15),
 'h2':ParagraphStyle('h2',fontName='AB',fontSize=11.5,leading=16,spaceBefore=11,spaceAfter=6),
 'text':ParagraphStyle('text',fontName='A',fontSize=9.4,leading=14,spaceAfter=8),
 'math':ParagraphStyle('math',fontName='A',fontSize=9,leading=14,leftIndent=10,spaceAfter=5),
 'small':ParagraphStyle('small',fontName='A',fontSize=8.2,leading=12,spaceAfter=6),
}
L={
'SK':{
 'title':'Overené prepojenie Stateflow v85 a bazéna 500 m³',
 'sub':'Skutočne vykonaný MATLAB/Simulink R2026a | nový model v03 | 1 hodina',
 'h1':'1. Architektúra, zdroj a metodická hranica',
 'a':'Pôvodný model v85 je spustený bez zmeny. Jeho certifikovaná priama tepelná služba HP sa presmeruje do bazéna a/alebo zostáva pôvodnému odberateľovi DH. Nejde o nové teplo odobraté zo zdroja DC. Plné ročné dáta v85 nie sú k dispozícii. V03 je jednosmerný prenos výstupnej stopy, nie spätnoväzbový dispečing.',
 'h2':'2. Energia, rekonštrukcia signálu a bilančná kontrola',
 'b':'Výkon z v85 vychádza z 80-prvkových segmentov platnej 1380-prvkovej stopy. Výkon priamej služby je z(25) v MW; z(7:8) určujú obálku trvania segmentu v h. Súčet energii je overený voči originálnemu certifikovanému reportu.',
 'h3':'3. Termostat a tepelná dynamika vody',
 'c':'Objem 500 m³, tepelná kapacita C = 2,084727 GJ/K. Zahrnuté sú modelové straty vyparovaním, konvekciou, sálaním, prestupom do podložia a doplnením vody. Scenárové parametre sa nesmú vydávať za merania konkrétneho bazéna.',
 'h4':'4. Spustené testy a skutočné výsledky',
 'cases':['Pôvodná dodávka v85','Bazén','Zvyšok DH'],
 'tblheader':['Režim','Bazén [MWh]','DH [MWh]'],
 'names':['Studená voda 16 °C','Teplá voda 27,70 °C','STOP bazéna'],
 'results':'Tieto tri režimy sú prevzaté z identickej potvrdenej stopy service_E3.0_a1.0_H2_dt0.25. Ďalšie prípady charge_E4.95_a1.0_H2_dt0.25 a binding_stop mali nulovú priamu dodávku, takže z nich bazén nedostal žiadnu energiu. Celkovo deväť Simulink scenárov.',
 'h5':'5. Nezávislá verifikácia a čo zostáva',
 'checks':'Prešlo 99 nezávislých kontrol: SHA-256 pôvodného v85, počet riadkov CSV, bilancie tepla pri každom kroku, prvý zákon pre bazén, STOP, teplotná hranica a nulová dodávka pri nabíjaní TES. Výsledky pôvodného v85 sú bitovo zhodné s uloženým MAT v86.',
 'limits':'V03 nezahŕňa obojsmerné riadenie v85, modelovaný prírastok odberu tepla z DC, výrobnú mapu COP bazénového TČ, reálnu hydrauliku či rok reálnych dát. Bez meračov a návrhu nie je možná certifikácia.',
},
'EN':{
 'title':'Verified Stateflow v85 integration with a 500 m³ pool',
 'sub':'Actually executed MATLAB/Simulink R2026a | new v03 model | 1 hour',
 'h1':'1. Architecture, provenance and boundary',
 'a':'The original v85 model is re-executed without modifications. Its certified direct heat pump service is redirected partly to the pool and the remainder continues to the existing district-heat customer. This is NOT additional waste heat recovery. No 8760-hour v85 record is available. V03 is a one-way output-trace link, not a closed-loop dispatcher.',
 'h2':'2. Heat allocation and trace reconstruction',
 'b':'The input signal is reconstructed from the valid 80-component macrosegments in the 1380-column v85 trace. Direct HP service is z(25), in MW. Segment duration uncertainty lies in z(7:8), in hours. Integrated service must fall inside the original independently reported certified energy hull.',
 'h3':'3. Pool thermostat and water energy balance',
 'c':'The 500 m³ pool has thermal capacity C = 2.084727 GJ/K. Model losses include evaporation, convection, radiation, construction and make-up water. Hypothetical parameters are not measurements of the actual site.',
 'h4':'4. Executed scenarios and measured simulation outputs',
 'cases':['v85 delivered service','Pool allocation','Remaining DH'],
 'tblheader':['Condition','Pool [MWh]','DH [MWh]'],
 'names':['Cold water 16 °C','Warm water 27.70 °C','Pool STOP'],
 'results':'These three cases use the bitwise-verified original service_E3.0_a1.0_H2_dt0.25 trace. The further charge_E4.95_a1.0_H2_dt0.25 and binding_stop traces contain no direct service suitable for pooling. Nine Simulink scenarios executed in all.',
 'h5':'5. Independent QA and remaining work',
 'checks':'99 independent checks passed: original v85 SHA-256, CSV length, allocation and water first-law balances, pool STOP, temperature bound and no redirection of TES charging. The newly run v85 outputs match the previous MAT evidence bit for bit.',
 'limits':'V03 is not closed-loop Stateflow control, extra heat recovery or a yearly data-centre simulation. Vendor COP maps, real hydraulic sizing, instrument validation and a 8760-hour measured time series are still absent.',
},
'RU':{
 'title':'Проверенная интеграция Stateflow v85 и бассейна 500 м³',
 'sub':'Реальный запуск MATLAB/Simulink R2026a | новая модель v03 | 1 час',
 'h1':'1. Архитектура, происхождение данных и границы',
 'a':'Исходная модель v85 запущена повторно без изменений. Уже произведённая тепловая энергия исходного теплового насоса делится между бассейном и первоначальным потребителем тепловой сети. Это НЕ дополнительная рекуперация. Проверенных годовых данных v85 нет. V03 является односторонней передачей реальной трассы, без обратного управления диспетчером.',
 'h2':'2. Перераспределение тепла и извлечение сигналов',
 'b':'Сигнал восстановлен из 80-элементных сегментов 1380-элементной трассы v85. Прямая тепловая поставка HP: z(25), МВт. Границы длительности сегмента: z(7:8), часы. Интегральная энергия проверена по первоначальному сертифицированному интервальному отчёту.',
 'h3':'3. Термостат и энергетический баланс воды',
 'c':'Теплоёмкость бассейна 500 м³ составляет C = 2,084727 ГДж/К. В модели есть потери на испарение, конвекцию, излучение, грунт и подпитку. Выбранные коэффициенты не являются измерениями реального объекта.',
 'h4':'4. Реально выполненные сценарии',
 'cases':['Поставка v85','В бассейн','Остаток потребителю'],
 'tblheader':['Сценарий','Бассейн [МВт·ч]','Сеть [МВт·ч]'],
 'names':['Холодная вода 16 °C','Тёплая вода 27,70 °C','STOP бассейна'],
 'results':'Три режима основаны на побитово сверенной исходной трассе service_E3.0_a1.0_H2_dt0.25. Другие сценарии charge_E4.95_a1.0_H2_dt0.25 и binding_stop не имели прямой тепловой поставки для перенаправления в бассейн. Всего выполнено девять Simulink-сценариев.',
 'h5':'5. Независимая проверка и ограничения',
 'checks':'Пройдены 99 независимых проверок: SHA-256 исходной v85, структура CSV, баланс перераспределения, первый закон для воды, STOP, ограничение температуры и запрет подменять заряд TES поставкой бассейну. Трассы повторного запуска v85 совпали с архивными MAT побитово.',
 'limits':'V03 не содержит обратной связи с диспетчером Stateflow, не моделирует дополнительное тепло от ЦОД и не представляет годовую симуляцию реальных данных. Остаются нужны каталог COP, гидравлика, независимые датчики и 8760 часов исходных показаний.',
}
}
COMMON={
 'eq1':'E_pool + E_DH_remaining = E_HP_service_v85',
 'eq2':'E_k [MWh] = sum_s z25(s) · (tau_low(s) + tau_high(s))/2',
 'eq3':'Q_k [W] = 10^6 · E_k [MWh] / dt_k [h]',
 'eq4':'C = rho · V · cp = 997 · 500 · 4182 = 2 084 727 000 J/K',
 'eq5':'E(16 -> 28 °C) = 12 · C / 3.6e9 = 6.94909 MWh (no losses)',
 'eq6':'T(k+1) = T(k) + dt [s] · (Q_pool - Q_loss) / C',
 'eq7':'Q_safe = max(0, C · (27.75 - T(k)) / 900 + Q_loss)',
 'eq8':'Q_pool <= min(Q_v85, 150 000 W, Q_safe)',
 'eq9':'Q_DH_remaining = Q_v85 - Q_pool',
}
def para(s,sty='text'):
 return Paragraph(escape(s),styles[sty])
def header(c,doc):
 c.saveState();c.setFont('A',8);c.setFillColor(colors.grey)
 c.drawString(42,24,'DC HEAT REUSE / v85->v03 | TESTED SYNTHETIC SCHEDULE | 2026-10-23')
 c.drawRightString(551,24,str(doc.page));c.restoreState()
src=[x for x in report['cases'] if x['pramen_v85']=='service_E3.0_a1.0_H2_dt0.25']
assert len(src)==3 and qa['status']=='VERIFIED'
src={x['scenar_bazen']:x for x in src}
for lang,x in L.items():
 path=OUT/f'Most_v85_bazen_v03_{lang}.pdf'
 story=[para(x['title'],'h1'),para(x['sub'],'small'),para(x['h1'],'h2'),para(x['a'])]
 story.extend([para(COMMON['eq1'],'math'),para(x['h2'],'h2'),para(x['b'])])
 story.extend([para(COMMON[t],'math') for t in ['eq2','eq3']])
 story.append(Spacer(1,7))
 story.append(para(x['h3'],'h2'));story.append(para(x['c']))
 story.extend([para(COMMON[t],'math') for t in ['eq4','eq5','eq6','eq7','eq8','eq9']])
 story.append(PageBreak())
 story.append(para(x['h4'],'h2'));story.append(para(x['results']))
 rows=[[para(v,'small') for v in x['tblheader']]]
 for label,key in zip(x['names'],('studena_voda','tepla_voda','stop_bazen')):
  t=src[key]
  rows.append([para(label,'small'),para(f"{t['bazen_presmerovane_MWh']:.6f}",'small'),para(f"{t['dh_zostava_MWh']:.6f}",'small')])
 tbl=Table(rows,colWidths=[205,138,138])
 tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfe8f4')),
 ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#b8c3d2')),
 ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
 ('LEFTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),
 ('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 story.append(tbl);story.append(Spacer(1,15))
 story.append(para('0.447565789 MWh = 0.150000000 MWh + 0.297565789 MWh','math'))
 story.append(para(x['h5'],'h2'));story.append(para(x['checks']))
 story.append(para(x['limits']))
 story.append(para('SHA256 v85: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7','small'))
 story.append(para('Sources: v85 trace, saved MAT v86, 9 CSV, independent QA report.','small'))
 story.append(para('EU 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj','small'))
 story.append(para('STN EN 15288-1+A1:2024: https://normy.normoff.gov.sk/norma/139372/nahlad/','small'))
 story.append(para('Slov-Lex 308/2012 published historical text: https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html','small'))
 story.append(PageBreak())
 chapter={'SK':'6. Grafy vykonanych scenarov','EN':'6. Charts of executed cases','RU':'6. Графики выполненных сценариев'}[lang]
 story.append(para(chapter,'h2'))
 story.append(para('Zdroj: Simulink v03, 4 intervaly po 15 minut; popisky grafov v slovencine.','small'))
 for g in ('priebeh_bazen_v85_SK.png','rozdelena_sluzba_v85_SK.png'):
  story.append(Image(str(OUT/g),width=486,height=269.7))
  story.append(Spacer(1,10))
 doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=42,rightMargin=42,
 topMargin=39,bottomMargin=40,title=x['title'])
 doc.build(story,onFirstPage=header,onLaterPages=header)
 pdf=pymupdf.open(str(path))
 content='\n'.join(p.get_text() for p in pdf)
 assert '0.297566' in content and '0.150000' in content
 assert len(pdf) in (2,3),len(pdf)
 for idx,p in enumerate(pdf):
  for b in p.get_text('blocks'):
   if b[2]>p.rect.width+1 or b[3]>p.rect.height+1:
    raise AssertionError((lang,idx,b))
 print('PDF_V03_OK',lang,len(pdf),path.stat().st_size)
