#include "contiki.h"
#include "net/netstack.h"
#include "net/routing/routing.h"
#include "net/ipv6/simple-udp.h"
#include "aggregate.h"
#include "events.h"
#include "energest_sampler.h"
#if LAB_POLICY_MODE
#include "policy.h"
static lab_policy_state policy_state = {
  .b3_threshold_nj_hi = LAB_B3_THRESHOLD_NJ_HI,
  .b3_threshold_nj_lo = LAB_B3_THRESHOLD_NJ_LO,
  .b6_profile = LAB_B6_PROFILE,
  .cost_nj = LAB_P1_COSTS,
  .transition_cost_nj = LAB_P1_TRANSITION_COST_NJ,
  .margin_nj_per_reading = LAB_P1_MARGIN_NJ,
  .min_dwell_ms = LAB_P1_MIN_DWELL_MS,
  .deadline_ms = LAB_DEADLINE_MS > LAB_FLUSH_LEAD_MS ? LAB_DEADLINE_MS - LAB_FLUSH_LEAD_MS : 0,
  .payload_budget = LAB_PAYLOAD_BUDGET,
  .reserved_bytes = LAB_RESERVED_BYTES
};
static bool policy_seen;
static uint8_t policy_prev_profile;
static uint8_t policy_prev_cap;
#endif
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
#include "boot_gate.h"
#include "ascon_aead.h"
#include <string.h>
uint8_t lab_provisioned_metadata[LAB_PROFILE_COUNT * LAB_PROVISION_SLOT_SIZE];
uint8_t lab_provisioned_keys[LAB_PROFILE_COUNT * LAB_CCM_KEY_SIZE];
static lab_security_context contexts[LAB_PROFILE_COUNT];
static unsigned selected;
#define security contexts[selected]
static lab_boot_gate boot_gate;
#if LAB_REORDER_TEST
static uint8_t delayed_packet[LAB_SECURE_PACKET_MAX];
static size_t delayed_length;
static uint32_t delayed_since, delayed_created;
#endif
#if LAB_ROOT_RESET_TEST
static uint8_t reset_packet[LAB_SECURE_PACKET_MAX];
static size_t reset_length;
static uint32_t reset_last;
static uip_ipaddr_t reset_root;
#endif
#if LAB_ATTACK_TEST
static uint8_t attack_original[LAB_SECURE_PACKET_MAX];
static size_t attack_length;
static unsigned attack_step;
static uint32_t attack_last;
#endif
#endif
PROCESS(sensor_process, "RSLAB deterministic sensor");
AUTOSTART_PROCESSES(&sensor_process);
static struct simple_udp_connection udp;
static lab_aggregator queue;
static uint32_t counter = 1;
void lab_application_deplete(void) {
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  for(unsigned i=0;i<LAB_PROFILE_COUNT;i++) lab_security_lock(&contexts[i]);
#endif
  while(queue.count) {
    LAB_EVENT("DROP", "%"PRIu32",%u", queue.ring[queue.head].id, 70u);
    lab_commit_on_send(&queue,1);
  }
}
static bool flush_due(uint32_t now, bool critical) {
  uint32_t lead = LAB_FLUSH_LEAD_MS < queue.deadline_ms ? LAB_FLUSH_LEAD_MS : queue.deadline_ms;
  return lab_should_flush(&queue,now,critical) ||
    (queue.count && lead && lab_oldest_hold(&queue,now) >= queue.deadline_ms - lead);
}
static void flush(uint32_t now) {
  static lab_batch b;
  #if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  static uint8_t payload[LAB_SECURE_PACKET_MAX];
#else
  static uint8_t payload[LAB_PACKET_MAX];
#endif
  uip_ipaddr_t root;
  if(!queue.count) return;
  /* A missed service slot must account/drop expired readings, never submit
   * a batch already outside the declared hold bound. */
  if(lab_oldest_hold(&queue,now) > queue.deadline_ms) {
    while(queue.count) {
      LAB_EVENT("DROP", "%"PRIu32",%u", queue.ring[queue.head].id, 71u);
      lab_commit_on_send(&queue,1);
    }
    return;
  }
  if(!NETSTACK_ROUTING.node_is_reachable() || !NETSTACK_ROUTING.get_root_ipaddr(&root)) {
    if(lab_oldest_hold(&queue, now) >= queue.deadline_ms) {
      while(queue.count) {
        LAB_EVENT("DROP", "%"PRIu32",%u", queue.ring[queue.head].id, 1u);
        lab_commit_on_send(&queue, 1);
      }
    }
    return;
  }
  if(counter == UINT32_MAX || !lab_build_batch(&queue, counter, &b)) {
    LAB_EVENT("ERROR", "%u", 2u); return;
  }
  size_t length = 0;
#if LAB_DUAL_PROFILE
  selected = LAB_SWITCH_TEST ? ((counter % 3u) == 2u ? 1u : 0u) : LAB_PROFILE - 1u;
#endif
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  if(!udp.udp_conn || !lab_secure_seal(&security, &b, payload, sizeof(payload), &length)) {
    LAB_EVENT("ERROR", "%u", 4u);
    lab_security_lock(&security);
    while(queue.count) {
      LAB_EVENT("DROP", "%"PRIu32",%u", queue.ring[queue.head].id, 4u);
      lab_commit_on_send(&queue, 1);
    }
    return;
  }
#else
  length = lab_encode(&b, payload, sizeof(payload));
#endif
  if(!length || !udp.udp_conn) { LAB_EVENT("ERROR", "%u", 3u); return; }
  /* Upstream send return is always zero: this is submission, not delivery. */
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2) && LAB_ATTACK_TEST
  if(node_id == 2 && counter == 2) {
    for(unsigned i = 0; i < b.count; i++) LAB_EVENT("DROP", "%"PRIu32",%u", b.readings[i].id, 99u);
    lab_commit_on_send(&queue, b.count); counter++;
    return;
  }
