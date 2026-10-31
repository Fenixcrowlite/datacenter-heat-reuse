function y=charge_memory_kernel_v62(step,cfg,previous,stage)
%#codegen
% Fixed-size compiled correlated charge memory. See v62 schema/derivation.
% Original binary operands define the exact manifold; no scalar event reset.
assert(all(isfinite(cfg))&&all(isfinite(step)),'v62 finite input required');
assert(step(1)==stage,'v62 phase mismatch');
assert(cfg(2)>0&&cfg(3)>0&&cfg(3)<=1&&cfg(4)>=0&&cfg(5)>0,'v62 ODE domain');
assert(cfg(13)>0&&cfg(14)>0&&cfg(15)>0&&cfg(16)>0&&cfg(17)>0&&cfg(18)>0,'v62 equipment domain');
assert(cfg(20)>=0&&cfg(21)>=0&&cfg(21)<=cfg(22),'v62 auxiliary/age domain');
assert(cfg(25)>0&&cfg(25)<cfg(26)&&cfg(26)<cfg(23),'v62 event time domain');
assert(all(cfg(27:31)==0|cfg(27:31)==1)&&cfg(27)==1&&cfg(30)==0,'v62 tie domain');
assert(cfg(24)==62,'v62 schema version');
if stage>0
    assert(all(cfg==previous(1:31)),'v62 immutable manifold provenance');
    assert(previous(55)==1&&previous(56)==0&&previous(57)==62,'v62 memory authorization');
end
P=@(v)[v v];
C=P(cfg(5));Ta=P(cfg(6));F=plusiv(P(cfg(7)),P(cfg(8)));d=P(cfg(9));
star=muliv(C,minusiv(minusiv(F,Ta),d));cap=muliv(C,minusiv(P(cfg(19)),Ta));
Te=minusiv(minusiv(P(cfg(11)),P(cfg(12))),P(cfg(13)));
a=muliv(P(cfg(14)),plusiv(Te,P(273.15)));
lf=minusiv(plusiv(F,P(cfg(10))),Te);
l0=minusiv(plusiv(plusiv(Ta,d),P(cfg(10))),Te);
assert(a(1)>0&&lf(1)>0&&star(1)>cfg(1)&&cap(1)>star(2),'v62 thermal domain');
B=muliv(P(cfg(3)),P(cfg(2)));k=-P(cfg(4));
assert(minusiv(B,muliv(P(cfg(4)),cap))*[1;0]>0,'v62 increasing whole trajectory required');
% Certify incoming/outgoing sides using the compiled flow, not host port data.
[elo,~]=flow(P(cfg(1)),P(cfg(25)),k,B);
[ehi,~]=flow(P(cfg(1)),P(cfg(26)),k,B);
assert(elo(2)<star(1)&&ehi(1)>star(2),'v62 event bracket not certified');
% The host exact-rational adapter certifies equivalent ties; compiled checks
% strict non-ties and interval equality consistency, never chooses a tie by eps.
limits=zeros(5,2);limits(1,:)=P(cfg(2));limits(2,:)=P(cfg(16));
limits(3,:)=muliv(P(cfg(15)),d);
limits(4,:)=muliv(muliv(P(cfg(17)),P(cfg(12))),plusiv(P(1),diviv(lf,a)));
limits(5,:)=P(cfg(18));
for j=1:5
    if cfg(26+j)==1
        assert(limits(j,1)<=cfg(2)&&limits(j,2)>=cfg(2),'v62 inconsistent equivalent tie');
    else
        assert(limits(j,1)>cfg(2),'v62 strict request limiter unresolved');
    end
end
if stage==0
    assert(step(2)==0&&previous(57)==0,'v62 initial memory required');t=P(0);
elseif stage==1
    assert(previous(34)==0&&step(2)==0,'v62 contact sequence');t=cfg(25:26)';
else
    assert(stage==2&&(previous(34)==1||previous(34)==2),'v62 outgoing sequence');
    assert(step(2)>cfg(26)&&step(2)>previous(36)&&step(2)<=cfg(23),'v62 physical horizon must advance');
    t=P(step(2));
end
[en,integral]=flow(P(cfg(1)),t,k,B);
if stage==1
    % Contact has the symbolic exact star, while root enclosure is retained.
    en=star;
elseif stage==2
    assert(en(1)>star(2),'v62 outgoing branch unresolved');
end
assert(en(1)>=0&&en(2)<cap(1),'v62 TES bounds');
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
law=minusiv(minusiv(minusiv(plusiv(P(cfg(1)),heat),en),standing),chargeLoss);
assert(source(1)>=0&&work(1)>=0&&standing(1)>=0&&chargeLoss(1)>=0,'v62 nonnegative ports');
assert(law(1)<=0&&law(2)>=0,'v62 first law enclosure');
age=plusiv(cfg(21:22)',t);
if stage>0,assert(age(1)>=previous(39)&&age(2)>=previous(40),'v62 HP clock reset');end
temp=plusiv(Ta,diviv(en,C));hot=[max(F(1),temp(1)+cfg(9)) max(F(2),temp(2)+cfg(9))];
if stage>0,waterFlow=diviv(P(cfg(2)),d);else,waterFlow=diviv(P(cfg(2)),minusiv(F,temp));end
if cfg(29)==1&&stage>0
    % Exact host certificate q=H*d; same d expression, no subtractive decorrelation.
    assert(waterFlow(1)<=cfg(15)&&waterFlow(2)>=cfg(15),'v62 finite hot-water tie');
else
    assert(waterFlow(1)>=0&&waterFlow(2)<=cfg(15),'v62 finite hot-water capacity');
end
y=zeros(64,1);y(1:31)=cfg;y(32:33)=star';y(34)=stage;y(35:36)=t';
y(37:38)=en';y(39:40)=age';y(41:42)=heat';y(43:44)=source';y(45:46)=work';
y(47:48)=standing';y(49:50)=chargeLoss';y(51:52)=aux';y(53:54)=law';
y(55)=1;y(56)=0;y(57)=62;y(58:59)=cap';y(60:61)=waterFlow';y(62:63)=hot';y(64)=128;
end
function [en,integral]=flow(initial,t,k,B)
if all(t==0),en=initial;integral=[0 0];return;end
x=muliv(k,t);assert(max(abs(x))<=1,'v62 outward span exceeds one');
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
if all(y==0),z=x;else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v62 positive denominator required');
if all(x==0),z=[0 0];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v62 arithmetic overflow');z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z))&&z(1)<=z(2),'v62 expansion overflow');
end
