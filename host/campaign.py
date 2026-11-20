"""Explicit, immutable experiment selections and paired statistical reports.

Historical runs are never moved or rewritten. A campaign names exact attempts.
"""
import hashlib
import json
from evidence import verify_artifacts
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('reading_pdr', 'p95_delay_ms', 'packets_submitted',
           'application_packet_bytes', 'energy_per_delivered_reading_nj')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def snapshot_sources():
    return {str(p.relative_to(ROOT)): sha(p)
            for folder in ('firmware', 'host', 'configs', 'simulations')
            for p in sorted((ROOT / folder).rglob('*'))
            if p.is_file() and 'build' not in p.parts and '__pycache__' not in p.parts
            and p.name != 'generated-conf.h'
            and (p.suffix in ('.c', '.h', '.py', '.mk', '.json', '.csc') or p.name == 'Makefile')}


def campaign_rows(directory):
    """Read only selected attempts whose immutable artifact hashes match."""
    directory = Path(directory)
    protocol = json.loads((directory / 'protocol.json').read_text())
    state = json.loads((directory / 'state.json').read_text())
    if sha(directory / 'protocol.json') != state['protocol_sha256']:
        raise ValueError('Campaign protocol changed')
    rows = []
    for attempt in state['attempts']:
        if not attempt.get('selected'):
            continue
        run = (ROOT / attempt['directory']).resolve()
        if not run.is_relative_to((ROOT / 'results').resolve()):
            raise ValueError('Unsafe campaign run path')
        for name in ('manifest', 'summary'):
            if sha(run / (name + '.json')) != attempt[name + '_sha256']:
                raise ValueError('Campaign artifact changed: ' + str(run))
        manifest = json.loads((run / 'manifest.json').read_text())
        if manifest.get('status') != 'passed' or manifest.get('mode') != attempt['mode'] or manifest.get('config', {}).get('seed') != attempt['seed']:
            raise ValueError('Campaign attempt identity mismatch')
        config = manifest['config']
        if manifest.get('schema_version') not in (1, 2) or manifest.get('config_sha256') != hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest():
            raise ValueError('Run schema/config identity mismatch')
        if manifest.get('scenario_sha256') != sha(run / 'scenario.csc'):
            raise ValueError('Run scenario identity mismatch')
        verified = verify_artifacts(run, manifest)
        required = {'summary.json', 'events.jsonl', 'generated-conf.h', 'scenario.csc', 'COOJA.testlog'}
        if not required.issubset(manifest.get('artifact_hashes', {})) or not manifest.get('binary_hashes') or any(v != 'OK' for v in verified.values()):
            raise ValueError('Incomplete or changed run evidence: ' + str(run))
        rows.append({'group': attempt['group'], 'mode': manifest['mode'],
                     'seed': manifest['config']['seed'], 'directory': str(run),
                     'summary': json.loads((run / 'summary.json').read_text()),
                     'manifest': manifest})
    return protocol, state, rows


def report(directory):
    from analysis import _bootstrap_ci, _paired_diff
    from comparison_guard import admit_group
    protocol, state, rows = campaign_rows(directory)
    groups = {}
    for spec in protocol['groups']:
        selected = [r for r in rows if r['group'] == spec['id']]
        lineage = admit_group([r['directory'] for r in selected])
        modes = {}
        baseline = {r['seed']: r for r in selected if r['mode'] == 'B1'}
        for mode in spec['modes']:
            runs = [r for r in selected if r['mode'] == mode]
            entry = {'n': len(runs), 'seeds': sorted(r['seed'] for r in runs),
                     'metrics': {}, 'paired_vs_B1': {},
                     'profiles': sorted({v for r in runs for v in (r['summary'].get('policy') or {}).get('profiles_used', [])}),
                     'caps': sorted({v for r in runs for v in (r['summary'].get('policy') or {}).get('caps_used', [])})}
            for key in METRICS:
                values = [r['summary'][key] for r in runs if r['summary'].get(key) is not None]
                stats = _bootstrap_ci(values)
                if len(values) < 2:
                    stats.update(ci_lo=None, ci_hi=None, std=None)
                entry['metrics'][key] = stats
                pairs = [(baseline[r['seed']]['summary'][key], r['summary'][key])
                         for r in runs if r['seed'] in baseline and r['summary'].get(key) is not None
                         and baseline[r['seed']]['summary'].get(key) is not None]
                if mode != 'B1':
                    diff = _paired_diff([p[0] for p in pairs], [p[1] for p in pairs])
                    diff.update(matched_pairs=len(pairs), missing_pairs=len(protocol['seeds'])-len(pairs))
                    diff['note'] = 'paired seed estimate; no automatic significance or adequacy claim'
                    if len(pairs) < 2:
                        diff.update(ci_lo=None, ci_hi=None)
                    entry['paired_vs_B1'][key] = diff
            modes[mode] = entry
        groups[spec['id']] = {'description': spec['description'], 'modes': modes, 'lineage': lineage}
    return {'campaign': protocol['id'], 'status': state['status'], 'groups': groups,
            'expected': sum(len(g['modes']) for g in protocol['groups'])*len(protocol['seeds']),
            'selected': len(rows), 'attempts': len(state['attempts']),
            'limitations': protocol['limitations'],
            'statistics': 'Seed is experimental unit; mean of run-level p95s; 95% percentile bootstrap, 4000 draws. Paired differences use matched seeds. Intervals are descriptive, without multiplicity correction.'}
