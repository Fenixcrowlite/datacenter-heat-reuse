# -*- coding: utf-8 -*-
"""Proposed requirements -> tests -> KPI links. They DO NOT establish standards conformance."""
from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent
std=json.loads((P/"standards_traceability_2026.json").read_text(encoding="utf-8"))
uc=json.loads((P/"use_case_catalog_2026.json").read_text(encoding="utf-8"))
kpi=json.loads((P/"kpi_catalog_2025.json").read_text(encoding="utf-8"))
cases={x["id"]:x for x in uc};metrics={x["id"]:x for x in kpi}
lookup={
"DC Energy":("UC-027,UC-028,UC-029,UC-030","PUE_assumed,ERF_reportable,WUE_reportable"),
"Data Center":("UC-001,UC-009,UC-010","E_recovered_source,E_rejected_IT"),
"IT Cooling":("UC-010,UC-019,UC-020,UC-021,UC-025,UC-036","Cooling_design_duty,Cooling_thermal_flow_at_5K"),
"Heat Pump":("UC-005,UC-006,UC-014,UC-015","SCOP_district_model,Electric_district_HP35"),
"Pool Design":("UC-002,UC-003,UC-034","Pool_peak_temperature,Pool_volume_m3"),
"Pool Operation":("UC-003,UC-004,UC-034","Pool_hours_above_28"),
"Pool Equipment":("UC-011,UC-033,UC-034","Pool_peak_temperature,Heat_pool_direct"),
"Pool Law":("UC-003,UC-004,UC-034","Pool_hours_above_28"),
"Pool Water":("UC-004,UC-033,UC-034","Pool_peak_temperature"),
"Pool Heating":("UC-002,UC-012,UC-013","Heat_pool_direct"),
"Pool Ventilation":("UC-012,UC-013","Heat_pool_direct"),
"HX":("UC-011,UC-033","Heat_pool_direct"),
"Hydraulics":("UC-011,UC-025","Cooling_thermal_flow_at_5K"),
"Thermal Storage":("UC-008,UC-017","TES_max_energy"),
"Water":("UC-029,UC-036","WUE_reportable"),
"Electrical":("UC-025,UC-026,UC-035","Cooling_design_duty"),
"Control":("UC-004,UC-017,UC-018,UC-024,UC-034","Pool_peak_temperature,Cooling_design_duty"),
"Metering":("UC-027,UC-028,UC-029","PUE_assumed,ERF_reportable,WUE_reportable"),
"Measurement":("UC-027,UC-028,UC-030","Source_overallocation_peak"),
"Environmental":("UC-029,UC-028","E_rejected_IT,WUE_reportable"),
"Business":("UC-031,UC-032","E_IT"),
"Operations":("UC-024,UC-030,UC-034,UC-035","Pool_peak_temperature")}
rows=[]
for r in std:
 c,m=lookup[r["domain"]]
 cids=c.split(",");mids=m.split(",")
 assert all(v in cases for v in cids)
 assert all(v in metrics for v in mids)
 case_pass=sum(cases[q]["status"]=="PASS" for q in cids)
 case_block=sum(cases[q]["status"]=="BLOCKED" for q in cids)
 rows.append({"std_id":r["id"],"standard_reference":r["standard_reference"],
 "discipline":r["domain"],"normative_status":r["compliance"],
 "suggested_use_case_ids":";".join(cids),"suggested_KPI_ids":";".join(mids),
 "simulation_tests_PASS":case_pass,"evidence_gaps_BLOCKED":case_block,
 "priority":r["priority"],"required_evidence":r["required_evidence"],
 "warning":"Software tests are not a demonstration of compliance to licensed standard text"})
with (P/"requirements_tests_metrics_traceability.csv").open("x",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(P/"requirements_tests_metrics_traceability.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
print("STANDARD_TRACEABILITY_CLOSED",len(rows),"requirements with valid usecases and KPI links")
