<?xml version='1.0' encoding='UTF-8'?>
<simconf>
  <simulation>
    <title>Mustafa Comparison: 10 nodes on Z1</title>
    <randomseed>123456</randomseed>
    <motedelay_us>1000000</motedelay_us>
    <radiomedium>
      org.contikios.cooja.radiomediums.UDGM
      <transmitting_range>50.0</transmitting_range>
      <interference_range>100.0</interference_range>
      <success_ratio_tx>1.0</success_ratio_tx>
      <success_ratio_rx>1.0</success_ratio_rx>
    </radiomedium>
    <events>
      <logoutput>40000</logoutput>
    </events>
    <motetype>org.contikios.cooja.mspmote.Z1MoteType<identifier>mtype829</identifier>
      <description>Cooja Mote Type #1</description>
      <source>/workspace/firmware/root/root.c</source>
      <commands>make -j1 root.z1 TARGET=z1 ASCON_IMPL=ref</commands>
      <firmware>/workspace/mustafa_benchmarks/results/raw/optA_10nodes_aes_cap1_20261121T050750Z/build/root.z1</firmware>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.IPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspClock</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.Msp802154Radio</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDefaultSerial</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspLED</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDebugOutput</moteinterface>
    </motetype>
    <motetype>org.contikios.cooja.mspmote.Z1MoteType<identifier>mtype405</identifier>
      <description>Cooja Mote Type #2</description>
      <source>/workspace/firmware/sensor/sensor.c</source>
      <commands>make -j1 sensor.z1 TARGET=z1 ASCON_IMPL=ref</commands>
      <firmware>/workspace/mustafa_benchmarks/results/raw/optA_10nodes_aes_cap1_20261121T050750Z/build/sensor.z1</firmware>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.IPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspClock</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.Msp802154Radio</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDefaultSerial</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspLED</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDebugOutput</moteinterface>
    </motetype>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>43.291897546941804</x>
        <y>7.17470867058031</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>1</id>
      </interface_config>
      <motetype_identifier>mtype829</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>41.0074953544532</x>
        <y>42.15996473110367</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>2</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>62.14716228260997</x>
        <y>33.4762563475895</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>3</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>82.83122911981513</x>
        <y>21.68868709116004</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>4</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>93.05570620505483</x>
        <y>4.903395862706303</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>5</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>60.028650247913106</x>
        <y>64.79735069148343</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>6</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>91.52155150461668</x>
        <y>49.56589548717288</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>7</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>115.1617201005399</x>
        <y>27.558102517230267</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>8</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>79.769185504542</x>
        <y>89.87729413135577</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>9</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
    <mote>
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>105.0</x>
        <y>60.0</y>
        <z>0.0</z>
      </interface_config>
      <interface_config>org.contikios.cooja.mspmote.interfaces.MspMoteID<id>10</id>
      </interface_config>
      <motetype_identifier>mtype405</motetype_identifier>
    </mote>
  </simulation>
  <plugin>org.contikios.cooja.plugins.ScriptRunner<plugin_config>
      <script>
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
var provisioning = {"1": [95, 8, -113, 54, 106, 118, -69, 126, 55, -99, -59, -89, -60, 24, 107, -94, -8, -65, -102, -37, -105, 99, -87, 64, 4, 121, -98, -26, 115, -54, 126, 5, 33, -128, 60, 13, 45, -120, 104, -102, -125, 100, -122, -127, -33, -122, 72, 84, -34, -119, 83, 11, -71, -103, -111, -120, -112, 47, -101, -116, 110, 115, -1, 65, -11, -64, -59, 106, 120, 106, 30, 20, 37, -37, -8, 88, -57, -37, -110, 50, 6, 108, -109, 62, 82, -38, -4, -68, -58, -122, 63, 110, -71, 91, -104, -10, -113, 110, -60, 81, 2, -88, -6, 94, 16, -55, -121, 51, 87, 95, -67, -1, -32, -84, 45, -128, 34, 73, -121, 68, 120, -3, -80, 124, 76, -4, 60, -28, 90, -53, -69, 18, 34, -85, -93, -39, -115, 44, 120, 68, 59, -59, 65, 69], "10": [90, -53, -69, 18, 34, -85, -93, -39, -115, 44, 120, 68, 59, -59, 65, 69], "2": [95, 8, -113, 54, 106, 118, -69, 126, 55, -99, -59, -89, -60, 24, 107, -94], "3": [-8, -65, -102, -37, -105, 99, -87, 64, 4, 121, -98, -26, 115, -54, 126, 5], "4": [33, -128, 60, 13, 45, -120, 104, -102, -125, 100, -122, -127, -33, -122, 72, 84], "5": [-34, -119, 83, 11, -71, -103, -111, -120, -112, 47, -101, -116, 110, 115, -1, 65], "6": [-11, -64, -59, 106, 120, 106, 30, 20, 37, -37, -8, 88, -57, -37, -110, 50], "7": [6, 108, -109, 62, 82, -38, -4, -68, -58, -122, 63, 110, -71, 91, -104, -10], "8": [-113, 110, -60, 81, 2, -88, -6, 94, 16, -55, -121, 51, 87, 95, -67, -1], "9": [-32, -84, 45, -128, 34, 73, -121, 68, 120, -3, -80, 124, 76, -4, 60, -28]};
var grants = {};

