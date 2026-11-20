# Phase 4 — Detailed Implementation and Verification Report

**Original date:** 14 November 2026
**Updated:** 17 November 2026
**Status:** All 35 validation cases complete. Event-level review and artifact hash verification done. Human review and independent reproduction pending.

## 17 November 2026 — Deferred cases closed and evidence verified

All 7 previously deferred validation cases (cases 29–35) now have stored passed runs and have been reviewed at event level.

### Event-level audit (22 deferred runs)
Audit file: `results/phase_05/audit_17nov/phase4_deferred_event_audit.json`

| Check | Result |
|---|---|
| Manifest status | 22/22 passed |
| Artifact hashes | 209 checked, 0 mismatches |
| Post-death TX from depleted node | 0 violations |
| DEPLETED + REMOVED events in lifetime runs | Present in all 12 lifetime runs |
| Survivor TX after depletion | Present — correct behavior (non-depleted nodes continue) |

### Lifetime terminology (additive correction)
- `crossing_ms` = first time service drops below threshold
- `confirmation_ms` = service stays below for the full persistence window

Earlier prose labelling `crossing_ms` as "functional failure confirmed" was imprecise. The stored summary fields correctly distinguish these; prose in earlier journal entries does not.

Representative (B1 seed=123456): crossing at 164,000 ms, confirmed at 174,000 ms.

### Case 29 — Boundary 4000 ms period
B1/B2/B4/B5, 2 clients, native. All PDR=1.0. B4/B5 p95=3044 ms (deadline flush at slow rate). No fragmentation.

### Case 30 — Boundary 47-byte payload
B1/B2/B4/B5, 2 clients, native. All PDR=1.0. 47−11−16=20 bytes → 2 readings per batch (not 1 as earlier text stated). B4/B5 p95=1038 ms.

### Cases 31–32 — Depletion sensitivity 125/250 ms sample
B2 only, Z1, seed=223456, 9 J budget. PDR≈0.47–0.48. FND confirmed ~158–159 s. Sample interval does not affect delivery.

### Cases 33–35 — Lifetime four-arm (seeds 123456/123457/123458)
B1/B2/B4/B5, Z1, 9 J budget, bottleneck. `PAIRED_IDENTICAL_PROSPECTIVE_DEMAND_VERIFIED_ALIVE_PREFIXES` for all 3 seed groups. FND ~158 s all seeds. Functional service failure crossing ~163–165 s, confirmed ~173–175 s.

### Open gates
- G0 two-student independent review: **PENDING — human action required**
- Phase 4 security/energy model human review: **PENDING**
- Independent reproduction on clean machine: **PENDING**
- Z1 binary stack safety (beyond msp430-size): **not independently verified**

---

## 1. What Phase 4 Implemented

Phase 4 added Ascon-AEAD128 as a second authenticated cipher alongside AES-128-CCM, a production energy accounting model with Energest sampling, terminal depletion and lifetime tracking, and a complete four-arm validated static comparison pilot (B1/B2/B4/B5).

### 1.1 Dual-Profile Crypto

- **AES-128-CCM (profile 1):** existing Phase 3 adapter, now explicitly selects Contiki software `aes_128_driver` via `firmware/crypto/aes-backend.mk`. Pinned MSPSim CC2420 has no SAES handler; without this selection the wrong-key fixture was incorrectly accepted on Z1.
- **Ascon-AEAD128 (profile 2):** official reference implementation from pinned commit `446347f21b209f3921c65ece70027c366cbe1693`, directory `crypto_aead/asconaead128/ref`. Linked via `firmware/crypto/ascon-backend.mk`. Host corpus: 1,089 official vectors pass. Z1 mote KAT (Count 1 empty + Count 35 nonempty) passes.
- Both ciphers use independent 16-byte keys per sender. Root stores bounded sender/profile/epoch slots (max 8 senders × 2 profiles = 16 contexts). Sensor retains both contexts; `--switch-test` exercises AES→Ascon→AES counter retention.
- Nonces are unique per `(node_id, profile, epoch, counter)`. Replay windows survive profile switching. Reading dedup is shared per sender across profiles.

### 1.2 Boot Gate and Provisioning

