# Heat-pump primary-boundary derivation v43

Research checkpoint 0.43; production model remains saved Stateflow 0.42.
This is a component-equation/assumption audit, not article replication or
equipment calibration. Read the latest STATUS/stageboards, acceptance, frontier,
progress and production HP/Stateflow code before this additive work.

## Verified local primary text and access scope

Selected ledger source 20: Verzino, Talluri, Rocchetti and Socci (2026),
*Smart Reuse of Waste Heat from Data Centres: Energy and Exergy Analysis for a
District-Heating Network in Bulgaria*, Energies 19(3), 800,
[DOI 10.3390/en19030800](https://doi.org/10.3390/en19030800).
The existing publisher PDF has 27 pages with matching printed/PDF numbering.
Its byte hash, extracted pages and visually inspected page PNGs are bound in
the v43 evidence directory. This is verification of the existing local version;
the newest publisher PDF has not been reacquired or proven byte-identical.
Direct publisher HTML access returned 429 during this run. Indexed publisher
equation text was accessible and corroborated the local page, but is not the
sole basis for primary verification. No abstract or metadata is used to supply
an equation or a measured performance point.

| Locator | Verified relationship or statement | Units / boundary / limits |
|---|---|---|
| Section 2.1.1, p8, Eq (4) | Compressor work equals evaporator cooling power divided by cooling EER | Q and W are thermal/work powers in kW (p23 nomenclature); compressor cycle boundary |
| p8, Eq (5) | Condenser heat equals evaporator heat plus compressor work | Same cycle, steady power balance; fan power is treated separately in adjacent text |
| p8, Eq (6) | Ideal cooling EER is TL/(TH-TL) | Absolute Kelvin; low/high refrigerant saturation temperatures, expressly not the varying external source temperatures |
| p8, Eq (7) | Cooling second-law factor is EER/EERideal | Dimensionless; requires TL>0, TH>TL for this reduction |
| Section 2.2.1, p10 | VCC2 and VCC3 use assumed cooling second-law factor 0.5; VCC1 instead uses a polynomial | Article modeling assumption, not a measured performance map; cited 0.45-0.55 range not independently verified upstream |
| Section 2.2, p9; Figure 3 and Section 2.2.2, p10 | VCC1 -> VCC2 -> thermochemical store -> VCC3 -> DHN; no recovery in FC mode | Three compressors and a TCS black box; not v42's single HP and sensible TES |
| p23 data statement | Data sharing requires author evaluation | No hourly data or independent measured validation acquired |
| p27, references [61], [62], [64] | CoolSelector; TSEP 2025, 61, 103513; Arpagaus et al., Energy 2018, 152, 985-1010 | References identified in primary text; upstream content, coefficients and claimed performance range NOT VERIFIED |

## Independent derivation (not additional numbered article equations)

Write QL>0 for evaporator heat, QH for condenser heat, W>0 for compressor work,
and etaC=EER/EERideal. At the same compressor boundary:

    QH = QL + W
    EER = QL/W = etaC*TL/(TH-TL)
    COPH = QH/W = 1 + EER = 1 + etaC*TL/(TH-TL)

Heating Carnot COP is TH/(TH-TL)=1+TL/(TH-TL). If the existing implementation
uses COPH=etaH*TH/(TH-TL), it must use the temperature-dependent conversion:

    etaH = ((TH-TL) + etaC*TL)/TH
         = etaC + (1-etaC)*(TH-TL)/TH
         = 1 - (1-etaC)*TL/TH

For 0<etaC<=1 and 0<TL<TH, etaC<=etaH<=1. Directly assigning etaH=etaC gives:

    COPH_correct - COPH_same_factor = 1 - etaC

This is a convention mismatch, not an arithmetic bug in the accepted generic
screening component. A constant heating factor cannot reproduce a constant
cooling factor over changing refrigerant temperature ratios. Kelvin offsets
cancel in temperature differences, but not in the numerator; a Celsius
temperature ratio is inadmissible. These equations describe compressor-only
power. Adding pumps/fans to W changes system COP and invalidates COPH=EER+1
unless cooling EER uses that exact same enlarged electrical boundary.

Dimension check: Q/W and EER are dimensionless; TL/(TH-TL) is K/K;
etaH is dimensionless; QL/EER has power units. Converting kW to MW rescales
all three ports together by 1/1000 and leaves the ratios unchanged.

For the source-limited, constant-COP case, an independent analytic bound is:

    QH_max = min(request, capacity, QL_available*COPH/(COPH-1))
    W = QH/COPH
    QL = QH - W

A lower COP draws more electricity and adds more condenser heat for a fixed
evaporator budget. Thus copying the cooling factor can falsely remove unmet
demand even though its COP is lower. Increasing COP by substituting external
water temperatures can reduce electricity at fixed output, yet also reduce
source-limited condenser output. Both effects must be assessed with boundaries.

For the existing assumed linear part-load law C(Q)=A+B*Q, the independent
positive root follows from Q-Q/C(Q)=s:

    B*Q^2 + (A-1-s*B)*Q - s*A = 0
    A=Cnominal*(1-penalty), B=Cnominal*penalty/capacity

The QA computes this with 80-digit Decimal, rather than reusing production
bisection. Exact rational arithmetic verifies the factor identities separately.
This quadratic is our verification of the existing engineering law; the Varna
paper does not provide evidence for that part-load law.

## Mapping to the accepted implementation

`heat_pump_step_v40.m` applies a heating Carnot factor to reservoir proxies,
then COP clipping and an assumed part-load penalty. `dchr_stateflow_hp_v42.m`
passes h(2) as that factor and x(2:3) as source/condenser proxies. Neither
implements the three-cycle Varna architecture or refrigerant-side pinches.

| Implementation assumption | Article support | Required follow-up |
|---|---|---|
| First law QH=QL+W; source-side limit | Supported at compressor cycle boundary by Eqs (4)-(5) | Keep auxiliaries on separately stated electrical boundaries |
| h(2) heating factor | Cannot copy p10 cooling factor 0.5 into it | Recompute converted etaH from refrigerant TL,TH for each condition in a separate scenario/backend |
| Source/sink water proxies in Carnot numerator/lift | Does not reproduce Eq (6) refrigerant boundary | Resolve HX approach/pinch and finite water glide; symmetric +/- pinch in this audit is an engineering fixture only |
| part_load_penalty and COP clips/cutoff | Not calibrated by Eqs (4)-(7) | Acquire equipment operating map/domain and validate cycling/control behavior |
| lift_polynomial with lift alone | Not the verified VCC1 two-saturation-level correlation | Verify [61]/[62] full data and domains before adopting coefficients |
| One HP plus sensible TES | Different from p9-10 chain and TCS | Build a separate, explicitly bounded Varna scenario if replication is pursued |

324 synthetic sweep points cover source 20/35/45 C, sink 65/80/95 C, etaC
0.45/0.5/0.55, symmetric pinch 0/5/10 K, source 0.5/5 MW and requests 1/100 MW.
These temperatures/powers/pinches are not article equipment observations. The
audit uses generous capacity/COP limits and zero part-load penalty to isolate
the factor conversion. Four additional focused saved-v42 simulations expose
the convention, temperature-boundary and assumed-part-load differences. They
are implementation comparisons, not a new model release or calibrated plant.

Open scientific blocker: the verified article does not calibrate the accepted
HP screening assumptions. Upstream [61]/[62]/[64] and measured maps remain
unverified. Full primary signoffs remain 0/31; no physical-validation claim.
