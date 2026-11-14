# Phase 1 Software Implementation Playbook
## Deadline-Constrained Energy-Aware Secure Data Delivery in RPL-Based IoT Networks

**Version:** 1.1 (mid-term sprint rebaseline) | **Date:** 12 November 2026 | **Team:** 3 students | **Scope:** 100% software; no physical hardware purchases or testing.

> This is an engineering and experimental plan, not a claim that any benchmark has been run or that any energy improvement is guaranteed. Reconfirm any tool-specific commands after pinning your Contiki-NG revision. All values identified as *initial proposals* must be fixed in a preregistered experiment protocol before final runs.

## 0. What success looks like — November 17 is the dividing line

**Mandatory mid-term evaluation: Tuesday, 17 November 2026.** The deadline for all development, actual simulation runs, evidence collection and slides is **Monday, 16 November 2026, end of day (IST)**. The mid-term is a demo/review day, **not** a development day. These dates supersede *all* dates in the uploaded research plan and the prior version of this playbook.

**First half: 12–16 November 2026 — show a working prototype and honest preliminary results.** Minimum defensible outcome (MVP-M): (a) a reproducible Cooja RPL network with a root and clients; (b) real, uniquely identified sensor readings and parseable receive logs; (c) a fixed batch-size/deadline implementation contrasted with one-reading-per-packet mode, with matched generated readings; (d) at least one executed small simulation comparison with packet/delivery/latency charts; (e) an evidence folder, recorded commands and a short live demo. **One fully tested AEAD is the preferred secure milestone, not a reason to discard a functioning network/results demonstration.** If authenticated encryption is not finished by the integration cutoff, make the limitation explicit: results are *unprotected transport/aggregation pilot data*, NOT results for the proposed secure system. Never mark an unencrypted mode as AES-CCM/Ascon.

**Stretch by 16 November only if the MVP is stable:** integrate vetted AES-CCM end-to-end (official known-answer vector, bad-tag rejection, no plaintext fallback), compare fixed secure no-batching vs fixed secure batching, and/or implement a simple measured traffic/deadline-aware batch policy. Do not rush a second AEAD suite, authentic profile renegotiation, full energy-based adaptation or publication-sized simulations for the mid-term.

**Second half: 18 November onward — strengthen, optimize, validate, and publish.** After the evaluation, complete both authenticated cipher profiles, nonce/replay handling, a cost- and energy-aware decision policy, measured Energest power model, modelled battery depletion, paired-seed experiments, ablations, security tests, and manuscript preparation. Date targets in Section 9 are *new internal targets*, not copied from the former research plan; adjust them after seeing the working simulator's runtime.

**Out of scope:** physical boards/batteries, manufacturing, cloud/phone dashboards, production key provisioning, new RPL protocol, custom cryptographic primitives, blockchain, and claims of a guaranteed energy/lifetime percentage improvement.

**Decision rule:** demo honesty outranks feature count. Native Cooja motes can establish functional behaviour and relative network counters but not hardware-accurate cryptographic CPU energy. If an AEAD fails integration, preserve real N0 network/aggregation results with explicit qualification and carry AEAD completion into the second half. If no energy instrumentation is validated by 16 Nov, show *packet count, delivery and latency*, not fabricated energy or battery-lifetime charts.

## 1. Research question, hypotheses, constraints

**Question:** Can a small, decentralised, measurement-driven policy that chooses an authenticated-encryption profile and bounded aggregation size lower energy per successfully delivered sensor reading and extend functional RPL network lifetime while preserving authenticated security, delivery reliability and application latency?

**H1, primary:** the proposed joint policy reduces mean/median energy **per uniquely delivered authenticated reading** against the strongest of fixed-AEAD no-batching and fixed-AEAD static-batching controls, under the same traffic and conditions.

**H2, secondary:** it improves functional lifetime and/or first node death (FND) without violating preregistered PDR and latency requirements.

**H3, mechanism:** joint policy gains remain measurable after separating the effects of batching and cipher selection in an ablation experiment; decision and profile-switching overhead do not dominate savings.

**Security invariant:** all experimental protected modes must provide confidentiality plus authentication/integrity; use vetted AES-CCM and NIST SP 800-232 Ascon-AEAD128 implementations and identical 128-bit tags if the implementations support those choices. They are different constructions; don't claim identical implementation cost or security proof. Do not compare raw block-cipher encryption with a complete AEAD service.

**Recommended initial constraints (hypotheses, tune with pilot and then freeze):** successful reading PDR >= 95%; p95 reading delivery delay <= 5 seconds for the relevant scenario; fail-safe behaviour for profile disagreement; no accidental fragmentation in the 'unfragmented' test class; same generated readings for all arms. These are illustrative, not baseline facts.

## 2. Ownership and team operating rules

| Owner | Responsibilities | Must deliver | Backup reviewer |
|---|---|---|---|
| Student 1 - Network | Docker/WSL2 or Linux environment, Cooja, RPL UDP transport, topology, scenario saves, build and integration | `firmware/sensor`, `firmware/root`, `.csc` scenarios, network README | Student 3 |
| Student 2 - Security/policy | AEAD library selection, crypto wrapper and known-answer tests, packet format, aggregation, profile logic, policy | `firmware/crypto`, `firmware/aggregate`, `firmware/policy`, protocol & threat docs | Student 1 |
| Student 3 - Experiments | Energest, lifetime accounting, structured logging, scripted runs, parser, statistics, charts, paper, reproducibility | `host/`, `configs/`, benchmark protocol, reports and results manifest | Student 2 |

Cross-cutting: each change needs a second-person review; every experimental claim requires evidence from logs. All three should be able to explain the 9-node demo. **Until 16 Nov:** 15-minute standups at 09:30 and 20:30 IST, a shared integration check at 20:30 daily, and immediate blocker escalation (do not hold code until the weekend). Student 1 is integration/release owner, Student 2 owns packet correctness/security, Student 3 owns run evidence and figures. From 18 Nov return to three short standups per week and two integrations weekly. Keep a decision log describing cuts, assumptions and why they were made.

A student is not allowed to accept an agent's 'done' message as proof: run the build/tests, check git diff, reproduce output, then merge.

## 3. Technology choices and exact starting point

