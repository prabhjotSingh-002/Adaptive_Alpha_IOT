# Phase 4 remaining work, Phase 5 implementation, Phase 6 final release

Date: 14 November 2026. Status: **implementation plan; no new firmware build, simulation or research result produced by this review.**

Requested location: project root, `phase_4_5_6.md`. This is the consolidated forward plan. Phase 4's detailed completion contract remains [PLANS/PHASE_04_IMPLEMENTATION_PLAN.md](PLANS/PHASE_04_IMPLEMENTATION_PLAN.md), with repairs in [PLANS/PHASE_04_PROBLEM_RESOLUTION_PLAN.md](PLANS/PHASE_04_PROBLEM_RESOLUTION_PLAN.md). This document reconciles their older inventories with inspected code/evidence and expands the previously unplanned Phase 5 and Phase 6 execution steps.

Follow-up master-to-code audit: see **Section 10** for requirement coverage, confirmed source gaps and additional mandatory acceptance checks. Inclusion in this plan is not implementation completion.

## 1. Authority, reading record and scope

The [master](PLANS/MASTER_IMPLEMENTATION_PLAN.md) owns research scope, controls, calendar and gates; the [decision review](PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md) owns the companion W0–W9 sequence. Their historical “not implemented” statements are not current status. Both originals remain unchanged. Read [AGENTS.md](AGENTS.md), [handoff](docs/CODEX_HANDOFF_AND_RESUME.md), [planning index](PLANS/README.md) and [journey index](phase_jouney/README.md) when resuming.

Reviewed all five documents in `PLANS/` and all four documents in the actual root `tmp/`:

- [Phase 2 snapshot](tmp/phase_02_implementation_plan.md).
- [Phase 3 detailed snapshot](tmp/phase_03_implementation_plan.md).
- [Phase 4 original detailed requirements](tmp/phase_04_implementation_plan.md).
- [Phase 4 synchronized snapshot](tmp/phase_04_synced_completion_plan.md).

Also inspected Phase 1–4 reports/journals, technical contracts and usage documentation, project source/config/test/script/scenario inventory, selected current implementation paths, dependency revisions and saved Phase 4 evidence. The whole-directory check inventories dependencies/generated artifacts; it is **not** a line-by-line audit of all upstream sources or a fresh reproduction of every archived run.

User intentionally moved the historical plans to root `tmp/`. Preserve that location and every historical file. Some old Markdown links still assume `phase_jouney/tmp/`; this is navigation debt, not missing implementation. Do not move directories back or remove failures/build evidence as cleanup.

This request authorizes planning all three phases, not claiming their implementation. During subsequent implementation, complete each phase's evidence/reports and honor the phase-boundary instruction before beginning the next. No adaptive code is required to close Phase 4. Phase 6 is the final execution/release phase; no extra Phase 7 is introduced. The original midterm/calendar is not rescheduled by this plan.

## 2. Directory and current-state audit

Inventory before creating this document (counts include generated files):

| Directory | Files | Role / finding |
|---|---:|---|
| `PLANS/` | 5 | Two authoritative originals, current Phase 4 plan, repair plan, index |
| `tmp/` | 4 | Permanent historical planning snapshots |
| `phase_jouney/` | 9 | Execution history; final Phase 4 report absent; Phase 5/6 not started |
| `docs/` | 10 | Contracts, usage, setup, handoff and historical directory audit; energy/research protocol absent |
| `configs/` | 3 | Phase 2/3/4 JSON; no validated power, policy or final-matrix config |
| `firmware/` | 1,824 | Production C plus generated builds; no `energy/` or `policy/` module |
| `host/` | 11 | Runner, target adapter, parser, metrics, plotter and caches |
| `scripts/` | 12 | Setup, smoke, crypto and scenario helpers |
| `tests/` | 9 | Shared C/Python tests; energy/policy/lifetime tests absent |
| `simulations/` | 1 | Existing 9-node scenario; grid/bottleneck/larger scenarios still needed |
| `results/` | 522 | Historical logs, binaries, manifests and failures; preserve |
| `external/` | 7,920 | Pinned upstream dependencies; preserve, do not refactor |

Project Git has no initial commit and project content is untracked. Record null revision plus source hashes until an actual reviewed commit exists. Root quickstart README, CI workflow and pinned analysis environment remain release work. Untracked/generated does not mean disposable.

### Verified existing evidence and its limits

All ten hashes listed in [static provisioning evidence](results/phase_04/provision-set-evidence-20261114.json) matched the current referenced files during this review, including six source files, three run manifests and the host log. This verifies integrity against that index, not execution on a new machine.

| Area | Existing state / evidence | Still not established |
|---|---|---|
| Official crypto | AES adapter and standardized Ascon reference wrapper; saved Ascon host corpus reports 1,089 vectors | Complete final-source adversarial and target matrix |
| Static network | Latest Z1 B2 run `20261113T202636104292Z-B2-2`: 48/48 authenticated deliveries; native AES regression `20261113T202709373776Z-B1-2`: 48/48 | These different targets are not an AES-versus-Ascon timing comparison |
| Four static modes | Earlier native root+2 B1/B2/B4/B5 pilot, matching GEN traces, 48/48/16/16 submissions | Final-source root+8, repeated seeds, target energy/lifetime comparisons |
| Provisioning | Four-byte grant; eight-byte slot metadata; validate static context set before activation; valid zero keys accepted | Application dual-profile context sets, exhaustive metadata/reset integration |
| Target | Reference Z1 mote KAT/network work; Sky reference/optimized ROM overflow preserved | Full root/sensor memory, stack and Energest timing qualification |
| Optimized Ascon | Host corpus passes; Z1 mote KAT fails | Cause unresolved; excluded Z1 combination must remain rejected |
| Security integration | Saved Z1 seven-injection rejection and root-reset lockout tests | All profiles/reset types, on-wire reordering/loss, malformed authenticated body, critical flush |
| Energy/lifetime | Pending entries in [ledger](results/phase_04/phase4-evidence.json) | No production energy/depletion implementation or validated joule/lifetime evidence |

The root-reset probe uses direct-neighbor link-local replay to prove lockout; it is not multi-hop recovery evidence. Pre-UDP deliberate omission is not radio loss. Historical native results are functional/network evidence, not hardware CPU timing.

### Newly confirmed cross-phase blockers

