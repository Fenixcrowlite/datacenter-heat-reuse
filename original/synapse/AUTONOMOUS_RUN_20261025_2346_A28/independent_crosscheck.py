"""Independent A28 cross-check with stdlib statistics and A27 PSD gate."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
A27=HERE.parent/"AUTONOMOUS_RUN_20261025_2252_A27"/"metrology_psd_hardening.py"
SOURCE=HERE/"example_synthetic"/"paired.csv"
EVIDENCE=HERE/"FIELD_GATE_EVIDENCE.json"


def main():
    data=json.loads(EVIDENCE.read_text(encoding="utf8"))
    rows=list(csv.DictReader(SOURCE.open(newline="",encoding="utf8")))
    cols=[]
    for k in ("flow","hot","cold"):
        cols.append([float(r[k+"_read_m3h" if k=="flow" else k+"_read_C"])
                     -float(r[k+"_ref_m3h" if k=="flow" else k+"_ref_C"]) for r in rows])
    cov=[[statistics.covariance(cols[i],cols[j]) for j in range(3)] for i in range(3)]
    checks=[]
    checks.append(("synthetic_not_released",data["source_class"]=="SYNTHETIC_TEST" and not data["release_allowed"]))
    checks.append(("n32",len(rows)==data["sample_count"]==32))
    checks.append(("csv_sha",hashlib.sha256(SOURCE.read_bytes()).hexdigest()==data["csv_sha256"]))
    for i in range(3):
        checks.append(("bias_"+str(i),math.isclose(statistics.mean(cols[i]),list(data["residual_bias"].values())[i],abs_tol=1e-12)))
        for j in range(3):
            checks.append((f"cov_{i}_{j}",math.isclose(cov[i][j],data["residual_sample_covariance"][i][j],rel_tol=1e-10,abs_tol=1e-12)))
    spec=importlib.util.spec_from_file_location("a27_independent",A27)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate_covariance_psd(cov)
    checks.append(("a27_psd",True))
    if not all(ok for _,ok in checks):
        raise AssertionError([name for name,ok in checks if not ok])
    result={"status":"PASS","checks":len(checks),"a27_sha256":hashlib.sha256(A27.read_bytes()).hexdigest(),
            "source_class":"SYNTHETIC_TEST","field_calibration_verified":False}
    target=HERE/"INDEPENDENT_QA.json"
    if target.exists(): raise FileExistsError(target)
    target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print("INDEPENDENT_QA_PASS",len(checks))


if __name__=="__main__":main()
