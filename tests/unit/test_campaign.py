import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'host'))
from campaign import atomic_json, campaign_rows, sha
from comparison_guard import admit_group


class CampaignTests(unittest.TestCase):
    def test_protocol_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            atomic_json(d/'protocol.json', {'id':'fixture'})
            atomic_json(d/'state.json', {'protocol_sha256':sha(d/'protocol.json'),'attempts':[]})
            self.assertEqual(campaign_rows(d)[2], [])
            atomic_json(d/'protocol.json', {'id':'changed'})
            with self.assertRaisesRegex(ValueError,'protocol changed'):
                campaign_rows(d)

    def test_topologies_must_not_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs=[]
            for i,topology in enumerate(('grid16','tree16')):
                d=Path(tmp)/str(i);d.mkdir();dirs.append(d)
                atomic_json(d/'manifest.json', {'status':'passed','clients':15,'mode':'B1',
                            'config':{'purpose':'functional','seed':i,'topology':topology}})
                atomic_json(d/'summary.json', {})
            with self.assertRaisesRegex(ValueError,'Mixed comparison'):
                admit_group(dirs)

    def test_duplicate_seeds_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs=[]
            for i in range(2):
                d=Path(tmp)/str(i);d.mkdir();dirs.append(d)
                atomic_json(d/'manifest.json', {'status':'passed','clients':8,'mode':'B1',
                            'config':{'purpose':'functional','seed':42}})
                atomic_json(d/'summary.json', {})
            with self.assertRaisesRegex(ValueError,'duplicate'):
                admit_group(dirs)


if __name__=='__main__':
    unittest.main()
