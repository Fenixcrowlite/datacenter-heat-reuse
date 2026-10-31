# C130 source archive distribution hold and release compliance gate

**Date:** 2026-10-31. **Status: BLOCKED_EXTERNAL_DISTRIBUTION.**

The private research archive still supports local scientific reproduction.
This hold applies to **copying, uploading, publishing or sharing** the
historical C130 ZIPs or any portable kit embedding them with an external
recipient, even if the recipient ZIP and its SHA-256 have passed QA.

## Independently verified evidence

- Three **exact**, already verified, original C130 source ZIPs were
  audited through their manifests without printing any secret file data.
- The main source ZIP has 98,321 declared file paths. Restricted path
  detector results (overlapping categories, **not** an additive count):
  **139** browser QA profile paths, **24** known browser state filenames,
  **1** credential-like filename (a historical `runtime/secrets.json`).
  Broader earlier name-pattern searches found up to 159 browser-network
  paths and 52 state-associated paths. Neither scan proves whether
  credentials within these files are usable.
- The same manifest contains **161** PDF/PPTX/DOCX documents whose
  redistribution rights are not established by their presence in the
  project.
- The repository has **no top-level LICENSE or COPYING file**, nor
  automatically discoverable bundled source license files. This is a
  licensing **documentation gap**, not a legal determination that all
  authored material is proprietary or unlicensable.
- Supplement and QA correction ZIPs had no matching restricted path
  patterns under the current rules; this is **not** a full content/secret scan.

Local machine-readable evidence:
`C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/DCHR_RELEASE_COMPLIANCE_20261031/C130_COMPLIANCE_REPORT.json`.

The privacy classifications are deliberately based on declared path
metadata only. No confidential credential values are included in the
report or the PR; do not upload original browser data for public audits.

## Implemented controls

`python -m tools.release_compliance --checkout . --archive <path-to-ZIP>`
produces a redacted JSON risk inventory. Add one `--archive` per source
ZIP. With `--gate`, the tool exits **2** whenever a publication is
requested, because automated path inspection cannot grant copyright or
privacy clearance.

The `tools.portable_kit build` command now **refuses** to package known
historical C130 source ZIPs without explicit `--internal-only`. When
used for local forensic reproducibility, kit manifests carry
`distribution_status=PRIVATE_LOCAL_ONLY` and a disclosure warning,
which the companion verifier enforces before extraction. This does not
turn a restricted kit into a safe sharable deliverable.

Four release-compliance regressions and two additional kit restrictions
were added; local Windows and Ubuntu tests passed.

## Required conditions for an external/private partner or public release

1. Identify the rights holders and valid license grants for application
   code, research models, datasets, downloaded papers, presentations,
   MATLAB examples, and other third-party content. Add appropriate
   LICENSE/NOTICE and source attribution.
2. Review all historical root directories for browser profiles,
   credentials, private account metadata, machine identifiers,
   screenshots and personal information; remove/rebuild a **new**
   sanitized release, rather than editing C130 in place.
3. Independently scan non-browser binary objects and unrestricted
   text sources for secrets and privacy risks. A filename-based filter
   is not a content scanner.
4. Validate the *new* release by complete clean-recipient extraction,
   SHA-256 readback, automated model regression and independent
   legal/security sign-off.
5. Publish a separately versioned artifact with a verified external
   distribution policy. Preserve the original C130 cutoff untouched
   as restricted historical evidence.

This remains a private development project. Neither a successful CI run
nor a correctly signed bundle establishes legal permission or
privacy-safe external redistribution.
