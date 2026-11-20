## Follow-up repair implementation

- Dynamic-cap validation now follows per-node POLICY state, checks profile consistency and retains static limits. Protected two-reading POLICY→TX fixture passes; lowering the policy cap rejects it. 19 metrics host tests pass; log: results/priority_repairs/followup/metrics.log. An initial fixture failed because its RX profile identity did not match TX; corrected the fixture to protected AES with explicit context/authentication events.
- Added pre-generation policy integer/range/threshold/cost-shape validation; imported calibration run IDs, manifest/summary hashes, status and seed are checked. Full target/model compatibility of imported tables still needs completion; current status explicitly says compatibility pending.
- Missing costs/default calibration are explicitly qualified in resolved config. Existing safe fallback remains. No new calibration run performed.
- Shared comparison guard rejects mixed source/config cohorts and repeated mode/seed cells for analysis/plots. Figure/analysis source hashes and missing-pair counts recorded. Dedicated negative fixtures for the new shared guard remain needed.
- Added POLICY_TIME rtimer telemetry around decision and application; parser/summary expose time/sample count. It is not an energy measurement and does not separately isolate switching cost. Timing has not been built/validated on the mote; short rtimer interval/wrap assumptions remain to verify when phase validation is authorized.
- GUI desktop inspection: Wayland/KWin, no open Cooja window. Added software-rendering JVM flags and propagate nonzero GUI exit. Blank-window resolution remains unverified; no GUI/simulation launched.
- No Phase 4/5 validation or Phase 6 work executed. Remaining nondeferred closure includes calibration target/model compatibility, guard tests, firmware compile/timing checks and actual GUI verification.

# Priority repair checkpoint — 14 November 2026

User explicitly deferred Phase 4/5 validation and prohibited Phase 6 start. No simulator or phase-validation matrix ran. See [audit checkpoint](../lastAstra%20check.md) for repairs and remaining work.

Commands: `python3 -B -m unittest discover -s tests/unit -p test_policy.py -v` initially failed on host (GCC absent), then passed 19 actual production-C tests inside the pinned official container. `python3 -B -m unittest discover -s tests/unit -p test_priority_repairs.py -v` checks calibration seed guard and paired-bootstrap constant difference / unequal-array rejection. Python compilation checks passed. Source hashes and outcomes are recorded in results/priority_repairs/repair-evidence.json. Network/build/resource qualification remains pending; old pilot logs remain unchanged.

# Phase 5 execution journal

## Checkpoint: Phase 5 initial implementation complete — B3/B6/P1 smoke pass

**Date:** 14 November 2026

### What was implemented

**Policy module** (`firmware/policy/policy.c`, `policy.h`):
- Portable C, no heap, no OS calls — same code for host tests and mote firmware
- `lab_policy_b3`: battery-threshold cipher switch (AES above hi threshold, Ascon below lo, hysteresis hold in between), fixed cap=1
- `lab_policy_b6`: fixed cipher from calibration (B2/Ascon won from Phase 4 static pilots), adaptive cap by queue occupancy and deadline
- `lab_policy_p1`: joint cost-aware selection over (profile, cap) action space; respects dwell timer, transition cost and saving margin; falls back to AES cap=1 on missing data
- Safe fallback always returns AES profile=1 cap=1 — never disables authentication

**Sensor integration** (`firmware/sensor/sensor.c`):
- `#if LAB_POLICY_MODE` block: calls B3/B6/P1 policy each service tick before flush
- Updates `selected` profile and `queue.cap` from policy output
- Emits `POLICY` event: profile, cap, reason, residual_nj, oldest_hold_ms, queue_count
- Emits `SWITCH` event when profile or cap changes

**Events** (`firmware/common/events.h`): `LAB_EVENT_POLICY` and `LAB_EVENT_SWITCH` macros added

**project-conf.h**: policy defaults `LAB_POLICY_MODE`, `LAB_B3_THRESHOLD_NJ_HI/LO`, `LAB_B6_PROFILE`, `LAB_P1_*`

**firmware/Makefile**: added `../policy` to `PROJECTDIRS` and `policy.c` to `PROJECT_SOURCEFILES`

**configs/phase5.json**: 7-mode config (B1/B2/B3/B4/B5/B6/P1), calibration seed 223457, b6_profile updated to 2 (Ascon, from calibration)

**host/calibrate.py**: reads Phase 4 static summaries, computes cost table, selects B6 winner, outputs P1 cost array

