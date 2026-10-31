# DataCenter Heat Reuse — additive checkpoint v0.17

Inherits v0.15 stageboard. The uncheckpointed v16 Python/MATLAB implementation was inspected; existing v0.3/v0.4 and other earlier checkpoints were not modified.

**Completed:** seeded randomized property test of Python v16 dispatch reference, 1000/1000 cases with no algebraic balance failures; maximum absolute residual 1.4432899320127035e-14 MWh. See `audit/dispatch_properties_v17.json`, test source `audit/test_dispatch_properties_v17.py`, and `audit/run_notes_v17.md`.

**Not established:** agreement with 31 primary papers (0 full signoffs), physical calibration, MATLAB/Python equivalence, complete TES property domain, or finished Stateflow controller.

**Next independent checkpoint:** varied timestep/efficiency/charge/discharge limits and invalid-input tests, then MATLAB-v16 parity; resume original-paper evidence review independently. Local Codex CLI currently rate-limited until 04:46 local time; direct Python verification succeeded.
