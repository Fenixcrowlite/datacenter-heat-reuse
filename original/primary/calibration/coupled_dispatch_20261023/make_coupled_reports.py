# -*- coding: utf-8 -*-
"""Generate independent trilingual research handoff, with plots and math.
No changes to parallel pool/Simulink model. Only writes this owned directory.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import csv, json, math
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/"coupled_results_2025.json").read_text(encoding="utf-8"))
with (ROOT/"pool_volume_cover_sensitivity_2025.csv").open(encoding="utf-8-sig",newline="") as f:
    sens=list(csv.DictReader(f))
C={x["case"]:x for x in data["cases"]}
cfg=["liquid35_without_pool","liquid35_direct_pool","air25_without_pool","air25_hp_pool"]
cases=[C[x] for x in cfg]
assert len(cases)==4
assert abs(cases[1]["pool_heat_MWh"]-250.125)<1e-4
assert abs(cases[1]["pool_energy_residual_MWh"])<1e-4
assert data["main_dispatch_core_regression_verified"]
p=Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial",str(p/"arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold",str(p/"arialbd.ttf")))
pdfmetrics.registerFontFamily("Arial",normal="Arial",bold="Arial-Bold")
langs={
"SK":{
"title":"Integrovaná ročná simulácia: dátové centrum, teplovodná sieť a plavecký bazén",
"sub":"Výsledky nezávislej integrácie MATLAB R2026a, rok počasia 2025, 23.10.2026",
"notice":"Výlučne výskumný scenár. Nie je to certifikovaný projekt stavby ani meraná prevádzka.",
"intro":"Úloha: porovnať využitie odpadového tepla dátového centra v teplovodnej sieti pri pridaní bazéna. Reálna vstupná teplota pochádza z hodinovej reanalýzy NASA POWER, ale výkon serverov, vlastnosti výmenníka a prostredie plavárne zostávajú predpokladmi.",
"method":"Metodika a matematická bilancia",
"p1":"Bazén: L = 25 m, W = 12,5 m, priemerná hĺbka 1,6 m, V = 500 m³, A = 312,5 m². Začiatočná teplota vody 16 °C, hysterézia vykurovania 27,25 °C / 27,60 °C, modelový strop 27,80 °C. Tepelný výmenník 150 kW, denná prevádzka 08:00-20:00 v čase Europe/Bratislava. V noci sa modeluje zakrytie hladiny.",
"p2":"Použitá dynamika: C·dT/dt = Q_bazén - Q_výpar - Q_konvekcia - Q_žiarenie - Q_konštrukcia - Q_doplnková voda - Q_ostatné; C = ρ·V·cp. Päťminútový explicitný numerický krok je vložený do hodinového dispečingu siete.",
"p3":"Energetická hranica DC: Q_HP,out = Q_DC,odoberané + W_kompresor. Príkon kompresora nie je recyklovaným serverovým teplom. Na účely predbežného ERF sa počíta iba extrahované teplo, skutočný ERF však vyžaduje meranie na systémovej hranici podľa nariadenia (EÚ) 2024/1364.",
"p4":"Zabezpečenie proti dvojitému použitiu: najvyšší päťminútový odber tepla bazénom počas každej hodiny sa najprv rezervuje. Až zvyšný hodinový zdroj možno prideliť tepelnému čerpadlu pre sieť. Táto konzervatívna aproximácia môže podhodnotiť využitie zdroja v krátkych intervaloch.",
"results":"Ročné výsledky",
"types":["Zdroj 35°C bez bazéna","35°C priamy výmenník","Zdroj 25°C bez bazéna","25°C bazén cez TČ"],
"table":["Prípad","Bazén MWh","Zdroj DC MWh","Plyn MWh","Zdroj do bazéna MWh"],
"econ":"Ekonomické porovnanie",
"econdetail":"Modelová dodatočná úspora voči alternatíve, keď sa rovnaké teplo bazéna získa plynovým kotlom (účinnosť 90 %): priamy výmenník {direct} EUR/rok; nízkoteplotný zdroj s TČ pri COP = 4: {hp} EUR/rok. Zahrnutá je strata tepla dostupného pre sieť a dodatočný plyn. Nie sú zahrnuté CAPEX, čerpadlá, výmenníkový návrh, servis ani VZT bazénovej haly.",
"sensitivity":"Citlivosť bazénových parametrov",
"sensdetail":"Rok a rovnaké zdroje; bazén 500 m³ s nočným zakrytím: {base} MWh; 1000 m³ so zakrytím: {large} MWh; 500 m³ bez zakrytia: {no_cover} MWh. Zväčšenie plochy a koeficient prestupu UA sú stále modelové škálovania, nie údaje z konkrétnej stavby.",
"checks":"Validácia a obmedzenia",
"checkdetail":"Rovnaký dispečer bez bazéna reprodukoval referenčnú implementáciu dchr.simulate_system (elektrina TČ, plyn, akumulátor, výkon TČ). Bilancia bazéna uzatvorená, zdroj sa nepoužíva dvakrát. Najvyššia vypočítaná teplota vody 27,62 °C. Neoveruje to poruchu snímača, prestupný čas ventilu, kvalitu vody ani normovú zhodu.",
"sources":"Oficiálne zdroje a pôvod údajov",
"limits":"Nevyriešené: hodinové merania IT záťaže; skutočný COP pri čiastočnej záťaži a teplotách; teplonosné prietoky; BMS plavárne, vzduchotechnika a spotreba vody; skutočná cena energií; tepelné straty výmenníka a čerpadiel; aktuálne úplné znenie požiadaviek STN a zákona. Model Simulink iného pracovného toku zostal nezmenený.",
"handoff":"Podklady a reprodukcia: run_coupled_annual_SK.m; simulate_coupled_pool_SK.m; coupled_scenarios_2025.csv; 4 × 8760h CSV; pool_volume_cover_sensitivity_2025.csv."
},
"RU":{
"title":"Годовая связанная модель: дата-центр, теплосеть и плавательный бассейн",
"sub":"Результаты независимого моделирования MATLAB R2026a, погода 2025 года, 23.10.2026",
"notice":"Исследовательский сценарий, не сертифицированный проект и не измерения работающей установки.",
"intro":"Задача: оценить утилизацию серверного тепла в теплосети при подключении дополнительного потребителя, бассейна. Часовая наружная температура получена из реанализа NASA POWER. Нагрузки серверов, свойства оборудования и параметры бассейна пока остаются допущениями.",
"method":"Методика и тепловой баланс",
"p1":"Бассейн: длина 25 м, ширина 12,5 м, глубина 1,6 м, объём 500 м³, площадь воды 312,5 м². Начало 16 °C, термостат 27,25/27,60 °C, моделируемый верхний предел 27,80 °C. Тепловая мощность 150 кВт. Работа 08:00-20:00 по времени Братиславы, ночью принимается покрытие.",
"p2":"Динамика: C·dT/dt = Q_нагрев - Q_испарение - Q_конвекция - Q_излучение - Q_конструкция - Q_подпитка - Q_прочее; C = ρ·V·cp. Интегрирование бассейна с шагом 300 секунд, диспетчер теплосети с шагом один час.",
"p3":"Энергия теплового насоса: Q_HP,out = Q_DC,источник + W_компрессор. Электроэнергия компрессора не является серверным теплом. Рассчитанный ERF_source_proxy лишь оценка извлечённого тепла к общему потреблению DC, не показатель отчётности по EU 2024/1364.",
"p4":"Во избежание двойного счёта в каждом часовом интервале резервируется пиковое пятиминутное потребление серверного тепла бассейном. Оставшееся выделяется теплосети. Это консервативная аппроксимация, которая может временно недоиспользовать доступное тепло.",
"results":"Результаты годовых симуляций",
"types":["35°C без бассейна","35°C прямой теплообмен","25°C без бассейна","25°C бассейн через тепловой насос"],
"table":["Сценарий","Бассейн МВт·ч","Тепло DC МВт·ч","Газ МВт·ч","DC → бассейн МВт·ч"],
"econ":"Экономическая оценка",
"econdetail":"Дополнительная расчётная экономия относительно независимого газового нагрева того же бассейна при КПД 90%: прямой теплообмен {direct} €/год, тепловой насос COP=4 {hp} €/год. Учтены отвлечение тепла от теплосети, возможное дополнительное газовое тепло и электроэнергия компрессора. Не учтены CAPEX, насосы, обслуживание, здание бассейна и осушение.",
"sensitivity":"Изменяемые параметры бассейна",
"sensdetail":"500 м³ и ночное покрытие: {base} МВт·ч/год; 1000 м³ и ночное покрытие: {large} МВт·ч/год; 500 м³ без покрытия: {no_cover} МВт·ч/год. Изменение UA выполнено геометрическим масштабированием, а не на основе проекта ограждающих конструкций.",
"checks":"Проверки и ограничения",
"checkdetail":"Вариант без бассейна воспроизвёл прежний dchr.simulate_system по тепловому насосу, газу и накопителю. Проверены балансы энергии и запрет двойного использования серверного тепла. Максимальная температура в модели 27,62 °C. Проверка не подтверждает безопасность реальной автоматики с погрешностью датчика или задержкой клапана.",
"sources":"Официальные источники и происхождение параметров",
"limits":"Не подтверждены: реальные часовые данные IT, заводская карта COP, расход и температура теплоносителя, параметры вентиляции и осушения бассейна, измеренный ERF, договорные тарифы, гидравлика и полные актуальные стандарты. Исходная Simulink-модель другого чата не изменялась.",
"handoff":"Воспроизведение: run_coupled_annual_SK.m, simulate_coupled_pool_SK.m, coupled_scenarios_2025.csv, четыре годовых CSV и pool_volume_cover_sensitivity_2025.csv."
},
"EN":{
"title":"Annual coupled model: data centre, district heating and swimming pool",
"sub":"Independent MATLAB R2026a simulations with 2025 weather reanalysis, 23 October 2026",
"notice":"Research scenario only. Not a certified system design or monitored operating plant.",
"intro":"Goal: evaluate data-centre waste-heat utilisation for a district-heating network with an additional swimming-pool consumer. External air temperature comes from the NASA POWER hourly gridded reanalysis. IT electrical load, equipment characteristics and pool environment remain engineering assumptions.",
"method":"Methodology and energy balances",
"p1":"Pool: 25 m × 12.5 m × 1.6 m, volume 500 m³, water area 312.5 m². Initial temperature 16 °C, thermostat switching 27.25/27.60 °C, model safety ceiling 27.80 °C. Maximum pool heat input 150 kW; 08:00-20:00 local Bratislava opening hours, covered overnight.",
"p2":"Governing equation: C·dT/dt = Q_heating - Q_evaporation - Q_convection - Q_radiation - Q_structure - Q_makeup - Q_other, with C = ρ·V·cp. Pool integration uses a 300-second step nested within one-hour district dispatch.",
"p3":"Heat pump partition: Q_HP,out = Q_DC,source + W_compressor. Compressor electricity is not recovered IT waste heat. The reported ERF_source_proxy is only a source-extraction indicator, not the EU 2024/1364 metered energy-reuse factor.",
"p4":"To avoid double allocation, the maximum 5-minute pool source draw within every hour is reserved before assigning the remaining source to district heating. This conservative hourly interface can underutilise heat within individual subintervals.",
"results":"Annual simulation results",
"types":["35°C source without pool","35°C direct pool exchanger","25°C source without pool","25°C pool heat pump"],
"table":["Case","Pool MWh","DC source MWh","Gas MWh","DC to pool MWh"],
"econ":"Operating-energy comparison",
"econdetail":"Additional modelled savings versus independent gas-boiler heating of an equivalent pool load at 90% efficiency: direct exchanger {direct} EUR/year, COP=4 pool heat pump {hp} EUR/year. The displacement of heat from district heating and additional gas/HP electricity are included. CAPEX, pumps, service and natatorium HVAC are excluded.",
"sensitivity":"Pool-parameter sensitivity",
"sensdetail":"500 m³ with overnight cover: {base} MWh/year; 1000 m³ with cover: {large} MWh/year; 500 m³ uncovered: {no_cover} MWh/year. The structure UA is scaled geometrically, not calibrated from a building-envelope design.",
"checks":"Verification and limitations",
"checkdetail":"The pool-disabled branch exactly reproduced the original dchr.simulate_system heat pump, gas and storage results. Pool-energy conservation and exclusive DC source allocation passed. Peak model pool water temperature was 27.62 °C. This does not validate real sensor uncertainty, valve lag or pool safety compliance.",
"sources":"Authoritative datasets and references",
"limits":"Outstanding: actual hourly IT power, manufacturer partial-load COP tables, coolant temperatures and flows, natatorium occupancy and dehumidification, boundary metering for ERF, contracted tariffs, hydraulic losses and complete currently effective standards. Concurrent pool Simulink files were not modified.",
"handoff":"Reproducibility: run_coupled_annual_SK.m, simulate_coupled_pool_SK.m, coupled_scenarios_2025.csv, four 8760-hour CSVs and pool_volume_cover_sensitivity_2025.csv."
}
}
SOURCES=[
 ("NASA POWER 2025, 8760h Bratislava, gridded reanalysis","https://power.larc.nasa.gov/docs/services/api/temporal/hourly/"),
 ("Eurostat non-household electricity nrg_pc_205, Slovakia 2025","https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table"),
 ("Eurostat non-household gas nrg_pc_203, Slovakia 2025","https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table"),
 ("EU Commission Delegated Regulation 2024/1364 PUE & ERF","https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj"),
 ("Slovak Decree 308/2012 §8 swimming pools published text","https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html"),
 ("STN EN 15288-1+A1 pool safety design","https://normy.normoff.gov.sk/norma/139372/?lang=en"),
]
def fnum(v,dec=1):return f"{v:,.{dec}f}"
def table_values(lang):
 t=langs[lang]
 rows=[t["table"]]
 for j,v in enumerate(cases):
  rows.append([t["types"][j],fnum(v["pool_heat_MWh"]),fnum(v["total_source_used_MWh"]),fnum(v["gas_heat_MWh"]),fnum(v["pool_source_MWh"])])
 return rows
def make_markdown(lang):
 t=langs[lang]
 rows=table_values(lang)
 s=[f"# {t['title']}","","*"+t["sub"]+"*","","> **"+t["notice"]+"**","",t["intro"],"",f"## {t['method']}","",t["p1"],"",t["p2"],"",t["p3"],"",t["p4"],"",f"## {t['results']}","","| "+" | ".join(rows[0])+" |","|"+"|".join(["---"]*len(rows[0]))+"|"]
 for r in rows[1:]:s.append("| "+" | ".join(r)+" |")
 s.extend(["",f"## {t['econ']}","",t["econdetail"].format(direct=fnum(data["incremental_value_direct_EUR"],0),hp=fnum(data["incremental_value_hp_EUR"],0)),"",f"## {t['sensitivity']}","",t["sensdetail"].format(base=fnum(float(sens[0]["PoolHeat_MWh"])),large=fnum(float(sens[1]["PoolHeat_MWh"])),no_cover=fnum(float(sens[2]["PoolHeat_MWh"]))),"",f"## {t['checks']}","",t["checkdetail"],"",f"## {t['sources']}"])
 for name,url in SOURCES:s.append(f"- [{name}]({url})")
 s.extend(["",t["limits"],"",t["handoff"],"",
 "![[coupled_annual_SK.png]]"])
 return "\n".join(s)+"\n"
HEAD="#1E3A56"; BLUE="#165C86"
for lang,t in langs.items():
 markdown=make_markdown(lang)
 md=ROOT/f"Annual_Coupled_Study_{lang}.md"
 if md.exists():raise FileExistsError(str(md))
 md.write_text(markdown,encoding="utf-8")
 pdf=ROOT/f"Annual_Coupled_Study_{lang}.pdf"
 if pdf.exists():raise FileExistsError(str(pdf))
 style_title=ParagraphStyle("title",fontName="Arial-Bold",fontSize=17,leading=23,textColor=colors.HexColor(HEAD),spaceAfter=10)
 style_h=ParagraphStyle("h",fontName="Arial-Bold",fontSize=11,leading=15,textColor=colors.HexColor(BLUE),spaceBefore=11,spaceAfter=6)
 style_body=ParagraphStyle("body",fontName="Arial",fontSize=9,leading=13,spaceAfter=8)
 style_small=ParagraphStyle("small",fontName="Arial",fontSize=7.5,leading=10,spaceAfter=4)
 style_sub=ParagraphStyle("sub",fontName="Arial",fontSize=9.5,leading=14,spaceAfter=8,textColor=colors.HexColor("#64748b"))
 doc=SimpleDocTemplate(str(pdf),pagesize=A4,topMargin=18*mm,bottomMargin=16*mm,leftMargin=18*mm,rightMargin=18*mm)
 P=lambda v,style=style_body:Paragraph(escape(str(v)),style)
 story=[P(t["title"],style_title),P(t["sub"],style_sub),P(t["notice"],style_h),P(t["intro"])]
 story.append(P(t["method"],style_h))
 for key in ["p1","p2","p3","p4"]:story.append(P(t[key]))
 story.append(P(t["results"],style_h))
 rowvals=table_values(lang)
 cells=[[P(col,style_small) for col in row] for row in rowvals]
 tb=Table(cells,colWidths=[60*mm,29*mm,29*mm,26*mm,27*mm],repeatRows=1,hAlign="CENTER")
 tb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF6")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F5F8FC")]),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#C9D7E3")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),4)]))
 story.extend([tb,Spacer(1,7*mm),P(t["econ"],style_h),P(t["econdetail"].format(direct=fnum(data["incremental_value_direct_EUR"],0),hp=fnum(data["incremental_value_hp_EUR"],0)))])
 story.extend([P(t["sensitivity"],style_h),P(t["sensdetail"].format(base=fnum(float(sens[0]["PoolHeat_MWh"])),large=fnum(float(sens[1]["PoolHeat_MWh"])),no_cover=fnum(float(sens[2]["PoolHeat_MWh"]))))])
 imagefile=ROOT/"coupled_annual_SK.png"
 if imagefile.exists():story.append(Image(str(imagefile),width=168*mm,height=97*mm,kind="proportional",hAlign="CENTER"))
 story.extend([P(t["checks"],style_h),P(t["checkdetail"]),P(t["limits"]),P(t["sources"],style_h)])
 for name,url in SOURCES:story.append(P(name+" — "+url,style_small))
 story.extend([P(t["handoff"],style_small)])
 def footer(canvas,document):
  canvas.setFont("Arial",8);canvas.setFillColor(colors.grey)
  canvas.drawString(18*mm,10*mm,"DataCenter Heat Reuse | 2026-10-23 | "+lang)
  canvas.drawRightString(A4[0]-18*mm,10*mm,str(document.page))
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print("REPORT_READY",lang,str(pdf),pdf.stat().st_size,str(md),flush=True)
