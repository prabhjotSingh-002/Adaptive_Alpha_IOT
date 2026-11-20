"""Latest dashboard acceptance; synthetic integrity fixtures stay in /tmp."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'host'))
import latest_results as results
from latest_dashboard import register_latest
from campaign_dashboard import register_campaign
from flask import Flask

class LatestDashboardTests(unittest.TestCase):
    def app(self):
        app=Flask(__name__);register_campaign(app);register_latest(app);return app
    def test_actual_snapshot_keeps_p1_purposes_separate(self):
        data=results.load_latest()
        self.assertEqual(data['verified_runs'],16);self.assertEqual(data['artifact_binary_checks'],190)
        rows={r['name']:r for r in data['runs']}
        functional=rows['p1-qualified-functional'];finite=rows['p1-qualified-finite']
        self.assertEqual(functional['category'],'functional');self.assertEqual(finite['category'],'finite-budget')
        self.assertEqual(functional['summary']['energy_per_delivered_reading_nj'],246375438)
        self.assertEqual(finite['summary']['unique_authenticated_delivered'],20)
        self.assertEqual(finite['summary']['lifetime']['scheduled_readings'],48)
    def test_main_page_archive_and_downloads(self):
        c=self.app().test_client();r=c.get('/')
        self.assertEqual(r.status_code,200)
        for label in ('Latest P1 measurements','246.38','410.06','energy-chart','p1-qualified-functional','p1-qualified-finite'):
            self.assertIn(label,r.get_data(as_text=True))
        data=c.get('/api/latest').json;record=next(r for r in data['runs'] if r['name']=='p1-qualified-functional')
        artifact=c.get('/api/latest/artifact',query_string={'run':record['directory'],'name':'summary.json'})
        self.assertEqual(artifact.status_code,200);self.assertEqual(json.loads(artifact.data)['generated'],48)
        self.assertEqual(c.get('/api/latest/artifact',query_string={'run':record['directory'],'name':'../../etc/passwd'}).status_code,404)
        archive=c.get('/api/historical').json
        ids={r['run_id'] for r in archive['records']}
        self.assertIn('20261117T024032053990Z-P1-2',ids)
        self.assertIn('20261117T021307655729Z-B6-2',ids)
        self.assertEqual(c.get('/campaign').status_code,200)
        self.assertIn('attachment',c.get('/api/latest/export').headers['Content-Disposition'])
    def fixture(self,root):
        run=root/'results'/'<img src=x onerror=alert(1)>';run.mkdir(parents=True)
        cfg={'target':'z1','seed':1,'modes':{'P1':1},'profile':1,'warmup_ms':0,'period_ms':1000,'readings_per_sensor':1,'deadline_ms':0,'drain_ms':0}
        summary={'generated':1,'unique_authenticated_delivered':1,'energy_per_delivered_reading_nj':1000000,'packets_submitted':1,'reading_pdr':1,'p95_delay_ms':1,'lifetime':None,
                 'policy':{'caps_used':[1],'total_switches':0,'fallback_actions':0},'mechanism_checks':{'policy_wire':{'tx_profiles':[1],'wire_profile_changes':0}}}
        files={'summary.json':json.dumps(summary),'events.jsonl':'','generated-conf.h':'fixture','scenario.csc':'fixture','COOJA.testlog':'fixture','binary':'fixture'}
        for name,text in files.items():(run/name).write_text(text)
        m={'status':'passed','schema_version':2,'clients':2,'run_id':run.name,'mode':'P1','config':cfg,
           'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),'scenario_sha256':results.sha(run/'scenario.csc'),
           'source_hashes':{'host/fixture.py':'fixture'},'artifact_hashes':{n:results.sha(run/n) for n in files if n!='binary'},'binary_hashes':{'binary':results.sha(run/'binary')}}
        (run/'manifest.json').write_text(json.dumps(m))
        validation=root/'results/validation';validation.mkdir();frozen={'host/fixture.py':'fixture'}
        (validation/'frozen-sources.json').write_text(json.dumps(frozen));(validation/'protocol.json').write_text(json.dumps({'source_sha256':hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()}));(validation/'status.json').write_text(json.dumps({'runs':1}))
        catalog={'schema_version':1,'title':'fixture','validation_directory':'results/validation','references':{},'limitations':['fixture only'],
                 'records':[{'name':'p1-qualified-functional','directory':str(run.relative_to(root)),'manifest_sha256':results.sha(run/'manifest.json'),'summary_sha256':results.sha(run/'summary.json')}]}
        dashboard=root/'results/dashboard';dashboard.mkdir();(dashboard/'catalog.json').write_text(json.dumps(catalog));(dashboard/'current.json').write_text(json.dumps({'catalog':'results/dashboard/catalog.json','catalog_sha256':results.sha(dashboard/'catalog.json')}))
        return run
    def test_tampered_artifact_withholds_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=self.fixture(root)
            with patch.object(results,'ROOT',root):
                c=self.app().test_client();self.assertEqual(c.get('/api/latest').status_code,200)
                (run/'events.jsonl').write_text('tampered')
                self.assertEqual(c.get('/api/latest').status_code,409)
                page=c.get('/');self.assertEqual(page.status_code,503)
                self.assertNotIn('Latest P1 measurements',page.get_data(as_text=True))
    def test_html_like_run_identity_is_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            with patch.object(results,'ROOT',root):
                r=self.app().test_client().get('/');self.assertEqual(r.status_code,200)
                self.assertNotIn('<img src=x',r.get_data(as_text=True))
                self.assertIn('&lt;img',r.get_data(as_text=True))
    def test_launcher_rejects_invalid_port_before_docker(self):
        run=subprocess.run([sys.executable,str(results.ROOT/'host/run_dashboard.py'),'--port','0'],capture_output=True,text=True)
        self.assertEqual(run.returncode,2);self.assertIn('port must be',run.stderr)
