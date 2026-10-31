# Stateflow temporal verification before retained-state commit v77

Model release 0.77 retains trace schema 75, the unchanged embedded v75 thermal
kernel, and compatibility with the v76 reporting API. This is an engineering
consistency guard, not an equipment calibration or primary-paper equation.

## Why a saved model is needed

The accepted v76 reporting API detects temporal inconsistencies after a saved
v75 simulation. It does not execute inside the chart before its candidate
record becomes retained memory. Release v77 places an embedded monitor in both
entry and during actions of every one of the six states, between kernel
evaluation and `trace=core; retained_memory=core;`. Transition guards still
evaluate the unchanged kernel. Solver ticks are protocol calls; intra-interval
events retain physical-time hulls and symbolic contacts.

## Equations and identities

Incoming E, latch b, age A, contact g and clock c come from the preceding
retained record. On the first call, they are initialized from physical input
fields 10:12 and zero clock/contact. Macro start and inventory copies must equal
these values. The held boundary is outward(c + [dt,dt]) and both recorded copies
must equal that result. The monitor binds the immutable policy, source capacity,
binary duration and enable commands to the actual input.

Starting with elapsed hull t=[0,0], each segment must preserve incoming E,b,A,g
and record elapsed=outward(t+d) for its positive duration hull d. Reason 1
changes OFF to ON; reasons 2/3 change ON to OFF. Only these explicit boundary
changes reset age before a segment. The stop event resets latch and age and
records stop tag 1. Cutoff preserves latch, adds duration to age and records
tag 2. Restart sets ON and resets age, recording tag 3 for a thermal contact
and zero for a dwell-only restart. Non-events advance age and clear the tag.
These are the existing protocol semantics, not newly derived dispatch rules.

All interior segments require events; the final segment requires event zero
and duration=outward([dt,dt]-t). Its endpoint E,b,A,g must match the header.
Final mode and event count must match the segment sequence. Unused slots must
remain zero; complete finite schema-75 records and integer count 1..16 are
required before dynamic indexing.

The production arithmetic uses the kernel's deterministic binary64 operator:
out([lo,hi])=[lo-2*eps(lo),hi+2*eps(hi)], retaining exact zero-operand and scalar
cancellation identities. Equality checks apply to protocol copies, not physical
accuracy tolerances. Thermal conservation and nonnegative port assertions
remain in the unchanged kernel, with offline energy reconstruction in v76.

## Execution and independent QA

The builder saves a new SLX without overwriting any baseline. The harness closes
and reopens it, executes real normal-mode Stateflow simulations, and compares
every output double with freshly executed saved v75 on identical schedules.
Six required modes, three interior event types, source/demand/enable changes,
variable holds, exact ON dwell and multiple cycles are exercised.

Fault controls modify only an unsaved in-memory copy of the embedded kernel.
Each changes specified output fields immediately after a completed valid kernel
evaluation. The active monitor must fail with the expected runtime assertion.
Removing monitor calls in this unsaved test copy must allow the exact isolated
fault to appear in the trace, proving that the injection was reached. Instrumented
models are never saved or labelled as physical plant trajectories. The clean
saved SLX is reopened after instrumentation and compared again.

Python consumes binary64 exports made after MATLAB reopens the original MAT.
Fraction arithmetic independently checks exact temporal enclosure sums and
differences, links and reset identities. Closed exponential/logarithmic equations
at 120 and 160 digits independently check nonlinear TES trajectories, events,
source/compressor integrals and all energy totals. Python calls no production
MATLAB function and does not reproduce its eps-based temporal operator.
Archive inspection binds exact embedded kernel/monitor source and checks all
six pre-commit action sequences. Prior files and ledger prefixes are hashed.
Separate synthetic reviewer corruptions are distinguished from runtime controls.

## Limits

Same-agent algorithmic independence, not independent personnel. Binary exports
depend on MATLAB reopening, not an independent HDF5 reader. This guard validates
temporal protocol consistency; it does not prove every nonlinear event/dwell
inequality or defeat coordinated internally consistent record substitution.
Synthetic bounded normal-mode schedules only; inherited collision/span/clock/
segment-budget refusals remain. No annual, generated-code, calibrated equipment,
primary article replication or measured physical validation claim.
