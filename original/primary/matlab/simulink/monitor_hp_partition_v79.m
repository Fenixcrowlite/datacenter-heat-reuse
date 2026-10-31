function monitor_hp_partition_v79(u,p,old,y)
%#codegen
% Necessary temperature-dependent HP integral bounds, not equipment calibration.
monitor_energy_commit_v78(u,p,old,y);
Te=subiv(subiv(P(p(12)),P(p(13))),P(p(14)));
A=muliv(P(p(15)),addiv(Te,P(273.15)));
floor=addiv(P(p(19)),P(p(20)));
for j=1:y(13)
    z=y(100+80*(j-1)+(1:80));
    heat=z(32:33)';source=z(34:35)';work=z(36:37)';
    if z(24)==0
        assert(all(source==0)&&all(work==0),'v79 OFF HP energies');
        continue;
    end
    % Held affine TES flow is monotone. Its endpoint hull extrema therefore
    % bound all intermediate temperatures; no production flow/root call.
    E=[min(z(11),z(13)) max(z(12),z(14))];
    hot=addiv(addiv(P(p(2)),diviv(E,P(p(1)))),P(p(17)));
    hot=[max(floor(1),hot(1)) max(floor(2),hot(2))];
    lift=subiv(addiv(hot,P(p(18))),Te);
    assert(A(1)>0&&lift(1)>0,'v79 positive HP axes');
    % Source fraction decreases with lift; work fraction increases. Integral
    % means belong to these ranges for every positive segment duration.
    sf=[diviv(P(A(1)),addiv(P(A(1)),P(lift(2))))*[1;0] ...
        diviv(P(A(2)),addiv(P(A(2)),P(lift(1))))*[0;1]];
    wf=[diviv(P(lift(1)),addiv(P(A(2)),P(lift(1))))*[1;0] ...
        diviv(P(lift(2)),addiv(P(A(1)),P(lift(2))))*[0;1]];
    sb=muliv(heat,sf);wb=muliv(heat,wf);
    assert(source(1)<=sb(2)&&sb(1)<=source(2),'v79 source temperature partition');
    assert(work(1)<=wb(2)&&wb(1)<=work(2),'v79 compressor temperature partition');
end
end
function z=P(x),z=[x x];end
function z=addiv(x,y)
z=out([x(1)+y(1) x(2)+y(2)]);
end
function z=subiv(x,y)
z=out([x(1)-y(2) x(2)-y(1)]);
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
v=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(v) max(v)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v79 positive denominator');
v=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(v) max(v)]);
end
function z=out(x)
z=[x(1)-2*eps(x(1)) x(2)+2*eps(x(2))];assert(all(isfinite(z)),'v79 HP bound arithmetic');
end
