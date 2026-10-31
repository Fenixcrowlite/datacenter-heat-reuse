# -*- coding: utf-8 -*-
"""Independent MATLAB CSV interface audit; no external files modified."""
import csv,json,math
from datetime import datetime,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
names=["liquid35_without_pool","liquid35_direct_pool",
       "air25_without_pool","air25_hp_pool"]
out=[]
for name in names:
 p=ROOT/(name+"_8760h.csv")
 with p.open(encoding="utf-8-sig",newline="") as f:
  rdr=csv.DictReader(f)
  rows=0;peak_t=-1e9;max_source_over=-1e9;max_dh_residual=0;max_hp_residual=0
  max_pool_residual=0;max_tes=0;min_tes=1e9;monthly=[]
  for row in rdr:
   rows+=1
   a={k:float(v) for k,v in row.items() if k!="Time"}
   peak_t=max(peak_t,a["Pool_T_C"])
   total_dc=a["DC_Source_Available_MW"]
   source_alloc=a["DH_Source_MW"]+a["Pool_Source_Reserved_MW"]
   max_source_over=max(max_source_over,source_alloc-total_dc)
   dh_res=(a["DH_HP_Q_MW"]-a["TES_Charge_MW"]+
          a["TES_Discharge_MW"]+a["Gas_Q_MW"]-a["DH_Demand_MW"])
   hp_res=a["DH_HP_Q_MW"]-a["DH_Source_MW"]-a["DH_HP_El_MW"]
   pool_res=a["Pool_Q_MW"]-a["Pool_Source_MW"]-a["Pool_El_MW"]
   max_dh_residual=max(max_dh_residual,abs(dh_res))
   max_hp_residual=max(max_hp_residual,abs(hp_res))
   max_pool_residual=max(max_pool_residual,abs(pool_res))
   max_tes=max(max_tes,a["TES_E_MWh"])
   min_tes=min(min_tes,a["TES_E_MWh"])
   assert a["Pool_Source_Reserved_MW"]+1e-9>=a["Pool_Source_MW"]
   assert all(math.isfinite(v) for v in a.values())
   assert a["Pool_Q_MW"]>=-1e-8 and a["Gas_Q_MW"]>=-1e-8
  assert rows==8760 and max_source_over<1e-8 and max_dh_residual<1e-8
  assert max_hp_residual<1e-8 and max_pool_residual<1e-8
  assert max_tes<=50.001 and min_tes>=-1e-7
  if "without" not in name:assert peak_t<=27.801
  out.append({"case":name,"rows":rows,"max_pool_C":peak_t,
   "max_source_overallocation_MW":max_source_over,
   "max_DH_balance_residual_MW":max_dh_residual,
   "max_HP_partition_residual_MW":max_hp_residual,
   "max_pool_partition_residual_MW":max_pool_residual,
   "TES_min_max_MWh":[min_tes,max_tes]})
contract={
"date":"2026-10-23","model":"independent coupled_dispatch research bridge",
"simulink_owner":"parallel pool workstream; NO changes performed to their .slx",
"time_axis":{"field":"Time","calendar_year":2025,"rows":8760,
 "UTC_basis":"NASA weather source UTC; Simulink MATLAB datetime naive represents UTC",
 "local_pool_hours":"Europe/Bratislava timezone including DST, 08:00-20:00"},
"units":{"DH_Demand_MW":"MW thermal","DC_Source_Available_MW":"MW thermal IT source",
 "Pool_Q_MW":"MW useful heat delivered to pool","Pool_Source_MW":"MW DC waste heat allocated to pool",
 "Pool_El_MW":"MW pool heat pump compressor electricity",
 "Pool_Source_Reserved_MW":"MW max instantaneous (5min) source reservation for each dispatch hour",
 "DH_Source_MW":"MW DC source actually extracted by district HP",
 "DH_HP_Q_MW":"MW district HP useful thermal output",
 "DH_HP_El_MW":"MW district HP compressor electricity",
 "TES_Charge_MW":"MW TES heat input",
 "TES_Discharge_MW":"MW TES heat output",
 "TES_E_MWh":"MWh TES stored energy",
 "Gas_Q_MW":"MW useful thermal backup",
 "Pool_T_C":"degrees C (hour-end water temperature)",
 "Pool_Loss_MW":"MW pool net heat loss","Pool_Cover":"fraction of substeps covered in hour",
 "DH_COP":"dimensionless; theoretical Carnot factor surrogate"},
"identity_checks":[
 "DH_Q=DH_HP_Q-TES_Charge+TES_Discharge+Gas_Q",
 "DH_HP_Q=DH_Source+DH_HP_El",
 "Pool_Q=Pool_Source+Pool_El",
 "DH_Source+Pool_Source_Reserved <= DC_Source_Available",
 "Pool_Source <= Pool_Source_Reserved"],
"safety":{"do_not_replay_Pool_Q_into_unmodified_original_28C_relay":True,
 "original_pool_slx_has_28.2_off_threshold":True,
 "coupled_study_control_off_C":27.60,"hard_model_ceiling_C":27.80,
 "legal_design_certified":False,"independent_IT_cooling_required":True},
"caveats":[
 "Exports are outputs, not the inputs for a numerically closed co-simulation.",
 "Feed source CAPACITY to updated Simulink with a proper feedback loop, not presimulated delivered pool heat.",
 "For true combined co-simulation, Simulink must feed actual subhourly source draw back into district dispatch.",
 "Exhaustive year still uses synthetic IT profile, assumed heat capture and pool hall psychrometrics.",
 "ERF needs an actual heat meter at DC boundary and correct annual measurement perimeter.",
 "Fixed COP4 for pool HP and theoretical network COP are NOT manufacturer maps"],
"independent_QA":out}
p=ROOT/"coupled_interface_contract_2025.json"
if p.exists():raise FileExistsError(str(p))
p.write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding="utf-8")
print("INDEPENDENT_CSV_QA_PASS",json.dumps([{"case":i["case"],"rows":i["rows"],"max_temp":round(i["max_pool_C"],3)} for i in out],ensure_ascii=False))
