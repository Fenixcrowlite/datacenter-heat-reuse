# Simulink status v0.3

`matlab/simulink/DataCenterHeatReuse_Core.slx` успешно открывается в MATLAB R2026a и является исполняемым core-макетом потока энергии.

## Что есть в текущем SLX

- IT load input;
- heat recovery;
- heat-pump thermal uplift with fixed reference COP;
- HP thermal capacity limit;
- direct heat to DH;
- gas backup;
- curtailment;
- HP electricity output.

## Что намеренно остается в MATLAB reference model

Полная годовая логика v0.3, включая weather-dependent DH temperatures, component HP model, storage SOC, exergy, economics, sensitivity и uncertainty, сейчас реализована в `+dchr` и `run_full_study_v3.m`.

Это сделано для прозрачности и удобства массовых 8760-hour прогонов.

## Следующий этап Simulink

Полная Simulink-версия должна повторять те же интерфейсы:

1. `DC_Source` masked subsystem.
2. `Heat_Exchanger` subsystem.
3. `Heat_Pump` subsystem с dynamic COP map.
4. `Thermal_Storage` subsystem с SOC state.
5. `District_Heating` demand/temperature subsystem.
6. `Dispatch_Controller` subsystem.
7. `KPI_Logger`.

После этого MATLAB и Simulink должны запускаться на одном наборе входных данных и проходить cross-validation по energy balance, COP, storage SOC и annual KPI.

## Проверка

04.10.2026 выполнена headless-проверка `load_system(...)`; модель загрузилась без ошибки (`SIMULINK_MODEL_LOAD_OK`).
