from pathlib import Path
import tempfile
import unittest
import zipfile

from heat_reuse.catalog import extract_model

ROOT=Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_saved_v85_graph_and_provenance(self):
        model=ROOT/'original/primary/matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx'
        result=extract_model(model)
        self.assertEqual('2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7',result['sha256'])
        states={s['label'].split('\n')[0].split('/')[0].strip() for s in result['states']}
        self.assertTrue({'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'}<=states,states)
        self.assertGreater(len(result['functions']),0)
        self.assertGreater(len(result['transitions']),0)
        self.assertEqual('not_ported',result['execution_status'])

    def test_no_code_executed_during_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/'sample.slx'
            with zipfile.ZipFile(model,'w') as z:
                z.writestr('simulink/stateflow/chart_1.xml','<Stateflow><chart><eml><P Name="script">function y=f(x)\ny=x+1;\nend</P></eml></chart></Stateflow>')
            result=extract_model(model)
            self.assertIn('x+1',result['functions'][0]['source'])
            self.assertEqual('not_ported',result['execution_status'])


if __name__=='__main__':unittest.main()
