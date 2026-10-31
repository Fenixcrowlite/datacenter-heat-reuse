# -*- coding: utf-8 -*-
"""Pridavny model bazena pre DataCenter Heat Reuse: vypocet, citlivost, PDF."""
import math, csv, json, datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, PolyLine, Rect, String, Line
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_500m3_v01'
DOC=ROOT/'docs'/'pool_500m3'
OUT.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)
P={'V_m3':500,'rho':997.,'cp':4182.,'A_m2':312.5,'T0_C':16.,'Tset_C':28.,
'Tair_C':29.,'Twall_C':27.,'Tground_C':20.,'Tmakeup_C':15.,'RH':.6,
'UA_W_K':800.,'hconv_W_m2K':3.,'epsilon':.95,'hfg_J_kg':2440000.,
'Q_other_W':2000.,'cover_evap':.9,'cover_conv_rad':.75,'COP':4.,
'DC_rated_IT_MW':10.,'IT_utilization':.82,'recoverable_fraction':.85,
'PUE':1.2,'source_branch_W':500000.}
C=P['V_m3']*P['rho']*P['cp']; sig=5.670374419e-8
def ps(t):return .61094*math.exp(17.625*t/(t+243.04))
def loss(t,h,rh=.6,cover=True):
    covered=bool(cover and not (8 <= h%24 < 20))
    factor=1 if 8 <= h%24 <20 else .5
    me=max(0.,4e-5*P['A_m2']*(ps(t)-rh*ps(29))*factor*(1-.9*covered))
    e=me*P['hfg_J_kg']; conv=3*P['A_m2']*(t-29)*(1-.75*covered)
    rad=.95*sig*P['A_m2']*((t+273.15)**4-300.15**4)*(1-.75*covered)
    ground=800*(t-20); makeup=me*4182*(t-15); other=2000.
    return {'evap':e,'conv':conv,'rad':rad,'ground':ground,'makeup':makeup,
            'other':other,'total':e+conv+rad+ground+makeup+other,'covered':int(covered)}
def run(name,q=150000,mode='HP',cover=True,rh=.6,dt=300):
    n=int(7*86400/dt); temp=16.; active=True; target=None
    Eh=El=Es=Ee=0.; rows=[]
    for i in range(n):
        h=i*dt/3600
        if temp<=27.8:active=True
        if temp>=28.2:active=False
        losses=loss(temp,h,rh,cover)
        cap=500000/(1-1/4) if mode=='HP' else 500000
        qin=min(q,cap) if active else 0.
        source=qin*(1-1/4) if mode=='HP' else qin
        electric=qin/4 if mode=='HP' else 0.
        next_t=temp+(qin-losses['total'])*dt/C
        if target is None and temp<28<=next_t:
            target=(i+(28-temp)/(next_t-temp))*dt/3600
        Eh+=qin*dt/3.6e9; El+=losses['total']*dt/3.6e9
        Es+=source*dt/3.6e9;Ee+=electric*dt/3.6e9
        if i%max(1,int(3600/dt))==0 or i==n-1:
            rows.append([h,temp,qin,losses['total'],losses['evap'],
                losses['ground'],losses['conv'],losses['rad'],losses['makeup'],
                source,electric,losses['covered']])
        temp=next_t
    with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['cas_h','teplota_C','dodane_teplo_W','strata_W','vypar_W',
         'podlozie_W','konvekcia_W','salanie_W','doplnana_voda_W',
         'zdroj_DC_W','elektrina_TC_W','zakryte']);w.writerows(rows)
    return {'name':name,'target_h':target,'T_end_C':temp,'heat_MWh':Eh,'loss_MWh':El,
            'source_MWh':Es,'electric_MWh':Ee,'energy_residual_MWh':C*(temp-16)/3.6e9-Eh+El,
            'rows':rows}
