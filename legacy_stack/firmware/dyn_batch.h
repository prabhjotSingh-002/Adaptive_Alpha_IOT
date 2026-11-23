#ifndef DYN_BATCH_H
#define DYN_BATCH_H

#include <stdint.h>
#include "contiki.h"
#include "net/rpl/rpl.h"

#define DYN_K_MAX               4
#define DYN_K_LOSSY             2
#define DYN_TAU_ALARM           50      /* Trigger immediate flush if |x - base| >= 50 */
#define DYN_AOI_MAX_MS          35000UL /* Max age of oldest buffered sample (35s guard) */
#define DYN_ETX_CLAMP_RAW       192     /* ETX >= 1.50 (128 = 1.0 in Contiki 2.7) */
#define DYN_ETX_RECOVER_RAW     160     /* Hysteresis recovery: ETX <= 1.25 */

typedef enum {
  FLUSH_NONE = 0,
  FLUSH_ALARM_VOI = 1,
  FLUSH_ETX_CAP = 2,
  FLUSH_NORMAL_CAP = 3,
  FLUSH_AOI_TIMEOUT = 4,
  FLUSH_WINDOW_END = 5
} flush_reason_t;

typedef struct {
  int16_t  x_baseline;      /* Smoothed calm baseline (spikes do NOT corrupt this) */
  uint32_t first_ts_ms;     /* Timestamp of oldest buffered reading */
  uint16_t prev_etx;        /* Previous valid link metric for trend tracking */
  uint8_t  buf_cnt;         /* Current buffered count: 0..4 */
  uint8_t  k_cap;           /* Active dynamic cap: 2 or 4 */
  uint8_t  initialized;     /* Baseline init flag */
  uint8_t  last_was_alarm;  /* Flag indicating current reading triggered an alarm */
} dyn_batch_ctx_t;

static inline void dyn_batch_init(dyn_batch_ctx_t *ctx) {
  ctx->x_baseline = 0;
  ctx->first_ts_ms = 0;
  ctx->prev_etx = 0;
  ctx->buf_cnt = 0;
  ctx->k_cap = DYN_K_MAX;
  ctx->initialized = 0;
  ctx->last_was_alarm = 0;
}

static inline uint16_t get_parent_etx_raw(void) {
  rpl_dag_t *dag = rpl_get_any_dag();
  if(dag != NULL && dag->preferred_parent != NULL) {
    return dag->preferred_parent->link_metric;
  }
  return 128; /* Default ETX = 1.0 if parent unavailable */
}

static inline flush_reason_t dyn_batch_evaluate(
    dyn_batch_ctx_t *ctx, int16_t x_t, uint32_t now_ms,
    uint16_t parent_etx_raw, uint8_t is_last_reading) {

  int16_t diff;
  uint32_t age_ms;

  if(!ctx->initialized) {
    ctx->x_baseline = x_t;
    ctx->initialized = 1;
  }
  if(ctx->buf_cnt == 1) {
    ctx->first_ts_ms = now_ms;
  }

  /* Gate 1: Hard VoI Alarm Check against calm baseline */
  diff = x_t - ctx->x_baseline;
  if(diff < 0) diff = -diff;

  if(diff >= DYN_TAU_ALARM) {
    ctx->last_was_alarm = 1;
    /* Flush immediately: do NOT update x_baseline on alarm samples */
    return FLUSH_ALARM_VOI;
  }

  /* Update calm baseline (EWMA: 7/8 old + 1/8 new) ONLY on non-alarm samples */
  ctx->x_baseline = (int16_t)((ctx->x_baseline * 7 + x_t) >> 3);
  ctx->last_was_alarm = 0;

  /* Gate 2: Local RPL Parent ETX Cap with Hysteresis & Trend Filter */
#ifndef DISABLE_ETX_CLAMP
  /* Filter out uninitialized / stale values (>= 512) and 0 */
  if(parent_etx_raw >= DYN_ETX_CLAMP_RAW && parent_etx_raw < 512) {
    /* Only clamp when ETX actually climbed due to retries/NOACK (parent_etx_raw > prev_etx),
       ignoring static unchanged buffer intervals and monotonic decay from initial RPL metric */
    if(ctx->prev_etx > 0 && parent_etx_raw > ctx->prev_etx) {
      ctx->k_cap = DYN_K_LOSSY;
    }
  } else if(parent_etx_raw > 0 && parent_etx_raw <= DYN_ETX_RECOVER_RAW) {
    ctx->k_cap = DYN_K_MAX;
  }

  /* Track previous valid metric */
  if(parent_etx_raw > 0 && parent_etx_raw < 512) {
    ctx->prev_etx = parent_etx_raw;
  }
#endif

  /* Gate 3: Capacity, AoI Freshness, and End-of-Window Drain */
  if(ctx->buf_cnt >= ctx->k_cap) {
    return (ctx->k_cap == DYN_K_LOSSY) ? FLUSH_ETX_CAP : FLUSH_NORMAL_CAP;
  }

  if(ctx->buf_cnt > 0) {
    age_ms = now_ms - ctx->first_ts_ms;
    if(age_ms >= DYN_AOI_MAX_MS) {
      return FLUSH_AOI_TIMEOUT;
    }
  }

  if(is_last_reading && ctx->buf_cnt > 0) {
    return FLUSH_WINDOW_END;
  }

  return FLUSH_NONE;
}

#endif /* DYN_BATCH_H */


