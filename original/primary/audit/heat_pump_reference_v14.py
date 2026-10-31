"""Independent heating-mode heat-pump kernel, v14 (engineering assumptions).

No paper or measured-system replication is claimed. Temperatures represent
isothermal reservoir temperatures; they are not inferred refrigerant states.
Power quantities are MW. Heating mode requires 0 < Tc < Th, in kelvin.

First law: Qh = Qe + W; heating COP C = Qh/W.
Reservoir entropy generation Qh/Th - Qe/Tc >= 0 implies
C <= Th/(Th-Tc). A minimum COP is an operating eligibility threshold,
never a thermodynamic correction that increases a predicted COP.

The assumed part-load curve is C(Q)=a+bQ, where
a=Cnom*(1-penalty), b=Cnom*penalty/capacity. The source boundary
Q-Q/C(Q)=S gives bQ^2+(a-1-Sb)Q-Sa=0. This module solves that
quadratic analytically, independently of the MATLAB bisection implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


def _scalar(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real scalar")
    return float(value)


@dataclass(frozen=True)
class HeatPumpParameters:
    capacity_MW: float = 12.0
    carnot_efficiency: float = 0.45
    cop_min: float = 2.2
    cop_max: float = 7.0
    part_load_penalty: float = 0.08
    backend: str = "carnot"
    poly_c0: float = 7.2
    poly_c1: float = -0.075
    poly_c2: float = 2.2e-4

    def __post_init__(self) -> None:
        for name in ("capacity_MW", "carnot_efficiency", "cop_min", "cop_max", "part_load_penalty"):
            _scalar(getattr(self, name), name)
        if self.capacity_MW < 0:
            raise ValueError("capacity_MW must be nonnegative")
        if not 0 < self.carnot_efficiency <= 1:
            raise ValueError("carnot_efficiency must be in (0,1]")
        if not 1 < self.cop_min <= self.cop_max:
            raise ValueError("COP bounds must satisfy 1 < cop_min <= cop_max")
        if not 0 <= self.part_load_penalty < 1:
            raise ValueError("part_load_penalty must be in [0,1)")
        if self.backend not in ("carnot", "lift_polynomial"):
            raise ValueError("unsupported heat-pump backend")
        if self.backend == "lift_polynomial":
            for name in ("poly_c0", "poly_c1", "poly_c2"):
                _scalar(getattr(self, name), name)


@dataclass(frozen=True)
class HeatPumpStep:
    cop_carnot: float
    cop_raw: float
    cop_nominal: float
    cop_operating: float
    heat_output_MW: float
    electric_MW: float
    source_used_MW: float
    available: bool
    lift_K: float


def heat_pump_step(
    q_source_MW: float, source_C: float, sink_C: float, request_MW: float,
    p: HeatPumpParameters = HeatPumpParameters(),
) -> HeatPumpStep:
    """Maximum continuously operable output up to request, capacity and source.

    Below-cutoff operating points are unavailable, with all powers zero and
    operating COP NaN. This kernel does not average cycling operation, model
    resistive heating, select direct recovery, or enforce minimum compressor load.
    """
    q_source_MW = _scalar(q_source_MW, "q_source_MW")
    request_MW = _scalar(request_MW, "request_MW")
    source_C = _scalar(source_C, "source_C")
    sink_C = _scalar(sink_C, "sink_C")
    if q_source_MW < 0 or request_MW < 0:
        raise ValueError("source and requested heat must be nonnegative")
    tc, th = source_C + 273.15, sink_C + 273.15
    lift = sink_C - source_C
    if tc <= 0 or th <= 0 or lift <= 0:
        raise ValueError("heating-mode domain requires 0 < Tc < Th in kelvin")
    carnot = th / lift
    if p.backend == "carnot":
        raw = p.carnot_efficiency * carnot
    else:
        raw = p.poly_c0 + p.poly_c1 * lift + p.poly_c2 * lift * lift
        if raw > carnot * (1.0 + 32.0 * math.ulp(1.0)):
            raise ValueError("polynomial prediction exceeds Carnot bound")
    if not math.isfinite(raw):
        raise ValueError("nonfinite predicted COP")
    nominal = min(raw, p.cop_max)

    def off() -> HeatPumpStep:
        return HeatPumpStep(carnot, raw, nominal, math.nan, 0.0, 0.0, 0.0, False, lift)

    if q_source_MW == 0 or request_MW == 0 or p.capacity_MW == 0 or nominal < p.cop_min:
        return off()
    a = nominal * (1.0 - p.part_load_penalty)
    b = nominal * p.part_load_penalty / p.capacity_MW
    qhi = min(request_MW, p.capacity_MW)
    qlo = max(0.0, (p.cop_min - a) / b) if b > 0 else 0.0
    if qhi < qlo:
        return off()
    cop_lo = a + b * qlo
    # qlo=0 may have a COP below one when the curve has a nonzero cutoff;
    # the cutoff definition above guarantees cop_lo>=cop_min whenever qlo>0.
    source_lo = qlo * (1.0 - 1.0 / cop_lo)
    if source_lo > q_source_MW:
        return off()
    if b == 0:
        source_boundary = q_source_MW * a / (a - 1.0)
    else:
        d = a - 1.0 - q_source_MW * b
        discriminant = math.sqrt(d * d + 4.0 * b * q_source_MW * a)
        # Rationalize when subtraction would lose precision.
        source_boundary = (2.0 * q_source_MW * a / (d + discriminant)
                           if d >= 0 else (-d + discriminant) / (2.0 * b))
    q = min(qhi, source_boundary)
    if q < qlo:
        if qlo - q > 1e-12 * max(1.0, p.capacity_MW):
            return off()
        q = qlo
    cop = a + b * q
    electric = q / cop
    source = q - electric
    return HeatPumpStep(carnot, raw, nominal, cop, q, electric, source, True, lift)
