"""Run the remaining 5 calibration cells serially, generate qualified table, and verify preflight."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
out = root / "results/phase_05/z1-revised-calibration"
out.mkdir(parents=True, exist_ok=True)

first = "results/phase_04/20261120T074536709390Z-B1-8"
runs = [first]
records = [{
    "command": [sys.executable, "-B", "host/run_experiment.py", "--phase", "4", "--mode", "B1",
                "--clients", "8", "--target", "z1", "--power-model", "--seed", "223457", "--calibration-cap", "1"],
    "exit_code": 0,
    "manifests": [first + "/manifest.json"]
}]

for mode in ("B1", "B2"):
    caps = (2, 4) if mode == "B1" else (1, 2, 4)
    for cap in caps:
        cmd = [sys.executable, "-B", "host/run_experiment.py", "--phase", "4", "--mode", mode,
               "--clients", "8", "--target", "z1", "--power-model", "--seed", "223457", "--calibration-cap", str(cap)]
        before = set((root / "results/phase_04").glob("*/manifest.json"))
        rec = {"command": cmd, "started": time.time()}
        records.append(rec)
        log_file = out / f"calibration-{mode}-cap{cap}.log"
        with log_file.open("w") as log:
            res = subprocess.run(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        rec.update(exit_code=res.returncode, seconds=time.time() - rec["started"])
        after = set((root / "results/phase_04").glob("*/manifest.json")) - before
        rec["manifests"] = [str(p.relative_to(root)) for p in after]
        (out / "calibration-commands.json").write_text(json.dumps(records, indent=2))
        if res.returncode != 0 or len(after) != 1:
            raise SystemExit(f"Calibration failure on {mode} cap {cap}")
        new_run = str(next(iter(after)).parent.relative_to(root))
        runs.append(new_run)
        (out / "calibration-inputs.json").write_text(json.dumps(runs, indent=2))
        print(f"{mode} cap {cap} passed: {new_run}", flush=True)

# Build qualified cost table
calib_table = out / "cost-table-revised.json"
build_cmd = [sys.executable, "-B", "host/calibrate.py", "--seed", "223457",
             "--calibration-inputs", str(out / "calibration-inputs.json"),
             "--out", str(calib_table)]
build_log = out / "table-build.log"
with build_log.open("w") as log:
    print(build_cmd, file=log, flush=True)
    subprocess.run(build_cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
print(f"Built qualified cost table at {calib_table}", flush=True)

# Preflight check for 9-node P1
preflight_cmd = [sys.executable, "-B", "host/run_experiment.py", "--phase", "5", "--mode", "P1",
                 "--clients", "8", "--target", "z1", "--power-model", "--seed", "123456",
                 "--policy-cost-table", str(calib_table), "--require-qualified-policy",
                 "--energy-budget-nj", "4097000000", "--preflight-only"]
preflight_log = out / "p1-preflight.log"
with preflight_log.open("w") as log:
    print(preflight_cmd, file=log, flush=True)
    subprocess.run(preflight_cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
print("P1 preflight passed successfully!", flush=True)
