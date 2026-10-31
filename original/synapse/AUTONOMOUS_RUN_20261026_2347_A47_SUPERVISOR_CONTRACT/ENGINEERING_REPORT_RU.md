# DataCenter A47: контракт интеграции графического Stateflow
Статус: VERIFIED для проверки логики состояний; НЕ является готовой интеграцией Simulink.
Источники: неизменённые A44 graphical Stateflow, A46 Simulink EMChart, семь CSV A45.
Синтетические данные, физический safety-case отсутствует.

## Подтверждённый интерфейс A44 → A46
- fault = (nominal_cap_W <= 0) OR (T_start_C >= 42).
- recover = (nominal_cap_W > 0) AND (T_start_C < 36).
- ramp_done = (previous_active_it_W + 15000 >= requested_qdc_W - 1e-8).
- Важно: requested_qdc_W берётся из INPUTS_A41.csv, а НЕ из active_it_W или qit_W.
- Состояния: ACTIVE=0, TRIP_PENDING=1, TRIPPED=2, RAMPING=3.
- Stateflow transition guards выполняются до during actions.
- Длительность шага 900 с; двухшаговое ожидание аварийного отключения.

## QA
7 × 672 = 4704 совпадений состояний A44 reference ↔ A45/A46.
5/5 независимых unittest PASS, включая 4 оригинальных сценария A44 и отрицательный контроль.
При неверном ramp_done (использование фактической IT вместо заданной) было 53 расхождения.
Исправленный адаптер даёт 0 расхождений; исходные модели не изменены.

## Ограничения
Это Python pre-integration contract gate. Графическая диаграмма ещё НЕ подключена
к A46 Simulink. MATLAB/Simulink в этом запуске НЕ запускались.
Нужен A48: отдельная A44-equivalent Chart в новом SLX, убрать FSM из EMChart,
замкнуть обратную связь, проверить 7×672 численных траекторий и переходы.
