# A67 read-only replay | 2026-10-27T16:53:26+01:00
A66 repeat finalizer exposed a changing timestamp; original A66 artifacts and event remain intact.
New read-only replay gate: 7/7 regression tests, 10/10 real SHA checks, repeated output identical, 0 mutations.
Temporary SQLite handles explicitly closed after tests; initial Windows lock failure corrected.
No Codex, GPU, VRS, shared GUI, OAuth or foreign worktree changes.
Evidence SHA256: f475b40213f15b2a1f3f8418478ab3da7323ca1759ac480f6c25e3f425e064fa
Manifest SHA256: 7c4c6d72710815e4f0eba1d2784ad24c72f3179d25b0f88da6f34fd5de28ad1e
NEXT: Use a stable checkpoint timestamp in future finalizers; do not rewrite already registered A66 evidence.
