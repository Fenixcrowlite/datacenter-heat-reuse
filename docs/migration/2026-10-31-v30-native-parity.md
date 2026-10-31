# Native MATLAB Stateflow v30 acceptance replay

The source-based parity test is `tests/test_v30_native_parity.py`. The four
`datasets/reference/v30_native_*` files are byte-for-byte copies of MATLAB
R2026a Stateflow acceptance evidence from 2026-10-09 at
`DataCenter_Heat_Reuse/results/stateflow_v30_20261009T212727142Z/`.
Their original SHA-256 hashes are pinned in the test.

The test independently executes original MATLAB chart and component source using
`heat_reuse.matlab_subset`. Native outputs enter **only after execution** for
comparison. The original five source-function SHA-256 hashes are pinned too.

Results observed locally on 2026-10-31: 23/23 scenarios, 69 intervals,
1863/1863 values, six modes, zero mismatches within
`2e-9 + 2e-11*abs(reference)`, worst absolute difference
`4.973799150320701e-14`. The 18/18 source-native fault configurations
also reproduced the expected diagnostic and accepted-prefix length.

Run with `python3 -m unittest discover -s tests -p test_v30_native_parity.py -v`.
Windows Python 3.14 and Ubuntu 24.04 WSL Python 3.12 each passed two tests.

Limitations: this verifies the saved native test cases, not every possible
Stateflow transition, GUI/Stateflow scheduler fidelity, or measured physical
tank behavior. The original MAT files and complete scientific archive stay
in their original location. This is a draft PR, not a release approval.