- **OS:** Linux recommended; Windows users can use WSL2 Ubuntu with Linux container tooling. Avoid mixed Windows and Linux paths under the same build tree.
- **Simulator/OS:** Contiki-NG + Cooja, one pinned Contiki-NG commit and submodule versions. Start from `examples/rpl-udp` (UDP server is RPL root and client motes send periodically).
- **Development languages:** C (node code), Python 3 (runner, logs, statistics), minimal Bash and GitHub Actions.
- **Container:** official `contiker/contiki-ng` Docker image, pinned by digest or recorded exact image identity after validation. Official docs favour Docker for toolchain consistency.
- **Agent workflow:** Kiro (requirements/design/tasks specs); Codex (small C/Python changes and tests); Antigravity (multi-file inspection/integration and debugging). They are interchangeable; the primary source of truth remains git + specs, not agent chat history.
- **Simulation target:** `Cooja mote` first for quick functionality; try `Sky mote`/MSPSim after profiling code size and confirming library support. Emulated runs are preferable for CPU timing but may fail due to ROM/RAM limits; record this honestly.
- **Networking:** Contiki-NG RPL Lite/RPL with UDP over 6LoWPAN, default MAC/radio kept identical in controls. Use an application-layer security envelope so intermediate routers only forward packets.
- **Security libraries:** inspect Contiki-NG existing cryptographic primitives, availability and configuration first; use trusted, version-pinned AEAD implementations with NIST known-answer tests. Don't instruct an agent to invent AES-CCM/Ascon from scratch. Record licence and code provenance.
- **Analysis:** `pytest`, `numpy`, `pandas`, `matplotlib`, `scipy` or equivalent for reproducible tables and confidence intervals; use a pinned Python environment.

### Initial bootstrapping (illustrative; adjust GUI details to your machine)

```bash
# Run in Linux/WSL2; Docker engine must be available.
git clone https://github.com/contiki-ng/contiki-ng.git external/contiki-ng
cd external/contiki-ng
git submodule update --init --recursive
git rev-parse HEAD        # record exact commit
cd ../..
docker pull contiker/contiki-ng
# Follow the official Contiki-NG Docker instructions to mount this source
# and forward GUI display to Cooja. GUI forwarding differs on WSLg/desktop Linux.
# Inside a validated Contiki-NG toolchain environment:
cd tools/cooja
./gradlew run
```

You must first reproduce the official RPL tutorial **unaltered**: one `udp-server.c` RPL root + eight `udp-client.c` motes. Save console output and the `.csc` file. Only then introduce custom application code.

**Headless operation:** Cooja documentation supports `--no-gui` for a saved `.csc`, but headless simulations must contain a termination timeout in the simulation script. Capture the precise command that works with your pinned revision; provide `scripts/smoke.sh` and `scripts/run_experiment.py` to hide version-specific details. Do not assume an unknown Gradle option works without testing.

### Repo and output layout

```text
secure-rpl-research/
  README.md                    # 15-minute quickstart + commands
  AGENTS.md                    # agent guidance in all tools
  .kiro/specs/secure-rpl/      # requirements.md, design.md, tasks.md
  .github/workflows/ci.yml
  docs/
    scope.md                   # research question, variables, scope freeze
    architecture.md            # data flow and module interfaces
    protocol.md                # wire format, replay/nonce, suite negotiation
    threat-model.md            # attacks and non-goals
    power-model.md             # current/voltage assumptions and calibration
    experiment-protocol.md     # frozen baselines, seeds, stop criteria
    decision-log.md
    reproducibility.md
  firmware/
    Makefile project-conf.h
    common/                   # types, serializer, logging
    sensor/ root/             # Contiki processes and UDP
    crypto/                   # vetted library adapters, tests
    aggregate/                # fixed queue and timer
    policy/                   # fixed, threshold and joint rules
    energy/                   # Energest sampling and budget updates
  simulations/
    scenarios/                # .csc files; node positions + radio models
    scripts/                  # simulator log capture and seed injection
  configs/
    pilot.yaml main.yaml      # configuration matrices
    platform-power.yaml       # model-specific power values and references
  host/
    run_experiment.py parse_logs.py metrics.py plots.py
    requirements.lock
  tests/
    unit/ integration/ security/ regression/
  results/
    manifests/ summaries/ plots/   # small tracked artifacts
    raw/                         # ignore large raw logs; archive separately
  external/contiki-ng/            # pinned upstream, preferably submodule
```

Do not edit upstream Contiki-NG core unless the experiment proves it unavoidable; isolate modifications in `firmware/`. If a patch is unavoidable, maintain a clear small upstream patch file and document it.

## 4. Architecture and interfaces

### Sensor side

1. Periodic application process generates deterministic reading `reading_id`, simulated value, `created_at`, originating node ID.
2. `Aggregator` accumulates only **the same node's own readings**, not readings from arbitrary neighbouring nodes; flush when batch limit, maximum waiting deadline, maximum encrypted payload size, or critical event occurs.
3. `Policy` reads local energy estimate, traffic moving average, measured suite cost table and delivery metrics; selects `(AEAD profile, batch cap)` subject to constraints.
4. `Crypto adapter` serializes the batch, binds metadata as Additional Authenticated Data (AAD), uses unique AEAD nonce, writes authenticated packet.
5. UDP sends to the RPL root; intermediate RPL forwarders do not decrypt application data.
6. Energest counters and software counters produce structured event logs; simulated battery budget is updated.

### Root side

1. UDP receives packet; parse bounded, versioned header and length.
2. Identify permitted profile from header, select preprovisioned per-sensor test context.
3. Verify AEAD tag **before** releasing plaintext; reject invalid, unknown-profile, replayed, malformed or oversized packets.
4. Extract batch of readings; count each unique `(node_id, reading_id)` once; log generation and reception timestamps and route-related stats if available.
5. An optional authenticated profile request/ack (an extension, not assumed 'free') can validate explicit suite coordination under loss.

### Packet format specification, proposed v1

`version | sender_id | profile_id | key_epoch | packet_counter | readings_count | ciphertext | tag`

