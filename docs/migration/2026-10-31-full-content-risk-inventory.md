# DCHR historical C130 full-content risk inventory (private)

This tool examines **all unique content-addressed objects** in each original
C130 research ZIP and associates the resulting classifications with every
declared logical path. It is a read-only **data minimization and review
workflow**, NOT a new release, not a deletion or sanitization of the original
files, and not permission for external distribution.

## Scope and verification

Run from the repository with the three already authenticated and SHA-256
verified source ZIPs:

```powershell
python -m tools.source_risk_inventory --archive <source.zip> --archive <supplement.zip> --archive <scientific-qa.zip> --report <private-empty-folder>/RISK_AGGREGATE.json --index <private-empty-folder>/PATH_HASH_RISK_INDEX.csv --progress <private-empty-folder>/SCAN_PROGRESS.json
```

The scanner first checks each content-addressed manifest for format, object
counts, missing/extra ZIP entries, duplicate members and SHA/size metadata
conflicts. It then reads each unique object through a bounded streaming
buffer, **independently recomputes each full-object SHA-256**, and searches
for configured indicators of GitHub/AWS tokens, private-key markers,
credential-style assignments, email-like strings and absolute user-home
paths. These indicators are never copied to output.

Every one of the manifest's logical paths is classified for browser
profile/state, credential filenames, possible personal data and source or
third-party document review. Paths are referred to in the local index
**only by SHA-256 of the root alias and SHA-256 of the combined root/path**.
Risk flags and byte counts stay machine-readable without printing original
paths. Root statistics are grouped under SHA-256 aliases.

## Interpreting the outputs

- `RISK_AGGREGATE.json` has counts by archive, unique content object
  instance, total paths and risk category, plus hashed-root totals.
- `PATH_HASH_RISK_INDEX.csv` maps each of the ~98k source paths to its
  **private hashed identifier**, file suffix, size and flagged risk types.
  It is **not a shareable source catalog**. Hashes can be guessed using a
  known filename dictionary, so keep this local and access-controlled.
- `SCAN_PROGRESS.json` tracks the most recent completed object number
  for visibility. The scan does not modify the archive and does not
  automatically resume from partial output.
- A successful object hash verification rules out unseen byte corruption
  for the objects scanned. A negative pattern match **does not prove**
  content to be safe or licensed.

## Important limitations

This streaming pass does not fully decode every nested proprietary format,
encrypted ZIP member, compressed `slx` XML, proprietary `.mat` object or
binary blob, and it cannot discover every secret or identity. Email-like
strings can be false positives. It never decides who owns source code.
The complete historical C130 release remains `BLOCKED_EXTERNAL_DISTRIBUTION`;
the previously prepared 21-file scientific v30 subset remains private too.

Next use the per-root aggregated risk counts to prioritize *authorized local*
inspection, rights verification and a new distinctly versioned,
content-minimized research export. Do not overwrite C130 or share these
reports publicly.
