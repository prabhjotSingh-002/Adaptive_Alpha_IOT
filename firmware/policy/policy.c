#include "policy.h"
#include "../common/protocol.h"
#include <string.h>

void lab_rate_observe(lab_rate_estimator *s, uint32_t now_ms) {
    if(!s) return;
    if(!s->seen) { s->seen = true; s->last_ms = now_ms; return; }
    uint32_t delta = now_ms - s->last_ms;
    if(!delta) return;
    if(delta > INT32_MAX) {
        memset(s, 0, sizeof(*s)); s->seen = true; s->last_ms = now_ms; return;
    }
    if(s->count == LAB_RATE_WINDOW) s->sum_ms -= s->intervals[s->next];
    else s->count++;
    s->intervals[s->next] = delta; s->sum_ms += delta;
    s->next = (s->next + 1u) % LAB_RATE_WINDOW; s->last_ms = now_ms;
}

uint16_t lab_rate_get(const lab_rate_estimator *s, uint32_t now_ms) {
    if(!s || !s->seen || !s->count || !s->sum_ms) return 0;
    uint64_t stale_ms = 2u * s->sum_ms / s->count;
    if(stale_ms < 1000u) stale_ms = 1000u;
    if((uint32_t)(now_ms - s->last_ms) > stale_ms) return 0;
    uint64_t rate = 100000u * (uint64_t)s->count / s->sum_ms;
    return rate > UINT16_MAX ? UINT16_MAX : (uint16_t)rate;
}

static bool runtime_valid(const lab_policy_state *s) {
    return !s->initialized || ((s->current_profile == 1u || s->current_profile == 2u) &&
           (s->current_cap == 1u || s->current_cap == 2u || s->current_cap == 4u));
}

/* Deadline-first service excludes equality: a reading due at expiry is offered
 * only after the old queue is flushed. This predicts full-cap occupancy only. */
static bool fills_before_deadline(const lab_policy_state *s, const lab_policy_features *f, uint8_t cap) {
    return cap == 1u || (f->rate_hz_x100 && (uint64_t)(cap - 1u) * 100000u <
           (uint64_t)s->deadline_ms * f->rate_hz_x100);
}

/* Estimate energy demand (in nJ) required to complete and transmit a batch of size 'cap'.
 * Based on remaining fill time at measured rate and background power model (~57.4 mJ/s). */
static uint64_t estimate_batch_fill_demand_nj(const lab_policy_features *f, uint8_t cap) {
    if(cap <= 1u || !f->rate_hz_x100) return 350000ULL;
    uint16_t pending = (f->queue_count < cap) ? (uint16_t)(cap - f->queue_count) : 0u;
    if(!pending) return 561000ULL;
    uint64_t fill_time_ms = (uint64_t)pending * 100000u / f->rate_hz_x100;
    return fill_time_ms * 57436ULL + 561000ULL;
}

/* Safe default: AES profile 1, cap 1. Used whenever estimates are
 * unavailable, context is inactive or no feasible action exists. */
static lab_policy_action safe_fallback(uint8_t reason) {
    lab_policy_action a;
    a.profile = 1;
    a.cap     = 1;
    a.reason  = reason;
    a.feasible = false;
    return a;
}

/* Returns the highest cap (1,2,4) whose encoded protected length fits the
 * payload budget for a given profile (tag size = reserved_bytes = 16). */
uint8_t lab_policy_max_cap(const lab_policy_state *s) {
    if(!s || s->payload_budget < s->reserved_bytes + LAB_HEADER + LAB_READING_BYTES) return 0;
    uint8_t fit = (uint8_t)((s->payload_budget - s->reserved_bytes - LAB_HEADER) / LAB_READING_BYTES);
    if(fit >= 4) return 4;
    if(fit >= 2) return 2;
    return 1;
}

/* ---- B3 ------------------------------------------------------------------ */

lab_policy_action lab_policy_b3(lab_policy_state *s, const lab_policy_features *f) {
    lab_policy_action out;

    if(!s || !f) return safe_fallback(LAB_POL_FALLBACK);
    if(!f->context_active) return safe_fallback(LAB_POL_DEPLETED);
    if(!runtime_valid(s)) { s->initialized = false; return safe_fallback(LAB_POL_FALLBACK); }

    /* Initialise current profile from thresholds on first call. */
    if(!s->initialized) {
        s->current_profile = (f->residual_nj < (uint64_t)s->b3_threshold_nj_lo) ? 2u : 1u;
        s->current_cap = 1;
        s->initialized = true;
    }

    uint8_t chosen = s->current_profile;
    uint8_t reason;

    if(f->residual_nj > (uint64_t)s->b3_threshold_nj_hi) {
        chosen = 1; reason = LAB_POL_B3_AES;
    } else if(f->residual_nj < (uint64_t)s->b3_threshold_nj_lo) {
        chosen = 2; reason = LAB_POL_B3_ASCON;
    } else {
        /* Hysteresis band: hold current choice. */
        chosen = s->current_profile;
        reason = LAB_POL_B3_HOLD;
    }

    s->current_profile = chosen;
    s->current_cap = 1;

    out.profile  = chosen;
    out.cap      = 1;
    out.reason   = reason;
    out.feasible = true;
    return out;
}

/* ---- B6 ------------------------------------------------------------------ */

