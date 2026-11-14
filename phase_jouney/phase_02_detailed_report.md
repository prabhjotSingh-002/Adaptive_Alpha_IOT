# Phase 2 detailed implementation and verification report

**Status:** automated Phase 2 engineering work complete; stopped before Phase 3. Original master and companion plans under PLANS/ remained byte-for-byte unchanged. Formal human checks are not inferred from automated tests.

## 1. Original plan alignment and pre-implementation work

Reread both Markdown files in PLANS/ after the user requested it. Saved [temporary implementation plan](tmp/phase_02_implementation_plan.md) before source edits, with original plan hashes. Scope follows master Sections 3/4/6/7/8 and companion W1–W3: deterministic custom readings, bounded packet serialization, fixed-memory aggregation, real UDP integration, structured events and accounting evidence. Phase 3 owns AES-CCM; Phase 2 is explicitly diagnostic N0.

Phase 1 already established the unchanged official network and pinned tools. Its two-student human sign-off remains pending. The user explicitly authorized proceeding with Phase 2 engineering; no reviewer identity or formal gate approval was invented.

## 2. What was implemented, why, how and impact

| Component / location | What and how | Why / downstream impact |
|---|---|---|
| firmware/common/protocol.h, protocol.c | Explicit big-endian v1 header and bounded 10-byte readings; exact-length decode into temporary state; reject invalid version/profile/epoch/count/counter/order | Shared contract avoids structure padding, unsafe parsing and duplicate codecs; future AEAD can use defined metadata |
| firmware/aggregate/ | Four-entry ring; configured count cap, oldest-reading deadline and byte/reserved-overhead bound; offer/build/commit operations | Constant memory and shared host/mote logic; building a batch does not consume readings, enabling explicit submission handling |
| firmware/common/events.h | RSLAB event prefix, numeric fields, source time helper | One vocabulary for generation/submission/drop/root events |
| firmware/sensor/sensor.c | Thin Contiki process, finite deterministic 24-reading trace, 125ms etimer service, registered simple-udp socket and route checks | Existing network is reused; reading IDs/values/schedules are independent of mode and network RNG |
| firmware/root/root.c | RPL root, bounded packet decode, configured sender bounds/address sanity and per-source 32-ID duplicate window | Count unique source/reading pairs, including in-window reordering; diagnostic checks do not claim authentication |
| firmware Makefiles/config | Common build definitions plus generated config header | Same application/module code in both modes; clean builds and READY checks prevent stale configuration |
| configs/phase2.json | Central pilot parameters, mode caps, shared warmup/rate/deadline/drain | Reproducible paired inputs; CLI overrides recorded in manifests |
| host/run_experiment.py | Source-pin checks, serialized config/build access, generated scenario, exact Docker command and status/artifact manifests | Reproducible actual Cooja runs; preserve failed evidence rather than accepting generated code as proof |
| host/parse_logs.py | Strict field/node/schema checks, simulator-global event times and explicit unprotected RX marker | Prevent local-clock subtraction errors; reject incomplete/malformed logs |
| host/metrics.py | Unique reading delivery, complete sender disposition, payload consistency, delay and packet/byte accounting; MAC-boundary fragmentation analysis | One implementation of metrics and no manual chart arithmetic |
| host/plots.py | Chart validated primary-pair summaries using existing matplotlib | Reviewable unprotected pilot chart; no fabricated energy/security chart |
| tests/unit/ and scripts/test_phase2.sh | Shared production C tests under warnings-as-errors/ASan/UBSan and Python known-answer/failure fixtures | Catch bounds, deadline, send-commit and parser errors before/alongside integration |
| docs/ and AGENTS.md | Protocol, architecture, threat scope, commands and phase collaboration rules | Preserve decisions and prevent accidental security claims or concurrent config writers |

The codec header is 11 bytes; each reading is 10 bytes. N0 application datagrams are 21–51 bytes depending on count. The configured 67-byte budget includes a 16-byte reservation, leaving 51 actual N0 bytes maximum. Reserved space is not an actual tag and does not establish future encrypted fragmentation behaviour.

## 3. Downloads / installs / reuse in this phase

