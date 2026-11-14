# Copy/paste prompt for the next AI IDE

Workspace: `/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT`
Handoff date: 14 November 2026. This snapshot describes partially completed Phase 4. Verify drift before editing. This prompt does not certify the code or pass any gate.

You are continuing an existing software-only Contiki-NG/Cooja research project. Read the actual documents and source deeply, reconcile conflicting historical statuses, then complete the remaining authorized **Phase 4** implementation and evidence. Do not restart completed modules or substitute another planning-only turn for implementation. Phase 5/6 remain planned; complete Phase 4 reports and respect the phase boundary before starting them.

## 1. Mandatory reading order — read files completely

1. `AGENTS.md`.
2. `PLANS/MASTER_IMPLEMENTATION_PLAN.md` — authoritative research scope, architecture, baseline definitions, energy/lifetime requirements, statistics, G0–G6 and calendar.
3. `PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md` — authoritative companion, especially correctness decisions, module reuse and W6–W9.
4. `PLANS/README.md` and `phase_jouney/README.md` — planning versus execution navigation.
5. `phase_4_5_6.md` — consolidated roadmap; read all sections, especially F4.1–F4.8, Section10's M01–M25/A01–A08 audit and later implementation updates. Its initial inventory is older than the latest journal/source.
6. `PLANS/PHASE_04_IMPLEMENTATION_PLAN.md` and `PLANS/PHASE_04_PROBLEM_RESOLUTION_PLAN.md` — detailed P4.0–P4.7/R1–R8 acceptance requirements; inventories are partly historical.
7. Every preserved root `tmp/` plan: `phase_02_implementation_plan.md`, `phase_03_implementation_plan.md`, `phase_04_implementation_plan.md`, `phase_04_synced_completion_plan.md`.
8. `phase_jouney/phase_04_environment_and_implementation.md` **from the top**. New checkpoints were prepended; reading only its tail shows obsolete “not implemented” entries.
9. All Phase1–3 journals/reports:
   - `phase_jouney/phase_01_environment.md`
   - `phase_jouney/phase_01_downloads_problems_and_resolutions.md`
   - `phase_jouney/phase_02_environment_and_implementation.md`
   - `phase_jouney/phase_02_detailed_report.md`
   - `phase_jouney/phase_03_environment_and_implementation.md`
   - `phase_jouney/phase_03_detailed_report.md`
   - `phase_jouney/phase_03_downloads_problems_and_resolutions.md`
10. Every technical document in `docs/`: `architecture.md`, `protocol.md`, `threat-model.md`, `phase3-security-contract.md`, `phase4-security-contract.md`, `power-model.md`, `phase4-experiment-protocol.md`, all `phase*-usage.md`, `setup-linux.md`, `CODEX_HANDOFF_AND_RESUME.md`, `DIRECTORY_AUDIT_AND_CLEANUP_PROPOSAL.md`. The old handoff/audit are historical snapshots, not current implementation inventory or cleanup authorization.
11. Actual source/tests/configs/scenarios and raw evidence below. Read complete relevant functions and their callers, not only keyword matches.

The user moved historical plans to **root `tmp/`**. Some old links still assume `phase_jouney/tmp/`; resolve those links to the real files. Never move plans back or delete their contents. Do not confuse the master document's broad “Phase1 playbook” title with execution phases1–6 in the journey.

## 2. Non-negotiable collaboration/evidence rules

- Preserve both original authoritative plans byte-for-byte. Master SHA256: `2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385`; decision-review SHA256: `69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a`.
- N0 is unprotected. No placeholder crypto, invented logs/results/energy gains, automatic human approval or physical-battery claims.
- Custom production code belongs under `firmware/` and `host/`; reuse pinned networking/crypto. Do not edit upstream core.
- Approximately4GB RAM: serial `-j1` builds and simulations. All generated config/build writers share `results/phase_02/.runner.lock`.
- Check scripts before wrapping locks: Ascon/energy host-test scripts already acquire that lock; nesting the same lock can deadlock.
- Do not edit source while experiments run. Preserve the source snapshot used by every comparison. Run manifests have source/config/scenario/binary/log hashes; Git historically has no initial commit, so a hash is not a fabricated commit ID.
- Preserve failures and original manifests. New qualification/exclusion metadata must not rewrite old logs into passes or overwrite historical evidence.
- Explain progress in clear Hinglish, distinguish code implemented / tested / comparison eligible / human reviewed. User is frustrated by repeated tiny partial turns and vague “only tests left” statements. Be explicit about remaining code work and test failures; continue routine authorized work without repeatedly requesting design permission.
- Docker/network sandbox permissions may still require environment approval. Do not bypass them or loosen Docker socket permissions.

