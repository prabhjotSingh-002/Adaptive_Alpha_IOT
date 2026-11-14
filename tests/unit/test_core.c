#include "aggregate.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static lab_reading reading(uint32_t id, uint32_t time) { lab_reading r = {id, time, (uint16_t)(200 + id)}; return r; }
int main(void) {
  unsigned checks = 0;
  for(unsigned cap = 1; cap <= 4; cap *= 2) {
    lab_aggregator a; lab_batch b, decoded;
    assert(lab_aggregate_init(&a, 2, cap, 3000, 67, 16));
    for(unsigned i = 1; i <= cap; ++i) assert(lab_offer(&a, 2, reading(i, i * 1000)) == LAB_OFFER_OK);
    assert(lab_offer(&a, 2, reading(cap + 1, 5000)) == LAB_OFFER_FULL);
    assert(lab_should_flush(&a, cap * 1000, false));
    assert(lab_build_batch(&a, 1, &b));
    assert(a.count == cap); /* build without commit simulates interrupted send */
    uint8_t bytes[LAB_PACKET_MAX + 1];
    size_t n = lab_encode(&b, bytes, sizeof(bytes));
    assert(n == LAB_HEADER + cap * LAB_READING_BYTES);
    assert(bytes[0] == 1 && bytes[1] == 0 && bytes[2] == 2 && bytes[9] == 1);
    assert(!lab_encode(&b, bytes, n - 1));
    assert(lab_decode(bytes, n, &decoded));
    assert(decoded.count == cap && decoded.readings[cap-1].id == cap);
    for(size_t cut = 0; cut < n; ++cut) assert(!lab_decode(bytes, cut, &decoded));
    assert(!lab_decode(bytes, n + 1, &decoded));
    for(unsigned offset = 0; offset <= 10; ++offset) {
      if(offset != 0 && offset != 3 && offset != 4 && offset != 10) continue;
      uint8_t old = bytes[offset]; bytes[offset] = 255;
      assert(!lab_decode(bytes, n, &decoded)); bytes[offset] = old;
    }
    assert(!lab_commit_on_send(&a, cap + 1));
    assert(lab_commit_on_send(&a, cap)); assert(!a.count);
    assert(lab_offer(&a, 2, reading(cap, 6000)) == LAB_OFFER_ORDER);
    checks++;
  }
  lab_aggregator a; lab_batch b;
  assert(!lab_aggregate_init(&a, 1, 4, 3000, 67, 16));
  assert(!lab_aggregate_init(&a, 2, 0, 3000, 67, 16));
  assert(!lab_aggregate_init(&a, 2, 4, 3000, 20, 16));
  assert(!lab_aggregate_init(&a, 2, 4, UINT32_MAX, 67, 16));
  assert(lab_aggregate_init(&a, 2, 4, 3000, 47, 16)); assert(a.cap == 2);
  assert(lab_offer(&a, 3, reading(1, 100)) == LAB_OFFER_WRONG_SOURCE);
  assert(lab_offer(&a, 2, reading(1, 100)) == LAB_OFFER_OK);
  assert(lab_offer(&a, 2, reading(1, 200)) == LAB_OFFER_ORDER);
  assert(!lab_should_flush(&a, 3099, false)); assert(lab_should_flush(&a, 3100, false));
  assert(lab_should_flush(&a, 100, true));
  assert(lab_build_batch(&a, 9, &b)); assert(lab_commit_on_send(&a, 1));
  assert(!lab_should_flush(&a, 4000, true));
  assert(lab_offer(&a, 2, reading(2, UINT32_MAX - 999)) == LAB_OFFER_OK);
  assert(!lab_should_flush(&a, 1999, false)); assert(lab_should_flush(&a, 2000, false));
  assert(lab_commit_on_send(&a, 1));
  /* Rotate head through multiple ring wraps and preserve order. */
  for(unsigned id = 3; id < 24; id++) {
    assert(lab_offer(&a, 2, reading(id, id * 1000)) == LAB_OFFER_OK);
    assert(lab_build_batch(&a, id, &b) && b.readings[0].id == id);
    assert(lab_commit_on_send(&a, 1));
  }
  /* Partial submission leaves the later reading and its own deadline intact. */
  assert(lab_aggregate_init(&a, 2, 4, 3000, 67, 16));
  assert(lab_offer(&a, 2, reading(1, 1000)) == LAB_OFFER_OK);
  assert(lab_offer(&a, 2, reading(2, 2000)) == LAB_OFFER_OK);
  assert(lab_build_batch(&a, 1, &b) && a.count == 2);
  assert(lab_commit_on_send(&a, 1));
  assert(lab_build_batch(&a, 2, &b) && b.count == 1 && b.readings[0].id == 2);
  assert(!lab_should_flush(&a, 4999, false)); assert(lab_should_flush(&a, 5000, false));
  uint8_t packet[LAB_PACKET_MAX];
  b.counter = 0; assert(lab_encode(&b, packet, sizeof(packet)) == 0);
  b.counter = 1; b.count = 2; b.readings[1] = b.readings[0];
  assert(lab_encode(&b, packet, sizeof(packet)) == 0);
  b.count = 1;
  size_t length = lab_encode(&b, packet, sizeof(packet));
  lab_batch unchanged = b;
  packet[3] = 1; assert(!lab_decode(packet, length, &b));
  assert(memcmp(&b, &unchanged, sizeof(b)) == 0);
  lab_seen w = {0};
  assert(lab_mark_new(&w, 3)); assert(lab_mark_new(&w, 1)); assert(!lab_mark_new(&w, 3));
  assert(lab_mark_new(&w, 40)); assert(!lab_mark_new(&w, 1)); assert(lab_mark_new(&w, 39)); assert(!lab_mark_new(&w, 39));
  assert(!lab_mark_new(&w, 0));
  assert(lab_aggregate_init(&a, 2, 4, 0, 67, 16));
  assert(lab_offer(&a, 2, reading(1, 0)) == LAB_OFFER_OK); assert(lab_should_flush(&a, 0, false));
  puts("PASS: codec caps 1/2/4, bounds, malformed packets, queue/byte caps, deadline/wrap, send interruption, ring rotation, dedup");
  printf("cap variants checked: %u\n", checks);
  return 0;
}
