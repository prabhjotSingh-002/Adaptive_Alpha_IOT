# Phase 4 synchronized completion plan

> Preserved planning snapshot. The current maintained plan is [PLANS/PHASE_04_IMPLEMENTATION_PLAN.md](../../PLANS/PHASE_04_IMPLEMENTATION_PLAN.md). Keep this historical content; make future planning updates in PLANS.

Date: 14 November 2026. Status: implementation partially complete; this document plans all remaining work. No new experiment was run to prepare this update.

## Authority and use

Read this together with the [preserved original Phase 4 plan](phase_04_implementation_plan.md), [execution journal](../phase_04_environment_and_implementation.md), [master](../../PLANS/MASTER_IMPLEMENTATION_PLAN.md) and [decision review](../../PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md). The original plan's detailed security, energy, validation and reporting requirements remain binding. This document updates its stale implementation inventory and gives the execution sequence; it does not reduce scope or change the master calendar.

The original plan and everything in `phase_jouney/tmp` remain permanent records. Both authoritative plan hashes still match the recorded baseline. This planning task changes documentation only. During implementation, routine progress through these packages does not require fresh design permission at each checkpoint. Environment approvals still apply. Finish Phase 4 reports and stop before Phase 5; do not implement adaptive policy, B3/B6/P1 or a negotiation protocol here.

## 1. Verified current state

Source and existing logs were inspected for this update; a saved PASS is historical evidence, not a newly executed test.

| Area | Present now | Remaining |
|---|---|---|
| Official Ascon | Pinned reference adapter and host corpus harness | Complete provenance manifest, expanded negatives, on-mote validation |
| Host evidence | `results/phase_04/ascon-resume-approved-20261114.log` and `ascon-boot-gate-20261114.log` contain 1,089-vector and packet PASS output | Timestamped manifests with commands, exit status, source/dependency/binary hashes for final candidate |
| Secure envelope | Profile-aware initialization and conditional Ascon dispatch | Bounded permitted context set, profile-return validation, application integration |
| Boot gate | `lab_boot_gate_init_profile`; legacy AES wrapper; single-context grant tests | All-context provisioning validation and atomic activation; both-profile replacement/reset tests |
| Firmware | Existing sensor/root still guard protected paths with profile 1; Makefile does not link Ascon | Shared B1/B2/B4/B5 builds and authenticated telemetry |
| Runner | Only phases 2/3; derives phase from cipher; one shared lock | Explicit phase 4, mode registry, allowed profiles, target/model/purpose/schema configuration |
| Parser/metrics | Authentication and tag accounting assume profile 1; all clients require full generation/DONE | Strict versioned profile-aware events and lifetime-specific completion |
| Energy/lifetime | No production energy module or phase4 config found | Timing feasibility, model, arithmetic, sampling, terminal shutdown, lifetime metrics |
| Comparisons/reports | No Phase 4 network pilots/evidence index/final report found | Full acceptance matrix and reports below |

Reuse Ascon commit `446347f21b209f3921c65ece70027c366cbe1693`, directory `crypto_aead/asconaead128/ref`, implementation `aead.c`. KAT SHA-256: `bbbc34692fe05e5fda0a3b025585622ab3e3747495e5e3655b29aae8c2a4bd33`; license SHA-256: `5537d4d10b76b81b6e8dfd8b644480a4b1efa332fbb0cdb61126c5be781ef7b4`. Recheck these on execution. Retain the pinned Contiki/Cooja/container from `results/setup/source-pins.json` and the original plan.

## 2. Common implementation contract

