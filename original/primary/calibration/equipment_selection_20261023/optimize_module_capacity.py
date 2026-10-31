# -*- coding: utf-8 -*-
"""Rank 2MW modules with N+1 using actual executed 105120-step Simulink HP output.
Clipping source at nameplate is a SCREENING approximation, no rescheduled TES.
"""
from pathlib import Path
import csv,json,math
HERE=Path(__file__).resolve().parent
CL=HERE.parent/"closed_loop_simulink_20261023"
SOURCE=CL/"no_pool_35_8760h.csv"
PRICE_E=152.0726027397;PRICE_G=55.6347945205;GASETA=.9
DT=1/12;DISCOUNT=.06;YEARS=20;ANNUITY=(1-(1+DISCOUNT)**-YEARS)/DISCOUNT
caps=[6,8,10,12] # useful MW provided by duty modules only, plus 2MW N+1 spare
bycap={c:{"HPHeat_MWh":0.0,"HPElec_MWh":0.0,"new_gas_heat_MWh":0.0,"hours_limited":0.0,"unavailable_HP_thermal_MWh":0.0} for c in caps}
count=0;maxHP=0.0
with SOURCE.open(encoding="utf-8-sig",newline="") as f:
 for v in csv.DictReader(f):
  count+=1
  q=float(v["DistrictHPHeat_MW"])
  we=float(v["DistrictHPel_MW"])
  gas=float(v["GasHeat_MW"])
  assert q>=0 and we>=0 and q+1e-8>=we
  maxHP=max(maxHP,q)
  for cap in caps:
   used=min(q,cap)
   frac=(used/q if q>0 else 0)
   b=bycap[cap]
   b["HPHeat_MWh"]+=used*DT
   b["HPElec_MWh"]+=we*frac*DT
   b["new_gas_heat_MWh"]+=(gas+q-used)*DT
   b["unavailable_HP_thermal_MWh"]+=(q-used)*DT
   b["hours_limited"]+=(DT if q>cap+1e-10 else 0)
assert count==105120
cases=[]
for cap in caps:
 q=bycap[cap]
 gross=q["HPHeat_MWh"]/GASETA*PRICE_G-q["HPElec_MWh"]*PRICE_E
 for price in [700,1000,1400]:
  installedMW=cap+2 # 2MW spare physically purchased
  capital=installedMW*1000*price
  auxkw=50*installedMW/14
  auxcost=auxkw*8760/1000*PRICE_E
  maint=.02*capital
  annual=gross-auxcost-maint
  case={"duty_nameplate_MW":cap,"reserve_MW":2,"installed_total_MW":installedMW,
        "modules_2MW_total":int(installedMW/2),
        "max_model_hp_MW":round(maxHP,3),"limited_hours":round(q["hours_limited"],2),
        "HP_heat_delivered_MWh":round(q["HPHeat_MWh"],2),
        "additional_gas_due_capacity_MWh":round(q["unavailable_HP_thermal_MWh"],2),
        "HP_electricity_MWh":round(q["HPElec_MWh"],2),
        "CAPEX_assumed_EUR_per_kW":price,"CAPEX_total_EUR":round(capital),
        "gross_heat_energy_saving_EUR_y":round(gross),
        "annual_aux_pumps_EUR_y":round(auxcost),
        "annual_fixed_maintenance_EUR_y":round(maint),
        "net_benefit_EUR_y":round(annual),
        "NPV_20y_6percent_EUR":round(-capital+annual*ANNUITY),
        "payback_simple_y":round(capital/annual,2) if annual>0 else None,
        "model_warning":"clipped HP output; TES/gas redispatch approximated not independently rerun"}
  cases.append(case)
path=HERE/"network_module_2MW_Nplus1_screen.csv"
if path.exists():raise FileExistsError(str(path))
with path.open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
j=HERE/"network_module_2MW_Nplus1_screen.json"
if j.exists():raise FileExistsError(str(j))
j.write_text(json.dumps({"source":"actual Simulink 105120-step hourly 2025, fixed PLR scaling","scope":"screening capacity selection only; manufacturer duty not confirmed","cases":cases},indent=2,ensure_ascii=False),encoding="utf-8")
for v in cases:
 if v["CAPEX_assumed_EUR_per_kW"]==1000:
  print("HP_BANK_CAP",v["duty_nameplate_MW"],"MW",v["modules_2MW_total"],"modules","unserved",v["additional_gas_due_capacity_MWh"],"MWh","limited_hours",v["limited_hours"],"NPV_MEUR",round(v["NPV_20y_6percent_EUR"]/1e6,2))
print("HP_BANK_SCREEN_VERIFIED",len(cases),"cases, lines",count,"peak_HP_MW",round(maxHP,3))
