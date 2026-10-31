"""Idempotent evidence checkpoint for A51 in existing DataCenter Synapse card."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time,zipfile
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a51-graphical-trip-delay-20261027-0450"
SRC=D.parent/"AUTONOMOUS_RUN_20261027_0351_A50_SENSOR_LAG_MATLAB"/"DCHR_A50_Sensor_Lag.slx"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_once(p,data):
 if p.exists():
  if p.read_text(encoding="utf-8-sig")!=data:raise RuntimeError("FILE_CONFLICT "+str(p))
 else:p.write_text(data,encoding="utf-8")
def guard():
 for root in (CENTER,CENTER/"recovery",CENTER/"Continuity",
              Path(r"C:\Users\Lysda\Desktop\temp_coding"),
              Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
              Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")):
  for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
 guard()
 assert sha(SRC)=="8edb7f64b9fe27c54be4c5d1223e242feb6f733cde97dce4c044b25729dc5cbe"
 r=json.loads((D/"MATLAB_A51_RESULT.json").read_text(encoding="utf-8-sig"))
 assert r["status"]=="A51_GRAPHICAL_TRIP_DELAY_PARITY_PASS" and r["comparisons"]==15840 and len(r["cases"])==6 and not r["physical_release"]
 qa=subprocess.run([sys.executable,"-B",str(D/"test_a51.py")],capture_output=True,text=True,timeout=30)
 assert qa.returncode==0 and "Ran 9 tests" in qa.stderr and "OK" in qa.stderr,qa.stderr
 assert "Ran 9 tests" in (D/"QA_STDERR.txt").read_text(encoding="utf-8-sig")
 models=[D/f"DCHR_A51_TripDelay_{n}.slx" for n in (0,2,4)]
 for n,p in zip((0,2,4),models):
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   data=b"".join(z.read(f) for f in z.namelist() if "stateflow" in f.lower())
   assert f"pending&gt;={n}".encode() in data
 next_step="A52: cross-test sensor lag 0/1/4 against graphical trip delays 0/2/4, verify trip-time sensitivity and energy balances in isolated MATLAB/Python models; physical equipment and 31 source signoffs remain BLOCKED."
 ev=dict(task_id=TASK,scope="A51_graphical_trip_delay_variants",status=r["status"],artifact_directory=str(D),
  source_a50_sha256=sha(SRC),models={p.name:sha(p) for p in models},
  matlab_result_sha256=sha(D/"MATLAB_A51_RESULT.json"),matlab_executed=True,
  numeric_comparisons=15840,scenarios=6,steps_per_scenario=240,python_tests="9/9 PASS",
  trip_delay_steps=[0,2,4],trip_indices={"neither":[96,98,100],"backup_only":[96,98,100]},
  synthetic_only=True,physical_release=False,limitations="Graphical Stateflow simulated; not validated against physical equipment, safety hardware, or primary-source signoffs.",
  next_step=next_step)
 write_once(D/"EVIDENCE_A51.json",json.dumps(ev,ensure_ascii=False,indent=2)+"\n")
 names=["make_references.py","run_a51.m","test_a51.py","MATLAB_A51_RESULT.json","REFERENCE_MANIFEST.json","QA_STDERR.txt","EVIDENCE_A51.json"]+[p.name for p in models]+[f"REF_{s}_trip{n}.csv" for s in ("neither","backup_only") for n in (0,2,4)]
 manifest={n:sha(D/n) for n in names}
 write_once(D/"SHA256_MANIFEST_A51.json",json.dumps(manifest,indent=2)+"\n")
 handoff=(
 "# A51 graphical Stateflow trip-delay acceptance | 2026-10-27 04:50 CET\n"
 "Existing Synapse card scc-3d9d172beb6e1b; primary SynapseMCP Web timed out during MATLAB launch, authorized Ngrok fallback verified process exited and results complete. Do not repeat a timed-out command without observing state.\n"
 "MATLAB R2026a: three SAVED graphical Stateflow models, trip guard 0/2/4 samples; 2 REJECT modes x 3 delays x 240 samples x 11 channels = 15840 numeric comparisons, all PASS against independent Python A45.\n"
 "TRIPPED first zero-based indices: neither 96/98/100; backup_only 96/98/100. Delay increments 15 minutes per sample; 0 delay uses direct ACTIVE/RAMPING-to-TRIPPED transitions. This is synthetic and NOT certified protective behavior.\n"
 "Independent Python 9/9 PASS, including decimal energy/temperature audit, five mutation probes, SLX ZIP/Stateflow guard verification, input/reference checks and source hash guard.\n"
 f"A50 source SHA256 unchanged: {sha(SRC)}\n"
 + "".join(f"{p.name} SHA256 {sha(p)}\n" for p in models)
 + f"MATLAB result SHA256 {sha(D/'MATLAB_A51_RESULT.json')}\n"
 + f"Evidence SHA256 {sha(D/'EVIDENCE_A51.json')}\n"
 + f"Manifest SHA256 {sha(D/'SHA256_MANIFEST_A51.json')}\n"
 "No Codex, new worker, GPU job, VRS, shared GUI, STOP/OAuth or external side effects. Physical release BLOCKED.\n"
 f"NEXT: {next_step}\n")
 write_once(D/"FINAL_HANDOFF.md",handoff)
 payload=dict(scope=ev["scope"],artifact_directory=str(D),models=ev["models"],
  result_sha256=ev["matlab_result_sha256"],evidence_sha256=sha(D/"EVIDENCE_A51.json"),
  manifest_sha256=sha(D/"SHA256_MANIFEST_A51.json"),handoff_sha256=sha(D/"FINAL_HANDOFF.md"),
  qa="MATLAB 6x240, 15840/15840 numeric parity; Python 9/9 PASS",physical_release=False,next_step=next_step)
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
 write_once(D/"REGISTRY_RESULT_A51.json",json.dumps({"event_id":event,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event,"qa":"PASS","evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
