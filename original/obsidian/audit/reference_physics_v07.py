"""Independent first-law heat reuse reference kernel, v0.7.
NOT a replication of any paper; scenario values must not be presented as measured.
All heat/electric powers in MW, storage state in MWh, timestep hours.
Positive delivered heat is towards district heating. stdlib only.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

def _finite_nonnegative(x:float,name:str)->None:
    if not math.isfinite(x) or x < 0: raise ValueError(f"{name} must be finite and nonnegative")

@dataclass(frozen=True)
class Parameters:
    hp_capacity_mw: float = 37.0
    boiler_capacity_mw: float = 20.0
    storage_capacity_mwh: float = 82.0
    charge_limit_mw: float = 20.0
    discharge_limit_mw: float = 20.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    standing_loss_fraction_per_hour: float = 0.0005
    dt_h: float = 1.0
    def __post_init__(self):
        for n in ("hp_capacity_mw","boiler_capacity_mw","storage_capacity_mwh","charge_limit_mw",
                  "discharge_limit_mw","standing_loss_fraction_per_hour"):
            _finite_nonnegative(getattr(self,n),n)
        if not math.isfinite(self.dt_h) or self.dt_h <= 0: raise ValueError("dt_h > 0 required")
        for n in ("charge_efficiency","discharge_efficiency"):
            v=getattr(self,n)
            if not math.isfinite(v) or not 0 < v <= 1: raise ValueError(n+" must be in (0,1]")
        if self.standing_loss_fraction_per_hour*self.dt_h > 1: raise ValueError("storage decay > 100% of state")

@dataclass(frozen=True)
class Step:
    demand_mw: float
    source_available_mw: float
    hp_cop: float
    hp_heat_mw: float
    evaporator_mw: float
    compressor_mw: float
    direct_mw: float
    charge_mw: float
    discharge_mw: float
    boiler_mw: float
    unmet_mw: float
    unused_source_mw: float
    storage_start_mwh: float
    storage_end_mwh: float
    storage_loss_mwh: float

def dispatch_step(p:Parameters, demand_mw:float, source_available_mw:float, hp_cop:float,
                  storage_start_mwh:float)->Step:
    for name,x in (("demand_mw",demand_mw),("source_available_mw",source_available_mw),
                   ("storage_start_mwh",storage_start_mwh)):
        _finite_nonnegative(x,name)
    if storage_start_mwh > p.storage_capacity_mwh + 1e-9: raise ValueError("storage exceeds cap")
    if not math.isfinite(hp_cop) or hp_cop <= 1.0: raise ValueError("COP must be >1")
    decay=storage_start_mwh*p.standing_loss_fraction_per_hour*p.dt_h
    available_storage=storage_start_mwh-decay
    hp_source_limited=source_available_mw * hp_cop/(hp_cop-1.0)
    hp_limit=min(p.hp_capacity_mw,hp_source_limited)
    max_charge=min(p.charge_limit_mw,
                   max(0.0,(p.storage_capacity_mwh-available_storage)/(p.charge_efficiency*p.dt_h)))
    # Do not run HP to waste heat: only demand plus available storage charge sink.
    hp_heat=min(hp_limit,demand_mw+max_charge)
    direct=min(demand_mw,hp_heat)
    charge=max(0.0,hp_heat-direct)
    deficiency=max(0.0,demand_mw-direct)
    discharge=min(deficiency,p.discharge_limit_mw,available_storage*p.discharge_efficiency/p.dt_h)
    remaining=max(0.0,deficiency-discharge)
    gas=min(remaining,p.boiler_capacity_mw)
    unmet=max(0.0,remaining-gas)
    energy=available_storage + p.charge_efficiency*charge*p.dt_h-discharge*p.dt_h/p.discharge_efficiency
    # Floating point noise at physical boundaries is allowed but not hidden.
    if energy < -1e-9 or energy > p.storage_capacity_mwh + 1e-9: raise ArithmeticError("storage bounds")
    energy=min(p.storage_capacity_mwh,max(0.0,energy))
    electric=hp_heat/hp_cop
    evap=hp_heat-electric
    unused=max(0.0,source_available_mw-evap)
    return Step(demand_mw,source_available_mw,hp_cop,hp_heat,evap,electric,direct,charge,
                discharge,gas,unmet,unused,storage_start_mwh,energy,decay)

@dataclass(frozen=True)
class HeatExchanger:
    heat_mw: float
    hot_out_c: float
    cold_out_c: float
    effectiveness: float

def counterflow_hx(hot_in_c:float,cold_in_c:float,hot_capacity_mw_per_k:float,
                   cold_capacity_mw_per_k:float,ua_mw_per_k:float)->HeatExchanger:
    """Idealized counterflow epsilon-NTU, NOT Sintong's crossflow equation 17."""
    for n,x in (("hot_capacity",hot_capacity_mw_per_k),("cold_capacity",cold_capacity_mw_per_k),
                ("UA",ua_mw_per_k)):
        _finite_nonnegative(x,n)
    if not all(math.isfinite(v) for v in (hot_in_c,cold_in_c)): raise ValueError("temperatures finite")
    if hot_in_c <= cold_in_c or min(hot_capacity_mw_per_k,cold_capacity_mw_per_k,ua_mw_per_k)==0:
        return HeatExchanger(0.,hot_in_c,cold_in_c,0.)
    cmin=min(hot_capacity_mw_per_k,cold_capacity_mw_per_k)
    cmax=max(hot_capacity_mw_per_k,cold_capacity_mw_per_k)
    cr=cmin/cmax
    ntu=ua_mw_per_k/cmin
    if abs(1.0-cr)<1e-12: eps=ntu/(1.0+ntu)
    else:
        a=math.exp(-ntu*(1.-cr))
        eps=(1.-a)/(1.-cr*a)
    eps=min(1.0,max(0.0,eps))
    q=eps*cmin*(hot_in_c-cold_in_c)
    h_out=hot_in_c-q/hot_capacity_mw_per_k
    c_out=cold_in_c+q/cold_capacity_mw_per_k
    return HeatExchanger(q,h_out,c_out,eps)
