"""Idempotent A50 evidence checkpoint; existing Synapse card only."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a50-graphical-sensor-lag-20261027-0351"
SOURCE=D.parent/"AUTONOMOUS_RUN_20261027_0150_A48_EXECUTABLE_QA"/"DCHR_A48_Graphical_Closed_Loop.slx"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_once(p,content):
 if p.exists():
  if p.read_text(encoding="utf-8-sig")!=content:raise RuntimeError("CONFLICT "+str(p))
 else:p.write_text(content,encoding="utf-8")
def guard():
 for root in [CENTER,CENTER/"recovery",CENTER/"Continuity",
              Path(r"C:\Users\Lysda\Desktop\temp_coding"),
              Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
              Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")]:
  for n in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def main():
 guard()
 assert sha(SOURCE)=="063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb"
 r=json.loads((D/"MATLAB_A50_RESULT.json").read_text(encoding="utf-8-sig"))
 assert r["status"]=="A50_GRAPHICAL_SENSOR_LAG_PARITY_PASS" and r["comparisons"]==15840 and len(r["scenarios"])==6 and not r["physical_release"]
 qa=subprocess.run([sys.executable,"-B",str(D/"test_a50.py")],capture_output=True,text=True,timeout=30)
 assert qa.returncode==0 and "Ran 7 tests" in qa.stderr and "OK" in qa.stderr,qa.stderr
 assert "Ran 7 tests" in (D/"QA_LOG.txt").read_text(encoding="utf-8-sig")
 next_step="A51: vary trip-delay guard in an isolated graphical Stateflow copy (0/2/4 steps), independently compare 240-step trajectories and prove thermal/energy balances; keep physical validation and 31 source signoffs BLOCKED."
 ev={
  "task_id":TASK,"scope":"A50_graphical_stateflow_sensor_lag_fault_injection",
  "status":"A50_GRAPHICAL_SENSOR_LAG_PARITY_PASS",
  "artifact_directory":str(D),"model_sha256":sha(D/"DCHR_A50_Sensor_Lag.slx"),
  "a48_source_sha256":sha(SOURCE),"matlab_result_sha256":sha(D/"MATLAB_A50_RESULT.json"),
  "matlab_executed":True,"comparisons":15840,"cases":6,"steps_per_case":240,
  "python_tests":"7/7 PASS","sensor_lag_steps":[0,1,4],"trip_delay_steps":2,
  "trip_indices":{"neither":[98,98,98],"backup_only":[98,98,103]},
  "synthetic_only":True,"physical_release":False,
  "model_limitation":"Saved A50 SLX is a baseline copy of A48; sensor-lag blocks are inserted into an in-memory isolated copy for each MATLAB simulation, not persisted as six separate SLX files.",
  "next_step":next_step}
 write_once(D/"EVIDENCE_A50.json",json.dumps(ev,ensure_ascii=False,indent=2)+"\n")
 names=["make_references.py","run_a50.m","test_a50.py","MATLAB_A50_RESULT.json","REFERENCE_MANIFEST.json","QA_LOG.txt","DCHR_A50_Sensor_Lag.slx","EVIDENCE_A50.json"]+[f"REF_{scenario}_lag{lag}.csv" for scenario in ("neither","backup_only") for lag in (0,1,4)]
 manifest={n:sha(D/n) for n in names}
 write_once(D/"SHA256_MANIFEST_A50.json",json.dumps(manifest,indent=2)+"\n")
 handoff=(
  "# A50 graphical Stateflow sensor-lag integration | 2026-10-27 03:51-04:00 CET\n"
  f"Existing Synapse task {TASK}; no new task/worker. Primary SynapseMCP Web initially ONLINE, then timed out; Ngrok authorized fallback used after verifying live ping. Desktop Commander unavailable due usage limit.\n"
  "MATLAB R2026a executed six synthetic fault-injection scenarios: neither and backup_only x sensor lag 0/1/4 samples, 240 steps each, 11 channels, 15840 numeric parity comparisons PASS vs independent Python A45.\n"
  "First TRIPPED zero-based indices: neither 98/98/98; backup_only 98/98/103. Extra 60-minute sensor delay postpones backup_only trip by five 15-minute samples, a modeled safety-relevant behavior. Zero REJECT interlock remains independent of sensor lag.\n"
  "7/7 independent Python acceptance tests PASS; MATLAB script initially had argument quoting and chained-indexing errors, corrected and rerun to completion.\n"
  "A50 saved SLX is a baseline isolated A48 copy; sensor lag is injected in memory during each run. Graphical Stateflow is the supervisor; no physical equipment or external control.\n"
  f"A48 SHA256 unchanged: {sha(SOURCE)}\n"
  f"A50 SLX SHA256: {sha(D/'DCHR_A50_Sensor_Lag.slx')}\n"
  f"Evidence SHA256: {sha(D/'EVIDENCE_A50.json')}\n"
  f"Manifest SHA256: {sha(D/'SHA256_MANIFEST_A50.json')}\n"
  "No Codex, new worker, GPU render, GUI/OAuth/STOP change or VRS. Physical release BLOCKED.\n"
  f"NEXT: {next_step}\n")
 write_once(D/"FINAL_HANDOFF.md",handoff)
 payload={
  "scope":ev["scope"],"artifact_directory":str(D),
  "model_sha256":ev["model_sha256"],"result_sha256":ev["matlab_result_sha256"],
  "evidence_sha256":sha(D/"EVIDENCE_A50.json"),
  "manifest_sha256":sha(D/"SHA256_MANIFEST_A50.json"),
  "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
  "qa":"MATLAB 6x240, 15840/15840 numeric parity; Python 7/7 PASS",
  "physical_release":False,"next_step":next_step}
 db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
 db.execute("PRAGMA busy_timeout=15000")
 assert db.execute("PRAGMA quick_check").fetchone()[0]=="ok"
 db.execute("BEGIN IMMEDIATE")
 try:
  row=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
  if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
  prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
  if len(prior)>1:raise RuntimeError("DUPLICATE")
  if prior:
   if json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
   event=prior[0][0]
  else:
   event=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
     (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:db.rollback();raise
 finally:db.close()
 write_once(D/"REGISTRY_RESULT_A50.json",json.dumps({"event_id":event,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event,"qa":"PASS","model_sha256":ev["model_sha256"],
  "evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
