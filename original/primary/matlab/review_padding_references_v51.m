function review_padding_references_v51(folder)
% Reopen original fixture MATs; compare shared physical outputs to v30.
% v30 records an attempted HP request even when unavailable; OFF latch uses 0.
fixtures=jsondecode(fileread(fullfile(folder,'fixtures_v51.json')));
checks=jsondecode(fileread(fullfile(folder,'repair_assertions_v51.json')));
shared=[1:21 23:25];reviews=[];
for j=1:numel(fixtures)
    f=fixtures(j);s=load(fullfile(folder,[f.id '_fixture_simulation.mat']));
    actual=reshape(s.result.dispatch_trace_v51.Data,25,[])';
    reference=reshape(f.reference,1,[]);delta=actual(:,shared)-reference(:,shared);delta(isnan(delta))=0;
    ok=isequal(isnan(actual(:,shared)),isnan(reference(:,shared)))&&max(abs(delta),[],'all')<1e-9;
    id=[f.id '_independent_MATLAB_reference'];index=find(strcmp({checks.name},id));assert(numel(index)==1);
    checks(index).passed=ok;
    item=struct('id',f.id,'shared_columns',shared,'passed',ok,'max_physical_delta',max(abs(delta),[],'all'), ...
        'actual_request_MW',actual(22),'reference_attempted_request_MW',reference(22));
    if isempty(reviews),reviews=item;else,reviews(end+1)=item;end %#ok<AGROW>
end
r=struct('reviews',reviews,'corrected_assertions',checks,'passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'exclusion_reason','Column22 is attempted request versus latch-authorized request; every physical energy/flow/mode column remains compared.');
path=fullfile(folder,'reference_review_v51.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(r,PrettyPrint=true));fprintf('REFERENCE_REVIEW_V51 pass=%d fail=%d\n',r.passed,r.failed);
assert(r.failed==0);
end
