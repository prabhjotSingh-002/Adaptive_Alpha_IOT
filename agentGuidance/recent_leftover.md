# Recent Leftover — What Remains To Do

**Date:** 14 November 2026
**Mid-term deadline:** 17 November 2026 (Monday 16 Nov is evidence freeze)

Ye file batati hai ki abhi tak kya implement ho gaya hai aur aage kya karna bacha hai — seedha aur honestly. Koi inflate nahi, koi invented result nahi.

---

## MASTER PROMPT — Project Ka Poora Context

> **Kisi bhi AI agent ko ye section pehle padhna chahiye. Ye project ka complete mental model hai.**

---

### Project Kya Hai

**Research project:** Contiki-NG + Cooja simulator pe IoT network — energy-aware adaptive security protocol.

**Core research question:** Kya ek small adaptive policy jo cipher aur batch size dono choose kare, energy per authenticated delivered reading reduce kar sakti hai vs fixed static modes — bina security compromise kiye?

**Team:** 3 students. **Deadline:** Mid-term evaluation **17 November 2026**. Evidence freeze **16 November 2026 EOD**.

**Scope strictly:** 100% software only. No physical hardware. No custom crypto primitives. No invented logs or energy claims.

---

### Architecture — Kya Bana Hai

```
IoT Sensor Nodes (Z1 motes, emulated in Cooja/MSPSim)
    ↓  UDP over 6LoWPAN/RPL
Root Node (RPL root, receives + authenticates)
    ↓  Cooja logs → host/parse_logs.py
Host Analysis Pipeline
    host/run_experiment.py  → builds firmware, runs Cooja, parses output
    host/metrics.py         → sole metric calculator
    host/calibrate.py       → cost table from static run summaries
    host/plots.py           → charts from validated summaries only
```

**Firmware modules** (all under `firmware/`):

| Module | Kya karta hai |
|--------|--------------|
| `common/protocol.c` | Wire encoding — header 11 bytes, reading 10 bytes, cap 4 |
| `aggregate/aggregate.c` | Bounded queue, deadline flush, drop accounting |
| `crypto/aes_ccm.c` | AES-128-CCM wrapper (Contiki software backend) |
| `crypto/ascon_aead.c` | Ascon-AEAD128 wrapper (pinned official ref) |
| `crypto/secure_packet.c` | Seal/open with profile dispatch, nonce, replay |
| `crypto/boot_gate.c` | One-use provisioning gate, 4-byte mailbox |
| `energy/energy.c` | Checked integer energy accounting, budget |
| `energy/energest_sampler.c` | Energest counters → ENERGY_RAW/MODEL events |
| `policy/policy.c` | B3/B6/P1 adaptive policy — portable C, no heap |
| `sensor/sensor.c` | Contiki process — generates readings, calls all modules |
| `root/root.c` | Contiki process — receives, authenticates, deduplicates |

---

### Protocol — Wire Format

```
[version 1B][sender_id 2B][profile 1B][epoch 2B][counter 4B][count 1B] = 11 bytes AAD header
[readings N×10B ciphertext]
[tag 16B]
Total: 11 + N×10 + 16 bytes  (N = 1,2,4)
Protected lengths: 37 / 47 / 57 / 67 bytes
```

**Profile 1 = AES-128-CCM. Profile 2 = Ascon-AEAD128. Profile 0 = N0 (unprotected diagnostic only, never in secure comparison).**

Nonce = `(node_id, profile, epoch, counter)` encoded — unique per packet. Counter never reuses. Reset → locked context, no regrant with same key.

---

### 7 Experiment Modes

| Mode | Cipher | Cap | Policy | Description |
|------|--------|-----|--------|-------------|
| N0 | None | — | None | Unprotected diagnostic ONLY — never security-equivalent |
| B1 | AES | 1 | Static | Fixed AES, 1 reading/packet — primary static baseline |
| B2 | Ascon | 1 | Static | Fixed Ascon, 1 reading/packet |
| B4 | AES | 4 | Static | Fixed AES, batch 4 — aggregation baseline |
| B5 | Ascon | 4 | Static | Fixed Ascon, batch 4 |
| B3 | Threshold | 1 | B3 policy | Battery-threshold cipher switch |
| B6 | Ascon (calib) | 1–4 | B6 policy | Fixed best cipher + adaptive batch |
| P1 | Cost-aware | 1–4 | P1 policy | Joint cost-aware profile + adaptive batch |

