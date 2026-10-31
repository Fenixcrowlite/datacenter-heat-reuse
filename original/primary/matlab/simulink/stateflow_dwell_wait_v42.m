function t=stateflow_dwell_wait_v42(hi,lo,bound,dwell)
% Normal-mode wait: certify the post-add lower age, including new discard.
[ok,margin]=stateflow_dwell_ready_v42(hi,lo,bound,dwell);
if ok,t=0;return;end
t=-margin;t=t+eps(t);
for k=1:16
    [H,L,B]=stateflow_clock_add_v42(hi,lo,bound,t);
    [ok,shortfall]=stateflow_dwell_ready_v42(H,L,B,dwell);
    if ok,return;end
    extra=max(-shortfall,eps(t));next=t+extra+eps(t);
    assert(isfinite(next) && next>t,'DCHR:v42:DwellResolution','Unresolvable conservative dwell progress.');
    t=next;
end
error('DCHR:v42:DwellResolution','Cannot certify conservative dwell wait.');
end
