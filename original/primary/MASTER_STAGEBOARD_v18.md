# DataCenter Heat Reuse — checkpoint v0.18

Inherits v17; prior v0.3/v0.4 and earlier checkpoints remain untouched.

**Completed:** varied-domain Python v16 dispatch property test: 1500/1500 randomized cases and 13/13 invalid-input rejections passed. Maximum system-balance residual 4.973799150320701e-14 MWh. Repeat run reproduced the stored report exactly. Evidence: `audit/test_dispatch_properties_v18.py`, `audit/dispatch_properties_v18.json`, `audit/run_notes_v18.md`.

**Not established:** 31 primary-paper full signoffs (still 0), independent physical validation, MATLAB/Python equivalence, or finished Stateflow controller. This checkpoint verifies only bounded Python algebraic consistency and constraints.

**Next:** deterministic MATLAB v16/Python cross-check including variable timestep, TES saturation, HP-off and boiler-limit cases; continue page-level primary-paper review.