## 3. Phase-wise actual status

| Phase | Existing work | Remaining qualification |
|---|---|---|
| 1 | Pinned environment, unchanged official root+8 tutorial, smoke automation | Two-student G0 manual review and independent reproduction pending |
| 2 | Shared reading codec, deterministic generator, aggregation, N0 network/pilot and pipeline | Retain regressions; N0 never becomes authenticated evidence |
| 3 | AES wrapper/envelope, replay/nonce/reset controls, native secure pilot and reports | Human review and expanded inherited checks; later shared changes need regression |
| 4 | Substantial implementation described below | **Incomplete**: remaining contracts/error paths, final affected matrices, measurement audit, final reports/figures/gates |
| 5 | B3/B6/P1/calibration/ablations planned | Not implemented |
| 6 | Research matrix/statistics/reproducibility/release planned | Not implemented |

Neither “everything remains unimplemented” nor “Phase4 complete, only testing left” accurately describes the current tree.

## 4. Current implementation map — inspect these files

- `firmware/common/protocol.*`: shared explicit codec and reading dedup; header11 bytes, reading10 bytes, capacity4.
- `firmware/aggregate/aggregate.*`: bounded queue, count/byte/oldest-deadline and build/commit semantics.
- `firmware/crypto/aes_ccm.*`, `ascon_aead.*`, `secure_packet.*`, `boot_gate.*`, `aes-backend.mk`, `ascon-backend.mk`.
- `firmware/sensor/sensor.c`, `firmware/root/root.c`, shared/app Makefiles and project configs.
- `firmware/energy/energy.*`, `energest_sampler.*`: checked integer energy, fractional carry, raw sampling, model totals, terminal state and one-time shutdown accounting.
- `firmware/security_test/crypto_kat.c`, `ascon_kat.c`, boot/reset fixtures; `scripts/phase4_kat_scenario.py`.
- `host/run_experiment.py`, `scenario_target.py`, `parse_logs.py`, `metrics.py`, `energy_reconcile.c`, `energy_reconcile.py`, `lifetime.py`, `plots.py`, `validate_phase4.py`.
- `configs/phase2.json`, `phase3.json`, `phase4.json`, `power-z1-v1.json`; existing saved scenario under `simulations/scenarios/`.
- All `tests/unit/` and `tests/security/`; `scripts/test_phase4_ascon.sh`, `test_phase4_energy.sh`, legacy tests and smoke scripts.

Implemented Phase4 features include:

1. Reference standardized Ascon and host official1089-vector suite; independent AES/Ascon keys and retained per-profile contexts; bounded root lookup and shared per-sender reading dedup.
2. Compact provisioning tables, explicit byte mailbox/slot metadata, whole-set validation before activation, one-use simulator grant outside mote RAM.
3. Actual TX identity from sealed header, verified RX identity, separate accepted-packet events; schema2 config identity and exact completion marker; packet PDR distinct from reading PDR.
4. Rejection status categories, correctly authenticated malformed-body fixture, critical flush, actual packet receive reordering, actual radio-medium loss/recovery, root/sensor reset and provisioning-fault fixtures.
5. Sourced component power config, official Energest snapshots, shared production-C host reconciliation, component conservation, CPU-current sensitivity, stack telemetry and controlled idle/CPU-work fixtures.
6. Model budget exhaustion, queue DROP70/context locking, MAC/radio-off, simulator removal/REMOVED evidence, actual-versus-planned demand, lifetime events/censoring.
7. Four-arm plotter, serial acceptance driver, attempt records/preparation diagnostics, control registry checks and source-drift detection.

These are implemented paths, not a blanket claim that all acceptance rows passed on the latest source.

## 5. Critical discovered errors, fixes and evidence limits

### A. Z1 ninth mote / resource fit

Z1 default source-route graph has8 entries, but the pinned graph stores the root too. Root+8 needs9. An initial root-local config edit was not selected by the include path; `results/phase_04/z1-route-config-inspection.log` proved the actual value remained8. Shared `firmware/project-conf.h` now sets `NETSTACK_MAX_ROUTE_ENTRIES=LAB_LAST_NODE`. Provisioning also no longer allocates unused sender slots. Phase4 packet queues are explicitly4 across controls to improve RAM fit.

Old static RAM headroom figures (696 bytes at root before compaction/queue changes) are historical. Inspect current binary sizes and official stack-check logs. The stack guard requires128 bytes remaining, but the official fill checker has documented limits for unwritten reserved frames; observed workloads are not universal stack safety.

### B. Z1 default hardware AES was not a valid secure backend

