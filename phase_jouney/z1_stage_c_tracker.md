# 9-node Z1 Stage C tracker

- [x] Freeze the seven-arm protocol for seed 123456, legacy Z1 topology, 4.097 J per sensor, unbounded root and 102 s horizon. The saved P1 outcome was known before this freeze. [Protocol and commands](../results/phase_05/z1-stage-c-20261120/protocol.json)
- [x] Verify the qualified calibration and current source. Admit the saved finite-budget P1 run after checking its configuration, scenario and 13 artifact and binary hashes. Eight deliberately mismatched manifests were rejected. All seven CLI preflights passed. [Admission evidence](../results/phase_05/z1-stage-c-20261120/admission.json)
- [x] Run B1, B2, B3, B4, B5 and B6 serially. Record each attempt and check its manifest against the frozen cohort before including it.
- [x] Publish seven paired rows covering modeled energy per authenticated reading, generated and scheduled delivery, p95 latency, first/half-node death and service failure or censoring.
- [ ] Review changing traffic, switching energy and battery-aware ranking in separate validations.
- [ ] Complete dashboard walkthrough, Phase 4/5 human review and independent reproduction before the Phase 6 decision.

Reproduce the admission check from the repository root with `PYTHONPATH=host python3 -B results/phase_05/z1-stage-c-20261120/check-admission.txt`. This is a Stage C evidence check alongside the frozen protocol. The existing functional comparison command still applies its functional-run rules.

The serial control ledger records each command, log, manifest and admission status as runs finish. [Control attempts](../results/phase_05/z1-stage-c-20261120/control-attempts.json) · [Control progress](../results/phase_05/z1-stage-c-20261120/control-progress.log)

## Stage C results

| Mode | Modeled sensor mJ per authenticated reading | Authenticated / generated | Authenticated / scheduled | p95 ms | First death s | Half death s | Service confirmed s |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 | 364.53 | 90/96 | 90/192 | 121.64 | 72.573 | 72.835 | 85 |
| B2 | 364.54 | 90/96 | 90/192 | 122.81 | 72.573 | 72.835 | 85 |
| B3 | 399.97 | 82/88 | 82/192 | 148.89 | 71.199 | 71.461 | 85 |
| B4 | 437.54 | 75/96 | 75/192 | 2977.27 | 72.672 | 72.850 | 85 |
| B5 | 437.54 | 75/96 | 75/192 | 2989.39 | 72.672 | 72.850 | 85 |
| B6 | 431.72 | 76/88 | 76/192 | 1148.97 | 71.300 | 71.478 | 85 |
| P1 | 431.80 | 76/88 | 76/192 | 1140.90 | 71.300 | 71.478 | 85 |

All six new controls passed and matched the frozen cohort. The saved finite-budget P1 arm was reused. The first and half-node deaths were observed in every arm, and service crossed the threshold at 75 s and was confirmed at 85 s in each case. All seven summaries recorded zero post-depletion application or RF violations. The modeled energy metric covers the eight battery-powered sensors from boot to the 102 s horizon. [Comparison CSV](../results/phase_05/z1-stage-c-20261120/comparison.csv) · [Run directories](../results/phase_05/z1-stage-c-20261120/selected-runs.json)

On this seed, B1 and B2 delivered 90 of 192 scheduled readings, compared with 76 for P1. P1 used 18.45% more modeled sensor energy per authenticated reading than B1. B6 and P1 both delivered 76, with p95 delays of 1,149 and 1,141 ms, respectively. These are descriptive single-seed results with the P1 outcome known before comparison setup. Stage C is complete at this checkpoint.

## Changing-traffic host checkpoint

- [x] Rechecked Stage C artifact hashes for all seven arms and reproduced the comparison JSON byte for byte. The Stage C findings and selected-run references are above.
- [x] Ran the production-C P1 host test against the saved nine-node cost table and configured dwell, margin and transition cost. Eight intervals per segment at 500 ms, 4,000 ms and 500 ms measured 2 Hz, 0.25 Hz and 2 Hz. P1 selected Ascon cap 4, AES cap 1 and Ascon cap 4. All six measured-rate tests passed in the pinned container. [Test log](../results/phase_05/z1-changing-traffic-20261120/host-tests.log) · [Evidence hashes](../results/phase_05/z1-changing-traffic-20261120/evidence.sha256)
- [x] Implement an opt-in within-run schedule in the Z1 runner. Include it in the resolved config, horizon and calibration compatibility checks. Then run a three-node pilot and verify the generation timestamps, measured rate, applied profile and cap, and authenticated packets. Current Z1 runs schedule readings at one fixed interval.
- [ ] Measure switching energy and separately validate battery-aware P1 ranking before dashboard review, sign-off and independent reproduction.

The rate-step observations above come from a host fixture and exercise the production policy and rate estimator. The Z1 workload-step result remains pending.

## Changing-traffic Z1 checkpoint

