"""Independent loss-first TES and finite-backup dispatch reference, v16.

Engineering assumptions, not a primary-paper or measured-system replication.
Powers are MW, stored energy is MWh, and the fixed timestep is in hours.
The heat pump imports the analytic quadratic reference from v14; the MATLAB
implementation's root search is intentionally not reproduced here.

E_after = E_start * (1 - lambda * dt)
E_next = E_after + eta_charge * charge * dt - discharge * dt / eta_discharge
Demand = HP_direct + discharge + boiler + unmet

The linear standing-loss fraction is a discrete scenario assumption. Its
domain lambda*dt <= 1 does not make it a continuous exponential decay model.
Charge/discharge are mutually exclusive and their efficiencies account for
heat losses, rather than silently disappearing from the system balance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

from heat_pump_reference_v14 import HeatPumpParameters, heat_pump_step


def finite_scalar(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real numeric scalar")
    return float(value)


@dataclass(frozen=True)
class StorageParameters:
    capacity_MWh: float = 50.0
    charge_limit_MW: float = 5.0
    discharge_limit_MW: float = 5.0
    eta_charge: float = 0.95
    eta_discharge: float = 0.95
    loss_fraction_per_h: float = 1e-4

    def __post_init__(self) -> None:
        for name in ("capacity_MWh", "charge_limit_MW", "discharge_limit_MW",
                     "loss_fraction_per_h"):
            if finite_scalar(getattr(self, name), name) < 0:
                raise ValueError(f"{name} must be nonnegative")
        for name in ("eta_charge", "eta_discharge"):
            if not 0 < finite_scalar(getattr(self, name), name) <= 1:
                raise ValueError(f"{name} must be in (0,1]")

    def validate_timestep(self, dt_h: float) -> float:
        dt_h = finite_scalar(dt_h, "dt_h")
        if dt_h <= 0:
            raise ValueError("dt_h must be positive")
        if self.loss_fraction_per_h * dt_h > 1:
            raise ValueError("linear standing loss requires lambda*dt_h <= 1")
        return dt_h


@dataclass(frozen=True)
class DispatchParameters:
    hp: HeatPumpParameters = HeatPumpParameters()
    storage: StorageParameters = StorageParameters()
    boiler_capacity_MW: float = 20.0
    dt_h: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.hp, HeatPumpParameters):
            raise ValueError("hp must be a HeatPumpParameters instance")
        if not isinstance(self.storage, StorageParameters):
            raise ValueError("storage must be a StorageParameters instance")
        self.storage.validate_timestep(self.dt_h)
        if finite_scalar(self.boiler_capacity_MW, "boiler_capacity_MW") < 0:
            raise ValueError("boiler_capacity_MW must be nonnegative")


@dataclass(frozen=True)
class StorageStep:
    charge_MW: float
    discharge_MW: float
    energy_start_MWh: float
    energy_after_loss_MWh: float
    energy_next_MWh: float
    standing_loss_MWh: float
    charge_loss_MWh: float
    discharge_loss_MWh: float


def storage_step(energy_start_MWh: float, surplus_MW: float, deficit_MW: float,
                 p: StorageParameters, dt_h: float) -> StorageStep:
    """Loss first, then one feasible charge or discharge within the step.

    Input energy bounds are exact. Only final floating-point boundary noise
    within 64 ulps of max(1,capacity) is rounded back to the physical bound.
    Surplus and deficit cannot both be positive, including tiny positives.
    """
    dt_h = p.validate_timestep(dt_h)
    energy = finite_scalar(energy_start_MWh, "energy_start_MWh")
    surplus = finite_scalar(surplus_MW, "surplus_MW")
    deficit = finite_scalar(deficit_MW, "deficit_MW")
    if not 0 <= energy <= p.capacity_MWh:
        raise ValueError("energy_start_MWh must be in [0,capacity_MWh]")
    if surplus < 0 or deficit < 0:
        raise ValueError("surplus_MW and deficit_MW must be nonnegative")
    if surplus > 0 and deficit > 0:
        raise ValueError("simultaneous positive surplus and deficit are invalid")
    after = energy * (1 - p.loss_fraction_per_h * dt_h)
    charge = discharge = 0.0
    if p.capacity_MWh > 0 and surplus > 0:
        charge = min(surplus, p.charge_limit_MW,
                     (p.capacity_MWh - after) / (p.eta_charge * dt_h))
    elif p.capacity_MWh > 0 and deficit > 0:
        discharge = min(deficit, p.discharge_limit_MW,
                        after * p.eta_discharge / dt_h)
    next_raw = after + p.eta_charge * charge * dt_h - discharge * dt_h / p.eta_discharge
    tolerance = 64 * math.ulp(max(1.0, p.capacity_MWh))
    if not math.isfinite(next_raw) or not -tolerance <= next_raw <= p.capacity_MWh + tolerance:
        raise ArithmeticError("derived storage energy violates finite physical bounds")
    next_energy = min(p.capacity_MWh, max(0.0, next_raw))
    return StorageStep(charge, discharge, energy, after, next_energy,
                       energy-after, (1-p.eta_charge)*charge*dt_h,
                       (1/p.eta_discharge-1)*discharge*dt_h)


@dataclass(frozen=True)
class DispatchStep:
    HP_Request_MW: float
    HP_Heat_MW: float
    HP_Direct_MW: float
    HP_Electric_MW: float
    HP_Source_Used_MW: float
    COP: float
    HP_Available: bool
    Source_Unused_MW: float
    Storage_Charge_MW: float
    Storage_Discharge_MW: float
    Storage_E_Start_MWh: float
    Storage_E_After_Loss_MWh: float
    Storage_E_Next_MWh: float
    Storage_Standing_Loss_MWh: float
    Storage_Charge_Loss_MWh: float
    Storage_Discharge_Loss_MWh: float
    Gas_Heat_MW: float
    Unmet_Heat_MW: float
    Supplied_Heat_MW: float


def dispatch_step(source_heat_MW: float, source_C: float, sink_C: float,
                  heat_demand_MW: float, storage_energy_MWh: float,
                  p: DispatchParameters = DispatchParameters()) -> DispatchStep:
    """Request heat for demand plus feasible storage charge; dispatch backup last.

    Source heat enters the evaporator. HP electricity enters separately; gas
    heat is useful boiler output. Boiler fuel and upstream/network losses are
    outside this deliberately limited component boundary.
    """
    source = finite_scalar(source_heat_MW, "source_heat_MW")
    demand = finite_scalar(heat_demand_MW, "heat_demand_MW")
    if source < 0 or demand < 0:
        raise ValueError("source_heat_MW and heat_demand_MW must be nonnegative")
    # Validate the initial state and use this shared loss-first state when
    # requesting HP charging headroom, including room opened by standing loss.
    idle = storage_step(storage_energy_MWh, 0, 0, p.storage, p.dt_h)
    room = p.storage.capacity_MWh - idle.energy_after_loss_MWh
    charge_sink = min(p.storage.charge_limit_MW,
                      room / (p.storage.eta_charge * p.dt_h))
    request = demand + charge_sink
    if not math.isfinite(request):
        raise ValueError("derived heat-pump request must be finite")
    hp = heat_pump_step(source, source_C, sink_C, request, p.hp)
    direct = min(hp.heat_output_MW, demand)
    storage = storage_step(storage_energy_MWh, max(hp.heat_output_MW-demand, 0.0),
                           max(demand-hp.heat_output_MW, 0.0), p.storage, p.dt_h)
    remaining = max(demand-direct-storage.discharge_MW, 0.0)
    boiler = min(p.boiler_capacity_MW, remaining)
    unmet = max(remaining-boiler, 0.0)
    return DispatchStep(request, hp.heat_output_MW, direct, hp.electric_MW,
                        hp.source_used_MW, hp.cop_operating, hp.available,
                        max(source-hp.source_used_MW, 0.0), storage.charge_MW,
                        storage.discharge_MW, storage.energy_start_MWh,
                        storage.energy_after_loss_MWh, storage.energy_next_MWh,
                        storage.standing_loss_MWh, storage.charge_loss_MWh,
                        storage.discharge_loss_MWh, boiler, unmet,
                        direct+storage.discharge_MW+boiler)
