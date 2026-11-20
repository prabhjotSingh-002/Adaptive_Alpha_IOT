"""Run a matched, radio-free Z1 P1 switch/hold timing experiment."""
import argparse
import fcntl
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from run_experiment import PROJECT, container_command, digest
from scenario_target import configure_z1

SOURCE = Path("firmware/policy/benchmark")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    container_out = "/workspace/" + str(out.relative_to(PROJECT))
    out.mkdir(parents=True, exist_ok=False)
    pins = json.loads((PROJECT / "results/setup/source-pins.json").read_text())
    tree = ET.parse(PROJECT / "simulations/scenarios/phase1-rpl-9.csc")
    sim = tree.find("simulation")
    for element in [*sim.findall("motetype")[1:], *sim.findall("mote")[1:]]:
        sim.remove(element)
    motetype = sim.find("motetype")
    motetype.find("source").text = f"/workspace/{SOURCE}/transition.c"
    motetype.find("commands").text = "make -j1 transition.z1 TARGET=z1"
    configure_z1(sim)
    tree.find("plugin/plugin_config/script").text = """
TIMEOUT(15000, log.testFailed());
while (true) {
  log.log(time + "," + id + "," + msg + "\\n");
  if (msg.startsWith("TRANSITION_FAIL")) log.testFailed();
  if (msg.startsWith("TRANSITION_DONE")) log.testOK();
  YIELD();
}
"""
    scenario = out / "scenario.csc"
    tree.write(scenario, encoding="UTF-8", xml_declaration=True)
    command = container_command(pins, ["bash", "-c",
        f"set -eu; cd /workspace/{SOURCE}; make TARGET=z1 clean; "
        "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja "
        f"--no-gui --contiki=/home/user/contiki-ng --logdir={container_out} {container_out}/scenario.csc"])
    files = [SOURCE / "transition.c", SOURCE / "Makefile", Path("firmware/policy/policy.c"),
             Path("firmware/policy/policy.h"), Path("host/run_transition_benchmark.py"),
             Path("configs/power-z1-v1.json")]
    manifest = dict(command=command, pins=pins, status="running",
                    source_hashes={str(path): digest(PROJECT / path) for path in files},
                    scenario_sha256=digest(scenario))
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    try:
        with (PROJECT / "results/phase_02/.runner.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with (out / "console.log").open("w") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
                manifest["exit_code"] = result.returncode
                result.check_returncode()
            binary = out / "transition.z1"
            shutil.copy2(PROJECT / SOURCE / "build/z1/transition.z1", binary)
        raw = (out / "COOJA.testlog").read_text()
        rows = [tuple(map(int, row)) for row in re.findall(
            r"TRANSITION_PAIR,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", raw)]
        if (len(rows) != 128 or {(r[0], r[1]) for r in rows} !=
                {(trial, profile) for trial in range(32) for profile in range(4)} or
                "TRANSITION_DONE" not in raw or "TRANSITION_FAIL" in raw):
            raise ValueError("Incomplete matched measurement")
        model = json.loads((PROJECT / "configs/power-z1-v1.json").read_text())
        if any(r[4:] != (16, model["frequency"]) or min(r[2:4]) <= 0 for r in rows):
            raise ValueError("Unexpected sample clock or elapsed time")
        # The CPU model includes an idle-radio baseline. Remove it for radio-off windows.
        cpu_na = model["nanoamps"][0] - model["radio_idle_nanoamps"]
        actions = (((1, 1), (2, 1)), ((2, 1), (1, 1)),
                   ((1, 1), (2, 4)), ((2, 4), (1, 1)))
        samples = [dict(trial=trial, initial_action=actions[profile][0],
                        target_action=actions[profile][1], hold_ticks=hold, switch_ticks=change,
                        repetitions=count, frequency_hz=hz,
                        delta_cpu_nj_per_action=(change-hold)*cpu_na*model["millivolts"]/(count*hz*1000))
                   for trial, profile, hold, change, count, hz in rows]
        (out / "samples.json").write_text(json.dumps(samples, indent=2) + "\n")
        manifest["status"] = "passed"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        manifest["artifact_hashes"] = {p.name: digest(p) for p in out.iterdir()
                                       if p.is_file() and p != manifest_path}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
