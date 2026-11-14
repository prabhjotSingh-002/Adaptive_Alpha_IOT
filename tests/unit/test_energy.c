#include "energy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
  /* Synthetic exact arithmetic oracle; not target currents or a research run. */
  lab_power_model m = {3, 1000, {1,2,0,4,5}};
  lab_energy split, whole, old;
  uint64_t ticks[5] = {0};
  assert(lab_energy_init(&split,&m,100));
  assert(lab_energy_init(&whole,&m,100));
  for(unsigned j=1;j<=9;j++) {
    for(unsigned i=0;i<5;i++) ticks[i]=j;
    assert(lab_energy_sample(&split,&m,ticks));
  }
  assert(lab_energy_sample(&whole,&m,ticks));
  assert(split.total_nj==36 && split.total_nj==whole.total_nj);
  assert(!memcmp(split.remainder,whole.remainder,sizeof split.remainder));
  assert(lab_energy_remaining(&split)==64);
  old=split; ticks[2]=0;
  assert(!lab_energy_sample(&split,&m,ticks) && !split.valid);
  assert(split.total_nj==old.total_nj);
  assert(lab_energy_init(&split,&m,1));
  for(unsigned i=0;i<5;i++) ticks[i]=1;
  assert(lab_energy_sample(&split,&m,ticks) && split.depleted);
  assert(!lab_energy_sample(&split,&m,ticks) && !lab_energy_remaining(&split));
  for(unsigned i=0;i<5;i++) ticks[i]=2;
  assert(lab_energy_close(&split,&m,ticks) && split.closed && split.depleted);
  assert(!lab_energy_close(&split,&m,ticks));
  assert(lab_energy_init(&split,&m,100)); ticks[0]=UINT64_MAX;
  assert(!lab_energy_sample(&split,&m,ticks) && !split.valid && !split.total_nj);
  puts("PASS: shared energy precision, conservation, fractional carry, invalid delta, overflow and terminal budget");
}
