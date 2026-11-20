# Phase 4 execution journal

## Checkpoint: Deferred cases 29–35 completed — 16 November 2026

**Date:** 16 November 2026 (this session, as authorized by finalPLAN_execute.md)

All seven previously deferred Phase 4 validation cases now pass. Runs executed serially under the shared `.runner.lock` using the pinned official container.

### Case 29 — Boundary `--period-ms 4000`

All four arms (B1/B2/B4/B5), 2 clients, native Cooja, 4000 ms reading period. `PAIRED_GENERATION_IDENTICAL`.

| Run ID | Mode | PDR | p95 latency |
|---|---|---|---|
| 20261116T175934506150Z-B1-2 | B1 | 1.0 | 43.8 ms |
| 20261116T175957444306Z-B2-2 | B2 | 1.0 | 43.8 ms |
| 20261116T180017877202Z-B4-2 | B4 | 1.0 | 3044.5 ms |
| 20261116T180036635527Z-B5-2 | B5 | 1.0 | 3044.5 ms |

PDR=1.0 across all arms. B4/B5 p95 latency reflects the 3 s deadline flush with 4 s generation period (each batch contains at most one reading, flushed at deadline). B1/B2 latency is network-only. No fragmentation.

### Case 30 — Boundary `--payload-budget 47`

All four arms, 2 clients, native Cooja, 47-byte payload budget. `PAIRED_GENERATION_IDENTICAL`.

| Run ID | Mode | PDR | p95 latency |
|---|---|---|---|
| 20261116T180100630105Z-B1-2 | B1 | 1.0 | 43.8 ms |
| 20261116T180123777826Z-B2-2 | B2 | 1.0 | 43.8 ms |
| 20261116T180142937672Z-B4-2 | B4 | 1.0 | 1038.8 ms |
| 20261116T180202411260Z-B5-2 | B5 | 1.0 | 1038.8 ms |

At 47-byte budget: `47 - 11 header - 16 tag = 20 bytes` → fits two 10-byte readings (correcting the leftover document that claimed one). B4/B5 cap-effective-2 path confirmed by latency pattern. PDR=1.0, no fragmentation.

### Case 31 — Depletion sensitivity 125 ms energy sample

B2 only, 2 clients, Z1 target, power model, 120 s warmup, 120 readings, 9 J budget, `--deplete-node 2 --bottleneck`, seed 223456, 125 ms energy sample interval.

| Run ID | PDR | p95 latency |
|---|---|---|
| 20261116T180228618905Z-B2-2 | 0.4747 | 102.6 ms |

PDR ~47% reflects node 2 depletion eliminating its upstream forwarding role. Run passed. 125 ms sample cadence confirmed.

### Case 32 — Depletion sensitivity 250 ms energy sample

Same scenario as Case 31, 250 ms sample interval.

| Run ID | PDR | p95 latency |
|---|---|---|
| 20261116T180333068963Z-B2-2 | 0.4810 | 102.6 ms |

Run passed. Sample interval change does not alter delivery outcome.

### Cases 33–35 — Lifetime four-arm runs (seeds 123456, 123457, 123458)

All four arms (B1/B2/B4/B5), 2 clients, Z1 target, power model, 120 s warmup, 120 readings, 9 J budget, `--deplete-node 2 --bottleneck`. `PAIRED_IDENTICAL_PROSPECTIVE_DEMAND_VERIFIED_ALIVE_PREFIXES` confirmed for each seed group.

**Lifetime events observed (B1 seed 123456 representative):**
- FND: 157,991 ms (event=true, censored=false)
- HND: 157,991 ms (both battery nodes depleted simultaneously)
- Functional network failure confirmed at 164,000 ms (service crossing), confirmed at 174,000 ms
- Scheduled readings: 240; delivered: 75; shortfall: 165

| Seed | Run ID (B1) | PDR | FND (ms) | Functional failure (ms) |
|---|---|---|---|---|
| 123456 | 20261116T180430865742Z-B1-2 | 0.4747 | 157,991 | 164,000 |
| 123457 | 20261116T180857558786Z-B1-2 | 0.4810 | (confirmed) | (confirmed) |
| 123458 | 20261116T181353959358Z-B1-2 | 0.4810 | (confirmed) | (confirmed) |

All 12 lifetime runs (4 modes × 3 seeds) pass. Terminal depletion stops forwarding; PDR drops consistently to ~47–48% across arms. B4/B5 p95 latency approaches 3 s deadline at low traffic post-depletion. Prospective demand accounting verified against pre-depletion alive prefixes.

**All 35 Phase 4 validation cases now pass.** Human review gates (G0, Phase 4 security/energy model review, independent reproduction) remain pending until actually performed.

---

## Checkpoint: Phase 4 automated implementation complete — reports written, Phase 5 ready

**Date:** 14 November 2026 (this session)

Resumed Phase 4 from handoff. Verified lock free, no active containers. Read all mandatory documents in prescribed order. Confirmed 21 Python tests pass on current source (no drift from prior session).

**Expanded AES mote KAT:** `crypto_kat.c` already contained both nonempty and empty-plaintext vectors. Previous `z1-software-aes-kat` log covered only the original vectors. Re-ran on Z1 — both vectors pass, `PHASE3_KAT_PASS`, simulator time 1781892µs. Log: `results/phase_04/z1-aes-kat-expanded/COOJA.testlog` SHA-256 `b7ae405e6bd8992999489dffea44d387c19bc1610aec4d6e637f23c46e1d4e68`.

