# Phase 5 — Implementation Plan

**Date:** 14 November 2026
**Status:** Planning complete; implementation starting now.
**Authority:** MASTER_IMPLEMENTATION_PLAN.md (unchanged), phase_4_5_6.md Section 5, IMPLEMENTATION_AND_DECISION_REVIEW.md W8/G5.

---

## What Phase 5 Adds

Three new modes on top of the existing B1/B2/B4/B5 infrastructure:

| Mode | Cipher | Batching | Description |
|------|--------|----------|-------------|
| B3 | Battery-threshold: AES below threshold, Ascon at/above | 1 (fixed) | Simple residual-energy threshold switch |
| B6 | Fixed best cipher (from calibration) | Adaptive cap 1/2/4 + deadline | Adaptive batching only ablation |
| P1 | Cost-aware profile selection | Adaptive cap 1/2/4 + deadline | Full joint policy |

All three reuse existing crypto/aggregation/energy firmware. New work: `firmware/policy/` module + calibration + 7-arm runner extension.

---

## Sync With Existing Code

### What we reuse unchanged
- `firmware/crypto/secure_packet.c` — seal/open with profile dispatch ✓
- `firmware/crypto/boot_gate.c` — dual-profile provisioning ✓
- `firmware/aggregate/aggregate.c` — offer/flush/build/commit queue ✓
- `firmware/energy/energy.c` + `energest_sampler.c` — budget/depletion ✓
- `firmware/sensor/sensor.c` — just needs `selected` profile + cap driven by policy ✓
- `host/run_experiment.py` — add B3/B6/P1 modes + calibration purpose ✓
- `host/metrics.py` / `host/plots.py` — add policy events + 7-arm plotting ✓

### What is new
- `firmware/policy/policy.h` + `policy.c` — portable, heap-free, shared for host+mote
- `firmware/common/events.h` — POLICY, SWITCH, FEATURE events
- `configs/phase5.json` — calibration + pilot config
- `host/calibrate.py` — cost table from Phase 4 static run summaries
- `results/phase_05/` — all Phase 5 evidence

---

## Ordered Work Packages

### P5.1 — Policy contract and calibration config
Files: `docs/policy-contract.md`, `configs/phase5.json`, `firmware/policy/policy.h`

Define:
- Action space: `(profile ∈ {1,2}, cap ∈ {1,2,4})`
- Features: `residual_nj`, `queue_count`, `oldest_hold_ms`, `rate_hz` (rolling 8-reading window)
- B3 threshold: `b3_threshold_nj` from calibration, one-way AES→Ascon (Ascon stays when residual below threshold)
- B6: fixed `b6_profile` from calibration winner, adaptive cap by queue/deadline
- P1: cost ranker over feasible actions, hysteresis `margin_nj_per_reading`, dwell `min_dwell_ms`
- Safe fallback: profile=1 (AES), cap=1 when estimates unavailable/stale
- No auth downgrade ever; no free root PDR oracle

### P5.2 — Calibration script
File: `host/calibrate.py`

Reads Phase 4 static run summaries (`results/phase_04/*/summary.json`) for B1/B2/B4/B5.
Computes per-mode: `energy_nj_per_delivered_reading`, `p95_delay_ms`, `reading_pdr`.
Outputs `results/phase_05/cost_table.json` — hashed, frozen before evaluation.
B6 winner = mode with lowest `energy_nj_per_delivered_reading` among passing PDR/delay.

### P5.3 — Policy C module
Files: `firmware/policy/policy.c`, `firmware/policy/policy.h`

Portable C, no heap, no OS calls. Compiled same for host tests and mote.

```c
typedef struct {
    uint8_t  profile;      /* 1=AES 2=Ascon */
    uint8_t  cap;          /* 1,2,4 */
    uint8_t  reason;       /* LAB_POL_* reason code */
    bool     feasible;
} lab_policy_action;

typedef struct {
    uint64_t residual_nj;
    uint16_t queue_count;
    uint32_t oldest_hold_ms;
    uint16_t rate_hz_x100;  /* rate * 100, integer */
    uint32_t now_ms;
} lab_policy_features;

typedef struct {
    /* Config — set once from calibration */
    uint32_t b3_threshold_nj_hi;  /* enter Ascon above this */
    uint32_t b3_threshold_nj_lo;  /* hysteresis lo bound */
    uint8_t  b6_profile;
    uint64_t cost_nj[2][3];       /* [profile-1][cap_index] nj/reading */
    uint32_t transition_cost_nj;
    uint32_t min_dwell_ms;
    uint32_t deadline_ms;
    uint8_t  payload_budget;
    uint8_t  reserved_bytes;
    /* Runtime state */
    uint8_t  current_profile;
    uint8_t  current_cap;
    uint32_t last_switch_ms;
    bool     initialized;
} lab_policy_state;

lab_policy_action lab_policy_b3(lab_policy_state *s, const lab_policy_features *f);
lab_policy_action lab_policy_b6(lab_policy_state *s, const lab_policy_features *f);
lab_policy_action lab_policy_p1(lab_policy_state *s, const lab_policy_features *f);
```