1. `host/run_experiment.py` restricts clients to 1–8, readings to 1–1,000 and slices the existing scenario. Phase 6 cannot reach 10/20 total nodes by changing a JSON number alone; long lifetime demand also needs reviewed bounds/timers.
2. `lab_boot_gate_poll_set` rejects context counts above 16. Eight dual-profile sensors require 16 root contexts; nine require 18; nineteen require 38. Use explicit validated compile-time dimensions, bounded lookup and overflow checks, with actual memory tests. Never simply remove the limit.
3. Application security remains one selected profile per sender. Host AES→Ascon→AES tests do not implement application switching.
4. Manifests remain schema 1; accepted RX events lack explicit authenticated profile/epoch. Completion parsing and historical marker variants need deliberate migration.
5. `host/plots.py` takes exactly two runs and recognizes only B1/B4 or N0 pairs. Four static arms and seven research arms need group-aware comparison and plotting.
6. Older plan inventories and ledger notes predate successful Z1/provisioning changes. Reconcile status from evidence; do not redo solved work or mark broad requirements passed from a narrow subtest.

## 3. Non-negotiable implementation contracts

- Reuse common sensor/root, codec, aggregation, crypto and host metric pipeline. Keep custom production code in `firmware/` and `host/`; no upstream core edits or custom cryptographic primitive.
- N0 remains explicitly unprotected and outside security-equivalent comparisons. Both protected profiles use independent 16-byte keys and 16-byte tags.
- Preserve 11-byte AAD header, 10-byte readings, capacity four, protected lengths 37/47/57/67, AES nonce and standardized Ascon nonce contract. Counter/replay state stays per authorized sender/profile/epoch; reading dedup stays shared per sender.
- Preserve GEN-before-network and oldest-reading deadline. Profile/batch changes never alter prospective demand, restart a nonce counter, extend an existing reading's expiry or release unverified plaintext.
- Use the single `results/phase_02/.runner.lock`, serial `-j1` builds and serial simulations. Do not nest a lock around scripts that already acquire it. Freeze source for an entire comparison group.
- Preserve every failed attempt and every historical result. A run pass, valid comparison, measurement qualification and human sign-off are separate statuses.
- No guessed power constants, free feedback, laptop-time crypto costs, fabricated CI/reproduction or guaranteed percentage improvements. Missing data must remain unavailable.

## 4. Phase 4 — complete remaining static security, measurement and lifetime

Dependencies: W6/W7; existing P4.0–P4.7 and R1–R8. The following checklist closes remaining requirements, rather than restarting completed adapters.

| ID / mapping | Concrete work and files | Acceptance evidence |
|---|---|---|
| F4.1 / P4.0, R1/R3 | Reconcile ledger/status; snapshot source/config/backend/API/KAT/license; initialize attempt manifest before preparation; finalize preparation/build/provision/parse/timeout failures; lock every build entry point | Injected failure paths retain honest manifests; no stale binary attribution; reference/backend selection explicit; excluded optimized target recorded |
| F4.2 / P4.1–2, R2/R5 | Extend `boot_gate.*`, `secure_packet.*`, sensor/root and runner to bounded allowed profile sets, independent keys and retained contexts; shared per-sender dedup; controlled AES→Ascon→AES selector only | Atomic all-slot activation; missing/version/profile/epoch/size/grant negatives; counters/replay retained on profile return; both profiles' application/sensor/root reset tests on supported targets |
| F4.3 / P4.2, R3 | Version events/manifests; runtime config ID, phase/purpose/target/backend/allowed set/epoch/model/timer; explicit profile+epoch in TX/RX; exact structured terminal event; legacy producer-specific interpretation | Stale settings, forged/unknown profile/schema, contradictory completion and unexpected boot rejected; early Phase 4 legacy logs remain replayable without rewriting |
| F4.4 / P4.3, R4 | Full dual-profile root/sensor builds, maps/stack under load, AES and Ascon mote KATs; root+2 then root+8; inspect pinned timer/Energest instrumentation and wrap cadence | Defensible RAM/stack headroom, real crypto timing/counter progression and generation fairness; target accepted before energy claims |
| F4.5 / P4.4, R6 | New `firmware/energy/` portable checked calculator/budget plus thin official Energest sampler; validated power JSON and `docs/power-model.md`; shared-C host reconciliation | Sourced component currents/voltage, correct units, fractional remainder, wrap/overflow/invalid-delta tests; real idle/load, conservation, overhead and sampling sensitivity |
| F4.6 / P4.5, R7 | Terminal ACTIVE→DEPLETED with final counter/budget/queue accounting; verified whole-node shutdown/removal; lifetime parser/metrics and bottleneck scenario | Actual forwarder path before death; no post-cutoff forwarding/ACK/radio resurrection; final evidence retained; correct lifetime and censoring cases |
| F4.7 / P4.6, R5/R8 | Finish security/aggregation matrix; group manifest and four-arm plotting; frozen static and lifetime pilots | Actual matched runs, raw frames, validated summaries, model-sensitive figures and all required row-to-artifact mappings |
| F4.8 / P4.7, R8 | Final-source regression, artifact reconciliation, detailed reports, usage, handoff/index updates | All mandatory automated rows evidenced; unresolved human gates separate; stop before Phase 5 implementation |

### F4.2–4 detailed checks

Test official vectors plus wrong key/nonce/AAD/ciphertext/tag, alias/capacity/truncation bounds, output isolation, forged-high counter, replay offsets 31/32, counter exhaustion/consumption and valid-tag malformed bodies. Require rejection without replay/dedup mutation and valid traffic controls around injected failures. Close actual receive reordering, radio-layer loss and end-to-end critical flush; host fixtures cannot substitute.

Keep Z1/reference as the provisional emulated path, not an already fully accepted energy platform. Earlier reference sensor data+BSS was 6,498 bytes against 8 KiB RAM: 1,694 bytes before stack/runtime demands, measured before expanded contexts and telemetry. Rebuild and measure both root and sensor at final dimensions. Reduce avoidable buffer duplication safely or evaluate another supported target if needed; do not remove security to fit. Sky support and optimized Z1 repair are optional if the accepted reference target meets every required gate.

