# Implementation roadmap and decision review

Date: 13 November 2026
Status: proposed implementation decisions; no firmware or simulation validated yet.
Authority: MASTER_IMPLEMENTATION_PLAN.md v1.1. This companion explains execution and reuse; the master owns scope, deadlines, research requirements, baseline definitions and release gates. In a conflict, follow the master and record the unresolved decision.

## 1. Current state and review conclusion

The workspace contains the master plan. No firmware, pinned upstream checkout, run evidence or Git repository was found during this review. Previously linked upstream documentation establishes available capabilities, not compatibility with a locally validated build.

Retain the master's full implementation scope and staged delivery. Reuse the established network/simulator/cryptographic infrastructure and implement the project-specific protocol, bounded aggregation, decision policy and measurement pipeline. Avoid duplicated baseline applications. Future quality requires shared code, explicit failure semantics, reproducible configuration and evidence from the beginning.

## 2. Reviewed decisions

| Decision | Review | Implementation condition |
|---|---|---|
| Contiki-NG + Cooja + official rpl-udp example | Retain | Pin source/submodules; reproduce unchanged 1-root/8-client scenario before application modifications |
| Existing RPL, UDP, 6LoWPAN and MAC | Reuse | Configure existing stack; keep MAC/radio settings identical across compared arms |
| Official container | Retain | Validate on this machine and record image digest; source checkout remains separately pinned |
| Native Cooja first; emulated target later | Retain | Native functional results do not establish hardware crypto timing; validate memory and timing on supported emulation |
| Built-in timers | Reuse | Aggregator owns deadline semantics; callbacks/process events only drive it |
| Contiki CCM* implementation | Conditional candidate | Inspect pinned API, tag and nonce support, shared key state, bounds; require exact-variant KAT and invalid-tag tests before selection |
| Official Ascon-AEAD128 implementation | Retain as planned integration | Pin standardized variant and implementation; compile/test for selected target; retain licence and vectors |
| Common crypto adapter | Retain | Explicit success/failure; authenticated plaintext released only on success |
| Energest/simple-energest | Reuse | Confirm available counters and tick frequency; custom power/depletion model remains necessary |
| Shared code for all baseline modes | Adopt | Mode configuration selects policy/profile/batch cap; common generator, serializer, receive validation and metrics |
| Central experiment configuration | Adopt | Validate once; materialize build/runtime settings; record resolved values and artifact hashes |
| Headless simulation | Reuse | Validate version-specific invocation and script timeout; preserve raw output and terminal status |
| Python scientific libraries | Retain | Pin environment; custom metric definitions remain in host/metrics.py |
| Online profile renegotiation | Keep master's optional extension | Initial authenticated per-packet profile selection needs no new handshake |

Dependency acceptance requires provenance/licence, target compilation, necessary behaviour, resource fit and reproducible tests. Availability on the web alone is insufficient. Keep upstream code isolated under external/; document unavoidable patches.

## 3. Module ownership and DRY boundaries

Use the repository layout in master Section 3.

| Module | Owns | Interface / boundary |
|---|---|---|
| firmware/common | Reading types, bounded wire encoding, event vocabulary | Explicit field sizes/network byte order; never transmit raw C structures |
| firmware/sensor | Contiki process, generation schedule, send orchestration | Calls aggregate, policy and crypto modules; uses simple-udp |
| firmware/root | Receive orchestration and per-sender security context | Validates, authenticates, checks replay, decodes, accounts for unique readings |
| firmware/aggregate | Fixed memory queue, count/byte/deadline bounds and drops | offer, should_flush, build_batch, commit_on_send; deterministic core with supplied time |
| firmware/crypto | Vetted backend adapters, nonce and authentication boundaries | seal/open return explicit status; suite-specific lengths remain in backend metadata |
| firmware/policy | Fixed, threshold and joint action selection | Input: measured features; output: permitted profile and batch action |
| firmware/energy | Counter deltas, power model and residual budget | Explicit units, depletion events and selected platform assumptions |
| host/run_experiment.py | Config resolution, build/run lifecycle and manifest | Canonical runner; scripts/run_experiment.py may be a thin forwarding entry point |
| host/parse_logs.py | Event validation and normalization | Simulator capture adds common simulation time and run identity |
| host/metrics.py | Final metric definitions | Sole implementation of published metrics |
| host/plots.py | Presentation of validated summaries | No independent metric recalculation |

