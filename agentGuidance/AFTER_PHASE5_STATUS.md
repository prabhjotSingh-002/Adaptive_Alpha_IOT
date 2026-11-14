> Current audit correction: see [last Astra check](../lastAstra%20check.md). Historical policy pilots do not establish intended adaptive behaviour: policy state/configuration was not loaded, B6 used AES fallback and P1 lacked costs. Priority repairs have targeted host checks only; Phase 4/5 network validation is deferred by user and Phase 6 has not started. Older completion/performance explanations below are historical and superseded where contradictory.

# After-Phase-5 Status and Handoff

**Date:** 2026-11-14
**State:** Phase 5 implementation complete. Pilot runs complete. Reports written. Human review gate pending. Do not start Phase 6 without explicit human authorization.

---

## 1. Project Overview

This project implements and evaluates an adaptive policy for energy-aware secure sensing on IoT nodes running Contiki-NG, simulated in Cooja. Sensor nodes collect readings, encrypt them (AES-CCM or Ascon-128), and transmit aggregated packets to a RPL root over IEEE 802.15.4. The core research question is whether an adaptive cipher-and-batching policy can extend node lifetime without compromising security or delivery quality.

The experiment design uses seven arms:

| Arm | Description |
|---|---|
| N0 | Unprotected baseline (no authentication or encryption) |
| B1 | AES-CCM, cap=1 (single-reading packets) |
| B2 | Ascon-128, cap=1 |
| B4 | AES-CCM, cap=4 (batched packets) |
| B5 | Ascon-128, cap=4 |
| B3 | Adaptive battery-threshold policy (B3 switches between AES and Ascon by residual energy) |
| B6 | Fixed Ascon profile=2, adaptive batching cap |
| P1 | Cost-aware joint policy (cipher + batching, transition cost accounted) |

The hardware target is the Texas Instruments Z1 mote (MSP430F2617 + CC2420), modelled via Contiki-NG's Energest framework. The container image is `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`.

---

## 2. What Is Complete (by Phase)

### Phase 1 — Environment and official RPL demo
Contiki-NG and Cooja set up in the official container. Official RPL UDP example compiled and simulated. Environment verified.

**Status:** Complete. Human G0 two-student independent review pending.

### Phase 2 — Reading protocol, N0 transport, aggregation
Custom reading protocol implemented. N0 (unprotected) transport working end-to-end. Aggregation logic in place. Host parsing and metrics tools operational.

**Status:** Complete.

### Phase 3 — AES-CCM secure pilot
AES-CCM authentication and encryption integrated into the firmware. Security contract documented. Injection and root-reset tests pass.

**Status:** Complete.

### Phase 4 — Ascon + energy model + B1/B2/B4/B5 static pilots
Ascon-128 integrated. Energest-based power model implemented. Static baseline arms B1, B2, B4, B5 piloted on Z1 with power model. Phase 4 calibration run (21 source runs) produced `results/phase_05/cost_table.json` (Ascon cap1 = B2 is the cheapest per-reading arm at 229,361,704 nJ/reading).

Seven matrix cases deferred to Phase 6 (see §4).

**Status:** Core complete. 7 deferred cases documented in `phase_jouney/phase_04_leftover.md`.

### Phase 5 — Adaptive policy B3/B6/P1
Policy module implemented (`firmware/policy/policy.{h,c}`). Three policies (B3, B6, P1) implemented, unit tested, smoke tested, and security regression tested. Z1 power-model pilot completed (3 seeds × 3 arms = 9 unique runs; 4 duplicate runs preserved). Reports written.

**Status:** Implementation complete. Pilot complete. Reports written. Human review gate pending.

---

## 3. Phase 5 Results Summary

### Pins

| Component | Hash |
|---|---|
| Contiki-NG | `a304687372e2917d325d4d71cf68610fe9a6279b` |
| Cooja | `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4` |
| Ascon-C | `446347f21b209f3921c65ece70027c366cbe1693` |
| Container | `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609` |

