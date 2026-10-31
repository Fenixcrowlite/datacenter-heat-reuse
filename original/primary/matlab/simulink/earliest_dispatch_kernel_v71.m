function y=earliest_dispatch_kernel_v71(u,p,old)
%#codegen
% Interval-valued event segments with symbolic threshold contacts, never a
% root midpoint. See audit/Earliest_dispatch_derivation_v71.md for schema.
assert(all(isfinite([u;p;old])),'v71 finite domain');
assert(u(1)==1&&u(5)>0&&u(6)>=0&&u(7)>=0&&all(u(8:9)==0|u(8:9)==1),'v71 input domain');
assert(all(p([1 7 8 13 14 16 17 18])>0)&&p(7)<=1&&p(8)<=1&&p(6)>=0&& ...
    all(p([9 10 11 21 22 23 24])>=0)&&p(15)>0&&p(15)<=1,'v71 equipment domain');
assert(p(2)>-273.15&&p(2)<p(4)&&p(4)<p(5)&&p(5)<p(25)&&p(25)<p(3)&& ...
    p(19)<=p(4)&&p(6)*u(5)<=1,'v71 thermal/span domain');
P=@(v)[v v];C=P(p(1));Ta=P(p(2));cap=muliv(C,minusiv(P(p(3)),Ta));
cut=muliv(C,minusiv(P(p(4)),Ta));restart=muliv(C,minusiv(P(p(5)),Ta));stop=muliv(C,minusiv(P(p(25)),Ta));
y=zeros(1380,1);y(2)=71;y(76:100)=p;
if old(2)==0
    assert(u(10)>=0&&u(10)<cap(1)&&ismember(u(11),[0 1])&&u(12)>=0,'v71 initial domain');
    E=P(u(10));on=u(11);age=P(u(12));clock=P(0);tag=0;total=zeros(20,1);origin=E;
else
    assert(old(2)==71&&all(old(76:100)==p),'v71 immutable policy');
    E=old(5:6)';on=old(7);age=old(8:9)';clock=old(10:11)';tag=old(12);total=old(31:50);origin=old(51:52)';