Build the same portable C aggregation/protocol/policy sources for host tests and firmware. Keep OS timer/UDP calls at application boundaries. Add abstractions only where they support actual interchangeable backends or testability.

## 4. Correctness decisions to resolve before integration

1. **Timing:** use simulator-global timestamps for joining generation and receive events. Local boot-relative clocks cannot be subtracted across nodes without validated alignment. Local timers still control batching. Specify wraparound and timer resolution handling.
2. **Traffic fairness:** generation schedule must be independent of batching, cipher choice and network RNG consumption. Record or deterministically reproduce the same reading trace across paired arms. A shared simulator seed alone does not prove matched traffic.
3. **Batch feasibility:** check period versus maximum hold time. With a 10-second reading period and 3-second deadline, normal periodic batches will contain one reading. Select and freeze meaningful pilot scenarios without changing traffic between arms.
4. **Deadline semantics:** measure hold time from the oldest queued reading. A new arrival must not reset its deadline. Count/byte limits may flush earlier; test exact-deadline ordering.
5. **Packet budget:** calculate full encoded header, readings and tag size; verify actual radio fragmentation. Payload assumptions require evidence for the selected MAC/compression settings.
6. **Send semantics:** determine what simple-udp submission actually reports. Local submission is not root delivery. Define queue commit/drop behaviour explicitly; do not invent acknowledgements or silent retries.
7. **Authentication:** the reviewed CCM* API calculates a MIC rather than providing complete receive acceptance. Verify the pinned implementation; compare tags in constant time and keep tentative plaintext private until verification succeeds. Clear rejected plaintext buffers.
8. **Security state:** bind profile/header as AAD, enforce nonce uniqueness and fail closed on reset/wrap as prescribed by the master. Commit replay-window updates only after authentication; forged counters must not advance accepted state. Account for shared backend key state.
9. **Unprotected diagnostic modes:** retain explicit N0 batch-cap variants as permitted by master Section 7. Never mark their readings authenticated or include them in security-equivalent comparisons.
10. **Energy:** validate counter deltas/wrap and frequency, avoid double-counting component current, and preserve model assumptions. Depletion must disable forwarding/radio as specified, not merely stop sensor generation.
11. **End of run:** freeze warm-up, generation stop, drain interval and receive cutoff. Account for queued, dropped and undelivered readings; a timed-out/incomplete run must not silently generate a valid summary.
12. **Adaptive feedback:** define how sender-side delivery estimates become available. Root-only PDR is not automatically a local policy feature. Any feedback traffic has measured cost; unavailable estimates use the master's safe static fallback.

## 5. Execution packages and acceptance evidence

Owner numbers follow master Section 2. Calendar/cutoffs remain master Section 9.

| Package | Owner | Work and outputs | Acceptance / dependency |
|---|---|---|---|
| W0: environment and official network | 1 | Version/provenance records, validated setup, saved 9-node example, smoke entry point | G0: unchanged tutorial runs, logs and commands retained, required human verification |
| W1: contracts and host harness | 2 + 3 | Protocol/threat docs, event schema, portable C test build, parser fixtures | Bounded encoding tests, malformed lengths, fixture counts; no simulation claims from fixtures |
| W2: reading transport | 1 + 2 | Deterministic generator, thin client/root applications, stable reading IDs | G1: correct unique readings at 1+2 then 1+8; verify same schedule across modes |
| W3: aggregation | 2 | Shared queue, timer integration, cap 1/2/4 and byte/deadline enforcement | Host boundary tests and actual N0 comparison if security pending; protected G3 requires G2 |
| W4: AES security | 2 + 1 | Vetted adapter, test keys, counters/replay state and authenticated packet path | G2: published vectors, wrong-key/AAD/tag rejection and on-mote roundtrip; then protected G3 |
| W5: repeatable pilot/release | 3 + 1 | Runner, manifests, validated summaries/plots, demo evidence | Mid-term scope and cutoffs in master; B1/B4 only if security proven, otherwise labelled N0 |
| W6: second cipher and static controls | 2 | Ascon adapter and permitted profile dispatch | Same security regressions; B2/B5 actual runs, resource usage and provenance |
| W7: energy and lifetime | 3 + 1 | Counter validation, power config, depletion behaviour and lifetime accounting | G4: idle/load sanity, monotonic budget accounting, forwarding-node depletion behaviour |
| W8: adaptive research method | 2 + 3 | Calibration tables, B3/B6/P1, feasibility filtering, hysteresis/dwell/transition cost | G5: policy edge tests, valid local inputs, no auth downgrade, comparison to strong static controls |
| W9: full experiments and release | All | Frozen protocol, full controls/ablations, paired seeds, uncertainty, clean rerun, manuscript evidence | G6 and master Section 12; every claim traceable to run/log/config/source |

