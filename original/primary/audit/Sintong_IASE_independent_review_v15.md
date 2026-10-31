# Sintong IASE Eq. 15-16: independent physical-domain review v15

Review timestamp: 2026-10-08 21:59:38 UTC. Scope: a steady, dry, sensible, passive, adiabatic two-stream heat exchanger with positive mass flows, equal constant air specific heats, no mixing, no fan heat added inside the thermal boundary, and no latent heat. This is an engineering derivation and formula applicability review, not a replication of the thesis simulation or a validated equipment model.

## Primary text and interpretation boundary

The local original `sources/papers/09_Sintong_Stockholm_2023.pdf` was read at printed pages 30-31 (zero-based PDF indices 29-30). Page 30, section 3.2.3, attributes the IASE model to Park et al. [38], prints Eq. 15-16, describes cooling the return air towards outdoor air, and uses a maximum 20 C supply criterion. Page 31 Figure 14 shows distinct return-air and outdoor-air inlet/outlet streams. Page images `audit/Sintong_p30_IASE_visual_v15.png` and `audit/Sintong_p31_IASE_visual_v15.png` were visually inspected. The page-30 equation labels and flow-ratio numerator/denominator were checked against the original image.

The printed Eq. 15 contains the notation `HX_flow_ratio(m_dot_OA/m_dot_RA)`. This review interprets the parentheses as the argument of the flow-ratio function defined by Eq. 16, giving the composition below. It does not insert another multiplicative mass-flow ratio. Author code or the cited original is required to settle any remaining typography/implementation ambiguity.

```text
r = m_dot_OA / m_dot_RA
HX_flow_ratio(r) = (1 + r)/2
T_RA_star = T_RA + epsilon * (1+r)/2 * (T_OA - T_RA)
```

The primary thesis text establishes the equation and attribution. It does not, on these two pages, establish the normalization of `epsilon`, a measured applicability interval for unequal flows, or the complete outlet-temperature balance. Those are separate evidence gaps. No Park equation or experimental range is inferred here. Eq. 17 and Eq. 24 are outside this review; their v07 transcription corrections are preserved.

Relevant code inspected: `audit/sintong_consistency_v06.py` identifies only a return-air overshoot example; `matlab/+dchr/+components/heat_exchanger.m` is an aggregate source-heat/capacity/approach interface without two air streams. Neither establishes a flow-ratio domain or independently verifies the thesis IASE model.

## First-law derivation and both outlet bounds

Define capacities and temperature difference:

```text
C_RA = m_dot_RA * c_p        [kW/K if c_p is kJ/(kg K)]
C_OA = m_dot_OA * c_p = r*C_RA
DeltaT = T_RA - T_OA         [K]
alpha = epsilon*(1+r)/2      [dimensionless]
```

For a cooling case `DeltaT > 0`, the heat removed from the return stream is positive. Eq. 15 implies

```text
T_RA_star = T_RA - alpha*DeltaT
Q = C_RA*(T_RA-T_RA_star) = C_RA*alpha*DeltaT.
```

With no external heat/work and no storage, that same heat must enter the outdoor stream:

```text
Q = C_OA*(T_OA_out-T_OA)
T_OA_out = T_OA + (alpha/r)*DeltaT.
```

The outdoor outlet above is independently derived, not a claim that it appears as another numbered equation in the thesis. Each outlet must lie within the two inlet temperatures for the assumed passive sensible exchanger:

```text
T_OA <= T_RA_star <= T_RA    iff    0 <= alpha <= 1
T_OA <= T_OA_out  <= T_RA    iff    0 <= alpha/r <= 1
```

For positive `r`, their intersection gives the necessary and sufficient algebraic condition for BOTH inlet-range outlet bounds together with this first-law balance:

```text
0 <= alpha <= min(1,r)
0 <= Q <= min(C_RA,C_OA)*DeltaT = C_min*DeltaT
0 <= epsilon <= 2*min(1,r)/(1+r).
```

The previous return-air-only bound `epsilon <= 2/(1+r)` misses the smaller outdoor capacity when `r < 1`. Conservation by itself also misses the defect: a formula can conserve heat by making the outdoor outlet hotter than both inlet streams.

This is a necessary/sufficient statement for lumped outlet/energy admissibility under the stated assumptions. It does not guarantee a finite-area exchanger can attain every admitted outlet pair. Geometry, conductance, pressure effects and heat transfer restrictions can impose stricter performance limits; ideal maximum-transfer boundaries can require asymptotically large conductance. No finite-UA or crossflow performance claim follows from this derivation.

For heating (`DeltaT < 0`), the same algebra and inlet-interval test apply with the signs of heat transfer reversed. Calling that signed result "free cooling" would be a separate control error. For `DeltaT = 0`, both outlets remain equal and `Q=0` for finite coefficients; an effectiveness defined using `Q/DeltaT` is then undefined, so this trivial case cannot validate an effectiveness normalization.

## Three different effectiveness definitions

The following quantities are distinct even if all are informally called effectiveness:

| Definition | Physical domain | Return-side coefficient |
|---|---|---|
| Standard heat-transfer effectiveness `epsilon_Q = Q/(C_min*DeltaT)` | `0 <= epsilon_Q <= 1` | `alpha = epsilon_Q*min(1,r)` |
| Return-side temperature effectiveness `epsilon_RA = (T_RA-T_RA_star)/DeltaT = Q/(C_RA*DeltaT)` | `0 <= epsilon_RA <= min(1,r)` | `alpha = epsilon_RA` |
| Mean-capacity normalization `epsilon_mean = Q/[((C_RA+C_OA)/2)*DeltaT]` | `0 <= epsilon_mean <= 2*min(1,r)/(1+r)` | `alpha = epsilon_mean*(1+r)/2` |

