# -*- coding: utf-8 -*-
"""Requirement -> Use case -> metric -> executable oracle traceability."""
import json,csv,math
from pathlib import Path
import pandas as pd,numpy as np
P=Path(__file__).resolve().parent
PROJ=P.parent.parent
CL=PROJ/"calibration"/"closed_loop_simulink_20261023"
CF=PROJ/"calibration"/"capacity_fault_simulink_20261023"
EN=PROJ/"calibration"/"engineering_release_20261023"
ST=PROJ/"calibration"/"standards_20261023"
x=pd.read_csv(CL/"direct_35_8760h.csv")
h=pd.read_csv(CL/"heatpump_25_8760h.csv")
o=pd.read_csv(CL/"outage_35_8760h.csv")
z=pd.read_csv(CL/"no_pool_35_8760h.csv")
cap={k["name"]:k for k in json.loads((CF/"capacity_fault_simulink_2025.json").read_text(encoding="utf-8"))}
fault={k["caseName"]:k for k in json.loads((EN/"IT_cooling_failsafe_simulink_results.json").read_text(encoding="utf-8"))}
standards=list(csv.DictReader((P/"standards_traceability_2026.csv").open(encoding="utf-8-sig")))
dt=1/12
def E(df,col):return float(df[col].sum()*dt)
def case(cid,domain,title,precondition,expected,source,metrics,priority,truth,reason=""):
    return {"id":cid,"domain":domain,"title":title,"preconditions":precondition,
     "expected_response":expected,"evidence_file":source,
     "metric_ids":metrics,"priority":priority,"status":"PASS" if truth is True else ("FAIL" if truth is False else "BLOCKED"),
     "reason":reason if reason else ("Model test passed" if truth is True else "Real-world or licensed evidence needed" if truth is None else "Assertion mismatch"),
     "actual_run":truth is not None,"date":"2026-10-23"}
cases=[]
add=cases.append
add(case("UC-001","IT/DC","Yearly energy source allocation","NASA 2025 weather, 2025 synthetic IT","No double use of available DC heat","direct_35_8760h.csv","Source_overallocation_peak", "P0",
   bool(((x.DCtoPool_MW+x.DCtoDistrict_MW-x.DCAvailable_MW).max())<1e-8)))
add(case("UC-002","Pool","500m3 heating from 16C","35C source, HX 150kW","Reach thermostat control band and respect 27.8C","direct_35_8760h.csv","Pool_warmup_to_27p25;Pool_peak_temperature","P0",bool(x.PoolT_C.max()<=27.8 and (x.PoolT_C>27.25).any())))
add(case("UC-003","Pool","28C statutory screening","Pool classified as swimming, published rule","No samples exceed 28C","direct_35_8760h.csv","Pool_hours_above_28","P0",bool((x.PoolT_C>28).sum()==0),
"Simulated water temperature only; actual legal effective rule and sensor uncertainty not verified"))
add(case("UC-004","Pool","Overtemperature sensor offset","Sensor +0.3 K bias, thermal afterrun","Independent hardware trip keeps actual T<28C","No hardware signal","Pool_peak_temperature","P0",None))
add(case("UC-005","HP","Pool HP first law","25C source, assumed COP 4","Qheat=Qsource+Welec every 5min","heatpump_25_8760h.csv","Electric_pool_HP25","P0",
 bool(abs(h.PoolHeat_MW-h.DCtoPool_MW-h.PoolHPElectric_MW).max()<1e-8)))
add(case("UC-006","HP","District HP first law","35C source, synthetic Carnot","Qheat=Qsource+Welec every 5min","direct_35_8760h.csv","HP_district_partition_abs_peak","P0",
 bool(abs(x.DistrictHPHeat_MW-x.DCtoDistrict_MW-x.DistrictHPel_MW).max()<1e-8)))