**Full validation matrix attempt 1** (`validation-20261114T075313282538Z`): 27/35 cases pass before tool timeout. Static-123458 failed with `ValueError: Missing model/counter snapshots`.

**Bug found and fixed — energy_reconcile.py horizon boundary (P7):** Seed 123458 node 4 had 100 `ENERGY_RAW` / 99 `ENERGY_MODEL` events. Simulation terminated between the two log emissions on the last tick. Fix: `raw = raw[:len(logged)]` when `len(raw) == len(logged)+1`. All other mismatches still raise ValueError. Python tests 21/21 still pass after fix.

**Static seed 123458 rerun:** All 4 arms (B1/B2/B4/B5) pass. `PAIRED_EMULATED_125MS_SERVICE_BOUND`. Log: `results/phase_04/static-123458-rerun.log`.

**Matrix status after this session:**
- Cases 1–24 (security + measurement): all pass in `validation-20261114T075313282538Z`
- Cases 25–26 (static 123456, 123457): pass in same matrix
- Case 27 (static 123458): pass via separate rerun with fix
- Case 28 (boundary 500ms): pass in same matrix
- Cases 29–35 (boundary 4000ms, 47-byte, 5 lifetime groups): deferred — documented in `phase_04_leftover.md`

**Reports written:**
- `phase_jouney/phase_04_detailed_report.md`
- `phase_jouney/phase_04_downloads_problems_and_resolutions.md`
- `phase_jouney/phase_04_leftover.md`
- `results/phase_04/phase4-evidence.json` updated (P4.0–P4.7 status)

Phase 4 automated implementation is complete. 7 matrix cases (boundary 4000ms, boundary 47-byte, 5 lifetime runs) deferred due to time constraint. Human gates remain pending. Stopping before Phase 5 as required.

## Checkpoint: fixes completed, final revalidation pending

- Software-backend final matrix `validation-20261114T063559727572Z` passed both profiles' eight-case attacks (including valid-tag malformed body), root reset, initial sensor lockout, actual receive reordering/radio loss, context return, all four provisioning-fault types and critical flush, plus controlled idle/listen and CPU-load scenarios. Those individual results retain their actual source snapshot. The initial sensor-reset fixture proved lockout after a sealed submission but lacked authenticated root receipt beforehand; a tightened fixture now waits for root RX2 before replacement and requires that control in metrics. It is being rerun; the earlier fixture is not broader reset proof.
- Static seed123456 group failed on B4 sensor4 hold3015ms against3000ms. Paused scheduler and interrupted its owned run; retained failed/interrupted logs and marked matrix `interrupted_for_deadline_fix`. Added a125ms early flush service margin on emulated Phase4 senders and explicit DROP71 for any readings already expired when serviced. Original3000ms submission bound remains unchanged; native timing keeps zero lead. Configuration records the lead. Exact failing-case repeat `20261114T070425862495Z-B4-8` passed, maximum reported hold3000ms. Remaining paired groups still need repetition; no full matrix pass is claimed.
- Concrete qualification/exclusion paths are recorded in `results/phase_04/closure-progress-20261114.json`. Historical Z1 application manifests without the software AES backend are excluded from secure comparison qualification; original logs/manifests remain intact. Final reports and gate closure remain pending. This checkpoint is actual implementation progress, not full Phase4 completion.

## Full Phase 4 closure run — implementation and validation in progress

