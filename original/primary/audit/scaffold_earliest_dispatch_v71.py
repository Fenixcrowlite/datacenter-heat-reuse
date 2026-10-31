"""Additive development scaffold; never writes any baseline file."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'matlab/simulink/event_candidates_v70.m').read_text()
root=src[src.index('function z=certify_event_root_v70'):].replace('certify_event_root_v70','certify_event_root_v71')
target=ROOT/'matlab/simulink/certify_event_root_v71.m'
assert not target.exists();target.write_text(root)
src=(ROOT/'matlab/simulink/build_event_candidates_v70.m').read_text()
src=src.replace('build_event_candidates_v70','build_earliest_dispatch_v71').replace('DCHR_Event_Candidates_Stateflow_v70r2','DCHR_Earliest_Dispatch_Stateflow_v71')
src=src.replace("'[60 1]'","'[25 1]'").replace("'[283 1]'","'[1380 1]'").replace("'[205 1]'","'[1380 1]'").replace('zeros(205,1)','zeros(1380,1)')
src=src.replace('interval_dispatch_kernel_v70','earliest_dispatch_kernel_v71').replace('event_candidates_v70','certify_event_root_v71')
src=src.replace('interval_mode_v66','earliest_mode_v71').replace('mode=y(115)','mode=y(1)').replace('core(115)','core(1)')
src=src.replace('trace=[core;certify_event_root_v71(horizon_input,policy_input,core)];','trace=core;')
src=src.replace('v70 mode-conditioned prospective event candidates in SAME six-mode sampled v66 chart. Observer does not switch at roots or reset inventory. Embedded plant schema remains v66.',
    'v71 SAME six-mode chart executes analytic earliest-event segments. Root hulls, symbolic thresholds, port offsets and physical clock survive each segment. No root midpoint. Macro solver ticks are protocol calls, not physical event times.')
target=ROOT/'matlab/simulink/build_earliest_dispatch_v71.m';assert not target.exists();target.write_text(src)
