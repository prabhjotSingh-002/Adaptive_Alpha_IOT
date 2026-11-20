#!/usr/bin/env python3
"""Phase 2 config-driven Cooja runs; evidence retained for failed runs too."""
import argparse
import fcntl
import datetime
import hashlib
import json
import shlex
import secrets
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from policy_validation import validate_policy_config
from demand_schedule import run_horizon_ms
from parse_logs import parse
from metrics import summarize
from scenario_target import configure_z1
from topologies import configure_layout, validate_layout

PROJECT = Path(__file__).resolve().parents[1]
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def container_command(pins, args, container_name=None):
    command = ["docker", "run", "--rm"]
    if container_name: command.extend(["--name", container_name])
    command += ["--mount", f"type=bind,source={PROJECT / 'external/contiki-ng'},destination=/home/user/contiki-ng", "--mount", f"type=bind,source={PROJECT},destination=/workspace", pins["container_image"], *args]
    return ["sg", "docker", "-c", shlex.join(command)]


def scenario(out, clients, config, keys=None):
    tree = ET.parse(PROJECT / "simulations/scenarios/phase1-rpl-9.csc")
    root = tree.getroot(); simulation = root.find("simulation")
    simulation.find("randomseed").text = str(config["seed"])
    configure_layout(simulation, clients, config.get("topology", "legacy"))
    target = config.get("target", "cooja")
    backend = config.get("backend", "ref")
    for mote_type in simulation.findall("motetype"):
        name = "root" if "udp-server" in mote_type.find("source").text else "sensor"
        mote_type.find("source").text = f"/workspace/firmware/{name}/{name}.c"
        mote_type.find("commands").text = f"make -j1 {name}.{target} TARGET={target} ASCON_IMPL={backend}"
    if config.get("bottleneck"):
        for mote in simulation.findall("mote"):
            for interface in mote.findall("interface_config"):
                if "Position" in (interface.text or ""):
                    index = list(simulation.findall("mote")).index(mote)
                    interface.find("x").text = str(index*40)
                    interface.find("y").text = "0"
    if target == "z1": configure_z1(simulation)
    script = root.find("plugin/plugin_config/script")
    end = run_horizon_ms(config)
    script.text = r'''
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
TIMEOUT(END_MS, log.log("PHASE2_COMPLETE\n"); log.testOK());
while (true) { YIELD(); log.log(time + "," + id + "," + msg + "\n"); }
'''.replace("END_MS", str(end))
    if config.get("phase") in (4, 5):
        script.text = script.text.replace("PHASE2_COMPLETE", "PHASE4_SCHEMA2_COMPLETE")
    if keys is not None:
        slots = 2 if config.get("dual_profile") else 1
        root_keys = [0] * (16 * slots * clients)
        per_mote = {}
        for sender, key in keys.items():
            values = [b if b < 128 else b - 256 for b in key]
            root_keys[16 * slots * (sender - 2):16 * slots * (sender - 1)] = values
            one = values
            per_mote[str(sender)] = one
        per_mote["1"] = root_keys
        startup = r"""
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
var provisioning = PROVISIONING;
var grants = {};
var rootReplaced = false;
var sensorReplaced = false;
var lossActive = false;
var originalTxRatio = sim.getRadioMedium().SUCCESS_RATIO_TX;
"""
        startup = startup.replace("PROVISIONING", json.dumps(per_mote, sort_keys=True))
        script.text = startup + script.text.replace(
            r'while (true) { YIELD(); log.log(time + "," + id + "," + msg + "\n"); }',
            r'''var firstMessage = true;
while (true) {
  if(!firstMessage) { YIELD(); }
  firstMessage = false;
  if (msg == "LOSS_RESTORE") {
    sim.getRadioMedium().SUCCESS_RATIO_TX = originalTxRatio;
    lossActive=false; log.log(time + ",2,RSLAB,2,LOSS,0\n"); continue;
  }
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RSLAB,2,LOSS,1") >= 0) {
    if(lossActive) log.testFailed();
    lossActive=true; sim.getRadioMedium().SUCCESS_RATIO_TX=0;
    GENERATE_MSG(750,"LOSS_RESTORE");
  }
  if (SENSOR_RESET_TEST && id == 1 && !sensorReplaced && msg.indexOf("RSLAB,1,RX2,2,") >= 0) {
    sensorReplaced=true;
    var previous=sim.getMoteWithID(2); var conf=previous.getConfigXML();
    var fresh=previous.getType().generateMote(sim);
    if(!fresh.setConfigXML(sim,conf,false)) log.testFailed();
    sim.removeMote(previous); sim.addMote(fresh); continue;
  }
  if (msg.indexOf("RSLAB," + id + ",DEPLETED,") >= 0) {
    if (id == 1) log.testFailed();
    sim.removeMote(sim.getMoteWithID(id));
    log.log(time + "," + id + ",RSLAB," + id + ",REMOVED,1\n");
    continue;
  }
  if (msg.indexOf("RSLAB," + id + ",BOOT_REQUEST,") >= 0) {
    if (grants[id] || !provisioning[id]) {
      log.log("BOOT_REGRANT_REFUSED\n");
      if (!(ROOT_RESET_TEST && id == 1 && rootReplaced) && !(SENSOR_RESET_TEST && id==2 && sensorReplaced)) log.testFailed();
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
        var slot = [1, SLOTS == 2 ? p + 1 : PROFILE, (sender >> 8) & 255, sender & 255, 0, 1, 1, 0];
        for (var j = 0; j < 8; j++) metadata[(index * SLOTS + p) * 8 + j] = slot[j];
      }
    }
    if (id == 1 && PROVISION_FAULT != "none") {
      var at=metadata.length-8;
      if(PROVISION_FAULT=="missing") metadata[at+6]=0;
      if(PROVISION_FAULT=="version") metadata[at]=0;
      if(PROVISION_FAULT=="profile") metadata[at+1]=255;
      if(PROVISION_FAULT=="epoch") metadata[at+5]=2;
    }
    if (memory.getVariableSize("lab_provisioned_metadata") != metadata.length) throw new Error("Metadata ABI mismatch");
    memory.setByteArray("lab_provisioned_metadata", Java.to(metadata, "byte[]"));
    if (memory.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
    memory.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
    grants[id] = true;
  }
  if (ROOT_RESET_TEST && id == 1 && !rootReplaced && (msg.indexOf("RSLAB,1,RX_AUTH,") >= 0 || msg.indexOf("RSLAB,1,RX2,") >= 0)) {
    rootReplaced = true;
    var previous = sim.getMoteWithID(1);
    var conf = previous.getConfigXML();
    var fresh = previous.getType().generateMote(sim);
    if (!fresh.setConfigXML(sim, conf, false)) log.testFailed();
    sim.removeMote(previous);
    sim.addMote(fresh);
    log.log("ROOT_MOTE_REPLACED\n");
  }
}''')
    if keys is not None:
        script.text = script.text.replace("PROFILE", str(config["profile"]))
        script.text = script.text.replace("SLOTS", str(slots))
        script.text = script.text.replace("SENSOR_RESET_TEST", "true" if config.get("sensor_reset_test") else "false")
        script.text = script.text.replace("PROVISION_FAULT", json.dumps(config.get("provision_fault") or "none"))
        script.text = script.text.replace("ROOT_RESET_TEST", "true" if config.get("root_reset_test") else "false")
    if keys is None:
        script.text = script.text.replace('while (true) { YIELD();', 'var firstMessage = true; while (true) { if(!firstMessage) { YIELD(); } firstMessage = false;')
    if config.get("gui_mode"):
        visual_plugins = """<plugins>
  <plugin>
    org.contikios.cooja.plugins.SimControl
    <width>280</width>
    <z>3</z>
    <height>160</height>
    <location_x>420</location_x>
    <location_y>0</location_y>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.Visualizer
    <plugin_config>
      <moterelations>true</moterelations>
      <skin>org.contikios.cooja.plugins.skins.IDVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.GridVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.TrafficVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.UDGMVisualizerSkin</skin>
      <viewport>1.5 0.0 0.0 1.5 50.0 50.0</viewport>
    </plugin_config>
    <width>400</width>
    <z>2</z>
    <height>400</height>
    <location_x>1</location_x>
    <location_y>1</location_y>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.LogListener
    <plugin_config>
      <filter />
      <formatted_time />
      <coloring />
    </plugin_config>
    <width>700</width>
    <z>1</z>
    <height>300</height>
    <location_x>420</location_x>
    <location_y>165</location_y>
  </plugin>
</plugins>"""
        for p in ET.fromstring(visual_plugins):
            root.append(p)
    ET.indent(root); tree.write(out, encoding="UTF-8", xml_declaration=True)

