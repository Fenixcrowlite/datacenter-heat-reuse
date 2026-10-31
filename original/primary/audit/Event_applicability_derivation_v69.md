# Event applicability and forcing audit v69

This is a focused integration-defect audit of the preserved saved v68 model.
It does not implement earliest-event dispatch or revise accepted plant physics.
All equipment constants and synthetic schedules come from the existing project
fixtures. No new primary article equation or calibration is claimed.

For a held segment the reduced storage balance is

\[
\dot E=B-\lambda E,\qquad
B=\eta_C q_C-q_D/\eta_D.
\]

The independent reviewer uses the closed form

\[
E(t)=B/\lambda+(E_0-B/\lambda)e^{-\lambda t}
\]

for positive loss, and `E(t)=E0+B*t` for zero loss. A decreasing threshold
`G` has root

\[
t_G=-\log[(G-B/\lambda)/(E_0-B/\lambda)]/\lambda,
\]

when the ratio is strictly between zero and one. For zero loss and negative
forcing, `tG=(G-E0)/B`. Dwell readiness is
`max(tG, max(0, minOFF-age))`. Roots must be certified using the forcing of the
enabled proposed segment; a mathematically correct root of a different forcing
does not establish a dispatch event.

## Three candidate defects

1. The v68 cutoff observer uses `-min(demand,disLimit)/etaD` even when the
   sampled controller serves the entire demand directly through the HP and
   allocates zero TES discharge. With zero loss, actual inventory is constant.
   A hypothetical full-discharge near-contact can therefore cause strict
   ordering rejection despite no actual cutoff event. Exact binary inputs are
   reviewed; the decimal fixture label is not proof of an exact root tie.
2. The stop observer uses full available charging power while the retained HP
   latch can be OFF with unsatisfied OFF dwell. A strictly interior hypothetical
   stop root is then not actionable. Actual zero charge and zero loss leave
   inventory unchanged below the stop. The observer is still valid as a
   hypothetical-path observer; it is unsafe to consume as an enabled event list.
3. The restart observer always assumes `B=0`. During an enabled OFF segment with
   TES service, actual `B=-qD/etaD` can cross the restart threshold before the
   horizon while passive cooling does not. The independent root and dwell
   comparison establish a missing eligible restart candidate, not an error in
   the deliberately sampled service policy or an accepted event controller.

The actual chart harness executes the required six baseline modes, strict and
non-strict controls, a delayed valid prefix and forced-restart probes. The
reviewer checks binary exports of original MATLAB-reopened MAT traces using
exact Fraction inputs and 120/160-digit Decimal closed exp/log algorithms.
Production uses outward Taylor arithmetic and bisection; no production MATLAB
function is called by the Python reviewer. Corruptions test inventory, service,
source accounting, mode, root brackets and the omission witness.

## Required repair before event-segment integration

Build a mode-conditioned candidate record with retained incoming inventory and
OFF-age hulls, held-demand/source boundary, selected direct/charge/discharge
ports, forcing hull, threshold identity and enablement reason. Evaluate restart
under the OFF segment's actual discharge forcing. Evaluate stop only for an
admissible charging segment and cutoff only for a discharging segment. Keep
strict root witnesses, root-time correlation and source/work/service offsets.
Reject ordering only among enabled event candidates. Do not use a midpoint or
silently remove a real boundary collision.

Regress these witnesses, genuine stop-boundary rejection, the v66 stop witness,
repeated dt=0.25/0.5/1 schedules and the v68 exact represented
lambda*duration=1 boundary. A new saved SAME six-mode chart must actually execute
the event policy before earliest-event implementation can be accepted.

Limitations: this is same-agent algorithmic QA, not independent personnel;
MATLAB-reopened exports are compared without an independent HDF5 parser.
Normal-mode conditional arithmetic, primary calibration and physical validation
remain open. Prior saved models and evidence are preserved.
