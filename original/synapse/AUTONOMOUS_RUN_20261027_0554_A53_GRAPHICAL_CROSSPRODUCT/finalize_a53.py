"""A53 immutable evidence and idempotent existing-card Synapse receipt."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time,zipfile
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a53-graphical-crossproduct-20261027-0554"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(p,text):
 if p.exists():
  if p.read_text(encoding="utf-8-sig")!=text:raise RuntimeError("CONFLICT "+str(p))
 else:p.write_text(text,encoding="utf-8")
def stop_guard():
 for root in (CENTER,CENTER/"recovery",CENTER/"Continuity",
   Path(r"C:\Users\Lysda\Desktop\temp_coding"),
   Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
   Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")):
  for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
 stop_guard()
 r=json.loads((D/"MATLAB_A53_RESULT.json").read_text(encoding="utf-8-sig"))
 assert r["status"]=="A53_GRAPHICAL_CROSSPRODUCT_PARITY_PASS" and r["comparisons"]==47520 and len(r["cases"])==18
 assert r["synthetic_only"] and not r["physical_release"]
 qa=subprocess.run([sys.executable,"-B",str(D/"test_a53.py")],capture_output=True,text=True,timeout=30)
 assert qa.returncode==0 and "Ran 10 tests" in qa.stderr and "OK" in qa.stderr,qa.stderr
 once(D/"QA_STDERR.txt",qa.stderr)
 models=[D/f"DCHR_A53_TripDelay_{n}.slx" for n in (0,2,4)]
 for p in models:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
 source=D.parent/"AUTONOMOUS_RUN_20261027_0450_A51_TRIP_DELAY_GRAPHICAL"
 known={0:"3691770ae5f531824389035eafe19bafbdbd2e674d109d68c4a92ca8dacd073c",2:"c78bf64b0b2b1ac4d1436498db6caed535d3a174c7d78656baa02f7016eeeda4",4:"1c569018b7c8cadcf94845086a01c886c99f3551e7da9b3948aaae1a22021789"}
 for k,w in known.items():assert sha(source/f"DCHR_A51_TripDelay_{k}.slx")==w
 next_step="A54: independent sensitivity/uncertainty and protection envelope from A53, primary-source signoffs and physical protection validation remain BLOCKED; do not infer certified safe thresholds."
 ev=dict(task_id=TASK,scope="A53_graphical_sensor_trip_crossproduct",status=r["status"],artifact_directory=str(D),
   models={p.name:sha(p) for p in models},source_a51_sha256=known,
   matlab_result_sha256=sha(D/"MATLAB_A53_RESULT.json"),matlab_executed=True,
   numeric_comparisons=47520,scenarios=18,steps_per_scenario=240,python_tests="10/10 PASS",
   trip_indices={k:v["first_trip_index_zero_based"] for k,v in r["cases"].items()},
   synthetic_only=True,physical_release=False,
   limitations="Graphical Stateflow synthetic simulation; no real sensor, PLC, safety certification, or primary-source signoffs.",
   next_step=next_step)
 once(D/"EVIDENCE_A53.json",json.dumps(ev,ensure_ascii=False,indent=2)+"\n")
 names=["make_references.py","run_a53.m","test_a53.py","MATLAB_A53_RESULT.json","REFERENCE_MANIFEST.json","QA_STDERR.txt","EVIDENCE_A53.json"]+[p.name for p in models]+[f"REF_{s}_lag{l}_trip{t}.csv" for s in ("neither","backup_only") for l in (0,1,4) for t in (0,2,4)]
 manifest={n:sha(D/n) for n in names}
 once(D/"SHA256_MANIFEST_A53.json",json.dumps(manifest,indent=2)+"\n")
 handoff=(
 "# A53 graphical Stateflow sensor x trip-delay | 2026-10-27 05:54 CET\n"
 "Live SynapseMCP Web ping initially ONLINE; MATLAB launch RPC timed out; authorized Ngrok readback confirmed MATLAB PID exited and result exists. Never reissue timed-out MATLAB launch without process check.\n"
 "MATLAB R2026a 3 isolated graphical SLX models, 2 REJECT modes x 3 sensor delays x 3 trip delays x 240 samples x 11 channels = 47520 comparisons PASS.\n"
 "Independent Python Decimal energy/temperature ledger and source/SLX integrity QA 10/10 PASS.\n"
 "Full failure REJECT TRIPPED index 96/98/100 across sensor lags; backup_only with sensor 60min and trip guard 60min index 105 versus 100 without sensor lag. Synthetic model, NOT real-world safety certification.\n"
 "MATLAB JSON initially had a trailing literal escaped newline from report formatting; repaired JSON and source script in owned scope, validated parser and QA. No rerun necessary.\n"
 + "".join(f"{p.name} SHA256 {sha(p)}\n" for p in models)
 + f"MATLAB result SHA256 {sha(D/'MATLAB_A53_RESULT.json')}\n"
 + f"Evidence SHA256 {sha(D/'EVIDENCE_A53.json')}\n"
 + f"Manifest SHA256 {sha(D/'SHA256_MANIFEST_A53.json')}\n"
 "No Codex, new worker, GPU job, VRS, shared GUI, STOP/OAuth, or physical changes.\n"
 f"NEXT: {next_step}\n")
 once(D/"FINAL_HANDOFF.md",handoff)
 payload=dict(scope=ev["scope"],artifact_directory=str(D),models=ev["models"],
   result_sha256=ev["matlab_result_sha256"],evidence_sha256=sha(D/"EVIDENCE_A53.json"),
   manifest_sha256=sha(D/"SHA256_MANIFEST_A53.json"),handoff_sha256=sha(D/"FINAL_HANDOFF.md"),
   qa="MATLAB 18x240, 47520/47520 numeric parity; independent Python 10/10 PASS",
   physical_release=False,next_step=next_step)
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
 once(D/"REGISTRY_RESULT_A53.json",json.dumps({"event_id":event,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event,"qa":"PASS","evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()

