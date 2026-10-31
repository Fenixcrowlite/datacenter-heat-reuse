function monitor_temporal_commit_v77(u,p,old,y)
%#codegen
% Verify the candidate record BEFORE trace emission and retained-memory commit.
% Trace schema remains 75; model release is 77. No thermal solver is called.
assert(all(isfinite(y))&&y(2)==75&&all(y(76:100)==p),'v77 schema');
assert(y(13)>=1&&y(13)<=16&&y(13)==fix(y(13)),'v77 segment count');
assert(all(y(100+80*y(13)+1:end)==0),'v77 unused segments');
assert(all(y(73:75)==[u(5);u(7);u(8)+2*u(9)]),'v77 input binding');
if old(2)==0
    E=[u(10) u(10)];on=u(11);age=[u(12) u(12)];tag=0;clock=[0 0];
else
    assert(old(2)==75&&all(old(76:100)==p),'v77 retained schema');
    E=old(5:6)';on=old(7);age=old(8:9)';tag=old(12);clock=old(10:11)';
end
boundary=plusiv(clock,[u(5) u(5)]);
assert(all(y(3:4)'==E)&&all(y(58:59)'==clock)&& ...
    all(y(60:61)'==boundary)&&all(y(10:11)'==boundary),'v77 macro continuity');
t=[0 0];events=0;mode=0;
for j=1:y(13)
    z=y(100+80*(j-1)+(1:80));d=z(7:8)';event=z(3);reason=z(23);
    assert(d(1)>0&&d(1)<=d(2)&&ismember(event,0:3)&& ...
        ismember(reason,0:3)&&ismember(z(4),[0 1]),'v77 transition domain');
    assert(all(z(5:6)'==t)&&all(z(9:10)'==plusiv(t,d)),'v77 segment clock');
    assert(all(z(11:12)'==E)&&z(78)==on&&all(z(79:80)'==age)&&z(21)==tag,'v77 incoming memory');
    currentOn=on;currentAge=age;
    if reason>0
        assert((reason==1&&on==0)||(reason>=2&&on==1),'v77 boundary transition');
        currentAge=[0 0];currentOn=double(reason==1);
    end
    assert(z(19)==currentOn&&all(z(15:16)'==currentAge),'v77 boundary memory');
    nextOn=currentOn;nextAge=plusiv(currentAge,d);nextTag=0;
    if event==1,nextOn=0;nextAge=[0 0];nextTag=1;
    elseif event==2,nextTag=2;
    elseif event==3,nextOn=1;nextAge=[0 0];nextTag=3*z(4);end
    assert(z(20)==nextOn&&all(z(17:18)'==nextAge)&&z(22)==nextTag&& ...
        ((event==0&&z(4)==0)||(event==1&&z(4)==1)||(event==2&&z(4)==1)||event==3),'v77 event memory');
    if j==y(13)
        assert(event==0&&all(d==minusiv([u(5) u(5)],t)),'v77 held boundary');
    else
        assert(event>0,'v77 interior event');
    end
    E=z(13:14)';on=nextOn;age=nextAge;tag=nextTag;t=z(9:10)';
    events=events+double(event>0);mode=z(2);
end
assert(all(y(5:6)'==E)&&y(7)==on&&all(y(8:9)'==age)&&y(12)==tag,'v77 endpoint memory');
assert(y(1)==mode&&y(14)==events,'v77 mode event count');
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
function z=out(x)
z=[x(1)-2*eps(x(1)) x(2)+2*eps(x(2))];
assert(all(isfinite(z)),'v77 temporal arithmetic');
end
