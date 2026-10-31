function packed=stateflow_collect_v40(previous,z,index)
%#codegen
% Bounded event slots; zero-span padding contributes neither energy nor time.
assert(index>=1 && index<=64,'Unexpected segment iteration.');
packed=previous;
if index==1,packed=zeros(1792,1);end
packed((double(index)-1)*28+(1:28))=z;
end