**Calibration result** (`results/phase_05/cost_table.json`):
- B1 (AES cap1): 247,233,663 nJ/reading (n=5)
- B2 (Ascon cap1): 229,361,705 nJ/reading (n=9) ← B6 winner
- B4 (AES cap4): 243,928,893 nJ/reading (n=4)
- B5 (Ascon cap4): 244,171,890 nJ/reading (n=3)
- B6 winner: **B2 / Ascon profile 2** — lowest energy per delivered reading in Phase 4 static pilots

**host/run_experiment.py**: extended for `--phase 5`, modes B3/B6/P1, `all5`, policy defs in generated-conf.h, schema 2 / PHASE4_SCHEMA2_COMPLETE for phase 5

**host/parse_logs.py**: POLICY and SWITCH event fields added; phase 5 schema 2 accepted

**host/metrics.py**: policy summary (total ticks, switches, switch reasons, profiles/caps used) added to output

**tests/unit/test_policy.py**: 17 tests covering all three policies — B3 hysteresis/thresholds, B6 adaptive cap, P1 cost ranking/dwell/margin/fallback — all pass

### Test results

```
Ran 38 tests in 0.009s — OK  (21 Phase 4 + 17 Phase 5 policy)
```

### Smoke runs (native, 2 clients, seed 123456)

| Mode | Run ID | Status |
|------|--------|--------|
| B3 | 20261114T091850125887Z-B3-2 | passed |
| B6 | 20261114T091919114788Z-B6-2 | passed |
| P1 | 20261114T091937880366Z-P1-2 | passed |

POLICY and SWITCH events confirmed in COOJA.testlog. B3 starts with AES (residual = UINT64_MAX, above hi threshold). B6 uses profile 2 (Ascon, from calibration). P1 selects minimum cost action from cost table.

### Remaining Phase 5 work

- Z1 target runs for B3/B6/P1 with power model (--target z1 --power-model)
- Security regression: B3/B6/P1 attack-test, root-reset-test
- 7-arm root+8 pilot: seeds 123456/123457/123458 (21 runs)
- phase_05_detailed_report.md
- results/phase_05/phase5-evidence.json

Status: initial implementation complete; full pilot runs pending.

## Corrected campaign launched — 16 November 2026

**Date:** 16 November 2026 (this session)

**Policy.c infeasibility fix applied before campaign:** The resolution audit (lastAstra check) identified that P1's dwell/saving checks could retain a now-infeasible batch cap after traffic slowed. Fix: `current_feasible` boolean now tracks whether the current action survived feasibility checks; dwell and saving comparisons only apply when `current_feasible == true`. 20 policy host tests pass in the pinned official container (up from 19; new test: `test_p1_rate_drop_overrides_dwell_and_savings`). Source hash of `firmware/policy/policy.c` changed from `36ab47af...` to `e1289ab7...`.

**Campaign 20261116-fresh invalidated by source drift:** The 21 runs from seed 523456 were produced against the old `policy.c`. Because `run_campaign.py` detects source drift and refuses to resume, those runs form a separate historical record. They remain in `results/campaigns/20261116-fresh/` and `results/phase_05/` unchanged per project preservation rules.

**New campaign 20261116-corrected created:** Same protocol (seeds 523456–523465, groups grid16/tree16/z1-legacy8, 7 modes, 210 total cells) with updated `id: "20261116-corrected"` and a note referencing the replaced campaign. Campaign launched in background; PID 158217.

```bash
python3 host/run_campaign.py results/campaigns/20261116-corrected
```

Campaign is running serially under the shared `.runner.lock`. Estimated completion time ~4 hours (based on 82.6 s mean per run). Progress will be tracked in `results/campaigns/20261116-corrected/state.json`.

**Verified running:** Grid16 (7/7 seed 523456 passed), Tree16 (7/7), Z1-legacy8 started (~130 s/run). No failures in the first 16 cells.

**Limitations carried over from protocol:**
- Native Cooja groups establish network metrics only; no hardware-validated CPU energy.
- B3 uses unbounded residual energy in native functional runs; threshold switching is not exercised.
- P1 has no qualified loaded cost table; it is a fallback diagnostic.
- B6 uses configured Ascon (profile 2 from Phase 4 calibration), not a newly re-qualified winner.
- These limitations are recorded in `protocol.json` and are not evidence of adaptive energy gains.

**Stopping point (per finalPLAN_execute.md §10):** Phase 4/5 closure work is complete. Campaign is running. Human review gate required before Phase 6. Waiting for next user instruction.

