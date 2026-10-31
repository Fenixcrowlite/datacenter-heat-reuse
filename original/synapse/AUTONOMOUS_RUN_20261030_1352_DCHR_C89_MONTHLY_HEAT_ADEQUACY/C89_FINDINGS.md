# C89 | Synthetic annual heat adequacy and monthly dispatch

Native MATLAB R2026a C88 dataset; 8760 synthetic hours, seed 42. Not field-validated.
Input SHA256: `07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370`

Annual demand: 59430.0 MWh; gas backup: 10542.5 MWh.
Non-gas share of heat demand: 82.26%; gas share: 17.74%.
Gas required in 2879 of 8760 hours; maximum gas: 9.74 MW at 2026-01-24T03:00:00.
Worst gas-share month: 2026-01 (34.40%).
Storage active in 5975 hours. HP electricity: 7969.9 MWh.

## Interpretation and gates
Non-gas fraction is NOT solely recovered data-center heat: heat-pump electricity and storage are included in the system.
The scenario still requires gas backup. It cannot establish actual pool-heating adequacy without a separate pool-load profile.
No Stateflow v85 parity, measured thermal data, prices, emissions, standards or primary-source signoffs verified.
Next: reconcile a standard 500 m3 pool load, temperature/loss assumptions and heat-pump electricity with cited field data.
