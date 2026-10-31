# Telegram / LearningHub integration v0.3

## Цель

Telegram-бот и web LearningHub не должны содержать вторую копию физической модели. Они являются presentation/orchestration layer и читают опубликованные артефакты проекта.

Canonical source проекта: OneDrive `Projects/DataCenter_Heat_Reuse`.

Obsidian mirror: `02_PROJECTS/02_Automation/DataCenter_Heat_Reuse`.

LearningHub уже сканирует `Bimba/02_PROJECTS`, поэтому презентации и PDF из зеркала автоматически становятся media sources после sync.

## Публикуемый data contract

- `integration/project_manifest_v3.json`
- `results/scenario_summary_v2.csv`
- `results/temperature_lift_sensitivity_v2.csv`
- `results/storage_sensitivity_v2.csv`
- `results/uncertainty_summary_v3.csv`
- `results/tests_v2.csv`
- `results/tests_v3.csv`
- `docs/*.md`
- `results/figures/*.png`
- `presentation/DataCenter_Heat_Reuse_v0_3_RU.pptx`
- `presentation/DataCenter_Heat_Reuse_v0_3_RU.pdf`

## Рекомендуемые команды Telegram

- `/dchr` - версия, last run, test status, ключевой сценарий.
- `/dchr_kpi` - COP / coverage / gas / electricity / ERF / CO2 / payback.
- `/dchr_plot cop` - COP map.
- `/dchr_plot storage` - storage trade-off.
- `/dchr_plot uncertainty` - uncertainty figure.
- `/dchr_explain cop` - учебное объяснение temperature lift и COP.
- `/dchr_explain storage` - power, capacity, SOC, short-term vs seasonal.
- `/dchr_sources` - literature map и parameter traceability.
- `/dchr_files` - презентация, PDF, MATLAB entrypoint, results.

## Разделы web-приложения

1. Overview
2. System architecture
3. Parameters
4. Scenario comparison
5. Time series
6. Sensitivity maps
7. Uncertainty
8. Literature / traceability
9. Learn
10. Validation/tests
11. Releases

## API boundary для будущего project adapter

Read-only:
- `GET /projects/data-center-heat-reuse/manifest`
- `GET /projects/data-center-heat-reuse/scenarios`
- `GET /projects/data-center-heat-reuse/uncertainty`
- `GET /projects/data-center-heat-reuse/tests`
- `GET /projects/data-center-heat-reuse/figures/{id}`
- `GET /projects/data-center-heat-reuse/docs/{id}`

Compute:
- `POST /projects/data-center-heat-reuse/run`

Compute endpoint должен создавать versioned run directory/job record. Он не должен молча перезаписывать опубликованный baseline.

## Offline behavior

Ноутбук может быть выключен. Поэтому Telegram/web должны уметь читать последний опубликованный release из Obsidian/OneDrive cache. Новый MATLAB run в offline-состоянии помечается `compute_unavailable`, но документация, результаты последнего запуска и учебные материалы остаются доступны.

## Текущая интеграция

Bot config содержит:
- `LEARNING_HUB_ROOTS=...Bimba/01_UNIVERSITY;...Bimba/02_PROJECTS`
- проект лежит внутри `02_PROJECTS`, поэтому отдельный root не требуется;
- `scripts/sync_learning_hub_all.py` выполняет загрузку media sources;
- Markdown остается источником для Obsidian, а презентация/PDF служат media-версией для LearningHub.
