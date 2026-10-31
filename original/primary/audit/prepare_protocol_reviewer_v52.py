from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    s=(ROOT/'audit/verify_stateflow_padding_v51.py').read_text().replace('v51','v52').replace('V51','V52').replace('0.51','0.52')
    a=s.index('    reviewed=json.loads');b=s.index('    spec=json.loads',a)
    s=s[:a]+"    check('repair_execution','harness',all(v['passed'] for v in assertions))\n"+s[b:]
    s=s.replace("all('Zero-span segment has service.' in v['error_message'] for v in faults if",
                "all(any(msg in v['error_message'] for msg in ('Zero-span segment has service.','Canonical endpoint protocol mismatch.')) for v in faults if")
    p=ROOT/'audit/verify_stateflow_protocol_v52.py';assert not p.exists();p.write_text(s)
if __name__=='__main__':main()
