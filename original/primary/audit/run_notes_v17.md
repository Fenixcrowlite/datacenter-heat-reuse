# DataCenter Heat Reuse: v17 bounded dispatch stress audit

Date (UTC): 2026-10-08 22:30. This is additive to v15 and the uncheckpointed v16 implementation; no legacy model or original PDF was overwritten.

## Evidence
- Executed Python 3.14 test: `audit/test_dispatch_properties_v17.py`.
- Reproducible seed: 17009; 1000 randomized source-power, heat-demand, source-temperature and TES initial-energy scenarios.
- Output: `audit/dispatch_properties_v17.json`; 1000 completed, 0 algebraic-balance failures; maximum absolute one-hour whole-system balance residual 1.4432899320127035e-14 MWh.
- SHA256 output JSON: 20BFF3F40C751E9A1488B32B270EC54DEB59128A0293283A16DB3BBCFF2C0DF7.

## Interpretation and limits
This verifies algebraic consistency of the independent Python dispatch reference over a bounded randomized sample, **not** independent physical validation, source-paper agreement, MATLAB/Python equivalence, or all possible inputs. Boiler capacity fixed at 10 MW, timestep fixed at 1 h, default TES parameters used, temperature lift fixed at 30 C. The test does not yet cover extreme timestep/efficiency/capacity domains. Primary-source signoffs remain 0/31 (inherited v15).

## Blocker and next step
The local Codex CLI engineering agent returned a usage-limit error in the 00:26 local log, indicating next access at 04:46. This test was run directly using the authorized PC, not via that agent. Next: vary timestep/TES efficiency/limits, test invalid inputs, then run versioned MATLAB v16 vectors and compare against Python; only then pursue an integrated Simulink/Stateflow controller. Maintain the source-provenance workstream independently.