Determine actual compiled clock/Energest width/frequency; a 64-bit accumulated counter does not prevent missed narrow-timer wraps. Measure controlled CPU/radio work, sampling resolution and instrumentation cost. Preserve strict native trace equality; if emulated scheduling requires a different fairness contract, diagnose and freeze it before comparisons, documenting deviation and measured jitter rather than silently rounding timestamps.

### F4.5–6 energy and lifetime semantics

Choose numerical power assumptions from authoritative target documentation during implementation and archive references/revisions. Account compatible MCU and incremental radio components; never add whole-board baselines twice or charge crypto separately when included in CPU time. Use checked integer arithmetic, retain fractions, preserve uint64 precision through logs/JSON and expose validity. Unsupported states are unavailable, not measured zero.

Budgets start at boot; analysis uses declared warm-up/start/end/drain snapshots. Primary network energy includes battery sensors/forwarders and excludes mains root, whose counters are reported separately. Energy per delivered reading is undefined for zero authenticated deliveries.

Before comparative lifetime runs freeze budget, model, sample interval, horizon, generation/death tie ordering, pending-queue disposition, in-flight frame boundary and post-death drain treatment. Verify actual multi-hop forwarding before killing the bottleneck. If application APIs cannot guarantee radio/forwarding shutdown, validate simulator removal with final telemetry captured first. No upstream patch is assumed.

Use a fixed battery-node population: FND first verified death, HND death number `ceil(N/2)`. Functional lifetime requires a frozen planned-demand delivery/connectivity threshold, rolling window and persistence; record crossing and confirmation. No observed event means right-censored, not death at horizon. Missing terminal telemetry/crash/timeout means failed instrumentation, not censoring. Test odd/even counts, simultaneous deaths, zero demand/delivery, surviving nodes, late packets, malformed terminals and fixed-trace budget monotonicity.

Keep actual GEN/reading PDR separate from prospective demand and scheduled-demand shortfall. Lifetime arms can generate different actual totals after death; validate identical prospective demand and alive intervals. Non-depletion arms retain strict matching requirements.

### Phase 4 execution matrix

Freeze `docs/phase4-experiment-protocol.md` before comparisons. Current short defaults: 60s warm-up, 24 readings/client, 1s period, 3s deadline, 15s drain, 67-byte protected budget. Count three at 1Hz is expected deadline precedence, not a cap-four bug.

| Matrix | Required execution |
|---|---|
| Smoke / regression | Both mote KATs; root+2 B1/B2/B4/B5; N0; existing host suites |
| Security | Both profiles' negative/reset/provision/return tests; actual loss/reordering/malformed-body/critical-flush cases |
| Static continuity / repeatability | Root+8 × B1/B2/B4/B5 × seeds 123456, 123457, 123458 = 12 runs |
| Boundaries | Root+2 × four arms × 500ms, 4000ms, 47-byte cases = 12 runs at seed 123456 |
| Measurement / death | Idle/CPU/radio/load/wrap/conservation/sensitivity; multi-hop cutoff; terminal accounting |
| Lifetime | Separate calibration seed 223456; freeze shared parameters; four arms × three paired seeds = 12 comparative runs |
| Lifecycle faults | Invalid config, lock contention, partial build/provision, stale metadata, parse failure, bounded timeout and owned cleanup |

Reuse a previous run only if final source/config/target/schema and evidence scope match. Three seeds are an engineering repeatability pilot, not final inferential evidence. Meaningful loss is reported; seed-shopping for perfect delivery is prohibited.

Phase 4 outputs: detailed report, downloads/problems report and updated journal under `phase_jouney/`; `docs/phase4-usage.md`, security contract, power model, frozen protocol; complete `results/phase_04/phase4-evidence.json`. Each requirement records status, command/exit, artifact hashes, exact coverage and unresolved reason. G4 remains open until measurement and actual forwarding-node death pass.

## 5. Phase 5 — implement adaptive policies and controls

Entry: Phase 4 mandatory automated measurement/security/depletion gates closed and reported; phase transition authorized. Human review remains honestly recorded. Work maps to W8/G5. Implement no online negotiation handshake unless separately scoped; v1 authenticates each packet's profile and root accepts the preprovisioned set.

### Exact mode contract

| Mode | Cipher action | Aggregation action |
|---|---|---|
| B1 / B2 | Fixed AES / Ascon | One reading |
| B4 / B5 | Fixed AES / Ascon | Identical fixed cap/deadline |
| B3 | Battery-threshold selection between permitted profiles | One reading |
| B6 | Fixed best cipher selected from separate calibration | Adaptive cap/deadline |
| P1 | Measured cost-aware permitted-profile selection | Adaptive cap/deadline |

N0 remains a diagnostic only. B6 and P1 share the same batching feasibility core; B3 never secretly gains batching. Freeze B3's initial profile, threshold(s), direction and tie behavior from calibration, without assuming Ascon is always cheaper. Initial proposed B3 semantics: one residual-budget threshold, one-way transition, no implicit recharge; record whether a configured no-op choice results from equal costs. Any reversible/hysteretic B3 variant is separately named. B6's fixed winner, tie rule and global/per-scenario selection rule must be frozen before evaluation.

### Policy interface and decision rules

Create a small portable `firmware/policy/` core compiled unchanged for host tests and mote firmware. Inputs: timestamped valid energy snapshot; local generation-rate estimate; queue occupancy/oldest age; capability/payload limits; current action/dwell timestamp; versioned measured costs and uncertainty; explicitly available delivery/link features. Output: `(profile, cap, deadline)`, feasibility, reason and predicted saving. No heap allocation or policy-owned crypto context reinitialization.

Candidate caps are 1/2/4; candidate deadlines must respect the validated scheduler granularity and application bound. A cap reduction flushes eligible queued readings through the shared queue path, with explicit accounting. A deadline change cannot extend an already queued reading's previously assigned expiry. Profile changes occur at a defined batch boundary before fresh counter allocation; already sealed packets retain their original context.

Estimate cost per expected unique delivered reading from calibrated CPU/radio/control/loss terms with units, provenance, uncertainty and nonzero-denominator validation. Expected future cost is for selection only, not an extra charge to measured energy totals. Reject unsupported/unprovisioned actions, payload/fragmentation violations and latency/PDR-infeasible actions before ranking. Use conservative calibrated latency/reliability estimates and test actual outcomes; prediction is not a delivery guarantee.

