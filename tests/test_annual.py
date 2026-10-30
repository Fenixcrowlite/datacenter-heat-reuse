import csv
import gzip
import math
from pathlib import Path
import unittest

from heat_reuse.annual import run_annual

DATA = Path(__file__).resolve().parents[1] / 'datasets/reference'


def read(name):
    with gzip.open(DATA / name, 'rt', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


class AnnualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = read('annual_inputs.csv.gz')

    def test_native_matlab_all_192720_values(self):
        actual = run_annual(self.inputs, 'Warm45_Storage100')
        expected = read('annual_warm45_native.csv.gz')
        self.assertEqual(8760, len(actual['rows']))
        for index, (a, e) in enumerate(zip(actual['rows'], expected)):
            self.assertEqual(e['Time'], a['Time'])
            for key, value in e.items():
                if key != 'Time':
                    self.assertLessEqual(abs(float(value)-a[key]), 2e-8, (index, key))
        self.assertEqual('PYTHON_COMPUTED', actual['source_kind'])
        self.assertLess(actual['validation']['max_storage_residual_MWh'], 1e-9)

    def test_second_revision_correct_oracle_and_all_five_summaries(self):
        actual = run_annual(self.inputs, 'Liquid35_LowTempDH')
        for index, (a, e) in enumerate(zip(actual['rows'], read('annual_liquid35_lowtemp.csv.gz'))):
            for key, value in e.items():
                if key != 'Time':
                    self.assertLessEqual(abs(float(value)-a[key]), 2e-8, (index, key))
        for scenario in read('annual_summary_v2.csv.gz'):
            result = run_annual(self.inputs, scenario['Scenario'])
            for native, python in [('GasHeat_MWh','gas_heat_MWh'),('HPElectric_MWh','hp_electric_MWh'),
                                   ('HeatDemand_MWh','heat_demand_MWh'),('ReusedHeat_MWh','reused_to_network_MWh'),
                                   ('UsefulExergy_MWh','exergy_delivered_MWh'),('OpexSaving_EUR','opex_saving_EUR')]:
                self.assertLessEqual(abs(float(scenario[native])-result['metrics'][python]), 2e-6, (scenario['Scenario'], native))

    def test_settings_change_calculation_and_invalid_input_refused(self):
        small = self.inputs[:48]
        a = run_annual(small, 'Warm45_Storage100')
        b = run_annual(small, 'Warm45_Storage100', {'hp_capacity_MW': 1.0})
        self.assertGreater(b['metrics']['gas_heat_MWh'], a['metrics']['gas_heat_MWh'])
        for overrides in ({'hp_capacity_MW': math.nan}, {'storage_capacity_MWh': -1}, {'unknown': 5}, {'dt_h': 0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_annual(small, 'Warm45_Storage100', overrides)
        with self.assertRaises(ValueError):
            run_annual([dict(small[0], IT_MW='nan')], 'Warm45_Storage100')


if __name__ == '__main__':
    unittest.main()