---

### Phase History — Kya Kab Hua

| Phase | Kya tha | Status |
|-------|---------|--------|
| 1 | Official 9-node RPL demo, environment setup | Complete (automated); G0 human review pending |
| 2 | Reading protocol, N0 transport, aggregation | Complete |
| 3 | AES-CCM end-to-end, secure pilot | Complete |
| 4 | Ascon + energy model + dual-profile + security matrix | Automated complete; 7 runs deferred; human review pending |
| 5 | B3/B6/P1 adaptive policy + calibration + pilot | **In progress** — implementation done, Z1 + pilot runs pending |
| 6 | Full 560-run matrix, statistics, reproducibility, release | Not started |

---

### Pinned Dependencies (DO NOT CHANGE)

| Dependency | Pin |
|-----------|-----|
| Contiki-NG | `a304687372e2917d325d4d71cf68610fe9a6279b` |
| Cooja | `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4` |
| Ascon-C | `446347f21b209f3921c65ece70027c366cbe1693` |
| Container | `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609` |

**Authoritative plan hashes (must remain unchanged):**
- Master: `2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385`
- Decision review: `69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a`

---

### Non-Negotiable Rules

1. **N0 never in secure comparison.** It is unprotected. Never label it AES-CCM/Ascon.
2. **Never invent logs, energy values, or test results.** Only actual run output counts.
3. **One writer at a time.** Lock: `results/phase_02/.runner.lock`. Serial `-j1` builds.
4. **Never modify upstream Contiki/Cooja/Ascon source.**
5. **Never invent crypto primitives.** Use only pinned official implementations.
6. **Policy never disables authentication.** B3/B6/P1 always use profile 1 or 2.
7. **Preserve ALL failures.** Failed runs stay as evidence, not deleted or relabelled.
8. **Stop before next phase.** Write reports, wait for user instruction.
9. **Human gates stay pending** until a human actually performs them.

---

### Key Files To Read Before Working

```
AGENTS.md                                    ← collaboration rules
PLANS/MASTER_IMPLEMENTATION_PLAN.md          ← authoritative scope (DO NOT EDIT)
PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md  ← reuse decisions (DO NOT EDIT)
phase_4_5_6.md                               ← consolidated roadmap
PLANS/PHASE_05_IMPLEMENTATION_PLAN.md        ← current phase plan
phase_jouney/phase_04_environment_and_implementation.md  ← phase 4 journal
phase_jouney/phase_05_environment_and_implementation.md  ← phase 5 journal
results/phase_04/phase4-evidence.json        ← gate ledger
results/phase_05/cost_table.json             ← calibration output
recent_leftover.md                           ← THIS FILE — current remaining work
```

---

### Calibration Result (Frozen)

Phase 4 static pilot data se cost table (14 Nov 2026, `results/phase_05/cost_table.json`):

| Mode | Mean Energy/Reading | Samples |
|------|--------------------|---------| 
| **B2 (Ascon cap1)** | **229,361,705 nJ** ← B6 winner | 9 |
| B5 (Ascon cap4) | 244,171,890 nJ | 3 |
| B4 (AES cap4) | 243,928,893 nJ | 4 |
| B1 (AES cap1) | 247,233,663 nJ | 5 |

**B6 uses Ascon (profile 2).** P1 cost array: `[[247M, 0, 244M], [229M, 0, 244M]]` — cap=2 cells empty (no Phase 4 B2/4 data).

---

### Test Status (14 Nov 2026)

```
Python unit tests: 38/38 PASS
  - 21 Phase 4 metrics/lifetime/parser tests
  - 17 Phase 5 policy tests (B3/B6/P1 logic)

Phase 4 matrix: 28/35 cases PASS (7 deferred)
Phase 5 smoke (native): B3/B6/P1 — all 3 PASS
Phase 5 Z1 runs: 0 (PENDING)
Phase 5 7-arm pilot: 0/21 (PENDING)
```

---

## Current State — Kya Ho Chuka Hai

