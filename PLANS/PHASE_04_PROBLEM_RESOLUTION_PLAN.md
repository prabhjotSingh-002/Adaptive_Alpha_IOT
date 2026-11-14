# Phase 4 — current problems and resolution plan

Date: 14 November 2026. Status: **planning only; proposed fixes have not been executed by this review**.

Implementation follow-up: the later [execution journal](../phase_jouney/phase_04_environment_and_implementation.md) records partial R1–R5 work, including fixed-byte grants, Z1 network/negative/reset runs and remaining gaps. The original review below is preserved; its planning-only statement describes that review, not current implementation completion. No complete R1–R8 closure is claimed.

This is the repair sequence for the current implementation, to be used with the [Phase 4 completion plan](PHASE_04_IMPLEMENTATION_PLAN.md), [original detailed plan](../tmp/phase_04_implementation_plan.md), [synced planning snapshot](../tmp/phase_04_synced_completion_plan.md) and [execution journal](../phase_jouney/phase_04_environment_and_implementation.md). The master and decision review remain authoritative. This document does not replace the complete Phase 4 scope or claim any pending gate passed.

The user requested a resolution plan only. This review inspected source, pinned upstream configuration and saved evidence; it did not compile firmware, run simulations, install dependencies or implement fixes. Existing PASS/FAIL statements below describe saved artifacts.

## 1. Findings that determine the next steps

| Finding | Classification | Evidence / practical consequence |
|---|---|---|
| Sky ROM overflow: reference 4136 bytes, optimized 3696 bytes | Confirmed build failures | `results/phase_04/sky-feasibility-20261114.log`, `sky-opt32-build-20261114.log`; Sky is not currently a viable full application target |
| Z1 reference sensor builds; Ascon mote KAT passes | Limited positive evidence | `z1-ref-build-20261114.log`: text/data/BSS 51498/354/6144; `z1_kat_ref_01/COOJA.testlog`: TEST OK |
| Z1 optimized KAT fails despite successful host corpus/build | Confirmed failure; cause unresolved | `z1_kat_02/COOJA.testlog`: PHASE4_KAT_FAIL; `opt32-validation-20261114.log`: host PASS. Do not infer a compiler, endian or primitive defect without isolation |
| Boot mailbox uses native `int` for 32-bit magic | Confirmed source portability defect; network effect not yet executed | `boot_gate.c:2`, `boot_gate.h` and runner `setIntValueOf`; pinned `MspMoteMemory.java:45` declares a 2-byte int. A Z1 `int` cannot represent 0x42544731, so current grant handling cannot simply be reused |
| Runner builds only native Cooja applications | Confirmed missing integration | Scenario commands, clean commands, binary collection and platform metadata hardcode cooja; no target CLI |
| Root activation is not a validated all-context transaction | Confirmed implementation gap | Root uses context 2 as the readiness gate, activates other contexts without checking return values and has no provisioning completeness metadata |
| Application has one profile context per sender/run | Confirmed gap relative to plan | Host profile-return test proves independent local contexts only; application provision/selection/telemetry does not implement the allowed profile set |
| Phase 4 security-test CLI is unavailable | Confirmed CLI restriction | Runner attack/root-reset options require Phase 3 B1; actual Ascon negative/reset integration remains open |
| Phase 4 marker was fixed, full event/schema migration was not | Partially resolved | Parser has PHASE4_COMPLETE support, but manifest schema remains 1; RX_AUTH omits profile/epoch and authentication attribution depends on configured profile |
| Four-arm results exist, plotting still supports only two legacy pairs | Confirmed tooling gap | `host/plots.py` accepts exactly two paths, requires equal security labels and permits only B1/B4 or N0 pairs |
| Production energy/depletion implementation absent | Unimplemented scope, not a failed energy measurement | No firmware/energy module; no validated power model, terminal cutoff or lifetime accounting |
| Planning/status navigation has drift | Confirmed documentation gap | Current plan inventory predates static integration; root tmp snapshot still contains relative links for its previous directory; evidence ledger omits some latest runs |

Existing native four-arm root+2 pilot delivered 48/48 authenticated readings per arm with equal generation traces and 48/48/16/16 submissions. This remains functional evidence only. Saved Python log reports 14 passing tests. Neither result closes provisioning, emulated timing, energy or depletion gates.

