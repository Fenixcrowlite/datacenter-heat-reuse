"""Python port of dchr.simulate_system_v2 and compute_metrics_v2.

Original equations: default_config[_v2].m, +dchr/+components/*.m.
Continuation C37 supplies an independent previously compared implementation.
The bundled input is synthetic MATLAB seed-42 data, reused exactly rather than
pretending Python and MATLAB have the same Gaussian random-number generator.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class AnnualConfig:
    source_temp_C: float = 45.0
    recovery_fraction: float = .90
    storage_capacity_MWh: float = 100.0
    initial_soc: float = 0.0
    charge_limit_MW: float = 5.0
    discharge_limit_MW: float = 5.0
    eta_charge: float = .95
    eta_discharge: float = .95
    storage_loss_fraction_h: float = 1e-4
    hp_capacity_MW: float = 12.0
    carnot_efficiency: float = .45
    cop_min: float = 2.2
    cop_max: float = 7.0
    part_load_penalty: float = .08
    hx_effectiveness: float = .97
    hx_max_MW: float = 20.0
    hx_approach_K: float = 3.0
    supply_min_C: float = 55.0
    supply_max_C: float = 80.0
    return_min_C: float = 35.0
    return_max_C: float = 50.0
    fixed_temperature: bool = False
    supply_fixed_C: float = 70.0
    dt_h: float = 1.0
    pue: float = 1.2
    boiler_efficiency: float = .9
    electricity_EUR_MWh: float = 100.0
    gas_EUR_MWh: float = 50.0
    grid_CO2_t_MWh: float = .2
    gas_CO2_t_MWh: float = .202
    hp_capex_EUR_kW: float = 650.0
    storage_capex_EUR_kWh: float = 35.0
    hx_capex_EUR_kW: float = 80.0
    project_years: float = 20.0
    discount_rate: float = .06


SCENARIOS = {
    'Air25_Fixed70': {'source_temp_C': 25., 'recovery_fraction': .70, 'storage_capacity_MWh': 0., 'fixed_temperature': True},
    'Liquid35_Weather': {'source_temp_C': 35., 'recovery_fraction': .85, 'storage_capacity_MWh': 0.},
    'Warm45_Weather': {'storage_capacity_MWh': 0.},
    'Warm45_Storage100': {},
    'Liquid35_LowTempDH': {'source_temp_C': 35., 'recovery_fraction': .85, 'supply_min_C': 45.,
                          'supply_max_C': 65., 'return_min_C': 30., 'return_max_C': 40.},
}


def configuration(scenario, overrides=None):
    if scenario not in SCENARIOS:
        raise ValueError('Unknown annual scenario')
    data = asdict(AnnualConfig()) | SCENARIOS[scenario]
    overrides = overrides or {}
    if not isinstance(overrides, dict) or set(overrides) - set(data):
        raise ValueError('Unknown annual settings')
    data.update(overrides)
    for key, value in data.items():
        if key == 'fixed_temperature':
            if not isinstance(value, bool):
                raise ValueError('fixed_temperature must be boolean')
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Setting must be finite: ' + key)
    c = AnnualConfig(**data)
    if c.dt_h <= 0 or c.project_years <= 0 or c.discount_rate < 0 or c.pue < 1:
        raise ValueError('Invalid time, economic horizon or PUE')
    if not 0 <= c.initial_soc <= 1 or not 0 <= c.recovery_fraction <= 1 or not 0 <= c.hx_effectiveness <= 1:
        raise ValueError('Invalid fraction')
    if not (0 < c.eta_charge <= 1 and 0 < c.eta_discharge <= 1 and 0 < c.boiler_efficiency <= 1):
        raise ValueError('Invalid efficiency')
    if not (1 < c.cop_min <= c.cop_max and 0 < c.carnot_efficiency <= 1 and 0 <= c.part_load_penalty <= 1):
        raise ValueError('Invalid COP parameters')
    if min(c.storage_capacity_MWh, c.charge_limit_MW, c.discharge_limit_MW, c.hp_capacity_MW,
           c.hx_max_MW, c.hx_approach_K, c.storage_loss_fraction_h) < 0 or c.storage_loss_fraction_h * c.dt_h > 1:
        raise ValueError('Invalid storage or power limits')
    if min(c.source_temp_C, c.supply_min_C, c.return_min_C, c.supply_fixed_C) <= -273.15:
        raise ValueError('Temperature below absolute zero')
    return c


def step(row, energy, c):
    required = ('Tout_C', 'IT_Util', 'IT_MW', 'DC_Total_MW')
    if not isinstance(row, dict) or not all(k in row for k in (*required, 'Time')):
        raise ValueError('Missing annual input fields')
    values = {key: float(row[key]) for key in required}
    if not all(math.isfinite(v) for v in values.values()) or values['IT_MW'] < 0:
        raise ValueError('Invalid annual input')
    tout, it = values['Tout_C'], values['IT_MW']
    clamp = lambda x, lo, hi: min(hi, max(lo, x))
    demand = (2. + 18. * clamp((16. - tout) / 28., 0., 1.15)) / .94
    fraction = clamp((16. - tout) / 28., 0., 1.)
    supply = c.supply_fixed_C if c.fixed_temperature else c.supply_min_C + fraction * (c.supply_max_C - c.supply_min_C)
    ret = supply - 30. if c.fixed_temperature else c.return_min_C + fraction * (c.return_max_C - c.return_min_C)
    source = max(0., it) * c.recovery_fraction
    hx = max(0., min(source * c.hx_effectiveness, c.hx_max_MW))
    evaporator = c.source_temp_C - c.hx_approach_K
    lift = max(1., supply - evaporator)
    nominal_cop = clamp(c.carnot_efficiency * (supply + 273.15) / lift, c.cop_min, c.cop_max)
    potential = min(c.hp_capacity_MW, max(0., hx * nominal_cop / max(1e-6, nominal_cop - 1.)))
    direct = min(potential, demand)
    surplus, deficit = max(0., potential - demand), max(0., demand - potential)
    after_loss = max(0., energy * (1. - c.storage_loss_fraction_h * c.dt_h))
    charge = discharge = 0.
    if surplus > 0.:
        charge = min(surplus, c.charge_limit_MW, max(0., c.storage_capacity_MWh - after_loss) / (c.eta_charge * c.dt_h))
    elif deficit > 0.:
        discharge = min(deficit, c.discharge_limit_MW, after_loss * c.eta_discharge / c.dt_h)
    next_energy = max(0., after_loss + c.dt_h * (c.eta_charge * charge - discharge / c.eta_discharge))
    used = direct + charge
    gas = max(0., demand - direct - discharge)
    plr = clamp(used / max(math.ulp(1.), c.hp_capacity_MW), 0., 1.)
    cop = clamp(nominal_cop * (1. - c.part_load_penalty * max(0., 1. - plr)), c.cop_min, c.cop_max)
    electric = used / cop
    exergy = (direct + discharge) * max(0., 1. - 283.15 / (supply + 273.15))
    result = dict(Time=row['Time'], **values, Heat_Demand_MW=demand, DH_Supply_C=supply, DH_Return_C=ret,
                  Source_Heat_Available_MW=source, HX_Heat_to_HP_MW=hx, HX_Rejected_MW=max(0., source-hx),
                  Temperature_Lift_K=lift, COP=cop, HP_Heat_MW=potential, HP_Heat_Used_MW=used,
                  HP_Electric_MW=electric, HP_Source_Used_MW=max(0., used-electric), Storage_Charge_MW=charge,
                  Storage_Discharge_MW=discharge, Storage_E_MWh=energy, Gas_Heat_MW=gas,
                  Curtailed_HP_Heat_MW=max(0., potential-used), Useful_Heat_Exergy_MW=exergy,
                  Storage_E_end_MWh=next_energy)
    return result, next_energy


def metrics(rows, c):
    total = lambda field: math.fsum(r[field] for r in rows) * c.dt_h
    demand, gas, electric = total('Heat_Demand_MW'), total('Gas_Heat_MW'), total('HP_Electric_MW')
    reused = max(0., demand - gas)
    saving = (demand - gas) / c.boiler_efficiency * c.gas_EUR_MWh - electric * c.electricity_EUR_MWh
    capex = c.hp_capacity_MW * 1000 * c.hp_capex_EUR_kW + c.storage_capacity_MWh * 1000 * c.storage_capex_EUR_kWh + c.hx_max_MW * 1000 * c.hx_capex_EUR_kW
    rate, years = c.discount_rate, c.project_years
    crf = 1 / years if rate == 0 else rate * (1 + rate)**years / ((1 + rate)**years - 1)
    return dict(heat_demand_MWh=demand, gas_heat_MWh=gas, hp_electric_MWh=electric,
                reused_to_network_MWh=reused, exergy_delivered_MWh=total('Useful_Heat_Exergy_MW'),
                curtailed_hp_heat_MWh=total('Curtailed_HP_Heat_MW'), coverage_fraction=reused / max(1e-300, demand),
                mean_cop=math.fsum(r['COP'] * r['HP_Heat_Used_MW'] for r in rows) / max(1e-300, total('HP_Heat_Used_MW') / c.dt_h),
                erf=reused / max(1e-300, total('DC_Total_MW')),
                ere_system=(total('DC_Total_MW') + electric - reused) / max(1e-300, total('IT_MW')),
                opex_saving_EUR=saving, CO2_saving_t=(demand-gas) / c.boiler_efficiency * c.gas_CO2_t_MWh-electric*c.grid_CO2_t_MWh,
                capex_EUR=capex, screening_LCOH_EUR_per_MWh=(capex*crf+electric*c.electricity_EUR_MWh)/max(1e-300,reused),
                simple_payback_y=capex/saving if saving>0 else None)


def run_annual(inputs, scenario='Warm45_Storage100', overrides=None):
    c = configuration(scenario, overrides)
    if not isinstance(inputs, list) or not inputs or len(inputs) > 105120:
        raise ValueError('Provide 1..105120 annual input records')
    energy = c.initial_soc * c.storage_capacity_MWh
    rows, residuals = [], []
    for source in inputs:
        row, new_energy = step(source, energy, c)
        residuals.append(abs(new_energy-energy*(1-c.storage_loss_fraction_h*c.dt_h)-c.dt_h*(c.eta_charge*row['Storage_Charge_MW']-row['Storage_Discharge_MW']/c.eta_discharge)))
        rows.append(row)
        energy = new_energy
    return dict(model_id='annual-v2', scenario=scenario, source_kind='PYTHON_COMPUTED', synthetic=True,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                input_sha256=hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
                config=asdict(c), rows=rows, metrics=metrics(rows,c),
                units={key: 'MW' if key.endswith('_MW') else 'MWh' if key.endswith('_MWh') else 'degC' if key.endswith('_C') else '1' for key in rows[0] if key!='Time'},
                validation={'max_storage_residual_MWh': max(residuals), 'physical_validation': False,
                            'algorithm': 'MATLAB simulate_system_v2 source-equation port', 'reference': 'C88 native synthetic annual fixture'})
