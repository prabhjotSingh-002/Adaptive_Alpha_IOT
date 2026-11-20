"""Read-only, contained artifact verification shared by evidence consumers."""
import hashlib
from pathlib import Path


def verify_artifacts(directory, manifest):
    root = Path(directory).resolve()
    result = {}
    for name, expected in {**manifest.get('artifact_hashes', {}), **manifest.get('binary_hashes', {})}.items():
        path = (root / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root):
            result[name] = 'UNSAFE_PATH'
        elif not path.is_file():
            result[name] = 'MISSING'
        else:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            result[name] = 'OK' if actual == expected else 'MISMATCH'
    return result


def policy_qualification(manifest, summary):
    if manifest.get('mode') != 'P1':
        return 'functional'
    config = manifest.get('config', {})
    status = config.get('policy_calibration_status', '')
    if status == 'qualified':
        return 'qualified cost-aware'
    costs = config.get('p1_cost_nj', [])
    if not costs or not any(v for row in costs for v in row):
        return 'fallback diagnostic (costs unavailable)'
    return 'calibration compatibility pending'