- Explicit mode table: B1=(AES,1), B2=(Ascon,1), B4=(AES,4), B5=(Ascon,4). N0 remains an explicitly unprotected regression, never a protected fallback.
- Preserve header 11 bytes, reading 10 bytes, capacity 4, 16-byte tag, protected lengths 37/47/57/67. Preserve AES nonce; Ascon uses the original plan's 16-byte context encoding. Preserve GEN-before-network and exact-deadline flush ordering.
- Use a small capability table and bounded contexts indexed by authorized sender/profile/epoch. Reject unsupported profiles before dispatch. Counters and replay windows survive AES → Ascon → AES selection; reading dedup remains shared per sender.
- Provision independent OS-random keys for every allowed sender/profile. Validate declared slots, lengths, version and epoch before activating any context. Zero key bytes alone are not a reliable indication of missing provisioning. No header-driven allocation or activation.
- Keep existing application, codec, aggregator and analysis pipeline. Custom production code stays in `firmware/` and `host/`; no upstream core edits or invented primitives.
- All generated config/build writers, including test scenarios, use `results/phase_02/.runner.lock`. Serial `-j1` builds and one Cooja run at a time. Preserve old evidence and failed attempts.
- New schema must identify phase, purpose, target, profile/allowed set, epoch, config ID, model and timer. RX authentication derives from successful verified receive. Old logs keep their legacy parser path; new completion markers must match phase/schema.
- Every package records changed files, commands, exit codes, failures/fixes, source/config/scenario/binary/log hashes, limitations and next dependency in the journal. Git revision is a real SHA or null.

## 3. Ordered work and acceptance

### P4.0 — Baseline and contracts

1. Confirm no other writer; inspect Git status, dependency pins and existing baseline artifacts. Preserve Phase 3 reference pair and all failures.
2. Write `docs/phase4-security-contract.md` and schema/config definitions covering the common contract above. Define explicit run purposes: functional, security, calibration, static comparison and lifetime.
3. Create an initially pending requirement ledger in `results/phase_04/phase4-evidence.json`; record evidence paths only when artifacts exist.

Exit: reproducible baseline inventory and reviewed implementation contracts. Human review is recorded as pending unless actually performed.

### P4.1 — Finish backend validation and provenance

Extend existing `tests/security/` and `scripts/test_phase4_ascon.sh`; do not rebuild the primitive. Test truncated/oversized inputs, capacity limits, pointer/alias contract, wrong key/nonce/AAD/ciphertext/tag, unchanged caller output, invalid profiles, counter exhaustion/consumption, replay edges 31/32 and valid-tag malformed bodies. Verify rejected packets leave replay and reading state unchanged. Add independent contexts and AES → Ascon → AES return tests, with independent keys.

Run existing AES and Ascon production-C sanitizer suites; retain complete fresh logs and manifests, including backend, license and KAT hashes and compiler flags. Preserve the earlier sandbox failure. Ensure test harnesses cannot race on output binaries.

Exit: official corpus plus adversarial host matrix passes; this does not close mote or network gates.

### P4.2 — End-to-end protected integration

1. `firmware/Makefile`, project configuration: link the pinned Ascon sources/includes and explicit capability flags; fail builds for unsupported selected profiles. Clean builds prevent stale profile settings.
2. `boot_gate.c/.h`: extend to validate the complete declared context set before activation; retain one-use simulator grants outside mote RAM and fail-closed reset. Adapt provisioning to target memory interfaces through verified adapters.
3. `sensor.c`, `root.c`: common protected send/receive paths, bounded per-profile contexts, shared reading dedup, runtime settings/context telemetry. Root startup must not report ready after partial activation.
4. `configs/phase4.json`, `host/run_experiment.py`: explicit phase independent of cipher; B1/B2/B4/B5 registry; new `--mode all` for four arms; preserve legacy `both` semantics for phases 2/3. Validate unsupported combinations before build. Add explicit seed, purpose and target selection needed by the matrix.
5. `parse_logs.py`, `metrics.py`, `plots.py`: schema-aware authentication, overhead and labels; strict READY/config matching; generalize comparison to four runs and finalize hashes after comparison metadata.
6. Extend existing security-test applications/scenario helpers for representative empty/nonempty/AAD KATs on motes. Then execute B2/B5 root+2 smoke, AES B1/B4 and N0 regressions. Compare exact non-depletion GEN tuples; inspect captured radio frames and fragmentation.

Exit: actual mote KATs, authenticated Ascon smoke and retained regressions. Repeat application reset, fresh sensor replacement and root replacement for both profiles; unprovisioned/partial grants must fail. A host-only boot test does not satisfy these rows.

