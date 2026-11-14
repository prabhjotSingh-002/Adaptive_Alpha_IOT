<?xml version='1.0' encoding='UTF-8'?>
<simconf>
  <simulation>
    <title>Phase 1 official RPL tutorial: root + eight clients</title>
    <randomseed>123457</randomseed>
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
var provisioning = {"1": [-16, 39, -84, 107, 70, 61, -98, 120, 35, 85, 14, -98, 73, -25, -95, -47, -24, 13, -125, -88, -10, 48, 4, 34, 40, 34, -71, 38, 71, -67, -90, 106, 123, -73, -35, 39, 42, -50, 26, 46, -17, -35, 2, 100, -8, 46, 3, -110, 115, 67, 87, -2, 62, 117, -128, -68, 25, -128, 15, -68, 68, -92, -106, -30, -127, 69, -20, 1, -60, 28, -112, -122, 117, -103, -59, -80, -57, 36, 44, 122, -70, -74, 22, -126, 38, -128, -62, 67, -9, -24, -25, 25, 95, 100, -103, -54, 9, 91, -109, 58, 49, 106, 93, 8, 77, -95, -15, -85, 114, -91, 77, -17, 118, 86, 123, -121, 22, -45, -89, -108, 9, -32, 103, -47, -85, 87, 114, 44, 123, -14, 49, 51, -103, 61, 95, -49, -82, -10, -97, 17, 29, -69, 104, 100, -63, -67, 30, -27, 13, 41, -41, 87, -83, 91, -10, 29, 103, 87, 30, 86, -48, 16, 119, -55, -122, 98, -49, 15, -13, 22, 124, 109, 106, 89, 24, -105, 13, 10, -121, -69, -52, 65, -76, -87, -117, -67, 114, 108, 92, -15, 112, -17, 88, 12, 40, -22, 34, -61, -101, -53, 104, -47, 14, -82, -36, 39, 111, 88, -68, 29, -103, 95, 117, 104, 23, 127, 114, 53, 59, -36, 55, -86, -75, 61, 65, -44, 97, 91, -13, -118, -122, 49, -75, 16, 41, 79, 70, -38, 22, 24, 35, 13, -12, 104, 4, -1, 121, 76, 91, 93, 120, -128, 77, -100, 46, -100], "2": [-16, 39, -84, 107, 70, 61, -98, 120, 35, 85, 14, -98, 73, -25, -95, -47, -24, 13, -125, -88, -10, 48, 4, 34, 40, 34, -71, 38, 71, -67, -90, 106], "3": [123, -73, -35, 39, 42, -50, 26, 46, -17, -35, 2, 100, -8, 46, 3, -110, 115, 67, 87, -2, 62, 117, -128, -68, 25, -128, 15, -68, 68, -92, -106, -30], "4": [-127, 69, -20, 1, -60, 28, -112, -122, 117, -103, -59, -80, -57, 36, 44, 122, -70, -74, 22, -126, 38, -128, -62, 67, -9, -24, -25, 25, 95, 100, -103, -54], "5": [9, 91, -109, 58, 49, 106, 93, 8, 77, -95, -15, -85, 114, -91, 77, -17, 118, 86, 123, -121, 22, -45, -89, -108, 9, -32, 103, -47, -85, 87, 114, 44], "6": [123, -14, 49, 51, -103, 61, 95, -49, -82, -10, -97, 17, 29, -69, 104, 100, -63, -67, 30, -27, 13, 41, -41, 87, -83, 91, -10, 29, 103, 87, 30, 86], "7": [-48, 16, 119, -55, -122, 98, -49, 15, -13, 22, 124, 109, 106, 89, 24, -105, 13, 10, -121, -69, -52, 65, -76, -87, -117, -67, 114, 108, 92, -15, 112, -17], "8": [88, 12, 40, -22, 34, -61, -101, -53, 104, -47, 14, -82, -36, 39, 111, 88, -68, 29, -103, 95, 117, 104, 23, 127, 114, 53, 59, -36, 55, -86, -75, 61], "9": [65, -44, 97, 91, -13, -118, -122, 49, -75, 16, 41, 79, 70, -38, 22, 24, 35, 13, -12, 104, 4, -1, 121, 76, 91, 93, 120, -128, 77, -100, 46, -100]};
var grants = {};
var rootReplaced = false;
var sensorReplaced = false;
var lossActive = false;
var originalTxRatio = sim.getRadioMedium().SUCCESS_RATIO_TX;

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
  if (msg == "LOSS_RESTORE") {
    sim.getRadioMedium().SUCCESS_RATIO_TX = originalTxRatio;
    lossActive=false; log.log(time + ",2,RSLAB,2,LOSS,0\n"); continue;
  }
  log.log(time + "," + id + "," + msg + "\n");
  if (msg.indexOf("RSLAB,2,LOSS,1") &gt;= 0) {
    if(lossActive) log.testFailed();
    lossActive=true; sim.getRadioMedium().SUCCESS_RATIO_TX=0;
    GENERATE_MSG(750,"LOSS_RESTORE");
  }
  if (false &amp;&amp; id == 1 &amp;&amp; !sensorReplaced &amp;&amp; msg.indexOf("RSLAB,1,RX2,2,") &gt;= 0) {
    sensorReplaced=true;
    var previous=sim.getMoteWithID(2); var conf=previous.getConfigXML();
    var fresh=previous.getType().generateMote(sim);
    if(!fresh.setConfigXML(sim,conf,false)) log.testFailed();
    sim.removeMote(previous); sim.addMote(fresh); continue;
  }
  if (msg.indexOf("RSLAB," + id + ",DEPLETED,") &gt;= 0) {
    if (id == 1) log.testFailed();
    sim.removeMote(sim.getMoteWithID(id));
    log.log(time + "," + id + ",RSLAB," + id + ",REMOVED,1\n");
    continue;
  }
  if (msg.indexOf("RSLAB," + id + ",BOOT_REQUEST,") &gt;= 0) {
    if (grants[id] || !provisioning[id]) {
      log.log("BOOT_REGRANT_REFUSED\n");
      if (!(false &amp;&amp; id == 1 &amp;&amp; rootReplaced) &amp;&amp; !(false &amp;&amp; id==2 &amp;&amp; sensorReplaced)) log.testFailed();
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
        var slot = [1, 2 == 2 ? p + 1 : 2, (sender &gt;&gt; 8) &amp; 255, sender &amp; 255, 0, 1, 1, 0];
        for (var j = 0; j &lt; 8; j++) metadata[(index * 2 + p) * 8 + j] = slot[j];
      }
    }
    if (id == 1 &amp;&amp; "none" != "none") {
      var at=metadata.length-8;
      if("none"=="missing") metadata[at+6]=0;
      if("none"=="version") metadata[at]=0;
      if("none"=="profile") metadata[at+1]=255;
      if("none"=="epoch") metadata[at+5]=2;
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