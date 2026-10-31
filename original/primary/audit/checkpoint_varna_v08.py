"""Varna v0.8 checkpoint: traceability + immutable outputs + checksum-verified Obsidian sync."""
from pathlib import Path
import json,hashlib,shutil,csv
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];audit=root/"audit"
expected=[("reference_physics_tests_v07.json","tests_run",11),
("sintong_equations_tests_v07.json","tests",9),
("varna_source_tests_v07.json","tests",8),
("varna_unit_sanity_v07.json","unit_gate_tests",4)]
for name,key,count in expected:
 p=audit/name
 if not p.exists():raise RuntimeError(f"Missing {name}")
 d=json.loads(p.read_text(encoding="utf8"))
 if d["status"]!="PASS" or d[key]!=count:raise RuntimeError("Test did not pass: "+name)
pdf=root/"sources/papers/20_Verzino_Varna_2026.pdf"
if not pdf.exists() or pdf.open("rb").read(4)!=b"%PDF":raise RuntimeError("Source 20 PDF unverified")
src=root/"audit/literature_traceability_v06.csv";target=root/"audit/literature_traceability_v08.csv"
with src.open(encoding="utf-8-sig",newline="") as f:
 r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
assert len(rows)==31
for row in rows:
 if row["id"]=="20":
  row["review_level"]="PARTIAL_PRIMARY_PDF_AND_PUBLISHER_HTML"
  row["fully_signed_off"]="NO"
  row["local_original_pdfs"]="20_Verzino_Varna_2026.pdf"
  row["primary_url_known"]="https://doi.org/10.3390/en19030800"
  row["equations_transcribed"]="PARTIAL_1_to_20"
  row["paper_replicated"]="NO"
  row["blockers"]="Original full PDF obtained, but hourly raw DHN data unavailable; exact exergy sign validation open; publisher PDF p16 printed 9122 Sm3 for 97522 MWh, inconsistent by ~1000x; author clarification pending"
with target.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
d=json.loads((root/"STATUS_v07.json").read_text(encoding="utf8"))
d["version"]="0.8";d["updated_utc"]=datetime.now(timezone.utc).isoformat()
d["source20_varna"]={
 "review":"PARTIAL_PRIMARY_PDF_AND_PUBLISHER_HTML","original_pdf":"sources/papers/20_Verzino_Varna_2026.pdf",
 "page16_table6_checked":True,"gas_volume_unit_discrepancy_confirmed_in_print":True,
 "printed": {"thermal_energy_MWh_y":97522,"gas_volume_Sm3":9122,"gas_specific_kWh_per_Sm3":10.7},
 "tests": {"paper_unit_preflight":8,"gas_dimension":4},
 "remaining":["source eq8-20 detailed exergy sign audit","raw hourly operator data","author gas unit clarification"]}
for ms in d["milestones"]:
 if ms["id"]=="M1":
  ms["partial_review"]=sorted(set(ms.get("partial_review",[])+[20]))
  ms["original_pdfs_local"]=7
  ms["fully_closed"]=[]
d["next"]=["M1 continue 31 source primary audits, prioritize №18 Oró, №23 Yuan, №21 Ebrahimi full review",
 "M1 source №20 exergy symbols Eq 9–20 and unit mismatch require further confirmation",
 "M2/M3 independent mathematics not complete; 32 source/reference proof checks passed, not paper replications",
 "MATLAB, Simulink, Stateflow only after M1/M2/M3 validation gate"]
(root/"STATUS_v08.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf8")
(root/"MASTER_STAGEBOARD_v08.md").write_text((root/"MASTER_STAGEBOARD_v07.md").read_text(encoding="utf8")+
 "\n\n## Частичный аудит Varna (№20), контрольная точка v0.8\n"
 "- Оригинал 27 стр. получен, локально: sources/papers/20_Verzino_Varna_2026.pdf.\n"
 "- Стр.16 оригинала подтверждает таблицу S1 FC/AC и конфликт единиц газа: 9122 Sm3 вместо порядка 9.11 млн Sm3 при 97522 MWh (требует комментария авторов).\n"
 "- VCC1→VCC2→TCS→VCC3→DHN; FC во время сценарного восстановления тепла отключает AC; нельзя смешивать с Frankfurt TES.\n"
 "- Проверки Varna: 8 базовых + 4 размерностных PASS; research SIGNOFF=NО.\n"
 "- Итого новая серия: 11 reference + 9 Sintong + 8 Varna + 4 gas = 32/32 PASS. 2500 randomized scenarios; один синтетический 8760h энергетический цикл.\n"
 "- Статус / исходники: STATUS_v08.json, audit/literature_traceability_v08.csv.\n",
 encoding="utf8")
files=["MASTER_STAGEBOARD_v08.md","STATUS_v08.json",
 "audit/literature_traceability_v08.csv",
 "audit/Varna_Verzino_2026_primary_source_audit_v07_RU.md",
 "audit/Varna_unit_discrepancy_v07_RU.md",
 "audit/varna_source_preflight_v07.py","audit/varna_source_tests_v07.json",
 "audit/varna_unit_sanity_v07.py","audit/varna_unit_sanity_v07.json",
 "audit/Varna_p16_gas_table_visual_v08.png",
 "audit/fetch_varna_source_v08.py","audit/varna_pdf_acquisition_v08.json",
 "sources/papers/20_Verzino_Varna_2026.pdf"]
obs=Path(r"C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse")
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1<<20),b""):h.update(part)
 return h.hexdigest()
result=[]
for f in files:
 a=root/f;b=obs/f
 if not a.exists():status="SOURCE_MISSING"
 elif b.exists():status="IDENTICAL" if sha(a)==sha(b) else "CONFLICT_SKIPPED"
 else:
  b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
  status="COPIED" if sha(a)==sha(b) else "CHECKSUM_FAIL"
 result.append({"file":f,"status":status})
report={"run_utc":datetime.now(timezone.utc).isoformat(),"files":result}
(root/"integration/obsidian_v08_sync_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps({"status":"DONE" if all(v["status"] in ("COPIED","IDENTICAL") for v in result) else "PROBLEM",
 "test_count":sum(x[2] for x in expected),"sync_counts":{x:sum(r["status"]==x for r in result) for x in set(r["status"] for r in result)},
 "pdf_bytes":pdf.stat().st_size},ensure_ascii=False))
