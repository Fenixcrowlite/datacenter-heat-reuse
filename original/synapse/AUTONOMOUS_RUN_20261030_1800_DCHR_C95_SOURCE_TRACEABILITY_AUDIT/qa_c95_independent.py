"""Independent C95 audit QA; does not import the generator."""
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path
D=Path(__file__).resolve().parent
P=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\sources")
C94=D.parent/"AUTONOMOUS_RUN_20261030_1755_DCHR_C94_HX_TEMPERATURE_ENVELOPE"/"C94_METADATA.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    report=json.loads((D/"C95_AUDIT.json").read_text(encoding="utf-8"))
    with (D/"C95_DRIFT_MATRIX.csv").open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    c94=json.loads(C94.read_text(encoding="utf-8"))
    yaml=(P/"parameter_registry.yaml").read_text(encoding="utf-8")
    catalog=(P/"source_catalog.md").read_text(encoding="utf-8")
    checks=[]
    def ok(name,pred):
        if not pred:raise AssertionError(name)
        checks.append(name)
    pins=report["input_sha256"]
    ok("catalog_hash",sha(P/"source_catalog.md")==pins["source_catalog.md"])
    ok("registry_hash",sha(P/"parameter_registry.yaml")==pins["parameter_registry.yaml"])
    ok("trace_hash",sha(P/"traceability_matrix_v0_2.csv")==pins["traceability_matrix_v0_2.csv"])
    ok("C94_hash",sha(C94)==pins["C94_METADATA.json"])
    ok("catalog_31_ordered",list(map(int,re.findall(r"(?m)^(\d+)\.\s",catalog)))==list(range(1,32)))
    ok("report_31",report["catalog_entries_verified"]==31)
    ok("not_signoffs",report["primary_source_signoffs_added"]==0 and report["catalog_not_formal_signoff"])
    ok("synthetic",report["C94_synthetic"] and c94["synthetic"] and not c94["measured"])
    ok("matrix_8",len(rows)==report["drift_rows"]==8)
    ok("unique_parameters",len(set(r["parameter"] for r in rows))==8)
    ok("matrix_hash",sha(D/"C95_DRIFT_MATRIX.csv")==report["matrix_sha256"])
    counts=Counter(r["verdict"] for r in rows)
    ok("verdict_counts",dict(counts)==report["verdict_counts"])
    ok("outside_temp",set(c94["assumptions"]["source_inlet_C"])=={18,25,35} and
       all(not 38<=t<=50 for t in c94["assumptions"]["source_inlet_C"]))
    ok("outside_eta",c94["assumptions"]["carnot_efficiency_assumed"]==0.35 and not 0.4<=0.35<=0.5)
    ok("canonical_present","source_temperature_C_baseline: {value: 35, class: D}" in yaml and
       "carnot_efficiency: {value: 0.45, class: D}" in yaml)
    ok("no_false_verified",all(r["class_C94"]=="D" and
       r["verdict"] not in ("SIGNED_OFF","MEASURED","VALIDATED") for r in rows))
    out={"schema":"C95_INDEPENDENT_QA_V1","status":"PASS",
         "checks":len(checks),"passed":checks,"catalog_sources":31,
         "source_signoffs_added":0,"matrix_sha256":report["matrix_sha256"]}
    (D/"C95_INDEPENDENT_QA.json").write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(f"C95 INDEPENDENT QA {len(checks)}/{len(checks)} PASS")
if __name__=="__main__":run()
