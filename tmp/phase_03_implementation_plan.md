# Temporary Phase 3 implementation plan — AES-CCM and secure pilot

Date: 13 November 2026 (IST).
Status: PLANNING ONLY. Phase 3 firmware, tests, provisioning, simulations and results have NOT been implemented or executed by this planning task.
Purpose: a detailed implementation handoff for another model. Stop after creating/reviewing this document; implementation requires the user's subsequent instruction.

## 1. Authority, scope and reading order

Read these before editing implementation:

1. [Project rules](../../AGENTS.md).
2. [Original master](../../PLANS/MASTER_IMPLEMENTATION_PLAN.md), especially Sections 3, 4, 6, 7, 8 and 9.
3. [Original decision review](../../PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md), especially correctness decisions and W4/W5.
4. [Phase index](../README.md), [Phase 1 environment](../phase_01_environment.md), [Phase 1 downloads/problems](../phase_01_downloads_problems_and_resolutions.md).
5. [Phase 2 temporary plan](phase_02_implementation_plan.md), [Phase 2 journal](../phase_02_environment_and_implementation.md), [Phase 2 detailed report](../phase_02_detailed_report.md), [Phase 2 usage](../../docs/phase2-usage.md).
6. Existing production code, tests, config and evidence referenced below.

The original documents remain authoritative and unchanged. The companion's introductory statement that no firmware exists describes its original review date/state; actual progress is recorded in the phase journals. The master's title “Phase 1 Software Implementation Playbook” names the broader software project; the execution phases here follow phase_jouney/README.md.

This phase implements vetted AES-128-CCM, authenticated packet handling, nonce/key/replay lifecycle, protected aggregation and a reproducible B1/B4 engineering pilot. Target G2 and the protected portion of G3; retain G1. Automated evidence does not satisfy G0's two-student manual review or G6's independent reproduction.

Do not implement Ascon, energy/battery models, adaptive policies, online suite negotiation, custom networking, production key provisioning or the full research matrix here. Those remain required in later phases. Reserve extension boundaries without placeholder backends or speculative frameworks.

Master deadlines remain: AES integration checkpoint 14 November 21:00 IST; feature freeze 16 November 14:00; evaluation 17 November. If execution takes place later, record the actual date and missed checkpoint honestly. Never relabel existing N0 data as secure to meet a deadline.

## 2. Verified starting point and evidence

These are observations from reading existing source and saved evidence, not new test results.

| Area | Existing state | Phase 3 consequence |
|---|---|---|
| Phase 1 | Pinned official Contiki/Cooja/container; unchanged official 1-root/8-client RPL demo ran | Reuse toolchain, topology and network stack |
| G0 | Two-student human verification remains pending | Preserve pending status |
| Phase 2 transport | Shared codec, generator, UDP path, bounded aggregator and validated logs | Extend these modules; do not fork B1/B4 applications |
| Primary N0 pair | Seed 123456, 192 generated/delivered in each arm; 192 vs 64 submissions; exact matching GEN traces | Useful regression reference, not authenticated evidence |
| Primary batch behavior | 1-second period, 3-second deadline, cap 4 produced count-3 batches | Preserve exact-deadline flush-before-offer ordering |
| Boundary runs | 500ms gives full count 4; 4000ms gives count 1; 47-byte budget gives effective cap 2 | Repeat under real tag overhead |
| Radio capture | Selected N0 runs had zero observed fragments | Does not establish protected 67-byte safety |
| Timing | GEN was moved before networking to fix a measured 1ms paired-trace mismatch | Preserve this ordering; test cipher-induced effects |
| Git | Project has no initial commit; files are untracked | Record actual source hashes and null SHA; never invent a revision |
| Failures | Failed builds/scripts and an early mismatched pair were preserved | Keep them and preserve all new failures |
| Existing tests | Shared C ASan/UBSan checks and 10 Python fixture checks passed in Phase 2 | Reuse and extend; fixtures are not experiments |

Evidence anchors:

- [Source pins](../../results/setup/source-pins.json).
- [Phase 2 evidence index](../../results/phase_02/phase2-evidence.json).
- [Primary N0 single manifest](../../results/phase_02/20261113T093713547602Z-N0-single-8/manifest.json).
- [Primary N0 batch manifest](../../results/phase_02/20261113T093733639048Z-N0-batch-8/manifest.json).
- [Primary pair check](../../results/phase_02/20261113T093733639048Z-N0-batch-8/paired-comparison.json).
- [Phase 1 regression manifest](../../results/phase_01/smoke-20261113T094208160354Z/manifest.json).

Pinned dependencies to reuse:

- Contiki-NG: a304687372e2917d325d4d71cf68610fe9a6279b.
- Cooja: fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4.
- Container: contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609.
- Existing built launcher inside the standard container mount: /home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja.
- Reuse Java/GCC/Make/Python and existing matplotlib in that environment. Use serial builds/runs; 4GB RAM affects concurrency, not required quality or scope.

## 3. Decisions reviewed and proposed

