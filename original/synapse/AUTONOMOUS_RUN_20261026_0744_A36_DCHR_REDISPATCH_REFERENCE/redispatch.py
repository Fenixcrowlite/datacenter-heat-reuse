"""Conservative instantaneous heat redispatch for synthetic DCHR v08 CSV.

NOT a Stateflow controller, hardware command, calibrated heat-pump model,
or dynamic TES/pool/pipe simulation. No assumed reject capacity by default.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

REQUIRED = (
    "Q_DC_eff_W", "Q_HX_phys_W", "Q_HP_source_W", "Q_reject_physical_W",
    "Q_HP_pool_W", "Q_HP_DH_W", "Q_HP_charge_W",
    "Q_TES_discharge_W", "P_HP_W", "Q_pool_phys_W", "Q_DH_W",
    "Q_pool_req_W", "Q_DH_req_W", "Q_leak_W", "Q_unhandled_W",
)
TOL = 1e-5

@dataclass(frozen=True)
class Caps:
    pool_W: float | None = None
    dh_W: float | None = None
    reject_W: float | None = None  # hypothetical until certified

    def __post_init__(self):
        for name in ("pool_W", "dh_W", "reject_W"):
            value = getattr(self, name)
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"invalid {name}: {value!r}")

def _v(row, key):
    value = float(row[key])
    if not math.isfinite(value) or value < -TOL:
        raise ValueError(f"invalid {key}: {value}")
    return max(0.0, value)

def _near(a, b, what):
    if abs(a - b) > TOL * max(1.0, abs(a), abs(b)):
        raise ValueError(f"baseline {what} not conserved: {a} vs {b}")

def dispatch(row, caps: Caps = Caps()):
    """Rebalance one interval, preserving baseline DH/TES charging and fixed COP.

    Baseline instantaneous first-law closure is checked before redispatch.
    Released DC source heat is routed to REJECT; cap excess is unhandled/unsafe.
    TES discharge is curtailed with DH, but TES state is NOT propagated.
    """
    b = {k: _v(row, k) for k in REQUIRED}
    hx, hp_pool = b["Q_HX_phys_W"], b["Q_HP_pool_W"]
    hp_dh, hp_charge = b["Q_HP_DH_W"], b["Q_HP_charge_W"]
    tes = b["Q_TES_discharge_W"]
    q_dc, p_hp = b["Q_DC_eff_W"], b["P_HP_W"]
    condenser = hp_pool + hp_dh + hp_charge
    _near(hx + hp_pool, b["Q_pool_phys_W"], "pool")
    _near(hp_dh + tes, b["Q_DH_W"], "DH")
    _near(condenser, b["Q_HP_source_W"] + p_hp, "HP")
    _near(q_dc, hx + b["Q_HP_source_W"] + b["Q_reject_physical_W"]
          + b["Q_leak_W"] + b["Q_unhandled_W"], "DC")
    if condenser > TOL and p_hp >= condenser - TOL:
        raise ValueError("baseline HP has no positive evaporator heat")
    if condenser <= TOL and p_hp > TOL:
        raise ValueError("baseline compressor power without heat")

    pool_cap = b["Q_pool_phys_W"] if caps.pool_W is None else min(
        b["Q_pool_phys_W"], caps.pool_W)
    dh_cap = b["Q_DH_W"] if caps.dh_W is None else min(
        b["Q_DH_W"], caps.dh_W)
    # Direct HX takes priority over HP for reduced pool demand.
    new_hx = min(hx, pool_cap)
    new_hp_pool = min(hp_pool, max(0.0, pool_cap - new_hx))
    # HP takes priority over TES for curtailed district heat.
    new_hp_dh = min(hp_dh, dh_cap)
    new_tes = min(tes, max(0.0, dh_cap - new_hp_dh))
    new_condenser = new_hp_pool + new_hp_dh + hp_charge
    # Fixed interval-specific condenser COP is a PROXY, not an equipment curve.
    new_p = p_hp * (new_condenser / condenser) if condenser > TOL else 0.0
    new_source = new_condenser - new_p
    if new_source < -TOL:
        raise ValueError("negative HP source")
    new_source = max(0.0, new_source)
    reject_required = q_dc - new_hx - new_source - b["Q_leak_W"] - b["Q_unhandled_W"]
    if reject_required < -TOL:
        raise ValueError("new dispatch exceeds DC source")
    reject_required = max(0.0, reject_required)
    reject_actual = (reject_required if caps.reject_W is None
                     else min(reject_required, caps.reject_W))
    excess = max(0.0, reject_required - reject_actual)
    unhandled = b["Q_unhandled_W"] + excess
    q_pool = new_hx + new_hp_pool
    q_dh = new_hp_dh + new_tes
    residuals = {
        "DC_W": q_dc - new_hx - new_source - reject_actual
                - b["Q_leak_W"] - unhandled,
        "HP_W": new_condenser - new_source - new_p,
        "pool_W": q_pool - new_hx - new_hp_pool,
        "DH_W": q_dh - new_hp_dh - new_tes,
    }
    if max(abs(v) for v in residuals.values()) > TOL:
        raise AssertionError(f"redispatch failed conservation: {residuals}")
    if excess > TOL or b["Q_unhandled_W"] > TOL:
        status = "UNSAFE_UNHANDLED_HEAT"
    elif caps.reject_W is None:
        status = "REJECT_CAPACITY_UNKNOWN"
    else:
        status = "WITHIN_ASSUMED_REJECT_CAP"
    return {
        "Q_pool_W": q_pool, "Q_DH_W": q_dh,
        "Q_HX_W": new_hx, "Q_HP_pool_W": new_hp_pool,
        "Q_HP_DH_W": new_hp_dh, "Q_HP_charge_W": hp_charge,
        "Q_TES_discharge_W": new_tes,
        "Q_HP_source_W": new_source, "P_HP_proxy_W": new_p,
        "Q_reject_required_W": reject_required,
        "Q_reject_actual_W": reject_actual,
        "Q_unhandled_W": unhandled,
        "Q_pool_unmet_W": max(0.0, b["Q_pool_req_W"] - q_pool),
        "Q_DH_unmet_W": max(0.0, b["Q_DH_req_W"] - q_dh),
        "COP_baseline_effective": condenser / p_hp if p_hp > TOL else None,
        "status": status,
        "residuals_W": residuals,
        "TES_state_validated": False,
        "electric_savings_validated": False,
    }

def apply_after(row, caps, start_hour):
    """Use original baseline until start_hour; do not alter input."""
    hour = float(row["cas_h"])
    if not math.isfinite(hour):
        raise ValueError("invalid cas_h")
    return dispatch(row, Caps() if hour < start_hour else caps)