lab_policy_action lab_policy_b6(lab_policy_state *s, const lab_policy_features *f) {
    lab_policy_action out;

    if(!s || !f) return safe_fallback(LAB_POL_FALLBACK);
    if(!f->context_active) return safe_fallback(LAB_POL_DEPLETED);
    if(!runtime_valid(s)) { s->initialized = false; return safe_fallback(LAB_POL_FALLBACK); }
    if(s->b6_profile != 1u && s->b6_profile != 2u) return safe_fallback(LAB_POL_FALLBACK);

    if(!s->initialized) {
        s->current_profile = s->b6_profile;
        s->current_cap = 1;
        s->initialized = true;
    }

    uint8_t max_cap = lab_policy_max_cap(s);
    if(!max_cap) return safe_fallback(LAB_POL_NO_FEASIBLE);

    /* Choose the waiting target before enqueue; cap=1 would flush every
     * first arrival and prevent the queue ever reaching two readings. */
    uint8_t cap = 1;
    for(uint8_t candidate = 2; candidate <= max_cap; candidate *= 2) {
        if(fills_before_deadline(s, f, candidate)) cap = candidate;
    }

    s->current_profile = s->b6_profile;
    s->current_cap     = cap;

    out.profile  = s->b6_profile;
    out.cap      = cap;
    out.reason   = LAB_POL_B6_FIXED;
    out.feasible = true;
    return out;
}

/* ---- P1 ------------------------------------------------------------------ */

lab_policy_action lab_policy_p1(lab_policy_state *s, const lab_policy_features *f) {
    static const uint8_t cap_values[3] = {1, 2, 4};

    if(!s || !f) return safe_fallback(LAB_POL_FALLBACK);
    if(!f->context_active) return safe_fallback(LAB_POL_DEPLETED);
    if(!runtime_valid(s)) { s->initialized = false; return safe_fallback(LAB_POL_FALLBACK); }

    if(!s->initialized) {
        s->current_profile = 1;
        s->current_cap     = 1;
        s->last_switch_ms  = f->now_ms;
        s->initialized     = true;
    }

    uint8_t max_cap = lab_policy_max_cap(s);

    /* Find feasible action with minimum estimated cost. */
    uint8_t best_profile = 0, best_cap = 0;
    uint64_t best_cost = UINT64_MAX;
    bool any_feasible = false;
    bool any_affordable = false;
    bool current_feasible = false;
    bool current_affordable = false;

    for(uint8_t pi = 0; pi < 2; pi++) {           /* profiles 1,2 */
        for(uint8_t ci = 0; ci < 3; ci++) {        /* caps 1,2,4 */
            uint8_t cap = cap_values[ci];
            if(cap > max_cap) continue;
            if(!fills_before_deadline(s, f, cap)) continue;
            if(s->cost_nj[pi][ci] == 0) continue;  /* No calibration data */

            uint64_t demand = estimate_batch_fill_demand_nj(f, cap);
            bool is_afford = (f->residual_nj == UINT64_MAX) || (demand <= f->residual_nj);

            if(pi + 1u == s->current_profile && cap == s->current_cap) {
                current_feasible = true;
                current_affordable = is_afford;
            }

            uint64_t est = s->cost_nj[pi][ci];
            if(is_afford) {
                if(!any_affordable || est < best_cost) {
                    best_cost    = est;
                    best_profile = pi + 1u;
                    best_cap     = cap;
                    any_affordable = true;
                }
            } else if(!any_affordable && (!any_feasible || est < best_cost)) {
                best_cost    = est;
                best_profile = pi + 1u;
                best_cap     = cap;
            }
            any_feasible = true;
        }
    }

    if(!any_feasible) return safe_fallback(LAB_POL_NO_FEASIBLE);

    /* Check if already on the best action. */
    if(best_profile == s->current_profile && best_cap == s->current_cap) {
        lab_policy_action out;
        out.profile  = s->current_profile;
        out.cap      = s->current_cap;
        out.reason   = LAB_POL_P1_BEST;
        out.feasible = true;
        return out;
    }

    /* Dwell check: applies only when current action is feasible AND affordable. */
    if(current_feasible && current_affordable && s->initialized && s->min_dwell_ms > 0 &&
       (f->now_ms - s->last_switch_ms) < s->min_dwell_ms) {
        lab_policy_action out;
        out.profile  = s->current_profile;
        out.cap      = s->current_cap;
        out.reason   = LAB_POL_P1_DWELL;
        out.feasible = true;
        return out;
    }

    /* Saving check: applies only when current action is feasible AND affordable. */
    uint8_t cur_ci = (s->current_cap == 4) ? 2u : (s->current_cap == 2) ? 1u : 0u;
    uint64_t cur_cost = (current_feasible && current_affordable) ? s->cost_nj[s->current_profile - 1u][cur_ci] : 0;

    if(current_feasible && current_affordable && cur_cost > 0) {
        uint64_t horizon = (uint64_t)f->rate_hz_x100 * s->min_dwell_ms / 100000u;
        if(!horizon) horizon = 1;
        /* Compare per-reading saving against amortized transition cost. */
        if(cur_cost <= best_cost || cur_cost - best_cost <= s->margin_nj_per_reading ||
           (cur_cost - best_cost - s->margin_nj_per_reading) <=
           s->transition_cost_nj / horizon) {
            lab_policy_action out;
            out.profile  = s->current_profile;
            out.cap      = s->current_cap;
            out.reason   = LAB_POL_P1_NOSAVE;
            out.feasible = true;
            return out;
        }
    }

    /* Commit switch. */
    bool battery_switch = current_feasible && !current_affordable && any_affordable;
    s->current_profile = best_profile;
    s->current_cap     = best_cap;
    s->last_switch_ms  = f->now_ms;

    lab_policy_action out;
    out.profile  = best_profile;
    out.cap      = best_cap;
    out.reason   = battery_switch ? LAB_POL_P1_BATTERY : LAB_POL_P1_BEST;
    out.feasible = true;
    return out;
}
