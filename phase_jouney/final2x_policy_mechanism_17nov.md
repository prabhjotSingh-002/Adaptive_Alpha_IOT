# finalPLAN2X items 4–5 — Policy/queue and small Z1 mechanism report

Date: 17 November 2026. Scope: the user's authorized policy/queue repairs and bounded root+2 Z1 validation. This is a checkpoint report, not closure of every original Phase 4/5 or 2X requirement.

**Outcome:** bounded safety/wire/reset/depletion checks pass. **Residual-aware P1 ranking remains OPEN**: scenario-level network costs are not a validated local battery-demand predictor. B3's real residual-threshold behavior is verified separately. No energy/lifetime superiority claim is made.

## What changed and why

- `firmware/policy/policy.c/.h`: reject initialized invalid profiles/caps before indexing; protect maximum-cost selection and wrap-safe dwell arithmetic; use shared packet constants; require full-cap fill strictly before effective expiry. Add an eight-observed-interval generation-rate estimator with startup, staleness, saturation and bounded-wrap semantics.
- `firmware/aggregate/aggregate.c`: build `min(queue_count, current_cap)` readings and retain the rest until commit, so a cap reduction cannot put too many readings in a sealed packet.
- `firmware/sensor/sensor.c`: replace configured-period rate with actual observed reading intervals; emit FEATURE changes; log the new action before bounded backlog draining. Failed-progress/deadline cases retain explicit accounting.
- `host/parse_logs.py`, `metrics.py`, `mechanism_checks.py`: validate measured inputs against GEN, join POLICY→sealed TX2→authenticated RX2, distinguish startup/logged/wire changes, require real reset probes/locked refusals, and enforce terminal energy/RF accounting. Policy-family security labels describe dual-profile capability rather than assuming the compile-time profile was the actual wire profile.
- `firmware/project-conf.h`: suppress generic OS MAIN startup INFO uniformly to fit Z1 linker regions; keep every structured RSLAB evidence event. Upstream core and crypto primitives were not edited.
- `host/run_experiment.py`: capture the initial Cooja event, align static/adaptive Z1 flush lead to 125 ms, run canonical mechanism acceptance, and provide `--preflight-only` for real resolved-CLI/table admission without a build. Explicit unqualified-table bypass is restricted to native diagnostics.
- `host/calibration_contract.py`: include capture semantics and the scenario-template digest in compatibility. Fresh final-source calibration was performed; older tables/runs remain historical source cohorts.

The scheduling/feature/accounting contract and limits are in [policy-contract.md](../docs/policy-contract.md). The permanent work record is [the preserved phase plan](tmp/policy_mechanism_17nov.md).

## Executed tests and resource checks

Pinned official container: `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`. Contiki/Cooja/Ascon pins, commands, config/scenario/source and binary digests are recorded by each canonical run.

- **122 unit tests, OK**: includes actual CLI static/adaptive preflight equivalence, shared production C invalid-state/cap/deadline/wrap checks, and integration of the measured-rate C estimator with the B6 C policy. Log: `results/phase_05/mechanism_17nov/final-unit-and-size.log`.
- **ASan/UBSan safety binary passed**: all 256 runtime profile values, maximum cost and cap-shrink chunk order; command/source: `test_safety.sh` and `tests/unit/test_policy_safety.c`.
- **1,089 official Ascon-AEAD128 vectors passed**, plus roundtrip/bad-tag/bounds and dual-profile packet/replay regression. Log: `unit-and-security-acceptance.log`; official script `scripts/test_phase4_ascon.sh`, backend ref.
- Actual archived Z1 binaries inspected with GNU msp430-size. Maximum text+data: **57,164 bytes**; maximum data+bss: **6,240 bytes**. Minimum observed stack reserved-minus-used: **1,166 bytes**. Linker fits and exercised stack paths are evidence; this is not an all-path stack proof. See `binary-size-evidence.json` and `msp430-size.log`.

Unit fixtures and sanitizer cases are correctness tests, not network research measurements.

