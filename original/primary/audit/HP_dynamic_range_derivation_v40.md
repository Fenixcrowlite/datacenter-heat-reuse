# v40 source-relative HP bracket repair

This derives a numerical repair of the assumed screening law, not a primary
paper equation or calibrated equipment model. The v39 exact-input analytic
quadratic oracle remains independent of production bisection.

For C(Q)=N[1-p+p Q/K], operate only at C>=Cmin>1 with 0<=Q<=min(R,K).
Available source S constrains Qev=Q(1-1/C)<=S. Because C>=Cmin,

    Qev >= Q (Cmin-1)/Cmin,
    Q <= S Cmin/(Cmin-1).

Therefore intersect the request/capacity upper bound with a source-relative
bound. Compute f=(Cmin-1)/Cmin instead of 1-1/Cmin to avoid cancellation near
one. An outward allowance of four ulps avoids inward rounding of this bound.
If S/f overflows, keep the finite request/capacity bound. All flows are MW;
f and COP are dimensionless. No COP/MW slope or S/K ratio is formed.

On the admissible interval, dQev/dQ=1-a/C^2>0, where a=N(1-p)<=C.
Maintain a feasible lower endpoint and bisect until no distinct binary64
midpoint exists. A 2048-step guard rejects unresolved progress; it does not
choose a result based on a fixed accuracy budget. The old request-relative
80-step stopping rule is removed. Return only positive output with finite
COP and positive representable electricity; otherwise explicitly reject
DCHR:v40:HPResolution. OFF due to zero inputs or an infeasible operating
cutoff retains the existing convention.

Evaluate Qev as Q[(C-1)/C], including the returned source flow. This avoids
subtraction of nearly equal Q and W near COP=1; positive unrepresentable
evaporator flow is also rejected. First-law comparisons allow rounded
binary64 sums. Include the smallest representable COP above one as a stress
fixture, not a realistic equipment operating condition.

Floating-point evaporator evaluation is still rounded, and exact-input COP
thresholds can differ by an ulp. Thus test analytic maximal output with
relative and ulp tolerances; retain the exact v39 cutoff as observed only.
The correction does not prove every possible near-cutoff classification.
Subnormal comparisons use ulp allowances and explicitly require nonzero
heat/electricity where representable, so false OFF cannot pass by tolerance.

Acceptance requires executing the newly saved v40 Stateflow model, retained
v39 wide/tight counterexamples, all six modes, prior dwell/fallback references,
actual runtime fault rejections and separate saved-MAT re-export. Independent
QA uses 150-digit exact-input quadratic roots, Decimal TES ODEs, six-mode
reference simulation, source/request invariance, source/archive bindings and
preservation hashes. Same-agent algorithmic independence is not independent
personnel or measured physical validation. Clock seed/bound/event ordering,
solver-clock events, generated code and article parameter signoffs remain open.
