function z=stateflow_allocate_v52(mode,seg,cfg,clock)
%#codegen
% Actual Stateflow state authorizes instantaneous TES and finite boiler ports.
span=seg(1);A=seg(2);direct=0;qc=0;qd=0;gas=0;unmet=0;
if span>0
    if mode>=1,direct=min(seg(3),seg(4));end
    if mode==2,qc=seg(11);end
    if mode>=3,qd=seg(12);end
    if mode>=4,gas=min(cfg(11),max(0,seg(3)-direct-qd));end
    if mode==5,unmet=max(0,seg(3)-direct-qd-gas);end
end
[endpoint,standing]=stateflow_tes_endpoint_v52(A,qc,qd,cfg,span,seg(13));
roundoff=64*eps(max(1,cfg(2)));
assert(isfinite(seg(23)) && seg(23)>=0 && seg(23)<=cfg(2) && abs(endpoint-seg(23))<=roundoff,'Canonical endpoint disagrees with physical integration.');
endpoint=seg(23); % explicit state protocol across host/compiled arithmetic

lc=(1-cfg(5))*qc*span;ld=(1/cfg(6)-1)*qd*span;
supplied=direct+qd+gas;
residual=(seg(6)+seg(5)+gas)*span+A-supplied*span-endpoint-standing-lc-ld;
z=[mode;span;seg(14);A;endpoint;direct;qc;qd;gas;unmet;seg(4:8);seg(10); ...
    standing;lc;ld;supplied;residual;cfg(10)+A/cfg(9);cfg(10)+endpoint/cfg(9);seg(13);seg(9);clock(1);seg(16);clock(2)];
end
