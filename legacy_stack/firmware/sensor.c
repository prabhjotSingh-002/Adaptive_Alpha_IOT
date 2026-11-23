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
#if ENABLE_DYN_BATCH
#include "dyn_batch.h"
static dyn_batch_ctx_t dyn_ctx;
static uint16_t stat_alarm = 0;
static uint16_t stat_etx_cap = 0;
static uint16_t stat_cap4 = 0;
static uint16_t stat_aoi = 0;
static uint16_t stat_end = 0;
static uint16_t stat_max_etx = 0;
static uint16_t stat_last_etx = 0;
#endif
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
#define LAB_TOTAL_READINGS 12
#endif

#ifndef LAB_WARMUP_S
#define LAB_WARMUP_S 100
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
#if ENABLE_DYN_BATCH
  dyn_batch_init(&dyn_ctx);
  lab_aggregate_init(&agg_queue, (uint16_t)node_id, DYN_K_MAX, 35000, 67, 16);
#else
  lab_aggregate_init(&agg_queue, (uint16_t)node_id, LAB_BATCH_CAP, 35000, 67, 16);
#endif

#if (LAB_PROFILE > 0)
  lab_security_init_profile(&security_ctx, LAB_PROFILE, (uint16_t)node_id, 1, master_key);
  lab_security_activate(&security_ctx);
#endif

  simple_udp_register(&sensor_conn, UDP_PORT, NULL, UDP_PORT, NULL);

  /* Target Root is aaaa::1 */
  uip_ip6addr(&root_addr, 0xaaaa, 0, 0, 0, 0, 0, 0, 1);

  /* Stagger initial sensor tick to prevent synchronous ContikiMAC strobe collisions (450ms spacing) */
  clock_time_t initial_offset = (clock_time_t)(((node_id - 2) * (CLOCK_SECOND * 45 / 100)) % (CLOCK_SECOND * 10));
  if(initial_offset > 0) {
    etimer_set(&tick_timer, initial_offset);
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick_timer));
  }
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
      reading_id++;
      rd.id = ((uint32_t)node_id << 16) | reading_id;
      rd.created_ms = (uint32_t)clock_seconds() * 1000 + (uint32_t)((clock_time() % CLOCK_SECOND) * 1000 / CLOCK_SECOND);

#if ENABLE_SPIKE_TRACE
      if(reading_id == 5 || reading_id == 10) {
        rd.value = 330;
      } else {
        rd.value = 250 + (uint16_t)((reading_id + node_id) % 5);
      }
#else
      rd.value = 250 + (uint16_t)(reading_id % 30);
#endif

      lab_offer(&agg_queue, (uint16_t)node_id, rd);
      readings_sent++;

#if ENABLE_DYN_BATCH
      uint16_t etx_raw = get_parent_etx_raw();
      stat_last_etx = etx_raw;
      if(etx_raw > stat_max_etx && etx_raw < 512) {
        stat_max_etx = etx_raw;
      }
      dyn_ctx.buf_cnt = agg_queue.count;
      flush_reason_t reason = dyn_batch_evaluate(&dyn_ctx, (int16_t)rd.value, rd.created_ms, etx_raw, (readings_sent >= LAB_TOTAL_READINGS));
      printf("RSLAB,%u,TICK,rd=%lu,val=%u,etx=%u,cap=%u,reason=%u\n", (unsigned)node_id, (unsigned long)reading_id, (unsigned)rd.value, etx_raw, dyn_ctx.k_cap, (unsigned)reason);

      bool do_flush = (reason != FLUSH_NONE);
      if(reason == FLUSH_ALARM_VOI) stat_alarm++;
      else if(reason == FLUSH_ETX_CAP) stat_etx_cap++;
      else if(reason == FLUSH_NORMAL_CAP) stat_cap4++;
      else if(reason == FLUSH_AOI_TIMEOUT) stat_aoi++;
      else if(reason == FLUSH_WINDOW_END) stat_end++;
#else
      bool do_flush = (agg_queue.count >= LAB_BATCH_CAP || readings_sent >= LAB_TOTAL_READINGS);
#endif

      /* Flush batch if capacity reached or all readings generated */
      if(do_flush) {
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
#if ENABLE_DYN_BATCH
            dyn_ctx.buf_cnt = agg_queue.count;
            dyn_ctx.first_ts_ms = 0;
#endif
          } else {
            printf("RSLAB,%u,ERR_ENCODE\n", (unsigned)node_id);
          }
        } else {
          printf("RSLAB,%u,ERR_BUILD\n", (unsigned)node_id);
        }
      }

#if ENABLE_DYN_BATCH
      if(readings_sent >= LAB_TOTAL_READINGS && agg_queue.count == 0) {
        printf("RSLAB,%u,DYN_STATS,alarm=%u,etx_cap=%u,cap4=%u,aoi=%u,end=%u,max_etx=%u,last_etx=%u\n",
               (unsigned)node_id, stat_alarm, stat_etx_cap, stat_cap4, stat_aoi, stat_end, stat_max_etx, stat_last_etx);
      }
#endif
    }

    etimer_reset(&tick_timer);
  }

  PROCESS_END();
}