| Decision | Recommendation | Evidence or acceptance condition |
|---|---|---|
| Network and simulator | Keep pinned Contiki RPL, UDP, MAC, 6LoWPAN and Cooja | No upstream core edits |
| AES implementation | First candidate: pinned software ccm_star_driver plus AES-128 | Source inspected; 16-byte-tag KAT and actual mote build still required |
| Cipher parameters | AES-128; 13-byte nonce; 16-byte tag; encryption and authentication enabled | Matches inspected backend dimensions; exact-variant tests required |
| Profile registry | 0=N0; 1=AES-128-CCM; other values rejected | Ascon remains unavailable until its own phase |
| Wire version | Retain v1 header offsets; profile selects body protection | Preserve strict N0 profile/epoch rules |
| Key policy | Independent host-generated test key per sender and run, with run-scoped context | No traffic-seeded keys or project-wide permanent key |
| Startup/reset | Default-locked crypto plus one-use simulator boot authorization; fail closed after reset | Proposed mechanism; must prove against pinned Cooja reset behavior |
| Replay | Separate authenticated packet-counter window per sender/context | Existing reading-ID window is not packet replay protection |
| Batching | Existing aggregator and shared application sources | Tag budget counted exactly once |
| Runner | Extend host/run_experiment.py with explicit phase/config/mode | One lock shared across both phases |
| Metrics | Extend host/metrics.py; schema-aware normalization | N0 remains unauthenticated; secure counts require verified receive path |
| Evidence | Separate Phase 3 run directories and schema; preserve old artifacts | No in-place “upgrade” of historical results |
| New dependencies | None expected for AES/network/build; official vector download required | Any fallback dependency must pass provenance/license/build review |

The boot mechanism, exact-vector coverage, measured fragmentation boundary and native target resource footprint are unresolved validation gates, not claims of compatibility. Resolve them early; do not bury them behind pilot plotting.

## 4. Concrete integration map

| Existing file/module | Required change | Compatibility and checks |
|---|---|---|
| firmware/common/protocol.h/.c | Factor shared bounded header/body serialization from N0 policy; add profile metadata/constants | N0 encoding remains byte-identical; N0 decode rejects nonzero profile/epoch |
| firmware/aggregate/aggregate.h/.c | Reuse queue operations and overhead budgeting; only change if interface tests require it | Build must not consume queue; deadline, overflow and own-node rules unchanged |
| firmware/crypto/ (new) | Small AEAD adapter, packet protection, nonce/context lifecycle and replay logic | Portable production sources used by host and mote tests |
| firmware/sensor/sensor.c | Mode dispatch, startup gate, secure counter reservation, seal/send/drop handling | GEN-before-network; no silent retries or plaintext fallback |
| firmware/root/root.c | Startup gate, context lookup, authenticated open, replay check/commit, secure RX logging | Do not call existing N0 decoder on ciphertext |
| firmware/Makefile | Link vetted backend and project adapter correctly for both applications | Inspect map to avoid duplicate/wrong AES driver |
| firmware/project-conf.h and generated settings | Profile, schema/config identity, context dimensions and overhead | Generated from validated config; clean build each arm |
| configs/phase3.json (new) | AES parameters, B1/B4 caps, boot policy, seed/timing/budget | Keep configs/phase2.json unchanged unless a documented compatible migration is necessary |
| host/run_experiment.py | Phase/config/modes, lifecycle/boot harness, shared lock, manifests and pair checks | Existing Phase 2 invocation remains N0 |
| host/parse_logs.py | Versioned secure events and explicit completion handling | Legacy logs never acquire auth_ok=true |
| host/metrics.py | Profile-aware lengths and authenticated delivery/accounting | Sole metric implementation |
| host/plots.py | Derive labels from validated summaries and pair metadata | Current hardcoded N0 title must not label B1/B4 |
| tests/unit/, tests/security/, tests/integration/ | Production-core crypto and negative integration coverage | No parallel toy crypto implementation |
| scripts/test_phase3.sh (new) | Thin reproducible test entry point | Dependencies/build commands recorded; no duplicate runner |
| docs/protocol.md, architecture.md, threat-model.md | Freeze exact security/state/event contract before integration | Distinguish simulation test policy from production guarantees |
| docs/phase3-usage.md, decision-log.md, reproducibility.md | Commands, design selections, limitations and evidence paths | Create only what is useful for this phase |
| phase_jouney/ phase 3 reports | Detailed work/download/problem/evidence record | Finish reports and stop before Phase 4 |

Suggested small module split: crypto.h/.c for explicit status/profile dispatch, aes_ccm.c for vetted backend adaptation, security_context.h/.c for nonce/replay/lifecycle, protected_packet.h/.c for wire orchestration. Names may be simplified; preserve ownership and a single implementation of each behavior.

## 5. Wire contract and buffer migration

Current N0 valid() explicitly requires profile=0, epoch=0, positive packet counter and 1..4 readings. lab_encode/lab_decode cannot simply be reused with profile=1. Refactor common serialization, retaining N0-specific entry points and tests.

All integer wire fields use big-endian, with no raw C-structure copies:

| Offset | Size | Meaning | AES rule |
|---:|---:|---|---|
| 0 | 1 | version | 1 |
| 1 | 2 | sender_id | Configured sender, currently 2..clients+1 |
| 3 | 1 | profile_id | 1 |
| 4 | 2 | key_epoch | Nonzero, exactly the provisioned context epoch |
| 6 | 4 | packet_counter | Positive, allocated once per encryption attempt |
| 10 | 1 | readings_count | 1..4, also bounded by effective cap |
| 11 | 10 × count | Reading body | Ciphertext for AES; plaintext only for explicit N0 |
| 11 + 10 × count | 16 | Tag | AES only |

AAD is the exact 11 header bytes received/transmitted, including version, sender, profile, epoch, counter and count. Authenticate the received bytes; do not silently repair or normalize malformed headers.

The existing network addresses remain routing metadata. The source IPv6 suffix check is a sanity check, not identity authentication. Bind sender/context/direction through authenticated header and nonce. Document that outer IP/MAC fields are not all application AAD in this layout.

Reading body stays id:u32, created_ms:u32, value:u16; require nonzero strictly increasing IDs within a batch. Empty AEAD plaintext is a crypto test case, but a zero-reading application packet is invalid.

Lengths:

| Count | Body | N0 wire | AES wire |
|---:|---:|---:|---:|
| 1 | 10 | 21 | 37 |
| 2 | 20 | 31 | 47 |
| 3 | 30 | 41 | 57 |
| 4 | 40 | 51 | 67 |

