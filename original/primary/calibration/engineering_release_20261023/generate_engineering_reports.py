# -*- coding: utf-8 -*-
"""Create evidence-grounded SK/RU/EN report markdown from independently executed results."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent
cool=json.loads((P/"independent_cooling_design_scenarios.json").read_text(encoding="utf-8"))
sim=json.loads((P/"IT_cooling_failsafe_simulink_results.json").read_text(encoding="utf-8"))
stress={r["caseName"]:r for r in sim}
assert len(stress)==6
assert cool["profile"]["rows"]==105120
sections={
"RU":{
"title":"Инженерное завершение этапа: дата-центр, бассейн, теплосеть и независимое охлаждение",
"status":"Численно проверено в Python и MATLAB/Simulink. НЕ является рабочим проектом или подтверждением нормативного соответствия.",
"methods":"### 1. Граница энергетической модели",
"method":"Сценарий 10 МВт номинальной IT-мощности, профиль нагрузки IT синтетический; годовая погода NASA POWER Bratislava 2025 является реанализом. Показатель PUE выбран сценарно, не измерен. Реальное предприятие/серверная станция не идентифицированы и существование оборудования не подтверждено.",
"heat":"### 2. Годовой баланс IT-охлаждения",
"helpc":"Из Simulink взято 105 120 пятиминутных отсчётов: IT тепловыделение 71 833 МВт·ч; использованное серверное тепло 38 275 МВт·ч; оставшаяся тепловая энергия к отведению 33 558 МВт·ч. Средний остаточный поток 3,831 МВт. Если все потребители тепла недоступны, независимые охладители обязаны покрывать расчётные 10 МВт.",
"hydro":"### 3. Гидравлика и тепловая инерция",
"hydrotext":"При воде 997 кг/м³ и cp 4182 Дж/(кг·К): 10 МВт и перепад 5 К требуют примерно 1 727 м³/ч; оценочный внутренний диаметр единого коллектора при 2 м/с около 553 мм. Это не окончательный DN: необходимы фактические свойства теплоносителя, трубы, перепады давления и расчёт насосов.",
"stress":"### 4. Проверка реального аварийного режима в Simulink",
"stressintro":"Отдельная сохранённая схема IT_Independent_HeatRejection_20261023_SK.slx, шесть 1-часовых сценариев с шагом 5 секунд и модельным буфером 10 м³, температура базовая 35°C, аварийный порог 40°C.",
"tabhead":"Сценарий | Наибольшая T модели °C | Прошёл защиту?",
"safety":"### 5. Принципиальная безопасная конфигурация",
"safetext":"Резервное охлаждение должно быть независимым от контрактов теплосети и режима бассейна. Условный блок с полезной мощностью 2 МВт должен подтверждать её при максимальной наружной температуре. Для 10-МВт IT шестиблочная схема N+1 достаточна только без потери номинала; при снижении производительности на 10% нужна схема минимум 7×2 МВт при условии подтверждённой способности отводить 10,8 МВт после отказа одного блока. Буфер 2,88 м³ при 30-секундном дефиците 2 МВт и 5 К является лишь идеальным энергетическим минимумом, не обеспечивает расход через холодные пластины. Питание насосов от UPS, клапаны, резервная электросеть и аппаратная остановка по перегреву остаются P0.",
"vendors":"### 6. Реальные каталоги и неснятые ограничения",
"vendortext":"Carrier 61XWH-ZE17: опубликованный номинал 1570 кВт при источнике 20/15 °C и сети 70/75 °C, не наш рабочий режим. Oilon ChillHeat P30–P450: максимум 450 кВт при B0/W35; линейка S достигает 2000 кВт в других условиях, но требует отдельной заводской проверки температур. Alfa Laval предлагает пластинчатые теплообменники с нержавеющими либо титановыми пластинами, а Güntner/Kelvion выпускают сухие и гибридные охладители дата-центров. Реальные COP и полезная мощность при 25/20 и 35/30 → 50/70 °C не подтверждены. Не принимать предложения без OEM-таблиц.",
"pools":"### 7. Бассейн и требования",
"pooltext":"Исходные 500 м³, 25×12,5×1,6 м: прямой теплообменник 150 кВт требует предварительно UA 37,63 кВт/К с проектным запасом и двух независимых насосных контуров. Эти числа основаны на предполагаемых U и давлении, не заводской подбор. Опубликованный текст §8(7) Vyhláška 308/2012 приводит верхнюю границу температуры плавательного бассейна 28°C; действующую консолидированную редакцию и STN EN 15288-1+A1 требуется проверить. ERF по EU 2024/1364 нуждается в реальном измерении на границе дата-центра.",
"rfq":"### 8. Запросы поставщикам и открытые задачи",
"rfqtext":"Сформированы четыре готовых к копированию технических запроса Carrier, Oilon, Alfa Laval и поставщикам охладителей. Они НЕ отправлены и не представлены как действующий заказ. От поставщика нужны карты COP/PLR, температурный диапазон, реальные расходы, давление, скорость пуска резервного агрегата, стоимость и документированная возможность N+1. На следующих этапах необходимы реальные журналы IT нагрузки, гидравлическая P&ID, SLD электропитания, фрагмент паспорта ТН, протокол испытаний автоматики, коммерческие предложения и рецензия лицензированного проектировщика."},
"SK":{
"title":"Záverečná výskumná etapa: dátové centrum, bazén, teplovod a nezávislé chladenie",
"status":"Numericky overené v Pythone a MATLAB/Simulinku. NIE je to certifikovaný projekt ani osvedčenie o zhode.",
"methods":"### 1. Hranica energetického modelu",
"method":"Scenár menovitého IT výkonu 10 MW, profil zaťaženia IT syntetický; NASA POWER Bratislava 2025 je meteorologická reanalýza. PUE je predpoklad, nie meranie prevádzky.",
"heat":"### 2. Ročná bilancia chladenia IT",
"helpc":"Zo 105 120 päťminútových údajov Simulinku: teplo IT 71 833 MWh, reálne použité serverové zdrojové teplo v modeli 38 275 MWh, zvyšné teplo na odvedenie 33 558 MWh. Priemer zvyšku 3,831 MW. Pri súbežnom výpadku bazéna a teplovodu treba nezávisle odviesť návrhových 10 MW.",
"hydro":"### 3. Hydraulika a akumulácia",
"hydrotext":"Pre vodu 997 kg/m³, cp 4182 J/(kgK): 10 MW a 5 K znamená cca 1 727 m³/h, vnútorný priemer jedného rozvodu pri 2 m/s približne 553 mm. Definitívne DN určuje glykol, skutočný rozvod, tlaková strata a čerpadlá.",
"stress":"### 4. Skutočné bezpečnostné testy Simulinku",
"stressintro":"Samostatný uložený model IT_Independent_HeatRejection_20261023_SK.slx, šesť 1-hodinových prípadov, krok 5 sekúnd, bazén a sieť nevykupujú žiadne teplo, zásobník vody 10 m³, T0=35°C a trip=40°C.",
"tabhead":"Scenár | Maximum T modelu °C | Bez prekročenia?",
"safety":"### 5. Bezpečnostná architektúra",
"safetext":"Chladenie IT musí pracovať nezávisle od tepelného odberu bazéna či teplovodu. Čistý výkon 2 MW/blok musí výrobca doložiť pri návrhovej letnej vonkajšej teplote. Pri 10-MW IT sa 6 modulov N+1 udrží len bez deratingu; pri -10% je potrebných približne 7×2 MW, ak po jednej poruche zostane 10,8 MW. Pre 30-s deficit 2 MW pri ΔT=5K je ideálne tepelné minimum zásobníka 2,88m³. To však NEZARUČUJE prietok IT: UPS čerpadlá, ventily, napájanie a bezpečnostné relé sú P0.",
"vendors":"### 6. Výrobcovia a overené hranice",
"vendortext":"Carrier 61XWH-ZE17 1570kW pri W20/15 a W70/75, nie v našej prevádzke. Oilon ChillHeat P30-P450 do 450kW B0/W35; séria S až 2000kW v iných podmienkach. Alfa Laval ponúka zákazkové doskové výmenníky pre bazény. Güntner a Kelvion sú kandidáti nezávislého chladenia. Výrobné mapy COP/PLR pre 25/20 alebo 35/30 → 50/70°C zatiaľ nie sú k dispozícii.",
"pools":"### 7. Bazén a legislatíva",
"pooltext":"500m³ bazén 25×12,5×1,6m, nízkoteplotný výmenník 150kW predbežne UA=37,63 kW/K so scenárovým faktorom zanesenia. Vyhlásený §8 ods.7 308/2012 uvádza 28°C pre plavecký bazén, účinné znenie a plnú STN EN15288-1+A1 pred stavbou overiť. ERF meraný podľa EU 2024/1364 na hranici dátového centra.",
"rfq":"### 8. RFQ a otvorené požiadavky",
"rfqtext":"Vyhotovené štyri nezáväzné návrhy dopytov pre Carrier, Oilon, Alfa Laval a dodávateľov recoolerov. NEODOSLANÉ. Potrebujeme výrobcom overené tepelné parametre, COP/PLR, prietoky, tlakové straty, N+1 záložný čas, ceny a realizovateľnosť; ďalej reálne IT/BMS údaje, hydrauliku, SLD napájania, plné normy a funkčné skúšky."},
"EN":{
"title":"Engineering research release: data centre, pool, district heating and independent IT cooling",
"status":"Numerical MATLAB/Simulink and Python results only. NOT a commissioned or compliance-certified installation.",
"methods":"### 1. Energy model perimeter",
"method":"The IT facility is a 10 MW nominal heat scenario, not metered equipment. IT demand remains synthetic; Bratislava 2025 weather comes from NASA POWER gridded reanalysis. PUE is an assumption rather than metered site data.",
"heat":"### 2. Annual IT cooling heat balance",
"helpc":"Across 105,120 five-minute Simulink points: 71,833 MWh IT heat, 38,275 MWh actually used IT source heat, 33,558 MWh residual IT heat to reject. Mean rejected load 3.831 MW. When both district and pool reuse are absent, independent backup cooling must support 10 MW design-rated IT heat.",
"hydro":"### 3. Hydraulic and ride-through screening",
"hydrotext":"For liquid water rho=997 kg/m³ and cp=4182 J/(kgK), 10 MW across 5K needs roughly 1727 m³/h; a single line at 2 m/s requires 553mm inside diameter. Actual glycol fluid, network layout, pressure drops and hydraulic pump selection are not available.",
"stress":"### 4. Executed Simulink failure tests",
"stressintro":"New saved IT_Independent_HeatRejection_20261023_SK.slx: six one-hour runs with 5-second steps, all pool and district consumers disabled, water buffer 10m³, T initial 35°C, protection threshold 40°C.",
"tabhead":"Scenario | Model max T °C | Did not trip?",
"safety":"### 5. Minimum safety architecture",
"safetext":"Independent IT heat rejection must not depend on the heat reuse business. Every nominally 2MW net cooler needs manufacturer proof at the site's maximum outdoor design condition. With 10MW IT, 6 installed units N+1 cover full design only without derating; with 10% derating, 7x2MW would leave 10.8MW after one failure. A 30-second 2MW cooling deficit and 5K buffer interval requires a minimum theoretical 2.88m³ water; this does NOT provide IT chip coolant flow. UPS-supported pumps, independent actuators, hardware safety relays and dual power feeds remain P0.",
"vendors":"### 6. Equipment envelopes and unknowns",
"vendortext":"Carrier 61XWH-ZE17 up to 1570kW nominal at W20/15 source and W70/75 sink, not the target conditions. Oilon ChillHeat P30-P450 max 450kW at B0/W35; S series up to 2000kW at other conditions. Alfa Laval offers industrial gasketed plate pool exchangers. Güntner and Kelvion provide data center recooling systems. Actual 25/20 and 35/30 to 50/70C COP/PLR and effective duty are not confirmed.",
"pools":"### 7. Pool/standards boundary",
"pooltext":"A 500m³ pool (25×12.5×1.6m) using direct 150kW low-temperature exchanger has preliminary design UA=37.63kW/K with an assumed fouling allowance. Slovak Decree 308/2012 published §8(7) specifies a 28°C maximum for swimming pools, but effective consolidated legislation and licensed STN EN15288-1+A1 require review. Reportable ERF under EU 2024/1364 requires a boundary heat meter.",
"rfq":"### 8. RFQs and unresolved work",
"rfqtext":"Created four engineering RFQ drafts for Carrier, Oilon, Alfa Laval and recooler manufacturers. NOT SENT and no vendor quotes obtained. Obtain certified COP/PLR maps, capacity/flow/pressure loss, fault recovery, N+1, commissioning and budget prices, then actual IT/BMS logs, hydraulic schematics, electrical SLD, qualified legal review and safety commissioning test results."}
}
stress_labels={
"RU":["6 блоков, 0% снижения, переключение 30 с","7 блоков, -10%, переключение 30 с","7 блоков, -10%, переключение 300 с","6 блоков, -10%, длительный дефицит","7 блоков, -20%, длительный дефицит","7 блоков, отказ насоса на 10 с"],
"SK":["6 modulov, 0% derating, 30 s","7 modulov, -10%, 30 s","7 modulov, -10%, 300 s","6 modulov, -10%, trvalý deficit","7 modulov, -20%, trvalý deficit","7 modulov, porucha čerpadla 10 s"],
"EN":["6 units, 0% derating, 30s","7 units, 10% derating, 30s","7 units, 10% derating, 300s","6 units, 10% derating, persistent","7 units, 20% derating, persistent","7 units, 10s pump failure"]
}

keys=['N6_nominal_fail30s','N7_der10_fail30s','N7_der10_fail300s',
      'N6_der10_nominal_undersized','N7_der20_nominal_undersized',
      'N7_der10_pump_fault']
references=[
 ("Carrier 61XWH-ZE 2025, published 1570 kW W20/15 / W70/75",
  "https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf"),
 ("Oilon ChillHeat product data", "https://oilon.com/wp-content/uploads/2024/04/Oilon_ChillHeat-EN.pdf"),
 ("Alfa Laval Slovakia plate heat exchangers",
  "https://www.alfalaval.sk/produkty-a-riesenia/prenos-tepla/doskove-vymenniky-tepla/plate-heat-exchangers/"),
 ("Güntner data center cooling","https://guntner.com/applications/data-centers"),
 ("Kelvion data center cooling","https://www.kelvion.com/industry-solutions/data-center"),
 ("ASHRAE Data Centers engineering",
  "https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx"),
 ("EU delegated regulation 2024/1364 ERF",
  "https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj"),
 ("Slov-Lex swimming pool requirements, decree 308/2012 original edition",
  "https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html")
]
for lang,v in sections.items():
    report=[
      "# "+v["title"],"",
      "**23 October 2026 | Model status: VERIFIED NUMERICAL STUDY**",
      "> "+v["status"],"",
      v["methods"],v["method"],"",v["heat"],v["helpc"],"",
      v["hydro"],v["hydrotext"],"",v["stress"],v["stressintro"],"",
      "| "+v["tabhead"].replace(" | "," | ")+" |",
      "|---|---:|:---:|"
    ]
    for i,key in enumerate(keys):
        z=stress[key]
        report.append("| "+stress_labels[lang][i]+
          " | "+format(z["maxTemperature_C"],".2f")+
          " | "+("PASS" if z["safeSimulation"] else "TRIP")+" |")
    report +=["",
      "**Note / Poznámka / Примечание:** Results ABOVE the configured trip threshold are invalid for physical equipment; no IT load shedding or boiling model is included.",
      "",
      v["safety"],v["safetext"],"",v["vendors"],v["vendortext"],"",
      v["pools"],v["pooltext"],"",v["rfq"],v["rfqtext"],"",
      "### Source material",""
    ]
    for name,url in references:report.append("- ["+name+"]("+url+")")
    report +=["","### Reproducible outputs",
      "- `independent_cooling_design_scenarios.json` and `cooling_nplus1_derating.csv`",
      "- `IT_Independent_HeatRejection_20261023_SK.slx`",
      "- `test_IT_cooling_failure_SK.m` and `IT_cooling_failsafe_simulink_results.json`",
      "- `cooling_fault_second_scale.csv`, `cooling_failover_sensitivity.csv`",
      "- `RFQ_Carrier_EN.md`, `RFQ_Oilon_EN.md`, `RFQ_AlfaLaval_EN.md`, `RFQ_DryCooler_EN.md`",
      "- `cooling_resilience_calculator.html`",
      "- `FMEA_engineering_gaps.csv`",
      "",
      "**No procurement, email delivery, commissioning or operating safety certification has occurred.**"]
    f=P/("Engineering_Release_"+lang+".md")
    if f.exists():raise FileExistsError(str(f))
    f.write_text("\n".join(report)+"\n",encoding="utf-8")
    print("ENGINEERING_REPORT_MD_CREATED",lang,len(report))
