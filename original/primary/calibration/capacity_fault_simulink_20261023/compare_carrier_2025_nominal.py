# -*- coding: utf-8 -*-
from pathlib import Path
import json,csv,math
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/"capacity_fault_simulink_2025.json").read_text(encoding="utf-8"))
s={r["name"]:r for r in data}
ratings=[("3",300),("5",484),("7",727),("10",967),("14",1453),("15",1468),("17",1570)]
peak_MW=10.372
rows=[]
for model,rating in ratings:
 for goal in (10.0,peak_MW):
  duty=math.ceil(1000*goal/rating)
  rows.append({"Carrier_61XWH_ZE_model":model,
   "nominal_kW_at_W20_15_W70_75":rating,
   "required_useful_MW":goal,
   "duty_units_min":duty,"spare_units_Nplus1":1,
   "total_units":duty+1,
   "installed_nominal_MW":round((duty+1)*rating/1000,3),
   "interpretation":"Published 2025 EN14511 nominal at W20/15 source and W70/75 sink, NOT at actual site operating temperatures"})
outfile=HERE/"Carrier_2025_nominal_vs_Nplus1_options.csv"
if outfile.exists():raise FileExistsError(str(outfile))
with outfile.open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]))
 w.writeheader();w.writerows(rows)
six=s["carrier9p42"];seven=s["carrier10p99"]
extra_gas=six["gas_MWh"]-seven["gas_MWh"]
extra_elec=seven["HPel_MWh"]-six["HPel_MWh"]
p_gas=55.6347945205;p_elec=152.0726027397;eta=.9
savings=extra_gas/eta*p_gas-extra_elec*p_elec
pv_factor=(1-(1+.06)**-20)/.06
capex_ceiling=savings/(.02+1/pv_factor)
out={
"evidence":"Carrier 2025 manufacturer product PDF, nominal EN14511, W20/15 evaporator and W70/75 condenser, not actual site",
"pdf_url":"https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf",
"models":rows,"model17_6_duty_plus_1_spare_nominal_MW":6*1.57,
"model17_7_duty_plus_1_spare_nominal_MW":7*1.57,
"simulink_2025_6_duty_gas_MWh":six["gas_MWh"],
"simulink_2025_7_duty_gas_MWh":seven["gas_MWh"],
"incremental_gas_saved_MWh":extra_gas,
"incremental_hp_electricity_MWh":extra_elec,
"incremental_energy_cost_benefit_EUR_per_year":savings,
"extra_module_CAPEX_NPV_zero_limit_EUR":capex_ceiling,
"additional_annual_fixed_maintenance_rate_assumed":.02,
"discount":.06,"duration_year":20,
"liabilities":["Actual Carrier duty point 35C source/70C sink must be calculated by manufacturer",
"6x model17 or 7x model17 not a vendor-validated equipment bank",
"Investments assume zero parasitic changes between 6 and 7 duty units",
"Simulink dispatch COP is theoretical and unchanged by module sizing",
"Carrier 2025 max rated heating capacity 1570kW, not confirmed 2000kW"],
"updated":"2026-10-23"}
(HERE/"Carrier_2025_rated_vs_simulated_economics.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("CARRIER_2025_N1_COMPARISON",json.dumps({"gas_saved_MWh":round(extra_gas,3),
"HP_electricity_added_MWh":round(extra_elec,3),"net_energy_value_EUR_y":round(savings,2),
"NPV0_CAPEX_additional_unit_EUR":round(capex_ceiling,2),
"max_Carrier_model17_kW":1570},ensure_ascii=False))