### Unit tests
38 tests total (test_policy: 17, test_metrics: 18, test_lifetime: 3) — all pass.

### Security regression
All 6 security tests pass (3 modes × 2 test types): 8/8 injections rejected in every attack test, 88 rejections after root-reset in every root-reset test.

### Z1 pilot (8 clients, power model)

| Arm | Mean energy (nJ) | Mean PDR | Mean p95 latency (ms) | Seeds |
|---|---|---|---|---|
| B3 | 254,460,219 | 0.9653 | 146.8 | 3 |
| B6 | 254,457,201 | 0.9653 | 146.8 | 3 |
| P1 | 254,470,055 | 0.9653 | 145.6 | 3 |

### Phase 4 baseline (for comparison)

| Arm | Mean energy (nJ) | Mean PDR | Mean p95 latency (ms) | n |
|---|---|---|---|---|
| B1 — AES cap1 | 247,233,663 | 0.9696 | 142.1 | 5 |
| B2 — Ascon cap1 | 247,501,031 | 0.9677 | 152.5 | 5 |
| B4 — AES cap4 | 243,928,892 | 0.9805 | 2985.8 | 4 |
| B5 — Ascon cap4 | 244,171,889 | 0.9792 | 3004.8 | 3 |

### Key observation

B3, B6, and P1 show approximately +2.9% higher energy than the B1 (AES cap1) baseline in this pilot. All three policy modes operated on AES profile=1, cap=1 throughout. Cipher switching did not activate in any run because residual battery energy stayed above the B3 hi threshold (6,000,000,000 nJ) for the full run duration, and P1 found no switching action with positive net savings. This is an honest, expected pilot outcome — the scenario did not drive the system into the low-energy regime where the adaptive policies are designed to engage. Longer lifetime runs (Phase 4 deferred cases 33–35) are required to exercise the switching logic.

---

## 4. Phase 4 Leftover — Pending Runs

Seven cases were deferred from Phase 4 and are documented with commands in `phase_jouney/phase_04_leftover.md`. They must be completed before or during Phase 6.

| Case | Description | Priority | Est. time |
|---|---|---|---|
| 29 | Boundary: `--period-ms 4000` | Low | ~20 min |
| 30 | Boundary: `--payload-budget 47` | Low | ~10 min |
| 31 | Depletion-sensitivity 125 ms, seed 223456 | Medium | ~15 min |
| 32 | Depletion-sensitivity 250 ms, seed 223456 | Medium | ~15 min |
| 33 | Lifetime 4-arm, seed 123456 | **High — required for Phase 6** | ~40 min |
| 34 | Lifetime 4-arm, seed 123457 | **High — required for Phase 6** | ~40 min |
| 35 | Lifetime 4-arm, seed 123458 | **High — required for Phase 6** | ~40 min |

Cases 33–35 are the Phase 4 lifetime runs that provide the survival-curve baseline needed before comparing Phase 5 and 6 policy arms in Phase 6's main matrix.

Commands for all seven cases are in `phase_jouney/phase_04_leftover.md`.

---

## 5. Phase 5 Data Cleanup Needed

### B6 — 5 runs exist for 3 seeds

The runner loop executed twice for seeds 123457 and 123458, producing 2 duplicate runs:

- `20261114T122303203171Z-B6-8` (seed 123457 duplicate)
- `20261114T122749326614Z-B6-8` (seed 123458 duplicate)

These are preserved per project rules. For analysis, use the first run per seed (the three listed in the evidence file under `B6.runs`). Do not delete the duplicates.

### P1 — 5 runs exist for 3 seeds

Same situation. Duplicate runs:

- `20261114T122525404803Z-P1-8` (seed 123457 duplicate)
- `20261114T123025682022Z-P1-8` (seed 123458 duplicate)