Switch only when expected saving over a declared horizon exceeds measured transition cost plus frozen hysteresis/uncertainty margin and minimum dwell has elapsed. Deterministic ties retain current action. Missing/stale/model-mismatched estimates use the preselected secure static fallback. If no action meets all delivery bounds, retain fail-closed authentication, apply documented queue/drop rules and log infeasibility; never downgrade to N0 or conceal a deadline violation.

Root-only PDR is not a sender feature. Start with local features and validated calibration estimates; any local link proxy must be labelled as such and cannot be called end-to-end delivery. If runtime end-to-end feedback is essential, explicitly add an authenticated reverse-direction protocol with independent nonce/key/replay domain, expiry and measured bytes/CPU/energy, then test loss/replay/reset. Do not smuggle free oracle feedback into the policy. Decision logs and selected-feature contracts must make this choice auditable.

### Ordered work packages

| ID | Implementation / main files | Acceptance |
|---|---|---|
| F5.1 | `docs/policy-contract.md`, `configs/phase5.json`; capability/energy/cost interfaces and calibration schema | Feature availability, units, safe fallback, action space, timing, constraints and baseline semantics explicit |
| F5.2 | Extend runner calibration purpose; measured operation/action/transition costs under `results/phase_05/` | Separate seeds, actual target/flags/backend/model/payload identities, repeat samples/uncertainty; missing cells rejected; calibrated tables hashed |
| F5.3 | Portable fixed and B3 threshold policy; production integration | Threshold below/equal/above, absent/stale budget, exhausted context, no-auth-downgrade; actual switching with retained counters/replay |
| F5.4 | Adaptive batch selector and B6; existing aggregator integration | Queue/byte/deadline bounds, rate changes, cap transitions and critical events; B6 fixed cipher chosen only from calibration |
| F5.5 | P1 feasible-action cost ranker, transition cost, hysteresis, dwell, deterministic fallback | Shared-C tests for unit/range errors, no feasible action, equal costs, uncertainty, rapid oscillation, stale data, timer wrap and zero expected delivery |
| F5.6 | POLICY/SWITCH/FEATURE validity telemetry; parser/metrics/groups and seven-mode runner | Requested versus applied action, reason/estimated costs, successful switches, decision time, control bytes and failures reconciled; spoofed policy events rejected |
| F5.7 | Real root+2 switching/security tests, root+8 seven-arm pilot and bottleneck/traffic change cases | No cross-sender corruption, AES→Ascon→AES continuity, shared dedup, correct pending queue, valid fallback, switching/depletion/reset boundaries |
| F5.8 | Ablation hooks, source/resource regression, report and handoff | G5 comparison to all four static controls; no guaranteed advantage; complete evidence and frozen candidate for Phase 6 |

### Calibration, tests and pilot freeze

Before executing calibration, reserve proposed Phase 5 calibration seeds 223457–223459; proposed evaluation pilot seeds 323456–323458. These are planned inputs, not executed results. Keep Phase 4 exploratory data labelled separately. Hash/freeze calibrated tables and policy parameters before the evaluation pilot. If tuning follows a pilot, that pilot becomes development data and reserve fresh holdout seeds before claiming evaluation.

Measure cipher sizes/counts 1–4, cap/rate/deadline combinations, both transition directions, initialization/selection/decision/logging costs and target resource overhead. Measure the actual mechanism: retained-context profile selection is not a fictitious negotiation handshake. CPU operation tables and integrated Energest totals must not double-count costs.

Host tests use production policy/aggregate/energy/crypto sources. Integration covers noisy thresholds, burst/low/high traffic, no route, loss/reordering, deadline near expiry, max payload, stale estimates, unknown profiles, reset during/after switch, exhausted counter, terminal depletion, interleaved senders and repeated profile returns. Bad authenticated bodies/tags must not alter policy-security acceptance state.

Execute seven protected modes × three paired pilot seeds at root+8 = 21 clean pilot runs after smoke. Repeat selected bottleneck/traffic-change cases with identical prospective demand/model/budgets. Include actual decision/switch overhead and p95/PDR feasibility, not only selected action counts. Strong static baselines may win; a no-switch P1 outcome is valid if justified by measurements.

Master Section 7 also requires a **10-node research pilot**. Root+8 is only the historical 9-node continuity pilot. Before closing F5.7, implement the minimum scenario/provisioning expansion for root+9 (18 dual-profile root contexts), prove memory fit, and run all seven modes × the three frozen pilot seeds at 10 total nodes: another 21 runs. This brings the general scenario/dimension foundation of F6.1 forward into F5.7; F6.1 retains 20-node validation and full grid/bottleneck scaling. If the selected target cannot support root+9, preserve that blocker rather than calling the 9-node pilot equivalent.

Prepare distinct ablation configurations: no cipher choice (B6 where equivalent), no adaptive batching, no hysteresis, ignored transition cost and no deadline protection. The last is an explicitly noncompliant diagnostic ablation, never eligible as an acceptable protected service policy. Authentication/nonce/replay protections remain enabled in every ablation. Phase 5 proves hooks and selected pilot behavior; Phase 6 executes the frozen research ablation matrix.

Phase 5 outputs: journal, detailed and downloads/problems reports; `docs/phase5-usage.md`, policy contract, calibration report; `results/phase_05/phase5-evidence.json`, cost tables and pilot group manifests. Stop after the phase report. G5 requires actual comparisons and no authentication downgrade, not a positive saving percentage.

## 6. Phase 6 — final research experiments, reproducibility and release

Entry: Phase 5 implementation/pilot and required earlier gates audited; transition authorized. Work maps to W9/G6 and master Section 12. Freeze software, policy tables, protocol and analysis before main results. Phase 6 includes implementation of missing experiment/statistics/release tooling, not just running a shell loop.

### Ordered work packages

