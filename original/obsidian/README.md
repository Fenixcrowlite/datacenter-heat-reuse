# DataCenter Heat Reuse

Модульный исследовательский проект по использованию низкопотенциального тепла дата-центра для централизованного теплоснабжения через теплообменник, тепловой насос и тепловой накопитель.

## Текущий статус: v0.3 reference model

Реализовано:
- компонентная математическая модель `DC -> HX -> heat pump -> storage -> district heating -> gas backup`;
- почасовая симуляция полного года, 8760 шагов;
- air / liquid / warm-liquid сценарии;
- weather-compensated temperature schedule теплосети;
- заменяемые модели HX, HP и storage;
- energy + exergy KPI;
- OPEX, CO2, screening CAPEX/LCOH/payback;
- факторная чувствительность `source temperature x DH supply temperature`;
- sweep емкости storage;
- uncertainty-анализ;
- физические и направленные regression tests;
- Simulink core model;
- презентация, литература и учебные материалы;
- интеграция с Obsidian, OneDrive и Telegram LearningHub.

## Полный запуск MATLAB

```matlab
cd('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab')
report = run_full_study_v3(300);
```

Быстрый сценарный прогон:

```matlab
summary = run_experiment_v2();
```

Результаты сохраняются в `results/`, графики - в `results/figures/`.

## Архитектура

```text
IT load / PUE / cooling
        |
        v
[DC heat source]
        |
        v
[Heat exchanger] ----------> rejected heat
        |
        v
[Heat pump] <--------------- electricity
        |
        +----> [Thermal storage] ----+
        |                             |
        v                             v
[District-heating demand] <---- [dispatch]
        |
        +---- deficit ----> [Gas backup]
```

Каждый физический узел имеет отдельный интерфейс. Реальные weather/load series, telemetry DC, manufacturer COP map, stratified/PCM/thermochemical storage, LP/MILP/MPC, тарифы и гидравлика могут добавляться по одному модулю.

## Читать по порядку

1. `00_Project_Hub.md`
2. `docs/01_How_System_Works.md`
3. `docs/Mathematical_Model_v0_3_RU.md`
4. `docs/Dependency_Map_v0_3_RU.md`
5. `docs/Experiment_Design_v0_3_RU.md`
6. `docs/Literature_Map.md`
7. `sources/parameter_registry.yaml`
8. `docs/Learning_Path_v0_3_RU.md`
9. `docs/Extension_Roadmap.md`

## Важное ограничение

v0.3 - воспроизводимая reference-модель, а не цифровой двойник конкретной теплосети Братиславы. Числа из сценариев используются для исследования зависимостей. Для вывода о реальном объекте нужны измеренные weather/load/temperature/DC telemetry, performance map оборудования, реальные цены и последующая calibration + hold-out validation.
