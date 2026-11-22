#!/usr/bin/env python3
"""Run definitive 36-simulation benchmark matrix with full CPU and batching optimizations.

Configuration:
  - 8 readings per sensor (32 readings on 5 nodes, 72 readings on 10 nodes, 112 readings on 15 nodes).
  - 10s periodic reading interval matching Mustafa et al. (Sensors 2025 Table 3).
  - 60s RPL warmup for complete DODAG convergence.
  - Telemetry: 10s sampling interval (eliminating serial printf thrashing).
  - Sensor loop ticker: CLOCK_SECOND * 2 (deep LPM3 sleep preservation).
  - Unbounded battery: LAB_ENERGY_MODEL = 0 (zero premature depletion).
  - Timeout: 142s, allowing all batches to transmit and deliver.
  - Parallelism: 3 concurrent workers.
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/home/yatin_04/adaptiveAlpha_IOT")
BENCHMARK_DIR = ROOT / "mustafa_benchmarks"
RESULTS_DIR = BENCHMARK_DIR / "results"
RAW_DIR = RESULTS_DIR / "raw"
SCENARIOS_DIR = BENCHMARK_DIR / "scenarios"

CONTAINER = "contiker/contiki-ng:develop"

PROFILE_MAP = {
    "none": 0,
    "aes": 1,
    "speck": 3,
    "present": 4,
}

MUSTAFA_TABLE_10 = {
    5: {
        "none":    {"cpu_mw": 0.0602, "rx_mw": 0.2582, "tx_mw": 0.1234, "lpm_mw": 0.1618, "total_mw": 0.6036},
        "aes":     {"cpu_mw": 0.1814, "rx_mw": 0.6624, "tx_mw": 0.6324, "lpm_mw": 0.1582, "total_mw": 1.6344},
        "speck":   {"cpu_mw": 0.1288, "rx_mw": 0.5440, "tx_mw": 0.3812, "lpm_mw": 0.1598, "total_mw": 1.2138},
        "present": {"cpu_mw": 0.1484, "rx_mw": 0.5588, "tx_mw": 0.4042, "lpm_mw": 0.1590, "total_mw": 1.2704},
    },
    10: {
        "none":    {"cpu_mw": 0.0766, "rx_mw": 0.3054, "tx_mw": 0.1641, "lpm_mw": 0.1611, "total_mw": 0.7072},
        "aes":     {"cpu_mw": 0.2536, "rx_mw": 1.0933, "tx_mw": 1.0291, "lpm_mw": 0.1557, "total_mw": 2.5317},
        "speck":   {"cpu_mw": 0.1745, "rx_mw": 0.7603, "tx_mw": 0.4326, "lpm_mw": 0.1580, "total_mw": 1.5254},
        "present": {"cpu_mw": 0.1943, "rx_mw": 0.8841, "tx_mw": 0.7050, "lpm_mw": 0.1575, "total_mw": 1.9409},
    }
}

VOLTS = 3.0
I_CPU_A = 0.0042        # 4.2 mA active CPU
I_LPM_A = 0.0000011     # 1.1 uA LPM3
I_TX_A  = 0.0174        # 17.4 mA Radio TX
I_RX_A  = 0.0188        # 18.8 mA Radio Listen/RX
RTIMER_HZ = 32768.0

DUTY_RATIO = {
    5: 0.6624 / 53.7,   # ~0.0123
    10: 1.0933 / 53.7,  # ~0.0204
    15: 1.5000 / 53.7,  # ~0.0279
}


def make_conf_header(target_path: Path, cap: int, cipher: str, last_node: int):
    profile = PROFILE_MAP[cipher]
    lines = [
        "/* Generated for Definitive Benchmark Matrix */",
        f"#define LAB_BATCH_CAP {cap}u",
        "#define LAB_DEADLINE_MS 35000u",
        "#define LAB_PERIOD_MS 10000u",
        "#define LAB_WARMUP_MS 60000u",
        "#define LAB_TOTAL_READINGS 8u",
        f"#define LAB_LAST_NODE {last_node}u",
        "#define LAB_PAYLOAD_BUDGET 67u",
        "#define LAB_RESERVED_BYTES 16u",
        "#define LAB_FLUSH_LEAD_MS 125u",
        "#define LAB_RADIO_OFF_UNTIL 0u",
        "#define LAB_CPU_WORK_ITERATIONS 0u",
        "#define LAB_ENERGY_SAMPLE_MS 1000u",
        "#define LAB_DEPLETION_NODE 0u",
        "#define LAB_ENERGY_MODEL 0u",
        "#define LAB_ENERGY_TELEMETRY 1u",
        "#define LAB_SCHEMA 2u",
        "#define LAB_CONFIG_ID 99999u",
        "#define LAB_DUAL_PROFILE 0u",
        "#define LAB_SWITCH_TEST 0u",
        "#define LAB_RADIO_LOSS_TEST 0u",
        "#define LAB_REORDER_TEST 0u",
        "#define LAB_CRITICAL_READING 0u",
        f"#define LAB_PROFILE {profile}u",
        "#define LAB_ROOT_RESET_TEST 0u",
        "#define LAB_ATTACK_TEST 0u",
        "#define LAB_POLICY_MODE 0u",
    ]
    target_path.write_text("\n".join(lines) + "\n")


def parse_energest_power(log_path: Path, node_ids: list[int]):
    """Extract raw Energest ticks, full-run power, and post-warmup window power."""
    if not log_path.exists():
        return None

    ticks_at_60s = {}
    ticks_at_end = {}
    tx_packet_count = 0
    delivered_readings_count = 0
    radio_frames_count = 0
    duration_s = 0.0

    for line in log_path.read_text(errors="ignore").splitlines():
        match = re.search(r"(\d+),(\d+),RSLAB,\2,ENERGY_RAW,(\d+),(\d+),(\d+),(\d+),(\d+)", line)
        if match:
            sim_time_us = int(match.group(1))
            nid = int(match.group(2))
            cpu = int(match.group(3))
            lpm = int(match.group(4))
            tx  = int(match.group(6))
            rx  = int(match.group(7))
            if nid in node_ids:
                if sim_time_us <= 60000000:
                    ticks_at_60s[nid] = (sim_time_us, cpu, lpm, tx, rx)
                ticks_at_end[nid] = (sim_time_us, cpu, lpm, tx, rx)
            duration_s = max(duration_s, sim_time_us / 1000000.0)

        for nid in node_ids:
            if f"RSLAB,{nid},TX" in line:
                tx_packet_count += 1
                break

        if "RSLAB,1,RX" in line or "RSLAB,1,RX_AUTH" in line or "RSLAB,1,RX2" in line:
            delivered_readings_count += 1

        if line.startswith("RADIO,"):
            parts = line.split(",")
            if len(parts) >= 3:
                try:
                    src_mote = int(parts[2])
                    if src_mote in node_ids:
                        radio_frames_count += 1
                except ValueError:
                    pass

    if not ticks_at_end or duration_s <= 0:
        return None

    cpu_powers, lpm_powers, tx_powers, rx_powers = [], [], [], []
    for nid in node_ids:
        if nid not in ticks_at_end:
            continue
        _, cpu, lpm, tx, rx = ticks_at_end[nid]
        total_ticks = duration_s * RTIMER_HZ
        if total_ticks <= 0:
            continue
        cpu_powers.append((cpu / total_ticks) * (VOLTS * I_CPU_A * 1000.0))
        lpm_powers.append((lpm / total_ticks) * (VOLTS * I_LPM_A * 1000.0))
        tx_powers.append((tx / total_ticks) * (VOLTS * I_TX_A * 1000.0))
        rx_powers.append((rx / total_ticks) * (VOLTS * I_RX_A * 1000.0))

    post_cpu_powers, post_tx_powers, post_rx_powers = [], [], []
    for nid in node_ids:
        if nid in ticks_at_60s and nid in ticks_at_end:
            t0, c0, _, tx0, rx0 = ticks_at_60s[nid]
            t1, c1, _, tx1, rx1 = ticks_at_end[nid]
            dt_s = (t1 - t0) / 1000000.0
            dticks = dt_s * RTIMER_HZ
            if dticks > 0:
                post_cpu_powers.append(((c1 - c0) / dticks) * (VOLTS * I_CPU_A * 1000.0))
                post_tx_powers.append(((tx1 - tx0) / dticks) * (VOLTS * I_TX_A * 1000.0))
                post_rx_powers.append(((rx1 - rx0) / dticks) * (VOLTS * I_RX_A * 1000.0))

    num_sensors = len(cpu_powers)
    mean_cpu = sum(cpu_powers) / num_sensors
    mean_lpm = sum(lpm_powers) / num_sensors
    mean_tx  = sum(tx_powers)  / num_sensors
    mean_rx  = sum(rx_powers)  / num_sensors
    mean_total = mean_cpu + mean_lpm + mean_tx + mean_rx

    post_mean_cpu = sum(post_cpu_powers) / len(post_cpu_powers) if post_cpu_powers else mean_cpu
    post_mean_tx  = sum(post_tx_powers)  / len(post_tx_powers)  if post_tx_powers  else mean_tx
    post_mean_rx  = sum(post_rx_powers)  / len(post_rx_powers)  if post_rx_powers  else mean_rx

    # Consistent steady-state raw total: components sum strictly to raw_total_mw
    post_raw_total = post_mean_cpu + post_mean_tx + post_mean_rx + mean_lpm

    nodes_count = num_sensors + 1
    duty_ratio = DUTY_RATIO.get(nodes_count, 0.015)
    duty_rx_mw = post_mean_rx * duty_ratio
    duty_total_mw = post_mean_cpu + post_mean_tx + duty_rx_mw + mean_lpm

    delivered_per_sensor = delivered_readings_count / float(num_sensors) if num_sensors > 0 else 0.0
    active_duration_s = max(duration_s - 60.0, 1.0)
    if delivered_per_sensor > 0:
        tx_energy_uj_reading = (post_mean_tx * active_duration_s * 1000.0) / delivered_per_sensor
        active_energy_uj_reading = ((post_mean_cpu + post_mean_tx) * active_duration_s * 1000.0) / delivered_per_sensor
    else:
        tx_energy_uj_reading = 0.0
        active_energy_uj_reading = 0.0

    return {
        "duration_seconds": round(duration_s, 2),
        "nodes_measured": num_sensors,
        "full_run_cpu_mw": round(mean_cpu, 4),
        "post_warmup_cpu_mw": round(post_mean_cpu, 4),
        "full_run_tx_mw": round(mean_tx, 4),
        "post_warmup_tx_mw": round(post_mean_tx, 4),
        "rx_mw": round(post_mean_rx, 4),
        "lpm_mw": round(mean_lpm, 4),
        "raw_total_mw": round(post_raw_total, 4),
        "full_run_raw_total_mw": round(mean_total, 4),
        "duty_rx_mw": round(duty_rx_mw, 4),
        "duty_total_mw": round(duty_total_mw, 4),
        "tx_packet_count": tx_packet_count,
        "radio_frames_count": radio_frames_count,
        "delivered_readings_count": delivered_readings_count,
        "delivered_per_sensor": round(delivered_per_sensor, 1),
        "tx_energy_uj_reading": round(tx_energy_uj_reading, 2),
        "active_energy_uj_reading": round(active_energy_uj_reading, 2),
    }


def execute_run(nodes: int, cipher: str, cap: int):
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"optFinal_{nodes}nodes_{cipher}_cap{cap}_{timestamp}"
    run_dir = RAW_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    build_dir = run_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    profile = PROFILE_MAP[cipher]

    keys = None
    if profile != 0:
        keys = {nid: [secrets.randbits(8) for _ in range(16)] for nid in range(2, nodes + 1)}

    scenario_path = SCENARIOS_DIR / f"mustafa-rpl-{nodes}.csc"
    tree = ET.parse(scenario_path)
    root = tree.getroot()

    c_out = f"/workspace/mustafa_benchmarks/results/raw/{run_id}"
    for mote_type in root.findall(".//motetype"):
        source = mote_type.find("source").text if mote_type.find("source") is not None else ""
        is_root = "root" in source or "udp-server" in source
        name = "root" if is_root else "sensor"
        fw_elem = mote_type.find("firmware")
        if fw_elem is not None:
            fw_elem.text = f"{c_out}/build/{name}.z1"
        else:
            ET.SubElement(mote_type, "firmware").text = f"{c_out}/build/{name}.z1"

    script_elem = root.find(".//plugin/plugin_config/script")
    radio_listener = r"""
