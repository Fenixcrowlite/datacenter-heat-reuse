# Private C130 remediation queue and reviewer disposition policy

Status: **BLOCKED_EXTERNAL_DISTRIBUTION**.
Source: completed 2026-10-31 full-content risk inventory of the three
immutable original C130 ZIPs. This stage only creates an **internal review
queue**. It neither deletes source material, selects a permitted release
subset, nor approves anything for external sharing.

The `tools/remediation_plan.py` command consumes the local hashed-path
risk index and deterministically assigns **every declared file** exactly
one review disposition, in precedence order:

| Disposition | Paths | Intended reviewer action |
|---|---:|---|
| P0_QUARANTINE_CANDIDATE | 157 | Restrict and inspect in place; exclude from a proposed new transfer bundle unless explicitly cleared |
| P1_IDENTITY_REVIEW | 2,528 | Review home paths, email-like data and personal references |
| P2_NESTED_METADATA_REVIEW | 918 | Review SLX/Office creator/last-modifier information |
| P3_OPAQUE_OR_RIGHTS_REVIEW | 61,711 | Decode binary containers and check source/third-party ownership |
| P4_SOURCE_PROVENANCE_REVIEW | 29,590 | Establish authorship, license and permitted use |
| P5_UNREVIEWED_NO_CLEARANCE | 3,687 | Manual review, not automatically safe or licensed |

Total **98,591** classified paths; **0 files approved** automatically.
The categories are exclusive by precedence, unlike the original
overlapping risk flags. An item with multiple issues is assigned the
highest-priority applicable category; the underlying per-file risk index
retains all individual flags.

## Reproducible local command

```powershell
python -m tools.remediation_plan --index <private>/PATH_HASH_RISK_INDEX.csv --queue <private>/PRIVATE_REMEDIATION_QUEUE.csv --report <private>/PRIVATE_REMEDIATION_SUMMARY.json
```

Outputs are locally restricted. The CSV contains SHA-256 IDs of root/path,
source archive filename, review disposition and fixed category codes;
no original file paths, user names, browser content or credential values.
Its input is bound by the SHA-256 of the completed risk index. It does
not contain a list of files authorized for redistribution.

The remediation generator rejects invalid/missing hashed IDs, duplicate
path records, unknown risk categories, and attempts to overwrite existing
results. It preserves a fail-closed policy and includes synthetic
regression tests.

Human review should begin with the two P0 root groups in
`ROOT_REVIEW_QUEUE.json`, then address identity, opaque/binary files,
nested model metadata and rights. A new sanitized release must be built
separately and validated only **after** the rights/privacy decisions are
documented, without modifying any C130 original. See
`docs/migration/2026-10-31-deep-c130-risk-findings.md` for scan
limitations and provenance.