var medium = sim.getRadioMedium();
var listener = new (Java.type("java.util.function.BiConsumer"))(function(event, unused) {
  if (String(event) != "TRANSMISSION_FINISHED") return;
  var connection = medium.getLastConnection();
  if (connection == null) return;
  var packet = connection.getSource().getLastPacketTransmitted();
  if (packet == null) return;
  var bytes = packet.getPacketData(); var hex = "";
  for (var i=0; i&lt;bytes.length; i++) hex += ("0" + ((bytes[i] &amp; 255).toString(16))).slice(-2);
  log.log("RADIO," + sim.getSimulationTime() + "," + connection.getSource().getMote().getID() + "," + hex + "\n");
});
medium.getRadioTransmissionTriggers().addTrigger(listener, listener);
TIMEOUT(135000, log.log("MUSTAFA_RUN_COMPLETE\n"); log.testOK());

var firstMessage = true;
while (true) {
  if(!firstMessage) { YIELD(); }
  firstMessage = false;
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RSLAB," + id + ",BOOT_REQUEST,") &gt;= 0) {
    if (grants[id] || !provisioning[id]) {
      log.log("BOOT_REGRANT_REFUSED\n");
      continue;
    }
    var memory = new VarMemory(sim.getMoteWithID(id).getMemory());
    if (memory.getVariableSize("lab_provisioned_keys") != provisioning[id].length) throw new Error("Key-slot ABI mismatch");
    memory.setByteArray("lab_provisioned_keys", Java.to(provisioning[id], "byte[]"));
    var metadata = new Array(provisioning[id].length / 16 * 8);
    for (var k = 0; k &lt; metadata.length; k++) metadata[k] = 0;
    for (var index = 0; index &lt; provisioning[id].length / (16 * 1); index++) {
      var sender = id == 1 ? index + 2 : id;
      for (var p = 0; p &lt; 1; p++) {
        var slot = [1, 1, (sender &gt;&gt; 8) &amp; 255, sender &amp; 255, 0, 1, 1, 0];
        for (var j = 0; j &lt; 8; j++) metadata[(index * 1 + p) * 8 + j] = slot[j];
      }
    }
    if (memory.getVariableSize("lab_provisioned_metadata") != metadata.length) throw new Error("Metadata ABI mismatch");
    memory.setByteArray("lab_provisioned_metadata", Java.to(metadata, "byte[]"));
    if (memory.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
    memory.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
    grants[id] = true;
  }
}
</script>
      <active>true</active>
    </plugin_config>
  </plugin>
</simconf>