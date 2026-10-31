"""DCHR EU metrics isolated artifact -> existing source-audit task evidence."""
from __future__ import annotations
import hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).resolve().parent
CENTER=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-eu-metrics-boundary-20261028-0906"
FILES=["eu_dc_metrics.py","test_eu_dc_metrics.py","independent_qa.py",
 "DCHR_EU_METRICS_NOTE_SK.md","SYNTHETIC_EU_METRICS_SAMPLE.json",
 "QA_INDEPENDENT_DCHR_EU.json","UNITTEST_DCHR_EU.log","finalize_dchr_eu.py"]
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
MATRIX=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\audit\literature_traceability_v44.csv")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def immutable(n,obj):
 p=H/n
 raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
 if p.exists():
  if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT:"+n)
 else:
  with p.open("xb") as f:f.write(raw)
 return sha(p)
def main():
 for p in [CENTER/"STOP",CENTER/"PAUSE",CENTER/"STOP.txt",
           Path(r"C:\Users\Lysda\Desktop\temp_coding\STOP")]:
  if p.exists():raise RuntimeError("STOP_ACTIVE:"+str(p))
 q=json.loads((H/"QA_INDEPENDENT_DCHR_EU.json").read_text(encoding="utf-8"))
 s=json.loads(STATUS.read_text(encoding="utf-8-sig"))
 assert q["status"]=="PASS" and q["rational_identity_checks"]==4002
 assert q["unittest_passed"]==25 and q["full_primary_signoff"] is False
 assert s["full_primary_signoffs"]==0 and s["total_sources"]==31
 assert sha(STATUS)==q["source_status_v86_sha256"]
 assert sha(MATRIX)==q["source_literature_v44_sha256"]
 sample=json.loads((H/"SYNTHETIC_EU_METRICS_SAMPLE.json").read_text(encoding="utf-8"))
 assert sample["data_class"]=="SYNTHETIC_FIXTURE_NOT_MEASURED"
 assert sample["metrics"]["PUE"]=="1.2" and sample["metrics"]["ERF"]=="0.25"
 assert all((H/n).is_file() for n in FILES)
 manifest_sha=immutable("SHA256_MANIFEST_DCHR_EU.json",
   {"files":{n:sha(H/n) for n in FILES},"count":len(FILES)})
 next_step=("Integrate metered E_DC, E_IT, E_REUSE and water time series with explicit energy boundaries; "
   "independently verify the consolidated 2026 EU legislation and national transposition. "
   "Keep source #25 unsigned and 0/31 primary signoffs until full original legal text and applicability review. "
   "Do not equate pool heat-pump delivery with DC waste heat reused.")
 ev={"scope":"DCHR_EU_METRICS_BOUNDARY_AND_THRESHOLD_PROTOTYPE",
  "task_id":TASK,"actor":ACTOR,"artifact_directory":str(H),
  "qa":"25/25 unittest PASS; 4002/4002 independent rational checks PASS",
  "source_status_v86_sha256":sha(STATUS),"source_matrix_v44_sha256":sha(MATRIX),
  "synthetic_sample_only":True,"full_primary_signoff":False,
  "full_primary_signoffs_total":0,"production_modified":False,
  "legal_compliance_certified":False,
  "source_urls":[
    "https://eur-lex.europa.eu/eli/dir/2023/1791/oj/eng",
    "https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj/eng"],
  "manifest_sha256":manifest_sha,"next_step":next_step}
 evsha=immutable("EVIDENCE_DCHR_EU.json",ev)
 payload={"scope":ev["scope"],"artifact_directory":str(H),"qa":ev["qa"],
   "evidence_sha256":evsha,"manifest_sha256":manifest_sha,
   "source_status_v86_sha256":sha(STATUS),"full_primary_signoff":False,
   "production_modified":False,"next_step":next_step}
 with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=8) as db:
  db.row_factory=sqlite3.Row
  db.execute("PRAGMA busy_timeout=8000")
  assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  db.execute("BEGIN IMMEDIATE")
  task=db.execute("SELECT id,project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
  if not task or task["project"]!="DataCenter Heat Reuse" or task["status"] in ("done","cancelled") or task["worker_pid"] is not None:
   raise RuntimeError("TASK_NOT_ELIGIBLE")
  prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
  if prior:
   if len(prior)!=1 or json.loads(prior[0]["data_json"])!=payload:raise RuntimeError("EVENT_CONFLICT")
   eid=prior[0]["id"];state="ALREADY_RECORDED"
  else:
   eid=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
      (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False,sort_keys=True))).lastrowid
   state="RECORDED"
  db.commit()
  assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  assert db.execute("SELECT count(*) FROM task_events WHERE task_id=? AND actor=?",(TASK,ACTOR)).fetchone()[0]==1
 handoff=(f"# DCHR EU metrics | 2026-10-28 09:08 CET\n\n"
  "VERIFIED isolated Python calculator for PUE, ERF, REF, WUE and separate legal-threshold indicators; "
  "integrates hourly kW to kWh with Decimal arithmetic. "
  "25/25 unit tests PASS and 4002/4002 independent rational identity checks PASS.\n"
  "Synthetic sample PUE=1.2, ERF=0.25, REF=0.5, WUE=2 m3/MWh; NOT measured site data. "
  "EU Directive 2023/1791 Article 12 installed IT >=500 kW is a DIFFERENT threshold from Article 26 total rated input >1 MW.\n"
  "Official EUR-Lex excerpts reviewed 2026-10-28, but consolidated legal changes, national law and full primary PDF signoff NOT reviewed. "
  "Original STATUS_v86 and literature v44 unchanged, 0/31 source signoffs remain.\n"
  f"Existing Synapse task {TASK} remains QUEUED for full source audit; evidence event #{eid}.\n"
  f"Evidence SHA256: {evsha}\nManifest SHA256: {manifest_sha}\n"
  "Live resource snapshot 09:07 CET: RAM free 2.69 GiB, battery 66% unplugged; no new Codex/GPU/GUI worker. "
  "No VRS, OAuth, OneDrive source modification, publication, or paid action.\n"
  f"NEXT: {next_step}\n")
 hp=H/"FINAL_HANDOFF.md"
 if hp.exists():
  if hp.read_text(encoding="utf-8")!=handoff:raise RuntimeError("HANDOFF_CONFLICT")
 else:hp.write_text(handoff,encoding="utf-8")
 immutable("REGISTRY_RESULT_DCHR_EU.json",{"event_id":eid,"state":"RECORDED_OR_VERIFIED",
  "task_id":TASK,"evidence_sha256":evsha,"manifest_sha256":manifest_sha,
  "handoff_sha256":sha(hp),"full_primary_signoff":False})
 print(json.dumps({"state":state,"event_id":eid,"checks":4002,
  "unit_tests":25,"evidence_sha256":evsha,"manifest_sha256":manifest_sha,
  "handoff_sha256":sha(hp)},ensure_ascii=False))
if __name__=="__main__":main()