The pinned MSPSim `CC2420.java` strobe dispatcher has no SAES implementation. The first security matrix accepted the wrong-key fixture under the default Z1 hardware AES path, including reading2147483647/counter6.

- Interrupted matrix: `results/phase_04/validation-20261114T061839506081Z/manifest.json` (`interrupted_for_backend_fix`).
- Shared `firmware/crypto/aes-backend.mk` now explicitly selects vetted Contiki `aes_128_driver` for application and KAT builds.
- Official software-backend Z1 KAT: `results/phase_04/z1-software-aes-kat/`.
- Exact formerly failing attack case then passed: `results/phase_04/20261114T063051801657Z-B1-2/manifest.json`.

**Exclude old Z1 application runs without the software AES selection from secure-comparison qualification**, including dual-profile apps with that allowed hardware AES capability. Preserve their raw evidence. Native software AES and direct reference Ascon primitive KATs retain their narrower scopes. See `closure-progress-20261114.json` for concrete exclusion paths.

The current AES mote fixture was subsequently extended with the official empty-plaintext vector. The earlier KAT log does not prove that later-added case: refresh the expanded KAT and preserve new outputs.

Sky remains ROM-infeasible; optimized Ascon passed host vectors but failed a Z1 mote KAT. Keep that combination excluded; validated reference is the intended path.

### C. Batching deadline failure and actual fix

The restarted matrix failed static seed123456 B4: node4 reported hold3015ms against3000ms.

- Matrix: `results/phase_04/validation-20261114T063559727572Z/manifest.json` (`interrupted_for_deadline_fix`,25 recorded cases; not an all-pass35-group matrix).
- Exact failed run: `results/phase_04/20261114T065725646751Z-B4-8/`.
- Current sender has125ms early flush lead for emulated Phase4, zero lead for native, and DROP71 for readings already expired when serviced. Validation still enforces the original3000ms bound.
- Exact failing-case repeat passed: `results/phase_04/20261114T070425862495Z-B4-8/manifest.json`, max hold3000ms.

Affected paired/static/boundary/lifetime groups still need complete reruns. Do not loosen bounds or relabel the failed group as successful.

### D. Sensor-reset proof was tightened

The initial fixture reset after local TX submission and did not establish authenticated root receipt beforehand. It is superseded for that broader requirement. Current harness waits for root RX2 from sender2 before replacing sensor2, and metrics require that control plus no protected activity after the second boot.

- Tightened B1/Z1 case passed: `results/phase_04/20261114T070903748685Z-B1-2/manifest.json`.
- Tightened B2 repeat remains to be checked/executed.

### E. Energy/depletion scope

Read `docs/power-model.md` and `docs/phase4-experiment-protocol.md` completely. Model is MCU+radio estimate, not whole-board measurement. The selected no-DMA configuration and DCO/deep-state guards resolve the mixed-LPM issue only for this build. CPU current is an explicitly approximate datasheet-curve reading with sensitivity.

Initial Ascon depletion fixture `results/phase_04/20261114T055834736669Z-B2-2/` demonstrated terminal forwarder removal, but its service failure began before death; do not claim that death caused that first crossing. Later source adds atomic snapshots, one-time final close, richer reconciliation and longer-warm-up lifetime fixtures; full latest-source terminal/sampling/lifetime matrices remain pending.

`model_validated` in existing summaries denotes accounting under the model assumptions, not physical calibration. Review units, component separation, timer wrap, final observation boundary, zero-delivery handling, survivor completion and missing-terminal failure behavior.

## 6. Execution/evidence files to inspect

Read these JSON records and follow references to actual manifests, commands, config, binaries and raw logs:

- `results/setup/source-pins.json`
- `results/phase_01/evidence.json`
- `results/phase_02/phase2-evidence.json`
- `results/phase_03/phase3-evidence.json`
- `results/phase_04/phase4-evidence.json`
- `results/phase_04/closure-progress-20261114.json`
- `results/phase_04/dual-schema-energy-evidence-20261114.json`
- `results/phase_04/rejection-status-evidence-20261114.json`
- Both interrupted `validation-*/manifest.json` records above and their per-case logs.
- `results/phase_04/validation-20261114T063559727572Z/source-snapshot/` and its `hashes.json`:45 custom source/config files used by that frozen run. Generated headers are archived per run.
- `results/phase_04/energy-close-tests.log`, `final-source-python-tests.log`, crypto/vector and earlier target-validation logs.

Recorded Python suite reached21 passing tests before the latest deadline/reset changes. That is saved evidence, not a fresh current-source test. Refresh relevant suites. Sanitizer close tests passed; final mote close validation still needs its actual run. Older evidence indexes may lag the latest code: repair coverage/navigation, not historical raw results.

