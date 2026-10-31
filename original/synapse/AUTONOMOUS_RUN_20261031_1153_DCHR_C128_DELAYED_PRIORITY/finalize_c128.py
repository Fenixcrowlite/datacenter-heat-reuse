"""C128 fail-closed finalizer: immutable evidence in existing Synapse card."""
import datetime,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parent.parent
sys.path.insert(0,str(ROOT))
import registry
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c128-delayed-priority-20261031-1153"
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
def jonce(name,obj):once(name,json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
def main():
 guard()
 meta=json.loads((D/"C128_METADATA.json").read_text(encoding="utf-8"))
 qa=json.loads((D/"C128_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
 reg=json.loads((D/"C128_REGRESSION_QA.json").read_text(encoding="utf-8"))
 s=json.loads((D/"C128_SUMMARY.json").read_text(encoding="utf-8"))
 assert meta["task_id"]==TASK and meta["synthetic"] and not meta["field_validated"]
 assert meta["rows"]==qa["rows"]==6720 and meta["selftests"]==6
 assert qa["status"]=="PASS" and qa["independent"] and qa["negative_controls"]==9
 assert reg["status"]=="PASS" and reg["matched_numeric_fields"]==6720 and reg["max_abs_difference"]<2e-9
 assert meta["data_sha256"]==qa["data_sha256"]==sha(D/"C128_DELAYED_PRIORITY.csv.gz")
 assert meta["summary_sha256"]==sha(D/"C128_SUMMARY.json")
 w=s["water_first_20kW_d0"];a=s["air_first_20kW_d0"]
 wd=s["water_first_20kW_d2"];ad=s["air_first_20kW_d2"]
 assert w["cap_binding_quarters"]>0 and a["cap_binding_quarters"]>0
 findings=f"""# C128: competing thermal source priorities with command transport delay

## Change
An isolated 15-minute synthetic heat-dispatch model now compares water-first
and air-first policies at **20 and 25 kW** source caps, with **0 or 30 minutes**
of command transport delay. Also replays a 150 kW zero-delay baseline.
Ten scenarios, 672 quarters each (7 days), total **6720 transitions**.
Thermal source kW is not electrical draw; no COP has been modeled.

## Observed results at 20 kW (7 days)
| Priority | Delay | Final pool C | Air heat MWh | Binding quarters |
|---|---:|---:|---:|---:|
| Water-first | 0 min | {w['final_pool_C']:.6f} | {w['air_heat_MWh']:.6f} | {int(w['cap_binding_quarters'])} |
| Air-first | 0 min | {a['final_pool_C']:.6f} | {a['air_heat_MWh']:.6f} | {int(a['cap_binding_quarters'])} |
| Water-first | 30 min | {wd['final_pool_C']:.6f} | {wd['air_heat_MWh']:.6f} | {int(wd['cap_binding_quarters'])} |
| Air-first | 30 min | {ad['final_pool_C']:.6f} | {ad['air_heat_MWh']:.6f} | {int(ad['cap_binding_quarters'])} |

Priority now changes allocation and pool temperature; 150 kW replay does not.
Delay uses a cold-start FIFO of two 15-minute commands; **not** measured actuator
inertia. Air heating has a live-temperature safety interlock, so stale air commands
are clipped by the current air request. Pool commands can remain active after
a thermostat switch, explicitly exposing possible delay overshoot.
Cooling remains independent of recovered source.

## Verification
Six embedded tests; 6720 independent CSV row checks with energy/mass,
FIFO, source-cap, thermostat, priority and continuity reconstruction;
nine negative controls. Separate regression matched 1344 baseline
C127 quarters across 6720 numeric fields, max difference {reg['max_abs_difference']:.3g}.
The energy/mass balances verify implementation consistency, not field validity.

## Limitations and next step
All parameters and weather are synthetic; no validated HVAC curves, electrical
COP, intra-step switching or field instrumentation. Primary source signoffs
remain 0/31. Next: implement finite thermal actuator slew-rate and explicit
electrical input/COP, then run robust sensitivity on cap and delay without
altering SCADA/MATLAB or shared runtime.
"""
 once("C128_FINDINGS.md",findings)
 names=("c128_delayed_priority.py","qa_c128_independent.py","qa_c128_regression.py",
 "C128_DELAYED_PRIORITY.csv.gz","C128_SUMMARY.json","C128_METADATA.json",
 "C128_INDEPENDENT_QA.json","C128_REGRESSION_QA.json","C128_FINDINGS.md")
 manifest={"schema":"C128_SHA256_MANIFEST_V1","task_id":TASK,
 "files":{n:sha(D/n) for n in names}}
 jonce("SHA256_MANIFEST_C128.json",manifest)
 ev={"task_id":TASK,"actor":ACTOR,"artifact":str(D/"C128_DELAYED_PRIORITY.csv.gz"),
 "sha256":meta["data_sha256"],"qa":str(D/"C128_INDEPENDENT_QA.json"),
 "regression":str(D/"C128_REGRESSION_QA.json"),
 "findings":str(D/"C128_FINDINGS.md"),"manifest":str(D/"SHA256_MANIFEST_C128.json"),
 "manifest_sha256":sha(D/"SHA256_MANIFEST_C128.json"),
 "rows":6720,"scenarios":10,"negative_controls":9,"synthetic":True,
 "field_validated":False,"source_signoffs_added":0,
 "next":"Finite actuator slew-rate and explicit electrical COP, with robust cap/delay sensitivity; no shared runtime edits."}
 jonce("EVIDENCE_C128.json",ev)
 guard()
 with registry._open() as db:
  row=db.execute("SELECT status FROM tasks WHERE id=?",(TASK,)).fetchone()
  if not row or row["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
  prior=db.execute("SELECT id FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchone()
  if prior:eid=prior["id"]
  else:
   registry._event(db,TASK,"evidence",ACTOR,{"artifact":ev["artifact"],"sha256":ev["sha256"],
    "qa":ev["qa"],"regression":ev["regression"],"findings":ev["findings"],
    "manifest":ev["manifest"],"evidence":str(D/"EVIDENCE_C128.json"),
    "qa_result":"6720 independent rows + 9 negative controls + 6720 baseline numeric comparisons PASS",
    "synthetic":True,"not_field_validated":True,"next":ev["next"]})
   eid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
 jonce("CANONICAL_RECEIPT_C128.json",{"task_id":TASK,"event_id":eid,"actor":ACTOR,
 "evidence_sha256":sha(D/"EVIDENCE_C128.json"),"manifest_sha256":ev["manifest_sha256"]})
 with registry._open() as db:
  back=db.execute("SELECT actor FROM task_events WHERE id=? AND task_id=?",(eid,TASK)).fetchone()
 assert back and back["actor"]==ACTOR
 now=datetime.datetime.now().astimezone().isoformat()
 handoff=f"""# C128 FINAL_HANDOFF | {now}

## Live preflight
SynapseMCP Web ping success 2026-10-31 11:50:42 CET, control_enabled true.
Owner NIGHT_HANDOFF, AGENTS, INDEX, Kernel v1.2 and isolation, lifecycle,
concurrency skills read. At 11:51 CET RAM free 3769/16203 MiB,
VRAM 1224/8188 MiB, GPU 0%. STOP/PAUSE absent in checked roots.
Existing Jarvice/Synapse processes, scheduled tasks and Git worktrees
inspected; preserved. Desktop Commander monthly quota exhausted.
No new Codex, GPU jobs, permanent workers, GUI, OAuth, VRS or SCADA edits.

## Engineering evidence
10 isolated 7-day synthetic scenarios, 6720 quarter-hour transitions,
6 embedded tests, 6720 independent QA rows, 9 negative controls PASS.
Cross-version C127 regression: 1344 quarters, 6720 numeric values,
maximum difference {reg['max_abs_difference']}. Data SHA256 {ev['sha256']}.
Manifest SHA256 {ev['manifest_sha256']}.
Water/air priorities genuinely compete at 20 and 25 thermal kW.
Model not physically validated, signoffs 0/31.

## Synapse registry
Existing card {TASK}, evidence event {eid} read back, task status queued.
No new task, worker, or GPU job created.

## Exact next executable step
Model finite actuator slew rate and source electrical COP; test against
0/30-minute delay and thermal cap envelope. Independently validate
equipment curves and all 31 primary-source signoffs before deployment.
"""
 once("FINAL_HANDOFF.md",handoff)
 print(json.dumps({"status":"PASS","event_id":eid,"readback":"VERIFIED","task_status":"queued",
 "data_sha256":ev["sha256"],"manifest_sha256":ev["manifest_sha256"],
 "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),"files_in_manifest":len(names)},indent=2))
if __name__=="__main__":main()
