"""C120: independent, synthetic 15-minute responsive dehumidification comparison.
Read-only SHA-pinned C116/C106/C104. No equipment or shared-runtime modifications.
"""
import csv,gzip,hashlib,importlib.util,json,math,os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent; R=D.parent; S=R.parent
C116=R/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
C106=R/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
C104=R/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"c104_psychrometric.py"
C118=R/"AUTONOMOUS_RUN_20261031_0550_DCHR_C118_SUBHOUR_RH"/"c118_subhour_rh.py"
PINS={str(C116):"6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf",
      str(C106):"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
      str(C104):"1bbe6dbbf18f04c5bc0ef7b407efdbbebbf60ec496a1b5178ee66ab3bf7a1600",
      str(C118):"DYNAMIC"}
TASK="scc-2aab24704c2bd0"
M=3540.; V=3540.; DT=.25
DEHUM_CAP=45.66; HUMID_CAP=29.70; TARGET=.55; GAIN=.75
PATTERNS={"flat":(1.,1.,1.,1.),"front_loaded":(4.,0.,0.,0.)}
MODES=("legacy_fixed","fixed_capped","feedback_capped","predictive_capped")
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
FIELDS=("policy","control","pattern","mode","time","RH_start","RH_peak","RH_end","RH_min",
        "evap_kg","dehum_kg","humid_kg","condensate_kg","vent_kg","storage_kg",
        "mass_residual_kg","hidden_high65","high_quarters","dehum_capacity_quarters")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,R,S,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
        for f in FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def demand(mode,w,ws,evap_rate,base_dehum,base_humid,target_w):
    baseline=base_dehum-base_humid
    if mode=="legacy_fixed":return baseline
    if mode=="fixed_capped":return max(-HUMID_CAP,min(DEHUM_CAP,baseline))
    if mode=="feedback_capped":
        raw=baseline+GAIN*M*(w-target_w)/DT
    elif mode=="predictive_capped":
        a=math.exp(-V/M*DT)
        raw=evap_rate+V*(ws+(a*w-target_w)/(1-a))
    else:raise ValueError("MODE")
    return max(-HUMID_CAP,min(DEHUM_CAP,raw))
def selftest(c104,c118):
    target=c104.w_ratio(c104.T_IN,TARGET)
    assert demand("feedback_capped",target,.01,5,10,0,target)==10
    assert demand("feedback_capped",target+.01,.01,5,10,0,target)==DEHUM_CAP
    assert demand("feedback_capped",target-.01,.01,5,10,0,target)==-HUMID_CAP
    assert demand("fixed_capped",target,.01,5,100,0,target)==DEHUM_CAP
    assert demand("fixed_capped",target,.01,5,0,100,target)==-HUMID_CAP
    p=demand("predictive_capped",target,target,5,0,0,target)
    end,*_=c118.exact_quarter(target,target,5-p,c104.w_ratio(c104.T_IN,1))
    assert abs(end-target)<1e-12
    try:demand("invalid",target,target,0,0,0,target)
    except ValueError:pass
    else:raise AssertionError("INVALID_MODE")
    return 7
