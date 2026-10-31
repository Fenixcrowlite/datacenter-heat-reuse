# Complete three-asset source release: independent recipient restore QA

**Status: PASS, 2026-10-31.** This is the private **draft** source
release identified in `manifests/release.json`, release ID `429949218`,
source cutoff **2026-10-31 C130**. The live SCADA installation and
original OneDrive research sources were not modified.

## Exact artifacts re-downloaded and checked

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `heat-reuse-source-2026-10-30.zip` | 464100930 | `3eecbe7e2c7bae487d3c9d083e23520566ae863edac060130aaab424a07c9880` |
| `heat-reuse-supplement-2026-10-31.zip` | 72538624 | `56787a7fb97f08aa50dc05c0dd87a52f5653ec1d3cd2e90b045186e15c8538f5` |
| `heat-reuse-scientific-qa-correction-2026-10-31.zip` | 169500 | `3f78994f2f85790b0e81ea6ede400a397f7a14de0fe96334518267f807d617a6` |

The private release metadata matched all three expected asset IDs/sizes.
Each ZIP was downloaded through the authenticated GitHub release API and
promoted from a temporary filename only after its exact SHA-256 and size
were verified. Authentication credentials were not saved in any output.

## All-three-manifest preflight

- **91** unique root aliases.
- **98,591** unique paths across the three archives.
- **15,177** distinct content SHA-256 digests across the combined release.
- Zero duplicate case-insensitive paths and zero cross-asset name overlaps.
- Zero file-as-parent collisions.
- Zero recorded snapshot errors.

## Clean Windows recipient extraction and readback

The improved `tools.snapshot.restore` was used on each ZIP, in order,
into a fresh isolated directory after validating the **combined** path
graph. For every content-addressed object, the restore operation first
checked decompressed size and SHA-256. After all three extraction steps,
a separate audit re-opened **every restored file** and checked its
actual on-disk size and SHA-256 against its manifest entry.

- Restored: **98,591 / 98,591** files.
- Independent on-disk readback: **98,591 / 98,591** SHA-256 PASS.
- Object verification: **15,197** archive object instances across
  three ZIPs (some content repeats across ZIPs; 15,177 distinct hashes).
- Read-back logical bytes: **3,883,130,845**.
- Mismatches or logged errors: **0**.

Local evidence directory:
`C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/DCHR_FULL_RELEASE_VERIFY_20261031/`

- Machine-readable evidence: `FULL_RESTORE_EVIDENCE.json`;
  SHA-256 `62a597cc4bc33f148257913d8ee1c240ef905460a28ea04b2a5471b404fb5093`.
- Download evidence: `RELEASE_DOWNLOAD_MANIFEST.json`.
- Path/manifest audit: `RELEASE_MANIFEST_AUDIT.json`.
- Reproducible scripts: `restore_full_release.py`,
  `inspect_manifests.py` and `download_verify_release.py`.
- Recipient: `recipient_complete/`.
- Restore stderr log was empty; `FULL_RESTORE_STDOUT.log` concludes
  `FULL_RELEASE_RESTORE_AND_READBACK_PASS`.

The independent archive hardening tests remain **9/9 PASS** on both
Windows 11 and Ubuntu 24.04, and GitHub Actions run `41224632499`
passed **44/44** Python and **44/44** Docker regression tests, plus
HTTP and persistence checks.

## Scope and remaining release gates

This verifies the exact three uploaded **research-source cutoff** assets.
It does **not** mean all more recent local project work (including
unmerged PR #1 changes) is included in those ZIPs. It does not certify
arbitrary Stateflow scheduling, measured heating-system performance,
industrial-controller deployment, or licensing/redistribution suitability.
The release remains a draft and PR #1 remains unmerged pending
independent peer review and final distribution policy checks.
