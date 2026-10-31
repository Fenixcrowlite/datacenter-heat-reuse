# Параметры, допущения и доверие к данным

Ниже специально разделено, что является **литературным ориентиром**, а что выбрано для нашего контролируемого эксперимента. Иначе очень быстро получается научно выглядящий суп из несопоставимых цифр.

## Параметры v0.1

| Параметр | v0.1 | Статус | Комментарий |
|---|---:|---|---|
| IT capacity | 10 MW | SCENARIO | средний условный DC для reference model |
| PUE | 1.20 | SCENARIO | не привязан к конкретному объекту |
| IT utilization mean | 0.82 | SCENARIO | synthetic load generator |
| source T | 25/35/45 °C | SCENARIO | sensitivity by cooling concept |
| recovery fraction | 0.70/0.85/0.90 | SCENARIO | proxy, позже calibration |
| DH supply T | 70 °C | SCENARIO | medium-temperature reference |
| Carnot efficiency factor | 0.50 | SCENARIO | surrogate for real compressor map |
| HP max heat | 12 MW | SCENARIO | capacity limit |
| DH space heat design | 18 MW | SCENARIO | synthetic district |
| DHW/base load | 2 MW | SCENARIO | synthetic district |
| network efficiency | 0.94 | SCENARIO | aggregate loss proxy |
| storage | 0 / 100 MWh | SCENARIO | short-term comparison |
| gas boiler efficiency | 0.90 | SCENARIO | baseline/backup |
| electricity | 100 EUR/MWh | SCENARIO | not current market quote |
| gas fuel | 50 EUR/MWh | SCENARIO | not current market quote |
| grid EF | 0.20 tCO2/MWh | SCENARIO | sensitivity placeholder |
| gas EF | 0.202 tCO2/MWh fuel | SCENARIO | placeholder for comparison |

## Literature anchors used to design the experiment

- **Espoo / Wahlroos 2017:** 20–60 MW waste-heat cases; annual DH production simulation and utilization/cost effects. Это обосновывает годовой dispatch и KPI utilization/operating cost.
- **Frankfurt / Jürgens 2024:** 144 GWh/year demand, 37 MWth HP, 20 MWth gas, daily-peak storage, 97.5 % coverage in their case. Это обосновывает topology HP + storage + backup.
- **Hiltunen & Syri 2021:** liquid cooling highlighted because higher-grade waste heat is useful. Это обосновывает source-temperature scenarios.
- **Oró 2019:** air-cooled urban DC can have limited economic attractiveness. Поэтому air cooling не выбрасывается из исследования, а используется как weaker baseline.
- **Varna / Verzino 2026:** integrated HP + thermal/thermochemical storage + existing district-heating context. Это направление для storage/exergy extension.

## Почему мы пока не копируем числа из одной статьи

Чтобы корректно воспроизвести publication case, нужны как минимум:

1. погодный ряд конкретного года;
2. часовой heat-load profile;
3. supply/return temperatures;
4. реальные мощности источников;
5. HP performance map / COP assumptions;
6. electricity/fuel prices того периода;
7. storage control;
8. сетевые потери и ограничения;
9. CAPEX/OPEX boundary conditions.

Часть этих данных в review/list PDF отсутствует. Поэтому текущая версия строит **свою воспроизводимую систему**, а статьи используются как anchors и sanity checks.

## Что калибровать первым

При переходе на реальный Bratislava/Slovakia case:

1. `weather` -> исторический hourly dataset;
2. `heat_demand` -> реальная/типовая нагрузка выбранного района;
3. `source_temp_C`, `recovery_fraction` -> выбранная DC cooling architecture;
4. HP model -> datasheet/performance map;
5. DH supply/return schedule -> реальная сеть;
6. energy prices + emission factors -> год и тарифная структура;
7. storage capacity/control -> оптимизация, а не произвольный размер.

## Уровни доверия

- **A:** непосредственно измеренные данные выбранного объекта.
- **B:** параметры из peer-reviewed case study с понятной методикой.
- **C:** manufacturer/data-provider values.
- **D:** engineering scenario assumptions.

v0.1 в основном B/D. Цель v1.0 — поднять ключевые параметры до A/B/C.