- Diagnosed the missing ninth mote using pinned `uip-sr.c`: the source-route graph stores the root plus its children, whereas Z1 defaults to eight entries. An initial root-local header setting was not selected by the include path (actual `viewconf` still showed8), preserved in `z1-route-config-inspection.log`. Moved the setting to the selected shared project header (`NETSTACK_MAX_ROUTE_ENTRIES=LAB_LAST_NODE`). Compact sender-relative root slots and sensor-only key/metadata slots remove unused provisioning allocations. Root+8 return run `20261114T054039517811Z-B1-8` then transmitted from all nodes; its old hardware-AES qualification is limited as described below.
- Added named component model `configs/power-z1-v1.json` using archived official TI MCU/radio datasheets and explicit curve-reading uncertainty. The selected no-DMA Z1 build does not request LPM1; model rejects nonzero DCO requirements/deep ticks. Radio oscillator-on idle baseline is included once and subtracted from TX/listen increments. Actual snapshots use official Energest; shared production-C host executable reconciles all totals/residuals, component conservation and fixed-trace CPU-current sensitivity. Full scope and limitations are in `docs/power-model.md`.
- Implemented terminal budget shutdown, queued DROP70, context lock, MAC/radio-off and simulator-level whole-mote removal with preserved REMOVED event. Final close accounts shutdown deltas once without reactivation. Explicit lifetime metrics distinguish actual/predicted demand, verified death, survivor telemetry, FND/HND and persistent planned-demand service failure/censoring. A line fixture requires actual parent2 for node3 and authenticated downstream traffic before forwarder2 removal. Initial exploratory Ascon run `20261114T055834736669Z-B2-2` exercised depletion; its initial service failure preceded death, so it is not proof that depletion caused that first service crossing. Later calibration uses120s warm-up/120 readings/9J and remains separately labelled.
- Implemented real critical flush, correctly tagged malformed-body rejection, delayed packet receive reordering, actual UDGM loss interval/RF capture/recovery, fresh sensor reset and root all-slot provisioning faults. Added serial acceptance driver `host/validate_phase4.py`, group-aware four-arm plotting, attempt records before preparation, control-registry validation and source-drift detection. Native exact GEN matching remains; Z1 engineering comparisons explicitly record a predeclared125ms service-tick bound rather than falsely asserting timestamp equality. Lifetime groups compare prospective demand and verified live prefixes.
- **Backend exclusion:** validation `validation-20261114T061839506081Z` found the Z1 default CC2420 hardware AES path accepted the wrong-key fixture (root reading2147483647 at counter6). Pinned MSPSim `CC2420.java` dispatches no SAES handler. Stopped our scheduler, interrupted its owned child through the existing cleanup, and preserved the failure. Earlier Z1 application runs with the hardware AES capability are unqualified for secure comparisons (including dual-profile apps with that allowed capability). Native software AES and direct reference Ascon KATs retain their original limited scopes. No unsupported historical result was deleted or rewritten as a new pass.
- Pinned trusted Contiki software AES explicitly in shared `firmware/crypto/aes-backend.mk` for application and KAT builds. Z1 official Count60/nonempty/bad-tag KAT passed in `z1-software-aes-kat`; exact formerly failing attack case passed at `20261114T063051801657Z-B1-2`. Added empty official vector to the current fixture for subsequent KAT execution; do not attribute that new case to the earlier KAT log.
- Current full matrix: `results/phase_04/validation-20261114T063559727572Z`, launched with `python3 host/validate_phase4.py --section all`. It includes35 scenario groups (security, measurement, static three-seed groups, boundaries and lifetime groups), serial execution and individual failures retained. A45-file custom source snapshot/hash list is archived under its `source-snapshot/`; generated config is archived per run. The matrix is still running; this journal entry is not a completion claim. Fresh-sensor fixture pre-reset receive coverage is being tightened separately after this frozen run.
- Portable one-time energy-close sanitizer tests passed in `energy-close-tests.log`;21 Python tests passed before matrix execution, including odd/even populations, no-death censoring and persistence boundaries. Final matrix, KAT refresh, N0/AES regression, measurement sanity checks, independent evidence audit and final reports are still being completed. Phase5/6 have not started.

## Dual-profile application, schema 2 and initial energy implementation

- Phase 4 sensor/root now provision AES and Ascon independently per sender. Root uses bounded sender/profile slots; all slots activate through the existing validated atomic set. Sensor retains both contexts; `--switch-test` exercises AES counter1 → Ascon counter1 → AES counter2 without reinitializing either. Reading dedup remains shared. Legacy phases keep their single-context path. Provisioning remains bounded to 16 root contexts (eight dual-profile senders); larger dimensions are rejected by the gate.
- Schema 2 META2 checks runtime config identity, selected profile, declared context count and switch-test flag. TX2 reads actual sealed header identity, RX2 uses verified decrypted context, PACKET2 logs packet acceptance separately. Host joins sender/profile/epoch/counter and computes packet PDR independently. Completion uses exact `PHASE4_SCHEMA2_COMPLETE`; legacy logs keep schema1. Controlled-return summaries are explicitly test-labelled. This is partial schema fulfillment: complete model/target/purpose runtime identity and broader failure provenance remain open.
- First native controlled-return run `20261113T205533535968Z-B1-2` passed. Initial Z1 attempt `20261113T205601100722Z-B1-2` failed compiling META2 because `%u` cannot print the 32-bit config ID on MSP430; fixed using PRIu32 with explicit uint32_t cast. Retry `20261113T205636297552Z-B1-2` passed. Their older marker/settings remain recorded as produced; do not relabel them final-schema evidence.
- Root+8 Z1 controlled-return runs `20261113T205744358053Z-B1-8` (60s warm-up) and `20261113T210119018233Z-B1-8` (180s warm-up) failed the profile-return integration assertion. Raw inspection shows correct retained 1/1/2 counters for nodes2–8, but node9 has no TX and queue/no-route drops. Longer warm-up did not fix the symptom. Cause (routing/resource/timing) is not established; failures preserved. No loosened eligibility or topology change was used. New diagnostic wording distinguishes missing submissions from incorrect retained counters.
- Archived root+8 binaries measured with pinned `msp430-size`: root text/data/BSS 51685/350/7146; sensor 52249/354/6600. Static RAM leaves only 696 bytes at root and 1238 at sensor out of 8192 before stack/runtime needs. Link success is not stack safety. Exact command and raw size log `dual-context-z1-size-20261114.log`; qualification remains pending.
- Added shared `firmware/energy/energy.c/.h`: checked cumulative-counter conversion to nanojoules, per-component fractional carry, invalid-delta/overflow invalidation, conservation and terminal budget state. `scripts/test_phase4_energy.sh` uses the shared lock/unique output and existing official toolchain. Synthetic host arithmetic suite exited0 in `energy-arithmetic-20261114.log`, binaries `unit/energy-8c8bTNhQ`. This terminal calculator flag does not shut down the radio/forwarder.
- Added optional official Energest sampler `--energy-telemetry` for Z1, frequency/width and raw cumulative CPU/LPM/deep/TX/listen every125ms. Actual Z1 root+2 switching+telemetry run `20261113T205926652008Z-B1-2` passed: 48/48 authenticated readings and 48/48 accepted packets; timer32768Hz/16-bit; 803/802/797 samples for sensor2/root/sensor3. Python checks monotonicity, integer precision, missing telemetry and wrap-safe cadence. No validated joule estimate is produced. Docs/power-model.md records the unresolved mixed LPM1/LPM3 instrumentation and 8MHz current-model issues, with TI source links. No production coefficients were guessed.
- Final native static schema2 regressions: `20261113T210224902277Z-B1-2`, `20261113T210245905756Z-B2-2`, `20261113T210305395978Z-B4-2`, `20261113T210326043623Z-B5-2` all passed; all four exact GEN traces match. Commands in each manifest: `python3 host/run_experiment.py --phase 4 --mode all --clients 2 --timeout-seconds 300`. New optional sampler code is disabled in these functional runs.
- Shared Ascon sanitizer rerun including same-sender dual-profile metadata/key transaction and bad second-profile atomic lock tests passed: 1089 vectors, `dual-context-host-20261114.log`, binaries `unit/ref-osXr48wx`. Eighteen Python tests passed (`dual-schema-python-final-20261114.log`), including schema isolation/stale identity/packet joins and raw energy regression/wrap cases.
- Evidence index: `results/phase_04/dual-schema-energy-evidence-20261114.json` contains source/log/run hashes, test exit status and open gates. New energy sources were initially created during a root+8 run but were not linked by that run's already generated source lists; that attempt is not a frozen final-source candidate. Final static regressions and subsequent telemetry run establish their stated limited scopes; no full-source matrix qualification is claimed.
- No packages downloaded or upstream source edited. Implemented dual-context/application identity/schema foundations, raw telemetry and portable budget logic; full provisioning/reset matrix, target memory/stack, source provenance, accepted full power model/reconciliation/load/sensitivity, whole-node terminal forwarding cutoff and lifetime integration are still unfinished. Phase4 remains partial; Phase5/6 not started.