| ID | Concrete implementation | Acceptance |
|---|---|---|
| F6.1 | Scale scenario generation beyond current eight-client slice; grid/bottleneck layouts, explicit node roles/positions/radio; expand validated provisioning and demand limits | Root+2, root+8 then root+19 checks; all contexts provisioned; memory/stack/routing/traffic fairness at each supported size; no invented nodes from a truncated scenario |
| F6.2 | `docs/experiment-protocol.md`, frozen `configs/phase6.json`, separate seed registry and matrix expansion | Hypotheses, controls, calibration separation, endpoints, feasibility thresholds, exclusions, stop/censor rules and analysis fixed before execution |
| F6.3 | Extend canonical runner with serial matrix scheduling/resume, unique attempt records and group manifests; thin host helper only if needed | Exact identity deduplication, content/hash verification before reuse, deterministic scheduling, timeout cleanup, immutable failed attempts and clear matrix completeness |
| F6.4 | Execute final baseline/policy, lifetime, stress and ablation matrices | Every planned cell has valid evidence or documented unresolved failure; no seed replacement/cherry-picking; raw telemetry and artifacts retained |
| F6.5 | Run-level paired statistics in host analysis; group-aware plots from validated metrics | Known-answer statistical fixtures, deterministic resampling, uncertainty/censoring handled correctly; no reading-level pseudoreplication |
| F6.6 | Reproducibility bootstrap, pinned Python environment, CI fast checks and manual heavy workflow; independent clean rerun | Restore from exact pins, regenerate selected summaries/figures, real second-person execution recorded; unresolved human gate stays pending |
| F6.7 | Final claims/evidence audit, release bundle, quickstart/demo, research methods and manuscript draft | Every figure/claim traced to source/config/run/analysis hashes; required release contents present; limitations/negative outcomes explicit |

### Matrix and freeze rules

Use explicit **total nodes including root**: 10 = root+9 and 20 = root+19. This differs from the historical root+8 (9-node) demo. Define whether dedicated forwarders also generate readings; fix battery-node membership and demand denominators in each scenario.

Master main-matrix candidate: seven protected policies × two topologies (grid/bottleneck) × two sizes (10/20 total) × two rates × ten paired seeds = **560 runs** for one declared experiment purpose. A separate full lifetime matrix would add another 560; do not hide that cost. Calibrate runtime/storage first and freeze whether delivery and lifetime use full or declared subsets before viewing main outcomes. Any scope reduction must be explicit and justified, not silently dropped. Optional 30-node expansion requires new resource acceptance.

Proposed held-out main seeds: 423456–423465, disjoint from Phase 4/5 development/calibration/pilots. Freeze topology/demand/random-stream derivation and order before execution. Same seed alone cannot guarantee identical traffic when radio RNG consumption differs: validate prospective trace independently. Fresh OS-random test keys remain separate from experimental RNG.

Freeze rates, burst traces, link settings, warm-up/drain/horizon, power model, budget distributions, target/backend, logging cadence, sample interval, policy constants, comparator selection and tolerances. Values not yet calibrated remain explicit blocking decisions; do not fill them with guessed currents or outcome-dependent thresholds. Master's illustrative PDR ≥95% and p95 ≤5s are proposals until frozen, not existing guarantees.

Stress subset must cover actual radio loss, bursty traffic, heterogeneous initial budgets, deadline sensitivity, smaller/larger allowed caps, reboot and route churn. Use the same underlying distributions/paired seeds per arm. Power-current uncertainty and sample cadence need sensitivity analyses. Keep attack/reboot diagnostics separate from clean performance comparisons. Run the declared ablations with all security invariants intact and label intentionally removed deadline protection.

### Statistics and metrics contract

`host/metrics.py` remains the sole owner of per-run metrics. A host statistics helper may consume validated summaries; plots do not recalculate metrics. Each row carries run/group/config/analysis identity and measurement tier.

- Primary endpoint: network energy per unique authenticated delivered reading in the declared window. Preselect the strongest feasible static comparator using independent calibration, or freeze a multiple-comparison procedure; do not select the most favorable main-result contrast afterward.
- Report reading PDR, packet PDR, scheduled-demand service, actual GEN/drops/missing readings, p95 delay, radio/application bytes/frames/fragments, component energy and node energy distribution.
- Report FND/HND/functional lifetime separately with event/censor flags. Use survival estimates and/or restricted mean lifetime to a common frozen horizon; never replace censored values with observed deaths. If event information is insufficient, report inconclusive results.
- Report switch count, decision CPU time, actual transition/control overhead, failure/fallback reasons, ROM/RAM/stack and timing limitations.
- Experimental unit is the run/paired seed, not each reading. Freeze paired differences and 95% bootstrap intervals over run pairs (including deterministic resampling seed/count), or an appropriate paired test, before final execution. Preserve scenario strata; do not pool unrelated topologies/rates as interchangeable samples.
- Freeze handling of zero-delivery undefined energy, missing pairs, invalid instrumentation, protocol violations, multiplicity and unsuccessful outcomes. Low delivery/negative savings are scientific outcomes, not reasons to remove an otherwise valid run.

Figures: energy per delivered reading, energy–p95 trade-off, PDR/service, FND/functional survival, switch/decision overhead, CPU/radio contributions, packet-size effects, ablations and sensitivity. Every generated figure receives a source manifest with exact included/excluded runs, summary hashes, analysis version and parameters.

### Reproducibility and release

Create a reviewed source snapshot before frozen experiments, with actual commit ID, dirty-state handling and dependency/license records. Pin the analysis environment only after selecting needed libraries; reuse the existing container and avoid unnecessary installations. Provide a restore procedure for ignored `external/` dependencies and a checksum-verified evidence archive. No blanket deletion/ignore of results.

CI: shared-C sanitizer tests, Python schema/metrics/policy/lifetime tests, config validation and selected build checks. Heavy Cooja matrices run manually/scheduled with the same single-writer rule. CI configuration presence is not a successful CI run.

Independent reproduction requires a real second person, clean environment, commands/date/outcomes, regenerated evidence and explained tolerances; another local agent run is not human sign-off. Formal G0 two-student review must also be recorded if still outstanding. GUI/live demo validation remains distinct from headless correctness.

Release artifacts: root README quickstart; setup/reproducibility guide; protocol/threat/policy/power/experiment contracts; source/dependency/licenses; static/adaptive firmware; scenarios/configs/seed registries; raw logs/binaries/manifests; validated tables/figures and generation commands; demo script/video or verified live procedure; methods/manuscript draft and limitations; complete Phase 6 journal/report/problem record and `results/phase_06/phase6-evidence.json`. Publication/submission/push is a separate action requiring its appropriate authorization; do not imply release planning publishes anything.

## 7. Cross-phase completion and risk ledger

