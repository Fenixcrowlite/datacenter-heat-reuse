# DataCenter Heat Reuse — MASTER STAGEBOARD v0.6
Дата: 2026-10-08. Источник истины для продолжения: этот файл, source_catalog.md, audit/literature_traceability_v05.csv и STATUS_v06.json.
Принцип: нельзя объявлять research/validation DONE без первоисточника, уравнений, физических границ, тестов и сохранённых артефактов.

## Правила работы
- Прежние модели v0.3/v0.4, результаты и презентации не перезаписывать; новое сохранять в v0.6+.
- Этапы выполнять автоматически в порядке зависимостей; при блокере переходить к независимому фрагменту, а не подменять источники предположениями.
- Единая система СИ и MW/MWh, фиксированные знаки потоков, размерности при каждом преобразовании.
- Для каждой публикации сохранять библиографию/DOI/доступный текст, формулы с страницей/таблицей, единицы, границы системы, фактические числа, допущения, связь с будущим блоком модели, доступность исходных данных и уровень надёжности.
- Слова «измерено», «взято из литературы», «реконструировано нами», «сценарное допущение» нельзя смешивать.
- Количественные литературные результаты сравнивать только при одинаковой топологии, границах модели и нормировке.
- Любой готовый этап должен иметь evidence: файл + воспроизводимая проверка + заметка о расхождениях.
- Состояние и следующий этап хранить в STATUS_v06.json, а не полагаться на память чата.

## Этапы и критерии выхода
### M0 — Инвентаризация и карантин старого baseline — DONE
Evidence: найден первичный PDF C:\Users\Lysda\Downloads\Telegram Desktop\Datacentra_teplo_vedecke_prace.pdf (4 стр, список 31).
Evidence: два полнотекстовых первоисточника в sources/papers/, audits v0.5, MATLAB / Simulink baseline.
Результат: старую модель не изменять; v0.4 не является точной репликацией Frankfurt.

### M1 — Аудит ВСЕХ 31 источников — IN_PROGRESS (0/31 fully signed off; №1/17 core audits, №4/21 partial)
На каждую работу: verified DOI; оригинал/ссылка; конкретные математические уравнения, их область применимости; результаты и данные; quality (full/abstract/restricted); действия model-use/advisory/skip.
Подэтап M1A (сначала): №1 Wahlroos и №17 Jürgens имеют подробные, но ещё не полностью закрытые аудиты v0.5; 21 Ebrahimi (охлаждение), 18 Oró (air cooling), 20 Verzino (Varna) и 23 Yuan 2025.
Подэтап M1B: первичные физические/экономические исследования 2–6, 11–16, 19, 22,24.
Подэтап M1C: review/business/regulation/case №7–10,25–31.
Не все статьи содержат свою математическую модель; честно отмечать 'no equations applicable'.
GATE: матрица 31/31, хотя бы full primary verification для каждого доступного; paywall/blocker отмечены отдельно.

### M2 — Единая независимая математическая спецификация — PENDING
Граф границ: IT→DC cooling→HX→HP→DH→consumer; TES и gas; позже economics/exergy.
Для каждой формулы: физическое происхождение, единицы, знак, границы, параметр A/B/C/D, тест и связь с опубликованной формулой.
Три НЕ смешиваемых ветки: Frankfurt short TES, Espoo economics/CHP, Varna seasonal TCS.
GATE: математические и размерностные проверки на бумаге/в независимом коде, открытые источники допущений.

### M3 — Независимая reference physics + property tests — PENDING
Тесты HX energy/pinch, HP COP/first-law/source limit/part-load, TES SOC / loss / no simultaneous charge/discharge, DH heat/loss, finite boiler/unmet demand, closed annual balance, negative/zero/boundary.
Точность double и tolerance заранее заданы; две независимые реализации для контрольных случаев.
GATE: машинный отчёт с точными входами и минимум 1 экстремальным тестом для каждого блока.

### M4 — Frankfurt faithful replication — PENDING
Цели: 144 GWh/a sold, ~152 GWh/a into network, HP ~148 GWh, gas ~4 GWh, 37/20 MW, TES 82 MWh, source 25/15C, DH 70/50→80/50C; -10C artificial stress day.
Реконструировать SigLinDe, отделить опубликованное от предположенного; не калибровать и затем выдавать fitted KPI за независимый prediction.
GATE: таблица reproduced/not reproduced/unverifiable с объяснением каждой причины.