## 2. Priority and dependency order

1. **R1: Reproducible target/backend builds and reliable evidence.** Isolate the optimized failure, fix misleading backend selection and preserve the reference path.
2. **R2: Portable provisioning and bounded context activation.** Fix mailbox ABI before attempting protected Z1 network tests.
3. **R3: Unified target-aware runner and schema.** Make native and emulated runs explicit, with failure-safe provenance.
4. **R4: Full Z1 network, resource and timing acceptance.** Establish whether reference Z1 can support all required contexts and telemetry.
5. **R5: Both-profile security and inherited integration checks.** Complete these before treating the application as a final candidate.
6. **R6: Energy arithmetic, instrumentation and sourced model.** Depends on R4's validated timing source.
7. **R7: Terminal depletion and lifetime accounting.** Depends on R6 and verified multi-hop routing.
8. **R8: Four-arm comparisons, frozen pilots and closure.** Execute the remaining matrix and reporting from the main plan.

Work on independent portable tests may proceed while a target issue is investigated. Shared generated directories always have one writer. No package completion is inferred from source files being present. Stop before Phase 5 after Phase 4's documented closure.

## 3. R1 — Backend failure isolation and build/evidence correctness

### Confirmed issues

- Sky cannot link either attempted backend in the full sensor application. Changing to Z1 is a target decision, not a fix to Sky's resource limit.
- The optimized backend is not accepted on Z1. Its failed log does not identify which vector/check failed; the later source has numbered failure messages, so source-at-failure must not be assumed identical to current source.
- `scripts/phase4_kat_scenario.py` defaults its backend argument to opt32_lowsize for Z1, despite reference being the validated default. For native target, an explicit backend argument is currently ignored in the generated make command.
- Switching ASCON_IMPL reuses target object directories and object basenames. The helper does not force clean builds or own a lock. Last experiments used outer locks/selected cleans, but direct helper/test use is not protected by that convention.
- `scripts/test_phase4_ascon.sh` overwrites the same unit executable paths for both backends and does not acquire a lock itself.

### Resolution

1. Make reference the explicit default for every supported target and record the selected backend in configuration, commands, runtime identity and manifests. Reject ignored/unsupported combinations.
2. Centralize target/backend build selection in a small shared make include or equivalent existing build layer. Avoid diverging application and KAT source lists.
3. Ensure the orchestrator owns one shared lock from config generation through artifact finalization; standalone entry points must acquire it or clearly participate in the same ownership protocol without nested-lock deadlocks.
4. Clean between backend changes or use separate target/backend/config output directories. Archive exact source inputs, generated config, compiler/flags, scenario and binary before executing tests. Do not replace historical files with newly generated evidence.
5. Reproduce optimized failure in a clean isolated run with numbered vector/operation failures, lengths and bounded fixture bytes. Check actual compiled backend/source paths first. Compare host/reference/optimized results for the same exact fixtures and keys. Inspect compiler integer widths, endian macros, alignment, aliasing, optimizer flags and generated code only as hypotheses until evidence identifies a cause.
6. Keep the official source pinned and unchanged. If an alternative official backend or documented compiler flag is needed, validate it through the full corpus and mote matrix before accepting it. If the optimized variant remains unsupported, formally exclude that target/backend combination with the failure artifact and use validated reference for required work. Do not weaken authentication or edit the primitive to obtain a PASS.

Acceptance: reference and candidate builds cannot silently share stale objects; explicit backend selection is honored; each attempt has its own log/binary/manifest; either a verified optimized fix or documented exclusion exists. Full Phase 4 does not require spending indefinitely on an optional optimized backend when reference meets every required target gate.

## 4. R2 — Fix boot ABI, provisioning completeness and retained contexts

Files: `firmware/crypto/boot_gate.*`, `secure_packet.*`, sensor/root and runner provisioning code.

