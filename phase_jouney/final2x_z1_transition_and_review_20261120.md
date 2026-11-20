# finalPLAN2X transition measurement and review checkpoint

This checkpoint continues the Z1 work in Sections 12–13 of [finalPLAN2X](../finalPLAN2X.md). The archived Stage C comparison and the changing-traffic pilot retain their own source, workload and calibration identities.

## Isolated switching cost

A single Z1 mote ran the production `lab_policy_p1` switch and hold paths at cap 1. Each pair used the same features, cost entries, preferred action and initial switch time. The starting cipher was the preferred cipher for the hold arm and the other cipher for the switch arm. The benchmark alternated execution order. Fixture cost values exercised the two branches deterministically. There were 32 pairs for each destination cipher and 16 decisions in each timing window. The radio was off, interrupts were masked during timing, and the window contained no packet sealing, transmission or logging. The bench applies the returned profile and cap with the sensor's validity checks and verifies resulting state outside the timer window.

Both directions had a median incremental modeled CPU energy of **7.018 µJ per switch decision**, with per-pair results from **6.993 to 7.042 µJ**. This estimate uses the Z1 3 V MCU active current with the idle-radio baseline removed. It covers the extra decision and application work at fixed cap 1, measured with matched emulated timer ticks. Joint cipher/cap changes and transition effects on subsequent packet work remain outside this measurement. The production transition-cost setting remains 50 µJ.

The first attempt used an incorrect pins path. The second encountered the sandbox Docker group error. The first passing run included an assertion in the timer window. The final run moved assertions outside that window. The raw logs preserve all attempts. [Final manifest](../results/phase_05/z1-transition-20261120-final/manifest.json) · [Paired samples](../results/phase_05/z1-transition-20261120-final/samples.json) · [Raw log](../results/phase_05/z1-transition-20261120-final/COOJA.testlog)

## Battery-aware P1

The offline forecast uses a two-second service horizon and per-node medians from six static cap/profile calibrations at 0.25 and 2 Hz on seed 223457. It interpolates only inside that measured rate interval. The evaluator uses held-out seed 123456, checks residual affordability only in finite-budget runs, and records forecast error for windows with stable observed actions and rate. The older finite-budget trace is identified as a distinct source cohort.

| Held-out traces | Evaluated windows | Median absolute relative error | Maximum |
| --- | ---: | ---: | ---: |
| Changing-traffic P1 | 14 | 3.116% | 3.213% |
| Historical finite-budget P1 | 6 | 1.954% | 2.039% |
| Fresh stationary static controls | 86 | 0.049% | 0.269% |

The six completed finite-budget forecast windows were all affordable. An additional retrospective diagnostic replayed eight overlapping starts near the two observed removals. The selected-action affordability forecast agreed with all eight observed outcomes, including four shortfalls inside the horizon. [Observed-cutoff diagnostic](../results/phase_05/z1-closure-20261120/battery-cutoff-check.json)

An additional paired cap-1 diagnostic set a hypothetical residual budget between the predicted AES and Ascon demand in each fixed window. The predicted affordable action set matched the observed set in **1 of 21** windows. Absolute demand forecasts were much more accurate than discrimination between nearby actions. Under the plan's D4 acceptance rule, residual-aware P1 ranking stays unresolved. The forecast runs offline and the production ranker remains cost-aware. [Forecast data and per-window outcomes](../results/phase_05/z1-closure-20261120/battery-forecast-v2.json)

## Browser walkthrough

Firefox rendered the pinned local Flask dashboard at 1600 × 1100. The latest page opened its run evidence disclosure with two links. Filtering the archive to failed runs reduced 429 rows to 40. The campaign group selector changed to tree16 and a real run drill-down loaded identity and integrity fields. The campaign page rendered the historical 40/210 stopped campaign and labelled its P1 rows as fallback diagnostics. The latest page still presents the earlier 16-run mechanism snapshot. It has not yet been promoted to include the newer changing-traffic and Stage C cohorts. [Interaction log](../results/phase_05/z1-closure-20261120/walkthrough-interactive.log) · [Latest](../results/phase_05/z1-closure-20261120/latest-ready.png) · [Archive](../results/phase_05/z1-closure-20261120/historical-ready.png) · [Campaign](../results/phase_05/z1-closure-20261120/campaign-ready.png)

## Reproduction and human gates

Use the pinned Contiki-NG and Cooja checkout and official container recorded by the benchmark manifest. From a checkout containing the captured sources and the curated artifacts, run:

```bash
python3 -B host/run_transition_benchmark.py results/phase_05/z1-transition-reproduction
python3 -B host/audit_battery_forecast.py results/phase_05/z1-battery-forecast-reproduction.json
PYTHONPATH=host python3 -B results/phase_05/z1-closure-20261120/phase4-audit.txt
```

The archived Phase 4 audit is given the original control log in the closure directory. Its ledger records the scope and configuration of the 35 archived cases and the four fresh static controls. On a checkout with the new tools present, the old experiment manifests still identify their original source cohort.

The pinned unit run passed 128 tests after the benchmark. A repeat of the forecast audit in this workspace produced identical JSON. A second team member must run the pinned reproduction, compare against the recorded results, and record the checkout, exact commands, resulting hashes and any differences. The Phase 4 and Phase 5 human sign-offs and independent reproduction remain pending. [Unit log](../results/phase_05/z1-closure-20261120/post-benchmark-unit.log) · [Phase 4 review](final2x_phase_03_evidence_20261120.md)

## Targeted current-source Phase 4 reruns

Both Z1 measurement controls passed. The native Cooja 500 ms, 4000 ms and 47-byte boundary groups also passed in all four static modes. Across these five groups, **14 runs** authenticated 48/48 readings each, and all **147 indexed artifact and binary hashes** matched. The batched boundary runs submitted four, one and two readings per packet respectively. Together with the earlier snapshot, this updates the targeted current-source evidence for measurement, boundary and ordinary static behavior. Other historical groups remain mapped in the archived ledger, and full current-source matrix coverage remains open.

```bash
python3 -B host/validate_phase4.py --section measurement
python3 -B host/validate_phase4.py --section boundaries
PYTHONPATH=host python3 -B results/phase_05/z1-closure-20261120/targeted-phase4-verify.txt
```

[Targeted evidence](../results/phase_05/z1-closure-20261120/targeted-phase4-verify.json) · [Measurement log](../results/phase_05/z1-closure-20261120/current-measurement.log) · [Boundary log](../results/phase_05/z1-closure-20261120/current-boundaries.log)