The thesis composition is algebraically consistent with the third normalization. This is a possible mathematical interpretation, not verified author intent. Its parameter cannot be freely assigned the standard `0..1` heat-transfer range when flows differ. Conversely, if the thesis `epsilon` is intended as `epsilon_RA`, multiplying it by `(1+r)/2` changes its definition; if intended as standard `epsilon_Q`, the correct two-stream coefficient under these assumptions is `epsilon_Q*min(1,r)`, not `epsilon_Q*(1+r)/2`.

For the thesis composition, the standard effectiveness that it implies is

```text
epsilon_Q_implied = epsilon*(1+r)/(2*min(1,r)).
```

All three definitions coincide at balanced flows `r=1`. Thus balanced-flow checks cannot resolve this ambiguity or certify extrapolation to unequal flow.

For a fixed `0 < epsilon <= 1`, the complete admitted flow interval can be written explicitly:

```text
epsilon/(2-epsilon) <= r <= (2-epsilon)/epsilon.
```

For a hypothetical `epsilon=0.8`, this is `[2/3, 3/2]`; for hypothetical `epsilon=0.7`, it is `[7/13, 13/7]`. These are derived limits, not reported equipment ranges. At `epsilon=0`, all positive flow ratios produce zero transfer. At `epsilon>1`, no positive flow ratio admits the composition under these assumptions.

## Independent boundary and counterexample vectors

The following values are chosen engineering test inputs, not paper data: `T_RA=35 C`, `T_OA=5 C`, `m_dot_RA=1 kg/s`, and `c_p=1.005 kJ/(kg K)`. Thus `C_RA=1.005 kW/K` and `DeltaT=30 K`. Decimal entries below are exact for these rational test inputs. They were calculated by hand from the equations above and independently checked with Python `fractions.Fraction` on 2026-10-08; all six classifications agreed.

| Case | r | epsilon | alpha | T_RA_star (C) | T_OA_out (C) | Q (kW) | Q_max (kW) | epsilon_Q implied | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Balanced flow | 1 | 0.8 | 0.8 | 11 | 29 | 24.12 | 30.15 | 0.8 | Both outlets admitted |
| Hidden outdoor violation | 0.25 | 0.8 | 0.5 | 20 | 65 | 15.075 | 7.5375 | 2 | Fails outdoor bound and capacity limit |
| Outdoor capacity boundary | 0.25 | 0.4 | 0.25 | 27.5 | 35 | 7.5375 | 7.5375 | 1 | Algebraic maximum-transfer boundary |
| Return-air overshoot | 3 | 0.8 | 1.6 | -13 | 21 | 48.24 | 30.15 | 1.6 | Fails return bound and capacity limit |
| Return capacity boundary | 4 | 0.4 | 1 | 5 | 12.5 | 30.15 | 30.15 | 1 | Algebraic maximum-transfer boundary |
| Zero effectiveness | 0.25 | 0 | 0 | 35 | 5 | 0 | 7.5375 | 0 | Zero transfer |

The hidden outdoor violation is the new diagnostic: the equation reaches the thesis's stated 20 C supply criterion while requiring a 65 C outdoor outlet from 5 C and 35 C inlets. A return-only guard would pass it. The exact maximum possible removal is 7.5375 kW; the candidate requires twice that. This counterexample proves the composition is not a generally valid passive two-stream model over unrestricted positive flow ratios. It does not establish that the thesis's actual simulation used this vector or that a reported annual result is wrong.

Zero-flow limits require explicit treatment. As `r -> 0` at fixed positive `epsilon`, the equation predicts `alpha -> epsilon/2` and nonzero return-side heat removal although `C_OA -> 0`; the derived outdoor outlet diverges. At exactly `m_dot_OA=0`, a passive exchanger cannot transfer sensible heat to that absent stream, so `Q=0` and the return air bypasses unchanged. At `m_dot_RA=0`, Eq. 16 is undefined and a return outlet has no transported physical meaning. Negative/nonfinite mass flows and nonpositive/nonfinite specific heat are outside the model. These cases should not be repaired by blindly dividing by a small artificial flow.

## Engineering handoff and remaining evidence

1. Preserve the source equation as a diagnostic with explicit `r`, `alpha`, both derived outlets, `Q`, `Q_max`, and applicability classification. Reject an inadmissible source candidate before a supply-temperature control decision. Clipping only the return temperature is insufficient.
2. Use a separately named engineering reference `Q=epsilon_Q*C_min*DeltaT`, deriving both outlets from the same signed `Q`. Its parameter normalization is explicit. A specific UA-to-effectiveness correlation still needs the exchanger geometry and an evidence-backed applicability domain.
3. Resolve Park [38] primary-text normalization, flow correction and calibrated domain; obtain source simulation code if accessible. Keep Park metadata/abstract discovery separate from equation verification. The thesis-only derivation must not upgrade a full source signoff.
4. Before annual or Simulink adoption, test unequal flows on BOTH sides of unity, capacity boundaries, zero-flow bypass, reversed/equal inlet temperatures, invalid inputs, conservation and the hidden outdoor overshoot. Report standard and return-side effectiveness separately.

No production MATLAB component, Simulink/Stateflow model, status file or progress file was changed by this independent review. No new annual simulation, actual source-data reproduction, Stateflow availability result, or experimental equipment validation is claimed.