## Resolution audit started — 16 November 2026

User authorized proceeding with finalPLAN_execute.md. Historical preservation baseline contains 2,866 files, with original paths, sizes and SHA-256 hashes; see `results/resolution_audit/20261116T175309857770Z`. Existing workspace diff/status preserved.

Found and repaired a constraint bug: P1 could retain a now-infeasible batch cap after traffic slowed because dwell/saving checks held the current action. These checks now apply only when the current action remains feasible. Added a production-C regression for rate reduction during dwell with a prohibitive transition cost. All 20 policy host tests passed in the pinned official container. Initial sandbox sg failure and test/source evidence are recorded in policy-test-evidence.json. This is host correctness evidence, not Cooja adaptation or energy evidence.

Calibration qualification, actual mote validation, depletion track, dashboard redesign and final Phase 5 closure remain pending. Phase 6 has not started.

## 17 November — items 1–3 repair checkpoint

Deadline harness, dashboard correctness/shared evidence checks, and versioned calibration qualification implemented. Final-source unit suite: 108 tests, OK, pinned official container; log results/phase_05/repairs_17nov/tests-acceptance.log. Flask dependencies reused from results/dashboard-deps; earlier missing-Flask failure retained. Five actual dashboard/archive APIs/routes passed in the pinned environment. Final-source 3-node six-cell calibration is complete; separate 9-node calibration was still running at this checkpoint. See phase_jouney/final2x_phase_01.md for scope and results/phase_05/repairs_17nov/ for commands/logs. User explicitly deferred policy/mechanism items 4–5; these and human gates remain pending. No adaptive-policy evaluation, lifetime comparison or Phase 6 run started.


## 17 November — items 1–3 closure

Deadline harness and dashboard/evidence repairs pass 108 production-C/Python tests in the pinned container. Final-source Z1 calibration completed **six cells for 3 nodes and six for 9 nodes**, independently. Both schema-v1 tables qualify; **144 artifact/binary hashes matched**. Point-estimate B6 selection is Ascon for 3 nodes, AES for 9 nodes; n=1/cell, no superiority claim. Required cap-2 measurements are present, actual batch occupancy retained, and runtime/source/model/dependency compatibility enforced. Actual CLI rejects 3-node-to-9-node transfer before build. Evidence and complete run table: phase_jouney/final2x_phase_01.md and results/phase_05/repairs_17nov/calibration-acceptance.json. Usage: docs/calibration-v1.md.

Earlier source cohorts and failures remain preserved. User deferred items 4–5: no policy/queue firmware repair or adaptive/security/depletion mechanism validation was performed in this package. Browser visual review, full semantic Phase 4 acceptance, human review and independent reproduction remain pending. No corrected-campaign restart or Phase 6 execution. Stopped at this bounded checkpoint.


## 17 November — authorized items 4–5 bounded mechanism checkpoint

Shared-C policy/queue safety, measured own-generation rate, cap-shrink chunking, initial-event capture and uniform Z1 125-ms flush-lead fixes were implemented. **122 unit tests pass**, ASan/UBSan safety passes, and **1,089 official Ascon vectors** plus packet/replay checks pass. Six fresh calibration cells and ten mechanism/security cells completed on root+2 Z1: **16/16 passed**. Raw reanalysis checked **44,020 events / 190 artifact+binary hashes**.

Qualified P1: 48/48 readings, 26 matched authenticated packets, 2 actual wire changes versus 4 logged changes. Frozen 4.093-J-per-sensor P1 run produced actual depletion/removal of nodes 2/3 with zero post-death application/RF violations. B3's 9-J threshold transition was verified on accepted AES/Ascon traffic. B3/B6/P1 attack tests each rejected 8/8; reset tests each had 40 probes and zero post-reset acceptance. Bottleneck cutoff passed, but its service threshold failed BEFORE death (crossing75s, death157.585165s); retain this negative result without attributing that first failure to depletion.

Detailed commands, failures, metrics and limits: [bounded mechanism report](final2x_policy_mechanism_17nov.md); evidence `results/phase_05/mechanism_17nov/`. Original source cohorts and ROM/capture/preflight failures remain preserved.

**P1 residual-aware ranking remains OPEN**, as does changing-workload mote validation, isolated transition-energy calibration, full Phase 4 semantic mapping, human review and independent reproduction. Older 9-node tables remain historical and require new-source qualification before reuse. This bounded checkpoint does not close the full 2X phase. No 9-node/scaling/comparative lifetime or Phase 6 campaign started; stop here.