- Use unambiguous on-wire field sizes and network byte order; define them in `docs/protocol.md` *before* implementation.
- Bind all routing/application header fields (including profile) as AEAD AAD. Transmit only metadata essential for decryption, parsing and replay protection; not a raw secret key.
- Derive each cipher's required nonce of exact size from a unique `(node identity, key epoch, packet counter, direction)` encoding. Enforce uniqueness under a given key; counter wrap/restarts must never reuse a nonce. For the simulator, fail closed if persistent state is unavailable after a simulated reset; call this a non-production test key policy.
- Keys for two profiles must be distinct or safely derived using a standard KDF. Label all fixed test keys as test-only. Store no secrets in cloud logs.
- Use the same authentication tag length where the implementations allow. Mark any different overhead in results.
- Verify payload lengths before parsing. Use fixed-size buffers and bound all batch and message sizes; avoid dynamic heap allocations in the mote hot path.
- First integration version: both root and sensor pre-agree on supported suites, and sender places authenticated `profile_id` in each packet. That is **profile agility without online renegotiation**; report decision and reinitialisation costs but do not claim a handshake cost. After correctness is proven, a distinct `PROFILE_PROPOSE / PROFILE_ACK` exchange can be added as a measured extension. This avoids a premature distributed state-machine bug.

### Replay and failure semantics

Every packet gets a monotonically increasing counter per security context; root stores last accepted counter or a bounded replay window per sender. Duplicate UDP packets never count twice. Tag failures never fall back to plaintext. Unknown profiles are rejected, not silently accepted. Packet loss causes delivery loss but not cipher desynchronisation in profile-tagged v1. If negotiation is added, test lost propose, lost ack, duplicate and delayed ack, power-budget exhaustion during switch and node reset.

### Aggregation algorithm

Use a fixed-size ring buffer with operations `offer(reading)`, `should_flush(now)`, `build_batch()`, `commit_on_send()` and explicit drop accounting. Initial candidate batch caps: 1, 2, 4 readings; select based on actual encoded lengths. Initial candidate deadlines: 0, 1 and 3 seconds (not final protocol values). Buffer must flush on deadline even at low traffic; a high traffic rate may flush early at `max_batch`. Handle root/server backpressure or transmission failures consistently across arms. Do not change the sensor generation rate to make aggregation appear more efficient.

Check actual 802.15.4 frames using Cooja radio inspection. Typical 802.15.4 frames have a 127-byte PHY maximum, but the safe encrypted application size depends on MAC/6LoWPAN/IPv6/UDP compression and security overhead. Verify whether a simulated packet fragments; do **not** assume '64 bytes' always prevents fragmentation. If batching introduces fragments, treat this as an experiment variable or cap payload to remain below the measured threshold.

### Adaptive policy algorithm

First collect static calibration results for candidate pairs `(cipher, batch cap)` over a range of traffic and packet sizes. Use simple rolling-measurement features, not pre-trained ML; keep policy execution cheap.

For feasible actions `a=(cipher,batch)` estimate:

`cost(a) = [E_CPU_crypto(a) + E_radio(a) + E_control(a) + E_expected_loss_retransmit(a)] / E[unique_delivered_readings(a)]`

Reject an action if predicted p95 deadline, payload budget, authenticated-security support or PDR bound is violated. Switch only when expected benefit exceeds estimated transition cost plus a hysteresis margin; impose a minimum dwell interval. If estimates are unavailable, default to a preselected safe static profile. Low battery can increase an energy-priority weighting, but it must not disable authentication or violate the deadline.

Pseudo-logic:

```text
on_periodic_policy_tick:
  sample residual_energy, rate, packet_loss, Energest_deltas
  candidates = supported_AEAD_profiles x allowed_batch_sizes
  for a in candidates:
    if not secure(a) or !fits_mtu(a) or predict_delay(a) > limit: discard
    otherwise estimate energy_per_delivered_reading(a)
  best = min_cost(feasible candidates)
  if best is not current and dwell_time_ok and
     expected_horizon_saving(best,current) > transition_cost + margin:
       activate(best)
  log policy_features, estimates, selected_action, reason
```

The initial policy may optimize only aggregation if static benchmarking shows no reliable difference between authenticated ciphers. A negative cipher-switching result is scientifically acceptable.

## 5. Energy accounting and battery lifetime

Use Contiki-NG Energest periodic counters for CPU, LPM, deep LPM, radio transmit and radio listen. Convert ticks to seconds using the actual `ENERGEST_SECOND` of the chosen build. Sample time deltas, not repeated cumulative totals. **A plausible simulated battery is not physical battery measurement.**

One possible component-aware model:

`E_total[J] = V * (I_cpu*T_cpu + I_lpm*T_lpm + I_deep*T_deep + I_tx*T_tx + I_listen*T_listen)`

Only sum component currents that represent disjoint hardware components/modes. If datasheet radio currents represent *whole-board* draw rather than incremental radio current, subtract baseline MCU contribution or use calibrated total-platform states to avoid double counting. Keep voltage/current assumptions and source references in `platform-power.yaml`; run a sensitivity analysis on them. Never call native Cooja timing 'hardware-validated'.

At each sampling tick, `battery_remaining = initial_energy_budget - accumulated_energy`; mark a simulated node depleted when <= 0 and stop its application/radio or implement an equivalent explicit simulated failure. For research, state that this is a modelled death event, not Cooja's automatic battery physics. The initial budget must be fixed before main runs and large enough for warm-up but small enough to observe failures in the chosen horizon.

Track three different lifetimes: (1) FND = first battery-budget node death; (2) HND = half nodes depleted; (3) **functional network lifetime** = first time the network violates preregistered connectivity / delivered-reading condition for a persistent interval. FND can be misleading if a noncritical leaf dies first; functional lifetime is particularly important when multi-hop bottlenecks fail.

Track energy per **unique authenticated reading delivered**, not just energy per sent packet. Also report radio-on time, total bytes, mean energy per node, max/min node remaining energy and node lifetime distribution.

## 6. Instrumentation / telemetry schema

Emit one machine-parsable event per line with a stable prefix such as `RSLAB,` followed by JSON or escaped CSV. Avoid verbose debug in final runs because logging can perturb timing. For every event, include `run_id`, `sim_time_ms`, `node_id`, `event_type`, and optional fields. Suggested events:

| Event | Required fields |
|---|---|
| `READING_GENERATED` | reading_id, created_ms, bytes |
| `BATCH_SENT` | batch_id, reading_ids or range, count, plaintext_bytes, protected_bytes, profile, counter, policy_reason |
| `RECEIVED` | sender, batch_id, reading_ids, received_ms, auth_ok, duplicates |
| `AUTH_FAIL` | sender, reason_code, profile_id |
| `POLICY` | residual_J, traffic_rate, chosen_profile, batch_cap, predicted_cost, switch_reason |
| `ENERGY` | cpu_ticks, lpm_ticks, deep_ticks, tx_ticks, listen_ticks, residual_J |
| `ROUTE` | preferred_parent or rank (if exposed), route_change_count |
| `DEPLETED` | residual_J, time_ms |

