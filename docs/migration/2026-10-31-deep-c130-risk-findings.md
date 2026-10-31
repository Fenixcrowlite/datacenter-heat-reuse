# Deep audit of complete private C130 research corpus (2026-10-31)

**Status: BLOCKED_EXTERNAL_DISTRIBUTION.** This review is read-only.
The original source cutoff and its three immutable ZIPs remain byte-preserved.
Never attach source archive objects, matched credential strings, browser state,
user names, file path labels, or raw binary data to public GitHub issues.

## Evidence and boundaries

A new standard-library-only scanner `tools/source_risk_inventory.py`
validated each source manifest's object listing, SHA-256 digest format,
declared sizes and duplicate entries. It then **streamed every distinct
content object in each of the three C130 archives, recalculating SHA-256
for each**, and classified the declared logical file paths using
approved risk categories. This is broader than the original filename-only
manifest check, which cannot find home paths or emails inside source files.

**Completed first-pass findings:**

| Item | Count |
|---|---:|
| Declared research file paths | 98,591 |
| Verified distinct object SHA-256 digests | 15,177 |
| Root aliases | 91 |
| File paths with one or more high-risk indicators | 157 |
| Paths whose file content contains an absolute user-home directory | 2,462 |
| Paths with email-like patterns in content | 82 |
| Paths with credential-style assignments in content | 1 |
| Browser QA profile paths | 139 |
| Known browser state filenames | 24 |
| Credential-like filenames | 1 |
| Third-party document rights review | 161 |
| Paths containing or referring to opaque/binary data | 62,542 |
| Paths requiring source and dataset provenance review | 34,634 |

These categories **overlap**: the 157 high-risk paths count unique
logical paths in that severity class, not a sum of category counts.
An indicator is not proof of compromised access or live credentials.
A negative check is not proof of safety.

The content scan found **2,015 unique source archive object instances**
containing user-home strings, 36 containing email-like strings, and one
containing a credential-like assignment. Distinguish this from the 2,462
path occurrences because content objects can be reused by many filenames.

The secondary `tools/nested_model_risk.py` scanner independently examined
**72 distinct SLX/Office ZIP object payloads** referenced by **918 logical
file paths**. It opened the inner XML ZIP entries, scanned the decoded
member bytes and found nonempty creator/last-modifier XML metadata in
containers associated with all 918 paths. It did **not** export any
creator names. This warrants human inspection because even byte-valid
MATLAB source archives can contain embedded authorship metadata.

## Private artifacts and data minimization

These are retained in the approved Windows recovery workspace
`DCHR_RISK_INVENTORY_20261031`:

- `RISK_AGGREGATE.json`: numeric counts by risk flag, archive, and
  SHA-256-hashed root ID. SHA-256:
  `6682a269bf471da512660672893afdba12f8a2c3182c148d8377c29381bff5f5`
- `PATH_HASH_RISK_INDEX.csv`: 98,591 per-path rows, each with only
  SHA-256-hashed path and root identifiers, filename suffix, size, and
  category flags. SHA-256:
  `4000e6263625a2a16d106b8503bd10c908885cc1fb8808200a363a138cff6e56`
- `NESTED_MODEL_RISKS_V2.json`: nested-container aggregate and
  object-content digests, no raw names or creator values. SHA-256:
  `6dbb0cc7e816a07a1bfae8b8540f7107f6a448fb4238ce47735d6c0c958019ec`
- `ROOT_REVIEW_QUEUE.json`: review priority for 91 hashed root aliases:
  **2 P0 restricted**, **87 P1 identity review**, **2 P2 provenance and rights**.
  Priority is a heuristic, not a fully reviewed decision.
- `C130_COMPLIANCE_DEEP.json`: fail-closed release-compliance audit
  incorporating verified redacted content and nested archive evidence.
  It remains `BLOCKED_EXTERNAL_DISTRIBUTION`. CLI gate exit: **2**.

The original file names, content snippets, matched emails, human names,
credentials, and browser values are **never written in these reports**.
Hashed filenames are pseudonymous, not completely anonymous, and the
reports must stay inside the private authorization boundary.

## Threat model and caveats

- Pattern matches are intentionally limited to high-confidence token/key
  markers and broader email, absolute user-home and credential-assignment
  patterns. False positives are possible. The scanner does not expose
  matched values for manual validation in an untrusted log.
- The first pass does **not** fully decode arbitrary binary `.bin`,
  encrypted or proprietary `.mat` data; nor does it evaluate
  scientific model validity or infer copyright ownership.
- The secondary pass decodes supported nested ZIP/XML documents with
  fixed per-object limits. Nested ZIPs beyond those limits remain
  candidates for manual review.
- The 21-file curated native v30 evidence subset is separately useful for
  scientific reproducibility, but remains `PRIVATE_REVIEW_NO_EXTERNAL_SHARING`.
- Original C130, old and current bundles containing C130, and this risk
  index are **not authorized for external transfer**.

## Developer commands

```text
python -m tools.source_risk_inventory --archive SOURCE.zip --archive SUPPLEMENT.zip --archive QA.zip --report PRIVATE/RISK_AGGREGATE.json --index PRIVATE/PATH_HASH_RISK_INDEX.csv --progress PRIVATE/SCAN_PROGRESS.json
python -m tools.nested_model_risk --archive SOURCE.zip --archive SUPPLEMENT.zip --archive QA.zip --report PRIVATE/NESTED_MODEL_RISKS_V2.json
python -m tools.release_compliance --checkout . --archive SOURCE.zip --archive SUPPLEMENT.zip --archive QA.zip --full-content-report PRIVATE/RISK_AGGREGATE.json --nested-report PRIVATE/NESTED_MODEL_RISKS_V2.json --report PRIVATE/C130_COMPLIANCE_DEEP.json --gate
```

Expected release-gate exit is `2`, regardless of whether unit tests
and continuous integration passed. The next milestone is an authorized
human review of the two P0 root categories, rights provenance for any
retained material, and a new separately versioned source archive. Never
overwrite the original C130 source release to hide this evidence.
