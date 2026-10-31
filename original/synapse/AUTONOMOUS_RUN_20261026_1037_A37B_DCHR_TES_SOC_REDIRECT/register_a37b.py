"""Idempotent existing-card A37B evidence, with STOP/owner/provenance gates."""
import hashlib,json,sqlite3,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b";ACTOR="chatgpt-a37b-dchr-tes-soc-20261026"
V04=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_feedback_v04\alokuj_teplo_v04_sk.txt")
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
A36=HERE.parent/"AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"/"scenario_both_off.csv"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(path,obj):
 if path.exists():
  if json.loads(path.read_text(encoding="utf8"))!=obj:raise RuntimeError("CONFLICT "+str(path))
 else:path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
 for root in [CENTER,CENTER/"recovery",HERE,V04.parent.parent.parent]:
  for name in ["STOP","STOP.flag","STOP.txt",".stop",".STOP","PAUSE","PAUSE.flag","PAUSE.txt",".pause",".PAUSE","STOP_MANAGED_WORKERS.txt"]:
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
 result=json.loads((HERE/"RESULTS_A37B.json").read_text(encoding="utf8"))
 qa=json.loads((HERE/"INDEPENDENT_QA.json").read_text(encoding="utf8"))
 log=(HERE/"TEST_LOG.txt").read_text(encoding="utf8")
 if "Ran 11 tests" not in log or "OK" not in log or qa["status"]!="PASS" or qa["independent_decimal_checks"]!=8064:raise RuntimeError("QA_FAILED")
 if result["physical_release_allowed"] or result["clip_intervals"]!=6 or result["baseline_replay_max_E_error_J"]>1e-4:raise RuntimeError("RESULT_INVALID")
 for path,key in [(V04,"source_v04_sha256"),(V08,"source_v08_sha256"),(A36,"source_a36_sha256")]:
  if sha(path)!=result[key]:raise RuntimeError("SOURCE_CHANGED "+key)
 if sha(HERE/result["trace"])!=result["trace_sha256"]:raise RuntimeError("TRACE_CHANGED")
 evidence={"scope":"isolated_DCHR_A37B_v04_TES_SOC_dynamic_charge_saturation_and_REJECT_redirect",
  "qa":"11/11 unit PASS; original v08 TES baseline within 5.01e-6 J; 672 steps / 8064 independent Decimal checks PASS",
  "key_finding":"A36 fixed TES charge overfills synthetic 900kWh storage: 6 intervals clipped after hour 69; 75.688kWh charge curtailed; +61.346kWh reject; 14.342kWh HP power proxy reduction.",
  "source_v04_sha256":result["source_v04_sha256"],"source_v08_sha256":result["source_v08_sha256"],
  "decision":"TES_SOC_REDIRECT_SYNTHETIC_VERIFIED_PHYSICAL_RELEASE_BLOCKED",
  "limits":"synthetic v04 parameters, fixed COP proxy, no full HP/TES/Stateflow feedback, no hardware control",
  "next_step":"Owner integrate A37B TES SOC and A37 N-1 IT thermal logic in isolated MATLAB/Stateflow, validate equipment parameters and full dynamic energy closure.",
  "physical_release_allowed":False}
 save_once(HERE/"EVIDENCE.json",evidence)
 files=["tes_soc.py","test_tes_soc.py","independent_qa.py","TEST_LOG.txt","RUN_LOG.txt","INDEPENDENT_QA_LOG.txt",
        "RESULTS_A37B.json","INDEPENDENT_QA.json","TES_SOC_TRACE.csv","DCHR_A37B_TES_RU.md","HANDOFF.md","EVIDENCE.json","register_a37b.py"]
 save_once(HERE/"SHA256_MANIFEST.json",{f:sha(HERE/f) for f in files})
 payload={"scope":evidence["scope"],"artifact_directory":str(HERE),
          "evidence_sha256":sha(HERE/"EVIDENCE.json"),"manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
          "qa":evidence["qa"],"key_finding":evidence["key_finding"],"decision":evidence["decision"],
          "limits":evidence["limits"],"next_step":evidence["next_step"]}
 with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=6,isolation_level=None) as db:
  db.execute("pragma busy_timeout=6000")
  if db.execute("pragma quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE")
  db.execute("begin immediate")
  try:
   state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
   if state!=("review","planned",None,"MATLAB/Stateflow QA"):raise RuntimeError("OWNER_CHANGED "+repr(state))
   found=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
   if len(found)>1:raise RuntimeError("DUPLICATE")
   if found:
    if json.loads(found[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
    event_id,action=found[0][0],"EXISTING_EVENT"
   else:
    event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
     (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
    action="CREATED_EVENT"
   db.commit()
  except BaseException:db.rollback();raise
 save_once(HERE/"REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,**payload})
 print(json.dumps({"event_id":event_id,"action":action,"evidence_sha256":payload["evidence_sha256"],
                   "manifest_sha256":payload["manifest_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
