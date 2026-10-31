# Roadmap: от v0.1 к полноценному проекту

## v0.1 — Energy screening ✅

- 8760 h energy balance;
- DC heat source;
- temperature-dependent HP COP;
- simple DH demand;
- generic storage;
- backup gas;
- ERF / ERE / OPEX / CO2;
- scenario + sensitivity experiments;
- MATLAB + Simulink core;
- presentation + docs.

## v0.2 — Real data calibration

### Weather
Заменить synthetic profile на hourly Bratislava / selected-city dataset.

### District heating
Вместо degree-day proxy использовать:
- measured hourly heat demand, если найдём;
- либо calibrated building/district RC model;
- реальные supply/return curves.

### Data centre
Выбрать 2–3 реальных cooling architectures:
- air-cooled;
- rear-door / cold plate liquid;
- warm-water direct liquid cooling.

Для каждой определить source temperature, flow, recoverable fraction.

## v0.3 — Component physics

### Heat exchanger
Добавить:

$$Q = UA\Delta T_{lm}$$

pressure drop, pump electricity, approach temperatures.

### Heat pump
Заменить constant Carnot-efficiency на map:

$$COP=f(T_{source,in},T_{sink,out},PLR)$$

от manufacturer или published test data.

### Storage
Три взаимозаменяемые модели:
1. well-mixed water tank;
2. stratified sensible storage;
3. thermochemical / seasonal storage.

## v0.4 — Thermo-economic model

Добавить:
- HP CAPEX by MWth;
- heat exchanger and connection CAPEX;
- storage CAPEX;
- electricity spot/time-of-use prices;
- heat selling price;
- maintenance;
- NPV, IRR, discounted payback;
- LCOH.

Сделать ownership scenarios: DC-owned, utility-owned, ESCO/shared investment.

## v0.5 — Exergy and carbon

Energy balance не показывает качество энергии. Добавить exergy:

$$Ex_Q = Q\left(1-\frac{T_0}{T}\right)$$

Проверять, где уничтожается exergy: cooling, HX, HP, network, storage.

Carbon layer:
- hourly grid emission factor;
- marginal vs average EF;
- gas/backup emissions;
- embodied carbon optional.

## v0.6 — Optimization / control

Сначала deterministic LP/MILP:

Цель:

$$\min \sum_t (c_e(t)P_{HP}(t)+c_g Q_{gas}(t)+c_{start}u(t))$$

при ограничениях HP/storage/network.

Затем MPC:
- weather forecast;
- heat demand forecast;
- electricity price forecast;
- IT load forecast;
- SOC constraints.

## v0.7 — Uncertainty

Monte-Carlo / Latin Hypercube по:
- CAPEX;
- electricity/gas price;
- DC utilization;
- source temperature;
- heat demand;
- COP map uncertainty.

Sensitivity: Morris -> Sobol для самых важных параметров.

## v0.8 — Hydraulic / Simscape model

Добавить:
- pumps;
- pipes;
- valves;
- heat exchangers;
- dynamic temperatures and flows;
- Simscape Fluids where justified.

Важно не тащить Simscape в каждый кусок только потому, что он существует. Детализация нужна там, где она меняет инженерный вывод.

## v0.9 — Digital twin integration

Interfaces:
- OPC UA / MQTT;
- TimescaleDB / InfluxDB;
- Grafana / web dashboard;
- anomaly detection;
- parameter estimation;
- model-vs-measurement residuals.

## v1.0 — Calibrated case study

Полноценный результат:
- выбранный DC + район/теплосеть;
- validated inputs;
- calibrated model;
- sizing + control optimization;
- techno-economic analysis;
- uncertainty;
- comparison with literature;
- reproducible repository;
- thesis/paper-ready figures and tables.
