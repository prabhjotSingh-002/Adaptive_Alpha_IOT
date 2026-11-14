#!/usr/bin/env python3
"""Derive a headless tutorial scenario without editing upstream firmware."""
from pathlib import Path
import xml.etree.ElementTree as ET

project = Path(__file__).resolve().parents[1]
source = project / "external/contiki-ng/examples/rpl-udp/rpl-udp-cooja.csc"
root = ET.parse(source).getroot()
simulation = root.find("simulation")
# Upstream saved scenario contains 16 nodes; tutorial requires root + 8 clients.
for mote in list(simulation.findall("mote"))[9:]:
    simulation.remove(mote)
simulation.find("title").text = "Phase 1 official RPL tutorial: root + eight clients"
for commands in simulation.findall("motetype/commands"):
    commands.text = commands.text.replace("-j$(CPUS)", "-j1")
for plugin in list(root.findall("plugin")):
    root.remove(plugin)
plugin = ET.SubElement(root, "plugin")
plugin.text = "org.contikios.cooja.plugins.ScriptRunner"
config = ET.SubElement(plugin, "plugin_config")
ET.SubElement(config, "script").text = r'''TIMEOUT(600000);
var responded = {};
var rootRequests = 0;
while (true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (id == 1 && msg.indexOf("Received request") >= 0) rootRequests++;
  if (id >= 2 && id <= 9 && msg.indexOf("Received response") >= 0) responded[id] = true;
  var all = true;
  for (var client = 2; client <= 9; client++) if (!responded[client]) all = false;
  if (all && rootRequests >= 8) {
    log.log("PHASE1_PASS: root received requests; all eight clients received responses\n");
    log.testOK();
  }
}
'''
ET.SubElement(config, "active").text = "true"
out = project / "simulations/scenarios/phase1-rpl-9.csc"
ET.indent(root)
ET.ElementTree(root).write(out, encoding="UTF-8", xml_declaration=True)
print(out)
