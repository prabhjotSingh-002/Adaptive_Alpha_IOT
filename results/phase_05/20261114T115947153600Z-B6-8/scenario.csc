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
var provisioning = {"1": [59, 78, -118, 112, -14, 66, -106, 64, -57, -24, -43, 3, 49, -42, 120, -105, -59, -59, 28, -85, 86, -123, 121, -23, 125, -9, 108, -14, 30, 123, -59, 97, 8, 91, -14, 16, 67, 42, -31, -5, 86, 52, 28, 125, -25, 92, 69, 56, -109, -116, -120, 111, -37, -66, 59, 58, -120, 28, 121, -110, -24, 114, -34, 37, 122, 10, -123, 108, -3, -27, -15, -66, 127, -121, 124, -23, -85, -59, -67, -44, -6, 21, 102, -8, 110, -49, 69, 5, 107, 101, -119, -69, 0, 91, 99, -68, -29, 54, -19, 96, -13, 118, -73, -17, -60, -22, 97, -68, 32, -5, -118, -62, -24, 18, -105, -106, -95, -29, 88, 64, -98, -87, 88, 95, -112, -114, -23, 95, -90, 104, -66, 39, 58, 18, -27, 32, 14, -4, 52, -77, -84, 112, -81, 99, 96, 118, -48, 30, 85, -113, -30, 116, -109, -37, 45, -122, -105, -104, -69, -71, -42, 53, 99, -120, 36, 107, 37, -66, -41, 36, 27, 34, -96, -2, -7, -23, 26, -35, -51, -70, 12, -6, -8, 116, 49, -76, -62, 15, 117, -49, -101, -81, 102, -88, -106, -79, 109, 34, 61, -12, -86, -105, 119, 35, 27, -56, -57, -75, -18, 63, 23, -63, -115, 117, -127, 120, -77, -42, 8, 0, -122, 5, -51, -84, 108, -110, -17, 116, -41, -111, -52, 21, 9, -90, -17, 33, -42, -89, 106, -120, -6, -52, -113, -27, -41, 16, 46, -35, 109, -42, 97, -64, -54, -106, -12, 45], "2": [59, 78, -118, 112, -14, 66, -106, 64, -57, -24, -43, 3, 49, -42, 120, -105, -59, -59, 28, -85, 86, -123, 121, -23, 125, -9, 108, -14, 30, 123, -59, 97], "3": [8, 91, -14, 16, 67, 42, -31, -5, 86, 52, 28, 125, -25, 92, 69, 56, -109, -116, -120, 111, -37, -66, 59, 58, -120, 28, 121, -110, -24, 114, -34, 37], "4": [122, 10, -123, 108, -3, -27, -15, -66, 127, -121, 124, -23, -85, -59, -67, -44, -6, 21, 102, -8, 110, -49, 69, 5, 107, 101, -119, -69, 0, 91, 99, -68], "5": [-29, 54, -19, 96, -13, 118, -73, -17, -60, -22, 97, -68, 32, -5, -118, -62, -24, 18, -105, -106, -95, -29, 88, 64, -98, -87, 88, 95, -112, -114, -23, 95], "6": [-90, 104, -66, 39, 58, 18, -27, 32, 14, -4, 52, -77, -84, 112, -81, 99, 96, 118, -48, 30, 85, -113, -30, 116, -109, -37, 45, -122, -105, -104, -69, -71], "7": [-42, 53, 99, -120, 36, 107, 37, -66, -41, 36, 27, 34, -96, -2, -7, -23, 26, -35, -51, -70, 12, -6, -8, 116, 49, -76, -62, 15, 117, -49, -101, -81], "8": [102, -88, -106, -79, 109, 34, 61, -12, -86, -105, 119, 35, 27, -56, -57, -75, -18, 63, 23, -63, -115, 117, -127, 120, -77, -42, 8, 0, -122, 5, -51, -84], "9": [108, -110, -17, 116, -41, -111, -52, 21, 9, -90, -17, 33, -42, -89, 106, -120, -6, -52, -113, -27, -41, 16, 46, -35, 109, -42, 97, -64, -54, -106, -12, 45]};
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