#include "contiki.h"
#include "dev/watchdog.h"
#include "net/netstack.h"
#include "msp430-def.h"
#include "policy.h"
#include <stdio.h>

#define TRIALS 32u
#define REPETITIONS 16u

PROCESS(transition_process, "P1 transition measurement");
AUTOSTART_PROCESSES(&transition_process);

static unsigned measure(unsigned initial, unsigned initial_cap, unsigned preferred, unsigned target_cap)
{
  lab_policy_state state = {
    .initialized = true, .current_cap = initial_cap, .deadline_ms = 2875,
    .payload_budget = 67, .reserved_bytes = 16, .min_dwell_ms = 2000,
    .transition_cost_nj = 50000, .margin_nj_per_reading = 10000,
    .cost_nj = {{200000000, 0, 200000000}, {200000000, 0, 200000000}}
  };
  lab_policy_features features = {
    .context_active = true, .now_ms = 4000, .rate_hz_x100 = 200
  };
  volatile unsigned applied_profile = 0;
  volatile unsigned applied_cap = 0;
  state.cost_nj[preferred - 1][target_cap == 1 ? 0 : 2] = 190000000;

  watchdog_periodic();
  spl_t saved = splhigh();
  rtimer_clock_t start = RTIMER_NOW();
  for(unsigned i = 0; i < REPETITIONS; i++) {
    state.current_profile = initial;
    state.current_cap = initial_cap;
    state.last_switch_ms = 0;
    lab_policy_action action = lab_policy_p1(&state, &features);
    if(action.profile == 1 || action.profile == 2) applied_profile = action.profile - 1;
    if(action.cap == 1 || action.cap == 2 || action.cap == 4) applied_cap = action.cap;
  }
  rtimer_clock_t elapsed = (rtimer_clock_t)(RTIMER_NOW() - start);
  splx(saved);
  if(applied_profile != preferred - 1 || applied_cap != target_cap ||
     state.current_profile != preferred || state.current_cap != target_cap ||
     state.last_switch_ms != (initial == preferred && initial_cap == target_cap ? 0 : features.now_ms)) {
    printf("TRANSITION_FAIL,%u\n", preferred);
  }
  return elapsed;
}

PROCESS_THREAD(transition_process, ev, data)
{
  static struct etimer timer;
  PROCESS_BEGIN();
  NETSTACK_RADIO.off();
  etimer_set(&timer, CLOCK_SECOND);
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));
  for(unsigned i = 0; i < TRIALS; i++) {
    for(unsigned scenario = 0; scenario < 4; scenario++) {
      unsigned initial = scenario % 2 + 1;
      unsigned initial_cap = scenario == 3 ? 4 : 1;
      unsigned target_cap = scenario == 2 ? 4 : 1;
      unsigned hold, change;
      if(i % 2 == 0) {
        hold = measure(initial, initial_cap, initial, initial_cap);
        change = measure(initial, initial_cap, 3 - initial, target_cap);
      } else {
        change = measure(initial, initial_cap, 3 - initial, target_cap);
        hold = measure(initial, initial_cap, initial, initial_cap);
      }
      printf("TRANSITION_PAIR,%u,%u,%u,%u,%u,%lu\n",
             i, scenario, hold, change, REPETITIONS, (unsigned long)RTIMER_SECOND);
    }
  }
  printf("TRANSITION_DONE\n");
  PROCESS_END();
}
