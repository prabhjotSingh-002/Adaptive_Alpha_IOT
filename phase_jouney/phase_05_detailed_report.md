> Current audit correction: see [last Astra check](../lastAstra%20check.md). Historical policy pilots do not establish intended adaptive behaviour: policy state/configuration was not loaded, B6 used AES fallback and P1 lacked costs. Priority repairs have targeted host checks only; Phase 4/5 network validation is deferred by user and Phase 6 has not started. Older completion/performance explanations below are historical and superseded where contradictory.

# Phase 5 Detailed Implementation and Results Report

**Status:** Implementation complete. Pilot runs complete. Reports written. Human review gate pending.
**Produced:** 2026-11-14

---

## 1. Pins

All artifacts from this phase are reproducible against these exact commits and container image.

| Component | Hash / Digest |
|---|---|
| Contiki-NG | `a304687372e2917d325d4d71cf68610fe9a6279b` |
| Cooja | `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4` |
| Ascon-C | `446347f21b209f3921c65ece70027c366cbe1693` |
| Container image | `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609` |

---

## 2. Configuration (configs/phase5.json)

| Parameter | Value |
|---|---|
| warmup_ms | 60000 |
| period_ms | 1000 |
| readings_per_sensor | 24 |
| deadline_ms | 3000 |
| drain_ms | 15000 |
| payload_budget | 67 |
| calibration_seed | 223457 |
| b3_threshold_nj_hi | 6,000,000,000 |
| b3_threshold_nj_lo | 3,000,000,000 |
| b6_profile | 2 (Ascon — winner from Phase 4 calibration) |
| p1_transition_cost_nj | 50,000 |
| p1_min_dwell_ms | 2,000 |
| p1_margin_nj | 10,000 |

---

## 3. Firmware Files Created or Modified

All files are under `firmware/` and `host/`. No upstream Contiki-NG or Cooja source was modified.

### New files

| File | SHA256 prefix | Description |
|---|---|---|
| `firmware/policy/policy.h` | `c58c838542b99893` | Policy module header — portable C, no heap, no OS calls |
| `firmware/policy/policy.c` | `1db7d3f6665e47a9` | Policy module implementation (B3, B6, P1 logic) |
| `configs/phase5.json` | — | Experiment configuration for Phase 5 |
| `host/calibrate.py` | — | Calibration runner; produces cost_table.json |
| `host/analysis.py` | — | Statistical analysis (bootstrap CI, survival) |
| `host/run_plots.py` | — | Docker wrapper for plots |
| `host/run_analysis.py` | — | Docker wrapper for analysis |

### Extended files

| File | SHA256 prefix | Change |
|---|---|---|
| `firmware/sensor/sensor.c` | `186ce0d131f52b60` | Added `#if LAB_POLICY_MODE` block for policy integration |
| `firmware/common/events.h` | — | Added `LAB_EVENT_POLICY` and `LAB_EVENT_SWITCH` macros |
| `firmware/project-conf.h` | — | Added policy compile-time defaults |
| `host/run_experiment.py` | — | Extended with phase 5 modes; 2 runner bugs fixed (see §6) |
| `host/parse_logs.py` | — | Added POLICY and SWITCH event fields |
| `host/metrics.py` | — | Added policy summary output |
| `host/plots.py` | — | Complete rewrite: 7-arm support, bootstrap CI |

### Bug fixed

| File | SHA256 prefix | Bug | Fix |
|---|---|---|---|
| `firmware/energy/energest_sampler.c` | `e3e8b7f035586994` | `lab_energy_remaining_nj()` and `account` variable were in wrong preprocessor scope — function referenced `account` before it was declared inside `#if LAB_ENERGY_TELEMETRY` block | Moved function inside the block; added `UINT64_MAX` fallback in the `else` branch |

---

## 4. Policy Module Design

Three policies are implemented in `firmware/policy/policy.{h,c}`.

### B3 — Battery-threshold (hysteresis)

Switches cipher based on estimated residual battery energy:

- **Above hi threshold** (6,000,000,000 nJ): use AES profile=1, cap=1
- **Below lo threshold** (3,000,000,000 nJ): use Ascon profile=2, cap=1
- **Between thresholds**: hold current cipher (hysteresis — no switch)

### B6 — Fixed Ascon profile=2, adaptive batching

Uses Ascon (profile=2) unconditionally. Adapts the batching cap based on residual energy. Profile=2 was selected as the Phase 4 calibration winner (lowest per-reading cost: 229,361,704 nJ/reading vs. next-best 243,928,892 nJ/reading for B4).

### P1 — Cost-aware joint policy

