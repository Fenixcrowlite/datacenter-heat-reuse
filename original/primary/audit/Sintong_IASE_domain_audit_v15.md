# Sintong IASE free-cooling domain audit v15

Completed research/mathematical task: establish a two-stream applicability gate for the existing interpretation of Sintong Eq15-16 and trace Park [38] to primary text. The main finding is conditional: an unrestricted constant coefficient in the thesis flow-function composition can satisfy the return-air supply target while exceeding the outdoor stream's available heat capacity. This establishes an adoption/domain defect, not an error in the authors' executed annual simulations.

## Evidence and scope

Before edits, read STATUS_v14.json, MASTER_STAGEBOARD_v14.md, audit/research_frontier_2026_10_08.md, automation/engineering_progress.md, the v06/v07 Sintong audits and equation scripts, and existing MATLAB source/HX/HP components. Earlier Eq17/24 corrections were treated as existing evidence and were not re-presented as new results.

The local original thesis `sources/papers/09_Sintong_Stockholm_2023.pdf` has SHA256 `8149370d2df0c5899c844095f3890fea112c3d81eaff6671cb3cf0f3da9185f5`. Printed page numbers equal PDF page numbers for the pages used here. Page23 identifies the IASE context; page30, section3.2.3, contains Eq15-16 and the supply-temperature criterion; page31 Fig14 shows two air streams; page70 contains reference38. These four pages were rendered and visually inspected. Timestamped text, PNGs and hashes are listed in `Sintong_IASE_primary_evidence_v15_20261008T220047_157053Z.json`. The Eq15-16 page locator is p30, more precise than the earlier audit's broad pp30-32 interval.

Faithful notation record from p30, with dot denoting mass flow:

```text
Eq15: T_RA* = T_RA + epsilon HX_flow_ratio(m_OA/m_RA) x (T_OA-T_RA)
Eq16: HX_flow_ratio = (m_OA+m_RA)/(2 m_RA)
```

The implemented diagnostic treats the parenthesized ratio in Eq15 as a function argument: `f(r)=(1+r)/2`, `alpha=epsilon*f(r)`. A separately labelled alternative treats it as another factor, `alpha=epsilon*r*f(r)`; this branch is a notation-sensitivity check only. Neither branch is verified author code. The thesis passage does not settle the coefficient normalization or unequal-flow calibration. Its supply criterion alone is not a physical-domain test.

Park and Seo (2018), Energies11(2),444, DOI10.3390/en11020444, is the exact reference38. Publisher full text was read, beyond metadata/abstract. Section3.3, PDF p9, prints Eq22 with `epsilon_HX(r)` and Eq23 with the same mean-flow ratio; it states a 70% HX-effectiveness setting and points to Ham et al. [21] for the model. This typography does not establish the thesis's expanded coefficient as a faithful executable transcription. Park PDF visual checking and a local original copy remain unavailable in this run. See `Park_IASE_provenance_v15.md` for precise evidence levels and access failures. [Publisher primary full text](https://www.mdpi.com/1996-1073/11/2/444), [publisher PDF](https://mdpi-res.com/d_attachment/energies/energies-11-00444/article_deploy/energies-11-00444.pdf).

## Independent derivation

Assumptions: steady sensible exchange, positive flows, equal constant air cp, no mixing, no storage, and no heat/work addition inside the exchanger boundary. Fan heat, humidity, frost, leakage and geometry are excluded. Let `C_RA=m_RA*cp`, `r=m_OA/m_RA`, `C_OA=r*C_RA`, and `D=T_RA-T_OA`. All temperatures are Celsius differences in kelvin; cp in J/(kg K) and flows in kg/s give C in W/K and Q in W.

```text
T_RA,out = T_RA-alpha*D
Q = C_RA*alpha*D
T_OA,out = T_OA+(alpha/r)*D             [derived by first law]
```

For unequal inlet temperatures, the return outlet lies in the inlet interval iff `0<=alpha<=1`; the outdoor outlet does so iff `0<=alpha<=r`. Therefore both outlet/first-law endpoint requirements are equivalent to

```text
0 <= alpha <= min(1,r)
|Q| <= min(C_RA,C_OA)*|D|
0 <= epsilon <= 2*min(1,r)/(1+r)        [flow-function interpretation]
```

For fixed `0<epsilon<=1`, the allowed interval is `epsilon/(2-epsilon)<=r<=(2-epsilon)/epsilon`. At scenario epsilon=.8 this gives `[2/3,3/2]`; at scenario epsilon=.7 it gives `[7/13,13/7]`. These are derived applicability bounds, not measured equipment ranges. An extra-r interpretation instead needs `epsilon<=2*min(1,r)/(r*(1+r))`.