configs=[('TC_75kW',75000,'HP',True,.6),('TC_150kW',150000,'HP',True,.6),
 ('TC_300kW',300000,'HP',True,.6),('VYMENNIK_150kW',150000,'DIRECT',True,.6),
 ('TC_150kW_bez_krytu',150000,'HP',False,.6),
 ('TC_150kW_RH40',150000,'HP',True,.4),
 ('TC_150kW_RH80',150000,'HP',True,.8)]
runs=[run(*c) for c in configs]
base=runs[1]; high_res=run('TC_150kW_dt60',150000,'HP',True,.6,60)
day=loss(28,12); night=loss(28,0)
energy_12=C*12/3.6e9
summary={'assumption':'SCENARIO, no measured system parameters','params':P,
 'C_J_K':C,'E_16_to_28_MWh':energy_12,
 'holding_open_kW':day['total']/1000,'holding_covered_kW':night['total']/1000,
 'holding_24h_average_kW':(day['total']+night['total'])/2000,
 'IT_waste_heat_potential_MW':10*.82*.85,
 'cases':[{k:v for k,v in r.items() if k!='rows'} for r in runs],
 'test':{'balance_residual_MWh':base['energy_residual_MWh'],
 'hp_balance_MWh':base['heat_MWh']-base['source_MWh']-base['electric_MWh'],
 'dt60_dt300_final_delta_C':abs(high_res['T_end_C']-base['T_end_C']),
 'first_28C_delta_minutes':abs(high_res['target_h']-base['target_h'])*60}}
