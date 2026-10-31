"""Independent A29 physics/energy cross-check; synthetic fixture only."""
import csv
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

def check(folder: Path):
    cal=json.loads((folder/"cal_report.json").read_text())
    meta=json.loads((folder/"holdout_meta.json").read_text())
    report=json.loads((folder/"HOLDOUT_EVIDENCE.json").read_text())
    with (folder/"holdout.csv").open(newline="") as f:
        rows=list(csv.DictReader(f))
    rho=meta["density_kg_m3"];cp=meta["specific_heat_kj_kg_K"]
    bias=cal["residual_bias"];cov=cal["residual_sample_covariance"]
    def heat(vals):
        flow,hot,cold=vals
        return rho*cp*flow*(hot-cold)/3600
    model=[];meter=[];std=[]
    for r in rows:
        x=[float(r["flow_read_m3h"])-bias["flow"],float(r["hot_read_C"])-bias["hot"],float(r["cold_read_C"])-bias["cold"]]
        model.append(heat(x));meter.append(float(r["meter_kw"]))
        # Independent finite-difference sensitivity instead of A29's analytic Jacobian
        j=[]
        for k in range(3):
            h=1e-4 if k==0 else 1e-5
            a=x.copy();b=x.copy();a[k]+=h;b[k]-=h
            j.append((heat(a)-heat(b))/(2*h))
        v=sum(j[i]*cov[i][k]*j[k] for i in range(3) for k in range(3))
        std.append(math.sqrt(v+meta["meter_std_uncertainty_kw"]**2))
    ts=[datetime.fromisoformat(r["time_utc"]) for r in rows]
    e=sum(model[i]*(ts[i+1]-ts[i]).total_seconds()/3600 for i in range(len(rows)-1))
    diff=[a-b for a,b in zip(model,meter)]
    assert abs(e-report["model_energy_kwh_left_rectangle"])<1e-9
    assert abs(statistics.mean(diff)-report["mean_bias_kw"])<1e-9
    assert abs(math.sqrt(statistics.mean(x*x for x in diff))-report["rmse_kw"])<1e-9
    assert abs(statistics.mean(std)-report["pointwise_combined_standard_uncertainty_kw"]["mean"])<1e-6
    assert report["release_allowed"] is False
    assert report["source_class"]=="SYNTHETIC_TEST"
    for key, filename in (("calibration_report_sha256","cal_report.json"),("holdout_csv_sha256","holdout.csv"),("holdout_metadata_sha256","holdout_meta.json")):
        assert report[key]==hashlib.sha256((folder/filename).read_bytes()).hexdigest()
    return {"status":"PASS","checks":8,"sample_count":len(rows),
            "independent_energy_kwh":e,"independent_rmse_kw":math.sqrt(statistics.mean(x*x for x in diff)),
            "independent_pointwise_u_mean_kw":statistics.mean(std),"release_allowed":False}

if __name__=="__main__":
    result=check(Path(sys.argv[1]))
    print(json.dumps(result,indent=2))
