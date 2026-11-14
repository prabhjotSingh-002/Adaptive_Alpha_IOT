#include "energy.h"
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <errno.h>
static uint64_t number(const char *s) {
  char *end; errno=0; uint64_t n=strtoull(s,&end,10);
  if(errno || *end || !*s || *s=='-') exit(2);
  return n;
}
int main(int argc, char **argv) {
  if(argc!=9) return 2;
  lab_power_model m; lab_energy state; uint64_t ticks[5];
  uint64_t frequency=number(argv[1]), voltage=number(argv[2]);
  if(frequency>UINT32_MAX || voltage>UINT32_MAX) return 2;
  m.frequency=(uint32_t)frequency; m.millivolts=(uint32_t)voltage;
  for(unsigned i=0;i<5;i++) { uint64_t n=number(argv[i+3]); if(n>UINT32_MAX) return 2; m.nanoamps[i]=(uint32_t)n; }
  if(!lab_energy_init(&state,&m,number(argv[8]))) return 2;
  int count;
  while((count=scanf("%"SCNu64" %"SCNu64" %"SCNu64" %"SCNu64" %"SCNu64,&ticks[0],&ticks[1],&ticks[2],&ticks[3],&ticks[4]))==5) {
    if(!lab_energy_sample(&state,&m,ticks)) return 3;
    printf("%"PRIu64,state.total_nj);
    for(unsigned i=0;i<5;i++) printf(" %"PRIu64,state.nanojoules[i]);
    putchar('\n');
  }
  return count==EOF ? 0 : 2;
}
