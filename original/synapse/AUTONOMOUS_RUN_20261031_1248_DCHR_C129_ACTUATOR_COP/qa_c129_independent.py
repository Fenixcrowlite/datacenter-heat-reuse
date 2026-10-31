"""Independent CSV reconstruction and C128 regression for C129; no model import."""
import csv,gzip,hashlib,json,math
from pathlib import Path
D=Path(__file__).resolve().parent
BASE=D.parent/"AUTONOMOUS_RUN_20261031_1153_DCHR_C128_DELAYED_PRIORITY"
FIELDS=("pool_T1","air_T1","w1","pool_heat_kJ","air_heat_kJ","RH1")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def f(r,k):return float(r[k])
def close(a,b,tol=1e-6):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>tol:raise ValueError(f"DIFF {a} {b}")
def check(r,previous=None):
    for key in ("source_kw","COP","source_desired_kJ","source_output_kJ","source_bypass_kJ",
                "electric_kJ","recovered_kJ","pool_heat_kJ","air_heat_kJ","source_cap_kJ",
                "lag_pool_kJ","safe_air_kJ","pool_T0","pool_T1","air_T0","air_T1","w0","w1",
                "RH1","pool_residual_kJ","air_residual_kJ","combined_residual_kJ",
                "air_mass_residual_kg"):
        if not math.isfinite(f(r,key)):raise ValueError("NONFINITE_"+key)
    cop=f(r,"COP");cap=f(r,"source_cap_kJ");output=f(r,"source_output_kJ")
    desired=f(r,"source_desired_kJ");qp=f(r,"pool_heat_kJ");qa=f(r,"air_heat_kJ")
    lag=f(r,"lag_pool_kJ");air=f(r,"safe_air_kJ");bypass=f(r,"source_bypass_kJ")
    if cop<=1 or cap<=0 or min(output,desired,qp,qa,bypass)<-1e-7:raise ValueError("DOMAIN")
    close(cap,f(r,"source_kw")*900.)
    close(desired,min(cap,lag+air))
    if output>cap+1e-7:raise ValueError("SOURCE_CAP")
    if r["ramp_kw_per_quarter"]=="ideal":expected=desired
    else:
        ramp=float(r["ramp_kw_per_quarter"])
        if not math.isfinite(ramp) or ramp<=0:raise ValueError("RAMP")
        prior=0. if previous is None else f(previous,"source_output_kJ")
        expected=min(cap,max(0.,max(prior-ramp*900.,min(prior+ramp*900.,desired))))
    close(output,expected)
    available=min(output,desired)
    if r["priority"]=="water_first":
        exp_p=min(lag,available);exp_a=min(air,available-exp_p)
    elif r["priority"]=="air_first":
        exp_a=min(air,available);exp_p=min(lag,available-exp_a)
    else:raise ValueError("PRIORITY")
    close(qp,exp_p);close(qa,exp_a)
    close(output,qp+qa+bypass)
    close(f(r,"electric_kJ"),output/cop)
    close(f(r,"recovered_kJ"),output*(1-1/cop))
    close(output,f(r,"electric_kJ")+f(r,"recovered_kJ"))
    close(f(r,"source_unused_kJ"),cap-qp-qa)
    if not 0<f(r,"pool_T1")<45 or not 0<f(r,"RH1")<=1:raise ValueError("STATE")
    for k in ("pool_residual_kJ","air_residual_kJ","combined_residual_kJ"):
        if abs(f(r,k))>1e-5:raise ValueError("ENERGY_RESIDUAL")
    if abs(f(r,"air_mass_residual_kg"))>1e-7:raise ValueError("MASS_RESIDUAL")
    if previous:
        for k0,k1 in (("pool_T0","pool_T1"),("air_T0","air_T1"),("w0","w1")):
            close(f(r,k0),f(previous,k1),2e-9)
        q=int(r["quarter"]);prevq=int(previous["quarter"])
        if q!=(prevq+1)%4:raise ValueError("QUARTER_SEQUENCE")