One and only one place computes final metrics: `host/metrics.py`; never manually calculate paper charts from screenshots. Include a manifest per run with git SHA, Docker image digest, Python lockfile hash, scenario `.csc` SHA, config hash, software versions, seed, platform, network size, mode, generation rate, topology, run duration and build flags.

## 7. Exact baseline matrix

| ID | AEAD policy | Aggregation | Question answered |
|---|---|---|---|
| N0 | No application AEAD (diagnostic only) | None | Does the network work? Never use as a security-equivalent control |
| B1 | Fixed AES-CCM | 1 reading | Static strong authenticated baseline |
| B2 | Fixed Ascon-AEAD128 | 1 reading | Alternative AEAD cost |
| B3 | Battery-threshold fixed choice of permitted AEAD | 1 reading | Original research idea and switch overhead |
| B4 | Fixed AES-CCM | Fixed batch cap (e.g., 4) with deadline | Aggregation alone |
| B5 | Fixed Ascon-AEAD128 | Same fixed batch cap/deadline | Best static crypto + aggregation |
| B6 | Fixed best benchmarked AEAD | Adaptive batch cap/deadline | Adaptive aggregation alone (ablation) |
| P1 | Cost-aware secure profile choice | Adaptive batch cap/deadline | Full proposed method |

If results do not support cipher-specific differences, a secondary policy may use only batching and should be presented without claiming active cipher-choice benefits. All protected arms must generate identical readings and uphold the same end-to-end integrity/security requirement.

### Evaluation design

1. **Pilot:** 10-node network; fixed topology; one traffic profile; 3 seeds; establish network and metrics sanity. Start with B1/B2/B4/P1; then add all controls.
2. **Mid-term demonstration (16 Nov evidence freeze):** one reproducible 9-node (1 root + 8 clients) topology, one reading schedule, two actual executable modes (single reading and fixed batching), and preferably 3 paired seeds if runtime permits; 1 paired seed is an **engineering pilot** only, not a statistical claim. First measure generated readings, unique received readings, packet count/bytes and p95 delay. Add Energest-derived J/reading only after its counters and current model pass independent sanity checks. If AES-CCM is validated, compare **B1 vs B4**; otherwise explicitly label both pilot arms as **N0 (no AEAD), batch cap 1 vs cap 4**, not as security-equivalent research baselines. Dynamic batch sizing and AES-CCM secure tests are stretch for this deadline. Do not attempt the seven-policy matrix before the mid-term.
3. **Post-mid-term publication-grade main matrix:** e.g. 7 policies x 2 topologies (grid/bottleneck) x 2 sizes (10/20, expand to 30 if feasible) x 2 rates x 10 seeds = 560 runs. Start only after pilot provides expected simulation throughput; reduce factorial size if resources are insufficient, and record the decision *before* viewing main outcomes.
4. **Stress/robustness:** packet loss, bursty traffic, heterogeneous initial energy, deadline sensitivity, smaller/larger batch limits, simulated reboot, and route parent churn. Run select variants instead of doubling the entire matrix.
5. **Ablation:** no cipher choice; no adaptive batch; hysteresis disabled; switching cost ignored; no deadline protection. These explain what caused the improvement.

Every comparison must share node placement and random seed in paired runs, fixed radio model, initial battery budget, traffic generation traces, warm-up duration, link parameters, and experiment horizon. Final random seeds must not be tuned against the main outcome; retain separate calibration and test seeds.

### Metric definitions

- `PDR_reading = unique_authentic_readings_received_at_root / readings_generated_at_all_live_sensors` under a documented generation schedule.
- `PDR_packet = valid_data_packets_received / data_packets_transmitted` (different denominator; report separately).
- `Energy_per_delivered_reading = sum(network_node_energy_J) / unique_authentic_readings_received` (explicitly say whether root energy is excluded; primary recommend sensor/forwarder energy excluding mains-powered root).
- `Reading_delay = reception_time - generation_time`, per individual reading; p95 over uniquely delivered readings, and report number of missing readings separately.
- `FND/HND` and `functional_lifetime` per definitions in Section 5.
- `Switch_count`, `decision_CPU_time`, `control_bytes`, `failed switches`, `fragmentation_count`, `replay_rejection_count`, `auth_failure_count`.
- `ROM/RAM/stack`, CPU active time, radio TX/RX-on fractions where trustworthy.

### Statistics and figures

Aggregate per **run**, not per reading (readings within one simulation are dependent). Use paired-seed differences vs strongest static baseline, 95% bootstrap confidence intervals over runs or valid randomization/paired tests; preregister which. Show full distributions or confidence intervals, not just best seed. Plot: energy per reading, p95 latency vs energy, PDR, FND/functional survival curves, switching overhead, CPU/radio energy shares, packet-size effect, and ablation chart. Report negative and inconclusive results. Do not assert a guaranteed 25%-40% gain.

## 8. Software testing strategy and acceptance gates

**Unit tests (host builds):** batch serialize/deserialize roundtrip; empty/partial/full batches; timer expiry; buffer overflow; wrong node; malformed lengths; nonce allocator monotonicity; policy edge values; hysteresis; battery budget never negative before clamping. Compile C with warnings as errors and run sanitizer builds on host where supported.

**Crypto known-answer tests:** AES-CCM and Ascon-AEAD128 official published NIST/implementation test vectors for the exact variants; empty plaintext; different AAD lengths; exact tag mismatch; altered ciphertext/header; wrong key; replay; counter/epoch rollover rejection. Diff cryptographic source against pinned upstream and check licenses. Never accept self-generated-only vectors.

**Network integration:** 1 root + 2 nodes, then 1+8, then 1+19; successful RPL convergence and UDP delivery; verify root sees each reading once. Disconnect/kill a forwarding node to verify route loss/repair reporting. Use fixed seeds.

**Aggregation integration:** each reading appears once in decrypted batch, same total application bytes produced across modes, deadline hold time <= cap, no silent dropping, no unexpected fragmentation under the defined small-packet scenario.

