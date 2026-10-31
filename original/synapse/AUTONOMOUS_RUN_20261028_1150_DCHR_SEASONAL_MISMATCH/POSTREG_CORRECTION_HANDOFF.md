# DCHR seasonal mismatch | post-registration correction | 2026-10-28

The scientific artifact remains VERIFIED: 8760 simulated hours, zero simultaneous gas heating and curtailed heat-pump potential, 15/15 unit tests, independent Decimal QA (12 months and 120 counterfactual fields) PASS.

Post-registration QA found a defect in v1 finalize.py: the immutable handoff embeds transient registration state RECORDED or ALREADY_RECORDED. Rerunning v1 finalize.py therefore raises HANDOFF_CONFLICT. That failed retry did not insert a duplicate event. The original signed files, event #1384, and 10/10 SHA256 manifest are preserved.

The new read-only verify_recorded_evidence.py was executed twice, both PASS, with identical output, one unique event and SQLite integrity OK. For repeat verification, run this verifier rather than v1 finalize.py. The next artifact template should normalize registration state before comparing immutable handoffs.

This correction is a supplementary handoff, not a modification of the original. Source CSV, MATLAB/SCADA, VRS, OAuth, shared GUI, worktrees and secrets unchanged. No new workers or Codex.

NEXT: Build a physically constrained coupled storage simulation including additional HP electricity, COP, storage losses, charge/discharge MW limits and temperature bounds. Never claim the ideal counterfactual as measured savings.