Define separate header, body maximum, N0 wire maximum and protected wire maximum constants. Current sensor payload[LAB_PACKET_MAX] is only 51 bytes: secure transmission needs 67. Audit root scratch, adapter outputs, tests, metrics and every bound together. Validate size_t arithmetic before narrowing to uint16_t.

Aggregator fit stays floor((payload_budget - header - profile_overhead)/10), then min(configured cap, fit, 4); reject negative/too-small budgets before unsigned subtraction. For AES profile_overhead=16 and actual length already includes it. Do not check actual_AES_length+16 against the budget. Phase 2's N0 reserve=16 remains a historical budgeting policy, not an on-wire tag.

Proposed API contracts (names may change):

- encode_header/decode_header: bounded syntax only, no plaintext parsing.
- encode_readings/decode_readings: shared reading validation and byte order.
- N0 encode/decode: profile 0 and epoch 0 only.
- seal/open: explicit status, input/output capacities, zero produced-length on error.
- protected_packet_seal/open: compose wire, context, body codec and backend; do not duplicate serializer code.
- replay_candidate/commit: state mutation separated from tentative checks.

Define whether input/output aliasing is permitted. Reject unsupported aliasing or lengths explicitly. open() must leave caller plaintext/batch output unchanged on any error; tentative bytes remain private and are wiped.

## 6. AES backend integration and independent correctness evidence

Inspected source:

- [CCM driver header](../../external/contiki-ng/os/lib/ccm-star.h).
- [CCM implementation](../../external/contiki-ng/os/lib/ccm-star.c).
- [AES implementation](../../external/contiki-ng/os/lib/aes-128.c).
- [Existing upstream test](../../external/contiki-ng/tests/08-native-runs/11-aes-ccm/test-aesccm.c).

The pinned CCM code has a 13-byte nonce, L=2, uint16_t lengths and valid even MIC sizes 4..16. The driver returns void. On decrypt it modifies the supplied message and computes a MIC; it does not accept/check a received tag or return authentication success. Invalid MIC length silently returns. The project adapter must enforce the fixed 16-byte tag and all bounds before calling it.

Receive adapter sequence:

1. Validate key/context, nonce size, tag size, lengths, buffers and capacities.
2. Copy ciphertext to private fixed-size scratch.
3. Set the exact context key immediately before the backend call.
4. Decrypt scratch and compute the candidate 16-byte tag.
5. Compare all 16 bytes using a vetted constant-time comparison facility if available, or a reviewed fixed-length accumulator without early exit. Inspect compiler behavior; do not claim whole-backend constant-time execution.
6. On mismatch, wipe scratch and temporary tag, return authentication error and release no plaintext.
7. On success, validate/decode the application body into tentative output; publish only after receive-state checks pass.
8. Wipe sensitive temporary buffers using a method that survives optimization.

Use the pinned implementation directly; do not retype AES, CCM, key expansion or a bespoke MAC. Preserve upstream notices and record source/license hashes. Software AES uses shared round-key storage and table lookups: no side-channel-resistance claim follows from constant-time tag comparison.

Select/link the software driver deliberately. Check platform CCM_STAR/AES_128 configuration, linker map and whether another network component uses the same key schedule. Serialize set_key plus AEAD without yielding; no interleaved callback/interrupt user may overwrite the key. If the target cannot establish that ownership, isolate a vetted supported context backend or block that target. Do not disable interrupts for an unbounded duration without platform evidence. Existing application-level crypto does not require changing MAC security.

Existing upstream AES tests use MICLEN=8 and generated test vectors. They are supplemental regression evidence, not proof of the required 16-byte-tag profile.

Official-vector acquisition during implementation:

