# -*- coding: utf-8 -*-
"""Immutable packaged handoff of whole observability and standards research branch."""
from pathlib import Path
from hashlib import sha256
import zipfile,json
root=Path(__file__).resolve().parent
project=root.parent.parent
qa=json.loads((root/"QA_OBSERVABILITY_STANDARDS_20261023.json").read_text(encoding="utf-8"))
sync=json.loads((root/"OBSIDIAN_OBSERVABILITY_MANIFEST.json").read_text(encoding="utf-8"))
assert qa["chart_png_and_svg"]==20 and qa["KPI"]==34 and qa["standards"]==56
assert qa["signal_contract_fields"]==14 and qa["usecases"]==36
assert qa["software_PASS"]==22 and qa["physically_BLOCKED"]==14
assert sync["verified"]==sync["total"]==61
intro=[
"# DataCenter Heat Reuse | графики, метрики, стандартизация, юзкейсы",
"",
"Дата: 2026-10-23. Это численно проверенное исследование, НЕ инженерное разрешение на строительство, не сертификат и не телеметрия реального дата-центра.",
"",
"## Как открывать",
"- Интерактивная HTML-панель: Engineering_Dashboard_2026.html (открыть в браузере).",
"- PDF на русском: Standards_Graphs_Usecases_RU.pdf (15 страниц).",
"- PDF на словацком: Standards_Graphs_Usecases_SK.pdf (14 страниц).",
"- PDF на английском: Standards_Graphs_Usecases_EN.pdf (14 страниц).",
"- Графики: charts (20 PNG + 20 масштабируемых SVG).",
"- Все показатели: kpi_catalog_2025.csv + JSON.",
"- Нормативы: standards_traceability_2026.csv (56 требований, 22 дисциплины).",
"- Матрица требований и тестов: requirements_tests_metrics_traceability.csv.",
"- Юзкейсы: use_case_catalog_2026.csv (36; 22 PASS численно, 14 BLOCKED).",
"- Стандартизованные сигналы: signal_dictionary_300s.csv (14 полей и единицы).",
"- Воспроизведение: build_observability.py, build_standards_register.py, build_usecases.py, build_traceability_links.py.",
"",
"## Основные ограничения",
"1. PUE=1.36 и ERF source proxy относятся к синтетическому IT; нормативные ERF, WUE, REF отсутствуют без счётчиков.",
"2. Проверка до 27.8 °C только численная: полный правовой статус бассейна, датчики и независимая защита не подтверждены.",
"3. Полные тексты лицензируемых стандартов STN не проанализированы; все 56 пунктов имеют статус UNVERIFIED, а не COMPLIANT.",
"4. Реальные COP(Tsource, Tsink, PLR), теплообменники, насосные характеристики, гидравлика и аварийный UPS не проверены.",
"5. Для физического строительства необходимы подписи ответственного проектировщика, заводской подбор и FAT/SAT.",
"",
"## Независимая QA",
"Выполнено: 420480 пятиминутных отсчётов / 4 сценария; 20 SVG проходят XML-разбор и соответствуют PNG; 34 KPI с единицами;",
"все PDF проверены на выход текста за страницу, HTML JS синтаксически проверен, юзкейсы 22 PASS без FALSE COMPLIANCE.",
"",
"## Где в Obsidian",
"calibration/observability_standards_usecases_20261023/00_Observability_Standards_UseCases_SK.md",
"calibration/observability_standards_usecases_20261023/00_Observability_Standards_UseCases_RU.md",
]
(root/"README_START_RU.md").write_text("\n".join(intro)+"\n",encoding="utf-8")
package=project/"OBSERVABILITY_STANDARDS_USECASES_20261023.zip"
if package.exists():raise FileExistsError("Preserve original zip, use new version")
files=[p for p in root.rglob("*") if p.is_file() and
  "slprj" not in p.parts and "__pycache__" not in p.parts]
with zipfile.ZipFile(package,mode="x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:
  z.write(p,arcname="observability_standards_usecases_20261023/"+str(p.relative_to(root)).replace("\\","/"))
with zipfile.ZipFile(package,"r") as z:
 assert z.testzip() is None
 names=z.namelist()
 assert sum(q.endswith(".pdf") for q in names)==3
 assert sum(q.endswith(".svg") for q in names)==20
 assert sum(q.endswith(".png") for q in names)>=20
report={"date":"2026-10-23","archive":str(package),"bytes":package.stat().st_size,
        "members":len(files),"SHA256":sha256(package.read_bytes()).hexdigest(),
        "zip_integrity":"PASSED","Obsidian_mirror_verified":61,"status":"VERIFIED_RESEARCH_NOT_CERTIFIED"}
(root/"ARCHIVE_OBSERVABILITY_VERIFIED.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
handoff=project/"CALIBRATION_HANDOFF_20261023.md"
text="""

## Research observability, standards and use cases | 23.10.2026

**OWNED BRANCH:** calibration/observability_standards_usecases_20261023 (isolated; prior models and parallel pool branch NOT changed).
- 20 independent charts as PNG+SVG based on executed 2025 300-second Simulink outputs, with source chart manifest.
- 34 KPIs with units, equations, model vs measured provenance; official PUE, ERF, WUE, REF NOT available without actual physical metering; synthetic PUE assumed 1.36.
- 14 normalized signal definitions, 300-second samples in UTC, 420480 data points across four annual cases pass allocation and thermal partition test.
- 56 standard traceability requirements across 22 disciplines; catalog references rechecked including latest ISO/IEC 30134-2:2026 and ISO 9001:2026; effective Slovak pool public standards STN EN 15288-1+A1:2024 / 15288-2:2019. Full licensed STN text NOT available or reviewed; all entries UNVERIFIED, not certified.
- 36 use cases with explicit input expected response, result, source and priority: 22 SOFTWARE PASS, 14 BLOCKED real measurements/hardware/legal verification; no false compliance claims.
- 56-entry cross-links standard -> relevant use case -> KPI -> missing evidence (requirements_tests_metrics_traceability.csv).
- Standalone offline dashboard HTML with plot selection and interactive filters, 20 PNG+SVG, all supporting JSON/CSV.
- Trilingual reports Standards_Graphs_Usecases_SK/RU/EN.pdf, 14/15/14 pages; PDF coordinate QA zero clipped words; all charts SVG parse and HTML script node syntax PASS.
- Obsidian calibration/observability_standards_usecases_20261023 has 61 SHA256-matched files; no collision.
- Immutable project ZIP OBSERVABILITY_STANDARDS_USECASES_20261023.zip, verified integrity.
- NEXT P0: obtain real IT electrical/thermal and WUE/ERF meters, OEM heat-pump and exchanger COP curves, hydronic/electrical UPS P&ID/SLD, hardware-in-the-loop & FAT/SAT, applicable current consolidated law/full license norms, signed independent safety case.

No autonomous background executor was started. STOP, ownership and OAuth boundaries respected.
"""
with handoff.open("a",encoding="utf-8") as f:f.write(text)
print("OBSERVABILITY_RELEASE_ARCHIVED_VERIFIED",json.dumps(report,ensure_ascii=False))
