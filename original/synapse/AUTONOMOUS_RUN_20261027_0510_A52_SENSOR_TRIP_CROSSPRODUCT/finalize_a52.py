"""A52 idempotent checkpoint in existing Synapse DataCenter card."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a52-sensor-trip-crossproduct-20261027-0510"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_once(p,text):
 if p.exists():
  if p.read_text(encoding="utf-8-sig")!=text:raise RuntimeError("CONFLICT "+str(p))
 else:p.write_text(text,encoding="utf-8")
def main():
 for root in (CENTER,CENTER/"recovery",CENTER/"Continuity",Path(r"C:\Users\Lysda\Desktop\temp_coding"),Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline")):
  for n in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
 data=json.loads((D/"SENSITIVITY_A52.json").read_text(encoding="utf-8-sig"))
 assert data["status"]=="A52_SYNTHETIC_CROSSPRODUCT_REFERENCE_PASS" and len(data["cases"])==18
 assert not data["matlab_crossproduct_executed"] and not data["physical_release"]
 qa=subprocess.run([sys.executable,"-B",str(D/"test_a52.py")],capture_output=True,text=True,timeout=30)
 assert qa.returncode==0 and "Ran 8 tests" in qa.stderr and "OK" in qa.stderr
 next_step="A53: run full 18-case sensor-lag x trip-delay matrix in graphical MATLAB/Stateflow (240 steps, 11 channels), compare 47520 values with Python A52, then assess safety margins and independent primary-source evidence; physical deployment BLOCKED."
 ev=dict(task_id=TASK,scope="A52_independent_sensor_trip_sensitivity",artifact_directory=str(D),
  result_sha256=sha(D/"SENSITIVITY_A52.json"),scenarios=18,samples_each=240,
  independent_energy_ledgers="18/18 PASS",python_tests="8/8 PASS",
  first_trip_backup_sensor4_trip4=105,first_trip_backup_sensor0_trip4=100,
  worst_synthetic_temperature_C=max(x["max_temperature_C"] for x in data["cases"]),
  matlab_crossproduct_executed=False,synthetic_only=True,physical_release=False,next_step=next_step)
 write_once(D/"EVIDENCE_A52.json",json.dumps(ev,ensure_ascii=False,indent=2)+"\n")
 names=["a52_sensitivity.py","test_a52.py","SENSITIVITY_A52.json","QA_STDERR.txt","EVIDENCE_A52.json"]
 write_once(D/"SHA256_MANIFEST_A52.json",json.dumps({n:sha(D/n) for n in names},indent=2)+"\n")
 handoff=(f"# A52 independent sensor x trip-delay sensitivity | 2026-10-27\n"
 f"Existing Synapse task {TASK}; A51 event 1279 already recorded separately. No new task, agent or GPU job.\n"
 "Python 18 synthetic scenarios: 2 REJECT configurations x sensor lag 0/1/4 x trip guard 0/2/4; 240 samples per scenario, independent decimal ledger on each trace. 8/8 independent regression tests PASS.\n"
 "Backup-only, 60-minute sensor lag plus 60-minute trip guard: first TRIPPED index 105; with zero sensor lag and same trip guard: 100. Thus modeled delay difference 75 minutes. Neither REJECT mode is sensor-lag independent, trip indices 96/98/100.\n"
 f"Worst synthetic max IT temperature across matrix {ev['worst_synthetic_temperature_C']:.4f} C; model assumptions are NOT physical safety validation. No cross-product MATLAB run in A52.\n"
 f"Evidence SHA256 {sha(D/'EVIDENCE_A52.json')}\nManifest SHA256 {sha(D/'SHA256_MANIFEST_A52.json')}\n"
 "No Codex, VRS, shared GUI, STOP/OAuth changes, external actions or physical equipment. Primary SynapseMCP Web timed out during A51; authorized fallback used after live ping.\n"
 f"NEXT: {next_step}\n")
 write_once(D/"FINAL_HANDOFF.md",handoff)
 payload=dict(scope=ev["scope"],artifact_directory=str(D),result_sha256=ev["result_sha256"],
  evidence_sha256=sha(D/"EVIDENCE_A52.json"),manifest_sha256=sha(D/"SHA256_MANIFEST_A52.json"),
  handoff_sha256=sha(D/"FINAL_HANDOFF.md"),qa="18 independent energy audits; Python 8/8 PASS; no MATLAB crossproduct",
  physical_release=False,next_step=next_step)
 db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
 db.execute("PRAGMA busy_timeout=15000")
 assert db.execute("PRAGMA quick_check").fetchone()[0]=="ok"
 db.execute("BEGIN IMMEDIATE")
 try:
  row=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
  if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
  prior=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
  if len(prior)>1:raise RuntimeError("DUPLICATE")
  if prior:
   if json.loads(prior[0][1])!=payload:raise RuntimeError("CONFLICT")
   event=prior[0][0]
  else:
   event=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:db.rollback();raise
 finally:db.close()
 write_once(D/"REGISTRY_RESULT_A52.json",json.dumps({"event_id":event,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event,"evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
