# Saved-v40 compensated-clock uncertainty audit

This is an engineering numerical-domain derivation, not a paper equation or
equipment measurement. Model release remains 0.40; checkpoint 0.41 audits the
existing saved executable without changing its builder, chart or host code.

The documented TwoSum state is (H,L,B), all in physical hours. H+L is the
represented elapsed age and B>=0 encloses discarded roundoff. Consequently
the admissible physical age interval is [H+L-B,H+L+B]. It is an enclosure,
not a statement that physical error has either particular sign. Exact seeds
with B=0 instead specify the sum of the exact binary64 H and L inputs.

For minimum dwell D, an unconditionally safe transition needs

    H + L - B >= D.

If H+L+B<D it is certainly premature. If D lies within the interval, the
transition is unresolved from the supplied information. A conservative
policy may wait until the lower endpoint reaches D or explicitly reject an
unresolved decision. Which policy to adopt belongs in the next repair.
Simply classifying H+L>=D does not prove dwell for every admissible age.

For constant held inputs with an energy guard already satisfied, nominal
wait is max(0,D-H-L). A conservative wait is max(0,D-H-L+B), before accounting
for new arithmetic uncertainty. Both have units of hours. Production v40
uses the nominal form; its planner and chart guard receive/persist B but omit
it from dwell decisions. Independent QA evaluates exact binary64 inputs
using 120-digit Decimal and records each unresolved transition separately
from trace/execution/first-law evidence checks.

Fixtures with B=1e-9 and B=2^-80 are allowed by v40's 1e-8-hour cumulative
accuracy budget. The former is a stress seed, not an observed real-machine
history or a measured early physical restart. The latter checks that a
small positive enclosure does not become mathematically zero. No bounded
uncertainty claim can assign its sign without more history. Seed controls
before/after the enclosure, signed exact residuals, and rejected B=2e-8
separate guard safety from domain validation and arithmetic continuity.

Zero-loss event ties use dE/dt=eta_c Qc-Qd/eta_d. Capacity and cutoff arrival
times are independently computed by division of energy difference by this
constant power. Dwell is exactly one hour or its neighboring binary64 value.
These fixtures audit execution/event precedence only within the existing
energy/time resolution budgets; one-ulp energy snapping is not a claim of
exact event-order correctness over every real input.

No primary-source evidence was fetched for this focused implementation
audit. Existing primary signoffs, physical-validation limits and accepted
v40 scope remain unchanged. Independent algorithms are run by the same
agent, not independent personnel.
