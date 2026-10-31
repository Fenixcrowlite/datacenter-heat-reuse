# Карта литературы: что именно берём в модель

Источник исходного списка: `Datacentra_teplo_vedecke_prace.pdf` (31 научная работа / официальный материал).

## A. Работы, определяющие ядро модели

### 1. Wahlroos et al. (2017), Espoo
**Зачем:** системная интеграция DC waste heat в district heating.

Из списка: моделирование Espoo с 20–60 MW waste heat, снижение operating costs 0.6–7.3 %, использование DC heat более 95 % часов.

**В проект:** годовая почасовая симуляция, heat-demand profile, dispatch, utilization/curtailment, operating-cost KPI.

### 17. Jürgens et al. (2024), Frankfurt
**Зачем:** ближайшая по логике задача для существующей городской застройки.

Из списка: 144 GWh/year demand; 37 MW heat pumps + 20 MW gas boilers; 97.5 % heat demand potentially covered; CO2 reduction 78 %.

**В проект:** архитектура `HP + storage + gas backup`, load-duration curve, sizing, coverage KPI. Это главный reference-case для будущей калибровки.

### 20. Verzino et al. (2026), Varna / THUNDER
**Зачем:** современная CEE-конфигурация и связь с seasonal thermal storage.

**В проект:** отдельный interchangeable storage module и будущий exergy layer. Позже generic storage v0.1 заменяется thermochemical storage submodel.

### 21. Ebrahimi et al. (2014)
**Зачем:** связь cooling technology с температурным уровнем waste heat.

**В проект:** `source_temp_C` и `recovery_fraction` не зашиваются константой, а являются параметрами сценария.

### 22–23. Yuan et al. (2023, 2025), reviews
**Зачем:** общая taxonomy технологий, storage, экономика, законодательство.

**В проект:** modular architecture и roadmap: heat source / HP / DH / storage / economics / regulation.

## B. Работы для heat-pump / temperature-lift гипотезы

### 2. Wahlroos et al. (2018)
Низкая температура waste heat и CAPEX названы основными барьерами. Поэтому source temperature — одна из независимых переменных эксперимента.

### 5. Hiltunen & Syri (2021)
В исходном списке отдельно отмечена рекомендация liquid cooling из-за более высокой температуры доступного тепла.

**В проект:** сценарии 25 / 35 / 45 °C и график `COP(source temperature)`.

### 12. Sorknæs et al. (2022)
Более высокая DC outlet temperature имеет системную ценность; 4th generation low-temperature DH снижает требования к temperature lift.

**В проект:** следующий 2-D sweep `source temperature × DH supply temperature`.

### 18. Oró et al. (2019), Barcelona
1 MW air-cooled DC; ERF до 55 %, но в большинстве air-cooled случаев экономика слабая.

**В проект:** отдельный air-cooled scenario и обязательная techno-economic проверка. Наличие доступного тепла само по себе не гарантирует экономическую целесообразность проекта.

## C. Работы для экономики и бизнес-модели

### 3. Pärssinen et al. (2019)
Investment analysis с точки зрения DC operator.

**Добавить в L1:** CAPEX heat recovery + HP + connection, discounted cash flow, NPV, payback.

### 7–10. Stockholm / ODH studies
Покрывают prosumer-схемы, contracts, actual electricity prices и барьеры сотрудничества.

**Добавить в L1/L3:** heat purchase price, electricity spot price, ownership scenario, dispatch by price.

### 28. Stockholm official case
В исходном списке: ~190,000 EUR/year per MW delivered heat, 15-year connection repayment, >100 GWh from 20 suppliers in 2022.

**В проект:** business-model scenario, но не смешивать эти шведские цены с техническим baseline без адаптации к стране/году.

## D. Работы для city / national energy-system level

### 11. Petrović et al. (2020), Denmark
Показывает, что DC нельзя рассматривать изолированно от энергосистемы.

### 13. Jerez Monsalves et al. (2023)
Flexible cooling + waste heat recovery.

**Будущий модуль:** flexible IT/cooling load и demand response.

### 14–16. London / UK
Показывают городской масштаб и 5th-generation network concepts. В списке: 3.5 MW DC case с >4000 t CO2e и ~£1M/year savings; 261 UK colocation DC дают оценочно 16.8 TWh heat/year, 93 % в городах.

**В проект:** GIS/location layer позже: расстояние до DH load, urban density, connection economics.

## E. Existing 3rd-generation district heating

### 19. Socci et al. (2025), Italy
В исходном списке: для старой 3rd-generation network газ снижается на 11–58 %.

**В проект:** это важнее для Словакии, чем фантазия о мгновенном строительстве идеальной 5GDH с нуля. Нужен сценарий high-temperature existing DH.

### 20. Varna (2026)
3rd-generation network + heat pump + storage в CEE context.

**В проект:** кандидат №1 для расширения storage/exergy части.

## F. Official / regulation layer

### 25. EU Energy Efficiency Directive 2023/1791 + Delegated Regulation 2024/1364
В исходном списке: reporting of reused heat и assessment of waste-heat utilization.

**В проект:** отдельный `compliance/` layer позже: KPI mapping и данные, которые должны логироваться в digital twin.

### 26–31. EC / Euroheat / Covenant of Mayors / London toolkit / Fjernvarme Fyn / ReUseHeat
Используются не как источник одной физической формулы, а для system architecture, business cases, implementation constraints и validation targets.

## Как статьи связаны с файлами модели

| Literature concept | Код / документ |
|---|---|
| annual DH dispatch | `+dchr/simulate_system.m` |
| waste-heat availability | `default_config.m`, `make_inputs.m` |
| source temperature | `default_config.m`, scenarios |
| heat-pump lift/COP | `+dchr/heat_pump_capability.m` |
| peak backup | `simulate_system.m` |
| storage | `simulate_system.m` -> later specialized module |
| ERF/ERE | `+dchr/compute_metrics.m` |
| economics | `compute_metrics.m` -> later DCF/LCOH |
| exergy | roadmap v0.2 |
| existing DH temperature | planned parameter sweep |
| business contracts | planned economic/ownership layer |

## Что нельзя честно утверждать из текущего набора

- что наш v0.1 «воспроизводит Espoo/Frankfurt»;
- что выбранные electricity/gas prices являются текущими ценами в Словакии;
- что synthetic Bratislava-like weather заменяет исторический метеоряд;
- что generic storage эквивалентен THUNDER thermochemical storage;
- что один constant Carnot-efficiency заменяет manufacturer performance map.

Эти пункты являются задачами калибровки и должны быть закрыты до формальных выводов о конкретном объекте.
