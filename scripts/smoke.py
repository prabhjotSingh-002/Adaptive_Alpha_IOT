#!/usr/bin/env python3
"""Rerun the validated Phase 1 scenario using the pinned image and built Cooja."""
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

project = Path(__file__).resolve().parents[1]
pins = json.loads((project / "results/setup/source-pins.json").read_text())
for relative, expected in [("external/contiki-ng", pins["contiki_ng_commit"]), ("external/contiki-ng/tools/cooja", pins["cooja_commit"])]:
    actual = subprocess.check_output(["git", "-C", str(project / relative), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected:
        raise SystemExit("Source pin mismatch: " + relative)
if not (project / "external/contiki-ng/tools/cooja/build/install/cooja/bin/cooja").exists():
    raise SystemExit("Build Cooja using scripts/phase1_container.sh first")
run_id = datetime.datetime.now(datetime.timezone.utc).strftime("smoke-%Y%m%dT%H%M%S%fZ")
out = project / "results/phase_01" / run_id
out.mkdir()
container_out = "/workspace/" + out.relative_to(project).as_posix()
command = ["docker", "run", "--rm", "--mount", f"type=bind,source={project / 'external/contiki-ng'},destination=/home/user/contiki-ng", "--mount", f"type=bind,source={project},destination=/workspace", pins["container_image"], "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja", "--no-gui", "--contiki=/home/user/contiki-ng", "--logdir=" + container_out, "/workspace/simulations/scenarios/phase1-rpl-9.csc"]
manifest = {"run_id": run_id, "pins": pins, "command": command, "status": "running", "scenario_sha256": hashlib.sha256((project / "simulations/scenarios/phase1-rpl-9.csc").read_bytes()).hexdigest()}
manifest_path = out / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
with (out / "console.log").open("w") as log:
    try:
        result = subprocess.run(["sg", "docker", "-c", shlex.join(command)], stdout=log, stderr=subprocess.STDOUT, timeout=900)
        manifest["exit_code"] = result.returncode
        raw = (out / "COOJA.testlog").read_text() if (out / "COOJA.testlog").exists() else ""
        clients = sorted({int(line.split(",", 2)[1]) for line in raw.splitlines() if "Received response" in line})
        manifest["clients_with_response"] = clients
        manifest["status"] = "passed" if result.returncode == 0 and "TEST OK" in raw and clients == list(range(2, 10)) else "failed"
    except subprocess.TimeoutExpired:
        manifest["status"] = "timeout"
manifest["artifacts_sha256"] = {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in out.iterdir() if file != manifest_path and file.is_file()}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print(manifest["status"], out)
sys.exit(0 if manifest["status"] == "passed" else 1)
