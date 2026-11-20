"""Collect serial Z1 controls for the frozen affordability replay."""
import json
from pathlib import Path
import re
import subprocess
import sys

from run_experiment import digest

out = Path("results/phase_05/z1-affordability-v3")
protocol = json.loads((out / "protocol.json").read_text())
for workload, options in (
    ("changing", ("--period-ms", "500", "--middle-period-ms", "4000", "--readings", "27")),
    ("finite", ("--period-ms", "1000", "--energy-budget-nj", "4097000000", "--readings", "96")),
):
    for mode in ("B1", "B2"):
        stem = out / f"{workload}-{mode}"
        command = [
            sys.executable, "-B", "host/run_experiment.py", "--phase", "4",
            "--mode", mode, "--target", "z1", "--clients", "2", "--power-model",
            "--seed", str(protocol["seed"]), *options,
        ]
        with stem.with_suffix(".log").open("x") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        log_path = stem.with_suffix(".log")
        matches = re.findall(r"^passed .*?/results/phase_04/(\S+)", log_path.read_text(), re.M)
        attempt = dict(command=command, exit_code=result.returncode, log_sha256=digest(log_path),
                       passed=result.returncode == 0 and len(matches) == 1)
        if attempt["passed"]:
            directory = Path("results/phase_04") / matches[0]
            attempt.update(directory=str(directory), manifest_sha256=digest(directory / "manifest.json"))
        stem.with_suffix(".json").write_text(json.dumps(attempt, indent=2) + "\n")
        if not attempt["passed"]:
            raise SystemExit(f"Control failed. See {log_path}")
