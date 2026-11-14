"""Docker wrapper to run host/analysis.py inside the pinned Contiki container.

Numpy is available in the container.  analysis.py itself can also run on any
host that has numpy installed.

Usage:
    python3 host/run_analysis.py --phase 4
    python3 host/run_analysis.py --phase 4 --phase 5 --output results/phase_05/analysis.json
"""
import argparse
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
CONTAINER  = "contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609"


def main():
    parser = argparse.ArgumentParser(
        description='Run statistical analysis via Docker container.')
    parser.add_argument('--phase', type=int, action='append', dest='phases',
                        default=[], choices=[2, 3, 4, 5],
                        help='Phase(s) to analyse (repeatable)')
    parser.add_argument('--output', type=str, default=None,
                        help='JSON output path (relative to workspace)')
    parser.add_argument('--min-clients', type=int, default=8)
    args = parser.parse_args()
    phases = args.phases if args.phases else [4]

    phase_flags = ' '.join(f'--phase {p}' for p in phases)
    out_flag    = f'--output /workspace/{args.output}' if args.output else ''
    min_flag    = f'--min-clients {args.min_clients}'

    cmd_inner = (
        f"cd /workspace && python3 host/analysis.py "
        f"{phase_flags} {out_flag} {min_flag}"
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

    print(f"[run_analysis] Phases {phases} …", file=sys.stderr)
    result = subprocess.run(docker_cmd)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
