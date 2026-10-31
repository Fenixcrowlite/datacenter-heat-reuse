# Synapse autonomous handoff | A36 + A36B | 2026-10-26

## Verified this run

Primary SynapseMCP Web ping 07:45:04 CET OK, control_enabled=true. Read NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel.md, workstream-isolation.md, registry-task-lifecycle.md, synapsemcp-web-concurrency.md, A35B handoff and DCHR v07/v08 source. Did not assume old handoff live. Live resource check at 07:51:02 CET: free RAM 2.452 GiB, VRAM 1640/8188 MiB, GPU 0%; 361 Jarvice worktrees. Existing SCADA PID 5264, FUXA 16288, Jarvice 8860/35484, MATLAB bridge 6124. Synapse 209 tasks, existing DataCenter task review/planned/worker_pid NULL. STOP/PAUSE absent in checked roots; no exhaustive recursion claimed.

## A36 | Independent instantaneous energy-balanced redispatch

Directory: `C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE`.

Implemented conservative Python reference for pool/DH OFF, capped loads, HP/HX/TES discharge/reject reallocation with fixed per-interval COP proxy. Replayed 672 existing synthetic v08 samples x 6 scenarios; 17/17 unit tests PASS; 20833 independent CSV checks PASS across 4032 intervals. Original v08 SHA256 `5a976573e27d52e25c74e056ece807c7fdc13a8884c130117b1a8ab426f69bf3` unchanged. Both OFF after 24h: max required reject 213.6295 kW, delta rejected heat +16730.698881 kWh relative to baseline.

Synapse existing DataCenter card scc-3d9d172beb6e1b **event 1209**, idempotency rerun EXISTING_EVENT; evidence SHA256 `ea34ef6226bd1256220bea0cea9d803b24a173915fd1978743c9d93b0b7424f0`. Handoff SHA256 `894829bd164aa3a09bc1807cbdc64810748aabc3629e6f0c366cbffb5d69adc5`.

## A36B | Source-backed synthetic REJECT redundancy N-1

Directory: `C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261026_0752_A36B_REJECT_N1_ENVELOPE`.

Discovered MATLAB v07 source `fyzikalne_ochrany_v07.txt` explicitly defines REJECT A=180kW, B=150kW as **scenario values**, not hardware-certified ratings. Source SHA256 `00e7350db86fe98773992cac6fc7f4a442d579f89d60ba75a278f902829a1252`. Analyzed 24 combinations (six A36 load scenarios x four reject availability states). Both consumers OFF: A+B (330kW) 0 overload intervals; only A (180kW) 171 intervals / 42.75h / 636.609653 kWh excess; only B (150kW) 358 intervals / 89.5h / 2543.427491 kWh excess; neither 576 intervals / 144h / 22976.385584 kWh excess. These are no-shedding fixed-load hypothetical excesses, NOT physical failure predictions.

QA: 10/10 tests PASS, independent Decimal check, source SHA check, 24-row scenario CSV. Synapse **event 1210** in existing DataCenter card; idempotency rerun EXISTING_EVENT. Evidence SHA256 `db1ec79972d27faf6890350ac19bf96a3b5ac8567f11a4befd4f150a58224f4b`; manifest SHA256 `0493cd4f6754759338e5b80914d363b921f11f24364991f6c3a8e638427432f5`.

## Exact next executable step and restrictions

1. **Model owner:** in OWNED Simulink/Stateflow copy integrate A36 redispatch and A36B REJECT A/B availability with TES SOC, reject derating, IT shedding, compressor part-load COP and pool/DH dynamics. Run 672-row synthetic regression and failure-safety cases. **No model/SCADA source modified in this run.**
2. Obtain real certified reject capacity and measurements. The v07 180/150kW values are synthetic scenario parameters, not manufacturer data. Physical acceptance remains BLOCKED.
3. EduMotion S04 still awaits human audiovisual review and TTS rights; dispatcher A19 requires ownership transfer. VRS skipped.
4. Resource guard: avoid GPU workers, new Codex sessions and shared GUI writes. Existing processes and STOP/OAuth untouched.

No new task cards, Codex sessions, persistent workers, GPU jobs, public actions or paid services. Automation is discrete, not continuously running between invocations.
