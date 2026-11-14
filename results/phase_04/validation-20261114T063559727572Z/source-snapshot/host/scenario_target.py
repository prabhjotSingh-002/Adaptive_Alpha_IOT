"""Target-specific Cooja XML adaptation; no networking or metric logic."""
import xml.etree.ElementTree as ET


def configure_z1(simulation):
    interfaces = ["interfaces.Position", "interfaces.IPAddress",
                  "mspmote.interfaces.MspClock", "mspmote.interfaces.MspMoteID",
                  "mspmote.interfaces.Msp802154Radio", "mspmote.interfaces.MspDefaultSerial",
                  "mspmote.interfaces.MspLED", "mspmote.interfaces.MspDebugOutput"]
    for mote_type in simulation.findall("motetype"):
        mote_type.text = "org.contikios.cooja.mspmote.Z1MoteType"
        source = mote_type.find("source").text
        directory, name = source.rsplit("/", 1)
        stem = name.removesuffix(".c")
        for child in list(mote_type):
            if child.tag in ("moteinterface", "firmware"):
                mote_type.remove(child)
        ET.SubElement(mote_type, "firmware").text = f"{directory}/build/z1/{stem}.z1"
        for interface in interfaces:
            ET.SubElement(mote_type, "moteinterface").text = "org.contikios.cooja." + interface
    for mote in simulation.findall("mote"):
        for interface in list(mote.findall("interface_config")):
            if "MoteID" in (interface.text or ""):
                interface.text = "org.contikios.cooja.mspmote.interfaces.MspMoteID"
            elif "Position" not in (interface.text or ""):
                mote.remove(interface)
