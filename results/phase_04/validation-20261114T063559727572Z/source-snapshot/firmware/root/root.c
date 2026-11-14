#include "contiki.h"
#include "net/netstack.h"
#include "net/routing/routing.h"
#include "net/ipv6/simple-udp.h"
#include "protocol.h"
#include "events.h"
#include "energest_sampler.h"
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
#include "boot_gate.h"
#include <string.h>
uint8_t lab_provisioned_metadata[(LAB_LAST_NODE - 1) * LAB_PROFILE_COUNT * LAB_PROVISION_SLOT_SIZE];
uint8_t lab_provisioned_keys[(LAB_LAST_NODE - 1) * LAB_PROFILE_COUNT * LAB_CCM_KEY_SIZE];
static lab_security_context security[(LAB_LAST_NODE - 1) * LAB_PROFILE_COUNT];
static lab_boot_gate boot_gate;
#endif
PROCESS(root_process, "RSLAB reading root");
AUTOSTART_PROCESSES(&root_process);
static struct simple_udp_connection udp;
void lab_application_deplete(void) { }
static lab_seen seen[LAB_LAST_NODE + 1];
static void receive(struct simple_udp_connection *c, const uip_ipaddr_t *source, uint16_t source_port,
                    const uip_ipaddr_t *destination, uint16_t destination_port, const uint8_t *data, uint16_t length) {
  lab_batch b;
  (void)c; (void)source_port; (void)destination; (void)destination_port;
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  uint16_t sender = length >= LAB_HEADER ? (uint16_t)(((uint16_t)data[1] << 8) | data[2]) : 0;
  lab_open_status verdict = LAB_OPEN_CONTEXT;
  unsigned profile = length >= LAB_HEADER ? data[3] : 0;
  unsigned slot = (sender - 2u) * LAB_PROFILE_COUNT + (LAB_DUAL_PROFILE && profile == 2 ? 1u : 0u);
  if(sender < 2 || sender > LAB_LAST_NODE ||
     source->u8[14] != (uint8_t)(sender >> 8) || source->u8[15] != (uint8_t)sender ||
     (verdict = lab_secure_open_status(&security[slot], data, length, &b)) != LAB_OPEN_OK) {
#else
  if(!lab_decode(data, length, &b) || b.sender > LAB_LAST_NODE ||
      source->u8[14] != (uint8_t)(b.sender >> 8) || source->u8[15] != (uint8_t)b.sender) {
#endif
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
    LAB_EVENT("REJECT_DETAIL", "%u,%u", (unsigned)length, (unsigned)verdict);
#else
    LAB_EVENT("REJECT", "%u", (unsigned)length);
#endif
    return;
  }
#if LAB_SCHEMA == 2
  LAB_EVENT("PACKET2", "%u,%u,%u,%"PRIu32, b.sender, b.profile, b.epoch, b.counter);
#endif
  for(unsigned i = 0; i < b.count; ++i) {
    lab_reading *r = &b.readings[i];
    unsigned duplicate = !lab_mark_new(&seen[b.sender], r->id);
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
#if LAB_SCHEMA == 2
    LAB_EVENT("RX2", "%u,%u,%u,%"PRIu32",%"PRIu32",%"PRIu32",%u,%u",
              b.sender, b.profile, b.epoch, b.counter, r->id, r->created_ms, r->value, duplicate);
#else
    LAB_EVENT("RX_AUTH", "%u,%"PRIu32",%"PRIu32",%"PRIu32",%u,%u", b.sender, b.counter, r->id, r->created_ms, r->value, duplicate);
#endif
#else
    LAB_EVENT("RX", "%u,%"PRIu32",%"PRIu32",%"PRIu32",%u,%u", b.sender, b.counter, r->id, r->created_ms, r->value, duplicate);
#endif
  }
}
PROCESS_THREAD(root_process, ev, data) {
  (void)ev; (void)data;
  PROCESS_BEGIN();
  lab_energy_telemetry_start();
#if LAB_SCHEMA == 2
  LAB_EVENT("META2", "%"PRIu32",%u,%u,%u", (uint32_t)LAB_CONFIG_ID, LAB_PROFILE, LAB_PROFILE_COUNT, LAB_SWITCH_TEST);
#endif
  NETSTACK_ROUTING.root_start();
  if(!simple_udp_register(&udp, 5678, NULL, 8765, receive)) LAB_EVENT("ERROR", "%u", 1u);
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  static struct etimer tick;
  lab_boot_gate_init_profile(&boot_gate, &security[0], LAB_DUAL_PROFILE ? 1 : LAB_PROFILE, 2, 1,
                             &lab_provisioned_keys[0]);
  for(unsigned i = 2; i <= LAB_LAST_NODE; i++)
    for(unsigned j = 0; j < LAB_PROFILE_COUNT; j++) {
      unsigned slot = (i - 2u) * LAB_PROFILE_COUNT + j;
      lab_security_init_profile(&security[slot], LAB_DUAL_PROFILE ? j + 1 : LAB_PROFILE, i, 1,
                                &lab_provisioned_keys[slot * LAB_CCM_KEY_SIZE]);
    }
  LAB_EVENT("BOOT_REQUEST", "%u", (unsigned)LAB_PROFILE);
  etimer_set(&tick, CLOCK_SECOND / 8);
  while(!security[0].active) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick));
    if(lab_boot_grant_pending() && !boot_gate.consumed) {
      if(lab_boot_gate_poll_set(&boot_gate, &security[0], (LAB_LAST_NODE - 1) * LAB_PROFILE_COUNT,
           &lab_provisioned_metadata[0],
           &lab_provisioned_keys[0])) {
        LAB_EVENT("CONTEXT_READY", "%u", (unsigned)LAB_PROFILE);
      }
    }
    etimer_reset(&tick);
  }
  LAB_EVENT("ROOT_READY", "%u", (unsigned)LAB_PROFILE);
#else
  LAB_EVENT("ROOT_READY", "%u", 0u);
#endif
  PROCESS_END();
}
