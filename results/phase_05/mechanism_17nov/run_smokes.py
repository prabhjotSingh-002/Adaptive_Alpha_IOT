import json,subprocess,sys,time,fcntl,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=root/'results/phase_05/mechanism_17nov'
sys.path.insert(0,str(root/'host'))
from campaign import snapshot_sources
(out/'frozen-sources.json').write_text(json.dumps(snapshot_sources(),indent=2))
records=[]
for name,extra in [('native-no-cost-fallback',['--mode','P1','--target','cooja']),('z1-measured-batching',['--mode','B6','--target','z1','--power-model'])]:
 cmd=[sys.executable,'-B','host/run_experiment.py','--phase','5','--clients','2','--seed','123456',*extra]
 record={'name':name,'command':cmd,'started':time.time(),'status':'running'};records.append(record)
 (out/'smoke-attempts.json').write_text(json.dumps(records,indent=2))
 before=set((root/'results/phase_05').glob('*/manifest.json'))
 with (out/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
 new=set((root/'results/phase_05').glob('*/manifest.json'))-before
 record.update(exit_code=result.returncode,seconds=time.time()-record['started'],status='passed' if result.returncode==0 else 'failed',manifests=[str(p.relative_to(root)) for p in new])
 (out/'smoke-attempts.json').write_text(json.dumps(records,indent=2))
 print(name,record['status'],flush=True)
 if result.returncode:raise SystemExit(result.returncode)
 if snapshot_sources()!=json.loads((out/'frozen-sources.json').read_text()):raise SystemExit('Source drift; stop before next run')