#endif
#if LAB_ROOT_RESET_TEST
  if(node_id == 2 && counter == 1) {
    memcpy(reset_packet, payload, length); reset_length = length; reset_last = now;
    reset_root = root;
    memset(reset_root.u8, 0, 8); reset_root.u8[0] = 0xfe; reset_root.u8[1] = 0x80;
  }
#endif
#if LAB_REORDER_TEST
  if(node_id == 2 && counter == 2) {
    memcpy(delayed_packet,payload,length); delayed_length=length;
    delayed_since=now; delayed_created=b.readings[0].created_ms;
    lab_commit_on_send(&queue,b.count); counter++; return;
  }
#endif
#if LAB_RADIO_LOSS_TEST
  if(node_id == 2 && counter == 2) LAB_EVENT("LOSS", "%u", 1u);
#endif
  simple_udp_sendto(&udp, payload, (uint16_t)length, &root);
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2) && LAB_ATTACK_TEST
  if(node_id == 2 && counter == 1) {
    memcpy(attack_original, payload, length);
    attack_length = length;
    attack_last = now;
  }
#endif
#if LAB_SCHEMA == 2
  uint32_t wire_counter = ((uint32_t)payload[6] << 24) | ((uint32_t)payload[7] << 16) |
                          ((uint32_t)payload[8] << 8) | payload[9];
  LAB_EVENT("TX2", "%u,%u,%"PRIu32",%u,%u,%"PRIu32",%"PRIu32",%"PRIu32,
            payload[3], ((unsigned)payload[4] << 8) | payload[5], wire_counter,
            b.count, (unsigned)length, lab_oldest_hold(&queue, now), b.readings[0].id, b.readings[b.count-1].id);
