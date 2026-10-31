"""C128: isolated synthetic shared heat cap, priority and 30-min command transport delay."""
import csv,gzip,hashlib,importlib.util,json,math,os
from pathlib import Path
from collections import deque,defaultdict
D=Path(__file__).resolve().parent; R=D.parent; ROOT=R.parent
BASE=R/"AUTONOMOUS_RUN_20261031_1049_DCHR_C127_BOUNDED_DISPATCH"/"c127_bounded_dispatch.py"

TASK="scc-2aab24704c2bd0"
SC={}
for cap in (20.,25.):
 for priority in ("water_first","air_first"):
  for delay in (0,2):
   SC[f"{priority}_{int(cap)}kW_d{delay}"]=(priority,cap,delay)
for priority in ("water_first","air_first"):
 SC[f"{priority}_150kW_d0"]=(priority,150.,0)
FIELDS=("scenario","time","quarter","priority","source_kw","delay_quarters","pool_T0","pool_T1",
"air_T0","air_T1","w0","w1","RH1","pool_req_kJ","air_req_kJ",
"lag_pool_kJ","lag_air_kJ","safe_air_kJ","pool_heat_kJ","air_heat_kJ",
"source_cap_kJ","source_unused_kJ","pool_loss_kJ","evap_kg","latent_kJ",
"makeup_kJ","other_loss_kJ","air_evap_kJ","vent_kJ","hvac_kJ",
"dehum_kJ","humid_kJ","cond_kJ","pool_residual_kJ","air_residual_kJ",
"combined_residual_kJ","air_mass_residual_kg","thermostat_on")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,R,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for flag in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def core(base,pool,air,c91,c92,st,hour,cap_kw,priority,delay):
 tp,ta,w,on=st["state"]
 rh=air.rh_from(ta,w)
 loss_hour,evap_hour=pool.loss_components(c91,c92,tp,hour,max(1e-9,min(1-1e-9,rh)),.15)
 evap=evap_hour/4.;loss=loss_hour*900000.
 latent=evap*(2501.-2.361*tp);makeup=evap*4.186*(tp-12.);other=loss-latent-makeup
 pool_cap=c91.CAP*3600000.
 if tp<=27.95:on=True
 if tp>=28.05:on=False
 reqp=max(0.,loss+.35*pool_cap*(28.-tp)) if on else 0.
 reqa=max(0.,min(15.,5.*(air.TARGET_T-ta)))*900.
 if delay:
  lagp,laga=st["queue"].popleft()
  st["queue"].append((reqp,reqa))
 else:lagp,laga=reqp,reqa
 # Local current-temperature safety interlock prevents stale air heat beyond the live air request.
 safea=min(laga,reqa)
 cap=cap_kw*900.
 qp,qa=base.dispatch(lagp,safea,cap,priority)
 hvac_cap=15. if ta>=air.TARGET_T else qa/900.
 x=air.step(ta,w,tp,evap,5.,hvac_cap)
 hvac=x[13]
 if abs(max(0.,hvac)-qa)>1e-7:raise AssertionError("HVAC_MISMATCH")
 tp1=tp+(qp-loss)/pool_cap;ta1,w1=x[:2]
 pres=pool_cap*(tp1-tp)-(qp-loss)
 ares=x[10]-x[9]-(x[11]+x[12]+hvac-x[14]+x[15]-x[16])
 cres=pool_cap*(tp1-tp)+x[10]-x[9]-(qp-makeup-other+x[12]+hvac-x[14]+x[15]-x[16])
 if max(abs(pres),abs(ares),abs(cres))>1e-5 or abs(x[8])>1e-7:raise AssertionError("BALANCE")
 if not 0<tp1<45:raise AssertionError("POOL_BOUND")
 st["state"]=(tp1,ta1,w1,on)
 return (tp,tp1,ta,ta1,w,w1,air.rh_from(ta1,w1),reqp,reqa,lagp,laga,safea,qp,qa,
 cap,cap-qp-qa,loss,evap,latent,makeup,other,x[11],x[12],hvac,x[14],x[15],x[16],
 pres,ares,cres,x[8],int(on))