| Gate / risk | Owner phase | Closure condition |
|---|---|---|
| G0 human verification | Inherited; final audit in 6 | Actual two-student execution record |
| G1/G2/G3 regressions and inherited negatives | 4, repeated after relevant changes | Production code plus real network evidence, all required safety/batch cases |
| G4 model/timing/death | 4 | Validated measurement and sourced model, terminal forwarder death, honest lifetime accounting |
| G5 adaptive controls | 5 | B3/B6/P1 implemented/tested and compared to four static controls without downgrade |
| G6 reproducibility/release | 6 | Frozen seeded experiments, validated statistics/figures, independent reproduction and release deliverables |
| Target RAM / >16 contexts / >8 clients | 4 feasibility, 6 scaling | Bounded dimension redesign and measured resource/network checks; no silent target/model mixing |
| Missing sender delivery feedback | 5 | Local-feature contract or separately measured authenticated feedback; no oracle |
| Stale schema/evidence/navigation | 4, final audit 6 | Explicit legacy paths, hash-valid new artifacts and truthful current links |
| No improvement / heavy censoring | 5–6 | Report negative/inconclusive outcome; preserve security and frozen conditions |
| Runtime/storage pressure | 6 pre-freeze | Measured serial throughput and explicit matrix sizing; never discard required checks after outcomes |

For each work item record: requirement ID, changed files, source/config identities, command and exit status, raw artifacts/hashes, expected versus observed behavior, failure/fix, automated status, human status and downstream invalidations. Refresh only evidence affected by subsequent source/config/model changes; do not relabel old runs as final-source results.

## 8. First implementation actions on resume

1. Read this plan alongside the existing Phase 4 completion/repair contracts and latest journal; recheck drift/pins and single-writer ownership.
2. Finish F4.1 evidence/schema foundation and F4.2 dual-profile retained contexts; preserve latest static provisioning/network passes as regression anchors.
3. Prove expanded target memory/timing early (F4.4), then build/test energy, terminal depletion and lifetime (F4.5–6).
4. Execute F4.7 final matrix and F4.8 reports. Close Phase 4 explicitly before implementing Phase 5.
5. After phase authorization, implement F5.1–8, freeze and report the adaptive pilot; then execute F6.1–7 as the final phase.

Do not stop routine authorized implementation after a single small subtask and call the phase complete. Equally, do not mark a failed required gate passed to advance phases.

## 9. Inspection fingerprints and review limits

Verified dependency HEADs: Contiki `a304687372e2917d325d4d71cf68610fe9a6279b`; Cooja `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4`; Ascon `446347f21b209f3921c65ece70027c366cbe1693`. Tracked working-tree diffs were empty for each. Reuse official image pin from `results/setup/source-pins.json`; this review did not launch Docker or revalidate its runtime.

Authoritative hashes verified unchanged:

- Master: `2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385`.
- Decision review: `69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a`.

Review used filesystem inventory, document/source reads, Git status/revision/diff inspection and saved-evidence hash/status checks. It did not install packages, delete/move files, edit firmware, rerun tests/simulations, select numerical power assumptions or create new performance evidence. The phase plans remain pending until their implementation and acceptance actually execute.

## 10. Master requirements → actual code → remaining phase coverage

Follow-up audit: 14 November 2026, requested explicitly against the original master. Status vocabulary: **present** means implementation exists with the stated historical validation; **partial** means some required behavior/evidence remains; **absent** means no first-party implementation was found in the inspected source tree. None of these labels substitutes for a fresh test run.

### 10.1 Coverage matrix

