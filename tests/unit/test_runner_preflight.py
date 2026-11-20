"""Actual CLI resolution checks; never build firmware or produce run results."""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ResolvedPreflightTests(unittest.TestCase):
    def test_static_and_adaptive_z1_flush_contract_matches(self):
        config=ROOT/'firmware/generated-conf.h';before=hashlib.sha256(config.read_bytes()).hexdigest()
        contexts=[]
        for phase,mode in ((4,'B1'),(5,'P1')):
            cmd=[sys.executable,'-B',str(ROOT/'host/run_experiment.py'),'--phase',str(phase),'--mode',mode,'--clients','2','--target','z1','--power-model','--preflight-only']
            run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads(run.stdout)
            self.assertFalse(data['build_executed']);self.assertFalse(data['simulation_executed'])
            contexts.append(data['context'])
        self.assertEqual(contexts[0],contexts[1])
        self.assertEqual(contexts[0]['flush_lead_ms'],125)
        self.assertEqual(before,hashlib.sha256(config.read_bytes()).hexdigest())
