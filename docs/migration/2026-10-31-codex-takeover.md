# Codex continuation, 31 October 2026

Original Codex thread: `01a18289-f4aa-7af1-b117-c6d6ac2ba7f4`. Continuation after usage-limit stop at 13:21 UTC.

## Verified work

- The previously unfinished v22 external MATLAB function linker is retained.
- Implemented bounded MATLAB `try/catch`, `MException`, `addCause`, `throw`, `rethrow`, error identifiers and `isfield`; unsupported external instructions still fail closed rather than being interpreted as physical-domain errors.
- Exercised original extracted v24 and v28 MATLAB component chains. v24 dispatch passes its contract for a representative source-defined input and rejects a bad timestep; v28 exponential standing-loss contract passes and rejects corrupt TES next-energy.
- **These are executable source and physical-invariant smoke checks, not full model-versus-MATLAB golden-trace parity.** v30 dynamic structure-field indexing (e.g. `cfg.(names{j})`) is still unimplemented.
- GitHub Actions run `41204851424` on the previous `c8ecc94` commit failed exactly four subtests on Linux at pool v04 intervals 63 and 422. Linux libm inputs left a `7.450580596923828e-09` J TES residue and toggled the source-defined `discharge > 0` auxiliary 250 W condition.
- Stored the source-equation-generated 672-step baseline exogenous forcing as binary64 input values in `heat_reuse/pool_v04_forcing_17digit.json.gz` (30,840 bytes, SHA256 `16f11695c65acfec60ea2d8b01808a2258bd99200761d0121e21f1c0c4716aa6`). The profile contains no calculated simulation output. Each scenario still applies its source-defined perturbations and executes the model from first principles. Beyond interval 672, the original formulas generate new inputs.
- Replayed both previously failing scenarios under Linux using pinned input stimulus with **zero numerical field mismatches** at the retained source tolerance. Both tests of the Python pool implementation and source MATLAB function interpreter now pass on Linux.
- Complete verification: **33 tests PASS on Windows** and **33 tests PASS on Ubuntu 24.04 WSL**; see local ignored `.superpowers/sdd/2026-10-28-transfer/verify_{windows,linux}_20261031.err.log` for reproducible logs. The latest remote CI must still be checked on a newly pushed commit.
- Release metadata was already staged locally by Codex for a private draft release with three SHA-matched archive assets. Keep it draft until remaining model migrations and clean container reproduction pass.

## Next work

1. Implement guarded dynamic structure field access and cell indexing for the v30 source only after adding failing tests. Do not replace unsupported mathematics with canned archived outputs.
2. Expand genuine golden fixtures for v22–v30 and later historical models; mark source-smoke separately from MATLAB parity.
3. Re-run GitHub Actions native and container checks on the new commit and test a clean recipient checkout.
4. Publish a final release only when historical migration coverage, QA and container start are independently verified.

## Follow-up: scoped v30 dynamic field support (31 October)

In review branch `codex/v30-dynamic-fields-20261031`, the MATLAB subset gained strict dynamic struct-field reads/writes
(`s.(names{j})`), scalar cell-brace indexing (`names{j}`) and accurate `numel`/`length`/`isempty`
for literal cell arrays. Dynamic names must be scalar MATLAB identifiers and the target must be
a struct; unknown symbols and non-struct access fail closed. There is no Python `getattr`, eval,
file-system access, or arbitrary attribute invocation.

Observed local QA in an isolated Windows project directory:
- 17 non-legacy subset tests pass, 3 legacy fixture tests deselected (fixtures not copied).
- Original MATLAB `+dchr/+components/storage_parameters_v30.m` was executed with the
  original linked `storage_kernel_v30.m` and returned
  `[1,60,1,1,0.9,0.9,0.1,16,2,20]` for explicit synthetic physical input.
- Missing `eta_discharge` and nonphysical zero discharge efficiency were rejected.
- These are original-source contract tests. The v30 Simulink/Stateflow trace has **not**
  been compared against the original native-MATLAB golden record. No release approval.

Full-repo Linux and Windows verification for this new branch remains pending. The previous
commit `85297c1` retains its separately documented 33/33 tests per OS. The branch should
remain unmerged pending CI and independent source review.

- Full original `storage_step_v30.m` was also executed through the linked
  `storage_parameters_v30.m` and `storage_kernel_v30.m`. At A=30 MWh,
  the source-calculated next energies were 28.00158577875515 MWh (1 MW charge),
  26.08776051925611 MWh (1 MW discharge), and 27.145122541078784 MWh
  (idle); each matched the independent analytic exponential solution.
  Simultaneous charging/discharging was rejected. This is component-chain
  parity with its source equations, **not** a native Stateflow model trace.


- Independent bounded subset execution on Ubuntu 24.04 via WSL:
  **17/17 PASS**; source chain includes parameter checks, charge, discharge,
  idle and mutual-exclusion rejection. Log SHA256:
  `8a7fe97d0d7e01b41a039e0ecc3c4075b8b274416fc584c97d22f10b05aaa0d7`.
  Windows rerun: **17/17 PASS**, three legacy model fixture cases deselected.
  Neither run substitutes for full 33-case repository CI or native v30
  MATLAB/Stateflow trace comparison.


## Full PR-branch Python regression (31 October, subsequent checkpoint)

Checked out exact reviewed branch `codex/v30-dynamic-fields-20261031`
at `d71e51222a9531a4de2e4ae34e6185eaf4ddd5a3` in a **separate,
clean Git sparse checkout** on Windows. Explicit checkout scope includes
`heat_reuse`, `tests`, `models/extracted`, `datasets/reference`,
`original/primary/matlab`, `web`, `tools`, `docs`, `.github`.
This is a full Python test-suite run, not a restored full research archive.

- Windows 11, Python 3.14: `python -m unittest discover -s tests -v`:
  **38 tests PASS**, elapsed **117.034 s**.
- Ubuntu 24.04 WSL, Python 3.12: `python3 -m heat_reuse verify`:
  **38 tests PASS**, elapsed **88.056 s**; Linux process exit code **0**.
- Windows saved stderr log
  `QA_WINDOWS_ALL.stderr.log` SHA256:
  `fdba1028e535fc333e52161bfd0586b0476b33eb265756910fd9bd377f65035c`.
- Linux saved stderr log
  `QA_LINUX_ALL.stderr.log` SHA256:
  `c4bdca14e6099b97f47f2aa337191cb989a7ca29ebee0b68f3392d9189110439`.
- Local evidence directory:
  `C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/DCHR_FULL_VERIFY_20261031/`.
- The `main` branch was not modified; changes remain in **draft PR #1**.

**Boundaries:** container build and actual HTTP + persisted-volume workflow
were not successfully executed at this checkpoint. Docker Desktop
Windows service was observed stopped. GitHub Actions result on the PR
head was not confirmed by the available read interface.
Native MATLAB/Stateflow whole-model-v30 golden-trace parity remains
unverified even though the original v30 storage component chain and
its analytic equation checks pass on both OSes.
