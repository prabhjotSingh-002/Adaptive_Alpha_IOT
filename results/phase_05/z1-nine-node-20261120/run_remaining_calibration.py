"""Small serial six-cell calibration; canonical runner retains all artifacts."""
import json,subprocess,sys,time,hashlib,fcntl
from pathlib import Path
root=Path(__file__).resolve().parents[3]
out=root/'results/phase_05/z1-nine-node-20261120'
out.mkdir(exist_ok=True)
checks=subprocess.run(['ps','-eo','pid,comm,args'],capture_output=True,text=True)
(out/'host-processes.log').write_text(checks.stdout)
containers=subprocess.run(['sg','docker','-c','docker ps --no-trunc'],capture_output=True,text=True)
(out/'host-containers.log').write_text(containers.stdout+containers.stderr)
lock=(root/'results/phase_02/.runner.lock').open('a')
first = 'results/phase_04/20261119T191047113613Z-B1-8'
deadline = time.monotonic() + 900
while True:
 status = json.loads((root/first/'manifest.json').read_text())['status']
 if status == 'passed': break
 if status != 'running' or time.monotonic() >= deadline:
  raise SystemExit(f'Initial calibration did not pass: {status}')
 time.sleep(5)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
runs=[first]
records=[{'command':[sys.executable,'-B','host/run_experiment.py','--phase','4','--mode','B1','--clients','8','--target','z1','--power-model','--seed','223457','--calibration-cap','1'], 'exit_code':0, 'manifests':[first+'/manifest.json']}]
for mode in ('B1','B2'):
 for cap in ((2,4) if mode == 'B1' else (1,2,4)):
  command=[sys.executable,'-B','host/run_experiment.py','--phase','4','--mode',mode,'--clients','8','--target','z1','--power-model','--seed','223457','--calibration-cap',str(cap)]
  before=set((root/'results/phase_04').glob('*/manifest.json'))
  record={'command':command,'started':time.time()};records.append(record)
  (out/'calibration-commands.json').write_text(json.dumps(records,indent=2))
  with (out/f'calibration-{mode}-cap{cap}.log').open('w') as log:
   result=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT)
  record.update(exit_code=result.returncode,seconds=time.time()-record['started'])
  after=set((root/'results/phase_04').glob('*/manifest.json'))-before
  record['manifests']=[str(p.relative_to(root)) for p in after]
  (out/'calibration-commands.json').write_text(json.dumps(records,indent=2))
  if result.returncode or len(after)!=1:raise SystemExit('Calibration failure preserved; no further cells launched')
  runs.append(str(next(iter(after)).parent.relative_to(root)))
  (out/'calibration-inputs.json').write_text(json.dumps(runs,indent=2))
  print(mode,cap,'passed',runs[-1],flush=True)

def logged(command, filename):
 with (out/filename).open('w') as log:
  print(command, file=log, flush=True)
  subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)

logged([sys.executable,'-B','host/calibrate.py','--seed','223457','--calibration-inputs',str(out/'calibration-inputs.json'),'--out',str(out/'cost-table-v1.json')],'table-build.log')
logged([sys.executable,'-B','host/run_experiment.py','--phase','5','--mode','P1','--clients','8','--target','z1','--power-model','--seed','123456','--policy-cost-table',str(out/'cost-table-v1.json'),'--require-qualified-policy','--preflight-only'],'p1-preflight.log')