**Profile tests:** root processes both allowed AEAD modes, wrong suite ID causes authentication rejection, switching a sender does not corrupt other sensors, packet loss does not cause permanent desync (if v1 uses per-packet profile ID).

**Energy tests:** idle node consumes >0 simulated energy with expected radio duty cycle; increased radio-on time increases energy; total energy equals sum of modelled state contributions; depleted node stops sending; changing initial budget changes death time monotonically holding state schedule fixed. Validate independent summary counts against raw log samples.

**Experiment tests:** every run returns exit code/status and manifest; parser rejects incomplete logs; missing seed fails CI; source SHA included; repeated same-seed deterministic traces are within known tolerated simulator variability; no chart is generated from malformed runs.

**Release gates:**

- G0: official unmodified 9-node RPL tutorial successfully runs (verified manually by two students).
- G1: root receives correct unique reading IDs under a custom client/root.
- G2: complete baseline AEAD roundtrip + failure tests in Cooja.
- G3: batching with correct delay/size bounds and successful decryption.
- G4: Energest collection + documented component power model + simulated death.
- G5: threshold then joint policy compared with B1/B2/B4/B5, no auth downgrades.
- G6: automated seeded experiments + independent reproducibility + charts.

Do not pass a gate based solely on an agent-generated summary or a screenshot.

## 9. REVISED execution calendar — first-half results by 16 November EOD

> **Hard milestone:** 17 November 2026 (Tuesday) is the **mid-term evaluation**. **All code, recorded runs, charts, demo video/screenshots, slides, and a release tag must be frozen on Monday 16 November.** Treat 12 Nov evening through 16 Nov as a compressed ~4-day-and-evening sprint; all dates/times below are **IST**. This schedule intentionally *does not follow* the uploaded research plan's earlier sequence or December-first prototype target.

### 9.1 Two halves and the exact demo scope

| Half | Dates | Primary outcome | Explicitly deferred |
|---|---|---|---|
| **Pre-mid-term / must execute** | **Thu 12 Nov evening – Mon 16 Nov EOD** | Running RPL+Cooja demo and **actual pilot plots** for single vs batched readings; show authenticated baseline too if it passes the security gate | Second AEAD, handshake/renegotiation, exhaustive switching policy, FND/HND, extensive scenarios, statistical significance claims |
| **Mid-term review** | **Tue 17 Nov** | Present reproducible demo, actual results and limitations; collect evaluator feedback | New feature merges and untested demo changes |
| **Post-mid-term / improve results** | **Wed 18 Nov onward** | Complete secure profiles, energy model, joint adaptive method, rigorous controls, optimisation, statistics and paper | Physical hardware remains out of scope throughout |

**First-half claims rule:** If tests establish only unprotected UDP and aggregation, write **'functional network/aggregation pilot, no end-to-end security yet'** on slides. If AES-CCM KAT and root-side tag failure are demonstrated, say **'AES-CCM-protected pilot'** and include B1/B4. A simulated energy estimate must be described as a model estimate, never a physical battery measurement.

### 9.2 Daily critical-path schedule for 12–16 November

| Deadline (IST) | Student 1 — Cooja / network / integration | Student 2 — payload / security / batching | Student 3 — measurement / reporting | Verifiable end-of-day output |
|---|---|---|---|---|
| **12 Nov, 18:30–23:00** | Create repo, pin Contiki commit, get official 1-root+8-client RPL UDP demo building, start GUI/headless troubleshooting | Define tiny payload `{node_id, reading_id, generated_at, value}`; choose one vetted AES-CCM adapter and plan host KATs; create minimal batch module skeleton | Make tiny CSV/JSONL schema (`GEN`, `TX`, `RX`), 3-event parser fixture, create result directories and plot stub | Shared branch structure, executable setup command or precise blocker log; signed-off 9-node target and minimal wire/log contract |
| **13 Nov, 13:00** | Show **G0** working: official Cooja nodes and root receive packets, save `.csc`, startup log, command; then fork example into repo | Implement bounded serialization, batch counter/deadline and host tests **without touching Contiki internals**; run crypto KAT on host separately | Make parser tests, count unique generated/received reading IDs, build PDR and packet-count CSV | Verified simulator startup and parseable example event format |
| **13 Nov, 21:00** | Integrate custom generator with root for **G1**; first 1+2 clients, then full 1+8 | Integrate simple fixed-batch mode, preserve reading IDs; if AES-CCM works on host, begin adapter integration | Capture N0 single-reading pilot and check reading totals/denominators | **Working unique-reading RPL demo** with raw logs and successful parser output |
| **14 Nov, 14:00** | Stabilise same `.csc` topology in both modes; document run seed and traffic period | Fixed batching with cap 4 / e.g. 1–3 s flush deadline; unit tests and no oversized packets; continue AES-CCM KAT/integration if safe | Execute same reading trace in single vs fixed-batch modes; produce preliminary packet-count/PDR/latency output | **Two actual modes on same network**; CSVs or explicit unresolved failure |
| **14 Nov, 21:00** | Repair packet loss, root parser failures, node crashes; verify multi-hop if topology permits | **AEAD decision checkpoint:** retain AES-CCM only if official KAT, bad-tag failure and root Cooja roundtrip are proven; otherwise freeze it as post-mid-term and label all current comparisons N0 | Validate metrics against raw logs, compare generated count and received unique IDs, make first 2–3 figures | **First defensible comparison**, either secured B1/B4 (preferred) or unprotected N0 single/batched (labelled) |
| **15 Nov, 13:00** | Turn configuration into repeatable script; fix root/client messages and scenario load | If B1/B4 secure and stable, add a small traffic/deadline batch policy; otherwise polish deterministic fixed batching and its tests | Run matched seeds (target 3; minimum 1 pilot) and one light/heavy rate if fast; generate script-driven charts | **Prototype demonstration candidate + real preliminary results** |
| **15 Nov, 21:00** | Conduct full rehearsal from clean checkout/other teammate's machine if possible; capture video and exact commands | Stop optional feature work; run security regression for any protected modes, audit payload lengths and deadline | Cross-check plots against run manifests and logs; produce an honest limitations table | Demo works without agent intervention; figure-source manifest exists |
| **16 Nov, 14:00** | **Feature freeze**: no new cipher, routing or policy features; only reproducibility/release blockers | Test existing working features, fix only stop-ship bugs; document 'implemented vs planned' | Re-run final chosen arms on frozen commit; collect raw log, SHA, seed, run status | Frozen candidate with reproducible trial(s) |
| **16 Nov, 18:00** | Package commands, `.csc`, tagged commit, 3–5-minute demo recording | Prepare architecture/security and limitations slides, one exact packet example | Final charts and numbers from actual runs only; maintain denominator/units | `results/midterm-2026-11-17/` contains run configs, logs, CSV, figures, screenshots and evidence index |
| **16 Nov, 21:00–23:00** | **Release `midterm-2026-11-17`**; cache dependencies and working copy; no disruptive changes | Rehearse 2-minute methods explanation + questions about security | Rehearse 2-minute evidence explanation + figures, include what was not yet implemented | Full live demo, 6–8 slides, offline backup video, Q&A, release tag |
| **17 Nov** | **MID-TERM EVALUATION** | Present exactly what passed | Record evaluator feedback | Written feedback and list of second-half improvements; no experimental claims beyond evidence |