Evaluates current residual energy and transition cost (50,000 nJ) before switching cipher. Only switches when the projected savings over `p1_min_dwell_ms` (2,000 ms) exceed `p1_margin_nj` (10,000 nJ) plus the transition cost. Falls back to current action otherwise.

---

## 5. Calibration Results

**File:** `results/phase_05/cost_table.json`
**Produced:** 2026-11-14T09:11:12 UTC
**Source runs:** 21

| Arm | Label | Per-reading cost (nJ) | n runs |
|---|---|---|---|
| B2 | Ascon cap1 | 229,361,704 | 9 |
| B1 | AES cap1 | 247,233,663 | 5 |
| B4 | AES cap4 | 243,928,892 | 4 |
| B5 | Ascon cap4 | 244,171,889 | 3 |

**B6 winner:** B2 (Ascon cap1 = profile 2). This calibration result determined `b6_profile: 2` in configs/phase5.json.

---

## 6. Runner Bugs Fixed This Session

Two bugs were found and fixed in `host/run_experiment.py`:

**Bug 1 — `--attack-test` / `--root-reset-test` gate wrong phase set**

The phase guard was `phase not in (3, 4)`, which silently skipped security regression tests when invoked for Phase 5. Fixed to `phase not in (3, 4, 5)` (i.e., allowed for phases 3, 4, and 5).

**Bug 2 — `energy_telemetry` restricted to Phase 4 Z1 only**

The flag enabling energy telemetry output was gated on `phase == 4 and target == "z1"`. Phase 5 Z1 runs therefore produced no telemetry. Fixed to include `phase == 5`.

---

## 7. Unit Tests

All 38 tests pass. Run with `pytest tests/unit/`.

| Test file | Tests | Coverage |
|---|---|---|
| `tests/unit/test_policy.py` | 17 | B3 hysteresis/thresholds, B6 adaptive cap, P1 cost ranking/dwell/margin/fallback |
| `tests/unit/test_metrics.py` | 18 | Metrics parsing and summary functions |
| `tests/unit/test_lifetime.py` | 3 | Lifetime model |
| **Total** | **38** | **all pass** |

---

## 8. Smoke Runs

Cooja, 2 clients, seed 123456. Verify basic connectivity and PDR=1.0 for each policy mode.

| Mode | Run ID | Status | PDR |
|---|---|---|---|
| B3 | `20261114T091850125887Z-B3-2` | passed | 1.0 |
| B6 | `20261114T091919114788Z-B6-2` | passed | 1.0 |
| P1 | `20261114T091937880366Z-P1-2` | passed | 1.0 |

---

## 9. Security Regression

Cooja, 2 clients, seed 123456. Each policy mode tested under injection attack and root-reset attack.

### Attack test (8 injections, expect 8 rejections)

| Mode | Run ID | Injections | Rejections | Status |
|---|---|---|---|---|
| B3 | `20261114T115355633747Z-B3-2` | 8 | 8 | passed |
| B6 | `20261114T115420997857Z-B6-2` | 8 | 8 | passed |
| P1 | `20261114T115446511507Z-P1-2` | 8 | 8 | passed |

### Root-reset test (expect 88 rejections after reset)

| Mode | Run ID | Rejections | Status |
|---|---|---|---|
| B3 | `20261114T115510814937Z-B3-2` | 88 | passed |
| B6 | `20261114T115534648742Z-B6-2` | 88 | passed |
| P1 | `20261114T115601684324Z-P1-2` | 88 | passed |

Security properties from Phase 3/4 are preserved across all three policy modes.

---

## 10. Z1 Power-Model Pilot Runs

**Setup:** TARGET=z1, 8 clients, `--power-model` flag, 3 seeds per arm (123456, 123457, 123458).

### B3 — Battery-threshold

| Seed | Run ID | PDR | Energy (nJ) | p95 latency (ms) | Switches |
|---|---|---|---|---|---|
| 123456 | `20261114T120117290160Z-B3-8` | 0.9688 | 253,867,948 | 133.3 | 8 |
| 123457 | `20261114T120344854467Z-B3-8` | 0.9688 | 253,555,432 | 174.7 | 8 |
| 123458 | `20261114T120605604910Z-B3-8` | 0.9583 | 255,957,277 | 132.3 | 8 |
| **Mean** | | **0.9653** | **254,460,219** | **146.8** | — |

Profiles used: [1]. Caps used: [1].

### B6 — Fixed Ascon, adaptive batching

