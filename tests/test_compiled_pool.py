import csv
import gzip
import json
from pathlib import Path
import unittest
from heat_reuse.matlab_subset import compile_functions,M
from heat_reuse.pool import generate_inputs,INPUTS,OUTPUTS,SCENARIOS

ROOT=Path(__file__).resolve().parents[1]


class CompiledPoolTests(unittest.TestCase):
    def test_python_numerical_evaluator_all_original_pool_functions_and_scenarios(self):
        model=json.loads(next((ROOT/'models/extracted').glob('dc-bazen-uzavreta-regulacia-v04-*.json')).read_text(encoding='utf-8'))
        functions={}
        for source in model['functions']:functions.update(compile_functions(source['source']))
        request=functions['vypocitaj_dopyt_bazena_sk'];mode=functions['volba_rezimu_v04_sk'];allocate=functions['alokuj_teplo_v04_sk']
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                file=ROOT/'datasets/reference/pool_v04'/('scenar_'+scenario+'_SK.csv.gz')
                with gzip.open(file,'rt',encoding='utf-8-sig',newline='') as f:expected=list(csv.DictReader(f))
                temperature,energy,thermostat=16.,.45*3.6e9,1.
                for index,(row,golden) in enumerate(zip(generate_inputs(scenario),expected)):
                    u=M([row[key] for key in INPUTS],1,11)
                    req,loss,new_thermostat=request(temperature,thermostat,u)
                    state=mode(req,u,temperature,energy)
                    actual=allocate(temperature,energy,req,loss,state,u).flat()
                    for key,value in zip(OUTPUTS,actual):
                        self.assertLessEqual(abs(value-float(golden[key])),1e-5,(scenario,index,key))
                    temperature,energy=actual[:2];thermostat=new_thermostat


if __name__=='__main__':unittest.main()
