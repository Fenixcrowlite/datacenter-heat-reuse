"""Additive interval-renewable compressor cap prototype, NOT integrated with Stateflow.
Engineering derivation: Horizon_renewal_derivation_v86.md. All numeric inputs synthetic.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
import hashlib
import hmac
import json

D = lambda x: Decimal(str(x))
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class Raw:
    A: Decimal
    floor: Decimal
    b: Decimal
    C: Decimal
    capacity: Decimal
    charge_port: Decimal
    thermal_cap: Decimal
    p_max: Decimal
    eta_charge: Decimal
    def validate(self):
        if min(self.A, self.floor, self.C) <= 0: raise ValueError("positive A, floor, C required")
        if min(self.capacity,self.charge_port,self.thermal_cap,self.p_max,self.eta_charge) < 0:
            raise ValueError("negative capacities, compressor rating or efficiency")
        if self.eta_charge > 1: raise ValueError("charge efficiency > 1")
    def fingerprint(self):
        return digest({k: str(v) for k,v in asdict(self).items()})

@dataclass(frozen=True)
class Retained:
    generation: int
    clock_upper: Decimal
    inventory_upper: Decimal
    latch: str
    on_age: Decimal
    off_age: Decimal
    source_energy: Decimal
    work_energy: Decimal
    loss_energy: Decimal
    event_memory_digest: str

@dataclass(frozen=True)
class Certificate:
    schema: int
    origin: str
    generation: int
    policy_hash: str
    clock_start_upper: str
    expiry_upper: str
    inventory_bound: str
    effective_heat_cap: str
    retained_hash: str
    signature: str

def payload(c: Certificate):
    d = asdict(c)
    d.pop("signature")
    return d

def renew(raw: Raw, state: Retained, horizon_upper: Decimal,
          origin: str, key: bytes, previous: Certificate | None = None) -> Certificate:
    raw.validate()
    if not key or not origin: raise ValueError("nonempty key and origin required")
    if horizon_upper <= 0: raise ValueError("positive renewal window required")
    if not (0 <= state.inventory_upper <= raw.capacity): raise ValueError("inventory upper outside tank")
    if state.clock_upper < 0: raise ValueError("invalid clock upper")
    if previous is not None:
        verify(previous, raw, key)
        if previous.origin != origin or state.generation != previous.generation:
            raise ValueError("origin or generation mismatch")
        if state.clock_upper < D(previous.expiry_upper):
            raise ValueError("early renewal: expiry unresolved")
    else:
        if state.generation != 0: raise ValueError("first certificate needs generation zero")

    # All quantities nonnegative. Ceiling yields an outward inventory bound;
    # downward rounding of the work-limiting cap avoids an optimistic certificate.
    with localcontext() as ctx:
        ctx.prec=80; ctx.rounding=ROUND_CEILING
        universal=raw.p_max*(1+raw.A/raw.floor)
        q_charge=max(D(0),min(raw.charge_port,raw.thermal_cap,universal))
        bound=min(raw.capacity,state.inventory_upper + raw.eta_charge*q_charge*horizon_upper)
        lift=max(raw.floor,raw.b + bound/raw.C)
        expiry=state.clock_upper+horizon_upper
    with localcontext() as ctx:
        ctx.prec=80; ctx.rounding=ROUND_FLOOR
        q_effective=min(raw.thermal_cap,raw.p_max*(1+raw.A/lift))
    next_generation=1 if previous is None else previous.generation+1
    fields=dict(schema=1,origin=origin,generation=next_generation,
        policy_hash=raw.fingerprint(), clock_start_upper=str(state.clock_upper),
        expiry_upper=str(expiry), inventory_bound=str(bound),
        effective_heat_cap=str(q_effective),
        retained_hash=digest({k:str(v) for k,v in asdict(state).items()}))
    signature=hmac.new(key,json.dumps(fields,sort_keys=True).encode(),hashlib.sha256).hexdigest()
    return Certificate(**fields,signature=signature)

def verify(cert: Certificate, raw: Raw, key: bytes):
    if cert.schema != 1 or cert.policy_hash != raw.fingerprint():
        raise ValueError("schema or raw policy changed")
    expected=hmac.new(key,json.dumps(payload(cert),sort_keys=True).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,cert.signature):
        raise ValueError("unauthenticated certificate")
    return True
