"""Static contract, first-law, and isolation checks for *unexecuted* DH Simulink v02 builder.

Not a substitute for loading/running the new SLX in MATLAB.
"""
from __future__ import annotations
import hashlib, json, math, pathlib, re, sys
HERE=pathlib.Path(__file__).resolve().parent
LIVE=HERE.parent
SCADA=LIVE.parent
PROJ=SCADA.parent
sys.path.insert(0,str(LIVE))
from dh_dynamic_pilot import step, calculate, DesignAssumptions

SRC=PROJ/"matlab"/"pool_feedback_v04"/"DC_Bazen_Uzavreta_Regulacia_v04_SK.slx"
EXPECTED="0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0"
BUILD=(HERE/"build_and_run_dh_v02.m").read_text(encoding="utf-8-sig")
LAUNCH=(HERE/"run_guarded_v02.ps1").read_text(encoding="utf-8-sig")

def assert_check(name, condition, checks):
    if not condition: raise AssertionError(name)
    checks[name]="PASS"

def main():
    checks={}
    assert_check("source_sha256_unchanged",hashlib.sha256(SRC.read_bytes()).hexdigest().upper()==EXPECTED,checks)
    assert_check("no_STOP_changed",not (LIVE/"STOP").exists() and not (SCADA/"STOP").exists(),checks)
    assert_check("source_remains_outside_destination", "copyfile(src,clone)" in BUILD and
                 "save_system(srcmodel,clone)" in BUILD and "save_system(src," not in BUILD,checks)
    assert_check("two_timeline_cases", "DH_ON" in BUILD and "DH_OFF_96h" in BUILD
                 and "dh(h>=96)=0" in BUILD,checks)
    assert_check("feedback_signal_delayed", all(x in BUILD for x in
        ("Ts_prev_CZT/1","Feedback_dopyt_CZT/2",
         "Feedback_dopyt_CZT/1","Dispecer_Stateflow/2",
         "Rozdelovac_energie_DC_TES_Bazen/6")),checks)
    assert_check("feedback_is_causally_delayed", "simulink/Discrete/Unit Delay" in BUILD and
                 "InitialCondition" in BUILD,checks)
    assert_check("stateflow_pump_heat_balance", all(x in BUILD for x in
         ("q=max(0,y(11))", "res=(cs*(tS-Ts)+cr*(tR-Tr))/dt+qs+qr+load-q",
          "pump=dp*mdot/(997*0.70)", "mdot=0;end")),checks)
    assert_check("enforced_model_dh_off", all(x in BUILD for x in
         ("all(abs(Y(mask,11))<1e-5)", "all(abs(D(mask,3))<1e-5)",
          "all(abs(D(mask,4))<1e-5)", "all(abs(D(mask,6))<1e-5)")),checks)
    assert_check("residual_absolute", "all(abs(Y(:,22:25))<1e-5" in BUILD and
                 "max(abs(D(:,5)))<1e-5" in BUILD,checks)
    assert_check("no_v85_file_reference", "DCHR_Electrical_Dispatch_Stateflow_v85.slx" not in BUILD,checks)
    assert_check("guard_has_memory_threshold", "RequiredFreeRamMB = 7168" in LAUNCH and
                 "BLOCKED_RAM" in LAUNCH and "STOP" in LAUNCH,checks)

    # An independently recalculated two-node balance using the previously saved (already
    # executed) v04 data. This tests the pilot assumptions, not the new MATLAB chart.
    p=calculate("ca74c32211a44b6d9e83cd61d96cf59f")
    assert_check("v04_saved_run_672_samples", len(p["rows"])==672 and p["dt_s"]==900,checks)
    assert_check("pilot_balance", p["max_energy_residual_W"]<1e-6,checks)
    assert_check("pilot_off_at_96h", all(r["Q_load_W"]==0 and
       r["P_pump_W"]==0 and r["flow_kg_s"]==0 for r in p["rows"] if r["interval_start_h"]>=96),checks)
    # Independent energy and pump check for a fixed positive flow (not checking FUXA).
    a=DesignAssumptions()
    s=step(48,38,80000,100000,5,38,a=a)
    eq=(a.mass_supply_kg*a.cp_J_kgK*(s["T_supply_C"]-48)+
        a.mass_return_kg*a.cp_J_kgK*(s["T_return_C"]-38))/900
    rhs=80000-s["Q_load_W"]-a.ua_supply_W_K*(s["T_supply_C"]-a.ambient_C)-a.ua_return_W_K*(s["T_return_C"]-a.ambient_C)
    assert_check("independent_two_node_first_law",abs(eq-rhs)<1e-6,checks)
    assert_check("pump_power_positive_only_with_flow",s["P_pump_W"]>0 and
                 step(45,38,0,0,0,38)["P_pump_W"]==0,checks)
    # Simple scalar feedback invariants equivalent to builder's multiplier policy.
    feedback=lambda req,ts: 0 if req<=0 else min(500000,req*max(.45,min(1.25,1+.025*(52-ts))))
    assert_check("feedback_dependent_on_temperature", feedback(100000,40)>feedback(100000,70),checks)
    assert_check("zero_demand_no_stale_request",feedback(0,20)==0,checks)

    result={
      "status":"STATIC_AND_INDEPENDENT_PILOT_QA_PASS",
      "count":len(checks),
      "checks":checks,
      "source_sha256":EXPECTED,
      "new_simulink_run_verified":False,
      "new_slx_generated":(HERE/"runtime"/"run_20261025"/"DH_ON"/"DCHR_DH_Dynamic_v02.slx").exists(),
      "blocked_by_ram_at_check":True,
      "existing_run_used":"ca74c32211a44b6d9e83cd61d96cf59f",
      "warning":"The new MATLAB block-diagram builder has not completed Simulink compilation or a real run. Pilot output is a separate approximate source."
    }
    dst=HERE/"QA_STATIC_CHECKPOINT.json"
    dst.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="checks"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