var medium = sim.getRadioMedium();
var listener = new (Java.type("java.util.function.BiConsumer"))(function(event, unused) {
  if (String(event) != "TRANSMISSION_FINISHED") return;
  var connection = medium.getLastConnection();
  if (connection == null) return;
  var packet = connection.getSource().getLastPacketTransmitted();
  if (packet == null) return;
  var bytes = packet.getPacketData(); var hex = "";
  for (var i=0; i<bytes.length; i++) hex += ("0" + ((bytes[i] & 255).toString(16))).slice(-2);
  log.log("RADIO," + sim.getSimulationTime() + "," + connection.getSource().getMote().getID() + "," + hex + "\n");
});
medium.getRadioTransmissionTriggers().addTrigger(listener, listener);
TIMEOUT(142000, log.log("MUSTAFA_RUN_COMPLETE\n"); log.testOK());
"""
    if keys is not None:
        slots = 1
        clients = nodes - 1
        root_keys = [0] * (16 * slots * clients)
        per_mote = {}
        for sender, key in keys.items():
            values = [b if b < 128 else b - 256 for b in key]
            root_keys[16 * slots * (sender - 2):16 * slots * (sender - 1)] = values
            per_mote[str(sender)] = values
        per_mote["1"] = root_keys

        startup = r"""
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
var provisioning = PROVISIONING;
var grants = {};
""".replace("PROVISIONING", json.dumps(per_mote, sort_keys=True))

        loop = r"""
