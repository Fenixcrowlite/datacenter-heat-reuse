"""C116: synthetic two-way pool RH / evaporation / water / HVAC coupling.
Standalone sidecar, immutable SHA-pinned C111 and C112 sources. No SCADA/MATLAB writes.
"""
from __future__ import annotations
import csv, gzip, hashlib, importlib.util, json, math, os
from pathlib import Path
from collections import defaultdict

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C111=REC/"AUTONOMOUS_RUN_20261031_0152_DCHR_C111_EVAP_FEEDBACK"/"c111_evap_feedback.py"
C112=REC/"AUTONOMOUS_RUN_20261031_0251_DCHR_C112_FINITE_HUMIDITY"/"c112_finite_humidity.py"
PINS={"C111":"dba0c4a1d1fc7b568b83e62dea4548c28df0b755720e84f2f5d4c3b4cdfb1395",
      "C112":"6dc6c77adc479f9bdbfcc2c5937aee6b8f31b6b02764d93b0ffefab95b84ebc8"}
TASK="scc-2aab24704c2bd0"
CAPS={"ideal":(1e9,1e9),"limited5":(5.,5.),"capacity_C114":(45.66,29.70)}
FIELDS=("policy","control","time","pool_start_C","pool_end_C","room_RH_start",
 "room_RH_end","evap_kg","pool_loss_MWh","latent_pool_MWh","makeup_pool_MWh",
 "other_pool_loss_MWh","pool_HP_heat_MWh","pool_HP_electric_MWh",
 "air_HP_heat_MWh","air_HP_electric_MWh","air_heat_request_MWh",
 "air_unmet_MWh","air_HVAC_electric_MWh","pump_electric_MWh",
 "source_cap_MWh","source_pool_MWh","source_air_MWh","room_dehum_kg",
 "room_humid_kg","room_condensate_kg","room_storage_delta_kg",
 "room_vent_net_kg","room_moisture_residual_kg","pool_energy_residual_MWh",
 "source_energy_residual_MWh","total_electric_MWh")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,REC,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def assert_balance(x,tol=2e-9):
 for k in ("room_moisture_residual_kg","pool_energy_residual_MWh","source_energy_residual_MWh"):
  if not math.isfinite(x[k]) or abs(x[k])>tol:raise AssertionError("BALANCE_"+k)
 if x["evap_kg"]<0 or x["source_pool_MWh"]+x["source_air_MWh"]>x["source_cap_MWh"]+tol:
  raise AssertionError("PHYSICAL_BOUND")
 if not (0<=x["room_RH_end"]<=1+tol and 0<x["pool_end_C"]<45):
  raise AssertionError("STATE_BOUND")
def simulate(c111,c112,c93,c104,c108,c96,c91,c92,policy,source,weather,label,cap,writer):
 t=28.;w=c104.W_IN;active=False
 s=defaultdict(float);rh_min=1.;rh_max=0.;t_min=100.;baseline=0
 for i,row in enumerate(source):
  if i%720==0:guard()
  stamp=row["time"];out=weather[stamp];hour=int(stamp[11:13])
  rh=c112.rh_from_w(c104,w)
  # C93 requires strict RH < 1; saturation is a valid physical endpoint.
  loss,evap=c93.loss_components(c91,c92,t,hour,max(1e-9,min(1-1e-9,rh)),.15)
  latent=evap*(2501.-2.361*t)/3600000.
  makeup=evap*4.186*(t-12.)/3600000.
  other=loss-latent-makeup
  if other<-1e-9:raise AssertionError("NEGATIVE_OTHER_POOL_LOSS")
  # C104 coil is an idealized fixed-29C supply preconditioner; room actuator is bounded.
  base=c111.air(c104,out,evap)
  supply=min(c104.w_ratio(float(out["Tout_C"]),float(out["RH_out"])),c104.W_IN)
  room=c112.step(c104,w,supply,evap,*cap)
  new_w,d_req,h_req,d,h,unmet_d,unmet_h,cond,storage,vent,residual,humid_electric=room
  new_rh=c112.rh_from_w(c104,new_w)
  # Replace ideal C104 room actuator electric and condenser credit with actual actuator.
  ideal_actuator_el=(base[3]*c104.DEHUM_KWH_KG+base[4]*c104.STEAM_KWH_KG)/1000.
  hvac_el=base[16]-ideal_actuator_el+humid_electric
  latent_room=d*(2501.-2.361*c104.T_IN)/3600000.
  credit=min(base[13],c104.COND_CREDIT_FRACTION*(latent_room+d*c104.DEHUM_KWH_KG/1000.))
  air_request=max(0.,base[13]-credit)
  if t<=c91.ON_C:active=True
  elif t>=c91.OFF_C:active=False
  pool_request=max(0.,loss+(c91.OFF_C-t)*c91.CAP) if active else 0.
  source_cap=float(row["source_cap_MWh"])
  ps,ats,ph,ah=c108.allocate(source_cap,pool_request,air_request,policy)
  pe=ph/c108.POOL_COP;ae=ah/c108.AIR_COP
  pump=c96.pump_power_mw(0.5) if ps+ats>1e-12 else 0.  # C111 constrained source: 0.5 kg/s
  end=t+(ph-loss)/c91.CAP
  total=pe+ae+pump+hvac_el
  vals=dict(policy=policy,control=label,time=stamp,pool_start_C=t,pool_end_C=end,
   room_RH_start=rh,room_RH_end=new_rh,evap_kg=evap,pool_loss_MWh=loss,
   latent_pool_MWh=latent,makeup_pool_MWh=makeup,other_pool_loss_MWh=other,
   pool_HP_heat_MWh=ph,pool_HP_electric_MWh=pe,air_HP_heat_MWh=ah,
   air_HP_electric_MWh=ae,air_heat_request_MWh=air_request,
   air_unmet_MWh=max(0.,air_request-ah),air_HVAC_electric_MWh=hvac_el,
   pump_electric_MWh=pump,source_cap_MWh=source_cap,source_pool_MWh=ps,
   source_air_MWh=ats,room_dehum_kg=d,room_humid_kg=h,
   room_condensate_kg=cond,room_storage_delta_kg=storage,
   room_vent_net_kg=vent,room_moisture_residual_kg=residual,
   pool_energy_residual_MWh=c91.CAP*(end-t)-(ph-loss),
   source_energy_residual_MWh=(ph-pe-ps)+(ah-ae-ats),
   total_electric_MWh=total)
  assert_balance(vals)
  if label=="ideal":
   # Independent immutable C111 dynamic source must be reproduced with ideal room RH.
   for key,actual in (("pool_end_C",end),("air_evap_kg",evap),
                      ("air_external_heat_MWh",air_request),
                      ("air_HVAC_electric_MWh",hvac_el)):
    if abs(actual-float(row[key]))>2e-8:raise AssertionError("IDEAL_REGRESSION_"+key)
   baseline+=1
  writer.writerow([vals[k] if k in ("policy","control","time") else f"{vals[k]:.12f}" for k in FIELDS])
  for key in ("evap_kg","pool_loss_MWh","latent_pool_MWh","makeup_pool_MWh",
              "pool_HP_heat_MWh","air_unmet_MWh","air_HVAC_electric_MWh",
              "total_electric_MWh","room_dehum_kg","room_humid_kg",
              "room_condensate_kg","room_storage_delta_kg","room_vent_net_kg"):
   s[key]+=vals[key]
  s["hours_below_RH45"]+=int(new_rh<.45)
  s["hours_above_RH65"]+=int(new_rh>.65)
  s["hours_pool_below_27p5"]+=int(end<27.5)
  rh_min=min(rh_min,new_rh);rh_max=max(rh_max,new_rh);t_min=min(t_min,end)
  t=end;w=new_w
 if abs(s["room_storage_delta_kg"]-c112.M_ROOM*(w-c104.W_IN))>1e-6:raise AssertionError("ANNUAL_MASS_BALANCE")
 return dict(policy=policy,control=label,hours=len(source),min_pool_C=t_min,
             final_pool_C=t,min_RH=rh_min,max_RH=rh_max,
             ideal_reference_hours=baseline,**s)
