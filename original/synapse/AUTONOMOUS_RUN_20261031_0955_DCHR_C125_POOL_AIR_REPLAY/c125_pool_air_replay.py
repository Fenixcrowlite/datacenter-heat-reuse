"""C125: SHA-pinned synthetic coupled pool/room replay, isolated from MATLAB/SCADA."""
import csv, gzip, hashlib, importlib.util, json, math, os
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
ROOT=REC.parent
SRC=REC/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
AIR=REC/"AUTONOMOUS_RUN_20261031_0900_DCHR_C124_AIR_ENTHALPY"/"c124_air_enthalpy.py"
POOL=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
PINS={
 "source":"6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf",
 "air":"998d5da270714a1b84dfecaa774578174e7815fe4178af28920d0a24d4da3b11",
 "pool":"0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923"}
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
FIELDS=("mode","time","quarter","pool_T0","pool_T1","air_T0","air_T1","w0","w1","RH0","RH1",
 "evap_kg","pool_heat_kJ","pool_loss_kJ","latent_kJ","makeup_kJ","other_loss_kJ",
 "air_evap_kJ","vent_kJ","hvac_kJ","dehum_kJ","humid_kJ","cond_kJ",
 "air_H0_kJ","air_H1_kJ","pool_residual_kJ","air_residual_kJ","combined_residual_kJ",
 "air_mass_residual_kg")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,REC,ROOT,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return m
def calc(pool,air,c91,c92,t_pool,t_air,w,hour,heat_mwh,mode):
 if not all(map(math.isfinite,(t_pool,t_air,w,heat_mwh))):raise ValueError("NONFINITE")
 if heat_mwh<0 or not 0<t_pool<45:raise ValueError("BAD_INPUT")
 rh0=air.rh_from(t_air,w)
 evap_rh=.55 if mode=="fixed_RH" else max(1e-9,min(1-1e-9,rh0))
 loss_hour,evap_hour=pool.loss_components(c91,c92,t_pool,hour,evap_rh,.15)
 evap=evap_hour/4.
 q_loss=loss_hour*3600000./4.
 q_lat=evap*(2501.-2.361*t_pool)
 q_makeup=evap*4.186*(t_pool-12.)
 q_other=q_loss-q_lat-q_makeup
 q_heat=heat_mwh*3600000./4.
 t_pool1=t_pool+(q_heat-q_loss)/(c91.CAP*3600000.)
 x=air.step(t_air,w,t_pool,evap,5.,15.)
 t_air1,w1=x[:2]
 air_evap,vent,dehum,humid,cond=x[11:12][0],x[12],x[14],x[15],x[16]
 h0,h1=x[9],x[10]
 pool_res=c91.CAP*3600000.*(t_pool1-t_pool)-(q_heat-q_loss)
 air_res=h1-h0-(air_evap+vent+x[13]-dehum+humid-cond)
 combined=c91.CAP*3600000.*(t_pool1-t_pool)+h1-h0-(q_heat-q_makeup-q_other+vent+x[13]-dehum+humid-cond)
 if abs(air_evap-q_lat)>1e-8:raise AssertionError("LATENT_MISMATCH")
 if max(abs(pool_res),abs(air_res),abs(combined))>1e-5:raise AssertionError("ENERGY_BALANCE")
 if abs(x[8])>1e-7 or not 0<t_pool1<45:raise AssertionError("MASS_OR_TEMPERATURE")
 return (t_pool1,t_air1,w1,(t_pool,t_pool1,t_air,t_air1,w,w1,rh0,air.rh_from(t_air1,w1),
   evap,q_heat,q_loss,q_lat,q_makeup,q_other,air_evap,vent,x[13],dehum,humid,cond,
   h0,h1,pool_res,air_res,combined,x[8]))
