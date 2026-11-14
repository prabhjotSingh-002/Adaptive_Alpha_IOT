#!/usr/bin/env python3
"""One-use Cooja mailbox proof with a security-context reinitialization."""
import sys
import xml.etree.ElementTree as ET
tree = ET.parse("simulations/scenarios/phase1-rpl-9.csc")
sim = tree.getroot().find("simulation")
types = sim.findall("motetype")
sim.remove(types[1])
for mote in sim.findall("mote")[1:]:
    sim.remove(mote)
types[0].find("source").text = "/workspace/firmware/security_test/boot_kat.c"
types[0].find("commands").text = "make -j1 boot_kat.cooja TARGET=cooja"
script = tree.getroot().find("plugin/plugin_config/script")
script.text = r"""
var grants = 0;
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
TIMEOUT(60000, log.testFailed());
while(true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("BOOT_FAIL") >= 0) log.testFailed();
  if (msg.indexOf("BOOT_REQUEST") >= 0) {
    if (grants === 0) {
      var mem = new VarMemory(sim.getMoteWithID(id).getMemory());
      if (mem.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
      mem.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
      grants++;
      log.log("HARNESS_GRANT_ONCE\n");
    } else {
      log.log("HARNESS_REFUSED_REGRANT\n");
    }
  }
  if (msg.indexOf("BOOT_REINIT_LOCKED_PASS") >= 0 && grants === 1) log.testOK();
}
"""
ET.indent(tree.getroot())
tree.write(sys.argv[1], encoding="UTF-8", xml_declaration=True)
