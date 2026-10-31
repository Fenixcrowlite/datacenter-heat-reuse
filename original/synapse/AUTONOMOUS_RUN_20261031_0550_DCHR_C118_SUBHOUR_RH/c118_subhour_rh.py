"""C118: isolated synthetic 15-minute humidity pulse stress test.
Hourly C116 forcing is replayed, not a new coupled pool/air design.
No source, MATLAB, SCADA, or shared GUI modifications.
"""
from __future__ import annotations
import csv, gzip, hashlib, importlib.util, json, math, os
from pathlib import Path
from collections import defaultdict

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C116=REC/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
C106=REC/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
C104=REC/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"c104_psychrometric.py"
PINS={"C116":"6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf",
      "C106":"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
      "C104":"1bbe6dbbf18f04c5bc0ef7b407efdbbebbf60ec496a1b5178ee66ab3bf7a1600"}
TASK="scc-2aab24704c2bd0"
M=3000.0*1.18
V=3000.0*1.18
K=V/M
DT=0.25
PATTERNS={"flat":(1.,1.,1.,1.),"front_loaded":(4.,0.,0.,0.),
          "back_loaded":(0.,0.,0.,4.),"double_pulse":(2.,0.,2.,0.)}
FIELDS=("policy","control","pattern","time","RH_start","RH_min_15m",
        "RH_peak_15m","RH_end_15m","RH_C116_hour_end","evap_kg",
        "dehum_kg","humid_kg","supply_w","condensate_kg",
        "vent_net_kg","storage_delta_kg","mass_residual_kg",
        "saturated_quarters","hidden_high65","hidden_low45")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def guard():
    for root in (D,REC,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def module(path):
    spec=importlib.util.spec_from_file_location("c104_c118",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def rh(c104,w):
    pv=c104.P*w/(.62198+w)
    return pv/c104.sat(c104.T_IN)
def exact_quarter(w0,ws,net_kg_h,wsat,dt=DT):
    """Well-mixed ODE with exact saturation onset and continuous condensate drain.
    Returns (w_end, ventilation_kg, condensate_kg, mass_residual_kg, saturated).
    """
    if not all(math.isfinite(v) for v in (w0,ws,net_kg_h,wsat,dt)):
        raise ValueError("NONFINITE")
    if min(w0,ws,wsat,dt)<0 or dt<=0 or w0>wsat+1e-9:
        raise ValueError("INVALID_STATE")
    eq=ws+net_kg_h/V
    free_end=eq+(w0-eq)*math.exp(-K*dt)
    if free_end < -1e-10:raise ValueError("NEGATIVE_HUMIDITY")
    if free_end<=wsat+1e-13:
        end=max(0.,min(wsat,free_end))
        integ=eq*dt+(w0-eq)*(-math.expm1(-K*dt))/K
        vent=V*(ws*dt-integ)
        cond=0.
        saturated=False
    else:
        if eq<=wsat+1e-13:raise AssertionError("CROSSING_IMPOSSIBLE")
        if w0>=wsat-1e-13:
            tc=0.
        else:
            ratio=(wsat-eq)/(w0-eq)
            if not 0<ratio<=1:raise AssertionError("CROSSING_RATIO")
            tc=-math.log(ratio)/K
            if not 0<=tc<=dt+1e-10:raise AssertionError("CROSSING_TIME")
            tc=min(dt,tc)
        integ=eq*tc+(w0-eq)*(-math.expm1(-K*tc))/K+wsat*(dt-tc)
        vent=V*(ws*dt-integ)
        cond=max(0.,V*(eq-wsat)*(dt-tc))
        end=wsat
        saturated=True
    storage=M*(end-w0)
    residual=storage-(vent+net_kg_h*dt-cond)
    if abs(residual)>1e-8:raise AssertionError("MASS_CLOSURE")
    return end,vent,cond,residual,saturated
def selftest(c104):
    sat=c104.w_ratio(c104.T_IN,1)
    a=exact_quarter(.01,.01,0,sat)
    assert abs(a[0]-.01)<1e-14 and abs(a[3])<1e-10
    b=exact_quarter(.01,.01,400,sat)
    assert b[2]>0 and abs(b[0]-sat)<1e-12
    c=exact_quarter(sat,sat,10,sat)
    assert abs(c[2]-2.5)<1e-9
    d=exact_quarter(sat,.005,0,sat)
    assert d[0]<sat and d[2]==0
    for bad in ((-1,.01,1,sat),(.01,.01,float("nan"),sat),
                (.01,.01,1,-.01)):
        try:exact_quarter(*bad)
        except ValueError:pass
        else:raise AssertionError("NEGATIVE_TEST_FAILED")
    # Explicit pulse can have a hidden within-hour high even when endpoint is normal.
    w=.011;ends=[]
    for rate in (100.,-100./3,-100./3,-100./3):
        w,*_=exact_quarter(w,.011,rate,sat)
        ends.append(w)
    assert max(ends)>ends[-1]+.001
    return 8
def read_weather(c104):
    w={}
    with gzip.open(C106,"rt",encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row["scenario"]=="RHout70_HRV50":
                key=row["time"]
                if key in w:raise AssertionError("DUPLICATE_WEATHER")
                outdoor=c104.w_ratio(float(row["Tout_C"]),float(row["RH_out"]))
                w[key]=min(outdoor,c104.W_IN)
    if len(w)!=8760:raise AssertionError("WEATHER_LENGTH")
    return w
def run():
    guard()
    for key,path in (("C116",C116),("C106",C106),("C104",C104)):
        if sha(path)!=PINS[key]:raise RuntimeError("SOURCE_DRIFT_"+key)
    c104=module(C104)
    tests=selftest(c104)
    weather=read_weather(c104)
    wsat=c104.w_ratio(c104.T_IN,1)
    out=D/"C118_SUBHOUR_STRESS.csv.gz"
    tmp=D/"C118_SUBHOUR_STRESS.partial.csv.gz"
    summ=D/"C118_SUMMARY.csv"
    meta=D/"C118_METADATA.json"
    if any(p.exists() for p in (out,tmp,summ,meta)):
        raise RuntimeError("OUTPUT_EXISTS")
    states={}
    stats=defaultdict(lambda:defaultdict(float))
    rows=0
    with gzip.open(C116,"rt",encoding="utf-8",newline="") as source,\
         gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
        writer=csv.writer(f);writer.writerow(FIELDS)
        for hourly in csv.DictReader(source):
            if rows%2880==0:guard()
            policy=hourly["policy"];control=hourly["control"];stamp=hourly["time"]
            supply=weather[stamp]
            evap=float(hourly["evap_kg"])
            dehum=float(hourly["room_dehum_kg"])
            humid=float(hourly["room_humid_kg"])
            ref=float(hourly["room_RH_end"])
            for pattern,weights in PATTERNS.items():
                key=(policy,control,pattern)
                w=states.get(key,c104.W_IN)
                start=rh(c104,w);peak=start;minimum=start
                vent_total=0.;cond_total=0.;residual_total=0.;sat_quarters=0
                for weight in weights:
                    net=evap*weight-dehum+humid
                    next_w,vent,cond,res,saturated=exact_quarter(w,supply,net,wsat)
                    current=rh(c104,next_w)
                    peak=max(peak,current);minimum=min(minimum,current)
                    vent_total+=vent;cond_total+=cond;residual_total+=res
                    sat_quarters+=int(saturated)
                    w=next_w
                end=rh(c104,w)
                storage=M*(w-states.get(key,c104.W_IN))
                if abs(storage-(vent_total+evap-dehum+humid-cond_total))>1e-7:
                    raise AssertionError("HOUR_MASS_CLOSURE")
                hidden_high=int(start<=.65 and end<=.65 and peak>.65)
                hidden_low=int(start>=.45 and end>=.45 and minimum<.45)
                vals=(policy,control,pattern,stamp,start,minimum,peak,end,ref,
                      evap,dehum,humid,supply,cond_total,vent_total,storage,
                      residual_total,sat_quarters,hidden_high,hidden_low)
                writer.writerow([v if isinstance(v,str) else
                                 str(v) if isinstance(v,int) else f"{v:.12f}" for v in vals])
                states[key]=w
                s=stats[key]
                s["hours"]+=1
                s["RH_min"]=min(s.get("RH_min",1.),minimum)
                s["RH_max"]=max(s.get("RH_max",0.),peak)
                s["hours_endpoint_high65"]+=int(end>.65)
                s["hours_peak_high65"]+=int(peak>.65)
                s["hours_endpoint_low45"]+=int(end<.45)
                s["hours_peak_low45"]+=int(minimum<.45)
                s["hidden_high65"]+=hidden_high
                s["hidden_low45"]+=hidden_low
                s["condensate_kg"]+=cond_total
                s["saturated_quarters"]+=sat_quarters
                s["mass_abs_residual_kg"]+=abs(residual_total)
                s["max_C116_endpoint_difference"]=max(s.get("max_C116_endpoint_difference",0.),abs(end-ref))
                if pattern=="flat" and control in ("ideal","capacity_C114"):
                    if abs(end-ref)>2e-8:raise AssertionError("FLAT_C116_REGRESSION")
            rows+=1
    if rows!=52560 or len(stats)!=24 or any(s["hours"]!=8760 for s in stats.values()):
        raise AssertionError("SCENARIO_COUNT")
    guard();os.replace(tmp,out)
    columns=("policy","control","pattern","hours","RH_min","RH_max",
             "hours_endpoint_high65","hours_peak_high65","hours_endpoint_low45",
             "hours_peak_low45","hidden_high65","hidden_low45",
             "condensate_kg","saturated_quarters","mass_abs_residual_kg",
             "max_C116_endpoint_difference")
    with summ.open("x",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(columns)
        for key in sorted(stats):
            s=stats[key]
            w.writerow(list(key)+[s[c] for c in columns[3:]])
    m={"schema":"C118_SYNTHETIC_SUBHOUR_RH_V1","task_id":TASK,"synthetic":True,
       "field_validated":False,"source_signoffs_added":0,
       "source_sha256":PINS,"hourly_source_rows":rows,
       "output_rows":rows*len(PATTERNS),"patterns":PATTERNS,
       "quarter_hours":DT,"room_dry_air_kg":M,"vent_dry_air_kg_h":V,
       "indoor_C":c104.T_IN,"selftests":tests,
       "hourly_sha256":sha(out),"summary_sha256":sha(summ),
       "limitations":[
         "One-way forcing sensitivity only: hourly C116 pool evaporation and equipment actions are frozen.",
         "Pulse patterns are adversarial synthetic redistributions, not measured quarter-hour loads.",
         "Fixed 29C air, 3000 m3 room, constant ventilation and coil supply within each hour.",
         "No controller retuning or dynamic room enthalpy; quarter-hour saturation drain is an alternative to C116 endpoint clip.",
         "Not vendor sizing, real-time control validation, or 31-source physical signoff."]}
    with meta.open("x",encoding="utf-8") as f:
        json.dump(m,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"status":"PASS","source_hours":rows,"output_rows":m["output_rows"],
                      "selftests":tests,"hourly_sha256":m["hourly_sha256"],
                      "hidden_high65":{"/".join(k):int(s["hidden_high65"]) for k,s in stats.items()},
                      "max_peak_RH":max(s["RH_max"] for s in stats.values())},indent=2))
if __name__=="__main__":run()
