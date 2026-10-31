function y=interval_service_core_v65(u,p,old)
%#codegen
% u=[kind,phase,horizon,restart,dt,demand,sourceCapacity,HPenable,chargeEnable,E0,latch0,age0].
% p=[C,Ta,Tmax,cutoff,restart,lambda,etaC,etaD,chargeLimit,disLimit,
%    HPnameplate,sourceIn,glide,evapApproach,factor,hotCapacity,chargeApproach,
%    condApproach,delivery,directApproach,aux,minON,minOFF,boiler,stopTemperature].
% Engineering sampled controller: conservative scalar service from retained hulls.
assert(all(isfinite(u))&&all(isfinite(p))&&all(isfinite(old)),'v65 finite domain');
assert(all(p([1 7 8 13 14 16 17 18])>0)&&p(7)<=1&&p(8)<=1&& ...
    p(6)>=0&&all(p([9 10 11 21 22 23 24])>=0),'v65 equipment domain');
assert(p(2)>-273.15&&p(2)<p(4)&&p(4)<p(5)&&p(5)<p(25)&&p(25)<p(3)&& ...
    p(19)<=p(4)&&p(15)>0&&p(15)<=1,'v65 temperature policy');
assert(u(1)==1&&u(5)>0&&u(6)>=0&&u(7)>=0&&all(u(8:9)==0|u(8:9)==1), ...
    'v65 service input domain');
P=@(x)[x x];C=P(p(1));Ta=P(p(2));dt=P(u(5));lam=P(p(6));
cap=muliv(C,minusiv(P(p(3)),Ta));cut=muliv(C,minusiv(P(p(4)),Ta));
restart=muliv(C,minusiv(P(p(5)),Ta));stop=muliv(C,minusiv(P(p(25)),Ta));
y=old;
if old(180)==0
    assert(u(10)>=0&&u(10)<cap(1)&&ismember(u(11),[0 1])&&u(12)>=0,'v65 initial domain');
    initial=P(u(10));on=u(11);age=P(u(12));y(174:175)=initial';
    y(176:177)=0;
else
    assert(old(180)==65,'v65 memory schema');
    assert(all(old(181:205)==p),'v65 immutable policy');
    initial=old(37:38)';on=old(55);age=old(39:40)';
    assert(old(178)==0||old(114)==6,'v65 incomplete prefix handoff');
end
assert(initial(1)>=0&&initial(1)<=initial(2)&&initial(2)<cap(2)&& ...
    age(1)>=0&&age(1)<=age(2),'v65 retained memory bounds');
assert(u(3)>y(177),'v65 physical clock must advance');
% dt is the authoritative held physical duration. The supplied cumulative
% horizon is a rounded label, certified at the cumulative-clock scale.
% Subtracting two large rounded labels cannot certify dt at eps(dt).
nextClock=plusiv(y(176:177)',dt);
assert(nextClock(1)<=u(3)&&nextClock(2)>=u(3),'v65 physical interval mismatch');
Te=minusiv(minusiv(P(p(12)),P(p(13))),P(p(14)));
a=muliv(P(p(15)),plusiv(Te,P(273.15)));
floor=plusiv(P(p(19)),P(p(20)));
lf=minusiv(plusiv(floor,P(p(18))),Te);
assert(Te(1)>-273.15&&a(1)>0&&lf(1)>0,'v65 refrigerant domain');
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
want=u(6)+chargeBound;assert(isfinite(want),'v65 request overflow');
hpCandidate=min(want,hpLimit);reason=0;newOn=on;
if on==0
    if u(8)==1&&hpCandidate>0&&age(1)>=p(23)&&initial(2)<=restart(1)
        newOn=1;reason=1;
    end
else
    if hpCandidate==0
        newOn=0;reason=3; % no source/capacity/sink: safety OFF overrides ON dwell
    elseif u(8)==0
        assert(age(1)>=p(22),'v65 ON dwell not certified');newOn=0;reason=2;
    end
end
if newOn==0,hpCandidate=0;end
direct=min(u(6),hpCandidate);
z=service_difference_v65(P(hpCandidate),P(direct));charge=min(chargeBound,max(0,z(1)));
remaining=service_difference_v65(P(u(6)),P(direct));
% E(t)>=Elo-lambda*Ehi*dt-discharge*dt/etaD for a decreasing TES.
lossBudget=muliv(muliv(lam,P(initial(2))),dt);
available=minusiv(minusiv(P(initial(1)),P(cut(2))),lossBudget);
disBound=0;
if charge==0&&available(1)>0
    z=diviv(muliv(P(p(8)),available),dt);disBound=min(p(10),max(0,z(1)));
end
dis=min(disBound,max(0,remaining(1)));
remaining=service_difference_v65(remaining,P(dis));boiler=min(p(24),max(0,remaining(1)));
unmet=max(0,u(6)-direct-dis-boiler);served=direct+dis+boiler;
q=plusiv(P(direct),P(charge));B=minusiv(muliv(P(p(7)),P(charge)),diviv(P(dis),P(p(8))));
[en,integral]=flow(initial,dt,-lam,B);
assert(en(1)>=0&&en(2)<cap(1),'v65 interval capacity termination');
assert(dis==0||min(initial(1),en(1))>=cut(2),'v65 certified discharge cutoff');
assert(charge*dis==0,'v65 exclusive TES ports');
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
        assert(rate(2)<=sourceCap(2),'v65 finite source capacity');
        waterGlide=minusiv(hot,tank);waterGlide(1)=max(waterGlide(1),p(17));
        water=diviv(q,waterGlide);
        % Correlation hot=tank+approach proves denominator>=approach exactly.
        water(2)=min(water(2),diviv(q,P(p(17)))*[0;1]);
        assert(water(2)<=p(16),'v65 finite water capacity');
        src=plusiv(src,muliv(rate,diviv(dt,P(128))));
        srcRate=[min(srcRate(1),rate(1)) max(srcRate(2),rate(2))];
        hotRate=[min(hotRate(1),water(1)) max(hotRate(2),water(2))];
    end
end
function z=service_difference_v65(x,y)
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
assert(all([heat src work standing closs dloss]>=0),'v65 nonnegative ports');
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
assert(law(1)<=0&&law(2)>=0,'v65 global first law enclosure');
y(53:54)=law';y(115)=mode;y(116:117)=initial';y(118:119)=old(176:177);
y(120:127)=[direct+charge;direct;charge;dis;boiler;unmet;served;u(5)];
y(128:139)=reshape([heat;src;work;standing;closs;dloss]',12,1);
y(154:155)=srcRate';y(156:157)=hotRate';y(158:159)=plusiv(Ta,diviv(en,C))';
y(160:161)=initial';y(162:163)=age';y(164:171)=[on;reason;chargeBound;disBound;cap(1);cut(2);restart(1);u(6)-served-unmet];
y(172:173)=law';y(176:177)=plusiv(y(176:177)',dt)';y(179)=old(179)+1;y(180)=65;y(181:205)=p;
assert(y(176)<=u(3)&&u(3)<=y(177),'v65 sampled physical horizon enclosure');
assert(abs(y(171))<=32*eps(max(1,u(6))),'v65 demand closure');
end
