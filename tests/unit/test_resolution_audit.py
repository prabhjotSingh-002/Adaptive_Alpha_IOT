"""Integrity regression checks; fixtures are not simulation evidence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'host'))
import audit_resolution


class AuditTests(unittest.TestCase):
    def test_tampering_and_escape_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / 'results/run'
            run.mkdir(parents=True)
            log = run / 'raw.log'
            log.write_bytes(b'original')
            manifest = {'artifact_hashes': {'raw.log': hashlib.sha256(b'original').hexdigest()}}
            (run / 'manifest.json').write_text(json.dumps(manifest))
            with patch.object(audit_resolution, 'ROOT', root):
                self.assertEqual(audit_resolution.inspect_run(run)['errors'], [])
                log.write_bytes(b'tampered')
                self.assertIn('hash mismatch', audit_resolution.inspect_run(run)['errors'][0])
                manifest['artifact_hashes'] = {'../../outside': '0' * 64}
                (run / 'manifest.json').write_text(json.dumps(manifest))
                self.assertTrue(audit_resolution.inspect_run(run)['errors'])
