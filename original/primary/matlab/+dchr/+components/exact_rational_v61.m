function z=exact_rational_v61(op,varargin)
% Host-only exact binary64 rational arithmetic. No Symbolic Toolbox required.
% Decimal strings are serialized; Java BigInteger is NOT a codegen claim.
J=@(x)javaObject('java.math.BigInteger',x);one=J('1');zero=J('0');
if strcmp(op,'from')
    x=varargin{1};assert(isa(x,'double')&&isreal(x)&&isscalar(x)&&isfinite(x),'DCHR:v61:Domain','Finite real scalar double required.');
    h=num2hex(x);head=hex2dec(h(1:3));ex=mod(head,2048);n=javaObject('java.math.BigInteger',h(4:16),16);
    if ex==0,power=-1074;else,n=n.add(one.shiftLeft(52));power=ex-1023-52;end
    if head>=2048,n=n.negate();end
    d=one;if power>=0,n=n.shiftLeft(power);else,d=d.shiftLeft(-power);end
else
    a=varargin{1};n=J(a.numerator);d=J(a.denominator);
    assert(d.compareTo(zero)>0,'DCHR:v61:Domain','Positive rational denominator required.');
    if numel(varargin)>1,b=varargin{2};m=J(b.numerator);e=J(b.denominator);assert(e.compareTo(zero)>0,'DCHR:v61:Domain','Positive denominator required.');end
    switch op
        case 'add',n=n.multiply(e).add(m.multiply(d));d=d.multiply(e);
        case 'sub',n=n.multiply(e).subtract(m.multiply(d));d=d.multiply(e);
        case 'mul',n=n.multiply(m);d=d.multiply(e);
        case 'div'
            assert(m.compareTo(zero)~=0,'DCHR:v61:Domain','Nonzero divisor required.');n=n.multiply(e);d=d.multiply(m);
            if d.signum()<0,n=n.negate();d=d.negate();end
        case 'cmp',z=double(n.multiply(e).compareTo(m.multiply(d)));return;
        case 'bounds'
            value=n.doubleValue()/d.doubleValue();assert(isfinite(value)&&isfinite(d.doubleValue()),'DCHR:v61:Resolution','Rational estimate overflow.');
            r=struct('numerator',char(n.toString()),'denominator',char(d.toString()));lo=value;hi=value;
            for it=1:16
                if dchr.components.exact_rational_v61('cmp',dchr.components.exact_rational_v61('from',lo),r)<=0,break;end
                lo=neighbor(lo,-1);
            end
            for it=1:16
                if dchr.components.exact_rational_v61('cmp',dchr.components.exact_rational_v61('from',hi),r)>=0,break;end
                hi=neighbor(hi,1);
            end
            assert(dchr.components.exact_rational_v61('cmp',dchr.components.exact_rational_v61('from',lo),r)<=0&&dchr.components.exact_rational_v61('cmp',dchr.components.exact_rational_v61('from',hi),r)>=0,'DCHR:v61:Resolution','Cannot bracket rational.');
            z=[lo hi];return;
        otherwise,error('DCHR:v61:Domain','Unknown rational operation.');
    end
end
g=n.abs().gcd(d);n=n.divide(g);d=d.divide(g);
z=struct('numerator',char(n.toString()),'denominator',char(d.toString()));
end
function y=neighbor(x,direction)
if x==0,y=direction*eps(0);return;end
u=typecast(x,'uint64');if (x>0)==(direction>0),u=u+uint64(1);else,u=u-uint64(1);end
y=typecast(u,'double');assert(isfinite(y),'DCHR:v61:Resolution','Neighbor overflow.');
end


