#include "policy.h"
#include "aggregate.h"
#include <assert.h>
#include <string.h>
int main(void) {
  lab_policy_state s; lab_policy_features f; lab_policy_action a;
  memset(&f,0,sizeof f); f.context_active=true; f.rate_hz_x100=100; f.now_ms=10000;
  for(unsigned profile=0;profile<256;profile++) {
    memset(&s,0,sizeof s); s.initialized=true;s.current_profile=profile;s.current_cap=1;
    s.payload_budget=67;s.reserved_bytes=16;s.deadline_ms=3000;s.cost_nj[0][0]=UINT64_MAX;s.cost_nj[1][1]=1;
    a=lab_policy_p1(&s,&f);assert(a.profile==1 || a.profile==2);
    if(profile!=1 && profile!=2) assert(!a.feasible);
  }
  lab_aggregator q;lab_batch batch;
  assert(lab_aggregate_init(&q,2,4,3000,67,16));
  for(unsigned i=1;i<=4;i++) {lab_reading r={i,(i-1)*100,200};assert(lab_offer(&q,2,r)==LAB_OFFER_OK);}
  q.cap=1;
  for(unsigned i=1;i<=4;i++) {assert(lab_build_batch(&q,i,&batch));assert(batch.count==1 && batch.readings[0].id==i);assert(lab_commit_on_send(&q,1));}
  assert(!q.count);
  return 0;
}