**Unrealistic-goal guardrail:** aim for real AES-CCM integration, but do not allow it to block a verified RPL + aggregation comparison. All modes labelled `B1`, `B4`, etc. must genuinely use the specified AEAD, with real authentication checking. Do not substitute XOR/placeholder encryption, manually edit plots or invent run output. The minimum review artefact is a working network plus a truthful pilot; full paper-level evidence comes later.

### 9.3 Definition of done for the mid-term (MVP-M)

**P0 / must be complete by 16 Nov EOD:**

- [ ] One root + eight simulated nodes in a saved Cooja scenario, with traffic received at the root and route evidence.
- [ ] Sensor generator emits stable source/reading IDs, deterministic rate/seed and parseable structured logs.
- [ ] Two *executed* traffic modes on same setup: no batching and deadline-bounded fixed batching; all readings accounted for.
- [ ] One config/command can rerun both modes; at least one paired comparison (3 paired seeds if run throughput permits).
- [ ] Generated/delivered unique reading counts, packets sent, packet bytes and delay; figures produced via script from raw logs.
- [ ] If claiming 'secure': vetted AES-CCM actual on-mote encrypt/decrypt + known-answer vector + tamper/tag rejection; otherwise explicitly label pilot 'not yet authenticated'.
- [ ] `midterm-2026-11-17` git tag, exact version/commands, limitations, 6–8 slides and backup recorded demo.

**P0+ / use only after the above is green:** Energest ticks and clearly documented Joule conversion; static AES-CCM B1 vs B4 with authentication; rate/deadline-aware batching policy; a second traffic rate; 3 paired seeds. These are stronger but **must not endanger the functioning demonstration**.

**P1 / after 17 Nov:** Ascon-AEAD128, reliable cipher agility, switch energy, residual-energy model, FND/HND, multi-topology/battery experiments, enough seeds for inferential comparisons. **P2 / optional:** authenticated renegotiation handshake, routing-load feature, 30–50 nodes, second simulator/hardware (physical hardware stays excluded for Phase 1).

**Presentation structure:** slide 1 problem and date; 2 architecture and scope; 3 simulator/topology; 4 methods and modes with clear 'secured/unsecured' labelling; 5 live recorded packet trace; 6 actual comparisons with units and denominators; 7 limitations and second-half experiments; 8 contribution and questions. Demo: 3–5 minutes, with a video fallback if Cooja UI stalls.

### 9.4 Stop/go and fallback cutoffs (protect the 17 Nov evaluation)

| If blocked by… | Cutoff | What to do, honestly |
|---|---|---|
| Cooja GUI/toolchain | **13 Nov 13:00** | Switch to a validated Docker/Linux VM/headless path; continue official tutorial, log exact blocker. Never call a host-only C mock a Cooja/RPL result. |
| Custom UDP/RPL integration | **13 Nov 21:00** | Preserve official `rpl-udp` demo; instrument the existing packet path before designing a bigger custom app. Student 1 owns end-to-end repair. |
| AES-CCM on-mote build or tag verification | **14 Nov 21:00** | Keep vetted host crypto tests as partial evidence; continue N0 batching pilot. Defer B1/B4 claims and second cipher until after mid-term. |
| Batching on mote fails | **15 Nov 13:00** | Freeze known-good no-batch network; use host batch unit tests and packet-count *estimates as estimates*, never present them as simulated comparative performance. Prioritise making one second executable mode. |
| Energest/power-model validation fails | **15 Nov 21:00** | Show true packet counts/PDR/latency only. Defer joules, FND/HND and network-lifetime claims. |
| Plots / automation / environment fragile | **16 Nov 14:00** | Stop features, generate charts from last good real logs and record video on the proven environment. Any remaining missing feature is a transparent next-half item. |

### 9.5 Second half after mid-term: research and optimisation timeline (fresh internal schedule)

| Internal target | Priority outcome | Student 1 | Student 2 | Student 3 |
|---|---|---|---|---|
| **18–22 Nov** | Close MVP technical/security gaps | Harden saved topology, rerun scripts/headless if supported | Finish AES-CCM KAT/integration + nonce/replay if not already complete | Validate log metrics and traffic trace fairness; calibrated pilot |
| **23–30 Nov** | Two real secure static controls | Add 10/20-node reproducible cases, confirm packet MTU | Integrate Ascon-AEAD128 with official variant vectors; suite field and safe decoding | Energy counters/Energest and documented component-current model |
| **1–10 Dec** | Original idea + proposed improvement | Reliable route/traffic instrumentation | Implement B3 threshold profile choice and adaptive batch policy with hysteresis/cost gate | Instrument policy/switch counts, root-side unique delivery and measured action costs |
| **11–20 Dec** | Reliable joint method & preliminary comparative results | Integrate energy-depletion simulation and route changes | Fail-closed profile handling, replay/reboot tests, optimise memory | First complete B1–B6/P1 pilot comparison; actual signed plots and limitations |
| **21 Dec–10 Jan** | Result optimisation, fair ablations | Topology/traffic stress scenarios | Tune policy **only on separate calibration seeds**, fix security bugs | Paired pilots and targeted sensitivity studies, freeze main experiment protocol |
| **11–31 Jan** | Research-grade frozen experiments | Independent clean rerun and scenario ownership | Security regression and ablations | Execute pre-registered seed matrix; stats, confidence intervals, integrity checks |
| **February onward** | Publication preparation | Reproducibility/architecture/method details | Security and algorithm contribution/write-up | Tables, figures, comparative discussion and manuscript assembly |

