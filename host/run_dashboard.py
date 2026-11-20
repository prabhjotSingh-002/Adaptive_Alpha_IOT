"""Launch the AdaptiveAlpha dashboard inside the pinned Contiki container.

Flask is reused from results/dashboard-deps; numerical libraries come from
the pinned container. The results/
directory is bind-mounted read-only so the dashboard reads live data.
Port 5000 is forwarded to the host.

Usage:
    python3 host/run_dashboard.py
    python3 host/run_dashboard.py --port 8080
"""
import argparse
import shlex
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
CONTAINER = "contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609"


def main():
    parser = argparse.ArgumentParser(description="Start the experiment dashboard.")
    parser.add_argument("--port", type=int, default=5000,
                        help="Host port to forward (default 5000)")
    args = parser.parse_args()

    port = args.port
    if not 1 <= port <= 65535: parser.error("port must be between 1 and 65535")

    # Reuse the existing local Flask dependencies; do not download at launch.
    cmd_inner = (
        "test -d /workspace/results/dashboard-deps/flask || exit 1; "
        f"cd /workspace && "
        f"PYTHONPATH=/workspace/results/dashboard-deps DASHBOARD_PORT={port} python3 host/dashboard.py"
    )

    docker_cmd = [
        "sg", "docker", "-c",
        shlex.join([
            "docker", "run", "--rm",
            "--name", f"adaptivealpha-dashboard-{port}",
            "-p", f"127.0.0.1:{port}:{port}",
            "--mount", f"type=bind,source={WORKSPACE}/external/contiki-ng,destination=/home/user/contiki-ng,readonly",
            "--mount", f"type=bind,source={WORKSPACE},destination=/workspace,readonly",
            CONTAINER,
            "bash", "-c", cmd_inner,
        ])
    ]

    print(f"[run_dashboard] Starting dashboard on http://localhost:{port}", flush=True)
    print(f"[run_dashboard] Open your browser at http://localhost:{port}", flush=True)
    print(f"[run_dashboard] Press Ctrl+C to stop.", flush=True)

    try:
        result = subprocess.run(docker_cmd)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        print("\n[run_dashboard] Stopped.", flush=True)


if __name__ == "__main__":
    main()
