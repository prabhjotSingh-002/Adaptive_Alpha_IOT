"""Versioned calibration eligibility and resolved-runtime compatibility."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from evidence import verify_artifacts

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('target','backend','topology','warmup_ms','period_ms','readings_per_sensor',
          'deadline_ms','drain_ms','payload_budget','reserved_bytes','power_model',
          'energy_sample_ms','aes_backend','flush_lead_ms','bottleneck',
          'radio_off_until_ms','cpu_work_iterations','queuebuf_count','dual_profile')
DEFAULTS = {'topology':'legacy','flush_lead_ms':0,'bottleneck':False,
            'radio_off_until_ms':0,'cpu_work_iterations':0}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def context(config, clients):
    return {'clients':clients, **{k:config.get(k,DEFAULTS.get(k)) for k in FIELDS}}

def sources():
    return {str(p.relative_to(ROOT)):sha(p) for folder in ('firmware','host')
            for p in sorted((ROOT/folder).rglob('*')) if p.is_file()
            and 'build' not in p.parts and p.name != 'generated-conf.h'
            and (p.suffix in ('.c','.h','.py','.mk') or p.name=='Makefile')}

def build_table(paths, seed, min_pdr=0.95, max_p95=5000):
    accepted=[]; rejected=[]; cells={}; cohort=None; source_set=None; deps=None; pins=None
    for value in paths:
        d=Path(value).resolve()
        try:
            if not d.is_relative_to((ROOT/'results').resolve()): raise ValueError('outside results')
            m=json.loads((d/'manifest.json').read_text());s=json.loads((d/'summary.json').read_text());c=m['config']
            cap=c.get('calibration_cap', c['modes'][m['mode']]);profile=c['profile']
            if m['status']!='passed' or c['seed']!=seed or c.get('lifetime') or c.get('purpose')!='calibration': raise ValueError('not an isolated calibration run')
            if c.get('target')!='z1' or not c.get('power_model') or not m.get('energy_reconciliation'): raise ValueError('unqualified energy model')
            if type(profile) is not int or type(cap) is not int or profile not in (1,2) or cap not in (1,2,4): raise ValueError('invalid cell')
            if m['effective_cap']!=cap: raise ValueError('configured cap clipped by packet budget')
            cost=s.get('energy_per_delivered_reading_nj');pdr=s.get('reading_pdr');delay=s.get('p95_delay_ms')
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in (cost,pdr,delay)): raise ValueError('nonfinite or nonnumeric metrics')
            if cost<=0 or not min_pdr<=pdr<=1 or not 0<=delay<=max_p95 or s.get('unique_authenticated_delivered',0)<=0: raise ValueError('quality threshold')
            if m.get('config_sha256') != hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest() or m.get('scenario_sha256') != sha(d/'scenario.csc'):
                raise ValueError('config/scenario identity mismatch')
            checks=verify_artifacts(d,m)
            if not m.get('binary_hashes') or not {'events.jsonl','summary.json','COOJA.testlog','generated-conf.h','scenario.csc'}.issubset(m.get('artifact_hashes',{})) or any(v!='OK' for v in checks.values()): raise ValueError('artifact/binary integrity')
            ctx=context(c,m['clients']);src={k:v for k,v in m['source_hashes'].items() if k!='firmware/generated-conf.h'}
            signature=(ctx,src,m['dependency_hashes'],m['pins'])
            if cohort is None: cohort,source_set,deps,pins=ctx,src,m['dependency_hashes'],m['pins']
            if signature!=(cohort,source_set,deps,pins): raise ValueError('mixed context/source/dependencies')
            key=(profile,cap)
            if key in cells: raise ValueError('duplicate cell')
            events=[json.loads(line) for line in (d/'events.jsonl').read_text().splitlines()]
            tx=[e for e in events if e['event_type']=='TX']
            if not tx or any(e['profile']!=profile or not 1<=e['count']<=cap for e in tx): raise ValueError('wire profile/count mismatch')
            record={'directory':str(d.relative_to(ROOT)), 'run_id':m['run_id'],'profile':profile,'cap':cap,
                    'seed':seed,'manifest_sha256':sha(d/'manifest.json'),'summary_sha256':sha(d/'summary.json'),
                    'cost_nj_per_reading':cost,'actual_batch_distribution':dict(Counter(str(e['count']) for e in tx))}
            cells[key]=record;accepted.append(record)
        except (ValueError,KeyError,OSError,TypeError) as exc:
            rejected.append({'directory':str(d),'reason':str(exc)})
    array=[[int(cells[(p,c)]['cost_nj_per_reading']) if (p,c) in cells else 0 for c in (1,2,4)] for p in (1,2)]
    complete=len(cells)==6 and not rejected
    winner=min(accepted,key=lambda r:r['cost_nj_per_reading']) if accepted else None
    return {'schema_version':1,'qualification':'qualified' if complete else 'incomplete',
            'units':'nJ/unique_authenticated_reading','estimator':'battery-node total energy / unique authenticated deliveries; includes warmup and drain; scenario proxy',
            'quality':{'min_pdr':min_pdr,'max_p95_ms':max_p95},'context':cohort,'source_hashes':source_set,
            'dependency_hashes':deps,'pins':pins,'source_seed_filter':seed,'source_records':accepted,
            'rejected_records':rejected,'p1_cost_nj':array,'b6_profile':winner['profile'] if winner else None,
            'scope':'single-seed scenario calibration; no robust superiority or residual-aware prediction claim'}

def validate_table(table, config, clients):
    if table.get('schema_version')!=1 or table.get('qualification')!='qualified': raise ValueError('Unqualified calibration schema/coverage')
    if config.get('seed')==table.get('source_seed_filter'): raise ValueError('Calibration/evaluation seed overlap')
    if context(config,clients)!=table['context']: raise ValueError('Calibration runtime context mismatch (including topology/client count)')
    if table.get('units')!='nJ/unique_authenticated_reading' or table.get('quality')!={'min_pdr':0.95,'max_p95_ms':5000}: raise ValueError('Unsupported calibration units/quality contract')
    if sources()!=table['source_hashes']: raise ValueError('Calibration source mismatch')
    for name,h in table['dependency_hashes'].items():
        p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or sha(p)!=h: raise ValueError('Calibration dependency mismatch')
    rebuilt=build_table([ROOT/r['directory'] for r in table['source_records']],table['source_seed_filter'],**{'min_pdr':table['quality']['min_pdr'],'max_p95':table['quality']['max_p95_ms']})
    for k in ('qualification','context','source_hashes','dependency_hashes','pins','source_records','p1_cost_nj','b6_profile'):
        if rebuilt[k]!=table[k]: raise ValueError('Calibration provenance/cost mismatch: '+k)
    return True
