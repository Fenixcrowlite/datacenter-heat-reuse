# Учебный маршрут по проекту

Цель: не просто запустить MATLAB, а понимать, что означает каждый блок, какая формула за ним стоит и какой параметр реально двигает результат.

## 1. Data center как тепловой источник

Разобраться:
- IT load и электрическая мощность серверов;
- PUE;
- почему почти вся электрическая энергия в итоге становится теплом;
- air cooling против liquid cooling;
- recoverable heat и temperature level.

После этого открыть `+dchr/+components/dc_source.m`.

## 2. Теплообменник

Разобраться:
- heat flow `Q`;
- approach temperature;
- effectiveness;
- `UA`, LMTD, epsilon-NTU.

В модели посмотреть `heat_exchanger.m`, затем менять `cfg.hx.effectiveness` и `cfg.hx.approach_K`.

## 3. Тепловой насос

Разобраться:
- evaporator, condenser, compressor;
- COP;
- Carnot limit;
- temperature lift;
- part-load behavior.

Практика: `run_sensitivity_v2` и график `11_cop_map_v2.png`.

## 4. District heating

Разобраться:
- supply/return temperature;
- weather compensation;
- network losses;
- 3GDH, 4GDH, 5GDH;
- почему понижение supply temperature улучшает тепловой насос.

Практика: сравнить fixed 70 C, weather curve и low-temperature DH.

## 5. Thermal storage

Разобраться:
- power [MW] против capacity [MWh];
- SOC;
- charge/discharge efficiency;
- standing losses;
- short-term и seasonal storage.

Практика: `13_storage_tradeoff_v2.png`.

## 6. Dispatch и управление

Сначала понять baseline rule-based dispatch. Затем изучать:
- linear programming;
- MILP;
- MPC;
- forecast-based control;
- constraints и objective function.

Цель следующего этапа - заменить правила оптимизатором, не меняя модели компонентов.

## 7. KPI

Нужно уметь объяснить без подсказки:
- COP;
- coverage;
- ERF;
- ERE;
- curtailment;
- exergy;
- OPEX;
- CO2 saving;
- LCOH;
- simple payback и NPV.

Особенно важно: высокий COP сам по себе не гарантирует максимальное годовое coverage.

## 8. Валидация

Разобраться:
- conservation test;
- calibration;
- hold-out validation;
- sensitivity analysis;
- uncertainty analysis;
- Monte Carlo;
- Morris/Sobol для будущей глобальной чувствительности.

Практика: `run_tests_v3`, затем `run_uncertainty_v3`.

## Порядок запуска

```matlab
cd('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab')
run_tests_v3
summary = run_experiment_v2
run_sensitivity_v2
uncertainty = run_uncertainty_v3(300)
```

Или весь пакет одной командой:

```matlab
report = run_full_study_v3(300);
```

## Как читать результат каждого эксперимента

Для каждого графика ответить на четыре вопроса:
1. Что находится на осях и в каких единицах?
2. Какая физическая причина формы графика?
3. Какой параметр сильнее всего двигает результат?
4. Какое инженерное решение из этого следует и какие данные нужны, чтобы проверить его на реальном объекте?
