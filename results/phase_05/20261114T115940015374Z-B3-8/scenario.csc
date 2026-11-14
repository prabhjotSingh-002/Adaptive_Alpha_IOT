<?xml version='1.0' encoding='UTF-8'?>
<simconf>
  <simulation>
    <title>Phase 1 official RPL tutorial: root + eight clients</title>
    <randomseed>123458</randomseed>
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
var provisioning = {"1": [111, 2, -102, -125, -21, 97, -68, 44, -102, 75, 94, 87, 102, 44, 111, 57, -94, -24, -26, -63, -103, 29, 33, 22, -20, -64, 74, -110, 47, -84, -52, 39, -74, -99, -119, -115, 59, -6, -105, 31, -120, -14, 12, -121, -8, -122, -44, -111, 122, -111, 91, 8, -64, 39, -85, -110, -121, -69, 32, 21, 114, 11, 115, 50, 23, 85, -4, 103, 3, -1, -56, 35, -114, 123, 93, 2, 29, -10, 73, -22, 127, -65, 108, 104, -116, -68, -120, 10, -30, 76, -10, -50, 78, 118, 78, 74, -128, 50, -104, -117, 23, -36, 8, 88, -1, -103, 100, -36, -21, 13, -88, 21, -110, 125, 78, -27, 99, -82, 72, 69, 118, -97, 90, 53, 88, -28, 122, -92, 96, -60, -35, 27, 108, -83, 47, -106, 63, -33, -22, 95, 93, -9, -28, 54, -120, 69, 49, -67, 34, 72, 123, 95, 49, 86, 94, 47, -45, 69, -53, 121, -66, 69, -32, 75, -26, -93, 31, -120, -125, -17, -115, 99, -103, -79, -86, -39, -104, 71, -91, 3, -98, -70, -28, 29, -23, 63, 71, 57, 107, 104, -118, -51, 55, 67, -105, -71, 51, -23, -33, -117, 39, 105, 113, 99, 86, 29, -10, -3, -122, 114, 64, -102, 74, -45, 121, -96, 98, 74, -95, 37, 22, 44, 34, -44, 19, -15, 38, -48, -106, 121, -93, 47, -103, -79, -20, -43, -17, 99, 27, 109, 75, 53, -108, -81, 41, -42, 72, -70, 22, 31, -85, -24, 5, -34, 42, 40], "2": [111, 2, -102, -125, -21, 97, -68, 44, -102, 75, 94, 87, 102, 44, 111, 57, -94, -24, -26, -63, -103, 29, 33, 22, -20, -64, 74, -110, 47, -84, -52, 39], "3": [-74, -99, -119, -115, 59, -6, -105, 31, -120, -14, 12, -121, -8, -122, -44, -111, 122, -111, 91, 8, -64, 39, -85, -110, -121, -69, 32, 21, 114, 11, 115, 50], "4": [23, 85, -4, 103, 3, -1, -56, 35, -114, 123, 93, 2, 29, -10, 73, -22, 127, -65, 108, 104, -116, -68, -120, 10, -30, 76, -10, -50, 78, 118, 78, 74], "5": [-128, 50, -104, -117, 23, -36, 8, 88, -1, -103, 100, -36, -21, 13, -88, 21, -110, 125, 78, -27, 99, -82, 72, 69, 118, -97, 90, 53, 88, -28, 122, -92], "6": [96, -60, -35, 27, 108, -83, 47, -106, 63, -33, -22, 95, 93, -9, -28, 54, -120, 69, 49, -67, 34, 72, 123, 95, 49, 86, 94, 47, -45, 69, -53, 121], "7": [-66, 69, -32, 75, -26, -93, 31, -120, -125, -17, -115, 99, -103, -79, -86, -39, -104, 71, -91, 3, -98, -70, -28, 29, -23, 63, 71, 57, 107, 104, -118, -51], "8": [55, 67, -105, -71, 51, -23, -33, -117, 39, 105, 113, 99, 86, 29, -10, -3, -122, 114, 64, -102, 74, -45, 121, -96, 98, 74, -95, 37, 22, 44, 34, -44], "9": [19, -15, 38, -48, -106, 121, -93, 47, -103, -79, -20, -43, -17, 99, 27, 109, 75, 53, -108, -81, 41, -42, 72, -70, 22, 31, -85, -24, 5, -34, 42, 40]};
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
        var slot = [1, 2 == 2 ? p + 1 : 1, (sender &gt;&gt; 8) &amp; 255, sender &amp; 255, 0, 1, 1, 0];
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