### P4.3 — Early target/timing feasibility gate

Perform immediately after minimal build integration, before substantial energy implementation or expensive pilot matrices. Start with the original plan's supported-emulation candidate, verifying support in the pinned checkout rather than assuming compiler presence proves it.

Build both AEADs plus the real RPL application; execute KATs and root+2 smoke; preserve linker maps, flash/RAM limits, stack-risk assessment, toolchain identity and timing evidence. Inspect official Energest timer width/frequency and state instrumentation. Prove safe flush cadence across underlying timer wrap. Compare idle and controlled CPU/radio work; native laptop execution time is not mote CPU time.

If reference code does not fit, preserve failure and evaluate a pinned official optimized backend with the same vectors. If a target is unsupported, investigate another supported emulated target and record the decision. Do not silently replace full CPU energy with native radio-only results. Missing faithful timing leaves full-model acceptance open; continue independent functional work while investigating.

Exit: documented target/backend/timer decision with actual build, resource, KAT and network evidence, or an explicit unresolved blocker. Compiler availability alone is insufficient.

### P4.4 — Production energy accounting

Create `firmware/energy/` portable model/budget logic plus thin Contiki sampler. Enable official Energest and flush before snapshots; no duplicate OS state tracker. Add a versioned power configuration and `docs/power-model.md` with sourced target component currents, voltage, units, timer frequency, sample interval, unsupported states and model identity. Fetch authoritative numerical sources during implementation; no placeholder currents enter comparative runs.

Use checked integer arithmetic with retained fractional remainders. Prove maximum products/horizon fit; invalid deltas/overflow invalidate the run. Preserve uint64 precision through logs and JSON. Reuse production C for host reconciliation, with independent high-precision fixtures as test oracles.

Emit cumulative CPU/LPM/deep/TX/LISTEN counters, sample times, component energies, remaining budget and validity. CPU and radio overlap: sum compatible component contributions, not whole-board currents twice. Do not separately charge crypto already included in CPU time.

Validate wrap, precision, invalid deltas, overflow, conservation, idle positive consumption, controlled radio-load increase, accounting overhead and sampling sensitivity. Reconcile raw telemetry against reported totals. Budget runs from boot; snapshot analysis start/end; root is mains-powered/excluded from primary network energy but reported separately. Include drain energy consistently. Zero authenticated deliveries means undefined energy per delivered reading.

Exit: shared-C tests and actual idle/load/reconciliation evidence with a sourced model. Native functional success cannot establish full energy validity.

### P4.5 — Terminal depletion and lifetime

Implement ACTIVE → DEPLETED as terminal. Account final deltas first, emit final energy/budget/queue dispositions, stop application work and disable whole-node forwarding/radio. Verify pinned MAC/routing timers cannot reactivate it. If application APIs cannot ensure this, use a verified simulator power-off/removal mechanism and preserve the final snapshot before removal; do not modify upstream core.

Capture actual multi-hop path evidence before depleting a bottleneck forwarder. Verify no post-cutoff TX/ACK/forwarding or resurrection, with an explicit in-flight boundary and a sufficiently long observation interval. Report sampled detection time, overshoot and uncertainty; repeat with tighter sampling.

Extend parser/metrics only for explicit lifetime purpose. Fix prospective demand independently of deaths; count actual GEN while alive and separately report scheduled-demand shortfall. Depletion requires terminal evidence, survivors require final telemetry, and unexplained missing data/timeouts fail. Preserve ordinary non-depletion strictness. Define equal-time depletion/generation order and delivery/drain cohort before runs.

Compute FND and HND over the fixed battery-node set (HND at ceil(N/2)); exclude root. Functional failure uses frozen planned-demand window, threshold and persistence, recording crossing and confirmation times. No observed event yields event=false and censoring time, not a death at the horizon. Test odd/even populations, no deaths, simultaneous deaths, no delivery, missing terminal events and persistence boundaries. Larger budgets must not cause earlier death for an identical state trace; topology-feedback runs require separate interpretation.

Exit: actual forwarding cutoff plus lifetime-accounting validation and replayable raw evidence.

### P4.6 — Integrated static pilots and inherited checks

