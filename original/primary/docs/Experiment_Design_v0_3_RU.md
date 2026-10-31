# Эксперимент v0.3

## Цель

Проверить не одну красивую цифру, а причинные связи в системе рекуперации тепла дата-центра: как температура источника, температура теплосети, доля рекуперации, мощность HP и storage влияют на COP, покрытие нагрузки, газ, электричество, CO2 и экономику.

## Базовая система

Reference district:
- IT capacity: 10 MW;
- PUE: 1.20;
- синтетическая почасовая IT-нагрузка;
- синтетическая Bratislava-like погода;
- design space-heating load: 18 MW;
- DHW base: 2 MW;
- network efficiency: 0.94;
- HP thermal limit: 12 MW;
- шаг модели: 1 h;
- горизонт: 8760 h.

Эти числа являются управляемыми исходными условиями эксперимента, а не утверждением о конкретной сети.

## Эксперимент A - архитектурные сценарии

`run_experiment_v2.m` сравнивает пять конфигураций:

| Сценарий | Source T | Recovery | Storage | DH temperature |
|---|---:|---:|---:|---|
| Air25_Fixed70 | 25 C | 0.70 | 0 MWh | fixed 70 C |
| Liquid35_Weather | 35 C | 0.85 | 0 MWh | weather curve |
| Warm45_Weather | 45 C | 0.90 | 0 MWh | weather curve |
| Warm45_Storage100 | 45 C | 0.90 | 100 MWh | weather curve |
| Liquid35_LowTempDH | 35 C | 0.85 | 100 MWh | lower-temperature curve |

Основной вопрос: что выгоднее улучшать первым - качество источника, температурный режим сети или storage.

## Эксперимент B - факторная чувствительность

`run_sensitivity_v2.m` изолирует два ключевых фактора:

1. `T_source = 20...50 C` с шагом 5 C.
2. `T_supply = 50...90 C` с шагом 10 C.

Для каждого сочетания считаются COP, coverage, HP electricity и screening LCOH. Это дает карту temperature lift -> performance.

Отдельный sweep storage:

`0, 25, 50, 100, 250, 500, 1000 MWh`.

Он показывает, где дальнейшее увеличение накопителя почти перестает давать энергетический эффект, но продолжает увеличивать CAPEX.

## Эксперимент C - uncertainty / robustness

`run_uncertainty_v3.m` выполняет Monte-Carlo-like сценарный анализ. По умолчанию 300 прогонов вокруг warm-liquid + 100 MWh storage.

Варьируются:
- source temperature: примерно 38...50 C;
- recovery fraction: 0.82...0.95;
- Carnot efficiency factor: 0.40...0.50;
- electricity price: 70...140 EUR/MWh;
- gas price: 40...80 EUR/MWh fuel;
- grid emissions: 0.08...0.30 tCO2/MWh.

Это не статистически идентифицированные распределения. Их задача - ответить: сохраняется ли инженерный вывод при разумном разбросе допущений.

Выход: P05 / median / P95 для COP, coverage, OPEX saving, CO2 saving, LCOH и payback.

## Верификация

`run_tests_v2.m` проверяет:
- тепловой баланс;
- границы SOC;
- границы COP;
- невозможность забрать больше тепла источника, чем доступно;
- неотрицательность gas/HP power.

`run_tests_v3.m` добавляет направленные sanity checks:
- повышение source temperature должно повышать COP при прочих равных;
- снижение DH supply temperature должно повышать COP;
- увеличение recovery fraction не должно ухудшать coverage;
- добавление storage не должно ухудшать coverage в одинаковом сценарии.

## Как запустить весь пакет

```matlab
cd('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab')
report = run_full_study_v3(300);
```

Генерируются CSV, MAT, log и графики в `results/`.

## Критерии перехода к v1.0

Reference-модель считается готовой к calibrated study, когда будут подключены:
- реальная hourly weather series;
- реальный/репрезентативный DH load profile;
- supply/return temperatures;
- IT-load и cooling telemetry выбранного DC;
- manufacturer performance map HP;
- auxiliary pump/fan electricity;
- реальные CAPEX/OPEX и time-dependent tariffs;
- country/year specific emission factors.

После этого dataset делится на calibration и hold-out validation. Только тогда можно делать численный вывод о конкретной площадке.