## Final frozen-source experiment ledger

All runs below are **root+2, Z1**, serial through `host/run_experiment.py`. Six static calibration cells use seed **223457**; mechanism/security cells use **123456**. The six profile×cap cells qualify under predeclared PDR>=0.95 and p95<=5000 ms. Actual cap-4 batch occupancy remains recorded rather than assumed.

| Purpose | Run ID | Status | Key evidence |
|---|---|---|---|
| cal-B1-cap1 | `20261117T023634948551Z-B1-2` | passed | calibration cell |
| cal-B1-cap2 | `20261117T023714431056Z-B1-2` | passed | calibration cell |
| cal-B1-cap4 | `20261117T023753194817Z-B1-2` | passed | calibration cell |
| cal-B2-cap1 | `20261117T023831400765Z-B2-2` | passed | calibration cell |
| cal-B2-cap2 | `20261117T023910366789Z-B2-2` | passed | calibration cell |
| cal-B2-cap4 | `20261117T023948665737Z-B2-2` | passed | calibration cell |
| p1-qualified-functional | `20261117T024032053990Z-P1-2` | passed | authenticated packet joins=26 |
| p1-qualified-finite | `20261117T024127105801Z-P1-2` | passed | terminal nodes=[2, 3] |
| b3-threshold-finite | `20261117T024208744064Z-B3-2` | passed | terminal nodes=[2, 3] |
| bottleneck-depletion | `20261117T024314393934Z-B1-2` | passed | terminal nodes=[2] |
| b3-attack | `20261117T024408479815Z-B3-2` | passed | 8 injections / 8 rejections |
| b3-root-reset | `20261117T024451744653Z-B3-2` | passed | post-reset accepted=0; probes=40 |
| b6-attack | `20261117T024536275754Z-B6-2` | passed | 8 injections / 8 rejections |
| b6-root-reset | `20261117T024617823636Z-B6-2` | passed | post-reset accepted=0; probes=40 |
| p1-attack | `20261117T024700243978Z-P1-2` | passed | 8 injections / 8 rejections |
| p1-root-reset | `20261117T024742346478Z-P1-2` | passed | post-reset accepted=0; probes=40 |

Exact commands and durable statuses: `results/phase_05/mechanism_17nov/validation-v2/attempts.json`. Frozen source/protocol: `frozen-sources.json`, `protocol.json`. Actual qualified CLI preflight: `qualified-preflight.log` (`build_executed=false`, `simulation_executed=false`, calibration status qualified).

## Policy and finite-budget findings

Qualified P1 functional run delivered **48/48 authenticated readings**, with **26/26 sealed/accepted packet joins**, p95 approximately **1072.98 ms** and no fallback actions. Both profiles were observed in actual sealed TX and authenticated RX. There were **4 logged profile changes but only 2 actual wire-profile changes**: post-traffic/stale-state decisions need not produce transmitted packets. Startup assignments are separate.

P1 finite mechanism used **4,093,000,000 nJ per sensor**, both sensors bounded and root unbounded. This budget was frozen from independent static AES cap-1 calibration consumption near the middle of the generation span, before qualified P1 outcomes. The rule and exact samples are in `validation-v2/finite-budget-freeze.json`; it was not adjusted to improve P1 results.

Finite P1 generated **22** readings: **20 delivered**, **2 explicitly dropped at terminal depletion**. Prospective demand remained **48**, so scheduled shortfall was **28**. Both nodes 2 and 3 depleted/removed; post-death application/RF violations were **0**. FND=HND at **71462.851 ms**; this is the half-population definition, not proof that both died simultaneously. Functional crossing was **77000 ms**, confirmed **87000 ms**.

B3 finite mechanism used the independently specified historical **9 J** control budget with 120 planned readings per sensor. Each sensor's actual threshold actions were replayed from residual telemetry and both sensors delivered authenticated AES and Ascon packets. Total accepted readings: **188/188 actually generated**, against **240 scheduled**. Two actual wire profile changes and terminal removal of both sensors were verified. This validates threshold behavior, not P1 residual-aware optimization.

