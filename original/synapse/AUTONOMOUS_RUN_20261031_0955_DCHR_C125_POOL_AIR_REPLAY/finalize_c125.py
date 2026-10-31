"""Register C125 isolated synthetic engineering result in EXISTING Synapse card."""
import datetime,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
sys.path.insert(0,str(ROOT))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c125-pool-air-replay-20261031-0955"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for name in FLAGS:
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def write_once(name,txt):
 p=D/name
 if p.exists():
  if p.read_text(encoding="utf-8")!=txt:raise RuntimeError("EXISTING_DRIFT "+name)
 else:p.write_text(txt,encoding="utf-8")
def jonce(name,obj):
 write_once(name,json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def main():
 guard()
 meta=json.loads((D/"C125_METADATA.json").read_text(encoding="utf-8"))
 qa=json.loads((D/"C125_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 results=json.loads((D/"C125_SUMMARY.json").read_text(encoding="utf-8"))
 assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
 assert qa["status"]=="PASS" and qa["rows"]==70080 and qa["negative_controls"]==5
 assert qa["data_sha256"]==meta["data_sha256"]==sha(D/"C125_POOL_AIR_QUARTER.csv.gz")
 fixed,feedback=results["fixed_RH"],results["feedback_RH"]
 diff_evap=feedback["evap_kg"]-fixed["evap_kg"]
 diff_t=feedback["final_pool_C"]-fixed["final_pool_C"]
 diff_rh=feedback["RH_above65_quarters"]-fixed["RH_above65_quarters"]
 findings=f"""# C125: two-way pool/air replay with 15-minute feedback (synthetic)

## Actual change
Added task-local Python model that recomputes C93 evaporation from live quarter-step
pool temperature and room relative humidity, propagates moist-air T/w via immutable
C124 step(), and updates pool thermal storage with the SAME latent heat removed
from water and added to air. Hourly pool heat is replayed from SHA-pinned C116,
not newly optimized or reallocated. No MATLAB, SCADA or shared runtime edits.

## Results (two 8760-hour scenarios, 70080 quarter-steps)
- Frozen evaporation RH=55%: total evaporation {fixed['evap_kg']:.2f} kg,
  final pool {fixed['final_pool_C']:.4f} C, quarters RH>65% {int(fixed['RH_above65_quarters'])}.
- Feedback evaporation RH=actual: {feedback['evap_kg']:.2f} kg,
  final pool {feedback['final_pool_C']:.4f} C, quarters RH>65% {int(feedback['RH_above65_quarters'])}.
- Difference: evaporation {diff_evap:+.2f} kg ({100*diff_evap/fixed['evap_kg']:+.2f}%),
  final pool temperature {diff_t:+.4f} C, high-RH quarters {int(diff_rh):+d}.
- These differences expose sensitivity to humidity feedback and the fixed heat replay.
  In particular, 31.18 C final pool is NOT a safe operating forecast.

## Verification and limits
6 embedded checks and 70080 independent CSV-only energy/mass/continuity checks;
5 negative controls PASS. Exact source and output SHA256 recorded in manifest.
All results are SYNTHETIC. Replayed C116 heating ignores thermostat response to
new pool temperature, which exaggerates heat accumulation. C93 hourly loss law
is sampled quarterly, and C124 synthetic supply/HVAC and dehumidifier assumptions
remain. No measured climate, real equipment curves, external physical validation,
or 31 primary-source signoffs have been obtained. Conservation is a mathematical
identity test, not field validation.

## Next executable engineering step
Implement a bounded quarter-step heat-dispatch/thermostat feedback instead of
replaying C116 pool heat, and explicitly report any source-capacity violation.
Do not present equipment sizing or operating temperatures as validated.
"""
 write_once("C125_FINDINGS.md",findings)
 files=("c125_pool_air_replay.py","qa_c125_independent.py","finalize_c125.py",
        "C125_POOL_AIR_QUARTER.csv.gz","C125_SUMMARY.json","C125_METADATA.json",
        "C125_INDEPENDENT_QA.json","C125_FINDINGS.md")
 assert all((D/f).is_file() for f in files)
 jonce("SHA256_MANIFEST_C125.json",{"schema":"C125_MANIFEST_V1","task_id":TASK,
  "qa":"PASS","files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in files}})
 ev={"schema":"C125_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
  "artifact":str(D/"C125_POOL_AIR_QUARTER.csv.gz"),"sha256":meta["data_sha256"],
  "qa":str(D/"C125_INDEPENDENT_QA.json"),"findings":str(D/"C125_FINDINGS.md"),
  "manifest":str(D/"SHA256_MANIFEST_C125.json"),
  "manifest_sha256":sha(D/"SHA256_MANIFEST_C125.json"),
  "synthetic":True,"field_validated":False,"source_signoffs_added":0,
  "next":"Implement quarter-step thermostat/heat dispatch with source-capacity bounds; verify against measured equipment before acceptance."}
 jonce("EVIDENCE_C125.json",ev)
 guard()
 with registry._open() as db:
  row=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()
  if not row or row["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
  if prior:eid=prior["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{
    "artifact":ev["artifact"],"sha256":ev["sha256"],"qa":ev["qa"],
    "findings":ev["findings"],"manifest":ev["manifest"],
    "evidence":str(D/"EVIDENCE_C125.json"),"qa_result":"70080 independent quarter-step checks + 5 negative controls PASS",
    "synthetic":True,"not_field_validated":True,"next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 jonce("CANONICAL_RECEIPT_C125.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
   "evidence_sha256":sha(D/"EVIDENCE_C125.json"),"manifest_sha256":ev["manifest_sha256"]})
 with registry._open() as db:
  back=db.execute("SELECT actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
 assert back and back["actor"]==ACTOR
 handoff=f"""# C125 FINAL_HANDOFF | {datetime.datetime.now().astimezone().isoformat()}

## Live preflight
SynapseMCP Web ping OK at 09:51 CET; owner NIGHT_HANDOFF, AGENTS, INDEX,
Kernel v1.2 and relevant skills read. RAM free 3936 MiB; VRAM 1218/8188 MiB,
GPU 0% at 09:52 CET. STOP/PAUSE absent in checked project roots. Existing
workers, worktrees and preview listeners untouched. No new Codex/GPU workers.

## Engineering
Isolated C125 pool/air 15-minute feedback replay; 8760 h x 4 x 2 = 70080 rows.
Source C116 and C124 SHA pinned. Results and limitations in C125_FINDINGS.md.
Synthetic only, field validated=false, 31 source signoffs still open.

## QA and registry
6 embedded tests; 70080 independent mass/energy/continuity checks and
5 negative controls PASS. Data SHA256 {ev['sha256']}.
Manifest SHA256 {ev['manifest_sha256']}.
Existing Synapse card {TASK}; evidence event {eid} read back; status queued.

## Exact next step
Implement a quarter-step thermostat/heat dispatch with bounded source power
instead of fixed C116 heat replay, then test a no-heat and saturation case.
Do not modify live SCADA/MATLAB, OAuth, STOP or another owner's worktree.
"""
 write_once("FINAL_HANDOFF.md",handoff)
 print(json.dumps({"status":"PASS","event_id":eid,"readback":"VERIFIED",
  "task_status":"queued","data_sha256":ev["sha256"],
  "manifest_sha256":ev["manifest_sha256"],"handoff_sha256":sha(D/"FINAL_HANDOFF.md")},indent=2))
if __name__=="__main__":main()
