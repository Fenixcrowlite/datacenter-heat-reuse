function y=restart_chain_kernel_v64(step,cfg,previous,stage)
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
function y=capacity_history(step,cfg,previous,stage)
%#codegen
% Fixed-size compiled correlated charge memory. See v63 schema/derivation.
% Original binary operands define the exact manifold; no scalar event reset.
assert(all(isfinite(cfg))&&all(isfinite(step)),'v63 finite input required');
assert(step(1)==stage,'v63 phase mismatch');
assert(numel(cfg)==34&&cfg(34)>0,'v63 OFF dwell domain');
assert(step(3)==0,'v63 restart unsupported: OFF dwell and restart integration required');
assert(cfg(2)>0&&cfg(3)>0&&cfg(3)<=1&&cfg(4)>=0&&cfg(5)>0,'v63 ODE domain');
assert(cfg(13)>0&&cfg(14)>0&&cfg(15)>0&&cfg(16)>0&&cfg(17)>0&&cfg(18)>0,'v63 equipment domain');
assert(cfg(20)>=0&&cfg(21)>=0&&cfg(21)<=cfg(22),'v63 auxiliary/age domain');
assert(cfg(25)>0&&cfg(25)<cfg(26)&&cfg(26)<cfg(23),'v63 event time domain');
assert(all(cfg(27:31)==0|cfg(27:31)==1)&&cfg(27)==1&&cfg(30)==0,'v63 tie domain');
assert(cfg(24)==63,'v63 schema version');
if stage>0
    assert(all(cfg(1:31)==previous(1:31))&&all(cfg(32:34)==previous(65:67)),'v63 immutable manifold provenance');
    assert(previous(56)==0&&previous(57)==63,'v63 memory authorization');
end
P=@(v)[v v];
C=P(cfg(5));Ta=P(cfg(6));F=plusiv(P(cfg(7)),P(cfg(8)));d=P(cfg(9));
star=muliv(C,minusiv(minusiv(F,Ta),d));cap=muliv(C,minusiv(P(cfg(19)),Ta));
Te=minusiv(minusiv(P(cfg(11)),P(cfg(12))),P(cfg(13)));
a=muliv(P(cfg(14)),plusiv(Te,P(273.15)));
lf=minusiv(plusiv(F,P(cfg(10))),Te);
l0=minusiv(plusiv(plusiv(Ta,d),P(cfg(10))),Te);
assert(a(1)>0&&lf(1)>0&&star(1)>cfg(1)&&cap(1)>star(2),'v63 thermal domain');
B=muliv(P(cfg(3)),P(cfg(2)));k=-P(cfg(4));
assert(minusiv(B,muliv(P(cfg(4)),cap))*[1;0]>0,'v63 increasing whole trajectory required');
% Certify incoming/outgoing sides using the compiled flow, not host port data.
[elo,~]=flow(P(cfg(1)),P(cfg(25)),k,B);
[ehi,~]=flow(P(cfg(1)),P(cfg(26)),k,B);
assert(elo(2)<star(1)&&ehi(1)>star(2),'v63 event bracket not certified');
% The host exact-rational adapter certifies equivalent ties; compiled checks
% strict non-ties and interval equality consistency, never chooses a tie by eps.
limits=zeros(5,2);limits(1,:)=P(cfg(2));limits(2,:)=P(cfg(16));
limits(3,:)=muliv(P(cfg(15)),d);
limits(4,:)=muliv(muliv(P(cfg(17)),P(cfg(12))),plusiv(P(1),diviv(lf,a)));
limits(5,:)=P(cfg(18));
for j=1:5
    if cfg(26+j)==1
        assert(limits(j,1)<=cfg(2)&&limits(j,2)>=cfg(2),'v63 inconsistent equivalent tie');
    else
        assert(limits(j,1)>cfg(2),'v63 strict request limiter unresolved');
    end
end
[clo,~]=flow(P(cfg(1)),P(cfg(32)),k,B);
[chi,~]=flow(P(cfg(1)),P(cfg(33)),k,B);
assert(cfg(26)<cfg(32)&&cfg(32)<cfg(33)&&cfg(33)<cfg(23),'v63 capacity event ordering');
assert(clo(2)<cap(1)&&chi(1)>cap(2),'v63 capacity bracket not certified');
if stage==0
    assert(step(2)==0&&previous(57)==0,'v63 initial memory required');t=P(0);
elseif stage==1
    assert(previous(34)==0&&step(2)==0,'v63 contact sequence');t=cfg(25:26)';
elseif stage==2
    assert(stage==2&&(previous(34)==1||previous(34)==2),'v63 outgoing sequence');
    assert(step(2)>cfg(26)&&step(2)>previous(36)&&step(2)<=cfg(23),'v63 physical horizon must advance');
    t=P(step(2));
    assert(t(2)<cfg(32),'v63 active horizon crosses capacity event');
elseif stage==3
    assert(previous(34)==2&&step(2)==0,'v63 capacity contact sequence');
    t=cfg(32:33)';
else
    assert(stage==4&&(previous(34)==3||previous(34)==4),'v63 passive sequence');
    assert(step(2)>cfg(33)&&step(2)>previous(36)&&step(2)<=cfg(23),'v63 passive physical horizon must advance');
    t=cfg(32:33)';
