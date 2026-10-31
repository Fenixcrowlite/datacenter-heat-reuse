function run_dispatch_crosscheck_v18()
% Independent Python reference compared to existing MATLAB v16 kernel.
root = fileparts(fileparts(mfilename('fullpath')));
reference = fullfile(root,'audit','dispatch_reference_vectors_v18.csv');
output = fullfile(root,'results','dispatch_contract_v18_20261009');
run_dispatch_contract_v16(reference,output);
end