1. Replace the native-int mailbox contract with an explicit-width/byte-layout contract. Use fixed byte serialization for simulator writes or a verified target-aware accessor; do not rely on host/mote `int` having equal width or byte order. Validate symbol sizes/addresses and write the final grant only after all provisioning fields are present. A cast of the magic to 16 bits is not a sufficient fix.
2. Add version, authorized sender/profile/epoch, slot count/completeness and provisioning state. Missing slots must be distinguishable from legitimate all-zero key values. Keep the one-use grant ledger outside mote RAM.
3. Preconfigure bounded allowed contexts with independent per-profile keys. Root validates the whole required set before any activation; reject partial or invalid sets and remain locked. Check activation return values and emit READY only after complete success. Do not dynamically allocate contexts from packet headers.
4. Retain separate send counters and receive replay state per context; keep reading dedup shared per sender. Add an application-level controlled AES → Ascon → AES exercise without implementing an adaptive policy.
5. Test native and Z1 mailbox size/order, wrong version/profile/epoch, missing/partial slots, wrong/repeated grants and application/fresh-sensor/fresh-root resets. Preserve valid pre-reset traffic and prove rejection after reset without new authorized keys.

Acceptance: grant bytes round-trip correctly on both targets; partial provisioning activates no contexts; all required contexts preserve counter/replay state on return; reset never restarts the same-key counter via a repeated grant. The passing Ascon KAT does not cover this package because it calls the adapter directly.

## 5. R3 — Complete target, configuration, schema and provenance integration

Files: `host/run_experiment.py`, `parse_logs.py`, `metrics.py`, `configs/phase4.json`, event definitions and scenario helper.

### Target/configuration

- Add explicit phase, mode, target, backend, purpose, seed and configuration/schema identifiers. Validate allowed mode→profile→cap mappings, tag budget and target/backend capability before writing generated config. Current Phase 4 CLI relies on config's phase field; make CLI/resolved phase agreement mandatory rather than falling back to cipher inference.
- Extend the existing runner to Z1 mote types, interfaces, ELF paths, clean commands and binary collection. Use verified target memory provisioning from R2. Validate IPv6 sender mapping against actual target addresses; do not assume native address suffix behavior or weaken authentication to bypass a mismatch.
- Retain named-container timeouts/owned cleanup for standalone target/KAT runs too. A simulator timeout or crash is not a valid censored lifetime outcome.

### Schema/validation

- Introduce a new schema version for new Phase 4 telemetry and manifests; explicitly dispatch legacy records using their recorded schema/producer provenance. Early Phase 4 pilots used PHASE2_COMPLETE while later ones use PHASE4_COMPLETE. Both remain historical records; never silently rewrite them or infer one universal parser rule from phase alone.
- Require runtime metadata matching resolved settings: profile/allowed set, epoch, cap, period, deadline, tag budget, model/timer identity and config ID. Add authenticated profile/epoch to accepted RX events and context identity to TX/accounting keys where required by multi-profile operation.
- Parse completion as an exact structured event rather than an arbitrary substring. Reject contradictory completion markers and malformed/missing terminal records. Keep strict non-depletion rules.
- Validate each BOOT_REQUEST and context activation against declared identities rather than merely collecting boot events or trusting any nonzero profile.

### Evidence issues visible in current runner

- Manifest initialization/config/scenario work occurs outside the execution try/finalization block. Failures there can leave incomplete directories without a complete failure manifest. Persist an attempt record first and finalize all supported failure paths.
- Commands/container identity are added in memory after the initial manifest write; persist them before launch so abrupt termination leaves reconstructable intent.
- After a failed launch, the runner copies every existing native build binary. If Docker never started/clean never ran, these may be artifacts from a previous run. Record build success/identity and copy only artifacts proven to belong to this attempt; mark unavailable otherwise.
- Dependency hashes always enumerate reference sources. Hash the actually selected backend, API headers, KAT, license, dependency commit and dirty state. Verify Ascon pin at execution just as Contiki/Cooja pins are checked.
- Freeze or snapshot source inputs before a multi-arm process. Do not edit runner/source while it executes: the process may execute previously loaded Python while later manifests hash different on-disk code. The existing journal discloses such a metadata edit; preserve that qualification and rerun a stable final candidate.

Acceptance: wrong target/backend/config/schema fails; injected provisioning/build/parse/timeout failures leave honest manifests; archived binaries and hashes correspond to executed inputs; old evidence is replayable through explicit legacy parsing; both native and Z1 routes use the single pipeline.

## 6. R4 — Establish complete Z1 feasibility before energy claims