Use workstream progress instead of a fixed promise of publication or numeric gain. **Do not transplant** original PDF timeline milestones back into this schedule.

### 9.6 Working rules specific to this compressed sprint

1. **Daily check-ins:** 09:30 and 20:30 IST through 16 Nov; 15 minutes each plus immediate blocker escalation. An owner can work asynchronously in between.
2. **Parallel tasks, serial integration:** Student 1 owns the one verified Cooja setup. Student 2 develops a testable batch/crypto module on a separate branch. Student 3 builds logs/parser/plots in parallel; integrate changes with short PRs daily.
3. **One current demo branch:** don't refactor Contiki core or fork in three incompatible environments. Student 1 merges only tested changes; tag a known-good state nightly.
4. **Research evidence:** every plotted value references raw log/run ID, commit, seed, config, parser command and a measurement definition. Label one-seed plots as pilot observations.
5. **Time allocation:** reserve at least the final 30–40% of 16 Nov for test runs, slides, backup video and release. Do not start new features after 14:00 that day.
6. **Agent rule:** open one bite-size issue per agent (<=2–4 hours of human-auditable scope where feasible). Agents cannot report completion based on generated code; a student must execute build/tests and save evidence.

## 10. How to operate coding agents without losing control

### Tools, roles and guardrails

- **Kiro:** use spec workflow to generate `requirements.md`, `design.md`, `tasks.md`. Humans review/correct the research assumptions and sign off requirements before any feature implementer starts.
- **Codex:** take a *single testable git issue* such as 'add bounded batch serializer and five tests', inspect repository and pinned docs, propose files, implement, run commands in sandbox, report diff, unresolved questions and exact test output. Persist guardrails in `AGENTS.md`.
- **Antigravity:** use for repository-wide inspection, integration diagnosis, multi-file worktree tasks and verifying Cooja logs; keep task worktrees or separate branches so no two agents write the same files. Validate any claimed browser/test outcome against local files.
- **Other agent (Claude Code, Copilot, etc.):** use as independent code reviewer or failure-analysis assistant, not parallel writer of the same crypto/protocol file. Extra tools are optional, not deliverables.

### Working agreement (mandatory)

1. Human opens a well-scoped GitHub issue with acceptance criteria and test commands.
2. Agent first inspects files, `AGENTS.md`, pinned Contiki source and official docs; **no edits until a short plan**.
3. Agent modifies one component, adds unit/integration tests and updates docs/manifest fields.
4. Agent provides git diff summary, commands run, logs, limitations and unverified assumptions. Human reproduces tests.
5. Another human reviews correctness; one student owns merge. Pin upstream versions and avoid unreviewed broad refactors.
6. Agent outputs may contain hallucinated library paths, compile flags or APIs. Prefer `grep`, `find` and compilation to undocumented assumptions.
7. Agent must not submit papers, change security assumptions, rewrite metrics, alter frozen experiment configs or push secrets without human approval.

### Required content of every coding-agent task

```text
Issue: <ID and title>
Owner: <person> | Branch: feat/<slug>
Goal: <observable functionality>
Context: Read AGENTS.md; docs/{architecture,protocol,experiment-protocol}.md
Files allowed: <explicit paths>
Do not change: <frozen files/Contiki core>
Acceptance tests: <exact commands and what should pass>
Evidence required: git diff, build output, test logs, sample generated log
Research constraint: Do not alter data generation/security/energy model implicitly
Request: Inspect -> propose small plan -> implement -> run tests -> summarize.
```

### Team branching scheme

- `main` protected; 1 approval from another student; checks green; no force push.
- `feat/network-*` Student 1, `feat/security-*` Student 2, `feat/experiments-*` Student 3, `fix/*` targeted patches.
- PRs under ~300 lines of functional changes when reasonable. **Through 16 Nov merge tested changes at least daily**, not at the weekend; maintain a stable demo branch/tag. After mid-term, integrate at least twice weekly.
- Pin dependencies (`git submodule SHA`, container digest, pip lockfile). Save simulation seeds, scripts and configs in git; archive large raw logs with hashes.
- Use basic CI for unit/build quickly; keep heavy 20-50-node Cooja simulations in a scheduled/manual workflow. Record execution environment for every plot.

### Mini-prompt A - first environment task

```text
Read AGENTS.md and the Contiki-NG official Cooja and Docker docs. Do not modify source code yet.
Inspect this repository and identify the current Contiki-NG SHA, target and toolchain.
Create docs/setup-linux.md with precise steps to launch the official 1-root/8-client
examples/rpl-udp simulation on our validated Linux/WSL2 environment.
Record observed commands, terminal output and versions; do not claim success unless you ran them.
Add scripts/smoke.sh only after proving the commands locally.
```

### Mini-prompt B - secure packet feature

```text
Read docs/protocol.md, docs/threat-model.md and AGENTS.md.
Implement the smallest AES-CCM AEAD adapter for application-level UDP payloads.
First identify an existing vetted implementation compatible with the pinned Contiki build.
Do not write your own primitive. Add official known-answer tests, invalid-tag and wrong-AAD tests,
length checks, sender/counter handling, and integration acceptance test with 1 root + 2 clients.
No insecure plaintext fallback. Report exact build/test commands and any memory constraints.
```

### Mini-prompt C - aggregation feature

```text
Implement a bounded reading aggregator with caps for maximum count, deadline,
and serialized payload bytes; fixed memory only. Use tests covering exact deadline,
1/2/4 reading batches, overflow, duplicate IDs and interruption during send.
Do not alter generated-reading schedule or RPL configuration. Instrument per-reading
latency at root. Run unit tests then one Cooja integration scenario. Provide diff and logs.
```

### Mini-prompt D - reproducible energy and experiment runner

```text
Create a host parser and experiment runner for the existing RSLAB event schema.
Make no changes to firmware. Validate run manifests, seeded settings, energy tick deltas,
duplicate-reading counting, incomplete runs and depleted-node events.
Use a config-driven scenario matrix; write deterministic summary tables and CI-friendly
plots. Test using fixtures with known expected answers; fail on missing required events.
```

### Mini-prompt E - independent red-team review

