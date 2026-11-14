#include "contiki.h"
#include "energest_sampler.h"
static bool terminal;
bool lab_energy_is_depleted(void) { return terminal; }
#if LAB_ENERGY_TELEMETRY
#include "sys/energest.h"
#include "sys/stack-check.h"
#include "events.h"
#include "energy.h"
#include "net/netstack.h"
#include "net/routing/rpl-lite/rpl.h"
#include "net/routing/rpl-lite/rpl-neighbor.h"
extern int msp430_dco_required;
#if LAB_ENERGY_MODEL
static lab_energy account;
static const lab_power_model model = {32768, LAB_POWER_MV, {LAB_POWER_CPU,LAB_POWER_LPM,0,LAB_POWER_TX,LAB_POWER_LISTEN}};
#endif
static uint64_t counters[5];
static void snapshot(void) {
  int irq = splhigh();
  energest_flush();
  counters[0]=energest_type_time(ENERGEST_TYPE_CPU); counters[1]=energest_type_time(ENERGEST_TYPE_LPM);
  counters[2]=energest_type_time(ENERGEST_TYPE_DEEP_LPM); counters[3]=energest_type_time(ENERGEST_TYPE_TRANSMIT);
  counters[4]=energest_type_time(ENERGEST_TYPE_LISTEN);
  splx(irq);
}
PROCESS(lab_energy_process, "RSLAB Energest accounting");
void lab_energy_telemetry_start(void) { process_start(&lab_energy_process, NULL); }
PROCESS_THREAD(lab_energy_process, ev, data) {
  static struct etimer tick;
  static unsigned samples;
  static volatile unsigned work;
  static bool radio_started;
  static uint16_t last_parent = 65535;
  (void)ev; (void)data;
  PROCESS_BEGIN();
#if LAB_ENERGY_MODEL
  if(ENERGEST_SECOND != 32768 || !lab_energy_init(&account, &model,
       node_id != 1 && (!LAB_DEPLETION_NODE || LAB_DEPLETION_NODE == node_id) ? LAB_ENERGY_BUDGET : UINT64_MAX)) {
    LAB_EVENT("ERROR", "%u", 80u); PROCESS_EXIT();
  }
#endif
  LAB_EVENT("ENERGY_TIMER", "%lu,%u", (unsigned long)ENERGEST_SECOND, (unsigned)(sizeof(ENERGEST_TIME_T) * 8));
  etimer_set(&tick, (CLOCK_SECOND * LAB_ENERGY_SAMPLE_MS) / 1000);
  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick));
    for(unsigned i=0;i<LAB_CPU_WORK_ITERATIONS;i++) work+=i;
    if(LAB_RADIO_OFF_UNTIL) {
      if(lab_now_ms()<LAB_RADIO_OFF_UNTIL) { NETSTACK_MAC.off(); NETSTACK_RADIO.off(); }
      else if(!radio_started) { NETSTACK_MAC.on(); radio_started=true; }
    }
    snapshot();
#if LAB_ENERGY_MODEL
    if(msp430_dco_required || energest_type_time(ENERGEST_TYPE_DEEP_LPM)) {
      LAB_EVENT("ERROR", "%u", 81u); PROCESS_EXIT();
    }
    if(!lab_energy_sample(&account,&model,counters)) { LAB_EVENT("ERROR", "%u", 82u); PROCESS_EXIT(); }
#endif
#if LAB_ENERGY_MODEL
    if(account.depleted) {
      terminal=true; lab_application_deplete();
      NETSTACK_MAC.off(); NETSTACK_RADIO.off();
      snapshot();
      if(!lab_energy_close(&account,&model,counters)) { LAB_EVENT("ERROR", "%u", 84u); PROCESS_EXIT(); }
    }
#endif
    if(++samples % (1000 / LAB_ENERGY_SAMPLE_MS) == 0
#if LAB_ENERGY_MODEL
       || account.depleted
#endif
    ) {
      LAB_EVENT("ENERGY_RAW", "%"PRIu64",%"PRIu64",%"PRIu64",%"PRIu64",%"PRIu64,
                counters[0],counters[1],counters[2],counters[3],counters[4]);
      LAB_EVENT("STACK", "%u,%u", (unsigned)stack_check_get_reserved_size(), (unsigned)stack_check_get_usage());
#if LAB_ENERGY_MODEL
      LAB_EVENT("ENERGY_MODEL", "%u,%"PRIu64",%"PRIu64, LAB_ENERGY_MODEL, account.total_nj, lab_energy_remaining(&account));
#endif
      uip_ipaddr_t *parent = rpl_parent_get_ipaddr(curr_instance.dag.preferred_parent);
      uint16_t parent_id = parent ? ((uint16_t)parent->u8[14] << 8) | parent->u8[15] : 0;
      if(parent_id != last_parent) {
        last_parent = parent_id;
        LAB_EVENT("ROUTE", "%u,%u", parent_id, (unsigned)curr_instance.dag.rank);
      }
    }
#if LAB_ENERGY_MODEL
    if(account.depleted) {
      LAB_EVENT("DEPLETED", "%"PRIu64, account.total_nj);
      PROCESS_EXIT();
    }
#endif
    etimer_reset(&tick);
  }
  PROCESS_END();
}
#else
void lab_energy_telemetry_start(void) { }
#endif
