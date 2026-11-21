#!/usr/bin/env python3
"""Generate dedicated Cooja simulation scenarios for Mustafa comparison.

Creates:
  - scenarios/mustafa-rpl-5.csc  (1 Root + 4 Sensors = 5 nodes)
  - scenarios/mustafa-rpl-10.csc (1 Root + 9 Sensors = 10 nodes)
All nodes are configured as Zolertia Z1 motes running MSP430F2617.
"""
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "simulations/scenarios/phase1-rpl-9.csc"
OUT_DIR = Path(__file__).resolve().parent / "scenarios"


def create_scenario(num_nodes: int, output_file: Path, end_ms: int = 120000):
    tree = ET.parse(TEMPLATE)
    root = tree.getroot()
    sim = root.find("simulation")
    sim.find("title").text = f"Mustafa Comparison: {num_nodes} nodes on Z1"
    sim.find("randomseed").text = "123456"

    # Configure Z1 mote types
    interfaces = [
        "interfaces.Position", "interfaces.IPAddress",
        "mspmote.interfaces.MspClock", "mspmote.interfaces.MspMoteID",
        "mspmote.interfaces.Msp802154Radio", "mspmote.interfaces.MspDefaultSerial",
        "mspmote.interfaces.MspLED", "mspmote.interfaces.MspDebugOutput"
    ]
    for mote_type in sim.findall("motetype"):
        mote_type.text = "org.contikios.cooja.mspmote.Z1MoteType"
        source = mote_type.find("source").text
        is_root = "udp-server" in source
        name = "root" if is_root else "sensor"
        mote_type.find("source").text = f"/workspace/firmware/{name}/{name}.c"
        mote_type.find("commands").text = f"make -j1 {name}.z1 TARGET=z1 ASCON_IMPL=ref"
        for child in list(mote_type):
            if child.tag in ("moteinterface", "firmware"):
                mote_type.remove(child)
        ET.SubElement(mote_type, "firmware").text = f"/workspace/firmware/{name}/build/z1/{name}.z1"
        for iface in interfaces:
            ET.SubElement(mote_type, "moteinterface").text = "org.contikios.cooja." + iface

    motes = sim.findall("mote")

    # If num_nodes == 5: keep motes 1..5, delete motes 6..9
    if num_nodes == 5:
        for m in motes[5:]:
            sim.remove(m)
    elif num_nodes == 10:
        # Clone mote 9 to create mote 10
        mote10 = copy.deepcopy(motes[-1])
        # Update ID to 10
        for iface in mote10.findall("interface_config"):
            if "MoteID" in (iface.text or ""):
                iface.find("id").text = "10"
            elif "Position" in (iface.text or ""):
                iface.find("x").text = "105.0"
                iface.find("y").text = "60.0"
                iface.find("z").text = "0.0"
        sim.append(mote10)

    # Adjust interfaces on all motes for Z1
    for m in sim.findall("mote"):
        for iface in list(m.findall("interface_config")):
            if "MoteID" in (iface.text or ""):
                iface.text = "org.contikios.cooja.mspmote.interfaces.MspMoteID"
            elif "Position" not in (iface.text or ""):
                m.remove(iface)

    # Configure ScriptRunner
    script_elem = root.find("plugin/plugin_config/script")
    script_elem.text = f"""
var medium = sim.getRadioMedium();
var listener = new (Java.type("java.util.function.BiConsumer"))(function(event, unused) {{
  if (String(event) != "TRANSMISSION_FINISHED") return;
  var connection = medium.getLastConnection();
  if (connection == null) return;
  var packet = connection.getSource().getLastPacketTransmitted();
  if (packet == null) return;
  var bytes = packet.getPacketData(); var hex = "";
  for (var i=0; i<bytes.length; i++) hex += ("0" + ((bytes[i] & 255).toString(16))).slice(-2);
  log.log("RADIO," + sim.getSimulationTime() + "," + connection.getSource().getMote().getID() + "," + hex + "\\n");
}});
medium.getRadioTransmissionTriggers().addTrigger(listener, listener);
TIMEOUT({end_ms}, log.log("MUSTAFA_RUN_COMPLETE\\n"); log.testOK());
while (true) {{ YIELD(); log.log(time + "," + id + "," + msg + "\\n"); }}
"""
    ET.indent(root)
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"Created {output_file} with {len(sim.findall('mote'))} motes.")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    create_scenario(5, OUT_DIR / "mustafa-rpl-5.csc")
    create_scenario(10, OUT_DIR / "mustafa-rpl-10.csc")
