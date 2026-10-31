# Independent archive restore review, 31 October 2026

## Bugs reproduced and fixed

The original `tools.snapshot.restore` had two demonstrable defects:

1. `--prefix primary/results` also selected `primary/results_fake` because
   it used raw string `startswith` rather than path segment equality.
2. A manifest containing both `primary/a` and `primary/a/b.txt`
   could create one file before crashing on the next. No preflight
   file-as-parent collision check existed.

The independent audit also added portable case-insensitive collision
detection (e.g. `A.txt` and `a.TXT`) and rejects noncanonical path
segments (`a//b` and `a/./b`) before restoring.

All checks are in `tests/test_snapshot.py`. Archive restoration still
verifies all object SHA-256 digests and sizes before writing. These changes
are preventative, not a blanket guarantee of transactional recovery from
disk failure or process interruption.

## Actual clean-recipient trial

A **real research-source** checkpoint was taken read-only from the
authoritative MATLAB v30 `source_snapshot`, alongside committed
`datasets/reference` numerical inputs and provenance, then extracted
to a previously nonexistent isolated recipient directory on Windows.

Results of `RUN_REAL_V30_RESTORE.py` stored in the local Synapse recovery
checkpoint:

- `38` logical paths, `37` unique SHA-256 objects.
- `38/38` recovered files and `37/37` objects verified.
- ZIP size: `3,220,973` bytes.
- ZIP SHA-256: `79ba47b15d9ae4c49d61b63a46db241d8aa5cf4d4f98a5c3a26ea3e49e92477e`.
- Actual restored SLX SHA-256:
  `a940a1380f265feaa1426bfb0bda92ecf0514a9497453734e3a95830154e18fe`.
- All four v30 native benchmark fixtures matched their source files
  **byte-for-byte**.
- Repeat restore into the same destination was rejected without overwrite.

Local evidence:
`C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/DCHR_ARCHIVE_RESTORE_CHECK_20261031/RESTORE_CHECK.json`.

**Limitations:** This is an independently generated **scoped v30 source and
evidence** archive, **not** the previously published `heat-reuse-source-2026-10-30.zip`
full research release, nor its supplement/QA correction. Full 91-root /
98,591-path three-asset recipient restoration remains a separate release gate.
The original OneDrive source files and live SCADA were not modified.

## QA

The focused archive test suite contains 9 cases, passing on both
Windows 11 and Ubuntu 24.04 WSL, including four new adversarial
preflight and prefix tests.
