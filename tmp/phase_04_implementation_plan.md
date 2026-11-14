# Temporary Phase 4 implementation plan — Ascon, energy and simulated lifetime

Date: 13 November 2026 (IST).
Status: **PLANNING ONLY — implementation has not started.**
Purpose: implementation handoff synchronized with the existing Phase 1–3 application and evidence. This document records proposed work and acceptance criteria, not completed tests.
Stop condition for this planning task: save and review this file, then wait for the user's instruction. Do not install dependencies, change firmware/host code or execute Phase 4 experiments now.
Preservation rule: never delete phase_jouney/tmp or any of its contents. “Temporary” describes the planning stage, not permission to remove this record.

## 1. Authority and reading order

Read [AGENTS.md](../../AGENTS.md), the [master plan](../../PLANS/MASTER_IMPLEMENTATION_PLAN.md), the [decision review](../../PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md), and the [phase index](../README.md).
Then read the [Phase 1 journal](../phase_01_environment.md), [Phase 2 report](../phase_02_detailed_report.md), [Phase 3 temporary plan](phase_03_implementation_plan.md), [Phase 3 report](../phase_03_detailed_report.md), [latest Phase 3 journal](../phase_03_environment_and_implementation.md), [security contract](../../docs/phase3-security-contract.md), and actual code/evidence below.

The master owns scope, deadlines and gates. This plan expands its Sections 4–8 and the companion's W6/W7. It does not edit or replace either authoritative document. Their historical statements about implementation status are interpreted alongside the newer phase journals.

| Authoritative file | SHA-256 verified during planning |
|---|---|
| PLANS/MASTER_IMPLEMENTATION_PLAN.md | 2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385 |
| PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md | 69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a |

Phase 4 covers the second vetted AEAD, static B2/B5 controls alongside B1/B4, energy instrumentation, a documented power model, residual budgets, simulated depletion and lifetime accounting. Target G4 while retaining existing protocol/security/batching correctness. Phase 5 owns adaptive policy, B3/B6/P1 behavior and decision evaluation; Phase 6 owns the full research matrix, statistical conclusions and release reproduction. No production provisioning, physical boards, new routing protocol or cloud service is needed.

The master keeps its 16 November freeze and 17 November evaluation, with second-cipher/energy work principally post-midterm. Authorization to plan Phase 4 does not change those dates or justify destabilizing the demonstrated pilot. Preserve a reproducible Phase 3 baseline before subsequent implementation.

## 2. Verified baseline and constraints

These observations come from existing source and saved reports; no tests were rerun for this planning task.

| Existing work | Reuse and preservation requirement |
|---|---|
| Phase 1 official RPL network and pinned toolchain | Keep Contiki RPL/UDP/6LoWPAN/MAC/Cooja; no upstream core modifications |
| Phase 2 production codec and aggregation | Keep 11-byte header, 10-byte readings, capacity 4, exact bounds, oldest-reading deadline and explicit build/commit lifecycle |
| Deterministic generation | Preserve reading identity/value/schedule independent of cipher and network RNG; GEN occurs before network/crypto work |
| Native clock handling | Global simulator GEN/RX timestamps define delivery latency; source-local timestamps remain consistency/queue fields |
| Phase 3 AES envelope | Retain authenticated header, private decrypt scratch, fail-closed reset, counter allocation and transactional replay updates |
| Existing pipeline | Extend runner/parser/metrics/plots; do not create parallel baseline applications or a second competing metric pipeline |
| Evidence ownership | Keep all old successes/failures; write new runs under results/phase_04 |
| Workspace | No initial project commit at inspection; untracked files exist. Source hashes are authoritative; git_sha is null if no commit exists |
| Machine | Approximately 4GB RAM: serialize builds/simulations; retain required project scope |

Pins from [source-pins.json](../../results/setup/source-pins.json):

- Contiki-NG: a304687372e2917d325d4d71cf68610fe9a6279b.
- Cooja: fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4.
- Official image: contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609.
- Existing container launcher: /home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja.
- Reuse existing Java/GCC/Make/Python and container matplotlib; inspect before installing anything.

Evidence anchors:

- [Phase 2 evidence index](../../results/phase_02/phase2-evidence.json).
- [Phase 1 regression smoke](../../results/phase_01/smoke-20261113T102520721060Z/manifest.json).
- [Current Phase 3 B1](../../results/phase_03/20261113T103709606387Z-B1-8/manifest.json) and [B4](../../results/phase_03/20261113T103749292302Z-B4-8/manifest.json).
- [Phase 3 evidence index](../../results/phase_03/phase3-evidence.json).
- [Latest malformed-body host test](../../results/phase_03/unit/crypto-malformed-body.log).