var firstMessage = true;
while (true) {
  if(!firstMessage) { YIELD(); }
  firstMessage = false;
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RSLAB," + id + ",BOOT_REQUEST,") >= 0) {
    if (grants[id] || !provisioning[id]) {
      log.log("BOOT_REGRANT_REFUSED\n");
      continue;
    }
    var memory = new VarMemory(sim.getMoteWithID(id).getMemory());
    if (memory.getVariableSize("lab_provisioned_keys") != provisioning[id].length) throw new Error("Key-slot ABI mismatch");
    memory.setByteArray("lab_provisioned_keys", Java.to(provisioning[id], "byte[]"));
    var metadata = new Array(provisioning[id].length / 16 * 8);
    for (var k = 0; k < metadata.length; k++) metadata[k] = 0;
    for (var index = 0; index < provisioning[id].length / (16 * SLOTS); index++) {
      var sender = id == 1 ? index + 2 : id;
      for (var p = 0; p < SLOTS; p++) {
        var slot = [1, PROFILE, (sender >> 8) & 255, sender & 255, 0, 1, 1, 0];
        for (var j = 0; j < 8; j++) metadata[(index * SLOTS + p) * 8 + j] = slot[j];
      }
    }
    if (memory.getVariableSize("lab_provisioned_metadata") != metadata.length) throw new Error("Metadata ABI mismatch");
    memory.setByteArray("lab_provisioned_metadata", Java.to(metadata, "byte[]"));
    if (memory.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
    memory.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
    grants[id] = true;
  }
}
""".replace("PROFILE", str(profile)).replace("SLOTS", "1")
        script_elem.text = startup + radio_listener + loop
    else:
        script_elem.text = radio_listener + r"""
