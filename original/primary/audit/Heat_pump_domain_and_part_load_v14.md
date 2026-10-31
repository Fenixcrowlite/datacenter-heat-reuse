# Heat-pump domain and actual part-load source limit — v14

This is an additive engineering component and an independent mathematical check. It is not a replication of a publication, a measured-system validation, or a calibrated compressor map. Existing components, v13 annual dispatch, data and models remain unchanged. This run read STATUS_v12.json, MASTER_STAGEBOARD_v12.md, the research frontier, the v05/v07 mathematical specifications and the relevant MATLAB/Python code before edits.

## Defects and evidence boundaries

**F14-HP-01 / F12-03:** the old component silently replaces a nonpositive or sub-kelvin lift with 1 K. Heating-mode equations require a strictly positive temperature difference and positive absolute temperatures. A source above the sink needs a separately specified direct-recovery/cooling mode; it does not justify a synthetic heating lift.

**F14-HP-02:** an upward COP floor can violate the second law. With the existing scenario efficiency 0.45 and source −100 °C / sink 80 °C, the reservoir Carnot COP is 353.15/180 = 1.9619444444, while the old function returns COP 2.2 after raising its raw prediction 0.882875. This is an adversarial mathematical counterexample, not a plausible operating point or a paper value. Even when the floor stays below Carnot it changes the surrogate prediction without evidence. v14 treats cop_min as a declared operating eligibility cutoff and returns zero flows when the model cannot support it.

**F14-HP-03:** old dispatch sizes output with nominal COP, then reduces COP at part load. For a nonnegative efficiency penalty, actual evaporator extraction is lower than its nominal estimate; this is conservative unused source, rather than source overdraw. v14 solves against actual COP to obtain the largest feasible requested continuous output. The gain is an engineering-model consequence, not measured efficiency improvement.

The Marcinichen original remains unavailable. See [acquisition evidence](Marcinichen_acquisition_v14.md) for the separate EPFL HTTP 429, publisher HTTP 403 and local transport restriction. Search metadata/abstracts have not verified its original temperature tables or equations. No source receives a full signoff.

## Independent derivation

All power is MW; temperature is converted from °C to K with 273.15. For the idealized reservoir boundary, let Th > Tc > 0, condenser heat H, evaporator heat S_used and compressor electricity W be positive.

1. First law: H = S_used + W. Heating COP C = H/W, so W = H/C and S_used = H(1 − 1/C). This recovery model requires C > 1.
2. Reservoir entropy balance: entropy generation = H/Th − S_used/Tc ≥ 0. Substituting the first law yields C ≤ Th/(Th − Tc). This is a necessary thermodynamic bound. It does not establish real equipment performance.
3. Scenario surrogate: C_raw = eta_C × Th/(Th − Tc), with 0 < eta_C ≤ 1. C_nom = min(C_raw, cop_max). A polynomial alternative is accepted only if its prediction respects the same Carnot bound. Neither alternative has a manufacturer or article calibration in this run.
4. Assumed partial-load curve: C(H) = C_nom[1 − penalty(1 − H/H_cap)] = a + bH, with a = C_nom(1 − penalty), b = C_nom penalty/H_cap and 0 ≤ penalty < 1.
5. On the operating interval C(H) ≥ cop_min > 1, the source extraction derivative is dS_used/dH = 1 − a/C(H)^2 > 0. The admissible lower output is max(0, (cop_min − a)/b) when b > 0; the requested/rated upper output is min(request, H_cap). A request or source below the lower operating point is explicitly unavailable, with no excess production to meet a cutoff.
6. The source boundary S_used = S_available gives bH² + (a − 1 − S_available b)H − S_available a = 0. Python solves the positive root analytically, using a rationalized expression to avoid cancellation; MATLAB independently bisects the admissible monotone interval. With penalty zero, the solution reduces to H ≤ S_available C_nom/(C_nom − 1).

The cutoff is calculated once from the interval bound. Rechecking C(H_lower) < cop_min can incorrectly reject an exact boundary after one unit of floating-point rounding; a concrete regression is included in the comparison vectors.

## Reproducible example and implementation

For source 32 °C, sink 70 °C, available source 5 MW, requested output 12 MW, rated output 12 MW, eta_C = 0.45, penalty = 0.08 and COP bounds 2.2–7 (all existing scenario assumptions), the quadratic gives H = 6.712114501705883 MW, W = 1.712114501705883 MW, S_used = 5 MW and C = 3.920365428257397. Legacy nominal sizing gives 6.632057036098525 MW and leaves about 0.0605729412 MW of available source unused.

New scalar component: `matlab/+dchr/+components/heat_pump_step_v14.m`. Its inputs are source heat, source/sink temperatures, requested condenser heat and the existing config. It rejects nonfinite, complex, nonscalar, negative-power, invalid-temperature, invalid-efficiency, reversed-COP-bound and unknown-backend inputs. `available=false` means zero heat/electric/source flows; `cop_operating=NaN` expresses the undefined ratio at zero compressor work. `cop_raw` and `cop_nominal` retain the unraised prediction for diagnostics.

Independent reference: `audit/heat_pump_reference_v14.py`. Test/vector generator: `audit/test_heat_pump_reference_v14.py`. MATLAB comparison: `matlab/run_heat_pump_contract_v14.m`. Timestamped results and exact code/input hashes are listed in STATUS_v14.json and the v14 evidence manifest.

## Limits and next integration task

External source and sink temperatures remain isothermal reservoir proxies, not calculated refrigerant evaporation/condensation temperatures. Heat-exchanger pinch, equipment maps, cycling, minimum compressor load (`cfg.hp.part_load_min`), ramp/start/stop behavior and auxiliary electricity remain outside this component. Polynomial coefficients and COP thresholds are engineering assumptions. Off status is not a computed alternative recovery mode.

The new component is not wired into annual MATLAB dispatch or the existing no-storage Simulink model. The next engineering integration is a separate v14 dispatch that supplies demand plus feasible storage charging to this component, uses explicit finite-boiler/unmet-demand accounting, retains storage energy loss and physical parameter checks, and compares a deterministic trace against an independent Python trace. Only after that gate should the same numerical kernel enter a new, non-overwriting Simulink model. This run neither executes Simulink/Stateflow nor establishes Stateflow availability.

The next scheduled task rotates to primary evidence: audit the still-open IASE/free-cooling flow-ratio domain in the local Sintong original, Eq. 15–16 and its Park [38] provenance. The v07 corrected Eq. 17/24 transcription is already available and should not be repeated as a new result. This local task can establish a real temperature-bound defect or documented applicability domain while Marcinichen access remains blocked.

Input-validation API reference inspected: [MathWorks validateattributes documentation](https://www.mathworks.com/help/matlab/ref/validateattributes.html). The implementation uses explicit scalar checks to retain stable component error identifiers; no article equation is attributed to this API documentation. All equations above are independent derivations under the stated assumptions.
