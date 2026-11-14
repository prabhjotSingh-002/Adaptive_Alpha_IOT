#!/usr/bin/env python3
"""Generate a one-mote scenario for the actual production CCM adapter."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
tree = ET.parse("simulations/scenarios/phase1-rpl-9.csc")
simulation = tree.getroot().find("simulation")
types = simulation.findall("motetype")
simulation.remove(types[1])
for mote in simulation.findall("mote")[1:]:
    simulation.remove(mote)
types[0].find("source").text = "/workspace/firmware/security_test/crypto_kat.c"
types[0].find("commands").text = "make -j1 crypto_kat.cooja TARGET=cooja"
script = tree.getroot().find("plugin/plugin_config/script")
script.text = r"""
TIMEOUT(60000, log.testFailed());
while(true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("PHASE3_KAT_FAIL") >= 0) log.testFailed();
  if (msg.indexOf("PHASE3_KAT_PASS") >= 0) log.testOK();
}
"""
ET.indent(tree.getroot())
tree.write(Path(sys.argv[1]), encoding="UTF-8", xml_declaration=True)