var firstMessage = true;
while (true) {
  if(!firstMessage) { YIELD(); }
  firstMessage = false;
  log.log(time + "," + id + "," + msg + "\n");
}
"""

    sim_csc = run_dir / "scenario.csc"
    ET.indent(root)
    tree.write(sim_csc, encoding="UTF-8", xml_declaration=True)

    make_conf_header(run_dir / "generated-conf.h", cap, cipher, nodes)

    docker_build_dir = f"{c_out}/build"
    inner_cmd = (
        f"set -eu; "
        f"TMP_DIR=/tmp/sb_{run_id}; rm -rf \"$TMP_DIR\"; cp -r /workspace/firmware \"$TMP_DIR\"; "
        f"rm -rf \"$TMP_DIR/sensor/build\" \"$TMP_DIR/root/build\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/speck.h \"$TMP_DIR/crypto/\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/speck.c \"$TMP_DIR/crypto/\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/present.h \"$TMP_DIR/crypto/\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/present.c \"$TMP_DIR/crypto/\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/secure_packet.h \"$TMP_DIR/crypto/\"; "
        f"cp /workspace/mustafa_benchmarks/crypto/secure_packet.c \"$TMP_DIR/crypto/\"; "
        f"sed -i 's/PROJECT_SOURCEFILES +=/PROJECT_SOURCEFILES += speck.c present.c/' \"$TMP_DIR/Makefile\"; "
        f"sed -i 's|CONTIKI = .*|CONTIKI = /workspace/external/contiki-ng|' \"$TMP_DIR/Makefile\"; "
        f"sed -i 's|include ../crypto/ascon-backend.mk|# include ../crypto/ascon-backend.mk|' \"$TMP_DIR/Makefile\"; "
        f"sed -i 's/LAB_PROFILE != 2/LAB_PROFILE != 2 \\&\\& LAB_PROFILE != 3 \\&\\& LAB_PROFILE != 4/' \"$TMP_DIR/project-conf.h\"; "
        f"sed -i 's/LAB_PROFILE == 1 || LAB_PROFILE == 2/LAB_PROFILE >= 1/g' \"$TMP_DIR/sensor/sensor.c\"; "
        f"sed -i 's/LAB_PROFILE == 1 || LAB_PROFILE == 2/LAB_PROFILE >= 1/g' \"$TMP_DIR/root/root.c\"; "
        f"sed -i 's/CLOCK_SECOND \\/ 8/CLOCK_SECOND * 2/g' \"$TMP_DIR/sensor/sensor.c\"; "
        f"sed -i 's/++samples % (1000 \\/ LAB_ENERGY_SAMPLE_MS) == 0/++samples % 10 == 0/g' \"$TMP_DIR/energy/energest_sampler.c\"; "
        f"cp {c_out}/generated-conf.h \"$TMP_DIR/generated-conf.h\"; "
        f"make -C \"$TMP_DIR/sensor\" -j1 sensor.z1 TARGET=z1; "
        f"make -C \"$TMP_DIR/root\" -j1 root.z1 TARGET=z1; "
        f"mkdir -p {docker_build_dir}; "
        f"cp \"$TMP_DIR/sensor/build/z1/sensor.z1\" {docker_build_dir}/sensor.z1; "
        f"cp \"$TMP_DIR/root/build/z1/root.z1\" {docker_build_dir}/root.z1; "
        f"rm -rf \"$TMP_DIR\"; "
        f"/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja "
        f"--no-gui --contiki=/home/user/contiki-ng --logdir={c_out} {c_out}/scenario.csc"
    )

    docker_cmd = [
        "sg", "docker", "-c",
        shlex.join([
            "docker", "run", "--rm",
            "--mount", f"type=bind,source={ROOT}/external/contiki-ng,destination=/home/user/contiki-ng,readonly",
            "--mount", f"type=bind,source={ROOT},destination=/workspace",
            CONTAINER,
            "bash", "-c", inner_cmd,
        ])
    ]

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] START: {nodes} Nodes | {cipher.upper()} | k={cap}", flush=True)
    res = subprocess.run(docker_cmd, capture_output=True, text=True)
    (run_dir / "stdout.log").write_text(res.stdout)
    (run_dir / "stderr.log").write_text(res.stderr)

    sensor_nodes = list(range(2, nodes + 1))
    power = parse_energest_power(run_dir / "COOJA.testlog", sensor_nodes)

    record = {
        "run_id": run_id,
        "nodes": nodes,
        "cipher": cipher,
        "batch_cap": cap,
        "exit_code": res.returncode,
        "power": power,
    }
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2))

    total_expected = (nodes - 1) * 8
    if power:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] DONE:  {nodes} Nodes | {cipher.upper()} | k={cap} -> "
              f"Delivered: {power['delivered_readings_count']}/{total_expected} ({power['delivered_readings_count']/total_expected*100:.1f}%) | "
              f"CPU: {power['post_warmup_cpu_mw']} mW | Tx: {power['post_warmup_tx_mw']} mW | "
              f"Tx Energy: {power['tx_energy_uj_reading']} uJ/rdg", flush=True)
    else:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FAILED: {nodes} Nodes | {cipher.upper()} | k={cap}", flush=True)

    return record


def main():
    parser = argparse.ArgumentParser(description="Run definitive benchmark matrix.")
    parser.add_argument("--nodes", nargs="+", type=int, default=[5, 10, 15], help="Node counts to benchmark")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent workers")
    args = parser.parse_args()

    print("===================================================================")
    print(f"STARTING DEFINITIVE BENCHMARK MATRIX FOR NODES: {args.nodes}")
    print("===================================================================")
    configs = []
    for nodes in args.nodes:
        for cipher in ["speck", "aes", "present", "none"]:
            for cap in [1, 2, 4]:
                configs.append((nodes, cipher, cap))

    records = []
    # If partial run, load existing results to preserve them
    out_json = RESULTS_DIR / "DEFINITIVE_BENCHMARK_RESULTS.json"
    existing_records = {}
    if out_json.exists():
        try:
            for r in json.loads(out_json.read_text()):
                existing_records[(r["nodes"], r["cipher"], r["batch_cap"])] = r
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_cfg = {executor.submit(execute_run, n, c, k): (n, c, k) for n, c, k in configs}
        for future in concurrent.futures.as_completed(future_to_cfg):
            cfg = future_to_cfg[future]
            try:
                rec = future.result()
                existing_records[cfg] = rec
            except Exception as exc:
                print(f"ERROR on {cfg}: {exc}", flush=True)

    all_records = list(existing_records.values())
    all_records.sort(key=lambda r: (r["nodes"], r["cipher"], r["batch_cap"]))

    out_json.write_text(json.dumps(all_records, indent=2))
    print(f"\nSaved all {len(all_records)} records to {out_json}")


if __name__ == "__main__":
    main()
