import gzip
import json
import math
from pathlib import Path
import unittest
from heat_reuse.matlab_subset import compile_model,M

ROOT=Path(__file__).resolve().parents[1]


class DispatchTests(unittest.TestCase):
    def test_v85_every_saved_case_retains_state_and_matches_full_trace(self):
        model=json.loads(next((ROOT/'models/extracted').glob('dchr-electrical-dispatch-stateflow-v85-*.json')).read_text(encoding='utf-8'))
        functions=compile_model(model)
        with gzip.open(ROOT/'datasets/reference/stateflow_v85.json.gz','rt',encoding='utf-8') as stream:
            fixture=json.load(stream)
        self.assertEqual(model['sha256'],fixture['model_sha256'])
        modes=set();comparisons=0
        for case in fixture['cases']:
            with self.subTest(case=case['id']):
                memory=M([0.]*1380,1380,1);raw_memory=M([0.]*27,27,1)
                for index,(inputs,expected) in enumerate(zip(case['inputs'],case['traces'])):
                    memory,certificate=functions['electrical_dispatch_v85'](M(inputs,12,1),M(case['policy'],27,1),memory,raw_memory)
                    raw_memory=M(case['policy'],27,1)
                    actual=memory.flat();self.assertEqual(1380,len(actual));modes.add(actual[0])
                    for column,(a,b) in enumerate(zip(actual,expected)):
                        self.assertTrue(math.isfinite(a),(case['id'],index,column))
                        self.assertLessEqual(abs(a-b),1e-12,(case['id'],index,column,a,b))
                        comparisons+=1
        self.assertEqual({0,1,2,3,4,5},modes)
        print('V85_TRACE_COMPARISONS',comparisons,flush=True)


if __name__=='__main__':unittest.main()
