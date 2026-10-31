# HANDOFF | DataCenter A37B TES SOC | 2026-10-26

Existing Synapse task: scc-3d9d172beb6e1b (review). No new task, worker, Codex session, GPU process or shared GUI edits.

Inputs: original v04 MATLAB TES allocator, v08 synthetic 672x15min CSV, A36 both-off derived CSV. Source hashes in RESULTS_A37B.json.

Implementation: tes_soc.py, test_tes_soc.py, independent_qa.py. 11/11 unit tests PASS; 672 rows/8064 Decimal checks PASS. Baseline v08 TES reproduced within 5.01e-6 J. 6 charge clipping intervals, first t=69h; curtailed charge 75.688 kWh; +61.346 kWh REJECT; 14.342 kWh HP compressor proxy reduction. All synthetic.

First test run failed due to incorrect test expectation that full TES must accept zero charge; v04 correctly permits charging enough to offset thermal loss. Test corrected, rerun passed. No source production edits.

Previous A37: N-1 IT thermal model registered event 1216, 16 unit tests + 104832 independent checks; see sibling A37 directory. Current A37B event and SHA in REGISTRY_RESULT.json / SHA256_MANIFEST.json.

Live admission baseline 2026-10-26 10:23 CET: primary SynapseMCP Web online, 1.971 GiB RAM free, GPU 1834/8188 MiB, 361 worktrees, registry quick_check OK, STOP/PAUSE not found in seven checked roots (not exhaustive), no registered running tasks. Processes SCADA 5264, FUXA 16288, MATLAB bridge 6124; do not assume PIDs remain current.

Exact next action: verify STOP and ownership again, then port A37 thermal N-1 + A37B TES SOC together into an isolated MATLAB/Stateflow candidate with actual fault switching and HP COP curve. Compare 672 steps and reject heat balance, then obtain real equipment ratings and measurements. Shared v85 SLX, SCADA and OAuth must remain untouched.