**No new host packages, Python packages, cryptographic library or container image were installed/downloaded for Phase 2.** Reused the local digest-pinned Contiki image, Java/GCC/Make toolchain, built Cooja, Contiki networking and standard-library Python. Existing container matplotlib generated the chart. No host gcc/java/pytest/pandas installation was necessary for these tasks.

Actual source and image revisions are in results/setup/source-pins.json. New project C/Python/docs files are locally authored implementation, not third-party downloads. Make generated native mote binaries inside project firmware build directories, excluded from Git status. Source/binary/config/scenario and artifact hashes are retained where applicable; later metadata enhancements added explicit config hashes. Older runs already preserve their resolved config and generated-header source hash.

## 4. Behaviour and engineering decisions

- One sender implementation supports cap 1 or 4; there are no forked baseline applications.
- Sensor generation logs happen before network work. Paired global generation events must match exactly, including IDs, local times, values and global timestamps.
- Deadline applies to oldest queued reading; offering a new one cannot extend it. At exact expiry an existing batch flushes before the new reading is offered.
- At 1Hz with a 3s deadline, configured cap 4 emits count-3 batches. This is correct deadline precedence; a separate faster-traffic run verifies full count 4.
- A low-traffic source flushes partial batches on time. Byte limits reduce effective cap even if configured count cap is larger.
- No-route conditions retain an unexpired queue; once expired, queued readings are explicitly dropped and logged. There is no silent loss or hidden application acknowledgement/retry.
- Inspected pinned simple_udp_sendto: it always returns zero, so a successful local submission is not proof of radio/root delivery. Root events determine delivered readings.
- Root duplicate window is bounded and diagnostic; profile zero traffic can be forged. Future authenticated replay/nonce/key management is not implemented here.
- Global GEN/RX event times determine end-to-end latency. Source boot-relative timestamps are payload consistency fields only.
- Radio transmission triggers capture actual frame bytes. The parser validates supported classic unencrypted MAC layouts and checks FRAG1/FRAGN at the MAC payload boundary. Unsupported layouts require review.
- The protocol and aggregation modules allocate no heap memory in the mote hot path.

## 5. Problems, diagnosis and resolutions

| Problem | What evidence showed | Resolution / impact |
|---|---|---|
| Initial custom process build failed | Unused ev/data parameters became errors under project warning settings | Explicitly mark unused parameters in custom Contiki process functions |
| Next build failed in upstream beep.c | Extra global -Wextra affected existing upstream driver parameters | Retain upstream firmware warning policy; compile portable project C separately with strict extra warnings and sanitizers; no upstream edits |
| Cooja script failed to start | JavaScript Missing close quote; Python had converted embedded newline escapes | Use raw Python string for generated ScriptRunner; retain failed scenario/log |
| First individual runs passed but pair check failed | Exact GEN comparison showed 1ms timestamp shifts after deadline flushing, while IDs/values/local times matched | Move GEN logging before network work while preserving flush-before-offer semantics; rerun pair with exact check unchanged |
| Server restarted before 1+8 work | Recovery inspected manifests, journal, files and Docker containers | Resume remaining runs without blindly duplicating completed work |
| Compile-time config could become stale or collide | All modes share generated header/build directories | Clean builds, single runner lock and runtime READY configuration checks |
| Byte-bound run needs effective-cap validation | Nominal cap 4 can fit only two readings in a smaller budget | Log queue's effective cap; validate against resolved count/byte limits |

Failed runs remain under results/phase_02/ with status/error and console output. Two earlier individually valid runs with mismatched global generation must not be selected as a valid paired comparison. The final evidence identifies the corrected primary pair explicitly.

## 6. Executed tests and outcomes

### Production C unit checks

Compiled shared protocol.c and aggregate.c with -std=c11 -Wall -Wextra -Werror -pedantic and AddressSanitizer/UndefinedBehaviorSanitizer. Successful checks cover caps 1/2/4; exact wire bytes and lengths; truncation/trailing data; bad version/profile/epoch/count; invalid/duplicate reading IDs; insufficient buffers; queue overflow/wrong sender; exact deadline and time wrap; critical flush; empty queue; ring rotation; build without commit; partial commit and retained deadline; zero packet counter; failed decode output isolation; reordered/duplicate/too-old reading windows. Actual test log: results/phase_02/unit/tests.log.

### Python fixture checks

