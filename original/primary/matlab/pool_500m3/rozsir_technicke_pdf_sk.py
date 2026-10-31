# -*- coding: utf-8 -*-
"""Rozsirene 3-jazykove technicke prilohy. Merge s existujucimi PDF, bez straty stran."""
import json, math
from pathlib import Path
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_500m3_v01'
data=json.loads((OUT/'vysledky_bazen_500m3.json').read_text(encoding='utf-8'))
sim=json.loads((OUT/'simulink_scenare_SK.json').read_text(encoding='utf-8'))
base=data['cases'][1]
pdfmetrics.registerFont(TTFont('Ar',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArB',r'C:\Windows\Fonts\arialbd.ttf'))
txt={
'SK':{
'a':'Rozšírený matematický dodatok: hranice, odvodenia a validácia',
'b':'1. Východiskové predpoklady a rozmerová kontrola',
'body1':'Vnútorný bazén je modelovaný ako jedna dokonale premiešaná tepelná kapacita. Geometria 25 × 12,5 × 1,6 m je predpoklad, nie normatívny rozmer všetkých bazénov. Uvažujeme teplotu vody od 16 do 28 °C. Teplota haly 29 °C, relatívna vlhkosť 60 %, stien 27 °C, zeminy 20 °C a doplňovanej vody 15 °C.',
'cap':'K tepelnému obsahu bazéna treba pripočítať dynamické straty počas ohrevu a energiu na udržanie. Rovnica E = C deltaT je iba dolná hranica pre ohrev bez tepelných tokov s okolím. Nezahrnuje ohrev samotnej haly.',
'c':'2. Odvodenie prevádzkových strát a citlivosť',
'ev':'Korelácia ASHRAE je empirická a vyžaduje parciálne tlaky v kPa. Faktor aktivity 1,0 zodpovedá aktívnemu verejnému bazénu, faktor 0,5 neobsadenému. Hypotetická plachta znižuje výpar 90 % a konvekciu a sálanie 75 %. Ide o domnienky, ktoré sa musia nahradiť údajmi výrobcu alebo meraním.',
'ground':'Algebraické znamienko jednotlivých prenosov sa nesmie zmazať funkciou max(0, ...). Pri vode 28 °C a vzduchu 29 °C je konvekcia záporná: prúdi teplo zo vzduchu do vody. Funkcia max sa používa iba na nekladnú hodnotu potenciálnej miery vyparovania.',
'd':'3. Tepelné čerpadlo, priama vetva a hranica dátového centra',
'dc':'IT výkon sa neprepočítava rovno na prívod bazéna: potenciál zachytiteľného tepla je 10 MW × 0,82 × 0,85 = 6,97 MW, pričom bazénová zdrojová vetva má samostatný limit 500 kW. PUE 1,20 je charakteristika budovy, do výpočtu IT zdroja sa znovu nenásobí, aby sa teplo infraštruktúry nepripočítalo dvakrát.',
'hp':'COP=4 je pevná scenárová hodnota, nie katalógová mapa závisiaca od teplôt a zaťaženia. Pri priamom výmenníku sa nenulujú všetky elektrické odbery, iba elektrina kompresora tepelného čerpadla; čerpadlá a regulácia stále spotrebúvajú elektrinu.',
'e':'4. Integrácia, výsledky modelu a akceptačné kontroly',
'integr':'Python používa dopredný Eulerov krok 300 s, kontrolný prepočet 60 s; model Simulink používa integrátor so solverom ode4 a pevným krokom 60 s. Hysterézia spôsobuje fázu cyklov a pri porovnávaní poslednej teploty môže vzniknúť rozdiel aj pri veľmi podobnom fyzikálnom priebehu. Prioritou je bilancia, prvé dosiahnutie 28 °C, dostupnosť zdroja a kontrola limitov.',
'limitations':'Nadväzujúca práca: dosadiť skutočný časový profil teploty a prietoku chladiacej kvapaliny, navrhnúť výmenník a tlakové straty, overiť ochranu bazénovej vody, výkon tepelného čerpadla COP(T) a ročný klimatický režim. Tento doplnok neprepája priamo v85 Stateflow dispatch a nemení žiadnu jeho fyzickú alebo bezpečnostnú garanciu.',
'labels':['Variant Simulink','Čas do 28 °C [h]','Rel. odchýlka']},
'EN':{
'a':'Extended mathematical annex: boundaries, derivations and validation',
'b':'1. Input assumptions and dimensional analysis',
'body1':'The indoor pool is treated as one perfectly mixed thermal mass. Its 25 × 12.5 × 1.6 m geometry is an assumed example, not a standard volume for every pool. Water heats from 16 to 28 °C. Room air is 29 °C at 60% relative humidity, walls 27 °C, ground 20 °C, and make-up water 15 °C.',
'cap':'Time-dependent heat flows into and out of the pool must be added to stored-water energy. E = C deltaT is only the heat-storage requirement, not the total duty including thermal losses. It also excludes heating the natatorium building.',
'c':'2. Derivation of operating losses and sensitivity',
'ev':'The simplified ASHRAE evaporation equation is empirical and expects partial pressures in kPa. Activity factor 1.0 is representative of an active public pool; 0.5 is used for an unoccupied pool. The assumed cover reduces evaporation by 90% and convection/radiation by 75%. Measured or manufacturer performance must replace these hypothetical values.',
'ground':'Keep signed heat exchange in the energy balance. With 28 °C pool water and 29 °C room air, convection is negative, so the warmer air heats the pool. The nonnegative clamp is appropriate only for the potential evaporation rate.',
'd':'3. Heat pump, direct heat exchange and the data-center boundary',
'dc':'The IT nameplate is not the pool heating capacity: 10 MW × 0.82 × 0.85 = 6.97 MW of potential recoverable IT heat, while the dedicated source-side branch is only 500 kW. The assumed PUE of 1.20 is not multiplied into IT waste heat again: doing so would risk double counting infrastructure heat.',
'hp':'COP=4 is an assumed constant, not a part-load or temperature-dependent equipment map. Direct heat exchange avoids compressor electricity, but does not make circulation pumps, valves and control consume zero power.',
'e':'4. Integration, executed results and acceptance checks',
'integr':'The Python model uses explicit Euler with a 300-s time step and a 60-s sensitivity run. Simulink uses a continuous integrator with the ode4 solver and fixed 60-s step. Hysteresis changes the phase of on/off cycles and can shift the end-point temperature. Validate energy balance, first target crossing, source capacity, and operating limits rather than relying on a single final sample.',
'limitations':'Next work requires measured coolant temperatures and flow, an exchanger pressure-drop/thermal design, pool-water separation, COP(T) performance map and annual operation. This extension is not yet wired into the existing v85 Stateflow dispatcher and does not modify its physical or safety contracts.',
'labels':['Simulink case','First 28 °C [h]','Relative residual']},
'RU':{
'a':'Расширенное математическое приложение: выводы и проверка',
'b':'1. Исходные допущения и размерности',
'body1':'Крытый бассейн представлен единой идеально перемешанной тепловой ёмкостью. Геометрия 25 × 12,5 × 1,6 м выбрана для расчёта и не означает единый стандарт для всех бассейнов. Вода нагревается с 16 до 28 °C; воздух 29 °C при влажности 60%, стены 27 °C, грунт 20 °C, подпиточная вода 15 °C.',
'cap':'К энергии накопления воды необходимо добавить изменяющиеся во времени тепловые потоки. E = C deltaT показывает только энергетическую ёмкость, но не всю энергию с потерями. Отопление здания бассейна в данную границу модели не входит.',
'c':'2. Вывод теплопотерь и анализ чувствительности',
'ev':'Упрощённое уравнение ASHRAE является эмпирическим; парциальные давления подставляются в кПа. Коэффициент активности 1,0 соответствует активному общественному бассейну, 0,5 принят ночью без посетителей. Условное покрытие снижает испарение на 90%, а конвекцию и излучение на 75%. Это сценарные гипотезы, требующие проверки.',
'ground':'Не следует обнулять отрицательные тепловые потоки. При температуре воды 28 °C и воздуха 29 °C конвекция отрицательна: тёплый воздух передаёт тепло воде. Неотрицательное ограничение допустимо для потенциальной скорости испарения.',
'd':'3. Тепловой насос, прямой теплообмен и дата-центр',
'dc':'Номинал IT нельзя автоматически считать мощностью бассейна: 10 МВт × 0,82 × 0,85 = 6,97 МВт потенциально доступного тепла IT. Выделенная ветвь источника ограничена 500 кВт. PUE = 1,20 не умножается повторно на теплоту IT, чтобы не получить двойной учёт тепла инфраструктуры.',
'hp':'COP=4 является условной константой, а не реальной картой оборудования при разных температурах и частичной нагрузке. Прямой теплообмен исключает работу компрессора, но не потребление электроэнергии насосами, клапанами и управлением.',
'e':'4. Интегрирование, выполненные расчёты и проверка',
'integr':'В Python применён метод Эйлера с шагом 300 с и контрольным шагом 60 с. В Simulink установлен интегратор ode4, фиксированный шаг 60 с. Релейный термостат с гистерезисом даёт фазовый сдвиг циклов, поэтому конечная температура может отличаться даже при близких физических кривых. Проверяются баланс энергии, достижение 28 °C, доступный источник и ограничения.',
'limitations':'Для следующего этапа нужны реальные температуры и расходы охлаждающей жидкости, расчёт теплообменника, изоляция контуров, характеристика COP(T) и годовой режим. Дополнение пока не встроено внутрь диспетчера Stateflow v85 и не меняет его гарантий безопасности.',
'labels':['Режим Simulink','Первый 28 °C [ч]','Отн. невязка']}}
def make(code):
    t=txt[code]
    s=getSampleStyleSheet()
    s.add(ParagraphStyle(name='PTitle',fontName='ArB',fontSize=17,leading=21,spaceAfter=16))
    s.add(ParagraphStyle(name='PHead',fontName='ArB',fontSize=12,leading=17,spaceBefore=13,spaceAfter=8,textColor=colors.HexColor('#17658d')))
    s.add(ParagraphStyle(name='PBody',fontName='Ar',fontSize=9,leading=15,spaceAfter=10))
    s.add(ParagraphStyle(name='PFormula',fontName='Ar',fontSize=9,leading=15,spaceAfter=6))
    a=[]
    add=lambda x:a.append(Paragraph(x,s['PBody']))
    hd=lambda x:a.append(Paragraph(x,s['PHead']))
    fm=lambda x:a.append(Paragraph(x,s['PFormula']))
    a.append(Paragraph(t['a'],s['PTitle']))
    hd(t['b']);add(t['body1'])
    fm('V = 25 × 12.5 × 1.6 = 500 m³, A = 25 × 12.5 = 312.5 m².')
    fm('m = ρV = 997 kg/m³ × 500 m³ = 498500 kg.')
    fm('C = m cp = 498500 kg × 4182 J/(kg K) = 2,084,727,000 J/K.')
    fm('E = C (28 - 16) K = 25,016,724,000 J = 6.94909 MWh.')
    fm('1 MWh = 3.6e9 J; C = 0.57909 MWh/K.')
    fm('t_min,ideal = E / P = 92.65 h at 75 kW; 46.33 h at 150 kW; 23.16 h at 300 kW.')
    add(t['cap'])
    fm('First law: C dT/dt = Qheat(t) - Qevap(t) - Qconv(t) - Qrad(t) - Qground(t) - Qmakeup(t) - Qother(t).')
    fm('Every Q is W (J/s), so dT/dt = (J/s)/(J/K) = K/s.')
    a.append(PageBreak())
    hd(t['c']);add(t['ev'])
    fm('psat(T) = 0.61094 exp(17.625 T/(T+243.04)) kPa.')
    fm('pa = RH psat(Tair); RH = 0.60; Tair = 29 °C.')
    fm('mevap = 4e-5 A max(psat(T) - pa, 0) Fa (1 - 0.90 cover) kg/s.')
    fm('Qevap = mevap × 2.44e6 J/kg.')
    fm('Qconv = 3 A (T - 29) (1 - 0.75 cover) W.')
    fm('Qrad = 0.95 σ A [(T + 273.15)^4 - (27 + 273.15)^4] (1 - 0.75 cover) W.')
    fm('Qground = 800 (T - 20) W; Qmakeup = mevap 4182 (T - 15) W.')
    fm('Qother = 2000 W; σ = 5.670374419e-8 W/(m² K⁴).')
    add(t['ground'])
    fm('At 28 °C and 60%% RH: Qloss,open = %.3f kW, Qloss,covered = %.3f kW.'%
      (data['holding_open_kW'],data['holding_covered_kW']))
    fm('12 h open + 12 h covered, 28 °C throughout: Ehold,day ≈ %.3f MWh/day.'%
      (24*data['holding_24h_average_kW']/1000))
    fm('Equivalent mean holding power: %.3f kW.'%data['holding_24h_average_kW'])
    a.append(PageBreak())
    hd(t['d']);add(t['dc'])
    fm('QDC,usable = PIT,rated × utilization × recoverable_fraction = 6.97 MW.')
    fm('Direct HX: Qpool ≤ min(Qavailable, QHX,nameplate); verify coolant source temperature and 3 K approach.')
    fm('Heat pump: Qout = Qsource + Welectric; COP = Qout/Welectric.')
    fm('Welectric = Qout/COP; Qsource = Qout (1 - 1/COP).')
    fm('At Qout=150 kW and COP=4: Welectric=37.5 kW; Qsource=112.5 kW.')
    fm('At COP=3/4/5 and fixed Qout=150 kW, compressor electricity=50/37.5/30 kW.')
    fm('For 7-day baseline Qout=%.4f MWh:'%base['heat_MWh'])
    fm('W(COP=3)≈%.4f MWh; W(COP=4)=%.4f MWh; W(COP=5)≈%.4f MWh.'%
       (base['heat_MWh']/3,base['electric_MWh'],base['heat_MWh']/5))
    fm('At COP=4: source waste heat = %.4f MWh; compressor electricity = %.4f MWh.'%
      (base['source_MWh'],base['electric_MWh']))
    add(t['hp'])
    fm('Simple electricity-only energy cost formula: OPEX_el = Eout × electricity_price / COP.')
    fm('Avoid comparing direct HX and HP without circulation, capacity, seasonality, CAPEX and opportunity costs.')
    a.append(PageBreak())
    hd(t['e']);add(t['integr'])
    fm('Euler: T[k+1] = T[k] + dt/C (Qin[k] - Qloss[k]); dt=300 s.')
    fm('Check: C (Tfinal - T0) - Σ(Qin-Qloss) dt ≈ 0.')
    fm('Python first 28 °C at 150 kW = %.3f h.'%base['target_h'])
    fm('Python dt=60 s vs dt=300 s: first-crossing difference = %.3f min.'%
       data['test']['first_28C_delta_minutes'])
    fm('Executed Simulink solver: fixed-step ode4, dt=60 s, thermostat ON at 27.8 °C, OFF at 28.2 °C.')
    rows=[t['labels']]
    for r in sim:rows.append([r['scenar'],f"{r['prvy_dosiahnuty_28C_h']:.3f}",f"{r['reziduum_rel']:.6g}"])
    tab=Table(rows,colWidths=[235,124,128],repeatRows=1)
    tab.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Ar'),('FONTSIZE',(0,0),(-1,-1),8),
     ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1eef4')),
     ('GRID',(0,0),(-1,-1),.3,colors.grey),
     ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    a.append(tab);add(t['limitations'])
    fm('Sources: ASHRAE HVAC Applications 2023 ch. 6, Indoor Swimming Pools; EnergyPlus Engineering Reference.')
    fm('Project artifacts: MATLAB/Simulink model, executed CSV, JSON, validation logs and three-language report, 2026-10-23.')
    append=OUT/('priloha_'+code+'.pdf')
    SimpleDocTemplate(str(append),pagesize=A4,leftMargin=48,rightMargin=48,
       topMargin=38,bottomMargin=42).build(a)
    target=OUT/('Bazen_500m3_'+code+'.pdf')
    prior=pymupdf.open(str(target)); extra=pymupdf.open(str(append))
    prior.insert_pdf(extra)
    tmp=OUT/('spojeny_'+code+'.pdf');prior.save(str(tmp),garbage=4,deflate=True)
    prior.close();extra.close();tmp.replace(target);append.unlink()
    d=pymupdf.open(str(target)); pages=len(d); assert pages>=7
    for pg in d:
        text=pg.get_text()
        assert len(text.strip())>50
    d.close()
    return {'language':code,'pdf':str(target),'pages':pages,'bytes':target.stat().st_size}
print(json.dumps([make(lang) for lang in ['SK','EN','RU']],ensure_ascii=False))
