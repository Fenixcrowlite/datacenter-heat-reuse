"""C130: isolated synthetic finite DC waste-heat + buffer + temperature COP.
No SCADA/MATLAB/runtime modifications; NOT a vendor performance curve.
"""
from pathlib import Path
from collections import deque, defaultdict
import csv, gzip, hashlib, importlib.util, json, math, os

D=Path(__file__).resolve().parent
ROOT=D.parent.parent
C129=D.parent/"AUTONOMOUS_RUN_20261031_1248_DCHR_C129_ACTUATOR_COP"/"c129_actuator_cop.py"
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def guard():
    for root in (D,D.parent,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for flag in FLAGS:
            if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def cop_curve(source_c,sink_c,eta=.32):
    if not all(map(math.isfinite,(source_c,sink_c,eta))) or sink_c<=source_c or not 0<eta<1:
        raise ValueError("INVALID_COP_TEMPERATURE")
    return max(1.5,min(6.5,eta*(sink_c+273.15)/(sink_c-source_c)))
def source_kw(hour,quarter,mode):
    if mode=="scarce":return 5. if hour<6 or hour>=22 else 12.
    if mode=="abundant":return 25.
    raise ValueError("UNKNOWN_SOURCE_MODE")
class FiniteSourcePump:
    def __init__(self,base,c129,buffer_kwh):
        if not math.isfinite(buffer_kwh) or buffer_kwh<0:raise ValueError("BUFFER_CAP")
        self.base=base;self.c129=c129;self.capacity=buffer_kwh*3600000.
        self.buffer=0.;self.previous=0.;self.input=None;self.last=None
    def begin(self,source_c,sink_c,source_power_kw):
        if self.input is not None:raise RuntimeError("UNCLOSED_INTERVAL")
        if not math.isfinite(source_power_kw) or source_power_kw<0:raise ValueError("SOURCE_POWER")
        self.input=(cop_curve(source_c,sink_c),source_power_kw*900.,source_c,sink_c)
    def dispatch(self,p,a,cap,priority):
        if self.input is None:raise RuntimeError("INTERVAL_NOT_STARTED")
        if not all(map(math.isfinite,(p,a,cap))) or min(p,a,cap)<0:raise ValueError("REQUEST")
        cop,inflow,source_c,sink_c=self.input
        desired=min(p+a,cap)
        ramped=self.c129.ramp_to(self.previous,desired,cap,1800.)
        usable=inflow+self.buffer
        thermal=min(desired,ramped,usable/(1.-1./cop))
        qp,qa=self.base.dispatch(p,a,thermal,priority)
        if abs(thermal-qp-qa)>1e-6:raise AssertionError("DISPATCH_UNUSED")
        electric=thermal/cop
        recovered=thermal-electric
        before=self.buffer
        remaining=before+inflow-recovered
        after=min(self.capacity,max(0.,remaining))
        spill=max(0.,remaining-after)
        if min(electric,recovered,after,spill)>-1e-7:pass
        else:raise AssertionError("NEGATIVE_ENERGY")
        if abs((before+inflow)-(recovered+after+spill))>1e-6:raise AssertionError("SOURCE_BALANCE")
        if abs(thermal-electric-recovered)>1e-6:raise AssertionError("PUMP_BALANCE")
        self.buffer=after;self.previous=thermal;self.input=None
        self.last=(cop,inflow,before,after,spill,desired,ramped,thermal,electric,recovered,source_c,sink_c)
        return qp,qa
def selftest(base,c129):
    assert cop_curve(22,40)>cop_curve(15,40)
    assert cop_curve(15,45)<cop_curve(15,35)
    for a,b in ((40,40),(float("nan"),40),(15,14)):
        try:cop_curve(a,b)
        except ValueError:pass
        else:raise AssertionError("COP_BAD_ACCEPTED")
    p=FiniteSourcePump(base,c129,0)
    p.begin(15,40,0)
    assert p.dispatch(10000,0,18000,"water_first")== (0,0)
    p=FiniteSourcePump(base,c129,10)
    p.begin(15,40,20);p.dispatch(0,0,18000,"water_first")
    assert abs(p.buffer-18000)<1e-8
    p.begin(15,40,0);p.dispatch(10000,0,18000,"water_first")
    assert p.last[9]>0 and p.buffer<18000
    try:FiniteSourcePump(base,c129,-1)
    except ValueError:pass
    else:raise AssertionError("NEG_BUFFER")
    return 8
SCENARIOS={
    "water_scarce_no_buffer_cold":("water_first","scarce",0.,15.),
    "water_scarce_buffer_cold":("water_first","scarce",30.,15.),
    "water_scarce_buffer_warm":("water_first","scarce",30.,22.),
    "air_scarce_no_buffer_cold":("air_first","scarce",0.,15.),
    "air_scarce_buffer_warm":("air_first","scarce",30.,22.),
    "water_abundant_buffer_warm":("water_first","abundant",30.,22.),
}
EXTRA=("source_mode","buffer_capacity_kWh","COP","source_in_kJ","buffer_before_kJ",
       "buffer_after_kJ","source_spill_kJ","source_desired_kJ","source_ramped_kJ",
       "thermal_output_kJ","electric_kJ","recovered_kJ","source_temp_C","sink_temp_C")
def main():
    guard()
    c129=load(C129,"c130_c129")
    c128=load(c129.C128,"c130_c128")
    base=load(c128.BASE,"c130_c127")
    pool=load(base.POOL,"c130_pool");air=load(base.AIR,"c130_air")
    for key,path in (("source",base.SRC),("air",base.AIR),("pool",base.POOL)):
        if sha(path)!=base.PINS[key]:raise RuntimeError("SOURCE_DRIFT_"+key)
    tests=selftest(base,c129)
    c91,c92,_,_=pool.load()
    states={}
    for name,(priority,mode,buffer_kwh,temp) in SCENARIOS.items():
        states[name]={"state":(28.,29.,air.w_from(29.,.55),True),
            "queue":deque([(0.,0.)]*2),"plant":FiniteSourcePump(base,c129,buffer_kwh),
            "count":0,"s":defaultdict(float),"min_pool":99.}
    output=D/"C130_DYNAMIC_COP_BUFFER.csv.gz"
    temp=D/"C130_DYNAMIC_COP_BUFFER.partial.csv.gz"
    for p in (output,temp,D/"C130_SUMMARY.json",D/"C130_METADATA.json"):
        if p.exists():raise RuntimeError("OUTPUT_EXISTS "+str(p))
    hours=0
    with gzip.open(base.SRC,"rt",encoding="utf-8",newline="") as f, gzip.open(temp,"xt",encoding="utf-8",newline="",compresslevel=4) as g:
        writer=csv.writer(g);writer.writerow(c128.FIELDS+EXTRA)
        for row in csv.DictReader(f):
            if row["policy"]!="water_first" or row["control"]!="ideal":continue
            if hours>=168:break
            if hours%24==0:guard()
            hour=int(row["time"][11:13])
            for name,(priority,mode,buffer_kwh,source_base) in SCENARIOS.items():
                st=states[name];pump=st["plant"]
                for quarter in range(4):
                    source_c=source_base+2.*math.sin(2*math.pi*(hour+quarter/4)/24)
                    sink_c=40.+.3*(28.-st["state"][0])
                    pump.begin(source_c,sink_c,source_kw(hour,quarter,mode))
                    values=c128.core(pump,pool,air,c91,c92,st,hour,20.,priority,2)
                    last=pump.last
                    writer.writerow((name,row["time"],quarter,priority,20.,2)+
                        tuple(f"{x:.12f}" for x in values)+(mode,f"{buffer_kwh:.3f}")+
                        tuple(f"{x:.12f}" for x in last))
                    st["count"]+=1;st["min_pool"]=min(st["min_pool"],values[1])
                    sums=st["s"]
                    for key,val in (("source_in_MWh",last[1]),("buffer_spill_MWh",last[4]),
                                    ("electric_MWh",last[8]),("recovered_MWh",last[9]),
                                    ("thermal_MWh",last[7]),("pool_MWh",values[12]),
                                    ("air_MWh",values[13])):
                        sums[key]+=val/3600000.
                    sums["RH_above65_quarters"]+=int(values[6]>.65)
                    sums["source_limited_quarters"]+=int(last[7]+1e-7<last[6])
            hours+=1
    if hours!=168 or any(st["count"]!=672 for st in states.values()):
        raise AssertionError("HOUR_COUNT")
    guard();os.replace(temp,output)
    summary={name:{"quarters":st["count"],"min_pool_C":st["min_pool"],
                   "final_pool_C":st["state"][0],"final_air_C":st["state"][1],
                   "final_buffer_kWh":st["plant"].buffer/3600000.,
                   **dict(st["s"])} for name,st in states.items()}
    (D/"C130_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    metadata={"schema":"C130_SYNTHETIC_FINITE_WASTE_HEAT_V1","task_id":TASK,
        "hours":hours,"scenarios":len(SCENARIOS),"rows":sum(s["count"] for s in states.values()),
        "selftests":tests,"base_sha256":sha(C129),"source_pins":base.PINS,
        "data_sha256":sha(output),"summary_sha256":sha(D/"C130_SUMMARY.json"),
        "synthetic":True,"field_validated":False,"source_signoffs_added":0,
        "cop_model":"COP = clip(0.32*(T_sink+273.15)/(T_sink-T_source),1.5,6.5); illustrative not manufacturer curve",
        "storage":"source heat kJ conservation: buffer_before+inflow=recovered+buffer_after+spill",
        "limitations":["assumed temperatures and daily DC waste-heat profile",
                       "no compressor map, defrost, part-load degradation or real measurements",
                       "source shortage may curtail output faster than nominal down-ramp",
                       "air cooling independent from heat-pump electrical consumption"]}
    (D/"C130_METADATA.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","rows":metadata["rows"],"scenarios":len(SCENARIOS),
                      "selftests":tests,"data_sha256":metadata["data_sha256"],
                      "summary":summary},indent=2))
if __name__=="__main__":main()