## Bottleneck result and negative service finding

The dedicated static B1 bottleneck control bounded **node 2 only** at 9 J; node 3 and root were unbounded. Canonical checks require the actual node-3→node-2 parent path and downstream authenticated traffic before death. Node 2 depleted/removed at **157585.165 ms**, with no later RF/forwarding/application activity from it.

**Do not claim that its first functional failure was caused by death.** Functional service crossed the threshold at **75000 ms** and confirmed at **85000 ms**, well before node 2's depletion. It delivered **181/217 generated** readings (PDR≈0.8341), with **34 explicit drops**; prospective demand was 240 and scheduled shortfall 59. This poor service result is retained. The cause of pre-death loss was not isolated here. Targeted cutoff/accounting passed; the run does not establish an energy/lifetime improvement or acceptable pre-death QoS.

## Root reset and attack evidence

All B3/B6/P1 Z1 attack fixtures rejected **8/8 injections each**, with surrounding valid controls checked by canonical metrics. Each root-reset fixture recorded two actual boot requests, root replacement, boot-regrant refusal and **40 post-reset captured-packet probes**. Locked-context refusals were **55 / 41 / 49** for B3/B6/P1; post-reset accepted packets/readings were **0** in every case.

These are dedicated security fixtures without power-model comparison. P1's reset fixture uses protected no-cost fallback; qualified cost-driven wire operation is established by the separate functional/finite cells. The reset test proves fail-closed behavior without a second grant, not automatic recovery or persistent replay-state restoration.

## Independent raw/artifact acceptance

`audit_validation.py` reparsed each original COOJA.testlog with the canonical parser and compared it to the stored normalized events. **44,020 raw events** were reparsed; **190 artifact/binary hashes** matched. It reran the shared acceptance checks and independently replayed B3 threshold actions and P1 BEST-cost decisions from recorded measured features. Results: `mechanism-acceptance.json` and `raw-acceptance-audit.log`. These are additive analyses; original manifests/summaries/raw files were not rewritten.

## Preserved failures and corrections

1. `20261117T021307655729Z-B6-2`: linker ROM-region overflow **2 bytes**. Preserved console/build failure; resolved by project-level generic MAIN-log configuration, with research logs retained.
2. `20261117T021701461503Z-B6-2`: Cooja TEST OK but acceptance failed because the first ENERGY_TIMER was omitted. Pinned Cooja ScriptParser already performs an initial YIELD; the user-script extra YIELD skipped the first log. Capture was corrected to process the first delivered event. No missing event was fabricated into the old trace.
3. Earlier `validation/` six calibration runs qualified for their source, but P1 import was correctly blocked: static flush_lead_ms=125, adaptive=0. Defaults and actual CLI regression/preflight were fixed. Those runs and failed preflight remain; final measurements use `validation-v2/`, not mixed source cohorts.
4. The native no-cost fallback diagnostic and intermediate Z1 ROM/capture retries remain in their original directories. They are not substituted for the final qualified cells.

## Remaining work and stop

- **P1 residual-aware ranking OPEN:** requires a defensible measured local energy-demand predictor/objective, calibration and held-out validation. The current cost-aware policy must not be called validated residual-aware adaptation.
- Changing-arrival adaptation is covered by shared-C fixtures; current mote measurements use a stationary workload. No changing-workload research claim is made.
- Isolated transition-energy calibration, full new-source Phase 4 semantic mapping, human review and independent reproduction remain open. Configured transition energy is an assumption; POLICY_TIME is partial timing, not a separate energy measurement.
- Existing 9-node tables are preserved historical evidence and are incompatible with current-source admission after these changes. Fresh 9-node qualification/resource checks and the separately scoped pilot remain future work; no 9-node run was launched in this package.
- Browser/presentation gates and Phase 6 remain pending. No bulk/scaling or comparative lifetime campaign was started. Stop at this bounded checkpoint.
