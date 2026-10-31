"""IASE equation-domain diagnostic; not an adopted/calibrated DC component.

Sintong (2023), printed/PDF p30 Eq15-16. The flow-function interpretation
has alpha=epsilon*(1+r)/2, r=m_OA/m_RA for equal constant air cp.
The optional literal_r_product branch preserves an unresolved typography
alternative; it is NOT a verified author implementation.

For positive sensible capacity rates and unequal inlet temperatures,
Q=C_RA*alpha*(T_RA-T_OA), T_OA,out=T_OA+Q/C_OA. Both outlets
are in the inlet envelope iff 0<=alpha<=min(1,C_OA/C_RA).
This endpoint/energy gate does not identify exchanger geometry or UA.
"""
from dataclasses import dataclass
import math
from numbers import Real


def _scalar(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real scalar")
    return float(value)


def _temperature(value, name):
    value = _scalar(value, name)
    if value <= -273.15:
        raise ValueError(f"{name} must exceed absolute zero")
    return value


def _positive(value, name):
    value = _scalar(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def epsilon_limit(flow_ratio, interpretation="flow_function"):
    """Endpoint-energy bound under equal cp; not a fitted epsilon curve."""
    r = _positive(flow_ratio, "flow_ratio")
    if interpretation not in ("flow_function", "literal_r_product"):
        raise ValueError("unsupported Eq15 interpretation")
    limit = 2 * min(1.0, r) / (1 + r)
    return limit if interpretation == "flow_function" else limit / r


@dataclass(frozen=True)
class IaseDiagnostic:
    flow_ratio: float
    epsilon_limit: float
    alpha: float
    return_out_C: float
    outdoor_out_C: float
    heat_from_return_W: float
    max_passive_heat_magnitude_W: float
    return_envelope_pass: bool
    outdoor_envelope_pass: bool
    endpoint_energy_pass: bool
    equal_inlets: bool


def source_diagnostic(return_C, outdoor_C, return_kg_s, outdoor_kg_s,
                      epsilon, cp_J_kgK=1005.0, interpretation="flow_function"):
    """Evaluate source algebra without clipping impossible predictions.

    epsilon is a diagnostic nonnegative coefficient; no standard-effectiveness
    interpretation is attributed to the thesis. Zero-flow source evaluation is
    undefined here; use the independently defined passive reference to bypass.
    """
    tr = _temperature(return_C, "return_C")
    to = _temperature(outdoor_C, "outdoor_C")
    mr = _positive(return_kg_s, "return_kg_s")
    mo = _positive(outdoor_kg_s, "outdoor_kg_s")
    cp = _positive(cp_J_kgK, "cp_J_kgK")
    e = _scalar(epsilon, "epsilon")
    if e < 0:
        raise ValueError("epsilon must be nonnegative")
    r = mo / mr
    bound = epsilon_limit(r, interpretation)
    alpha = e * (1 + r) / 2
    if interpretation == "literal_r_product":
        alpha *= r
    q = mr * cp * alpha * (tr - to)
    tro = tr + alpha * (to - tr)
    too = to + alpha / r * (tr - to)
    if not all(math.isfinite(x) for x in (r, alpha, q, tro, too)):
        raise ValueError("nonfinite diagnostic prediction")
    equal = tr == to
    # Classify with dimensionless coefficients, not rounded temperatures.
    # Equal-temperature endpoints cannot identify a coefficient bound.
    ra_pass = equal or 0 <= alpha <= 1
    oa_pass = equal or 0 <= alpha <= r
    return IaseDiagnostic(r, bound, alpha, tro, too, q,
                          min(mr, mo) * cp * abs(tr - to),
                          ra_pass, oa_pass, ra_pass and oa_pass, equal)


def passive_reference(return_C, outdoor_C, return_kg_s, outdoor_kg_s,
                      epsilon_Q, cp_return_J_kgK=1005.0, cp_outdoor_J_kgK=1005.0):
    """Independent sensible-HX endpoint reference, Q=epsilon_Q*Cmin*dT.

    This is an engineering definition, NOT a transcription or correction of
    Park/Sintong. Unequal cp is allowed; zero outdoor flow means bypass.
    Signed Q>0 removes heat from RA. Fan work, humidity, leakage, frost,
    pressure loss, geometry and the free-cooling controller are excluded.
    """
    tr = _temperature(return_C, "return_C")
    to = _temperature(outdoor_C, "outdoor_C")
    mr = _positive(return_kg_s, "return_kg_s")
    mo = _scalar(outdoor_kg_s, "outdoor_kg_s")
    cr = mr * _positive(cp_return_J_kgK, "cp_return_J_kgK")
    co = mo * _positive(cp_outdoor_J_kgK, "cp_outdoor_J_kgK")
    e = _scalar(epsilon_Q, "epsilon_Q")
    if mo < 0 or not 0 <= e <= 1:
        raise ValueError("outdoor flow must be nonnegative and epsilon_Q in [0,1]")
    q = e * min(cr, co) * (tr - to)
    tro = tr - q / cr
    too = to + q / co if co else to
    if not all(math.isfinite(x) for x in (cr, co, q, tro, too)):
        raise ValueError("nonfinite passive-reference prediction")
    return {"return_out_C": tro, "outdoor_out_C": too,
            "heat_from_return_W": q, "C_return_W_K": cr, "C_outdoor_W_K": co}