(OUT/'vysledky_bazen_500m3.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
fontdir=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Arial',str(fontdir/'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBold',str(fontdir/'arialbd.ttf')))
L={
'SK':('Využitie odpadového tepla dátového centra na ohrev bazéna',
'Technický výpočet a numerická simulácia, 500 m³',
'Výsledky sú referenčné scenáre, nie návrh overený meraním.',
'Predpokladaná geometria 25 × 12,5 × 1,6 m, vodná plocha 312,5 m². Model obsahuje výpar, konvekciu, sálanie, prenos do konštrukcie, doplnenie odparenej vody a prídavnú tepelnú stratu. Vykurovanie, ventilácia a odvlhčovanie celej plavárne sú mimo tejto bilancie.',
'Bilančné rovnice a dosadenie','Výsledky simulácií','Priebeh teploty vody',
'Zložky strát pri teplote vody 28 °C','Overenie a obmedzenia',
'Termostat zapína pri 27,8 °C a vypína pri 28,2 °C. Denná prevádzka 08:00–20:00, noc s krycou plachtou. Pokles výparu o 90 % pri zakrytí, účinnosť prestupu do podložia, COP = 4 a vlhkosť sú predpoklady.',
'IT kapacita 10 MW, využitie 82 %, zachytenie tepla 85 %: približný potenciál 6,97 MW. Nie je to tepelný výkon bazéna. Zdrojová vetva do bazéna je obmedzená na 500 kW. Priamy výmenník predpokladá teplotu zdroja 35 °C a približenie 3 K. Tepelné čerpadlo predstavuje nižšiu teplotu zdroja, 25 °C.',
'Výstupy sú scenárové, bez reálneho prietoku a teplôt chladiaceho média, katalógovej mapy COP, údajov o bazénovej hale, tepelnom výmenníku a hydraulike. IT musí mať nezávislé záložné chladenie; okruhy serverov a bazéna musia byť oddelené.',
['Scenár','28 °C [h]','Teplo [MWh]','Elektrina [MWh]'],
['Výpar','Konvekcia','Sálanie','Konštrukcia','Doplnenie','Ostatné','Spolu']),
'EN':('Swimming pool heating using data-center waste heat',
'Engineering calculation and numerical simulations, 500 m³',
'Reference scenarios only: not a calibrated or commissioned system design.',
'Illustrative geometry is 25 × 12.5 × 1.6 m, water area 312.5 m². The model includes evaporation, convection, radiation, ground/structure losses, make-up water and auxiliary load. Building heating, ventilation and dehumidification energy are outside this balance.',
'Governing equations and substitution','Simulation results','Pool-water temperature',
'Heat-flow components at 28 °C water','Checks and limitations',
'Thermostat switches on at 27.8 °C and off at 28.2 °C. Open from 08:00–20:00; night cover thereafter. Cover evaporation reduction 90%, ground conductance, COP 4 and relative humidity are scenario assumptions.',
'Rated IT capacity 10 MW, utilization 82%, recoverable 85% of IT load implies 6.97 MW potential, not pool-delivered heat. The source branch to the pool is limited to 500 kW. Direct heat exchange assumes 35 °C coolant with 3 K approach; the heat-pump case represents a cooler 25 °C source.',
'The study lacks measured coolant temperatures/flows, equipment COP map, actual natatorium psychrometrics, heat-exchanger transfer limits, and hydraulics. Independent IT fail-safe cooling and separated pool-water circuits are essential.',
['Scenario','28 °C [h]','Heat [MWh]','HP electricity [MWh]'],
['Evaporation','Convection','Radiation','Structure','Make-up','Other','Total']),
'RU':('Обогрев бассейна отходящим теплом дата-центра',
'Инженерный расчёт и численная симуляция, 500 м³',
'Расчётные сценарии, а не откалиброванный проект реальной установки.',
'Пример геометрии 25 × 12,5 × 1,6 м, площадь воды 312,5 м². Учтены испарение, конвекция, излучение, потери через чашу, подпитка испарившейся воды и дополнительные потери. Отопление здания, вентиляция и осушение воздуха не входят в этот энергобаланс.',
'Основные уравнения и подстановка','Результаты симуляций','Температура воды',
'Составляющие теплопотерь при 28 °C','Проверки и ограничения',
'Термостат включается при 27,8 °C, выключается при 28,2 °C. Открыт 08:00–20:00, ночью покрыт. Снижение испарения на 90%, параметры конструкции, COP = 4 и влажность приняты как сценарные допущения.',
'IT-мощность 10 МВт, загрузка 82%, утилизация 85% от IT дают потенциал 6,97 МВт, но это не мощность на бассейне. Ветвь охлаждающей жидкости ограничена 500 кВт. Прямой теплообмен предполагает источник 35 °C и температурный напор 3 К; тепловой насос рассматривается при источнике 25 °C.',
'Нет реальных замеров температуры и расхода теплоносителя, карты COP, влажности помещения, характеристик теплообменника и гидравлики. Необходимы резервное охлаждение IT и разделение технологической и бассейновой воды.',
['Сценарий','28 °C [ч]','Тепло [МВт·ч]','Электр. [МВт·ч]'],
['Испарение','Конвекция','Излучение','Конструкция','Подпитка','Прочее','Всего'])}
def val(x):return '—' if x is None else ('%.2f'%x)
def plot():
    d=Drawing(480,218);x0=36;y0=19;w=430;h=168
    d.add(Rect(x0,y0,w,h,strokeColor=colors.grey,fillColor=colors.whitesmoke))
    for j in range(8):
        x=x0+w*j/7;d.add(Line(x,y0,x,y0+h,strokeColor=colors.lightgrey))
        d.add(String(x-3,5,str(j),fontSize=8,fontName='Arial'))
    for t in [16,20,24,28,30]:
        y=y0+h*(t-15)/16
        d.add(Line(x0,y,x0+w,y,strokeColor=colors.lightgrey))
        d.add(String(4,y-3,str(t),fontSize=8,fontName='Arial'))
    for j,col in [(0,'#1765a2'),(1,'#c44f8e'),(2,'#14916c')]:
        pts=[]
        for z in runs[j]['rows']:
            pts.extend([x0+w*z[0]/168,y0+h*(z[1]-15)/16])
        d.add(PolyLine(pts,strokeColor=colors.HexColor(col),strokeWidth=2))
        d.add(Line(40+141*j,207,60+141*j,207,strokeColor=colors.HexColor(col),strokeWidth=3))
        d.add(String(64+141*j,204,runs[j]['name'],fontSize=8,fontName='Arial'))
    return d
def make_pdf(code):
    t=L[code];styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='T',fontName='ArialBold',fontSize=17,leading=22,spaceAfter=13,textColor=colors.HexColor('#183d57')))
    styles.add(ParagraphStyle(name='H',fontName='ArialBold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=7,textColor=colors.HexColor('#18628c')))
    styles.add(ParagraphStyle(name='B',fontName='Arial',fontSize=9,leading=14,spaceAfter=8))
    styles.add(ParagraphStyle(name='S',fontName='Arial',fontSize=8,leading=12,spaceAfter=5))
    b=[]; p=lambda s: b.append(Paragraph(s,styles['B'])); h=lambda s:b.append(Paragraph(s,styles['H']))
    b.append(Paragraph(t[0],styles['T']));p(t[1]);p('<b>'+t[2]+'</b>')
    p(t[3]);h(t[4])
    for s in [
      'C = ρ V cp = 997 × 500 × 4182 = 2 084 727 000 J/K = 0,57909 MWh/K.',
      'E = C (28 − 16) = '+('%.4f'%energy_12)+' MWh.',
      'C·dT/dt = Qdod − Qvypar − Qkonv − Qrad − Qpod − Qdop − Qostatné.',
      'psat(T) = 0,61094 exp[17,625 T/(T+243,04)] kPa; pair = RH psat(Tair).',
      'mevap = 4e-5 A max(psat(T)-pair, 0) Fa (1-0,9·cover) kg/s.',
      'Qevap = mevap hfg; hfg = 2,44 MJ/kg.',
      'Qconv = h A (T-Tair) (1-0,75·cover), h = 3 W/(m² K).',
      'Qrad = ε σ A ((T+273,15)⁴-(Twall+273,15)⁴) (1-0,75·cover).',
      'Qground = UA (T-Tground); Qmakeup = mevap cp (T-Tmakeup).',
      'Qout,HP = Qsource,DC + Welectric; COP = Qout,HP / Welectric.'
    ]:b.append(Paragraph(s,styles['S']))
    p(t[9]);p(t[10]);b.append(PageBreak())
    h(t[5]); tab=[t[12]]
    for r in runs:tab.append([r['name'],val(r['target_h']),val(r['heat_MWh']),val(r['electric_MWh'])])
    tbl=Table(tab,colWidths=[173,93,105,105],repeatRows=1)
    tbl.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Arial'),('FONTSIZE',(0,0),(-1,-1),8),
      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9e8f2')),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.whitesmoke]),
      ('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    b.append(tbl);h(t[6]);b.append(plot());h(t[7])
    tab=[['', '08–20 [kW]', '20–08 [kW]']]
    for lab,key in zip(t[13],['evap','conv','rad','ground','makeup','other','total']):
        tab.append([lab,val(day[key]/1000),val(night[key]/1000)])
    tbl=Table(tab,colWidths=[236,120,120])
    tbl.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Arial'),('FONTSIZE',(0,0),(-1,-1),8),
      ('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9e8f2'))]))
    b.append(tbl);b.append(PageBreak());h(t[8])
    p(t[11]);p('Numerical integration: forward Euler, 300 s step, 7 days. 60-s independent step-size comparison.')
    p('Pool balance residual = %.3e MWh.'%summary['test']['balance_residual_MWh'])
    p('Heat pump first-law residual = %.3e MWh.'%summary['test']['hp_balance_MWh'])
    p('Time-grid difference, final pool temperature = %.5f °C.'%summary['test']['dt60_dt300_final_delta_C'])
    p('First 28 °C threshold crossing: 60-s versus 300-s step difference = %.2f minutes.'%summary['test']['first_28C_delta_minutes'])
    p('The final sample can differ with relay-cycle phase; the first threshold crossing is a more meaningful grid check.')
    p('Holding load: open %.2f kW, covered %.2f kW, average %.2f kW.'%
      (day['total']/1000,night['total']/1000,(day['total']+night['total'])/2000))
    h('References / Zdroje / Источники')
    for s in ['ASHRAE Handbook 2023, HVAC Applications, Ch. 6 Indoor Swimming Pools:',
      'https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx',
      'EnergyPlus Engineering Reference, Indoor Swimming Pool:',
      'https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v22.1.0/EngineeringReference.pdf',
      'Project data: docs/Assumptions_and_Parameters.md and scenario JSON/CSV in results/pool_500m3_v01.']:
        b.append(Paragraph(s,styles['S']))
    out=OUT/('Bazen_500m3_'+code+'.pdf')
    def foot(c,d):
        c.setFont('Arial',8);c.setFillColor(colors.grey)
        c.drawString(44,22,'DataCenter Heat Reuse | Pool 500 m³ | v01')
        c.drawRightString(A4[0]-44,22,str(d.page))
    SimpleDocTemplate(str(out),pagesize=A4,leftMargin=44,rightMargin=44,
      topMargin=40,bottomMargin=42,title=t[0]).build(b,onFirstPage=foot,onLaterPages=foot)
    return str(out)
