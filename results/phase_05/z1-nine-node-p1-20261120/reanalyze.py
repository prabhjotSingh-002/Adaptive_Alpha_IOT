from pathlib import Path
import json
import hashlib
from collections import Counter
from evidence import verify_artifacts
from parse_logs import parse
from mechanism_checks import policy_wire, depletion
from metrics import summarize

out = Path(__file__).parent
attempts = json.loads((out / 'attempts.json').read_text())
assert len(attempts) == 2
audit = []
for attempt in attempts:
    manifest = Path(attempt['manifests'][0])
    directory = manifest.parent
    m = json.loads(manifest.read_text())
    s = json.loads((directory / 'summary.json').read_text())
    c = dict(m['config'], energy_reconciliation=m['energy_reconciliation'])
    assert m['status'] == 'passed'
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == attempt['manifest_sha256']
    checks = verify_artifacts(directory, m)
    assert len(checks) == 13 and set(checks.values()) == {'OK'}, checks
    events, frames = parse(directory / 'COOJA.testlog', m['run_id'], profile=c['profile'], phase=5, schema=c['schema_version'])
    assert events == [json.loads(x) for x in (directory / 'events.jsonl').read_text().splitlines()]
    assert policy_wire(events, c) == s['mechanism_checks']['policy_wire']
    fresh = json.loads(json.dumps(summarize(events, frames, c, list(range(2, 10)), m['effective_cap'])))
    differences = [key for key, value in fresh.items() if s[key] != value]
    assert not differences, differences
    if c['lifetime']:
        assert depletion(events, frames, c, m['energy_reconciliation']) == s['mechanism_checks']['depletion']
    counts = Counter(f"{e['profile']}:{e['count']}" for e in events if e['event_type'] == 'TX')
    audit.append({
        'name': attempt['name'], 'directory': str(directory),
        'artifact_and_binary_checks': checks, 'raw_events': len(events),
        'radio_frames': len(frames), 'tx_profile_and_batch_size': dict(counts),
        'depletion_ms': {e['node_id']: e['sim_time_ms'] for e in events if e['event_type'] == 'DEPLETED'},
        'summary_reproduced_from_raw_log': True,
    })
(out / 'raw-reanalysis.json').write_text(json.dumps(audit, indent=2) + '\n')
print([(r['name'], r['raw_events'], r['radio_frames'], r['depletion_ms']) for r in audit])
