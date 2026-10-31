# v38 numerical-domain repair: engineering derivation

This derivation supports the executable Stateflow repair and its finite test
domain. It is engineering mathematics, not a paper equation or an equipment
curve. All temperatures, rates, efficiencies, capacities and control settings
in the fixtures are assumptions. No new primary article was verified or signed
off; the research checkpoint remains 0/31 full-primary signoffs. The prior
primary MathWorks evidence and its provenance remain in
`audit/TES_resolution_derivation_v37.md`.

## Normalize the HP law before evaluating it

Let N be the screened nominal COP, p the part-load penalty and Qmax the finite
positive HP output limit. After enforcing 0 <= Q <= min(request,Qmax), set
r=Q/Qmax. The assumed screening law is

    C(r) = N(1-p+p*r),   Qev = Q*(1-1/C(r)),   W = Q/C(r).

The interval has 0 <= r <= 1. The code therefore never forms N*p/Qmax,
which overflowed in v36 even when the final COP was finite. The minimum
admissible load fraction is max(0,(Cmin/N-(1-p))/p) for p>0; the p=0 case
has constant COP. N<Cmin and demand/source/capacity zero have explicit OFF
conventions. Cmin is an operating cutoff, not an upward efficiency clamp.

On the admissible interval, with a=N(1-p) >= 0 and b=N*p >= 0,
dQev/dQ = 1-a/C^2 > 0 for C>1: a<=C, hence a/C^2<=1/C<1.
Production retains an output-space feasible-endpoint bisection with 80
iterations; its COP evaluation uses normalized load. The independent reviewer
uses a different algorithm: write s=source/Qmax, then solve

    b*r^2 + (a-1-s*b)*r - s*a = 0.

For B=a-1-s*b >=0, the positive root is
2*s*a/(B+sqrt(B^2+4*b*s*a)); for B<0 use
(-B+sqrt(B^2+4*b*s*a))/(2*b). For b=0 use s*a/(a-1).
The independent computation uses 110-digit Decimal with exact binary64 inputs,
then bounds the result by the minimum COP point and the request/capacity.
The comparison tolerance scales with power ulps, including subnormal powers;
an ordinary absolute MW tolerance would make the tiny-power checks vacuous.

At Q=Qmax=1e-309 MW with N=4 and p=.3, normalized C=4 and W=Q/4 are
representable. Both the actual saved plant and component now execute this
fixture. An even smaller minimum-subnormal output cannot represent Q/4:
the component rejects with HPResolution instead of accepting zero electricity
at positive output. Underflow of a positive minimum operating output also
rejects explicitly. This does not prove every finite dynamic range or COP
threshold has a complete solver domain; the 80-iteration search and near-cutoff
classification retain a targeted audit handoff.

## Require separable numerical energy bands

For epsilon_E=64*eps(max(1,capacity)) MWh, endpoint snapping and restart guard
extension each use epsilon_E. Distinct neighborhoods are conservatively
supported by

    capacity - restart > 2*epsilon_E,
    restart - cutoff > 2*epsilon_E,
    cutoff > 2*epsilon_E.

The last condition separates the cutoff from the zero-energy endpoint in this
version's conservative domain. It intentionally excludes zero/near-zero cutoff
configurations, without claiming these are physically impossible. These are
numerical admissibility conditions, not equipment hysteresis recommendations.
The host planner checks them before constructing event segments and returns a
BandResolution diagnostic. Existing strict physical ordering alone was
insufficient. Capacity gaps of 1/32/64/65/128 ulps and cutoff/restart gaps of
1/64/128 ulps now reject explicitly; 129-ulp cutoff/restart and 256-ulp capacity
controls execute. The original v37 EventProgress counterexamples are preserved.

## Carry a two-part clock and a cumulative error bound

Clock memory is [latch, high_h, low_h, bound_h]. Initial high+low is interpreted
as the supplied elapsed-age seed; bound encloses prior error relative to that
seed. High is the binary64 reported clock; low is a signed residual. All clock
quantities are in hours, independent of MW/MWh tolerances.

TwoSum(a,b) returns a rounded sum and its exact addition residual within the
supported finite round-to-nearest domain. For a duration d, production computes

    (s,e) = TwoSum(high,d)
    (r,discard) = TwoSum(low,e)
    (high_new,low_new) = TwoSum(s,r).

Thus the new expansion equals the old expansion+d-discard. Add abs(discard)
to the accumulated bound, with an additional upward spacing allowance whenever
that term is nonzero. The clock rejects if abs(low)+bound exceeds 1e-8 h,
or if the inherited 64-spacing physical-hour resolution limit exceeds 1e-8 h.
The helper also rejects a nonfinite clock, negative high/bound and an
unnormalized residual larger than eps(max(1,high)). This is an explicitly
bounded representation, not an unlimited-age/count promise. Adversarial
initial residuals and cancellation at the numerical domain edges remain a
specific follow-up audit; no universal initial-seed validity is established.

At a latch transition both parts and the bound reset to zero. Planner, saved
Stateflow HP supervisor and runtime monitor carry the same representation;
the independent QA recomputes elapsed time using exact-input Decimal sums,
without calling or translating the production update. Unused zero-duration
slots preserve the clock rather than counting iterator ticks.

Dwell eligibility compares (high-dwell)+low >= 0, with no positive time
tolerance added to authorize a transition. Remaining dwell time is
(dwell-high)-low. These comparisons use the estimated compensated age, not a
claim of exact event ordering under every possible nonzero accumulated bound.
Runtime bounds and the independent transition tests scope their accuracy.
The negative-residual boundary fixture holds the HP OFF for the remaining
tiny positive duration; zero/positive residual fixtures can restart immediately.
Capacity/input safety overrides of ON dwell remain inherited.

Plan rows 19/20 carry start/end residuals and 21/22 start/end bounds. Saved
clock memory carries all four values; public 28-field segment traces retain
reported high ages. The gate verifies residual continuity, reset, helper output
and final supervisor memory. Exact-input QA also checks the expanded clock
against its reported error bound, across held and changing inputs.

## Physical equation and implementation boundary

For held ports during a segment, TES obeys E'=etaC*Qc-Qd/etaD-lambda*E.
With P=etaC*Qc-Qd/etaD, exact Eend=Estart*exp(-lambda*t)
+P*(1-exp(-lambda*t))/lambda, with the lambda=0 limit Estart+P*t.
Independent Decimal exponential integration verifies every positive segment,
standing/charge/discharge losses and first-law closure. Dispatch references
remain the independently derived v34 equations and freshly executed saved v36.

Actual thermal and HP Stateflow charts execute in a 64-slot bounded iterator.
Physical event offsets occur analytically within a macro sample; they are not
solver-clock event scheduling. The HP/planner remains normal-mode host MATLAB.
Standalone generated-code deployment, hydraulics/stratification, startup losses,
equipment calibration, article replication and measured validation remain
untested. Stateflow license availability and actual chart execution are checked;
the empty ver('Stateflow') lookup is not replaced with an invented version.