The current 1+8 AES pair has exactly matching 192 generated readings and 192 unique authenticated deliveries per arm; submissions are 192 versus 64. At 1Hz with a 3-second deadline, cap 4 produces count-3 batches because deadline expiry flushes the old batch before offering the new reading. A separate 500ms run exercises count 4. Preserve this behavior; changing it silently would change the experiment.

These are single-seed engineering observations, not energy measurements or general superiority evidence. Native shared-library sizes are not embedded RAM/flash measurements.

## 3. Inherited validation debt

The user's prior instruction permits progression with visible pending checks. Planning does not close them. Separate regression dependencies from formal human sign-off.

| Item | Existing evidence | Required treatment |
|---|---|---|
| Two-student G0 review | Automated official-network smoke exists | Keep human gate pending until actual reviewers record execution |
| Authenticated malformed inner body | Latest production-code host sanitizer test passed | Still run end-to-end Cooja rejection with unchanged replay state; older report wording predates this host check |
| Packet reordering | Host replay-window edges covered | Add controlled on-wire receive-order scenario; distinguish actual reordering from a fabricated parser fixture |
| Radio-layer loss | Existing attack run omits one packet before UDP submission | Add deliberate radio-layer loss with capture/config evidence; do not relabel pre-submission omission |
| Critical-event flush | Shared aggregation unit test exists | Exercise sensor-to-root integration with queued readings and a logged critical trigger |
| Independent review/reproduction | Local engineering results exist | Keep pending; no invented reviewer, clean-machine run or release certification |

Close the relevant automated items during Phase 4 integration/security validation before claiming that broader coverage. If a scenario remains unresolved, report it explicitly and keep its acceptance row open. Do not mark full automated handoff complete while required rows lack evidence.

## 4. Decisions and unresolved gates

| Decision | Phase 4 choice | Why / validation |
|---|---|---|
| Second cipher | Standardized Ascon-AEAD128, pinned official ascon-c source | Reuse a vetted primitive; exact variant and official vectors required |
| Implementation variant | Start with portable reference implementation; optimize only after resource evidence | Avoid premature architecture-specific assumptions |
| Registry | 0=N0, 1=AES-128-CCM, 2=Ascon-AEAD128 | Reject all unknown/disabled values; “nonzero” is not a sufficient protected-mode check |
| Tag/key | Both protected profiles use 16-byte tags and independent 16-byte keys | Keep comparable authenticated overhead and key separation |
| Nonce | Preserve AES 13-byte contract; use a separate specified 16-byte Ascon encoding | No truncation/padding of an AES backend call |
| Wire | Existing v1 header is AAD; body codec reused | No duplicate serialization or plaintext fallback |
| Static modes | B1 AES single; B2 Ascon single; B4 AES fixed batch; B5 Ascon fixed batch | Same queue, traffic, deadline and payload constraints |
| Energy | Official Energest counters plus explicit, sourced model | No guessed joules or host-wall-clock crypto energy |
| Depletion | Terminal simulated node failure with application and forwarding/radio shutdown | A stopped generator alone is not a dead routing node |
| Future adaptation | Stable profile/energy/cost interfaces only | No adaptive policy or negotiated handshake in Phase 4 |

