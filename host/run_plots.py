"""Docker wrapper to run host/plots.py inside the pinned Contiki container.

Matplotlib and numpy are available in the container but not on the host Python.
Usage:
    python3 host/run_plots.py --phase 4 --output results/phase_04/figures/phase4-static.png
    python3 host/run_plots.py --runs results/phase_04/RUN1 results/phase_04/RUN2 \\
                               --output results/phase_04/figures/custom.png

The script discovers all passed non-test runs for the requested phase, groups
them and passes the directories to plots.py inside the container.
"""
import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
CONTAINER  = "contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609"

# Minimum client count to include in comparison (smoke 2-client runs excluded)
MIN_CLIENTS = 8


def _discover_runs(phase: int, min_clients: int = MIN_CLIENTS):
    """Return list of passed, non-test run dirs for a phase with >=min_clients."""
    found = []
    pattern = str(WORKSPACE / f"results/phase_0{phase}/*/summary.json")
    for f in sorted(glob.glob(pattern)):
        try:
            s = json.loads(Path(f).read_text())
            m = json.loads(Path(f).with_name('manifest.json').read_text())
            status  = s.get('status') or m.get('status', 'unknown')
            clients = m.get('clients', 0)
            sec     = s.get('security', '')
            if status == 'passed' and clients >= min_clients and 'security test' not in sec:
                found.append(Path(f).parent)
        except Exception:
            pass
    return found


def _run_in_docker(run_dirs, output: Path, title: str = ''):
    """Execute plots.py inside the pinned container."""
    # Paths inside container (/workspace maps to WORKSPACE)
    def to_container(p: Path) -> str:
        return '/workspace/' + str(p.relative_to(WORKSPACE))

    c_runs   = ' '.join(to_container(d) for d in run_dirs)
    c_output = to_container(output)
    c_title  = title.replace("'", "")

    cmd_inner = (
        f"cd /workspace && python3 host/plots.py {c_runs} "
        f"--output {c_output}"
        + (f" --title '{c_title}'" if c_title else "")
    )

    docker_cmd = [
        'sg', 'docker', '-c',
        (
            f"docker run --rm "
            f"--mount type=bind,source={WORKSPACE}/external/contiki-ng,"
            f"destination=/home/user/contiki-ng "
            f"--mount type=bind,source={WORKSPACE},destination=/workspace "
            f"{CONTAINER} "
            f"bash -c '{cmd_inner}'"
        )
    ]

    print(f"[run_plots] Generating {output.name} from {len(run_dirs)} runs …", file=sys.stderr)
    result = subprocess.run(docker_cmd, capture_output=False)
    if result.returncode != 0:
        raise RuntimeError(f"Docker plot run failed (exit {result.returncode})")
    print(f"[run_plots] Done → {output}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Generate comparison plots via Docker container.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--phase', type=int, choices=[2, 3, 4, 5],
                       help='Auto-discover passed runs for this phase')
    group.add_argument('--runs', nargs='+', type=Path,
                       help='Explicit list of run directories')
    parser.add_argument('--output', required=True, type=Path,
                        help='Output PNG path (relative to workspace root)')
    parser.add_argument('--title', default='',
                        help='Optional figure title suffix')
    parser.add_argument('--min-clients', type=int, default=MIN_CLIENTS,
                        help=f'Min clients filter for auto-discover (default {MIN_CLIENTS})')
    args = parser.parse_args()

    if args.phase:
        run_dirs = _discover_runs(args.phase, args.min_clients)
        if not run_dirs:
            print(f"[run_plots] No qualifying runs found for phase {args.phase}.", file=sys.stderr)
            sys.exit(1)
        print(f"[run_plots] Found {len(run_dirs)} qualifying runs for phase {args.phase}.", file=sys.stderr)
        title = args.title or f"Phase {args.phase} static pilot"
    else:
        run_dirs = [Path(r) for r in args.runs]
        title = args.title

    output = WORKSPACE / args.output if not Path(args.output).is_absolute() else Path(args.output)
    _run_in_docker(run_dirs, output, title)


if __name__ == '__main__':
    main()
