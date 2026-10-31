# DataCenter Heat Reuse - Project Hub

> Цель: построить расширяемую инженерную модель утилизации тепла дата-центра, проверить ее в MATLAB/Simulink и довести до калибруемого проекта для реальной городской теплосети.

## 1. Порядок изучения

1. [[docs/01_How_System_Works]] - физическая цепочка от серверов до теплосети.
2. [[docs/Mathematical_Model_v0_3_RU]] - уравнения и границы модели.
3. [[docs/Dependency_Map_v0_3_RU]] - что на что влияет.
4. [[docs/Architecture]] - модульные интерфейсы.
5. [[docs/Experiment_Design_v0_3_RU]] - постановка экспериментов.
6. [[docs/Literature_Map]] - связь со статьями.
7. [[sources/source_catalog]] - каталог 31 исходного источника.
8. [[docs/Learning_Path_v0_3_RU]] - маршрут для самостоятельного разбора.
9. [[docs/Extension_Roadmap]] - путь от reference model к calibrated project.

## 2. Главные физические зависимости

- больше IT load -> больше доступного тепла;
- выше recovery fraction -> больше тепла поступает в HP;
- выше source temperature -> меньше temperature lift -> выше COP;
- ниже DH supply temperature -> меньше temperature lift -> выше COP;
- холоднее на улице -> выше heat demand и обычно выше требуемая температура подачи;
- storage переносит тепло во времени, но не создает энергию;
- HP capacity ограничивает peak coverage;
- избыток доступного тепла при маленьком спросе превращается в curtailment;
- экономика зависит не только от COP, но и от electricity/gas prices, CAPEX, utilization и ownership model.

## 3. Что смотреть в результатах

Основные файлы:
- `results/scenario_summary_v2.csv` - архитектурные сценарии;
- `results/temperature_lift_sensitivity_v2.csv` - source/supply sweep;
- `results/storage_sensitivity_v2.csv` - storage sweep;
- `results/uncertainty_v3.csv` - сценарный uncertainty ensemble;
- `results/uncertainty_summary_v3.csv` - P05/Median/P95;
- `results/tests_v2.csv`, `results/tests_v3.csv` - проверки модели;
- `results/figures/` - графики.

Главные KPI: Coverage, MeanCOP, ERF, ERE, HP electricity, GasHeat, Curtailment, OPEX saving, CO2 saving, LCOH, payback и exergy.

## 4. Главные точки входа MATLAB

- `matlab/default_config_v2.m` - базовая конфигурация;
- `matlab/+dchr/+components/` - физические компоненты;
- `matlab/+dchr/simulate_system_v2.m` - системный dispatch;
- `matlab/run_tests_v3.m` - тесты;
- `matlab/run_experiment_v2.m` - архитектурные сценарии;
- `matlab/run_sensitivity_v2.m` - sensitivity maps;
- `matlab/run_uncertainty_v3.m` - uncertainty;
- `matlab/run_full_study_v3.m` - полный воспроизводимый запуск;
- `matlab/simulink/DataCenterHeatReuse_Core.slx` - Simulink core.

## 5. Классы данных

Каждый параметр должен иметь происхождение:
- **A / MEASURED** - измерение выбранного объекта;
- **B / LITERATURE** - peer-reviewed case;
- **C / MANUFACTURER** - данные оборудования;
- **D / SCENARIO** - допущение для эксперимента;
- **DERIVED** - вычисляемая величина.

Пока большая часть чисел reference-модели относится к классу D. Это нормально для исследования структуры и чувствительности, но недостаточно для утверждений о конкретной площадке.

## 6. Следующий исследовательский рубеж

Перейти от synthetic reference case к `Bratislava-like calibrated case`: подключить реальную погоду, типичный/реальный профиль теплосети, supply/return temperature data, выбранную cooling architecture DC и manufacturer map теплового насоса. После этого провести calibration, hold-out validation и uncertainty analysis уже вокруг измеренных параметров.

## 7. Literature validation v0.4 — Frankfurt

Добавлен отдельный validation layer, не заменяющий reference scenarios v0.3:
- [[docs/Frankfurt_Validation_v0_4_RU]] — постановка, допущения и интерпретация;
- `matlab/run_frankfurt_validation_v4.m` — воспроизводимый MATLAB run;
- `results/frankfurt_validation_v4.csv` — baseline KPI;
- `results/frankfurt_sensitivity_v4.csv` — source temperature × storage;
- `results/figures/15_frankfurt_validation_sensitivity_v4.png` — sensitivity plot.

Контрольная точка: 144 GWh/year demand, 37 MWth HP и 97.5% DC heat coverage. Coverage используется для калибровки recovery fraction, поэтому не трактуется как независимое предсказание.

## 8. Аудит первоисточников v0.5 (08.10.2026) — читать ПЕРЕД старой v0.4

**Важное исправление:** опубликованные 144 GWh/a во Frankfurt относятся к теплу потребителей, а производство на входе DHN составляет ~152 GWh/a из-за потерь 5.2%. Поэтому старая v0.4, в которой 144 GWh/a нормированы как вся выработка, НЕ является независимой репликацией Jürgens. Исходную v0.4 не удалять: это архивный исследовательский сценарий.

- [[audit/Formal_Mathematical_Specification_v05_RU]] — физическая постановка, размерности, балансы и строгий план тестов;
- [[audit/Frankfurt_primary_source_audit_v05_RU]] — полный разбор основного опубликованного case, литература versus MATLAB;
- [[audit/Wahlroos_primary_source_audit_v05_RU]] — отдельный Espoo case: EnergyPRO, CHP, цены, optimization (не смешивать с Frankfurt);
- `audit/literature_traceability_v05.csv` — трекер 31 источника с проверяемым статусом;
- `audit/physics_audit_v05.md` — 8760-часовая проверка законов сохранения старой модели;
- `audit/paper_model_gap_v05.json` — пять несоответствий старой модели опубликованным ориентирам.

**Порядок:** первоисточники → независимая математическая модель → автоматические тесты → MATLAB → Simulink → Stateflow → презентация с кадрами реальной реализации. На данный момент подробно проверяются источники №1 и №17; остальные ещё в очереди.

## 9. Обновление v0.6 — полный научный контроль

- [[MASTER_STAGEBOARD_v06]] — девять этапов, критерии завершения и порядок MATLAB→Simulink→Stateflow;
- `STATUS_v06.json` — не смешивать `core review`, `partial review` и полностью закрытый первоисточник;
- [[audit/Ebrahimi_source_audit_v06_RU]] — обзор типов охлаждения и точек отбора тепла;
- [[audit/Hiltunen_Espoo_2020_primary_source_audit_v06_RU]] — Espoo 2020, COP/прайсы/NPV/DPP;
- [[audit/Sintong_2023_primary_source_audit_v06_RU]] — проверка Eq22/Eq24, free-cooling, KPI и экономики;
- `audit/literature_traceability_v06.csv` — 31 источник, матрица доказательств;
- `audit/analytical_preflight_v06.json` — 9/9 независимых тестов математических тождеств;
- `audit/sintong_consistency_v06.json` — 5/5 тестов возможных ошибок знаков и границ (не подтверждённые ошибки публикации);
- PDF первоисточников №4, №8, №9, №21 в `sources/papers/`; исходный список 31 работы в `sources/original/`.

**Строгий статус:** ни одна из 31 работ пока не получила полный научный sign-off; у №1 и №17 основная часть разбора есть, №4, №9, №21 частично проверены. Пока не переносить неподтвержденные Eq17/Eq22/Eq24 из работы №9 в рабочую MATLAB/Simulink модель.
