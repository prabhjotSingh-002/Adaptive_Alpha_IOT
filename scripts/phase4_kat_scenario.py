#!/usr/bin/env python3
"""Generate a one-mote scenario for the actual production Ascon adapter."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
tree = ET.parse("simulations/scenarios/phase1-rpl-9.csc")
simulation = tree.getroot().find("simulation")
types = simulation.findall("motetype")
simulation.remove(types[1])
for mote in simulation.findall("mote")[1:]:
    simulation.remove(mote)
profile = int(sys.argv[4]) if len(sys.argv)>4 else 2
if profile not in (1,2): raise SystemExit("Unsupported KAT profile")
program = "crypto_kat" if profile==1 else "ascon_kat"
types[0].find("source").text = f"/workspace/firmware/security_test/{program}.c"
target = sys.argv[2] if len(sys.argv) > 2 else "cooja"
if target not in ("cooja", "z1"): raise SystemExit("Unsupported KAT target")
backend = sys.argv[3] if len(sys.argv) > 3 else "ref"
if backend not in ("ref", "opt32_lowsize"): raise SystemExit("Unsupported backend")
types[0].find("commands").text = f"make TARGET={target} clean\nmake -j1 {program}.{target} TARGET={target} ASCON_IMPL={backend}"
if target == "z1":
    types[0].text = "org.contikios.cooja.mspmote.Z1MoteType"
    for child in list(types[0]):
        if child.tag in ("moteinterface", "firmware"): types[0].remove(child)
    ET.SubElement(types[0], "firmware").text = f"/workspace/firmware/security_test/build/z1/{program}.z1"
    for name in ["interfaces.Position", "interfaces.IPAddress", "mspmote.interfaces.MspClock", "mspmote.interfaces.MspMoteID", "mspmote.interfaces.Msp802154Radio", "mspmote.interfaces.MspDefaultSerial", "mspmote.interfaces.MspLED", "mspmote.interfaces.MspDebugOutput"]:
        ET.SubElement(types[0], "moteinterface").text = "org.contikios.cooja." + name
    for interface in simulation.find("mote").findall("interface_config"):
        if "MoteID" in (interface.text or ""): interface.text = "org.contikios.cooja.mspmote.interfaces.MspMoteID"
        elif "Position" not in (interface.text or ""): simulation.find("mote").remove(interface)

script = tree.getroot().find("plugin/plugin_config/script")
script.text = r"""
TIMEOUT(60000, log.testFailed());
while(true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("PHASE4_KAT_FAIL") >= 0) log.testFailed();
  if (msg.indexOf("PHASE4_KAT_PASS") >= 0) log.testOK();
}
"""
if profile==1: script.text=script.text.replace("PHASE4_KAT", "PHASE3_KAT")
ET.indent(tree.getroot())
tree.write(Path(sys.argv[1]), encoding="UTF-8", xml_declaration=True)
