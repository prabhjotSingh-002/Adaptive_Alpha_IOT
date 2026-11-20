import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=root/'results/phase_05/mechanism_17nov';records=[]
for mode in ('B6','P1'):
 name='z1-rom-retry-'+mode
 cmd=[sys.executable,'-B','host/run_experiment.py','--phase','5','--mode',mode,'--clients','2','--target','z1','--power-model','--seed','123456']
 before=set((root/'results/phase_05').glob('*/manifest.json'));r={'command':cmd,'status':'running','started':time.time()};records.append(r);(out/'rom-retry-attempts.json').write_text(json.dumps(records,indent=2))
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
 r.update(exit_code=p.returncode,status='passed' if p.returncode==0 else 'failed',seconds=time.time()-r['started'],manifests=[str(x.relative_to(root)) for x in set((root/'results/phase_05').glob('*/manifest.json'))-before]);(out/'rom-retry-attempts.json').write_text(json.dumps(records,indent=2))
 print(mode,r['status'],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
