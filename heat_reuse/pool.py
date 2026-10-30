"""Closed-loop Python port of the original pool Stateflow v04.

Equations and state update order match the saved 900-second Simulink model.
No archived result is consulted by the simulation. All values are assumptions.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
import math
from pathlib import Path

INPUTS = ('Qdc_available_W','Tdc_C','Qdh_demand_W','Tair_C','RH','aktivita','plachta','IT_ok','BAZEN_ok','TES_ok','HX_ok')
OUTPUTS = ('T_bazen_C','E_TES_J','Q_pool_req_W','Q_pool_W','Q_pool_loss_W','Q_direct_W',
           'Q_HP_pool_W','Q_HP_DH_W','Q_HP_TES_charge_W','Q_TES_dis_W','Q_DH_delivered_W',
           'Q_DH_unmet_W','Q_pool_unmet_W','Q_HP_source_W','P_HP_comp_W','P_aux_W','Q_reject_W',
           'Qdc_in_W','COP','rezim_Stateflow','Q_TES_standing_loss_W','rez_DC_W','rez_HP_W','rez_pool_W','rez_DH_W')
SCENARIOS = ('zaklad','vypnuty_bazen','vypadok_IT_24h','nulovy_zdroj_24h','teplejsi_zdroj',
             'bez_plachty','TES_vypnute','vysoky_dopyt_DH')


@dataclass(frozen=True)
class PoolConfig:
    volume_m3: float = 500.0
    initial_temperature_C: float = 16.0
    initial_TES_MWh: float = .45
    pool_limit_kw: float = 150.0
    hp_thermal_limit_kw: float = 200.0
    hp_electric_limit_kw: float = 55.0
    source_temperature_offset_C: float = 0.0
    pool_enabled: bool = True
    dh_enabled: bool = True
    hp_pool_enabled: bool = True
    it_enabled: bool = True
    tes_enabled: bool = True
    hx_enabled: bool = True


def configuration(settings):
    values = asdict(PoolConfig())
    if not isinstance(settings,dict) or set(settings)-set(values):
        raise ValueError('Unknown pool settings')
    for key,value in settings.items():
        if isinstance(values[key],bool):
            if not isinstance(value,bool):raise ValueError(key+' must be boolean')
        elif isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError(key+' must be finite')
    c=PoolConfig(**(values|settings))
    if not (0<c.volume_m3<=100000 and -50<c.initial_temperature_C<90 and 0<=c.initial_TES_MWh<=.9):
        raise ValueError('Invalid pool volume/initial condition')
    if min(c.pool_limit_kw,c.hp_thermal_limit_kw,c.hp_electric_limit_kw)<0:
        raise ValueError('Power limits must be nonnegative')
    return c


def generate_inputs(scenario='zaklad',steps=672):
    if scenario not in SCENARIOS or isinstance(steps,bool) or not isinstance(steps,int) or not 1<=steps<=35040:
        raise ValueError('Invalid pool scenario or step count')
    result=[]
    for k in range(steps):
        h=k/4;day=h/24;active=float(8<=h%24<20)
        qdc=max(0,170000+30000*math.cos(2*math.pi*day/7)+20000*math.sin(2*math.pi*h/24))
        ts=30+7*math.cos(2*math.pi*(day-2)/7)
        qdh=75000+35000*active+25000*(.5+.5*math.cos(2*math.pi*day/7))
        row=dict(cas_h=h,Qdc_available_W=qdc,Tdc_C=ts,Qdh_demand_W=qdh,
                 Tair_C=29+.6*math.sin(2*math.pi*day/7),RH=.60+.07*math.sin(2*math.pi*day/7),
                 aktivita=.5+.5*active,plachta=1-active,IT_ok=1.,BAZEN_ok=1.,TES_ok=1.,HX_ok=1.)
        if scenario=='vypnuty_bazen' and 60<=h<108:row['BAZEN_ok']=0.
        if scenario=='vypadok_IT_24h' and 72<=h<96:row['IT_ok']=0.
        if scenario=='nulovy_zdroj_24h' and 72<=h<96:row['Qdc_available_W']=0.
        if scenario=='teplejsi_zdroj':row['Tdc_C']+=12
        if scenario=='bez_plachty':row['plachta']=0.
        if scenario=='TES_vypnute':row['TES_ok']=0.
        if scenario=='vysoky_dopyt_DH':row['Qdh_demand_W']+=95000
        result.append(row)
    return result


def demand(T,thermostat,u,c):
    air,rh,activity,cover=u[3],min(1,max(0,u[4])),max(0,u[5]),min(1,max(0,u[6]))
    pv=.61094*math.exp(17.625*T/(T+243.04));pa=rh*.61094*math.exp(17.625*air/(air+243.04))
    mv=max(0,4e-5*312.5*(pv-pa)*activity*(1-.9*cover))
    losses=mv*2440000+3*312.5*(T-air)*(1-.75*cover)+.95*5.670374419e-8*312.5*((T+273.15)**4-(air-2+273.15)**4)*(1-.75*cover)+800*(T-20)+mv*4182*(T-15)+2000
    new=thermostat
    if T<=27.35:new=1
    elif T>=27.65:new=0
    if u[8]<.5:new=0
    request=0.
    if new>.5 and T<27.75 and u[8]>.5:
        capacity=997*c.volume_m3*4182
        request=min(c.pool_limit_kw*1000,max(0,(27.75-T)*capacity/900+losses),max(0,(27.58-T)*capacity/900+losses))
    return request,losses,new


def choose_mode(req,u,T,E):
    if u[7]<.5:return 4
    if u[0]<=1e-6:return 3 if E>100000 and u[9]>.5 and u[2]>0 else 0
    if u[10]>.5 and u[8]>.5 and req>0 and u[1]>T+5:return 1
    return 2


def allocate(T,E,request,losses,mode,u,c):
    dt=900;emax=900*3.6e6;eta_c=.93;eta_d=.91
    dc=max(0,u[0]);tdc=u[1];need=max(0,u[2]);tes=u[9]>.5
    standing=.002*max(0,E)/86400
    direct=hp_pool=hp_dh=charge=discharge=hp_source=electric=aux=cop=0.
    if mode==1 and u[10]>.5 and u[8]>.5:
        direct=min(request,dc,c.pool_limit_kw*1000,max(0,8500*(tdc-T-5)))
    left=max(0,dc-direct)
    if mode in (1,2):
        cop=min(6,max(2.5,.43*(52+273.15)/max(5,52-(tdc-5))))
        cap=min(c.hp_thermal_limit_kw*1000,c.hp_electric_limit_kw*1000*cop,left/max(1e-9,1-1/cop))
        minimum_dh=min(need,min(50000,cap))
        hp_pool=min(max(0,request-direct),max(0,cap-minimum_dh)) if c.hp_pool_enabled else 0.
        hp_dh=min(need,cap-hp_pool)
        spare=max(0,cap-hp_pool-hp_dh)
        if c.hp_pool_enabled:hp_pool+=min(max(0,request-direct-hp_pool),spare)
        spare=max(0,cap-hp_pool-hp_dh)
        if tes and E<emax and spare>0:
            charge=min(spare,70000,max(0,(emax-E+standing*dt)/(eta_c*dt)))
        hp_out=hp_pool+hp_dh+charge;electric=hp_out/cop;hp_source=hp_out-electric
        if hp_out>0:aux=1500.
    if direct>0:aux+=500.
    pool=direct+hp_pool;short=max(0,need-hp_dh)
    if tes and short>0 and E>0:
        discharge=min(short,80000,max(0,(E-standing*dt)*eta_d/dt))
        if discharge>0:aux+=250.
    if discharge>0 and charge>0:
        charge=0.;hp_out=hp_pool+hp_dh;electric=hp_out/cop;hp_source=hp_out-electric
    dh=hp_dh+discharge;reject=max(0,dc-direct-hp_source)
    next_e=max(0,min(emax,E+dt*(eta_c*charge-discharge/eta_d-standing)))
    next_t=T+dt*(pool-losses)/(997*c.volume_m3*4182)
    return [next_t,next_e,request,pool,losses,direct,hp_pool,hp_dh,charge,discharge,dh,
            max(0,need-dh),max(0,request-pool),hp_source,electric,aux,reject,dc,cop,mode,standing,
            dc-direct-hp_source-reject,hp_pool+hp_dh+charge-hp_source-electric,pool-direct-hp_pool,dh-hp_dh-discharge]


def run_pool(inputs=None,settings=None,scenario='zaklad',steps=672):
    c=configuration(settings or {})
    if inputs is None:inputs=generate_inputs(scenario,steps)
    if not isinstance(inputs,list) or not 1<=len(inputs)<=35040:raise ValueError('Invalid pool input length')
    T=c.initial_temperature_C;E=c.initial_TES_MWh*3.6e9;thermostat=1
    rows=[];water_residual=storage_residual=0.
    for index,record in enumerate(inputs):
        try:u=[float(record[k]) for k in INPUTS]
        except (KeyError,TypeError,ValueError) as error:raise ValueError('Invalid pool input fields') from error
        if not all(map(math.isfinite,u)) or not -50<u[1]<100 or not -50<u[3]<100:
            raise ValueError('Pool input must be finite and in temperature domain')
        u[1]+=c.source_temperature_offset_C
        for flag,key in ((7,'it_enabled'),(8,'pool_enabled'),(9,'tes_enabled'),(10,'hx_enabled')):
            if not getattr(c,key):u[flag]=0.
        if not c.dh_enabled:u[2]=0.
        req,loss,new_thermostat=demand(T,thermostat,u,c)
        mode=choose_mode(req,u,T,E)
        values=allocate(T,E,req,loss,mode,u,c)
        row=dict(zip(INPUTS,u));row['cas_h']=index/4
        row.update(zip(OUTPUTS,values))
        water_residual=max(water_residual,abs((values[0]-T)*997*c.volume_m3*4182/900-(row['Q_pool_W']-row['Q_pool_loss_W'])))
        storage_residual=max(storage_residual,abs((values[1]-E)/900-(.93*row['Q_HP_TES_charge_W']-row['Q_TES_dis_W']/.91-row['Q_TES_standing_loss_W'])))
        T,E=values[:2];thermostat=new_thermostat;rows.append(row)
    total=lambda field:math.fsum(r[field] for r in rows)*900/3.6e9
    return dict(model_id='pool-v04',scenario=scenario,source_kind='PYTHON_COMPUTED',synthetic=True,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                input_sha256=hashlib.sha256(json.dumps([{k:r[k] for k in INPUTS} for r in inputs],sort_keys=True).encode()).hexdigest(),
                config=asdict(c),rows=rows,units={k:'W' if k.endswith('_W') else 'J' if k.endswith('_J') else 'degC' if k.endswith('_C') else 'h' if k=='cas_h' else '1' for k in rows[0]},
                metrics=dict(pool_heat_MWh=total('Q_pool_W'),dh_heat_MWh=total('Q_DH_delivered_W'),
                             hp_electric_MWh=total('P_HP_comp_W'),dh_unmet_MWh=total('Q_DH_unmet_W'),
                             final_temperature_C=T,final_TES_MWh=E/3.6e9),
                validation=dict(max_water_residual_W=water_residual,max_storage_residual_W=storage_residual,
                                physical_validation=False,algorithm='Original Stateflow v04 numerical and discrete update-order port'))