def weather(c104):
    out={}
    with gzip.open(C106,"rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r["scenario"]=="RHout70_HRV50":
                if r["time"] in out:raise AssertionError("DUP_WEATHER")
                out[r["time"]]=min(c104.w_ratio(float(r["Tout_C"]),float(r["RH_out"])),c104.W_IN)
    assert len(out)==8760
    return out
def run():
    guard()
    for p,h in PINS.items():
        if h!="DYNAMIC" and sha(Path(p))!=h:raise RuntimeError("SOURCE_DRIFT "+p)
    c104=load(C104,"c104_c120"); c118=load(C118,"c118_c120")
    pins={p:(sha(Path(p)) if h=="DYNAMIC" else h) for p,h in PINS.items()}
    tests=selftest(c104,c118)
    wout=weather(c104);target_w=c104.w_ratio(c104.T_IN,TARGET)
    wsat=c104.w_ratio(c104.T_IN,1.)
    out=D/"C120_QUARTER_CONTROL.csv.gz"; tmp=D/"C120_QUARTER_CONTROL.partial.csv.gz"
    summ=D/"C120_SUMMARY.csv";meta=D/"C120_METADATA.json"
    if any(x.exists() for x in (out,tmp,summ,meta)):raise RuntimeError("OUTPUT_EXISTS")
    state={}; stats=defaultdict(lambda:defaultdict(float)); source_hours=0; rows=0
    with gzip.open(C116,"rt",encoding="utf-8",newline="") as f, gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as dest:
        reader=csv.DictReader(f); wr=csv.writer(dest);wr.writerow(FIELDS)
        for row in reader:
            if row["policy"]!="water_first" or row["control"] not in ("ideal","capacity_C114"):continue
            if source_hours%720==0:guard()
            policy=row["policy"];control=row["control"];stamp=row["time"]
            evap=float(row["evap_kg"]);base_d=float(row["room_dehum_kg"]);base_h=float(row["room_humid_kg"])
            ws=wout[stamp]
            for pattern,weights in PATTERNS.items():
                for mode in MODES:
                    key=(policy,control,pattern,mode)
                    w=state.get(key,target_w); start=c118.rh(c104,w)
                    peak=start;minimum=start;dehum=humid=cond=vent=0.
                    sat=high=capq=0
                    for weight in weights:
                        rate=evap*weight
                        cmd=demand(mode,w,ws,rate,base_d,base_h,target_w)
                        d=max(0.,cmd);h=max(0.,-cmd)
                        new,v,c,res,saturated=c118.exact_quarter(w,ws,rate-d+h,wsat)
                        if abs(res)>1e-8:raise AssertionError("QUARTER_MASS")
                        w=new;cur=c118.rh(c104,w)
                        peak=max(peak,cur);minimum=min(minimum,cur)
                        dehum+=d*DT;humid+=h*DT;cond+=c;vent+=v
                        sat+=int(saturated);high+=int(cur>.65)
                        capq+=int(mode!="legacy_fixed" and abs(cmd-DEHUM_CAP)<1e-8)
                    end=c118.rh(c104,w)
                    storage=M*(w-state.get(key,target_w))
                    residual=storage-(evap-dehum+humid+vent-cond)
                    if abs(residual)>1e-7:raise AssertionError("HOUR_MASS")
                    hidden=int(start<=.65 and end<=.65 and peak>.65)
                    vals=(policy,control,pattern,mode,stamp,start,peak,end,minimum,
                          evap,dehum,humid,cond,vent,storage,residual,hidden,high,capq)
                    wr.writerow([v if isinstance(v,str) else str(v) if isinstance(v,int) else f"{v:.12f}" for v in vals])
                    state[key]=w; rows+=1
                    st=stats[key];st["hours"]+=1
                    st["max_RH"]=max(st.get("max_RH",0.),peak)
                    st["min_RH"]=min(st.get("min_RH",1.),minimum)
                    st["hidden_high65"]+=hidden
                    st["high_quarters"]+=high
                    st["capacity_quarters"]+=capq
                    st["dehum_kg"]+=dehum;st["humid_kg"]+=humid;st["condensate_kg"]+=cond
                    st["mass_abs_residual_kg"]+=abs(residual)
            source_hours+=1
    assert source_hours==17520 and rows==140160 and len(stats)==16
    assert all(s["hours"]==8760 for s in stats.values())
    guard();os.replace(tmp,out)
    cols=("policy","control","pattern","mode","hours","min_RH","max_RH","hidden_high65",
          "high_quarters","capacity_quarters","dehum_kg","humid_kg","condensate_kg","mass_abs_residual_kg")
    with summ.open("x",encoding="utf-8",newline="") as f:
        wr=csv.writer(f);wr.writerow(cols)
        for key in sorted(stats):
            wr.writerow(list(key)+[stats[key][x] for x in cols[4:]])
    m={"schema":"C120_SYNTHETIC_15MIN_CONTROLLER_V1","task_id":TASK,
       "synthetic":True,"field_validated":False,"source_signoffs_added":0,
       "source_sha256":pins,"source_hours":source_hours,"output_rows":rows,
       "selftests":tests,"modes":MODES,"patterns":PATTERNS,"target_RH":TARGET,
       "feedback_gain":GAIN,"dehum_capacity_kg_h":DEHUM_CAP,"humid_capacity_kg_h":HUMID_CAP,
       "hourly_sha256":sha(out),"summary_sha256":sha(summ),
       "limitations":["One-way replay of C116 hourly evaporation, not a coupled heat/air simulation.",
       "Fixed 29 C air, no dynamic enthalpy, equipment startup delay, or sensor lag.",
       "Predictive mode assumes perfect knowledge of quarter-hour evaporation but is not proven optimal under actuator caps.",
       "Legacy fixed mode may exceed real capacity; compare fixed_capped to feedback_capped for equal capacity.",
       "Front-loaded pulses are synthetic stress tests, not measurements. No equipment validation."]}
    meta.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","rows":rows,"selftests":tests,"data_sha256":sha(out),
      "front_loaded":{"/".join(k):{"hidden":int(v["hidden_high65"]),"high_quarters":int(v["high_quarters"])}
      for k,v in stats.items() if k[2]=="front_loaded"}},indent=2))
if __name__=="__main__":run()

