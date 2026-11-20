# 20 November 2026 — 9-node Z1 P1 mechanism pilot

Stage B used one root and eight Z1 sensors, the qualified current-source cost table and evaluation seed 123456. Before either P1 run, the protocol froze a 102 s horizon and a finite budget of 4.097 J per sensor for nodes 2–9. The root had unbounded energy. The budget is the rounded-up median of the static AES cap-1 calibration's sensor energy samples nearest 12 s after each sensor's first generation event. [Frozen protocol](../results/phase_05/z1-nine-node-p1-20261120/protocol.json) · [Budget inputs](../results/phase_05/z1-nine-node-p1-20261120/finite-budget-freeze.json)

| Run | Authenticated / generated | Authenticated / scheduled | p95 delay | Authenticated packets matched to active policy and sealed TX |
|---|---:|---:|---:|---:|
| Functional | 186/192 (96.875%) | 186/192 (96.875%) | 1,135.14 ms | 100 |
| Finite budget | 76/88 (86.36%) | 76/192 (39.58%) | 1,140.90 ms | 45 |

In the functional run, all eight sensors delivered authenticated data. The wire contained 14 single-reading AES-CCM packets and 86 two-reading Ascon-AEAD128 packets, with seven actual cipher transitions between packets. P1 used both caps 1 and 2 with zero fallback actions. Sensor 9 delivered 18 of 24 readings. [Functional manifest](../results/phase_05/20261119T200722249256Z-P1-8/manifest.json) · [Functional summary](../results/phase_05/20261119T200722249256Z-P1-8/summary.json)

All eight battery-powered sensors depleted and were removed between 71.300 and 72.001 s. First-node death occurred at 71.300 s and half-node death at 71.478 s. The service threshold crossed at 75 s and was confirmed at 85 s. All three lifetime events were observed within the 102 s horizon. Prospective demand accounting retained the 104 readings that remained ungenerated, and the total scheduled shortfall was 116 readings. Terminal counters matched production-C energy reconciliation. The raw audit reported zero post-death application events and zero RF frames from removed sensors. [Finite-budget manifest](../results/phase_05/20261119T201051437412Z-P1-8/manifest.json) · [Finite-budget summary](../results/phase_05/20261119T201051437412Z-P1-8/summary.json)

Both builds linked. Across four archived binaries, maximum text+data was 57,166 bytes, maximum data+bss was 6,932 bytes, and the minimum observed stack headroom was 372 bytes in the exercised paths. Raw reanalysis reproduced both summaries across 27,573 events and 795 radio frames and verified 26 artifact and binary hashes. The first audit comparison used unnormalized Python keys against JSON and failed. JSON normalization resolved the comparison without changing either run. [Commands and manifest hashes](../results/phase_05/z1-nine-node-p1-20261120/attempts.json) · [Raw reanalysis](../results/phase_05/z1-nine-node-p1-20261120/raw-reanalysis.json) · [Build sizes](../results/phase_05/z1-nine-node-p1-20261120/binary-size-evidence.json)

Stage B is complete at the 2X checkpoint. The results describe one simulation seed with the Z1 component energy model. Stage C paired comparison, residual-aware ranking validation, presentation review and human gates remain pending.

## Decision review and remaining sequence

The latest two nine-node manifests passed. In the functional run, the policy logged 16 profile changes, seven of which appeared as changes between successive transmitted packets from a sensor. No fallback actions occurred. The finite-budget pilot confirmed terminal cutoff. Relative energy benefit remains an open comparison question.

1. Freeze Stage C as a descriptive seven-arm comparison on seed 123456, using the Stage B topology, traffic, horizon, per-sensor budget and qualified calibration digest. Record that the P1 outcome was already known.
2. Qualify lifetime comparison admission. The existing functional comparison guard rejects lifetime runs. Validate matching source, dependencies, workload, power model, battery population, horizon, seed and table, verify artifact hashes and test rejection of mismatched arms. Keep analysis tooling outside the frozen measurement source set if possible. Recheck calibration compatibility after any source change.
3. Admit the saved finite P1 arm if it passes those checks. Preflight and run missing B1–B6 controls serially using the same settings. Preserve each attempt and its hashes.
4. Report seven paired rows for modeled energy per authenticated reading, delivery against generated and scheduled demand, p95 delay, first and half-node death, and service failure or censoring. Include differences from P1. One paired seed supports a descriptive pilot.
5. Record the Stage C decision, then address changing traffic, switching energy and residual-aware ranking in separately scoped validations. Complete Phase 4 evidence review, dashboard walkthrough, human sign-off and independent reproduction before requesting Phase 6 authorization.

Stage C settings and saved P1 admission are verified. See the [Stage C tracker](z1_stage_c_tracker.md) for controls and reporting still pending.
