"""C127 isolated synthetic 15-minute pool thermostat and shared-source dispatch."""
import csv, gzip, hashlib, importlib.util, json, math, os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent; REC=D.parent; ROOT=REC.parent
SRC=REC/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
AIR=REC/"AUTONOMOUS_RUN_20261031_0900_DCHR_C124_AIR_ENTHALPY"/"c124_air_enthalpy.py"
POOL=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
PINS={"source":"6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf",
"air":"998d5da270714a1b84dfecaa774578174e7815fe4178af28920d0a24d4da3b11",
"pool":"0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923"}
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
SCENARIOS={"water_150kW":("water_first",150.,8760),"air_150kW":("air_first",150.,8760),
"water_10kW_7d":("water_first",10.,168),"noheat_7d":("water_first",0.,168)}
FIELDS=("scenario","time","quarter","pool_T0","pool_T1","air_T0","air_T1","w0","w1","RH0","RH1",
"evap_kg","pool_loss_kJ","pool_req_kJ","air_req_kJ","pool_heat_kJ","air_heat_kJ",
"source_cap_kJ","source_unused_kJ","pool_unmet_kJ","air_unmet_kJ",
"latent_kJ","makeup_kJ","other_loss_kJ","air_evap_kJ","vent_kJ","hvac_kJ",
"dehum_kJ","humid_kJ","cond_kJ","pool_residual_kJ","air_residual_kJ",
"combined_residual_kJ","air_mass_residual_kg","thermostat_on","source_kw")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,REC,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for f in FLAGS:
   if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return m
def dispatch(pool_req,air_req,cap,priority):
 if priority not in ("water_first","air_first"):raise ValueError("PRIORITY")
 if not all(map(math.isfinite,(pool_req,air_req,cap))) or min(pool_req,air_req,cap)<0:raise ValueError("BAD_DISPATCH")
 if priority=="water_first":
  qp=min(pool_req,cap);qa=min(air_req,max(0.,cap-qp))
 else:
  qa=min(air_req,cap);qp=min(pool_req,max(0.,cap-qa))
 return qp,qa
def step(pool,air,c91,c92,state,hour,source_kw,priority):
 tp,ta,w,on=state
 if not all(map(math.isfinite,(tp,ta,w,source_kw))) or source_kw<0:raise ValueError("INPUT")
 rh=air.rh_from(ta,w)
 loss_hour,evap_hour=pool.loss_components(c91,c92,tp,hour,max(1e-9,min(1-1e-9,rh)),.15)
 evap=evap_hour/4.;loss=loss_hour*900000.
 latent=evap*(2501.-2.361*tp);makeup=evap*4.186*(tp-12.)
 other=loss-latent-makeup
 cap_pool=c91.CAP*3600000.
 if tp<=27.95:on=True
 if tp>=28.05:on=False
 pool_req=max(0.,loss+.35*cap_pool*(28.-tp)) if on else 0.
 air_req=max(0.,min(15.,5.*(air.TARGET_T-ta)))*air.DT_S
 source_cap=source_kw*air.DT_S
 qp,qa=dispatch(pool_req,air_req,source_cap,priority)
 if ta>=air.TARGET_T:hvac_cap=15. # cooling is independent, not recovered source heat
 else:hvac_cap=qa/air.DT_S
 x=air.step(ta,w,tp,evap,5.,hvac_cap)
 hvac=x[13]
 if abs(max(0.,hvac)-qa)>1e-7:raise AssertionError("HVAC_DISPATCH_MISMATCH")
 tp1=tp+(qp-loss)/cap_pool
 ta1,w1=x[:2]
 pool_res=cap_pool*(tp1-tp)-(qp-loss)
 air_res=x[10]-x[9]-(x[11]+x[12]+hvac-x[14]+x[15]-x[16])
 combined=cap_pool*(tp1-tp)+x[10]-x[9]-(qp-makeup-other+x[12]+hvac-x[14]+x[15]-x[16])
 if max(abs(pool_res),abs(air_res),abs(combined))>1e-5 or abs(x[8])>1e-7:raise AssertionError("BALANCE")
 if abs(x[11]-latent)>1e-7:raise AssertionError("LATENT")
 if not 0<tp1<45:raise AssertionError("POOL_BOUND")
 values=(tp,tp1,ta,ta1,w,w1,rh,air.rh_from(ta1,w1),evap,loss,pool_req,air_req,qp,qa,
 source_cap,source_cap-qp-qa,pool_req-qp,air_req-qa,latent,makeup,other,x[11],x[12],hvac,
 x[14],x[15],x[16],pool_res,air_res,combined,x[8],int(on),source_kw)
 return (tp1,ta1,w1,on),values
