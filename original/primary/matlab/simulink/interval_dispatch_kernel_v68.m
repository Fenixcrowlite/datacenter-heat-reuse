function y=interval_dispatch_kernel_v68(u,cfg,old)
%#codegen
assert(all(isfinite(u))&&all(isfinite(cfg)),'v66 finite domain');
p=cfg(36:60);assert(old(180)==0||old(180)==66,'v66 memory schema');
if old(180)>0,assert(all(old(181:205)==p),'v66 immutable policy');end
if u(1)==0
    assert(old(179)==0,'v66 prefix cannot resume after service');
    assert(p(1)==cfg(5)&&p(2)==cfg(6)&&p(3)==cfg(19)&&p(5)==cfg(35)&& ...
        p(6)==cfg(4)&&p(7)==cfg(3)&&p(9)==cfg(18)&&p(11)==cfg(16)&& ...
        all(p(12:18)==cfg([11 12 13 14 15 9 10]))&&p(19)==cfg(7)&&p(20)==cfg(8)&& ...
        p(21)==cfg(20)&&p(23)==cfg(34),'v66 prefix equipment mismatch');
    step=[u(2);u(3);u(4)];
    legacy=retained_restart_v64(step,cfg(1:35),old(1:114),u(2));
    y=old;y(1:114)=legacy;y(115)=0;
    if legacy(55)==1&&u(2)>0,y(115)=2;end
    y(174:175)=cfg(1);y(176:177)=legacy(35:36);y(178)=1;y(180)=66;y(181:205)=p;
else
    y=interval_service_core_v66(u,p,old);
end
end
function y=interval_service_core_v66(u,p,old)
%#codegen
% u=[kind,phase,horizon,restart,dt,demand,sourceCapacity,HPenable,chargeEnable,E0,latch0,age0].
% p=[C,Ta,Tmax,cutoff,restart,lambda,etaC,etaD,chargeLimit,disLimit,
%    HPnameplate,sourceIn,glide,evapApproach,factor,hotCapacity,chargeApproach,
%    condApproach,delivery,directApproach,aux,minON,minOFF,boiler,stopTemperature].
% Engineering sampled controller: conservative scalar service from retained hulls.
assert(all(isfinite(u))&&all(isfinite(p))&&all(isfinite(old)),'v66 finite domain');
assert(all(p([1 7 8 13 14 16 17 18])>0)&&p(7)<=1&&p(8)<=1&& ...
    p(6)>=0&&all(p([9 10 11 21 22 23 24])>=0),'v66 equipment domain');
assert(p(2)>-273.15&&p(2)<p(4)&&p(4)<p(5)&&p(5)<p(25)&&p(25)<p(3)&& ...
    p(19)<=p(4)&&p(15)>0&&p(15)<=1,'v66 temperature policy');
assert(u(1)==1&&u(5)>0&&u(6)>=0&&u(7)>=0&&all(u(8:9)==0|u(8:9)==1), ...
    'v66 service input domain');
P=@(x)[x x];C=P(p(1));Ta=P(p(2));dt=P(u(5));lam=P(p(6));
cap=muliv(C,minusiv(P(p(3)),Ta));cut=muliv(C,minusiv(P(p(4)),Ta));
restart=muliv(C,minusiv(P(p(5)),Ta));stop=muliv(C,minusiv(P(p(25)),Ta));
y=old;
if old(180)==0
    assert(u(10)>=0&&u(10)<cap(1)&&ismember(u(11),[0 1])&&u(12)>=0,'v66 initial domain');
    initial=P(u(10));on=u(11);age=P(u(12));y(174:175)=initial';
    y(176:177)=0;
else
    assert(old(180)==66,'v66 memory schema');
    assert(all(old(181:205)==p),'v66 immutable policy');
    initial=old(37:38)';on=old(55);age=old(39:40)';
    assert(old(178)==0||old(114)==6,'v66 incomplete prefix handoff');
end
assert(initial(1)>=0&&initial(1)<=initial(2)&&initial(2)<cap(2)&& ...
    age(1)>=0&&age(1)<=age(2),'v66 retained memory bounds');
