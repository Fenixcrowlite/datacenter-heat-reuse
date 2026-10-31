function packed=stateflow_collect_v34(previous,z,index)
%#codegen
% Two calls per macro sample: preserve separate executed segment outputs.
assert(index>=1 && index<=64,'Unexpected segment iteration.');
packed=previous;
if index==1,packed=zeros(1792,1);end
packed((index-1)*28+(1:28))=z;
end
