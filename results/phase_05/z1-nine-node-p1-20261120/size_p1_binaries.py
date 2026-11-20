import json,subprocess
from pathlib import Path
root=Path('/workspace');base=root/'results/phase_05/z1-nine-node-p1-20261120'
a=json.loads((base/'attempts.json').read_text());paths=[];margins=[]
for row in a:
 d=(root/row['manifests'][0]).parent;m=json.loads((d/'manifest.json').read_text())
 paths.extend(d/name for name in m['binary_hashes'])
 for line in (d/'events.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e['event_type']=='STACK':margins.append(e['reserved']-e['used'])
version=subprocess.run(['msp430-size','--version'],capture_output=True,text=True,check=True)
r=subprocess.run(['msp430-size',*[str(p) for p in paths]],capture_output=True,text=True,check=True)
(base/'msp430-size.log').write_text(version.stdout+r.stdout+r.stderr)
records=[]
for line in r.stdout.splitlines()[1:]:
 values=line.split(None,5)
 if len(values)==6:records.append(dict(text=int(values[0]),data=int(values[1]),bss=int(values[2]),file=values[5]))
report={'tool':version.stdout.splitlines()[0],'binaries':records,
        'max_text_plus_data_bytes':max(x['text']+x['data'] for x in records),
        'max_data_plus_bss_bytes':max(x['data']+x['bss'] for x in records),
        'minimum_observed_stack_reserved_minus_used_bytes':min(margins),
        'scope':'Linker fit and observed stack usage in the two P1 runs'}
(base/'binary-size-evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='binaries'},indent=2))
