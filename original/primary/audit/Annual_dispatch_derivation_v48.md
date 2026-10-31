# Source-constrained annual dispatch — v48

These are deductions from versioned project code and explicit synthetic
engineering assumptions, not equations or calibration claimed from a paper.
The accepted actual Stateflow model remains v42. The new annual MATLAB
controller intentionally retains legacy loss-first TES to isolate the HP repair.

For one held interval of duration dt hours, demand D, source S, HP capacity H,
and charge/discharge limits Lc/Ld have units MW. Inventory E and capacity K
have units MWh; efficiencies etaC/etaD and loss fraction ell*dt are dimensionless.
The admitted TES domain is 0<=ell*dt<=1, 0<etaC,etaD<=1, E in [0,K].

    retained = E*(1-ell*dt)
    chargeBound = min(Lc, (K-retained)/(etaC*dt))
    request R = D + chargeBound

HP step v40 chooses the largest Q<=min(R,H) satisfying its source constraint
and operating cutoff. Reservoir proxy temperatures give C0=min(Cmax,
etaCarnot*(Tsink+273.15)/(Tsink-Tsource)); these are not refrigerant saturation
temperatures or a measured equipment map. Operating COP is C(Q)=a+bQ where
a=C0*(1-r), b=C0*r/H, r in [0,1). No upward COP clamp is used. Cm>1 is an
operating cutoff. If C0<Cm, or min(R,H)<Qmin, or S<F(Qmin), the HP stays off.
For r>0, Qmin=max(0,(Cm-a)/b); for r=0 it is zero when C0>=Cm.

    F(Q) = Q - Q/C(Q) = evaporator extraction
    F'(Q) = 1 - a/(a+bQ)^2 > 0 on the admissible operating interval
    b Q^2 + (a-1-bS) Q - aS = 0

The verifier uses a 60-digit Decimal positive quadratic root and the cutoff
domain, independently of production bisection. For B=a-1-bS>=0 the stable
root is 2*a*S/(B+sqrt(B^2+4*b*a*S)); for B<0 it is
(-B+sqrt(B^2+4*b*a*S))/(2*b). At b=0 the root is S*a/(a-1).
The maximum is min(R,H,root), after verifying the admissible lower endpoint.
Zero source/request/capacity gives zero ports and undefined operating COP.

    direct = min(Q,D)
    charge = min(max(0,Q-D), Lc, (K-retained)/(etaC*dt))
    discharge = min(max(0,D-Q), Ld, retained*etaD/dt)
    E_next = retained + etaC*charge*dt - discharge*dt/etaD
    gas = min(max(0,D-direct-discharge), boilerCapacity)
    unmet = max(0,D-direct-discharge-gas)

At K=0 both TES ports are zero. Since request includes only admissible charge,
all HP output is allocated: Q=direct+charge. Charge and discharge are exclusive.
This annual policy has no HP latch/dwell, temperature cutoff TES inventory,
continuous active-port heat loss, hydraulic model or solver-clock event claim.

Standing loss is E-retained. TES conversion loss is
[(1-etaC)*charge+(1/etaD-1)*discharge]*dt. The independent first law uses
actual delivered heat (direct+discharge+gas); unmet is never energy delivered:

    E + (sourceUsed + electric + gas - delivered)*dt
      - E_next - standingLoss - conversionLoss = 0.

Fresh whole-year trajectories, not static v47 capability credits, determine
delivered heat, gas, unmet and electricity. Explicit actual ports enter v45/v46
energy and equal-delivered-service comparison. Initial/terminal inventory value,
source provenance, auxiliaries, CAPEX and physical calibration remain unspecified.
Zero penalty is compared with preserved v13 only in a matched valid domain.
The deliberate cutoff fixture demonstrates that upward-clamped legacy COP and
the new operating cutoff can give different outputs; broad legacy compatibility
is not asserted. Matched no-storage cases are executed in saved actual v42.