pdfs=[make_pdf(c) for c in ['SK','EN','RU']]
md=['# Výpočty bazéna 500 m³: zdroj dátové centrum',
'> Referenčná fyzikálna simulácia, nie kalibrovaný návrh.','',
'## Energetická bilancia',
'$$\\rho Vc_p\\frac{dT}{dt}=\\dot Q_{dod}-\\dot Q_{vypar}-\\dot Q_{konv}-\\dot Q_{rad}-\\dot Q_{pod}-\\dot Q_{dop}-\\dot Q_{ostatne}$$',
'$$E=\\rho Vc_p(28-16)='+('%.4f'%energy_12)+'\\;\\mathrm{MWh}$$',
'','## Simulované varianty','| Prípad | Dosiahnutie 28 °C [h] | Dodané teplo [MWh] | Elektrina TČ [MWh] |',
'|---|---:|---:|---:|']
for r in runs:md.append('| '+r['name']+' | '+val(r['target_h'])+' | '+val(r['heat_MWh'])+' | '+val(r['electric_MWh'])+' |')
md+=['','## Podmienky','- T0 = 16 °C, regulácia [27,8; 28,2] °C.',
'- Objem 500 m³, plocha 312,5 m², Tair = 29 °C, RH = 60 %.',
'- 08:00 až 20:00 otvorené; v noci kryt (redukcia výparu 90 %).',
'- COP TČ = 4, tepelná dodávka 75, 150 alebo 300 kW. Zdroj DC vetva max. 500 kW.',
'- Bilancia zdroja TČ: Qout=Qsource+Welectric.',
'- Model nekryje vykurovanie, ventiláciu ani odvlhčovanie budovy.',
'','## Reprodukovateľné súbory','- Projektový model: matlab/pool_500m3/Bazen_DC_Ohrev_500m3_SK.slx',
'- MATLAB test: matlab/pool_500m3/spusti_simulaciu_bazena_sk.m',
'- Číselné údaje: results/pool_500m3_v01/vysledky_bazen_500m3.json',
'- PDF: Bazen_500m3_SK.pdf, Bazen_500m3_EN.pdf, Bazen_500m3_RU.pdf',
'','## Zdroj metodiky','https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx']
(DOC/'Vypocty_a_simulacie_bazen_500m3_SK.md').write_text('\n'.join(md),encoding='utf-8')
(OUT/'manifest.json').write_text(json.dumps({'pdfs':pdfs,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'validation':summary['test']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdfs':pdfs,'E_MWh':energy_12,'open_loss_kW':day['total']/1000,
 'covered_loss_kW':night['total']/1000,'baseline_h28':base['target_h'],'checks':summary['test']},ensure_ascii=False))
