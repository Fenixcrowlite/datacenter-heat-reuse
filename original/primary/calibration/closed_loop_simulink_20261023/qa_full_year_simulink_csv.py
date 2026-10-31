# -*- coding: utf-8 -*-
"""Streaming independent verification of actual 300-second Simulink output."""
from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parent
CASES=["no_pool_35","direct_35","heatpump_25","outage_35"]
analysis=[]
for name in CASES:
 p=ROOT/(name+"_8760h.csv")
 assert p.exists(),str(p)
 n=0;poolheat=0;poolSrc=0;poolEl=0;dhSource=0;dhElectric=0;gas=0
 highTemp=-1e9;srcViolation=0;dhBalance=0;poolBalance=0
 noSourceDuringOutage=0
 with p.open(encoding="utf-8-sig",newline="") as fh:
  rows=csv.DictReader(fh)
  for r in rows:
   n+=1
   u={k:float(v) for k,v in r.items()}
   h=u["time_h"]
   poolheat+=u["PoolHeat_MW"]/12
   poolSrc+=u["DCtoPool_MW"]/12
   poolEl+=u["PoolHPElectric_MW"]/12
   dhSource+=u["DCtoDistrict_MW"]/12
   dhElectric+=u["DistrictHPel_MW"]/12
   gas+=u["GasHeat_MW"]/12
   highTemp=max(highTemp,u["PoolT_C"])
   srcViolation=max(srcViolation,u["DCtoDistrict_MW"]+u["DCtoPool_MW"]-u["DCAvailable_MW"])
   poolBalance=max(poolBalance,abs(u["PoolHeat_MW"]-u["DCtoPool_MW"]-u["PoolHPElectric_MW"]))
   dhBalance=max(dhBalance,abs(u["DistrictHPHeat_MW"]-u["DCtoDistrict_MW"]-u["DistrictHPel_MW"]))
   assert u["PoolHeat_MW"]>=0 and u["DCAvailable_MW"]>=0
   if name=="outage_35" and 48<=h<72:
    noSourceDuringOutage=max(noSourceDuringOutage,abs(u["DCAvailable_MW"])+abs(u["PoolHeat_MW"]))
  if n!=8760*12:raise ValueError(f"Expected 105120 intervals, found {n}")
  if srcViolation>1e-8 or poolBalance>1e-8 or dhBalance>1e-8:
   raise AssertionError(f"{name}: double use/partition violation {srcViolation, poolBalance, dhBalance}")
  if "no_pool" not in name and highTemp>27.800001:raise AssertionError("Pool overheated")
  if name=="outage_35" and noSourceDuringOutage>1e-9:raise AssertionError("Outage fail-safe failed")
  analysis.append({"scenario":name,"N":n,"heat_pool_MWh":round(poolheat,4),
   "source_pool_MWh":round(poolSrc,4),"hp_electric_pool_MWh":round(poolEl,4),
   "gas_MWh":round(gas,4),"peak_T_pool_C":round(highTemp,5),
   "max_DC_overuse_MW":srcViolation,"max_pool_partition_err_MW":poolBalance,
   "max_dh_partition_err_MW":dhBalance,"outage_overlap":noSourceDuringOutage})
o=ROOT/"closed_loop_independent_QA_2025.json"
if o.exists():raise FileExistsError(str(o))
o.write_text(json.dumps({"dataset":"MATLAB Simulink generated CSV output",
 "verified":True,"interval_s":300,"cases":analysis,
 "limitations":"Energy and temperature tested against model equations; NOT site commissioning or equipment certification"},indent=2,ensure_ascii=False),encoding="utf-8")
print("INDEPENDENT_CLOSED_LOOP_QA_PASS",json.dumps(analysis,ensure_ascii=False))
