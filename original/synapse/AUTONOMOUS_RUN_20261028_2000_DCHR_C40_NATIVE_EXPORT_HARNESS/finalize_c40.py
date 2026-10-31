"""Idempotent evidence event for isolated C40 MATLAB export harness, not native parity."""
from __future__ import annotations
import datetime as dt,hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).resolve().parent;SCC=H.parent.parent
DCHR=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c40-native-export-harness-20261028-2000"
FILES=["c40_export_warm45_v2.m","c40_compare_native.py","c40_static_qa.py",
 "C40_HARNESS_SELFTEST.json","C40_STATIC_QA.json","C40_ENGINEERING_NOTE_SK.md","finalize_c40.py"]
NEXT=("When STOP/ownership clear and free RAM >=5 GiB, execute isolated MATLAB R2026a "
 "c40_export_warm45_v2; then run c40_compare_native.py against native CSV and "
 "validate 8760x22 fields before any Stateflow v85 or physical parity claim.")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def immutable(name,obj):
 p=H/name;raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
 if p.exists():
  if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
 else:
  with p.open("xb") as f:f.write(raw)
 return sha(p)
def guard():
 for root in (SCC,SCC/"recovery",SCC/"Continuity",DCHR,H):
  for n in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
   if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def main():
 guard()
 s=json.loads((H/"C40_STATIC_QA.json").read_text(encoding="utf-8"))
 q=json.loads((H/"C40_HARNESS_SELFTEST.json").read_text(encoding="utf-8"))
 assert s["status"]=="PASS" and s["passed"]==16 and all(s["checks"].values())
 assert q["status"]=="PASS" and q["self_tests"]==6
 assert q["self_identity_comparisons"]==192720
 assert s["native_execution_admitted"] is False and s["native_executed"] is False
 assert q["native_parity_verified"] is False
 assert not (H/"Warm45_Storage100_v2_MATLAB_NATIVE.csv").exists()
 assert all((H/f).is_file() for f in FILES)
 manifest_sha=immutable("SHA256_MANIFEST_C40.json",{"files":{f:sha(H/f) for f in FILES},"count":len(FILES)})
 evidence={"scope":"DCHR_C40_NATIVE_EXPORT_HARNESS",
  "artifact_directory":str(H),"manifest_sha256":manifest_sha,
  "matlab_source_sha256":s["matlab_source_sha256"],
  "qa":"16/16 static contract checks, 6/6 comparator self-tests PASS",
  "self_identity_comparisons":q["self_identity_comparisons"],
  "resource_gate_free_ram_gib":s["free_ram_gib"],"resource_gate_min_gib":s["min_ram_for_native_gib"],
  "native_matlab_executed":False,"native_parity_verified":False,
  "source_files_modified":False,"shared_csv_modified":False,
  "stateflow_parity_verified":False,"physical_validation":False,
  "primary_source_signoffs":0,"next_step":NEXT}
 evidence_sha=immutable("EVIDENCE_C40.json",evidence)
 payload=dict(evidence,evidence_sha256=evidence_sha)
 guard()
 with sqlite3.connect(SCC/"tasks.sqlite3",timeout=10) as db:
  db.execute("PRAGMA busy_timeout=10000")
  assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  db.execute("BEGIN IMMEDIATE")
  row=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
  if not row or row[0]!="DataCenter Heat Reuse" or row[1] in ("done","cancelled") or row[2] is not None:
   raise RuntimeError("TASK_NOT_ELIGIBLE "+str(row))
  prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
  if prior:
   if len(prior)!=1 or json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
   event_id,state=prior[0][0],"ALREADY_RECORDED"
  else:
   event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,sort_keys=True,ensure_ascii=False))).lastrowid
   state="RECORDED"
  db.commit()
  assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 handoff=H/"FINAL_HANDOFF.md"
 if not handoff.exists():
  lines=["# DCHR C40 — isolated native MATLAB Warm45 v2 export harness",
   "Verified local: "+dt.datetime.now().astimezone().isoformat(timespec="seconds"),"",
   "Runnable isolated MATLAB R2026a function created. Does not call destructive run_experiment_v2.",
   "Comparator supports strict 8760 rows, 23 columns, 192720 numeric comparisons.",
   "QA: 16/16 static contract checks, 6/6 comparator tests PASS; self-identity is not MATLAB proof.",
   "MATLAB NOT RUN due free RAM "+str(s["free_ram_gib"])+" GiB < "+str(s["min_ram_for_native_gib"])+" GiB guard.",
   "No source/SLX/shared CSV, VRS, OAuth, GUI, worker, Codex or GPU changes.",
   "Existing task "+TASK+" event #"+str(event_id)+"; task remains queued, no worker.",
   "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task="+TASK,
   "Artifact: "+str(H),"Manifest SHA256: "+manifest_sha,
   "Evidence SHA256: "+evidence_sha,"Next: "+NEXT,""]
  with handoff.open("x",encoding="utf-8") as f:f.write("\n".join(lines))
 immutable("REGISTRY_RESULT_C40.json",{"task_id":TASK,"event_id":event_id,
  "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
  "handoff_sha256":sha(handoff)})
 print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
  "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
  "handoff_sha256":sha(handoff)},ensure_ascii=False))
if __name__=="__main__":main()
