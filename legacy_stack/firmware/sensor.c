#include "contiki.h"
#include "contiki-lib.h"
#include "contiki-net.h"
#include "net/uip.h"
#include "net/rpl/rpl.h"
#include "net/simple-udp.h"
#include "sys/node-id.h"
#include "sys/energest.h"
#include "protocol.h"
#include "aggregate.h"
#include "secure_packet.h"
#include <stdio.h>
#include <string.h>

#define UDP_PORT 1234

#ifndef LAB_BATCH_CAP
#define LAB_BATCH_CAP 1
#endif

#ifndef LAB_PROFILE
#define LAB_PROFILE 0
#endif

#ifndef LAB_TOTAL_READINGS
#define LAB_TOTAL_READINGS 8
#endif

#ifndef LAB_WARMUP_S
#define LAB_WARMUP_S 60
#endif

#ifndef LAB_PERIOD_S
#define LAB_PERIOD_S 10
#endif

static struct simple_udp_connection sensor_conn;
static lab_aggregator agg_queue;
static lab_security_context security_ctx;
static const uint8_t master_key[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};

static void
set_global_address(void)
{
  uip_ipaddr_t ipaddr;
  uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);
}

PROCESS(sensor_process, "Contiki 2.7 RPL Sensor Client");
AUTOSTART_PROCESSES(&sensor_process);

PROCESS_THREAD(sensor_process, ev, data)
{
  static struct etimer tick_timer;
  static uip_ipaddr_t root_addr;
  static uint32_t reading_id = 0;
  static uint32_t batch_counter = 1;
  static uint8_t readings_sent = 0;
  static unsigned seconds_elapsed = 0;
  static uint8_t wire[LAB_SECURE_PACKET_MAX];
  static size_t wire_len;

  PROCESS_BEGIN();

  set_global_address();

  /* Initialize Aggregation Queue with Capacity k */
  lab_aggregate_init(&agg_queue, (uint16_t)node_id, LAB_BATCH_CAP, 35000, 67, 16);

#if (LAB_PROFILE > 0)
  lab_security_init_profile(&security_ctx, LAB_PROFILE, (uint16_t)node_id, 1, master_key);
  lab_security_activate(&security_ctx);
#endif

  simple_udp_register(&sensor_conn, UDP_PORT, NULL, UDP_PORT, NULL);

  /* Target Root is aaaa::1 */
  uip_ip6addr(&root_addr, 0xaaaa, 0, 0, 0, 0, 0, 0, 1);

  /* Start Unified 10-second Tick Timer */
  etimer_set(&tick_timer, CLOCK_SECOND * 10);

  printf("RSLAB,%u,BOOT,sensor_initialized,cap=%u,profile=%u\n", (unsigned)node_id, LAB_BATCH_CAP, LAB_PROFILE);

  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick_timer));
    seconds_elapsed += 10;

    /* 1. Emit Hardware Energest Telemetry */
    energest_flush();
    unsigned long cpu = (unsigned long)energest_type_time(ENERGEST_TYPE_CPU);
    unsigned long lpm = (unsigned long)energest_type_time(ENERGEST_TYPE_LPM);
    unsigned long tx  = (unsigned long)energest_type_time(ENERGEST_TYPE_TRANSMIT);
    unsigned long rx  = (unsigned long)energest_type_time(ENERGEST_TYPE_LISTEN);

    printf("RSLAB,%u,ENERGY_RAW,%lu,%lu,0,%lu,%lu\n", (unsigned)node_id, cpu, lpm, tx, rx);

    /* 2. Sensor Reading Generation (Post-Warmup Window) */
    if(seconds_elapsed >= LAB_WARMUP_S && readings_sent < LAB_TOTAL_READINGS) {
      lab_reading rd;
      rd.id = ((uint32_t)node_id << 16) | (++reading_id);
      rd.created_ms = (uint32_t)((uint64_t)clock_time() * 1000 / CLOCK_SECOND);
      rd.value = 250 + (uint16_t)(reading_id % 30);

      lab_offer(&agg_queue, (uint16_t)node_id, rd);
      readings_sent++;
      printf("RSLAB,%u,GEN,%lu,q=%u\n", (unsigned)node_id, (unsigned long)rd.id, (unsigned)agg_queue.count);

      /* Flush batch if capacity reached or all readings generated */
      if(agg_queue.count >= LAB_BATCH_CAP || readings_sent >= LAB_TOTAL_READINGS) {
        lab_batch batch;
        if(lab_build_batch(&agg_queue, batch_counter++, &batch)) {
          batch.sender = (uint16_t)node_id;
#if (LAB_PROFILE == 0)
          batch.epoch = 0;
          batch.profile = 0;
#else
          batch.epoch = 1;
          batch.profile = LAB_PROFILE;
#endif

          wire_len = 0;
#if (LAB_PROFILE == 0)
          wire_len = lab_encode(&batch, wire, sizeof(wire));
#else
          lab_secure_seal(&security_ctx, &batch, wire, sizeof(wire), &wire_len);
#endif

          if(wire_len > 0) {
            simple_udp_sendto(&sensor_conn, wire, wire_len, &root_addr);
            printf("RSLAB,%u,TX\n", (unsigned)node_id);
            lab_commit_on_send(&agg_queue, batch.count);
          } else {
            printf("RSLAB,%u,ERR_ENCODE\n", (unsigned)node_id);
          }
        } else {
          printf("RSLAB,%u,ERR_BUILD\n", (unsigned)node_id);
        }
      }
    }

    etimer_reset(&tick_timer);
  }

  PROCESS_END();
}
