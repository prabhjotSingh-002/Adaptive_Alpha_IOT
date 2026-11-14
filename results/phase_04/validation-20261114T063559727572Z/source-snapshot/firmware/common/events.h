#ifndef LAB_EVENTS_H
#define LAB_EVENTS_H
#include "contiki.h"
#include "sys/node-id.h"
#include <inttypes.h>
#include <stdio.h>
#define LAB_EVENT(name, format, ...) printf("RSLAB,%u," name "," format "\n", (unsigned)node_id, __VA_ARGS__)
static inline uint32_t lab_now_ms(void) { return (uint32_t)((uint64_t)clock_time() * 1000 / CLOCK_SECOND); }
#endif