#else
  LAB_EVENT("TX", "%"PRIu32",%u,%u,%"PRIu32",%"PRIu32",%"PRIu32,
            counter, b.count, (unsigned)length, lab_oldest_hold(&queue, now), b.readings[0].id, b.readings[b.count-1].id);
  #endif
  lab_commit_on_send(&queue, b.count); counter++;
}
PROCESS_THREAD(sensor_process, ev, data) {
  static struct etimer tick;
  static uint32_t generated, next_due;
  static uint8_t done;
  (void)ev; (void)data;
  PROCESS_BEGIN();
  lab_energy_telemetry_start();
#if LAB_SCHEMA == 2
  LAB_EVENT("META2", "%"PRIu32",%u,%u,%u", (uint32_t)LAB_CONFIG_ID, LAB_PROFILE, LAB_PROFILE_COUNT, LAB_SWITCH_TEST);
#endif
  if(!lab_aggregate_init(&queue, node_id, LAB_BATCH_CAP, LAB_DEADLINE_MS, LAB_PAYLOAD_BUDGET, LAB_RESERVED_BYTES) ||
     !simple_udp_register(&udp, 8765, NULL, 5678, NULL)) { LAB_EVENT("ERROR", "%u", 1u); PROCESS_EXIT(); }
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
  selected = LAB_DUAL_PROFILE ? LAB_PROFILE - 1u : 0u;
  lab_boot_gate_init_profile(&boot_gate, &contexts[0], LAB_DUAL_PROFILE ? 1 : LAB_PROFILE, node_id, 1,
                             &lab_provisioned_keys[0]);
#if LAB_DUAL_PROFILE
  lab_security_init_profile(&contexts[1], 2, node_id, 1,
                            &lab_provisioned_keys[LAB_CCM_KEY_SIZE]);
#endif
  LAB_EVENT("BOOT_REQUEST", "%u", (unsigned)LAB_PROFILE);
#endif
#if LAB_SCHEMA == 2
  LAB_EVENT("SCHEDULE", "%"PRIu32",%"PRIu32",%u,%u", lab_now_ms(), (uint32_t)LAB_WARMUP_MS, LAB_PERIOD_MS, LAB_TOTAL_READINGS);
#endif
  LAB_EVENT("READY", "%u,%u,%u,%u", queue.cap, LAB_DEADLINE_MS, LAB_PERIOD_MS, LAB_TOTAL_READINGS);
  next_due = LAB_WARMUP_MS;
  etimer_set(&tick, CLOCK_SECOND / 8);
  while(1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&tick));
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2)
    if(!contexts[0].active) {
      if(lab_boot_grant_pending() && !boot_gate.consumed) {
        if(lab_boot_gate_poll_set(&boot_gate, contexts, LAB_PROFILE_COUNT,
             &lab_provisioned_metadata[0],
             &lab_provisioned_keys[0])) LAB_EVENT("CONTEXT_READY", "%u", (unsigned)LAB_PROFILE);
      }
      etimer_reset(&tick);
      continue;
    }
#endif
    if(lab_energy_is_depleted()) { PROCESS_EXIT(); }
    uint32_t now = lab_now_ms();
#if LAB_POLICY_MODE
    {
      lab_policy_features pf;
      pf.residual_nj    = lab_energy_remaining_nj();
      pf.queue_count    = (uint16_t)queue.count;
      pf.oldest_hold_ms = lab_oldest_hold(&queue, now);
      pf.rate_hz_x100   = 100000u / LAB_PERIOD_MS;
      pf.now_ms         = now;
      pf.context_active = contexts[0].active && contexts[1].active;
      rtimer_clock_t policy_started = RTIMER_NOW();
      lab_policy_action pa;
#if LAB_POLICY_MODE == 1
      pa = lab_policy_b3(&policy_state, &pf);
#elif LAB_POLICY_MODE == 2
      pa = lab_policy_b6(&policy_state, &pf);
#elif LAB_POLICY_MODE == 3
      pa = lab_policy_p1(&policy_state, &pf);
#else
      pa.profile = LAB_PROFILE; pa.cap = LAB_BATCH_CAP; pa.reason = 0; pa.feasible = true;
#endif
      /* Apply policy output: update profile and cap. */
      if(pa.profile == 1 || pa.profile == 2) selected = pa.profile - 1u;
      if(pa.cap == 1 || pa.cap == 2 || pa.cap == 4) queue.cap = pa.cap;
      rtimer_clock_t policy_elapsed = (rtimer_clock_t)(RTIMER_NOW() - policy_started);
      LAB_EVENT("POLICY_TIME", "%lu,%lu", (unsigned long)policy_elapsed, (unsigned long)RTIMER_SECOND);
      LAB_EVENT_POLICY(pa.profile, pa.cap, pa.reason, pf.residual_nj, pf.oldest_hold_ms, pf.queue_count);
      if(policy_seen && (pa.profile != policy_prev_profile || pa.cap != policy_prev_cap)) {
        LAB_EVENT_SWITCH(policy_prev_profile, pa.profile, policy_prev_cap, pa.cap, pa.reason);
      }
      policy_seen = true;
      policy_prev_profile = pa.profile;
      policy_prev_cap     = pa.cap;
    }
#endif
#if LAB_ROOT_RESET_TEST
    /* Dedicated direct-neighbor reset probe: replay the captured authenticated
     * packet without depending on a rebooted root's RPL convergence. */
    if(node_id == 2 && reset_length && now - reset_last >= 1000) {
      LAB_EVENT("RESET_PROBE", "%u", 1u);
      simple_udp_sendto(&udp, reset_packet, (uint16_t)reset_length, &reset_root);
      reset_last = now;
    }
