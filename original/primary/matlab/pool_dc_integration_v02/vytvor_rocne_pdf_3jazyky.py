# -*- coding: utf-8 -*-
"""Tri jazykove technicke PDF pre vykonany rocny Simulink v02."""
from pathlib import Path
import json
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
import pymupdf
BASE=Path(__file__).resolve().parents[2]
OUT=BASE/'results'/'pool_dc_integration_v02'
j=json.loads((OUT/'rocne_vysledky_SK.json').read_text(encoding='utf-8'))
rows=j['scenare']
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold',r'C:\Windows\Fonts\arialbd.ttf'))
L={
'SK':dict(title='Rocna integracia DC - ohrev bazena 500 m³',sub='Simulink R2026a | 8760 h | vysledky syntetickych scenarov v02',
s1='1. Geometria, tepelna kapacita a vychodiskova energia',s1b='Ukazkovy vnutorny bazen 25 × 12,5 × 1,6 m: V=500 m³ a A=312,5 m². Vodna hmota je jediny dokonale premiesany uzol. Nejde o certifikovany standard sutazneho bazena.',
s2='2. Dynamicka bilancia vody a fyzikalne straty',s2b='Smer toku urcuje znamienko. Konvekcia a salanie mozu byt zaporne, ked okolie ohrieva vodu. Odparovanie zavisi od aktivity a krytu. Model nezahrna HVAC haly a skutocnu bazenovu hydrauliku.',
s3='3. Tok tepla cez vymennik, TC a rozdelovac',s3b='V priamej vetve zalezi prenos na rozdiele teplot. Pre nizkoteplotny zdroj je vybrane tepelne cerpadlo so scenarovou Carnotovou aproximaciou COP; ide o parametrizaciu, nie mapu konkretneho vyrobcu.',
s4='4. Regulacia, interlocky a krok integracie',s4b='Termostat spina pod 27,35 °C a vypina nad 27,65 °C. Nezavisla matematicka podmienka obmedzuje ohrievaci vykon tak, aby vypocitana hodnota po 1 h nepresiahla 27,75 °C. STOP zrusi odber tepla bazenom, sietou aj zasobnikom; zostava nezavisly odvod tepla IT.',
s5='5. Vykonane rocne scenare a bilancie',s5b='Model ma hodinovy krok a 8760 simulovanych intervalov. Scenar bez krytu predpoklada v noci rovnaku nekrytu hladinu. Vsetky cisla nizsie su vysledky vykonanej simulacie na umelo skonstruovanych vstupoch.',
s6='6. Obmedzenia, overenie a hranice interpretacie',s6b='Hodnoty zdrojovej teploty, dostupneho IT tepla, vykonu vymennika, COP a strat su predpoklady. Nie su meraniami skutocneho objektu. Kontrola maxima v jednouzlovom modeli neznamena certifikaciu bezpecnosti senzora alebo celeho bazena. Pre skutocny navrh treba nezavisle snimace, hydraulicke vypocty, studiu poruch, aktualne predpisy a udaje vyrobcu.',
table=['Scenar','T max [°C]','Bazen [MWh]','TC el. [MWh]','Zdroj DC [MWh]'],
names=['Zaklad','Teplejsi zdroj','STOP 168 h','Bez plachty'],
qa='Kontroly: bilancia DC, TC a energie akumulovanej vo vode; signal STOP; maximum teploty. Vsetky presli. Vykazovany ERF plati iba pre zvolene hranice objektu a domnienku odovzdania do externej siete/bazena.'),
'EN':dict(title='Annual data-centre heat reuse for a 500 m³ pool',sub='Simulink R2026a | 8760 hours | synthetic scenario results v02',
s1='1. Geometry, thermal capacity and initial heat requirement',s1b='Illustrative indoor pool 25 × 12.5 × 1.6 m: V=500 m³ and water surface A=312.5 m². The water is represented by one perfectly mixed thermal state. These dimensions are not proof of competition-pool compliance.',
s2='2. Dynamic energy balance and heat exchange',s2b='Algebraic signs matter: convection and radiation can heat the water when the surroundings are warmer. Evaporation depends on activity and cover assumptions. Hall HVAC and physical water circulation are not included.',
s3='3. Direct heat exchanger, heat pump and dispatch',s3b='The direct exchanger depends on temperature approach. A heat pump is used when the source is too cool, with a capped Carnot-based COP scenario model rather than certified manufacturer performance data.',
s4='4. Temperature controller, stop signal and time step',s4b='The thermostat switches on below 27.35 °C and off above 27.65 °C. An independent model-level heat ceiling prevents the one-hour predicted water temperature exceeding 27.75 °C. STOP routes all available heat to independent rejection instead of the pool, district network or storage.',
s5='5. Executed 8760-hour scenarios',s5b='Four hourly synthetic profiles were run to completion in Simulink. The uncovered scenario removes the nightly pool cover. Numerical figures below are model outputs, not measurements or installation performance promises.',
s6='6. Uncertainty, verification and design limitations',s6b='Source temperature, heat recovery fraction, heat exchanger UA, COP and pool loss parameters are hypothetical. This single-node limiter does not certify sensor fault tolerance or legal compliance. Field design requires measured temperatures and flows, proper hydraulic sizing, equipment COP maps, risk analysis and the applicable consolidated rules.',
table=['Case','T max [°C]','Pool [MWh]','HP el. [MWh]','DC input [MWh]'],
names=['Base','Warmer source','168 h STOP','No cover'],
qa='Verified: data-centre heat allocation, heat pump/heat exchanger energy closure, water storage balance, STOP isolation and maximum modeled water temperature. Reported ERF is only a scenario boundary estimate, not an externally certified KPI.'),
'RU':dict(title='Годовая интеграция тепла ЦОД и бассейна 500 м³',sub='Simulink R2026a | 8760 часов | синтетические сценарии v02',
s1='1. Геометрия, теплоёмкость и энергия первого нагрева',s1b='Расчётный закрытый бассейн 25 × 12,5 × 1,6 м: V=500 м³, поверхность A=312,5 м². Вода представлена одной идеально перемешанной тепловой ёмкостью. Геометрия не является подтверждённым соревновательным стандартом.',
s2='2. Динамический баланс воды и тепловые потоки',s2b='В модели сохранены знаки потоков: конвекция и излучение могут нагревать воду от более тёплого помещения. Испарение зависит от активности и покрытия. Отопление зала, осушение и реальная гидравлика не моделируются.',
s3='3. Теплообменник, тепловой насос и распределение',s3b='Прямой теплообмен ограничен температурным напором. Для низкопотенциального источника используется тепловой насос с ограниченной оценкой COP через цикл Карно. Это сценарная формула, не испытанная карта COP производителя.',
s4='4. Термостат, защита и шаг симуляции',s4b='Термостат включает нагрев ниже 27,35°C и выключает выше 27,65°C. Дополнительное ограничение мощности не допускает прогнозируемую температуру выше 27,75°C за час. STOP отключает все каналы утилизации, а независимый отвод тепла ИТ остаётся.',
s5='5. Выполненные годовые сценарии',s5b='Просчитаны четыре сценария с часовым шагом по 8760 интервалов. Вариант без покрытия предусматривает открытую воду и ночью. Результаты получены на искусственных профилях, а не по показаниям реального дата-центра.',
s6='6. Ограничения, проверка и границы применимости',s6b='Температура источника, доля извлечения тепла, UA теплообменника, COP и теплопотери заданы предположениями. Ограничитель одноузловой модели не заменяет независимые датчики, проектирование гидравлики, защиту от отказов и проверку действующей редакции законодательства.',
table=['Сценарий','T макс [°C]','Бассейн [МВт·ч]','Эл. ТН [МВт·ч]','Из ЦОД [МВт·ч]'],
names=['Базовый','Тёплый источник','STOP 168 ч','Без покрытия'],
qa='Проверены: баланс тепла ЦОД, первый закон для теплового насоса, накопленная энергия воды, STOP и максимальная модельная температура. ERF является предварительной сценарной оценкой с явно заданной границей, а не сертифицированным KPI.')
}
L['SK'].update(
    title='Ročná integrácia tepla dátového centra a bazéna 500 m³',
    sub='Simulink R2026a | 8760 hodín | výsledky syntetických scenárov v02',
    s1='1. Geometria, tepelná kapacita a energia prvého ohrevu',
    s1b='Ilustračný vnútorný bazén má rozmery 25 × 12,5 × 1,6 m: V=500 m³ a A=312,5 m². Voda tvorí jediný dokonale premiešaný tepelný uzol. Geometria sama osebe nepreukazuje splnenie požiadaviek na súťažný bazén.',
    s2='2. Dynamická bilancia vody a prestupy tepla',
    s2b='Algebraické znamienka tepelných tokov sú dôležité: konvekcia a sálanie môžu ohrievať vodu, ak je okolie teplejšie. Vyparovanie závisí od aktivity a predpokladov o plachte. Vzduchotechnika haly a skutočná hydraulika nie sú zahrnuté.',
    s3='3. Priamy výmenník, tepelné čerpadlo a dispečing',
    s3b='Výkon priameho výmenníka závisí od teplotného spádu. Tepelné čerpadlo sa použije pri nízkopotenciálnom zdroji. Jeho COP vychádza z obmedzenej scenárovej aproximácie Carnotovho cyklu, nie z certifikovanej mapy výrobcu.',
    s4='4. Termostat, bezpečnostné vstupy a časový krok',
    s4b='Termostat zopne pod 27,35 °C a vypne nad 27,65 °C. Samostatné modelové obmedzenie výkonu zaručuje, že vypočítaná teplota po jednom kroku neprekročí 27,75 °C. Signál STOP presmeruje všetko dostupné teplo do nezávislého odvodu, nie do bazéna, siete ani zásobníka.',
    s5='5. Vykonané ročné scenáre a výsledky',
    s5b='Simulované boli štyri syntetické scenáre, každý s 8760 hodinovými intervalmi. Scenár bez plachty odstraňuje kryt aj mimo prevádzky. Čísla v tabuľke pochádzajú z vykonanej simulácie, nie z meraní.',
    s6='6. Neistota, overenie a obmedzenia návrhu',
    s6b='Teplota zdroja, podiel zachytiteľného tepla, UA výmenníka, COP a parametre strát sú hypotetické. Jednouzlový model s obmedzením teploty necertifikuje odolnosť snímačov proti poruchám ani právnu zhodu. Reálny návrh vyžaduje merania, výpočet hydrauliky, katalógové mapy strojov, analýzu rizík a aktuálne konsolidované predpisy.',
    table=['Scenár','T max [°C]','Bazén [MWh]','TČ el. [MWh]','Z DC [MWh]'],
    names=['Základ','Teplejší zdroj','STOP 168 h','Bez plachty'],
    qa='Overené: bilancia rozdelenia tepla DC, prvý termodynamický zákon TČ/výmenníka, bilancia akumulovanej energie vody, odpojenie cez STOP a najvyššia vypočítaná teplota. ERF je iba scenárový odhad pre stanovenú energetickú hranicu, nie certifikovaný ukazovateľ.'
)
sty={
'title':ParagraphStyle('T',fontName='ArialBold',fontSize=19,leading=24,spaceAfter=12),
'sub':ParagraphStyle('Sub',fontName='Arial',fontSize=10,leading=14,spaceAfter=15,textColor=colors.HexColor('#44546a')),
'h':ParagraphStyle('H',fontName='ArialBold',fontSize=12,leading=16,spaceBefore=13,spaceAfter=7),
'p':ParagraphStyle('P',fontName='Arial',fontSize=9.2,leading=14,spaceAfter=8),
'formula':ParagraphStyle('Formula',fontName='Arial',fontSize=9.3,leading=14,spaceAfter=6,leftIndent=12),
'foot':ParagraphStyle('Foot',fontName='Arial',fontSize=8,leading=11),
}
FORMULAS={
'thermal':[
'V=L W d = 25 · 12.5 · 1.6 = 500 m³;    A=L W = 312.5 m²',
'm = ρV = 997 · 500 = 498 500 kg',
'C = ρ V cp = 997 · 500 · 4182 = 2 084 727 000 J/K',
'E(16→28 °C) = C · 12 / (3.6 · 10^9) = 6.94909 MWh  (bez strát / excluding losses)',
],
'loss':[
'C · ΔT/Δt = Qpool - Qloss     [W];  Δt = 3600 s',
'Qloss = Qevap + Qconv + Qrad + Qconstruction + Qmakeup + 2000 W',
'm_evap = 4 · 10^-5 A · max(0, psat(Tw) - RH · psat(Tair)) · activity · (1 - 0.90 cover)',
'psat(T) = 0.61094 exp(17.625 T / (T + 243.04))    [kPa]',
'Qevap = m_evap · 2.44 · 10^6 J/kg;    Qconv = 3 A (Tw - Tair) (1 - 0.75 cover)',
'Qrad = 0.95 σ A [ (Tw+273.15)^4 - (Tair-2+273.15)^4 ] (1-0.75 cover)',
'Qconstruction = 800 (Tw - 20); Qmakeup = m_evap · 4182 · (Tw - 15)',
],
'dispatch':[
'Q_HX = min(Qdemand, Qdc, 150 kW, max(0, 8500 (Tsource - Tw - 3)))',
'COP = clamp(0.43 · Tcond,K / max(5, Tcond,K - Tevap,K), 2.5, 6)',
'Tcond = max(34, Tw+8) °C;    Tevap = Tsource - 5 °C',
'Q_HP ≤ min(Qdemand, 150 kW, Qdc / (1 - 1/COP), 35 kW · COP)',
'P_HP = Q_HP/COP;    Qsource = Q_HP - P_HP',
'Qdc = Qsource + Qdistrict + Qstorage + Qrejected   [W]',
'ERF = E_REUSE / E_DC  (boundary-specific); PUE = E_DC/E_IT',
]
}
def P(text, style='p'):return Paragraph(escape(text),sty[style])
def section(story, heading, text, formulas):
    story.append(P(heading,'h'));story.append(P(text))
    for f in formulas:story.append(P(f,'formula'))
