"""A45 heat-pump source-side compressor ramp. Synthetic, no hardware I/O."""
from __future__ import annotations
import math
import sys
from pathlib import Path

A42 = Path(__file__).resolve().parent.parent / "AUTONOMOUS_RUN_20261026_1850_A42_COUPLED_FAILSAFE"
sys.path.insert(0, str(A42))
import coupled_a42 as base


def step_capacity(previous_W, target_W, dt_s, tau_s):
    """Exact ZOH first-order lag of *available* HP evaporator extraction."""
    if any(not math.isfinite(x) for x in (previous_W, target_W, dt_s, tau_s)):
        raise ValueError("NONFINITE_COMPRESSOR")
    if previous_W < 0 or target_W < 0 or dt_s <= 0 or tau_s < 0:
        raise ValueError("INVALID_COMPRESSOR")
    alpha = 1.0 if tau_s == 0 else -math.expm1(-dt_s / tau_s)
    return max(0.0, previous_W + alpha * (target_W - previous_W))


def dispatch_limited(row, qit, E, T, reject_cap_W, hp_source_cap_W):
    """Recompute all HP/TES/user/IT balances with capped evaporator extraction."""
    if not math.isfinite(hp_source_cap_W) or hp_source_cap_W < 0:
        raise ValueError("INVALID_HP_CAP")
    if any(not math.isfinite(x) for x in (qit, E, T, reject_cap_W)):
        raise ValueError("NONFINITE_STATE")
    if not 0 <= qit <= row["qdc"] + 1e-7 or not 0 <= E <= base.E_MAX + 1e-4 or reject_cap_W < 0:
        raise ValueError("INVALID_STATE")
    hx = min(row["hx"], qit)
    leak = min(row["leak"], max(0.0, qit - hx))
    available = max(0.0, qit - hx - leak)
    demand = row["qpool"] + row["qdh"]
    loss = .002 * E / 86400.0
    dis_cap = max(0.0, (E - base.DT * loss) * .91 / base.DT)
    discharge = min(row["qdis"], demand, dis_cap)
    room = max(0.0, (base.E_MAX - E + base.DT * (discharge / .91 + loss)) / (base.DT * .93))
    charge_req = min(row["qcharge"], room)
    need = max(0.0, demand - discharge)
    cop = base.cop_proxy(T)
    source_target = min(available, (need + charge_req) * (cop - 1) / cop)
    source = min(source_target, hp_source_cap_W)
    electric = source / (cop - 1)
    condenser = source + electric
    served_hp = min(need, condenser)
    charge = min(charge_req, max(0.0, condenser - served_hp))
    served = discharge + served_hp
    unmet = max(0.0, demand - served)
    E_next = max(0.0, min(base.E_MAX, E + base.DT * (.93 * charge - discharge / .91 - loss)))
    required = max(0.0, qit - hx - leak - source)
    rejected = min(required, reject_cap_W)
    unhandled = max(0.0, required - rejected)
    return dict(qit_W=qit, hx_W=hx, leak_W=leak, hp_source_W=source,
        hp_electric_W=electric, hp_condenser_W=condenser, cop_proxy=cop,
        pool_dh_demand_W=demand, pool_dh_served_W=served,
        pool_dh_unmet_W=unmet, tes_charge_W=charge, tes_discharge_W=discharge,
        tes_loss_W=loss, E_next_J=E_next, required_reject_W=required,
        reject_W=rejected, unhandled_W=unhandled,
        it_balance_W=qit-hx-leak-source-rejected-unhandled,
        hp_balance_W=condenser-source-electric,
        user_balance_W=demand-served-unmet,
        tes_balance_J=E_next-E-base.DT*(.93*charge-discharge/.91-loss),
        hp_source_target_W=source_target, hp_source_cap_W=hp_source_cap_W)
