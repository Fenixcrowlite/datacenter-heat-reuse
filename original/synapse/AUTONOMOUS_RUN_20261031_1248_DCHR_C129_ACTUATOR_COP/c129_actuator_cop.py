"""C129: isolated synthetic heat-pump ramp/COP sensitivity, without runtime edits."""
from pathlib import Path
from collections import deque, defaultdict
import csv, gzip, hashlib, importlib.util, json, math, os

D=Path(__file__).resolve().parent
ROOT=D.parent.parent
C128=D.parent/"AUTONOMOUS_RUN_20261031_1153_DCHR_C128_DELAYED_PRIORITY"/"c128_delayed_priority.py"
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for n in FLAGS:
            if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def load(p,name):
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ramp_to(previous,desired,cap,step):
    if not all(math.isfinite(x) for x in (previous,desired,cap)):raise ValueError("NONFINITE")
    if min(previous,desired,cap)<0 or desired>cap+1e-7:raise ValueError("BOUNDS")
    if step is None:return desired
    if not math.isfinite(step) or step<=0:raise ValueError("RAMP")
    return min(cap,max(0.,max(previous-step,min(previous+step,desired))))
class HeatPump:
    def __init__(self,base,ramp_kw,cop):
        if not math.isfinite(cop) or cop<=1:raise ValueError("COP")
        self.base=base;self.ramp=ramp_kw;self.cop=cop;self.prev=0.;self.last=None
    def dispatch(self,p,a,cap,priority):
        desired=min(p+a,cap)
        output=ramp_to(self.prev,desired,cap,None if self.ramp is None else self.ramp*900.)
        qp,qa=self.base.dispatch(p,a,min(desired,output),priority)
        bypass=output-qp-qa
        electric=output/self.cop
        recovered=output-electric
        if bypass< -1e-7 or abs(output-electric-recovered)>1e-7:raise AssertionError("PUMP_BALANCE")
        self.prev=output
        self.last=(desired,output,bypass,electric,recovered)
        return qp,qa
def scenarios():
    out={}
    for cap in (20.,25.):
        for priority in ("water_first","air_first"):
            for delay in (0,2):
                for ramp in (2.,None):
                    for cop in (2.5,4.):
                        name=f"{priority}_{int(cap)}kW_d{delay}_r{'ideal' if ramp is None else '2'}_cop{str(cop).replace('.','p')}"
                        out[name]=(priority,cap,delay,ramp,cop)
    for priority in ("water_first","air_first"):
        out[f"{priority}_150kW_d0_rideal_cop4p0"]=(priority,150.,0,None,4.)
    return out
def selftest():
    assert ramp_to(0,18000,18000,1800)==1800
    assert ramp_to(18000,0,18000,1800)==16200
    assert ramp_to(5000,0,18000,None)==0
    assert ramp_to(1800,3600,18000,1800)==3600
    for bad in (0.,-1.,float("nan")):
        try:ramp_to(0,1,2,bad)
        except ValueError:pass
        else:raise AssertionError("INVALID_RAMP_ACCEPTED")
    try:HeatPump(None,2,1.)
    except ValueError:pass
    else:raise AssertionError("INVALID_COP_ACCEPTED")
    return 8
