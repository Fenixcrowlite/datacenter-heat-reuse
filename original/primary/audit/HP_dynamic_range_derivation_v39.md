# v39 heat-pump search domain: independent derivation

This is an audit of the saved v38 implementation, not a calibrated equipment
model, a primary-article equation, or acceptance of a corrected controller.
Fixture constants are engineering assumptions. Existing models are preserved.

Let K be the output capacity, S the available source heat, R the request,
N the nominal COP, and p the part-load penalty. In the assumed screening law,

    C(Q) = a + b Q/K,   a=N(1-p), b=Np,
    W=Q/C(Q),   Qev=Q-W,   0 <= Q <= min(R,K).

Operate only at C>=Cmin>1. The minimum admissible output is
max(0,K(Cmin-a)/b) when b>0, or zero when b=0 and N>=Cmin.
On this domain dQev/dQ=1-a/C(Q)^2>0 because 0<=a<=C and C>1.
The source-limited positive root therefore uniquely maximizes feasible output.

Multiplying Qev(Q)=S by K C(Q) gives

    b Q^2 + B Q - a K S = 0,   B=(a-1)K-bS.

For b>0 and B>=0, the cancellation-resistant root is
2aKS/(B+sqrt(B^2+4baKS)); for B<0 it is
(sqrt(B^2+4baKS)-B)/(2b). For b=0 and a>1 it is aS/(a-1).
The audit oracle evaluates this with 150-digit Decimal arithmetic from the
exact binary64 inputs, then applies source, request and cutoff bounds. It does
not import or reproduce MATLAB's bisection. The polynomial terms have MW^2
units; COP and a,b are dimensionless. Decimal coefficients avoid binary64
overflow/underflow in the independent audit, not in a proposed production fix.

## Why 80 iterations do not guarantee binary64 accuracy

The source-constrained v38 search starts with lower=0 when the operating
cutoff imposes no positive output floor. Let U=min(R,K). If its first j
midpoints are infeasible, midpoint j is U/2^j and the feasible lower endpoint
remains zero. If the root Q*<U/2^80, every one of the 80 tested midpoints is
infeasible and the function returns lower=0. This is false OFF despite S>0
and a feasible positive operating point. Even after a feasible midpoint is
found, 80 total iterations provide an absolute interval width U/2^80, not a
relative error bound scaled to Q*. A wider request can consequently degrade
the answer despite an unchanged source-limited optimum.

For N=4,p=0, Q*=4S/3 exactly. With K=8 MW, R=3 MW and S=8*2^-90 MW,
Q*=8.616464714094038e-27 MW, while R/2^80 is about 2.481541837659083e-24 MW.
False OFF is thus predicted without translating the production loop.
At the same S, setting R=S bounds the request below the source-limited root:
Q=S, W=S/4 and Qev=3S/4 are feasible. In the saved plant, disabling its
otherwise-unused charging request yields this matched service control.
These extreme ratios are numerical stress fixtures, not equipment sizes.

## Evidence gates and scope

The saved v38 SLX must execute afresh: all six baseline modes and both wide
and tight request cases. Compare the numeric plant/component outputs to the
analytic optimum, retaining failures separately from defect-reproduction QA.
Use relative power and ulp tolerances, so a zero result cannot pass solely
because its absolute MW value is small. Independently re-export SimulationOutput
MATs in another MATLAB process, verify numeric bindings, TES Decimal ODEs,
first-law closure, ports/SOC bounds, chart metadata, archive/source hashes and
all prior sealed artifacts. Label synthetic oracle checks separately.

Cutoff controls separated by 1e-10 relative test ordinary threshold behavior.
The exact binary64 threshold fixture is observed but excluded from defect
counts because production and exact-input cutoff evaluation can differ by an
ulp. This audit does not establish every near-cutoff domain, compensated-clock
seed/event ordering, physical validation, article replication, standalone code
generation or solver-clock event scheduling. No new literature source or
equipment parameter is adopted; primary article signoffs remain 0/31.

## Additive repair handoff

Implement a versioned source-relative bracket or a stable scaled root with
explicit representability diagnostics. Do not merely increase the fixed count:
cover source/output ratios through the positive binary64 domain, request
invariance when request exceeds the source optimum, cutoff feasibility and
nonzero representable electricity. Use the v39 counterexamples plus all six
modes and independently check analytic maxima and first-law closure. Preserve
v38 and every defect trace. Clock seed/bound and strict event ordering remain
a separate open audit; no broader acceptance follows from an HP-only repair.
