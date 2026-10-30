import csv
import gzip
import math
from pathlib import Path
import unittest

from heat_reuse.pool import run_pool, generate_inputs

DATA = Path(__file__).resolve().parents[1] / 'datasets/reference/pool_v04'


class PoolTests(unittest.TestCase):
    def test_all_eight_original_simulink_scenarios(self):
        for file in sorted(DATA.glob('*.csv.gz')):
            with self.subTest(file=file.name):
                with gzip.open(file, 'rt', encoding='utf-8-sig', newline='') as f:
                    expected = [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
                scenario = file.name[len('scenar_'):-len('_SK.csv.gz')]
                # The MATLAB CSV rounds inputs to 15 significant digits. Regenerate
                # the original full-precision inputs: tiny quantization residues
                # can legitimately change an exact-zero auxiliary-pump branch.
                result = run_pool(generate_inputs(scenario),scenario=scenario)
                self.assertEqual(672,len(result['rows']))
                for i,(a,e) in enumerate(zip(result['rows'],expected)):
                    for key,value in e.items():
                        self.assertLessEqual(abs(a[key]-value),1e-5,(i,key,a[key],value))
                    self.assertEqual(e['rezim_Stateflow'],a['rezim_Stateflow'])
                self.assertLess(result['validation']['max_water_residual_W'],1e-5)

    def test_fresh_simulation_not_replay_and_pool_disable(self):
        inputs=generate_inputs('zaklad',48)
        actual=run_pool(inputs)
        off=run_pool(inputs,{'pool_enabled':False})
        self.assertGreater(actual['metrics']['pool_heat_MWh'],0)
        self.assertEqual(0,off['metrics']['pool_heat_MWh'])
        self.assertLess(off['rows'][-1]['T_bazen_C'],actual['rows'][-1]['T_bazen_C'])
        for row in inputs:row['T_bazen_C']=-12345
        again=run_pool(inputs)
        self.assertEqual(actual['rows'],again['rows'])

    def test_invalid_inputs_refused(self):
        for settings in ({'pool_limit_kw':-1},{'initial_temperature_C':math.inf},{'unknown':1}):
            with self.subTest(settings=settings),self.assertRaises(ValueError):
                run_pool(generate_inputs('zaklad',2),settings)
        inputs=generate_inputs('zaklad',2);inputs[0]['Qdc_available_W']=math.nan
        with self.assertRaises(ValueError):run_pool(inputs)


if __name__=='__main__':unittest.main()