def selftest(pool,air,c91,c92):
 assert dispatch(10,20,0,"water_first")== (0,0)
 assert dispatch(10,20,15,"water_first")== (10,5)
 assert dispatch(10,20,15,"air_first")== (0,15)
 assert dispatch(10,20,40,"air_first")== (10,20)
 for args in ((-1,1,5,"water_first"),(1,1,float("nan"),"water_first"),(1,1,5,"invalid")):
  try:dispatch(*args)
  except ValueError:pass
  else:raise AssertionError("NEGATIVE_TEST")
 st=(28.,29.,air.w_from(29.,.55),True)
 for priority in ("water_first","air_first"):
  for cap in (0.,10.,150.):
   s,v=step(pool,air,c91,c92,st,12,cap,priority)
   assert abs(v[12]+v[13]+v[15]-v[14])<1e-6
   assert v[12]+v[13]<=cap*900+1e-6
 return 13
def main():
 guard()
 for key,p in (("source",SRC),("air",AIR),("pool",POOL)):
  if sha(p)!=PINS[key]:raise RuntimeError("SOURCE_DRIFT_"+key)
 pool=load(POOL,"c127_pool");air=load(AIR,"c127_air")
 c91,c92,_,_=pool.load();tests=selftest(pool,air,c91,c92)
 out=D/"C127_BOUNDED_QUARTER.csv.gz";part=D/"C127_BOUNDED_QUARTER.partial.csv.gz"
 summary=D/"C127_SUMMARY.json";meta=D/"C127_METADATA.json"
 if any(p.exists() for p in (out,part,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
 states={name:{"state":(28.,29.,air.w_from(29.,.55),True),"n":0,"min_pool":99.,
 "max_pool":-99.,"max_RH":0.,"s":defaultdict(float)} for name in SCENARIOS}
 hours=0
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f,gzip.open(part,"xt",encoding="utf-8",newline="",compresslevel=4) as g:
  writer=csv.writer(g);writer.writerow(FIELDS)
  for row in csv.DictReader(f):
   if row["policy"]!="water_first" or row["control"]!="ideal":continue
   if hours%168==0:guard()
   hour=int(row["time"][11:13])
   for name,(priority,kw,limit) in SCENARIOS.items():
    if hours>=limit:continue
    st=states[name]
    for quarter in range(4):
     new,v=step(pool,air,c91,c92,st["state"],hour,kw,priority)
     writer.writerow([name,row["time"],quarter]+[f"{x:.12f}" for x in v])
     st["state"]=new;st["n"]+=1
     st["min_pool"]=min(st["min_pool"],new[0]);st["max_pool"]=max(st["max_pool"],new[0])
     st["max_RH"]=max(st["max_RH"],v[7])
     st["s"]["pool_heat_MWh"]+=v[12]/3600000.
     st["s"]["air_heat_MWh"]+=v[13]/3600000.
     st["s"]["pool_unmet_MWh"]+=v[16]/3600000.
     st["s"]["air_unmet_MWh"]+=v[17]/3600000.
     st["s"]["cap_saturated_quarters"]+=int(v[16]+v[17]>1e-6 and v[15]<1e-6)
     st["s"]["RH_above65_quarters"]+=int(v[7]>.65)
   hours+=1
 assert hours==8760
 for name,(_,_,limit) in SCENARIOS.items():assert states[name]["n"]==limit*4
 guard();os.replace(part,out)
 results={name:{"quarters":st["n"],"min_pool_C":st["min_pool"],"max_pool_C":st["max_pool"],
 "final_pool_C":st["state"][0],"final_air_C":st["state"][1],"max_RH":st["max_RH"],**dict(st["s"])}
 for name,st in states.items()}
 summary.write_text(json.dumps(results,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 metadata={"schema":"C127_SYNTHETIC_DISPATCH_V1","task_id":TASK,"source_sha256":PINS,
 "rows":sum(s["n"] for s in states.values()),"selftests":tests,"data_sha256":sha(out),
 "summary_sha256":sha(summary),"synthetic":True,"field_validated":False,
 "source_signoffs_added":0,"limitations":["Source cap is thermal kW, not electrical input/COP.",
 "Cooling is independently available and not charged to recovered heat.",
 "Quarterly pool thermostat uses synthetic loss model and ideal actuators.",
 "C124 room HVAC/dehumidifier remain synthetic, no measured hardware curves."]}
 meta.write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","rows":metadata["rows"],"selftests":tests,
 "data_sha256":metadata["data_sha256"],"summary":results},indent=2))
if __name__=="__main__":main()