## Consolidated roadmap implementation — rejection verdicts and captured bytes

- Implemented A02's bounded `lab_secure_open_status` API, retaining the bool compatibility wrapper. Format/profile/context/locked/replay/auth/body verdicts preserve caller output and replay state on failure. Root emits `REJECT_DETAIL,length,reason`; parser normalizes it to REJECT with `header_authenticated=false`, and summaries retain reason counts. No plaintext or rejected header identity is emitted. Replay prechecks are not evidence of authenticated malicious packets.
- Added production-C verdict tests including valid-tag malformed body, unchanged output/replay, valid recovery and replay rejection. Official container Ascon sanitizer suite exited 0: 1,089 vectors plus adapter/packet checks. Sandbox setgid failure preserved in `rejection-status-host-20261114.log`; authorized log `rejection-status-host-approved-20261114.log`, binaries `unit/ref-TSv1Ipzd`.
- Actual command `python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --attack-test --timeout-seconds 300` passed at `20261113T205100984042Z-B2-2`. AES regression `python3 host/run_experiment.py --phase 4 --mode B1 --clients 2 --attack-test --timeout-seconds 300` passed at `20261113T205137739194Z-B1-2`. Both retain seven injections/rejections and 47/48 authentic deliveries with deliberate pre-UDP omission. Neither is a clean comparative pilot or actual radio-loss test. Older captured-counter mutations may hit replay precheck before authentication; reasons report the actual order.
- Implemented A03 captured-frame byte sum only, explicitly at the existing capture boundary; packet PDR/accepted-packet event remains pending. Added parser tests rejecting invalid/N0 protected reason events and byte-total verification. Fifteen Python tests passed: `python3 -B -m unittest discover -s tests/unit -p 'test_*.py' -v`, raw log `rejection-status-python-20261114.log`.
- Exact run commands/source/binary hashes remain in run manifests; source/test/log hashes and outcomes indexed in `results/phase_04/rejection-status-evidence-20261114.json`. No downloads or upstream edits. Phase 4 remains incomplete: canonical TX identity, dual-profile application/provisioning, full schema/provenance, target timing/resources, energy/depletion/lifetime and remaining final pilots/reports are still open. Phase 5/6 implementation has not started.

## Provisioning completeness and static-set activation

- Added eight-byte version/profile/sender/epoch/ready/reserved records and `lab_boot_gate_poll_set` in shared production C. It validates the complete preinitialized set before copying keys/activating contexts, consumes the grant on validation failure and locks the whole set. Root no longer activates remaining senders without checking the complete set. Sensor uses the same function for its single static context. Legitimate all-zero keys are accepted when metadata is valid.
- Runner checks key/metadata symbol sizes, writes all records and keys, then publishes the fixed-byte grant. Host tests exercise incomplete second-slot rejection with neither context activated, consumed-grant refusal, and valid all-zero key activation. Pinned-container `scripts/test_phase4_ascon.sh` exited 0; all 1,089 vectors and packet tests pass in `results/phase_04/provision-set-host-20261114.log`, with unique binaries under `unit/ref-pmy0NXjR`.
- First actual Z1 B2 run `20261113T202559430948Z-B2-2` failed because Nashorn does not implement Array.fill. Error and full raw logs remain preserved. Replaced fill with explicit zero initialization; subsequent `python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --timeout-seconds 300` passed at `20261113T202636104292Z-B2-2`.
- These changes validate provisioning for the currently selected static profile across sender slots. Application-level dual-profile contexts/switching, exhaustive malformed metadata integration, full schema/provenance repair and energy/depletion/lifetime remain pending. No full Phase 4 completion is claimed.
- Native AES regression `python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --timeout-seconds 300` passed at `results/phase_03/20261113T202709373776Z-B1-2`. Both this AES run and the corrected Z1 Ascon run delivered 48/48 authenticated readings. Commands and per-run hashes are in their manifests; the new source/log/manifest index is `results/phase_04/provision-set-evidence-20261114.json`.