- Use [NIST CAVP block cipher mode vectors](https://csrc.nist.gov/Projects/cryptographic-algorithm-validation-program/cavp-testing-block-cipher-modes), specifically its CCM SP 800-38C collection.
- Record final archive URL, retrieval date, archive/file hashes, parameter blocks and case identifiers.
- Select published AES-128 / nonce-length 13 / tag-length 16 cases. Preserve original bytes and expected ciphertext/tag. Do not truncate a tag from a different CCM parameterization.
- Cover encryption and decryption, official rejection cases where available, empty/nonempty plaintext and different AAD lengths. If the official exact-parameter subset does not cover every edge, supplement with a pinned independent oracle and clearly mark provenance; never replace all official vectors with self-generated cases.
- Freeze the bounded lengths supported by the application adapter. Reject unsupported long inputs explicitly; do not accidentally claim support for the backend's entire uint16_t range.
- Verify the same adapter on host and in a small actual Cooja test application. Host include/config shims may supply platform declarations, never crypto behavior.

NIST describes these vectors as informal correctness checks, not a replacement for CAVP validation. No certification claim is permitted. No vector archive was downloaded or executed by this planning task.

## 7. Nonce, key, boot and restart lifecycle

This is a mandatory early work package. A packet counter initialized to 1 with a compiled fixed key is not safe across resets.

### 7.1 Proposed exact nonce encoding

13 bytes, injective within the configured domains:

| Bytes | Meaning |
|---|---|
| 0..2 | Domain bytes 0x52,0x53,0x4c (“RSL”) |
| 3 | Profile 1 |
| 4 | Direction 0 for sensor-to-root |
| 5..6 | sender_id, big-endian |
| 7..8 | key_epoch, big-endian |
| 9..12 | packet_counter, big-endian |

Version remains authenticated in AAD. Different future protocol versions must not reuse a key/domain with counters restarted. Direction 1 is reserved, unsupported in Phase 3; do not send reverse protected messages with this key context.

Epoch must match a preinstalled context. A larger received epoch does not authorize installing a new context or resetting replay state. Counter zero, epoch zero, unsupported profile/direction and counter/epoch rollover are rejected.

### 7.2 Test-key provisioning and reproducibility

Use Python's standard-library OS-backed secure randomness for independent 16-byte per-sender, per-run test keys. Keep key generation independent of the traffic/radio RNG. Root receives the corresponding test key table; each sensor selects only its own context. This is simulation provisioning, not production secret storage.

For each new experiment execution, including each paired arm and normal reruns, provision fresh keys. Save a clearly labeled local test fixture plus hashes/context IDs so inputs are auditable; keys never go into serial logs or ordinary charts. Test keys compiled into binaries are recoverable and are not production secrets.

Keep fixtures separate from actual future credentials. Controlled archived-fixture replay for byte-for-byte debugging must be explicitly isolated and labeled a test replay; it is not a fresh operational context. A default rerun uses fresh keys and compares generation/behavior, not ciphertext identity. Do not derive a key by ad hoc hashing a seed, timestamp or node ID. No KDF is needed for independent keys.

Use epoch=1 for a newly generated independent run key if desired; a new key is the new cryptographic context. Never recycle an exhausted epoch under the same key. Refuse collisions/reuse in the local context registry rather than silently accepting a duplicate fixture.

### 7.3 Recommended simulator-only fail-closed boot design

No durable restart mechanism has been validated in Phase 1/2. The inspected Cooja CFS implementation stores simCFSData in mote memory; that alone does not prove reset persistence. Do not call a static variable, CFS array, random boot ID or a host manifest a persistent nonce allocator.

Recommended bounded implementation for this phase:

1. Crypto state starts LOCKED on every sensor/root boot and on security-context reinitialization. Data send/open routines themselves check this state.
2. Firmware exposes a small simulator provisioning mailbox, initially empty, and emits a boot-request event. No secure application data can be emitted/accepted while locked.
3. The Cooja script owns a one-boot ledger per mote outside emulated mote RAM. Through the pinned Cooja memory API it grants one run-context activation to each expected mote, tied to expected profile/epoch/config identity.
4. The firmware consumes and clears the mailbox grant before becoming active. Initialization always clears active state; the initial binary image must not contain an already-valid grant.
5. A second boot request or missing/mismatched grant never unlocks the same context. The harness records the reset and stops the affected security test/run as appropriate; the firmware stays locked even if the harness is absent.
6. A root reset likewise remains locked: clearing its replay window must never automatically resume acceptance under the old keys.
7. Restart the whole experiment through the runner with new keys/context and fresh build/config when recovery is required. No in-band handshake is added.

Local API starting point: external/contiki-ng/tools/cooja/java/org/contikios/cooja/mote/memory/VarMemory.java provides named-variable access including setIntValueOf. Exact script bindings, scheduling, reset API, symbol retention and memory reinitialization behavior still need an executable proof. Implement harness code under host/ and custom firmware under firmware/; do not patch Cooja.

Required proof cases: no grant/no crypto activity; one grant/normal traffic; sensor reboot after transmission/no further protected send; root reboot/no old replay acceptance; repeated/spoofed boot log/no extra grant; wrong context grant/rejection; context reinitialization while running/locks first. The script must grant only expected genuine startup state, not arbitrary text matching.

A harness that merely notices a reboot after a repeated nonce has already been sent is insufficient. Verify the firmware gate is the enforcement point. Differentiate application restart from full mote-memory reset. If the pinned native target lacks a faithful reset facility, implement/test the supported security reset hook and explicitly report that narrower coverage; the full reset acceptance item remains pending.

Simulator snapshot rollback that restores both application and external ledger is outside this design's protection. Disable such resume workflows in the experiment runner and state the limitation. Supporting arbitrary rollback/power failure would require a separately validated persistent state design; do not claim it here.

If this mechanism cannot be validated, stop secure pilot qualification and document the blocker. Alternatives may use a proven persistent counter/epoch backend, but must preserve fail-closed startup and be reviewed/logged before selection. Do not quietly simplify to “tests never reboot.”

### 7.4 Counter allocation and failure semantics

Use READY/LOCKED/EXHAUSTED or equivalent explicit states.

- Check route/socket, batch validity and output capacity before requesting a counter.
- Reserve and consume the counter immediately before AEAD invocation, not after UDP submission.
- Once reserved, never reuse it if sealing, submission or later processing fails. Gaps are valid.
- Reserve UINT32_MAX as exhausted sentinel to match the current conservative boundary: use 1..UINT32_MAX-1, then lock; never wrap to zero.
- Keep queue commit separate from counter commit. Batch construction does not remove readings.
- On internal crypto/context failure, emit a specific fatal error, account queued/generated readings explicitly, and stop that secure application path. Never retry the same plaintext with the same key/nonce or switch to N0.
- The failure scenario is a failed normal pilot, even if all drops were logged. Dedicated negative tests assert the expected failure.
- Root reception, not simple_udp_sendto's always-zero return, establishes delivery.

## 8. Root replay and authenticated acceptance

Keep separate state for packet replay and reading deduplication. The existing lab_seen window tracks reading IDs and cannot protect a packet context by itself.

Recommended packet window: highest counter plus 32-bit bitmap, keyed by sender/profile/key identity/epoch/direction. A nonmutating eligibility check followed by commit avoids state poisoning. A copy-then-commit reuse of generic window arithmetic is acceptable; do not use one mutable instance for both packet and reading state.

Receive order:

1. Require active root context; validate minimum/maximum and exact length, header syntax and configured sender bounds.
2. Select only a preprovisioned profile/key/epoch. Reject N0 in a secure run; profile 0 is not a downgrade escape.
3. Apply source address sanity and optionally a nonmutating old/duplicate counter precheck.
4. Authenticate/decrypt into scratch using received header AAD and derived nonce.
5. Validate complete reading body into temporary batch state.
6. Recheck replay eligibility if state could have changed, then commit the accepted counter exactly once.
7. Update reading deduplication and emit authenticated receive events.
8. Wipe scratch; errors must not change caller output, replay state or delivery counts.

A forged high counter must not advance the replay window. Invalid-tag packets must not evict legitimate packets or poison another sender. Shift deltas >=32 require a branch that avoids undefined C shifts. Counter arithmetic does not use wraparound sequence comparisons because wrap is prohibited.

Valid reordered counters inside the window may pass once; duplicates and older counters are rejected. An authenticated packet containing already-delivered reading IDs must not increase unique delivery. Invalid plaintext structure after successful authentication is rejected without publishing a partial batch. Keep reason categories distinct: format/profile/context/replay/auth/body/lifecycle.

## 9. Sensor integration, timing and queue behavior

Reuse current 125ms etimer service, deterministic generator, warmup and finite schedule. Preserve GEN logging before any flush/crypto/network work. Continue flushing an expired old batch before offering the new reading at the exact deadline.

Do not allow cipher selection, key RNG or packet-count-dependent RNG consumption to change generated data or schedule. Compare full sorted GEN tuples (node,id,created_ms,value,sim_time_us) between B1/B4 as Phase 2 does. If cipher work exposes drift, fix scheduling or explicitly preregister a justified timing tolerance before comparison; do not silently round timestamps or drop disagreeing rows.

Distinguish three times:

- oldest queue hold at flush initiation: existing Phase 2 definition;
- seal/submission duration or actual submission time, if instrumented;
- simulator-global generation-to-authenticated-RX delay.

Never relabel flush initiation hold as completed radio-send time. If protected processing makes actual enqueue-to-submission exceed an intended hard deadline, expose it and adjust flush scheduling consistently rather than hiding cost. Do not claim hardware-accurate AES runtime from native Cooja.

Preserve no-route-before-deadline retention and explicit expired-queue drops. Add explicit terminal accounting for crypto/context failures so the loop cannot repeatedly log an error forever with a permanently stuck queue. Ensure normal DONE and the drain horizon are meaningful after the last pending batch.

Do not add application ACKs, retransmission or inter-node aggregation. If later needed, they require separate measured protocol work.

## 10. Configuration, orchestration and artifact ownership

Extend the existing runner rather than duplicating it. Proposed CLI, to be implemented and documented (not currently available):

    python3 host/run_experiment.py --phase 3 --mode B1 --clients 2
    python3 host/run_experiment.py --phase 3 --mode B4 --clients 2
    python3 host/run_experiment.py --phase 3 --mode both --clients 8

Keep the current no-phase invocation equivalent to Phase 2 N0. Select configs/phase3.json explicitly for Phase 3; “both” means the selected phase's pair. Wrong phase/mode/profile/tag combinations fail validation before generated files are touched.

Initial matched secure pilot parameters:

- B1: AES profile 1, cap 1.
- B4: same AES profile, cap 4, deadline 3000ms.
- Both: seed 123456, warmup 60000ms, period 1000ms, 24 readings/sensor, drain 15000ms, payload budget initially 67.
- Same root+2 then root+8 topology, radio/MAC settings, node ordering and generation schedule.
- No attacks/reset injection in performance arms.
- Independent run keys do not change traffic inputs or key length/algorithm cost assumptions.
- Keep any additional seed list explicit and frozen before running it.

Retain one writer for generated config, key fixtures and both build directories. Safest compatibility path is to keep using the existing results/phase_02/.runner.lock for both phases initially, despite its historical name; migrate to a common results/.runner.lock only with coordinated legacy handling. Two different locks for the same build directories are unsafe. Hold ownership through artifact capture and pair metadata finalization.

Validate all config fields/types/ranges, timer multiples, horizon bounds, allowed modes, sender count, effective cap, profile availability, key dimensions and budget before build. Firmware READY/ROOT_READY should identify resolved config/schema/profile/epoch/tag/nonce/budget/cap; compare with manifest to catch stale binaries. Do not expose secret key bytes.

Clean root/sensor builds sequentially; use pinned environment. Test process ownership and timeout handling. Use uniquely named/labeled per-run containers; on timeout/interruption terminate only the owned container and retain logs/status. Never stop unrelated Docker jobs. Existing sg docker invocation may still be necessary because an inherited session lacks effective docker-group membership.

Create fresh results/phase_03/<unique-run-id>/ artifacts. At minimum preserve:

- resolved configuration and hash, input config hash;
- generated firmware config and test provisioning fixture/hash;
- source hashes (including harness, tests, selected backend, vector provenance), source pins and working-tree state;
- actual git SHA when present, otherwise null plus explicit source hashes;
- command argv, environment/tool versions, build flags, platform, start/end times and exit status;
- scenario and script hashes, actual root/sensor binary copies or durable references and hashes;
- console/build log, raw Cooja serial/radio capture, normalized events, summary;
- expected test-case identity for negative tests;
- pair comparison with source run IDs/hashes and figure-source metadata.

Record status/error even when validation/build/parsing fails, including before simulator launch where possible. Hash artifacts after all pair/evidence files are finalized; current Phase 2 writes pair metadata after its run hash table, so correct that ordering for new evidence without rewriting history.

A passed instrumentation run, a qualified secure run and a valid matched pair are separate assertions. Explicitly record pair failure even if both individual runs pass. Exclude invalid pairs from plots.

## 11. Event schema, parsing and metrics

Current parser expects PHASE2_COMPLETE and sets every RX auth_ok=false. Current metrics hardcode 11+10*count and N0 labels. Update together using explicit schema/profile metadata, preserving legacy parsing.

Suggested new events/fields:

| Event | Essential information |
|---|---|
| BOOT_REQUEST / CONTEXT_READY | Mote, schema/config/context ID, activation state; no key bytes |
| TX_SECURE | Sender inferred/checked, profile, epoch, counter, count, wire bytes, hold, reading range |
| RX_AUTH | Sender, profile, epoch, counter, count or joined packet identity, reading ID/time/value, duplicate flag |
| REJECT_SECURITY | Reason, safe bounded metadata; no unauthenticated plaintext |
| CRYPTO_ERROR / CONTEXT_LOCKED | Fatal reason and lifecycle state |
| INJECT / EXPECTED_CASE_RESULT | Test-case identity and expected/observed verdict, only in security scenarios |
| GEN / DROP / DONE | Existing meanings with complete accounting |

Keep compact logging to limit perturbation. A schema marker alone does not prove security: auth_ok must originate only from the verified firmware acceptance path, matched to compiled configuration and tested code. N0 RX can never become authenticated because a manifest mode string says B1.

Maintain one metric implementation:

- unique generated and authenticated-delivered (sender,reading_id);
- explicit drops, submitted readings and missing delivery;
- reading PDR with clearly stated numerator/denominator;
- application submissions and full datagram bytes including tags;
- separate plaintext-reading bytes, if useful;
- batch counts, queue hold and global generation-to-accepted-RX delay;
- duplicate/replay/auth/format rejection counts by reason;
- radio frame/byte/fragment observations separate from application counters.

In N0 summaries unique_authenticated_delivered is zero or explicitly not applicable; do not reuse diagnostic delivered count as authenticated delivery. For secure summaries verify every counted RX joins a valid generation and a submitted secure packet/context. Handle counter gaps from failed reservations. Normal pilots reject unexpected fatal/security-test events.

Zero authenticated delivery gives PDR=0 and undefined latency (null with explanation), not a fabricated zero-latency success. Distinguish network loss from incomplete logging. Negative-test injected packets are classified separately from normal traffic accounting; they do not silently inflate performance submissions/bytes or delivery.

Reject missing completion, missing/mismatched READY/DONE, unsupported schema, corrupted lengths, impossible timestamps, stale config, incomplete radio capture and unauthorized profile mixtures. Dedicated security scenarios may define a different expected terminal condition; that must be explicit, not a parser-wide relaxation.

Plot only validated matched B1/B4 summaries, with “engineering pilot” and seed count. No energy, battery-life or statistical-significance claim in this phase. Native Cooja is functional/network evidence, not calibrated hardware crypto timing.

## 12. Fragmentation, footprint and fairness gates

Actual AES wire sizes are 37/47/57/67, not the N0 sizes with a hypothetical reservation. Capture actual radio frames for each selected secure scenario.

Reuse the MAC-boundary FRAG1/FRAGN classification, verify the same unencrypted MAC layouts apply, and reject unknown layouts rather than interpreting them as no fragmentation. Application AEAD does not automatically enable MAC security.

If the 67-byte packet fragments:

1. Preserve the failing run and actual frames.
2. Document the measured threshold and configuration.
3. Reduce the frozen secure payload budget/effective cap if the intended pilot is nonfragmenting; rerun both arms.
4. Keep a separate explicit fragmentation experiment only if it is deliberately scoped/documented.
5. Never truncate tags or silently drop readings to fit.

Measure binary text/data/bss and bounded buffer/context memory from actual builds. Record root cost as sender count grows, scratch stack/static storage and nonreentrancy assumptions. Avoid large borrowed upstream test arrays in mote tests. Native footprints are not proof of embedded-target feasibility; any emulated-platform check must name the actual supported target and remain separately evidenced.

One paired seed is the required engineering pilot, not inferential research. Three paired seeds are desirable only after correctness is complete and time permits; do not postpone required safety tests for extra performance runs. Later main experiments retain the master's statistical and larger-topology requirements.

## 13. Ordered implementation packages

Execute sequentially at integration boundaries. Independent reading/review or portable test preparation may run in parallel; generated configs/builds/runs have one writer.

| Package | Work | Exit evidence |
|---|---|---|
| P3.0 — baseline inventory | Re-read plans/reports; check pins, hashes, running containers, upstream diff and current tests; create implementation journal | Recorded actual starting state and preserved prior evidence |
| P3.1 — freeze contracts | Document header/body/AAD, nonce, keys, boot/reset states, replay, event schema and failure semantics | Reviewable protocol decisions and boundary test list |
| P3.2 — backend and lifecycle proof | Add adapter; obtain exact official vectors; host/mote KAT; prove default-lock/reset mechanism before broad pilot work | Actual KAT, negative tag/output-isolation, activation/reset logs; unresolved requirements block qualification |
| P3.3 — shared packet path | Refactor codec compatibly; add packet protection and replay; integrate sensor/root and tag budgeting | N0 compatibility + shared C tests + real protected 1+2 build/run |
| P3.4 — runner and accounting | Add Phase 3 config/modes, harness, single lock, manifests, schema-aware parser/metrics/plots | Malformed-input tests, stale-config rejection, failure preservation and pair validation |
| P3.5 — security and batch integration | Execute negative cases, interleaved senders, reset/wrap cases and 1+2 boundaries | Actual Cooja rejection/no-state-poisoning and authenticated batching evidence |
| P3.6 — protected pilot and regressions | Run clean B1/B4 1+8 matched pair, radio checks, N0/Phase 1 regression, source/plan audit | Validated summaries/figure-source manifest; regression logs |
| P3.7 — review and handoff | Review claims, document downloads/problems/decisions, update phase status, list pending human gates | Detailed reports and stop before Phase 4 |

Do not mark a package complete from compiled code alone when its exit requires execution. Report blockers with exact command, error, attempted fix and next action. Maintain short progress updates and journal commands as work proceeds.

## 14. Required test matrix

### A. Portable production C and backend tests

- Existing codec/aggregation tests continue to pass unchanged in meaning.
- N0 exact bytes/profile/epoch rejection; secure header/body lengths and count 1/2/4.
- Official exact-parameter AES encryption/decryption vectors with provenance.
- Empty AEAD plaintext, supported AAD boundary lengths, zero-length AAD, application AAD=11, max supported body.
- Each tag-byte corruption; modified ciphertext and each header field; wrong key/nonce/direction.
- Truncated/extra packet bytes, short/missing tag, impossible count, insufficient output capacity, invalid arguments/unsupported aliasing.
- Rejected open leaves caller output untouched, scratch wiped and replay/dedup unchanged.
- Key switching between two senders catches stale shared key state.
- Unique nonce byte encoding across sender/epoch/counter/direction; exact size and no host-endian dependence.
- Counter gaps, failed seal reservation, zero/max boundary, exhaustion, invalid epoch and epoch rollover.
- Packet replay: duplicate, reorder within 32, boundary 31/32, large forward jump, forged-high-counter followed by valid lower packet.
- Separate reading dedup: same reading in another authenticated packet does not count twice.
- Boot locked, consume-one-grant, reinitialization locks, missing/wrong/reused grant, root replay-state reset refuses activation.
- Warning-clean project C plus ASan/UBSan with actual production adapter and pinned backend. Scope warnings so unchanged upstream/platform sources are not “fixed” unnecessarily.

### B. Python configuration/parser/metric/lifecycle tests

- Correct N0 vs AES length/overhead/cap calculations; invalid config before writes.
- Legacy log compatibility; secure logs cannot be parsed as N0 or vice versa.
- False/missing auth markers, unknown profile, mismatched config/context, corrupted reading joins.
- Duplicate/replay accounting, counter gaps, zero delivery, missing GEN/TX/DONE/termination.
- Expected negative-test rejections vs unexpected normal-run failure.
- Exact matched-generation comparison and invalid-pair plot refusal.
- Same lock excludes concurrent Phase 2/3 writers; failed startup retains manifest.
- Timeout/interruption cleanup targets only the run's container.
- Artifact hashes include final pair metadata; missing source/config/binary provenance rejects qualification.

### C. Actual Cooja security scenarios

Use production crypto/receive code with bounded test hooks or a dedicated firmware test application. Hooks are disabled in normal pilots and identified in build/config hashes.

- Official-vector adapter self-test on a mote, plus actual sensor-to-root AES roundtrip.
- Wrong key; altered header/AAD, ciphertext and tag; unsupported profile; secure-run N0 downgrade attempt.
- Replay captured packet; reorder valid packets; forge high counter then deliver valid packet.
- Interleave valid traffic from two senders with different keys; one sender's failure cannot damage the other.
- Invalid body with a legitimately computed test tag to exercise post-auth validation.
- Sender reset, root reset, missing grant and context reinitialization with enforcement before protected send/accept.
- Near-exhaustion counter/epoch fixture and fail-closed behavior.
- Packet loss followed by later valid counter; no permanent desynchronization.

Every rejection test needs a valid control before/after where appropriate. “No RX appeared” by itself is insufficient because a disconnected network also produces no RX. Demonstrate attempted delivery/injection, the expected receiver verdict and unchanged state. Reset cases additionally require no post-reset protected transmission/acceptance before any harness abort.

### D. Actual batching and matched pilot

| Order | Scenario | Required observation |
|---|---|---|
| 1 | Root+2, B1 and B4 at 1Hz | Correct authenticated readings, bounded hold/lengths, matching GEN traces |
| 2 | Root+2, B4 at 500ms | Count-4 ciphertext packet exercised if measured budget permits |
| 3 | Root+2, B4 at 4000ms | Partial deadline flush, no indefinite wait |
| 4 | Root+2, B4 budget 47 | Effective cap 2 with actual 16-byte tag |
| 5 | Root+2, critical/queue-boundary fixture | Critical flush and overflow/drop accounting; identify as integration test |
| 6 | Root+8, clean matched B1/B4 | Secure engineering pilot with validated radio capture and figure source |
| 7 | Current N0 pair and official Phase 1 smoke | Network/codec regression; no forced equality of random network outcomes |

Expect 192 generated readings in the primary root+8 scenario from configuration; do not prefill delivered counts, latency or packet savings. If otherwise-valid network runs lose readings, report the actual loss; do not tune seeds until perfect delivery is obtained. Separate scientific outcome from gate/instrumentation validity.

## 15. Downloads, installation and commands

This planning task installed/downloaded no packages and ran no Phase 3 tests. Reuse existing local pinned sources and image first.

Expected implementation downloads: official CCM vector archive and any missing explicitly verified submodule/tool component. The backend itself is already in the pinned checkout. Optional independent Python crypto oracle is unnecessary if adequate official vectors cover the chosen profile; if needed, pin it in an isolated test environment and retain versions/hashes/license. Do not add host Java/GCC, a second Docker image, a broad scientific stack or an unneeded crypto framework by default.

For every actual download/install record: item/version/source URL/hash/license, reason, command, host-vs-container-vs-project location, disk impact if measured, error/retry/resolution, and which requirement it enabled. Explain required installs to the user while proceeding within authorization.

Existing commands available now (not executed by this planning task):

    sg docker -c 'docker info'
    python3 host/run_experiment.py --clients 2 --mode both
    python3 host/run_experiment.py --clients 8 --mode both
    bash scripts/smoke.sh

The N0 commands write results and build artifacts; run them only during authorized implementation. Read scripts/smoke.sh and docs/phase2-usage.md for its actual environment prerequisites.

Existing portable test invocation from project root:

    sg docker -c 'docker run --rm --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/test_phase2.sh'

The future scripts/test_phase3.sh should follow that environment and record its exact compiler/linker/vector/test commands. The proposed --phase 3 CLI in Section 10 is a target interface, not an already working command.

Workspace permissions may require an escalation for writes/downloads/tests. User authorization to implement does not change sandbox permissions. Use the tool's specific approval mechanism when required, explain the actual restriction and avoid blanket privilege requests.

## 16. Detailed reporting and completion criteria

Create during implementation:

- phase_jouney/phase_03_environment_and_implementation.md — chronological commands, decisions, attempts, outputs and evidence paths.
- phase_jouney/phase_03_detailed_report.md — what changed, why, how, impact on previous/next phases, tests and limitations.
- phase_jouney/phase_03_downloads_problems_and_resolutions.md — downloads/reuse/install scope, failures, diagnosis, fixes and remaining problems.
- results/phase_03/phase3-evidence.json — actual run/test references and selected pilot pair.
- Updated phase_jouney/README.md status only after evidence/report review.

The current temporary plan stays a planning record; later mark execution status honestly and link final reports. Never turn proposed commands or expected numbers into execution evidence.

Phase completion checklist for the implementing model:

- [ ] Original plan files unchanged and hashes checked.
- [ ] Pinned backend selected only after exact 16-byte-tag KAT and actual mote build.
- [ ] No unauthenticated plaintext release/fallback.
- [ ] Nonce allocation, per-context keys, boot/reset safety and replay behavior evidenced; unsupported reset coverage clearly pending.
- [ ] Shared N0 codec/aggregation and Phase 1 regression preserved.
- [ ] Root+2 secure negative cases and protected aggregation boundaries passed with valid controls.
- [ ] Root+8 B1/B4 pair has matched traffic, honest delivery accounting and actual fragmentation evidence.
- [ ] Parser/metrics/plots separate N0 from authenticated delivery and reject incomplete/invalid evidence.
- [ ] Commands, config/source/scenario/backend/vector/binary/artifact hashes and failures retained.
- [ ] Source/license/resource limitations and test-key policy documented.
- [ ] Formal G0/two-person review and independent reproduction remain pending unless real people performed them.
- [ ] G2/protected G3 status based on actual Cooja evidence; G4/G5/G6 not claimed.
- [ ] Detailed phase reports completed; stop and wait for user before Phase 4.

If a required criterion fails, report Phase 3 incomplete/blocked at that criterion, preserve useful partial evidence and the verified N0 demo, and do not claim successful secure completion.

## 17. Review checkpoints and future connections

Ask a reviewer to focus on these concrete risks rather than stylistic refactoring:

1. Codec refactor accidentally permits profile 0 fallback in secure builds.
2. Received tag checked after plaintext has escaped or parser mutated state.
3. Counter consumed too late; reboot/reset restarts a compiled key at counter 1.
4. Boot ledger lives in resettable memory or grants twice on repeated logs.
5. Forged counter/epoch updates replay/key state before authentication.
6. Shared AES key schedule leaks between sender contexts.
7. Reserved tag overhead counted twice, or 51-byte buffer reused for 67-byte output.
8. Global timestamps/paired traffic weakened to hide crypto scheduling differences.
9. Legacy N0 logs relabeled authenticated by parser or plot title.
10. Phase-specific locks permit simultaneous writes to common build directories.
11. Negative-test loss counted as passing rejection without a live control.
12. Evidence hashes captured before final artifacts, or failed runs overwritten.

Phase 4 should be able to add a vetted standardized Ascon adapter with its own exact nonce length and independent key domain through profile metadata, preserving packet/body/aggregation and metric contracts. Do not force a 13-byte nonce on other ciphers or accept the future profile until its implementation/tests exist.

Later energy/policy work can instrument the shared seal/open/send boundaries and use authenticated unique-reading counts. This phase supplies no joule, lifetime or adaptive-policy result. Larger topology and independent reproduction remain later requirements, not deleted scope.

## 18. Planning audit and source snapshot

Planning performed: reread original plans and phase reports; inspected current codec/aggregator/sensor/root/runner/parser/metrics/plots, pinned CCM/AES API and upstream tests, Cooja CFS and memory API declarations; located the official NIST CCM-vector source. No Phase 3 firmware, config, harness, test, dependency or result was created.

The selected file hashes below identify the review snapshot. Recheck before implementation; if code changed, reconcile the plan with actual source. These are not a claim that the entire repository was frozen.

    2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385  PLANS/MASTER_IMPLEMENTATION_PLAN.md
    69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a  PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md
    1083c1178b0afc0559eaf6d46f119e097eb5aba6d0214e7b848905025f6c40ec  firmware/common/protocol.c
    bae672e0182bb7aea54f1d1374e443f443534e356f62827c75779739413d5c1d  firmware/aggregate/aggregate.c
    997d386664dfa918d0e9a55650ab8a60d9481296c522359aaaf939b4118f674a  firmware/sensor/sensor.c
    1c23ef56abd7ec5f3b7a0de4d564b5ea80942611d2e16664a5b7a0d4e3faf4eb  firmware/root/root.c
    7b6f79f9eb7ac7ed178c966e1090ad607d63a19b70c34ed1c04ee9760dfb8cc6  host/run_experiment.py
    71956a34044dea1bf49bb3271da8dde165ddc0a169c71741ebcc0c1b67aa52c5  host/parse_logs.py
    92cf334635dea8026df27d701c5247903c164c5f8f9263a75d2daa75a4cfaeaa  host/metrics.py
    0523167e3319324e310efa9ae1189739c09664e6661466369f9d48cce5a6c227  host/plots.py
    b9cd00a79295ca8d7c9e0bad9d30a16897f6d4e0eeaa931a68d7d021657fbd8d  external/contiki-ng/os/lib/ccm-star.c
    c147f04f585b492e04e8e11a7e98f0d3b1c96af25bb9df64740eac931f27e935  external/contiki-ng/os/lib/aes-128.c

Handoff instruction: implement only after the user authorizes Phase 3 execution. Start with P3.0, complete the required packages/evidence, write detailed phase reports, and stop before Phase 4.
