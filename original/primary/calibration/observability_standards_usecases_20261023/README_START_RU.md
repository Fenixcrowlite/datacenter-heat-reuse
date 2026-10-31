# DataCenter Heat Reuse | графики, метрики, стандартизация, юзкейсы

Дата: 2026-10-23. Это численно проверенное исследование, НЕ инженерное разрешение на строительство, не сертификат и не телеметрия реального дата-центра.

## Как открывать
- Интерактивная HTML-панель: Engineering_Dashboard_2026.html (открыть в браузере).
- PDF на русском: Standards_Graphs_Usecases_RU.pdf (15 страниц).
- PDF на словацком: Standards_Graphs_Usecases_SK.pdf (14 страниц).
- PDF на английском: Standards_Graphs_Usecases_EN.pdf (14 страниц).
- Графики: charts (20 PNG + 20 масштабируемых SVG).
- Все показатели: kpi_catalog_2025.csv + JSON.
- Нормативы: standards_traceability_2026.csv (56 требований, 22 дисциплины).
- Матрица требований и тестов: requirements_tests_metrics_traceability.csv.
- Юзкейсы: use_case_catalog_2026.csv (36; 22 PASS численно, 14 BLOCKED).
- Стандартизованные сигналы: signal_dictionary_300s.csv (14 полей и единицы).
- Воспроизведение: build_observability.py, build_standards_register.py, build_usecases.py, build_traceability_links.py.

## Основные ограничения
1. PUE=1.36 и ERF source proxy относятся к синтетическому IT; нормативные ERF, WUE, REF отсутствуют без счётчиков.
2. Проверка до 27.8 °C только численная: полный правовой статус бассейна, датчики и независимая защита не подтверждены.
3. Полные тексты лицензируемых стандартов STN не проанализированы; все 56 пунктов имеют статус UNVERIFIED, а не COMPLIANT.
4. Реальные COP(Tsource, Tsink, PLR), теплообменники, насосные характеристики, гидравлика и аварийный UPS не проверены.
5. Для физического строительства необходимы подписи ответственного проектировщика, заводской подбор и FAT/SAT.

## Независимая QA
Выполнено: 420480 пятиминутных отсчётов / 4 сценария; 20 SVG проходят XML-разбор и соответствуют PNG; 34 KPI с единицами;
все PDF проверены на выход текста за страницу, HTML JS синтаксически проверен, юзкейсы 22 PASS без FALSE COMPLIANCE.

## Где в Obsidian
calibration/observability_standards_usecases_20261023/00_Observability_Standards_UseCases_SK.md
calibration/observability_standards_usecases_20261023/00_Observability_Standards_UseCases_RU.md