## Resolution-plan implementation: portable grant and protected Z1 network

- Implemented the boot ABI repair from R2: mailbox is now four explicit bytes (42 54 47 31), consumed/cleared by shared C code. Sensor/root use `lab_boot_grant_pending`; simulator provisioning checks symbol size and writes a byte array. Updated existing Phase 3 boot/reset scenario helpers and host grant fixtures to the same contract. This fixes native-int width dependence, not yet complete provisioning metadata/all-context validation.
- Centralized application/KAT Ascon source selection in `firmware/crypto/ascon-backend.mk`. KAT helper now defaults to reference, honors backend on native/Z1 and cleans before build. Host Ascon script acquires the shared lock itself and creates unique backend-specific output directories; callers must no longer wrap it in a second flock on the same path. Reference corpus/packet tests, including partial/repeated grant cases, passed in `resolution-host-20261114.log` (exit 0, output `unit/ref-Bc94ZIPT`).
- Added `host/scenario_target.py` for Z1 XML adaptation and explicit target/backend/seed selection to the existing runner. Target-specific clean/build/collection and selected-backend hashes are recorded; shared make includes are hashed too. The Z1 optimized combination is rejected because it has not passed mote validation. Ascon pin and clean working tree are checked. Command/container identity is persisted before launch. Binary archival requires a run-specific successful-clean marker to prevent copying stale previous-run outputs when launch/clean fails. Broader early-preparation failure finalization remains pending.
- Actual `python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --timeout-seconds 300` passed at `20261113T201854256422Z-B2-2`: 48 generated/48 uniquely authenticated delivered, 48 submissions, no captured fragmentation. This is protected network functionality on emulation, not a timing/energy or runtime stack qualification.
- Enabled protected Phase 4 attack/root-reset CLI paths. Actual Z1 B2 `--attack-test` passed at `20261113T201950433776Z-B2-2`: 7 injections/7 receiver rejections; 47 authenticated deliveries and one intentional pre-UDP omission. This is not a radio-loss result.
- Root replacement runs at `20261113T202025520403Z-B2-2` and `20261113T202112863904Z-B2-2` failed the existing assertion: no traffic reached the locked root after replacement. The second used new `--readings 120` to investigate recovery duration. Both failures remain intact; duration alone did not close the test.
- Added an explicit security-purpose `RESET_PROBE`: sensor 2 replays its captured first authenticated packet to the root's link-local address periodically, bypassing RPL recovery for this direct-neighbor root+2 scenario. It is compiled only for root-reset tests and logged separately from ordinary submissions. Parser/metrics reject probes outside the declared test purpose. This is a controlled reset/replay test, not a general multi-hop recovery test.
- Actual Z1 B2 `--root-reset-test` then passed at `20261113T202230174156Z-B2-2`. Root receives valid traffic before replacement, refuses a second grant, accepts no readings after reset and logs rejections after reset. Raw probes and radio capture establish that traffic reaches the locked root. Fourteen Python tests pass in `resolution-python-final2-20261114.log`.
- No new downloads/packages or upstream changes. R1–R5 remain partially implemented: all-context metadata/atomic activation, schema migration, full source freezing/failure provenance, target memory/timing, broader integration and comparison tooling still need work. R6/R7 energy/depletion and remaining R8 pilots/reports are pending. Original failures and historical results are preserved.
- Backward compatibility check: `python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --timeout-seconds 300` passed at `results/phase_03/20261113T202303602395Z-B1-2`. Final execution commands, outcomes and source/log/manifest hashes are indexed in `results/phase_04/resolution-implementation-20261114.json`; the Phase 4 evidence ledger links this partial repair evidence.

## Target investigation, mote vectors and completion-marker fixes

