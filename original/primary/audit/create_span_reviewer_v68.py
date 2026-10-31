"""Reuse unchanged exact exp/log plant QA; add a separately derived tail proof."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'audit/verify_event_brackets_v67.py').read_text()
s=s.replace('event_brackets_v67.mat','span_repair_v68.mat').replace('DCHR_Event_Brackets_Stateflow_v67r2','DCHR_Span_Repair_Stateflow_v68')
s=s.replace("'interval_dispatch_kernel_v66.m','event_observer_v67.m'", "'interval_dispatch_kernel_v68.m','event_observer_v68.m'")
s=s.replace("version='0.67'", "version='0.68'").replace('root_traces_v67_','root_traces_v68_').replace('independent_QA_v67_','independent_QA_v68_')
s=s.replace('from verify_interval_dispatch_v66 import analyze, storage', 'from verify_interval_dispatch_v66 import analyze, storage\nfrom span_tail_review_v68 import additional_review')
s=s.replace("check('coverage','six_modes'", "additional_review(folder, report, check)\n    check('coverage','six_modes'")
with (ROOT/'audit/verify_span_repair_v68.py').open('x',encoding='utf-8') as f:f.write(s)
print('Created versioned independent reviewer')