Same rule: preserve, use first run per seed for analysis.

---

## 6. Phase 6 — Full Plan

### 6.1 Entry requirement

Phase 5 reports are written ✅. Human review of Phase 5 implementation and results is **pending** (human gate). Phase 6 must not start until a human reviewer has explicitly authorized it after reviewing:

- `phase_jouney/phase_05_detailed_report.md`
- `results/phase_05/phase5-evidence.json`
- `firmware/policy/policy.{h,c}` and the firmware changes

### 6.2 F6.1 — Scenario scaling

The current runner and `.csc` scenario files are limited to 8 clients. The Cooja boot gate tracks contexts, and the limit is 16 contexts (8 sensors × 2 profiles = 16; 9 sensors would require 18 contexts and overflow). Scaling to 10- or 20-node experiments requires:

1. New `.csc` scenario files for 10-node and 20-node topologies.
2. A fix to the boot gate context-dimension calculation to support more than 8 clients.
3. Validation that the runner passes the correct node count to Cooja.

### 6.3 F6.2 — Experiment protocol freeze

Two files do not yet exist and must be created before the main matrix starts:

- `docs/experiment-protocol.md` — describes the full experimental procedure, including seed selection, run ordering, stopping rules, and analysis plan.
- `configs/phase6.json` — experiment configuration for Phase 6.

Proposed held-out seeds: 423456–423465 (10 seeds for the main matrix).

### 6.4 F6.3 — Runner matrix engine

`host/run_experiment.py` runs experiments serially, one at a time. For the Phase 6 matrix, the runner needs:

- Matrix scheduling: enumerate all (mode × topology × size × rate × seed) combinations and schedule them in a reproducible order.
- Resume capability: skip already-completed runs (by run ID or manifest check) so a partial matrix can be continued after interruption.
- Group manifests: produce a per-group summary JSON after each subset completes.

### 6.5 F6.4 — Full experiment matrix

The master plan proposes: 7 modes × 2 topologies × 2 sizes × 2 rates × 10 seeds = 560 runs.

A realistic reduced matrix for the first Phase 6 iteration: 7 modes × 1 topology × 1 size × 1 rate × 5 seeds = 35 runs minimum. The lifetime matrix (survival curves, FND/HND) is separate and uses Phase 4 deferred cases 33–35 as its starting point.

The 35-run reduced matrix provides enough data for statistical comparison of B3/B6/P1 against B1/B2 baselines. The full 560-run matrix is the stretch goal.

### 6.6 F6.5 — Statistics

`host/analysis.py` and `host/plots.py` were implemented in this session. Current capabilities:

- Bootstrap confidence intervals (pandas + numpy, available in Docker ✅)
- Policy summary output
- 7-arm comparison plots

Gap: `scipy` is not installed in the current Docker container. Survival analysis (FND/HND curves) and parametric tests require scipy. Options:

1. Install scipy inside the container at run time via `apt install python3-scipy` (or pip).
2. Build a custom Docker image that extends `contiker/contiki-ng` with scipy pre-installed.
3. Run analysis scripts outside the container on the host, with matching Python version.

Option 1 is simplest for now; option 2 is correct for reproducibility.

### 6.7 F6.6 — Reproducibility

Two files are missing that are required for a fully reproducible project:

- `host/requirements.lock` — pinned Python dependency versions for host tools.
- `.github/workflows/ci.yml` — CI workflow that runs unit tests and validates configs on every push.

Independent clean-machine reproduction (a second person replicating results on a different machine from the pinned container and commits) is a human gate — it cannot be automated.

### 6.8 F6.7 — Release

The following are needed for final release and are not yet created:

- `README.md` at the repository root (currently absent).
- `results/phase_06/phase6-evidence.json` — machine-readable evidence manifest for Phase 6.
- Manuscript draft.
- Git release tag with signed commit, linking the tag to the evidence files and container digest.

### 6.9 Blockers summary

