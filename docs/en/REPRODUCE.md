# Reproduction record

The approved scope includes all unique working algorithms, the complete source archive, Python calculation, interactive diagrams, containers and a private repository. Work remains in progress until every promised model and the delivery checks are completed.

## Verified numerical adapters

- `annual-v2`: native C88 MATLAB warm-source fixture, 192,720 numeric fields; independent second annual oracle; all five saved MATLAB scenario summaries. Native absolute field tolerance: 2e-8; summary tolerance: 2e-6.
- `pool-v04`: eight saved 672-step Simulink scenarios; all numerical fields with absolute tolerance 1e-5 and exact dispatcher modes. Full-precision inputs are generated using the original source formulas.

Run `python -m heat_reuse verify` to execute current tests. Test outputs prove only the cases that ran; historical reports are retained as provenance and are not substituted for new execution.

## Known numerical boundary

Original MATLAB CSV exports round inputs to roughly 15 significant digits. In pool v04, this can leave around 7e-9 J after a storage-empty event instead of exactly zero. The unchanged exact-zero branch may then show a 250 W auxiliary pump for a vanishing discharge. The transfer preserves the original equations rather than adding a hidden numerical cutoff. Reference comparison therefore regenerates the original full-precision scenario inputs; imported rounded records are a distinct input dataset.

## Model completeness

`models/catalog.json` records extracted original binary models and their migration status. `not_ported` means no verified numerical Python adapter exists yet. The structural browser is available for those models, but its presence is not a successful simulation claim. The annual adapter corresponds to MATLAB source version v2, and must not be reported as Stateflow v85 parity.

## Distribution checks

The source archive is streamed independently of the operational checkout. Restoration validates every referenced object before writing. Container base images are pinned by digest; network access is needed for the first build. Record the actual build, health check and fresh-container experiment results in the release evidence before claiming container reproduction.
