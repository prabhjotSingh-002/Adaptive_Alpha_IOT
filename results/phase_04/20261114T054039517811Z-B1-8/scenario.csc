<?xml version='1.0' encoding='UTF-8'?>
<simconf>
  <simulation>
    <title>Phase 1 official RPL tutorial: root + eight clients</title>
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
      <firmware>/workspace/firmware/root/build/z1/root.z1</firmware>
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
      <firmware>/workspace/firmware/sensor/build/z1/sensor.z1</firmware>
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
  </simulation>
  <plugin>org.contikios.cooja.plugins.ScriptRunner<plugin_config>
      <script>
var VarMemory = Java.type("org.contikios.cooja.mote.memory.VarMemory");
var provisioning = {"1": [-100, 74, -28, -73, 82, 94, -39, -94, 1, 4, -13, 74, -88, -6, -90, 122, 42, 102, -14, 48, 87, -48, -128, 126, -60, -69, -5, 103, 79, -61, 112, 53, -78, 92, -67, -100, -80, 51, 24, -120, 104, 80, -14, 90, 10, 6, -50, -51, -9, 20, -16, -69, -23, -64, -113, -104, 22, -108, 56, -14, -65, 53, -16, 68, -53, -30, 40, 69, 12, -55, -74, -56, -107, 3, -44, -52, 97, -97, 33, 3, -46, -22, -51, 73, -118, -105, 71, 111, 52, -34, -87, 11, 78, 50, -70, 89, -70, 58, -10, -14, -23, 76, 21, 19, -115, 58, 2, 69, -128, -96, 78, -93, 39, -126, -4, -51, 4, 115, 11, -106, -121, -89, -108, -81, 18, 36, -63, 30, 13, -4, -69, 105, 97, 47, 58, 119, 117, -33, 83, -11, -53, -106, -62, -47, -109, -128, -9, 75, -47, 110, 74, -104, -58, 29, 123, 78, 55, -100, -82, -40, -33, -117, -128, 22, -123, -95, -98, 98, 114, 119, -80, -73, -57, 116, -103, -119, 63, 18, -27, -9, -33, -122, -66, 31, 24, -63, 79, 52, -50, -43, 0, -67, 114, 62, 62, -38, -19, -94, 31, 88, -66, 94, -24, -38, 32, 30, -8, 32, 115, -67, -10, 13, 123, -56, 78, 25, 51, -100, 61, -71, -81, -64, -112, 110, -35, 111, -48, -113, 124, -27, 29, 52, -34, -1, 120, 28, -122, -75, -69, 81, 96, -68, 1, 22, -2, 109, 65, 42, -49, 17, 88, 44, -42, 114, -40, 39], "2": [-100, 74, -28, -73, 82, 94, -39, -94, 1, 4, -13, 74, -88, -6, -90, 122, 42, 102, -14, 48, 87, -48, -128, 126, -60, -69, -5, 103, 79, -61, 112, 53], "3": [-78, 92, -67, -100, -80, 51, 24, -120, 104, 80, -14, 90, 10, 6, -50, -51, -9, 20, -16, -69, -23, -64, -113, -104, 22, -108, 56, -14, -65, 53, -16, 68], "4": [-53, -30, 40, 69, 12, -55, -74, -56, -107, 3, -44, -52, 97, -97, 33, 3, -46, -22, -51, 73, -118, -105, 71, 111, 52, -34, -87, 11, 78, 50, -70, 89], "5": [-70, 58, -10, -14, -23, 76, 21, 19, -115, 58, 2, 69, -128, -96, 78, -93, 39, -126, -4, -51, 4, 115, 11, -106, -121, -89, -108, -81, 18, 36, -63, 30], "6": [13, -4, -69, 105, 97, 47, 58, 119, 117, -33, 83, -11, -53, -106, -62, -47, -109, -128, -9, 75, -47, 110, 74, -104, -58, 29, 123, 78, 55, -100, -82, -40], "7": [-33, -117, -128, 22, -123, -95, -98, 98, 114, 119, -80, -73, -57, 116, -103, -119, 63, 18, -27, -9, -33, -122, -66, 31, 24, -63, 79, 52, -50, -43, 0, -67], "8": [114, 62, 62, -38, -19, -94, 31, 88, -66, 94, -24, -38, 32, 30, -8, 32, 115, -67, -10, 13, 123, -56, 78, 25, 51, -100, 61, -71, -81, -64, -112, 110], "9": [-35, 111, -48, -113, 124, -27, 29, 52, -34, -1, 120, 28, -122, -75, -69, 81, 96, -68, 1, 22, -2, 109, 65, 42, -49, 17, 88, 44, -42, 114, -40, 39]};
var grants = {};
var rootReplaced = false;

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
TIMEOUT(102000, log.log("PHASE4_SCHEMA2_COMPLETE\n"); log.testOK());
while (true) {
  YIELD();
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RSLAB," + id + ",BOOT_REQUEST,") &gt;= 0) {
    if (grants[id] || !provisioning[id]) {
      log.log("BOOT_REGRANT_REFUSED\n");
      if (!(false &amp;&amp; id == 1 &amp;&amp; rootReplaced)) log.testFailed();
      continue;
    }
    var memory = new VarMemory(sim.getMoteWithID(id).getMemory());
    if (memory.getVariableSize("lab_provisioned_keys") != provisioning[id].length) throw new Error("Key-slot ABI mismatch");
    memory.setByteArray("lab_provisioned_keys", Java.to(provisioning[id], "byte[]"));
    var metadata = new Array(provisioning[id].length / 16 * 8);
    for (var k = 0; k &lt; metadata.length; k++) metadata[k] = 0;
    for (var index = 0; index &lt; provisioning[id].length / (16 * 2); index++) {
      var sender = id == 1 ? index + 2 : id;
      for (var p = 0; p &lt; 2; p++) {
        var slot = [1, 2 == 2 ? p + 1 : 1, (sender &gt;&gt; 8) &amp; 255, sender &amp; 255, 0, 1, 1, 0];
        for (var j = 0; j &lt; 8; j++) metadata[(index * 2 + p) * 8 + j] = slot[j];
      }
    }
    if (memory.getVariableSize("lab_provisioned_metadata") != metadata.length) throw new Error("Metadata ABI mismatch");
    memory.setByteArray("lab_provisioned_metadata", Java.to(metadata, "byte[]"));
    if (memory.getVariableSize("lab_boot_mailbox") != 4) throw new Error("Boot ABI size mismatch");
    memory.setByteArray("lab_boot_mailbox", Java.to([0x42, 0x54, 0x47, 0x31], "byte[]"));
    grants[id] = true;
  }
  if (false &amp;&amp; id == 1 &amp;&amp; !rootReplaced &amp;&amp; (msg.indexOf("RSLAB,1,RX_AUTH,") &gt;= 0 || msg.indexOf("RSLAB,1,RX2,") &gt;= 0)) {
    rootReplaced = true;
    var previous = sim.getMoteWithID(1);
    var conf = previous.getConfigXML();
    var fresh = previous.getType().generateMote(sim);
    if (!fresh.setConfigXML(sim, conf, false)) log.testFailed();
    sim.removeMote(previous);
    sim.addMote(fresh);
    log.log("ROOT_MOTE_REPLACED\n");
  }
}
</script>
      <active>true</active>
    </plugin_config>
  </plugin>
</simconf>