Ten tests passed: known-count delivery/global latency, duplicate accounting, missing generation, missing DONE, malformed/incomplete trace, stale config, corrupted payload, missing sender disposition, deadline breach and fragmentation-dispatch boundary recognition. Fixtures are synthetic validation inputs, not simulation results.

### Actual Cooja runs

| Scenario | Clients | Generated / delivered | Submissions | Batch counts | Maximum hold | Fragment frames |
|---|---:|---:|---:|---|---:|---:|
| Corrected single, 1Hz | 2 | 48 / 48 | 48 | 1 | 0ms | 0 |
| Corrected batch, 1Hz | 2 | 48 / 48 | 16 | 3 | 3000ms | 0 |
| Primary single, 1Hz | 8 | 192 / 192 | 192 | 1 | 0ms | 0 |
| Primary batch, 1Hz | 8 | 192 / 192 | 64 | 3 | 3000ms | 0 |
| Full-batch traffic, 2Hz | 2 | 48 / 48 | 12 | 4 | 1500ms | 0 |
| Low traffic, 0.25Hz | 2 | 48 / 48 | 48 | 1 | 3000ms | 0 |
| Byte budget 47 incl. reservation | 2 | 48 / 48 | 24 | 2 | 1000ms | 0 |

Primary pair seed: 123456. Both arms have the exact same 192 generation events. One run per arm is an engineering pilot, not an inferential result. No explicit drops or missing readings in the selected scenarios.

Primary single: 4,032 application packet bytes and p95 delay 103.554ms. Primary batching: 2,624 application packet bytes and p95 delay 3,074.6856ms. Batching lowered application submissions/bytes in this pilot and increased delay, as expected from queue hold. These are application-level counters, not total on-air bytes or energy savings. No security-equivalence claim is made.

Actual radio captures classified all observed data frames with zero fragmentation dispatches. This observation is limited to these N0 configurations; secure profiles, different MAC settings, routes or larger payloads require rechecking.

The unchanged Phase 1 smoke regression also passed: results/phase_01/smoke-20261113T094208160354Z/manifest.json. Original plan hashes and empty upstream Contiki/Cooja tracked diffs were verified after work.

## 7. Evidence, commands and reproducibility

- [Execution journal](phase_02_environment_and_implementation.md)
- [Pre-implementation temporary plan](tmp/phase_02_implementation_plan.md)
- [Evidence index](../results/phase_02/phase2-evidence.json)
- [All run statuses / CSV](../results/phase_02/run-index.csv)
- [Primary single manifest](../results/phase_02/20261113T093713547602Z-N0-single-8/manifest.json)
- [Primary batch manifest](../results/phase_02/20261113T093733639048Z-N0-batch-8/manifest.json)
- [Exact paired-trace comparison](../results/phase_02/20261113T093733639048Z-N0-batch-8/paired-comparison.json)
- [Unit verification log](../results/phase_02/unit/tests.log)
- [Pilot chart](../results/phase_02/pilot-comparison.png)
- [Usage and test commands](../docs/phase2-usage.md)

Default command from project root:

```bash
python3 host/run_experiment.py --clients 8 --mode both
```

Each run saves manifest/scenario/raw serial and radio events, normalized events and validated summary. The repository still has no initial project commit; git_sha is null and source hashes identify actual inputs. This limitation is explicit and must be resolved before a frozen release/main experiment matrix. The run lock protects shared generated settings. Externally interrupted Docker clients may leave a container; inspect running containers before resuming (as done during recovery).

## 8. Gate status, limitations and handoff

G1 automated custom reading transport is established at 1+2 and 1+8. N0 count/deadline/byte-bound batching and radio fragmentation checks pass. G2 is not implemented. Full G3 requires successful authenticated decryption and remains pending for Phase 3. G0 manual two-student review remains pending. No human review/merge, hardware energy calibration, authenticated reading result, nonce/replay guarantee or publication-scale statistics is claimed.

Phase 3 can reuse the tested modules, exact packet field definitions, central config and evidence pipeline to add vetted AES-CCM plus nonce/replay failure handling and protected B1/B4. The diagnostic codec must not be treated as a security fallback. The original plan's remaining Ascon, energy, policy and experiment work is preserved.

Stopped after Phase 2 documentation/verification. Phase 3 has not started and needs a new user instruction.
