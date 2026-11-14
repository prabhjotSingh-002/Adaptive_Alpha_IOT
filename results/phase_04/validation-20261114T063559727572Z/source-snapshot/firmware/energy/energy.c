#include "energy.h"
#include <string.h>
#include <limits.h>
static bool model_ok(const lab_power_model *m) {
  return m && m->frequency && m->millivolts;
}
bool lab_energy_init(lab_energy *s, const lab_power_model *m, uint64_t budget) {
  if(!s) return false;
  memset(s, 0, sizeof *s);
  if(!model_ok(m) || !budget) return false;
  s->budget_nj = budget; s->valid = true;
  return true;
}
bool lab_energy_sample(lab_energy *s, const lab_power_model *m, const uint64_t ticks[LAB_ENERGY_STATES]) {
  lab_energy next;
  if(!s || !s->valid || s->depleted) return false;
  if(!model_ok(m) || !ticks) { s->valid = false; return false; }
  next = *s;
  uint64_t denominator = (uint64_t)m->frequency * 1000u;
  for(unsigned i = 0; i < LAB_ENERGY_STATES; i++) {
    if(ticks[i] < s->ticks[i]) goto invalid;
    uint64_t delta = ticks[i] - s->ticks[i];
    uint64_t power = (uint64_t)m->millivolts * m->nanoamps[i];
    if(power && delta > (UINT64_MAX - s->remainder[i]) / power) goto invalid;
    uint64_t numerator = power * delta + s->remainder[i];
    uint64_t energy = numerator / denominator;
    if(energy > UINT64_MAX - next.nanojoules[i] || energy > UINT64_MAX - next.total_nj) goto invalid;
    next.nanojoules[i] += energy; next.total_nj += energy;
    next.remainder[i] = numerator % denominator; next.ticks[i] = ticks[i];
  }
  next.depleted = next.total_nj >= next.budget_nj;
  *s = next;
  return true;
invalid:
  s->valid = false;
  return false;
}
bool lab_energy_close(lab_energy *s, const lab_power_model *m, const uint64_t ticks[LAB_ENERGY_STATES]) {
  if(!s || !s->valid || !s->depleted || s->closed) return false;
  lab_energy final = *s;
  final.depleted = false;
  if(!lab_energy_sample(&final,m,ticks)) { s->valid=false; return false; }
  final.depleted=true; final.closed=true; *s=final;
  return true;
}
uint64_t lab_energy_remaining(const lab_energy *s) {
  return !s || s->depleted || s->total_nj >= s->budget_nj ? 0 : s->budget_nj - s->total_nj;
}