- [x] Added an opt-in middle-third generation interval to non-lifetime Z1 power-model runs. The resolved workload enters the horizon and calibration checks. Lifetime preflight rejects the option because lifetime demand accounting uses a stationary schedule.
- [x] Ran six fresh calibration cells on three Z1 motes, seed 223457, with 27 readings per sensor and 500/4,000/500 ms generation intervals. The table qualified. P1 ran with seed 123456 and the same resolved workload. Both sensors measured 2/0.25/2 Hz and selected Ascon cap 4, AES cap 1, then Ascon cap 4 at the sampled segment endpoints. Root authenticated **54/54 readings**. All **44 packets** matched sealed TX and applied decisions, with **12 actual wire cipher changes**, zero fallback actions and 13 verified P1 artifact hashes. [Attempts](../results/phase_05/z1-changing-traffic-20261120/mote-attempts.json) · [Raw event audit](../results/phase_05/z1-changing-traffic-20261120/mote-audit.json)
- [x] Verified the archived Stage C artifacts again for all seven arms. The changing-traffic build has its own source and calibration identity.
- [x] Ran 128 unit tests and checked six dashboard routes in the pinned container. All passed after running the tests after simulation and including the packaged dependencies. The initial unit run encountered the experiment lock and missing Flask. A host-only dashboard check encountered missing NumPy. The unsuccessful checks are preserved alongside the passing log. [Passing checks](../results/phase_05/z1-changing-traffic-20261120/post-run-tests.log)

### Open work

1. Measure transition energy with matched switch and no-switch executions and isolate the transition window from packet and radio work. The saved POLICY_TIME measurements cover policy timing and cannot establish isolated transition energy.
2. Define and calibrate a per-node energy-demand predictor, then validate on held-out traffic and battery conditions. Current P1 uses rate, feasibility and calibrated costs in its ranking. Residual energy threshold decisions are implemented in B3.
3. Close the current-source Phase 4 evidence mapping, visual browser walkthrough, human sign-off and independent reproduction. The automated HTTP checks are complete for the six checked routes. Record actual review and reproduction before Phase 6 authorization.

### finalPLAN2X evidence checkpoint

All 35 archived Phase 4 cases now have a machine-readable mapping. Raw replay matched seven summary fields across 62 runs and verified 685 indexed hashes. Four fresh Z1 static controls passed with 48/48 authenticated readings each. Phase 4 review can trace historical source drift run by run. Full current-source matrix coverage remains open. Browser captures exist for the latest, archive and campaign routes, with campaign still loading at capture time. [2X Phase 3 evidence checkpoint](final2x_phase_03_evidence_20261120.md)

### Switching-energy and browser follow-up

- [x] Measured the isolated fixed-cap P1 cipher decision and application paths on Z1. Both switch directions added a median 7.018 µJ of modeled CPU energy over matched hold windows. Joint cap/cipher changes remain outside the window measured here.
- [ ] Battery-aware ranking remains unresolved after a held-out forecast test and a cap-1 affordability diagnostic. The forecast classified the affordable action set correctly on 1 of 21 paired diagnostic windows. The production policy continues to rank by measured cost and feasibility.
- [x] Walked through the desktop Firefox pages and exercised the latest evidence disclosure, the historical failure filter and the campaign run detail. The landing page still pins the earlier mechanism snapshot.
- [ ] Phase 4 and 5 human acceptance and independent reproduction require a reviewer. See the reproduction commands and evidence index in the [follow-up report](final2x_z1_transition_and_review_20261120.md).

Two fresh measurement controls and all three boundary groups also passed after the transition benchmark. All 14 runs authenticated 48/48 readings and 147 indexed hashes matched. [Targeted Phase 4 evidence](../results/phase_05/z1-closure-20261120/targeted-phase4-verify.json)

### Battery-ranking failure diagnosis

The original affordability failure was reproduced on a fresh seed. Median demand error exceeded the modeled action gap on both seeds. An empirical uncertainty envelope abstained in every window, so battery-aware ranking remains unqualified. The current-source 125 and 250 ms Z1 bottleneck reruns both confirmed terminal forwarding cutoff. [Diagnosis and evidence](final2x_z1_ranking_diagnosis_20261120.md)

## Held-out cap-one affordability replay

On seed 123459, the recent-rate forecast matched 135/294 changing-traffic budget cases and 4/20 cases with exactly one observed affordable action. Both prespecified changing-traffic thresholds failed. At 4.097 J per sensor, all 12 scored windows spanning terminal depletion were correctly classified as unaffordable. R04 remains open and the gated nine-node P1 run was skipped. [Protocol, results and reproduction](final2x_z1_affordability_v3.md)

## Joint transition and affordability follow-up

The 42-window diagnostic and 128 matched radio-off Z1 measurements are saved. Joint switch medians were 7.066 µJ for AES cap 1 to Ascon cap 4 and 6.945 µJ for the reverse direction. Radio-enabled queued shrink and calibrated affordability qualification remain pending. [Follow-up report](final2x_z1_affordability_followup.md)

## Radio-enabled queued shrink and finite changing traffic

The three-node matched queued-shrink pair passed, with 24/24 authenticated readings in both arms. The switch increased modeled two-second demand by 792.45 and 789.64 µJ on the two sensors, including the sustained smaller-cap packet work. The changing-traffic finite-budget harness passed a static AES smoke. Development replay of the rate-conditioned candidate scored 106/294 versus 135/294 for the existing baseline. R04 and the conditional revised nine-node P1 run remain open. [Report and artifacts](final2x_z1_queued_shrink.md)
