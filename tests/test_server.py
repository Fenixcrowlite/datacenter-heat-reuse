import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError

from heat_reuse.server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.server=make_server('127.0.0.1',0,Path(self.temp.name))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()

    def get(self,path):
        with urlopen(self.url+path) as r:return json.load(r)

    def run_model(self,body):
        request=Request(self.url+'/api/run',json.dumps(body).encode(),{'Content-Type':'application/json'})
        with urlopen(request) as r:return json.load(r)

    def test_real_calculation_persistence_and_export(self):
        self.assertTrue({'annual-v2','pool-v04','stateflow-v85'}<={m['id'] for m in self.get('/api/models')['models']})
        result=self.run_model({'model_id':'pool-v04','steps':32,'config':{'pool_enabled':False}})
        self.assertEqual('PYTHON_COMPUTED',result['source_kind'])
        self.assertEqual(0,result['metrics']['pool_heat_MWh'])
        self.assertEqual(result['id'],self.get('/api/results')[0]['id'])
        loaded=self.get('/api/results/'+result['id'])
        self.assertEqual(result['rows'],loaded['rows'])
        with urlopen(self.url+'/api/results/'+result['id']+'.csv') as r:
            self.assertIn('T_bazen_C',r.read().decode())
        self.assertTrue((Path(self.temp.name)/(result['id']+'.json')).exists())

    def test_untrusted_host_rejected_before_read_or_calculation(self):
        port=self.server.server_port
        for host in ('evil.example:'+str(port),
                     'localhost.evil.example:'+str(port),
                     '127.0.0.1.evil.example:'+str(port),
                     'localhost:'+str(port+1)):
            with self.subTest(host=host):
                req=Request(self.url+'/api/models',headers={'Host':host})
                with self.assertRaises(HTTPError) as error:
                    urlopen(req)
                self.assertEqual(error.exception.code,403)
                error.exception.close()
                body=json.dumps({'model_id':'annual-v2','steps':1}).encode()
                req=Request(self.url+'/api/run',body,headers={
                    'Host':host,'Origin':'http://'+host,
                    'Content-Type':'application/json'})
                with self.assertRaises(HTTPError) as error:
                    urlopen(req)
                self.assertEqual(error.exception.code,403)
                error.exception.close()
        self.assertEqual([],self.get('/api/results'))

    def test_localhost_host_and_matching_origin_work(self):
        port=self.server.server_port
        req=Request(self.url+'/api/models',headers={'Host':'localhost:'+str(port)})
        with urlopen(req) as response:
            self.assertIn('models',json.load(response))
        req=Request(self.url+'/api/run',
                    json.dumps({'model_id':'annual-v2','steps':1}).encode(),
                    headers={'Host':'localhost:'+str(port),
                             'Origin':'http://localhost:'+str(port),
                             'Content-Type':'application/json'})
        with urlopen(req) as response:
            self.assertEqual('PYTHON_COMPUTED',json.load(response)['source_kind'])

    def test_invalid_requests_cannot_replace_saved_result(self):
        good=self.run_model({'model_id':'annual-v2','steps':4})
        for body in ({'model_id':'not-real'},{'model_id':'annual-v2','steps':True},
                     {'model_id':'pool-v04','config':{'initial_temperature_C':float('nan')}},
                     {'model_id':'annual-v2','path':'C:/anything'}):
            with self.subTest(body=body),self.assertRaises(HTTPError) as error:self.run_model(body)
            self.assertEqual(400,error.exception.code)
            error.exception.close()
        self.assertEqual(good['id'],self.get('/api/results')[0]['id'])
        with self.assertRaises(HTTPError) as error:urlopen(self.url+'/files/../../.git/config')
        error.exception.close()


if __name__=='__main__':unittest.main()
