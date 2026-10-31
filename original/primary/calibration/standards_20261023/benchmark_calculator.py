# -*- coding: utf-8 -*-
"""Independent scenario/benchmark calculator. Never writes existing Simulink files.
Assumptions and reference-data provenance: sources_and_benchmarks.json.
NOTE: linear screening model, not the transient pool / heat-pump plant.
"""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RHO = 997.0             # kg/m3; illustrative near 25 C
CP = 4182.0             # J/(kg K); illustrative liquid water
HOURS_PER_YEAR = 8760
PUE_SURVEY_2026 = 1.52  # Uptime Institute 2026, n=644, survey mean
SK_POOL_MAX_C = 28.0    # 308/2012 published text, confirm current law

@dataclass
class Inputs:
    length_m: float = 25.0
    width_m: float = 12.5
    depth_m: float = 1.6
    initial_C: float = 16.0
    target_C: float = 27.5
    switch_off_C: float = 27.8
    standard_max_C: float = SK_POOL_MAX_C
    heater_kW: float = 150.0
    holding_loss_kW: float = 31.45  # from pool500m3 scenario at 28 C, NOT observation
    cop: float = 4.0                # fixed COP placeholder, NOT EN 14511 equipment rating
    source_C: float = 35.0
    approach_K: float = 3.0
    it_capacity_MW: float = 10.0
    it_utilization: float = 0.82
    recovery_fraction: float = 0.85
    pue: float = 1.20
    hours: int = HOURS_PER_YEAR

def calculate(x: Inputs) -> dict:
    warnings = []
    if min(x.length_m,x.width_m,x.depth_m,x.heater_kW,x.cop,x.pue,x.it_capacity_MW,x.hours) <= 0:
        raise ValueError("Dimensions, heater, COP, PUE, IT rating and hours must be positive")
    if x.pue < 1: raise ValueError("PUE must be >= 1")
    if not (0 <= x.it_utilization <= 1 and 0 <= x.recovery_fraction <= 1):
        raise ValueError("Fractions must lie between 0 and 1")
    if x.cop <= 1: raise ValueError("COP must exceed 1 for source/electricity partition")
    if x.target_C < x.initial_C: raise ValueError("Target below initial temperature: use cooling model")
    if x.holding_loss_kW < 0: raise ValueError("Negative constant pool loss unsupported")
    if x.switch_off_C > x.standard_max_C + 1e-10:
        warnings.append("NORMATIVE REVIEW: switch-off temperature exceeds published swimming pool maximum")
    if x.target_C >= x.standard_max_C:
        warnings.append("No control margin below maximum: reduce target and allow measurement uncertainty")
    if x.target_C > x.switch_off_C:
        warnings.append("Thermostat off threshold below heating target")
    area_ratio = x.length_m*x.width_m/312.5
    effective_holding_loss_kW = x.holding_loss_kW * area_ratio
    if x.heater_kW <= effective_holding_loss_kW:
        warnings.append("No positive net capacity for heat-up under constant-loss screening approximation")
    if x.source_C < x.target_C + x.approach_K:
        warnings.append("Direct heat exchanger not feasible by simple temperature approach rule")
    warnings += [
        "PUE 1.52 is a 2026 population survey benchmark, not site measurement/mandatory target",
        "31.45 kW loss is a 312.5 m2 synthetic baseline, scaled linearly by area; NOT measured or valid for changed ambient conditions",
        "constant COP and losses are screening assumptions; use dynamic pool model for annual simulations",
        "EU ERF measured at DC boundary; screening result is not a reportable compliance metric",
        "legal effective version, STN text, equipment and safety still need professional review"
    ]
    V = x.length_m*x.width_m*x.depth_m
    Eheat_MWh = RHO*V*CP*(x.target_C-x.initial_C)/3.6e9
    net_kW = x.heater_kW-effective_holding_loss_kW
    time_h = 1000*Eheat_MWh/net_kW if net_kW>0 else None
    electricity_MWh = Eheat_MWh/x.cop
    source_MWh = Eheat_MWh-electricity_MWh
    pool_year_hold_MWh = effective_holding_loss_kW*x.hours/1000
    pool_year_heat_MWh = pool_year_hold_MWh+Eheat_MWh
    pool_year_hp_electric_MWh = pool_year_heat_MWh/x.cop
    pool_year_hp_source_MWh = pool_year_heat_MWh-pool_year_hp_electric_MWh
    P_IT_MW = x.it_capacity_MW*x.it_utilization
    EIT_MWh = P_IT_MW*x.hours
    EDC_MWh = EIT_MWh*x.pue
    P_recoverable_MW = P_IT_MW*x.recovery_fraction
    annual_potential_MWh = P_recoverable_MW*x.hours
    ERF_screening = min(pool_year_hp_source_MWh, annual_potential_MWh)/EDC_MWh
    return {
        "input":asdict(x),
        "provenance":{"it_and_COP":"D engineering assumption","holding_loss":"D synthetic pool model","PUE_benchmark":"B Uptime 2026","pool_max":"published Slov-Lex 308/2012 text, consolidation not independently verified"},
        "pool":{"volume_m3":V,"water_surface_m2":x.length_m*x.width_m,
                "area_scaled_holding_loss_kW":effective_holding_loss_kW,
                "ideal_heatup_MWh":Eheat_MWh,"constant_loss_heatup_h":time_h,
                "ideal_hp_electric_MWh":electricity_MWh,"ideal_hp_dc_source_MWh":source_MWh,
                "screening_hold_year_MWh":pool_year_hold_MWh,
                "screening_annual_heat_MWh":pool_year_heat_MWh,
                "screening_annual_hp_electric_MWh":pool_year_hp_electric_MWh},
        "datacentre":{"IT_MW":P_IT_MW,"annual_EIT_MWh":EIT_MWh,
                "annual_EDC_MWh":EDC_MWh,"scenario_recoverable_MW":P_recoverable_MW,
                "scenario_recoverable_annual_MWh":annual_potential_MWh,
                "benchmark_pue_2026":PUE_SURVEY_2026,
                "reference_PUE_2026_EDC_MWh":EIT_MWh*PUE_SURVEY_2026,
                "delta_current_minus_survey_EDC_MWh":EIT_MWh*(x.pue-PUE_SURVEY_2026),
                "pool_HP_source_boundary_ERF_screening":ERF_screening},
        "direct_exchange_possible_screening":x.source_C>=x.target_C+x.approach_K,
        "warnings":warnings
    }

def parse_args():
    p=argparse.ArgumentParser(description="Research screening calculator, independently owned")
    for name in Inputs.__dataclass_fields__:
        field=Inputs.__dataclass_fields__[name]
        default=field.default
        p.add_argument("--"+name.replace("_","-"),type=int if name=="hours" else float,default=default)
    p.add_argument("--output",default="comparison_result.json")
    return p.parse_args()

def main():
    opts=parse_args()
    x=Inputs(**{k:getattr(opts,k) for k in Inputs.__dataclass_fields__})
    result=calculate(x)
    target=Path(opts.output)
    if not target.is_absolute():target=HERE/target
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite an existing result: {target}")
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({
        "saved":str(target),"volume_m3":result["pool"]["volume_m3"],
        "heatup_MWh":round(result["pool"]["ideal_heatup_MWh"],3),
        "heatup_screening_h":None if result["pool"]["constant_loss_heatup_h"] is None else round(result["pool"]["constant_loss_heatup_h"],2),
        "pue":x.pue,"pue_market_2026":PUE_SURVEY_2026,
        "warnings":result["warnings"][:2]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