```text
Review the proposed RPL AEAD packet implementation without modifying code.
Focus on nonce uniqueness per key and restarts, replay window, profile-id AAD coverage,
tag verification before parsing, batch bounds, integer overflow and invalid-profile handling.
Return severity-ranked findings with file/line references and a concrete failing test idea
for each finding. Do not claim vulnerability without showing a reproducible path.
```

## 11. Risk register and go/no-go decisions

| Risk | Early symptom | Mitigation / stop rule |
|---|---|---|
| Cooja/Java/WSL2 GUI issues | simulator fails before custom code | Follow official Docker/GUI docs, pin versions; fall back to Linux VM or headless after validating GUI once |
| AEAD library exceeds Sky mote ROM/RAM | link/build fails for emulation | Prove functional crypto with native Cooja first; select supported emulated platform or document emulation limit; never use native timing as hardware cycles |
| Nonce reuse/replay bug | duplicate accepted; altered header decrypts | Block merge at G2; use official KAT and malicious-packet tests, per-sensor counters and no key reuse |
| Batching increases delay or fragmentation | p95 violates bound; many fragments | Lower batch cap/deadline, log fragments, prefer data-driven upper limit |
| Energy results are implausible | identical energy for high/low load, radio always-on dominates | Inspect Energest and radio duty-cycle, document current assumptions, test sensitivity |
| Strong static baseline wins | joint policy gives zero/negative benefit | Report result honestly; reframe contribution as limits and trade-offs or focus on proven aggregation effect |
| Simulation does not reach node death | all nodes alive at horizon | Adjust preregistered energy budget or observe longer runs before final matrix; never adjust budgets separately by algorithm |
| Too many main runs | no time to complete | Pilot runtime first, reduce factorial dimension pre-results, reserve paired seeds, document design power and limitations |
| Agent hallucinates Contiki APIs | code does not compile | Require grep/file inspection, compile/run evidence and human review |
| Last-minute large merges | integration broken before demo | Daily merges during 12–16 Nov, feature freeze **16 Nov 14:00 IST**, verified regression and backup recording |

## 12. Definition of done and deliverables

**Release package:** (1) public/private code repository with exact licence/provenance, (2) validated setup instructions, (3) `.csc` scenarios and deterministic generator, (4) AEAD test report and threat model, (5) static and adaptive firmware, (6) Energest-based model/assumption table, (7) a one-command or clearly documented experiment runner, (8) raw logs plus hashes and summary CSV, (9) scripts generating all figures, (10) B.Tech demonstration video or live run script, (11) discussion of limitations/negative results, (12) research-method section and subsequent paper draft.

**An experiment is complete only if:** it has one versioned manifest, an exit/timeout status, no silent authentication error, validated generator/receiver counts, reproducible `seed`, measured policy/security state, documented link/power assumptions and parseable raw output.

**The team is ready for a manuscript when:** all planned controls were run or exclusions documented, primary metric and seed policy were frozen before final runs, uncertainty is reported, a second member reproduced a subset from a clean checkout, claims can be traced to generated tables, and no confidential keys or unsupported hardware-accuracy claims appear.

## 13. Immediate actions on 12 November evening (do not defer to the next working day)

1. **18:30–19:00 IST / all:** open a shared repository/issue board, assign Student 1 integration, Student 2 batch/security, Student 3 metrics/plots, and explicitly adopt the 16 Nov EOD freeze.
2. **19:00 onward / Student 1:** launch the official 1-root/8-client RPL example in one pinned Contiki environment; save exact working commands and simulator version. Log a blocker immediately if the launch fails.
3. **19:00 onward / Student 2:** implement a small fixed-memory reading serializer and batch scheduler with host tests; simultaneously inspect vetted AES-CCM availability and run *official* host tests without delaying the network path.
4. **19:00 onward / Student 3:** create structured `GEN/TX/RX` parser with 3-generated/2-unique-delivered fixture; define the exact two-mode paired-run table and make plot generation work against known test fixtures (fixtures are not research results).
5. **20:30 / all:** check the path from simulated source to root and agree minimal packet/log fields. Merge only verified changes; save nightly known-good commit.
6. **13 Nov 13:00:** G0 simulator decision. **13 Nov 21:00:** first custom reading demo. **14 Nov 21:00:** preliminary comparison. **15 Nov 21:00:** rehearsal. **16 Nov 14:00:** feature freeze. **16 Nov 21:00:** tag + deliver.

## 14. Reference links and provenance

### User-supplied research materials
- `Adaptive_Cipher_Selection_Synopsis(3).pdf`: original per-node battery-driven RPL cipher-switching idea, Cooja/Contiki-NG, network lifetime/security/overhead.
- `Detailed Research Plan Adaptive Cipher Selection in RPL (1)(3).pdf`: original milestones, C/Contiki/Python stack, software simulation targets and delivery dates.
- `Research Foundation for Adaptive Cipher Selection in RPL(1).pdf`: research gap caveats, authenticated-encryption fairness, switching/energy measurements and standards correction.

### Current official external references, accessed Nov 12, 2026
- Contiki-NG Docker: https://docs.contiki-ng.org/en/master/doc/getting-started/Docker.html
- Contiki-NG Cooja tutorial: https://docs.contiki-ng.org/en/master/doc/tutorials/Running-Contiki-NG-in-Cooja.html
- Contiki-NG RPL network tutorial: https://docs.contiki-ng.org/en/master/doc/tutorials/Running-a-RPL-network-in-Cooja.html
- Contiki-NG RPL example: https://github.com/contiki-ng/contiki-ng/tree/develop/examples/rpl-udp
- Contiki-NG Energest instrumentation: https://docs.contiki-ng.org/en/master/doc/tutorials/Instrumenting-Contiki-NG-applications-with-energy-usage-estimation.html
- Contiki-NG headless simulation guide: https://github.com/contiki-ng/contiki-ng/blob/develop/doc/tutorials/Running-Contiki-NG-in-Cooja.md
- NIST SP 800-232: https://csrc.nist.gov/pubs/sp/800/232/final
- Codex AGENTS.md: https://learn.chatgpt.com/docs/customization/overview
- Kiro spec workflow: https://kiro.dev/docs/specs/
- Google Antigravity agent/project docs: https://antigravity.google/docs/overview

---
**End of software-only Phase 1 master plan. No network, experiment results, repository, or firmware has been created by this document.**
