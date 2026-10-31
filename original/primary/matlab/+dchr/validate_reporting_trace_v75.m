function validate_reporting_trace_v75(a,trace)
% Input provenance is embedded by the actual saved v75 chart. This validator
% binds reporting operands and reconstructs energy offsets and header totals.
% It is a consistency gate, not authentication against coordinated forgery.
canonical=dchr.adapt_held_schedule_v74(a.schedule,a.p,a.initial);
assert(isequal(a.input,canonical.input)&&isequal(a.protocol_ticks,canonical.protocol_ticks), ...
    'DCHR:v75:AdapterBinding','Adapter operands must match canonical schedule');
n=size(a.input,1);
assert(isequal(size(trace),[n 1380])&&all(isfinite(trace(:))), ...
    'DCHR:v75:TraceShape','Finite complete saved-model trace required');
assert(all(trace(:,2)==75)&&all(all(trace(:,76:100)==repmat(a.p,n,1))), ...
    'DCHR:v75:TraceSchema','Saved v75 schema and immutable policy required');
assert(isequal(trace(:,73),a.input(:,5))&&isequal(trace(:,74),a.input(:,7))&& ...
    isequal(trace(:,75),a.input(:,8)+2*a.input(:,9)), ...
    'DCHR:v75:InputBinding','Held duration, source capacity and enable commands must match actual trace');
total=zeros(1,20);origin=[a.initial(1) a.initial(1)];
for k=1:n
    row=trace(k,:);count=row(13);
    assert(count>=1&&count<=16&&count==fix(count)&&row(14)>=0&&row(14)==fix(row(14)), ...
        'DCHR:v75:SegmentCount','Integer segment counts required');
    assert(all(row(100+80*count+1:end)==0),'DCHR:v75:UnusedSegments','Unused segment slots must be zero');
    ports=zeros(1,20);events=0;
    for j=1:count
        z=row(100+80*(j-1)+(1:80));energy=z(32:51);
        assert(z(1)==j&&z(2)>=0&&z(2)<=5&&z(2)==fix(z(2))&& ...
            z(3)>=0&&z(3)<=3&&z(3)==fix(z(3))&&z(7)>0&&z(7)<=z(8)&&all(z(24:29)>=0), ...
            'DCHR:v75:SegmentDomain','Positive segments, modes and nonnegative ports required');
        assert(all(energy>=0)&&all(energy(1:2:end)<=energy(2:2:end)), ...
            'DCHR:v75:EnergyDomain','Nonnegative ordered energy hulls required');
        assert(isequal(z(52:71),ports),'DCHR:v75:SegmentOffsets','Segment offsets must match preceding segment energies');
        heat=muliv(plusiv([z(25) z(25)],[z(26) z(26)]),z(7:8));
        service=muliv(repmat(z(25)+z(27)+z(28),1,2),z(7:8));
        back=muliv([z(28) z(28)],z(7:8));missing=muliv([z(29) z(29)],z(7:8));
        assert(isequal(energy(1:2),heat)&&isequal(energy(13:14),service)&& ...
            isequal(energy(15:16),back)&&isequal(energy(17:18),missing), ...
            'DCHR:v75:PortEnergyBinding','Heat, service, backup and unmet energy must match segment ports');
        sourceWork=plusiv(energy(3:4),energy(5:6));
        assert(sourceWork(1)<=heat(2)&&heat(1)<=sourceWork(2)&& ...
            isequal(energy(19:20),muliv([a.p(21) a.p(21)],energy(5:6))), ...
            'DCHR:v75:ElectricalEnergyBinding','Source/work first law and auxiliary multiplier required');
        for t=1:10,ix=2*t-1:2*t;ports(ix)=plusiv(ports(ix),energy(ix));end
        events=events+(z(3)>0);
    end
    assert(row(1)==z(2)&&row(14)==events,'DCHR:v75:ModeEvents','Final mode and event count must match segments');
    assert(isequal(row(15:30),ports(1:16))&&isequal(row(55:56),ports(17:18)), ...
        'DCHR:v75:IntervalTotals','Interval header energies must match segments');
    for t=1:10,ix=2*t-1:2*t;total(ix)=plusiv(total(ix),ports(ix));end
    assert(isequal(row(31:50),total),'DCHR:v75:CumulativeTotals','Cumulative energies must match every segment');
    assert(isequal(row(51:52),origin),'DCHR:v75:OriginBinding','Initial storage origin must match');
    law=minusiv(minusiv(minusiv(minusiv(plusiv(origin,plusiv(total(1:2),total(15:16))),total(13:14)),row(5:6)),total(7:8)),plusiv(total(9:10),total(11:12)));
    assert(isequal(row(53:54),law)&&law(1)<=0&&law(2)>=0, ...
        'DCHR:v75:RecomputedLaw','Stored residual must match recomputed first law');
end
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;
elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==-y(1),z=[0 0];
else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=minusiv(x,y)
if all(y==0),z=x;elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[0 0];else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=out(x)
z=[x(1)-2*eps(x(1)) x(2)+2*eps(x(2))];
assert(all(isfinite(z)),'DCHR:v75:ArithmeticDomain','Finite outward arithmetic required');
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
