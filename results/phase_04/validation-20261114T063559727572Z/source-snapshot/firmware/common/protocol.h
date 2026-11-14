#ifndef LAB_PROTOCOL_H
#define LAB_PROTOCOL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define LAB_CAPACITY 4u
#define LAB_HEADER 11u
#define LAB_READING_BYTES 10u
#define LAB_PACKET_MAX (LAB_HEADER + LAB_CAPACITY * LAB_READING_BYTES)
typedef struct { uint32_t id, created_ms; uint16_t value; } lab_reading;
typedef struct { uint16_t sender, epoch; uint8_t profile, count; uint32_t counter; lab_reading readings[LAB_CAPACITY]; } lab_batch;
size_t lab_encode(const lab_batch *batch, uint8_t *out, size_t capacity);
bool lab_decode(const uint8_t *data, size_t length, lab_batch *out);
typedef struct { uint32_t highest, bits; } lab_seen;
/* true means new; false means duplicate or older than the bounded window. */
bool lab_mark_new(lab_seen *window, uint32_t id);
#endif
