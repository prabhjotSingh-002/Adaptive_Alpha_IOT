"""Read-only resolution baseline; writes only a new audit directory."""
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def inspect_run(directory):
    directory = directory.resolve()
    directory.relative_to((ROOT / 'results').resolve())
    manifest = json.loads((directory / 'manifest.json').read_text())
    checked, errors = 0, []
    for group in ('artifact_hashes', 'binary_hashes'):
        for relative, expected in manifest.get(group, {}).items():
            path = (directory / relative).resolve()
            try:
                path.relative_to(directory)
                if sha(path) != expected:
                    errors.append('hash mismatch: ' + relative)
                checked += 1
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
    return {'directory': str(directory.relative_to(ROOT)), 'checked_hashes': checked,
            'errors': errors, 'status': manifest.get('status'),
            'qualification': manifest.get('config', {}).get('policy_calibration_status')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', default='results/campaigns/20261116-corrected')
    args = parser.parse_args()
    campaign = (ROOT / args.campaign).resolve()
    campaign.relative_to((ROOT / 'results/campaigns').resolve())
    out = ROOT / 'results/resolution_audit' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-phase1')
    out.mkdir(parents=True, exist_ok=False)
    for name, command in [('git-status.txt', ['git', 'status', '--short']),
                          ('baseline.diff', ['git', 'diff', '--binary']),
                          ('processes.txt', ['ps', '-eo', 'pid,ppid,etime,comm'])]:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (out / name).write_text(result.stdout + result.stderr)
    inventory = []
    for base in [*sorted((ROOT / 'results').glob('phase_0[1-5]')), ROOT / 'results/campaigns', ROOT / 'PLANS']:
        for path in sorted(base.rglob('*')):
            if path.is_file() and not path.is_symlink():
                inventory.append({'path': str(path.relative_to(ROOT)), 'size': path.stat().st_size, 'sha256': sha(path)})
    (out / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    state = json.loads((campaign / 'state.json').read_text())
    results, errors = [], []
    for attempt in state['attempts']:
        if not attempt.get('selected'):
            continue
        try:
            directory = (ROOT / attempt['directory']).resolve()
            directory.relative_to((ROOT / 'results').resolve())
            for name in ('manifest', 'summary'):
                if sha(directory / (name + '.json')) != attempt[name + '_sha256']:
                    raise ValueError(name + ' selection hash mismatch')
            results.append(inspect_run(directory))
        except (OSError, ValueError, KeyError) as exc:
            errors.append({'attempt': attempt.get('directory'), 'error': str(exc)})
    report = {'campaign': args.campaign, 'recorded_status': state['status'],
              'protocol_hash_matches': sha(campaign / 'protocol.json') == state['protocol_sha256'],
              'inventory_files': len(inventory), 'runs': results, 'errors': errors,
              'liveness': 'Process namespace snapshot only; host writer/container absence not certified.',
              'scope': 'Integrity audit, not scientific reanalysis or calibration qualification.'}
    (out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(out.relative_to(ROOT))
    print(json.dumps({'selected_checked': len(results), 'artifact_binary_hashes': sum(r['checked_hashes'] for r in results),
                      'errors': len(errors) + sum(len(r['errors']) for r in results), 'protocol_matches': report['protocol_hash_matches']}))
    return int(bool(errors or any(r['errors'] for r in results) or not report['protocol_hash_matches']))


if __name__ == '__main__':
    raise SystemExit(main())
