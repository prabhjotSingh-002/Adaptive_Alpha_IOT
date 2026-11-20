"""Serial bounded mechanism protocol. Failures are retained and stop execution."""
import datetime,hashlib,json,statistics,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=root/'results/phase_05/mechanism_17nov/validation';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'host'))
from campaign import snapshot_sources
from calibration_contract import validate_table
frozen=snapshot_sources();(out/'frozen-sources.json').write_text(json.dumps(frozen,indent=2))
protocol={'scope':'items 4–5; root+2 only; separate calibration and evaluation','calibration_seed':223457,'evaluation_seed':123456,
          'quality':{'min_pdr':0.95,'max_p95_ms':5000},'finite_budget_rule':'Round median static AES cap1 node energy at first GEN plus half the declared generation span up to next 1e6 nJ; freeze before P1 finite outcomes',
          'b3_bottleneck_budget_nj':9000000000,'b3_bottleneck_readings':120,'root_power':'unbounded','source_sha256':hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest(),
          'limitations':['single-seed mechanism evidence','P1 residual-aware ranking unvalidated','no comparative lifetime or scaling claim']}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2));records=[]

def job(name,phase,mode,extra):
 if snapshot_sources()!=frozen:raise SystemExit('Source changed before '+name)
 cmd=[sys.executable,'-B','host/run_experiment.py','--phase',str(phase),'--mode',mode,'--clients','2','--target','z1',*extra]
 before=set((root/f'results/phase_0{phase}').glob('*/manifest.json'))
 row={'name':name,'command':cmd,'status':'running','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};records.append(row)
 (out/'attempts.json').write_text(json.dumps(records,indent=2));started=time.time()
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT)
 added=set((root/f'results/phase_0{phase}').glob('*/manifest.json'))-before
 row.update(exit_code=p.returncode,status='passed' if p.returncode==0 else 'failed',wall_seconds=time.time()-started,manifests=[str(p.relative_to(root)) for p in added])
 (out/'attempts.json').write_text(json.dumps(records,indent=2));print(name,row['status'],flush=True)
 if p.returncode or len(added)!=1:raise SystemExit('Stopped at failure; evidence preserved: '+name)
 if snapshot_sources()!=frozen:raise SystemExit('Source changed during '+name)
 d=next(iter(added)).parent;m=json.loads((d/'manifest.json').read_text());s=json.loads((d/'summary.json').read_text())
 row['manifest_sha256']=hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest();(out/'attempts.json').write_text(json.dumps(records,indent=2))
 return d,m,s

inputs=[]
for mode in ('B1','B2'):
 for cap in (1,2,4):
  d,_,_=job(f'cal-{mode}-cap{cap}',4,mode,['--power-model','--seed','223457','--calibration-cap',str(cap)])
  inputs.append(str(d.relative_to(root)))
(out/'calibration-inputs.json').write_text(json.dumps(inputs,indent=2))
cmd=[sys.executable,'-B','host/calibrate.py','--seed','223457','--calibration-inputs',str(out/'calibration-inputs.json'),'--out',str(out/'cost-table-v1.json')]
r=subprocess.run(cmd,cwd=root,capture_output=True,text=True);(out/'table-build.log').write_text(r.stdout+r.stderr)
if r.returncode:raise SystemExit('Calibration did not qualify; do not launch adaptive evaluation')
table=json.loads((out/'cost-table-v1.json').read_text())
context=dict(table['context'],seed=123456);context.pop('clients');validate_table(table,context,2)
# Derive a finite budget only from independently measured static calibration.
cal_dir=root/inputs[0];ev=[json.loads(x) for x in (cal_dir/'events.jsonl').read_text().splitlines()];totals=[];samples=[]
for node in (2,3):
 first=min(e['sim_time_ms'] for e in ev if e['event_type']=='GEN' and e['node_id']==node)
 target=first+table['context']['readings_per_sensor']*table['context']['period_ms']/2
 sample=min((e for e in ev if e['event_type']=='ENERGY_MODEL' and e['node_id']==node),key=lambda e:abs(e['sim_time_ms']-target))
 totals.append(sample['total_nj']);samples.append({'node':node,'target_ms':target,'sample_ms':sample['sim_time_ms'],'total_nj':sample['total_nj']})
budget=int((statistics.median(totals)+999999)//1000000)*1000000
(out/'finite-budget-freeze.json').write_text(json.dumps({'budget_nj':budget,'calibration_run':inputs[0],'samples':samples,'horizon_ms':102000,'population':[2,3],'deplete_node':0,'root_budget':'unbounded','frozen_before_p1_evaluation':True},indent=2))
policy_args=['--power-model','--seed','123456','--policy-cost-table',str(out/'cost-table-v1.json'),'--require-qualified-policy']
d,m,s=job('p1-qualified-functional',5,'P1',policy_args)
if not s['mechanism_checks']['policy_wire']['authenticated_packets_matched_to_tx']:raise SystemExit('No accepted wire controls')
d,m,s=job('p1-qualified-finite',5,'P1',[*policy_args,'--energy-budget-nj',str(budget)])
if not s['mechanism_checks']['depletion']['depleted_nodes']:raise SystemExit('No death observed; retain censored mechanism result')
d,m,s=job('b3-threshold-finite',5,'B3',['--power-model','--seed','123456','--readings','120','--energy-budget-nj','9000000000'])
if not {1,2}.issubset(set(s['mechanism_checks']['policy_wire']['rx_profiles'])):raise SystemExit('B3 threshold transition not verified on accepted wire traffic')
d,m,s=job('bottleneck-depletion',4,'B1',['--power-model','--seed','123456','--readings','120','--energy-budget-nj','9000000000','--deplete-node','2','--bottleneck'])
if 2 not in s['mechanism_checks']['depletion']['depleted_nodes']:raise SystemExit('No intended bottleneck death observed')
for mode in ('B3','B6','P1'):
 for name,flag in (('attack','--attack-test'),('root-reset','--root-reset-test')):
  job(mode.lower()+'-'+name,5,mode,['--seed','123456',flag])
(out/'status.json').write_text(json.dumps({'status':'passed','runs':len(records),'protocol_sha256':hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest(),'items_4_5_residual_aware_p1':'unresolved as specified; no validated local forecast'},indent=2))
print('Bounded mechanism validation complete',flush=True)
