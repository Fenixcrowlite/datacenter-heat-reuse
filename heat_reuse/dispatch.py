"""Stateflow v85 dispatcher executed by the verified Python numerical runtime.

Raw 1,380-field traces and interval certificates remain authoritative. Scalar
chart values are explicitly upper-bound displays of the retained interval data.
"""
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path

from .matlab_subset import compile_model,M

ROOT=Path(__file__).resolve().parents[1]
_FIXTURE=None


def cases():
    global _FIXTURE
    if _FIXTURE is None:
        with gzip.open(ROOT/'datasets/reference/stateflow_v85.json.gz','rt',encoding='utf-8') as stream:_FIXTURE=json.load(stream)
    return _FIXTURE['cases']


def defaults(case):
    return dict(electric_ceiling_MW=case['policy'][25],demand_MW=case['inputs'][0][5],
                source_capacity_MW_per_K=case['inputs'][0][6],initial_energy_MWh=case['inputs'][0][9],
                initial_hp_on=bool(case['inputs'][0][10]),initial_age_h=case['inputs'][0][11])


def run_dispatch(scenario='HP_only',settings=None,steps=None):
    case=next((c for c in cases() if c['id']==scenario),None)
    if case is None:raise ValueError('Unknown v85 scenario')
    settings=settings or {}
    valid=set(defaults(case))|{'hp_enabled','charging_enabled'}
    if not isinstance(settings,dict) or set(settings)-valid:raise ValueError('Unknown v85 setting')
    for key,value in settings.items():
        if key in {'initial_hp_on','hp_enabled','charging_enabled'}:
            if not isinstance(value,bool):raise ValueError(key+' must be boolean')
        elif isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError(key+' must be finite and nonnegative')
    count=len(case['inputs']) if steps is None else steps
    if isinstance(count,bool) or not isinstance(count,int) or not 1<=count<=len(case['inputs']):
        raise ValueError('v85 steps must fit the selected held-input schedule')
    model=json.loads(next((ROOT/'models/extracted').glob('dchr-electrical-dispatch-stateflow-v85-*.json')).read_text(encoding='utf-8'))
    functions=compile_model(model)
    raw=list(case['policy'])
    if 'electric_ceiling_MW' in settings:raw[25]=settings['electric_ceiling_MW']
    memory=M([0.]*1380,1380,1);policy_memory=M([0.]*27,27,1)
    rows=[];traces=[];certificates=[];input_rows=[];max_residual=0.
    for held,original_input in enumerate(case['inputs'][:count]):
        u=list(original_input)
        for key,index in [('demand_MW',5),('source_capacity_MW_per_K',6),('initial_energy_MWh',9),('initial_hp_on',10),('initial_age_h',11),('hp_enabled',7),('charging_enabled',8)]:
            if key in settings:u[index]=float(settings[key])
        memory,certificate=functions['electrical_dispatch_v85'](M(u,12,1),M(raw,27,1),memory,policy_memory)
        policy_memory=M(raw,27,1);trace=memory.flat();traces.append(trace);certificates.append(certificate.flat());input_rows.append(u)
        max_residual=max(max_residual,abs(trace[52]),abs(trace[53]))
        start=u[2]-u[4]
        for segment in range(int(trace[12])):
            z=trace[100+80*segment:180+80*segment]
            duration_lo,duration_hi=z[6:8]
            if duration_lo<=0:raise ValueError('Nonpositive certified segment duration')
            source=u[6]*raw[12]
            electric_lo,electric_hi=z[35]/duration_hi,z[36]/duration_lo
            recovered_lo,recovered_hi=z[33]/duration_hi,z[34]/duration_lo
            end_lo,end_hi=z[12:14]
            row=dict(cas_h=start+z[9],time_lo_h=start+z[8],time_hi_h=start+z[9],
                     held_interval=held,segment=segment,mode=z[1],event=z[2],
                     Heat_Demand_MW=u[5],Source_Heat_Available_MW=source,HX_Heat_to_HP_MW=source,
                     HP_Heat_Used_MW=z[23],HP_Electric_MW=electric_hi,HP_Electric_lo_MW=electric_lo,
                     HP_Source_Used_MW=recovered_hi,HP_Source_lo_MW=recovered_lo,
                     Storage_Charge_MW=z[25],Storage_Discharge_MW=z[26],Gas_Heat_MW=z[27],Unmet_Heat_MW=z[28],
                     Reused_Heat_MW=z[24]+z[26],Storage_E_MWh=z[11],Storage_E_end_MWh=end_hi,
                     Storage_E_end_lo_MWh=end_lo,tank_temperature_C=raw[1]+end_hi/raw[0])
            rows.append(row)
    last=traces[-1]
    metrics=dict(hp_electric_MWh=last[35],hp_electric_lo_MWh=last[34],reused_to_network_MWh=last[43]-last[44],
                 delivered_service_hi_MWh=last[43],backup_heat_hi_MWh=last[45],unmet_heat_hi_MWh=last[47],
                 final_TES_MWh=last[5],final_TES_lo_MWh=last[4])
    return dict(model_id='stateflow-v85',scenario=scenario,source_kind='PYTHON_COMPUTED',synthetic=True,
                source_sha256=model['sha256'],input_sha256=hashlib.sha256(json.dumps(input_rows).encode()).hexdigest(),
                config=defaults(case)|settings,rows=rows,metrics=metrics,traces=traces,certificates=certificates,
                display_convention='Upper interval bounds; raw traces/certificates preserve both endpoints. No midpoint used in calculations.',
                units={k:'MW' if k.endswith('_MW') else 'MWh' if k.endswith('_MWh') else 'h' if k.endswith('_h') else 'degC' if k.endswith('_C') else '1' for k in rows[0]},
                validation=dict(max_storage_residual_MWh=max_residual,first_law_residual_hull=last[52:54],
                                physical_validation=False,algorithm='Original Stateflow v85 numerical functions in Python; retained memory and electrical policy unchanged between holds'))
