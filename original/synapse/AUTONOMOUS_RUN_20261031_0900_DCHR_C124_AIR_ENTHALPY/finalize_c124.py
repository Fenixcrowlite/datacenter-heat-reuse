"""Finalize isolated C124 with SHA evidence in existing DataCenter card."""
import datetime,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent; S=D.parent.parent
sys.path.insert(0,str(S))
import registry
TASK="scc-2aab24704c2bd0";ACTOR="chatgpt-dchr-c124-moist-air-20261031-0900"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,S,S/"recovery",Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for f in FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def once(name,obj):
    p=D/name;txt=json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if p.exists():
        if p.read_text(encoding="utf-8")!=txt:raise RuntimeError("DRIFT "+name)
    else:p.write_text(txt,encoding="utf-8")
def main():
    guard()
    m=json.loads((D/"C124_METADATA.json").read_text(encoding="utf-8"))
    q=json.loads((D/"C124_INDEPENDENT_QA.json").read_text(encoding="utf-8"))
    s=json.loads((D/"C124_SUMMARY.json").read_text(encoding="utf-8"))
    assert m["task_id"]==TASK and m["synthetic"] and not m["field_validated"]
    assert q["status"]=="PASS" and q["rows"]==140160 and q["negative_controls"]==4
    assert m["data_sha256"]==q["data_sha256"]==sha(D/"C124_QUARTER_AIR.csv.gz")
    assert m["summary_sha256"]==sha(D/"C124_SUMMARY.json")
    findings="""# C124: 15-minute moist-air enthalpy and temperature

Implemented a self-contained synthetic indoor-air state with moist-air
enthalpy H = m_dry [1.006 T + w (2501 + 1.86 T)] kJ.
Per 15-minute step: prescribed C116 pool evaporation and latent transfer,
ventilation dry-air/moisture/enthalpy exchange, capped dehumidification and
humidification, capped proportional HVAC, and saturation condensation
with explicit liquid condensate enthalpy export.

Four scenarios (5/45.66 kg/h humidity capacity x 5/15 kW HVAC cap);
8,760 hours x 4 quarters x 4 scenarios = 140,160 rows. Source C116 SHA
pinned and unchanged. 7 embedded selftests, 140,160 independent
mass/enthalpy/state/continuity checks and 4 negative controls PASS.
CSV rounding causes small differences in recomputed H; independent QA
uses 2e-5 kJ tolerance and preserves rejected initial QA source.

Results (synthetic): dehum5_hvac5: 18,614 quarters RH>65%;
dehum45.66_hvac5: 8,760 quarters RH>65%. Total saturation
condensation across scenarios: 19,710 quarter-steps. High humidity is
a stress-test artifact, not real equipment sizing. Results depend strongly
on first-quarter evaporation pulse, fixed supply 26 C / 55% RH, and the
simplified dehumidifier energy export model. No return coupling to pool,
no wall capacitance, no measured HVAC curves, no field validation.
Energy closure is a mathematical bookkeeping test, NOT physical validation.

Next: replace assumed supply and dehumidifier heat-rejection models with
measured/traceable equipment curves, add pool feedback and compare with
field measurements. Do not edit original MATLAB/SCADA or C116.
"""
    (D/"C124_FINDINGS.md").write_text(findings,encoding="utf-8")
    files=("c124_air_enthalpy.py","qa_c124_independent.py",
      "qa_c124_independent_rejected_v1.py","C124_QUARTER_AIR.csv.gz",
      "C124_SUMMARY.json","C124_METADATA.json","C124_INDEPENDENT_QA.json",
      "C124_RUN_LOG.txt","C124_QA_LOG.txt","C124_FINDINGS.md","finalize_c124.py")
    assert all((D/f).is_file() for f in files)
    once("SHA256_MANIFEST_C124.json",{"schema":"C124_MANIFEST_V1","task_id":TASK,
      "qa":"PASS","files":{f:{"sha256":sha(D/f),"bytes":(D/f).stat().st_size} for f in files}})
    ev={"schema":"C124_EVIDENCE_V1","task_id":TASK,"actor":ACTOR,
      "artifact":str(D/"C124_QUARTER_AIR.csv.gz"),"sha256":m["data_sha256"],
      "qa":str(D/"C124_INDEPENDENT_QA.json"),"findings":str(D/"C124_FINDINGS.md"),
      "manifest":str(D/"SHA256_MANIFEST_C124.json"),
      "manifest_sha256":sha(D/"SHA256_MANIFEST_C124.json"),
      "synthetic":True,"field_validated":False,"source_signoffs_added":0,
      "next":"Replace synthetic supply and dehumidifier heat models with traceable hardware curves; add pool feedback."}
    once("EVIDENCE_C124.json",ev)
    guard()
    with registry._open() as db:
        row=db.execute("select status from tasks where id=?",(TASK,)).fetchone()
        if not row or row["status"]!="queued":raise RuntimeError("TASK_STATE_DRIFT")
        prior=db.execute("select id from task_events where task_id=? and kind='evidence' and actor=?",(TASK,ACTOR)).fetchone()
        if prior:eid=prior["id"]
        else:
            registry._event(db,TASK,"evidence",ACTOR,{"artifact":ev["artifact"],
              "sha256":ev["sha256"],"qa":ev["qa"],"findings":ev["findings"],
              "manifest":ev["manifest"],"evidence":str(D/"EVIDENCE_C124.json"),
              "qa_result":"140160 quarter rows, 7 selftests, 4 negative controls PASS",
              "synthetic":True,"not_field_validated":True,"next":ev["next"]})
            eid=db.execute("select last_insert_rowid()").fetchone()[0]
    once("CANONICAL_RECEIPT_C124.json",{"task_id":TASK,"event_id":eid,
      "actor":ACTOR,"evidence_sha256":sha(D/"EVIDENCE_C124.json"),
      "manifest_sha256":sha(D/"SHA256_MANIFEST_C124.json")})
    with registry._open() as db:
        back=db.execute("select actor from task_events where id=? and task_id=?",(eid,TASK)).fetchone()
    assert back and back["actor"]==ACTOR
    handoff=f"""# C124 FINAL_HANDOFF | {datetime.datetime.now().astimezone().isoformat()}

## Preflight
Read owner governance, NIGHT_HANDOFF, AGENTS, INDEX and personal Kernel v1.2. SynapseMCP Web live 08:48 CET, STOP/PAUSE absent in checked roots. No new Codex, persistent worker, GPU job, GUI, OAuth, VRS, MATLAB, SCADA or other-owner worktree changes.

## Engineering
Synthetic 15-minute moist-air temperature, humidity and enthalpy state with ventilation, latent transfer, dehumidifier, humidifier, capped HVAC and saturation condensation. Four scenarios x 8760 hours x 4 quarters = 140160 rows. C116 SHA pinned, unchanged.
See C124_FINDINGS.md. No real equipment validation; source signoffs 0 added.

## QA and registry
7 selftests, 140160 independent state/mass/enthalpy/continuity checks, 4 negative controls PASS. Initial overly strict CSV-rounding QA preserved.
Data SHA256 {ev['sha256']}
Manifest SHA256 {ev['manifest_sha256']}
Synapse existing task {TASK}; evidence event {eid} read back; status queued.

## Next exact step
Replace assumed 26 C / 55% RH supply and dehumidifier heat export with verified equipment curves and actual climate traces; then add return feedback to pool energy and compare field measurements. Do not treat bookkeeping conservation as physical validation.
"""
    (D/"FINAL_HANDOFF.md").write_text(handoff,encoding="utf-8")
    print(json.dumps({"event_id":eid,"readback":"VERIFIED","task_status":"queued",
      "data_sha256":ev["sha256"],"handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
      "manifest_sha256":ev["manifest_sha256"]},indent=2))
if __name__=="__main__":main()
