"""C127 evidence finalizer, existing Synapse card only, idempotent actor."""
import datetime,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parent.parent
sys.path.insert(0,str(ROOT))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c127-bounded-dispatch-20261031-1049"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for f in FLAGS:
   if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def once(name,content):
 p=D/name
 if p.exists():
  if p.read_text(encoding="utf-8")!=content:raise RuntimeError("EXISTING_DRIFT "+name)
 else:p.write_text(content,encoding="utf-8")
def json_once(name,obj):once(name,json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
def main():
 guard()
 m=json.loads((D/"C127_METADATA.json").read_text(encoding="utf-8"))
 q=json.loads((D/"C127_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 s=json.loads((D/"C127_SUMMARY.json").read_text(encoding="utf-8"))
 assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"]
 assert m["rows"]==71424 and m["selftests"]==13
 assert q["status"]=="PASS" and q["independent"] and q["rows"]==71424 and q["negative_controls"]==6
 assert q["data_sha256"]==m["data_sha256"]==sha(D/"C127_BOUNDED_QUARTER.csv.gz")
 a=s["water_150kW"];b=s["air_150kW"];c=s["water_10kW_7d"];z=s["noheat_7d"]
 findings=f"""# C127: bounded quarter-step thermostat and shared thermal source (synthetic)

## Engineering change
Independent task-local 15-minute pool thermostat replaces C125's frozen hourly
pool-heat replay. At each step the pool requests feedforward losses plus proportional
temperature correction; heating is bounded by a shared thermal source. Positive
air-HVAC heating competes for the same source, dispatched either water-first or
air-first. Negative air-HVAC cooling is independent and excluded from source heat.
Pool evaporation and moist-air temperature/humidity continue to feed back.

## Measured simulation outputs
- 150 kW thermal source, water-first: 35040 quarters, final pool {a['final_pool_C']:.4f} C,
  delivered pool {a['pool_heat_MWh']:.3f} MWh, air {a['air_heat_MWh']:.3f} MWh,
  saturated quarters {int(a['cap_saturated_quarters'])}.
- 150 kW air-first: 35040 quarters, final pool {b['final_pool_C']:.4f} C,
  saturated quarters {int(b['cap_saturated_quarters'])}. Identical to water-first
  because the shared cap never binds in this synthetic scenario.
- 10 kW water-first, 7 days: 672 quarters, final pool {c['final_pool_C']:.4f} C,
  saturated quarters {int(c['cap_saturated_quarters'])}, air heat delivered
  {c['air_heat_MWh']:.4f} MWh.
- Zero source heat, 7 days: 672 quarters, final pool {z['final_pool_C']:.4f} C,
  pool heat delivered {z['pool_heat_MWh']:.4f} MWh.
- Total {m['rows']} quarter steps, 13 embedded tests, independent QA {q['rows']}
  row checks and {q['negative_controls']} negative controls PASS.

## Scientific limitations and interpretation
All inputs are synthetic. The ideal 150 kW thermostat holds exactly 28 C because
it can match the same loss law used by the simulator; this is NOT field performance.
The column pool_unmet_kJ measures unserved controller REQUEST (including feedback
catch-up), not observed heat leakage or equipment rating. Source caps are thermal
power, not electrical draw; no COP, cycling, actuator delay, calibrated dehumidifier,
weather measurements, physical validation or 31 primary-source signoffs are supplied.
Room air RH >65% persists even when pool temperature is controlled. Energy/mass
conservation tests prove accounting consistency, not real-world model accuracy.

## Next executable step
Introduce actuator delays, hysteresis switching costs and uncertain weather/COP,
then test constrained water-vs-air priority with a source cap that binds in both
directions. Independently verify all source and equipment assumptions before SCADA
or MATLAB deployment. Preserve original C116/C124/C125 and all shared runtimes.
"""
 once("C127_FINDINGS.md",findings)
 files=("c127_bounded_dispatch.py","qa_c127_independent.py","finalize_c127.py",
 "C127_BOUNDED_QUARTER.csv.gz","C127_SUMMARY.json","C127_METADATA.json",
 "C127_INDEPENDENT_QA.json","C127_FINDINGS.md")
 assert all((D/f).is_file() for f in files)
 manifest={"schema":"C127_MANIFEST_V1","task_id":TASK,"qa":"PASS",
 "files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in files}}
 json_once("SHA256_MANIFEST_C127.json",manifest)
 ev={"schema":"C127_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
 "artifact":str(D/"C127_BOUNDED_QUARTER.csv.gz"),"sha256":m["data_sha256"],
 "qa":str(D/"C127_INDEPENDENT_QA.json"),"findings":str(D/"C127_FINDINGS.md"),
 "manifest":str(D/"SHA256_MANIFEST_C127.json"),
 "manifest_sha256":sha(D/"SHA256_MANIFEST_C127.json"),
 "synthetic":True,"field_validated":False,"source_signoffs_added":0,
 "next":"Test binding source cap with competing water/air priorities and delayed actuators; independent physical validation."}
 json_once("EVIDENCE_C127.json",ev)
 guard()
 with registry._open() as db:
  row=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()
  if not row or row["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
  if prior:eid=prior["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{"artifact":ev["artifact"],"sha256":ev["sha256"],
   "qa":ev["qa"],"findings":ev["findings"],"manifest":ev["manifest"],
   "evidence":str(D/"EVIDENCE_C127.json"),
   "qa_result":"71424 independent quarter-step checks + 6 negative controls PASS",
   "synthetic":True,"not_field_validated":True,"next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 json_once("CANONICAL_RECEIPT_C127.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
 "evidence_sha256":sha(D/"EVIDENCE_C127.json"),"manifest_sha256":ev["manifest_sha256"]})
 with registry._open() as db:
  back=db.execute("SELECT actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
 assert back and back["actor"]==ACTOR
 handoff=f"""# C127 FINAL_HANDOFF | {datetime.datetime.now().astimezone().isoformat()}

## Verified live preflight
Primary SynapseMCP Web ping OK at 10:48:05 CET; owner NIGHT_HANDOFF,
AGENTS, INDEX, Kernel v1.2 and isolation/concurrency/lifecycle skills read.
RAM free 3990 MiB; VRAM 1224/8188 MiB, GPU 0% at 10:48:35 CET.
STOP/PAUSE absent in guarded roots at execution/finalization.
Jarvice and Synapse processes/worktrees inspected and preserved.
No Codex sessions, permanent workers, GPU jobs, GUI or OAuth changes.
Desktop Commander quota exhausted; used owner-preferred SynapseMCP Web.

## Engineering and QA
Isolated quarter-step shared thermal-source thermostat/air heat dispatch,
71424 synthetic steps, 13 embedded tests and 71424 independent QA checks,
6 negative controls PASS. Data SHA256 {ev['sha256']}.
Manifest SHA256 {ev['manifest_sha256']}.
Findings C127_FINDINGS.md: 150 kW cap nonbinding; 10 kW cap saturated,
0 kW noheat stress case. Source signoffs 0/31, physical validation OPEN.

## Existing Synapse card
{TASK}, evidence event {eid} read back, status queued.

## Exact next step
Use an intermediate thermal source cap to force both water/air priority
policies to compete, add actuator delays and independently test dispatch.
Do not alter shared SCADA/MATLAB, preview servers, OAuth, STOP or VRS.
"""
 once("FINAL_HANDOFF.md",handoff)
 print(json.dumps({"status":"PASS","event_id":eid,"readback":"VERIFIED",
 "task_status":"queued","data_sha256":ev["sha256"],
 "manifest_sha256":ev["manifest_sha256"],"handoff_sha256":sha(D/"FINAL_HANDOFF.md")},indent=2))
if __name__=="__main__":main()