assert(u(3)>y(177),'v66 physical clock must advance');
% dt is the authoritative held physical duration. The supplied cumulative
% horizon is a rounded label, certified at the cumulative-clock scale.
% Subtracting two large rounded labels cannot certify dt at eps(dt).
nextClock=plusiv(y(176:177)',dt);
assert(nextClock(1)<=u(3)&&nextClock(2)>=u(3),'v66 physical interval mismatch');
Te=minusiv(minusiv(P(p(12)),P(p(13))),P(p(14)));
a=muliv(P(p(15)),plusiv(Te,P(273.15)));
floor=plusiv(P(p(19)),P(p(20)));
lf=minusiv(plusiv(floor,P(p(18))),Te);
assert(Te(1)>-273.15&&a(1)>0&&lf(1)>0,'v66 refrigerant domain');
sourceCap=muliv(P(u(7)),P(p(13)));
sourceHeat=muliv(sourceCap,plusiv(P(1),diviv(lf,a)));
hotHeat=muliv(P(p(16)),P(p(17)));
hpLimit=max(0,min([p(11) sourceHeat(1) hotHeat(1)]));
room=minusiv(P(cap(1)),P(initial(2)));
chargeBound=0;
if u(9)==1&&initial(2)<stop(1)&&room(1)>0
    z=diviv(room,muliv(P(p(7)),dt));
    chargeBound=min(p(9),max(0,z(1)/2)); % leave a conservative capacity margin
end
% A sampled charge must stay below the thermal stop for the ENTIRE
% held interval. E(t)<=E.upper+etaC*qcharge*dt because loss>=0.
% If the proposed charge cannot be certified, withhold it for this sample.
% This permits early sampled OFF; it does not choose an event-root midpoint.
stopRoom=minusiv(P(stop(1)),P(initial(2)));
growth=muliv(muliv(P(p(7)),P(chargeBound)),dt);
if chargeBound>0&&growth(2)>=stopRoom(1),chargeBound=0;end
want=u(6)+chargeBound;assert(isfinite(want),'v66 request overflow');
hpCandidate=min(want,hpLimit);reason=0;newOn=on;
if on==0
    if u(8)==1&&hpCandidate>0&&age(1)>=p(23)&&initial(2)<=restart(1)
        newOn=1;reason=1;
    end
else
    if hpCandidate==0
        newOn=0;reason=3; % no source/capacity/sink: safety OFF overrides ON dwell
    elseif u(8)==0
        assert(age(1)>=p(22),'v66 ON dwell not certified');newOn=0;reason=2;
    end
end
if newOn==0,hpCandidate=0;end
direct=min(u(6),hpCandidate);
z=service_difference_v66(P(hpCandidate),P(direct));charge=min(chargeBound,max(0,z(1)));
remaining=service_difference_v66(P(u(6)),P(direct));
% E(t)>=Elo-lambda*Ehi*dt-discharge*dt/etaD for a decreasing TES.
lossBudget=muliv(muliv(lam,P(initial(2))),dt);
available=minusiv(minusiv(P(initial(1)),P(cut(2))),lossBudget);
disBound=0;
if charge==0&&available(1)>0
    z=diviv(muliv(P(p(8)),available),dt);disBound=min(p(10),max(0,z(1)));
end
dis=min(disBound,max(0,remaining(1)));
remaining=service_difference_v66(remaining,P(dis));boiler=min(p(24),max(0,remaining(1)));
unmet=max(0,u(6)-direct-dis-boiler);served=direct+dis+boiler;
q=plusiv(P(direct),P(charge));B=minusiv(muliv(P(p(7)),P(charge)),diviv(P(dis),P(p(8))));
[en,integral]=flow(initial,dt,-lam,B);
assert(en(1)>=0&&en(2)<cap(1),'v66 interval capacity termination');
assert(dis==0||min(initial(1),en(1))>=cut(2),'v66 certified discharge cutoff');
assert(charge*dis==0,'v66 exclusive TES ports');
assert(charge==0||en(2)<stop(1),'v66 held thermal stop');
src=P(0);srcRate=P(0);hotRate=P(0);
if q(2)>0
    for j=1:128
        t0=muliv(dt,diviv(P(j-1),P(128)));t1=muliv(dt,diviv(P(j),P(128)));
        [e0,~]=flow(initial,t0,-lam,B);[e1,~]=flow(initial,t1,-lam,B);
        hull=[min(e0(1),e1(1)) max(e0(2),e1(2))];
        tank=plusiv(Ta,diviv(hull,C));
        hot=plusiv(tank,P(p(17)));hot=[max(floor(1),hot(1)) max(floor(2),hot(2))];
        lift=minusiv(plusiv(hot,P(p(18))),Te);
        rate=muliv(q,diviv(a,plusiv(a,lift)));
        assert(rate(2)<=sourceCap(2),'v66 finite source capacity');
        waterGlide=minusiv(hot,tank);waterGlide(1)=max(waterGlide(1),p(17));
        water=diviv(q,waterGlide);
        % Correlation hot=tank+approach proves denominator>=approach exactly.
        water(2)=min(water(2),diviv(q,P(p(17)))*[0;1]);
        assert(water(2)<=p(16),'v66 finite water capacity');
        src=plusiv(src,muliv(rate,diviv(dt,P(128))));
        srcRate=[min(srcRate(1),rate(1)) max(srcRate(2),rate(2))];
        hotRate=[min(hotRate(1),water(1)) max(hotRate(2),water(2))];
    end
end
function z=service_difference_v66(x,y)
% Error-free TwoSum residual for finite, normal engineering powers. Retain
% a singleton only when binary64 subtraction is provably exact; otherwise
% keep the outward interval. No tolerance-based service normalization.
z=minusiv(x,y);
if x(1)==x(2)&&y(1)==y(2)&&max(abs([x y]))<realmax/4&& ...
        (x(1)==0||abs(x(1))>=realmin)&&(y(1)==0||abs(y(1))>=realmin)
    b=-y(1);s=x(1)+b;bb=s-x(1);error=(x(1)-(s-bb))+(b-bb);
    if error==0,z=[s s];end
end
end
heat=muliv(q,dt);work=minusiv(heat,src);
standing=muliv(lam,integral);closs=muliv(minusiv(P(1),P(p(7))),muliv(P(charge),dt));
dloss=muliv(minusiv(diviv(P(1),P(p(8))),P(1)),muliv(P(dis),dt));
if p(8)==1,dloss=P(0);end % exact unit-efficiency identity, not a clipped loss
assert(all([heat src work standing closs dloss]>=0),'v66 nonnegative ports');
if newOn==on,nextAge=plusiv(age,dt);else,nextAge=dt;end
mode=0;
if unmet>0,mode=5;elseif boiler>0,mode=4;elseif dis>0,mode=3;
elseif charge>0,mode=2;elseif direct>0,mode=1;end
y(37:38)=en';y(39:40)=nextAge';y(55)=newOn;
ports=[heat;src;work;standing;closs;muliv(P(p(21)),work)];
for j=1:6,ix=41+2*(j-1);y(ix:ix+1)=plusiv(y(ix:ix+1)',ports(j,:))';end
servedIV=plusiv(plusiv(P(direct),P(dis)),P(boiler));
increments=[dloss;muliv(servedIV,dt);muliv(P(boiler),dt);muliv(P(direct),dt);muliv(P(dis),dt);muliv(P(unmet),dt)];
for j=1:6,ix=140+2*(j-1);y(ix:ix+1)=plusiv(y(ix:ix+1)',increments(j,:))';end
law=minusiv(minusiv(minusiv(minusiv(plusiv(plusiv(y(174:175)',y(41:42)'),y(144:145)'), ...
    y(142:143)'),en),y(47:48)'),plusiv(y(49:50)',y(140:141)'));
assert(law(1)<=0&&law(2)>=0,'v66 global first law enclosure');
y(53:54)=law';y(115)=mode;y(116:117)=initial';y(118:119)=old(176:177);
y(120:127)=[direct+charge;direct;charge;dis;boiler;unmet;served;u(5)];
y(128:139)=reshape([heat;src;work;standing;closs;dloss]',12,1);
y(154:155)=srcRate';y(156:157)=hotRate';y(158:159)=plusiv(Ta,diviv(en,C))';
y(160:161)=initial';y(162:163)=age';y(164:171)=[on;reason;chargeBound;disBound;cap(1);cut(2);restart(1);u(6)-served-unmet];
y(172:173)=law';y(176:177)=plusiv(y(176:177)',dt)';y(179)=old(179)+1;y(180)=66;y(181:205)=p;
assert(y(176)<=u(3)&&u(3)<=y(177),'v66 sampled physical horizon enclosure');
assert(abs(y(171))<=32*eps(max(1,u(6))),'v66 demand closure');
end
function y=retained_restart_v64(step,cfg,previous,stage)
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
x=muliv(k,t);assert(max(abs(x))<=2,'v68 outward span exceeds two');
v=plusiv(muliv(k,initial),B);f1=[1 1];f2=[.5 .5];term=[1 1];
for ii=1:24,term=diviv(muliv(term,x),[ii+1 ii+1]);f1=plusiv(f1,term);f2=plusiv(f2,diviv(term,[ii+2 ii+2]));end
fac=[1 1];for ii=2:26,fac=muliv(fac,[ii ii]);end
% On the outward evaluation interval |x|<=2, e^2<8.
% Tail for both phi1 and phi2 is <=8*2^25/26!.
tail=diviv([268435456 268435456],fac);f1=plusiv(f1,[-tail(2) tail(2)]);f2=plusiv(f2,[-tail(2) tail(2)]);
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
