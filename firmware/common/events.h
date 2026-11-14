#ifndef LAB_EVENTS_H
#define LAB_EVENTS_H
#include "contiki.h"
#include "sys/node-id.h"
#include <inttypes.h>
#include <stdio.h>
#define LAB_EVENT(name, format, ...) printf("RSLAB,%u," name "," format "\n", (unsigned)node_id, __VA_ARGS__)
static inline uint32_t lab_now_ms(void) { return (uint32_t)((uint64_t)clock_time() * 1000 / CLOCK_SECOND); }

/* Phase 5 policy telemetry events.
 * POLICY: emitted each service tick — profile, cap, reason, residual_nj, oldest_hold_ms, queue_count.
 * SWITCH:  emitted only when profile or cap changes from previous tick. */
#define LAB_EVENT_POLICY(profile, cap, reason, residual_nj, hold_ms, queue) \
  printf("RSLAB,%u,POLICY,%u,%u,%u,%"PRIu64",%"PRIu32",%u\n", \
         (unsigned)node_id, (unsigned)(profile), (unsigned)(cap), \
         (unsigned)(reason), (uint64_t)(residual_nj), (uint32_t)(hold_ms), (unsigned)(queue))

#define LAB_EVENT_SWITCH(old_profile, new_profile, old_cap, new_cap, reason) \
  printf("RSLAB,%u,SWITCH,%u,%u,%u,%u,%u\n", \
         (unsigned)node_id, (unsigned)(old_profile), (unsigned)(new_profile), \
         (unsigned)(old_cap), (unsigned)(new_cap), (unsigned)(reason))

#endif
