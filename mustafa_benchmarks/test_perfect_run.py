import sys
import os
import subprocess
import json
import secrets
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/home/yatin_04/adaptiveAlpha_IOT")
BENCHMARK_DIR = ROOT / "mustafa_benchmarks"
sys.path.insert(0, str(BENCHMARK_DIR))

import run_mustafa_experiments as rme

run_id = "test_perfect_5nodes_speck_cap4"
run_dir = ROOT / "mustafa_benchmarks/results/raw" / run_id
run_dir.mkdir(parents=True, exist_ok=True)
build_dir = run_dir / "build"
build_dir.mkdir(parents=True, exist_ok=True)

# 8 readings, 10s interval, 142s simulation
conf_lines = [
    "/* Perfect Benchmark Test */",
    "#define LAB_BATCH_CAP 4u",
    "#define LAB_DEADLINE_MS 35000u",
    "#define LAB_PERIOD_MS 10000u",
    "#define LAB_WARMUP_MS 60000u",
    "#define LAB_TOTAL_READINGS 8u",
    "#define LAB_LAST_NODE 5u",
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
    "#define LAB_PROFILE 3u",  # Speck
    "#define LAB_ROOT_RESET_TEST 0u",
    "#define LAB_ATTACK_TEST 0u",
    "#define LAB_POLICY_MODE 0u",
]
(run_dir / "generated-conf.h").write_text("\n".join(conf_lines) + "\n")

scenario_path = ROOT / "mustafa_benchmarks/scenarios/mustafa-rpl-5.csc"
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

keys = {nid: [secrets.randbits(8) for _ in range(16)] for nid in range(2, 6)}
slots = 1
clients = 4
root_keys = [0] * (16 * slots * clients)
per_mote = {}
for sender, key in keys.items():
    values = [b if b < 128 else b - 256 for b in key]
    root_keys[16 * slots * (sender - 2):16 * slots * (sender - 1)] = values
    per_mote[str(sender)] = values
per_mote["1"] = root_keys

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
        var slot = [1, 3, (sender >> 8) & 255, sender & 255, 0, 1, 1, 0];
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
""".replace("SLOTS", "1")
script_elem.text = startup + radio_listener + loop

sim_csc = run_dir / "scenario.csc"
ET.indent(root)
tree.write(sim_csc, encoding="UTF-8", xml_declaration=True)

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

import shlex
docker_cmd = [
    "sg", "docker", "-c",
    shlex.join([
        "docker", "run", "--rm",
        "--mount", f"type=bind,source={ROOT}/external/contiki-ng,destination=/home/user/contiki-ng,readonly",
        "--mount", f"type=bind,source={ROOT},destination=/workspace",
        rme.CONTAINER,
        "bash", "-c", inner_cmd,
    ])
]

print("Executing test...", flush=True)
res = subprocess.run(docker_cmd, capture_output=True, text=True)
(run_dir / "stdout.log").write_text(res.stdout)
(run_dir / "stderr.log").write_text(res.stderr)

import run_option_a_all as roa
power = roa.parse_energest_power(run_dir / "COOJA.testlog", [2, 3, 4, 5])
print("Result power:", json.dumps(power, indent=2))