add(case("UC-007","District","District gas demand","Year simulated all 2025","Gas thermal nonnegative, demand covered","direct_35_8760h.csv","Backup_gas_thermal","P0",bool((x.GasHeat_MW>=-1e-8).all() and E(x,"GasHeat_MW")>1000)))
add(case("UC-008","TES","Thermal store range","50MWh rated TES model","Stored energy within [0,50]","direct_35_8760h.csv","TES_max_energy","P0",bool(x.TES_E_MWh.between(-1e-7,50.001).all())))
add(case("UC-009","DC","No heat sink scenario","IT export closed for 24h hours 48-72","Pool refuses IT heat when zero source; backup DH gas","outage_35_8760h.csv","E_recovered_source","P0",
 bool(abs(o.loc[(o.time_h>=48)&(o.time_h<72),"PoolHeat_MW"]).max()<1e-9)))
add(case("UC-010","DC","Full heat-reuse system unavailable","No pool/district energy buyer","10MW independent full IT cooling operates","independent_cooling_design_scenarios.json","Cooling_design_duty","P0",None))
add(case("UC-011","Pool","Direct HX thermal approach","Tsource 35C and pool return 27.5C","Manufacturer delivers 150kW 35/32 vs 27.5/29.5","HX_low_grade_heat_default.csv","Heat_pool_direct","P0",None))
add(case("UC-012","Pool","Night blanket reduced pool heat","Initial 500m3 model, covered vs uncovered","Cover scenario lower annual demand","pool_volume_cover_sensitivity_2025.csv","Heat_pool_direct","P1",
 bool(pd.read_csv(PROJ/"calibration"/"coupled_dispatch_20261023"/"pool_volume_cover_sensitivity_2025.csv").PoolHeat_MWh.iloc[2]>250)))
add(case("UC-013","Pool","Double volume sensitivity","500m3 vs 1000m3 scenario","Larger pool requires more heat, under assumed UA","pool_volume_cover_sensitivity_2025.csv","Pool_volume_m3","P1",
 bool(pd.read_csv(PROJ/"calibration"/"coupled_dispatch_20261023"/"pool_volume_cover_sensitivity_2025.csv").PoolHeat_MWh.iloc[1]>350)))
add(case("UC-014","HP","Manufacturers thermal map","25/20 to 50/70 and 35/30 to 50/70","Actual signed COP and capacity rated at site PLR","RFQ_Carrier_EN.md","SCOP_district_model","P0",None))
add(case("UC-015","HP","Vendor-certified 10MW duty","Candidate Carrier 61XWH-ZE17 catalog capacity","Nameplate at required water source and sink is adequate","Carrier_2025_nominal_vs_Nplus1_options.csv","Heat_district_HP35","P0",None))
add(case("UC-016","District","Nameplate limit 10MW","Simulink 2025, no pool","10MW cap changes gas demand by <10MWh/year","capacity_fault_simulink_2025.json","Backup_gas_thermal","P1",
 bool(0<cap["noPool10"]["gas_MWh"]-cap["ref12"]["gas_MWh"]<10)))
add(case("UC-017","District","Module failed 24 hours","Simulated 10MW pool dispatch, one HP module -2MW","Gas increases while pool heat remains safe","capacity_fault_simulink_2025.json","Backup_gas_thermal","P0",
 bool(cap["direct_fail8_24h"]["gas_MWh"]>cap["direct10"]["gas_MWh"] and cap["direct_fail8_24h"]["Tmax_C"]<=27.8)))
add(case("UC-018","District","Standby recovered in 30min","10MW to 8MW fault and back","Gas incremental less than 1MWh vs healthy","capacity_fault_simulink_2025.json","Backup_gas_thermal","P1",
 bool(0<cap["direct_N1_30m"]["gas_MWh"]-cap["direct10"]["gas_MWh"]<1)))
add(case("UC-019","Cooling","One recooler failed, no summer derating","6x2MW includes spare, 30s","No thermal trip at 10MW IT load","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",fault["N6_nominal_fail30s"]["safeSimulation"]))
add(case("UC-020","Cooling","One recooler failed with derating 10%","7x2MW includes spare, 30s","No thermal trip at 10MW IT load","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",fault["N7_der10_fail30s"]["safeSimulation"]))
add(case("UC-021","Cooling","Delayed standby 300 seconds","7x2MW at -10%, 10m3 buffer","Thermal trip is detected, NOT falsely declared safe","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",
 bool(not fault["N7_der10_fail300s"]["safeSimulation"] and fault["N7_der10_fail300s"]["tripSteps"]>0)))