The pinned MSPSim Z1 configuration specifies 8 KiB RAM. Current reference sensor static data+BSS is 6498 bytes, leaving approximately **1694 bytes before stack and other runtime demands**. This is an arithmetic resource warning, not measured safe stack headroom. Root+8, dual profiles and energy telemetry can increase memory use.

1. Build both root and sensor at root+2 and intended root+8 dimensions, for both ciphers and the full authorized context set. Preserve map/size output and measure worst-case stack under KAT, receive, encryption, logging and interrupt load. Review bounded scratch lifetimes rather than assuming linker success proves safety.
2. Run actual root+2 protected network traffic on Z1, then larger topology only after resource checks. Verify boot grants, routes, authentic delivery, exact packet lengths, deadlines, simulator-global timestamps and radio capture format.
3. Establish traffic fairness on emulated CPU timing. GEN-before-network reduces drift but expensive crypto and scheduling can still shift later generation. Test the prospective schedule and realized trace; measure any jitter. Resolve the generator/timing contract before comparisons, without silently relaxing old native matching checks.
4. Inspect built clock/Energest definitions and validate counter progression with idle, controlled CPU work and radio work. Pinned MSP430 defaults shown in `msp430-def.h` are a 4-byte clock at 128 Hz and a 2-byte rtimer; do not misdiagnose clock_time as 16-bit. Determine the actual Energest clock source/width/frequency from the build and prove safe flushing across wrap.
5. Quantify telemetry overhead, verify CPU/LPM/deep totals cover elapsed time within resolution, and treat radio timeline overlap separately. Native laptop elapsed time is not emulated MCU crypto time.
6. If full contexts/stack do not fit, preserve measurements, reduce avoidable application duplication/buffer lifetime safely, or evaluate another supported target. Do not delete required security/telemetry or assume a hybrid CPU/radio model without validation.

Acceptance: both root and sensors run securely at required dimensions, runtime memory is defensible and the timing path measures work with documented resolution. Only then select the target/model for energy comparisons.

## 7. R5 — Complete security and integration validation

Extend the runner's security purpose and CLI to Phase 4 and both profiles. Current restriction to Phase 3 B1 prevents exercising existing injection/root-reset scenarios on Ascon.

Required evidence: wrong key/tag/AAD/ciphertext, unknown/disabled profile, downgrade/substitution, valid-tag malformed body with unchanged replay state, counter/replay boundaries, profile return, application/sensor/root resets and incomplete grants. Preserve counts 1–4, exact deadline, low traffic, 47-byte budget, queue/no-route behavior and critical flush. Close actual receive reordering and radio-layer loss; a pre-UDP omission is not radio loss.

Run N0 and AES regressions after final shared changes. Use production protocol/aggregation/crypto code in host tests. Keep fixtures and security-purpose runs separate from clean comparative summaries.

Acceptance: every required automated row maps to an actual retained artifact; unexpected rejection/error remains a failure outside its declared negative test.

## 8. R6 — Energy work remains to be implemented

Create portable production energy/budget arithmetic under `firmware/energy/`, a thin sampler of official Energest counters, validated configuration and a sourced component power-model document. Select numerical assumptions from authoritative target documentation during implementation; this planning review supplies no guessed currents or joules.

Use checked integer units, retained fractional remainders and overflow/invalid-delta failure semantics. Preserve wide integer precision in telemetry. Test the same production C on host with independent high-precision fixtures. Reconcile raw counter intervals to component and total energy, avoid whole-board current double counting and avoid charging crypto twice.

Actual acceptance includes positive idle consumption, controlled load increase, wrap/precision/overflow/conservation tests, sampling sensitivity and overhead. Fix boot-to-death budgets separately from warm-up/measurement/drain reporting windows. Exclude mains root from primary battery-node energy but collect it separately. Energy per delivered reading is undefined at zero authenticated deliveries.

## 9. R7 — Terminal depletion and lifetime accounting

Add a terminal ACTIVE→DEPLETED transition with final counters, budget, sample time, overshoot and queued-reading disposition. Stop application activity and prove forwarding/radio shutdown; if supported application APIs cannot guarantee permanence, use verified simulator power-off/removal with final evidence and an explicit in-flight boundary. Timer reactivation, regrant or reset must not resurrect a dead mote within a lifetime run.