def selftest(base,pool,air,c91,c92):
 assert base.dispatch(10,20,15,"water_first")== (10,5)
 assert base.dispatch(10,20,15,"air_first")== (0,15)
 for priority in ("water_first","air_first"):
  st={"state":(28.,29.,air.w_from(29.,.55),True),"queue":deque()}
  v=core(base,pool,air,c91,c92,st,12,150.,priority,0)
  refstate,ref=base.step(pool,air,c91,c92,(28.,29.,air.w_from(29.,.55),True),12,150.,priority)
  assert all(abs(a-b)<1e-8 for a,b in zip(st["state"][:3],refstate[:3]))
  assert abs(v[12]-ref[12])<1e-8 and abs(v[13]-ref[13])<1e-8
 for bad in (-1.,float("nan")):
  try:base.dispatch(1,1,bad,"water_first")
  except ValueError:pass
  else:raise AssertionError("BAD_CAP_ACCEPTED")
 return 6
def main():
 guard()
 if not BASE.exists():raise RuntimeError("BASE_MISSING")
 base=load(BASE,"c128_c127");pool=load(base.POOL,"c128_pool");air=load(base.AIR,"c128_air")
 for k,p in (("source",base.SRC),("air",base.AIR),("pool",base.POOL)):
  if sha(p)!=base.PINS[k]:raise RuntimeError("SOURCE_DRIFT_"+k)
 c91,c92,_,_=pool.load();tests=selftest(base,pool,air,c91,c92)
 for n in ("C128_DELAYED_PRIORITY.csv.gz","C128_DELAYED_PRIORITY.partial.csv.gz","C128_SUMMARY.json","C128_METADATA.json"):
  if (D/n).exists():raise RuntimeError("OUTPUT_EXISTS "+n)
 states={name:{"state":(28.,29.,air.w_from(29.,.55),True),
  "queue":deque([(0.,0.)]*delay),"n":0,"s":defaultdict(float),
  "min_pool":99.,"max_pool":-99.} for name,(_,_,delay) in SC.items()}
 out=D/"C128_DELAYED_PRIORITY.csv.gz";tmp=D/"C128_DELAYED_PRIORITY.partial.csv.gz"
 hours=0
 with gzip.open(base.SRC,"rt",encoding="utf-8",newline="") as f,gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as g:
  writer=csv.writer(g);writer.writerow(FIELDS)
  for r in csv.DictReader(f):
   if r["policy"]!="water_first" or r["control"]!="ideal":continue
   if hours>=168:break
   if hours%24==0:guard()
   hour=int(r["time"][11:13])
   for name,(priority,cap,delay) in SC.items():
    st=states[name]
    for q in range(4):
     v=core(base,pool,air,c91,c92,st,hour,cap,priority,delay)
     writer.writerow((name,r["time"],q,priority,cap,delay)+tuple(f"{x:.12f}" for x in v))
     st["n"]+=1;st["min_pool"]=min(st["min_pool"],v[1]);st["max_pool"]=max(st["max_pool"],v[1])
     s=st["s"]
     s["pool_heat_MWh"]+=v[12]/3600000.;s["air_heat_MWh"]+=v[13]/3600000.
     s["pool_command_unmet_MWh"]+=max(0.,v[7]-v[12])/3600000.
     s["air_command_unmet_MWh"]+=max(0.,v[8]-v[13])/3600000.
     s["cap_binding_quarters"]+=int(v[9]+v[11]>v[14]+1e-7)
     s["RH_above65_quarters"]+=int(v[6]>.65)
   hours+=1
 assert hours==168
 guard();os.replace(tmp,out)
 result={name:{"quarters":st["n"],"final_pool_C":st["state"][0],
 "final_air_C":st["state"][1],"min_pool_C":st["min_pool"],"max_pool_C":st["max_pool"],
 **dict(st["s"])} for name,st in states.items()}
 (D/"C128_SUMMARY.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 meta={"schema":"C128_DELAYED_PRIORITY_SYNTHETIC_V1","task_id":TASK,"rows":sum(st["n"] for st in states.values()),
 "hours":hours,"selftests":tests,"base_sha256":sha(BASE),"source_sha256":base.PINS,
 "data_sha256":sha(out),"summary_sha256":sha(D/"C128_SUMMARY.json"),
 "synthetic":True,"field_validated":False,"source_signoffs_added":0,
 "delay_semantics":"FIFO transport delay 0 or 2 quarters; cold-start commands zero; air local live safety gate",
 "limitations":["thermal kW not electrical kW; no COP","synthetic HVAC/evaporation/weather",
 "air cooling independent of recovered source","no measured actuator response or physical validation"]}
 (D/"C128_METADATA.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","rows":meta["rows"],"selftests":tests,"data_sha256":meta["data_sha256"],"summary":result},indent=2))
if __name__=="__main__":main()