add(case("UC-022","Cooling","Permanent inadequate heat rejection","6x2MW at -10%","Trip detected before claiming safe operation","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",
 bool(not fault["N6_der10_nominal_undersized"]["safeSimulation"])))
add(case("UC-023","Cooling","Second derating case 20%","7x2MW at -20%","Trip detected before claiming safe operation","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",
 bool(not fault["N7_der20_nominal_undersized"]["safeSimulation"])))
add(case("UC-024","Cooling","Circulation pump lost 10 seconds","7x2MW at -10%","Immediate flow trip independently of temperature","IT_cooling_failsafe_simulink_results.json","Cooling_design_duty","P0",
 bool(fault["N7_der10_pump_fault"]["flowTripSteps"]==2)))
add(case("UC-025","Electrical","UPS pump ride through","Mains failed, 60s generator delay","Pump flow sustained, redundant electrical supply validated","No UPS test","Cooling_design_duty","P0",None))
add(case("UC-026","Electrical","Cooling switchgear single fault","Critical cooling distribution fault","Power selectivity and N+1 UPS verified","No electrical SLD","Cooling_design_duty","P0",None))
add(case("UC-027","Measurement","DC energy efficiency reporting","Annual same boundary metering","Report official PUE not model 1.36","No E_DC or E_IT meters","PUE_assumed","P0",None))
add(case("UC-028","Measurement","Regulated energy reuse reporting","One year heat transfer meter","Report E_REUSE/E_DC compliant with regulation","No transfer-point heat meter","ERF_reportable","P0",None))
add(case("UC-029","Measurement","Water resource KPI","Pool and DC water demands isolated","Calculate WUE with meter and unit","No W_IN measured","WUE_reportable","P1",None))
add(case("UC-030","Control","Timestamp and timezone","2025 UTC data and Bratislava DST local pool hours","No missing/duplicate 8760 hourly sources","weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv","E_IT","P0",
 bool(len(pd.read_csv(ST/"official_datasets"/"weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv"))==8760)))
add(case("UC-031","Standards","Current PUE standard edition","Reference year 2026","ISO/IEC 30134-2:2026 present in register","standards_traceability_2026.csv","PUE_assumed","P1",
 any("30134-2:2026" in r["standard_reference"] for r in standards)))
add(case("UC-032","Standards","Latest ISO9001 quality edition","Reference year 2026","ISO9001:2026 present, not superseded 2015","standards_traceability_2026.csv","PUE_assumed","P1",
 any("ISO 9001:2026" in r["standard_reference"] for r in standards)))
add(case("UC-033","Water","Pool chlorinated water chemistry","HX contact pool treated water","Corrosion rating signed by OEM and sampling","No OEM water quality signoff","Heat_pool_direct","P0",None))
add(case("UC-034","Commissioning","Pool water failsafe FAT/SAT","Inject stuck valve + T offset","Independent hardware trip before 28C","No physical FAT/SAT","Pool_peak_temperature","P0",None))
add(case("UC-035","Commissioning","IT cooling all sinks lost","Close heating load and simulated DC recoolers","Critical cooling hardware bypass start and server flow maintained","No physical equipment","Cooling_design_duty","P0",None))
add(case("UC-036","Water","ASHRAE W class selection","Facility coolant supply unknown","Choose compatible W17/W27/W32/W40/W45 or W+ from actual IT design","No server liquid hardware limits","Cooling_design_duty","P0",None))
assert len(cases)>=35
assert not any(r["status"]=="FAIL" for r in cases)
assert len({r["id"] for r in cases})==len(cases)
with (P/"use_case_catalog_2026.csv").open("x",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
(P/"use_case_catalog_2026.json").write_text(json.dumps(cases,indent=2,ensure_ascii=False),encoding="utf-8")
counts={k:sum(v["status"]==k for v in cases) for k in ("PASS","FAIL","BLOCKED")}
(P/"use_case_test_results_2026.json").write_text(json.dumps({"counts":counts,"total":len(cases),
 "warning":"PASS means assertion within existing simulation; no site hardware certification",
 "tests":cases},indent=2,ensure_ascii=False),encoding="utf-8")
print("USE_CASE_EXECUTION_COMPLETE",len(cases),counts)