The standardized algorithm is specified in [NIST SP 800-232](https://csrc.nist.gov/pubs/sp/800/232/final). The [official implementation repository](https://github.com/ascon/ascon-c) contains the standardized asconaead128 implementation. Its inspected [reference API](https://raw.githubusercontent.com/ascon/ascon-c/main/crypto_aead/asconaead128/ref/api.h) declares 16-byte key, public nonce and authentication overhead, and a no-overlap contract. These mutable URLs identify candidates, not reproducible dependency pins.

**Unresolved before implementation:** select and record an exact ascon-c commit, implementation directory, license files, source hashes and matching upstream KAT hash. Verify compatibility in the existing container and on the selected mote. Do not substitute pre-standard Ascon-128/128a vectors or infer compatibility from a family name. Keep protocol big-endian serialization independent of the primitive's internal byte convention.

**Unresolved before energy claims:** select a supported emulated target/timing source and documented current model; verify stack, AEAD and instrumentation compatibility. Numerical currents, battery budget, lifetime horizon and functional-failure thresholds are intentionally not invented here. Their selection is a mandatory recorded calibration step, not discretion to skip validation.

## 5. Concrete migration map

| Existing area | Change required | Main trap / acceptance |
|---|---|---|
| firmware/crypto/secure_packet.h/.c | Explicit profile descriptor/context, bounded dispatch, per-profile nonce and key | Currently includes AES types, hardcodes profile 1 and 13-byte nonce; preserve AES wire bytes |
| firmware/crypto/aes_ccm.c | Retain tested backend; adapt only through small common interface | Shared AES key schedule must remain serialized/non-yielding |
| New firmware/crypto/ascon_aead.c/.h | Bounded wrapper around pinned upstream implementation | Enforce lengths, no-overlap, private output and authentication result |
| firmware/crypto/boot_gate.c/.h | Extend provisioning to declared allowed contexts | A mailbox grant must not accidentally unlock unprovisioned profiles |
| firmware/sensor/sensor.c | Select explicit static profile through common envelope | Existing profile==1 branches must not route Ascon into N0 |
| firmware/root/root.c | Bounded lookup by sender/profile/epoch; shared reading dedup | Separate packet replay per context; no fresh context allocation from attacker input |
| firmware/common and aggregate | Reuse codec, ring and deadline logic | Protected overhead exactly once; no forked Ascon aggregator |
| firmware/project-conf.h and Makefiles | Energest flag, selected backend sources, include paths | Preserve clean native builds and no upstream edits |
| host/run_experiment.py | Explicit phase/mode/profile, provisioning, model config and new events | Currently derives phase=3 only for profile 1, otherwise 2; profile 2 would be misrouted |
| host/parse_logs.py | Versioned strict event normalization | RX_AUTH gating and completion marker currently assume old modes |
| host/metrics.py | Registry-aware authentication plus energy/depletion accounting | Current all-readings/all-DONE expectation is invalid after death |
| host/plots.py | Validated four-arm comparison and honest censored lifetime display | Current comparison is a two-run N0 or AES pair |
| configs | New phase4 and power/lifetime configuration with validation | Keep phase2/phase3 defaults and historical artifacts intact |
| tests/scripts/docs | Extend existing harnesses and document contracts | New test fixtures remain separate from experimental results |

Prefer a small static descriptor table and plain functions. Do not build a plugin framework, dynamic allocation system, alternate network stack or generic configuration language. Generate C configuration from resolved host configuration and validate runtime READY metadata against it.

## 6. Security and packet contract

### 6.1 Common adapter and envelope

Use a bounded AEAD interface with explicit profile, key/nonce lengths, AAD length, plaintext/ciphertext length, output capacity, output length and success/failure. Profiles declare their limits. Convert upstream length types only after range checks. The wrapper owns any required non-overlapping scratch buffers.

Decrypt into private scratch; publish plaintext only after authentication and complete body validation. Wipe sensitive temporary buffers on every exit. A library that writes tentative plaintext before returning failure must not expose it to root consumers. No software timing-resistance claim follows merely from tests or wiping.

Retain the 11-byte v1 header as exact AAD and the shared 10-byte reading representation. Protected packet sizes stay 37/47/57/67 bytes for counts 1/2/3/4. Nonces are derived from authenticated context/header fields, not transmitted as an added field. Validate all lengths before indexing or copying. Keep N0's existing profile=0/epoch=0 restrictions and unauthenticated labeling.

### 6.2 Nonce, key and replay separation

Preserve current AES nonce exactly:
RSL[3] | profile=1[1] | direction=0[1] | sender_BE[2] | epoch_BE[2] | counter_BE[4].

Proposed Ascon nonce, to freeze in the implementation contract before coding:
RSL[3] | profile=2[1] | direction=0[1] | sender_BE[2] | epoch_BE[2] | counter_BE[4] | reserved_zero[3].
Total 16 bytes. Reserved bytes must remain zero under this contract. Future encoding changes require an explicitly separated context/key domain and version review.

Generate independent OS-random test keys per sender, profile and run; never derive keys from traffic seeds. Keep sender identity, profile, epoch, direction and counter validation explicit. Current counter range remains 1 through UINT32_MAX-1; consume the counter before invoking encryption, and fail closed on exhaustion. Failed encryption must not recycle a consumed nonce. No wraparound or silent epoch rollover.

Root packet replay windows are per authenticated sender/profile/epoch context. The candidate window is committed only after tag and decoded-body validity. Reading deduplication is shared across profiles for the same source reading stream, so retransmitting a reading under another valid profile does not double-count delivery. Preserve bounded windows and document their retention limits.

A controlled AES → Ascon → AES test must retain each context's counter/replay state on return. This is an interface regression for future policy work, not an adaptive policy experiment. Preconfigure allowed contexts; unauthenticated header fields may select only an already authorized context and must never create or activate one.

### 6.3 Provisioning and reset

Extend the simulator's key slots and provisioning metadata to include profile and epoch; verify byte counts/layout against the compiled binary. Populate only each sensor's own declared keys; root receives the authorized sender/profile set. Reject missing, stale or incomplete provisioning before activation.

All contexts start locked. Retain the one-use grant outside mote RAM. Validate the full authorized context set before activation, avoiding partial activation followed by a misleading READY event. Review the existing root activation shortcut rather than mechanically duplicating it for profile 2.

Repeat application reinitialization, fresh sensor replacement and root replacement tests with both profiles. A reset must not restore the same key with counters/replay windows restarted. No automatic N0 fallback is permitted. Whole-simulation rollback restoring both grant ledger and mote state remains outside the supported model unless a separate mechanism is actually implemented and tested.

Generated scenarios contain public simulation test keys. Label them accordingly and never use real credentials. Existing cross-run key uniqueness relies on OS randomness, not a historical collision registry. Known-answer and malformed-message fixtures use isolated keys and must not become operational nonce-allocation examples.

## 7. Runner, schemas and reproducibility

1. Make phase, mode, cipher and experiment purpose explicit resolved fields. Phase 4 B1/B4 are fresh Phase 4 runs, not Phase 3 directories inferred from cipher ID.
2. Preserve Phase 2/3 CLI behavior. Add B2/B5 and an explicit four-arm selection; do not silently change the meaning of old --mode both calls.
3. Keep the shared results/phase_02/.runner.lock for all builds/runs until a coordinated migration covers every writer. A separate Phase 4 lock would fail to protect the shared generated header and build directories.
4. Extend the existing single writer to generate config, compile cleanly, provision, execute and finalize artifacts. No concurrent Cooja jobs on this machine; use -j1 builds.
5. Introduce versioned new telemetry/manifests and a normalization path for legacy evidence. Existing logs use PHASE2_COMPLETE even for Phase 3; accept it only under the legacy schema. New completion markers must agree with declared phase/schema. Never rewrite old logs.
6. READY/CONTEXT events identify profile, allowed set, epoch, effective cap, tag budget and model/timer identity. RX_AUTH must identify the authenticated profile; header claims alone do not establish authentication.
7. Preserve uniquely named containers, bounded timeouts and scoped cleanup. Never stop unrelated Docker containers. Preserve timeout, compile, provisioning, parse and comparison failures with commands and exit status.
8. Resolve and validate every override before building. Preserve invalid-config errors as diagnostic evidence when testing error paths.
9. Hash source, dependency/KAT/license files, generated and resolved configs, power model, scenario, binaries, raw logs, parser/metrics code and final artifacts. Finalize comparison hashes after comparison metadata is complete.
10. Record actual git revision when available, otherwise null plus complete source hashes. Never record the literal string HEAD as a revision. A later reviewed commit is useful but not fabricated by the runner.

Do not loosen strict parsing globally to accommodate death or attack tests. Use an explicit run-purpose/schema contract with allowed events and assertions; unexpected ERROR, unknown profile, missing final telemetry or unexplained REJECT remains a failure.

## 8. Energy instrumentation and model

### 8.1 Validate the measurement source first

Enable the pinned official Energest implementation in project configuration. Use its existing CPU/LPM/deep-LPM/TX/LISTEN instrumentation; project code samples and models those counters. Do not modify Contiki core or add a second state tracker.

Inspection found 64-bit accumulated Energest totals but an underlying configurable timer type used to calculate deltas. A wide total does not prevent lost time if the underlying clock wraps more than once between updates. Record timer frequency/width and prove sampling/flush intervals stay within its safe interval for each target.

Call energest_flush before consistent snapshots, using the platform's supported synchronization where necessary. Verify CPU+LPM+deep-LPM covers elapsed time within declared precision. Radio TX/LISTEN are a separate, potentially overlapping component timeline; never expect their sum with CPU states to equal wall time.

Native Cooja can validate networking, event accounting and radio state instrumentation. Native host C execution may consume no representative simulated MCU time. Check this explicitly; do not convert laptop wall time, native process CPU time or an arbitrary delay into measured mote crypto cost.

Run an early supported-emulated-target spike using the pinned environment: compile both AEADs, execute vectors/network smoke, determine timer/cycle fidelity, and measure resource feasibility. Keep target/toolchain/model IDs explicit. If the target cannot support the stack or faithful timing, preserve failure and investigate another supported target. Do not mix native radio measurements and unrelated CPU measurements without a separately documented, validated hybrid model.

Native functional/radio-only results may still be useful, but must be labeled as such. Full cipher CPU-energy comparisons and the associated research claims stay pending until a suitable measurement/model path passes. Successful radio accounting alone does not prove full-model accuracy.

### 8.2 Model configuration and arithmetic

Store voltage, per-state currents, source references/revisions, target, radio/MAC settings, timer units, sampling period, initial budgets and model version in a validated configuration. Cite actual target documentation for numerical assumptions. No arbitrary power numbers selected just to make Ascon win.

Use the master's component formula:
E = V × (I_cpu T_cpu + I_lpm T_lpm + I_deep T_deep + I_tx T_tx + I_listen T_listen).

This requires compatible component currents. CPU and radio can be active simultaneously; adding separate component currents is valid, but adding whole-board radio current to a whole-board CPU current double-counts shared power. If documentation provides combined currents, derive a documented non-overlapping model or reject that parameterization.

Implement bounded portable energy/budget arithmetic under firmware/energy and test that exact production C on the host. Prefer explicit integer units with checked intermediate products and retained fractional remainder. Select units only after proving range and precision for the maximum horizon. Prevent overflow, negative deltas and sample-by-sample rounding drift; invalid arithmetic must produce a failed run, not plausible energy.

Log cumulative raw counters, delta/sample timestamps, accumulated energy and remaining budget. Preserve integer precision through JSON/JavaScript boundaries, for example decimal strings for uint64 values exceeding exact numeric range. Declare unsupported states explicitly rather than silently treating missing instrumentation as measured zero.

Use the same model contract for firmware and host reconciliation. A small independent high-precision fixture oracle is useful for arithmetic validation, but avoid a second production energy implementation with drifting formulas. Expose the production C calculator to the host pipeline if needed; retain raw counters for independent review.

Measure accounting overhead and hold telemetry settings constant across arms. Do not add a separate per-encryption energy charge if CPU state deltas already include that operation.

### 8.3 Windows and reporting

Battery budgets decrease from boot, including warm-up. Snapshot cumulative energy at measurement start/end so the chosen analysis window is explicit. A calibration run dying during warm-up is unsuitable for the intended primary pilot and must be preserved as such; do not discard post hoc failures from a frozen experimental protocol.

Primary network energy includes battery sensors/forwarders and excludes a declared mains-powered root. Still collect root counters separately. Use one declared observation window for numerator and unique authenticated reading denominator, including any drain energy used to deliver those readings. Report the window and component breakdown.

No authenticated deliveries means energy-per-delivered-reading is undefined, not zero. Unsupported CPU measurement means the full total is unavailable; present validated components with explicit scope. Sensitivity to documented current assumptions is model analysis, not a physical battery measurement.

## 9. Depletion and lifetime — difficult integration work

### 9.1 Terminal failure semantics

Add an explicit ACTIVE → DEPLETED transition, terminal within the run. Before each sampling decision, account elapsed state deltas; on exhaustion record the final snapshot, model version, budget, timestamp and queued-reading disposition.

Stop generation, encryption and application timers; clear/account queued readings with explicit depletion drop reasons. Also disable MAC/radio and forwarding. Merely stopping UDP sends leaves the node available as an RPL router and does not satisfy G4.

Prove how shutdown works on the pinned target. Periodic MAC/routing timers must not reactivate the radio. If application-level APIs cannot guarantee terminal shutdown without core edits, use a documented simulator-level power-off/removal mechanism that preserves final evidence and disables the whole mote. Record simulator time/order and in-flight frame boundaries. Do not invent an unverified shutdown API.

Require no post-cutoff transmissions, receptions used for forwarding, ACKs or forwarded application traffic from the depleted node, subject to an explicitly defined already-in-flight boundary. Capture evidence beyond the last application TX. No reset, fresh key or renewed grant may resurrect a depleted node within a lifetime run.

Use a verified multi-hop bottleneck scenario: establish traffic/parent-path evidence that a selected forwarder is actually on a route, then observe its depletion and downstream route recovery or sustained failure. The existing 1+8 topology alone does not prove a forwarding-node test. Derive the smallest suitable scenario while reusing official routing and recording topology/radio changes.

Sampled depletion has finite detection delay. Report death time at the first exhausted-budget decision and its sampling uncertainty; do not claim sub-sample precision. Document budget clamp, final overshoot and treatment of events occurring at the same simulator timestamp. Validate tighter sampling sensitivity.

### 9.2 Generation, delivery and completion after death

Current metrics expect every sensor's 24 readings and DONE event. Replace this assumption only for explicit lifetime runs:

- Keep a prospective demand schedule fixed by seed/config, independent of algorithm and deaths.
- GEN records actual readings created while the sensor is alive. Suppressed scheduled readings after death are separate demand shortfall, never fabricated GEN events.
- Preserve each generated reading's final disposition: queued/drop/submitted/delivered or outstanding at the declared end.
- A depleted node supplies a verified terminal event/snapshot instead of ordinary DONE; survivors still supply completion/final snapshots.
- Missing logs, a crash or a timeout are not evidence of battery death. Treat unexplained absence as failure.
- Freeze treatment of generation/depletion at equal timestamps and of pre-death readings delivered during drain.

Reading PDR remains unique delivered readings divided by actual generated readings in the declared cohort; protected delivery additionally requires authenticated RX. Report scheduled-demand delivery and alive-node counts alongside it, so fewer living generators cannot create a misleading “improved PDR.” Packet PDR remains a separate metric.

For non-depletion static comparisons, retain exact matching generation traces. In lifetime runs realized traces legitimately diverge after deaths: require matching prospective schedules and verify actual generation against each node's alive interval. Compare common alive prefixes without demanding impossible post-death equality or weakening the original non-depletion checks.

### 9.3 Lifetime definitions

Record the battery-node set and denominator before running. Exclude the mains root from FND/HND unless the protocol explicitly gives it a battery.

- FND: first verified depletion among that fixed battery-node set.
- HND: time when at least ceil(N/2) of those nodes have depleted.
- Functional network lifetime: first violation lasting the preregistered interval of a specified delivery/connectivity requirement.

Freeze the delivery threshold, window size, persistence interval, warm-up eligibility and treatment of zero demand before pilots intended for comparison. Log both threshold crossing and confirmation times. Use planned demand or another explicit service requirement so a network with no surviving sources cannot appear healthy through an empty denominator.

If a lifetime event is not observed by the horizon, store event=false and censoring time; do not substitute horizon as an observed death or extrapolate a lifetime. Keep FND, HND and functional loss separate. Calibrate budgets/horizon with separate exploratory seeds, then freeze equal conditions across modes; never tune budgets separately to favor one cipher.

## 10. Ordered implementation packages

These are work packages within Phase 4, not new project phases. Complete and log each before moving to dependent work.

| Package | Work | Exit evidence |
|---|---|---|
| P4.0 Baseline and contract | Recheck pins/hashes, preserve Phase 3 reference, inventory dependencies, record inherited debt; freeze profile/schema design | Reviewed contract and baseline inventory; no old evidence overwritten |
| P4.1 Official backend | Pin source/license/KAT, build bounded Ascon adapter, run upstream vectors and adversarial buffer tests | Actual production C sanitizer logs; provenance manifest |
| P4.2 Shared protected integration | Generalize envelope, contexts, provisioning, sensor/root, runner and parser; retain AES/N0 behavior | Cooja KAT, B2/B5 1+2 smoke, AES/N0 regression, reset/cross-profile rejection evidence |
| P4.3 Timing feasibility | Select/validate emulated target and current-source assumptions; native limitations explicitly measured | Target build/KAT/network/resource logs and measurement decision |
| P4.4 Energy accounting | Sample official counters, implement shared model and telemetry, reconcile host results | Idle/load, conservation, precision/wrap/overflow and sampling-sensitivity results |
| P4.5 Depletion/lifetime | Terminal shutdown, multi-hop forwarder case, lifetime-aware completion and censored metrics | Radio/forwarding cutoff evidence and validated death/service-event accounting |
| P4.6 Integrated static pilots | Run four fixed controls with matched inputs; close inherited automated security/critical-flush coverage | Actual indexed runs, paired checks, packet/latency/validated energy plots and explicit limitations |
| P4.7 Review and stop | Verify evidence, update detailed reports and gate ledger, handoff interfaces for Phase 5 | Traceable closure table; no Phase 5 implementation |

P4.3 should happen early enough to expose a target/toolchain blocker before extensive energy code. P4.1 and portable contract work can proceed while target feasibility is investigated, but generated config/build execution remains serialized.

## 11. Required validation matrix

| Area | Required cases and evidence |
|---|---|
| Official vectors | Matching standardized Ascon upstream KAT corpus on host; representative empty/nonempty/AAD cases on actual mote; retain existing AES exact-parameter vectors |
| Bounds and output safety | Truncated/oversized inputs, wrong lengths, tag/body boundaries, insufficient output, alias restrictions, unchanged caller output on failure; ASan/UBSan on shared C |
| Authenticated envelope | Bad key/tag/AAD/ciphertext, unsupported and disabled profiles, AES/Ascon profile substitution, downgrade, valid-tag malformed body, no output/replay mutation |
| Nonce/replay | Sender/profile/epoch/direction separation, zero/exhausted counter, consumed counter on crypto failure, replay edges 31/32, controlled reordering and cross-profile return |
| Boot/reset | Unprovisioned/partial context rejection; initial grant; application reset; fresh sensor/root replacement; no repeated-key counter restart |
| Aggregation | Counts 1–4, exact deadline, low traffic, 47-byte budget, overflow/no route, critical flush; no duplicate tag overhead |
| Network regressions | Official smoke if shared environment changes; N0 remains unprotected; AES behavior retained; Ascon 1+2 then 1+8; actual loss/reordering cases distinctly labeled |
| Energy | Positive idle consumption under declared currents, radio-load increase under a controlled state schedule, component conservation, timer wrap, invalid delta, overflow and retained fractional precision |
| Depletion | Larger budget gives no earlier death for identical state traces; live-network topology feedback analyzed separately; no post-cutoff forwarding/radio reactivation |
| Accounting | Dead node needs terminal evidence; missing telemetry fails; zero delivery undefined; no deaths censored; HND odd/even N; functional persistence/equal-time boundaries |
| Runner | Old CLI paths work, stale READY fails, phase4 output path correct, all writers share lock, timeout cleans only owned container, failed manifests retained |
| Reporting | Four-arm metadata validation; no native hardware timing claim; root/window definitions explicit; artifact hashes reproduce summaries |

Do not rerun the entire matrix after every documentation edit. Run relevant tests per change, then one complete final candidate validation; rerun dependent checks after new failures or code/config changes.

## 12. Experiment sequence and comparability

Start with one mote KAT, then root+2 clients for functional/negative cases. Next use root+8 and the existing seed 123456 to establish continuity across B1/B2/B4/B5. Initial defaults retain 60s warm-up, 24 readings per client, 1s period, 3s deadline, 15s drain and 67-byte protected budget unless a separately labeled scenario overrides them.

Repeat boundary scenarios at 500ms, 4000ms and 47-byte budget. Capture actual radio frames for both profiles; equal application lengths alone do not prove equal fragmentation or on-air cost.

For an engineering repeatability pilot, preselect at least three paired seeds across all four static arms after smoke succeeds. Record all seeds before execution; this is not the final Phase 6 statistical sample-size justification. Pair topology, demand, radio settings, budgets, horizon and model; crypto keys remain independently generated test inputs.

Keep short no-depletion delivery pilots separate from long lifetime scenarios. Lifetime runs need a predeclared schedule/horizon that can observe depletion and sustained service loss; simply running the existing 24-reading trace does not establish useful functional lifetime. Use separate calibration runs to choose viable budgets/horizon, freeze them, and preserve all exploratory failures.

Produce packet/delivery/latency comparisons first. Add energy/lifetime plots only for validated measurement/model tiers. Report inconclusive or negative comparisons honestly. No adaptive superiority, guaranteed percentage gain, physical battery measurement or research confidence interval is established by this phase's small pilot.

## 13. File scope and DRY boundaries

Proposed new files/directories, to be created only during authorized implementation:

- firmware/crypto/ascon_aead.c/.h and a small shared profile descriptor interface.
- firmware/energy/ for portable model/budget logic plus the Contiki sampling integration.
- external/ascon-c as a separately pinned dependency checkout, or another documented vendor location consistent with repository conventions; retain license and avoid modifying upstream sources.
- configs/phase4.json and a versioned power/lifetime model configuration.
- New shared-C/security/energy fixtures and minimal Cooja scenario helpers extending existing tests/scripts.
- docs/phase4-usage.md and a security/energy contract update that clearly preserves historical Phase 3 behavior.
- results/phase_04 for actual logs, manifests, vectors/provenance, binaries, summaries and evidence index.
- Phase 4 journals/reports listed below.

Modify the existing sensor/root, runner/parser/metrics/plots and build configuration instead of copying them into phase-specific applications. Production custom C remains under firmware and host analysis under host; scripts remain thin execution helpers and tests remain tests. No upstream Contiki/Cooja core edit.

Future modifications should need one profile descriptor/backend, one validated model config or one schema migration, not scattered profile==1 checks. Keep the current capacity 4 unless a separately reviewed later requirement changes it. Dynamic capacity, ACK/retransmission, provisioning protocols and generic plugins are not required to prepare Phase 5.

## 14. Downloads, environment and likely failures

No downloads/installations are performed by this planning task. During implementation, explain the next required dependency and scope before installing, then record actual commands, source, size/hash, version, reason, errors and resolution.

| Candidate need | Expected scope | Action |
|---|---|---|
| Official ascon-c sources, license and matching KAT | Project dependency/evidence folders | Required; pin revision and hashes, avoid moving-branch builds |
| Existing official container and native toolchain | Docker image/cache is system-managed; project artifacts are bind-mounted | Reuse existing digest, do not pull a replacement merely for convenience |
| Emulated target/compiler support | Prefer existing container tools; additional image/toolchain only if missing | Discover exact requirement with a build spike; record any download and new pin |
| Python plotting/testing | Existing standard library and container matplotlib | Do not install pandas/pytest or host compiler/Java without an actual need |

Likely failures and responses:

- Standardized/legacy Ascon mismatch: verify directory/API/vector provenance before debugging networking.
- Native timing shows no meaningful crypto CPU delta: treat as a measurement limitation and complete emulated-target validation; do not manufacture costs.
- Reference implementation exceeds target resources: retain reference KAT oracle, evaluate a pinned upstream optimized implementation with the same vectors and platform-specific evidence.
- Container/group/DNS permission failure: use the environment's approval mechanism and record the failed attempt; avoid duplicate installations or unsafe Docker permission changes.
- Mutable generated config/stale binary: use the existing shared lock, clean build, READY checks and retained binary hashes.
- Counter precision/log format failure: preserve raw logs, reject the summary, correct typed serialization and rerun.
- Depleted router still forwards: verify radio/MAC timer behavior and simulator cutoff; application silence is insufficient.
- Long run exceeds timeout: preserve failure and scoped cleanup, estimate runtime from calibration, then record a justified timeout; do not label incomplete runs as censored success.
- Timer wrap or sample rounding changes lifetime: fix arithmetic/flush cadence before running the comparison matrix.
- Whole-board current overlap: revise the documented component model before reporting joules.

RAM limits concurrency, not deliverables. Do not delete old evidence, upstream checkouts or phase_jouney/tmp to save space.

## 15. Phase 5 handoff and future compatibility

Expose a read-only energy snapshot with timestamp, model identity, validity, remaining budget and component totals. Expose a bounded profile capability table with actual supported key/nonce/tag/payload constraints. Keep policy-independent queue/deadline and protected-send APIs.

A measured operation-cost table should identify platform, compiler/flags, backend revision, profile, payload/AAD length, measurement method/units, sample count and uncertainty. Mark unavailable cells unavailable. Do not seed an adaptive policy with guessed costs or native laptop timings. Do not charge both CPU Energest time and the same operation-cost estimate in one energy total.

Future policy changes must preserve independent per-profile counter/replay contexts, bounded reading dedup, explicit allowed profiles and safe static defaults. Phase 4 tests provide these seams; Phase 5 chooses actions, hysteresis/dwell behavior and policy baselines. No online negotiation, adaptive selection or “best cipher” declaration is implemented now.

Version power models and result schemas so later model corrections produce new analyses with provenance rather than overwriting original results. Retain raw counter evidence for reanalysis. Phase 6 can expand seeds/topologies and inferential comparisons using this same runner and metric definitions.

## 16. Completion evidence and mandatory stop

During implementation maintain:

- phase_jouney/phase_04_environment_and_implementation.md: chronological commands, changes, reasons, observed outputs, failures and downstream effects.
- phase_jouney/phase_04_downloads_problems_and_resolutions.md: every actual download/install, where it lives, why needed, exact failure/fix and unresolved issues; explicitly say if no new system packages were installed.
- phase_jouney/phase_04_detailed_report.md: final architecture, decisions, validation scope, static comparisons, model assumptions, remaining risks and Phase 5 interfaces.
- docs/phase4-usage.md: actual verified commands, pins, schema/config meaning and limitations.
- results/phase_04/phase4-evidence.json: actual artifact index, hashes and requirement-to-evidence mapping.
- Updated phase index/gate ledger only after the relevant work actually executes.

Automated completion requires actual Ascon KAT/mote integration, retained AES/N0 regressions, four static controls, validated energy accounting and simulated forwarding-node depletion, lifetime-aware metrics, resolved required automated integration checks, preserved failures and reproducible evidence. If measurement or implementation gates fail, report partial completion and the exact blocker; do not silently drop a required deliverable.

Human G0/review/reproduction checks stay pending until actually performed. Engineering progress does not manufacture sign-off or establish production security.

At the end of Phase 4, write the detailed reports, state completed/pending gates and **stop**. Await the user's instruction before planning or implementing Phase 5.

## 17. Planning-task validation and handoff note

This plan was prepared by inspecting the original plans, Phase 1–3 reports/journals, current security/runner/parser/metrics code, pinned Energest sources and official Ascon/NIST references. It distinguishes saved test evidence from proposed work and notes the latest host-only malformed-body completion.

Only this temporary planning document is to be added by the current task. No Phase 4 source, configuration, dependencies, test outputs or research results are created. Before implementation, recheck workspace drift against the baseline and resolve the explicit dependency/target/model decisions using actual builds and documentation. Keep both original plan hashes unchanged.