def selftest(pool,air,c91,c92):
 t=28.;a=29.;w=air.w_from(a,.55)
 for mode in ("fixed_RH","feedback_RH"):
  v=calc(pool,air,c91,c92,t,a,w,12,.005,mode)
  assert abs(v[3][11]-v[3][14])<1e-8
  assert max(abs(z) for z in v[3][-4:-1])<1e-5
 for invalid in (-1,float("nan")):
  try:calc(pool,air,c91,c92,28,29,w,12,invalid,"feedback_RH")
  except ValueError:pass
  else:raise AssertionError("INVALID_ACCEPTED")
 return 6
def main():
 guard()
 for key,p in (("source",SRC),("air",AIR),("pool",POOL)):
  if sha(p)!=PINS[key]:raise RuntimeError("SOURCE_SHA_DRIFT_"+key)
 air=load(AIR,"c125_air");pool=load(POOL,"c125_pool")
 c91,c92,_,_=pool.load()
 n=selftest(pool,air,c91,c92)
 modes=("fixed_RH","feedback_RH")
 states={m:{"pool":28.,"air":29.,"w":air.w_from(29.,.55),"n":0,"s":defaultdict(float),
             "min_pool":99.,"max_rh":0.,"min_rh":1.} for m in modes}
 output=D/"C125_POOL_AIR_QUARTER.csv.gz";partial=D/"C125_POOL_AIR_QUARTER.partial.csv.gz"
 summary=D/"C125_SUMMARY.json";meta=D/"C125_METADATA.json"
 if any(p.exists() for p in (output,partial,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
 hours=rows=0
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f,gzip.open(partial,"xt",encoding="utf-8",newline="",compresslevel=4) as g:
  writer=csv.writer(g);writer.writerow(FIELDS)
  for r in csv.DictReader(f):
   if r["policy"]!="water_first" or r["control"]!="ideal":continue
   if hours%720==0:guard()
   heat=float(r["pool_HP_heat_MWh"]);hour=int(r["time"][11:13])
   for mode,st in states.items():
    for quarter in range(4):
     t_pool,t_air,w,values=calc(pool,air,c91,c92,st["pool"],st["air"],st["w"],hour,heat,mode)
     writer.writerow([mode,r["time"],quarter]+[f"{v:.12f}" for v in values])
     st["pool"],st["air"],st["w"]=t_pool,t_air,w
     st["n"]+=1;rows+=1
     st["min_pool"]=min(st["min_pool"],t_pool)
     st["min_rh"]=min(st["min_rh"],values[7])
     st["max_rh"]=max(st["max_rh"],values[7])
     st["s"]["evap_kg"]+=values[8]
     st["s"]["pool_loss_MWh"]+=values[10]/3600000.
     st["s"]["RH_above65_quarters"]+=int(values[7]>.65)
     st["s"]["RH_below45_quarters"]+=int(values[7]<.45)
   hours+=1
 assert hours==8760 and rows==70080
 guard();os.replace(partial,output)
 results={mode:{"quarters":st["n"],"min_pool_C":st["min_pool"],"final_pool_C":st["pool"],
                "final_air_C":st["air"],"min_RH":st["min_rh"],"max_RH":st["max_rh"],**dict(st["s"])}
          for mode,st in states.items()}
 summary.write_text(json.dumps(results,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 metadata={"schema":"C125_SYNTHETIC_POOL_AIR_REPLAY_V1","task_id":TASK,"source_sha256":PINS,
           "rows":rows,"hours":hours,"selftests":n,"data_sha256":sha(output),
           "summary_sha256":sha(summary),"synthetic":True,"field_validated":False,
           "source_signoffs_added":0,
           "limitations":["C116 hourly pool heat is replayed exogenously, not re-dispatched.",
             "C93 hourly loss formula sampled at each quarter, fixed other boundary conditions.",
             "C124 fixed supply and simplified dehumidifier/HVAC assumptions retained.",
             "Conservation is bookkeeping, not physical or equipment validation.",
             "No measured weather, vendor COP, pool instrumentation or primary-source signoff."]}
 meta.write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","hours":hours,"rows":rows,"selftests":n,
                   "data_sha256":metadata["data_sha256"],"summary":results},indent=2))
if __name__=="__main__":main()
