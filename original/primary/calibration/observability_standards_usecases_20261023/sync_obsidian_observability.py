# -*- coding: utf-8 -*-
from pathlib import Path
from hashlib import sha256
import json,shutil
P=Path(__file__).resolve().parent
dest=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\observability_standards_usecases_20261023")
if not dest.parent.is_dir():raise FileNotFoundError(dest.parent)
dest.mkdir(parents=True,exist_ok=True)
std=json.loads((P/"standards_traceability_2026.json").read_text(encoding="utf-8"))
uc=json.loads((P/"use_case_catalog_2026.json").read_text(encoding="utf-8"))
graphs=json.loads((P/"graph_manifest.json").read_text(encoding="utf-8"))
sk=["---","date: 2026-10-23","status: VERIFIED_SIMULATION_NOT_CERTIFIED",
"tags: [datacentrum, bazen, standardizacia, Simulink, use-cases]","---",
"# Observability DC - bazen: normy, grafy, testy",
"> [!warning] PUE a ERF sú len scenárové; platná zhoda so všetkými normami NIE JE preukázaná.",
"",
"## Interaktívny dashboard a správy",
"- [[Engineering_Dashboard_2026.html]] (otvoriť externým prehliadačom)",
"- [[Standards_Graphs_Usecases_SK.pdf]]",
"- [[Standards_Graphs_Usecases_RU.pdf]]",
"- [[Standards_Graphs_Usecases_EN.pdf]]",
"- [[kpi_catalog_2025.csv]] - 34 KPI, definície, jednotky, proveniencia",
"- [[standards_traceability_2026.csv]] - 56 normových požiadaviek",
"- [[use_case_catalog_2026.csv]] - 36 testovacích scenárov: 22 PASS, 14 BLOCKED",
"- [[requirements_tests_metrics_traceability.csv]] - naviazanie normy, testu a KPI",
"- [[signal_dictionary_300s.csv]] - 14 časových signálov",
"",
"## Grafy modelového roku 2025"]
for g in graphs:
 sk.extend(["### "+g["name"],"![[charts/"+g["png"]+"]]","[Otvoriť SVG](charts/"+g["svg"]+")"])
sk.extend(["","## Potrebné vstupy","- Skutočné 8760h E_IT, E_DC, E_REUSE a spotreba vody",
"- Certifikované výkony tepelného čerpadla Q(Tsource, Tsink, PLR), COP",
"- Reálna hydraulika, čerpadlá, nezávislé záložné chladenie",
"- Úplné STN a účinné právne predpisy, overenie autorizovaným projektantom",
"","## BLOCKED testovacie prípady"])
for u in uc:
 if u["status"]=="BLOCKED":sk.append("- "+u["id"]+": "+u["title"]+" -> "+u["expected_response"])
sk+=["","## Verejné zdroje",
"- [ISO/IEC 30134-2:2026](https://www.iso.org/standard/30134-2)",
"- [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)",
"- [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en)",
"- [ASHRAE liquid cooling classes](https://www.ashrae.org/technical-resources/topics-and-initiatives/ai-data-center/introduction-and-purpose)"]
(P/"00_Observability_Standards_UseCases_SK.md").write_text("\n".join(sk)+"\n",encoding="utf-8")
ru=["# Обзор DC: стандарты, графики, метрики, юзкейсы","",
"Статус: модель численно проверена, соответствие реального объекта стандартам не сертифицировано.",
"Готово: 20 PNG и 20 SVG, 34 KPI, 56 пунктов по 22 дисциплинам, 36 юзкейсов: 22 PASS и 14 BLOCKED.",
"Интерактивная панель: Engineering_Dashboard_2026.html.",
"Отчёты: Standards_Graphs_Usecases_SK.pdf, Standards_Graphs_Usecases_RU.pdf, Standards_Graphs_Usecases_EN.pdf.",
"","## Блокирующие проверки"]
for u in uc:
 if u["status"]=="BLOCKED":ru.append("- "+u["id"]+": "+u["title"]+"; требование: "+u["expected_response"])
ru+=["","Главная причина блокировки: нет фактической телеметрии и заводских характеристик, полных текстов стандартов, испытаний электрики, гидравлики и автоматических защит."]
(P/"00_Observability_Standards_UseCases_RU.md").write_text("\n".join(ru)+"\n",encoding="utf-8")
names=["00_Observability_Standards_UseCases_SK.md","00_Observability_Standards_UseCases_RU.md",
"Engineering_Dashboard_2026.html","Standards_Graphs_Usecases_SK.pdf","Standards_Graphs_Usecases_RU.pdf","Standards_Graphs_Usecases_EN.pdf",
"kpi_catalog_2025.csv","kpi_catalog_2025.json","monthly_kpis_2025.csv",
"standards_traceability_2026.csv","standards_traceability_2026.json",
"use_case_catalog_2026.csv","use_case_catalog_2026.json","use_case_test_results_2026.json",
"signal_dictionary_300s.csv","signal_dictionary_300s.json","machine_validation_gates.json",
"requirements_tests_metrics_traceability.csv","requirements_tests_metrics_traceability.json",
"graph_manifest.json","QA_OBSERVABILITY_STANDARDS_20261023.json"]
names+=["charts/"+g[k] for g in graphs for k in ("png","svg")]
records=[]
for name in names:
 a=P/name;b=dest/name
 assert a.is_file(),str(a)
 b.parent.mkdir(parents=True,exist_ok=True)
 h=sha256(a.read_bytes()).hexdigest()
 if b.exists():status="ALREADY_IDENTICAL" if sha256(b.read_bytes()).hexdigest()==h else "CONFLICT_UNCHANGED"
 else:shutil.copy2(a,b);status="COPIED"
 records.append({"file":name,"status":status,"identical":sha256(b.read_bytes()).hexdigest()==h})
manifest={"destination":str(dest),"total":len(records),"verified":sum(z["identical"] for z in records),
"conflicts":[z["file"] for z in records if not z["identical"]],"files":records}
(P/"OBSIDIAN_OBSERVABILITY_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("OBSIDIAN_OBSERVABILITY_VERIFIED",manifest["verified"],"/",manifest["total"],"conflicts",len(manifest["conflicts"]))
if manifest["conflicts"]:raise SystemExit(3)
