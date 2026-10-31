function [endpoint,standing]=stateflow_tes_endpoint_v51(A,qc,qd,cfg,span,kind)
%#codegen
% Shared physical endpoint for host planner and actual Stateflow allocation.
% Zero duration is identity; correction belongs only to positive integration.
assert(span>=0 && A>=0 && A<=cfg(2),'Invalid canonical TES state.');
if span==0
    assert(qc==0 && qd==0,'Zero-duration TES ports.');
    endpoint=A;standing=0;return;
end
P=cfg(5)*qc-qd/cfg(6);rate=cfg(7);x=rate*span;
r=exp(-x);f=-expm1(-x);phi=span;beta=0;
if rate>0 && x>0
    phi=f/rate;
    if x<1e-4,beta=span*x*(.5-x*(1/6-x*(1/24-x*(1/120-x/720))));
    else,beta=span-phi;end
end
endpoint=A*r+P*phi;standing=A*f+P*beta;
roundoff=64*eps(max(1,cfg(2)));
assert(endpoint>=-roundoff && endpoint<=cfg(2)+roundoff,'TES segment crosses physical capacity.');
endpoint=min(cfg(2),max(0,endpoint));
% The same bounded normalization is applied before any next segment/padding.
if abs(endpoint-cfg(2))<=roundoff,endpoint=cfg(2);end
if abs(endpoint-cfg(8))<=roundoff,endpoint=cfg(8);end
if kind==1,assert(endpoint==cfg(2),'Capacity event endpoint mismatch.');end
if kind==2,assert(endpoint==cfg(8),'Cutoff event endpoint mismatch.');end
end
