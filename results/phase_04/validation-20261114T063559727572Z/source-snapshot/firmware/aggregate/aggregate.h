#ifndef LAB_AGGREGATE_H
#define LAB_AGGREGATE_H
#include "protocol.h"
typedef enum { LAB_OFFER_OK, LAB_OFFER_WRONG_SOURCE, LAB_OFFER_ORDER, LAB_OFFER_FULL } lab_offer_result;
typedef struct {
  lab_reading ring[LAB_CAPACITY];
  uint16_t sender;
  uint8_t head, count, cap;
  uint32_t deadline_ms, last_id;
} lab_aggregator;
bool lab_aggregate_init(lab_aggregator *a, uint16_t sender, uint8_t cap, uint32_t deadline_ms, size_t payload_budget, size_t reserved_bytes);
lab_offer_result lab_offer(lab_aggregator *a, uint16_t sender, lab_reading reading);
bool lab_should_flush(const lab_aggregator *a, uint32_t now, bool critical);
bool lab_build_batch(const lab_aggregator *a, uint32_t counter, lab_batch *out);
bool lab_commit_on_send(lab_aggregator *a, uint8_t count);
uint32_t lab_oldest_hold(const lab_aggregator *a, uint32_t now);
#endif
