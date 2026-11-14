"""Launch the AdaptiveAlpha dashboard inside the pinned Contiki container.

Flask + matplotlib + numpy are available in the container. The results/
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

    # Install flask + run dashboard inside container
    cmd_inner = (
        "pip3 install -q flask && "
        f"cd /workspace && "
        f"DASHBOARD_PORT={port} python3 host/dashboard.py"
    )

    docker_cmd = [
        "sg", "docker", "-c",
        shlex.join([
            "docker", "run", "--rm",
            "-p", f"{port}:{port}",
            "--mount", f"type=bind,source={WORKSPACE}/external/contiki-ng,destination=/home/user/contiki-ng",
            "--mount", f"type=bind,source={WORKSPACE},destination=/workspace",
            CONTAINER,
            "bash", "-c", cmd_inner,
        ])
    ]

    print(f"[run_dashboard] Starting dashboard on http://localhost:{port}", flush=True)
    print(f"[run_dashboard] Open your browser at http://localhost:{port}", flush=True)
    print(f"[run_dashboard] Press Ctrl+C to stop.", flush=True)

    try:
        subprocess.run(docker_cmd)
    except KeyboardInterrupt:
        print("\n[run_dashboard] Stopped.", flush=True)


if __name__ == "__main__":
    main()