| Item | Type | Detail |
|---|---|---|
| boot_gate context limit (16 max) | **BLOCKER** | Cannot run 9+ sensors without fixing boot gate dimension calculation and creating new scenarios |
| Experiment protocol not frozen | **BLOCKER** | `docs/experiment-protocol.md` and `configs/phase6.json` do not exist; cannot start main matrix without these |
| Human authorization required | **BLOCKER** | Phase 6 must not start until human reviewer authorizes after Phase 5 review |
| Python scipy not in Docker | Not a blocker | Matplotlib and numpy are available; scipy can be installed on demand or via custom image |
| Firmware changes | Not a blocker | No firmware changes are needed for Phase 6 — all three policies are already implemented |

---

## 7. Tools Available Now

| Command | Purpose |
|---|---|
| `python3 host/run_experiment.py` | Run experiments (all phases 2–5) |
| `python3 host/run_analysis.py --phase 4` | Statistical analysis via Docker |
| `python3 host/run_plots.py --phase 4 --output results/phase_04/figures/out.png` | Plots via Docker |
| `python3 host/validate_phase4.py` | Phase 4 validation matrix |
| `python3 host/calibrate.py` | Calibration runner; produces cost_table.json |
| `python3 host/analysis.py` | Statistical analysis (direct, not via Docker) |
| `pytest tests/unit/` | Run all 38 unit tests |

---

## 8. Human Gates (Cannot Be Automated)

These gates require a human action and cannot be cleared by the agent.

| Gate | Description | Status |
|---|---|---|
| G0 | Two-student independent review of official RPL tutorial (Phase 1) | Pending |
| Phase 4 human review | Code and security review of Phase 4 firmware and results | Pending |
| Phase 5 human review | Code and security review of Phase 5 firmware (policy module) and results | **Pending — required before Phase 6** |
| Phase 6 entry authorization | Explicit authorization to begin Phase 6 after reviewing this report | **Pending** |
| Independent reproduction | Clean-machine reproduction by a second person using pinned container and commits | Pending |
| Final release approval | Human sign-off on results, manuscript, and git release tag | Pending |

---

## 9. File Locations Quick Reference

| Category | Path |
|---|---|
| Master plan | `PLANS/MASTER_IMPLEMENTATION_PLAN.md` |
| Phase 5 implementation plan | `PLANS/PHASE_05_IMPLEMENTATION_PLAN.md` |
| Decision review | `PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md` |
| Phase journals | `phase_jouney/` |
| Phase 5 detailed report | `phase_jouney/phase_05_detailed_report.md` |
| Phase 4 leftover cases | `phase_jouney/phase_04_leftover.md` |
| Results (all phases) | `results/phase_01/` through `results/phase_05/` |
| Phase 5 evidence manifest | `results/phase_05/phase5-evidence.json` |
| Phase 4 evidence manifest | `results/phase_04/phase4-evidence.json` |
| Calibration cost table | `results/phase_05/cost_table.json` |
| Policy firmware | `firmware/policy/policy.h`, `firmware/policy/policy.c` |
| Sensor firmware | `firmware/sensor/sensor.c` |
| Energy sampler (bug fixed) | `firmware/energy/energest_sampler.c` |
| Other firmware | `firmware/crypto/`, `firmware/aggregate/`, `firmware/common/`, `firmware/root/` |
| Host tools | `host/` (run_experiment.py, calibrate.py, analysis.py, plots.py, run_plots.py, run_analysis.py, parse_logs.py, metrics.py) |
| Configs | `configs/phase2.json` through `configs/phase5.json`, `configs/power-z1-v1.json` |
| Docs | `docs/` (architecture.md, protocol.md, threat-model.md, phase4-security-contract.md, etc.) |
| Unit tests | `tests/unit/test_policy.py`, `tests/unit/test_metrics.py`, `tests/unit/test_lifetime.py` |
