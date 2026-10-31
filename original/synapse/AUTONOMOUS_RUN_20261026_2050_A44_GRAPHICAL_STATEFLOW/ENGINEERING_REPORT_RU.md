# A44: graphical Stateflow transition acceptance

This isolated Simulink SLX contains a real graphical Stateflow.Chart with four
states: ACTIVE, TRIP_PENDING, TRIPPED, RAMPING, and seven transitions including
the default transition. It was constructed and executed in MATLAB R2026a.

Four deterministic synthetic 672-sample sequences cover nominal operation,
a one-sample transient fault, sustained loss of capacity, and interrupted
recovery with repeated faults. The chart matched a separate Python reference
on all 5,376 state/alarm values. Eight Python regression tests pass.

A short transient is cancelled without shutdown. A sustained fault enters
TRIP_PENDING for two samples, then TRIPPED. Recovery requires qualification
and proceeds through RAMPING. This is a supervisor-only validation, not the
closed-loop heat balance from A43. The A43 model remains unchanged.

The first MATLAB attempt failed because Simulink From Workspace blocks did
not allow extrapolation. The isolated build was corrected to interpolate the
extended final sample; the second MATLAB run passed all cases.

IMPORTANT: all inputs and timings are synthetic. No compressor inertia,
HP ramp dynamics, real equipment I/O, measured shutdown latency, or safety
certification has been added. Physical release remains BLOCKED. The next
step is to integrate this chart with A43 thermal dynamics and implement an
energy-conserving compressor ramp/lag model, then repeat the seven A43 cases.
