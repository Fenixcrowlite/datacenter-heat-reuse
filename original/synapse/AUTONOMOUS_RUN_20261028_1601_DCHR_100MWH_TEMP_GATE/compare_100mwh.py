"""Physical temperature-gate reinterpretation of existing 100 MWh storage rating.
Isolated SYNTHETIC counterfactual, not actual Simulink parity or savings.
"""
from __future__ import annotations
import hashlib,importlib.util,json,math
from dataclasses import replace
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent.parent
PARENT=H.parent/"AUTONOMOUS_RUN_20261028_1451_DCHR_STRATIFIED_TANK_GATE"
MODEL=PARENT/"stratified_tank.py"
MODEL_SHA="e6a551b359823046c0623b1089920b20be4d5ffc915dade9694dff99b378e582"
TARGET_MWH=100.0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_model():
    if sha(MODEL)!=MODEL_SHA:raise ValueError("stratified model changed")
    spec=importlib.util.spec_from_file_location("dchr_stratified_c33",MODEL)
    module=importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module
def volume(target_mwh,hot_c,cold_c,cp=4180.0,rho=1000.0):
    if not all(math.isfinite(x) for x in (target_mwh,hot_c,cold_c,cp,rho)):raise ValueError("nonfinite")
    if target_mwh<=0 or hot_c<=cold_c or cp<=0 or rho<=0:raise ValueError("invalid capacity")
    return target_mwh*3.6e9/(rho*cp*(hot_c-cold_c))
def main():
    m=load_model()
    rows,source_sha=m.load()
    supply_peak=max(r["DH_Supply_C"] for r in rows)
    assert len(rows)==8760 and supply_peak<69
    cases=[]
    for hot in (72.0,80.0):
        cold_nominal=35.0
        cold_gate=supply_peak+3.0
        for mode,cold in (("NOMINAL_RETURN_35C",cold_nominal),("SUPPLY_GATE_MAX_PLUS_3K",cold_gate)):
            v=volume(TARGET_MWH,hot,cold)
            ua=m.geometry_ua_kw_per_k(v)
            c=m.Config(volume_m3=v,charge_temp_c=hot,ua_kw_per_k=ua)
            s=m.simulate(rows,c,years=3)
            last=s["yearly"][-1]
            assert abs(last["balance_residual_mwh"])<1e-5
            cases.append({
              "hot_c":hot,"capacity_definition":mode,"reference_cold_c":cold,
              "target_thermal_capacity_mwh":TARGET_MWH,"volume_m3":v,
              "ua_kw_per_k":ua,"year3_delivered_mwh":last["delivered_mwh"],
              "year3_added_electric_mwh":last["added_electric_mwh"],
              "year3_charge_mwh":last["charge_mwh"],
              "year3_loss_mwh":last["loss_mwh"],
              "year3_balance_residual_mwh":last["balance_residual_mwh"],
              "year3_temperature_blocked_hours":last["temperature_blocked_hours"],
              "year3_top_c":last["top_c"],"year3_bottom_c":last["bottom_c"]
            })
    assert cases[1]["volume_m3"]>cases[0]["volume_m3"]
    assert cases[3]["volume_m3"]>cases[2]["volume_m3"]
    result={
      "scope":"DCHR_C33_100MWH_TEMPERATURE_GATE_EQUIVALENCE",
      "source_data_sha256":source_sha,"source_model_sha256":MODEL_SHA,
      "source_rows":len(rows),"max_synthetic_dh_supply_c":supply_peak,
      "heat_exchanger_approach_k":3.0,"target_mwh":TARGET_MWH,
      "cases":cases,"baseline_simulink_storage_mwh":100.0,
      "synthetic_not_metered":True,"simulink_baseline_compared_dynamically":False,
      "incremental_gas_savings_verified":False,"physical_validation":False,
      "primary_source_signoffs":0,
      "notes":[
        "Capacity is energy above chosen reference temperature, NOT a guaranteed extractable MWh under dynamic stratification.",
        "35C nominal return is NOT equivalent to supply-temperature usable capacity.",
        "Conservative gate reference uses maximum synthetic DH supply plus 3K HX approach.",
        "All four configurations use the existing C31 isolated 8-layer synthetic model and its assumptions.",
        "Baseline Simulink 100 MWh is already embedded in the synthetic dispatch; no additional savings claim.",
        "No MATLAB run, no OEM heat pump COP map, no metered validation or primary-source signoffs."
      ]
    }
    (H/"C33_100MWH_GATE_RESULTS.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"source_rows":len(rows),"supply_peak_c":round(supply_peak,4),
        "cases":[{"hot_c":x["hot_c"],"mode":x["capacity_definition"],"volume_m3":round(x["volume_m3"],2),
                  "delivered_year3_mwh":round(x["year3_delivered_mwh"],2),
                  "electric_year3_mwh":round(x["year3_added_electric_mwh"],2)} for x in cases]},ensure_ascii=False))
if __name__=="__main__":main()
