import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host'))
from calibration_contract import validate_table, context

class CalibrationContractTests(unittest.TestCase):
    def test_legacy_table_cannot_claim_qualification(self):
        with self.assertRaisesRegex(ValueError,'schema/coverage'):
            validate_table({'p1_cost_nj':[[1,0,1],[1,0,1]]},{'seed':123456},2)
    def test_client_and_resolved_cli_mismatch(self):
        cfg={'seed':123456,'target':'z1','period_ms':1000}
        table={'schema_version':1,'qualification':'qualified','source_seed_filter':223457,'context':context(cfg,2)}
        with self.assertRaisesRegex(ValueError,'runtime context'):
            validate_table(table,cfg,8)
        changed=dict(cfg,period_ms=2000)
        with self.assertRaisesRegex(ValueError,'runtime context'):
            validate_table(table,changed,2)
    def test_calibration_evaluation_overlap(self):
        with self.assertRaisesRegex(ValueError,'seed overlap'):
            validate_table({'schema_version':1,'qualification':'qualified','source_seed_filter':223457},{'seed':223457},2)

class CalibrationEligibilityTests(unittest.TestCase):
    def _fixture(self, root, profile, cap, cost=100):
        import json, hashlib
        d=root/'results'/f'p{profile}c{cap}';d.mkdir(parents=True)
        cfg={'target':'z1','backend':'ref','seed':223457,'purpose':'calibration','mode':'B1' if profile==1 else 'B2',
             'profile':profile,'calibration_cap':cap,'modes':{'B1':1,'B2':1},'power_model':{'id':1},'lifetime':False}
        files={'summary.json':json.dumps({'energy_per_delivered_reading_nj':cost,'reading_pdr':1.0,'p95_delay_ms':100,'unique_authenticated_delivered':1}),
               'events.jsonl':json.dumps({'event_type':'TX','profile':profile,'count':min(cap,3)})+'\n',
               'COOJA.testlog':'fixture only','generated-conf.h':'fixture','scenario.csc':'fixture','binary':'fixture'}
        for name,data in files.items():(d/name).write_text(data)
        hashes={name:hashlib.sha256((d/name).read_bytes()).hexdigest() for name in files}
        binary={'binary':hashes.pop('binary')}
        m={'status':'passed','run_id':d.name,'mode':cfg['mode'],'config':cfg,'clients':2,'effective_cap':cap,'energy_reconciliation':True,
           'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),'scenario_sha256':hashes['scenario.csc'],
           'source_hashes':{'source':'fixture'},'dependency_hashes':{},'pins':{},'artifact_hashes':hashes,'binary_hashes':binary}
        (d/'manifest.json').write_text(json.dumps(m));return d
    def test_six_measured_cells_and_actual_distribution(self):
        import tempfile
        from unittest.mock import patch
        import calibration_contract as module
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);paths=[self._fixture(root,p,c) for p in (1,2) for c in (1,2,4)]
            with patch.object(module,'ROOT',root):table=module.build_table(paths,223457)
            self.assertEqual(table['qualification'],'qualified')
            self.assertEqual(table['p1_cost_nj'],[[100,100,100],[100,100,100]])
            self.assertEqual(table['source_records'][2]['actual_batch_distribution'],{'3':1})
    def test_nonfinite_cost_cannot_qualify(self):
        import tempfile
        from unittest.mock import patch
        import calibration_contract as module
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=self._fixture(root,1,1,float('nan'))
            with patch.object(module,'ROOT',root):table=module.build_table([p],223457)
            self.assertEqual(table['qualification'],'incomplete')
            self.assertIn('nonfinite',table['rejected_records'][0]['reason'])
