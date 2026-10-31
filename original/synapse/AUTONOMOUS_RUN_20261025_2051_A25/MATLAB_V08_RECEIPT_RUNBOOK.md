# DataCenter v08: independent MATLAB execution receipt gate

Scope: standalone **read-only** verifier for the existing synthetic v08 replay. No changes to the OneDrive MATLAB model, scripts, CSV, running MATLAB session, SCADA or GUI.

## Current evidence and gap

The current v08 package has eight synthetic replay CSV files, an independent QA JSON and source/model SHA values. They prove stored-artifact consistency, **not** that a particular MATLAB executable produced these outputs in a recorded process invocation. The gate checks 13 current source/output SHA256 values and looks for bounded, filename-matched receipt/log candidates. Absence in those checked directories is not proof of absence on the entire computer.

## Contract for a future *owner-authorized* capture

After the MATLAB workstream owner explicitly acquires execution ownership, capture a new MATLAB process with a trusted shell runner and a unique private log. The runner, not MATLAB's output text, must record process PID, executable path, executable version, exit code, UTC start/end and SHA256 of the script, model, input manifest, QA, result summary, eight output CSV files and the final log. Do not modify or overwrite the existing release outputs without owner approval. Prefer a copy in an isolated worktree with a distinct output directory and capture hashes after process exit. Never fabricate a run log or infer success from static CSV.

The receipt JSON schema is `dchr.v08.matlab_execution_receipt.v1`. Mandatory fields: `schema`, `source_class="D_SYNTHETIC"`, `exit_code=0`, `matlab_release="R2026a"` (actual release), `started_utc`, `finished_utc`, `sha256` map for the exact five input paths, `outputs` map keyed by the eight scenario names, `log_file` (relative to receipt directory) and `log_sha256`. The log must contain exactly eight distinct `V08_REPLAY_PASS <scenario> T_delta=...` lines and one final `V08_ALL_REPLAY_CASES_PASS 8` after them.

Example validation, **does not launch MATLAB**:

```powershell
python v08_matlab_receipt_gate.py --receipt C:\path\to\owner_receipt\receipt.json --output C:\path\to\new_unique_audit.json
```

A PASS validates receipt **internal consistency only**. Independent MATLAB execution attestation requires a trusted external process capture, reproducible rerun, and separate model/physical validation. Real-world measurement, standards compliance and pool safety are not established.

## Failure gates

Rejects wrong synthetic provenance, mismatched model/CSV/source hashes, changed QA manifest, missing or duplicate scenario markers, final marker out of order, nonzero or boolean exit code, naive or reversed timestamps, missing log, log hash mismatch and path traversal. Mutation tests use isolated synthetic fixtures only.

Next engineering step: owner-approved MATLAB v08 run in isolated output scope with a trusted capture script and then feed the resulting receipt to this gate. No unattended MATLAB launch is authorized in this checkpoint.
