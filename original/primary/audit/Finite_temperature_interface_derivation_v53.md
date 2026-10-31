# Finite-temperature interface v53

Accepted saved model remains 0.52. This is an additive steady boundary and input
adapter with executable saved-v52 comparisons, not a new SLX, calibrated plant,
universal numerical-domain proof or article replication.

## Evidence and definitions

Local source20, Verzino et al., Energies 19(3),800,
[DOI](https://doi.org/10.3390/en19030800), p8 Eqs4-7 defines cooling EER,
compressor balance and ideal cooling ratio using refrigerant saturation Kelvin
temperatures. The preserved p8 was visually inspected in this run. Its adjacent
text explicitly distinguishes external source temperatures, HX pinch and water/
air glide. The p10 cooling factor is an article modeling assumption, not a measured
equipment map. P27 reference62 is Rocchetti/Socci, TSEP61,103513,
[DOI](https://doi.org/10.1016/j.tsep.2025.103513). Upstream text and equipment
coefficients remain unverified. Current publisher opens returned429/403;
[university metadata](https://flore.unifi.it/handle/2158/1432822) lists no files.
The newly found source20 supplement link was inaccessible and must not be
confused with the upstream62 supplement. Observations and preserved local pages
are bound to timestamped evidence; no abstract supplies an equation.

Every numeric v53 sweep/fixture parameter is SYNTHETIC_ENGINEERING. No article
Table1 value is transplanted as a calibration. In particular, this model uses
one HP and sensible storage; source20 uses multiple cycles and thermochemical
storage. Full primary signoffs remain0/31.

## Endpoint constraints and independently derived equations

Choose external source inlet Ts,in and positive water glide gs; maximum source
heat-capacity rate Cs,max in MW/K; nonnegative evaporator approach de:

    Ts,out = Ts,in - gs
    Te = Ts,out - de
    QL,budget = Cs,max * gs

The refrigerant evaporates isothermally at Te. Every external source temperature
is at least Ts,out, so de is the minimum temperature difference. Variable water
flow holds this specified glide: Cs,required=QL/gs <= Cs,max. At OFF, flow is zero;
standby load/minimum stable flow is not represented. This is not a constant-flow
water-outlet or an epsilon-NTU/UA solver.

Choose tank maximum Tmax, network delivery Td, direct/charge/discharge approaches
ddir,dch,ddis, hot-water inlet Th,in and condenser approach dc:

    Tcut = Td + ddis
    Th,out = max(Tmax + dch, Td + ddir)
    Tc = Th,out + dc
    QH,hot_budget = Ch,max * (Th,out - Th,in)
    capacity = min(HP_nameplate, QH,hot_budget)

We impose ambient < Tcut < Trestart < Tmax, Th,in<Th,out and Tc>Te.
With variable flow, Ch,required=QH/(Th,out-Th,in) <= Ch,max keeps the hot outlet
setpoint at partial load. This requires an assumed controllable variable-flow
circuit; it is not a demonstrated hydraulic implementation. The tank charging
approach is available even at Tmax, and discharge stops when tank temperature
reaches Tcut. Approach imposes temperature feasibility, not a second energy
efficiency multiplier. Existing eta_charge/discharge account separately for
declared port energy losses. No minimum approach is invented from COP.

Set TL=Te+273.15, TH=Tc+273.15, lift=TH-TL>0, TL>0 and 0<etaC<=1:

    EERc = etaC * TL/lift
    COPh = 1 + EERc
    etaH = (lift + etaC*TL)/TH
    QH,rated = min(capacity, QL,budget*COPh/(COPh-1))
    Wc = QH,rated/COPh; QL = QH,rated-Wc

The factor conversion ensures etaH*TH/lift=COPh and COPh<=TH/lift.
For fixed etaC and external temperatures, increasing either refrigerant approach
reduces COP. Source-limited heat output can increase because more compressor
work is added; lower electricity and higher heat output are separate objectives.
Finite hot-side capacity can independently constrain output.

The adapter explicitly feeds saturation axes into the existing v52 Carnot
algebra and uses converted etaH, zero part-load penalty and inactive COP clips.
It labels that scenario boundary; the generic v52 wrapper's reservoir-oriented
comments are unchanged. An external generic annual scenario is not implicitly
converted. Fixed saturation temperatures across the run are deliberate: a
varying tank-linked condenser or varying etaH needs a new planner interface.

## Auxiliary boundary

Let Wa=r*Wc, r>=0; alpha in[0,1] is the fraction deposited at counted hot output:

    Qcounted = QH + alpha*Wa
    Qreject_aux = (1-alpha)*Wa
    Wtotal = Wc + Wa
    QL + Wtotal = Qcounted + Qreject_aux
    COPsystem = Qcounted/Wtotal, undefined at zero electricity

The component permits alpha for boundary experiments. The saved-model adapter
requires alpha=0: there is no auxiliary thermal port in v52. Actual segment
electricity determines auxiliary energy as r*sum(Wc*span), outside dispatch;
all auxiliary heat is rejected. No additional demand service/storage credit is
created. Aux standby consumption, pumping work equations and thermal placements
need evidence before a new integrated plant. Compressor first law remains strict.

## Verification scope and next engineering gate

MATLAB sweeps verify all ports/capacities and reject invalid temperatures, factors,
fractions, glides, nonfinite/overflow inputs and unsupported integrated aux heat.
Eleven saved-v52 cases include six required modes, a matched approach comparison,
finite hot-side limitation and a24-interval sequence with memory/transitions.
Original SimulationOutputs and report MATs are retained/reopened. A standalone
Python Decimal reviewer evaluates equations, constant-COP maximality, individual
TES segment ODE, nonnegative ports, macro memory and expanded auxiliary first law;
reviewer mutation tests are separate synthetic QA. No production equation import.
This is algorithmic independent QA by the same agent, not independent personnel
or measured physical validation. Stop after evidence closure with an explicit
handoff for a changing-temperature interface and actual flow/UA validation.
