# v18 varied-domain Python dispatch audit

Reproducible: `python audit/test_dispatch_properties_v18.py`, seed 18009. Two successful executions; second checked exact match against preserved JSON without overwriting.

Results: 1500/1500 varied-timestep/efficiency/capacity/loss randomized cases, 13/13 invalid-input rejection cases; 0 failures. Max absolute system balance residual 4.973799150320701e-14 MWh. JSON SHA256 7F9373D55FED4614A9958839248E2885CAF84D0CC9575B1FAE0B4E9F358CD82A. Script SHA256 B8974F3533C2BFDB1CFAA299C5476B0CAA59E8916B77B722A8E560A5A8FAFDCC.

Classification: algebraic/constraint verification of Python v16, NOT independent physical validation, NOT MATLAB parity, NOT original-paper agreement. Full source signoffs 0/31. No legacy files modified.

Next: independent deterministic MATLAB v16 vs Python parity; resume original-paper equation/page/DOI audit.
