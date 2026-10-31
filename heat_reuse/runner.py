"""Shared calculation interface for CLI, browser and verification."""
import csv
import gzip
from dataclasses import asdict
from pathlib import Path

from .annual import run_annual,configuration as annual_config,SCENARIOS as ANNUAL_SCENARIOS
from .pool import run_pool,SCENARIOS as POOL_SCENARIOS

ROOT=Path(__file__).resolve().parents[1]


def list_models():
    from .dispatch import cases,defaults
    return [dict(id='annual-v2',name='Annual heat-recovery study',scenarios=list(ANNUAL_SCENARIOS),
                 default_scenario='Warm45_Storage100',default_steps=8760,max_steps=8760,time_step_s=3600,
                 status='verified_python_port',scenario_defaults={s:asdict(annual_config(s)) for s in ANNUAL_SCENARIOS},
                 description='DC, HX, HP, TES and district heat; native MATLAB annual comparison'),
            dict(id='pool-v04',name='Pool · closed-loop Stateflow v04',scenarios=list(POOL_SCENARIOS),
                 default_scenario='zaklad',default_steps=672,max_steps=35040,time_step_s=900,
                 status='verified_python_port',description='500 m³ pool, thermostat, heat allocation and TES; eight Simulink reference scenarios'),
            dict(id='stateflow-v85',name='Stateflow v85 · interval dispatcher',scenarios=[c['id'] for c in cases()],
                 default_scenario='HP_only',default_steps=2,max_steps=4,time_step_s=None,status='verified_python_port',
                 scenario_defaults={c['id']:defaults(c)|{'steps':len(c['inputs'])} for c in cases()},
                 description='Retained-state dispatcher, 28 native scenarios / 120060 full-trace field comparisons')]


def run_model(model_id,config=None,inputs=None,scenario=None,steps=None):
    entry=next((m for m in list_models() if m['id']==model_id),None)
    if entry is None:raise ValueError('Model does not have a verified Python adapter')
    if model_id=='stateflow-v85':
        from .dispatch import run_dispatch
        if inputs is not None:raise ValueError('Use the versioned v85 schedule interface')
        return run_dispatch(scenario or entry['default_scenario'],config,steps)
    steps=entry['default_steps'] if steps is None else steps
    if isinstance(steps,bool) or not isinstance(steps,int) or not 1<=steps<=entry['max_steps']:
        raise ValueError('Invalid simulation length')
    scenario=scenario or entry['default_scenario']
    if scenario not in entry['scenarios']:raise ValueError('Unknown scenario for model')
    if model_id=='annual-v2':
        if inputs is None:
            with gzip.open(ROOT/'datasets/reference/annual_inputs.csv.gz','rt',encoding='utf-8-sig',newline='') as stream:
                inputs=list(csv.DictReader(stream))[:steps]
        return run_annual(inputs,scenario,config)
    return run_pool(inputs,config,scenario,steps)
