"""Independent final verifier; no registry mutations."""
import hashlib
import json
import sqlite3
from pathlib import Path

here=Path(__file__).resolve().parent
center=here.parent.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((here/"SHA256_MANIFEST.json").read_text(encoding="utf-8"))
hash_checks={name: (here/name).is_file() and sha(here/name)==digest for name,digest in manifest.items()}
ev=json.loads((here/"CORRELATED_METROLOGY_EVIDENCE.json").read_text(encoding="utf-8"))
mc=json.loads((here/"MONTE_CARLO_QA.json").read_text(encoding="utf-8"))
reg=json.loads((here/"REGISTRY_RESULT.json").read_text(encoding="utf-8"))
db=sqlite3.connect("file:"+str(center/"tasks.sqlite3").replace("\\","/")+"?mode=ro",uri=True)
row=db.execute("select status,stage from tasks where id=?",("scc-3d9d172beb6e1b",)).fetchone()
events=db.execute("select id,data_json from task_events where task_id=? and kind='evidence' and actor=?",
                  ("scc-3d9d172beb6e1b","chatgpt-dchr-a26-correlated-metrology-20261025-2155")).fetchall()
conditions={
    "all_manifest_hashes": all(hash_checks.values()),
    "manifest_count_8":len(manifest)==8,
    "source_hash_stable":sha(Path(ev["original_uncertainty_source_path"]))==ev["original_uncertainty_source_sha256"],
    "class_D_explicit":ev["source_class"]=="D_SYNTHETIC",
    "three_analytic_cases":len(ev["heat_cases"])==3,
    "mc_3x80000":mc["status"]=="PASS" and len(mc["cases"])==3 and all(x["n"]==80000 for x in mc["cases"].values()),
    "test_log_20": "Ran 20 tests" in (here/"TEST_LOG.txt").read_text(encoding="utf-8"),
    "task_state_preserved":row==("review","planned"),
    "single_event":len(events)==1 and events[0][0]==reg["event_id"],
    "event_evidence_hash":len(events)==1 and json.loads(events[0][1])["evidence_sha256"]==sha(here/"CORRELATED_METROLOGY_EVIDENCE.json"),
    "sqlite_quick_check":db.execute("pragma quick_check").fetchone()[0]=="ok",
    "handoff_present":(here/"HANDOFF.md").is_file(),
}
result={"status":"PASS" if all(conditions.values()) else "FAIL",
        "conditions":conditions,"manifest_file_checks":hash_checks,
        "handoff_sha256":sha(here/"HANDOFF.md"),
        "evidence_sha256":sha(here/"CORRELATED_METROLOGY_EVIDENCE.json"),
        "event_id":reg["event_id"],"task_id":reg["task_id"]}
out=here/"FINAL_VERIFY.json"
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(result["status"],sum(conditions.values()),"/",len(conditions),
      "handoff_sha256",result["handoff_sha256"])
if result["status"]!="PASS":raise SystemExit(1)
