# TES standing-loss primary-text and reduced-model audit v28

Review UTC: 2026-10-09. Scope: standing loss only, before changing the accepted v24 Stateflow storage policy. Read `STATUS_stateflow_v27.json`, `MASTER_STAGEBOARD_stateflow_v27.md`, `audit/research_frontier_2026_10_08.md`, `automation/STATEFLOW_ACCEPTANCE.md`, the v16 storage component/reference, and earlier Stateflow equation/QA records. This report does not change production code. Full source signoffs stay **0/31**: the new review verifies the relevant text and equation, rather than reproducing an article or calibrating equipment.

## Acquired evidence and classification

**Verified relevant primary article text.** Cadau, N.; De Lorenzi, A.; Gambarotta, A.; Morini, M.; Rossi, M. (2019), *Development and Analysis of a Multi-Node Dynamic Model for the Simulation of Stratified Thermal Energy Storage*, *Energies* 12(22), 4275, [DOI 10.3390/en12224275](https://doi.org/10.3390/en12224275). The editorial PDF has 22 pages; article page numbering and PDF page numbering coincide. Publication date on p1: 9 November 2019.

Locators: **Section 2, PDF/article p4, Eqs (2) and (4)**; the ambient term of Eq (4) is `-U*A*(T_i-T_amb)`. Uniform node temperature is stated on p4. **p6, Model Implementation** requires at least two nodes for its inlet-routing implementation. **p20, Nomenclature** defines `M` mass kg, `c` specific heat J/(kg K), `U` overall heat exchange coefficient W/(m2 K), `A` area m2, `T` degrees Celsius, and `t` seconds. Thus the paper's implemented stratified model is not the project's one-node dispatch model. These are verified text claims; no paper results or parameter values are adopted.

Saved source: `sources/papers/Cadau_2019_TES_v28_20261009T102911_076286Z.pdf`, SHA256 `693b8373e83c5b3cfcc17c449903a4dc320c9df76bb664b99aeab455d7d39dcb`; extraction with form-feed page boundaries is alongside it. Visually checked equation page: `audit/TES_Cadau_v28_page4.png`. Supplementary context render: `audit/TES_Cadau_v28_page5.png`.

**Verified primary engineering documentation, not a research article.** [EnergyPlus Engineering Reference, Water Thermal Tanks (includes Water Heaters)](https://energyplus.readthedocs.io/en/latest/guides/engineering-reference/19.3-water-thermal-tanks-includes-water-heaters.html), opened 2026-10-09: **Mixed Water Thermal Tank / Energy Balance, Eqs (19.100)-(19.104), (19.109)-(19.113)**. It supplies a well-mixed heat-capacity balance, ambient heat-transfer terms, the linear temperature ODE `T'=a+bT`, and its analytical solution including `b=0`. Source/use connections also have temperature-dependent heat exchange in Eqs (19.105)-(19.108). Coefficients apply while the conditions defining them hold; the control section describes piecewise integration when conditions change. An accessible fixed-version [EnergyPlus 9.5 reference](https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html#energy-balance) independently showed the same forms on the retrieval date, without the current numbered-equation labels.

**Supplementary educational text, not primary article evidence.** Song (2024), [*Modelling and Optimization of Seasonal Thermal Energy Storage*](https://publications.syscop.de/Song2024b.pdf), master's thesis, PDF p30 / printed p10, Section 2.1.1, Eq (2.10a)-(2.10b), presents the lumped cooling ODE and thermal resistance/capacitance interpretation. It corroborates the derivation below but does not upgrade the article signoff or establish empirical validation.

Acquisition limits: initial direct web retrievals of the article HTML/DOI/PDF produced inaccessible/403/429 results, while search-indexed equation text was available. Those snippets alone were not treated as full-text verification. A default-sandbox Python network probe failed with WinError 10013; subsequently an automatically approved, public read-only download from [the publisher PDF endpoint](https://mdpi-res.com/d_attachment/energies/energies-12-04275/article_deploy/energies-12-04275.pdf) returned HTTP 200 and 9,078,887 bytes. Timestamped acquisition evidence: `audit/TES_source_acquisition_v28_20261009T102911_076286Z.json` and matching `automation/logs/TES_source_acquisition_v28_20261009T102911_076286Z.log`. Only this project received files. No external publication occurred.

## Independent reduction and units

The following equations are **our derivation under explicit added assumptions**. They are not equations attributed to Cadau's implemented two-or-more-node model. Set all mass/transport terms to zero, remove inter-node exchange, and assume a mixed sensible store with constant positive heat capacity `C=M*c` J/K, constant `UA>=0` W/K, and constant ambient temperature `T_a`. Then the first law gives

`C*dT/dt_s = -UA*(T-T_a)`.

Temperature differences in Celsius have the same numerical magnitude as kelvin differences. Define **ambient-referenced** excess energy `E_J=C*(T-T_a)`, with `T>=T_a` for a nonnegative hot-store state. Differentiate using constant `C,T_a`:

`dE_J/dt_s = -(UA/C)*E_J`.

`UA/C` has units `(J/(s K))/(J/K)=s^-1`. Since one hour is 3600 seconds and one MWh is `3.6e9 J`, define `E=E_J/3.6e9` MWh and `lambda=3600*UA/C` h^-1. Then

`dE/dt_h=-lambda*E`,

`E(t+h)=E(t)*exp(-lambda*h)`,

`L_standing=E(t)*(1-exp(-lambda*h))` MWh.

The solution follows by separation for positive energy; `E=0` is also a solution. It gives nonnegative retention for every finite `lambda>=0,h>0` and the exact passive semigroup `r(h1)*r(h2)=r(h1+h2)`. There is no physical upper limit `lambda*h<=1` for this continuous coefficient. Very large products may underflow to zero in floating point; that is numerical representation of an exponentially small quantity, not finite-time emptying in the exact ODE. A stable small-product standing-loss calculation is `-E*expm1(-lambda*h)`.

**Applicability defect to avoid:** energy available above a useful return/cutoff temperature `T_min>T_a` is `E_use=C*(T-T_min)/3.6e9`. For fixed `T_min,T_a`, it obeys

`dE_use/dt_h=-lambda*(E_use+E_offset)`,

`E_offset=C*(T_min-T_a)/3.6e9`,

`E_use(t+h)=(E_use(t)+E_offset)*exp(-lambda*h)-E_offset`.

It can cross zero while the physical tank still contains ambient-referenced sensible heat. Delivery must cease or change below its cutoff. Pure exponential decay of usable energy would implicitly place equilibrium at `T_min`; it is not justified by the ambient-loss article term when `T_min!=T_a`. If ambient varies, differentiating ambient-referenced energy also adds `-C*dT_a/dt_s`; the simple autonomous ODE then fails. Temperature/phase-dependent `C` or nonlinear `UA` also invalidates this exact constant-coefficient solution.

Accordingly, the proposed v28 scalar energy state must be labeled **phenomenological zero-equilibrium / ambient-referenced energy**, with a scenario continuous decay coefficient. The project has no temperature state, tank geometry, calibrated `UA,C`, delivery cutoff, stratification, or time-varying ambient. Do not claim that changing a retention function reproduces a physical tank.

## Active ports: full simultaneous solution versus loss-first split

Assume external charge `Q_c` MW, useful external discharge `Q_d` MW, and constant efficiencies `0<eta_c,eta_d<=1`. Under an additional constant-power, single-state approximation, net internal power is `P=eta_c*Q_c-Q_d/eta_d` MW. The simultaneous ODE is

`E'=-lambda*E+P`.

Integrating factor `exp(lambda*t)` gives for `lambda>0`

`E_next=r*E_start+P*(1-r)/lambda`, `r=exp(-lambda*h)`.

For `lambda=0`, its continuous limit is `E_next=E_start+P*h`. This analytical extension agrees with the linear-ODE structure in the engineering reference but does not implement that reference's hydraulic connections. If constant power crosses an energy or temperature bound during the step, the unconstrained solution cannot remain physically feasible; a cutoff event or a different constrained control law is needed.

The full-ODE integrated standing loss is `L_cont=E_start+P*h-E_next`, equivalently `integral(lambda*E(t),dt)` over the interval. External-port closure is

`E_start+(Q_c-Q_d)*h=E_next+L_cont+(1-eta_c)*Q_c*h+(1/eta_d-1)*Q_d*h`.

The **proposed v28 policy** instead applies passive loss first, then charge/discharge:

`E_after=r*E_start`,

`E_next=E_after+P*h`,

`L_split=E_start-E_after`.

This is a discrete operator-split policy. Its storage port closure remains exact by construction, and idle decay is exact under the stated reduced ODE. Active charging/discharging is still time-partition dependent; new charge has no standing loss until the next interval, while withdrawal occurs after all initial-energy loss is charged. With identical unconstrained constant `P`,

`E_split-E_cont=P*(h-(1-r)/lambda)`.

The parenthesis is positive for `lambda,h>0`, so the split state overestimates continuous charging energy and underestimates continuous discharging energy. Expansion gives a one-step discrepancy `P*lambda*h^2/2+O(h^3)`; over a fixed horizon without saturation it converges at first order. State-dependent dispatch, saturation and mode changes can change the error path and must be tested explicitly, not inferred from passive semigroup behavior.

For comparison, legacy linear retention is `1-lambda*h`, the forward-Euler approximation to the same passive rate interpretation. Its accepted `lambda*h<=1` domain merely prevents negative energy; it is not an accuracy guarantee. A field called `loss_fraction_per_h` is ambiguous: `lambda` is a continuous rate coefficient, while a measured one-hour loss fraction `f` maps to `lambda=-log(1-f)` h^-1, not `lambda=f`, for `0<=f<1`. Reusing numerical coefficients in v24/v28 is a controlled scenario comparison of methods; it must not imply that fitted fractional loss and fitted ODE rate are identical.

## Independent equation QA and handoff

`audit/check_TES_derivation_v28.py` verifies an SI-to-MW/MWh unit mapping, independently integrates the ODE by RK4, tests passive and forced partition identities, tests the zero-rate limit and split bias sign, and demonstrates the useful-energy cutoff counterexample. Inputs are declared scenario assumptions; no article numerical values or equipment observations are used. It imports no MATLAB or production dispatch code. Its timestamped JSON and log carry pass/fail and the source PDF hash; executed results must be consulted rather than inferred from this file's existence.

Executed **14/14 PASS, 0 FAIL** at `2026-10-09T10:32:10Z`, exit code 0. Evidence: `audit/TES_derivation_checks_v28_20261009T103210_777150Z.json` and `automation/logs/TES_derivation_checks_v28_20261009T103210_777150Z.log`. This is reduced-equation and units QA, not an executed Stateflow result. Reproduce with `python -X utf8 audit/check_TES_derivation_v28.py` from the project root; each run writes fresh timestamped evidence.

Next acceptance work: preserve v24, build a new versioned v28 Stateflow model with exponential passive retention in both HP-request headroom and allocator/monitor paths, execute all six modes plus a rate-times-step-above-one control, independently verify numeric traces/ports/losses, and compare passive partition invariance and active split convergence to the full ODE. Continue to state that implementation acceptance is not source replication or measured-system validation. The temperature-reference/cutoff defect is an actionable subsequent physical-model task.