Before comparative execution write `docs/phase4-experiment-protocol.md` with frozen configuration hashes. Proposed repeatability seeds: 123456, 123457, 123458; separate exploratory calibration seed 223456. These are selected experiment inputs, not completed results. Preserve all calibration runs; freeze one shared model, budgets, sample period and horizon after calibration, never tune by cipher.

| Matrix | Required scope |
|---|---|
| Functional smoke | Representative mote KATs; B2/B5 root+2; AES/N0 regressions |
| Continuity | B1/B2/B4/B5 root+8 at seed 123456 |
| Repeatability | All four arms at all three declared paired seeds; continuity run may count if final frozen settings match |
| Boundaries | All four arms at 500ms, 4000ms and 47-byte budget, initially root+2 at seed 123456 |
| Security | Both profiles: mutation/downgrade/profile substitution, replay/reordering, valid-tag malformed body, application/sensor/root reset, partial provisioning and controlled profile return |
| Inherited network debt | Actual radio-layer loss, receive reordering and sensor-to-root critical flush; distinguish them from pre-UDP omissions and host fixtures |
| Energy/death | Idle/load/conservation/wrap, sampling sensitivity, fixed-trace budget monotonicity, actual multi-hop forwarder death |
| Lifetime | All four arms under identical frozen prospective demand/model/budgets/horizon and declared paired seeds; include censored cases honestly |
| Runner failure paths | Invalid config, stale READY, unknown schema/profile, lock exclusion, timeout and scoped container cleanup; retain failed manifests |

Short delivery defaults remain 60s warm-up, 24 readings/client, 1s period, 3s deadline, 15s drain, 67-byte protected budget. At 1Hz/3s the existing cap-4 flow may flush count 3; preserve it. Long lifetime demand/horizon is a separate calibrated configuration, not a relabelled 24-reading run.

Validate topology, radio/MAC, demand, model and observation windows before pairing. Non-depletion requires exact generation traces; lifetime compares prospective demand and alive intervals. Quantify and resolve target-induced scheduling differences rather than silently relaxing fairness. Capture real frames for both ciphers; equal application length does not prove equal on-air behavior.

Generate packet/delivery/latency and component-energy/lifetime plots only from validated summaries. Report model assumptions, uncertainty/sensitivity, censoring and negative results. Three seeds establish an engineering repeatability pilot, not Phase 6 statistical conclusions.

### P4.7 — Final audit, reports and stop

Run relevant tests after each substantive change, then the complete final-candidate matrix; rerun dependent evidence when source/config changes invalidate it. Verify every indexed artifact hash and regenerate summaries from preserved logs. No invented reviewer sign-off.

Required deliverables:

- Updated chronological `phase_04_environment_and_implementation.md` with commands/errors/fixes and downstream effects.
- `phase_04_detailed_report.md` and `phase_04_downloads_problems_and_resolutions.md`.
- `docs/phase4-usage.md`, security contract, power model and frozen experiment protocol.
- `results/phase_04/phase4-evidence.json`: requirement ID, status, run purpose, artifacts/hashes, exact evidence scope and unresolved reason for each open row.
- Updated phase index and handoff describing the final code, verified commands and limitations.
- Phase 5 interface notes: retained profile contexts, capability table, timestamped valid energy snapshots and measured cost table; unavailable cost cells stay unavailable.

Automated Phase 4 completion requires P4.1–P4.6 acceptance, not merely source presence or host KAT success. Full G4 requires validated counters/model and actual simulated forwarding-node death. Human G0, independent review and clean-machine reproduction stay pending until performed. If a required measurement/implementation gate cannot pass, report its exact evidence and blocker and label Phase 4 partial. Stop before Phase 5.

## 4. Resume procedure

Read the original plan and this update, then the latest journal and actual working tree. Begin at the first unmet acceptance row; reuse passing components instead of restarting them. The next implementation action is P4.0 contract/provenance completion followed by P4.1 adversarial coverage and P4.2 integration, with P4.3 timing feasibility early. Journal progress continuously and proceed across routine package boundaries without asking the user to repeat authorization.