def run(mode, clients, base, pins, override):
    config = dict(base); config.update(override)
    config["mode"] = mode
    validate_policy_config(config)
    cap = config.get("calibration_cap", config["modes"][mode])
    if "mode_profiles" in config: config["profile"] = config["mode_profiles"][mode]
    if config.get("phase") == 4 and not config.get("calibration_cap") and (config.get("profile"),cap) != {"B1":(1,1),"B2":(2,1),"B4":(1,4),"B5":(2,4)}.get(mode): raise ValueError("Invalid Phase4 control mapping")
    if config.get("phase") == 5 and mode not in ("B1","B2","B3","B4","B5","B6","P1"): raise ValueError("Invalid Phase5 mode")
    if config.get("profile", 0) not in (0, 1, 2): raise ValueError("Unsupported profile")
    for name in ("seed", "warmup_ms", "period_ms", "readings_per_sensor", "deadline_ms", "drain_ms", "payload_budget", "reserved_bytes"):
        if type(config[name]) is not int or config[name] < 0: raise ValueError("Invalid config " + name)
    validate_layout(clients, config.get("topology", "legacy"), config.get("target", "cooja"), config.get("bottleneck", False))
    if not 1 <= clients <= 15 or type(cap) is not int or cap not in (1, 2, 4) or not 1 <= config["readings_per_sensor"] <= 1000 or config["period_ms"] < 125 or config["period_ms"] % 125 or config["deadline_ms"] % 125 or config["deadline_ms"] > 2**31-1:
        raise ValueError("Unsupported pilot dimensions or timer resolution")
    if run_horizon_ms(config) >= 2**31 or config["payload_budget"] > 65535:
        raise ValueError("Pilot horizon/budget exceeds bounded representation")
    fit = (config["payload_budget"] - config["reserved_bytes"] - 11) // 10
    if fit < 1: raise ValueError("Payload cannot fit a reading")
    effective_cap = min(cap, fit)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + f"-{mode}-{clients}"
    target = config.get("target", "cooja")
    backend = config.get("backend", "ref")
    if target not in ("cooja", "z1") or backend not in ("ref", "opt32_lowsize"): raise ValueError("Unsupported target/backend")
    if target == "z1" and backend != "ref": raise ValueError("Z1 optimized backend has not passed mote validation")
    phase = config.get("phase", 3 if config.get("profile") == 1 else 2)
    out = PROJECT / f"results/phase_0{phase}" / run_id; out.mkdir(parents=True)
    (out/"manifest.json").write_text(json.dumps({"status":"preparing","run_id":run_id,"mode":mode,"config":config},indent=2)+"\n")
    global preparing_output
    preparing_output = out
    c_out = "/workspace/" + out.relative_to(PROJECT).as_posix()
    defs = {"BATCH_CAP": cap, "DEADLINE_MS": config["deadline_ms"], "PERIOD_MS": config["period_ms"], "WARMUP_MS": config["warmup_ms"], "TOTAL_READINGS": config["readings_per_sensor"], "LAST_NODE": clients+1, "PAYLOAD_BUDGET": config["payload_budget"], "RESERVED_BYTES": config["reserved_bytes"]}
    config["schema_version"] = 2 if config.get("phase") in (4, 5) else 1
    config["config_id"] = int(hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:8], 16)
    defs["FLUSH_LEAD_MS"] = config.get("flush_lead_ms",0)
    defs["RADIO_OFF_UNTIL"] = config.get("radio_off_until_ms",0)
    defs["CPU_WORK_ITERATIONS"] = config.get("cpu_work_iterations",0)
    defs["ENERGY_SAMPLE_MS"] = config.get("energy_sample_ms",125)
    defs["DEPLETION_NODE"] = config.get("deplete_node",0)
    defs["ENERGY_MODEL"] = config.get("power_model",{}).get("id",0)
    if config.get("power_model"):
        model=config["power_model"]
        defs["POWER_MV"] = model["millivolts"]
        for name,index in [("CPU",0),("LPM",1),("TX",3),("LISTEN",4)]: defs["POWER_"+name]=model["nanoamps"][index]
        defs["ENERGY_BUDGET"] = str(config["energy_budget_nj"])+"ULL"
    defs["ENERGY_TELEMETRY"] = int(bool(config.get("energy_telemetry")))
    defs["SCHEMA"] = config["schema_version"]
    if "middle_period_ms" in config:
        defs["MIDDLE_PERIOD_MS"] = config["middle_period_ms"]
    defs["CONFIG_ID"] = config["config_id"]
    defs["DUAL_PROFILE"] = int(bool(config.get("dual_profile")))
    if config.get("queued_shrink"):
        defs["QUEUED_SHRINK"] = {"hold": 1, "switch": 2}[config["queued_shrink"]]
    defs["SWITCH_TEST"] = int(bool(config.get("switch_test")))
    defs["RADIO_LOSS_TEST"] = int(bool(config.get("radio_loss_test")))
    defs["REORDER_TEST"] = int(bool(config.get("reorder_test")))
    defs["CRITICAL_READING"] = config.get("critical_reading",0)
    defs["PROFILE"] = config.get("profile", 0)
    defs["ROOT_RESET_TEST"] = config.get("root_reset_test", 0)
    defs["ATTACK_TEST"] = config.get("attack_test", 0)
    # Phase 5 policy defs
    policy_map = config.get("mode_policy", {})
    defs["POLICY_MODE"] = policy_map.get(mode, 0)
    defs["B3_THRESHOLD_NJ_HI"] = str(config.get("b3_threshold_nj_hi", 0)) + "ULL"
    defs["B3_THRESHOLD_NJ_LO"] = str(config.get("b3_threshold_nj_lo", 0)) + "ULL"
    defs["B6_PROFILE"] = config.get("b6_profile", 1)
    defs["P1_TRANSITION_COST_NJ"] = str(config.get("p1_transition_cost_nj", 0)) + "ULL"
    defs["P1_MIN_DWELL_MS"] = config.get("p1_min_dwell_ms", 0)
    defs["P1_MARGIN_NJ"] = str(config.get("p1_margin_nj", 0)) + "ULL"
    costs = config.get("p1_cost_nj", [[0,0,0],[0,0,0]])
    if (not isinstance(costs,list) or len(costs)!=2 or
        any(not isinstance(row,list) or len(row)!=3 or any(type(v) is not int or not 0<=v<=2**64-1 for v in row) for row in costs)):
        raise ValueError("Invalid policy cost table")
    defs["P1_COSTS"] = "{" + ",".join("{" + ",".join(str(v)+"ULL" for v in row) + "}" for row in costs) + "}"

    (PROJECT / "firmware/generated-conf.h").write_text("/* Generated from the resolved experiment config. */\n" + "".join(f"#define LAB_{name} {value if isinstance(value,str) else str(value)+'u'}\n" for name, value in defs.items()))
    keys = {node: secrets.token_bytes(32 if config.get("dual_profile") else 16) for node in range(2, clients + 2)} if config.get("profile") in (1, 2) else None
    if keys is not None:
        (out / "test-keys.json").write_text(json.dumps({"purpose": "public simulation-only test keys", "keys": {str(k): v.hex() for k, v in keys.items()}}, indent=2) + "\n")
    shutil.copy2(PROJECT / "firmware/generated-conf.h", out / "generated-conf.h")
    if config.get("power_model"): shutil.copy2(PROJECT/"configs/power-z1-v1.json",out/"power-model.json")
    scenario(out / "scenario.csc", clients, config, keys)
    sources = sorted(p for folder in ("firmware", "host") for p in (PROJECT / folder).rglob("*") if p.is_file() and (p.suffix in (".c", ".h", ".py") or p.name == "Makefile" or p.suffix == ".mk") and "build" not in p.parts)
    git_result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=PROJECT, capture_output=True, text=True)
    git_sha = git_result.stdout.strip() if git_result.returncode == 0 else None
    manifest = {"schema_version": config["schema_version"], "run_id": run_id, "mode": mode, "status": "running", "security": {0: "unprotected", 1: "AES-128-CCM", 2: "Ascon-AEAD128"}[config.get("profile", 0)], "pins": pins, "config": config, "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(), "config_file_sha256": digest(PROJECT / f"configs/phase{phase}.json"), "clients": clients, "effective_cap": effective_cap, "scenario_sha256": digest(out / "scenario.csc"), "source_hashes": {str(p.relative_to(PROJECT)): digest(p) for p in sources}, "git_sha": git_sha, "working_tree": "uncommitted source hashes authoritative", "python": sys.version, "platform": target, "backend": backend, "build_flags": f"TARGET={target} ASCON_IMPL={backend} AES_128_CONF=aes_128_driver -j1", "master_sha256": digest(PROJECT / "PLANS/MASTER_IMPLEMENTATION_PLAN.md")}
    if config.get("power_model"):
        manifest["power_model_file_sha256"] = digest(PROJECT/"configs/power-z1-v1.json")
        manifest["power_source_pdf_sha256"] = {name:digest(PROJECT/"results/phase_04"/name) for name in ("msp430f2617-SLAS541M.pdf","cc2420-SWRS041C.pdf")}
    if phase in (4, 5):
        manifest["dependency_hashes"] = {str(p.relative_to(PROJECT)): digest(p) for p in [PROJECT / "external/ascon-c/LICENSE", PROJECT / "external/ascon-c/crypto_aead/asconaead128/LWC_AEAD_KAT_128_128.txt", *sorted((PROJECT / "external/ascon-c/crypto_aead/asconaead128" / backend).glob("*.[ch]"))]}
    if phase in (4, 5):
        for relative in ("os/lib/aes-128.c","os/lib/aes-128.h","os/lib/ccm-star.c","os/lib/ccm-star.h"):
            path=PROJECT/"external/contiki-ng"/relative
            manifest["dependency_hashes"][str(path.relative_to(PROJECT))]=digest(path)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    # The host reconciliation binary links exactly the production energy C.
    energy_build = f"gcc -std=c11 -Wall -Wextra -Werror -Ifirmware/energy firmware/energy/energy.c host/energy_reconcile.c -o {c_out}/energy_reconcile; " if config.get("power_model") else ""
    # Build dirs are generated artifacts; clean to avoid stale compile-time mode.
    shell = f"set -eu; cd /workspace; {energy_build}cd firmware/sensor; make TARGET={target} clean; cd ../root; make TARGET={target} clean; touch {c_out}/build-clean-complete; /home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja --no-gui --contiki=/home/user/contiki-ng --logdir={c_out} {c_out}/scenario.csc"
    gui_shell = f"set -eu; cd /workspace; {energy_build}cd firmware/sensor; make TARGET={target} clean; cd ../root; make TARGET={target} clean; touch {c_out}/build-clean-complete; /home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja --contiki=/home/user/contiki-ng {c_out}/scenario.csc"
    container_name = "adaptivealpha-" + run_id.lower()
    command = container_command(pins, ["bash", "-c", shell], container_name); manifest["command"] = command
    manifest["container_name"] = container_name
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    # GUI mode: compile firmware then open Cooja with GUI window; results are NOT auto-parsed.
    if config.get("gui_mode"):
        import os as _os
        display = _os.environ.get("DISPLAY", ":0")
        x11_sock = "/tmp/.X11-unix"
        # Build the Docker command with X11 forwarding injected
        gui_docker_args = [
            "docker", "run", "--rm",
            "--name", container_name,
            "-e", f"DISPLAY={display}",
            "-e", "_JAVA_AWT_WM_NONREPARENTING=1",
            "-e", "AWT_TOOLKIT=XToolkit",
            "-e", "JAVA_TOOL_OPTIONS=-Dsun.java2d.opengl=false -Dsun.java2d.xrender=false",
            "-v", f"{x11_sock}:{x11_sock}",
            "--mount", f"type=bind,source={PROJECT / 'external/contiki-ng'},destination=/home/user/contiki-ng",
            "--mount", f"type=bind,source={PROJECT},destination=/workspace",
            pins["container_image"],
            "bash", "-c", gui_shell,
        ]
        gui_command = ["sg", "docker", "-c", shlex.join(gui_docker_args)]
        manifest["gui_command"] = gui_command
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        print(f"[GUI] Compiling firmware and opening Cooja GUI window ...", flush=True)
        print(f"[GUI] Scenario: {out / 'scenario.csc'}", flush=True)
        print(f"[GUI] DISPLAY={display}  — close the Cooja window when done.", flush=True)
        print(f"[GUI] NOTE: results are not parsed in GUI mode.", flush=True)
        subprocess.run(gui_command, check=True)
        manifest["status"] = "gui_session"
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        print(f"gui_session {out}", flush=True)
        return out
    interrupted = None
    try:
        with (out / "console.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=config.get("host_timeout_s", 900))
        manifest["exit_code"] = result.returncode
        if result.returncode: raise RuntimeError("Cooja/build failed; inspect console.log")
        events, frames = parse(out / "COOJA.testlog", run_id, profile=config.get("profile", 0), phase=phase, schema=config["schema_version"])
        if config.get("power_model"):
            from energy_reconcile import reconcile
            energy_result = reconcile(events,config,out/"energy_reconcile",list(range(1,clients+2)))
            manifest["energy_reconciliation"] = energy_result
        analysis_config = dict(config)
        if config.get("power_model"): analysis_config["energy_reconciliation"] = energy_result
        summary = summarize(events, frames, analysis_config, list(range(2, clients+2)), effective_cap)
        if not frames or summary["radio"]["unclassified_data_frames"]: raise ValueError("Radio capture incomplete/unsupported")
        if summary["radio"]["fragment_frames"]: raise ValueError("Unexpected fragmentation in this small-packet pilot")
        from mechanism_checks import policy_wire, root_reset, depletion
        mechanism = {}
        if phase == 5 and config.get('policy_repair_version',0) >= 2:
            mechanism['policy_wire'] = policy_wire(events, config)
        if config.get('root_reset_test'):
            mechanism['root_reset'] = root_reset(events)
            raw_text = (out/'COOJA.testlog').read_text()
            if 'ROOT_MOTE_REPLACED' not in raw_text or 'BOOT_REGRANT_REFUSED' not in raw_text:
                raise ValueError('Missing actual root replacement/regrant refusal markers')
        if config.get('lifetime'):
            mechanism['depletion'] = depletion(events, frames, config, energy_result)
        if mechanism:
            (out/'mechanism-checks.json').write_text(json.dumps(mechanism,indent=2)+'\n')
            summary['mechanism_checks'] = mechanism
        (out / "events.jsonl").write_text("".join(json.dumps(e)+"\n" for e in events))
        (out / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
        manifest["status"] = "passed"
    except BaseException as exc:
        manifest["status"] = "failed"; manifest["error"] = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, (subprocess.TimeoutExpired, KeyboardInterrupt)):
            stop_command = ["sg", "docker", "-c", shlex.join(["docker", "stop", "--time", "5", container_name])]
            try:
                stopped = subprocess.run(stop_command, capture_output=True, text=True, timeout=20)
                manifest["container_cleanup"] = {"command": stop_command, "exit_code": stopped.returncode,
                                                 "stdout": stopped.stdout, "stderr": stopped.stderr}
            except Exception as cleanup_error:
                manifest["container_cleanup"] = {"command": stop_command, "error": str(cleanup_error)}
        if isinstance(exc, (KeyboardInterrupt, SystemExit)): interrupted = exc
    binary_dir = out / "binaries"
    for name in (("sensor", "root") if (out / "build-clean-complete").exists() else ()):
        for binary in (PROJECT / f"firmware/{name}/build/{target}").glob(f"*.{target}"):
            binary_dir.mkdir(exist_ok=True)
            shutil.copy2(binary, binary_dir / f"{name}-{binary.name}")
    manifest["binary_hashes"] = {str(p.relative_to(out)): digest(p) for p in binary_dir.glob(f"*.{target}")} if binary_dir.exists() else {}
    manifest["artifact_hashes"] = {p.name: digest(p) for p in out.iterdir() if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(manifest["status"], out, manifest.get("error", ""), flush=True)
    if interrupted is not None: raise interrupted
    if manifest["status"] != "passed": raise RuntimeError(manifest.get("error", "failed"))
    return out

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--phase", type=int, choices=[2, 3, 4, 5], default=2); parser.add_argument("--mode", choices=["N0-single", "N0-batch", "B1", "B2", "B3", "B4", "B5", "B6", "P1", "both", "all", "all5"], default="both"); parser.add_argument("--clients", type=int, default=8); parser.add_argument("--timeout-seconds", type=int, default=900); parser.add_argument("--attack-test", action="store_true"); parser.add_argument("--root-reset-test", action="store_true"); parser.add_argument("--gui", action="store_true", help="Open Cooja GUI instead of running headless (for visual inspection; results not logged to file)"); parser.add_argument("--radio-off-until-ms", type=int, default=0); parser.add_argument("--cpu-work-iterations", type=int, default=0); parser.add_argument("--radio-loss-test", action="store_true"); parser.add_argument("--reorder-test", action="store_true"); parser.add_argument("--sensor-reset-test", action="store_true"); parser.add_argument("--provision-fault", choices=["missing","version","profile","epoch"]); parser.add_argument("--critical-reading", type=int, default=0); parser.add_argument("--power-model", action="store_true"); parser.add_argument("--energy-budget-nj", type=int); parser.add_argument("--deplete-node", type=int, default=0); parser.add_argument("--bottleneck", action="store_true"); parser.add_argument("--energy-sample-ms", type=int, choices=[125,250,500], default=125); parser.add_argument("--energy-telemetry", action="store_true"); parser.add_argument("--warmup-ms", type=int); parser.add_argument("--switch-test", action="store_true"); parser.add_argument("--readings", type=int); parser.add_argument("--seed", type=int); parser.add_argument("--target", choices=["cooja", "z1"], default="cooja"); parser.add_argument("--backend", choices=["ref", "opt32_lowsize"], default="ref"); parser.add_argument("--period-ms", type=int); parser.add_argument("--payload-budget", type=int)
    parser.add_argument("--topology", choices=["legacy", "grid16", "tree16"], default="legacy")
    parser.add_argument('--middle-period-ms', type=int, help='Generation interval during the middle third of a Z1 workload')
    parser.add_argument('--calibration-cap', type=int, choices=[1,2,4])
    parser.add_argument('--preflight-only', action='store_true', help='Validate resolved runtime/table compatibility without building or simulating')
    parser.add_argument('--require-qualified-policy', action='store_true')
    parser.add_argument('--allow-unqualified-policy', action='store_true', help='Explicit functional diagnostic only')
    parser.add_argument("--policy-cost-table", type=Path)
    parser.add_argument("--queued-shrink", choices=("hold", "switch"))
    args = parser.parse_args(); base = json.loads((PROJECT / f"configs/phase{args.phase}.json").read_text()); pins = json.loads((PROJECT / "results/setup/source-pins.json").read_text())
    if args.calibration_cap is not None:
        if args.phase != 4 or args.mode not in ('B1','B2') or not args.power_model or args.target != 'z1':
            parser.error('Calibration cap requires static Phase 4 B1/B2 Z1 power-model run')
        base['calibration_cap'] = args.calibration_cap
    if args.phase == 5:
        base["policy_repair_version"] = 2
        base["policy_scope"] = "cost-aware with measured eight-interval traffic; residual-aware P1 ranking unvalidated"
        base["policy_calibration_status"] = "unavailable_fallback_or_configured_default"
        if args.policy_cost_table:
            table = json.loads(args.policy_cost_table.read_text())
            if table.get("source_seed_filter") != base["calibration_seed"] or not table.get("source_records"):
                parser.error("Cost table must contain isolated calibration seed and source lineage")
            if (args.seed if args.seed is not None else base["seed"]) == table["source_seed_filter"]:
                parser.error("Evaluation seed overlaps calibration")
            for record in table['source_records']:
                rid = record.get('run_id', '')
                if Path(rid).name != rid or not rid:
                    parser.error('Invalid calibration run ID')
                directory = PROJECT / 'results/phase_04' / rid
                for name in ('manifest','summary'):
                    if digest(directory / (name+'.json')) != record.get(name+'_sha256'):
                        parser.error('Calibration source hash mismatch')
                source = json.loads((directory/'manifest.json').read_text())
                if source.get('status') != 'passed' or source.get('config',{}).get('seed') != table['source_seed_filter']:
                    parser.error('Unqualified calibration source')
            base['policy_calibration_status'] = 'source_hashes_verified_target_compatibility_pending'
            base["p1_cost_nj"] = table["p1_cost_nj"]
            base["b6_profile"] = table["b6_profile"]
            base["policy_cost_sha256"] = digest(args.policy_cost_table)
    elif args.policy_cost_table:
        parser.error("Policy costs require Phase 5")
    if args.phase in (4, 5):
        ascon_pin = "446347f21b209f3921c65ece70027c366cbe1693"
        if subprocess.check_output(["git", "-C", str(PROJECT/"external/ascon-c"), "rev-parse", "HEAD"],text=True).strip() != ascon_pin: raise ValueError("Ascon pin mismatch")
        if subprocess.check_output(["git", "-C", str(PROJECT/"external/ascon-c"), "status", "--porcelain"],text=True).strip(): raise ValueError("Ascon checkout is modified")
        pins["ascon_commit"] = ascon_pin
    for path,key in [("external/contiki-ng", "contiki_ng_commit"), ("external/contiki-ng/tools/cooja", "cooja_commit")]:
        if subprocess.check_output(["git", "-C", str(PROJECT/path), "rev-parse", "HEAD"],text=True).strip() != pins[key]: raise ValueError("Source pin mismatch")
    if args.mode not in ("both", "all") and args.mode not in base["modes"]: parser.error("mode does not belong to selected phase")
    if args.timeout_seconds < 1: parser.error("timeout must be positive")
    base["phase"] = args.phase
    base["capture_contract"] = "initial_log_event_included_v2"
    base["radio_off_until_ms"] = args.radio_off_until_ms
    base["cpu_work_iterations"] = args.cpu_work_iterations
    if not 0<=args.radio_off_until_ms<60000 or not 0<=args.cpu_work_iterations<=10000: parser.error("invalid controlled energy workload")
    if (args.radio_off_until_ms or args.cpu_work_iterations) and not args.power_model: parser.error("workload requires model instrumentation")
    base["radio_loss_test"] = args.radio_loss_test
    base["reorder_test"] = args.reorder_test
    base["sensor_reset_test"] = args.sensor_reset_test
    base["provision_fault"] = args.provision_fault
    tests=sum(bool(x) for x in (args.radio_loss_test,args.reorder_test,args.sensor_reset_test,args.provision_fault,args.switch_test,args.attack_test,args.root_reset_test))
    if tests>1: parser.error("select one dedicated fixture")
    if any((args.radio_loss_test,args.reorder_test,args.sensor_reset_test,args.provision_fault)) and (args.phase!=4 or args.mode not in ("B1","B2")):
        parser.error("fixture requires Phase4 B1/B2")
    if args.power_model and (tests or args.critical_reading): parser.error("measurement controls cannot include security fixture hooks")
    base["critical_reading"] = args.critical_reading
    if args.critical_reading and (args.phase != 4 or args.mode not in ("B4","B5") or not 1 <= args.critical_reading <= (args.readings or base["readings_per_sensor"])):
        parser.error("critical fixture requires Phase4 B4/B5 and a valid reading")
    base["energy_telemetry"] = args.energy_telemetry or args.power_model
    base["energy_sample_ms"] = args.energy_sample_ms
    base["deplete_node"] = args.deplete_node
    base["bottleneck"] = args.bottleneck
    base["topology"] = args.topology
    validate_layout(args.clients, args.topology, args.target, args.bottleneck)
    if args.power_model:
        base["power_model"] = json.loads((PROJECT/"configs/power-z1-v1.json").read_text())
        base["energy_budget_nj"] = args.energy_budget_nj if args.energy_budget_nj is not None else 2**64-1
        if not 0 < base["energy_budget_nj"] <= 2**64-1: parser.error("invalid energy budget")
    elif args.energy_budget_nj is not None: parser.error("budget requires power model")
    base["lifetime"] = args.energy_budget_nj is not None
    if args.deplete_node and (not base["lifetime"] or not 2 <= args.deplete_node <= args.clients+1): parser.error("invalid depletion node")
    if args.bottleneck and args.clients != 2: parser.error("bottleneck fixture requires two sensors")
    if base["energy_telemetry"] and (args.phase not in (4, 5) or args.target != "z1"):
        parser.error("raw Energest validation requires Phase 4 or 5 Z1")
    if args.warmup_ms is not None: base["warmup_ms"] = args.warmup_ms
    base["aes_backend"] = "contiki_software_aes_128_driver"
    base["queuebuf_count"] = 4 if args.phase in (4,5) else 8
    base["dual_profile"] = args.phase in (4,5)
    base["switch_test"] = args.switch_test
    base["purpose"] = "profile_return" if args.switch_test else "security" if tests or args.critical_reading else "lifetime" if base.get("lifetime") else "functional"
    if args.switch_test and (args.phase != 4 or args.mode not in ("B1", "B2") or args.attack_test or args.root_reset_test):
        parser.error("switch test requires Phase 4 B1/B2 without attack/reset")
    if args.queued_shrink:
        if (args.phase != 5 or args.mode != "P1" or args.target != "z1"
                or args.clients != 2 or not args.power_model or base["lifetime"]
                or tests or args.middle_period_ms is not None or args.policy_cost_table
                or args.period_ms != 500 or args.readings != 12):
            parser.error("Queued shrink requires three Z1 motes, P1, power model and 12 readings at 500 ms")
        base["queued_shrink"] = args.queued_shrink
        base["purpose"] = "queued_shrink_measurement"
    if args.readings is not None:
        base["readings_per_sensor"] = args.readings
    if args.seed is not None:
        if args.seed < 0: parser.error("seed must be nonnegative")
        base["seed"] = args.seed
    base["flush_lead_ms"] = 125 if args.phase in (4, 5) and args.target=="z1" else 0
    base["target"] = args.target
    base["backend"] = args.backend
    base["gui_mode"] = getattr(args, "gui", False)
    if args.target == "z1" and args.backend != "ref": parser.error("Z1 optimized backend is unvalidated")
    if args.phase in (3, 4, 5) and base.get("reserved_bytes") != 16: parser.error("AES tag overhead must be 16")
    base["host_timeout_s"] = args.timeout_seconds
    if args.mode == "all5" and args.phase != 5: parser.error("all5 requires Phase 5")
    if args.mode == "all" and args.phase != 4: parser.error("all requires Phase 4")
    if args.mode == "both" and args.phase in (4,5): parser.error("Phase 4/5 requires explicit mode or all/all5")
    if args.phase != 4 and base.get("profile", 0) != (1 if args.phase == 3 else 0): parser.error("phase/profile mismatch")
    if args.phase in (3, 4) and base.get("reserved_bytes") != 16: parser.error("AES tag overhead must be 16")
    if args.attack_test and args.root_reset_test: parser.error("select one security test")
    if args.root_reset_test:
        if args.phase not in (3, 4, 5) or args.mode not in ("B1", "B2", "B3", "B6", "P1") or args.clients < 2: parser.error("root reset test requires a protected mode and at least 2 clients")
        base["root_reset_test"] = 1
    if args.attack_test:
        if args.phase not in (3, 4, 5) or args.mode not in ("B1", "B2", "B3", "B6", "P1") or args.clients < 2: parser.error("attack test requires a protected mode and at least 2 clients")
        base["attack_test"] = 1
    if args.calibration_cap is not None:
        if base['purpose'] != 'functional': parser.error('Calibration cannot include fixtures or lifetime')
        base['purpose'] = 'calibration'
    override = {key: val for key,val in [("period_ms", args.period_ms), ("payload_budget", args.payload_budget)] if val is not None}
    if args.middle_period_ms is not None:
        period = override.get("period_ms", base["period_ms"])
        readings = base["readings_per_sensor"]
        if (args.phase not in (4, 5) or args.target != "z1" or not args.power_model
            or base["purpose"] not in ("functional", "calibration", "lifetime")
            or not 27 <= readings <= 999 or readings % 3
            or not 125 <= period <= 60000 or period % 125
            or not 125 <= args.middle_period_ms <= 60000 or args.middle_period_ms % 125):
            parser.error("Middle interval requires a Z1 power-model workload with 27–999 readings divisible by three and 125 ms aligned periods")
        base["middle_period_ms"] = args.middle_period_ms
    if args.phase == 5 and args.policy_cost_table:
        from calibration_contract import validate_table
        resolved = dict(base); resolved.update(override)
        try:
            validate_table(table, resolved, args.clients)
            base['policy_calibration_status'] = 'qualified'
        except ValueError:
            if args.require_qualified_policy or not args.allow_unqualified_policy: raise
            base['policy_calibration_status'] = 'unqualified_functional_diagnostic'
            if base.get('lifetime') or args.power_model or args.target != 'cooja': parser.error('Unqualified table is restricted to native functional diagnostics')
    elif args.require_qualified_policy:
        parser.error('Qualified policy requires a compatible --policy-cost-table')
    if args.preflight_only:
        from calibration_contract import context
        resolved = dict(base); resolved.update(override)
        print(json.dumps({'status':'preflight_passed', 'context':context(resolved,args.clients),
                          'calibration_status':base.get('policy_calibration_status'),
                          'policy_cost_sha256':base.get('policy_cost_sha256'),
                          'build_executed':False, 'simulation_executed':False}, indent=2))
        return
    def frozen_sources():
        return {str(p.relative_to(PROJECT)):digest(p) for folder in ("firmware","host","configs") for p in (PROJECT/folder).rglob("*") if p.is_file() and "build" not in p.parts and p.name!="generated-conf.h" and (p.suffix in (".c",".h",".py",".mk",".json") or p.name=="Makefile")}
    frozen = frozen_sources()
    outputs=[]
    for mode in (list(base["modes"]) if args.mode in ("both","all","all5") else [args.mode]):
        if frozen_sources()!=frozen: raise ValueError("Source changed during comparison")
        outputs.append(run(mode,args.clients,base,pins,override))
    if frozen_sources()!=frozen: raise ValueError("Source changed during comparison")
    if len(outputs)>=2:
        traces=[]; prospective=[]
        for out in outputs:
            events=[json.loads(line) for line in (out/"events.jsonl").read_text().splitlines()]
            prospective.append(sorted((e["node_id"],e["warmup_ms"],e["period_ms"],e["total"]) for e in events if e["event_type"]=="SCHEDULE"))
            traces.append(sorted((e["node_id"],e["reading_id"],e["created_ms"],e["value"],e["sim_time_us"]) for e in events if e["event_type"]=="GEN"))
        exact = all(trace == traces[0] for trace in traces[1:])
        bound_ok = exact
        local_jitter = global_jitter = 0
        if args.target == "z1":
            identities = [[(r[0],r[1],r[3]) for r in trace] for trace in traces]
            identity_ok = all(t == identities[0] for t in identities[1:])
            if identity_ok:
                local_jitter = max((abs(r[2]-base_row[2]) for trace in traces[1:] for r,base_row in zip(trace,traces[0])),default=0)
                global_jitter = max((abs(r[4]-base_row[4]) for trace in traces[1:] for r,base_row in zip(trace,traces[0])),default=0)
            bound_ok = identity_ok and local_jitter <= 125 and global_jitter <= 125000
        contract = "exact_native" if args.target=="cooja" else "emulated_125ms_service_bound"
        if base.get("lifetime"):
            bound_ok = bool(prospective[0]) and all(p == prospective[0] for p in prospective[1:])
            contract = "identical_prospective_demand_verified_alive_prefixes"
        comparison = {"runs":[str(p.relative_to(PROJECT)) for p in outputs],"generation_identical":exact,
                      "comparison_eligible":bound_ok,"generation_rows":len(traces[0]),
                      "timing_contract":contract, "actual_generation_rows":[len(t) for t in traces],
                      "max_local_jitter_ms":local_jitter,"max_global_jitter_us":global_jitter,
                      "scope":"paired engineering pilot; no inferential conclusion"}
        (outputs[1] / "paired-comparison.json").write_text(json.dumps(comparison,indent=2)+"\n")
        for output in outputs:
            manifest_path = output / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["pair_valid"] = comparison["comparison_eligible"]
            manifest["pair_comparison_sha256"] = digest(outputs[1] / "paired-comparison.json")
            manifest["artifact_hashes"] = {p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "manifest.json"}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        if not comparison["comparison_eligible"]: raise ValueError("Paired generation violates declared timing contract")
        print("PAIRED_GENERATION_IDENTICAL" if exact else "PAIRED_"+contract.upper(), flush=True)
if __name__ == "__main__":
    with (PROJECT / "results/phase_02/.runner.lock").open("w") as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit("Another Phase 2 run owns generated configuration/build dirs")
        attempt_dir = PROJECT/"results/attempts"
        attempt_dir.mkdir(parents=True,exist_ok=True)
        attempt_path=attempt_dir/(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json")
        attempt={"argv":sys.argv,"status":"running","started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
        attempt_path.write_text(json.dumps(attempt,indent=2)+"\n")
        preparing_output=None
        try:
            main()
            attempt["status"]="passed"
        except BaseException as exc:
            attempt["status"]="failed"; attempt["error"]=f"{type(exc).__name__}: {exc}"
            if preparing_output is not None:
                p=preparing_output/"manifest.json"
                if p.exists():
                    m=json.loads(p.read_text())
                    if m["status"] in ("running","preparing"):
                        m.update(status="failed",error=attempt["error"])
                        p.write_text(json.dumps(m,indent=2)+"\n")
            raise
        finally:
            attempt["ended_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
            attempt_path.write_text(json.dumps(attempt,indent=2)+"\n")
