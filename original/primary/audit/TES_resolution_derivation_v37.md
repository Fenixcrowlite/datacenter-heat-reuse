# v37 numerical-domain derivation and supported-resolution handoff

This is an engineering audit of preserved saved v36, not a corrected model,
equipment calibration, paper equation replication or physical validation.
All plant and stress-fixture values are assumptions. Independent QA means
independent algorithms/artifacts in the same agent, not a second human/agent.

## Persistent clock: local and cumulative error are different

For an unchanged latch with durations d_i in physical hours, the exact elapsed
age is A_n=A_0+sum(d_i). Binary64 updates instead compute
a_i=fl(a_(i-1)+d_i). Consequently
a_n-A_n=sum(e_i), where e_i=a_i-(a_(i-1)+d_i).
A positive representable increment establishes progress; it does not bound
the cumulative sum of rounding errors. A per-operation budget also does not
establish a global budget. Under round-to-nearest with finite normal results,
each addition contributes at most approximately half the local floating-point
spacing; a conservative accumulation budget depends on the number of updates.

At age 1e6 h, spacing is 2^-33 h. Adding the represented 1e-10 h rounds each
increment to that spacing. After 1024 updates, the Decimal reference using
exact binary64 inputs gives bias 1.6809289550781246e-8 h, or about 60.51
microseconds. The helper's local 64-spacing allowance remains
7.450580596923828e-9 h; its configured maximum is 1e-8 h (36 microseconds).
The experiment uses the latter as a cumulative comparison budget. **v36's
existing helper only promises a local allowance; it contains no global error
accumulator.** This finding exposes an unclosed cumulative-accuracy domain,
not proof that a documented universal global guarantee was made or that a
clean Stateflow dwell transition occurred early. The stressed age corresponds
to over a century and is not a deployment recommendation.

The exact physical ODE in these fixtures is E'=0, or E'=-demand/etaD when
demand changes with no available source, no standing losses and no backup.
Thus E_n=E_0-sum(demand_i*d_i/etaD), independently checkable without the
production event planner. The HP remains OFF; the inherited minimum dwell
does not bind at this old age. Clock error persists for both held and changing
demand and depends on partition count despite equal physical horizons.

Candidate repair: carry a compensation/residual in persistent clock memory,
including in the host plan and actual HP supervisor; clear both parts on a
latch reset. Derive its guard and monitor semantics before implementation.
Alternatively explicitly saturate a dwell timer after eligibility and give
it saturated-timer semantics, without claiming it reports physical elapsed
age. Simply relaxing the hour tolerance is not a repair. Either design needs
an exact-input cumulative oracle, transition/reset cases, and a declared
supported duration/age domain. This run implements neither candidate.

## Restart/capacity separation

Let epsilon_E=64*eps(max(1,capacity)) MWh. The current restart eligibility
tests E<=restart+epsilon_E. With E=capacity and
0<capacity-restart<=epsilon_E, an OFF controller becomes eligible at capacity.
For positive charging net power P and zero loss, the subsequent capacity
time t=(capacity-E)/P is zero. The planner raises EventProgress. In the exact
policy for the tested lossless, zero-demand case, E stays at capacity and the
HP should remain OFF forever because capacity>restart.

Strict ordering of capacity>restart>cutoff is therefore insufficient for
this numerical implementation. A conservative sufficient separation for
distinct tolerance neighborhoods is
capacity-restart>2*epsilon_E and restart-cutoff>2*epsilon_E.
The first epsilon accounts for energy snapping and the second for guard
extension. This is a proposed numerical domain, not a calibrated physical
hysteresis width or a proved complete domain for every event scenario.
Reject unsupported bands before event construction using an explicit
resolution-domain diagnostic, then test the allowed boundary and overlap
with capacity/cutoff snapping. Current capacity-gap probes isolate one
endpoint; cutoff overlap remains to be executed in the repair.

## Heat-pump overflow: normalize before multiplying

The inherited screening law is C(Q)=N(1-p)+N*p*Q/Qmax. It is an engineering
assumption, not an equipment curve. Current code first forms b=N*p/Qmax
and then evaluates a+b*Q. Finite physical inputs can produce infinite b
although the dimensionless Q/Qmax lies in [0,1] and the final COP is finite.
At N=4, p=.3 and Q=Qmax=1e-309 MW, b overflows but exact C=4.
The host component returns available=true, COP=Inf and electricity zero.
The actual saved Stateflow COP gate rejects it; **no invalid simulation
result is accepted or delivered as a successful plant response.**

Use normalized load r=Q/Qmax, evaluated after bounding Q<=Qmax, and
C(r)=N*(1-p+p*r). For p>0 the minimum-load fraction is
rmin=max(0,(Cmin/N-(1-p))/p); for p=0 the COP is constant.
Test the source law Qev=Q*(1-1/C) on the admissible interval with C>=Cmin>1.
Bound the normalized search interval with min(request,Qmax)/Qmax, avoiding
an unbounded request/Qmax division. Check every finite operating result and
explicitly reject unsupported underflow/overflow domains rather than returning
available=true with a nonfinite COP. A zero-capacity OFF case remains separate.
The normalized oracle in v37 verifies full-load COP and finite component
electricity/source flows including the subnormal boundary; it does not yet
validate a normalized production solver over arbitrary requests/source limits.

## Verified evidence provenance

MathWorks' primary software documentation defines spacing and describes
finite precision and rounding accumulation: [eps](https://www.mathworks.com/help/matlab/ref/double.eps.html)
and [Floating-Point Numbers](https://www.mathworks.com/help/matlab/matlab_prog/floating-point-numbers.html).
Full HTML text was opened on 2026-10-10. The live pages identify R2026b;
the executed local MATLAB is R2026a Update 5. The derivations above are our
engineering mathematics, not equations extracted from a primary heat-reuse
article. No new research-paper signoff, equipment value or experimental
physical result was adopted. The earlier full-primary signoffs remain 0/31.
