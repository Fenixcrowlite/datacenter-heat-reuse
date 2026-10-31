function [checked,summary,nextClock]=stateflow_contract_gate_v34(raw,plan,x,cfg,h,model_dt,clock,m,c)
%#codegen
% Per-segment independent ODE/HP/service laws, then integrate powers.
dt=cfg(1);cap=cfg(2);rate=cfg(7);ec=cfg(5);ed=cfg(6);
assert(all(isfinite(cfg)) && dt==model_dt && dt>0,'Invalid model interval.');
assert(all(isfinite(x)) && all(isfinite(h)),'Invalid host inputs.');
energy=zeros(9,1);loss=zeros(3,1);highest=0;
offset=0;previousE=plan(2,1);prevOn=m(1);prevAge=m(2);
for k=1:64
    z=raw((k-1)*28+(1:28));s=plan(:,k);span=z(2);
    finite=z;finite(15)=0;
    assert(all(isfinite(finite)) && all(isfinite(s([1:7 9:14]))),'Nonfinite segment.');
    tol=1e-9*max(1,cap+(z(11)+cfg(11))*dt);ptol=tol/max(dt,eps);
    assert(span>=0 && span==s(1) && z(3)==s(14) && abs(z(4)-s(2))<=tol,'Segment schedule mismatch.');
    assert(z(1)==floor(z(1)) && z(1)>=0 && z(1)<=5,'Undefined segment state.');
    assert(min(z(4:5))>=-tol && max(z(4:5))<=cap+tol,'TES bounds failure.');
    assert(all(z(6:14)>=-ptol) && all(z(16:20)>=-tol),'Negative flows/losses.');
    assert(z(7)<=cfg(3)+ptol && z(8)<=cfg(4)+ptol && z(9)<=cfg(11)+ptol && z(7)*z(8)==0,'Instantaneous port limits.');
    if span>0
        P=ec*z(7)-z(8)/ed;r=exp(-rate*span);phi=span;
        if rate>0 && rate*span>0,phi=-expm1(-rate*span)/rate;end
        assert(abs(z(5)-(z(4)*r+P*phi))<=tol,'Segment ODE failure.');
        assert(z(8)==0 || min(z(4:5))>=cfg(8)-tol,'Discharge crosses cutoff.');
        assert(abs(z(17)-(z(4)+P*span-z(5)))<=tol && ...
            abs(z(18)-(1-ec)*z(7)*span)<=tol && abs(z(19)-(1/ed-1)*z(8)*span)<=tol,'Segment losses failure.');
        assert(abs(z(11)-z(12)-z(13))*span<=tol && abs(z(11)-z(6)-z(7))*span<=tol,'HP first law/allocation failure.');
        assert(abs(x(4)-z(6)-z(8)-z(9)-z(10))*span<=tol && ...
            abs(z(20)-z(6)-z(8)-z(9))*span<=tol,'Segment service closure.');
        expected=0;
        if z(10)>0,expected=5;elseif z(9)>0,expected=4;elseif z(8)>0,expected=3;
        elseif z(7)>0,expected=2;elseif z(6)>0,expected=1;end
        assert(z(1)==expected,'State does not authorize actual segment flows.');
        assert(abs(x(1)-z(13)-z(16))<=ptol && z(11)<=h(1)+ptol && z(11)<=z(14)+ptol,'Source/request/capacity limit.');
        if z(11)>0
            carnot=(x(3)+273.15)/(x(3)-x(2));
            nominal=h(2)*carnot;if h(6)==1,nominal=h(7)+h(8)*(x(3)-x(2))+h(9)*(x(3)-x(2))^2;end
            expectedCOP=min(h(4),nominal)*(1-h(5)+h(5)*z(11)/h(1));
            assert(isfinite(z(15)) && z(15)>=h(3)-ptol && z(15)<=carnot+ptol && z(25)==1 && ...
                abs(z(15)-expectedCOP)<=ptol && abs(z(12)*z(15)-z(11))<=ptol,'Segment COP failure.');
        else,assert(isnan(z(15)) && z(25)==0,'Off HP convention.');end
        highest=max(highest,z(1));
    else
        assert(z(1)==0 && all(z(6:14)==0) && all(z(17:21)==0) && z(5)==z(4),'Zero-span segment has service.');
    end
    assert(abs(z(22)-(cfg(10)+z(4)/cfg(9)))<=tol/cfg(9) && ...
        abs(z(23)-(cfg(10)+z(5)/cfg(9)))<=tol/cfg(9),'Segment temperature mismatch.');
    residual=z(4)+(z(13)+z(12)+z(9)-z(20))*span-z(5)-sum(z(17:19));
    assert(abs(residual)<=tol && abs(z(21)-residual)<=tol,'Segment system balance failure.');
    assert(z(24)==s(13) && ismember(z(24),[0 1 2 3 4]),'Invalid event kind.');
    assert(abs(z(3)-offset)<=tol && abs(z(4)-previousE)<=tol,'Ordered event/energy handoff failure.');
    assert(z(26)==s(15) && ismember(z(26),[0 1]) && abs(z(27)-s(16))<=tol && ...
        abs(z(28)-z(27)-span)<=tol && abs(z(28)-s(18))<=tol,'Physical-hour clock failure.');
    if z(26)~=prevOn
        assert(stateflow_supervisor_guard_v34(z(26),s,cfg,c,prevAge),'Unauthorized HP latch transition.');
    else
        assert(s(17)==0 && abs(z(27)-prevAge)<=tol,'Persistent timer continuity failure.');
    end
    if span>0
        assert((z(26)==0 && z(11)==0) || (z(26)==1 && z(11)>0),'HP latch/allocation mismatch.');
    end
    if z(24)==1,assert(abs(z(5)-cap)<=tol,'Capacity event mismatch.');end
    if z(24)==2,assert(abs(z(5)-cfg(8))<=tol,'Cutoff event mismatch.');end
    prevOn=z(26);prevAge=z(28);previousE=z(5);offset=offset+span;
    energy=energy+[z(6:14)]*span;loss=loss+z(17:19);
end
first=raw(1:28);last=raw(1765:1792);
tol=1e-9*max(1,cap+(energy(6)+cfg(11)*dt));
assert(abs(offset-dt)<=tol,'Interval partition failure.');
assert(all(abs(clock-[prevOn;prevAge])<=tol),'Final persistent supervisor clock mismatch.');
nextClock=clock;
supplied=(energy(1)+energy(3)+energy(4))/dt;
residual=first(4)+energy(7)+energy(8)+energy(4)-supplied*dt-last(5)-sum(loss);
assert(abs(residual)<=tol,'Integrated first law failure.');
cop=NaN;if energy(7)>0,cop=energy(6)/energy(7);end
summary=[highest;energy(1:5)/dt;first(4)*exp(-rate*dt);last(5);loss;supplied;residual; ...
    first(22);last(23);max(0,first(4)-cfg(8));max(0,last(5)-cfg(8)); ...
    x(4);energy(6:9)/dt;cop;double(energy(6)>0);x(1)-energy(8)/dt];
checked=raw;
end

function ok=stateflow_supervisor_guard_v34(target,s,p,c,age)
%#codegen
% Independent Stateflow transition permission. Safety overrides ON dwell.
ok=false;tol=1e-10*max(1,p(2));
if target==1
    ok=s(17)==3 && s(2)<=c(1)+tol && age>=c(3)-tol && s(4)>0 && s(16)==0;
else
    ok=s(16)==0 && ((s(17)==2 && s(2)>=p(2)-tol && age>=c(2)-tol) || ...
        (s(17)==1 && s(4)==0));
end
end
