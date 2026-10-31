# Private curated MATLAB/Stateflow v30 evidence subset (2026-10-31)

**Classification:** `PRIVATE_REVIEW_NO_EXTERNAL_SHARING`. This is a narrowly
allowlisted, hash-preserved **research reproducibility subset**, **NOT** a
complete sanitized successor to the original 98,591-file C130 research
release, a license grant, or a general external distribution approval.

## Reason for a separate curated subset

The immutable C130 source release contains historical browser QA state,
a `runtime/secrets.json` file path and third-party rights uncertainty.
The four initial native v30 benchmark fixtures included two diagnostics
that carried Windows user-home-directory paths. Therefore a restricted,
scientifically useful set is selected at the **individual file** level,
rather than using a broad `results/` prefix or reusing the entire C130 ZIP.

## Exact included material

- **19** specific files from historical
  `primary/results/stateflow_v30_20261009T212727142Z/source_snapshot/`,
  including the native Stateflow v28 and v30 SLX models, supporting MATLAB
  `.m` implementations, the Python reference and scientific acceptance
  spec. The source ZIP's SHA-256 must match
  `3eecbe7e2c7bae487d3c9d083e23520566ae863edac060130aaab424a07c9880`.
- **Two** committed reference files: `v30_native_cases.json` and
  `v30_native_trace.csv`.
- Explicitly **not included**: `v30_native_faults.json`,
  `v30_native_fault_audit.json`, historical browser QA directories,
  old project `runtime` folders, any of the unselected 98,570 C130 paths,
  and unrelated archives.

Native MATLAB references are copied **byte-for-byte** from their original
content-addressed archive objects. The output is a new,
`dchr-source-archive-v1` compatible ZIP with a separate
`review_v30` root and immutable per-object SHA-256/size commitments.

## Build, verify, restore and attest

```powershell
python -m tools.curated_v30 build --source <verified-C130-source-ZIP> --benchmarks .\datasets\reference --out <new-private-curated-ZIP>
python -m tools.curated_v30 verify <new-private-curated-ZIP>
python -m tools.curated_v30 restore <new-private-curated-ZIP> <new-empty-recipient>
python -m tools.curated_v30 attest <new-private-curated-ZIP> <new-empty-recipient>
```

The builder checks the source ZIP SHA-256, only selects 19 exact
historical filenames and exactly two reference benchmarks, verifies all
underlying object hashes, checks for known sensitive patterns in the
content, and **opens the internal ZIP/XML files in SLX archives** to check
for suspect content, invalid member paths, symlinks, case-collisions and
excessive expansion. The output refuses overwrite and stays private.
The verifier refuses unexpected/duplicate members. The attestor
independently opens **every restored file on disk**, verifies its SHA-256
and size, and rejects added or missing files.

## Verified independent local evidence

- Candidate private archive:
  `DCHR_CURATED_V30_20261031/dchr-v30-private-curated.zip`.
- **21** logical paths, **20** unique content objects.
- Initial archive size **111,966 bytes**, SHA-256
  `ee36f41743ca8436765e9b49a7897d353f9c3985edec0fbf150373243e39d899`.
- Restored into previously absent isolated Windows and Ubuntu (WSL)
  recipient directories. **21/21** on-disk SHA-256 and size comparisons
  PASS on **both**, **zero extra paths**.
- The dedicated synthetic regression suite includes negative cases for
  sensitive home paths, source corruption, malicious nested SLX entries,
  path collisions, tampered restored bytes and output overwrites.
- Original source C130 asset was read only; its binary checksum and the
  previously audited 98,591-file release were not modified.

## Limits and next gate

This is **content-pattern screening, not full PII/secret clearance**.
The scanner can miss identifiers, credentials or proprietary material
that do not match its current rules, especially in opaque binary fields.
Data ownership, MATLAB/Stateflow redistribution rights and third-party
license provenance remain to be established. Human security/legal review
is required before any external transfer. Preserve the original archive
and its restricted status; do not replace the C130 historical cutoff.