#endif
#if LAB_REORDER_TEST
    if(node_id==2 && delayed_length && now-delayed_since>=1500) {
      uip_ipaddr_t target;
      if(NETSTACK_ROUTING.get_root_ipaddr(&target)) {
        simple_udp_sendto(&udp,delayed_packet,(uint16_t)delayed_length,&target);
        LAB_EVENT("TX2", "%u,%u,%u,%u,%u,%"PRIu32",%u,%u", LAB_PROFILE,1u,2u,1u,(unsigned)delayed_length,now-delayed_created,2u,2u);
        delayed_length=0;
      }
    }
#endif
    if(generated < LAB_TOTAL_READINGS && (int32_t)(now - next_due) >= 0) {
      lab_reading r;
      generated++; r.id = generated; r.created_ms = now; r.value = (uint16_t)(node_id * 100u + generated);
      LAB_EVENT("GEN", "%"PRIu32",%"PRIu32",%u", r.id, r.created_ms, r.value);
      /* Record generation before any network work changes simulator time.
       * Still flush an old deadline before offering this new reading. */
      if(flush_due(now,false)) flush(now);
      lab_offer_result result = lab_offer(&queue, node_id, r);
      if(result != LAB_OFFER_OK) LAB_EVENT("DROP", "%"PRIu32",%u", r.id, (unsigned)result + 10u);
      next_due += LAB_PERIOD_MS;
      if(r.id == LAB_CRITICAL_READING) LAB_EVENT("CRITICAL", "%"PRIu32, r.id);
      if(flush_due(now,r.id == LAB_CRITICAL_READING)) flush(now);
    } else if(flush_due(now,false)) {
      flush(now);
    }
#if (LAB_PROFILE == 1 || LAB_PROFILE == 2) && LAB_ATTACK_TEST
    if(node_id == 2 && attack_length && attack_step < LAB_ATTACK_CASES && now - attack_last >= 1000) {
      static uint8_t forged[LAB_SECURE_PACKET_MAX];
      static lab_security_context wrong_key;
      static lab_batch test_batch;
      static size_t forged_len;
      uip_ipaddr_t attack_root;
      memcpy(forged, attack_original, attack_length);
      forged_len = attack_length;
      if(attack_step == 1) forged[forged_len - 1] ^= 1;
      if(attack_step == 2) forged[6] ^= 0x40;
      if(attack_step == 4) forged[LAB_HEADER] ^= 1;
      if(attack_step == 5) forged[3] = 0;
      if(attack_step == 6) forged[3] = 255;
      if(attack_step == 3) {
        wrong_key = security;
        wrong_key.key[0] ^= 1;
        memset(&test_batch, 0, sizeof test_batch);
        test_batch.sender = node_id; test_batch.count = 1;
        test_batch.readings[0].id = 0x7fffffffu;
        if(!lab_secure_seal(&wrong_key, &test_batch, forged, sizeof forged, &forged_len)) {
          LAB_EVENT("ERROR", "%u", 8u);
          forged_len = 0;
        }
      }
      if(attack_step == 7) {
        /* Dedicated malformed-body fixture: counter cannot overlap the bounded
         * normal experiment stream. Authenticate zero reading ID, then verify
         * that ordinary lower counters continue to pass at the receiver. */
        uint8_t nonce[16] = {0}, body[LAB_READING_BYTES] = {0};
        uint32_t test_counter = UINT32_MAX - 2;
        lab_security_nonce(node_id, 1, test_counter, nonce);
        nonce[3] = security.profile;
        forged[6]=0xff; forged[7]=0xff; forged[8]=0xff; forged[9]=0xfd;
        size_t body_length = 0;
        bool sealed = security.profile == 1 ?
          lab_ccm_seal(security.key,nonce,forged,LAB_HEADER,body,sizeof body,forged+LAB_HEADER,sizeof forged-LAB_HEADER,&body_length) :
          lab_ascon_seal(security.key,nonce,forged,LAB_HEADER,body,sizeof body,forged+LAB_HEADER,sizeof forged-LAB_HEADER,&body_length);
        if(!sealed) { LAB_EVENT("ERROR", "%u", 83u); forged_len=0; }
        else forged_len=LAB_HEADER+body_length;
      }
      if(forged_len && NETSTACK_ROUTING.get_root_ipaddr(&attack_root)) {
        LAB_EVENT("INJECT", "%u", attack_step + 1);
        simple_udp_sendto(&udp, forged, (uint16_t)forged_len, &attack_root);
        attack_step++; attack_last = now;
      }
    }
#endif
    if(generated == LAB_TOTAL_READINGS && !queue.count && !done) {
      LAB_EVENT("DONE", "%"PRIu32, generated); done = 1;
    }
    etimer_reset(&tick);
  }
  PROCESS_END();
}
