# -*- coding: utf-8 -*-
"""Economic and standard-boundary comparison from verified MATLAB output."""
import json
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/"simulink_closed_loop_summary_8760h.json").read_text(encoding="utf-8"))
a={r["name"]:r for r in rows}
nopool25=json.loads((ROOT/"simulink_nopool25_baseline_8760h.json").read_text(encoding="utf-8"))
cel=152.07260273972602; cgas=55.63479452054794; eta=0.9
def dh_e(r):return r["DH_HP_heat_MWh"]-r["DH_source_MWh"]
def delta(b,p):
 gasextra=p["gas_heat_MWh"]-b["gas_heat_MWh"]
 elecextra=dh_e(p)-dh_e(b)+p["pool_HP_electric_MWh"]
 source_reuse_change=(p["DH_source_MWh"]+p["pool_source_MWh"])-b["DH_source_MWh"]
 gas_pool_counterfactual=p["pool_heat_MWh"]/eta*cgas
 gas_opportunity=gasextra/eta*cgas
 hp_power_opportunity=elecextra*cel
 return {"extra_gas_MWh":gasextra,"extra_hp_electric_MWh":elecextra,
  "source_reuse_change_MWh":source_reuse_change,
  "pool_gas_counterfactual_opex_EUR":gas_pool_counterfactual,
  "incremental_gas_opex_EUR":gas_opportunity,
  "incremental_HP_electricity_opex_EUR":hp_power_opportunity,
  "net_energy_opex_benefit_EUR":gas_pool_counterfactual-gas_opportunity-hp_power_opportunity}
direct=delta(a["no_pool_35"],a["direct_35"])
hp=delta({"DH_HP_heat_MWh":nopool25["DH_HP_heat_MWh"],
 "DH_source_MWh":nopool25["DH_source_MWh"],
 "gas_heat_MWh":nopool25["gas_heat_MWh"]},a["heatpump_25"])
assert 0<direct["net_energy_opex_benefit_EUR"]<50000
assert -1e-6<hp["incremental_HP_electricity_opex_EUR"]<50000
allout={"scope":"extra pool connected to existing DH, versus independent gas-only heating of same pool heat",
 "weather":"NASA POWER 2025 hourly","electricity_EUR_MWh_2025_X_VAT":cel,
 "gas_EUR_MWh_2025_X_VAT":cgas,"boiler_efficiency_scenario":eta,
 "PUE":1.36,"direct35":direct,"hp25":hp,
 "DO_NOT_CLAIM":"This is modeled energy OPEX only, not net profit, payback or verified equipment performance"}
p=ROOT/"closed_loop_incremental_opex_2025.json"
if p.exists():raise FileExistsError(str(p))
p.write_text(json.dumps(allout,ensure_ascii=False,indent=2),encoding="utf-8")
print("CLOSED_LOOP_OPEX_QA",json.dumps({"direct_savings_EUR":round(direct["net_energy_opex_benefit_EUR"],2),
 "hp_savings_EUR":round(hp["net_energy_opex_benefit_EUR"],2),
 "extra_gas_direct_MWh":round(direct["extra_gas_MWh"],2),
 "extra_gas_hp_MWh":round(hp["extra_gas_MWh"],2)},ensure_ascii=False))
