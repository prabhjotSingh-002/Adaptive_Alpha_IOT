"""Common comparison admission checks; never pool unlike cohorts."""
import hashlib
import json
from pathlib import Path

def admit_group(directories):
    cohort=None
    seen=set()
    sources=[]
    keys=('target','backend','warmup_ms','period_ms','readings_per_sensor','deadline_ms','drain_ms','payload_budget','reserved_bytes','power_model','energy_sample_ms','aes_backend','bottleneck','radio_off_until_ms','cpu_work_iterations','flush_lead_ms')
    for directory in directories:
        p=Path(directory)
        m=json.loads((p/'manifest.json').read_text())
        c=m['config']
        if m.get('status')!='passed' or c.get('purpose')!='functional' or c.get('lifetime'):
            raise ValueError('Unqualified comparison run: '+str(p))
        signature=json.dumps({'config':{k:c.get(k) for k in keys},'clients':m['clients'],
            'sources':{k:v for k,v in m.get('source_hashes',{}).items() if k!='firmware/generated-conf.h'}},sort_keys=True)
        if cohort is None: cohort=signature
        if signature!=cohort: raise ValueError('Mixed comparison cohorts; select a single source/config cohort')
        cell=(m['mode'],c.get('seed'))
        if type(cell[1]) is not int or cell in seen: raise ValueError('Missing seed or duplicate comparison cell')
        seen.add(cell)
        sources.append({'directory':str(p),'manifest_sha256':hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest(),
                        'summary_sha256':hashlib.sha256((p/'summary.json').read_bytes()).hexdigest()})
    return sources