Standard heat-transfer effectiveness has another definition: `epsilon_Q=Q/(C_min*D)`. A separately named engineering reference therefore uses `Q=epsilon_Q*C_min*D`, deriving both outlets from the same Q. It allows unequal cp and explicit zero-outdoor-flow bypass. The source composition is compatible algebraically with mean-capacity normalization, `epsilon_mean=Q/[((C_RA+C_OA)/2)*D]`; that interpretation is not attributed to the authors. Reusing the same numeric coefficient across these definitions is a scenario comparison, not a calibrated comparison of equipment.

Equal inlet temperatures give zero transfer and cannot identify an effectiveness normalization. Reverse inlet ordering reverses signed Q; it is not automatically a free-cooling control mode. Exactly zero outdoor flow requires Q=0, whereas Eq16's constant-coefficient continuation would imply heat removal at epsilon>0. Return flow zero makes Eq16 undefined. Endpoint admissibility is not proof of finite-UA or crossflow realizability.

## New counterexample and verification

Chosen test inputs, not paper data: return inlet35 C, outdoor inlet5 C, return flow1 kg/s, cp1005 J/(kg K).

| Outdoor/return flow r | Scenario epsilon | Return outlet C | Derived outdoor outlet C | Q W | Qmax W | Result |
|---:|---:|---:|---:|---:|---:|---|
| .25 | .8 | 20 | 65 | 15075 | 7537.5 | Supply criterion passes; outdoor capacity fails |
| 3 | .8 | -13 | 21 | 48240 | 30150 | Return outlet overshoots |
| .25 | .4 | 27.5 | 35 | 7537.5 | 7537.5 | Endpoint boundary |
| 1 | .8 | 11 | 29 | 24120 | 30150 | Both outlets admitted |

The first case is the new defect: checking only a 20 C return/supply target permits twice the maximum passive heat transfer. Energy conservation alone can conceal this by assigning an impossible outdoor outlet. A return-only clamp is inadequate; both stream capacities must determine Q before control eligibility.

Independent mathematical review is in `Sintong_IASE_independent_review_v15.md`. A second read of the diagnostic and test code found no material mathematical issue within the declared domain. Python verification passed15/15, failed0/errors0: 1342 exact rational endpoint points for the flow-function interpretation,671 for the alternative;2000 deterministic random passive-reference cases checked both-stream energy, endpoints and sensible-stream entropy;1000 random diagnostic cases compared direct outlets/capacity to classifications. Seed15026. A66-row CSV compares three scenario coefficients at eleven flow ratios and two notation branches against the separately normalized reference. This is a domain experiment, not annual energy savings or article-result reproduction.

Evidence: `Sintong_IASE_tests_v15_20261008T220043_794544Z.json`, `Sintong_IASE_domain_comparison_v15_20261008T220043_794544Z.csv`, and `automation/logs/Sintong_IASE_tests_v15_20261008T220043_794544Z.log`. The exact-point counts describe test loops; the CSV has66 comparison rows, not5013 independent experiments. Source extraction initially failed at the console's cp1251 encoding; explicit UTF8 extraction succeeded and the original hash passed. Local Park download failed with WinError10013; publisher parsed full text remained accessible. No failed acquisition is labelled a primary-original download.

## Disposition and handoff

- F15-IASE-01: conditional unrestricted-flow applicability defect confirmed in the diagnostic interpretation. Production adoption is blocked pending coefficient definition/domain or replacement with an explicitly defined physical model.
- F15-PROV-01: Park primary body text located and partially verified; typography/normalization and upstream Ham model still unresolved. Full primary-source signoffs remain0. No source simulation or measured-system validation is claimed.
- New code is an audit diagnostic and an independent endpoint reference. Existing MATLAB components, datasets and `.slx` artifacts were not edited. MATLAB/Simulink/Stateflow were not executed; Stateflow availability was not checked in this task.

Next engineering task: integrate `heat_pump_step_v14` into a separate finite-boiler/TES/unmet-demand dispatch, first reviewing TES parameter/time-step validation, then compare a deterministic multi-step trace with an independent Python reference before building a new Simulink model. Keep the unresolved IASE formula outside annual dispatch. The next research task is to acquire the upstream Ham primary model and author-code evidence for the Park/Sintong coefficient mapping.
