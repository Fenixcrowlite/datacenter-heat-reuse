"""Generate additive sources; preserve v63 byte-for-byte."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    base=(ROOT/'matlab/simulink/charge_memory_kernel_v63.m').read_text()
    base=base.replace('function y=charge_memory_kernel_v63','function y=capacity_history',1)
    wrapper='''function y=restart_chain_kernel_v64(step,cfg,previous,stage)
%#codegen
% Retained interval restart; no capacity-root midpoint or scalar inventory reset.
assert(all(isfinite(cfg))&&all(isfinite(step)),'v64 finite input required');
assert(cfg(35)>cfg(6)&&cfg(35)<cfg(19),'v64 thermal hysteresis domain');
assert(step(1)==stage,'v64 phase mismatch');
if stage>0
    assert(previous(112)==64&&previous(113)==cfg(35),'v64 restart provenance');
end
if stage<=4
    y=zeros(114,1);y(1:80)=capacity_history(step,cfg(1:34),previous(1:80),stage);
    y(112)=64;y(113)=cfg(35);y(114)=stage;return;
end
assert(all(cfg(1:31)==previous(1:31))&&all(cfg(32:34)==previous(65:67)),'v64 immutable provenance');
assert(step(3)==1,'v64 explicit restart continuation required');
assert(step(2)>previous(36)&&step(2)<=cfg(23),'v64 restart horizon must advance');
P=@(v)[v v];C=P(cfg(5));Ta=P(cfg(6));q=P(cfg(2));k=-P(cfg(4));B=muliv(P(cfg(3)),q);
cap=previous(58:59)';star=previous(32:33)';
y=previous;
if stage==5
    assert(previous(34)==4&&previous(55)==0,'v64 restart sequence');
    assert(previous(72)==1&&previous(70)>=cfg(34),'v64 OFF dwell not certified');
    temp=plusiv(Ta,diviv(previous(37:38)',C));
    assert(temp(2)<=cfg(35),'v64 thermal restart not certified');
    assert(previous(37)>star(2),'v64 restart floor branch unsupported');
    y(81)=previous(36);y(82:83)=previous(37:38);
    y(84:95)=previous(41:52);y(96:97)=previous(70:71);
elseif stage==6
    assert(previous(34)==5||previous(34)==6,'v64 continuation sequence');
    assert(previous(55)==1&&previous(80)==1,'v64 continuation authorization');
else
    assert(false,'v64 unsupported phase');
end
t=minusiv(P(step(2)),P(y(81)));initial=y(82:83)';
[en,integ]=flow(initial,t,k,B);
assert(en(1)>star(2)&&en(2)<cap(1),'v64 recharge capacity or branch crossing');
Te=minusiv(minusiv(P(cfg(11)),P(cfg(12))),P(cfg(13)));
a=muliv(P(cfg(14)),plusiv(Te,P(273.15)));
l0=minusiv(plusiv(plusiv(Ta,P(cfg(9))),P(cfg(10))),Te);
src=P(0);
for j=1:128
    t0=muliv(t,diviv(P(j-1),P(128)));t1=muliv(t,diviv(P(j),P(128)));
    [e0,~]=flow(initial,t0,k,B);[e1,~]=flow(initial,t1,k,B);
    lift=plusiv(l0,diviv([e0(1) e1(2)],C));
    rate=muliv(q,diviv(a,plusiv(a,lift)));
    assert(rate(2)<=cfg(17)*cfg(12),'v64 finite source capacity');
    src=plusiv(src,muliv(rate,diviv(t,P(128))));
end
heat=muliv(q,t);work=minusiv(heat,src);
y(41:42)=plusiv(y(84:85)',heat)';y(43:44)=plusiv(y(86:87)',src)';
y(45:46)=plusiv(y(88:89)',work)';y(47:48)=plusiv(y(90:91)',muliv(P(cfg(4)),integ))';
y(49:50)=plusiv(y(92:93)',muliv(minusiv(P(1),P(cfg(3))),heat))';
y(51:52)=plusiv(y(94:95)',muliv(P(cfg(20)),work))';
law=minusiv(minusiv(minusiv(plusiv(P(cfg(1)),y(41:42)'),en),y(47:48)'),y(49:50)');
assert(law(1)<=0&&law(2)>=0,'v64 first law enclosure');
assert(all(y(41:52)>=0),'v64 nonnegative ports');
water=diviv(q,P(cfg(9)));
if cfg(29)==1
    assert(water(1)<=cfg(15)&&water(2)>=cfg(15),'v64 exact water tie');
else
    assert(water(2)<=cfg(15),'v64 finite water capacity');
end
y(34)=stage;y(35:36)=step(2);y(37:38)=en';y(39:40)=t';y(53:54)=law';
y(55)=1;y(60:61)=water';y(62:63)=plusiv(plusiv(Ta,diviv(en,C)),P(cfg(9)))';
y(70:71)=0;y(72)=0;y(73)=4;y(80)=1;
y(98:99)=plusiv(Ta,diviv(initial,C))';y(100:101)=t';
y(102:103)=initial';y(104:105)=heat';y(106:107)=src';y(108:109)=work';
y(110:111)=muliv(P(cfg(4)),integ)';y(112)=64;y(113)=cfg(35);y(114)=stage;
end
'''
    target=ROOT/'matlab/simulink/restart_chain_kernel_v64.m';assert not target.exists();target.write_text(wrapper+base)
    b=(ROOT/'matlab/simulink/build_charge_memory_v63.m').read_text()
    b=b.replace('build_charge_memory_v63','build_restart_chain_v64').replace('DCHR_Capacity_Chain_Stateflow_v63','DCHR_Restart_Chain_Stateflow_v64')
    b=b.replace('charge_memory_kernel_v63','restart_chain_kernel_v64').replace('charge_cfg_v63','restart_cfg_v64').replace('charge_steps_v63','restart_steps_v64').replace('charge_trace_v63','restart_trace_v64')
    b=b.replace("'StopTime','6'","'StopTime','9'").replace("[(0:6)' repmat(cfg',7,1)]","[(0:9)' repmat(cfg',10,1)]")
    b=b.replace("'[34 1]','[80 1]','[80 1]'","'[35 1]','[114 1]','[114 1]'").replace('zeros(80,1)','zeros(114,1)')
    b=b.replace("'PASSIVE_COOLING'};states=cell(5,1)","'PASSIVE_COOLING','RESTART_CHARGE','RECHARGE_CONTINUATION'};states=cell(7,1)")
    b=b.replace('for j=1:5','for j=1:7').replace('for j=1:4\n    t=Stateflow.Transition','for j=1:6\n    t=Stateflow.Transition')
    b=b.replace('v63 fixed 80-double correlated capacity chain;', 'v64 retained interval restart chain;').replace('Five protocol phases','Seven protocol phases')
    target=ROOT/'matlab/simulink/build_restart_chain_v64.m';assert not target.exists();target.write_text(b)

if __name__=='__main__':main()
