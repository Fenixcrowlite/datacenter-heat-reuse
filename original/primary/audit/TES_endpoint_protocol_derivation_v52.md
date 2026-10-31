# Canonical state protocol across MATLAB and compiled Stateflow — v52

The unaccepted saved v51 passes both exact v50 seeds and all six simple modes,
but all nine annual attempts reject at the strengthened exact handoff assertion.
Sharing a formula alone does not guarantee bit-identical host/compiled results.
The failed MATs, model, initial harness diagnostic mismatch and all logs remain
preserved. v51 is not an accepted replacement for v42.

The additive v52 plan has 23 rows. Rows 1–22 retain the prior schema; row 23
carries the canonical physical endpoint calculated over the complete segment.
Each next segment starts at precisely that endpoint, and padding repeats it.
Allocation recomputes the positive-span ODE independently with the same kernel,
requires agreement within the existing 64-epsilon energy correction budget,
checks finite strict [0,capacity] bounds, and adopts the explicit endpoint.
Runtime and independent Decimal checks still verify the ODE, losses, first law,
ports, cutoff and dwell. No extra tolerance grants a physical transition.

This defines one persisted state representation across arithmetic engines.
Padding identity, row23-to-allocated-end equality, energy handoff and macro
memory identity remain exact. The consistency budget cannot excuse material
ODE error, out-of-capacity state or nonzero padding service/loss. Compensated
clock/bound/dwell functions and supervisor logic remain the accepted v42 code.

Validation includes actual saved-model runs and separately labelled diagnostic
v51 runs with a temporary in-memory continuity relaxation solely to expose the
rejected raw mismatch. Diagnostic simulations do not count as acceptance.
No prior SLX is overwritten and no diagnostic mutation is saved to a model.