### M5 — MATLAB code implementation — PENDING
Новая модульная v0.6, unit/CI smoke, сравнение reference, scenario / Monte Carlo / sensitivity. Не менять старые файлы.
GATE: run_full_study_v06.m и воспроизводимые таблицы с едиными входами/хешами.

### M6 — Simulink physics blocks — PENDING
DC/HX/HP/DHN/TES/gas, signal units, time step/sample times, numerical solver; реальные исполняемые блоки вместо иллюстративной картинки.
GATE: compare MATLAB ↔ Simulink on identical datasets, energy residual checks + outputs.

### M7 — Stateflow supervisory control — PENDING
Режимы NORMAL, CHARGE, DISCHARGE, BOILER, CURTAIL, FAULT; диаграмма состояний, guards, conditions; физика только в Simulink.
GATE: transition coverage + аварийные/пограничные тесты и отсутствие конфликтующих команд.

### M8 — независимая validation / economics / exergy — PENDING
Frankfurt, Espoo, Varna separate cases; manufacturer/real weather/loads where available; sensitivity; calibration vs hold-out; error bars.
GATE: residuals, uncertainties, source-to-output tables, admitted limitations.

### M9 — Presentation & integration — PENDING
Реальные кадры MATLAB-кода, Simulink, Stateflow, тестовых графиков, формул с номером статьи/страницы; визуально разъяснить цепочку физики и всё сопоставление.
Финальная PPTX + PDF, проводник/просмотр на ПК; копии в OneDrive и Obsidian в структуре дисциплины.
GATE: показ/открытие презентации и перечень файлов + тестовый запуск + итоговый отчёт.

## Рассылка этапов
Не заявлять о непрерывной автономной работе вне реально запущенных процессов. Автоматическое задание ChatGPT пока НЕ создано: достигнут лимит 5 активных задач. Пока отчёты по этапам передавать в чат при фактическом завершении работы в активном запуске. Альтернативное напоминание возможно только после освобождения слота пользователем или согласованной замены.


## Промежуточная точка v0.7, 08.10.2026
- Исправлено неверное извлечение Sintong Eq24: коэффициент 0.97 УМНОЖАЕТ Pcomp, не делит. Eq17/22/24 визуально сверены по PDF стр.32–33.
- Проверенный независимый reference kernel: audit/reference_physics_v07.py, 11/11 тестов, 1500 random + 8760h synthetic.
- Проверка формул Sintong (crossflow, знаки, losses): audit/sintong_equations_v07.py, 9/9 тестов, 1000 random.
- audit/Independent_First_Law_v07_RU.md: математическая спецификация для reference.
- **Этап M1 НЕ завершен. M2/M3 тоже НЕ завершены целиком; v0.7 является прототипом.**


## Частичный аудит Varna (№20), контрольная точка v0.8
- Оригинал 27 стр. получен, локально: sources/papers/20_Verzino_Varna_2026.pdf.
- Стр.16 оригинала подтверждает таблицу S1 FC/AC и конфликт единиц газа: 9122 Sm3 вместо порядка 9.11 млн Sm3 при 97522 MWh (требует комментария авторов).
- VCC1→VCC2→TCS→VCC3→DHN; FC во время сценарного восстановления тепла отключает AC; нельзя смешивать с Frankfurt TES.
- Проверки Varna: 8 базовых + 4 размерностных PASS; research SIGNOFF=NО.
- Итого новая серия: 11 reference + 9 Sintong + 8 Varna + 4 gas = 32/32 PASS. 2500 randomized scenarios; один синтетический 8760h энергетический цикл.
- Статус / исходники: STATUS_v08.json, audit/literature_traceability_v08.csv.


## Automation v0.9 — ACTIVE
- Старый истёкший PC Overnight Run переведён в hourly condition-watch DataCenter Heat Reuse: этапы.
- ID 6ac577fb64b081918f271322566b3e24. Прогресс только по воспроизводимым файлам и тестам, без заявлений о непрерывном background runtime.
- Источник истины последнего состояния STATUS_v09.json.
