function [ok,margin]=stateflow_dwell_ready_v42(hi,lo,bound,dwell)
%#codegen
% Outward lower endpoint of hi+lo-bound-dwell, in physical hours.
% TwoSum detects downward rounding; no time tolerance authorizes transition.
assert(all(isfinite([hi;lo;bound;dwell])) && hi>=0 && bound>=0 && dwell>=0,'Invalid dwell enclosure.');
a=lower_add(hi,-dwell);b=lower_add(lo,-bound);
margin=lower_add(a,b);ok=margin>=0;
end
function s=lower_add(a,b)
s=a+b;z=s-a;e=(a-(s-z))+(b-z);
assert(isfinite(s) && isfinite(e),'Nonrepresentable dwell comparison.');
if e<0,s=s-eps(abs(s));end
end
