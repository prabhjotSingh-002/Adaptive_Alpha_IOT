# finalPLAN2X battery-ranking diagnosis and Phase 4 cutoff evidence

## Why battery-aware ranking failed

The original test chose a hypothetical battery budget halfway between the forecast AES and Ascon energy demands over two seconds. It then compared the predicted and observed sets of actions that could fit that budget. On seed 123456, AES actually used less modeled energy in 20 of 21 paired windows. The absolute demand forecast was low by a median 55.2 µJ across the two actions, versus a median 33.0 µJ gap between their predicted demands. In 20 windows, the threshold was below both observed demands. The affordability check matched in one window. Exact component replay accounted for all recorded window energy. Listening was a median 95.2% of the modeled demand. [Original failure diagnosis](../results/phase_05/z1-ranking-diagnosis-20261120/diagnosis.json)

## Fresh held-out check

The protocol kept the two-second forecast and midpoint rule fixed and used seed 123458 for fresh B1 and B2 controls. Both runs authenticated 48/48 readings. Point forecasts matched the affordable set in **0/22** paired windows. Neither action fit the synthetic budget in any of them. Median underestimation was **65.1 µJ**, and the median predicted action difference was **24.8 µJ**. AES used less modeled energy in 20/22 windows.

An empirical uncertainty envelope estimated using the separately archived seed-223457 stationary traces abstained on all 21 original windows and all 22 fresh windows. That stopped unjustified affordability selections but yielded zero validated battery-driven choices. The research requirement stays open and the production ranker still uses cost and feasibility. These cap-one stationary windows use hypothetical residuals and share a simulation seed within each cohort. [Frozen held-out protocol](../results/phase_05/z1-ranking-diagnosis-20261120/holdout-protocol.json) · [Fresh paired results](../results/phase_05/z1-ranking-diagnosis-20261120/holdout-result.json)

The initial component replay multiplied interval tick deltas directly. Production floors cumulative component totals before summing. The corrected script takes the difference of the two floored cumulative values, then normalizes to two seconds. The first failed comparison is preserved. [First replay log](../results/phase_05/z1-ranking-diagnosis-20261120/diagnosis-first.log)

## Current-source Phase 4 sampling and cutoff

Rebuilt and ran the 125 ms and 250 ms sampler cases using the pinned Z1 simulator, a 9 J budget on node 2 and seed 223456. The raw replay verified both final energy totals through the production C reconciler, both removals and all 26 indexed artifact and binary hashes.

| Sampling | Node 2 removal | Node 3 authenticated readings before / after removal | Post-removal application or RF events by node 2 |
| --- | ---: | ---: | ---: |
| 125 ms | 158.666 s | 38 / 0 | 0 |
| 250 ms | 159.416 s | 38 / 0 | 0 |

Node 3's last parent before removal was node 2 in both runs. It reported no parent afterward and kept generating readings. The observed removal times differed by 0.750 s. Both runs demonstrate the current forwarding cutoff, with the broader source-cohort limits and Phase 4 human acceptance tracked separately. [Cutoff and reconciliation ledger](../results/phase_05/z1-ranking-diagnosis-20261120/depletion-replay.json)

## Reproduction

The fresh simulation commands and pinned container identities are embedded in each run manifest. The diagnosis commands below consume the saved artifacts.

```bash
PYTHONPATH=host python3 -B results/phase_05/z1-ranking-diagnosis-20261120/diagnose-archive.txt
PYTHONPATH=host python3 -B results/phase_05/z1-ranking-diagnosis-20261120/diagnose.txt --holdout
PYTHONPATH=host python3 -B results/phase_05/z1-ranking-diagnosis-20261120/depletion-replay.txt
```

Full current-source matrix acceptance still combines targeted current evidence with separately identified archived runs. Phase 4 and 5 human sign-off and an independent second-person reproduction remain pending. Phase 6 remains at its checkpoint.

The switching benchmark was also rebuilt and rerun on this host. Source hashes matched, the Z1 firmware binary was byte-identical, and all 64 paired samples matched exactly. This local check provides the expected output for the independent reviewer. [Repeat manifest](../results/phase_05/z1-transition-20261120-repeat/manifest.json) · [Comparison](../results/phase_05/z1-ranking-diagnosis-20261120/transition-repeat-comparison.json)
