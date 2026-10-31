function run_hp_boundary_v44(folder)
% New electrical/thermal-boundary audit, not production model calibration.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
out=fullfile(root,folder); spec=jsondecode(fileread(fullfile(out,'spec.json')));
v=spec.vectors; n=size(v,1); matrix=zeros(n,16); passed=0;
for k=1:n
    L=v(k,1)+273.15; lift=v(k,2); H=L+lift; eta=v(k,3); qL=v(k,4);
    eer=eta*L/lift; wc=qL/eer; wa=v(k,5)*wc; alpha=v(k,6);
    qH=qL+wc+alpha*wa; total=wc+wa;
    cooling=qL/total; heating=qH/total; gap=heating-cooling;
    target=(wc+alpha*wa)/total;
    assert(abs(qH-qL-wc-alpha*wa)<1e-10*max(1,qH)); passed=passed+1;
    assert(abs(gap-target)<1e-12*max(1,target)); passed=passed+1;
    assert(abs(target-(1-(1-alpha)*wa/total))<1e-12); passed=passed+1;
    assert(target>=alpha-1e-12 && target<=1+1e-12); passed=passed+1;
    assert(eer<=L/lift && eer>0 && H>L); passed=passed+1;
    if wa>0 && alpha<1
        assert(abs(gap-1)>1e-3); passed=passed+1;
    end
    matrix(k,:)=[v(k,:) eer wc wa qH total cooling heating gap target H/lift];
end
% Same lift, same eta, distinct absolute temperatures cannot give one EER.
eer1=.5*(5+273.15)/30; eer2=.5*(35+273.15)/30;
assert(abs((eer2-eer1)-.5)<1e-12); passed=passed+1;
assert(eer1~=eer2); passed=passed+1;
report=struct('matlab_version',version,'vector_count',n,'passed',passed,'failed',0,...
    'fixture_class',spec.fixture_class,'new_model',false,'matrix',matrix);
save(fullfile(out,'boundary_v44.mat'),'matrix','report','spec');
fid=fopen(fullfile(out,'boundary_v44.json'),'w'); clean=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(report)); clear clean;
fprintf('BOUNDARY_V44 vectors=%d passed=%d failed=0\n',n,passed);
end