| ID | Master requirement | Inspected implementation / current gap | Coverage and remaining owner |
|---|---|---|---|
| M01 | §§3,8: pinned official RPL network and reproducible smoke | `scripts/smoke.py`, `scripts/smoke.sh`, saved scenario and Phase 1 evidence exist; human G0 pending | Present automated baseline; F4.7 regression as affected, F6.6 actual human/clean reproduction |
| M02 | §4: deterministic source readings, unique delivery, shared bounded codec | `firmware/common/protocol.c`, sensor GEN and root dedup exist; generator is fixed periodic, not a general demand trace | Present basic behavior; F4.4 fairness, F4.6 lifetime demand, F5.7/F6.1 variable/bursty trace integration |
| M03 | §4: caps 1/2/4, byte/deadline/critical flush and drops | `aggregate.c` provides these core operations; sensor passes `false` to every critical argument | Partial integration; F4.7 must add real critical trigger/control and Cooja proof (A04 below) |
| M04 | §§1,4,8: vetted AES/Ascon, equal tags, nonce/replay, no fallback | `aes_ccm.c`, `ascon_aead.c`, `secure_packet.c`, host and mote tests exist | Partial end-to-end matrix; F4.2/F4.4/F4.7 retain vectors and close adversarial/target checks |
| M05 | §4: per-packet authenticated profile agility with independent context state | Root uses `security[sender]`; sensor uses one context selected at build; boot set is static | Partial; F4.2 dual contexts/provisioning/return; F5.3–5 runtime action selection |
| M06 | §§4,6: actual transmitted context/counter and authenticated received identity | Sensor logs separate global `counter`; secure seal allocates `ctx->next_counter`; TX/RX omit profile/epoch | Partial; F4.2/F4.3 must use actual sealed packet identity (A01) before switching |
| M07 | §§6,7: auth failures and replay rejection counts by cause | Root emits only `REJECT,length`; secure open returns bool; metrics aggregates generic rejection | Missing reason attribution; F4.2/F4.3/F4.7 add safe status/reason contract (A02) |
| M08 | §§4,6,8: route loss, preferred parent/rank where exposed, route repair | Sensor checks reachability but emits no ROUTE event; parser has no route vocabulary | Missing structured instrumentation; F4.3/F4.6 and F6 stress, A05 |
| M09 | §§5,7: reading PDR, packet PDR, bytes, latency, fragments | `metrics.py` computes reading PDR/p95/application bytes/fragments; packet PDR and total captured bytes absent | Partial; F4.3/F4.7 must implement packet-level accounting and byte totals, A03 |
| M10 | §§5–7: Energest component energy, residual budgets, duty fractions and node distribution | No `firmware/energy/`; no energy events/model reconciliation | Absent; F4.4–5; include active/TX/listen fractions, per-node mean/min/max/residual distribution, F6.5 figures |
| M11 | §§5,8: terminal simulated death, forwarder failure, FND/HND/functional lifetime | No depletion transition; metrics requires full generation and DONE | Absent; F4.6 and final lifetime runs, F6.4–5 |
| M12 | §§4,7: B3 threshold, B6 adaptive batch, P1 joint cost policy | No `firmware/policy/`; CLI only N0/B1/B2/B4/B5 | Absent; F5.1–8 explicitly includes all three controls and safe fallback |
| M13 | §4: local rolling features, measured loss/delivery estimate, dwell/hysteresis/transition cost | No policy features/calibration/control path | Absent; F5.1–6; local availability/feedback contract already explicit; no free root oracle |
| M14 | §§6,7: policy reason, decision CPU time, switches/control bytes/failures | No POLICY/SWITCH events or metrics | Absent; F5.2/F5.6, measured on accepted timing path, F6.5 analysis |
| M15 | §7: exact seven protected controls with matched inputs | Four static modes in config/runner; only two-arm plotter; N0 diagnostic distinct | Partial; F4.7 groups, F5.6–7 seven arms; protected equivalence excludes N0 |
| M16 | §7: 10-node, three-seed research pilot; 9-node demo distinct | Runner limits clients to eight, scenario holds nine total motes | **Earlier roadmap gap corrected:** F5.7 now requires root+9 pilot and prior bounded expansion; F6.1 expands further |
| M17 | §§7,8: root+19, grid/bottleneck, rates, frozen paired main matrix | No larger scenario generation; no matrix engine/config | Absent; F6.1–4; 560-run design remains proposed until protocol/runtime freeze |
| M18 | §7: loss/bursts/heterogeneous budgets/deadlines/reboot/churn stress | Seven security injections and reset probe exist; no full stress suite | Partial; F4.7 inherited loss/reorder, F5.7 policy stress, F6.4 declared stress matrix |
| M19 | §7: five mechanism ablations | No ablation selectors | Absent; F5.8 implements/test hooks, F6.4 executes; no auth downgrade |
| M20 | §§7,12: run-level paired uncertainty and traceable charts | `plots.py` only legacy two-arm bars; no statistical pipeline | Absent research analysis; F6.5, including censoring/missing pairs/negative outcomes |
| M21 | §§6,8,12: complete manifests, failures, seeds, runtime config identity | Runner has hashes/lock/timeout and schema 1; preparation before try; partial runtime metadata | Partial; F4.1/F4.3 plus explicit negative and identity checks A06; F6.3 immutable resume |
| M22 | §§3,10,12: CI, locked analysis environment and dependency restore | No `.github/workflows/ci.yml`, `host/requirements.lock` or root README | Absent; F6.6–7; earlier fast CI may be added in F4.8 once commands are proven |
| M23 | §§2,3,10: scope/design/tasks, decision log, human review and ownership | AGENTS/plans/contracts exist; scope/decision-log/spec set absent | Partial documentation/process; explicit equivalence/creation and human record in A07 |
| M24 | §§0,9: midterm 9-node demo, slides, backup recording, release tag | Saved secure pilot/plots exist; no completed presentation/tag evidence established | **Earlier roadmap insufficiently explicit:** deadline-bound A08; do not defer the midterm package until Phase 6 |
| M25 | §12: final code/licenses/config/raw results/figures/demo/methods/manuscript and independent reproduction | Partial historical artifacts; no final release/reproduction bundle | F6.6–7 already covers final deliverables; A07/A08 clarifies navigation and distinct release milestones |

### 10.2 Additional concrete acceptance tasks from source review

These are mandatory refinements of the existing F work packages, not a new project phase. They close omissions or overly broad wording in the first roadmap.

**A01 — Canonical protected packet identity (F4.2/F4.3, before F5 switching).** In `sensor.c`, the global application counter builds/logs batches, but `lab_secure_seal` ignores that counter for nonce allocation and uses the selected security context's counter. Existing static success does not prove correctness after alternating profiles or failed reservations. Return the allocated protected identity from the shared sealing API (or decode the successfully sealed header through the shared codec), and log/join `(sender, profile, epoch, counter)`. Do not copy global application counts into nonce state. Test profile sequence AES counter 1 → Ascon counter 1 → AES counter 2, gaps after failed seals, interleaved senders and shared reading dedup. Separate packet count statistics from nonce counters.

**A02 — Rejection reasons (F4.2/F4.3/F4.7).** Introduce bounded internal verdicts for format, disabled/unknown profile, context/epoch, lifecycle lock, replay, authentication and malformed authenticated body. Preserve existing bool compatibility wrappers where useful. Emit safe metadata only after bounds checks, with an explicit untrusted marker for unauthenticated header fields; never publish tentative plaintext. A replay precheck rejection is not necessarily an authenticated attacker packet. Metrics must report these categories without claiming all `REJECT` events are bad-tag failures. Test each verdict with valid controls and unchanged receive state; no timing-resistance claim follows from diagnostic status codes.

**A03 — Packet and radio accounting (F4.3/F4.7).** Add an accepted-packet event once per successfully authenticated/validated packet, independently of per-reading dedup events. Count unique accepted packet identities and submitted data packets for packet PDR, explicitly documenting local UDP submission as the denominator available at this layer; MAC retries/control frames are separate. A valid packet carrying already delivered reading IDs can count as an accepted packet but cannot increase unique-reading delivery. Test mixed batch sizes, duplicates, replays, complete loss and zero submissions. Sum captured frame byte lengths and report the capture boundary, frame classes and inclusion/exclusion of FCS/PHY overhead; do not call them physical-air bytes without validation. Preserve plaintext reading bytes and protected datagram bytes separately. Add impossible receive-before-submit/terminal-window checks using the defined event timing semantics.

**A04 — Critical and changing demand integration (F4.7, F5.7, F6.1).** Wire a deterministic, explicitly configured critical event into the real sensor queue path, log its identity and verify immediate bounded flush plus authenticated root delivery. The current `lab_should_flush(..., false)` calls cannot exercise the critical branch. Later add a shared prospective traffic schedule for bursts/rate changes, independent of policy and network RNG, with event-count/time bounds and explicit skipped-after-death demand. Normal comparisons use the same trace and critical flags for every arm. No alternate sensor app or changed traffic to favor batching.