Rules:
- B3: if `residual_nj < b3_threshold_nj_lo` → profile=2; if `residual_nj > b3_threshold_nj_hi` → profile=1 (hysteresis band). Cap always 1.
- B6: cap=min(queue_count,4) if oldest_hold_ms > deadline_ms*0.5 else 1; profile=b6_profile fixed.
- P1: for each `(p,c)` in action space, check MTU fit, estimate cost, pick min; switch only if saving > transition_cost + margin AND dwell elapsed.
- All: if context locked/depleted → fallback AES cap=1. Never return profile=0.

### P5.4 — Sensor integration
File: `firmware/sensor/sensor.c` (small additions)

Add `#if LAB_POLICY_MODE` block:
- Call `lab_policy_b3/b6/p1` before `flush()` to get `(profile, cap)`.
- Update `queue.cap` and `selected` from policy output.
- Emit `POLICY` event: `profile, cap, reason, residual_nj, oldest_hold_ms, queue_count`.
- Emit `SWITCH` event when profile or cap changes from previous tick.
- Generated-conf.h adds: `LAB_POLICY_MODE` (0=static,1=B3,2=B6,3=P1), `LAB_B3_THRESHOLD_NJ_HI`, `LAB_B3_THRESHOLD_NJ_LO`, `LAB_B6_PROFILE`, `LAB_P1_TRANSITION_COST_NJ`, `LAB_P1_MIN_DWELL_MS`.

### P5.5 — Runner extension
File: `host/run_experiment.py`

Add modes `B3`, `B6`, `P1` to `configs/phase5.json`.
Add `--mode calibration` purpose (runs B1/B2/B4/B5 with calibration seed 223457).
Pass policy constants from `configs/phase5.json` into `defs` → `generated-conf.h`.
Add `LAB_POLICY_MODE` def (0/1/2/3).
Validate: B3/B6/P1 require `--phase 5`, `--target z1`, `--power-model`.
Preserve all existing Phase 4 paths unchanged.

### P5.6 — Parser and metrics extension
Files: `host/parse_logs.py`, `host/metrics.py`, `host/plots.py`

`parse_logs.py`: add `POLICY` and `SWITCH` event parsers.
`metrics.py`: add `policy_switches`, `decision_overhead_ms`, `fallback_count`, `switch_reasons` to summary.
`plots.py`: extend to 7 arms (B1/B2/B3/B4/B5/B6/P1); group-aware bar chart energy per delivered reading.

### P5.7 — Pilot runs
Sequence:
1. Calibration run (seed 223457, B1/B2/B4/B5, 2 clients, power model) → `cost_table.json`
2. Smoke: B3/B6/P1 root+2, native, seed 123456
3. Security regression: B3/B6/P1 attack-test, root-reset-test
4. 7-arm root+8 pilot: seeds 123456/123457/123458 (21 runs)

### P5.8 — Reports
- `phase_jouney/phase_05_environment_and_implementation.md`
- `phase_jouney/phase_05_detailed_report.md`
- `results/phase_05/phase5-evidence.json`
- Stop before Phase 6.

---

## Key Constraints (from master + phase_4_5_6.md)

1. Policy never disables authentication or falls back to N0.
2. Cap change flushes current queue through existing `lab_should_flush` path.
3. Profile change happens at batch boundary — already sealed packets keep their context.
4. `firmware/policy/` compiled identically for host tests and mote (no OS calls).
5. B6 cipher winner chosen from calibration evidence, never from final evaluation outcome.
6. All 7 modes use identical generated readings (same seed = same GEN trace).
7. Single runner lock, serial `-j1` builds, no concurrent experiments.

---

## Files Created/Modified

| File | Action |
|------|--------|
| `firmware/policy/policy.h` | NEW |
| `firmware/policy/policy.c` | NEW |
| `firmware/policy/Makefile` | NEW |
| `firmware/sensor/sensor.c` | EXTEND (policy block under `#if LAB_POLICY_MODE`) |
| `firmware/common/events.h` | EXTEND (POLICY, SWITCH events) |
| `firmware/project-conf.h` | EXTEND (policy defaults) |
| `configs/phase5.json` | NEW |
| `host/calibrate.py` | NEW |
| `host/run_experiment.py` | EXTEND (B3/B6/P1 modes, policy defs) |
| `host/parse_logs.py` | EXTEND (POLICY/SWITCH parsing) |
| `host/metrics.py` | EXTEND (policy metrics) |
| `host/plots.py` | EXTEND (7-arm plotting) |
| `tests/unit/test_policy.py` | NEW |
| `docs/policy-contract.md` | NEW |
| `results/phase_05/` | NEW (all Phase 5 evidence) |

---

## Implementation Order (this session)

1. `firmware/policy/policy.h` + `policy.c` — portable module
2. Policy tests `tests/unit/test_policy.py` — host-only, no Cooja
3. `events.h` extensions
4. `project-conf.h` defaults
5. `sensor.c` policy integration
6. `configs/phase5.json`
7. `host/calibrate.py`
8. `host/run_experiment.py` extension
9. `host/parse_logs.py` + `metrics.py` + `plots.py` extensions
10. Run calibration → smoke → pilot
11. Reports
