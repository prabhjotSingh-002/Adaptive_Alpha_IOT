"""Serial, resumable experiment campaign using the canonical runner."""
import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path
from campaign import ROOT, atomic_json, sha, snapshot_sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    directory = args.directory.resolve()
    protocol = json.loads((directory/'protocol.json').read_text())
    lock = (directory/'campaign.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = directory/'state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state['protocol_sha256'] != sha(directory/'protocol.json'):
            raise ValueError('Frozen protocol changed')
    else:
        state = {'status':'running', 'protocol_sha256':sha(directory/'protocol.json'),
                 'source_hashes':snapshot_sources(), 'attempts':[]}
        atomic_json(state_path,state)
    if state['source_hashes'] != snapshot_sources():
        raise ValueError('Source changed; create a new campaign instead of mixing builds')
    completed = {(a['group'],a['mode'],a['seed']) for a in state['attempts'] if a.get('selected')}
    count = 0
    for seed in protocol['seeds']:
        for group in protocol['groups']:
            for mode in group['modes']:
                cell=(group['id'],mode,seed)
                if cell in completed:
                    continue
                if args.limit is not None and count >= args.limit:
                    state['status']='partial';atomic_json(state_path,state);return
                if state['source_hashes'] != snapshot_sources():
                    raise ValueError('Source changed during campaign')
                cmd=[sys.executable,str(ROOT/'host/run_experiment.py'),'--phase',str(group['phase']),
                     '--mode',mode,'--seed',str(seed),*group['arguments']]
                before=set((ROOT/f"results/phase_0{group['phase']}").glob('*/manifest.json'))
                attempt={'group':group['id'],'mode':mode,'seed':seed,'command':cmd,
                         'selected':False,'started':time.time()}
                log=directory/f"attempt-{len(state['attempts']):04d}.log"
                with log.open('w') as output:
                    result=subprocess.run(cmd,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
                attempt.update(exit_code=result.returncode,wall_seconds=time.time()-attempt['started'],log=str(log.relative_to(ROOT)))
                after=set((ROOT/f"results/phase_0{group['phase']}").glob('*/manifest.json'))-before
                candidates=[]
                for path in after:
                    m=json.loads(path.read_text())
                    if m.get('mode')==mode and m.get('config',{}).get('seed')==seed:
                        candidates.append(path.parent)
                if len(candidates)==1:
                    run=candidates[0];m=json.loads((run/'manifest.json').read_text())
                    attempt['directory']=str(run.relative_to(ROOT))
                    if result.returncode==0 and m.get('status')=='passed' and (run/'summary.json').exists():
                        attempt.update(selected=True,manifest_sha256=sha(run/'manifest.json'),summary_sha256=sha(run/'summary.json'))
                state['attempts'].append(attempt);count+=1
                state['status']='running' if attempt['selected'] else 'failed'
                atomic_json(state_path,state)
                print(f"{len(state['attempts'])}: {cell}: {'passed' if attempt['selected'] else 'FAILED'} ({attempt['wall_seconds']:.1f}s)",flush=True)
                if not attempt['selected']:
                    raise SystemExit('Campaign stopped at failed attempt; evidence preserved')
    state['status']='complete';atomic_json(state_path,state)


if __name__=='__main__':
    main()
