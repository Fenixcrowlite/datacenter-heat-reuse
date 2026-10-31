# Refrigerant approach sensitivity on saved Stateflow v80

Checkpoint 0.82 is a new experiment, not a new model release. The saved v80
six-mode chart, thermal kernel v75 and reporter v76 are preserved.

## Primary evidence and acquisition limit

The preserved source20 publisher PDF (SHA256
713d1ea564efacbb8813eafc474482292b167140e1b2f47d1e234d3db7302a6e)
was checked visually on printed pages 8 and 27. Section 2.1.1, Eqs (4)-(7),
defines compressor work, condenser heat, ideal cooling EER and the cooling
second-law factor. The temperature axes are refrigerant saturation temperatures
in Kelvin. The paragraph above Eq (4) describes evaporator/condenser pinches,
sink glide and minimum compressor lift. Its reference [62] is the validation
supplement for a commercial-device polynomial; no coefficient is supplied here.
This limited verification does not sign off the entire article or its database.

Reference [62]: [Rocchetti and Socci, TSEP 61 (2025), 103513](https://doi.org/10.1016/j.tsep.2025.103513).
On this run the [university repository](https://flore.unifi.it/handle/2158/1432822)
exposes metadata/abstract and explicitly lists no attached files. A new
[research-group route](https://www.dief.unifi.it/vp-278-research.html) identifies
the DOI but links to that DOI rather than a supplement. Publisher direct open
returned 403; its PDF route returned a tool cache miss. Indexed publisher text
is metadata/abstract, not acquired primary equations. These are access
observations, not proof of global unavailability. No correspondence was sent.

## Independent derivation of the implemented engineering reduction

Use the exact binary inputs of the saved model, with Kelvin conversion k=273.15:

    Te = Tsource - source_drop - evaporator_approach + k
    H = max(Tfloor, Ta + E/C + water_rise) + condenser_approach + k
    L = H - Te > 0, a = eta_cooling * Te > 0
    COPH = 1 + a/L
    source_power = q * a/(a+L)
    compressor_power = q * L/(a+L)

E is MWh, C is MWh/K, source_drop and both approaches are K, q and powers
are MW. This is a constant cooling-factor engineering backend, not the
unacquired reference [62] polynomial or the article's three-cycle architecture.
Auxiliary electricity remains a separately reported fraction of compressor
work, with no automatic thermal credit at the condenser.

For fixed q, fixed hot-water state and fixed source drop:

    d(COPH)/d(evaporator_approach) = -eta_cooling*H/L^2
    d(COPH)/d(condenser_approach) = -a/L^2
    d(W)/d(evaporator_approach) = q*eta_cooling*H/(a+L)^2
    d(W)/d(condenser_approach) = q*a/(a+L)^2

For a fixed evaporator budget S (MW), the unconstrained heating capacity is:

    q_source = S*(1 + L/a)
    d(q_source)/d(evaporator_approach) = S*H/(eta_cooling*Te^2)
    d(q_source)/d(condenser_approach) = S/(eta_cooling*Te)

Thus larger approaches lower COP and increase electricity at fixed heat output,
yet increase condenser output at fixed evaporator heat. Extra output is extra
compressor work; it cannot be described as more recovered waste heat. This
source-limited experiment has no independent compressor-electricity capacity.
That absent constraint is a calibration/architecture limitation, not a numerical
failure or evidence that worse heat exchangers are preferable.

## Predeclared experiment and independent QA

Two source-water temperatures (30,40 C), three evaporator approaches (1,5,10 K)
and three condenser approaches (1,5,10 K) give 18 points on each boundary:

- Fixed-output: demand 0.5 MW, ample source; source and work exchange while
  condenser delivery is fixed.
- Source-limited: source coefficient 0.02 MW/K, source drop 5 K (S=0.1 MW),
  demand 2 MW, backup disabled, initial TES below discharge cutoff. More output
  can reduce unmet demand solely by increased compressor work.

All 36 schedules have two 0.25-hour holds and disabled charging. Their tank
temperature stays below the hot-water floor, giving constant refrigerant axes
despite passive TES decay. Source drop, water glide, eta=0.5, auxiliaries and
all tested approach values are explicit synthetic assumptions, not fitted data.
Six acceptance fixtures additionally observe all required actual final modes.

QA uses exact Fraction arithmetic for boundary identities/derivative signs and
original-MAT binary exports. Separate 120/160-digit exp/log trajectories check
inventory, event logic, source/work/loss/service and reports without calling
production MATLAB code. A second constant-floor algebra calculation checks
each sensitivity point's source, work and heating COP directly. Comparisons
require disjoint reported work/delivery hulls where monotonic change is expected;
no hull midpoint is physical truth. Instrumented reviewer failures are synthetic
self-checks and never plant results. All prior MATLAB/model/checkpoint files
are checked for preservation. MATLAB reopens MAT to export binary; no independent
MAT-parser or independent-personnel claim is made.

No primary calibration, article replication, annual validation, measured plant
validation or generated-code acceptance is claimed.
