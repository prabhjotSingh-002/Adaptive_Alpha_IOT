"""Reparse actual raw logs and verify bounded-mechanism acceptance independently."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'host'))
from campaign import snapshot_sources
from evidence import verify_artifacts
from parse_logs import parse
from mechanism_checks import policy_wire,root_reset,depletion
from calibration_contract import validate_table
base=root/'results/phase_05/mechanism_17nov';directory=base/'validation-v2'
rows=json.loads((directory/'attempts.json').read_text());frozen=json.loads((directory/'frozen-sources.json').read_text())
assert snapshot_sources()==frozen,'Source drift after measurement'
assert json.loads((directory/'status.json').read_text())['status']=='passed'
table=json.loads((directory/'cost-table-v1.json').read_text());report={'runs':[],'artifact_binary_hashes_checked':0,'raw_events_reparsed':0,'residual_aware_p1':'unresolved; local forecast not validated','scope':'single-seed 3-node Z1 mechanisms, not comparative gains'}
for row in rows:
 assert row['status']=='passed' and row['exit_code']==0
 path=root/row['manifests'][0];d=path.parent;m=json.loads(path.read_text());c=m['config'];s=json.loads((d/'summary.json').read_text())
 assert hashlib.sha256(path.read_bytes()).hexdigest()==row['manifest_sha256']
 verification=verify_artifacts(d,m);assert verification and all(x=='OK' for x in verification.values())
 report['artifact_binary_hashes_checked']+=len(verification)
 events,frames=parse(d/'COOJA.testlog',m['run_id'],profile=c['profile'],phase=c['phase'],schema=c['schema_version'])
 assert events==[json.loads(line) for line in (d/'events.jsonl').read_text().splitlines()]
 report['raw_events_reparsed']+=len(events)
 record={'name':row['name'],'run_id':m['run_id'],'directory':str(d.relative_to(root)),
         'config_sha256':m['config_sha256'],'scenario_sha256':m['scenario_sha256'],'binary_hashes':m['binary_hashes'],
         'artifact_binary_checks':len(verification),'reading_pdr':s['reading_pdr'],'p95_delay_ms':s['p95_delay_ms'],
         'lifetime':s.get('lifetime'),'policy':s.get('policy'),'mechanism_checks':s.get('mechanism_checks')}
 if c.get('phase')==5:
  assert policy_wire(events,c)==s['mechanism_checks']['policy_wire']
 if c.get('root_reset_test'):
  assert root_reset(events)==s['mechanism_checks']['root_reset']
  text=(d/'COOJA.testlog').read_text();assert 'ROOT_MOTE_REPLACED' in text and 'BOOT_REGRANT_REFUSED' in text
 if c.get('lifetime'):
  assert depletion(events,frames,c,m['energy_reconciliation'])==s['mechanism_checks']['depletion']
 if row['name'].startswith('p1-qualified'):
  validate_table(table,c,m['clients'])
  assert c['p1_cost_nj']==table['p1_cost_nj']
  assert c['policy_cost_sha256']==hashlib.sha256((directory/'cost-table-v1.json').read_bytes()).hexdigest()
  match=re.search(r'^#define LAB_CONFIG_ID (\d+)u', (d/'generated-conf.h').read_text(),re.M)
  assert match and int(match[1])==c['config_id']
  # Replay cost ranking from the recorded measured-rate state; only reason BEST
  # claims to select/hold the minimum, while DWELL/NOSAVE may retain a valid action.
  rates={};checked=0
  for e in events:
   node=e['node_id']
   if e['event_type']=='FEATURE':rates[node]=e['rate_hz_x100']
   if e['event_type']=='POLICY' and e['reason']==6:
    candidates=[];fit=(c['payload_budget']-c['reserved_bytes']-11)//10
    for pi in range(2):
     for ci,cap in enumerate((1,2,4)):
      cost=c['p1_cost_nj'][pi][ci]
      if cost and cap<=fit and (cap==1 or (cap-1)*100000<(c['deadline_ms']-c.get('flush_lead_ms',0))*rates[node]):candidates.append((cost,pi+1,cap))
    expected=min(candidates)
    assert (e['profile'],e['cap'])==expected[1:],'Cost-rank decision mismatch'
    checked+=1
  assert checked;record['best_cost_actions_replayed']=checked
 if row['name']=='b3-threshold-finite':
  previous={};checked=0
  for e in events:
   if e['event_type']!='POLICY':continue
   node=e['node_id'];res=e['residual_nj'];prior=previous.get(node,2 if res<c['b3_threshold_nj_lo'] else 1)
   chosen=1 if res>c['b3_threshold_nj_hi'] else 2 if res<c['b3_threshold_nj_lo'] else prior
   assert e['profile']==chosen and e['cap']==1
   previous[node]=chosen;checked+=1
  for node in (2,3):assert {e['profile'] for e in events if e['event_type']=='RX' and e['sender']==node}=={1,2}
  record['threshold_actions_replayed']=checked
 report['runs'].append(record)
(base/'mechanism-acceptance.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'runs':len(report['runs']),'hashes':report['artifact_binary_hashes_checked'],'raw_events':report['raw_events_reparsed'],'status':'passed','residual_aware_p1':'unresolved'},indent=2))
