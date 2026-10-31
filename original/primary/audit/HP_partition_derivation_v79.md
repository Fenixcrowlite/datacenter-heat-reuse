# Temperature-dependent HP energy partition v79

Engineering-assumption traceability: this release audits the existing reduced
v75 HP equation. It adds no primary-source signoff, measured calibration or
paper-replication claim. Heating COP here is 1 + A/L, with A = eta*(Te+273.15),
Te = source inlet - source cooling - evaporator approach, and L = hot water
proxy + condenser approach - Te. The hot proxy is max(floor, Ta+E/C+water rise).
These refrigerant/water approximations remain uncalibrated.

For held heat power Q and duration d, source rate = Q*A/(A+L) and compressor
rate = Q*L/(A+L). A and L are positive. The TES equation E' = B-lambda*E
with constant B and lambda >= 0 has a derivative of constant sign, including
the lambda=0 affine limit. Consequently the start/end inventory hull extrema
bound all intermediate E, hence L lies in [Lmin,Lmax]. The floor max is monotone.

The source fraction decreases with L and increases with A; the compressor
fraction increases with L and decreases with A. Therefore source integral lies
in H*[Amin/(Amin+Lmax), Amax/(Amax+Lmin)] and work integral lies in
H*[Lmin/(Amax+Lmin), Lmax/(Amin+Lmax)], where H is the segment heat energy hull.
These are necessary integral bounds, not a quadrature reproduction. Units:
A,L are kelvin; fractions dimensionless; H, source and work are MWh.

The runtime contract requires overlap of recorded integral enclosures with
these bounds, rather than requiring the larger quadrature hull to fit inside
them. Overlap can reject disjoint impossible records but does not prove every
member of a wide recorded hull physically admissible. Exact OFF power requires
exact zero source/work. Independent Python Fraction arithmetic derives the
bounds directly from exact binary operands without the MATLAB eps operator,
thermal solver, root finder or subdivision loop. The existing high-precision
closed exp/log lane separately verifies full original-MAT trajectories.

The saved v79 chart preserves the v75 thermal kernel, trace schema 75, v76
reporting API and v78 energy/temporal gates. All six states check v79 before
trace emission and retained-memory commit. Paired source/work redistributions
in unsaved chart copies also update their auxiliary, interval and cumulative
copies. They preserve first-law balance and pass v78, but contradict the
temperature partition and must fail v79. Such fault records are QA controls,
never plant results. Clean models are reopened after instrumentation.
