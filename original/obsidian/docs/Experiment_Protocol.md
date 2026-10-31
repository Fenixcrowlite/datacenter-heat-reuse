# Эксперимент v0.1

## Исследовательский вопрос

Как температура извлекаемого тепла дата-центра, доля recoverable heat и наличие накопителя влияют на:

- COP теплового насоса;
- долю годового спроса теплосети, покрытую теплом DC;
- потребность в газовом backup;
- количество неиспользованного тепла;
- ERF/ERE;
- условные OPEX и CO2 относительно gas-only baseline.

## Baseline

Теплосеть полностью обслуживается газовым котлом с КПД 0.90. Baseline нужен только как единая точка сравнения.

## Reference system

- IT capacity: 10 MW.
- PUE: 1.20.
- Supply temperature: 70 °C.
- DH design: 18 MW space heat + 2 MW base hot water.
- Network efficiency: 0.94.
- Hourly time step, 8760 h.

Это **SCENARIO** параметры, а не попытка выдать их за параметры конкретного реального дата-центра.

## Сценарии

| ID | Источник | T source | Recovery | Storage |
|---|---|---:|---:|---:|
| S1 | air-cooled proxy | 25 °C | 0.70 | 0 MWh |
| S2 | liquid cooling | 35 °C | 0.85 | 0 MWh |
| S3 | warm liquid cooling | 45 °C | 0.90 | 0 MWh |
| S4 | warm liquid + storage | 45 °C | 0.90 | 100 MWh |

Сценарии не означают, что любой air-cooled DC обязательно отдаёт ровно 25 °C или 70 %. Это controlled experiment, чтобы увидеть чувствительность системы.

## Гипотезы

**H1.** Рост source temperature повышает COP, потому что уменьшается temperature lift.

**H2.** Рост recovery fraction увеличивает доступное тепло и снижает gas backup, пока система не упирается в спрос.

**H3.** Storage повышает полезное использование тепла, но эффект ограничивается несовпадением сезонного спроса и постоянного DC heat supply.

**H4.** При большом DC и малом летнем спросе появляется curtailment; увеличение оборудования само по себе не гарантирует высокий ERF.

## Контролируемые переменные

Во всех сценариях одинаковы:

- синтетическая погода;
- IT-load realization и random seed;
- DH demand model;
- HP capacity;
- electricity/gas assumptions;
- network losses.

Поэтому разница между сценариями относится именно к source temperature / recovery / storage.

## Выходные данные

`scenario_summary.csv`:

- MeanCOP
- HeatDemand_MWh
- ReusedHeat_MWh
- Coverage
- ERF
- ERE
- HPElectric_MWh
- GasHeat_MWh
- CurtailedHPHeat_MWh
- OpexSaving_EUR
- CO2Saving_t

`warm45_storage100_timeseries.csv` содержит почасовую динамику лучшего технического сценария.

## Графики

1. `01_scenario_comparison.png` — главные KPI по сценариям.
2. `02_winter_operation.png` — 14 зимних дней: demand/HP/gas/Tout/storage.
3. `03_load_duration.png` — load-duration curve.
4. `04_cop_sensitivity.png` — COP от source temperature.
5. `05_monthly_energy_balance.png` — месячный баланс DC heat + gas.

## Критерии проверки модели

### Conservation checks

На каждом шаге:

`DH demand ≈ HP direct + storage discharge + gas`.

Storage должен оставаться в `[0, Emax]`.

HP electricity не может быть отрицательной; COP не выходит из заданных engineering bounds.

### Literature sanity checks

Мы не требуем совпадения процентов с Espoo или Frankfurt, потому что у них другие мощности и реальные datasets. Проверяем направление эффектов и физически разумный порядок величин.

### Следующий эксперимент

После v0.1 делаем параметрический sweep:

- source T: 20…50 °C;
- DH supply: 50…90 °C;
- storage: 0…1000 MWh;
- IT capacity: 1…100 MW;
- electricity/gas price ratio;
- реальные Bratislava weather + реальный/типовой heat-load profile.

Затем Sobol/Morris sensitivity или Monte-Carlo покажет, какие параметры действительно определяют результат, а какие люди просто любят обсуждать на совещаниях.
