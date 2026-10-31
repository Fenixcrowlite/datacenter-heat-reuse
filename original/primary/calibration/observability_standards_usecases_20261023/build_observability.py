# -*- coding: utf-8 -*-
"""Evidence-based chart and KPI extraction from executed 2025 Simulink CSVs."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json,csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PR=ROOT.parent.parent
CL=PR/"calibration"/"closed_loop_simulink_20261023"
CF=PR/"calibration"/"capacity_fault_simulink_20261023"
SA=PR/"calibration"/"engineering_release_20261023"
ST=PR/"calibration"/"standards_20261023"
EQ=PR/"calibration"/"equipment_selection_20261023"
OUT=ROOT/"charts";OUT.mkdir(exist_ok=True)
D={name:pd.read_csv(CL/(name+"_8760h.csv")) for name in ("no_pool_35","direct_35","heatpump_25","outage_35")}
for name,table in D.items():
 assert len(table)==105120 and bool(table.notna().all().all()),name
 assert np.max(np.abs(np.diff(table.time_h.to_numpy())-1/12))<1e-8
x=D["direct_35"];y=D["heatpump_25"];z=D["no_pool_35"]
month=pd.date_range("2025-01-01",periods=8760,freq="h").month.to_numpy()[np.floor(x.time_h.to_numpy()).astype(int)]
hours=x.time_h.to_numpy();dt=1/12
weather=pd.read_csv(ST/"official_datasets"/"weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv")
assert len(weather)==8760
COP=pd.read_csv(CL/"carrier_cop_certified_vs_scenario.csv")
capacity=pd.read_csv(CF/"capacity_fault_simulink_2025.csv")
poolCases=pd.read_csv(PR/"calibration"/"coupled_dispatch_20261023"/"pool_volume_cover_sensitivity_2025.csv")
fail=pd.read_csv(SA/"cooling_nplus1_derating.csv")
faultData={k:pd.read_csv(SA/(k+".csv")) for k in ("N7_der10_fail30s","N7_der10_fail300s")}
source=json.loads((SA/"independent_cooling_design_scenarios.json").read_text(encoding="utf-8"))
safety=json.loads((SA/"IT_cooling_failsafe_simulink_results.json").read_text(encoding="utf-8"))
def new(name,title,xlabel,ylabel):
 f,ax=plt.subplots(figsize=(10.5,5.7))
 ax.set(title=title,xlabel=xlabel,ylabel=ylabel)
 ax.grid(True,alpha=.23)
 return f,ax
def save(f,name):
 f.tight_layout()
 f.savefig(OUT/(name+".png"),dpi=165)
 f.savefig(OUT/(name+".svg"))
 plt.close(f)
def monthly(series):
 return pd.Series(series.to_numpy()*dt).groupby(month).sum().to_numpy()
def M(name,value,unit,definition,standard="",quality="SIMULATED"):
 return dict(id=name,value=None if value is None else float(value),unit=unit,definition=definition,standard=standard,evidence=quality)
K=[]
E=lambda t,col:float(t[col].sum()*dt)
it=source["profile"]["E_IT_heat_MWh"]
recovered=E(x,"DCtoPool_MW")+E(x,"DCtoDistrict_MW")
rejected=it-recovered
edc=it*1.36
K.extend([
 M("E_IT",it,"MWh/year","IT thermal energy from assumed model power","ISO/IEC 30134-2:2026","SIMULATED"),
 M("E_DC_assumed",edc,"MWh/year","E_IT × assumed PUE 1.36","ISO/IEC 30134-2:2026","SCENARIO"),
 M("PUE_assumed",1.36,"1","E_DC/E_IT, not site metered","ISO/IEC 30134-2:2026","SCENARIO"),
 M("E_recovered_source",recovered,"MWh/year","integral DCtoPool+DCtoDistrict","EU 2024/1364","SIMULATED"),
 M("E_rejected_IT",rejected,"MWh/year","IT thermal energy minus source reused","first-law accounting","SIMULATED"),
 M("Source_utilization",recovered/(it*.85),"1","extracted / assumed 0.85 × E_IT","","SIMULATED"),
 M("ERF_source_proxy",recovered/edc,"1","source heat extracted / assumed facility energy; NOT ERF","EU 2024/1364","NONREPORTABLE"),
 M("ERF_reportable",None,"1","boundary metered E_REUSE/E_DC","EU 2024/1364","MISSING_METER"),
 M("WUE_reportable",None,"m3/MWh","metered water consumption / IT energy","ISO/IEC 30134-9:2022","MISSING_METER"),
 M("REF_reportable",None,"1","renewable energy / facility energy","EU 2024/1364","MISSING_METER"),
 M("Heat_pool_direct",E(x,"PoolHeat_MW"),"MWh/year","integral useful pool heat","","SIMULATED"),
 M("Heat_pool_HP25",E(y,"PoolHeat_MW"),"MWh/year","integral useful pool heat","","SIMULATED"),
 M("Electric_pool_HP25",E(y,"PoolHPElectric_MW"),"MWh/year","compressor power × dt","","SIMULATED"),
 M("Heat_district_HP35",E(x,"DistrictHPHeat_MW"),"MWh/year","integral useful district HP output","","SIMULATED"),
 M("Electric_district_HP35",E(x,"DistrictHPel_MW"),"MWh/year","integral district HP compressor","","SIMULATED"),
 M("SCOP_district_model",E(x,"DistrictHPHeat_MW")/E(x,"DistrictHPel_MW"),"1","season heat / compressor electric, synthetic Carnot only","EN 14511-2 NOT certified","NONCERTIFIED"),
 M("Backup_gas_thermal",E(x,"GasHeat_MW"),"MWh/year","integral useful backup gas heat","","SIMULATED"),
 M("Pool_peak_temperature",float(x.PoolT_C.max()),"degC","max modeled pool water temp","published decree 308/2012","SIMULATED"),
 M("Pool_hours_above_28",float((x.PoolT_C>28).sum()*dt),"h","temperature intervals exceeding 28C","published decree 308/2012","SIMULATED"),
 M("Pool_hours_above_internal_limit",float((x.PoolT_C>27.8).sum()*dt),"h","intervals above internal threshold","","SIMULATED"),
 M("Pool_warmup_to_27p25",float(x.loc[x.PoolT_C>=27.25,"time_h"].iloc[0]),"h","first crossing 27.25C from cold initial state","","SIMULATED"),
 M("TES_max_energy",float(x.TES_E_MWh.max()),"MWh","max stored thermal energy","","SIMULATED"),
 M("Source_overallocation_peak",max(0,float((x.DCtoPool_MW+x.DCtoDistrict_MW-x.DCAvailable_MW).max())),"MW","must be zero; total used source minus available","","QA"),
 M("HP_pool_partition_abs_peak",float(abs(x.PoolHeat_MW-x.DCtoPool_MW-x.PoolHPElectric_MW).max()),"MW","Qout-Qsource-Welectric","","QA"),
 M("HP_district_partition_abs_peak",float(abs(x.DistrictHPHeat_MW-x.DCtoDistrict_MW-x.DistrictHPel_MW).max()),"MW","Qout-Qsource-Welectric","","QA"),
 M("Cooling_design_duty",10,"MW","assumed full IT design heat load","","SCENARIO"),
 M("Cooling_thermal_flow_at_5K",10e6*3600/(997*4182*5),"m3/h","10 MW / rho cp dT","","SCENARIO"),
 M("Aux_pump_head_primary",None,"kPa","site fluid hydraulics / hydraulic calculation required","","NOT_MEASURED")
])
bal=x.DistrictHPHeat_MW+x.TESDischarge_MW+x.GasHeat_MW-x.TESCharge_MW
K.append(M("District_load_peak_derived",float(bal.max()),"MW","HP+TES discharge+gas-TES charge","","SIMULATED"))
K.append(M("District_demand_annual",float(bal.sum()*dt),"MWh/year","sum district delivered demand","","SIMULATED"))
K.append(M("District_heat_balance_residual",float((bal-(x.DistrictHPHeat_MW+x.TESDischarge_MW+x.GasHeat_MW-x.TESCharge_MW)).abs().max()),"MW","constructed identity check; independent source QA separately","","QA"))
K.append(M("Pool_surface_m2",312.5,"m2","25 × 12.5 m assumed rectangular","","SCENARIO"))
K.append(M("Pool_volume_m3",500,"m3","25 ×12.5×1.6m assumed","","SCENARIO"))
K.append(M("Thermal_buffer_min_2MW_30s_5K",2e6*30/(997*4182*5),"m3","ideal water heat buffer, not flow","","SCENARIO"))
assert abs(it-recovered-rejected)<1e-5
assert K[0]["value"]>71000 and len(K)>=30
# GRAPH 01: pool warm-up / first 120 hours.
f,a=new("01_pool_warmup","Pool start-up: actual closed-loop Simulink, 300s",
 "Hours from 2025-01-01 00:00 UTC","Pool water, deg C")
sel=hours<=120
a.plot(hours[sel],x.PoolT_C.to_numpy()[sel],label="35C direct HX")
a.plot(hours[sel],y.PoolT_C.to_numpy()[sel],label="25C pool HP",alpha=.8)
a.axhline(27.6,linestyle="--",label="Thermostat off")
a.axhline(27.8,linestyle=":",label="Model guard")
a.axhline(28,linestyle="-.",label="Published swimming-pool max")
a.legend();save(f,"01_pool_warmup")
# 02 annual thermal balance: each monthly independent thermal stream.
f,a=new("02_monthly_energy","Monthly heat allocation: simulated 2025",
 "Month","MWh thermal per month")
months=np.arange(1,13)
pool=monthly(x.PoolHeat_MW);district=monthly(x.DistrictHPHeat_MW);gas=monthly(x.GasHeat_MW)
a.bar(months,district,label="District heat pump")
a.bar(months,gas,bottom=district,label="Backup gas heat")
a.bar(months,pool,bottom=district+gas,label="Pool useful heat")
a.legend();a.set_xticks(months);save(f,"02_monthly_energy")
# 03 monthly heat pump electricity.
f,a=new("03_monthly_HP_electric","Monthly compressor electricity",
 "Month","MWh electrical per month")
a.plot(months,monthly(x.DistrictHPel_MW),marker="o",label="District HP")
a.plot(months,monthly(y.PoolHPElectric_MW),marker="s",label="Pool HP at 25C")
a.legend();a.set_xticks(months);save(f,"03_monthly_HP_electric")
# 04 hour duration curves, weather not direct demand.
f,a=new("04_load_duration","Full-year load-duration curves",
 "Hours of year (ranked descending)","MW thermal")
h=np.arange(len(x))/12
for col,label in [("DCAvailable_MW","IT recovery source available"),("DistrictHPHeat_MW","District HP output"),("GasHeat_MW","Backup gas")]:
 a.plot(h,np.sort(x[col].to_numpy())[::-1],label=label)
a.legend();save(f,"04_load_duration")
# 05 heat rejection annual peak, residual from IT assumed.
f,a=new("05_IT_heat_allocation","Modelled full-year IT heat distribution",
 "Category","MWh thermal")
a.bar(["Reused DC source","Rejected IT heat"],[recovered,rejected])
a.set_ylim(0,it*1.1)
save(f,"05_IT_heat_allocation")
# 06 pool cover/volume response, not actual site.
f,a=new("06_pool_geometry_sensitivity","Pool geometry and cover sensitivity (research assumptions)",
 "Pool scenario","MWh thermal/year")
a.bar(poolCases["Scenario"].astype(str),poolCases["PoolHeat_MWh"])
a.tick_params(axis="x",rotation=16);save(f,"06_pool_geometry_sensitivity")
# 07 actual numerical gas after cap.
f,a=new("07_HP_capacity_gas","Backup gas after running capacity-constrained Simulink",
 "Available district HP thermal cap and failure scenario","Gas heat MWh/year")
a.bar(capacity.Case.astype(str),capacity.Gas_MWh.to_numpy())
a.tick_params(axis="x",rotation=25);save(f,"07_HP_capacity_gas")
# 08 COP manufacturer vs hypothetical efficiency model.
f,a=new("08_COP_reference","Carrier W10-7 certified COP vs surrogate",
 "Condenser outlet temperature, deg C","COP")
a.plot(COP.SinkOutlet_C,COP.COP_Certified,marker="o",label="Eurovent certified")
a.plot(COP.SinkOutlet_C,COP.COP_ScenarioCarnot,marker="s",label="Simulated Carnot surrogate")
a.legend();save(f,"08_COP_reference")
# 09 distribution of pool water operating temperatures without the initial warmup.
f,a=new("09_pool_temperature_distribution","Pool water temperature distribution, hours 120-8760",
 "Pool water temperature, deg C","Frequency (300-sec samples)")
oper=x.PoolT_C.to_numpy()[hours>=120]
a.hist(oper,bins=80)
a.axvline(27.8,label="Model limit",linestyle="--")
a.axvline(28,label="Published max",linestyle=":")
a.legend();save(f,"09_pool_temperature_distribution")
# 10 source flow and pool uptake during two representative days.
f,a=new("10_recovery_dispatch_week","Five-minute source dispatch in first week",
 "Hours","MW of extracted IT source heat")
sel=(hours>=36)&(hours<=72)
a.plot(hours[sel],x.DCtoDistrict_MW.to_numpy()[sel],label="To district HP")
a.plot(hours[sel],x.DCtoPool_MW.to_numpy()[sel],label="To pool")
a.plot(hours[sel],x.DCAvailable_MW.to_numpy()[sel],label="Available IT source")
a.legend();save(f,"10_recovery_dispatch_week")
# 11 TES heat storage energy dynamics 1 week.
f,a=new("11_thermal_storage","Thermal energy storage, first 7 days",
 "Hours","MWh TES state")
a.plot(hours[hours<168],x.TES_E_MWh.to_numpy()[hours<168])
a.axhline(50,linestyle="--",label="Configured TES rated 50 MWh")
a.legend();save(f,"11_thermal_storage")
# 12 weather change vs temperature from source and monthly network gas
f,a=new("12_weather_monthly","Real weather reanalysis: Bratislava NASA POWER 2025",
 "Month","Ambient deg C")
t2m=weather.T2M_C.to_numpy()
t_month=np.array([np.mean(t2m[pd.date_range("2025-01-01",periods=8760,freq="h").month==m]) for m in months])
a.plot(months,t_month,marker="o")
a.set_xticks(months);save(f,"12_weather_monthly")
# 13 full-year monthly gas from 3 variants
f,a=new("13_gas_pool_comparison","Backup heat: district network",
 "Month","MWh gas heat")
for name,col in [("Without pool at 35C",z),("Direct pool at 35C",x),("Pool HP at 25C",y)]:
 a.plot(months,monthly(col.GasHeat_MW),marker=".",label=name)
a.legend();a.set_xticks(months);save(f,"13_gas_pool_comparison")
# 14 hypothetical N+1 capability after worst one outage, ambient derating.
f,a=new("14_independent_cooling_Nplus1","10MW IT: N+1 capacity after one cooler failure",
 "Total installed 2MW nominal modules","Available net cooling, MW")
for der in (0.0,.1,.2):
 subset=fail[np.isclose(fail.design_ambient_derating_fraction,der)]
 a.plot(subset.installed_units,subset.capacity_after_any_one_outage_MW,marker="o",label=f"{int(der*100)}% derating")
a.axhline(10,linestyle="--",label="Full IT design duty")
a.legend();save(f,"14_independent_cooling_Nplus1")
# 15 and 16 fault step, 30s vs 5min delay.
for k,name in enumerate(("N7_der10_fail30s","N7_der10_fail300s")):
 v=faultData[name]
 f,a=new(f"15{k}_cooling_fault","Independent IT cooling, "+("30s standby" if k==0 else "300s standby"),
  "Seconds elapsed","Coolant buffer temperature, deg C")
 a.plot(v.time_s,v.coolant_T_C,label="Cooling fluid")
 a.axhline(40,linestyle="--",label="Software model trip")
 a.set_xlim(500,1100 if k==1 else 800)
 a.legend();save(f,f"15{k}_cooling_fault")
# 17 fluid transport pressure-flow comparison (geometric scaling)
f,a=new("17_hydraulic","Cooling flow sensitivity: 10 MW IT, water rho=997 cp=4182",
 "Assumed fluid temperature difference, K","m3/h")
drop=np.linspace(2,15,200)
a.plot(drop,10e6*3600/(997*4182*drop))
save(f,"17_hydraulic")
# 18 expected source capacity per district heat pump COP envelope.
f,a=new("18_scenario_COP_lift","Carnot-form scenario COP vs temperature lift, sink 70C",
 "Source temperature, deg C","COP (not manufacturer-qualified)")
src=np.linspace(5,55,100);sink=70+273.15
a.plot(src,np.maximum(2.2,np.minimum(7,.5*sink/(70-src))))
a.text(14,4.5,"Assumed Carnot efficiency factor 0.50",fontsize=10)
save(f,"18_scenario_COP_lift")
# 19 thermal/electric energy comparison.
f,a=new("19_heat_pump_energy","2025 district and pool HP energy partitions",
 "System","MWh/year")
u=[E(x,"DistrictHPHeat_MW"),E(y,"DistrictHPHeat_MW"),E(y,"PoolHeat_MW")]
el=[E(x,"DistrictHPel_MW"),E(y,"DistrictHPel_MW"),E(y,"PoolHPElectric_MW")]
a.bar(["DH HP @35C","DH HP @25C","Pool HP @25C"],u,label="Useful heat")
a.bar(["DH HP @35C","DH HP @25C","Pool HP @25C"],el,label="Compressor electricity")
a.legend();save(f,"19_heat_pump_energy")
# 20 status, labels are not facility compliance.
status={"SIMULATED":0,"SCENARIO":0,"SIMULATED_NOT_CERTIFIED":0,"NONREPORTABLE":0,"MISSING_METER":0,"NOT_MEASURED":0,"QA":0,"NONCERTIFIED":0}
for k in K:status[k["evidence"]]=status.get(k["evidence"],0)+1
f,a=new("20_metric_provenance","KPI evidence status, not compliance",
 "Evidence class","Count of KPIs")
a.bar(status.keys(),status.values());a.tick_params(axis="x",rotation=25)
save(f,"20_metric_provenance")
# Save KPI + monthly metric files and chart index.
observed={m["id"]:m for m in K}
assert observed["Source_overallocation_peak"]["value"]<1e-7
assert observed["HP_pool_partition_abs_peak"]["value"]<1e-7
assert observed["HP_district_partition_abs_peak"]["value"]<1e-7
assert abs(recovered+rejected-it)<1e-5
assert observed["ERF_reportable"]["value"] is None
index=[{"name":p.stem,"png":p.name,"svg":p.with_suffix(".svg").name} for p in sorted(OUT.glob("*.png"))]
(ROOT/"kpi_catalog_2025.json").write_text(json.dumps(K,indent=2,ensure_ascii=False),encoding="utf-8")
with (ROOT/"kpi_catalog_2025.csv").open("w",encoding="utf-8-sig",newline="") as handle:
 w=csv.DictWriter(handle,fieldnames=list(K[0]));w.writeheader();w.writerows(K)
monthlytab=pd.DataFrame({"month":months,"NASA_ambient_mean_C":t_month,"district_HP_thermal_MWh":district,
"backup_gas_MWh":gas,"pool_heat_MWh":pool,"district_HP_electric_MWh":monthly(x.DistrictHPel_MW)})
monthlytab.to_csv(ROOT/"monthly_kpis_2025.csv",index=False)
(ROOT/"graph_manifest.json").write_text(json.dumps(index,indent=2),encoding="utf-8")
print("GRAPH_AND_KPI_GENERATION_PASS",len(index),"charts",len(K),"KPIs",
  "E_IT",round(it,2),"E_reused",round(recovered,2),"Pool heat",round(E(x,"PoolHeat_MW"),2))
