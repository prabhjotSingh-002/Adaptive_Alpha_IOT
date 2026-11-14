# Phase 2 implementation boundaries

The original plans under PLANS/ remain authoritative. Portable protocol and aggregation C files are compiled unchanged into host tests and both Contiki applications. Sensor uses existing RPL/UDP and etimer; root decodes bounded packets and maintains per-source reading windows. Phase 3 adds a vetted crypto adapter and secure envelope; diagnostic profile zero is never an implicit fallback.

Config: configs/phase2.json is resolved by host/run_experiment.py into firmware/generated-conf.h and a per-run manifest/scenario. Builds are serialized with a runner lock, cleaned between modes to prevent stale settings, and checked at runtime using READY events. Boot jitter/topology/radio model/seeds remain identical across paired modes. No network RNG is consumed by reading generation.

A 125ms polling tick services local generation/deadline timers. Configuration periods/deadlines are multiples of 125ms. Pilot generation begins at local 60s, 24 readings at 1Hz. Deadline precedence flushes the previous batch before offering a reading arriving at its exact expiry. Consequently the normal cap-4/3s pilot can emit count-3 batches; faster traffic verifies count-4 flushing. The deadline is queue hold time at submission initiation, not total network delay or a delivery guarantee.

GEN is logged before network work to prevent mode-dependent send processing from shifting measured generation time. Host joins source/reading IDs on Cooja-global event times; payload local clocks are checked for consistency only. RX unprotected events have auth_ok=false. Metrics validate generation and sender disposition, reject corrupt/incomplete runs, report missing deliveries, and count unique reading IDs independently of UDP packet counts. Radio-trigger capture saves actual raw MAC frames; parser recognizes classic unencrypted frame layouts and FRAG1/FRAGN dispatch at the MAC payload boundary. Unsupported layouts are rejected for review.

No new host package or Python dependency was needed for runner/metrics/tests: standard library is used. Existing container GCC/sanitizers provide C tests; its existing matplotlib provides plotting. No empirical energy or security result is claimed for Phase 2. Phase 3 controlled AES results are separately identified in its evidence index.

## Phase 3 extension

The same generator and bounded aggregator feed profile-specific N0 or AES packets. The AES path uses the pinned CCM driver, a test-only boot grant and per-sender root replay contexts; host/run_experiment.py serializes both phases. See [security contract](phase3-security-contract.md) and [usage](phase3-usage.md).
