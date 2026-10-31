function effective=electrical_policy_v83(raw)
%#codegen
% Conservative constant compressor ceiling across the entire TES domain.
assert(all(isfinite(raw))&&raw(26)>=0,'v83 finite nonnegative compressor ceiling');
effective=raw(1:25);
% All interval operations enclose exact binary operand expressions.
Te=sub(sub([raw(12) raw(12)],[raw(13) raw(13)]),[raw(14) raw(14)]);
A=mul([raw(15) raw(15)],add(Te,[273.15 273.15]));
floor=add([raw(19) raw(19)],[raw(20) raw(20)]);
hot=add([raw(3) raw(3)],[raw(17) raw(17)]);
hot=[max(floor(1),hot(1)) max(floor(2),hot(2))];
L=sub(add(hot,[raw(18) raw(18)]),Te);
assert(A(1)>0&&L(1)>0,'v83 positive electrical axes');
cop=add([1 1],divide(A,L));
cap=mul([raw(26) raw(26)],cop);
effective(11)=min(raw(11),max(0,cap(1)));
end
function z=add(x,y),z=out([x(1)+y(1) x(2)+y(2)]);end
function z=sub(x,y),z=out([x(1)-y(2) x(2)-y(1)]);end
function z=mul(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=divide(x,y)
assert(y(1)>0,'v83 positive electrical denominator');
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v83 electrical arithmetic overflow');
z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z)),'v83 electrical outward overflow');
end
