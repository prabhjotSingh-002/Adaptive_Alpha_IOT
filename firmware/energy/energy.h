#ifndef LAB_ENERGY_H
#define LAB_ENERGY_H
#include <stdbool.h>
#include <stdint.h>
#define LAB_ENERGY_STATES 5u
/* CPU, LPM, deep LPM, radio TX, radio listen. Compatible component currents
 * only. Missing/unsupported model parameters must not be passed as zero. */
typedef struct {
  uint32_t frequency, millivolts;
  uint32_t nanoamps[LAB_ENERGY_STATES];
} lab_power_model;
typedef struct {
  uint64_t ticks[LAB_ENERGY_STATES], nanojoules[LAB_ENERGY_STATES];
  uint64_t remainder[LAB_ENERGY_STATES], total_nj, budget_nj;
  bool valid, depleted, closed;
} lab_energy;
bool lab_energy_init(lab_energy *state, const lab_power_model *model, uint64_t budget_nj);
/* Cumulative counters; atomic on error except valid=false. Depletion is
 * terminal. Budget zero is rejected; root accounting uses UINT64_MAX. */
bool lab_energy_sample(lab_energy *state, const lab_power_model *model,
                       const uint64_t ticks[LAB_ENERGY_STATES]);
/* One final shutdown snapshot is allowed after terminal budget detection;
 * this never reactivates the state. */
bool lab_energy_close(lab_energy *state, const lab_power_model *model,
                      const uint64_t ticks[LAB_ENERGY_STATES]);
uint64_t lab_energy_remaining(const lab_energy *state);
#endif