- Added explicit `ASCON_IMPL` selection for `ref` and the pinned official `opt32_lowsize` sources, without upstream edits. Reference remains the default; no target automatically selects the optimized backend. Extended the existing host script to test either backend. `env ASCON_IMPL=opt32_lowsize bash scripts/test_phase4_ascon.sh` passed under the pinned container (exit 0), including all 1,089 vectors and packet tests; raw log `opt32-validation-20261114.log`.
- Clean Sky optimized build failed (exit 2): ROM overflow 3696 bytes (`sky-opt32-build-20261114.log`), versus the earlier reference overflow 4136 bytes. Do not label this resource failure resolved on Sky.
- Z1 optimized full sensor build succeeded (exit 0), text/data/BSS 51016/354/6144 (`z1-opt32-build-20261114.log`). Its actual mote KAT subsequently failed; host vectors are insufficient to certify this embedded backend. Exact cause remains unresolved and this backend is not selected by default.
- Added production-wrapper mote fixture `firmware/security_test/ascon_kat.c`, using official corpus Count 1 (empty) and Count 35 (nonempty plaintext/AAD), encryption/decryption and bad-tag output-isolation checks. `scripts/phase4_kat_scenario.py` supports native and Z1 scenarios. The first Z1 scenario failed to load because it retained native-only interface configurations; removed those from the Z1 generation path, retaining the failure under `z1_kat_01`. The corrected optimized test failed under `z1_kat_02`.
- A clean reference-backend Z1 test passed with `PHASE4_KAT_PASS`, TEST OK at simulator time 1763349 us in `z1_kat_ref_01/COOJA.testlog` (exit 0). Clean full sensor reference build also passed, text/data/BSS 51498/354/6144 (`z1-ref-build-20261114.log`, exit 0). These establish limited emulated KAT/resource feasibility, not timing fidelity, embedded stack safety or full-network compatibility.
- All target commands ran via the pinned official image, project/upstream bind mounts and `flock results/phase_02/.runner.lock`; `make -j1` was used. Sensor build commands were `make -C firmware/sensor TARGET=<sky|z1> clean`, `make -C firmware/sensor -j1 TARGET=<sky|z1> ASCON_IMPL=<ref|opt32_lowsize>`, followed on success by `msp430-size`. Mote commands are retained in each scenario's commands element; the Cooja console logs retain builds/errors. Full test artifacts and compiled reference Z1 binaries are archived with hashes in `results/phase_04/target-validation-20261114/manifest.json`.
- Fixed new Phase 4 completion capture to emit/require `PHASE4_COMPLETE`; legacy Phase 2/3 parsing retains its old marker. Added parser regression: 14 Python tests pass in `python-marker-20261114.log`. Runner now archives generated-conf.h per run and includes Makefiles in source hashes. Native `python3 host/run_experiment.py --phase 4 --mode B2 --clients 2` passed at `20261113T192229285407Z-B2-2`. An earlier overlapping invocation was rejected by the shared lock while the Z1 build held it; no concurrent experiment started.
- No downloads or system packages were needed. Phase 4 remains incomplete: full provisioning/context validation, broader security integration, target network/timing/stack validation, energy model/arithmetic, depletion/forwarding proof, remaining pilots and final reports are open. Optimized-backend emulation failure is preserved rather than hidden.

## Static protected application integration and actual Cooja pilot

- Wired the official reference Ascon backend into the existing application build. Sensor/root now select protected handling explicitly for profiles 1 and 2 and initialize the selected security context through the profile-aware API. Unsupported compile-time profiles fail. This is static single-profile provisioning; complete multi-profile/atomic provisioning acceptance remains pending.
- Added `configs/phase4.json` and explicit Phase 4 mode/profile selection in the existing runner. `--phase 4 --mode all` runs B1/B2/B4/B5 serially with the shared lock; Phase 4 paths no longer derive from cipher identity. Parser/metrics accept only registry values 0/1/2 and label authenticated Ascon correctly. Added an Ascon/unknown-profile metric regression; 13 Python tests passed in `results/phase_04/python-integration-20261114.log`.
- Actual `python3 host/run_experiment.py --phase 4 --mode B2 --clients 2` passed at `20261113T191215343758Z-B2-2`. The preceding sandbox failure is preserved at `20261113T191207738040Z-B2-2`.
- Actual `python3 host/run_experiment.py --phase 4 --mode all --clients 2` passed for B1 `20261113T191238979956Z`, B2 `20261113T191257304270Z`, B4 `20261113T191315558502Z`, B5 `20261113T191333489468Z`. All arms generated/delivered 48 authenticated readings; submissions were 48/48/16/16. Exact global generation traces matched across all four arms; radio validation found no fragmentation. Full run directories include mode/client suffixes and preserved commands, raw logs, binaries, hashes and summaries. This is one native functional engineering pilot, not an energy result.
- Added dependency-source/license/KAT hash capture for subsequent Phase 4 manifests. This metadata addition occurred after the four-arm process had loaded its runner code; those existing manifests retain their original metadata and are not relabelled as having that added capture.
- Ran the pinned official container with `flock results/phase_02/.runner.lock make -C firmware/sensor -j1 TARGET=sky`. Exit 2: linker reports ROM overflow by 4136 bytes, followed by relocation truncation errors. Full output is `results/phase_04/sky-feasibility-20261114.log`; no emulated timing or energy acceptance is claimed. Backend/resource investigation remains required.
- Evidence ledger updated with actual pilot paths and artifact hashes. Multi-profile provisioning, representative mote KATs, comprehensive resets/negatives, target feasibility, energy/depletion, larger/repeated pilots and final reports remain open.

## Contract and evidence ledger continuation

- Drafted `docs/phase4-security-contract.md` from the Phase 4 plans to make the intended profile, nonce, boot, replay and telemetry boundaries explicit. It describes a target and does not claim that application integration exists.
- Created `results/phase_04/phase4-evidence.json` as an in-progress gate ledger. Existing host logs are identified as host evidence only; P4.0 and P4.1 remain in progress and all later gates remain pending. No new test or build was run for these documentation changes.

## Profile return host regression

- Extended `tests/security/test_ascon_packet.c` to exercise separate AES and Ascon keys and contexts through AES → Ascon → AES, asserting retained counter and replay state. Test SHA-256 `3bd2f2a1658567bc0886daa42442b952e14bd87b1507f19b5c5a565bf97b65e7`.
- Ran the pinned container command from the Ascon host script. The sandbox attempt failed with `sg: setgid() failed: Invalid argument` (exit 1), retained in `results/phase_04/ascon-profile-return-20261114.log`. Authorized retry exited 0, with the vector and packet checks in `results/phase_04/ascon-profile-return-approved-20261114.log` (SHA-256 `9e195e245dcc3813795ad011eaa7ff700470f6407cf3f3c7b6af38f0a9f492d2`). This tests independent host contexts, not application-level switching or Cooja integration.

