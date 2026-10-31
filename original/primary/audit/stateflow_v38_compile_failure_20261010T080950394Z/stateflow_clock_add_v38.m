function [hi,lo,bound]=stateflow_clock_add_v38(hi,lo,bound,dt)
%#codegen
% TwoSum expansion in HOURS. bound encloses discarded low-order roundoff.
assert(all(isfinite([hi;lo;bound;dt])) && hi>=0 && bound>=0 && dt>=0,'Invalid compensated clock.');
stateflow_time_tolerance_v36([hi;dt]);
assert(abs(lo)<=eps(max(1,hi)) && abs(lo)+bound<=1e-8,'Clock cumulative accuracy budget exceeded.');
if dt==0,return;end
[s,e]=twosum(hi,dt);
[r,discard]=twosum(lo,e);
[hi,lo]=twosum(s,r);
candidate=bound+abs(discard);
% Conservative upward allowance, including when the addition rounds down.
if discard~=0,bound=candidate+eps(candidate);end
assert(isfinite(hi) && isfinite(lo) && abs(lo)+bound<=1e-8,'Clock cumulative accuracy budget exceeded.');
stateflow_time_tolerance_v36([hi;dt]);
end
function [s,e]=twosum(a,b)
s=a+b;z=s-a;e=(a-(s-z))+(b-z);
end
