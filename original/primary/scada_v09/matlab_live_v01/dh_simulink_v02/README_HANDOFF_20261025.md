# Data-center heat reuse: Simulink DH v02 | Engineering handoff 2026-10-25

## CURRENT: BUILDER PREPARED / ACTUAL SIMULINK RUN BLOCKED BY RAM

Original saved v04 Simulink/Stateflow source SHA256 is unchanged:
0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0.

New isolated MATLAB script build_and_run_dh_v02.m was written. It is designed to:
- Copy the v04 source SLX into two new run folders and edit only each copy.
- Add a delayed temperature-feedback chart adjusting district heating demand u(3).
- Connect that feedback to the original v04 Stateflow dispatcher and thermal allocator.
- Add a two-water-volume dynamic DH model with state delays, load, losses, nominal pressure and pump power.
- Compare two matching 168-hour 672-sample cases: DH ON and DH OFF after hour 96.
- Verify first law, source/flow/pump switch-off, synthetic provenance and unchanged original SHA256.

## WHY MATLAB WAS STOPPED

A new isolated MATLAB R2026a batch was started, and free RAM fell from about 5.5GB to 360MB. I stopped only that owned MATLAB batch to avoid exhausting the PC, preserving existing user MATLAB sessions. Therefore the new SLX was NOT generated and the two new v02 Simulink runs are NOT verified. There are no legitimate new v02 energy claims yet.

The new run_guarded_v02.ps1 now refuses to run MATLAB unless free RAM >=7168MB. A real invocation returned BLOCKED_RAM and exit code 3 at about 1068MB free. STOP markers and ownership are checked. Do not reduce this threshold without a resource assessment.

## VERIFIED ARTIFACTS

- qa_design.py -> QA_STATIC_CHECKPOINT.json: 18/18 PASS, static model contract plus an independent two-node energy check using a previously SAVED v04 job; not new Simulink execution.
- dh_dynamic_pilot.py: previously completed D_ASSUMED Python thermal pilot; not the new SLX.
- historian_v04.py: separate opt-in SQLite visited-sample historian for v04 D_SYNTHETIC to D_DERIVED jobs, keyed by job ID, SHA256 and sample index. Preserves the native v08 historian and never invents measured source data.
- tests_historian_v04.py: 10/10 PASS, including deduplication, job isolation, untrusted identifiers, source provenance, and temporary DB cleanup.
- The new historian module has NOT been connected to the live SCADA HTTP routes. No deployed UI feature is asserted.
- At last check: native SCADA 8091, MATLAB v04 bridge 8094, and MQTT 18883 listening. STOP files absent; no new-owned MATLAB process left. Free RAM was about 1.9GB.
- Source v04 and v85 were not modified. No hardware / PLC commands.

## SOURCE PROVENANCE

v08 = archive CSV D_SYNTHETIC.
v04 = verified previous genuine Simulink run, synthetic inputs, D_DERIVED.
Python DH pilot = D_ASSUMED_DYNAMIC_DH_PILOT, uncalibrated.
New v02 SLX builder = D_ASSUMED DESIGN ONLY, compiled run blocked.
v85 full electrical Stateflow = separate untouched model, not integrated.
FUXA / Grafana = not deployed.

## NEXT ENGINEERING GATE

After RAM is safely available, execute the guarded script from this folder (do NOT bypass safety):
powershell -NoProfile -File .\run_guarded_v02.ps1

Independently review model ownership, STOP, run folder and memory before running. Check generated cloned SLX charts and actual two MATLAB simulations, fix failures only in this isolated revision, then independently reconstruct the first-law balance and compare DH ON/OFF traces. Only after actual PASS may v02 be offered in the SCADA selector as a separately labelled D_ASSUMED source.

18 static contracts plus 10 historian tests do NOT mean v02 Simulink sim() passed. No calibration, industrial safety, or field sensors are claimed.
