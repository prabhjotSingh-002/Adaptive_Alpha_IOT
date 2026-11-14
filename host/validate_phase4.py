#!/usr/bin/env python3
"""Serial Phase 4 acceptance matrix, preserving individual failures and logs."""
import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--section',choices=['security','static','boundaries','lifetime','measurement','all'],default='all');args=parser.parse_args()
    now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
    out=ROOT/'results/phase_04'/('validation-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    base=[sys.executable,str(ROOT/'host/run_experiment.py'),'--phase','4','--timeout-seconds','300']
    cases=[]
    if args.section in ('security','all'):
        for mode in ('B1','B2'):
            for flag in ('--attack-test','--root-reset-test','--sensor-reset-test','--reorder-test','--radio-loss-test','--switch-test'):
                cases.append((mode+flag,base+['--mode',mode,'--clients','2','--target','z1',flag]))
            for fault in ('missing','version','profile','epoch'):
                cases.append((mode+'-provision-'+fault,base+['--mode',mode,'--clients','2','--target','z1','--provision-fault',fault]))
        for mode in ('B4','B5'):
            cases.append((mode+'-critical',base+['--mode',mode,'--clients','2','--target','z1','--critical-reading','2']))
    if args.section in ('measurement','all'):
        cases.append(('idle-listen-transition',base+['--mode','B2','--clients','2','--target','z1','--power-model','--radio-off-until-ms','30000','--seed','223456']))
        cases.append(('controlled-cpu-load',base+['--mode','B2','--clients','2','--target','z1','--power-model','--cpu-work-iterations','10000','--seed','223456']))
    if args.section in ('static','all'):
        for seed in (123456,123457,123458):
            cases.append(('static-'+str(seed),base+['--mode','all','--clients','8','--target','z1','--power-model','--seed',str(seed)]))
    if args.section in ('boundaries','all'):
        for flag,value in (('--period-ms','500'),('--period-ms','4000'),('--payload-budget','47')):
            cases.append(('boundary'+flag+value,base+['--mode','all','--clients','2',flag,value]))
    if args.section in ('lifetime','all'):
        for sample in (125,250):
            cases.append(('depletion-sensitivity-'+str(sample),base+['--mode','B2','--clients','2','--target','z1','--power-model','--warmup-ms','120000','--readings','120','--energy-budget-nj','9000000000','--deplete-node','2','--bottleneck','--seed','223456','--energy-sample-ms',str(sample)]))
        for seed in (123456,123457,123458):
            cases.append(('lifetime-'+str(seed),base+['--mode','all','--clients','2','--target','z1','--power-model','--warmup-ms','120000','--readings','120','--energy-budget-nj','9000000000','--deplete-node','2','--bottleneck','--seed',str(seed)]))
    index={'section':args.section,'status':'running','started':now(),'cases':[]}
    for i,(name,cmd) in enumerate(cases,1):
        log=out/(str(i).zfill(2)+'-'+name+'.log')
        record={'name':name,'command':cmd,'started':now(),'log':str(log.relative_to(ROOT))}
        print(f'[{i}/{len(cases)}] {name}',flush=True)
        with log.open('w') as f:
            try: code=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=1500).returncode
            except subprocess.TimeoutExpired: code=124
        record.update(exit_code=code,status='passed' if code==0 else 'failed',ended=now(),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        index['cases'].append(record);(out/'manifest.json').write_text(json.dumps(index,indent=2)+'\n')
        print(record['status'],name,flush=True)
    index.update(status='passed' if all(c['exit_code']==0 for c in index['cases']) else 'failed',ended=now())
    (out/'manifest.json').write_text(json.dumps(index,indent=2)+'\n');print(out,flush=True)
    return 0 if index['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
