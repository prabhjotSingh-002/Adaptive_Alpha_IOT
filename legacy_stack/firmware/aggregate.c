#include "aggregate.h"
#include <string.h>
bool lab_aggregate_init(lab_aggregator *a, uint16_t sender, uint8_t cap, uint32_t deadline, size_t budget, size_t reserved) {
  if(!a || sender < 2 || cap == 0 || cap > LAB_CAPACITY || deadline > INT32_MAX || reserved > budget || budget - reserved < LAB_HEADER + LAB_READING_BYTES) return false;
  size_t fit = (budget - reserved - LAB_HEADER) / LAB_READING_BYTES;
  memset(a, 0, sizeof(*a)); a->sender = sender; a->cap = fit < cap ? (uint8_t)fit : cap; a->deadline_ms = deadline; return true;
}
lab_offer_result lab_offer(lab_aggregator *a, uint16_t sender, lab_reading r) {
  if(sender != a->sender) return LAB_OFFER_WRONG_SOURCE;
  if(r.id == 0 || r.id <= a->last_id) return LAB_OFFER_ORDER;
  if(a->count >= a->cap) return LAB_OFFER_FULL;
  a->ring[(a->head + a->count) % LAB_CAPACITY] = r;
  a->count++; a->last_id = r.id; return LAB_OFFER_OK;
}
uint32_t lab_oldest_hold(const lab_aggregator *a, uint32_t now) { return a->count ? now - a->ring[a->head].created_ms : 0; }
bool lab_should_flush(const lab_aggregator *a, uint32_t now, bool critical) {
  return a->count && (critical || a->count >= a->cap || lab_oldest_hold(a, now) >= a->deadline_ms);
}
bool lab_build_batch(const lab_aggregator *a, uint32_t counter, lab_batch *out) {
  if(!a || !out || !a->count || !counter) return false;
  if(!a->cap || a->cap > LAB_CAPACITY) return false;
  memset(out, 0, sizeof(*out)); out->sender = a->sender; out->counter = counter;
  /* A reduced cap chunks the existing queue; commit removes only this chunk. */
  out->count = a->count < a->cap ? a->count : a->cap;
  for(unsigned i = 0; i < out->count; ++i) out->readings[i] = a->ring[(a->head + i) % LAB_CAPACITY];
  return true;
}
bool lab_commit_on_send(lab_aggregator *a, uint8_t count) {
  if(!a || !count || count > a->count) return false;
  a->head = (a->head + count) % LAB_CAPACITY; a->count -= count; return true;
}
