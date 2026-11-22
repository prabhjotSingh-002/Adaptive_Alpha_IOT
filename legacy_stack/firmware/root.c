#include "contiki.h"
#include "contiki-lib.h"
#include "contiki-net.h"
#include "net/uip.h"
#include "net/rpl/rpl.h"
#include "net/simple-udp.h"
#include "sys/node-id.h"
#include "sys/energest.h"
#include "protocol.h"
#include "secure_packet.h"
#include <stdio.h>
#include <string.h>

#define UDP_PORT 1234

static struct simple_udp_connection root_conn;
#if (LAB_PROFILE > 0)
#define MAX_SENSORS 16
static lab_security_context security_ctx[MAX_SENSORS];
#endif
static const uint8_t master_key[16] = {
  0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};

#ifndef LAB_PROFILE
#define LAB_PROFILE 0
#endif

PROCESS(root_process, "Contiki 2.7 RPL Root");
AUTOSTART_PROCESSES(&root_process);

static void
rx_callback(struct simple_udp_connection *c,
            const uip_ipaddr_t *sender_addr,
            uint16_t sender_port,
            const uip_ipaddr_t *receiver_addr,
            uint16_t receiver_port,
            const uint8_t *data,
            uint16_t datalen)
{
  lab_batch batch;
  bool ok = false;

#if (LAB_PROFILE == 0)
  ok = lab_decode(data, datalen, &batch);
#else
  uint16_t sender = datalen >= LAB_HEADER ? (uint16_t)(((uint16_t)data[1] << 8) | data[2]) : 0;
  if(sender >= 2 && sender < MAX_SENSORS) {
    ok = lab_secure_open(&security_ctx[sender], data, datalen, &batch);
  }
#endif

  if(ok) {
    uint8_t i;
    for(i = 0; i < batch.count; i++) {
      printf("RSLAB,1,RX,%lu,%u\n", (unsigned long)batch.readings[i].id, (unsigned)batch.readings[i].value);
    }
  }
}

PROCESS_THREAD(root_process, ev, data)
{
  static struct etimer timer;
  static uip_ipaddr_t ipaddr;
  rpl_dag_t *dag;

  PROCESS_BEGIN();

  /* Set Root global IP: aaaa::1 */
  uip_ipaddr_t prefix;
  uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 1);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_MANUAL);

  dag = rpl_set_root(RPL_DEFAULT_INSTANCE, &ipaddr);
  if(dag != NULL) {
    uip_ip6addr(&prefix, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
    rpl_set_prefix(dag, &prefix, 64);
    printf("RSLAB,1,BOOT,root_dag_created\n");
  }

#if (LAB_PROFILE > 0)
  {
    uint8_t n;
    for(n = 2; n < MAX_SENSORS; n++) {
      lab_security_init_profile(&security_ctx[n], LAB_PROFILE, n, 1, master_key);
      lab_security_activate(&security_ctx[n]);
    }
  }
#endif

  simple_udp_register(&root_conn, UDP_PORT, NULL, UDP_PORT, rx_callback);

  etimer_set(&timer, CLOCK_SECOND * 10);
  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));

    energest_flush();
    unsigned long cpu = (unsigned long)energest_type_time(ENERGEST_TYPE_CPU);
    unsigned long lpm = (unsigned long)energest_type_time(ENERGEST_TYPE_LPM);
    unsigned long tx  = (unsigned long)energest_type_time(ENERGEST_TYPE_TRANSMIT);
    unsigned long rx  = (unsigned long)energest_type_time(ENERGEST_TYPE_LISTEN);

    printf("RSLAB,1,ENERGY_RAW,%lu,%lu,0,%lu,%lu\n", cpu, lpm, tx, rx);

    etimer_reset(&timer);
  }

  PROCESS_END();
}
