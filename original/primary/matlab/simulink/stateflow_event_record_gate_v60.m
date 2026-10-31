function y=stateflow_event_record_gate_v60(s,previous,stage)
%#codegen
% Runtime projection gate, not an independent proof of the host exact record.
assert(all(isfinite(s)),'Event record must be finite.');
assert(s(1)==stage && s(29)==1 && s(30)==0,'Event stage or scalar-memory authorization invalid.');
pairs=[2 4 6 8 10 12 14 16 18 22 31];
for n=1:numel(pairs)
    j=pairs(n);assert(s(j)>=0 && s(j)<=s(j+1),'Event interval order/positivity invalid.');
end
assert(s(20)>=0&&s(21)>0&&s(22)>0&&s(23)<s(21),'Event time bounds invalid.');
assert(all(s(24:28)==0|s(24:28)==1)&&sum(s(24:28))>=1,'Event equivalent limiter mask invalid.');
% Conservatively expand every computed bound. Binary64 arithmetic condition is explicit.
srcLo=s(12)+s(14)-s(11);srcHi=s(13)+s(15)-s(10);
budget=16*eps(max([1;s(10:19)]));
assert(srcLo<=budget&&srcHi>=-budget,'Event source/compressor closure invalid.');
lawLo=s(20)+s(10)-s(3)-s(17)-s(19);lawHi=s(20)+s(11)-s(2)-s(16)-s(18);
budget=32*eps(max([1;s(2:3);s(10:20)]));
assert(lawLo<=budget&&lawHi>=-budget,'Event first law invalid.');
if stage==0
    assert(s(2)==s(20)&&s(3)==s(20)&&all(s(4:5)==0)&&all(s(8:19)==0),'Event initial record invalid.');
else
    assert(all(s(20:32)==previous(20:32)),'Event correlation identifier changed.');
    assert(s(6)>=previous(6)&&s(7)>=previous(7),'Event HP age moved backwards.');
    if stage==1
        assert(previous(1)==0&&all(s(2:3)==s(31:32))&&all(s(4:5)==s(22:23))&&all(s(8:9)==s(22:23)), ...
            'Event exact manifold handoff invalid.');
    else
        assert(stage==2&&previous(1)==1&&all(s(4:5)==s(21))&&s(2)>s(32), ...
            'Event outgoing side/clock invalid.');
        postLo=s(21)-s(23);postHi=s(21)-s(22);
        assert(s(8)<=postLo&&s(9)>=postHi,'Event shared-theta duration invalid.');
    end
end
y=s;
end
