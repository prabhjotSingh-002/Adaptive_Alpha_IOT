#include "contiki.h"
#include "boot_gate.h"
#include <stdio.h>
static const uint8_t key[16] = {1};
PROCESS(boot_test_process, "Boot grant test");
AUTOSTART_PROCESSES(&boot_test_process);
PROCESS_THREAD(boot_test_process, ev, data) {
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
  if(lab_secure_seal(&context, &batch, packet, sizeof packet, &len)) {
    puts("BOOT_FAIL"); PROCESS_EXIT();
  }
  puts("BOOT_REQUEST");
  etimer_set(&tick, CLOCK_SECOND / 8);
  while(!lab_boot_gate_poll(&gate, &context)) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick)); etimer_reset(&tick);
  }
  if(!lab_secure_seal(&context, &batch, packet, sizeof packet, &len)) {
    puts("BOOT_FAIL"); PROCESS_EXIT();
  }
  puts("BOOT_GRANTED_AND_SEALED");
  /* Simulate reinitialization, not a whole-mote power reset. */
  lab_boot_gate_init(&gate, &context, 2, 1, key);
  puts("BOOT_REQUEST");
  loops = 0;
  while(loops++ < 8) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick)); etimer_reset(&tick);
    if(lab_boot_gate_poll(&gate, &context) ||
       lab_secure_seal(&context, &batch, packet, sizeof packet, &len)) {
      puts("BOOT_FAIL"); PROCESS_EXIT();
    }
  }
  puts("BOOT_REINIT_LOCKED_PASS");
  PROCESS_END();
}