- `firmware/crypto/boot_gate.c` — fixed-byte mailbox `[0x42, 0x54, 0x47, 0x31]` (4 bytes, explicit layout, not native `int`). Portable across MSP430 2-byte int width.
- `lab_boot_gate_poll_set` validates complete slot set (version/profile/sender/epoch/ready fields) before activating any context. Partial provisioning leaves all contexts locked. Grant is one-use.
- Simulator writes byte array via `VarMemory`; size-checks both key and metadata symbols before write.
- Provisioning fault fixtures (`missing`, `version`, `profile`, `epoch`) all verified — root stays locked, no readings accepted.

### 1.3 Schema 2

- `META2` event reports runtime `config_id`, `profile`, `profile_count`, `switch_test` — verified against resolved config before accepting any delivery.
- `TX2` reads actual sealed header identity (sender, profile, epoch, counter).
- `RX2` uses verified decrypted context identity.
- `PACKET` logs accepted-packet events separately from reading delivery — packet PDR computable independently.
- Completion marker `PHASE4_SCHEMA2_COMPLETE` distinct from legacy `PHASE2_COMPLETE` / `PHASE4_COMPLETE`.

### 1.4 Energy Accounting

- `firmware/energy/energy.c` — portable production C, checked integer arithmetic, per-component fractional carry, overflow/invalid-delta invalidation, terminal budget state.
- `firmware/energy/energest_sampler.c` — official Energest counters (CPU/LPM/deep/TX/LISTEN), 125ms sample interval, `ENERGY_RAW` + `ENERGY_MODEL` paired events.
- Power config `configs/power-z1-v1.json` — TI MSP430F2617 + CC2420 datasheet values, explicit curve-reading uncertainty, no-DMA Z1 build assumption, radio idle-baseline subtracted from TX/LISTEN increments.
- `host/energy_reconcile.py` + `host/energy_reconcile.c` — shared production C binary reconciles all counter totals and component conservation. CPU-current sensitivity bounds computed.
- **Horizon-boundary fix (this session):** `energy_reconcile.py` now tolerates exactly one trailing `ENERGY_RAW` without matching `ENERGY_MODEL` at simulation end (seed 123458 hit this; simulation terminated between RAW and MODEL emit on node 4). Fix: `raw = raw[:len(logged)]` after verifying `len(raw) <= len(logged)+1`.

### 1.5 Terminal Depletion and Lifetime

- `ACTIVE → DEPLETED` is terminal: application stops, `lab_application_deplete()` called, MAC/radio off, `DEPLETED` event emitted.
- Simulator removes whole mote on `DEPLETED` via Cooja script; `REMOVED` event logged with `terminal=1`.
- Lifetime metrics: actual generation while alive, fixed prospective demand, FND/HND, persistent service loss, censored survivors.
- Bottleneck fixture: node 3 routes through node 2 — parent path and downstream traffic verified before node 2 depletion.
- Depletion sensitivity variants: 125ms vs 250ms sample intervals.

### 1.6 Security Test Matrix

Implemented and verified on Z1 with software AES + Ascon reference backends:

| Test | Both profiles | Result |
|------|--------------|--------|
| Attack (8 injection cases) | B1 + B2 | Pass |
| Root reset | B1 + B2 | Pass (tightened: RX2 required before replacement) |
| Sensor reset | B1 + B2 | Pass (tightened: authenticated receipt before replacement) |
| Receive reordering | B1 + B2 | Pass |
| Radio loss/recovery | B1 + B2 | Pass |
| Profile switch (AES→Ascon→AES) | B1 + B2 | Pass |
| Provisioning fault: missing | B1 + B2 | Pass |
| Provisioning fault: version | B1 + B2 | Pass |
| Provisioning fault: profile | B1 + B2 | Pass |
| Provisioning fault: epoch | B1 + B2 | Pass |
| Critical flush | B4 + B5 | Pass |

### 1.7 Static Comparison Pilots

Four-arm (B1/B2/B4/B5), 8 clients, Z1, with power model, three paired seeds:

| Seed | Status | Run IDs (B1/B2/B4/B5) |
|------|--------|----------------------|
| 123456 | Pass | `20261114T065413425942Z` / `065550757430Z` / `070217816028Z`→fail→`070425862495Z` / `065857010232Z` |
| 123457 | Pass | In `validation-20261114T075313282538Z` case 26 |
| 123458 | Pass (after fix) | `20261114T083350114195Z` / `083510489220Z` / `083631080729Z` / `083747256510Z` |