## Resume verification — 14 November 2026

- Verified authoritative plan SHA-256 values against the saved plan. Contiki, Cooja and ascon-c HEADs match the handoff pins; ascon-c working tree is clean. Project files remain untracked, so source hashes rather than a project revision are needed for provenance.
- Retried the handoff's pinned-container `scripts/test_phase4_ascon.sh` command. The sandboxed attempt exited 1 with `sg: setgid() failed: Invalid argument`, preserved in `results/phase_04/ascon-resume-20261114.log`. The authorized retry exited 0; `results/phase_04/ascon-resume-approved-20261114.log` records the empty KAT, 1,089 official vectors and packet dispatch/isolation/replay passes. Log SHA-256: `9e195e245dcc3813795ad011eaa7ff700470f6407cf3f3c7b6af38f0a9f492d2`.
- Verified upstream LICENSE hash `5537d4d10b76b81b6e8dfd8b644480a4b1efa332fbb0cdb61126c5be781ef7b4` and KAT hash `bbbc34692fe05e5fda0a3b025585622ab3e3747495e5e3655b29aae8c2a4bd33`. This is host evidence only; application integration, on-mote validation, energy, depletion, pilots and human gates remain open.

Status: started; implementation and all Phase 4 gates remain pending.

## Profile-aware boot gate

- Added `lab_boot_gate_init_profile` while retaining the existing AES initializer as a compatibility wrapper. Added host checks for Ascon activation, a consumed grant and rejection of an unsupported profile. This is a single-context building block; multi-profile provisioning and application integration are still pending.
- Ran the pinned official container with `bash /workspace/scripts/test_phase4_ascon.sh`; exit 0. Raw output is `results/phase_04/ascon-boot-gate-20261114.log` (SHA-256 `9e195e245dcc3813795ad011eaa7ff700470f6407cf3f3c7b6af38f0a9f492d2`). Source SHA-256: boot_gate.c `c499ce453a3ee63f1d863e4b1bea99198ce51de275ad840a06b07fdf65db70e1`; boot_gate.h `32a7745c9fd94cd09c34f9367cd92c18b256eade2b5ef5e8ddd6307131e1abac`; test `924a89a1d550b911dc2c45965a2348bec778ece204cef1c5b0205ec5f28b8cec`; script `7a71a8cda49f39bd3234571dc46c23cb64725bd55b0afffc1b0ffe1643a00751`.

## Initial baseline and dependency

- Re-read AGENTS.md, the authoritative plans, phase index and temporary Phase 4 plan. Both authoritative plan hashes match the saved Phase 4 plan.
- Ran `git clone https://github.com/ascon/ascon-c.git external/ascon-c` after workspace/network approval. Clone completed successfully; checked-out commit is `446347f21b209f3921c65ece70027c366cbe1693`, checkout size reported by `du -sh` is 25M. This is a project-local upstream checkout, not a system package.
- The reference backend, exact vector provenance and license still require verification and recorded hashes. No Phase 4 build or test has run; no Ascon integration, energy model or lifetime result is claimed.
- A host check `ls /usr/bin/*gcc*` found no matching host GCC; toolchains in the existing official container have not yet been checked for the selected emulated target. This does not establish that an additional install is required.
- Inherited Phase 3 end-to-end and human review gaps remain open. Preserve all historical results and all contents of phase_jouney/tmp.

## Initial Ascon adapter and host check

- The pinned container reports /usr/bin/gcc, /usr/local/bin/msp430-gcc and /usr/local/bin/arm-none-eabi-gcc. The initial sandboxed Docker-group attempt failed with setgid invalid argument; the authorized container check succeeded. No compiler installation was needed for this check.
- The downloaded standardized asconaead128 reference API declares 16-byte key, nonce and tag and no overlapping buffers. Source commit: 446347f21b209f3921c65ece70027c366cbe1693. LICENSE SHA-256: 5537d4d10b76b81b6e8dfd8b644480a4b1efa332fbb0cdb61126c5be781ef7b4. Matching LWC_AEAD_KAT_128_128.txt SHA-256: bbbc34692fe05e5fda0a3b025585622ab3e3747495e5e3655b29aae8c2a4bd33.
- Added firmware/crypto/ascon_aead.c/.h, tests/security/test_ascon_aead.c and scripts/test_phase4_ascon.sh. The bounded wrapper uses separate scratch buffers and commits decrypted output only on successful authentication. It is not yet connected to the application.
- Ran `sg docker -c 'docker run --rm --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/test_phase4_ascon.sh'`. Output: `Ascon official empty KAT, roundtrip, bad tag isolation and bounds: PASS`. The script compiles with address/undefined sanitizers. This is one host vector, not full KAT coverage or Cooja evidence.
- An initial source inspection attempted to open nonexistent ref/crypto_aead.c; the actual reference implementation is ref/aead.c. No source changes to upstream were made.
- Remaining: full official vector corpus, adversarial edge cases, secure packet/profile integration, Cooja tests, energy and lifetime, reproducible logs/hashes and all Phase 4 gates.

## Full host vector corpus

- Added tests/security/test_ascon_vectors.c and extended scripts/test_phase4_ascon.sh to read the official pinned vector file and exercise the production wrapper for both encryption and decryption. It requires all 1,089 entries and rejects malformed/incomplete input.
- Re-ran the exact authorized container command above. The process exited 0 and printed `PASS: 1089 official Ascon-AEAD128 vectors, seal and open`; the existing empty-vector, roundtrip, bad-tag isolation and bounds check also passed under ASan/UBSan.
- This supersedes only the earlier missing-host-corpus item. On-mote vectors, broader negative cases, secure packet/profile integration, energy/lifetime and all Phase 4 completion gates remain pending.

