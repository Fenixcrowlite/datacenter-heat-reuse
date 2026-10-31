# Frankfurt validation v0.4

## Зачем появился этот эксперимент

Версия v0.3 была хорошим исследовательским reference-case, но её годовой спрос 59.43 GWh был сценарным. В v0.4 добавлена отдельная **литературная контрольная ветвь**, чтобы framework проверялся на опубликованном кейсе, не ломая прежние сценарии.

Источник-якорь: Jürgens et al. (2024), Frankfurt. Из статьи/сводки проекта берутся:
- district heating demand = **144 GWh/year**;
- installed heat-pump capacity = **37 MWth**;
- gas backup = **20 MWth** как архитектурный ориентир;
- heat supplied from DC target = **97.5%**;
- reported CO2 reduction = **78%** как отдельная внешняя контрольная величина, пока не калибруемая в v0.4.

## Что НЕ взято из статьи

Следующие величины остаются сценарными параметрами:
- source temperature = 30 °C;
- fixed DH supply = 70 °C;
- Carnot efficiency factor = 0.50;
- storage = 300 MWh;
- synthetic hourly weather and IT-load profile;
- electricity/gas prices and CO2 factors.

Recovery fraction в validation-case **калибруется** по 97.5% coverage. Поэтому совпадение coverage является calibration check, а не независимым прогнозом.

## MATLAB run

Точка входа:
`matlab/run_frankfurt_validation_v4.m`

MATLAB реально выполнен 04.10.2026 на локальной машине.

Получено:

| KPI | Result |
|---|---:|
| Annual demand | 144.000 GWh/year |
| Heat coverage | 97.5000% |
| Mean COP | 4.155 |
| HP electricity | 33.947 GWh/year |
| Gas heat | 3.600 GWh/year |
| Gas fuel | 4.000 GWh/year |
| Scenario OPEX | 3.595 MEUR/year |
| Scenario CO2 | 7.597 kt/year |
| Calibrated recovery fraction | 0.92058 |
| HP rated capacity | 37 MWth |
| Storage | 300 MWh |

## Важная физическая тонкость из sensitivity sweep

При фиксированном **evaporator/source heat** повышение source temperature увеличивает COP и резко снижает electricity, но не обязано увеличивать coverage. Причина:

`Q_hot = Q_source * COP/(COP-1)`

При росте COP компрессор добавляет меньше электрической энергии к тому же source heat, поэтому condenser heat от фиксированного source heat может немного уменьшиться. Это не ошибка модели. Если вместо фиксированного source heat фиксировать IT capacity/recovery architecture другим способом, системный эффект может выглядеть иначе.

Пример без storage:
- 20 °C: COP 3.32, coverage 97.25%, electricity 42.15 GWh/y;
- 30 °C: COP 4.15, coverage 95.22%, electricity 33.07 GWh/y;
- 40 °C: COP 5.52, coverage 92.77%, electricity 24.21 GWh/y;
- 50 °C: COP 6.75, coverage 91.31%, electricity 19.49 GWh/y.

То есть **COP, coverage и source-energy availability нельзя смешивать в один показатель**.

## Storage sweep при Tsource=30 °C

- 0 MWh → 95.22% coverage;
- 100 MWh → 97.37%;
- 300 MWh → 97.50%;
- 600 MWh → 97.69%.

После ~300 MWh виден diminishing return для этого synthetic profile.

## Файлы

- `results/frankfurt_validation_v4.csv`
- `results/frankfurt_validation_v4_timeseries.csv`
- `results/frankfurt_validation_v4.mat`
- `results/frankfurt_sensitivity_v4.csv`
- `results/figures/15_frankfurt_validation_sensitivity_v4.png`

## Что это меняет в проекте

Теперь есть два разных слоя экспериментов:
1. **Reference research layer v0.3**: сравнение архитектур при 59.43 GWh/year.
2. **Literature validation layer v0.4**: отдельный Frankfurt-like case на 144 GWh/year.

Их нельзя смешивать в одну таблицу как будто это одна площадка. Первый слой исследует зависимости, второй проверяет воспроизводимость опубликованной системной точки.