### Phase 1–3: Complete
- Official 9-node RPL network, AES-CCM secure pilot, aggregation — done.

### Phase 4: Automated implementation complete, 7 runs deferred
- Dual-profile crypto (AES + Ascon), energy model, security matrix 28/35 cases pass.
- **7 cases deferred** (boundary 4000ms, 47-byte, 5 lifetime runs) — time constraint.
- Human review/reproduction: pending (never performed).

### Phase 5: Initial implementation done, runs pending
- Policy module B3/B6/P1 implemented and tested.
- Native smoke runs (B3/B6/P1, 2 clients) — all pass.
- Calibration run done: **B6 winner = Ascon (B2), 229M nJ/reading**.
- **Z1 runs and 7-arm pilot not yet run.**

---

## SECTION A — Actual Implementation Work (New Code / Simulations)

Ye woh kaam hai jo genuinely bacha hua hai — nayi simulations, nayi code, nayi data.

---

### A1 — Phase 5: Z1 Target Runs for B3/B6/P1

**Kya hai:** Native mein B3/B6/P1 pass ho gaye. Lekin asli comparison Z1 emulated hardware pe hoti hai with power model — wahi energy data deta hai.

**Kyun important:** Z1 pe policy firmware compile + run hona prove karta hai. Energy per delivered reading milti hai real model ke saath.

**Commands:**
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --target z1 --power-model --seed 123456 --timeout-seconds 300
python3 host/run_experiment.py --phase 5 --mode B6 --clients 2 --target z1 --power-model --seed 123456 --timeout-seconds 300
python3 host/run_experiment.py --phase 5 --mode P1 --clients 2 --target z1 --power-model --seed 123456 --timeout-seconds 300
```

**Time estimate:** ~15 min total (3 runs × ~5 min each)

**Output:** `results/phase_05/` mein 3 new run directories with energy data

---

### A2 — Phase 5: 7-Arm Root+8 Pilot (Main Research Data)

**Kya hai:** 7 modes (B1/B2/B3/B4/B5/B6/P1) × 3 seeds × 8 clients = **21 actual simulations**. Ye woh data hai jisse comparison chart banana hai — policy vs static controls.

**Kyun important:** Ye Phase 5 ka core research evidence hai. Iske bina koi comparison claim nahi kar sakte.

**Commands (each seed separately):**
```bash
# Seed 123456
python3 host/run_experiment.py --phase 5 --mode all5 --clients 8 --target z1 --power-model --seed 123456 --timeout-seconds 600

# Seed 123457
python3 host/run_experiment.py --phase 5 --mode all5 --clients 8 --target z1 --power-model --seed 123457 --timeout-seconds 600

# Seed 123458
python3 host/run_experiment.py --phase 5 --mode all5 --clients 8 --target z1 --power-model --seed 123458 --timeout-seconds 600
```

**Time estimate:** ~45–60 min total (7 arms × ~7 min each × 3 seeds)

**Output:** 21 run directories, comparison JSON per seed, energy per delivered reading per mode

**Note:** `all5` mode runs all 7 modes serially in one command.

---

### A3 — Phase 4 Deferred: Boundary + Lifetime Runs

**Kya hai:** 7 simulations jo Phase 4 matrix se skip ki gayi thi (time constraint).

**Priority:** LOW — Phase 5 research data zyada important hai. Ye baad mein bhi run ho sakti hain.

**Commands:**
```bash
# Boundary 4000ms period
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --period-ms 4000 --timeout-seconds 600

# Boundary 47-byte payload
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --payload-budget 47 --timeout-seconds 300

# Lifetime runs (each takes ~10 min)
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 125 --timeout-seconds 900
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 250 --timeout-seconds 900
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 123456 --timeout-seconds 900
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 123457 --timeout-seconds 900
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 123458 --timeout-seconds 900
```

**Time estimate:** ~2 hours total

---

## SECTION B — Testing / Verification Work (No New Code)

Ye woh kaam hai jo sirf existing firmware/code ko verify karta hai. Koi nayi implementation nahi.

---

### B1 — Phase 5: Security Regression for B3/B6/P1

**Kya hai:** Attack-test aur root-reset-test B3/B6/P1 ke liye. Policy modes mein bhi authentication fail honi chahiye on bad packets.

**Kyun:** Plans ke mutabiq security regression required hai for every new mode.

**Commands:**
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --target z1 --attack-test --timeout-seconds 300
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --target z1 --root-reset-test --timeout-seconds 300
python3 host/run_experiment.py --phase 5 --mode B6 --clients 2 --target z1 --attack-test --timeout-seconds 300
python3 host/run_experiment.py --phase 5 --mode P1 --clients 2 --target z1 --attack-test --timeout-seconds 300
```

