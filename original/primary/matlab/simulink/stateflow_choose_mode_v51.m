function mode=stateflow_choose_mode_v51(seg,cfg)
%#codegen
% Guard each positive-duration segment using instantaneous service deficit.
direct=min(seg(3),seg(4));remaining=max(0,seg(3)-direct-seg(12));
mode=0;
if seg(1)==0,return;end
if remaining>cfg(11),mode=5;
elseif remaining>0,mode=4;
elseif seg(12)>0,mode=3;
elseif seg(11)>0,mode=2;
elseif direct>0,mode=1;
end
end