W1 and analysis fixtures can progress alongside W0. W3 host logic and W4 backend tests can progress concurrently after contracts agree. Cooja integration follows the validated network. Early headless automation supports W5; full G6 remains the research-grade gate. Mid-term fallback does not remove subsequent security/energy/policy deliverables.

## 6. Verification and configuration policy

- Host C checks: compiler warnings, sanitizers where supported, real serialization/aggregation boundary cases, nonce/replay failures and policy feasibility cases.
- Crypto checks: published vectors for exact variants, altered ciphertext/AAD/tag, invalid lengths, wrong key, reset/wrap rejection; both host and on-mote integration evidence.
- Parser checks: known-count fixtures including duplicate IDs, incomplete runs, unprotected versus authenticated events, zero delivered readings and invalid timestamps.
- Integration checks: route establishment, unique readings, matched generation traces, deadline/MTU behaviour, protected receive failures and node depletion.
- Experiment checks: run status, source/dependency/config/scenario/binary hashes, seed, platform, build flags, units, warm-up/drain rules and evidence paths.
- A validated config produces the firmware settings and run manifest. Firmware logs the active mode/settings identifier to detect stale builds. A mode requiring an unavailable crypto backend fails explicitly.
- Keep calibration and final seeds separate. Choose B6's fixed best cipher from calibration evidence, not the final outcome being evaluated.
- Add CI incrementally using the proven local commands. Heavy Cooja matrices remain manual/scheduled as the master specifies.

## 7. Open decisions and next concrete step

Before implementation selection, inspect tool availability and pin Contiki/Cooja/container versions. Inspect the exact CCM* backend and test support, determine target footprint, define wire sizes and replay-window behaviour, validate simulation timestamp capture, and choose pilot traffic/deadline settings. These are engineering selections within the master, not changes to its research scope.

The first implementation issue is W0: validate the unchanged official network and retain reproducible evidence. No gate is currently passed. No energy, runtime, delivery improvement or compatibility result is claimed by this review.

## 8. Official references reviewed in this conversation

- RPL example/tutorial: https://docs.contiki-ng.org/en/master/doc/tutorials/Running-a-RPL-network-in-Cooja.html
- UDP API: https://github.com/contiki-ng/contiki-ng/blob/develop/doc/programming/UDP-communication.md
- Timers: https://docs.contiki-ng.org/en/master/doc/programming/Timers.html
- Cooja and headless operation: https://docs.contiki-ng.org/en/master/doc/tutorials/Running-Contiki-NG-in-Cooja.html
- Docker toolchain: https://docs.contiki-ng.org/en/master/doc/getting-started/Docker.html
- CCM* source snapshot: https://docs.contiki-ng.org/en/master/_api/ccm-star_8c_source.html
- Standardized Ascon implementation: https://github.com/ascon/ascon-c
- Energest: https://docs.contiki-ng.org/en/master/doc/tutorials/Instrumenting-Contiki-NG-applications-with-energy-usage-estimation.html

Moving documentation branches are discovery references. Implementation must record the exact pinned source revision and validate its behaviour locally.