def footer(canv,doc):
    canv.saveState();canv.setFont('Arial',8);canv.setFillColor(colors.HexColor('#59657a'))
    canv.drawString(42,24,'DCHR | 2026-10-23 | SCENARIO / NOT MEASURED')
    canv.drawRightString(555,24,f'{doc.page}')
    canv.restoreState()
for lang,x in L.items():
    target=OUT/f'Rocna_integracia_bazen_500m3_{lang}.pdf'
    doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=42,leftMargin=42,
        topMargin=40,bottomMargin=38,title=x['title'],author='DataCenter Heat Reuse')
    story=[P(x['title'],'title'),P(x['sub'],'sub')]
    section(story,x['s1'],x['s1b'],FORMULAS['thermal'])
    section(story,x['s2'],x['s2b'],FORMULAS['loss'])
    story.append(PageBreak())
    section(story,x['s3'],x['s3b'],FORMULAS['dispatch'])
    section(story,x['s4'],x['s4b'],[
        'T_on = 27.35 °C; T_off = 27.65 °C; T_hard_model = 27.75 °C',
        'Qsafe = max(0, (27.75 - Tw) C / Δt + Qloss)',
        'Qpool ≤ min(150 kW, Qsafe);  Tnew = Tw + Δt (Qpool - Qloss) / C',
        'STOP=1  => Qpool=Qdistrict=Qstorage=0; Qrejected=Qdc',
    ])
    story.append(PageBreak())
    story.append(P(x['s5'],'h'));story.append(P(x['s5b']))
    tab=[[P(c,'foot') for c in x['table']]]
    for i,s in enumerate(rows):
        tab.append([P(x['names'][i],'foot')]+[P(v,'foot') for v in [
            f"{s['Teplota_max_C']:.3f}",f"{s['Dodane_bazen_MWh']:.2f}",
            f"{s['Elektrina_TC_MWh']:.2f}",f"{s['Teplo_z_DC_do_bazena_MWh']:.2f}"]])
    table=Table(tab,colWidths=[128,79,93,95,108],repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dae5f1')),
        ('GRID',(0,0),(-1,-1),.25,colors.HexColor('#bec9d7')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    story.extend([table,Spacer(1,10)])
    fig=OUT/'rocna_teplota_SK.png'
    if fig.exists():
        from PIL import Image as PILImage
        im=PILImage.open(fig); w,h=im.size
        story.append(Image(str(fig),width=493,height=493*h/w))
    story.append(PageBreak())
    story.extend([P(x['s6'],'h'),P(x['s6b']),P(x['qa'])])
    base=rows[0]
    for f in [
        f"E_DC,source available = {base['Dostupne_teplo_DC_MWh']:.2f} MWh; E_IT = {base['E_IT_MWh']:.2f} MWh",
        f"E_pool = {base['Dodane_bazen_MWh']:.2f} MWh = E_DC_to_pool {base['Teplo_z_DC_do_bazena_MWh']:.2f} + E_HP_el {base['Elektrina_TC_MWh']:.2f}",
        f"E_DC_to_district = {base['Do_siete_MWh']:.2f} MWh; E_storage = {base['Do_akumulacie_MWh']:.2f} MWh; E_reject = {base['Nevyuzite_teplo_MWh']:.2f} MWh",
        f"ERF hypothetical / PUE=1.20: {base['ERF_scenar_PUE120']:.3f}; PUE=1.52: {base['ERF_scenar_PUE152']:.3f}",
        f"Max energy residual (pool) = {max(s['Nevyrovnanost_bazen_MWh'] for s in rows):.3g} MWh; max water T = {max(s['Teplota_max_C'] for s in rows):.3f} °C",
        "INPUT PROVENANCE: A = measured, B = published dataset, C = vendor, D = assumed. All operating inputs in these simulations: D.",
    ]:story.append(P(f,'formula'))
    story.append(P('Primary technical and regulatory references','h'))
    for name,url in [
      ('ASHRAE pool evaporation / natatorium','https://handbook.ashrae.org/handbooks/F17/SI/F17_Ch36/f17_ch36_si.aspx'),
      ('EU Regulation 2024/1364, PUE and ERF','https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj'),
      ('Slov-Lex 308/2012, 2012 reference version','https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2012/308/20121015.html')
    ]:story.append(P(name+'  '+url,'foot'))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    pdf=pymupdf.open(str(target))
    assert len(pdf)>=3,(target,len(pdf))
    texts=''.join(pg.get_text() for pg in pdf)
    assert '254.39' in texts and '27.750' in texts,(target,'missing values')
    issues=[]
    for pi,pg in enumerate(pdf):
        for b in pg.get_text('blocks'):
            if len(b)>=5 and (b[2]>pg.rect.width+1 or b[3]>pg.rect.height+1):
                issues.append((pi,b[:4]))
    assert not issues,issues
    print('PDF_OK',target.name,len(pdf),target.stat().st_size)
