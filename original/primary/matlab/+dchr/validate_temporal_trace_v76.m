function validate_temporal_trace_v76(a,trace)
% Additive saved-v75 temporal protocol gate. No thermal solver is called.
dchr.validate_reporting_trace_v75(a,trace);
E=repmat(a.initial(1),1,2);on=a.initial(2);age=repmat(a.initial(3),1,2);
tag=0;clock=[0 0];
for k=1:size(trace,1)
    r=trace(k,:);dt=a.schedule(k,1);boundary=plusiv(clock,[dt dt]);
    assert(isequal(r(3:4),E)&&isequal(r(58:59),clock)&& ...
        isequal(r(60:61),boundary)&&isequal(r(10:11),boundary), ...
        'DCHR:v76:MacroContinuity','Retained inventory and physical clocks must match');
    t=[0 0];
    for j=1:r(13)
        z=r(100+80*(j-1)+(1:80));duration=z(7:8);event=z(3);reason=z(23);
        assert(isequal(z(5:6),t)&&isequal(z(9:10),plusiv(t,duration)), ...
            'DCHR:v76:SegmentClock','Segment offsets and elapsed hulls must match');
        assert(isequal(z(11:12),E)&&z(78)==on&&isequal(z(79:80),age)&&z(21)==tag, ...
            'DCHR:v76:SegmentMemory','Incoming inventory, latch, age and contact must match');
        assert(ismember(reason,0:3)&&ismember(z(4),[0 1]), ...
            'DCHR:v76:TransitionDomain','Known boundary reason and thermal-contact flag required');
        currentOn=on;currentAge=age;
        if reason>0
            currentAge=[0 0];currentOn=double(reason==1);
            assert((reason==1&&on==0)||(reason>=2&&on==1), ...
                'DCHR:v76:BoundaryTransition','Boundary transition must change the incoming latch');
        end
        assert(z(19)==currentOn&&isequal(z(15:16),currentAge), ...
            'DCHR:v76:BoundaryMemory','Only explicit boundary transitions may reset age');
        nextOn=currentOn;nextAge=plusiv(currentAge,duration);nextTag=0;
        if event==1,nextOn=0;nextAge=[0 0];nextTag=1;
        elseif event==2,nextTag=2;
        elseif event==3,nextOn=1;nextAge=[0 0];nextTag=3*z(4);end
        assert(z(20)==nextOn&&isequal(z(17:18),nextAge)&&z(22)==nextTag&& ...
            ((event==0&&z(4)==0)||(event==1&&z(4)==1)||(event==2&&z(4)==1)||event==3), ...
            'DCHR:v76:EventMemory','Event latch, age and symbolic contact must match');
        if j==r(13)
            assert(event==0&&isequal(duration,minusiv([dt dt],t)), ...
                'DCHR:v76:HeldBoundary','Last segment must consume the exact held remainder');
        else
            assert(event>0,'DCHR:v76:InteriorEvent','Only event segments may precede the final hold');
        end
        E=z(13:14);on=nextOn;age=nextAge;tag=nextTag;t=z(9:10);
    end
    assert(isequal(r(5:6),E)&&r(7)==on&&isequal(r(8:9),age)&&r(12)==tag, ...
        'DCHR:v76:EndpointMemory','Header endpoint must equal the final segment memory');
    clock=boundary;
end
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
assert(all(isfinite(z)),'DCHR:v76:ArithmeticDomain','Finite temporal arithmetic required');
end