Timing contract: `emulated_125ms_service_bound` — identity (node/reading/value) exact, timestamps within 125ms local / 125,000µs global. All three seeds met this contract.

### 1.8 Measurement Controls

| Test | Seed | Status |
|------|------|--------|
| Idle/listen transition (radio off 30s) | 223456 | Pass |
| Controlled CPU load (10,000 iterations) | 223456 | Pass |

### 1.9 Runner and Tooling

- `host/run_experiment.py` — explicit phase/mode/target/backend/seed/purpose; validates mode→profile→cap mapping; source drift detection across four-arm runs; attempt records; failure manifest finalization.
- `host/validate_phase4.py` — serial 35-case acceptance matrix, individual failure preservation.
- `host/plots.py` — four-arm plotter with explicit security-string validation.
- `host/scenario_target.py` — Z1 XML adaptation, explicit backend selection.
- `scripts/phase4_kat_scenario.py` — one-mote KAT scenario generator for Z1/native.

---

## 2. Known Bugs Found and Fixed

| Bug | Discovery | Fix | Evidence |
|-----|-----------|-----|----------|
| Z1 CC2420 hardware AES accepts wrong key | `validation-20261114T061839506081Z` | `aes-backend.mk` explicitly selects `aes_128_driver` | `z1-software-aes-kat/COOJA.testlog`, `closure-progress-20261114.json` |
| B4 sender deadline 3015ms > 3000ms | `20261114T065725646751Z-B4-8` | 125ms early flush lead for Z1 Phase 4; DROP71 for expired readings | `20261114T070425862495Z-B4-8/manifest.json` pass |
| Sensor reset fixture insufficient | Initial: reset after TX submission | Tightened: waits for root RX2 before replacement; no protected activity after second boot | `20261114T070903748685Z-B1-2/manifest.json` pass |
| MSPSim native-int mailbox width | `int` = 2 bytes on MSP430, cannot hold 0x42544731 | Fixed-byte array `[0x42,0x54,0x47,0x31]` | `resolution-host-20261114.log` |
| NETSTACK_MAX_ROUTE_ENTRIES=8 missing 9th mote | Root+8 node9 no route | `firmware/project-conf.h` sets `=LAB_LAST_NODE` | `z1-route-config-inspection.log` |
| energy_reconcile trailing RAW at horizon | seed 123458 node4: 100 RAW / 99 MODEL | `raw = raw[:len(logged)]` when `len(raw)==len(logged)+1` | `static-123458-rerun.log` all 4 arms pass |

---

## 3. Excluded Evidence

Z1 application runs using default CC2420 hardware AES path (before `aes-backend.mk` fix) are excluded from secure-comparison qualification. 31 manifests listed in `results/phase_04/closure-progress-20261114.json` → `excluded_hardware_aes_application_manifests`. Original artifacts and manifests are preserved intact.

---

## 4. Validation Evidence Index

| Artifact | SHA-256 |
|----------|---------|
| `z1-aes-kat-expanded/COOJA.testlog` | `b7ae405e6bd8992999489dffea44d387c19bc1610aec4d6e637f23c46e1d4e68` |
| `final-source-python-tests.log` | `eeaece0b270d238d98442407a829101236faa209fb8e5c3613b331bfec702465` |
| `static-123458-rerun.log` | `76eafe765b2d505d6ad970f95ebc751f9ecdf67d44b91fdb98161d4e5c3535ce` |
| `validation-20261114T075313282538Z/manifest.json` | `9728b5d22b8249faf7f04b17001f408616b92b1d394cc7923cb0ceed69d83be5` |
| `host/energy_reconcile.py` | `ab16ec112d0405d8c2dbb066a77f3ede6567be6f23fd0f27519be9517f8b2d1d` |
| `firmware/energy/energy.c` | `f627950fcdcbb34f6e05649f322f3f96db7ee0f37120c8185f36e1f9e1e63bc2` |
| `firmware/energy/energest_sampler.c` | `e286ba91a1682e62ec9b43efc83e01cbaede15ca6e3562d26098db77d592b320` |

---

## 5. Open Gates (Human)

- **G0:** Two-student independent review and clean-machine reproduction — pending, never performed.
- **G4 full:** Physical-calibration component validation — out of scope (software-only project); model assumptions documented in `docs/power-model.md`.
- Human review of all Phase 4 security decisions — pending.

