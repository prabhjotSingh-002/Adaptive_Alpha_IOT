# Current status — 17 November 2026

Read-only audit of the stored results and current source. No campaign restarted/stopped, no dashboard pointer changed, no implementation modified by this review.

## Decision

Do not wait expecting this campaign to repair P1: its frozen protocol still has no qualified cost table. It measures functional baseline/fallback behavior. Corrected refers to the infeasible-current-action guard only, not a calibrated adaptive policy.

## Verified campaign snapshot

State says `running`; selected attempts **20/210**, all selected. Protocol and selected manifest/summary hashes passed campaign_rows verification. Current source snapshot matches frozen campaign sources: **True**. Checked **381** manifest-listed artifact hashes across the 20 selected campaign runs and 22 deferred Phase 4 runs; mismatches: **0**. This does not independently rerun metrics or certify all scientific claims.

Both selected native P1 runs report profile 1, cap 1, zero switches and unavailable calibration. The corrected protocol also leaves lifetime disabled and B3 effectively unbounded. B6 remains a configured cipher rather than a newly qualified calibration winner. These runs cannot demonstrate the requested joint adaptation or comparative lifetime gains.

The campaign log ends at attempt 20. A `running` JSON status is not a heartbeat. This sandbox's process view cannot establish host PID 158217 liveness; verify host process/container and current attempt output before claiming it is still running or estimating remaining time. Do not launch a competing runner.

## Dashboard

`results/campaigns/current.json` still points to `20261116-fresh`. New corrected results are not selected by the main dashboard. The requested comprehensive redesign is not implemented. Archive loader requires the selected campaign's historical.json and only scans runs with summaries; therefore failed/incomplete/manifest-less historical evidence is not comprehensively exposed. Verify/create an additive inventory before any pointer change; preserve original inventories.

## Issues and corrections

1. Missing qualified P1 calibration remains the principal blocker. Repeating 210 cells will not solve it. Complete target/model/source compatibility and calibration provenance first, then create a separate frozen validation campaign.
2. Do not label old fresh artifacts scientifically invalid merely because current sources changed. They belong to their original source cohort; preserve and qualify them separately.
3. Phase 4 closure now has 22 stored passed runs for the seven deferred groups. This alone does not freshly verify the other 28 groups or justify full Phase 4 certification. Human gates remain pending.
4. Phase 4 leftover historical text incorrectly describes 47 bytes as cap 1: 11 header + 16 tag leaves 20 bytes, enough for two readings.
5. P1 uses static costs; residual energy does not enter ranking. Calibration loading alone does not prove dynamic energy-sensitive optimization.
6. Policy batch-fill feasibility allows equality with deadline, while sensor flushes before enqueue at the exact deadline. Cap 4 at a 1-second period/3-second deadline need not yield four-reading batches. Validate calibration against actual transmitted counts.
7. Campaign runner records completed attempts only; abrupt exit can leave stale running status and an unregistered run. Reconcile in-flight attempt before resume. Its source freeze includes host/dashboard files: editing dashboard during execution can stop the campaign at the next source check.
8. Campaign reader verifies manifest/summary hashes, but does not itself verify all raw artifact hashes; this review performed that additional check for the listed records.

## Files and next work

Inspected campaign.py, run_campaign.py, campaign_dashboard.py, dashboard loader, protocol/current pointer, source diffs/status, Phase 4/5 journal/closure records and referenced manifests/summaries/artifact hashes. Earlier conversation inspected policy/sensor/calibration/runner. A complete fresh line-by-line review of every changed file and all historical report contents is NOT completed; do not interpret this report as that certification.

Priority order: establish runner liveness → preserve/reconcile active attempt → decide whether to finish functional-only campaign → qualify calibration and repair remaining constraints → native/Z1 mechanism/security validation → dedicated calibrated lifetime evaluation → comprehensive dashboard and archive → phase reports/human gates. No new simulation is necessary merely to establish current status.

## Deferred Phase 4 stored results

Values below are read from stored summaries; artifact bytes checked against their manifests. Full event-level depletion/forwarding reanalysis remains needed before closing all acceptance claims.

