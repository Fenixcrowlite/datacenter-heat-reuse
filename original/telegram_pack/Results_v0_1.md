# Результаты эксперимента v0.1

## Основной годовой эксперимент

Synthetic reference district: annual heat demand = **59.43 GWh**.

| Scenario | Mean COP | Heat coverage | Gas heat | HP electricity | Reused heat | ERF | Scenario OPEX saving* | CO2 saving* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Air 25 °C, no storage | 3.81 | 76.3 % | 14.09 GWh | 11.89 GWh | 45.34 GWh | 0.526 | 1.33 M€/a | 58.5 % |
| Liquid 35 °C, no storage | 4.90 | 81.9 % | 10.75 GWh | 9.93 GWh | 48.68 GWh | 0.565 | 1.71 M€/a | 67.0 % |
| Warm 45 °C, no storage | 6.86 | 81.3 % | 11.13 GWh | 7.04 GWh | 48.30 GWh | 0.560 | 1.98 M€/a | 70.7 % |
| Warm 45 °C + 100 MWh | 6.86 | **82.5 %** | **10.41 GWh** | 7.16 GWh | **49.02 GWh** | **0.569** | **2.01 M€/a** | **71.7 %** |

\* OPEX и CO2 рассчитаны по **scenario assumptions** из `default_config.m`; это не текущий тариф/эмиссионный фактор Словакии.

## Что здесь физически интересно

### 1. Higher source temperature резко снижает электрическое потребление HP

В сценарии 45 °C средний COP ≈ 6.86 против 3.81 при 25 °C. Поэтому HP electricity падает примерно с 11.9 до 7.0 GWh/a.

Это один из сильнейших аргументов в пользу warm-liquid cooling, если цель — heat reuse.

### 2. Coverage не обязано монотонно расти вместе с COP

Это важный нюанс. COP говорит об эффективности теплового насоса, но годовое heat coverage определяется также:

- количеством recovered source heat;
- HP thermal capacity;
- формой demand profile;
- storage;
- curtailment.

При фиксированном source heat более низкий COP означает больше добавленной compressor work к thermal output. Поэтому сравнивать cooling concepts только по `Q_HP_out` без electricity нельзя.

Для чистого влияния температуры мы отдельно запускаем factor-isolated sweep с одинаковым `recovery_fraction = 0.85`.

### 3. Storage 100 MWh помогает, но не совершает чудо

При 45 °C:
- coverage: 81.3 % -> 82.5 %;
- gas heat: 11.13 -> 10.41 GWh;
- reused heat: 48.30 -> 49.02 GWh.

То есть short-term storage сглаживает mismatch, но годовая сезонность остаётся. Именно поэтому следующий серьёзный вопрос — seasonal storage или дополнительные круглогодичные потребители тепла.

### 4. Curtailment остаётся большим

Даже лучший scenario имеет значительный unused heat-pump potential. Это не «ошибка модели», а сигнал sizing problem: летом или при низком спросе heat sink слишком мал.

Следующие решения:
- low-temperature DH / DHW / pools / industrial loads;
- district cooling / absorption option;
- сезонное хранение;
- оптимизация размера HP;
- несколько heat sinks.

## Файлы графиков

- `01_scenario_comparison.png` — четыре сценария.
- `02_winter_operation.png` — demand/HP/gas/storage за 14 дней.
- `03_load_duration.png` — load duration.
- `04_cop_sensitivity.png` — COP при source 20...50 °C.
- `05_monthly_energy_balance.png` — monthly heat balance.
- `06_cop_temperature_lift_map.png` — source × DH supply.
- `07_storage_sensitivity.png` — storage size vs coverage/curtailment.

## Как интерпретировать результат честно

Результат доказывает не то, что «в Братиславе будет ровно 82.5 % и 2.01 M€/year». Он доказывает, что:

1. модель замыкает энергетический баланс;
2. сценарии воспроизводимы;
3. temperature lift, recovery, capacity и storage дают измеримые эффекты;
4. framework готов к замене synthetic inputs на реальные данные;
5. можно поставить следующий calibrated experiment без переписывания проекта с нуля.