**A05 — Route telemetry and recovery (F4.3/F4.6, F6.4).** Inspect the pinned routing API for parent/rank/reachability; add bounded change-triggered ROUTE events and cumulative route-change counts where exposed. Mark unavailable fields explicitly. Correlate global timestamps, route loss/repair and captured forwarding path before/after bottleneck removal. Prove route recovery in a topology with an alternate path, and sustained service loss in a deliberate no-alternate-path case. The link-local reset probe cannot satisfy either. Keep logging cadence identical across comparative arms and measure its overhead.

**A06 — Explicit config/runner acceptance (F4.1/F4.3/F4.7; F6.3/F6.6).** Add executable negative checks for missing seed, wrong field types, invalid mode→profile/cap/tag mappings, runtime config-ID mismatch, invalid model/cost IDs and unsupported schema. Preserve a diagnostic attempt record for rejected input without touching generated configuration. Record actual compiler/tool versions, start/end/status/timeout, build inputs, analysis-lock identity and explicit topology/radio/MAC settings, not just their implicit presence in `.csc`. Validate dependency dirty state as well as HEAD; current Contiki/Cooja CLI checks only revisions. Ensure final archive failures are recorded too. Test same-seed repeatability and group compatibility across all relevant settings, plus CLI regressions and plot refusal for malformed/failed/unpaired inputs. Missing seed must fail the CI check rather than acquire an implicit research seed.

**A07 — Research specification and documentation coverage (F4.8, F5.1, F6.2/F6.7).** Add `docs/scope.md` for H1/H2/H3, variables/non-goals and freeze status, and `docs/decision-log.md` for target/backend/model/policy selections, exclusions and justified deviations. Refresh architecture/protocol/threat docs as each phase changes behavior; their current Phase 2/3 text is not the final Ascon/policy contract. Maintain requirements/design/tasks either in the master's suggested `.kiro/specs/secure-rpl/` files or an explicit linked equivalent in PLANS plus technical contracts; document equivalence rather than create a competing authority. JSON configs and `host/run_experiment.py` are already acceptable equivalents to illustrative YAML/script paths; empty placeholder folders or an unnecessary Kiro installation are not required. Human ownership, second-person review, branch protection and release approval remain human/process records, not agent-generated passes.

**A08 — Midterm milestone is separate from final release (deadline-bound alongside Phase 4; F6.7 final release).** Preserve the 16 November feature/evidence freeze and 17 November evaluation from the master. Package the verified 9-node B1/B4 pilot (or honestly labelled N0 fallback if necessary), 6–8 slides, 3–5-minute demo, offline video backup, exact evidence index and an actual reviewed `midterm-2026-11-17` tag. Track these in a milestone checklist and record actual dates; do not invent a tag or move this deliverable to the end of Phase 6. GUI/live behavior needs its own rehearsal. This roadmap's final release bundle is a second milestone, with completed adaptive/research evidence and independent reproduction.

### 10.3 Audit conclusion and boundaries

The main remaining security, energy, depletion, policy and final-research work was already assigned in Sections 4–6. The first roadmap was **not fully explicit** about packet/rejection/route instrumentation, canonical protected TX identity, the master's 10-node pilot, research-spec navigation and the separate midterm package. Sections 5 and 10 now assign those gaps and their acceptance conditions. All 25 requirement groups above have a phase/milestone owner; none is declared implemented merely because it appears in the table.

Online profile negotiation remains optional; physical boards, production key infrastructure, cloud dashboards, new routing and custom cryptographic primitives remain out of scope. Optional 30-node expansion is not a hidden completion gate. Sky/optimized Z1 support may stay excluded if a supported reference target satisfies the required measurement and resource gates.

This is source-based implementation/coverage review, not an exhaustive security audit. Read the actual current codec/aggregator, sensor/root, secure-packet/boot path, runner/parser/metrics/plotter, config/test inventory and master requirements. No firmware was edited and no build, unit test or simulation was run for this follow-up. Source fingerprints at review:

| File | SHA-256 |
|---|---|
| `firmware/sensor/sensor.c` | `311cffb1d6696a081fc251edfd952a3c36e6dbae26cda2dfe48c386b8c9998ac` |
| `firmware/root/root.c` | `817fa58435791fbd2f7c279fe1de31f8c39672fff116cc914c19dac99c712289` |
| `firmware/crypto/secure_packet.c` | `d51a14da080b9b9abbda89622e154aad407ed2dd9a3d380389d3ca29c4bf1b95` |
| `host/run_experiment.py` | `2f8bbd79b5ae11499435f69686b721c4717683c529b9755eea5e659a82757d68` |
| `host/parse_logs.py` | `f0566add89c76a0ace68308664821295febd6a5751b93045ab1ef1786555168f` |
| `host/metrics.py` | `b8331b12c7adde7b823c0cf26a67fa00c60e11a1f84baa659d69be9162702efb` |
| `host/plots.py` | `b06dd3f01d8d8e0fbc60b94dbc0e4a1d0bb8932cb83be6574fee72dffa470a98` |


## 11. Implementation progress — 14 November 2026

First executed increment: A02 production rejection verdicts/root telemetry/parser/summary, with host sanitizer and Z1 Ascon/native AES attack evidence. A03 captured-frame byte totals implemented; packet acceptance/PDR still pending. Fifteen Python regressions pass. See [latest journal](phase_jouney/phase_04_environment_and_implementation.md) and [evidence record](results/phase_04/rejection-status-evidence-20261114.json). This is partial Phase 4 progress; F4.1–8 and Phase 5/6 are not completed by this increment.


### Further implementation increment — dual contexts/schema and energy foundations

Dual-profile application provisioning/retained return, actual TX header identity, schema2 packet joins/acceptance and packet PDR now have native/Z1 root+2 evidence; four static native regressions retain identical demand. Portable checked energy/budget C and optional raw Energest telemetry are implemented/tested. Full-model joules and whole-node depletion are **not** completed. Root+8 Z1 attempts remain failed (node9 no TX at both warm-up settings), with only 696 bytes root static RAM headroom before stack. Detailed commands/failures and exact evidence scope: [journal](phase_jouney/phase_04_environment_and_implementation.md), [evidence](results/phase_04/dual-schema-energy-evidence-20261114.json), [power model status](docs/power-model.md). F4.2/F4.3/F4.5 remain partial acceptance packages, not closed gates.
