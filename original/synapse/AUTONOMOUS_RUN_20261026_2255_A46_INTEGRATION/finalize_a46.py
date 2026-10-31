"""Idempotent A46 evidence. Only writes to own folder and existing task_events."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time,unittest
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a46-emchart-compressor-simulink-parity-20261026"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(p,text):
 if p.exists():
  if p.read_text(encoding="utf8")!=text:raise RuntimeError("CONFLICT "+str(p))
 else:p.write_text(text,encoding="utf8")
def main():
 scopes=[CENTER,CENTER/"recovery",HERE,Path(r"C:\Users\Lysda\Desktop\temp_coding"),Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),Path(r"C:\Users\Lysda\Desktop\MicroFreelance_2026")]
 for scope in scopes:
  for name in ["STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"]:
   if (scope/name).exists():raise RuntimeError("STOP_ACTIVE "+str(scope/name))
 run=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(HERE),"-p","test_a46.py","-q"],capture_output=True,text=True,timeout=25)
 if run.returncode or "Ran 4 tests" not in run.stderr or "OK" not in run.stderr:raise RuntimeError("QA_FAIL "+run.stderr)
 audit=json.loads((HERE/"SIMULINK_A46_RESULT.json").read_text(encoding="utf8"))
 assert audit["numeric_comparisons"]==51744 and audit["samples"]==4704
 assert len(audit["scenarios"])==7
 evidence={"status":"A46_SIMULINK_COMPRESSOR_PARITY_PASS","task_id":TASK,"scenario_count":7,"steps_per_scenario":672,"matlab_python_numeric_comparisons":51744,"independent_unittest":"4/4 PASS","model_sha256":sha(HERE/"DCHR_A46_Compressor_Closed_Loop.slx"),"physical_release":False,"graphical_stateflow_controlling":False,"model_uses_stateflow_emchart":True,"next_step":"A47 replace EMChart internal FSM with externally connected graphical Stateflow A44-equivalent supervisor; 7x672 closed-loop parity and transitions"}
 once(HERE/"EVIDENCE.json",json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
 files=["build_a46.m","DCHR_A46_Compressor_Closed_Loop.slx","SIMULINK_A46_RESULT.json","prepare_a46.py","runner_a46.m","test_a46.py","EVIDENCE.json"]
 manifest={n:sha(HERE/n) for n in files}
 once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 payload={"scope":"A46_isolated_Simulink_EMChart_compressor_lag_parity","artifact_directory":str(HERE),"evidence_sha256":sha(HERE/"EVIDENCE.json"),"manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),"qa":"MATLAB 7x672 PASS, 51744 numeric parity, 4/4 independent Python QA, SLX ZIP PASS","graphical_stateflow_controlling":False,"physical_release":False,"next_step":evidence["next_step"]}
 db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
 db.execute("PRAGMA busy_timeout=10000")
 if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("DB_INTEGRITY_FAIL")
 db.execute("BEGIN IMMEDIATE")
 try:
  row=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
  if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+str(row))
  old=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
  if len(old)>1:raise RuntimeError("DUPLICATE_EVENTS")
  if old:
   if json.loads(old[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
   eid=old[0][0]
  else:
   eid=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",(TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:
  db.rollback();raise
 finally:db.close()
 once(HERE/"REGISTRY_RESULT.json",json.dumps({"event_id":eid,"task_id":TASK,**payload},indent=2,ensure_ascii=False)+"\n")
 handoff=f"""# A46 DataCenter checkpoint (26 Oct 2026, local)
Verified actual MATLAB R2026a execution: 7x672 synthetic scenarios, 51,744 numeric comparisons PASS against A45 Python reference.
4/4 independent acceptance tests PASS, upstream A43/A44 and A45 hashes unchanged, model SLX ZIP valid.
A46 model: {HERE/'DCHR_A46_Compressor_Closed_Loop.slx'}
Model SHA256: {evidence['model_sha256']}
Evidence SHA256: {payload['evidence_sha256']}
Manifest SHA256: {payload['manifest_sha256']}
Synapse existing task {TASK}, event {eid}, status review/planned (no worker).
Failed first MATLAB invocation due argument quoting; next due missing A45 trace path; corrected in isolated files and reran successfully.
No graphical A44 chart controlling A46 yet. A46 uses Stateflow.EMChart. No physical calibration or equipment control.
Next exact step: {evidence['next_step']}.
No Codex session, no GPU job, no new card, no GUI/OAuth edits, VRS skipped.
"""
 once(HERE/"FINAL_HANDOFF.md",handoff)
 print(json.dumps({"event_id":eid,"model_sha256":evidence["model_sha256"],"evidence_sha256":payload["evidence_sha256"],"manifest_sha256":payload["manifest_sha256"],"handoff_sha256":sha(HERE/"FINAL_HANDOFF.md"),"status":"PASS"}))
if __name__=="__main__":main()
