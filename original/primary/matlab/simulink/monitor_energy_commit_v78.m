function monitor_energy_commit_v78(u,p,old,y)
%#codegen
% Candidate energy/port verification before emission and retained-state commit.
% v77 checks schema/count/temporal links first. No thermal solver is called here.
monitor_temporal_commit_v77(u,p,old,y);
ports=zeros(20,1);total=zeros(20,1);origin=[u(10) u(10)];
if old(2)~=0,total=old(31:50);origin=old(51:52)';end
assert(all(y(51:52)'==origin),'v78 origin binding');
cap=muliv([p(1) p(1)],minusiv([p(3) p(3)],[p(2) p(2)]));
assert(y(57)>=0&&y(57)<=p(11)&&y(57)<=y(68)&&y(57)<=y(70),'v78 selected capacity');
for j=1:y(13)
    z=y(100+80*(j-1)+(1:80));d=z(7:8)';q=z(24:29);inc=z(32:51);
    assert(z(1)==j&&ismember(z(2),0:5)&&all(q>=0),'v78 port domain');
    assert(q(1)<=y(57)&&q(3)<=p(9)&&q(4)<=p(10)&&q(5)<=p(24)&& ...
        (q(3)==0||q(4)==0)&&(z(19)==1||q(1)==0),'v78 port capacity');
    heatPower=plusiv([q(2) q(2)],[q(3) q(3)]);
    assert(heatPower(1)<=q(1)&&q(1)<=heatPower(2),'v78 HP allocation');
    servicePower=plusiv(plusiv([q(2) q(2)],[q(4) q(4)]),[q(5) q(5)]);
    allocation=plusiv(servicePower,[q(6) q(6)]);
    assert(allocation(1)<=u(6)&&u(6)<=allocation(2),'v78 demand allocation');
    expectedMode=0;
    if q(6)>0,expectedMode=5;elseif q(5)>0,expectedMode=4;elseif q(4)>0,expectedMode=3;
    elseif q(3)>0,expectedMode=2;elseif q(2)>0,expectedMode=1;end
    assert(z(2)==expectedMode,'v78 mode allocation');
    assert(z(11)>=0&&z(11)<=z(12)&&z(12)<cap(2)&& ...
        z(13)>=0&&z(13)<=z(14)&&z(14)<cap(2),'v78 TES domain');
    B=minusiv(muliv([p(7) p(7)],[q(3) q(3)]),diviv([q(4) q(4)],[p(8) p(8)]));
    assert(all(z(30:31)'==B),'v78 forcing binding');
    assert(all(inc>=0)&&all(inc(1:2:end)<=inc(2:2:end)),'v78 energy domain');
    assert(all(z(52:71)==ports),'v78 segment offsets');
    heat=muliv(heatPower,d);service=muliv([q(2)+q(4)+q(5) q(2)+q(4)+q(5)],d);
    back=muliv([q(5) q(5)],d);missing=muliv([q(6) q(6)],d);
    assert(all(inc(1:2)'==heat)&&all(inc(13:14)'==service)&& ...
        all(inc(15:16)'==back)&&all(inc(17:18)'==missing),'v78 port energy binding');
    closs=muliv(minusiv([1 1],[p(7) p(7)]),muliv([q(3) q(3)],d));
    dloss=muliv(minusiv(diviv([1 1],[p(8) p(8)]),[1 1]),muliv([q(4) q(4)],d));
    assert(all(inc(9:10)'==closs)&&all(inc(11:12)'==dloss),'v78 efficiency loss binding');
    sourceWork=plusiv(inc(3:4)',inc(5:6)');
    assert(sourceWork(1)<=heat(2)&&heat(1)<=sourceWork(2),'v78 HP first law');
    assert(all(inc(19:20)'==muliv([p(21) p(21)],inc(5:6)')),'v78 auxiliary binding');
    law=minusiv(minusiv(minusiv(minusiv(plusiv(z(11:12)',plusiv(heat,back)),service),z(13:14)'),inc(7:8)'),plusiv(closs,dloss));
    assert(law(1)<=0&&law(2)>=0,'v78 segment first law');
    for k=1:10,ix=2*k-1:2*k;ports(ix)=plusiv(ports(ix)',inc(ix)')';end
end
assert(all(y(15:30)==ports(1:16))&&all(y(55:56)==ports(17:18)),'v78 interval totals');
for k=1:10,ix=2*k-1:2*k;total(ix)=plusiv(total(ix)',ports(ix)')';end
assert(all(y(31:50)==total),'v78 cumulative totals');
law=minusiv(minusiv(minusiv(minusiv(plusiv(origin,plusiv(total(1:2)',total(15:16)')),total(13:14)'),y(5:6)'),total(7:8)'),plusiv(total(9:10)',total(11:12)'));
assert(all(y(53:54)'==law)&&law(1)<=0&&law(2)>=0,'v78 cumulative first law');
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;
elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==-y(1),z=[0 0];
else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=minusiv(x,y)
if all(y==0),z=x;elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[0 0];
else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v78 positive denominator');if all(x==0),z=[0 0];return;end
if x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[1 1];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(x)
z=[x(1)-2*eps(x(1)) x(2)+2*eps(x(2))];assert(all(isfinite(z)),'v78 energy arithmetic');
end