def run():
 guard()
 for k,p in (("C111",C111),("C112",C112)):
  if sha(p)!=PINS[k]:raise RuntimeError("SOURCE_DRIFT_"+k)
 c111=module(C111,"c111_c116");c112=module(C112,"c112_c116")
 for k,p in c111.P.items():
  if sha(p)!=c111.PINS[k]:raise RuntimeError("SOURCE_DRIFT_"+k)
 for k,p in (("C111",c112.C111),("C106",c112.C106),("C104",c112.C104)):
  if sha(p)!=c112.PINS[k]:raise RuntimeError("SOURCE_DRIFT_C112_"+k)
 c93=c111.loadmod("C93");c104=c111.loadmod("C104");c108=c111.loadmod("C108")
 c91,c92,_,_=c93.load();c96=c108.module(c108.C96,"c96_c116")
 if c112.selftest(c104)!=21:raise RuntimeError("BASELINE_TEST_DRIFT")
 policies,weather=c112.read_inputs()
 out=D/"C116_TWO_WAY_HOURLY.csv.gz";tmp=D/"C116_TWO_WAY.partial.csv.gz"
 summary=D/"C116_SUMMARY.csv";meta=D/"C116_METADATA.json"
 if any(p.exists() for p in (out,tmp,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
 results=[]
 with gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
  writer=csv.writer(f);writer.writerow(FIELDS)
  for policy,rows in policies.items():
   for label,cap in CAPS.items():
    guard();results.append(simulate(c111,c112,c93,c104,c108,c96,c91,c92,
                                    policy,rows,weather,label,cap,writer))
 guard();os.replace(tmp,out)
 with summary.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
 data={"schema":"C116_TWO_WAY_SYNTHETIC_V1","task_id":TASK,"synthetic":True,
  "field_validated":False,"source_signoffs_added":0,"rows":len(results)*8760,
  "source_sha256":{"C111_SCRIPT":PINS["C111"],"C112_SCRIPT":PINS["C112"],
                    **c111.PINS},"controls":CAPS,
  "hourly_sha256":sha(out),"summary_sha256":sha(summary),
  "limitations":["Fixed 29 C indoor air and idealized C104 outdoor coil; not a full air enthalpy state model.",
   "Hourly explicit RH feedback uses start-of-hour RH; no subhour iteration.",
   "C112 saturation condensate is an endpoint clip; latent condensate heat not recovered.",
   "C114 capacities are synthetic hourly thresholds, not real vendor sizing.",
   "Shared source capacity replayed from C111; no re-solving heat exchanger temperature.",
   "No measured hardware curves, weather validation, MATLAB integration, or primary-source signoffs."]}
 with meta.open("x",encoding="utf-8") as f:json.dump(data,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"status":"PASS","rows":data["rows"],"hourly_sha256":data["hourly_sha256"],
  "summary":[{k:r[k] for k in ("policy","control","min_pool_C","min_RH","max_RH","hours_above_RH65","evap_kg")} for r in results]},indent=2))
if __name__=="__main__":run()
