"""Paper-to-model cross-check with explicit energy boundaries; no model modifications."""
from pathlib import Path
import csv,json
root=Path(__file__).resolve().parents[1]
summary=list(csv.DictReader((root/"results"/"frankfurt_validation_v4.csv").open()))[0]
paper={
"consumer_demand_MWh":144000.0,
"heat_input_MWh":152000.0,
"network_losses_fraction_of_input":0.052,
"HP_annual_heat_MWh":148000.0,
"gas_annual_heat_MWh":4000.0,
"storage_MWh":82.0,
"boiler_rated_MW":20.0,
"HP_rated_MW":37.0,
"HP_COP_min_claim":3.76,
"HP_COP_max_claim":3.90,
"source_in_C":25.0,"source_return_C":15.0,
"network_supply_range_C":[70.0,80.0],"network_return_C":50.0
}
model={
"claimed_demand_or_generation_MWh":float(summary["Demand_MWh"]),
"HP_annual_heat_MWh":float(summary["HP_Heat_MWh"]),
"gas_annual_heat_MWh":float(summary["Gas_Heat_MWh"]),
"storage_MWh":float(summary["Storage_MWh"]),
"mean_COP":float(summary["Mean_COP"]),
"recovery_fraction":float(summary["Calibrated_RecoveryFraction"])
}
derived={
"expected_input_from_144_and_5point2pct_MWh":144000.0/(1-0.052),
"paper_approx_HP_plus_gas_MWh":148000.0+4000.0,
"paper_HP_fraction_from_rounded_energy":148.0/152.0,
"paper_gas_full_load_hours_estimated":4000.0/20.0,
"paper_HP_full_load_hours_estimated":148000.0/37.0,
"paper_144_from_192x75percent_MWh":192000.0*.75,
"water_storage_implied_delta_T_K":82.0*3.6e9/(2400.0*1000*4186),
"baseline_vs_paper_HP_heat_error_MWh":model["HP_annual_heat_MWh"]-148000,
"baseline_vs_paper_gas_error_MWh":model["gas_annual_heat_MWh"]-4000,
"baseline_vs_paper_network_input_error_MWh":model["claimed_demand_or_generation_MWh"]-152000
}
tests={
"paper_144_is_75pct_of_192":abs(derived["paper_144_from_192x75percent_MWh"]-paper["consumer_demand_MWh"])<1e-7,
"losses_generate_about_152":abs(derived["expected_input_from_144_and_5point2pct_MWh"]-152000)<200,
"paper_HP_plus_gas_about_152":abs(derived["paper_approx_HP_plus_gas_MWh"]-152000)<1,
"model_reproduces_152_heat_generated":abs(model["claimed_demand_or_generation_MWh"]-152000)<1000,
"model_reproduces_148_HP_heat":abs(model["HP_annual_heat_MWh"]-148000)<1000,
"model_reproduces_4_gas_heat":abs(model["gas_annual_heat_MWh"]-4000)<100,
"model_reproduces_82_storage":abs(model["storage_MWh"]-82)<1,
"model_COP_inside_paper_nominal_range":3.76<=model["mean_COP"]<=3.9
}
out={"paper":paper,"baseline":model,"derived":derived,"checks":tests,
     "qualification":"Source Table 3 values rounded. COP min 3.76 conflicts with a subsequent 3.67 typo: requires visual verification."}
p=Path(__file__).with_name("paper_model_gap_v05.json")
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for name,res in tests.items():print(("PASS" if res else "FAIL")+" "+name)
print("AUDIT_OUTPUT",p)
