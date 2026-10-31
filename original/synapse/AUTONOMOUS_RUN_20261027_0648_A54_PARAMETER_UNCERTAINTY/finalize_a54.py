"""A54 fail-closed evidence finalizer, existing Synapse card only."""
from pathlib import Path
import json,hashlib,sqlite3,time,subprocess,sys
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a54-parameter-uncertainty-20261027-0648"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(p,text):
 if p.exists():
  if p.read_text(encoding="utf-8-sig")!=text:raise RuntimeError("CONFLICT "+str(p))
 else:p.write_text(text,encoding="utf-8")
def guards():
 for root in (CENTER,CENTER/"recovery",CENTER/"Continuity",Path(r"C:\Users\Lysda\Desktop\temp_coding"),Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")):
  for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
 guards()
 r=json.loads((D/"A54_UNCERTAINTY_RESULTS.json").read_text(encoding="utf-8"))
 assert r["status"]=="A54_SYNTHETIC_PARAMETER_UNCERTAINTY_VERIFIED"
 assert r["cases_checked"]==144 and r["baseline_A52_anchors_checked"]==18
 assert not r["physical_release"] and r["not_a_certified_safety_envelope"]
 qa=subprocess.run([sys.executable,"-B",str(D/"test_a54.py")],capture_output=True,text=True,timeout=30)
 assert qa.returncode==0 and "Ran 8 tests" in qa.stderr and "OK" in qa.stderr,qa.stderr
 if (D/"QA_VERIFIED.txt").exists():
  prior_qa=(D/"QA_VERIFIED.txt").read_text(encoding="utf-8-sig")
  assert "Ran 8 tests" in prior_qa and "OK" in prior_qa
 else:once(D/"QA_VERIFIED.txt",qa.stderr)
 next_step="A55: select measured thermal mass, compressor dynamics and residual heat bounds from primary equipment data; then test interval robustness in graphical Stateflow. Do not approve hardware or certify temperature limits from synthetic sweeps."
 ev=dict(task_id=TASK,scope="A54_synthetic_parameter_uncertainty",status=r["status"],artifact_directory=str(D),
   parameter_grid="2 scenarios x 2 sensor delays x 2 trip delays x 3 heat capacities x 3 residual fractions x 2 compressor taus",
   cases=144,baseline_A52_anchors=18,steps_per_case=240,
   independent_decimal_ledger=True,python_tests="8/8 PASS",
   source_A52_sha256=r["source_A52_sha256"],
   max_temperature_C={k:v["max_peak_C"] for k,v in r["scenarios"].items()},
   source_A53_model_sha256={n:sha(D.parent/"AUTONOMOUS_RUN_20261027_0554_A53_GRAPHICAL_CROSSPRODUCT"/n) for n in ("DCHR_A53_TripDelay_0.slx","DCHR_A53_TripDelay_2.slx","DCHR_A53_TripDelay_4.slx")},
   synthetic_only=True,matlab_A54_executed=False,physical_release=False,
   limitations="Hypothetical parameter bounds, not uncertainty confidence intervals or validated physical safety envelope. No A54 MATLAB run.",
   next_step=next_step)
 once(D/"EVIDENCE_A54.json",json.dumps(ev,ensure_ascii=False,indent=2)+"\n")
 names=["a54_uncertainty.py","test_a54.py","A54_UNCERTAINTY_RESULTS.json","RUN_OUTPUT.txt","QA_VERIFIED.txt","EVIDENCE_A54.json"]
 manifest={n:sha(D/n) for n in names}
 once(D/"SHA256_MANIFEST_A54.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 handoff=(
 "# A54 synthetic parameter uncertainty | 2026-10-27 06:48 CET\n"
 "Primary SynapseMCP Web ping ONLINE at 06:48; host DESKTOP-M9L3I4M; RAM used 68.5%, VRAM 1064/8188 MiB GPU 0%. Jarvice PID 11572 idle, scheduler Running; no STOP/PAUSE in six checked roots. Shared Jarvice repo dirty; no changes there.\n"
 "A54 new isolated Python parameter sweep: 144 cases x 240 samples, independent Decimal energy/temperature ledger on each trace, 18 A52 baseline anchors replayed, 8/8 unittest PASS. No MATLAB A54 run.\n"
 f"Peak synthetic temperature ranges: neither {r['scenarios']['neither']['min_peak_C']:.3f}..{r['scenarios']['neither']['max_peak_C']:.3f} C; backup_only {r['scenarios']['backup_only']['min_peak_C']:.3f}..{r['scenarios']['backup_only']['max_peak_C']:.3f} C.\n"
 "These are stress-test assumptions, NOT measured confidence intervals or certified safe operating limits. Primary source signoffs and physical validation remain BLOCKED.\n"
 f"Result SHA256 {sha(D/'A54_UNCERTAINTY_RESULTS.json')}\n"
 f"Evidence SHA256 {sha(D/'EVIDENCE_A54.json')}\n"
 f"Manifest SHA256 {sha(D/'SHA256_MANIFEST_A54.json')}\n"
 "No Codex, new workers, GPU tasks, VRS, GUI, STOP/OAuth or original model modifications.\n"
 f"NEXT: {next_step}\n")
 once(D/"FINAL_HANDOFF.md",handoff)
 payload=dict(scope=ev["scope"],artifact_directory=str(D),result_sha256=sha(D/"A54_UNCERTAINTY_RESULTS.json"),
  evidence_sha256=sha(D/"EVIDENCE_A54.json"),manifest_sha256=sha(D/"SHA256_MANIFEST_A54.json"),
  handoff_sha256=sha(D/"FINAL_HANDOFF.md"),qa="144 cases x 240 samples independent Decimal ledger, 18 A52 anchors, 8/8 Python tests",
  matlab_A54_executed=False,physical_release=False,next_step=next_step)
 db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
 db.execute("PRAGMA busy_timeout=15000")
 assert db.execute("PRAGMA quick_check").fetchone()[0]=="ok"
 db.execute("BEGIN IMMEDIATE")
 try:
  row=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
  if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
  prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
  if len(prior)>1:raise RuntimeError("DUPLICATE_EVENT")
  if prior:
   if json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
   event=prior[0][0]
  else:
   event=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
     (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
  db.commit()
 except BaseException:db.rollback();raise
 finally:db.close()
 once(D/"REGISTRY_RESULT_A54.json",json.dumps({"event_id":event,"task_id":TASK,**payload},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"event_id":event,"qa":"8/8 PASS","evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()