def main():
    guard()
    if not C128.exists():raise RuntimeError("MISSING_C128")
    c128=load(C128,"c129_c128");base=load(c128.BASE,"c129_c127")
    pool=load(base.POOL,"c129_pool");air=load(base.AIR,"c129_air")
    for key,p in (("source",base.SRC),("air",base.AIR),("pool",base.POOL)):
        if sha(p)!=base.PINS[key]:raise RuntimeError("SOURCE_DRIFT_"+key)
    tests=selftest()
    c91,c92,_,_=pool.load()
    specs=scenarios()
    states={}
    for name,(priority,cap,delay,ramp,cop) in specs.items():
        states[name]={"state":(28.,29.,air.w_from(29.,.55),True),
                      "queue":deque([(0.,0.)]*delay),
                      "plant":HeatPump(base,ramp,cop),"n":0,
                      "sum":defaultdict(float),"min_pool":float("inf")}
    out=D/"C129_ACTUATOR_COP.csv.gz";tmp=D/"C129_ACTUATOR_COP.partial.csv.gz"
    for n in (out.name,tmp.name,"C129_SUMMARY.json","C129_METADATA.json"):
        if (D/n).exists():raise RuntimeError("OUTPUT_EXISTS "+n)
    extra=("ramp_kw_per_quarter","COP","source_desired_kJ","source_output_kJ",
           "source_bypass_kJ","electric_kJ","recovered_kJ")
    hours=0
    with gzip.open(base.SRC,"rt",encoding="utf-8",newline="") as src, gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as dest:
        writer=csv.writer(dest);writer.writerow(c128.FIELDS+extra)
        for r in csv.DictReader(src):
            if r["policy"]!="water_first" or r["control"]!="ideal":continue
            if hours>=168:break
            if hours%24==0:guard()
            hour=int(r["time"][11:13])
            for name,(priority,cap,delay,ramp,cop) in specs.items():
                st=states[name];plant=st["plant"]
                for q in range(4):
                    v=c128.core(plant,pool,air,c91,c92,st,hour,cap,priority,delay)
                    desired,output,bypass,electric,recovered=plant.last
                    writer.writerow((name,r["time"],q,priority,cap,delay)+
                                    tuple(f"{x:.12f}" for x in v)+
                                    (("ideal" if ramp is None else f"{ramp:.1f}"),f"{cop:.3f}")+
                                    tuple(f"{x:.12f}" for x in plant.last))
                    st["n"]+=1;st["min_pool"]=min(st["min_pool"],v[1])
                    sums=st["sum"]
                    for key,value in (("thermal_MWh",output),("electric_MWh",electric),
                                      ("recovered_MWh",recovered),("bypass_MWh",bypass),
                                      ("pool_MWh",v[12]),("air_MWh",v[13])):
                        sums[key]+=value/3600000.
                    sums["RH_above65_quarters"]+=int(v[6]>.65)
                    sums["ramp_limited_quarters"]+=int(output+1e-7<desired)
            hours+=1
    if hours!=168:raise AssertionError("HOURS")
    guard();os.replace(tmp,out)
    summary={}
    for name,st in states.items():
        summary[name]={"quarters":st["n"],"final_pool_C":st["state"][0],
                       "final_air_C":st["state"][1],"min_pool_C":st["min_pool"],
                       **dict(st["sum"])}
    (D/"C129_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    meta={"schema":"C129_SYNTHETIC_HEAT_PUMP_RAMP_COP_V1","task_id":TASK,
          "hours":hours,"scenarios":len(specs),"rows":sum(x["n"] for x in states.values()),
          "selftests":tests,"base_sha256":sha(C128),
          "source_pins":base.PINS,"data_sha256":sha(out),
          "summary_sha256":sha(D/"C129_SUMMARY.json"),"synthetic":True,
          "field_validated":False,"source_signoffs_added":0,
          "interpretation":"synthetic electrically driven heat-pump stage; output=electric+recovered; bypass is thermal dump, not useful heating",
          "ramp_semantics":"thermal source output ramps +/- 2 kW per 15 min or ideal, starting cold at zero; dispatch never exceeds live delayed demand",
          "limitations":["fixed assumed COP, not a measured COP curve","waste heat supply assumed unlimited within thermal cap","no real equipment cycling/minimum on time","synthetic weather and pool/air parameters"]}
    (D/"C129_METADATA.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","rows":meta["rows"],"scenarios":len(specs),
                      "selftests":tests,"data_sha256":meta["data_sha256"]},indent=2))
if __name__=="__main__":main()
