# Обзор DC: стандарты, графики, метрики, юзкейсы

Статус: модель численно проверена, соответствие реального объекта стандартам не сертифицировано.
Готово: 20 PNG и 20 SVG, 34 KPI, 56 пунктов по 22 дисциплинам, 36 юзкейсов: 22 PASS и 14 BLOCKED.
Интерактивная панель: Engineering_Dashboard_2026.html.
Отчёты: Standards_Graphs_Usecases_SK.pdf, Standards_Graphs_Usecases_RU.pdf, Standards_Graphs_Usecases_EN.pdf.

## Блокирующие проверки
- UC-004: Overtemperature sensor offset; требование: Independent hardware trip keeps actual T<28C
- UC-010: Full heat-reuse system unavailable; требование: 10MW independent full IT cooling operates
- UC-011: Direct HX thermal approach; требование: Manufacturer delivers 150kW 35/32 vs 27.5/29.5
- UC-014: Manufacturers thermal map; требование: Actual signed COP and capacity rated at site PLR
- UC-015: Vendor-certified 10MW duty; требование: Nameplate at required water source and sink is adequate
- UC-025: UPS pump ride through; требование: Pump flow sustained, redundant electrical supply validated
- UC-026: Cooling switchgear single fault; требование: Power selectivity and N+1 UPS verified
- UC-027: DC energy efficiency reporting; требование: Report official PUE not model 1.36
- UC-028: Regulated energy reuse reporting; требование: Report E_REUSE/E_DC compliant with regulation
- UC-029: Water resource KPI; требование: Calculate WUE with meter and unit
- UC-033: Pool chlorinated water chemistry; требование: Corrosion rating signed by OEM and sampling
- UC-034: Pool water failsafe FAT/SAT; требование: Independent hardware trip before 28C
- UC-035: IT cooling all sinks lost; требование: Critical cooling hardware bypass start and server flow maintained
- UC-036: ASHRAE W class selection; требование: Choose compatible W17/W27/W32/W40/W45 or W+ from actual IT design

Главная причина блокировки: нет фактической телеметрии и заводских характеристик, полных текстов стандартов, испытаний электрики, гидравлики и автоматических защит.