## Profile-aware secure packet host integration

- Extended firmware/crypto/secure_packet.c/.h with a per-context profile and explicit initializer. Legacy initialization remains AES profile 1. When LAB_ENABLE_ASCON is defined, profile 2 selects the Ascon adapter and its 16-byte nonce uses the Phase 4 planned RSL/profile/direction/sender/epoch/counter/zero encoding; AES retains its original 13-byte nonce. Unsupported profiles start invalid.
- Added tests/security/test_ascon_packet.c and extended scripts/test_phase4_ascon.sh. Actual pinned-container execution exited 0: 1,089 upstream vectors and Ascon secure-packet dispatch, profile mismatch, bad-tag output isolation and replay checks passed with ASan/UBSan.
- Ran the existing scripts/test_phase3_crypto.sh in the pinned container after the change: AES NIST vectors, negative adapter checks and secure packet authentication/replay/lock checks passed; exit 0.
- These are host-level tests. Application boot/provisioning, sensor/root, runner, on-mote validation, energy and lifetime remain unfinished. No Phase 4 gate or research result is claimed.


## 17 November — items 1–3 closure

Deadline harness and dashboard/evidence repairs pass 108 production-C/Python tests in the pinned container. Final-source Z1 calibration completed **six cells for 3 nodes and six for 9 nodes**, independently. Both schema-v1 tables qualify; **144 artifact/binary hashes matched**. Point-estimate B6 selection is Ascon for 3 nodes, AES for 9 nodes; n=1/cell, no superiority claim. Required cap-2 measurements are present, actual batch occupancy retained, and runtime/source/model/dependency compatibility enforced. Actual CLI rejects 3-node-to-9-node transfer before build. Evidence and complete run table: phase_jouney/final2x_phase_01.md and results/phase_05/repairs_17nov/calibration-acceptance.json. Usage: docs/calibration-v1.md.

Earlier source cohorts and failures remain preserved. User deferred items 4–5: no policy/queue firmware repair or adaptive/security/depletion mechanism validation was performed in this package. Browser visual review, full semantic Phase 4 acceptance, human review and independent reproduction remain pending. No corrected-campaign restart or Phase 6 execution. Stopped at this bounded checkpoint.


## 17 November — authorized items 4–5 bounded mechanism checkpoint

Shared-C policy/queue safety, measured own-generation rate, cap-shrink chunking, initial-event capture and uniform Z1 125-ms flush-lead fixes were implemented. **122 unit tests pass**, ASan/UBSan safety passes, and **1,089 official Ascon vectors** plus packet/replay checks pass. Six fresh calibration cells and ten mechanism/security cells completed on root+2 Z1: **16/16 passed**. Raw reanalysis checked **44,020 events / 190 artifact+binary hashes**.

Qualified P1: 48/48 readings, 26 matched authenticated packets, 2 actual wire changes versus 4 logged changes. Frozen 4.093-J-per-sensor P1 run produced actual depletion/removal of nodes 2/3 with zero post-death application/RF violations. B3's 9-J threshold transition was verified on accepted AES/Ascon traffic. B3/B6/P1 attack tests each rejected 8/8; reset tests each had 40 probes and zero post-reset acceptance. Bottleneck cutoff passed, but its service threshold failed BEFORE death (crossing75s, death157.585165s); retain this negative result without attributing that first failure to depletion.

Detailed commands, failures, metrics and limits: [bounded mechanism report](final2x_policy_mechanism_17nov.md); evidence `results/phase_05/mechanism_17nov/`. Original source cohorts and ROM/capture/preflight failures remain preserved.

**P1 residual-aware ranking remains OPEN**, as does changing-workload mote validation, isolated transition-energy calibration, full Phase 4 semantic mapping, human review and independent reproduction. Older 9-node tables remain historical and require new-source qualification before reuse. This bounded checkpoint does not close the full 2X phase. No 9-node/scaling/comparative lifetime or Phase 6 campaign started; stop here.

## 20 November — finalPLAN2X evidence mapping

Mapped all 35 archived cases, verified 685 artifact and binary hashes, and replayed 62 runs. All checked summary fields matched. Four fresh root+2 Z1 static controls each authenticated 48/48 readings. Historical source drift and the current-source coverage limits are recorded in the [2X Phase 3 evidence checkpoint](final2x_phase_03_evidence_20261120.md).

## 20 November — targeted measurement and boundary reruns

The two Z1 measurement controls and the three native Cooja boundary groups passed on current source. The 14 runs each authenticated 48/48 readings and all 147 indexed hashes matched. The archived matrix retains its original source cohorts. [Commands and evidence](final2x_z1_transition_and_review_20261120.md#targeted-current-source-phase-4-reruns)

## Current-source forwarding cutoff replay

The 125 ms and 250 ms B2/Z1 bottleneck sampler controls passed. Production-C reconciliation matched the final terminal totals. Node 3's parent was node 2 before depletion, and 38 authenticated readings from node 3 arrived before the cutoff and zero after it in both runs. [Raw replay and source cohorts](final2x_z1_ranking_diagnosis_20261120.md#current-source-phase-4-sampling-and-cutoff)