end
assert(E(1)>=0&&E(1)<=E(2)&&E(2)<cap(2)&&age(1)>=0&&age(1)<=age(2),'v71 retained bounds');
boundary=plusiv(clock,P(u(5)));assert(u(3)>clock(2)&&boundary(1)<=u(3)&&boundary(2)>=u(3),'v71 physical clock');
y(3:4)=E';y(51:52)=origin';y(58:59)=clock';y(60:61)=boundary';
Te=minusiv(minusiv(P(p(12)),P(p(13))),P(p(14)));a=muliv(P(p(15)),plusiv(Te,P(273.15)));
floor=plusiv(P(p(19)),P(p(20)));lf=minusiv(plusiv(floor,P(p(18))),Te);
assert(a(1)>0&&lf(1)>0,'v71 refrigerant domain');
limit=max(0,min([p(11),muliv(muliv(P(u(7)),P(p(13))),plusiv(P(1),diviv(lf,a)))*[1;0],muliv(P(p(16)),P(p(17)))*[1;0]]));
t=P(0);ports=zeros(20,1);finished=false;events=0;lastmode=0;
for slot=1:16
    assert(~finished,'v71 internal finished sequence');
    remaining=minusiv(P(u(5)),t);assert(remaining(1)>0,'v71 unresolved remaining duration');
    incoming=E;incomingAge=age;incomingOn=on;incomingTag=tag;
    potential=max(0,min(p(9),limit-min(u(6),limit)));
    belowStop=(tag==2||tag==3)||(tag==0&&E(2)<stop(1));
    canCharge=u(9)==1&&belowStop&&potential>0;
    request=u(6);if canCharge,request=request+potential;end
    sink=request>0;futureSink=u(6)>0||(u(9)==1&&potential>0);
    atRestart=tag==3||(tag==2)||(tag==0&&E(2)<=restart(1));
    reason=0;
    if on==1&&(limit==0||~sink),on=0;age=P(0);reason=3;
    elseif on==1&&u(8)==0
        assert(age(1)>=p(22),'v71 ON dwell not certified');on=0;age=P(0);reason=2;
    elseif on==0&&u(8)==1&&limit>0&&sink&&atRestart&&age(1)>=p(23)
        on=1;age=P(0);reason=1;
    end
    hp=0;if on==1,hp=min(request,limit);end
    direct=min(u(6),hp);charge=0;if canCharge,charge=min(potential,max(0,hp-direct));end
    dis=0;aboveCut=tag==1||tag==3||(tag==0&&E(1)>cut(2));
    if charge==0&&aboveCut,dis=min(p(10),max(0,u(6)-direct));end
    boiler=min(p(24),max(0,u(6)-direct-dis));unmet=max(0,u(6)-direct-dis-boiler);
    B=minusiv(muliv(P(p(7)),P(charge)),diviv(P(dis),P(p(8))));
    mode=0;if unmet>0,mode=5;elseif boiler>0,mode=4;elseif dis>0,mode=3;elseif charge>0,mode=2;elseif direct>0,mode=1;end
    candidates=zeros(3,15);enabled=[charge>0 dis>0 on==0&&u(8)==1&&limit>0&&futureSink];
    if enabled(1)
        deriv=minusiv(B,muliv(P(p(6)),stop));
        if deriv(1)>0,candidates(1,:)=certify_event_root_v71(E,B,p(6),stop,1,u(5),0,P(0))';
        elseif deriv(2)>0,assert(false,'v71 unresolved stop derivative');end
    end
    if enabled(2),candidates(2,:)=certify_event_root_v71(E,B,p(6),cut,-1,u(5),0,P(0))';end
    if enabled(3)
        if atRestart
            r=zeros(1,15);r(1)=3;r(8:9)=max(0,minusiv(P(p(23)),age));r(10:11)=r(8:9);r(13)=-1;r(14:15)=restart;candidates(3,:)=r;
        else
            deriv=minusiv(B,muliv(P(p(6)),restart));
            if deriv(2)<0,candidates(3,:)=certify_event_root_v71(E,B,p(6),restart,-1,u(5),p(23),age)';
            elseif deriv(1)<0,assert(false,'v71 unresolved restart derivative');end
        end
    end
    duration=remaining;event=0;
    for j=1:3
        r=candidates(j,:);if r(1)==0,continue;end
        if r(1)==2
            % An unresolved root at the original macro span is harmless only
            % if the entire actual remaining trajectory is certainly before it.
            [tail,~]=flow(E,remaining,p(6),B);
            if j==1,before=tail(2)<stop(1);elseif j==2,before=tail(1)>cut(2);else,before=tail(1)>restart(2);end
            assert(before,'v71 unresolved event boundary');continue;
        end
        ready=r(10:11);
        if ready(1)>remaining(2),continue;end
        assert(ready(2)<remaining(1),'v71 unresolved event boundary');
        if event==0||ready(2)<duration(1),duration=ready;event=j;
        elseif ready(1)<=duration(2),assert(false,'v71 unresolved enabled event ordering');end
    end
    assert(duration(1)>0,'v71 zero-progress event');
    [endpoint,integral]=flow(E,duration,p(6),B);newtag=0;thermal=0;
    if event==1,endpoint=stop;newtag=1;thermal=1;
    elseif event==2,endpoint=cut;newtag=2;thermal=1;
    elseif event==3
        r=candidates(3,:);
        if r(1)==1&&r(2)>r(9),endpoint=restart;newtag=3;thermal=1;
        elseif r(8)>r(3)||r(1)==3
            % The age identity age+(minOFF-age)=minOFF is retained,
            % not reconstructed from independent interval endpoints.
            assert(endpoint(2)<=restart(2)||atRestart,'v71 dwell thermal readiness');
        else,assert(false,'v71 unresolved thermal/dwell ordering');end
        if thermal==1,assert(plusiv(age,duration)*[1;0]>=p(23),'v71 OFF dwell not certified');end
    end
    assert(endpoint(1)>=0&&endpoint(2)<cap(2),'v71 TES bounds');
    assert(dis==0||event==2||endpoint(1)>=cut(2),'v71 discharge cutoff');
    assert(charge==0||event==1||endpoint(2)<stop(1),'v71 charging stop');
    % The source rectangles cover the full event duration box. The exact
    % root/threshold relation is recorded; Cartesian evaluation only widens it.
    q=plusiv(P(direct),P(charge));src=P(0);
    for cell=1:32
        t0=muliv(duration,P((cell-1)/32));t1=muliv(duration,P(cell/32));
        [e0,~]=flow(E,t0,p(6),B);[e1,~]=flow(E,t1,p(6),B);
        eh=[min(e0(1),e1(1)) max(e0(2),e1(2))];hot=plusiv(plusiv(Ta,diviv(eh,C)),P(p(17)));
        hot=[max(floor(1),hot(1)) max(floor(2),hot(2))];lift=minusiv(plusiv(hot,P(p(18))),Te);
        rate=muliv(q,diviv(a,plusiv(a,lift)));
        assert(rate(2)<=muliv(P(u(7)),P(p(13)))*[0;1],'v71 finite source capacity');
        src=plusiv(src,muliv(rate,diviv(duration,P(32))));
    end
    assert(q(2)<=muliv(P(p(16)),P(p(17)))*[0;1],'v71 finite water capacity');
    heat=muliv(q,duration);work=minusiv(heat,src);standing=muliv(P(p(6)),integral);
    closs=muliv(minusiv(P(1),P(p(7))),muliv(P(charge),duration));
    dloss=muliv(minusiv(diviv(P(1),P(p(8))),P(1)),muliv(P(dis),duration));
    service=muliv(P(direct+dis+boiler),duration);back=muliv(P(boiler),duration);missing=muliv(P(unmet),duration);aux=muliv(P(p(21)),work);
    increment=[heat';src';work';standing';closs';dloss';service';back';missing';aux'];
    assert(all(increment>=0),'v71 nonnegative energy');
    seglaw=minusiv(minusiv(minusiv(minusiv(plusiv(E,plusiv(heat,back)),service),endpoint),standing),plusiv(closs,dloss));
    assert(seglaw(1)<=0&&seglaw(2)>=0,'v71 segment first law');
    offset=ports;for j=1:10,ix=2*j-1:2*j;ports(ix)=plusiv(ports(ix)',increment(ix)')';end
    elapsed=plusiv(t,duration);newage=plusiv(age,duration);outOn=on;
    if event==1,outOn=0;newage=P(0);elseif event==3,outOn=1;newage=P(0);end
    z=zeros(80,1);z(1:4)=[slot;mode;event;thermal];z(5:6)=t';z(7:8)=duration';z(9:10)=elapsed';
    z(11:14)=[E';endpoint'];z(15:18)=[age';newage'];z(19:23)=[on;outOn;incomingTag;newtag;reason];
    z(24:29)=[hp;direct;charge;dis;boiler;unmet];z(30:31)=B';z(32:51)=increment;z(52:71)=offset;
    if event>0,z(72:73)=candidates(event,2:3)';z(74:75)=candidates(event,8:9)';z(76:77)=candidates(event,14:15)';end
    z(78:80)=[incomingOn;incomingAge'];y(100+80*(slot-1)+(1:80))=z;
    E=endpoint;on=outOn;age=newage;tag=newtag;lastmode=mode;t=elapsed;
    if event==0
        % Exact held boundary identity t_start+(dt-t_start)=dt, with its
        % expression recorded in duration/offset fields. No midpoint used.
        t=P(u(5));finished=true;y(13)=slot;break;
    else,events=events+1;end
end
assert(finished,'v71 event segment budget');
for j=1:10,ix=2*j-1:2*j;total(ix)=plusiv(total(ix)',ports(ix)')';end
law=minusiv(minusiv(minusiv(minusiv(plusiv(origin,plusiv(total(1:2)',total(15:16)')),total(13:14)'),E),total(7:8)'),plusiv(total(9:10)',total(11:12)'));
assert(law(1)<=0&&law(2)>=0,'v71 cumulative first law');
y(1)=lastmode;y(5:6)=E';y(7)=on;y(8:9)=age';y(10:11)=boundary';y(12)=tag;y(14)=events;
y(15:30)=ports(1:16);y(31:50)=total;y(53:54)=law';y(55:56)=ports(17:18);y(57)=limit;
end
function [en,integral]=flow(initial,t,lambda,B)
if all(t==0),en=initial;integral=[0 0];return;end
P=@(v)[v v];k=-P(lambda);x=muliv(k,t);assert(max(abs(x))<=2,'v71 outward span');
v=plusiv(muliv(k,initial),B);f1=P(1);f2=P(.5);term=P(1);
for ii=1:24,term=diviv(muliv(term,x),P(ii+1));f1=plusiv(f1,term);f2=plusiv(f2,diviv(term,P(ii+2)));end
fac=P(1);for ii=2:26,fac=muliv(fac,P(ii));end
tail=diviv(P(268435456),fac);f1=plusiv(f1,[-tail(2) tail(2)]);f2=plusiv(f2,[-tail(2) tail(2)]);
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
assert(y(1)>0,'v71 positive denominator');if all(x==0),z=[0 0];return;end
if x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[1 1];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v71 arithmetic overflow');z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];assert(all(isfinite(z)),'v71 outward overflow');
end
