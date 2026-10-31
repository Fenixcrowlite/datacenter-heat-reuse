# DataCenter A45 | synthetic HP compressor source-capacity lag

A new Python-only isolated coupled reference extends A43 finite-trip thermal
simulation with first-order startup/ramp dynamics of available heat-pump
evaporator extraction. The recurrence is exact for zero-order-held targets:
C[k+1] = C[k] + (1-exp(-900/tau))*(Qtarget[k]-C[k]).
Actual HP extraction is min(Qtarget, C[k+1]). Compressor electricity and
condenser heat are recalculated from actual extraction and synthetic COP.
TES, IT, REJECT and user balances are recomputed, not patched post-hoc.

Seven synthetic 672-step scenarios completed; 12/12 Python tests PASS;
18,816 independent Decimal balance checks PASS across 4,704 intervals.
Tau=0 reproduces A43 for 3 tested scenarios/115 samples each.
This is a reference model only, NOT A45 Simulink integration and NOT
physical compressor identification. Compressor internal thermal storage,
coastdown electricity and real HP minimum-on/off limits remain absent.
Physical release BLOCKED; all parameters assumed.

Next: wire A44 graphical chart to this closed-loop reference in a new
isolated Simulink model, implement equivalent HP lag there, compare
7x672 trajectories and transitions, and independently QA any divergence.
