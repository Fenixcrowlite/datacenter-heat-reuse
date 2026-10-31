# Архитектура и расширяемость

## Принцип

Проект строится не вокруг одной статьи и не вокруг одного «магического» скрипта на 900 строк, потому что человечество уже достаточно страдало от таких файлов. Каждый физический/информационный слой имеет отдельный контракт.

## Модули

| Модуль | Вход | Выход | Текущая реализация | Чем заменяется |
|---|---|---|---|---|
| `make_inputs` | config | weather, IT-load | синтетический год | реальная погода, telemetry, CSV/API |
| DC heat source | IT load, recovery | source heat | `eta_rec * P_IT` | thermal server/rack model |
| heat demand | Tout, config | DH demand | linear degree-day | measured DH load, RC/EnergyPlus |
| heat pump | source T/Q, supply T | COP, Qmax | Carnot-efficiency | manufacturer map, Simscape |
| storage | charge/discharge requests | SOC, delivered heat | lumped energy balance | water tank layers, PCM, TCM |
| dispatch | supply/demand/SOC | HP/gas/storage flows | rule-based | LP/MILP/MPC/RL |
| metrics | time series | KPI | annual sums | uncertainty + lifecycle analysis |

## Уровни модели

### L0 — energy screening

Текущая v0.1. Почасовой баланс энергии. Быстро отвечает: «вообще есть смысл или нет?»

### L1 — thermo-economic

Добавляются реальные weather/load data, карты COP, electricity price, heat tariff, CAPEX/OPEX, NPV/LCOH.

### L2 — component physics

Теплообменники UA/LMTD, насосы, hydraulic pressure drop, stratified storage, Simscape Fluids.

### L3 — control and optimization

MPC/MILP: прогноз погоды, цены, IT-load и спрос теплосети. Оптимизируется HP setpoint, storage, backup.

### L4 — digital twin

Telemetry, OPC UA/MQTT, state estimation, online parameter identification, anomaly detection, dashboard.

## Интерфейс параметров

Все глобальные параметры находятся в `matlab/default_config.m`. Узкоспециализированный модуль получает только `cfg` и свои сигналы. Поэтому при замене, например, heat-pump модели не надо править demand или storage.

Рекомендуемое правило при расширении:

```text
new module -> unit test -> comparison against old module -> scenario regression -> only then default
```

## Структура репозитория

```text
DataCenter_Heat_Reuse/
├─ 00_Project_Hub.md
├─ README.md
├─ matlab/
│  ├─ default_config.m
│  ├─ run_experiment.m
│  ├─ +dchr/                 # computational modules
│  └─ simulink/              # generated / hand-edited Simulink models
├─ docs/                     # theory + project documentation
├─ sources/                  # source catalog / paper notes
├─ results/
│  └─ figures/
├─ presentation/
└─ integration/              # OneDrive / Telegram manifests
```

## Версионирование модели

- `v0.x`: screening/research prototype.
- `v1.x`: calibrated model with real Bratislava/selected case data.
- `v2.x`: detailed thermal-hydraulic + optimized dispatch.

Для каждой версии сохраняются config, input dataset, summary CSV и figures. Иначе через два месяца график окажется красивым, а откуда он взялся никто не вспомнит. Традиция, достойная прекращения.