end
[en,integral]=flow(P(cfg(1)),t,k,B);
if stage==1
    % Contact has the symbolic exact star, while root enclosure is retained.
    en=star;
elseif stage==2
    assert(en(1)>star(2),'v63 outgoing branch unresolved');
end
if stage>=3,en=cap;end
assert(en(1)>=0&&(stage>=3||en(2)<cap(1)),'v63 TES bounds');
heat=muliv(P(cfg(2)),t);source=P(0);
% Global-time rectangles include the uncertain event window. The continuous
% max(floor,Ttank+approach) water law avoids a scalar branch handoff.
for j=1:128
    t0=muliv(t,diviv(P(j-1),P(128)));t1=muliv(t,diviv(P(j),P(128)));
    [e0,~]=flow(P(cfg(1)),t0,k,B);[e1,~]=flow(P(cfg(1)),t1,k,B);
    ecell=[e0(1) e1(2)];lift=plusiv(l0,diviv(ecell,C));lift=[max(lf(1),lift(1)) max(lf(2),lift(2))];
    rate=muliv(P(cfg(2)),diviv(a,plusiv(a,lift)));
    source=plusiv(source,muliv(rate,diviv(t,P(128))));
end
work=minusiv(heat,source);standing=muliv(P(cfg(4)),integral);
chargeLoss=muliv(minusiv(P(1),P(cfg(3))),heat);aux=muliv(P(cfg(20)),work);
offage=P(0);ready=0;latch=1;
if stage>=3,latch=0;end
if stage==4
    offage=minusiv(P(step(2)),cfg(32:33)');
    assert(offage(1)>0,'v63 OFF clock unresolved');
    [en,~]=flow(cap,offage,k,P(0));
    if cfg(4)>0,standing=plusiv(standing,minusiv(cap,en));end
    if cfg(4)==0,en=cap;end
    assert(en(1)>=0&&en(2)<=cap(2),'v63 passive TES bounds');
    if offage(1)>=cfg(34),ready=1;elseif offage(2)>=cfg(34),ready=2;end
end
law=minusiv(minusiv(minusiv(plusiv(P(cfg(1)),heat),en),standing),chargeLoss);
assert(source(1)>=0&&work(1)>=0&&standing(1)>=0&&chargeLoss(1)>=0,'v63 nonnegative ports');
assert(law(1)<=0&&law(2)>=0,'v63 first law enclosure');
age=plusiv(cfg(21:22)',t);
if stage>0,assert(age(1)>=previous(39)&&age(2)>=previous(40),'v63 HP clock reset');end
if stage==4,t=P(step(2));end
temp=plusiv(Ta,diviv(en,C));hot=[max(F(1),temp(1)+cfg(9)) max(F(2),temp(2)+cfg(9))];
if stage>0,waterFlow=diviv(P(cfg(2)),d);else,waterFlow=diviv(P(cfg(2)),minusiv(F,temp));end
if stage>=3
    waterFlow=P(0);hot=P(0);
elseif cfg(29)==1&&stage>0
    % Exact host certificate q=H*d; same d expression, no subtractive decorrelation.
    assert(waterFlow(1)<=cfg(15)&&waterFlow(2)>=cfg(15),'v63 finite hot-water tie');
else
    assert(waterFlow(1)>=0&&waterFlow(2)<=cfg(15),'v63 finite hot-water capacity');
end
if stage>=3,waterFlow=P(0);hot=P(0);end
y=zeros(80,1);y(1:31)=cfg(1:31);y(32:33)=star';y(34)=stage;y(35:36)=t';
y(37:38)=en';y(39:40)=age';y(41:42)=heat';y(43:44)=source';y(45:46)=work';
y(47:48)=standing';y(49:50)=chargeLoss';y(51:52)=aux';y(53:54)=law';
y(55)=latch;y(56)=0;y(57)=63;y(58:59)=cap';y(60:61)=waterFlow';y(62:63)=hot';y(64)=128;y(65:67)=cfg(32:34);y(68:69)=cfg(32:33);y(70:71)=offage';y(72)=ready;
y(73)=3;y(74:75)=cfg(21:22);y(76:77)=cfg(25:26);y(78:79)=cap';y(80)=0;
end
function [en,integral]=flow(initial,t,k,B)
if all(t==0),en=initial;integral=[0 0];return;end
x=muliv(k,t);assert(max(abs(x))<=1,'v63 outward span exceeds one');
v=plusiv(muliv(k,initial),B);f1=[1 1];f2=[.5 .5];term=[1 1];
for ii=1:24,term=diviv(muliv(term,x),[ii+1 ii+1]);f1=plusiv(f1,term);f2=plusiv(f2,diviv(term,[ii+2 ii+2]));end
fac=[1 1];for ii=2:26,fac=muliv(fac,[ii ii]);end
tail=diviv([3 3],fac);f1=plusiv(f1,[-tail(2) tail(2)]);f2=plusiv(f2,[-tail(2) tail(2)]);
en=plusiv(initial,muliv(muliv(v,t),f1));integral=plusiv(muliv(initial,t),muliv(muliv(v,muliv(t,t)),f2));
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=minusiv(x,y)
if all(y==0),z=x;elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[0 0];else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v63 positive denominator required');
if all(x==0),z=[0 0];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v63 arithmetic overflow');z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z))&&z(1)<=z(2),'v63 expansion overflow');
end
