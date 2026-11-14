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
