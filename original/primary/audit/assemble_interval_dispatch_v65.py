"""Additive assembly: retain the v64 equations and their named provenance."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    target=ROOT/'matlab/simulink/interval_dispatch_kernel_v65.m'
    prefix='''function y=interval_dispatch_kernel_v65(u,cfg,old)
%#codegen
assert(all(isfinite(u))&&all(isfinite(cfg)),'v65 finite domain');
p=cfg(36:60);assert(old(180)==0||old(180)==65,'v65 memory schema');
if old(180)>0,assert(all(old(181:205)==p),'v65 immutable policy');end
if u(1)==0
    assert(old(179)==0,'v65 prefix cannot resume after service');
    assert(p(1)==cfg(5)&&p(2)==cfg(6)&&p(3)==cfg(19)&&p(5)==cfg(35)&& ...
        p(6)==cfg(4)&&p(7)==cfg(3)&&p(9)==cfg(18)&&p(11)==cfg(16)&& ...
        all(p(12:18)==cfg([11 12 13 14 15 9 10]))&&p(19)==cfg(7)&&p(20)==cfg(8)&& ...
        p(21)==cfg(20)&&p(23)==cfg(34),'v65 prefix equipment mismatch');
    step=[u(2);u(3);u(4)];
    legacy=retained_restart_v64(step,cfg(1:35),old(1:114),u(2));
    y=old;y(1:114)=legacy;y(115)=0;
    if legacy(55)==1&&u(2)>0,y(115)=2;end
    y(174:175)=cfg(1);y(176:177)=legacy(35:36);y(178)=1;y(180)=65;y(181:205)=p;
else
    y=interval_service_core_v65(u,p,old);
end
end
'''
    core=(ROOT/'matlab/simulink/interval_service_core_v65.m').read_text()
    inherited=(ROOT/'matlab/simulink/restart_chain_kernel_v64.m').read_text().replace(
        'function y=restart_chain_kernel_v64','function y=retained_restart_v64',1)
    target.write_text(prefix+core+inherited)
    print(target.relative_to(ROOT))
if __name__=='__main__':main()