Prove a multi-hop forwarder actually carries downstream traffic before depletion and observe cutoff/recovery/service failure afterwards. Application silence alone is insufficient.

Extend metrics by explicit lifetime purpose: actual generation while alive, fixed prospective demand, demand shortfall, verified terminal records, survivor final snapshots, drain delivery cohort and equal-time ordering. Missing telemetry/crashes remain errors. Compute FND, HND at ceil(N/2), and persistent functional loss over fixed battery-node/demand definitions. Unobserved events are censored, not invented deaths at the horizon. Test fixed-trace monotonic budgets, odd/even node counts, no deliveries/deaths and persistence boundaries.

## 10. R8 — Comparisons, remaining matrix and documentation closure

- Generalize plotting to four explicit supported static arms using comparable metadata and validated summaries. Current equal-security-string check must become explicit compatible-security/profile validation; forbid N0 mixed into security-equivalent results. Keep legacy plots reproducible.
- Give four-arm comparisons a clear group manifest; current placement inside the second run is ambiguous. Record all run identities/configuration checks and group success/failure. A trace mismatch must fail comparison eligibility even if individual runs completed.
- Add seed selection and freeze the main plan's three paired seeds (123456/123457/123458) separately from calibration seed 223456. Freeze one shared model, budgets, horizon and service criteria before comparative lifetime runs.
- Execute root+8 four-arm continuity/repeatability, 500ms/4000ms/47-byte boundaries, final security/regression matrix and validated lifetime runs. Preserve all exploratory and failed results. Plot only validated measurement tiers and honest censored outcomes.
- Refresh the current plan's stale inventory and evidence ledger with actual scope; repair root tmp relative navigation without deleting historical content. Link current execution state from the handoff. Preserve original authoritative plan hashes.
- Produce the required Phase 4 detailed report, downloads/problems report, usage, power model, experiment protocol and hash-indexed gate ledger. Human G0/review/reproduction stay pending until performed. Final automated completion requires all mandatory acceptance rows, including full energy and forwarding-node death, then stop before Phase 5.

## 11. Planned verification checkpoints

| Checkpoint | Evidence required before proceeding |
|---|---|
| A: stable build/provisioning | Explicit target/backend identity, clean/fresh binaries, portable grant and all-context validation |
| B: target viability | Both ciphers' mote KATs, protected Z1 root+2 network, root+8 resource/stack evidence, clock/counter validation |
| C: secure integration | Native/N0/AES regressions and both-profile negative/reset/reorder/loss/critical-flush evidence |
| D: trustworthy accounting | Shared energy C tests, actual idle/load/conservation/wrap and telemetry reconciliation |
| E: terminal lifetime behavior | Actual bottleneck-forwarder cutoff, terminal snapshots and lifetime/censoring tests |
| F: complete phase | Frozen four-arm matrix, reproducible summaries/plots, final reports and honest automated/human gate ledger |

The optimized backend's exact failure cause may remain a documented excluded-backend issue if validated reference satisfies all required gates. Sky need not become a supported target to complete Phase 4; an accepted emulated target is required. These decisions do not waive memory, timing, network or energy checks.

## 12. Inspection fingerprint and limits

Selected current-source SHA-256 values (for this review's context, not new test evidence):

| File | SHA-256 |
|---|---|
| firmware/crypto/boot_gate.c | c499ce453a3ee63f1d863e4b1bea99198ce51de275ad840a06b07fdf65db70e1 |
| host/run_experiment.py | 895cd2d4b4eb525df926d6afb4d1399c7209e4afb806432b5be85e586f75ea87 |
| scripts/phase4_kat_scenario.py | 5c85716eba73e116ca70bd9183fe184d4d17a8d6f605975c6cbdf99fa2778832 |
| firmware/common/events.h | 28bc2d92c3809618da4bb5f3de4a1e78f0756b2280659cdaff88f2fc4ed32f1f |

Original master SHA-256 remains `2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385`; decision review remains `69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a`.

Review method: read current implementation/plan sections, inspect saved host/build/Cooja outputs and pinned simulator type/memory configuration, and check source paths. One attempted read of `arch/cpu/msp430/clock.c` found no such file; no runtime inference relies on it. This is a targeted review, not an exhaustive security audit or independent reproduction. No root cause is claimed for the optimized mismatch beyond the observed target-dependent failure.
