# Annual nominal-COP dispatch audit — v47

Scope: deductions from preserved project code, not article equations or equipment
measurements. All inputs remain synthetic engineering assumptions. Accepted
saved Stateflow v42 uses HP step v40; annual v13 delegates to v2 and is a
different dispatch. No annual Stateflow equivalence is assumed.

Let source availability S, HP output Q, capacity H and request R be in MW;
nominal heating COP C0, minimum COP Cm>1 and penalty r in [0,1) are dimensionless.
Legacy capability is Q0=min(H,S*C0/(C0-1)). Chosen output Q<=Q0 is then assigned
C(Q)=clip(C0*(1-r+r*Q/H),Cm,Cmax), W=Q/C(Q), Qev=Q-W.
For the valid domain C0>=Cm and H>0, C(Q)<=C0. Hence

    Qev = Q*(1-1/C(Q)) <= Q*(1-1/C0) <= S.

Reducing heating COP increases compressor work at fixed delivered heat and
DECREASES evaporator extraction. The nominal-potential/operating-COP sequence
therefore implies conservative source use in this domain, not a source violation.
This is a scoped mathematical statement, not validation of arbitrary configs.

Where Q=Q0<H and C(Q)<C0, Qev<S. If request permits a larger Q, the output is
nonmaximal. Let a=C0*(1-r), b=C0*r/H (units MW^-1). On an unclipped branch,

    F(Q)=Q*(1-1/(a+b*Q)),
    F'(Q)=1-a/(a+b*Q)^2 > 0 on C(Q)>1 and C(Q)>=a,
    b*Q^2 + (a-1-b*S)*Q - a*S = 0.

For B=a-1-b*S >=0, the positive root can be evaluated without cancellation as
Qstar=2*a*S/(B+sqrt(B^2+4*b*a*S)). For B<0 use
Qstar=(-B+sqrt(B^2+4*b*a*S))/(2*b). When b=0, Qstar=S*a/(a-1).
The independently verified output is min(R,H,Qstar), provided the chosen COP
law is the same and its cutoff domain is met. Legacy upward COP clipping and
v40 operating cutoff differ outside this domain; comparisons must label that.
All terms in the quadratic have units MW. S=0 or R=0 gives Q=0.

Annual audit requests use the SAME starting TES energy E_k and legacy loss-first
room: R_k=demand_k+min(chargeLimit,(capacity-E_k*(1-loss*dt))/(etaC*dt)).
The resulting extra capability is a static per-interval diagnostic. Summing it
does not establish realizable annual extra delivery, cost savings, reduced unmet
heat or a revised TES trajectory. Any correction must redispatch the whole year.

Independent QA uses a 60-digit Decimal closed-form root, not production bisection;
recomputes source/HP/service laws from saved annual CSVs; independently checks
actual saved-v42 segments and MAT reopening; verifies baseline preservation.
Synthetic reviewer mutations are separate from actual execution evidence.
