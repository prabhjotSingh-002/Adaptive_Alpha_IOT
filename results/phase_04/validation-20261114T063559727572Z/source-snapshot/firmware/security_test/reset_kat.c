#include "contiki.h"
#include "boot_gate.h"
#include <stdio.h>
static const uint8_t key[16] = {1};
PROCESS(reset_test_process, "Full mote replacement test");
AUTOSTART_PROCESSES(&reset_test_process);
PROCESS_THREAD(reset_test_process, ev, data) {
  static struct etimer tick;
  static lab_boot_gate gate;
  static lab_security_context context;
  static lab_batch batch;
  static uint8_t packet[LAB_SECURE_PACKET_MAX];
  static size_t len;
  static unsigned loops;
  (void)ev; (void)data;
  PROCESS_BEGIN();
  batch.sender = 2; batch.count = 1; batch.readings[0].id = 1;
  lab_boot_gate_init(&gate, &context, 2, 1, key);
  puts("RESET_BOOT_REQUEST");
  etimer_set(&tick, CLOCK_SECOND / 8);
  loops = 0;
  while(!lab_boot_gate_poll(&gate, &context)) {
    if(lab_secure_seal(&context, &batch, packet, sizeof packet, &len)) {
      puts("RESET_FAIL"); PROCESS_EXIT();
    }
    if(++loops == 16) { puts("RESET_LOCKED_16_TICKS"); PROCESS_EXIT(); }
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick)); etimer_reset(&tick);
  }
  if(!lab_secure_seal(&context, &batch, packet, sizeof packet, &len)) {
    puts("RESET_FAIL"); PROCESS_EXIT();
  }
  puts("RESET_FIRST_SEALED");
  while(1) { PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick)); etimer_reset(&tick); }
  PROCESS_END();
}
