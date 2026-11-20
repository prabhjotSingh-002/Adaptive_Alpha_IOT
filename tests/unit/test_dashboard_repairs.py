import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'host'))
from evidence import verify_artifacts, policy_qualification

class EvidenceRepairs(unittest.TestCase):
    def test_traversal_and_binary_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'binary').write_bytes(b'changed')
            m = {'artifact_hashes': {'../secret': 'x'}, 'binary_hashes': {'binary': 'wrong'}}
            self.assertEqual(verify_artifacts(root,m), {'../secret':'UNSAFE_PATH','binary':'MISMATCH'})
    def test_stationary_qualified_is_not_fallback(self):
        m={'mode':'P1','config':{'policy_calibration_status':'qualified'}}
        self.assertEqual(policy_qualification(m, {'policy':{'total_switches':0}}),'qualified cost-aware')
        m['config']={}
        self.assertIn('fallback',policy_qualification(m,{}))
    def test_real_routes_and_switch_field(self):
        from flask import Flask
        import campaign_dashboard as module
        app=Flask(__name__);module.register_campaign(app)
        rows=[{'manifest':{'run_id':'actual','mode':'P1','status':'passed','config':{'policy_calibration_status':'qualified'}},'summary':{'policy':{'total_switches':2}},'group':'g','mode':'P1','seed':1,'directory':str(module.ROOT/'results/fixture')}]
        with patch.object(module,'_current_campaign_dir',return_value=Path('/unused')), patch.object(module,'campaign_rows',return_value=({}, {}, rows)):
            response=app.test_client().get('/api/campaign-runs')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['runs'][0]['switches'],2)
        self.assertEqual(response.json['runs'][0]['qualification'],'qualified cost-aware')

class CampaignAdmissionRepairs(unittest.TestCase):
    def test_changed_raw_evidence_blocks_selected_run(self):
        import campaign
        from campaign import atomic_json,sha
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'results/run';d.mkdir(parents=True);camp=root/'campaign';camp.mkdir()
            config={'seed':1}
            files=('summary.json','events.jsonl','generated-conf.h','scenario.csc','COOJA.testlog','binary')
            for name in files:(d/name).write_text('{}')
            hashes={name:sha(d/name) for name in files if name!='binary'}
            manifest={'schema_version':2,'mode':'B1','status':'passed','config':config,
                      'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
                      'scenario_sha256':sha(d/'scenario.csc'),'artifact_hashes':hashes,'binary_hashes':{'binary':sha(d/'binary')}}
            atomic_json(d/'manifest.json',manifest);atomic_json(camp/'protocol.json',{})
            atomic_json(camp/'state.json',{'protocol_sha256':sha(camp/'protocol.json'),'attempts':[{'selected':True,'directory':'results/run','mode':'B1','seed':1,'group':'g','manifest_sha256':sha(d/'manifest.json'),'summary_sha256':sha(d/'summary.json')}]})
            with patch.object(campaign,'ROOT',root):
                self.assertEqual(len(campaign.campaign_rows(camp)[2]),1)
                (d/'events.jsonl').write_text('changed')
                with self.assertRaisesRegex(ValueError,'changed run evidence'):
                    campaign.campaign_rows(camp)
