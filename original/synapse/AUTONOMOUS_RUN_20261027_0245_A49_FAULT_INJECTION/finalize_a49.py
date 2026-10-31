"""Fail-closed, idempotent A49 evidence registration into EXISTING Synapse card."""
from pathlib import Path
import hashlib, json, sqlite3, subprocess, sys, time
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a49-independent-fault-injection-20261027-0245"
PY=sys.executable
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(path, content):
 if path.exists():
  if path.read_text(encoding="utf-8-sig")!=content:
   raise RuntimeError("ARTIFACT_CONFLICT "+str(path))
 else:
  path.write_text(content,encoding="utf-8")
def guard():
 roots=[CENTER,CENTER/"recovery",CENTER/"Continuity",
        Path(r"C:\Users\Lysda\Desktop\temp_coding"),
        Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
        Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")]
 for root in roots:
  for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/name).exists(): raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
 guard()
 report=json.loads((D/"A49_AUDIT_RESULT.json").read_text(encoding="utf-8-sig"))
 if (report["status"]!="A49_INDEPENDENT_LEDGER_AND_FAULT_INJECTION_PASS"
     or report["physical_release"] or report["matlab_a49_executed"]
     or len(report["baseline"])!=7 or len(report["randomized_trials"])!=24
     or len(report["mutation_probes_detected"])!=5 or len(report["zero_cap_trip_indices"])!=9):
  raise RuntimeError("AUDIT_REPORT_FAILED")
 result=subprocess.run([PY,"-B",str(D/"test_a49.py")],capture_output=True,
                       text=True,encoding="utf-8",errors="replace",timeout=45)
 if result.returncode or "Ran 9 tests" not in result.stderr or "\nOK" not in result.stderr:
  raise RuntimeError("QA_FAILED "+result.stderr)
 if (D/"QA_LOG.txt").exists():
  saved=(D/"QA_LOG.txt").read_text(encoding="utf-8-sig")
  if "Ran 9 tests" not in saved or "\nOK" not in saved: raise RuntimeError("QA_LOG_INVALID")
 else: put(D/"QA_LOG.txt",result.stdout+result.stderr)
 model=D.parent/"AUTONOMOUS_RUN_20261027_0150_A48_EXECUTABLE_QA"/"DCHR_A48_Graphical_Closed_Loop.slx"
 if sha(model)!="063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb":
  raise RuntimeError("A48_UPSTREAM_CHANGED")
 evidence={
  "task_id":TASK,"status":"A49_SYNTHETIC_FAULT_INJECTION_QA_PASS",
  "artifact_directory":str(D),"source_a48_sha256":sha(model),
  "audit_source_sha256":sha(D/"a49_independent_audit.py"),
  "audit_result_sha256":sha(D/"A49_AUDIT_RESULT.json"),
  "tests":"9/9 PASS","baseline_scenarios":7,"randomized_trials":24,
  "mutation_probes_detected":5,"zero_capacity_trip_latency_cases":9,
  "independent_checks":["IT heat","HP heat","user heat","TES storage","temperature",
                        "sensor latency","REJECT ramp","HP compressor lag"],
  "matlab_a49_executed":False,"synthetic_only":True,"physical_release":False,
  "limits":"A49 is Python-only synthetic fault injection; no new MATLAB/Simulink run, no physical safety certification.",
  "next_step":"A50: run selected sensor-lag and trip-delay fault injections against graphical A48 Stateflow in MATLAB, compare with independent A49 trace ledger; retain 31-source physical signoff gate."}
 put(D/"EVIDENCE_A49.json",json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
 names=["a49_independent_audit.py","test_a49.py","A49_AUDIT_RESULT.json","QA_LOG.txt","EVIDENCE_A49.json"]
 manifest={n:sha(D/n) for n in names}
 put(D/"SHA256_MANIFEST_A49.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 summary=(
  "# A49 synthetic fault-injection checkpoint | 2026-10-27\n"
  f"Existing Synapse task: {TASK}, status review/planned, no live worker asserted.\n"
  "QA: 9/9 unittest PASS; 7 baseline cases x 672 steps; 24 deterministic randomized demand/latency/HP trials x 160 steps; 5 deliberate corruption probes detected; 9 zero-capacity trip-delay cases checked.\n"
  "Independent trace ledger: IT, HP, user, TES, temperature, sensor lag, REJECT ramp and compressor lag.\n"
  "Full zero-capacity fault: trip indices 96,98,100 for synthetic delays 0,2,4 samples, independent of sensor lag 0,1,4 samples.\n"
  "Important: A49 Python-only. No new MATLAB/Simulink run or real equipment testing; physical validation and 31 primary-source signoffs remain BLOCKED.\n"
  f"Source SHA256: {sha(D/'a49_independent_audit.py')}\n"
  f"Result SHA256: {sha(D/'A49_AUDIT_RESULT.json')}\n"
  f"Evidence SHA256: {sha(D/'EVIDENCE_A49.json')}\n"
  f"Manifest SHA256: {sha(D/'SHA256_MANIFEST_A49.json')}\n"
  f"Unmodified A48 model SHA256: {sha(model)}\n"
  "No Codex, new worker, GPU job, GUI/OAuth/STOP change, VRS, or external side effects.\n"
  f"Next: {evidence['next_step']}\n"
 )
 put(D/"FINAL_HANDOFF.md",summary)
 payload={"scope":"A49_independent_fault_injection_and_ledger",
  "artifact_directory":str(D),"evidence_sha256":sha(D/"EVIDENCE_A49.json"),
  "manifest_sha256":sha(D/"SHA256_MANIFEST_A49.json"),
  "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
  "result_sha256":sha(D/"A49_AUDIT_RESULT.json"),
  "qa":"9/9 PASS; 7x672 baseline; 24x160 seeded variations; 5 mutations caught; 9 zero-capacity checks",
  "matlab_a49_executed":False,"physical_release":False,"next_step":evidence["next_step"]}
 db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
 db.execute("PRAGMA busy_timeout=10000")
 if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("DB_INTEGRITY")
 db.execute("BEGIN IMMEDIATE")
 try:
  row=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
  if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
  prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind=?",
                   (TASK,ACTOR,"evidence")).fetchall()
  if len(prior)>1:raise RuntimeError("DUPLICATE_EVENTS")
  if prior:
   if json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
   event_id=prior[0][0]
  else:
   event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                       (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:
  db.rollback();raise
 finally:db.close()
 put(D/"REGISTRY_RESULT_A49.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event_id,"tests":"9/9 PASS","result_sha256":payload["result_sha256"],
  "evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
