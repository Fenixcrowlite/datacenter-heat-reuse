function tol=stateflow_time_tolerance_v36(values)
%#codegen
% All inputs and the tolerance are physical HOURS. No energy/power inputs.
assert(all(isfinite(values)) && all(values>=0),'Invalid physical-hour scale.');
tol=64*eps(max(1,max(abs(values))));
% Explicit numerical-resolution contract: never silently relax dwell/clock QA.
assert(tol<=1e-8,'Physical-hour resolution exceeds 1e-8 h budget.');
end
