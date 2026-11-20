#ifndef LAB_POLICY_H
#define LAB_POLICY_H
#include <stdint.h>
#include <stdbool.h>

/* Policy mode identifiers — written into LAB_POLICY_MODE by runner. */
#define LAB_POLICY_STATIC 0u  /* B1/B2/B4/B5: no policy, sensor uses fixed profile/cap */
#define LAB_POLICY_B3     1u  /* Battery-threshold cipher switch, fixed cap 1 */
#define LAB_POLICY_B6     2u  /* Fixed best cipher, adaptive cap/deadline */
#define LAB_POLICY_P1     3u  /* Joint cost-aware profile + adaptive cap */

/* Reason codes emitted in POLICY events. */
#define LAB_POL_STATIC       0u  /* No policy active */
#define LAB_POL_FALLBACK     1u  /* Estimates unavailable/stale — using safe default */
#define LAB_POL_B3_AES       2u  /* B3: residual above hi threshold */
#define LAB_POL_B3_ASCON     3u  /* B3: residual below lo threshold */
#define LAB_POL_B3_HOLD      4u  /* B3: within hysteresis band, no switch */
#define LAB_POL_B6_FIXED     5u  /* B6: fixed cipher from calibration */
#define LAB_POL_P1_BEST      6u  /* P1: switched to lower cost action */
#define LAB_POL_P1_DWELL     7u  /* P1: dwell timer not elapsed, retain current */
#define LAB_POL_P1_NOSAVE    8u  /* P1: saving < transition cost + margin */
#define LAB_POL_NO_FEASIBLE  9u  /* No feasible action found, fallback */
#define LAB_POL_DEPLETED    10u  /* Context depleted/locked */

/* Sensor-observable features passed to every policy tick. */
typedef struct {
    uint64_t residual_nj;      /* Remaining energy budget from energy module */
    uint16_t queue_count;      /* Current aggregator occupancy */
    uint32_t oldest_hold_ms;   /* How long oldest queued reading has been waiting */
    uint16_t rate_hz_x100;     /* Rolling generation rate * 100 (integer, e.g. 100 = 1.00 Hz) */
    uint32_t now_ms;           /* Current simulator time */
    bool     context_active;   /* Whether the current profile context is active */
} lab_policy_features;

/* Output from one policy tick. */
typedef struct {
    uint8_t  profile;      /* 1 = AES-CCM, 2 = Ascon-AEAD128 */
    uint8_t  cap;          /* Batch cap: 1, 2, or 4 */
    uint8_t  reason;       /* LAB_POL_* code */
    bool     feasible;     /* false => fell back to safe default */
} lab_policy_action;

/* Persistent policy state. Zero-initialise before first use; set config fields. */
typedef struct {
    /* ---- Configuration (set once from calibration/generated-conf.h) ---- */
    uint64_t b3_threshold_nj_hi;   /* B3: enter AES above this residual */
    uint64_t b3_threshold_nj_lo;   /* B3: enter Ascon below this residual (hysteresis) */
    uint8_t  b6_profile;           /* B6: fixed cipher from calibration (1 or 2) */

    /* P1 cost table: cost_nj_per_reading[profile-1][cap_index] where cap_index 0=cap1,1=cap2,2=cap4 */
    uint64_t cost_nj[2][3];

    uint64_t transition_cost_nj;   /* P1: one-off cost of switching profile */
    uint64_t margin_nj_per_reading;/* P1: hysteresis — required saving per reading */
    uint32_t min_dwell_ms;         /* P1: minimum time between switches */
    uint32_t deadline_ms;          /* Aggregator deadline (copy from config) */
    uint8_t  payload_budget;       /* Max payload bytes */
    uint8_t  reserved_bytes;       /* Tag size (16) */

    /* ---- Runtime state (updated by policy functions) ---- */
    uint8_t  current_profile;      /* Profile active last tick */
    uint8_t  current_cap;          /* Cap active last tick */
    uint32_t last_switch_ms;       /* Time of last profile or cap change */
    bool     initialized;          /* True after first successful tick */
} lab_policy_state;

/* Returns the max cap that fits within the payload budget for a given profile. */
uint8_t lab_policy_max_cap(const lab_policy_state *s);

/* B3: battery-threshold cipher selection, fixed cap=1.
 * Transitions: residual > hi → AES; residual < lo → Ascon; between → hold current.
 * Never downgrades auth. Returns safe fallback if context inactive. */
lab_policy_action lab_policy_b3(lab_policy_state *s, const lab_policy_features *f);

/* B6: fixed best cipher from calibration, adaptive cap by queue/deadline.
 * Cap chosen before enqueue using rate, deadline and payload limits.
 * Never changes profile. Returns safe fallback if context inactive. */
lab_policy_action lab_policy_b6(lab_policy_state *s, const lab_policy_features *f);

/* P1: joint cost-aware selection over (profile, cap) action space.
 * Estimates cost per delivered reading from cost table.
 * Switches only when saving > transition_cost + margin AND dwell elapsed.
 * Returns safe fallback on stale/missing data or no feasible action. */
lab_policy_action lab_policy_p1(lab_policy_state *s, const lab_policy_features *f);

#endif /* LAB_POLICY_H */
