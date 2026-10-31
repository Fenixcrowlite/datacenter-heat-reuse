function packed=stateflow_collect_v32(previous,z,index)
%#codegen
% Two calls per macro sample: preserve separate executed segment outputs.
assert(index==1 || index==2,'Unexpected segment iteration.');
packed=previous;
if index==1,packed=zeros(50,1);end
if index==1,packed(1:25)=z;else,packed(26:50)=z;end
end