## 20 November 2026 — 9-node Z1 calibration and P1 preflight

Six current-source legacy Z1 static calibration cells passed (AES-CCM and Ascon-AEAD128, caps 1/2/4). Both firmware roles linked in all runs; maximum text+data 54,929 B, maximum data+bss 6,932 B and minimum observed stack headroom 344 B in static paths. The versioned table qualified and the Phase 5 P1 CLI passed preflight with evaluation seed 123456. P1 build and simulation are pending. Commands, failed sandbox attempt, metrics, hashes and evidence are indexed in the [9-node calibration checkpoint](final2x_z1_nine_node_calibration_20261120.md).


## 20 November — 9-node Z1 P1 Stage B

The functional and finite-budget runs passed. Functional P1 authenticated 186/192 readings and matched all 100 packets to sealed TX and active cipher/cap. At a frozen 4.097 J per sensor, all eight bounded nodes depleted and were removed with zero post-death application or RF violations. Finite-budget delivery was 76/88 generated and 76/192 scheduled. The terminal mechanism checkpoint is complete. Stage C comparison and human gates remain pending. [Pilot report and evidence](final2x_z1_nine_node_p1_20261120.md)


## 20 November — 9-node Z1 Stage C

The six controls passed on the frozen seed and finite budget. The saved P1 result was reused. B1 and B2 delivered 90 scheduled readings each compared with 76 for P1 and B6. The comparison, commands, artifact hashes and remaining work are recorded in the [Stage C tracker](z1_stage_c_tracker.md).


## 20 November — changing-traffic Z1 P1

Six fresh calibration cells qualified and the three-mote P1 pilot authenticated 54/54 readings. Both sensors changed from Ascon cap 4 to AES cap 1 and back to Ascon cap 4 at the measured traffic plateaus. Full tests passed (128) and six dashboard routes returned HTTP 200 with pinned dependencies. Archived Stage C evidence verified independently of the new source. See the [tracker and evidence](z1_stage_c_tracker.md#changing-traffic-z1-checkpoint) for remaining research and human gates.

## 20 November — isolated P1 transition and forecast validation

The pinned Cooja/Z1 measurement collected 32 matched switch/hold windows in each cipher direction at cap 1. Median modeled incremental CPU energy was 7.018 µJ in both directions. A two-second node-level demand forecast achieved low absolute errors on held-out emulation traces but matched the affordable action set in only 1/21 paired cap-one diagnostic windows. Residual-aware ranking remains unresolved. The desktop Firefox walkthrough and 128 pinned unit tests passed. See the [follow-up report](final2x_z1_transition_and_review_20261120.md) for commands, attempts, raw logs and human gates.

## Battery-ranking failure diagnosed on a fresh seed

The component replay found demand forecast bias larger than the between-action energy gap. A fresh cap-1 pair at seed 123458 matched the midpoint budget in 0/22 windows. An empirical uncertainty envelope abstained throughout. Battery-aware ranking remains open and the older P1 mechanism evidence retains its original qualified scope. [Diagnosis and holdout](final2x_z1_ranking_diagnosis_20261120.md)

## Held-out cap-one affordability replay

On seed 123459, the recent-rate forecast matched 135/294 changing-traffic budget cases and 4/20 cases with exactly one observed affordable action. Both prespecified changing-traffic thresholds failed. At 4.097 J per sensor, all 12 scored windows spanning terminal depletion were correctly classified as unaffordable. R04 remains open and the gated nine-node P1 run was skipped. [Protocol, results and reproduction](final2x_z1_affordability_v3.md)

## Joint transition and affordability follow-up

The 42-window diagnostic and 128 matched radio-off Z1 measurements are saved. Joint switch medians were 7.066 µJ for AES cap 1 to Ascon cap 4 and 6.945 µJ for the reverse direction. Radio-enabled queued shrink and calibrated affordability qualification remain pending. [Follow-up report](final2x_z1_affordability_followup.md)

## Radio-enabled queued shrink and finite changing traffic

The three-node matched queued-shrink pair passed, with 24/24 authenticated readings in both arms. The switch increased modeled two-second demand by 792.45 and 789.64 µJ on the two sensors, including the sustained smaller-cap packet work. The changing-traffic finite-budget harness passed a static AES smoke. Development replay of the rate-conditioned candidate scored 106/294 versus 135/294 for the existing baseline. R04 and the conditional revised nine-node P1 run remain open. [Report and artifacts](final2x_z1_queued_shrink.md)