Pins to verify against actual checkouts:

- Contiki `a304687372e2917d325d4d71cf68610fe9a6279b`
- Cooja `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4`
- Ascon `446347f21b209f3921c65ece70027c366cbe1693`
- Official image `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`

## 7. First resume actions and remaining work

1. Establish single-writer ownership. Previous tool calls were interrupted deliberately. Check actual host processes, Docker containers, runner lock and latest manifests before any edit/build. Sandbox `ps` may not expose host processes; do not assume an empty sandbox process list proves nothing is running. Do not kill arbitrary PIDs from old `/tmp/` notes. Stop only verified owned work, record cleanup and preserve partial runs.
2. Verify source/pin/authority hashes and reconcile latest journal versus this snapshot. A nonblocking lock probe succeeded while this prompt was prepared, and no newer validation directory was observed; that is not a full host-process audit.
3. Audit and finish remaining Phase4 code contracts: explicit runtime schema fields/validation, model/config validation, lifecycle/failure/finalization paths, lifetime terminal/cohort edge cases and analysis/plot eligibility. Do not claim only tests remain without inspecting these gaps.
4. Refresh expanded AES/Ascon mote KATs on selected backends; refresh shared-C/Python suites, tightened B2 sensor-reset proof, affected critical/deadline cases and legacy N0/AES regressions. Use unique outputs and the shared lock.
5. Complete post-fix static paired groups (four arms × three seeds), boundary groups and declared lifetime/sample-sensitivity runs. Check `validate_phase4.py` before launching it: it runs serially, is substantial, and continues to retain individual failures. Start with the first unmet/affected row rather than blindly repeating every previously valid case.
6. Validate actual idle/load behavior, CPU/radio time consistency, accounting/logging overhead, model sensitivity, stack margins, final shutdown accounting, bottleneck path/cutoff and honest censoring. Do not equate mere scenario exit0 with every measurement gate.
7. Generate charts only from eligible validated groups; retain source manifests. Keep exact native GEN matching; the explicitly declared Z1 engineering contract permits at most125ms timing variation and records observed jitter. Lifetime compares prospective demand/live prefixes, not impossible post-death GEN equality. Do not widen these limits after a failure to obtain PASS.
8. Verify every required P4/R/A acceptance row; regenerate/reconcile evidence with exact producer/source identities. Keep unrelated/historical data and source snapshots intact. A later fix may require affected reruns, not fabricated qualification of old runs.
9. Produce `phase_jouney/phase_04_detailed_report.md`, `phase_04_downloads_problems_and_resolutions.md`, current usage/security/power/protocol docs, updated phase index/handoff and an honest requirement-to-evidence ledger. Human G0/review/reproduction stays pending until actually performed.
10. Declare Phase4 automated completion only if mandatory requirements actually pass. Otherwise record the exact remaining code/gate/blocker. Stop before Phase5 implementation and wait at the required boundary.

Existing example commands — read source/config first; do not treat these lines as executed evidence:

```bash
python3 host/run_experiment.py --phase 4 --mode B1 --clients 2 --target z1 --sensor-reset-test --timeout-seconds 300
python3 host/run_experiment.py --phase 4 --mode B4 --clients 8 --target z1 --power-model --seed 123456 --timeout-seconds 300
python3 host/validate_phase4.py --section static
python3 host/validate_phase4.py --section boundaries
python3 host/validate_phase4.py --section lifetime
```

Do not launch all commands simultaneously. The most recent attempted static-matrix launch was interrupted at the tool level; verify whether it actually started before proceeding.

## 8. What Phase5/6 will eventually require

Phase5: real B3 threshold selection, B6 adaptive aggregation, P1 cost-aware joint policy, separate calibration, local feature availability, secure fallback, hysteresis/dwell/transition costs and ablations. No free root PDR oracle or unmeasured feedback. None is implemented merely by the controlled profile-return test.

Phase6: larger grid/bottleneck networks, bounded context/dimension scaling beyond current8 clients/16 root contexts, frozen seeds/protocol, run-level paired statistics, uncertainty/censoring, independent clean reproduction, charts/demo/release/manuscript. The master10-node pilot differs from the existing9-node demo. Preserve all scope in `phase_4_5_6.md`; do not begin these phases silently while Phase4 remains open.

## 9. Response expected from you

After reading and checking source/evidence, briefly explain current status and the first concrete unmet dependency in Hinglish. Then implement/fix it and proceed through authorized remaining Phase4 work, with periodic factual progress updates. Report changed files, commands, actual tests/results, failures and exact limits. Never answer “done” from code presence, an old PASS, an interrupted matrix or a generated plan alone.
