"""Independent read-only QA of C118 quarter-hour sensitivity ledger."""
import csv,gzip,hashlib,json,math,random
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
META=json.loads((D/"C118_METADATA.json").read_text(encoding="utf-8"))
P=D/"C118_SUBHOUR_STRESS.csv.gz"
S=D/"C118_SUMMARY.csv"
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def close(a,b,tol=5e-8):
    return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def check_row(r):
    x={k:float(v) for k,v in r.items() if k not in ("policy","control","pattern","time")}
    tests=[
      0<=x["RH_min_15m"]<=x["RH_start"]+1e-9,
      x["RH_peak_15m"]>=x["RH_start"]-1e-9,
      x["RH_min_15m"]<=x["RH_end_15m"]<=x["RH_peak_15m"]+1e-9,
      x["RH_peak_15m"]<=1+1e-9,
      close(x["storage_delta_kg"],x["vent_net_kg"]+x["evap_kg"]-x["dehum_kg"]+x["humid_kg"]-x["condensate_kg"]),
      abs(x["mass_residual_kg"])<1e-8,
      x["condensate_kg"]>=-1e-10,
      x["saturated_quarters"] in (0,1,2,3,4),
      x["hidden_high65"] in (0,1),
      x["hidden_low45"] in (0,1),
      x["hidden_high65"]==int(x["RH_start"]<=.65 and x["RH_end_15m"]<=.65 and x["RH_peak_15m"]>.65),
      x["hidden_low45"]==int(x["RH_start"]>=.45 and x["RH_end_15m"]>=.45 and x["RH_min_15m"]<.45),
      x["evap_kg"]>=0 and x["dehum_kg"]>=0 and x["humid_kg"]>=0]
    if not all(tests):raise AssertionError("ROW_FAIL_"+str([i for i,v in enumerate(tests) if not v]))
    return x,len(tests)
def numerical(w0,ws,net,wsat,steps=3000):
    M=3540.;V=3540.;dt=.25/steps
    w=w0;vent=0.;cond=0.
    for _ in range(steps):
        rate=(V*(ws-w)+net)/M
        tentative=w+rate*dt
        midpoint=(w+min(wsat,tentative))/2
        vent+=V*(ws-midpoint)*dt
        if tentative>wsat:
            cond+=M*(tentative-wsat)
            w=wsat
        else:w=tentative
    return w,vent,cond
def independent_numerical():
    import importlib.util
    spec=importlib.util.spec_from_file_location("c118_test",D/"c118_subhour_rh.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rng=random.Random(118)
    sat=.026
    count=0;maxw=0.;maxvent=0.;maxcond=0.
    for i in range(60):
        w0=rng.uniform(.004,.025)
        ws=rng.uniform(.003,.023)
        net=rng.uniform(-5,400)
        try:a=m.exact_quarter(w0,ws,net,sat)
        except ValueError:continue
        b=numerical(w0,ws,net,sat)
        maxw=max(maxw,abs(a[0]-b[0]))
        maxvent=max(maxvent,abs(a[1]-b[1]))
        maxcond=max(maxcond,abs(a[2]-b[2]))
        if abs(a[0]-b[0])>5e-6 or abs(a[1]-b[1])>.02 or abs(a[2]-b[2])>.02:
            raise AssertionError("INDEPENDENT_ODE_MISMATCH_"+str(i))
        count+=1
    assert count>=50
    return {"cases":count,"max_w_abs":maxw,"max_vent_kg":maxvent,"max_cond_kg":maxcond}
def run():
    assert META["synthetic"] and not META["field_validated"] and META["source_signoffs_added"]==0
    assert sha(P)==META["hourly_sha256"] and sha(S)==META["summary_sha256"]
    groups=defaultdict(lambda:defaultdict(float))
    last={};same_hour={};n=0;checks=0;continuity=0;source_match=0
    with gzip.open(P,"rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            x,c=check_row(r);n+=1;checks+=c
            key=(r["policy"],r["control"],r["pattern"])
            if key in last:
                if not close(last[key],x["RH_start"],5e-9):raise AssertionError("STATE_DISCONTINUITY")
                continuity+=1
            last[key]=x["RH_end_15m"]
            key_hour=(r["policy"],r["control"],r["time"])
            vals=(x["evap_kg"],x["dehum_kg"],x["humid_kg"],x["supply_w"])
            if key_hour in same_hour:
                if any(not close(a,b,1e-10) for a,b in zip(vals,same_hour[key_hour])):
                    raise AssertionError("HOURLY_INPUT_DRIFT")
                source_match+=1
            else:same_hour[key_hour]=vals
            if r["pattern"]=="flat" and r["control"] in ("ideal","capacity_C114"):
                if not close(x["RH_end_15m"],x["RH_C116_hour_end"],5e-9):
                    raise AssertionError("BASELINE_REGRESSION")
            g=groups[key];g["n"]+=1
            g["hidden_high65"]+=x["hidden_high65"]
            g["hidden_low45"]+=x["hidden_low45"]
            g["condensate_kg"]+=x["condensate_kg"]
            g["saturated_quarters"]+=x["saturated_quarters"]
            g["hours_peak_high65"]+=int(x["RH_peak_15m"]>.65)
            g["hours_endpoint_high65"]+=int(x["RH_end_15m"]>.65)
    assert n==210240 and len(groups)==24 and len(same_hour)==52560
    assert all(g["n"]==8760 for g in groups.values())
    summary={}
    with S.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            key=(r["policy"],r["control"],r["pattern"])
            if key in summary:raise AssertionError("DUPLICATE_SUMMARY")
            summary[key]=r
    assert set(summary)==set(groups)
    summary_checks=0
    for key,g in groups.items():
        for field,value in g.items():
            if not close(float(summary[key]["hours" if field=="n" else field]),value,1e-7):
                raise AssertionError("SUMMARY_DRIFT_"+str((key,field)))
            summary_checks+=1
    assert groups[("water_first","ideal","front_loaded")]["hidden_high65"]>0
    assert groups[("water_first","ideal","flat")]["hidden_high65"]==0
    # Deliberate corruption must fail independent conservation and bound checks.
    with gzip.open(P,"rt",encoding="utf-8",newline="") as f:
        good=next(csv.DictReader(f))
    check_row(good)
    negatives=0
    for col,bad in (("storage_delta_kg","999"),("RH_peak_15m","1.3"),
                    ("hidden_high65","1"),("condensate_kg","-1")):
        altered=dict(good);altered[col]=bad
        try:check_row(altered)
        except AssertionError:negatives+=1
        else:raise AssertionError("NEGATIVE_NOT_REJECTED_"+col)
    numerical_result=independent_numerical()
    report={"status":"PASS","rows":n,"groups":len(groups),"independent_row_checks":checks,
            "continuity_checks":continuity,"shared_hourly_input_checks":source_match*4,
            "summary_checks":summary_checks,"negative_controls":negatives,
            "numerical_crosscheck":numerical_result,"source_sha256":META["source_sha256"],
            "artifact_sha256":META["hourly_sha256"]}
    with (D/"C118_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":run()