---

## 6. What Phase 5 Requires from Phase 4

- Retained profile contexts (AES + Ascon) with independent keys and counters — available.
- Measured cost table from static pilots (B1/B2/B4/B5 energy per delivered reading at 3 seeds) — available from static run summaries.
- Validated energy snapshots with power model — available from static + measurement runs.
- Capability table structure — available in `firmware/crypto/boot_gate.h`.

7 pending cases (boundary 4000ms, boundary 47-byte, 5 lifetime runs) are documented in `phase_04_leftover.md` and do not block Phase 5 implementation.


## 17 November — items 1–3 closure

Deadline harness and dashboard/evidence repairs pass 108 production-C/Python tests in the pinned container. Final-source Z1 calibration completed **six cells for 3 nodes and six for 9 nodes**, independently. Both schema-v1 tables qualify; **144 artifact/binary hashes matched**. Point-estimate B6 selection is Ascon for 3 nodes, AES for 9 nodes; n=1/cell, no superiority claim. Required cap-2 measurements are present, actual batch occupancy retained, and runtime/source/model/dependency compatibility enforced. Actual CLI rejects 3-node-to-9-node transfer before build. Evidence and complete run table: phase_jouney/final2x_phase_01.md and results/phase_05/repairs_17nov/calibration-acceptance.json. Usage: docs/calibration-v1.md.

Earlier source cohorts and failures remain preserved. User deferred items 4–5: no policy/queue firmware repair or adaptive/security/depletion mechanism validation was performed in this package. Browser visual review, full semantic Phase 4 acceptance, human review and independent reproduction remain pending. No corrected-campaign restart or Phase 6 execution. Stopped at this bounded checkpoint.


## 17 November — authorized items 4–5 bounded mechanism checkpoint

Shared-C policy/queue safety, measured own-generation rate, cap-shrink chunking, initial-event capture and uniform Z1 125-ms flush-lead fixes were implemented. **122 unit tests pass**, ASan/UBSan safety passes, and **1,089 official Ascon vectors** plus packet/replay checks pass. Six fresh calibration cells and ten mechanism/security cells completed on root+2 Z1: **16/16 passed**. Raw reanalysis checked **44,020 events / 190 artifact+binary hashes**.

Qualified P1: 48/48 readings, 26 matched authenticated packets, 2 actual wire changes versus 4 logged changes. Frozen 4.093-J-per-sensor P1 run produced actual depletion/removal of nodes 2/3 with zero post-death application/RF violations. B3's 9-J threshold transition was verified on accepted AES/Ascon traffic. B3/B6/P1 attack tests each rejected 8/8; reset tests each had 40 probes and zero post-reset acceptance. Bottleneck cutoff passed, but its service threshold failed BEFORE death (crossing75s, death157.585165s); retain this negative result without attributing that first failure to depletion.

Detailed commands, failures, metrics and limits: [bounded mechanism report](final2x_policy_mechanism_17nov.md); evidence `results/phase_05/mechanism_17nov/`. Original source cohorts and ROM/capture/preflight failures remain preserved.

**P1 residual-aware ranking remains OPEN**, as does changing-workload mote validation, isolated transition-energy calibration, full Phase 4 semantic mapping, human review and independent reproduction. Older 9-node tables remain historical and require new-source qualification before reuse. This bounded checkpoint does not close the full 2X phase. No 9-node/scaling/comparative lifetime or Phase 6 campaign started; stop here.

## 20 November — reproducible evidence review

The [2X Phase 3 checkpoint](final2x_phase_03_evidence_20261120.md) links all 35 archived cases to hash-checked runs and current semantic replay. Four fresh static controls verify ordinary current-source Z1 operation at one seed. Full current-source matrix coverage, independent reproduction and human acceptance remain pending.

The targeted current-source refresh passed the idle/listen, controlled CPU load, 500 ms, 4000 ms and 47-byte cases. [Run and hash ledger](../results/phase_05/z1-closure-20261120/targeted-phase4-verify.json)

The current-source cutoff evidence now includes both sampler settings. Both runs verified the upstream parent path, downstream authentication before removal, zero downstream authentication after removal, and exact production-C final energy reconciliation. [Cutoff audit](final2x_z1_ranking_diagnosis_20261120.md#current-source-phase-4-sampling-and-cutoff)
