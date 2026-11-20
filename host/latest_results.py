"""Verified, purpose-separated presentation of immutable measured results.

Presentation reads the recorded measurement source; it does not assert that a
historical calibration table is compatible with today's experiment source.
"""
import hashlib
import json
from pathlib import Path
from evidence import verify_artifacts

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {'summary.json','events.jsonl','generated-conf.h','scenario.csc','COOJA.testlog'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def result_path(relative):
    path=(ROOT/relative).resolve()
    if not path.is_relative_to((ROOT/'results').resolve()):
        raise ValueError('Evidence path outside results')
    return path


def category(config):
    if config.get('purpose')=='calibration': return 'calibration'
    if config.get('purpose')=='security': return 'security'
    if config.get('lifetime'): return 'finite-budget'
    return 'functional'


def build_catalog(validation_dir):
    directory=result_path(validation_dir)
    status=json.loads((directory/'status.json').read_text())
    attempts=json.loads((directory/'attempts.json').read_text())
    if status.get('status')!='passed' or len(attempts)!=status['runs']:
        raise ValueError('Validation snapshot not complete')
    if sha(directory/'protocol.json')!=status['protocol_sha256']:
        raise ValueError('Validation protocol changed')
    references={str((directory/name).relative_to(ROOT)):sha(directory/name) for name in
                ('status.json','protocol.json','attempts.json','frozen-sources.json','cost-table-v1.json','finite-budget-freeze.json')}
    records=[]
    for attempt in attempts:
        if attempt.get('status')!='passed' or attempt.get('exit_code')!=0 or len(attempt.get('manifests',[]))!=1:
            raise ValueError('Unaccepted validation attempt')
        manifest=result_path(attempt['manifests'][0]);run=manifest.parent
        if sha(manifest)!=attempt['manifest_sha256']: raise ValueError('Attempt manifest changed')
        records.append({'name':attempt['name'],'directory':str(run.relative_to(ROOT)),
                        'manifest_sha256':sha(manifest),'summary_sha256':sha(run/'summary.json')})
    catalog={'schema_version':1,'title':'Latest verified Z1 mechanisms','validation_directory':str(directory.relative_to(ROOT)),
             'references':references,'records':records,
             'limitations':['One evaluation seed; no confidence intervals or superiority claim.',
                            'Functional, finite-budget, security and calibration runs are separate purposes.',
                            'Energy is the declared Z1 component model, not a physical battery measurement.',
                            'P1 is cost-aware with measured traffic; residual-aware P1 ranking remains unvalidated.',
                            'Bottleneck service failure preceded death; cutoff is verified, causation is not.']}
    load_catalog(catalog)
    return catalog


def load_catalog(catalog):
    if catalog.get('schema_version')!=1: raise ValueError('Unsupported dashboard catalog')
    for relative,expected in catalog['references'].items():
        if sha(result_path(relative))!=expected: raise ValueError('Snapshot reference changed: '+relative)
    directory=result_path(catalog['validation_directory'])
    protocol=json.loads((directory/'protocol.json').read_text())
    frozen=json.loads((directory/'frozen-sources.json').read_text())
    if hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!=protocol['source_sha256']:
        raise ValueError('Frozen source identity changed')
    rows=[];verified_count=0;seen=set()
    for record in catalog['records']:
        run=result_path(record['directory'])
        if str(run) in seen: raise ValueError('Duplicate catalog run')
        seen.add(str(run))
        for name in ('manifest','summary'):
            if sha(run/(name+'.json'))!=record[name+'_sha256']: raise ValueError('Selected '+name+' changed')
        m=json.loads((run/'manifest.json').read_text());s=json.loads((run/'summary.json').read_text());c=m['config']
        if m.get('status')!='passed' or m.get('schema_version')!=2 or m.get('clients')!=2 or c.get('target')!='z1':
            raise ValueError('Unsupported/unaccepted latest run')
        if m['run_id']!=run.name or m['config_sha256']!=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest():
            raise ValueError('Run/config identity mismatch')
        if m['scenario_sha256']!=sha(run/'scenario.csc'): raise ValueError('Scenario changed')
        if not m.get('source_hashes') or any(frozen.get(k)!=v for k,v in m['source_hashes'].items() if k!='firmware/generated-conf.h'):
            raise ValueError('Mixed recorded measurement sources')
        if not REQUIRED.issubset(m.get('artifact_hashes',{})) or not m.get('binary_hashes'):
            raise ValueError('Incomplete evidence')
        check=verify_artifacts(run,m)
        if not check or any(value!='OK' for value in check.values()): raise ValueError('Artifact/binary verification failed')
        verified_count+=len(check)
        curve={};deaths=[]
        if c.get('lifetime'):
            for line in (run/'events.jsonl').read_text().splitlines():
                e=json.loads(line)
                if e['event_type']=='ENERGY_MODEL' and e['node_id']!=1:
                    curve.setdefault(str(e['node_id']),[]).append([e['sim_time_ms']/1000,e['remaining_nj']/1e9])
                if e['event_type']=='DEPLETED': deaths.append({'node':e['node_id'],'seconds':e['sim_time_ms']/1000})
        rows.append({'name':record['name'],'directory':record['directory'],'run_id':m['run_id'],
                     'category':category(c),'mode':m['mode'],'seed':c['seed'],'target':c['target'],'clients':m['clients'],
                     'profile':c['profile'],'configured_cap':c.get('calibration_cap',c['modes'][m['mode']]),
                     'calibration_status':c.get('policy_calibration_status'),'budget_nj':c.get('energy_budget_nj'),
                     'bounded_node':c.get('deplete_node',0),'summary':s,'energy_curve':curve,'deaths':deaths,
                     'horizon_seconds':(c['warmup_ms']+c['period_ms']*c['readings_per_sensor']+c['deadline_ms']+c['drain_ms'])/1000,
                     'manifest_sha256':record['manifest_sha256'],'config_sha256':m['config_sha256'],
                     'artifacts':['manifest.json',*sorted(m['artifact_hashes']),*sorted(m['binary_hashes'])],
                     'artifact_checks':len(check),'recorded_source_qualification':True})
    expected=json.loads((directory/'status.json').read_text())['runs']
    if len(rows)!=expected: raise ValueError('Snapshot count mismatch')
    return {'title':catalog['title'],'runs':rows,'verified_runs':len(rows),'artifact_binary_checks':verified_count,
            'evaluation_seeds':sorted({r['seed'] for r in rows if r['category']!='calibration'}),
            'calibration_seeds':sorted({r['seed'] for r in rows if r['category']=='calibration'}),
            'limitations':catalog['limitations'],'validation_directory':catalog['validation_directory'],
            'measurement_source':'verified recorded source snapshot; presentation code may be newer'}


def load_latest():
    pointer=ROOT/'results/dashboard/current.json'
    selection=json.loads(pointer.read_text());catalog_path=result_path(selection['catalog'])
    if sha(catalog_path)!=selection['catalog_sha256']: raise ValueError('Dashboard catalog changed')
    return load_catalog(json.loads(catalog_path.read_text()))
