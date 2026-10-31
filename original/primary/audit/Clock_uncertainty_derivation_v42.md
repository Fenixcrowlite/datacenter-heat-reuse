# Uncertainty-aware dwell repair, release 0.42

Engineering numerical derivation; no paper equation, calibrated timer or
equipment measurement is claimed. Model 0.40 and checkpoint 0.41 are preserved.

The compensated clock `(H,L,B)` encloses physical elapsed age in
`[H+L-B,H+L+B]` hours. A normal transition with minimum dwell `D` needs
`H+L-B-D >= 0`. ON-dwell safety overrides remain allowed when heat-pump output
is unavailable. The error bound is never substituted by a time tolerance.

Computing the rounded sum `H+L` first can erase a residual or a small positive
bound. Release 0.42 instead calculates an outward lower margin:

    A = lower_add(H,-D)
    C = lower_add(L,-B)
    M = lower_add(A,C)
    ready = (M >= 0)

`lower_add(a,b)` obtains a rounded sum `s` and the TwoSum residual `e`.
Under the finite arithmetic domain tested here, `s+e` is the exact input sum.
If `e<0`, subtracting `eps(abs(s))` moves to a conservative lower value;
otherwise `s` already lies at or below the exact sum. Monotonic addition
then gives `M <= H+L-B-D`. A nonnegative `M` certifies the lower age endpoint.
This comparison can conservatively defer an exact equality; it makes no
claim of exact classification for every representable combination. Independent
Fraction checks validate lower margins and ready decisions on executed probes.

For an unready clock, the candidate wait starts above `-M`, with an upward
spacing allowance. The existing compensated-add routine advances `(H,L,B)`
and propagates newly discarded roundoff. The candidate is accepted only if
the resulting lower-age comparison is ready. Otherwise the new conservative
shortfall is added and recertified, at most sixteen times; failed progress
or certification rejects explicitly. A macro interval may end before that
wait; the persisted enclosure carries to the next interval and is recertified.
Energy events can interrupt a wait without authorizing an uncertified transition.

The planner, saved Stateflow supervisor transition guards and saved runtime
contract gate all receive `B`. The runtime gate also checks the first planned
transition against the model's initial clock, covering supervisor initialization.
No transition consumes the uncertainty after a latch reset: the new state's
age and enclosure reset to zero by the existing contract.

The held-input TES equation remains `dE/dt=P-lambda*E`, where
`P=eta_charge*Q_charge-Q_discharge/eta_discharge`. Its analytic held-power
flow, finite boiler, useful service and source/electricity first laws are
unchanged. Independent Decimal flow evaluation and the verified v34 Python
baseline compare saved traces. Actual in-memory attacks replace only the host
planner with nominal v40 and require saved v42 gates to reject at execution.

Numerical seeds, including `B=1e-9` and `B=2^-80` hours, are uncertainty
fixtures. Their physical error signs and long-run histories remain unknown.
Conservative waits can shift almost coincident events by a few binary64
spacings; those tests are judged within the explicit existing resolution.
Exact real-input event ordering, generated-code execution, solver-clock events,
hydraulic/thermal calibration and measured plant validation remain outside scope.
Independent QA uses different algorithms in the same agent, not different personnel.
