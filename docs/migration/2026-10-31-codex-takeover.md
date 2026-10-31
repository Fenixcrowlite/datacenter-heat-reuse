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
