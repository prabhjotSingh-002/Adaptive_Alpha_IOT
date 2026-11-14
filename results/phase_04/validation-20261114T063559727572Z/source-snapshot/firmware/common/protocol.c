#include "protocol.h"
#include <string.h>
static void put16(uint8_t *p, uint16_t n) { p[0] = (uint8_t)(n >> 8); p[1] = (uint8_t)n; }
static void put32(uint8_t *p, uint32_t n) { put16(p, (uint16_t)(n >> 16)); put16(p + 2, (uint16_t)n); }
static uint16_t get16(const uint8_t *p) { return (uint16_t)(((uint16_t)p[0] << 8) | p[1]); }
static uint32_t get32(const uint8_t *p) { return ((uint32_t)get16(p) << 16) | get16(p + 2); }
static bool valid(const lab_batch *b) {
  if(!b || b->sender < 2 || b->profile != 0 || b->epoch != 0 || b->counter == 0 || b->count == 0 || b->count > LAB_CAPACITY) return false;
  for(unsigned i = 0; i < b->count; ++i)
    if(b->readings[i].id == 0 || (i && b->readings[i].id <= b->readings[i-1].id)) return false;
  return true;
}
size_t lab_encode(const lab_batch *b, uint8_t *out, size_t capacity) {
  if(!out || !valid(b)) return 0;
  size_t length = LAB_HEADER + b->count * LAB_READING_BYTES;
  if(capacity < length) return 0;
  out[0] = 1; put16(out + 1, b->sender); out[3] = b->profile;
  put16(out + 4, b->epoch); put32(out + 6, b->counter); out[10] = b->count;
  for(unsigned i = 0; i < b->count; ++i) {
    uint8_t *p = out + LAB_HEADER + i * LAB_READING_BYTES;
    put32(p, b->readings[i].id); put32(p + 4, b->readings[i].created_ms); put16(p + 8, b->readings[i].value);
  }
  return length;
}
bool lab_decode(const uint8_t *data, size_t length, lab_batch *out) {
  if(!data || !out || length < LAB_HEADER || data[0] != 1 || data[10] == 0 || data[10] > LAB_CAPACITY || length != LAB_HEADER + data[10] * LAB_READING_BYTES) return false;
  lab_batch b = {0};
  b.sender = get16(data + 1); b.profile = data[3]; b.epoch = get16(data + 4); b.counter = get32(data + 6); b.count = data[10];
  for(unsigned i = 0; i < b.count; ++i) {
    const uint8_t *p = data + LAB_HEADER + i * LAB_READING_BYTES;
    b.readings[i].id = get32(p); b.readings[i].created_ms = get32(p + 4); b.readings[i].value = get16(p + 8);
  }
  if(!valid(&b)) return false;
  *out = b; return true;
}
bool lab_mark_new(lab_seen *w, uint32_t id) {
  if(!w || !id) return false;
  if(id > w->highest) {
    uint32_t delta = id - w->highest;
    w->bits = delta >= 32 ? 1u : (w->bits << delta) | 1u;
    w->highest = id; return true;
  }
  uint32_t delta = w->highest - id;
  if(delta >= 32 || (w->bits & (UINT32_C(1) << delta))) return false;
  w->bits |= UINT32_C(1) << delta; return true;
}
