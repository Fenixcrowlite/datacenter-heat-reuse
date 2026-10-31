# Portable kit: independent engineering review checkpoint (2026-10-31)

**Scope:** strict review of the private draft `dchr-offline-kit-v1` assembler,
recipient verifier and nested application source archive. No changes to
`main`, the three immutable C130 archive assets, OneDrive or live SCADA.

## Review findings and changes

1. **Verifier provenance (correctness, high impact).** Earlier builds used
   `Path(__file__).read_bytes()` from the local working tree to create the
   recipient's standalone `verify_portable_kit.py`, but used
   `git archive <commit>` for `code/repository.zip`. An uncommitted edit
   could produce a mismatched verifier and application, despite a pinned SHA
   for the application snapshot. The builder now extracts the verifier
   **from `tools/portable_kit.py` in the same committed Git archive** and
   refuses to ship a code tree missing that file. An adversarial test
   intentionally dirties the local copy and verifies that the recipient
   receives the committed archive version instead.

2. **Nested code archive symlinks (security, high impact).** Application
   entries were checked for normal path traversal and sensitive names but not
   for Unix symlink metadata. The validator now rejects link entries using
   `ZipInfo.create_system` and `stat.S_ISLNK`. The new test constructs a
   synthetic symlink entry `tools/doclink` with target `../private` and
   confirms rejection.

3. **Portable case collision (security, medium impact).** Files in the
   nested application archive are now checked for case-insensitive path
   aliases before distribution, matching Windows recipient behavior. A
   synthetic `tools/Readme.txt` + `tools/readme.TXT` test rejects the
   collision.

4. **Recipient does not use Git.** Bundle verification also validates the
   **nested code archive** before creating a recipient directory, including
   symlinks, paths, source allowlist and high-confidence credential
   signatures. Only standard-library Python is required by the recipient.

5. **Resource safety.** The nested source archive validator enforces
   at most 20,000 entries and 1 GiB of declared decompressed content.
   This is a guardrail for the code portion, not a guarantee against every
   form of ZIP or filesystem resource exhaustion.

## QA and explicit limits

Targeted portable kit regression suite contains **10 tests**, passing on
Windows 11 / Python 3.14 and Ubuntu 24.04 WSL / Python 3.12. The tests
cover real Git-producer builds, mutation of the working tree, unsafe ZIP
metadata, corrupt or duplicate bundled assets and Git-free recipient use.

This is **technical self-review with regression evidence**, not an
independent human security audit, exhaustive secret scan, legal
redistribution clearance, physical controller certification or production
release approval. As before, recipients must compare a full-kit SHA-256 from
a trusted independent channel. Keep PR #1 in draft until reviewed.
