# Результаты v0.3

Дата воспроизводимого прогона: 04.10.2026.

## 1. Проверки модели

Все базовые conservation checks прошли:
- district heat balance;
- storage bounds;
- COP bounds;
- HP source availability;
- nonnegative gas and HP electricity.

Все directional sanity checks v0.3 также прошли:
- повышение температуры источника повышает COP при прочих равных;
- снижение температуры подачи теплосети повышает COP;
- увеличение recovery fraction не ухудшает coverage;
- добавление storage не ухудшает coverage в одинаковой конфигурации.

## 2. Годовые архитектурные сценарии

Reference heat demand: **59.43 GWh/year**.

| Scenario | Mean COP | Coverage | HP electricity | Gas heat | OPEX saving* | CO2 saving* | Simple payback* |
|---|---:|---:|---:|---:|---:|---:|---:|
| Air25_Fixed70 | 3.10 | 78.1% | 14.96 GWh | 13.03 GWh | 1.08 MEUR/y | 7.42 kt/y | 8.69 y |
| Liquid35_Weather | 4.70 | 82.25% | 10.62 GWh | 10.55 GWh | 1.65 MEUR/y | 8.85 kt/y | 5.68 y |
| Warm45_Weather | 6.19 | 81.06% | 7.85 GWh | 11.26 GWh | 1.89 MEUR/y | 9.24 kt/y | 4.97 y |
| Warm45_Storage100 | 6.21 | 82.26% | 7.97 GWh | 10.54 GWh | 1.92 MEUR/y | 9.38 kt/y | 6.72 y |
| Liquid35_LowTempDH | 6.41 | 78.88% | 7.36 GWh | 12.55 GWh | 1.87 MEUR/y | 9.05 kt/y | 6.91 y |

\* Экономика и CO2 используют scenario assumptions из конфигурации, а не текущие рыночные данные Словакии.

## 3. Что следует из сценариев

### Temperature lift - главный энергетический рычаг

Air25_Fixed70 дает mean COP около 3.10, тогда как warm-liquid сценарий около 6.2. Более качественный источник тепла резко снижает электрическую энергию теплового насоса.

### COP и coverage - разные показатели

Warm45_Weather имеет более высокий COP, чем Liquid35_Weather, но немного меньше coverage. Причина: coverage зависит не только от эффективности HP, но и от доступного source heat, recovery fraction, мощности HP и совпадения генерации с тепловым спросом.

### 100 MWh storage дает умеренный энергетический эффект

Для warm-liquid сценария storage повышает coverage примерно с 81.06% до 82.26% и снижает gas heat примерно с 11.26 до 10.54 GWh/year. Но screening payback ухудшается, потому что добавляется CAPEX storage.

Следовательно, storage надо оптимизировать, а не просто увеличивать.

## 4. Uncertainty experiment

Выполнено 200 сценарных прогонов вокруг `Warm45 + 100 MWh` с вариацией source temperature, recovery, Carnot efficiency, electricity/gas prices и grid CO2.

| KPI | P05 | Median | P95 |
|---|---:|---:|---:|
| Mean COP | 5.45 | 6.25 | 6.67 |
| Coverage | 77.8% | 81.9% | 85.4% |
| OPEX saving | 1.32 MEUR/y | 2.47 MEUR/y | 3.44 MEUR/y |
| CO2 saving | 8.53 kt/y | 9.42 kt/y | 10.28 kt/y |
| Screening LCOH | 35.0 EUR/MWh | 41.3 EUR/MWh | 46.7 EUR/MWh |
| Simple payback | 3.75 y | 5.23 y | 9.80 y |

Эти интервалы показывают чувствительность reference-case к допущениям. Они не являются статистическим confidence interval для реального объекта, потому что входные распределения пока заданы инженерно, а не идентифицированы по измерениям.

## 5. Главный инженерный вывод текущего этапа

Для следующей версии приоритет данных такой:

1. Температура доступного тепла DC и cooling architecture.
2. Реальный DH supply/return schedule.
3. Почасовое совпадение IT load и heat demand.
4. Manufacturer map теплового насоса.
5. Реальная цена электричества и газа.
6. Только после этого - точная оптимизация размера storage и HP.

То есть проект уже годится как исследовательский framework и стенд для экспериментов, но еще не как прогноз конкретной теплосети.

## 6. Файлы результатов

- `results/scenario_summary_v2.csv`
- `results/temperature_lift_sensitivity_v2.csv`
- `results/storage_sensitivity_v2.csv`
- `results/uncertainty_v3.csv`
- `results/uncertainty_summary_v3.csv`
- `results/tests_v2.csv`
- `results/tests_v3.csv`
- `results/full_study_v3.log`
- `results/figures/08_scenario_comparison_v2.png`
- `results/figures/09_lift_cop_coverage_v2.png`
- `results/figures/11_cop_map_v2.png`
- `results/figures/12_coverage_map_v2.png`
- `results/figures/13_storage_tradeoff_v2.png`
- `results/figures/14_uncertainty_v3.png`
