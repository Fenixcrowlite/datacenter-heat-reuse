# A65 mobile QA | 2026-10-27T15:58:08+01:00
Primary SynapseMCP Web available; STOP/PAUSE checked; existing task review/planned without worker.
Reproduced original A64 mobile overflow: 599px content in 390px viewport (+209px).
New isolated mobile_comparison.html; 320px, 390px and 1440px browser tests all PASS without horizontal overflow.
Preserved 2 tables, 10 rows, 60 cells, all numeric values and DERIVED_SIMULATION warning.
QA: 8/8 unit tests, 3/3 headless Chrome viewports; original browser failure CP1251 console encoding corrected and retested.
No modifications to A60-A64, shared GUI, browser profile, GPU, VRS, OAuth, Codex or foreign worktrees.
Evidence SHA256: c112e7aa77d8a6ffb1ac2bfff30391603bf44e19d37ef1275a0f018353bbad6f
Manifest SHA256: cea95ebd5ab515bc621e18a89f8d1d459cd47feb1eee3bab3aa9973da716fb8a
NEXT: Review the responsive offline report on actual mobile hardware; obtain calibrated measurements before physical validation.
