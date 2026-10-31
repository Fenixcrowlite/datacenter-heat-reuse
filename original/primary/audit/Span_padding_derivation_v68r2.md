# Outward-argument padding and Taylor remainder v68

This is an engineering numerical derivation, with synthetic test inputs. No
article equation, calibrated parameter or experimental result is attributed.

The v67 host root certificate admits the nominal represented product
`lambda*horizon <= 1`. Its flow helper, and the v66 plant helper embedded in
saved v67r2, form an outward interval for `x=-lambda*t` and then require every
expanded endpoint to satisfy `abs(x)<=1`. For exact binary inputs lambda=1/8
and t=8, the nominal product is exactly 1, but the expansion around -1 extends
below -1. The private helper therefore rejects an admissible boundary input.
At the adjacent representable t below 8, endpoint rounding reaches exactly -1
and the old implementation succeeds. Do not label that control a rejection.

For E'=B-lambda*E with held B, let v=B-lambda*E0 and x=-lambda*t:

    E(t) = E0 + v*t*phi1(x)
    integral_0^t E(s) ds = E0*t + v*t^2*phi2(x)
    phi1(x) = integral_0^1 exp(s*x) ds
    phi2(x) = integral_0^1 (1-s)*exp(s*x) ds

The existing degree-24 polynomials are

    phi1: sum_(n=0)^24 x^n/(n+1)!
    phi2: sum_(n=0)^24 x^n/(n+2)!

Numerical evaluation now has an explicitly checked outward domain |x|<=2.
This contains the rounding expansion at the nominal |x|=1 boundary. The public
root-domain test remains unchanged. A wider private domain needs a wider
proved remainder; retaining 3/26! after changing only the assertion is invalid.

Taylor's remainder for exp(s*x) on |x|<=2 is at most
e^2*|s*x|^25/25!. Integrating the two integral forms yields

    |R_phi1| <= e^2*2^25/26! < 8*2^25/26!
    |R_phi2| <= e^2*2^25/27! < 8*2^25/26!

The last common bound is intentionally conservative. An elementary bound
requires no rounded exp constant: sum_(n=0)^4 1/n! +
(1/5!)/(1-1/5) = 87/32 bounds e from above, and (87/32)^2 < 8.
The exact integer numerator 8*2^25 is 268435456. The existing outward
factorial/division calculations enclose this rational bound. Both polynomial
helpers now add its symmetric outward remainder. No argument clipping or
tolerance is used to choose an event side.

The standalone certifier, embedded observer and embedded plant flow are all
versioned. The kernel change is limited to its name, outward-span assertion
and common remainder; schema 66, allocations, source/water guards, port
accounting, clock handoffs and sampled policy are otherwise unchanged.
Interval widths may change; byte equality with older trace endpoints is not
an appropriate numeric acceptance condition.

Independent QA uses exact rational polynomial coefficients, Decimal exp/log
at 160 digits, all E/B/threshold corners, the integral-form remainder proof,
original-MAT binary exports, embedded archive sources and preservation hashes.
The exact boundary and adjacent controls are tested in the preserved saved
v67r2 model and host certifier; the corrected model additionally carries an
actual two-tick valid prefix into the formerly rejected duration.

The retained repeated dt=0.25/0.5/1 fixtures, six modes, finite domain faults,
near-boundary strict-order rejection and delayed strict-order rejection are
regressed in the same new saved chart. Root certificates remain observers;
this numerical repair does not claim earliest-event service integration.
Independent means separate mathematical algorithms by the same agent, not
independent personnel, calibrated physical validation or generated-code QA.

Proof revision: the conservative geometric tail ratio is 1/5, not 1/6.
The earlier sealed draft incorrectly equated the sharper 1/6 bound to 87/32.
The production numerator and its validity are unchanged.
