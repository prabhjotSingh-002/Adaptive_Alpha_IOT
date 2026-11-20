#include "policy.h"
#include <string.h>

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
    if(!s || s->payload_budget <= s->reserved_bytes + 11u) return 1;
    uint8_t fit = (uint8_t)((s->payload_budget - s->reserved_bytes - 11u) / 10u);
    if(fit >= 4) return 4;
    if(fit >= 2) return 2;
    return 1;
}

/* ---- B3 ------------------------------------------------------------------ */

lab_policy_action lab_policy_b3(lab_policy_state *s, const lab_policy_features *f) {
    lab_policy_action out;

    if(!s || !f) return safe_fallback(LAB_POL_FALLBACK);
    if(!f->context_active) return safe_fallback(LAB_POL_DEPLETED);

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
    if(s->b6_profile != 1u && s->b6_profile != 2u) return safe_fallback(LAB_POL_FALLBACK);

    if(!s->initialized) {
        s->current_profile = s->b6_profile;
        s->current_cap = 1;
        s->initialized = true;
    }

    uint8_t max_cap = lab_policy_max_cap(s);

    /* Choose the waiting target before enqueue; cap=1 would flush every
     * first arrival and prevent the queue ever reaching two readings. */
    uint8_t cap = 1;
    for(uint8_t candidate = 2; candidate <= max_cap; candidate *= 2) {
        if(f->rate_hz_x100 && (uint64_t)(candidate - 1u) * 100000u <=
           (uint64_t)s->deadline_ms * f->rate_hz_x100) cap = candidate;
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
    bool current_feasible = false;

    for(uint8_t pi = 0; pi < 2; pi++) {           /* profiles 1,2 */
        for(uint8_t ci = 0; ci < 3; ci++) {        /* caps 1,2,4 */
            uint8_t cap = cap_values[ci];
            if(cap > max_cap) continue;
            if(cap > 1 && (!f->rate_hz_x100 ||
               (uint64_t)(cap - 1u) * 100000u > (uint64_t)s->deadline_ms * f->rate_hz_x100)) continue;             /* MTU infeasible */
            if(s->cost_nj[pi][ci] == 0) continue;  /* No calibration data */

            if(pi + 1u == s->current_profile && cap == s->current_cap)
                current_feasible = true;
            uint64_t est = s->cost_nj[pi][ci];
            if(est < best_cost) {
                best_cost    = est;
                best_profile = pi + 1u;
                best_cap     = cap;
                any_feasible = true;
            }
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

    /* Dwell check. */
    if(current_feasible && s->initialized && s->min_dwell_ms > 0 &&
       (f->now_ms - s->last_switch_ms) < s->min_dwell_ms) {
        lab_policy_action out;
        out.profile  = s->current_profile;
        out.cap      = s->current_cap;
        out.reason   = LAB_POL_P1_DWELL;
        out.feasible = true;
        return out;
    }

    /* Saving check: compare best vs current cost.
     * If current action has no data, switch unconditionally (first useful data). */
    uint8_t cur_ci = (s->current_cap == 4) ? 2u : (s->current_cap == 2) ? 1u : 0u;
    uint64_t cur_cost = s->cost_nj[s->current_profile - 1u][cur_ci];

    if(current_feasible && cur_cost > 0) {
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
    s->current_profile = best_profile;
    s->current_cap     = best_cap;
    s->last_switch_ms  = f->now_ms;

    lab_policy_action out;
    out.profile  = best_profile;
    out.cap      = best_cap;
    out.reason   = LAB_POL_P1_BEST;
    out.feasible = true;
    return out;
}
