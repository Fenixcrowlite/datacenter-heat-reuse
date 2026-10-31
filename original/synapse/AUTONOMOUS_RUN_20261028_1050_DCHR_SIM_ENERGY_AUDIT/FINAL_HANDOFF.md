# DCHR simulation energy audit | 2026-10-28 10:50 CET

VERIFIED isolated annual simulation audit; 8760 rows, 13/13 unit tests PASS, independent float-based 9/9 energy totals PASS. No source CSV or production edits.

DISCOVERY: naive HP_Heat=HP_Source_Used+HP_Electric failed in 4587 hours because HP_Heat is potential output; correct identities are HP_Heat_Used=HP_Source_Used+HP_Electric and HP_Heat=HP_Heat_Used+Curtailed_HP_Heat. Both now 0/8760 violations, regression test added.

SIMULATED PUE ~1.2, curtailed heat 22545.421 MWh (~32.414% of potential), NOT metered/certified. ERF/REF/WUE deliberately unavailable; 0/31 primary signoffs.
Source SHA256: 8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25
Evidence SHA256: 38f38f31bf88cdf6f5780243a4036e05867930867746322083877da32c23b5bd
Manifest SHA256: c3152418100ab493592b3cc6f7733f25f48d1edb083f2a3ac1f745eb50606a1d
Existing Synapse task scc-2aab24704c2bd0, evidence event #1382; task remains queued.
Live snapshot at intake 10:47 CET: RAM free 7.34 GB, VRAM 733/8188 MiB; STOP absent in checked roots, existing workers/worktrees not touched. No Codex, GPU jobs, GUI, VRS, OAuth, external publication or expenses.
NEXT: Obtain authenticated measured E_DC/E_IT/E_REUSE/E_RES/W_IN with explicit measurement boundaries; reconcile heat-pump electricity and DC perimeter; only then calculate regulatory metrics. Keep primary source signoffs 0/31.
