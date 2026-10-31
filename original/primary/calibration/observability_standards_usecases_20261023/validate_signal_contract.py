# -*- coding: utf-8 -*-
"""Standardized data-contract and validation gates for every 300-second Simulink signal.
Engineering units, clock basis, evidence, quality and exact invariants are explicit.
"""
from pathlib import Path
import pandas as pd,numpy as np,json,csv
P=Path(__file__).resolve().parent
PR=P.parent.parent
CL=PR/"calibration"/"closed_loop_simulink_20261023"
cases={k:pd.read_csv(CL/(k+"_8760h.csv")) for k in ("no_pool_35","direct_35","heatpump_25","outage_35")}
definitions=[
# signal,unit,role,valid_range,required_source,calibration_requirement
("time_h","h since 2025-01-01T00:00 UTC","five-minute simulation timestamp","0..8759.916667","Simulink export, UTC timezone","UTC calendar & DST convention"),
("PoolT_C","degC","pool water temperature","-5..45 model","synthetic state","2 independent calibrated pool-water probes for operation"),
("PoolHeat_MW","MW_thermal","heat transferred to pool","0..0.15 scenario","Simulink computed useful duty","verified pool heat meter for physical site"),
("DCtoPool_MW","MW_thermal","data-centre waste heat source into pool","0..0.15 scenario","Simulink heat balance","DC boundary metered thermal source transfer"),
("PoolHPElectric_MW","MW_electrical","pool HP compressor electric input","0..0.15 scenario","Simulink COP4 hypothesis","true compressor electric submeters"),
("DistrictHPHeat_MW","MW_thermal","district HP useful heat","0..12 scenario","Simulink thermal source+compressor","calibrated heat meter at district heat delivery"),
("DCtoDistrict_MW","MW_thermal","DC waste heat extracted for district HP","0..8.5 scenario","Simulink HP first law","calibrated meter at actual DC boundary"),
("DistrictHPel_MW","MW_electrical","district HP compressor input","0..12 scenario","simulated Carnot COP","electric kWh site equipment submeter"),
("GasHeat_MW","MW_thermal","thermal backup useful output","0..20 scenario","simulated district residual","gas kWh fuel meter + boiler useful meter"),
("TESCharge_MW","MW_thermal","TES heat charging power","0..5 scenario","Simulink","TES charge heat meter"),
("TESDischarge_MW","MW_thermal","TES heat discharge power","0..5 scenario","Simulink","TES discharge heat meter"),
("TES_E_MWh","MWh_thermal","TES energy state","0..50 assumed","Simulink","calibrated TES sensor profile and thermal storage model"),
("PoolNetLoss_MW","MW_thermal","pool net heat loss, signed","may be negative","reduced evaporation and room thermal model","hall air and surface temperature RH flow meter"),
("DCAvailable_MW","MW_thermal","recoverable IT heat availability","0..8.5 model","IT assumed 85% capture","IT vendor cooling water flow and delta T")
]
default_tol={"PoolT_C":.01,"DCAvailable_MW":1e-8}
catalog=[]
for name,unit,meaning,valid,source,req in definitions:
 catalog.append({"signal":name,"SI_semantic_unit":unit,"definition":meaning,
   "normalization":"timestamp UTC year 2025, every 300 seconds, no UTC offset in CSV numeric elapsed time",
   "perimeter":"DC+pool+district Simulink model; physical metering boundaries TBD",
   "engineering_range":valid,"sample_seconds":300,
   "raw_origin":source,"physical_measurement_required":req,
   "software_data_qa":"EXECUTED_MODEL_ONLY","meter_id":None,
   "uncertainty":None,"standard_reportable":False,
   "validation_tolerance":default_tol.get(name,1e-7)})
signalNames={x["signal"] for x in catalog}
for case,v in cases.items():
 assert set(v.columns)==signalNames,(case,set(v.columns)^signalNames)
 assert len(v)==105120 and np.isfinite(v.to_numpy()).all(),case
 assert np.allclose(v.time_h.to_numpy(),np.arange(len(v))/12,atol=1e-8),case
 assert (v.PoolT_C<=27.800001).all()
 assert (v.PoolHeat_MW>=-1e-10).all()
 assert (v.TES_E_MWh>=-1e-8).all() and (v.TES_E_MWh<=50.001).all()
 assert (v.DCtoPool_MW+v.DCtoDistrict_MW<=v.DCAvailable_MW+1e-7).all()
 assert ((v.PoolHeat_MW-v.DCtoPool_MW-v.PoolHPElectric_MW).abs()<=1e-8).all()
 assert ((v.DistrictHPHeat_MW-v.DCtoDistrict_MW-v.DistrictHPel_MW).abs()<=1e-8).all()
 checks={
  "pool":float((v.PoolHeat_MW-v.DCtoPool_MW-v.PoolHPElectric_MW).abs().max()),
  "district":float((v.DistrictHPHeat_MW-v.DCtoDistrict_MW-v.DistrictHPel_MW).abs().max()),
  "source_oversub":max(0,float((v.DCtoPool_MW+v.DCtoDistrict_MW-v.DCAvailable_MW).max())),
  "TES_min":float(v.TES_E_MWh.min()),"TES_max":float(v.TES_E_MWh.max()),
  "pool_Tmax":float(v.PoolT_C.max()),"rows":len(v)}
 if case=="no_pool_35":assert (v.PoolHeat_MW==0).all()
 if case=="outage_35":assert (v.loc[v.time_h.between(48,72,inclusive="left"),"PoolHeat_MW"]==0).all()
 (P/(case+"_signal_qa.json")).write_text(json.dumps(checks,indent=2),encoding="utf-8")
with (P/"signal_dictionary_300s.csv").open("x",encoding="utf-8-sig",newline="") as f:
 writer=csv.DictWriter(f,fieldnames=list(catalog[0]));writer.writeheader();writer.writerows(catalog)
(P/"signal_dictionary_300s.json").write_text(json.dumps(catalog,indent=2,ensure_ascii=False),encoding="utf-8")
(P/"machine_validation_gates.json").write_text(json.dumps({
 "software_only":True,
 "passes":[
 "All four cases exactly 105120 five-minute steps covering 8760h",
 "All timestamps consecutive and finite for each signal",
 "Pool temperature <=27.800001C every sample",
 "TES within 0..50MWh every sample",
 "Source physical allocation <=available source all steps",
 "Pool first-law heat partition 1e-8MW tolerance",
 "District HP first-law heat partition 1e-8MW tolerance",
 "Source outage case no pool heat 48-72h",
 "No-pool case no delivered pool heat"],
 "not_tested_physically":[
 "calibration uncertainty of sensors","meter MPE","actual electrical PUE boundary",
 "physical compressor COP/PLR","flow preservation after pump failure",
 "third-party standard conformance and legal pool acceptance"]
 },indent=2,ensure_ascii=False),encoding="utf-8")
print("SIGNAL_CONTRACT_VALIDATED",len(definitions),"signals",len(cases)*105120,"timestamped samples")