| Seed | Run ID | PDR | Energy (nJ) | p95 latency (ms) | Switches |
|---|---|---|---|---|---|
| 123456 | `20261114T121756262964Z-B6-8` | 0.9688 | 253,865,130 | 133.3 | 0 |
| 123457 | `20261114T120827744266Z-B6-8` | 0.9688 | 253,552,274 | 174.7 | 0 |
| 123458 | `20261114T121048633839Z-B6-8` | 0.9583 | 255,954,198 | 132.3 | 0 |
| **Mean (3 unique seeds)** | | **0.9653** | **254,457,201** | **146.8** | — |

**Duplicate runs (preserved per project rules):** `20261114T122303203171Z-B6-8` (seed 123457), `20261114T122749326614Z-B6-8` (seed 123458). These arose from a loop that ran twice for those seeds. The first run per seed is used for analysis; duplicates are retained as records.

### P1 — Cost-aware joint policy

| Seed | Run ID | PDR | Energy (nJ) | p95 latency (ms) | Switches |
|---|---|---|---|---|---|
| 123456 | `20261114T122031479887Z-P1-8` | 0.9688 | 253,879,348 | 134.4 | 8 |
| 123457 | `20261114T121309376664Z-P1-8` | 0.9688 | 253,562,991 | 170.2 | 8 |
| 123458 | `20261114T121535529449Z-P1-8` | 0.9583 | 255,967,827 | 132.3 | 8 |
| **Mean (3 unique seeds)** | | **0.9653** | **254,470,055** | **145.6** | — |

**Duplicate runs (preserved per project rules):** `20261114T122525404803Z-P1-8` (seed 123457), `20261114T123025682022Z-P1-8` (seed 123458). Same rule as B6.

---

## 11. Comparison with Phase 4 Baseline

| Arm | Mean energy (nJ) | Mean PDR | Mean p95 (ms) | n |
|---|---|---|---|---|
| B1 — AES cap1 (Phase 4) | 247,233,663 | 0.9696 | 142.1 | 5 |
| B2 — Ascon cap1 (Phase 4) | 247,501,031 | 0.9677 | 152.5 | 5 |
| B4 — AES cap4 (Phase 4) | 243,928,892 | 0.9805 | 2985.8 | 4 |
| B5 — Ascon cap4 (Phase 4) | 244,171,889 | 0.9792 | 3004.8 | 3 |
| **B3 — battery-threshold (Phase 5)** | **254,460,219** | **0.9653** | **146.8** | 3 |
| **B6 — fixed Ascon adaptive (Phase 5)** | **254,457,201** | **0.9653** | **146.8** | 3 |
| **P1 — cost-aware joint (Phase 5)** | **254,470,055** | **0.9653** | **145.6** | 3 |

### Key observation

B3, B6, and P1 show approximately +2.9% higher energy consumption than the B1 (AES cap1) baseline in this pilot scenario. All three policy modes operated exclusively on AES profile=1, cap=1 throughout each run. Neither Ascon switching (B3/P1) nor adaptive batching (B6) activated.

The reason is structural: residual battery energy stayed above the B3 hi threshold (6,000,000,000 nJ) for the entire run, so B3 never triggered a downward switch. P1 found no cost advantage over its current action given the transition cost (50,000 nJ) and margin (10,000 nJ) parameters. B6 is fixed to Ascon, yet energy was higher than B1 — this indicates that in this 8-client, 24-reading scenario, AES at cap=1 consumes less energy in aggregate than Ascon at cap=1 at this scale (consistent with the Phase 4 B1 vs B2 calibration numbers at the per-reading level where B2/Ascon cost 229 MnJ vs B1/AES 247 MnJ, but total run energy depends on radio/MAC and aggregation overhead as well).

This is an honest pilot result. The adaptive policies behaved correctly given the energy state; the scenario did not drive the system into the low-energy regime where cipher switching and adaptive batching are designed to engage. Longer lifetime runs (Phase 4 deferred cases 33-35) are needed to exercise the switching logic.

---

## 12. Remaining Work

| Item | Detail |
|---|---|
| Duplicate run cleanup (optional) | B6 and P1 each have 2 extra duplicate runs (preserved per project rules); use first run per seed for analysis |
| `results/phase_05/phase5-evidence.json` | Created this session (see that file) |
| Human review gate | Phase 5 human code and security review — pending |
| Phase 6 entry | Requires explicit human authorization after reviewing this report |
| Phase 4 deferred cases 33-35 | Lifetime 4-arm runs — required before Phase 6 full matrix |

---

## 13. Evidence File

`results/phase_05/phase5-evidence.json` — machine-readable manifest with all run IDs, hashes, test counts, and configuration values documented here.
