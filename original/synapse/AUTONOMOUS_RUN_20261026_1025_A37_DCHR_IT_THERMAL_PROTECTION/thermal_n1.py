"""A37: isolated synthetic N-1 reject / IT thermal inertia / curtailment replay.

Source-backed constants (v07): dt=900s, C_IT=8e6 J/K, passive=2000*(T-30) W,
alarm threshold 42C, reject A/B=180/150 kW (scenario values, NOT certified).
Assumptions: immediate 1:1 decrease of reject demand per watt of shed IT heat;
fixed A36 other thermal branches; shedding capacity/ramp-up are sensitivity inputs; release of shedding is instant.
No physical safety claim, equipment control, TES dynamics or release approval.
"""
from dataclasses import dataclass
import math

DT_S = 900.0
C_IT_J_K = 8e6
PASSIVE_W_K = 2000.0
T_FLOOR_C = 30.0
T_ALARM_C = 42.0
REJECT_A_W = 180000.0
REJECT_B_W = 150000.0
EPS = 1e-7

def nonnegative(value, name):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid {name}: {value}")
    return value

@dataclass(frozen=True)
class Policy:
    name: str
    max_shed_fraction: float
    ramp_W_per_step: float | None = None
    def __post_init__(self):
        if not (0 <= self.max_shed_fraction <= 1) or not math.isfinite(self.max_shed_fraction):
            raise ValueError("invalid max_shed_fraction")
        if self.ramp_W_per_step is not None:
            nonnegative(self.ramp_W_per_step, "ramp_W_per_step")

POLICIES = {
    "no_shed": Policy("no_shed", 0.0),
    "ideal_40pct": Policy("ideal_40pct", 0.40),
    "ramp15k_40pct": Policy("ramp15k_40pct", 0.40, 15000.0),
}
CAPACITIES = {
    "both": REJECT_A_W + REJECT_B_W,
    "main_only": REJECT_A_W,
    "backup_only": REJECT_B_W,
    "neither": 0.0,
}

def advance(required_W, q_dc_W, capacity_W, T_C, previous_shed_W, policy: Policy):
    required = nonnegative(required_W, "required_W")
    q_dc = nonnegative(q_dc_W, "q_dc_W")
    cap = nonnegative(capacity_W, "capacity_W")
    prev = nonnegative(previous_shed_W, "previous_shed_W")
    if not math.isfinite(T_C) or T_C < T_FLOOR_C - EPS:
        raise ValueError("invalid T_C")
    if prev > q_dc + EPS:
        raise ValueError("previous shedding exceeds current DC heat")
    # Thermal source shedding is only a scenario, never a command to real IT.
    target = min(max(0.0, required - cap), policy.max_shed_fraction * q_dc, required)
    if policy.ramp_W_per_step is None:
        shed = target
    else:
        ramp = policy.ramp_W_per_step
        shed = min(target, prev + ramp)  # ramp-up only; recovery instant under frozen A36 branches
    reject_needed = required - shed
    reject = min(reject_needed, cap)
    unhandled = max(0.0, reject_needed - reject)
    passive = max(0.0, PASSIVE_W_K * (T_C - T_FLOOR_C))
    T_next = max(T_FLOOR_C, T_C + DT_S * (unhandled - passive) / C_IT_J_K)
    residual = required - shed - reject - unhandled
    if abs(residual) > EPS or shed > q_dc + EPS:
        raise AssertionError("energy accounting or shedding bound failed")
    return {
        "shed_W": shed, "Q_DC_after_shed_W": q_dc - shed,
        "reject_required_after_shed_W": reject_needed,
        "reject_actual_W": reject, "unhandled_W": unhandled,
        "passive_W": passive, "T_IT_start_C": T_C,
        "T_IT_next_C": T_next, "alarm_next": int(T_next >= T_ALARM_C),
        "balance_residual_W": residual,
    }

def simulate(rows, policy: Policy, fault_capacity_W: float, start_h=24.0):
    cap_fault = nonnegative(fault_capacity_W, "fault_capacity_W")
    t = T_FLOOR_C
    prev_shed = 0.0
    output = []
    last_hour = None
    for row in rows:
        hour = float(row["cas_h"])
        if not math.isfinite(hour):
            raise ValueError("invalid time")
        if last_hour is not None and abs(hour - last_hour - 0.25) > 1e-8:
            raise ValueError("non-15-minute or unordered samples")
        last_hour = hour
        if nonnegative(row["Q_unhandled_W"], "baseline unhandled") > EPS:
            raise ValueError("baseline unhandled heat requires separate accounting")
        active = hour >= start_h
        cap = cap_fault if active else CAPACITIES["both"]
        current_policy = policy if active else POLICIES["no_shed"]
        result = advance(row["Q_reject_required_W"], row["Q_DC_eff_W"],
                         cap, t, prev_shed, current_policy)
        output.append({"cas_h": hour, "fault_capacity_W": cap, **result})
        t = result["T_IT_next_C"]
        prev_shed = result["shed_W"]
    return output
