#!/usr/bin/env python3
"""Replace a Cooja mote with a freshly initialized mote of the same type."""
import sys
import xml.etree.ElementTree as ET
tree = ET.parse("simulations/scenarios/phase1-rpl-9.csc")
sim = tree.getroot().find("simulation")
types = sim.findall("motetype")
sim.remove(types[1])
for mote in sim.findall("mote")[1:]:
    sim.remove(mote)
types[0].find("source").text = "/workspace/firmware/security_test/reset_kat.c"
types[0].find("commands").text = "make -j1 reset_kat.cooja TARGET=cooja"
script = tree.getroot().find("plugin/plugin_config/script")
script.text = r"""
var grants = 0;
var replaced = false;
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
TIMEOUT(60000, log.testFailed());
while(true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RESET_FAIL") >= 0) log.testFailed();
  if (msg.indexOf("RESET_BOOT_REQUEST") >= 0) {
    if (grants === 0) {
      var mem = new VarMemory(sim.getMoteWithID(id).getMemory());
      if (mem.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
      mem.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
      grants++;
      log.log("HARNESS_GRANT_ONCE\n");
    } else log.log("HARNESS_REFUSED_REGRANT\n");
  }
  if (msg.indexOf("RESET_FIRST_SEALED") >= 0) {
    if (replaced) log.testFailed();
    replaced = true;
    var oldMote = sim.getMoteWithID(id);
    var config = oldMote.getConfigXML();
    var freshMote = oldMote.getType().generateMote(sim);
    if (!freshMote.setConfigXML(sim, config, false)) log.testFailed();
    sim.removeMote(oldMote);
    sim.addMote(freshMote);
    log.log("HARNESS_REPLACED_MOTE\n");
  }
  if (msg.indexOf("RESET_LOCKED_16_TICKS") >= 0 && replaced && grants === 1) log.testOK();
}
"""
ET.indent(tree.getroot())
tree.write(sys.argv[1], encoding="UTF-8", xml_declaration=True)