def negative_controls(sample,prev):
    tests=[
        ("BAD_COP",{"COP":"1"}),
        ("BAD_ELECTRIC",{"electric_kJ":str(f(sample,"electric_kJ")+10)}),
        ("BAD_RECOVERED",{"recovered_kJ":str(f(sample,"recovered_kJ")+10)}),
        ("BAD_BYPASS",{"source_bypass_kJ":str(f(sample,"source_bypass_kJ")+10)}),
        ("BAD_SOURCE",{"source_output_kJ":str(f(sample,"source_cap_kJ")+100)}),
        ("BAD_PRIORITY",{"priority":"invalid"}),
        ("BAD_CONTINUITY",{"pool_T0":str(f(sample,"pool_T0")+0.1)}),
        ("BAD_RAMP",{"ramp_kw_per_quarter":"-2"}),
        ("BAD_BALANCE",{"combined_residual_kJ":"2"}),
        ("BAD_MASS",{"air_mass_residual_kg":"0.1"}),
        ("BAD_COMMAND",{"source_desired_kJ":str(f(sample,"source_desired_kJ")+1)}),
    ]
    passed=0
    for name,changes in tests:
        r=dict(sample);r.update(changes)
        try:check(r,prev)
        except (ValueError,OverflowError):passed+=1
        else:raise AssertionError("NEGATIVE_NOT_REJECTED_"+name)
    return passed
def main():
    data=D/"C129_ACTUATOR_COP.csv.gz"
    meta=json.loads((D/"C129_METADATA.json").read_text(encoding="utf-8"))
    if sha(data)!=meta["data_sha256"]:raise AssertionError("DATA_SHA")
    if sha(D/"C129_SUMMARY.json")!=meta["summary_sha256"]:raise AssertionError("SUMMARY_SHA")
    prior={}
    with gzip.open(BASE/"C128_DELAYED_PRIORITY.csv.gz","rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            prior[(r["scenario"],r["time"],r["quarter"])]=r
    if len(prior)!=6720:raise AssertionError("C128_ROWS")
    previous={};rows=0;regression=0;max_delta=0.;ramp_limited=0
    sample=None;sampleprev=None;seen={}
    with gzip.open(data,"rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            key=r["scenario"];p=previous.get(key)
            check(r,p)
            if sample is None and p is not None and r["ramp_kw_per_quarter"]!="ideal":
                sample=dict(r);sampleprev=dict(p)
            previous[key]=r;seen[key]=seen.get(key,0)+1;rows+=1
            if ffloat(r,"source_output_kJ")+1e-7<ffloat(r,"source_desired_kJ"):
                ramp_limited+=1
            if r["ramp_kw_per_quarter"]=="ideal":
                baseline=key.split("_r")[0]
                ref=prior.get((baseline,r["time"],r["quarter"]))
                if ref is None:raise AssertionError("MISSING_C128_BASELINE")
                for k in FIELDS:
                    delta=abs(float(ref[k])-float(r[k]))
                    max_delta=max(max_delta,delta)
                    if delta>2e-9:raise AssertionError("C128_REGRESSION_"+k)
                regression+=1
    if rows!=meta["rows"] or len(seen)!=meta["scenarios"] or any(n!=672 for n in seen.values()):
        raise AssertionError("ROW_COUNTS")
    if regression!=12096 or ramp_limited==0:raise AssertionError("REGRESSION_OR_RAMP")
    if sample is None:raise AssertionError("NO_NEGATIVE_SAMPLE")
    negative=negative_controls(sample,sampleprev)
    if negative!=11:raise AssertionError("NEGATIVE_COUNT")
    qa={"status":"PASS","independent":True,"rows":rows,"scenarios":len(seen),
        "negative_controls":negative,"regression_numeric_fields":regression*len(FIELDS),
        "regression_rows":regression,"regression_max_abs_delta":max_delta,
        "ramp_limited_rows":ramp_limited,"data_sha256":sha(data),
        "checked":"source cap, FIFO-derived command, slew, priority, bypass, electric+recovered, balances, state continuity, exact C128 ideal-ramp regression"}
    (D/"C129_INDEPENDENT_QA.json").write_text(json.dumps(qa,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(qa,indent=2))
def ffloat(r,k):return float(r[k])
if __name__=="__main__":main()