**Time estimate:** ~12 min (4 runs)

**Priority:** MEDIUM — should run before claiming Phase 5 complete

---

### B2 — Reports

**Kya hai:** Markdown files likhna — koi simulation nahi, sirf documentation.

| File | Status |
|------|--------|
| `phase_jouney/phase_05_detailed_report.md` | Not written yet |
| `results/phase_05/phase5-evidence.json` | Not created yet |
| `docs/policy-contract.md` | Not written yet |

**Time estimate:** ~20 min

---

### B3 — Human Gates (Cannot Be Automated)

Ye kaam koi agent nahi kar sakta — sirf human kar sakta hai.

| Gate | Description |
|------|-------------|
| G0 | Two-student independent review of official RPL tutorial |
| Phase 4/5 human review | Security decisions, energy model, code review |
| Independent reproduction | Clean machine, fresh clone, run all results |
| Mid-term demo | Live demo + slides + video backup (deadline: 16 Nov EOD) |

**Status:** All pending — never performed.

---

## Priority Order (Time Available: ~2–3 days)

```
TODAY (Most Important):
  A1 → Z1 runs B3/B6/P1         (~15 min)
  A2 → 7-arm root+8 pilot       (~60 min)
  B1 → Security regression       (~12 min)
  B2 → Reports                   (~20 min)

BEFORE MID-TERM (16 Nov EOD):
  Slides + demo preparation      (human work)
  Phase 4 A3 boundary/lifetime   (~2 hours, LOW priority)

PHASE 6 (After mid-term):
  Full matrix 560 runs
  Statistics pipeline
  Reproducibility
  Manuscript
```

---

## Files Changed in Last Session (Phase 5 Implementation)

| File | Change |
|------|--------|
| `firmware/policy/policy.c` | NEW — B3/B6/P1 logic |
| `firmware/policy/policy.h` | NEW — interface |
| `firmware/policy/Makefile` | NEW |
| `firmware/sensor/sensor.c` | EXTENDED — policy tick, POLICY/SWITCH events |
| `firmware/common/events.h` | EXTENDED — event macros |
| `firmware/project-conf.h` | EXTENDED — policy defaults |
| `firmware/Makefile` | EXTENDED — policy.c linked |
| `firmware/energy/energest_sampler.h/.c` | EXTENDED — `lab_energy_remaining_nj()` |
| `configs/phase5.json` | NEW — 7-mode config |
| `host/calibrate.py` | NEW — cost table builder |
| `host/run_experiment.py` | EXTENDED — phase 5, B3/B6/P1, policy defs |
| `host/parse_logs.py` | EXTENDED — POLICY/SWITCH parsing |
| `host/metrics.py` | EXTENDED — policy summary in output |
| `host/energy_reconcile.py` | FIXED — horizon boundary truncation |
| `tests/unit/test_policy.py` | NEW — 17 policy tests |
| `PLANS/PHASE_05_IMPLEMENTATION_PLAN.md` | NEW |
| `phase_jouney/phase_05_environment_and_implementation.md` | NEW |
| `phase_jouney/phase_04_detailed_report.md` | NEW |
| `phase_jouney/phase_04_downloads_problems_and_resolutions.md` | NEW |
| `phase_jouney/phase_04_leftover.md` | NEW |

---

## Numbers At A Glance

| Metric | Value |
|--------|-------|
| Python tests passing | 38/38 |
| Phase 4 matrix cases passing | 28/35 |
| Phase 5 smoke runs passing | 3/3 (native) |
| Phase 5 Z1 runs | 0 (pending) |
| Phase 5 pilot runs (7-arm root+8) | 0/21 (pending) |
| Calibration | Done — Ascon wins |
| Human gates | 0/4 (all pending) |
