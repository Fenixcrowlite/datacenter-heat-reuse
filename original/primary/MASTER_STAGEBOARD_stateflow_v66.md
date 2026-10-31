# Executed sampled stop and repeated-cycle Stateflow checkpoint v66

UTC 2026-10-11T21:38:35.235052+00:00. New saved `DCHR_Interval_Dispatch_Stateflow_v66.slx` adds an
entire-interval thermal stop guard and actually executes four repeated charge,
cutoff and restart cycles at each of three binary timesteps. The original v65
stop witness reaches 9.70199459269636 MWh above the 9.6 MWh stop while remaining
below 10 MWh capacity. Same-input v66 withholds charge and remains below stop.
This strengthens the sampled contract; previous capacity-safety acceptance is
preserved. No earliest-event Stateflow replacement is accepted.

MATLAB 1317 PASS / 0 FAIL; independent 29497
PASS / 0 FAIL; 16 actual runs / 421
protocol ticks / 401 service intervals, all six modes,
10 actual runtime fault rejections, 385 v30
comparisons, eight separate reviewer corruptions detected. Each repeated run
observes four shutdowns and three restarts after the initial ON state. Retained
inventory, cumulative ports, age and physical-clock bounds survive every step.

Independent earliest comparator uses the SAME binary equipment and 52-hour
demand/source schedule with 2 MW boiler limit. Across all resolutions it delivers
26.933679986 MWh and leaves 21.066320014 MWh unmet; boiler energy is 16 MWh.
Numerical event roots and all ports agree at 120/160 digits. Actual sampled
service losses below are engineering policy consequences, not measured results.

| dt (h) | Sampled delivered (MWh enclosure) | Sampled unmet (MWh enclosure) | Earliest minus sampled upper service (MWh) |
| --- | --- | --- | --- |
| 0.25 | 26.177181244–26.177181244 | 21.822818756–21.822818756 | 0.756498743 |
| 0.5 | 25.807207775–25.807207775 | 22.192792225–22.192792225 | 1.126472212 |
| 1 | 25.916440576–25.916440576 | 22.083559424–22.083559424 | 1.017239411 |

The differences are NOT monotonic with timestep: the v65 half-capacity charge
budget and v66 whole-interval withholding change the sampled decisions. No
convergence, optimization or physical-equivalence conclusion follows.

Evidence: `results/stop_guard_v66_final_20261011T213720530Z`: actual MATLAB logs/exit receipt, original reopened MAT,
binary exports, numeric CSV, independent QA and event comparison JSON, sealed
sources and preservation hashes. Earlier startup/setup/reviewer failures remain
in `results/stop_guard_v66_20261011T213334_742656Z`; the reviewer correctly rejected
that folder's stale source manifest after its indentation repair. Fresh final
execution uses the already saved model and corrected sealed reviewer.

Limitations:
- Conservative sampled stop guard and repeated sampled cycles only; general repeated exact-event Stateflow remains OPEN. Legacy v57 and sampled v65 acceptance preserved.
- Withholding an entire uncertified charge interval can shut down early and lose delivered service. Timestep service is not monotonic in these fixtures.
- Earliest comparator is separate 120/160-digit engineering mathematics with explicit root ordering threshold; no certified compiled earliest-event switching or source/compressor comparison claimed.
- Inherited correlated v64 prefix, exact host equivalent-limiter certificate, 128-rectangle source/work enclosures and |lambda*dt|<=1 domain remain.
- Fixed refrigerant/water approaches, common tank return and cooling factor are engineering assumptions; equipment calibration, article replication and measured physical validation are untested.
- Same-agent independent algorithms, not independent personnel. Original MAT reopened/exported by MATLAB; standalone generated code and Python HDF5 parsing not accepted.
- Sandbox startup, initial MATLAB JSON vector setup and reviewer indentation/stale-manifest failures preserved in the earlier development evidence folder.

Next actionable task: Derive certified local thermal-stop/cutoff/restart root brackets for repeated v66 trajectories and integrate one repeated earliest-event cycle into an additive SAME six-mode chart. Carry original inventory/ports/age/clock correlation, certify OFF dwell and ordering against held demand/source boundaries, reject unresolved ordering, and compare original-MAT service and source/work enclosures to the independent v66 event reference. Use the v66 stop witness and repeated dt=0.25/0.5/1 schedules as regression fixtures; preserve v57-v66. Primary calibration and measured validation remain OPEN.
