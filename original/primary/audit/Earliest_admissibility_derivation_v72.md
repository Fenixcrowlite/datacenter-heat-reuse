# Saved-v71 numerical admissibility audit v72

This checkpoint tests the preserved executable six-mode Stateflow model v71.
No new SLX or corrected-controller acceptance is claimed. All inputs are
synthetic engineering fixtures. No primary text, article equation, calibration
or measured performance is introduced.

## Passive inventory dependency

Held storage satisfies E' = B - lambda E. With B=0 its exact positive solution
is E(t)=E0 exp(-lambda t); every positive finite E0 stays strictly positive at
finite times. The production expression E + (-lambda E) t phi1(-lambda t)
uses the same uncertain E twice as independent interval operands.

Ignoring arithmetic-rounding enlargement to expose that dependency alone,
let E be [m-w,m+w], x=lambda dt and r=exp(-x). The expression gives midpoint
rm and radius (2-r)w, although the exact interval image has radius rw.
After n calls the exact center contracts as r^n but dependency width grows
as (2-r)^n once seeded by outward rounding. This derivation describes the
wrapping mechanism, not an exact recurrence for all production Taylor bounds.
The source/work computations additionally widen intervals.

For lambda=0.2/h and 1/h, dt=1h, E0=3, the original saved model rejects at
hours 91 and 23 respectively. Independent exact-binary closed exponential
evaluation gives positive inventory at both rejected boundaries. The actual
90/22-interval prefixes are separately executed, saved in original MAT,
reopened and exported to binary. The rejection is fail-closed, but blocks
otherwise admissible service and any broad long-horizon acceptance.

## Minimum ON dwell equality

Two exactly binary 0.125h holds total 0.25h. Starting ON age at zero and
disabling at that boundary meets minimum ON dwell 0.25h exactly. Persisted
outward additions retain [0.2499999999999999,0.2500000000000001]; the guard
requires its lower endpoint to reach 0.25 and therefore rejects equality.
An earlier disable is a correct refusal and a later disable is accepted.
The tested policy requires the inclusive equality, so this is an admissible
boundary lost by the numerical representation, not a demonstrated premature
physical transition.

## Source-limiter proof dependency

Let a=factor*(Te+273.15), lift=hot+condenserApproach-Te, and finite source
capacity S=sourceFlow*glide. The reduced model's source extraction is
q*a/(a+lift). Its conservative constant HP bound uses the coldest hot floor:
q <= S*(1+liftFloor/a). For a floor-branch held trajectory the exact source
rate at the host replay's selected binary q is independently evaluated with
exact Fraction operands and 160-digit Decimal divisions; it is below S.

Nevertheless, a separately widened source-rate upper endpoint exceeds the
capacity upper endpoint by several binary ulps. The monitor rejects an
inconclusive enclosure comparison, although the structural limiter relation
and exact selected power satisfy capacity. Three saved-model rejections are
retained: source-limited, rounded source/water tie, and just below the tie.
A water-limited and just-above-tie control accept.

A diagnostic host replay inserts return/capture immediately before the failing
source/nonnegative assertions into a versioned copy of the same kernel. It
provides branch operands only and is explicitly **not** saved-model execution
or independent QA. The actual saved model and embedded script remain unchanged.
Independent equations validate those captured operands. The generated copies,
failed diagnostic startup, corrected replay, MAT and binary exports are sealed.

## Correlated energy nonnegativity

For restart/stop temperature band 2^-42 K, the certified root-duration box is
wide relative to its tiny duration. Heat and source energy share the same
duration, but work=heat-source is evaluated with independent endpoint boxes.
The resulting work enclosure has a negative lower endpoint, while independent
closed root and analytic source integration show strictly positive work.
The guard `all(increment>=0)` treats a conservative enclosure's negative lower
endpoint as negative physical energy. This is an explicit refusal, not evidence
of actual negative compressor work. Auxiliary energy inherits that enclosure.
Wider tested bands 2^-10, 2^-20 and 2^-32 K accept.

## Resource and verification limits

The narrow-band zero-OFF-dwell budget control mathematically needs 23 positive
segments under the ideal exact limiter. Its actual saved-v71 rejection at the
16-segment budget is an explicit resource-domain limit; no rejected-call trace
or corrected acceptance is claimed. That ideal calculation is distinct from
the actual conservative binary limiter and only confirms the resource issue.

All accepted runs and valid prefixes receive independent exact-binary
Fraction/120/160-digit closed exp/log trajectory, source/work/service and
first-law enclosure checks. No production Taylor/bisection function is called
by the reviewer. Mutation controls are counted separately. MAT reopening uses
MATLAB, not an independent HDF5 reader; this is same-agent algorithmic QA,
not independent personnel or physical validation. Actual trace containment
has no tolerance; inherited allocation comparisons and scalar v30 diagnostic
comparisons retain their labelled 1e-12 relative/absolute budget.

Repair handoff: build additive v73 with stable monotone passive/affine interval
images, a correlated ON-age equality certificate, a source-limit certificate
that retains its denominator/limiter relation, and correlated work/auxiliary
nonnegativity proof. Never silently relax bounds, inject root midpoints, treat
an inconclusive box as evidence of a physical violation, or hide segment
exhaustion. Regress original v72 witnesses, six modes, repeated service and
true early-disable/collision/resource controls before an annual adapter.
