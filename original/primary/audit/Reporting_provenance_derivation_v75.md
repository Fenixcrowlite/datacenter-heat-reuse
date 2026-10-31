# Saved-Stateflow input provenance and reporting consistency v75

This is an engineering implementation repair, not a new heat-pump calibration,
article replication or physical validation. Read the executed results and
versioned status before interpreting its acceptance scope.

## Defect and boundary

The v74 reporter checks demand, policy, initial state, inventory continuity and
clock labels but copies ten cumulative energy hulls from the last trace header.
It does not reconstruct those totals or bind the source and enable operands to
the executed chart. Independent offline v74 QA does verify original traces and
reports. Therefore its sealed v74 evidence is preserved; the uncovered defect
is permissive production reporting of altered or misassociated operands.

Fresh saved-model execution and single-fault controls determine which defects
are reproduced. Legacy acceptance of a mutated trace is recorded separately
from physical execution: no corrupted trace is represented as a plant result.

## Additive actual model

The new builder writes `DCHR_Earliest_Dispatch_Stateflow_v75.slx`, preserving
v73r2. Its six Stateflow states, dispatch transitions and embedded thermal
functions retain v73r2 behavior. The new kernel changes only the schema marker
and previously unused three header positions:

| MATLAB column | Meaning |
| --- | --- |
| 2 | Trace schema 75 |
| 73 | Authoritative binary held duration, h |
| 74 | Held source heat-capacity rate, MW/K |
| 75 | HP_enable + 2 * charge_enable, exactly one of 0, 1, 2, 3 |

Demand remains checked against each segment allocation. Policy remains stored
in columns 76:100. Initial inventory/latch/age, physical clock, cumulative energy
and segment records retain their previous semantics. Stored input changes do
not reset controller memory. This is a provenance change, not a new controller
policy or solver-clock event implementation.

For identical inputs, every output double outside columns 2 and 73:75 must be
bitwise identical to freshly executed saved v73r2. The model is built, saved,
closed by its builder, reopened, and simulated in normal mode. Archive QA checks
that the saved chart embeds the exact versioned kernel source.

## Reporting reconstruction

The v75 reporter first re-encodes the supplied schedule using the accepted v74
boundary adapter and requires equality of its complete input and protocol-tick
operands. It then binds duration/source/command columns to the actual v75 trace.
It rejects v73 traces rather than claiming missing provenance.

For energy hull x = [xL, xU], y = [yL, yU], the reconstruction uses the saved
kernel's same deterministic outward operation:

    plus(x,y) = [xL+yL - 2*eps(xL+yL), xU+yU + 2*eps(xU+yU)]

Zero operands and exact scalar cancellation retain the saved kernel identities.
Each segment offset must equal the sum of preceding segment energy hulls; each
interval header must equal the sum of its segments; and every cumulative header
must equal the sum over all executed intervals. No midpoint is substituted.
Nonnegative ordered energies, positive-duration segments, integer counts,
unused zero slots, final mode and event count are checked explicitly.

Selected segment port identities are reconstructed with the identical outward
product operation: HP heat = (direct + charge)*duration, delivered service =
(direct + discharge + backup)*duration, backup and unmet energy = their port
powers * duration. HP heat must overlap source + compressor work; auxiliary
work must equal the prescribed auxiliary multiplier times compressor work.
The cumulative residual is recomputed as:

    initial_TES + HP_heat + backup_heat - delivered_service - final_TES
      - standing_loss - charge_loss - discharge_loss

Its saved hull must match the reconstruction and contain zero. These gates
detect inconsistent records. They are not cryptographic authentication against
coordinated replacement of inputs, segments, headers and provenance together.

## Independent QA

Python reads binary64 exports from the reopened original v7.3 MAT. The existing
independent closed exp/log reviewer derives storage trajectories, event times,
source integrals, compressor work and every energy total using exact-binary
Fraction operands and 120/160-digit Decimal arithmetic. It never calls the
production kernel, adapter or reporting validator. Only after independently
checking schema 75 and the three provenance operands does it map those schema
positions back to the inherited v73 reviewer format. Original v75 columns remain
in saved MAT and binary evidence.

Actual MATLAB corruption controls demonstrate permissive legacy reporting and
the new report refusal. Separate synthetic reviewer corruptions verify the
independent report-containment checks. Counts remain separate. Actual changed-
source simulation distinguishes input misattribution from a harmless metadata
change. Preservation hashes and append-only ledger prefixes protect prior work.

## Limits

Same-agent algorithmic independence, not independent personnel. MATLAB reopens
MAT; Python reads its binary exports, not HDF5 independently. Synthetic bounded
schedules only; inherited thermal/span, ordering, dwell, clock and segment-budget
domains remain. The consistency validator does not replace independent thermal
equation QA or validate every coordinated adversarial alteration. No annual,
generated-code, equipment-calibration, article-replication or measured-validation
claim. Primary signoffs remain 0/31.