| Group | Run | Manifest status | Reading PDR | Stored lifetime summary |
|---|---|---|---|---|
| case29_boundary_4000ms | 20261116T175934506150Z-B1-2 | passed | 1.0 | null |
| case29_boundary_4000ms | 20261116T175957444306Z-B2-2 | passed | 1.0 | null |
| case29_boundary_4000ms | 20261116T180017877202Z-B4-2 | passed | 1.0 | null |
| case29_boundary_4000ms | 20261116T180036635527Z-B5-2 | passed | 1.0 | null |
| case30_boundary_47byte | 20261116T180100630105Z-B1-2 | passed | 1.0 | null |
| case30_boundary_47byte | 20261116T180123777826Z-B2-2 | passed | 1.0 | null |
| case30_boundary_47byte | 20261116T180142937672Z-B4-2 | passed | 1.0 | null |
| case30_boundary_47byte | 20261116T180202411260Z-B5-2 | passed | 1.0 | null |
| case31_depletion_125ms | 20261116T180228618905Z-B2-2 | passed | 0.47468354430379744 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158573.261, "censored": false}, "hnd": {"event": true, "time_ms": 158573.261, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 75, "scheduled_shortfall": 165, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case32_depletion_250ms | 20261116T180333068963Z-B2-2 | passed | 0.4810126582278481 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 159198.184, "censored": false}, "hnd": {"event": true, "time_ms": 159198.184, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 76, "scheduled_shortfall": 164, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case33_lifetime_123456 | 20261116T180430865742Z-B1-2 | passed | 0.47468354430379744 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 157991.724, "censored": false}, "hnd": {"event": true, "time_ms": 157991.724, "censored": false}, "functional": {"event": true, "crossing_ms": 164000, "confirmation_ms": 174000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 75, "scheduled_shortfall": 165, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case33_lifetime_123456 | 20261116T180535922718Z-B2-2 | passed | 0.47468354430379744 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 157991.459, "censored": false}, "hnd": {"event": true, "time_ms": 157991.459, "censored": false}, "functional": {"event": true, "crossing_ms": 164000, "confirmation_ms": 174000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 75, "scheduled_shortfall": 165, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case33_lifetime_123456 | 20261116T180637065241Z-B4-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158245.08, "censored": false}, "hnd": {"event": true, "time_ms": 158245.08, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case33_lifetime_123456 | 20261116T180745492043Z-B5-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158244.84, "censored": false}, "hnd": {"event": true, "time_ms": 158244.84, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case34_lifetime_123457 | 20261116T180857558786Z-B1-2 | passed | 0.4810126582278481 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158250.39, "censored": false}, "hnd": {"event": true, "time_ms": 158250.39, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 76, "scheduled_shortfall": 164, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case34_lifetime_123457 | 20261116T181020179899Z-B2-2 | passed | 0.4810126582278481 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158250.104, "censored": false}, "hnd": {"event": true, "time_ms": 158250.104, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 76, "scheduled_shortfall": 164, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case34_lifetime_123457 | 20261116T181129941826Z-B4-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158503.711, "censored": false}, "hnd": {"event": true, "time_ms": 158503.711, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case34_lifetime_123457 | 20261116T181239744526Z-B5-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158503.489, "censored": false}, "hnd": {"event": true, "time_ms": 158503.489, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case35_lifetime_123458 | 20261116T181353959358Z-B1-2 | passed | 0.4810126582278481 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158507.111, "censored": false}, "hnd": {"event": true, "time_ms": 158507.111, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 76, "scheduled_shortfall": 164, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case35_lifetime_123458 | 20261116T181501438398Z-B2-2 | passed | 0.4810126582278481 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158506.892, "censored": false}, "hnd": {"event": true, "time_ms": 158506.892, "censored": false}, "functional": {"event": true, "crossing_ms": 165000, "confirmation_ms": 175000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 76, "scheduled_shortfall": 164, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case35_lifetime_123458 | 20261116T181610768218Z-B4-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158760.494, "censored": false}, "hnd": {"event": true, "time_ms": 158760.494, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |
| case35_lifetime_123458 | 20261116T181712712015Z-B5-2 | passed | 0.45569620253164556 | {"battery_nodes": [2, 3], "fnd": {"event": true, "time_ms": 158760.257, "censored": false}, "hnd": {"event": true, "time_ms": 158760.257, "censored": false}, "functional": {"event": true, "crossing_ms": 163000, "confirmation_ms": 173000, "censor_ms": null}, "scheduled_readings": 240, "scheduled_delivered": 72, "scheduled_shortfall": 168, "service_window_ms": 10000, "service_persistence_ms": 10000, "delivery_bound_ms": 5000, "service_minimum": 0.95} |

Artifact mismatches: []
